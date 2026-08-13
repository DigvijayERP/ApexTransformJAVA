"""
Offline smoke test. Builds every Case-1 payload from a sample spec and asserts
the app identity actually landed in the URIs.

Makes NO network call and needs no credentials. Run it after any change to
config, identity or the builders:

    cd backend && python smoke_test.py

It exists because "the file was written" is not evidence the payload is right
(working rule 8). Every assertion below compares against a value read out of the
AUX reference implementation, so a silent shape change is caught here rather
than by QAD rejecting a deploy.
"""
from __future__ import annotations

import json
import sys

from core import config, stages
from builders.identity import AppIdentity
from builders import naming
from builders import event_handler_builder as eh
from builders import lookup_builder as lk
from builders.bc_builder import build_bc_payload, patch_dropdown_fields
from builders.form_builder import build_form_payload
from builders.view_builder import build_view_payload
from builders.deploy_builder import build_deploy_payload

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
    "bc_pascal": "SmokeOrder",
    "description": "Smoke-test business component",
    "fields": [
        {"code": "orderCode", "dataType": "character", "isPrimary": True, "maxLength": 20},
        {"code": "customerName", "dataType": "character", "isRequired": True},
        {"code": "orderDate", "dataType": "date"},
        {"code": "quantity", "dataType": "integer"},
        {"code": "status", "dataType": "dropdown",
         "dropdownValues": [{"code": "OPEN", "label": "Open"},
                            {"code": "SHIPPED", "label": "Shipped"}]},
    ],
}

PLACEMENTS = [
    {"fieldName": "orderCode", "panel": 1, "panelName": "Identity", "gridColumn": 0, "gridRow": 0},
    {"fieldName": "customerName", "panel": 1, "panelName": "Identity", "gridColumn": 1, "gridRow": 0},
    {"fieldName": "orderDate", "panel": 2, "panelName": "Details", "gridColumn": 0, "gridRow": 0},
    {"fieldName": "quantity", "panel": 2, "panelName": "Details", "gridColumn": 1, "gridRow": 0},
    {"fieldName": "status", "panel": 2, "panelName": "Details", "gridColumn": 0, "gridRow": 1},
]


