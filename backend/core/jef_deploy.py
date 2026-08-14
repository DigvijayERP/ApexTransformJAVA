"""
Uploads the extension jar, and records what was uploaded.

THE WIRE CONTRACT, ESTABLISHED LIVE 2026-08-14 (not inferred)

    POST {base}/api/qracore/sse/upload-packages?appURI={app_uri}
    Authorization: Bearer <token>
    multipart/form-data with EXACTLY ONE part:
        name="files"; filename="<fullAppName>-ext-cust.jar"
        Content-Type: application/java-archive

    success  HTTP 200, Content-Length: 0, EMPTY body
    failure  HTTP 4xx, {"errors": ["..."]}

There is no `submitResult` envelope, so success is the HTTP status alone. The
failure shape was learned the hard way: uploading a jar with no classes is
rejected with 400 "JAR file does not contain any signed entries", which is why
"deploy nothing" must be expressed as a jar holding one inert placeholder class.

WHY EVERY ATTEMPT IS RECORDED

QAD cannot be asked what is deployed. The upload also REPLACES the whole set,
so a class missing from the new jar is deleted with no warning and a 200 either
way. `store.jef_deploys` is therefore the only record of the live state, and
this module is the only writer of it: recording and sending live in one place
so they cannot drift.

⚠️ The VS Code plugin fails to deploy on this environment ("socket hang up",
its own Node HTTP layer - OPTIONS proves the route is healthy). This path works.
It is not a convenience.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core import config, store
from core.logging_setup import get_logger
from core.maven import jar_classes

logger = get_logger("adaptive.jef")

DEPLOY_ENDPOINT = "jef.deploy"
PART_FIELD_NAME = "files"          # confirmed live; not a guess
PART_CONTENT_TYPE = "application/java-archive"


class JefDeployError(RuntimeError):
    """The jar cannot be deployed, or QAD refused it."""


@dataclass
class DeployPlan:
    """Everything the gate must show BEFORE the user approves an upload."""
    jar: Path
    classes: List[str]
    url: str
    diff: Dict[str, Any]
    jar_bytes: int
    jar_sha256: str

    @property
    def erases(self) -> List[str]:
        return list(self.diff.get("removed") or [])

    def warnings(self) -> List[str]:
        """The loud parts. Ordered most-dangerous first."""
        out: List[str] = []
        if self.erases:
            out.append(
                "THIS DEPLOY DELETES " + str(len(self.erases)) + " EXTENSION(S): "
                + ", ".join(self.erases)
                + ". Uploading replaces the entire jar, so anything not in it stops "
                  "working immediately. QAD returns 200 either way and gives no warning.")
        if not self.diff.get("known"):
            out.append(self.diff.get("note") or "")
        if not self.classes:
            out.append(
                "The jar contains no classes. QAD rejects an empty jar with HTTP 400, "
                "so this upload will fail. To deploy nothing, keep one inert placeholder "
                "class in the workspace.")
        return [w for w in out if w]

    def summary(self) -> Dict[str, Any]:
        return {
            "jar": self.jar.name,
            "jar_bytes": self.jar_bytes,
            "jar_sha256": self.jar_sha256[:16],
            "url": self.url,
            "part_field_name": PART_FIELD_NAME,
            "part_filename": self.jar.name,
            "part_content_type": PART_CONTENT_TYPE,
            # The FULL list, deliberately, not a diff: under whole-jar
            # replacement this is the complete deployed set afterwards.
            "classes_after_deploy": self.classes,
            "added": self.diff.get("added") or [],
            "kept": self.diff.get("kept") or [],
            "removed": self.erases,
            "previously_deployed_known": bool(self.diff.get("known")),
        }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


async def plan(jar: Path, app_uri: Optional[str] = None,
               db_path: Optional[Path] = None) -> DeployPlan:
    """What this upload would do. Reads only; sends nothing."""
    jar = Path(jar)
    if not jar.is_file():
        raise JefDeployError(
            f"No jar at {jar}. Run the build stage first - `mvn clean package` "
            f"produces target/<fullAppName>-ext-cust.jar.")
    app = app_uri or config.app_uri()
    classes = jar_classes(jar)
    diff = await store.deploy_diff(app, classes, db_path=db_path)
    return DeployPlan(
        jar=jar,
        classes=classes,
        url=config.resolve_url(DEPLOY_ENDPOINT, {"app_uri": app}),
        diff=diff,
        jar_bytes=jar.stat().st_size,
        jar_sha256=_sha256(jar),
    )


async def deploy(jar: Path, *, dry_run: bool = True, app_uri: Optional[str] = None,
                 run_id: Optional[str] = None,
                 db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Upload the jar, or rehearse it. Records the attempt either way.

    A dry run reports exactly what would be sent and touches nothing - the same
    promise every other stage in this project keeps.
    """
    import httpx
    from qad_client import get_token

    p = await plan(jar, app_uri=app_uri, db_path=db_path)
    app = app_uri or config.app_uri()

    if dry_run:
        await store.record_deploy(
            app, p.classes, ok=True, dry_run=True, jar_bytes=p.jar_bytes,
            jar_sha256=p.jar_sha256, run_id=run_id, db_path=db_path,
            response={"rehearsed": True})
        logger.info("[JEF] dry run: would upload %d class(es) to %s", len(p.classes), app)
        return {"ok": True, "dry_run": True, "plan": p.summary(),
                "warnings": p.warnings(), "status_code": None, "response": None}

    token = await get_token()
    data = p.jar.read_bytes()
    logger.info("[JEF] uploading %s (%d bytes, %d class(es))",
                p.jar.name, len(data), len(p.classes))
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            p.url,
            headers={"Authorization": f"Bearer {token}"},
            files={PART_FIELD_NAME: (p.jar.name, data, PART_CONTENT_TYPE)},
        )

    body: Any = resp.text or ""
    if body:
        try:
            body = resp.json()
        except ValueError:
            pass
    # Success is the STATUS ALONE: a successful body is empty, and there is no
    # submitResult envelope to inspect.
    ok = resp.is_success

    await store.record_deploy(
        app, p.classes, ok=ok, dry_run=False, jar_bytes=p.jar_bytes,
        jar_sha256=p.jar_sha256, status_code=resp.status_code, response=body,
        run_id=run_id, db_path=db_path)

    if not ok:
        # Surface QAD's own words. No failure mode is well enough known to
        # pattern-match, so nothing here interprets them.
        detail = ""
        if isinstance(body, dict) and body.get("errors"):
            detail = "; ".join(str(e) for e in body["errors"])
        logger.warning("[JEF] deploy refused: HTTP %s %s", resp.status_code, detail)
        return {"ok": False, "dry_run": False, "plan": p.summary(),
                "warnings": p.warnings(), "status_code": resp.status_code,
                "response": body,
                "error": f"QAD refused the upload (HTTP {resp.status_code})"
                         + (f": {detail}" if detail else ".")}

    logger.info("[JEF] deployed: %d class(es) now live on %s", len(p.classes), app)
    return {"ok": True, "dry_run": False, "plan": p.summary(),
            "warnings": p.warnings(), "status_code": resp.status_code,
            "response": body}


