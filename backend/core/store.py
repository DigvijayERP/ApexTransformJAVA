"""
Per-stage artifact store. Everything the gated pipeline needs to survive a pause.

AUX persists ONE ROW PER COMPLETED RUN, written in the router after the
generator is exhausted (aux_web_version/backend/routers/client_extensions.py:
185-197). Its `runs` table has no per-step column at all
(aux_web_version/backend/database.py:14-27). So an aborted run leaves zero rows,
and there is nothing to show at a gate and nothing to regenerate from. That is
why this store is a prerequisite for the approval flow rather than a follow-on.

THREE TABLES

  runs            one row per run, with its position and dry-run mode
  stage_artifacts one row per (run, stage, ATTEMPT) - regenerating appends an
                  attempt rather than overwriting, so the history of what was
                  tried and what steered it is preserved
  qad_writes      every QAD call the run made, request and response. This is the
                  audit trail AND the source of truth for the regeneration lock

THE REGENERATION RULE (owner's decision, 2026-08-10)

  Free BEFORE a live write executes. Blocked AFTER.

Every gate sits before its write, so approving is what fires it. That gives a
clean line: until you approve, nothing has left the machine and anything may be
regenerated. Once a write has gone out, re-running the stage that made it would
fail - AUX's own code proves it, refusing a duplicate BC name because a
collision "cannot be repaired by editing fields"
(aux_web_version/backend/pipeline.py:226-231). QAD has no undo and Phase 0 found
no delete path.

DRY-RUN WRITES NEVER LOCK. Nothing left the process, so there is nothing to
regret. That is what makes the whole flow rehearsable without credentials.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from core import stages

DB_PATH = Path(__file__).resolve().parent.parent / "runs.db"

# Run-level status.
RUN_RUNNING = "running"
RUN_AWAITING = "awaiting_approval"
RUN_COMPLETE = "complete"
RUN_FAILED = "failed"

# Stage-level status.
STAGE_RUNNING = "running"
STAGE_AWAITING = "awaiting_approval"
STAGE_APPROVED = "approved"
STAGE_SKIPPED = "skipped"
STAGE_FAILED = "failed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dumps(value: Any) -> str:
    return json.dumps(value, default=str)


def _loads(raw: Optional[str]) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


async def init_db(db_path: Optional[Path] = None) -> None:
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id            TEXT PRIMARY KEY,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL,
                user_input    TEXT NOT NULL,
                mode          TEXT NOT NULL DEFAULT 'standard',
                status        TEXT NOT NULL,
                current_stage TEXT,
                bc_pascal     TEXT,
                dry_run       INTEGER NOT NULL DEFAULT 1,
                error         TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stage_artifacts (
                run_id      TEXT NOT NULL,
                stage_id    TEXT NOT NULL,
                attempt     INTEGER NOT NULL,
                status      TEXT NOT NULL,
                artifact    TEXT,
                instruction TEXT,
                error       TEXT,
                created_at  TEXT NOT NULL,
                approved_at TEXT,
                PRIMARY KEY (run_id, stage_id, attempt)
            )
        """)
        # The audit trail. `dry_run` is what decides whether a row locks
        # anything, so it is stored per write rather than read back off the run
        # (a run's mode could change between stages).
        await db.execute("""
            CREATE TABLE IF NOT EXISTS qad_writes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id       TEXT NOT NULL,
                stage_id     TEXT NOT NULL,
                endpoint_id  TEXT NOT NULL,
                dry_run      INTEGER NOT NULL,
                ok           INTEGER NOT NULL,
                -- Does this call lock regeneration? Only calls made by a
                -- stage's commit, i.e. by an APPROVAL. A stage may also
                -- call QAD while merely RENDERING its gate: the deploy stage
                -- runs deployCheckForWarnings so the dialog can show what QAD
                -- said. Those must be audited but must NOT lock, or simply
                -- opening the deploy dialog would freeze the whole run before
                -- the user approved anything.
                locking      INTEGER NOT NULL DEFAULT 1,
                request      TEXT,
                response     TEXT,
                executed_at  TEXT NOT NULL
            )
        """)
        # THE DEPLOY MANIFEST (Case 3).
        #
        # QAD offers no endpoint that reports which Java extensions are
        # currently deployed - the decompiled plugin has no such call and none
        # was found on the wire. Meanwhile the upload REPLACES the whole jar:
        # a class absent from the new one is deleted, silently, with HTTP 200
        # either way (proven live 2026-08-14).
        #
        # So this table is the ONLY record of what is live. Without it the
        # deploy gate cannot warn "you are about to erase these three
        # validations", and delete cannot know what there is to delete.
        # It is deliberately app-scoped, not run-scoped: the deployed set
        # belongs to the app and outlives any single run.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jef_deploys (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                app_uri     TEXT NOT NULL,
                run_id      TEXT,
                -- JSON array of fully-qualified class names in the uploaded jar
                classes     TEXT NOT NULL,
                jar_bytes   INTEGER NOT NULL DEFAULT 0,
                jar_sha256  TEXT,
                dry_run     INTEGER NOT NULL DEFAULT 1,
                ok          INTEGER NOT NULL,
                status_code INTEGER,
                response    TEXT,
                deployed_at TEXT NOT NULL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_writes_run ON qad_writes(run_id)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_artifacts_run ON stage_artifacts(run_id)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_deploys_app ON jef_deploys(app_uri)")
        await db.commit()


