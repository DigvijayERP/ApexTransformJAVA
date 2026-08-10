"""
View payload for `viewResourceMetadatas` — the browse, maintain and hybrid views.

Ported from aux_web_version/backend/builders/view_builder.py, shape unchanged.

This builder is a PURE FUNCTION OF THE APPROVED SPEC — no LLM call, nothing
generated, nothing to second-guess. That is why stage 4 carries no approval
dialog: there is no authored content for a human to judge. It still writes to
QAD, so what it registered is shown at the stage-5 deploy gate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from builders.identity import APP_MODULE_NAME, AppIdentity, resolve
from builders import naming


def build_view_payload(spec: Dict[str, Any],
                       identity: Optional[AppIdentity] = None) -> Dict[str, Any]:
    ident = resolve(identity)
    bc = spec["bc_pascal"]
    fields = spec["fields"]

    entity_uri = ident.entity_uri(bc)
    table_name = bc

    pk_fields = [f for f in fields if f.get("isPrimary") is True]
    if not pk_fields:
        raise ValueError("No primary key fields found.")

    key_fields = [
        {"entityKeyFieldName": naming.sql_safe(f["code"]), "browseKeyFieldName": None}
        for f in pk_fields
    ]

    browse_columns: List[Dict[str, Any]] = []
    for i, f in enumerate(fields):
        safe = naming.sql_safe(f["code"])
        label = naming.to_display_label(f["code"])
        dt = f["dataType"]
        browse_columns.append({
            "beBrowseRelationID": None,
            "relationId": None,
            "relationName": None,
            "relationshipPath": None,
            "relationshipsChain": None,
            "relationData": None,
            "isSelected": True,
            "field": safe,
            "bcFieldLabel": label,
            "fieldLabel": label,
            "displayLabel": label,
            "isLabelOverridden": False,
            "isSortable": True,
            "businessEntity": bc,
            "detailTable": table_name,
            "physicalTable": None,
            "entityURI": entity_uri,
            "sortPosition": i,
            "isPrimary": f.get("isPrimary", False),
            "isHiddenForUI": False,
            "isFilterOnly": False,
            "isHiddenFilter": False,
            "beBrowseFieldID": None,
            "fieldType": None,
            "displayFormat": None,
            # QAD wants this capitalised here but lowercase in the BC payload.
            "dataType": (dt[0].upper() + dt[1:]) if dt else dt,
            "beBrowseFieldConditions": [],
            "isConditional": False,
        })

    view_label = naming.to_view_label(bc)

    payload = {
        "viewResourceMetadatas": [{
            "isEligibleForMenu": True,
            "isSecure": True,
            "isUseBEBrowse": True,
            "browseView": {
                "browseDatasourceUri": ident.browse_uri(bc),
                "showExcelImport": True,
                "useBackgroundProcessExcelImport": True,
                "excelImportChunkSize": 0,
                "excelExportFetchSize": 0,
                "showExportFields": True,
                "useBusinessDocumentStructure": False,
                "browseColumns": browse_columns,
                "drillDowns": [],
                "initialSortFields": [],
                "tshandlersV2": [],
                "browseActions": [],
            },
            "maintView": {
                "viewMetadata": bc,
                "viewModule": ident.module_short,
                "isExtensible": False,
                "showActivityFeed": True,
                "showAttachment": True,
                "allowEdit": True,
                "allowAddNew": True,
                "allowDelete": True,
                "drillDowns": [],
                "tshandlersV2": [],
                "insights": [],
            },
            "hybridBrowseView": {
                "browseViewUri": ident.browse_view_uri(bc),
                "maintViewUri": ident.maint_view_uri(bc),
            },
            "entityViewParameters": {
                "usesDomain": False,
                "tableName": table_name,
                "appModuleName": APP_MODULE_NAME,
                "dataResourceName": f"be/{entity_uri}",
                "entityModule": ident.module,
                "keyFields": key_fields,
            },
            "moduleUri": ident.module_uri,
            "app": ident.app_name,
            "appURI": ident.module_uri,
            "isEntityVirtual": True,
            "canUseBEBrowse": True,
            "isShowCriteriaInSearch": False,
            "sortingRestrictedTable": False,
            "isBrowseNotExtensibleBC": False,
            "metaURI": ident.meta_uri(bc),
            "viewURI": ident.hybrid_browse_uri(bc),
            "primarySecureURI": entity_uri,
            "entityURI": entity_uri,
            "browseURI": ident.browse_uri(bc),
            "typeField": "HYBRID_BROWSE",
            "mobileCompatibility": "BROWSEANDREADONLYFORM",
            "entityDescription": bc,
            "nameStringCode": view_label,
            "bcBrowseSearchCondition": "",
            "initialBrowseURI": ident.browse_uri(bc),
        }],
    }

    return {
        "status": "built",
        "payload": payload,
        "summary": {
            "bc_pascal": bc,
            "bc_lower": bc.lower(),
            "pk_count": len(pk_fields),
            "pk_codes": [naming.sql_safe(f["code"]) for f in pk_fields],
            "field_count": len(fields),
            "view_label": view_label,
            "browse_uri": ident.browse_uri(bc),
            "hybrid_browse_uri": ident.hybrid_browse_uri(bc),
        },
    }
