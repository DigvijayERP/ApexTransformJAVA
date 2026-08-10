"""
Read-only environment check. THE FIRST LIVE CALL WE EVER MAKE.

    cd backend && python verify_environment.py

WRITES NOTHING. It authenticates, then issues one GET. There is no POST
anywhere in this file, so it is safe to run against the known-degraded Adaptive
environment and safe to run repeatedly.

WHY IT EXISTS

Every payload shape in this project was read out of the AUX reference
implementation, which targets a DIFFERENT QAD environment (qadee). The
environment-specific parts — base URL, context root, module, app name,
datastore — are all config now and already switched. What no amount of reading
can settle is whether `eeadaptive` runs the same QAD PLATFORM VERSION. If it
does not, payload fields may have been added, renamed or dropped, and we would
only find out when a write failed halfway through a run.

One GET answers it, and proves three things at once:

  1. The URL shape is right. AUX builds {bare-host}/qad-central/api/qracore/...
     while Adaptive's base already carries its context root (/clouderp), so we
     resolve to {base}/api/qracore/... with no extra prefix. That is derived
     from the confirmed JEF contract but has never been exercised.
  2. Auth works — client id, username, password, and the query-string grant.
  3. The entity-metadata model matches what bc_builder produces.

USAGE

    python verify_environment.py                 # auth + endpoint shapes only
    python verify_environment.py <entityURI>     # also diff a real BC's metadata

The second form is the valuable one. Pass any entityURI that exists in the
target environment and it will compare that BC's real field keys against the
ones bc_builder emits, reporting anything QAD has that we do not send, and
anything we send that QAD does not recognise.
"""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Dict, List

from core import config
from core.logging_setup import configure_logging
import qad_client
from builders.identity import AppIdentity
from builders.bc_builder import build_bc_payload

PROBE_SPEC = {
    "bc_pascal": "EnvProbe",
    "description": "shape probe - never sent",
    "fields": [{"code": "probeCode", "dataType": "character", "isPrimary": True}],
}


def line(ch: str = "-", n: int = 74) -> None:
    print(ch * n)


def show(label: str, value: Any) -> None:
    print(f"  {label:<28} {value}")


async def main(entity_uri: str = "") -> int:
    configure_logging()
    problems: List[str] = []

    print("\nADAPTIVE ENVIRONMENT CHECK - read only, writes nothing")
    line("=")

    # ── 1. Configuration ─────────────────────────────────────────────────────
    print("\n1. Configuration")
    line()
    try:
        ident = AppIdentity.from_config()
    except Exception as exc:
        print(f"  FAILED to load app identity: {exc}")
        return 1

    show("environment", config.active_environment_name())
    show("base URL", config.base_url())
    show("app URI", config.app_uri())
    show("module", ident.module)
    show("app name", ident.app_name)
    show("datastore URI", ident.datastore_uri)

    missing = config.missing_required_keys()
    if missing:
        print(f"\n  Cannot continue - missing {', '.join(missing)} in backend/.env")
        return 1
    show("credentials", "present")

    # ── 2. Resolved URLs ─────────────────────────────────────────────────────
    print("\n2. Resolved URLs - confirm the context root is right")
    line()
    for eid in ("auth.token.password", "bc.create", "form.save", "view.register",
                "eventhandler.register", "deploy.business_entity"):
        url = config.resolve_url(eid)
        # Never print the token URL's query - it carries the password.
        show(eid, url.split("?")[0] if eid.startswith("auth.") else url)
    if "/qad-central/" in config.resolve_url("bc.create"):
        problems.append(
            "The resolved URL still contains /qad-central/. Adaptive's base already "
            "carries its context root; check config/environment.json."
        )

    # ── 3. Authentication ────────────────────────────────────────────────────
    print("\n3. Authentication")
    line()
    try:
        token = await qad_client.get_token(force=True)
        show("token acquired", f"yes ({len(token)} chars)")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        print("\n  This is the first thing to fix. Either the base URL / context root is")
        print("  wrong, the credentials are wrong, or the environment is unreachable.")
        return 1

    # ── 4. Entity metadata shape ─────────────────────────────────────────────
    if not entity_uri:
        print("\n4. Entity metadata shape - SKIPPED")
        line()
        print("  Pass an entityURI that exists in this environment to diff its real")
        print("  field keys against what bc_builder emits. This is the check that")
        print("  catches a platform-version difference:")
        print("\n    python verify_environment.py urn:be:<module>.<Bc>.I<Bc>")
    else:
        print(f"\n4. Entity metadata shape - {entity_uri}")
        line()
        result = await qad_client.call("bc.metadata.read", params={"entity_uri": entity_uri})
        if not result.ok:
            print(f"  GET failed: {result.error or result.status_code}")
            problems.append(f"Could not read {entity_uri}: {result.error}")
        else:
            body = result.data.get("data") if isinstance(result.data.get("data"), dict) else result.data
            metadatas = body.get("entityMetadatas") or []
            if not metadatas:
                problems.append("Response carried no entityMetadatas - is that entityURI right?")
            else:
                real = metadatas[0]
                ours = build_bc_payload(PROBE_SPEC, ident)["payload"]["entityMetadatas"][0]

                real_keys, our_keys = set(real), set(ours)
                show("QAD returns keys", len(real_keys))
                show("we send keys", len(our_keys))

                # Keys QAD adds on read (uri, concurrencyHash, ids) are expected and
                # harmless. Keys WE send that QAD does not have are the real risk.
                unknown = sorted(our_keys - real_keys)
                if unknown:
                    print("\n  We send these and QAD's record does not have them:")
                    for k in unknown:
                        print(f"    - {k}")
                    problems.append(
                        f"{len(unknown)} key(s) we send are absent from a real record. "
                        f"Likely a platform-version difference - check each before writing."
                    )
                else:
                    show("all our keys recognised", "yes")

                real_fields = (real.get("entityFields") or [{}])[0]
                our_fields = ours["entityFields"][0]
                f_unknown = sorted(set(our_fields) - set(real_fields))
                if f_unknown:
                    print("\n  Field-level keys we send that the real record lacks:")
                    for k in f_unknown:
                        print(f"    - {k}")
                    problems.append(f"{len(f_unknown)} field key(s) unrecognised.")
                else:
                    show("all field keys recognised", "yes")

    # ── verdict ──────────────────────────────────────────────────────────────
    print()
    line("=")
    if problems:
        print(f"{len(problems)} PROBLEM(S) FOUND - resolve before any write:\n")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Environment check passed. Nothing was written.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "")))