# ── Runs ──────────────────────────────────────────────────────────────────────
async def create_run(user_input: str, mode: str = "standard",
                     dry_run: bool = True, db_path: Optional[Path] = None) -> str:
    run_id = uuid.uuid4().hex[:12]
    now = _now()
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        await db.execute(
            "INSERT INTO runs (id, created_at, updated_at, user_input, mode, status,"
            " current_stage, dry_run) VALUES (?,?,?,?,?,?,?,?)",
            (run_id, now, now, user_input, mode, RUN_RUNNING,
             stages.first(mode).id, 1 if dry_run else 0),
        )
        await db.commit()
    return run_id


async def get_run(run_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM runs WHERE id=?", (run_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    out = dict(row)
    out["dry_run"] = bool(out["dry_run"])
    return out


async def update_run(run_id: str, db_path: Optional[Path] = None, **fields) -> None:
    if not fields:
        return
    allowed = {"status", "current_stage", "bc_pascal", "dry_run", "error"}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"update_run got unknown field(s): {', '.join(sorted(bad))}")
    if "dry_run" in fields:
        fields["dry_run"] = 1 if fields["dry_run"] else 0
    fields["updated_at"] = _now()
    sets = ", ".join(f"{k}=?" for k in fields)
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        await db.execute(f"UPDATE runs SET {sets} WHERE id=?",
                         (*fields.values(), run_id))
        await db.commit()


async def list_runs(limit: int = 50, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ── Stage artifacts ───────────────────────────────────────────────────────────
async def save_stage(run_id: str, stage_id: str, artifact: Any,
                     status: str = STAGE_AWAITING, instruction: str = "",
                     error: str = "", db_path: Optional[Path] = None) -> int:
    """Append an attempt for this stage and return its attempt number.

    Regeneration APPENDS rather than overwrites, so what was tried before — and
    the free-text that steered each retry — stays inspectable.
    """
    stages.get(stage_id)  # raises on an unknown id rather than storing garbage
    path = db_path or DB_PATH
    async with aiosqlite.connect(path) as db:
        async with db.execute(
            "SELECT COALESCE(MAX(attempt), 0) FROM stage_artifacts WHERE run_id=? AND stage_id=?",
            (run_id, stage_id),
        ) as cur:
            row = await cur.fetchone()
        attempt = int(row[0]) + 1
        await db.execute(
            "INSERT INTO stage_artifacts (run_id, stage_id, attempt, status, artifact,"
            " instruction, error, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (run_id, stage_id, attempt, status, _dumps(artifact),
             instruction, error, _now()),
        )
        await db.execute("UPDATE runs SET updated_at=?, current_stage=? WHERE id=?",
                         (_now(), stage_id, run_id))
        await db.commit()
    return attempt


