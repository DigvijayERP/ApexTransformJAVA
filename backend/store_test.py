"""
Offline test for the per-stage artifact store, against a throwaway database.

Makes no network call and needs no credentials:

    cd backend && python store_test.py

The regeneration lock gets most of the attention here because it is the one
piece of logic that can cause real damage if it is wrong in either direction:
too loose and we re-fire a create that QAD cannot undo; too tight and the user
cannot steer their own run.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from core import store

FAILURES: list = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


async def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="adaptive_store_")) / "test.db"
    db = {"db_path": tmp}
    await store.init_db(tmp)

    section("1. Run lifecycle")
    run_id = await store.create_run("build me an order BC", **db)
    run = await store.get_run(run_id, **db)
    check("run created", run["status"], store.RUN_RUNNING)
    check("starts at the first stage", run["current_stage"], "requirements")
    check("dry-run is the default", run["dry_run"], True)

    await store.update_run(run_id, bc_pascal="SmokeOrder", **db)
    check("bc name recorded", (await store.get_run(run_id, **db))["bc_pascal"], "SmokeOrder")
    try:
        await store.update_run(run_id, nonsense=1, **db)
        check("unknown field rejected", False, True)
    except ValueError as exc:
        check("unknown field rejected", "unknown field" in str(exc), True)

    section("2. Attempts append, they do not overwrite")
    await store.save_stage(run_id, "requirements", {"text": "first pass"}, **db)
    a2 = await store.save_stage(run_id, "requirements", {"text": "steered"},
                                instruction="focus on shipping", **db)
    check("second attempt numbered 2", a2, 2)
    latest = await store.get_stage(run_id, "requirements", **db)
    check("latest attempt is returned", latest["artifact"]["text"], "steered")
    check("the steer is preserved", latest["instruction"], "focus on shipping")
    hist = await store.stage_history(run_id, "requirements", **db)
    check("both attempts kept", [h["artifact"]["text"] for h in hist],
          ["first pass", "steered"])
    try:
        await store.save_stage(run_id, "nosuchstage", {}, **db)
        check("unknown stage rejected", False, True)
    except KeyError:
        check("unknown stage rejected", True, True)

    section("3. Dry-run writes never lock")
    await store.set_stage_status(run_id, "requirements", store.STAGE_APPROVED, **db)
    await store.save_stage(run_id, "fields", {"fields": []}, **db)
    await store.record_write(run_id, "fields", "bc.create",
                             ok=True, dry_run=True, request={"m": "POST"}, **db)
    check("a dry-run write is recorded", len(await store.writes_for_run(run_id, **db)), 1)
    check("but counts as no live write", await store.has_live_writes(run_id, **db), False)
    allowed, why = await store.can_regenerate(run_id, "requirements", **db)
    check("upstream still regenerable after a dry run", allowed, True)
    check("no reason given when allowed", why, "")

    section("4. A live write locks itself and everything upstream")
    await store.record_write(run_id, "fields", "bc.create",
                             ok=True, dry_run=False, request={"m": "POST"}, **db)
    check("now there is a live write", await store.has_live_writes(run_id, **db), True)

    allowed, why = await store.can_regenerate(run_id, "fields", **db)
    check("the writing stage itself is locked", allowed, False)
    check("reason names the stage", "'Field mapping' has already written" in why, True)
    check("reason names the endpoint", "bc.create" in why, True)
    check("reason offers a way forward", "different Business Component name" in why, True)

    allowed, why = await store.can_regenerate(run_id, "requirements", **db)
    check("upstream is locked too", allowed, False)
    check("reason explains the downstream cause",
          "runs after 'Requirement gathering'" in why, True)

    section("5. Downstream stages stay free")
    for later in ("form", "handler", "view", "lookups", "deploy"):
        allowed, _ = await store.can_regenerate(run_id, later, **db)
        check(f"'{later}' still regenerable", allowed, True)

    section("6. A rejected live write changes nothing, so it must not lock")
    run2 = await store.create_run("second run", **db)
    await store.save_stage(run2, "fields", {"fields": []}, **db)
    await store.record_write(run2, "fields", "bc.create", ok=False, dry_run=False,
                             response={"error": "already exists"}, **db)
    allowed, _ = await store.can_regenerate(run2, "fields", **db)
    check("failed write does not lock", allowed, True)
    check("but it is still audited", len(await store.writes_for_run(run2, **db)), 1)

    section("7. The run's stage list")
    listing = await store.run_stages(run_id, **db)
    check("every stage appears", len(listing), 7)
    check("stage order preserved", [s["id"] for s in listing][:3],
          ["requirements", "fields", "form"])
    by_id = {s["id"]: s for s in listing}
    check("approved stage reports approved", by_id["requirements"]["status"], "approved")
    check("attempt count surfaced", by_id["requirements"]["attempts"], 2)
    check("untouched stage is pending", by_id["deploy"]["status"], "pending")
    check("conditional flag carried", by_id["lookups"]["conditional"], True)
    check("view marked as ungated", by_id["view"]["gated"], False)
    check("view still writes to QAD", by_id["view"]["writes_to_qad"], True)

    section("8. Skipping a conditional stage")
    await store.save_stage(run_id, "handler", {"needed": False},
                           status=store.STAGE_SKIPPED, **db)
    await store.set_stage_status(run_id, "handler", store.STAGE_SKIPPED, **db)
    by_id = {s["id"]: s for s in await store.run_stages(run_id, **db)}
    check("skipped stage reports skipped", by_id["handler"]["status"], "skipped")
    check("skipping wrote no QAD call",
          [w for w in await store.writes_for_run(run_id, **db) if w["stage_id"] == "handler"],
          [])

    section("9. Audit trail survives for the whole run")
    writes = await store.writes_for_run(run_id, **db)
    check("both attempts at bc.create are kept", len(writes), 2)
    check("dry-run flag distinguishes them",
          [w["dry_run"] for w in writes], [True, False])
    check("request body round-trips", writes[0]["request"], {"m": "POST"})

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print(f"All checks passed. Temp db: {tmp}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
