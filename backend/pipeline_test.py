"""
End-to-end dry run of all seven Case-1 stages.

    cd backend && python pipeline_test.py

No network, no credentials, no API key. Only the MODEL is stubbed — the engine,
every payload builder, the artifact store, the gating logic and the dry-run
recording are all the real thing.

WHY THIS TEST EXISTS, WHEN 141 OTHERS ALREADY PASS

Those test each piece in isolation, against hand-made fixtures. This one checks
that stage N's REAL output is a valid input to stage N+1 — that the field spec
the field stage stores is the shape the form stage reads, that the placements
survive a round trip through SQLite, that the field URIs built at stage 2 are
the ones the lookup stage finds. Chaining bugs cannot be seen from inside a
single unit test, and they are the ones that survive to production.
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

from core import engine, llm, stages, store

FAILURES: list = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


SPEC = {
    "bc_pascal": "PipelineOrder",
    "description": "End-to-end test business component",
    "fields": [
        {"code": "orderCode", "dataType": "character", "isPrimary": True, "maxLength": 20},
        {"code": "customerName", "dataType": "character", "isRequired": True,
         "needsLookup": True},
        {"code": "orderDate", "dataType": "date"},
        {"code": "status", "dataType": "dropdown",
         "dropdownValues": [{"code": "OPEN", "label": "Open"},
                            {"code": "SHIPPED", "label": "Shipped"}]},
    ],
}

PLACEMENTS_REPLY = {"panels": [
    {"panelName": "Identity", "panel": 1, "fields": [
        {"fieldName": "orderCode", "gridColumn": 0, "gridRow": 0},
        {"fieldName": "customerName", "gridColumn": 1, "gridRow": 0}]},
    {"panelName": "Details", "panel": 2, "fields": [
        {"fieldName": "orderDate", "gridColumn": 0, "gridRow": 0},
        {"fieldName": "status", "gridColumn": 1, "gridRow": 0}]},
]}

HANDLER_TS = "\n".join([
    "export class PipelineOrderHandler {",
    "  public onInit(): void {",
    '    const custBrowse: string = "{{BROWSE_URI:customerName}}";',
    "  }",
    "}",
])

CALLS: list = []


async def stub(system: str, user: str, role: str, json_mode: bool) -> str:
    """Answer by which placeholder prompt was sent."""
    # Dispatch on the OPENING LINE only. Matching anywhere in the body is
    # ambiguous: FIELD_CREATOR describes its own input as coming "from the
    # Requirements Gathering Agent", so a body search sends it the wrong reply.
    opening = system.split("\n", 1)[0].strip()
    CALLS.append(opening[:60])

    if opening.startswith("You are a Requirements Gathering Agent"):
        steer = " Honouring: " + user.split("apply this:")[-1].strip() \
            if "apply this:" in user else ""
        return ("An order business component with a code, customer, date and status."
                + steer + "\nHANDLER_NEEDED: yes\nIt validates the order code.")
    if opening.startswith("You are the Field Builder Agent"):
        return json.dumps({"spec": SPEC})
    if opening.startswith("You are the Form Planner Agent"):
        return "Panel 1 Identity: orderCode, customerName. Panel 2 Details: orderDate, status."
    if opening.startswith("You are the Form Field Builder Agent"):
        return json.dumps(PLACEMENTS_REPLY)
    if opening.startswith("You are the Event Handler Planner"):
        return "1. Validate orderCode is present.\n2. Default status to OPEN."
    if opening.startswith("You are a QAD TypeScript Event Handler developer"):
        return HANDLER_TS
    if opening.startswith("You are a TypeScript to JavaScript compiler"):
        return "var PipelineOrderHandler = (function () { return PipelineOrderHandler; }());"
    raise AssertionError(f"stub got an unexpected prompt: {opening[:80]}")


async def main() -> int:
    llm.set_stub(stub)
    tmp = Path(tempfile.mkdtemp(prefix="adaptive_pipeline_")) / "run.db"
    db = {"db_path": tmp}
    await store.init_db(tmp)

    section("0. Prompts render with OUR module, never AUX's")
    from agents import prompts
    ts = prompts.render(prompts.TS_CODE_WRITER)
    # AUX hardcodes com.extensions.customapp in FOUR places INSIDE the TypeScript
    # module the model is told to emit. Leaking it would generate handlers in
    # AUX's namespace on our app - silently, and only visible inside QAD.
    check("AUX's module never appears", "com.extensions.customapp" in ts, False)
    check("nor its pascal form", "ComExtensionsCustomapp" in ts, False)
    check("nor its underscore form", "com_extensions_customapp" in ts, False)
    check("our module substituted", ts.count("com.yash.digwish") >= 3, True)
    check("pascal form derived", "ComYashDigwish" in ts, True)
    check("underscore form derived", "com_yash_digwish" in ts, True)
    # {BCName} and {fieldName} are instructions to the MODEL, not values we fill.
    check("model placeholders left alone", "{BCName}" in ts, True)
    check("browse-uri convention taught", "BROWSE_URI:customerCode" in ts, True)
    check("AUX's comment-it-out instruction is gone",
          "api/TODO/provide-endpoint" in ts, False)
    check("docs slot filled, not left dangling", "{QAD_DOCS_CONTEXT}" in ts, False)
    check("requirements prompt asks for the handler signal",
          "HANDLER_NEEDED" in prompts.render(prompts.REQUIREMENTS_GATHERING), True)
    check("field prompt asks for lookup marking",
          "needsLookup" in prompts.render(prompts.FIELD_CREATOR), True)

    section("1. Stage 1 — requirements")
    run_id = await store.create_run("I need an order tracking BC", dry_run=True, **db)
    out = await engine.run_stage(run_id, "requirements", **db)
    check("gated", out["gated"], True)
    check("produced text", "order business component" in out["artifact"]["text"], True)
    check("handler signal parsed from the summary", out["artifact"]["handler_hint"], True)
    check("no writes declared", out["writes"], [])

    # Regenerating with a steer, before anything has been written.
    out = await engine.regenerate_stage(run_id, "requirements",
                                        instruction="mention shipping", **db)
    check("steer reached the model", "mention shipping" in out["artifact"]["text"], True)
    hist = await store.stage_history(run_id, "requirements", **db)
    check("both attempts preserved", len(hist), 2)
    await engine.approve_stage(run_id, "requirements", **db)

    section("2. Stage 2 — fields, and the writes it fires")
    out = await engine.run_stage(run_id, "fields", **db)
    art = out["artifact"]
    check("bc name surfaced", art["bc_pascal"], "PipelineOrder")
    check("entity uri built from OUR module", art["entity_uri"],
          "urn:be:com.yash.digwish.PipelineOrder.IPipelineOrder")
    check("payload preview present for the gate", "entityMetadatas" in art["payload_preview"], True)
    check("silent rename surfaced to the user",
          art["renamed_fields"], [{"asked_for": "status", "actual_column": "statusCode"}])
    check("and raised as a warning",
          "SQL reserved word" in out["warnings"][0], True)
    check("stage declares three writes", out["writes"],
          ["bc.create", "bc.metadata.read", "bc.metadata.write"])

    # Nothing has been written yet — running a stage never writes.
    check("running wrote nothing", await store.writes_for_run(run_id, **db), [])

    res = await engine.approve_stage(run_id, "fields", **db)
    check("approved", res["approved"], True)
    check("three dry-run calls recorded", len(res["writes"]), 3)
    check("all dry-run", all(w["dry_run"] for w in res["writes"]), True)
    check("advances to the form stage", res["next"], "form")
    check("bc name persisted on the run",
          (await store.get_run(run_id, **db))["bc_pascal"], "PipelineOrder")

    section("3. Dry-run writes leave regeneration open")
    allowed, _ = await store.can_regenerate(run_id, "requirements", **db)
    check("upstream still regenerable", allowed, True)

    section("4. Stage 3 — form reads the spec stage 2 stored")
    out = await engine.run_stage(run_id, "form", **db)
    art = out["artifact"]
    check("two panels", len(art["panels"]), 2)
    check("all four fields placed", len(art["placements"]), 4)
    check("form payload built", "viewMetadatas" in art["payload_preview"], True)
    check("panel label survived the round trip",
          art["panels"][1]["panelName"], "Details")
    await engine.approve_stage(run_id, "form", **db)

    section("5. Stage 4 — handler, with an unfilled Browse URI")
    out = await engine.run_stage(run_id, "handler", **db)
    art = out["artifact"]
    check("placeholder detected", [p["field"] for p in art["browse_placeholders"]],
          ["customerName"])
    check("not fully resolved without input", art["fully_resolved"], False)
    check("unfilled line is commented out",
          "// TODO: supply the Browse URI" in art["typescript"], True)
    check("and warned about", "No Browse URI supplied" in out["warnings"][0], True)

    # Now supply it — the same stage, re-run with the URI.
    out = await engine.run_stage(
        run_id, "handler",
        browse_uris={"customerName": "urn:browse:bebrowse:com.qad.erp.base.customers"}, **db)
    art = out["artifact"]
    check("URI substituted", "com.qad.erp.base.customers" in art["typescript"], True)
    check("fully resolved", art["fully_resolved"], True)
    check("no leftover placeholder", art["browse_placeholders"] and
          "{{BROWSE_URI" in art["typescript"], False)
    await engine.approve_stage(run_id, "handler", **db)

    section("6. Stage 5 — view is ungated but still writes")
    out = await engine.run_stage(run_id, "view", **db)
    check("not gated", out["gated"], False)
    check("hybrid browse uri", out["artifact"]["summary"]["hybrid_browse_uri"],
          "urn:view:hybridbrowse:com.yash.digwish.pipelineorder")
    await engine.approve_stage(run_id, "view", **db)

    section("7. Stage 6 — lookups, offered then configured")
    out = await engine.run_stage(run_id, "lookups", **db)
    art = out["artifact"]
    check("awaits configuration", art["awaiting_configuration"], True)
    check("only the marked field is offered",
          [f["code"] for f in art["fields"]], ["customerName"])
    opts = art["fields"][0]["auto_populate_options"]
    check("auto-populate offers the OTHER form fields",
          sorted(o["field_code"] for o in opts), ["orderCode", "orderDate", "status"])
    check("targets are form_builder's AutoField names",
          [o["target"] for o in opts if o["field_code"] == "orderDate"],
          ["PipelineOrder_orderDateAutoField2"])

    out = await engine.run_stage(run_id, "lookups", configs=[{
        "field_code": "customerName",
        "browse_uri": "urn:browse:bebrowse:com.qad.erp.base.customers",
        "browse_label": "Customers",
        "browse_entity": "customer",
        "result_field": "customer.name",
        "search_field": "customer.name",
        "additional_results": [{"field": "customer.city",
                                "target": "PipelineOrder_orderDateAutoField2"}],
    }], **db)
    art = out["artifact"]
    check("one lookup built", len(art["lookups"]), 1)
    check("fieldSet is the URI stage 2 created", art["lookups"][0]["field_uri"],
          "urn:field:com.yash.digwish.PipelineOrder.IPipelineOrder:PipelineOrder.customerName")
    check("unverified items surfaced, not hidden", len(out["warnings"]), 2)
    await engine.approve_stage(run_id, "lookups", **db)

    section("8. Stage 7 — deploy, terminal")
    out = await engine.run_stage(run_id, "deploy", **db)
    art = out["artifact"]
    check("terminal", art["terminal"], True)
    check("warnings response captured, not discarded",
          art["warnings_response"]["dry_run"], True)
    check("deploy payload carries our datastore",
          art["payload_preview"]["dataStoreURI"], "urn:datastore:com.yash.extension")
    res = await engine.approve_stage(run_id, "deploy", **db)
    check("run complete", res["complete"], True)
    check("no next stage", res["next"], None)
    check("run status", (await store.get_run(run_id, **db))["status"], store.RUN_COMPLETE)

    section("9. The whole run, as the UI would see it")
    listing = await store.run_stages(run_id, **db)
    check("every stage approved", [s["status"] for s in listing],
          ["approved"] * 7)
    writes = await store.writes_for_run(run_id, **db)
    check("nine QAD calls rehearsed", len(writes), 9)
    check("every one a dry run", all(w["dry_run"] for w in writes), True)
    check("in stage order", [w["stage_id"] for w in writes],
          ["fields", "fields", "fields", "form", "handler", "view", "lookups",
           "deploy", "deploy"])
    # The warnings check fires when the dialog OPENS, so it must be audited but
    # must not lock - otherwise merely looking at the deploy screen freezes the run.
    warn_rows = [w for w in writes if w["endpoint_id"] == "deploy.check_warnings"]
    check("warnings check is audited", len(warn_rows), 1)
    check("but marked non-locking", warn_rows[0]["locking"], False)
    check("the actual deploy DOES lock",
          [w["locking"] for w in writes if w["endpoint_id"] == "deploy.business_entity"],
          [True])
    check("each request captured for review",
          all(w["request"] and w["request"].get("url") for w in writes), True)
    check("bearer never stored",
          all(w["request"]["headers"].get("Authorization") == "Bearer <token>"
              for w in writes), True)

    section("10. A conditional stage skipping itself")
    run2 = await store.create_run("plain BC, no extras", dry_run=True, **db)
    await engine.run_stage(run2, "requirements", **db)
    await engine.approve_stage(run2, "requirements", **db)

    llm.set_stub(_no_lookup_stub)
    await engine.run_stage(run2, "fields", **db)
    await engine.approve_stage(run2, "fields", **db)
    await engine.run_stage(run2, "form", **db)
    await engine.approve_stage(run2, "form", **db)
    out = await engine.run_stage(run2, "lookups", **db)
    check("lookups skip themselves", out["skipped"], True)
    check("with a reason", "No field was marked" in out["reason"], True)
    check("and no QAD call",
          [w for w in await store.writes_for_run(run2, **db) if w["stage_id"] == "lookups"],
          [])
    llm.set_stub(stub)

    section("11. A live write closes the door behind it")
    run3 = await store.create_run("live-mode run", dry_run=False, **db)
    await store.save_stage(run3, "fields", {"spec": SPEC}, **db)
    await store.record_write(run3, "fields", "bc.create", ok=True, dry_run=False, **db)
    try:
        await engine.regenerate_stage(run3, "requirements", instruction="x", **db)
        check("upstream regeneration refused", False, True)
    except engine.StageError as exc:
        check("upstream regeneration refused", "already written to QAD" in str(exc), True)
        check("and says how to proceed", "different Business Component name" in str(exc), True)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print(f"All checks passed. {len(CALLS)} stubbed model calls, zero network calls.")
    return 0


async def _no_lookup_stub(system: str, user: str, role: str, json_mode: bool) -> str:
    if system.splitlines()[0].startswith("You are the Field Builder Agent"):
        plain = {k: v for k, v in SPEC.items()}
        plain["fields"] = [{k: v for k, v in f.items() if k != "needsLookup"}
                           for f in SPEC["fields"]]
        return json.dumps({"spec": plain})
    return await stub(system, user, role, json_mode)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