async def get_stage(run_id: str, stage_id: str,
                    db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """The LATEST attempt for a stage — what the gate should display."""
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM stage_artifacts WHERE run_id=? AND stage_id=?"
            " ORDER BY attempt DESC LIMIT 1",
            (run_id, stage_id),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    out = dict(row)
    out["artifact"] = _loads(out["artifact"])
    return out


async def stage_history(run_id: str, stage_id: str,
                        db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM stage_artifacts WHERE run_id=? AND stage_id=? ORDER BY attempt",
            (run_id, stage_id),
        ) as cur:
            rows = await cur.fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["artifact"] = _loads(d["artifact"])
        out.append(d)
    return out


async def set_stage_status(run_id: str, stage_id: str, status: str,
                           db_path: Optional[Path] = None) -> None:
    """Mark the latest attempt approved / skipped / failed."""
    approved = _now() if status in (STAGE_APPROVED, STAGE_SKIPPED) else None
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        await db.execute(
            "UPDATE stage_artifacts SET status=?, approved_at=? WHERE run_id=? AND stage_id=?"
            " AND attempt=(SELECT MAX(attempt) FROM stage_artifacts WHERE run_id=? AND stage_id=?)",
            (status, approved, run_id, stage_id, run_id, stage_id),
        )
        await db.execute("UPDATE runs SET updated_at=? WHERE id=?", (_now(), run_id))
        await db.commit()


async def run_stages(run_id: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """The run's ACTUAL stage list with each one's state.

    Conditional stages that never ran appear with status 'pending' rather than
    being omitted, so the UI can show the whole shape while still rendering only
    what applies. Nothing here is a fixed table — it is derived from the
    manifest plus what this run recorded.
    """
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT stage_id, status, attempt, created_at, approved_at FROM stage_artifacts"
            " WHERE run_id=? ORDER BY attempt",
            (run_id,),
        ) as cur:
            rows = await cur.fetchall()

    latest: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        latest[r["stage_id"]] = dict(r)

    # What earlier stages produced, so a conditional stage can be reported as
    # applying to this run or not — rather than as permanently "optional".
    artifacts: Dict[str, Any] = {}
    for needed in ("requirements", "fields"):
        row = await get_stage(run_id, needed, db_path=db_path)
        if row and row["artifact"]:
            artifacts[needed] = row["artifact"]

    run = await get_run(run_id, db_path=db_path)
    mode = (run or {}).get("mode") or "standard"

    out = []
    for stage in stages.stage_list(mode):
        seen = latest.get(stage.id)
        out.append({
            "id": stage.id,
            "number": stage.number,
            "label": stage.label,
            "gated": stage.gated,
            "conditional": bool(stage.conditional_on),
            "applies": stages.applies(stage.id, artifacts, mode),
            "writes_to_qad": bool(stage.writes),
            "status": seen["status"] if seen else "pending",
            "attempts": seen["attempt"] if seen else 0,
        })
    return out


# ── QAD write audit + the regeneration lock ───────────────────────────────────
async def record_write(run_id: str, stage_id: str, endpoint_id: str, *,
                       ok: bool, dry_run: bool, request: Any = None,
                       response: Any = None, locking: bool = True,
                       db_path: Optional[Path] = None) -> None:
    """Record one QAD call.

    Dry-run calls are recorded too — they are the rehearsal transcript — but
    they never lock. `locking=False` marks a call the stage made while
    RENDERING rather than committing, which is audited but must not freeze
    regeneration.
    """
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        await db.execute(
            "INSERT INTO qad_writes (run_id, stage_id, endpoint_id, dry_run, ok,"
            " locking, request, response, executed_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, stage_id, endpoint_id, 1 if dry_run else 0, 1 if ok else 0,
             1 if locking else 0, _dumps(request), _dumps(response), _now()),
        )
        await db.commit()


async def writes_for_run(run_id: str, live_only: bool = False,
                         db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM qad_writes WHERE run_id=?"
    if live_only:
        sql += " AND dry_run=0"
    sql += " ORDER BY id"
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (run_id,)) as cur:
            rows = await cur.fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["dry_run"] = bool(d["dry_run"])
        d["ok"] = bool(d["ok"])
        d["locking"] = bool(d["locking"])
        d["request"] = _loads(d["request"])
        d["response"] = _loads(d["response"])
        out.append(d)
    return out