def main() -> int:
    section("1. Config loads")
    ident_raw = config.app_identity()
    check("module", ident_raw["module"], "com.yash.digwish")
    check("module_short", ident_raw["module_short"], "yash.digwish")
    check("app_name", ident_raw["app_name"], "digwish")
    check("datastore_uri", ident_raw["datastore_uri"], "urn:datastore:com.yash.extension")
    print(f"  info  {len(config.list_endpoints())} endpoints registered")

    section("2. URL resolution — no /qad-central/, context root already in base")
    ident = AppIdentity.from_config()
    check(
        "bc.create URL",
        config.resolve_url("bc.create"),
        "https://eeadaptive.yash.com:33005/clouderp/api/qracore/entitymetadatas"
        "?viewUri=urn%3Abe%3Acom.qad.qra.adapter.entity.IEntityBuilderCRUD",
    )
    check(
        "form.save URL (no query)",
        config.resolve_url("form.save"),
        "https://eeadaptive.yash.com:33005/clouderp/api/qracore/viewMetadataV2",
    )
    # oauth sits outside api/qracore
    token_url = config.resolve_url("auth.token.password")
    check("token URL path", token_url.split("?")[0],
          "https://eeadaptive.yash.com:33005/clouderp/oauth/token")
    check("token URL carries grant_type", "grant_type=password" in token_url, True)

    section("3. Spec validation")
    check("valid spec has no problems", naming.validate_spec(SPEC), [])
    bad = {"bc_pascal": "9Bad", "fields": [{"code": "x", "dataType": "nope"}]}
    problems = naming.validate_spec(bad)
    check("bad spec is rejected", len(problems) >= 3, True)

    section("4. BC payload")
    bc = build_bc_payload(SPEC, ident)
    em = bc["payload"]["entityMetadatas"][0]
    check("entityURI", em["entityURI"], "urn:be:com.yash.digwish.SmokeOrder.ISmokeOrder")
    check("appURI", em["appURI"], "urn:app:com.yash.digwish")
    check("appName", em["appName"], "digwish")
    check("bdocumentURI", em["bdocumentURI"], "urn:bd:com.yash.digwish.SmokeOrder.SmokeOrder")
    check("cachedBdocumentURI", em["cachedBdocumentURI"], "urn:bd:com.yash.digwish.SmokeOrder.ISmokeOrder")
    check("field count", len(em["entityFields"]), 5)
    check("one PK", bc["summary"]["pk_count"], 1)
    check("PK is required", em["entityFields"][0]["isRequired"], True)
    check("fieldURI", em["entityFields"][0]["fieldURI"],
          "urn:field:com.yash.digwish.SmokeOrder.ISmokeOrder:SmokeOrder.orderCode")
    check("dropdown produced a data list", len(em["dataLists"]), 1)

    # 'status' is a SQL reserved word, so it is renamed for the physical column.
    # This is a SILENT RENAME the user must be shown at the field gate: they ask
    # for 'status' and QAD gets 'statusCode'.
    check("reserved word renamed", naming.sql_safe("status"), "statusCode")
    check("data list code uses the safe name",
          em["dataLists"][0]["dataListCode"], "statusCode")
    check("entityFieldCode uses the safe name",
          [f["entityFieldCode"] for f in em["entityFields"]],
          ["orderCode", "customerName", "orderDate", "quantity", "statusCode"])
    check("label still reads from the ORIGINAL code",
          [f["fieldLabel"] for f in em["entityFields"]][-1], "Status")
    check("dataListCode blank on first save",
          [f["dataListCode"] for f in em["entityFields"] if f["entityFieldCode"] == "statusCode"],
          [""])
    check("deployment datastore blank on create",
          bc["payload"]["entityDeployments"][0]["dataStoreURI"], "")

    section("5. Dropdown wiring — the second save")
    # QAD echoes back the SAFE field codes, which is what field_list_map is keyed on.
    enriched = {"entityMetadatas": [{"entityFields": [
        {"entityFieldCode": "statusCode", "dataListCode": "", "defaultValue": ""},
        {"entityFieldCode": "orderCode", "dataListCode": "", "defaultValue": ""},
    ]}]}
    patch_dropdown_fields(enriched, bc["field_list_map"])
    wired = enriched["entityMetadatas"][0]["entityFields"]
    check("dropdown got its list", wired[0]["dataListCode"], "statusCode")
    check("dropdown got a default", wired[0]["defaultValue"], "OPEN")
    check("non-dropdown untouched", wired[1]["dataListCode"], "")

    section("6. Form payload")
    form = build_form_payload(PLACEMENTS, SPEC, ident)
    vm = form["payload"]["viewMetadatas"][0]
    check("viewURI", vm["viewURI"], "urn:view:viewmeta:com.yash.digwish.SmokeOrder")
    check("moduleName", vm["moduleName"], "yash.digwish")
    check("panel count", form["summary"]["panel_count"], 2)
    outer = vm["viewMetadata"]["childElements"][0]
    navigator = outer["childElements"][1]
    check("navigator holds both panels", len(navigator["childElements"]), 2)
    panel2 = navigator["childElements"][1]
    check("panel 2 label", panel2["text"], "Details")
    check("panel 2 grid rows", panel2["childElements"][0]["rows"], "27,27")
    pk_element = navigator["childElements"][0]["childElements"][0]["childElements"][0]
    check("PK lookup hidden", pk_element["lookupVisibility"], "Hidden")

    section("7. Form rejects an incomplete layout")
    try:
        build_form_payload(PLACEMENTS[:2], SPEC, ident)
        check("incomplete layout raises", False, True)
    except ValueError as exc:
        check("incomplete layout raises", "not placed on any panel" in str(exc), True)

    section("8. View payload")
    view = build_view_payload(SPEC, ident)
    vrm = view["payload"]["viewResourceMetadatas"][0]
    check("viewURI", vrm["viewURI"], "urn:view:hybridbrowse:com.yash.digwish.smokeorder")
    check("browseURI", vrm["browseURI"], "urn:browse:bebrowse:com.yash.digwish.smokeorder")
    check("app", vrm["app"], "digwish")
    check("entityModule", vrm["entityViewParameters"]["entityModule"], "com.yash.digwish")
    check("appModuleName is a platform constant",
          vrm["entityViewParameters"]["appModuleName"], "qracore")
    check("browse columns", len(vrm["browseView"]["browseColumns"]), 5)
    check("dataType capitalised on browse",
          vrm["browseView"]["browseColumns"][2]["dataType"], "Date")
    check("view label", view["summary"]["view_label"], "Smoke order")

    section("9. Deploy payloads")
    dep = build_deploy_payload("SmokeOrder", ident)
    check("warnings payload keys", sorted(dep["check_warnings"]),
          ["entityURI", "isInitialDataLoaded"])
    check("deploy datastore", dep["deploy"]["dataStoreURI"], "urn:datastore:com.yash.extension")
    check("deploy entityURI", dep["deploy"]["entityURI"],
          "urn:be:com.yash.digwish.SmokeOrder.ISmokeOrder")

    section("10. Event handler — Browse URI placeholders")
    generated = "\n".join([
        "export class SmokeOrderHandler {",
        "  public onInit(): void {",
        '    const custBrowse: string = "{{BROWSE_URI:customerName}}";',
        '    this.ViewController.doHttpGet("{{BROWSE_URI:customerName}}");',
        '    const stBrowse: string = "{{BROWSE_URI:statusCode}}";',
        "  }",
        "}",
    ])
    found = eh.extract_placeholders(generated)
    check("two distinct placeholders", [p.field for p in found],
          ["customerName", "statusCode"])
    check("counts repeats", found[0].occurrences, 2)
    check("carries context for the dialog",
          "const custBrowse" in found[0].context, True)

    resolved = eh.substitute_placeholders(generated, {
        "customerName": "urn:browse:bebrowse:com.qad.erp.customers",
        "statusCode": eh.SKIP,
    })
    check("supplied URI substituted",
          "urn:browse:bebrowse:com.qad.erp.customers" in resolved["code"], True)
    check("both occurrences substituted",
          resolved["code"].count("urn:browse:bebrowse:com.qad.erp.customers"), 2)
    check("skipped one is commented out, AUX-style",
          "// TODO: supply the Browse URI for statusCode" in resolved["code"], True)
    check("comment reads in plain words, no machine token left",
          "<BROWSE URI FOR statusCode NOT SUPPLIED>" in resolved["code"], True)
    check("filled reported", resolved["filled"], ["customerName"])
    check("skipped reported", resolved["skipped"], ["statusCode"])
    check("not fully resolved", resolved["fully_resolved"], False)
    check("no placeholder survives", eh.extract_placeholders(resolved["code"]), [])

    section("11. Event handler payload")
    handler = eh.build_event_handler_payload(
        "SmokeOrder", resolved["code"], "var x = 1;", timing="BEFORE", identity=ident)
    row = handler["payload"]["eventHandlerV2s"][0]
    check("appURI", row["appURI"], "urn:app:com.yash.digwish")
    check("viewURI", row["viewURI"], "urn:view:viewmeta:com.yash.digwish.SmokeOrder")
    check("timing", row["eventHandlerType"], "BEFORE")
    check("appliesTo", row["appliesTo"], "WEB")
    check("isActive", row["isActive"], True)

    # AUX hardcodes BEFORE/WEB; these are parameters here, and validated.
    after = eh.build_event_handler_payload("SmokeOrder", "var a;", "var a;",
                                           timing="after", identity=ident)
    check("timing accepts AFTER, normalised",
          after["payload"]["eventHandlerV2s"][0]["eventHandlerType"], "AFTER")
    try:
        eh.build_event_handler_payload("SmokeOrder", "var a;", "var a;",
                                       timing="SOMETIME", identity=ident)
        check("bad timing rejected", False, True)
    except ValueError as exc:
        check("bad timing rejected", "must be one of" in str(exc), True)

    try:
        eh.build_event_handler_payload("SmokeOrder", generated, "var a;", identity=ident)
        check("unfilled placeholder blocks the POST", False, True)
    except ValueError as exc:
        check("unfilled placeholder blocks the POST",
              "unfilled Browse URI placeholders" in str(exc), True)

    section("12. Lookup Definition — derived for our own BC")
    uris = lk.field_uris_from_bc_payload(bc["payload"])
    check("field URIs harvested from the BC payload we built",
          uris["customerName"],
          "urn:field:com.yash.digwish.SmokeOrder.ISmokeOrder:SmokeOrder.customerName")

    # Pointing at a BC we created: nothing to type.
    target = lk.BrowseTarget.for_own_bc("Training", "className", ident)
    check("browse URI derived", target.uri,
          "urn:browse:bebrowse:com.yash.digwish.training")
    check("result field is a dotted path", target.result_field, "training.className")
    check("search field matches", target.search_field, "training.className")
    check("derived target is usable", target.problems(), [])

    # C4:219-221 — auto-populate targets are form_builder's AutoField names.
    targets = lk.auto_populate_targets(PLACEMENTS, "SmokeOrder", exclude_field="orderCode")
    check("auto-populate list excludes the lookup's own field",
          "orderCode" in [t["field_code"] for t in targets], False)
    check("auto-populate target is a form field name",
          [t["target"] for t in targets if t["field_code"] == "orderDate"],
          ["SmokeOrder_orderDateAutoField2"])

    built = lk.build_lookup_payload(
        lk.LookupSpec(
            field_code="customerName",
            browse=target,
            additional_results=[{"field": "training.location",
                                 "target": "SmokeOrder_quantityAutoField2"}],
        ),
        SPEC, uris, ident)
    row = built["payload"]["lookups"][0]
    # QAD's own Lookup entity declares exactly eight PascalCase fields. A live
    # POST rejected the camelCase payload ported from AUX, which also carried
    # five keys the entity does not have.
    # Shape captured off the wire from QAD's own Lookup Definition Save.
    check("keys are camelCase, as the captured Save shows", sorted(row),
          ["appName", "browseURI", "concurrencyHash", "customData", "dataOperation",
           "disallowedActions", "disallowedActionsMessage", "fieldLabel", "fieldSet",
           "lookupQualifiers", "lookupResultFields", "lookupSearchConditions",
           "moduleURI", "namespace", "reference", "resultField", "searchField",
           "searchFieldOperator"])
    check("field set reuses the BC's own field URI", row["fieldSet"], uris["customerName"])
    check("browse uri", row["browseURI"], target.uri)
    check("module uri", row["moduleURI"], "urn:app:com.yash.digwish")
    # namespace is the module's FIRST TWO SEGMENTS - com.yash, not com.yash.digwish.
    check("namespace is the first two module segments", row["namespace"], "com.yash")
    check("concurrencyHash null on create", row["concurrencyHash"], None)
    check("reference empty, per the confirmed record", row["reference"], "")
    # Element keys named by QAD's own code-571 context paths, 2026-08-12:
    # /lookups/lookups/0/lookupResultFields/0/ResultField|TargetFieldSet.
    check("auto-populate element keys are resultField/targetFieldSet",
          row["lookupResultFields"],
          [{"resultField": "training.location",
            "targetFieldSet": "SmokeOrder_quantityAutoField2"}])
    check("its value formats stay flagged until a fill-carrying save succeeds",
          len(built["unverified"]), 1)

    section("13. Lookup — refuses to send an incomplete config")
    blank = lk.BrowseTarget(uri="", label="X", entity="x", result_field="", search_field="")
    check("blank browse target reports 3 problems", len(blank.problems()), 3)
    bare = lk.BrowseTarget(uri="urn:browse:bebrowse:a.b", label="X", entity="x",
                           result_field="className", search_field="className")
    check("bare column rejected as not dotted", len(bare.problems()), 2)
    try:
        lk.build_lookup_payload(lk.LookupSpec(field_code="customerName", browse=blank),
                                SPEC, uris, ident)
        check("incomplete lookup raises", False, True)
    except ValueError as exc:
        check("incomplete lookup raises", "not ready to send" in str(exc), True)
    try:
        lk.build_lookup_payload(lk.LookupSpec(field_code="nosuchfield", browse=target),
                                SPEC, uris, ident)
        check("unknown field raises", False, True)
    except ValueError as exc:
        check("unknown field raises", "No field URI known" in str(exc), True)

    section("14. Docs grounding")
    from core.docs_loader import docs_loader, BUNDLES, READABLE_SUFFIXES
    # AUX's loader globs *.txt only; every file in Adaptive's Docs/ is .md, so a
    # straight port would have found nothing and said nothing about it.
    check("markdown is readable", ".md" in READABLE_SUFFIXES, True)
    diag = docs_loader.diagnose()
    check("every bundle is grounded", diag["ungrounded"], [])
    check("Docs root found", diag["roots"]["docs"]["exists"], True)

    handler_files = docs_loader.files_for("client_extension_event_handler")
    check("handler bundle uses the event-handler guide",
          any("class_7_Event_Handlers" in f for f in handler_files), True)
    ctx = docs_loader.as_prompt_context("client_extension_event_handler")
    check("wrapped with the heading prompts expect",
          ctx.startswith("## QAD Platform Reference Docs"), True)
    check("and carries real content", len(ctx) > 10_000, True)

    # An unknown bundle must not raise into a run - it degrades, loudly logged.
    check("unknown bundle returns empty", docs_loader.get_bundle("nope"), "")
    check("and leaves no dangling heading", docs_loader.as_prompt_context("nope"), "")

    # Every guide in Docs/ should fit whole; only class 3 is meant to be trimmed.
    check("no bundle was truncated",
          [b["name"] for b in diag["bundles"] if "[TRUNCATED" in
           docs_loader.get_bundle(b["name"])], [])

    # The corpus root is optional enrichment; its absence must not mark a
    # bundle ungrounded, or the handler bundle would read as broken.
    check("corpus is optional", diag["roots"]["corpus"]["exists"], False)
    check("yet the handler bundle is still grounded",
          [b["grounded"] for b in diag["bundles"]
           if b["name"] == "client_extension_event_handler"], [True])

    section("15. Prompts render grounded")
    from agents import prompts
    rendered = prompts.render(prompts.TS_CODE_WRITER, docs_context=ctx)
    check("docs injected into the prompt",
          "QAD Platform Reference Docs" in rendered, True)
    ungrounded = prompts.render(prompts.TS_CODE_WRITER)
    check("and no dangling token when absent",
          "{QAD_DOCS_CONTEXT}" in ungrounded, False)

    section("16. Stage manifest")
    check("seven stages", stages.total(), 7)
    check("stage order", [s.id for s in stages.STAGES],
          ["requirements", "fields", "form", "handler", "view", "lookups", "deploy"])
    check("handler sits between form and view", stages.next_after("form").id, "handler")
    check("view follows handler", stages.next_after("handler").id, "view")
    check("lookups sit before deploy", stages.next_after("lookups").id, "deploy")
    check("view stage is ungated", stages.get("view").gated, False)
    check("every other stage is gated",
          all(s.gated for s in stages.STAGES if s.id != "view"), True)
    check("handler is conditional", stages.get("handler").conditional_on, "handler_needed")
    check("lookups are conditional",
          stages.get("lookups").conditional_on, "any_field_needs_lookup")
    check("exactly two conditional stages",
          [s.id for s in stages.STAGES if s.conditional_on],
          ["handler", "lookups"])
    check("a plain BC therefore runs five stages",
          len([s for s in stages.STAGES if not s.conditional_on]), 5)
    check("fields stage writes 3 endpoints", len(stages.get("fields").writes), 3)
    check("downstream of fields", [s.id for s in stages.stages_after("fields")],
          ["form", "handler", "view", "lookups", "deploy"])
    check("deploy is terminal", stages.next_after("deploy"), None)
    known = set(config.list_endpoints())
    referenced = {w for s in stages.STAGES for w in s.writes}
    check("every stage write exists in the registry", sorted(referenced - known), [])

    section("17. Embedded manifest (Case 2)")
    check("five stages", stages.total("embedded"), 5)
    check("stage order", [s.id for s in stages.stage_list("embedded")],
          ["requirements", "fields", "relate", "deploy", "view"])
    check("the embedded view is GATED, unlike the standard one",
          stages.get("view", "embedded").gated, True)
    check("and conditional on the requirements flag",
          stages.get("view", "embedded").conditional_on, "separate_view_wanted")
    check("deploy is not terminal in embedded mode",
          stages.next_after("deploy", "embedded").id, "view")
    check("every embedded write exists in the registry",
          sorted({w for s in stages.stage_list("embedded") for w in s.writes} - known), [])

    section("18. Embedded builders match the EmbeddedExmpl2 capture")
    from builders import embedded_builder as emb
    from core import parent_registry as pr
    e_spec = {
        "bc_pascal": "CapCheck", "description": "capture fidelity",
        "parent_key": "Items",
        "fields": [
            {"code": "DomainCode", "dataType": "character", "primaryKey": 1, "isRequired": True},
            {"code": "ItemCode", "dataType": "character", "primaryKey": 2, "isRequired": True},
            {"code": "CapCheckCode", "dataType": "character", "primaryKey": 3, "isRequired": True},
            {"code": "Notes", "dataType": "character", "primaryKey": None},
            {"code": "Rating", "dataType": "dropdown", "primaryKey": None,
             "dropdownValues": [{"code": "A", "label": "A"}, {"code": "B", "label": "B"}]},
        ],
    }
    built = emb.build_embedded_entity_payload(e_spec, ident)
    em = built["payload"]["entityMetadatas"][0]
    check("top-level uri is the capture's generic constant",
          em["uri"], "urn:be:com.qad.qra.app.IApp:")
    check("extension flags", [em["isDataExtensionOnly"], em["isDataExtensionEnable"],
          em["isBusinessDocument"]], [True, True, False])
    check("physical table keeps the xx prefix",
          built["payload"]["entityDeployments"][0]["initialTableName"], "xxcapcheck")
    # sql_safe applies to hand-built specs too: DomainCode is reserved, so the
    # builder emits domainCd here (engine-built specs arrive already renamed).
    check("fieldURI follows the capture shape, sql_safe applied",
          em["entityFields"][0]["fieldURI"],
          "urn:field:com.yash.digwish.CapCheck.ICapCheck:xxcapcheck.domainCd")
    check("no modelId and no percent-encoding anywhere",
          ["modelId" in json.dumps(built["payload"]),
           "%2E" in json.dumps(built["payload"])], [False, False])
    check("every field carries a client uniqueID",
          all(f.get("uniqueID") for f in em["entityFields"]), True)
    check("PKs forced required", [f["isRequired"] for f in em["entityFields"][:3]],
          [True, True, True])
    check("dropdown enters the second-save map keyed by its exact code",
          list(built["field_list_map"]), ["Rating"])
    # Raw 'dropdown' type with an empty dataListCode at create, then wired by
    # the second save - the contract Case 1 proved live (DigSmokeTest's status
    # field; QAD's own picker reports it back as dataType 'dropdown').
    check("dropdown keeps its type, dataListCode empty until the second save",
          [(f["dataType"], f["dataListCode"]) for f in em["entityFields"]
           if f["entityFieldCode"] == "Rating"], [("dropdown", "")])
    check("dropdown values ride the create payload as dataLists",
          [(d["dataListCode"], [v["dataValue"] for v in d["dataListValues"]])
           for d in em["dataLists"]], [("Rating", ["A", "B"])])

    rel = emb.build_relation_payload(e_spec, pr.get("Items"), ident,
                                     relation_id="11111111-2222-3333-4444-555555555555")
    row = rel["payload"]["BERelations"][0]
    check("top-level keys, capitalised BERelations included",
          sorted(rel["payload"]), ["BERelations", "supplementaryMessages"])
    check("uri echoes the relationID",
          row["uri"], "urn:be:com.qad.qra.berelation.IBERelation:"
                      "11111111-2222-3333-4444-555555555555")
    check("capture flag set", [row["isExtension"], row["isEmbedded"],
          row["isIncludeOnParent"], row["isParent"], row["isCascadeDeleteForBD"],
          row["isUseInBusinessDocument"]], [True, False, False, False, True, True])
    check("cardinality client-sent", row["cardinality"], "MANYTOONE")
    check("every parent PK mapped",
          [(m["sourceFieldCode"], m["relatedFieldCode"]) for m in row["BERelationFields"]],
          [("DomainCode", "DomainCode"), ("ItemCode", "ItemCode")])

    # A child spec missing a parent-PK mirror must refuse to build, loudly.
    bad = dict(e_spec)
    bad["fields"] = [f for f in e_spec["fields"] if f["code"] != "ItemCode"]
    try:
        emb.build_relation_payload(bad, pr.get("Items"), ident)
        check("missing PK mirror refused", False, True)
    except ValueError as exc:
        check("missing PK mirror refused", "no 'ItemCode' field" in str(exc), True)

    check("InventoryMasters is in the file but never offerable",
          [p.key for p in pr.all_parents() if not p.offerable], ["InventoryMasters"])
    check("WorkOrderMasters carries all three PKs",
          [f["code"] for f in pr.get("WorkOrderMasters").pk_fields],
          ["DomainCode", "WorkOrderNumber", "WorkOrderID"])

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print("All checks passed. No network call was made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