async def fetch_dependency_jar(dest: Path, app_uri: Optional[str] = None) -> Path:
    """Download QAD's generated-types jar to `dest`.

    A GET whose only effect is a local file, so it needs no approval gate. It
    lives here rather than in qad_client because that client parses every
    response as JSON, and this one is 3 MB of `application/java-archive`.
    """
    import httpx
    from qad_client import get_token

    url = config.resolve_url("jef.dependency_jar",
                             {"app_uri": app_uri or config.app_uri()})
    token = await get_token()
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if not resp.is_success:
        raise JefDeployError(
            f"QAD refused the dependency jar (HTTP {resp.status_code}). Without it "
            f"there are no generated types to compile against. Body: {resp.text[:300]}")
    body = resp.content
    if not body[:2] == b"PK":
        raise JefDeployError(
            f"The dependency endpoint returned {len(body)} bytes that are not a jar "
            f"(content-type {resp.headers.get('content-type')!r}).")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    logger.info("[JEF] fetched dependency jar -> %s (%d bytes)", dest, len(body))
    return dest


async def live_classes(app_uri: Optional[str] = None,
                       db_path: Optional[Path] = None) -> Optional[List[str]]:
    """What we believe is deployed. None means we have no record.

    None is NOT "nothing is deployed": someone may have deployed by other
    means, and QAD cannot be asked. Callers must say so rather than imply an
    empty set.
    """
    return await store.deployed_classes(app_uri or config.app_uri(), db_path=db_path)
