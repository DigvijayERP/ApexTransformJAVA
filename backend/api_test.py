"""
API test — drives a complete run over HTTP.

    cd backend && python api_test.py

No network, no credentials, no key. The MODEL is stubbed and QAD calls are
dry-run; the FastAPI app, routers, engine, builders and store are all real.

This covers what pipeline_test.py cannot: request/response shapes, status
codes, and the auth gate. A stage function that works when called directly can
still be unreachable or wrongly-coded over HTTP.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Point the store at a throwaway database BEFORE the app imports it.
from core import store as _store
_TMP = Path(tempfile.mkdtemp(prefix="adaptive_api_")) / "api.db"
_store.DB_PATH = _TMP

from fastapi.testclient import TestClient  # noqa: E402

from core import llm  # noqa: E402
from pipeline_test import stub  # noqa: E402  - reuse the same canned model

FAILURES: list = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def main() -> int:
    llm.set_stub(stub)
    os.environ.pop("ADAPTIVE_API_TOKEN", None)

    from main import app
    with TestClient(app) as c:

        section("1. Manifest — the frontend's only source of stage identity")
        r = c.get("/api/run/stages")
        check("200", r.status_code, 200)
        m = r.json()
        check("seven stages", m["total"], 7)
        check("order", [s["id"] for s in m["stages"]],
              ["requirements", "fields", "form", "handler", "view", "lookups", "deploy"])
        check("conditional flags exposed",
              [s["id"] for s in m["stages"] if s["conditional_on"]],
              ["handler", "lookups"])
        check("recovery stage exposed too", m["recovery"]["id"], "fields.autofix")

        section("2. Health — reports the gaps rather than hiding them")
        h = c.get("/api/health").json()
        check("docs grounded", h["docs"]["all_grounded"], True)
        check("auth gap surfaced", h["auth_enforced"], False)
        check("and warned about",
              any("UNAUTHENTICATED" in w for w in h["warnings"]), True)
        check("pipeline shape reported", h["pipeline"]["conditional"],
              ["handler", "lookups"])
        check("not ok while warnings stand", h["ok"], False)

        section("3. A full run, over HTTP")
        r = c.post("/api/run", json={"user_input": "an order tracking BC"})
        check("201", r.status_code, 201)
        run_id = r.json()["run_id"]
        check("dry-run by default", r.json()["dry_run"], True)
        check("starts at requirements", r.json()["first_stage"], "requirements")

        for stage_id in ("requirements", "fields", "form"):
            rr = c.post(f"/api/run/{run_id}/stage/{stage_id}", json={})
            check(f"{stage_id} ran", rr.status_code, 200)
            ap = c.post(f"/api/run/{run_id}/stage/{stage_id}/approve")
            check(f"{stage_id} approved", ap.json()["approved"], True)

        # Stage 4 needs a Browse URI; supply it through the request body.
        rr = c.post(f"/api/run/{run_id}/stage/handler", json={
            "browse_uris": {"customerName": "urn:browse:bebrowse:com.qad.erp.base.customers"}})
        check("handler ran", rr.status_code, 200)
        check("URI substituted over the wire",
              "com.qad.erp.base.customers" in rr.json()["artifact"]["typescript"], True)
        c.post(f"/api/run/{run_id}/stage/handler/approve")

        rr = c.post(f"/api/run/{run_id}/stage/view", json={})
        check("view is ungated", rr.json()["gated"], False)
        c.post(f"/api/run/{run_id}/stage/view/approve")

        # Stage 6 offers its choices first, then takes configuration.
        rr = c.post(f"/api/run/{run_id}/stage/lookups", json={})
        check("lookups await configuration",
              rr.json()["artifact"]["awaiting_configuration"], True)
        rr = c.post(f"/api/run/{run_id}/stage/lookups", json={"configs": [{
            "field_code": "customerName",
            "browse_uri": "urn:browse:bebrowse:com.qad.erp.base.customers",
            "browse_label": "Customers", "browse_entity": "customer",
            "result_field": "customer.name", "search_field": "customer.name"}]})
        check("lookup built", len(rr.json()["artifact"]["lookups"]), 1)
        c.post(f"/api/run/{run_id}/stage/lookups/approve")

        rr = c.post(f"/api/run/{run_id}/stage/deploy", json={})
        check("deploy is terminal", rr.json()["artifact"]["terminal"], True)
        ap = c.post(f"/api/run/{run_id}/stage/deploy/approve")
        check("run complete", ap.json()["complete"], True)

        section("4. Refresh mid-flow restores everything")
        state = c.get(f"/api/run/{run_id}").json()
        check("every stage approved",
              {s["status"] for s in state["stages"]}, {"approved"})
        check("audit trail returned", len(state["writes"]), 9)
        check("bearer never leaves the server",
              {w["request"]["headers"]["Authorization"] for w in state["writes"]},
              {"Bearer <token>"})

        one = c.get(f"/api/run/{run_id}/stage/fields").json()
        check("stored artifact retrievable", one["artifact"]["bc_pascal"], "PipelineOrder")
        check("artifact kind tells the UI how to render", one["artifact_kind"], "field_spec")
        check("editable flag exposed", one["editable"], True)
        check("history preserved", one["attempt"], 1)

        section("5. Errors are the right shape")
        check("unknown run 404s", c.get("/api/run/nope").status_code, 404)
        check("unknown stage 404s",
              c.post(f"/api/run/{run_id}/stage/nope", json={}).status_code, 404)
        check("a stage that never ran 404s",
              c.get(f"/api/run/{run_id}/stage/fields.autofix").status_code, 404)
        check("empty prompt rejected by validation",
              c.post("/api/run", json={"user_input": ""}).status_code, 422)
        check("view cannot be skipped - it is not conditional",
              c.post(f"/api/run/{run_id}/stage/view/skip", json={}).status_code, 422)

        section("6. The regeneration lock, over HTTP")
        # Dry-run writes do not lock, so this run is still fully regenerable.
        one = c.get(f"/api/run/{run_id}/stage/requirements").json()
        check("dry-run leaves regeneration open", one["can_regenerate"], True)

        live = c.post("/api/run", json={"user_input": "live one", "dry_run": False}).json()
        lid = live["run_id"]
        c.post(f"/api/run/{lid}/stage/requirements", json={})
        c.post(f"/api/run/{lid}/stage/requirements/approve")
        # Simulate a successful live write without touching the network.
        import asyncio
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            _store.record_write(lid, "fields", "bc.create", ok=True, dry_run=False))
        blocked = c.post(f"/api/run/{lid}/stage/requirements/regenerate",
                         json={"instruction": "change it"})
        check("409 CONFLICT, not 403", blocked.status_code, 409)
        check("reason explains why", "already written to QAD" in blocked.json()["detail"], True)
        check("and offers a way forward",
              "different Business Component name" in blocked.json()["detail"], True)
        check("GET agrees it is locked",
              c.get(f"/api/run/{lid}/stage/requirements").json()["can_regenerate"], False)

        section("7. Auth, once a token is configured")
        os.environ["ADAPTIVE_API_TOKEN"] = "s3cret-token"
        check("health now reports it enforced",
              c.get("/api/health").json()["auth_enforced"], True)
        check("creating a run without a token is 401",
              c.post("/api/run", json={"user_input": "x"}).status_code, 401)
        check("approving without a token is 401",
              c.post(f"/api/run/{run_id}/stage/deploy/approve").status_code, 401)
        check("a wrong token is 401",
              c.post("/api/run", json={"user_input": "x"},
                     headers={"Authorization": "Bearer wrong"}).status_code, 401)
        check("the right token works",
              c.post("/api/run", json={"user_input": "x"},
                     headers={"Authorization": "Bearer s3cret-token"}).status_code, 201)
        check("reads stay open - they expose no secrets",
              c.get("/api/run/stages").status_code, 200)
        os.environ.pop("ADAPTIVE_API_TOKEN", None)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print(f"All checks passed. Temp db: {_TMP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
