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

    section("10. Stage manifest")
    check("five stages", stages.total(), 5)
    check("stage order", [s.id for s in stages.STAGES],
          ["requirements", "fields", "form", "view", "deploy"])
    check("view stage is ungated", stages.get("view").gated, False)
    check("every other stage is gated",
          all(s.gated for s in stages.STAGES if s.id != "view"), True)
    check("fields stage writes 3 endpoints", len(stages.get("fields").writes), 3)
    check("downstream of fields", [s.id for s in stages.stages_after("fields")],
          ["form", "view", "deploy"])
    check("deploy is terminal", stages.next_after("deploy"), None)
    known = set(config.list_endpoints())
    referenced = {w for s in stages.STAGES for w in s.writes}
    check("every stage write exists in the registry", sorted(referenced - known), [])

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print("All checks passed. No network call was made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