async def can_regenerate(run_id: str, stage_id: str,
                         db_path: Optional[Path] = None) -> Tuple[bool, str]:
    """May this stage be regenerated? Returns (allowed, reason-if-not).

    Regenerating a stage re-runs it and everything downstream. So it is safe
    only while NO LIVE WRITE has been executed by that stage or any stage after
    it. A successful live write downstream means re-running would attempt it a
    second time, and QAD offers no way back.

    Three kinds of call are ignored, each for its own reason:
      - dry-run       nothing left the process
      - failed        QAD rejected it, so no state changed — and a duplicate-name
                      rejection is exactly when the user most needs to go back
      - non-locking   made while rendering a gate, not by approving one.
                      Otherwise opening the deploy dialog would freeze the run.
    """
    run = await get_run(run_id, db_path=db_path)
    mode = (run or {}).get("mode") or "standard"
    stage = stages.get(stage_id, mode) if stage_id != stages.RECOVERY_STAGE.id \
        else stages.get(stage_id)
    order = {s.id: i for i, s in enumerate(stages.stage_list(mode))}
    if stage_id not in order:
        # Recovery stages hang off their host; judge them by the host's position.
        order_index = order.get("fields", 0)
    else:
        order_index = order[stage_id]

    for write in await writes_for_run(run_id, live_only=True, db_path=db_path):
        if not write["ok"] or not write["locking"]:
            continue
        w_index = order.get(write["stage_id"])
        if w_index is None or w_index < order_index:
            continue
        blocking_stage = stages.get(write["stage_id"], mode)
        if write["stage_id"] == stage_id:
            detail = f"'{stage.label}' has already written to QAD"
        else:
            detail = (
                f"'{blocking_stage.label}' runs after '{stage.label}' and has already "
                f"written to QAD"
            )
        return False, (
            f"{detail} ({write['endpoint_id']}). Regenerating would re-run that write, and "
            f"QAD has no undo, and a second create fails on the existing record. "
            f"Start a new run with a different Business Component name, or delete it in QAD "
            f"first and re-run."
        )
    return True, ""


async def has_live_writes(run_id: str, db_path: Optional[Path] = None) -> bool:
    return any(w["ok"] for w in await writes_for_run(run_id, live_only=True, db_path=db_path))


# ── The JEF deploy manifest (Case 3) ─────────────────────────────────────────
# Read the schema comment on jef_deploys first: this is the only record of what
# is deployed, because QAD cannot be asked.

async def record_deploy(app_uri: str, classes: List[str], *, ok: bool,
                        dry_run: bool, jar_bytes: int = 0,
                        jar_sha256: Optional[str] = None,
                        status_code: Optional[int] = None,
                        response: Any = None, run_id: Optional[str] = None,
                        db_path: Optional[Path] = None) -> int:
    """Record one upload attempt, successful or not.

    Failures are recorded too: a 400 tells us the deployed set did NOT change,
    which is exactly what the next gate needs in order to diff correctly.
    """
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO jef_deploys (app_uri, run_id, classes, jar_bytes, jar_sha256,"
            " dry_run, ok, status_code, response, deployed_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (app_uri, run_id, json.dumps(sorted(classes)), jar_bytes, jar_sha256,
             1 if dry_run else 0, 1 if ok else 0, status_code,
             json.dumps(response) if response is not None else None, _now()),
        )
        await db.commit()
        return int(cur.lastrowid)


async def deployed_classes(app_uri: str,
                           db_path: Optional[Path] = None) -> Optional[List[str]]:
    """What is live on QAD for this app, per our own record.

    Only SUCCESSFUL, LIVE uploads count: a dry run sent nothing, and a rejected
    one left the previous jar in place.

    None means "we have never successfully deployed this app", which is NOT the
    same as "nothing is deployed" - someone may have deployed by hand, and this
    table cannot know. Callers must present that difference honestly.
    """
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT classes FROM jef_deploys WHERE app_uri=? AND ok=1 AND dry_run=0"
            " ORDER BY id DESC LIMIT 1", (app_uri,)
        ) as cur:
            row = await cur.fetchone()
    return json.loads(row["classes"]) if row else None


async def deploy_history(app_uri: str, limit: int = 20,
                         db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(db_path or DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jef_deploys WHERE app_uri=? ORDER BY id DESC LIMIT ?",
            (app_uri, limit)
        ) as cur:
            rows = await cur.fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["classes"] = json.loads(d["classes"])
        out.append(d)
    return out


async def deploy_diff(app_uri: str, new_classes: List[str],
                      db_path: Optional[Path] = None) -> Dict[str, Any]:
    """What deploying `new_classes` would change. THE deploy gate's content.

    `removed` is the dangerous one: those extensions stop working the moment
    the upload succeeds, with no warning from QAD and a 200 either way. It is
    reported separately from added/kept so a gate can shout about it.
    """
    previous = await deployed_classes(app_uri, db_path=db_path)
    new = sorted(set(new_classes))
    if previous is None:
        return {
            "known": False,
            "previous": [],
            "added": new,
            "kept": [],
            "removed": [],
            "note": ("No successful live deploy of this app has been recorded here, so "
                     "what is currently deployed is unknown. If extensions were deployed "
                     "by other means, this upload REPLACES them and they will stop "
                     "working."),
        }
    prev = sorted(set(previous))
    return {
        "known": True,
        "previous": prev,
        "added": [c for c in new if c not in prev],
        "kept": [c for c in new if c in prev],
        "removed": [c for c in prev if c not in new],
        "note": "",
    }
