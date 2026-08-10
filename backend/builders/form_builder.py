"""
Form-design payload for `viewMetadataV2`.

Ported from aux_web_version/backend/builders/form_builder.py. The element tree
QAD expects is GroupPanelNavigator -> GroupPanel(per panel) -> Grid -> Field,
inside an OuterGrid alongside a SummaryPanel. Shape is byte-identical to AUX's.

Input is a flat placement list: [{fieldName, panel, panelName, gridColumn, gridRow}].
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from builders.identity import AppIdentity, PLATFORM_NAME, resolve
from builders import naming


def _rows_string(fields_in_panel: List[Dict[str, Any]]) -> str:
    """One '27' per grid row the panel uses."""
    max_row = max(f["gridRow"] for f in fields_in_panel)
    return ",".join(["27"] * (max_row + 1))


def _field_element(placement: Dict[str, Any], panel_idx: int, bc_pascal: str,
                   spec_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    safe = naming.sql_safe(placement["fieldName"])
    is_primary = next(
        (f.get("isPrimary", False) for f in spec_fields if f["code"] == placement["fieldName"]),
        False,
    )
    return {
        "childElements": [],
        "dockStyle": "None",
        "entityName": bc_pascal,
        "fieldName": safe,
        "gridColumn": placement["gridColumn"],
        "gridColumnSpan": 1,
        "gridRow": placement["gridRow"],
        "gridRowSpan": 1,
        "width": None,
        "height": 0,
        "isEnabled": True,
        "isReadOnly": None,
        "isRelatedField": False,
        "isBLHidden": False,
        "isExpanded": True,
        "isNullable": None,
        "isTabStop": True,
        "isTextLiteral": True,
        "isUserHidden": False,
        "isVisible": True,
        "labelText": None,
        "labelTextLiteral": True,
        "margin": None,
        "maxLength": None,
        "moduleName": None,
        "name": f"{bc_pascal}_{safe}AutoField{panel_idx}",
        "sourceTableName": bc_pascal,
        "tabIndex": 0,
        "tableName": bc_pascal,
        "type": "Field",
        # A primary key's lookup is hidden — the record is being created, so
        # there is nothing yet to look up.
        "lookupVisibility": "Hidden" if is_primary else "Visible",
        "lookupVisibilityChanged": True,
    }


def _group_panel(panel_num: int, panel_name: str, fields_in_panel: List[Dict[str, Any]],
                 bc_pascal: str, spec_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    grid = {
        "childElements": [_field_element(p, panel_num, bc_pascal, spec_fields)
                          for p in fields_in_panel],
        "columns": "50%,50%",
        "dockStyle": "None",
        "gridColumn": -1,
        "gridColumnSpan": 1,
        "gridRow": -1,
        "gridRowSpan": 1,
        "height": 0,
        "isEnabled": True,
        "isExpanded": True,
        "isTabStop": False,
        "isTextLiteral": True,
        "isVisible": True,
        "labelText": "",
        "labelTextLiteral": True,
        "name": f"{bc_pascal}_NewPanelGroupPanel{panel_num}Grid",
        "rows": _rows_string(fields_in_panel),
        "tabIndex": 0,
        "type": "Grid",
    }
    return {
        "childElements": [grid],
        "dockStyle": "None",
        "gridColumn": -1,
        "gridColumnSpan": 1,
        "gridRow": -1,
        "gridRowSpan": 1,
        "height": 0,
        "includeInGroupPanelNavigator": True,
        "isBLHidden": False,
        "isEnabled": True,
        "isExpanded": True,
        "isTabStop": False,
        "isTextLiteral": False,
        "isUserHidden": False,
        "isVisible": True,
        "labelText": "",
        "labelTextLiteral": True,
        "name": f"{bc_pascal}_NewPanelGroupPanel{panel_num}",
        "tabIndex": 0,
        "text": panel_name,
        "type": "GroupPanel",
        "isLabelOverridden": True,
    }


def build_form_payload(placements: List[Dict[str, Any]], spec: Dict[str, Any],
                       identity: Optional[AppIdentity] = None) -> Dict[str, Any]:
    ident = resolve(identity)
    bc_pascal = spec["bc_pascal"]
    spec_fields = spec["fields"]

    # A field required by the BC but absent from the layout makes the record
    # impossible to save in QAD, so this must never be allowed through silently.
    placed = {str(p.get("fieldName", "")).strip().lower() for p in placements}
    missing = [str(f["code"]) for f in spec_fields
               if str(f["code"]).strip().lower() not in placed]
    if missing:
        raise ValueError(
            f"Form layout is incomplete — {len(missing)} of {len(spec_fields)} field(s) "
            f"are not placed on any panel: {', '.join(missing)}. A required field that is "
            f"missing from the layout makes the record impossible to save in QAD."
        )

    panels_map: Dict[int, Dict[str, Any]] = {}
    for p in placements:
        pnum = p["panel"]
        panels_map.setdefault(pnum, {"panelName": p["panelName"], "fields": []})
        panels_map[pnum]["fields"].append(p)

    panel_numbers = sorted(panels_map)
    group_panels = [
        _group_panel(n, panels_map[n]["panelName"], panels_map[n]["fields"], bc_pascal, spec_fields)
        for n in panel_numbers
    ]

    summary_panel = {
        "childElements": [], "dockStyle": "None",
        "gridColumn": 0, "gridColumnSpan": 1, "gridRow": 0, "gridRowSpan": 1,
        "height": 0, "isEnabled": True, "isExpanded": True, "isTabStop": False,
        "isTextLiteral": False, "isVisible": True, "labelText": "",
        "labelTextLiteral": False, "margin": "", "name": "QraSummaryPanel",
        "tabIndex": 0, "text": "", "type": "SummaryPanel", "width": 0,
    }

    navigator = {
        "childElements": group_panels, "dockStyle": "None",
        "gridColumn": 0, "gridColumnSpan": 1, "gridRow": 1, "gridRowSpan": 1,
        "height": 0, "isEnabled": True, "isExpanded": True, "isTabStop": False,
        "isTextLiteral": False, "isVisible": True, "labelText": "",
        "labelTextLiteral": False, "margin": "", "name": "QraGroupPanelNavigator",
        "tabIndex": 0, "text": "", "type": "GroupPanelNavigator", "width": 0,
    }

    outer_grid = {
        "childElements": [summary_panel, navigator], "columns": "100%",
        "dockStyle": "None", "gridColumn": -1, "gridColumnSpan": 1,
        "gridRow": -1, "gridRowSpan": 1, "height": 0, "isEnabled": True,
        "isExpanded": True, "isTabStop": False, "isTextLiteral": False,
        "isVisible": True, "labelText": "", "labelTextLiteral": False,
        "margin": "12,12,12,12", "name": "OuterGrid", "rows": "27,100%",
        "tabIndex": 0, "text": "", "type": "Grid", "width": 0,
    }

    payload = {
        "viewMetadatas": [{
            "viewURI": ident.view_meta_uri(bc_pascal),
            "platformName": PLATFORM_NAME,
            "viewName": bc_pascal,
            "moduleURI": ident.module_uri,
            "parentURI": None,
            "moduleName": ident.module_short,
            "dataOperation": None,
            "entityURI": ident.entity_uri(bc_pascal),
            "isEligibleForMenu": None,
            "viewMetadata": {
                "name": bc_pascal,
                "entityURI": ident.entity_uri(bc_pascal),
                "childElements": [outer_grid],
            },
            "disallowedActions": None,
            "disallowedActionsMessage": None,
            "viewMetadataAdjusted": False,
            "labelFontFactor": 1.8,
            "defaultLabelWidth": 166,
        }],
    }

    return {
        "status": "built",
        "payload": payload,
        "summary": {
            "bc_pascal": bc_pascal,
            "panel_count": len(panel_numbers),
            "field_count": len(placements),
            "panels": [
                {"panel": n,
                 "panelName": panels_map[n]["panelName"],
                 "fields": len(panels_map[n]["fields"])}
                for n in panel_numbers
            ],
        },
    }
