"""
Tests for the deploy manifest and the erase warning.

Everything here runs against a TEMPORARY database and never contacts QAD. The
properties under test are the ones that keep a whole-jar deploy honest:

  * a dry run must never look like live state
  * a REFUSED deploy must not change what we believe is live
  * planning an upload that drops classes must say so, by name
  * "we have no record" must never be presented as "nothing is deployed"

Run:  python core/jef_deploy_test.py
"""
from __future__ import annotations

import asyncio
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from core import jef_deploy, store  # noqa: E402

FAILURES: list = []
APP = "urn:app:com.yash.digwish"


def check(name, actual, expected):
    if actual == expected:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(name)


def section(title):
    print(f"\n{title}\n" + "-" * len(title))


async def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    db = tmp / "deploys.db"
    await store.init_db(db)

    section("1. With no record, we say so rather than imply an empty set")
    check("live_classes is None, not []",
          await jef_deploy.live_classes(APP, db_path=db), None)
    diff = await store.deploy_diff(APP, ["com.x.A"], db_path=db)
    check("diff reports the state as unknown", diff["known"], False)
    check("nothing is claimed as removed", diff["removed"], [])
    check("and it warns that an unseen deploy would be replaced",
          "REPLACES" in diff["note"], True)

    section("2. A dry run is recorded but is NOT live state")
    await store.record_deploy(APP, ["com.x.Rehearsed"], ok=True, dry_run=True, db_path=db)
    check("still no live record", await jef_deploy.live_classes(APP, db_path=db), None)
    check("but the attempt is in the history",
          len(await store.deploy_history(APP, db_path=db)), 1)

    section("3. A successful live deploy becomes the believed state")
    await store.record_deploy(APP, ["com.x.B", "com.x.A"], ok=True, dry_run=False, db_path=db)
    check("classes recorded, sorted",
          await jef_deploy.live_classes(APP, db_path=db), ["com.x.A", "com.x.B"])

    section("4. A REFUSED deploy must not change what we believe")
    # QAD rejected it, so the previous jar is still installed. Believing the
    # rejected set would make the next diff wrong in the dangerous direction.
    await store.record_deploy(APP, ["com.x.Wrong"], ok=False, dry_run=False,
                              status_code=400, db_path=db)
    check("believed state unchanged",
          await jef_deploy.live_classes(APP, db_path=db), ["com.x.A", "com.x.B"])

    section("5. THE ERASE WARNING")
    # The whole point of the manifest: whole-jar replacement deletes silently
    # and QAD returns 200 either way.
    diff = await store.deploy_diff(APP, ["com.x.A", "com.x.C"], db_path=db)
    check("known state is used", diff["known"], True)
    check("added detected", diff["added"], ["com.x.C"])
    check("kept detected", diff["kept"], ["com.x.A"])
    check("REMOVED detected", diff["removed"], ["com.x.B"])

    plan = jef_deploy.DeployPlan(
        jar=Path("x/com.yash.digwish-ext-cust.jar"), classes=["com.x.A", "com.x.C"],
        url="https://example/upload", diff=diff, jar_bytes=1234, jar_sha256="ab" * 32)
    warns = plan.warnings()
    check("a warning is raised", len(warns) >= 1, True)
    check("it names the doomed class", "com.x.B" in warns[0], True)
    check("it says deletion is silent", "200 either way" in warns[0], True)
    check("the summary shows the FULL post-deploy set, not a diff",
          plan.summary()["classes_after_deploy"], ["com.x.A", "com.x.C"])
    check("and the confirmed wire details",
          (plan.summary()["part_field_name"], plan.summary()["part_content_type"]),
          ("files", "application/java-archive"))

    section("6. An empty jar is refused before it is ever sent")
    empty = jef_deploy.DeployPlan(
        jar=Path("x/empty.jar"), classes=[], url="u",
        diff=await store.deploy_diff(APP, [], db_path=db), jar_bytes=22,
        jar_sha256="00" * 32)
    check("the no-classes warning appears",
          any("rejects an empty jar" in w for w in empty.warnings()), True)
    check("and the erase warning fires too, since everything would go",
          any("DELETES" in w for w in empty.warnings()), True)

    section("7. No deploy when there is no jar")
    try:
        await jef_deploy.plan(tmp / "nope.jar", app_uri=APP, db_path=db)
        check("missing jar raises", False, True)
    except jef_deploy.JefDeployError as exc:
        check("missing jar raises", "build stage first" in str(exc), True)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print("All checks passed. No network call was made.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
