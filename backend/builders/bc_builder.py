"""
Business Component payload for `entitymetadatas`.

Ported from aux_web_version/backend/bc_builder.py. The payload SHAPE is
byte-identical to AUX's — it is proven against a live QAD and is not the place
to be clever. What changed: app identity is injected rather than hardcoded, and
the naming helpers are shared instead of copy-pasted.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from builders.identity import AppIdentity, ENTITY_DEPLOYMENT_URI, resolve
from builders import naming


def build_data_lists(fields: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, str]]]:
    """QAD dataLists entries plus a field -> list-info map for dropdown fields.

    Shape QAD expects:
      { dataListCode, dataListValues: [{dataValue, dataLabel}, ...], serviceCall: "" }

    The list code is the SQL-safe field code (QAD scopes list codes per entity);
    the default is the first value's code.
    """
    data_lists: List[Dict[str, Any]] = []
    field_list_map: Dict[str, Dict[str, str]] = {}

    for f in fields:
        if f["dataType"] not in naming.DROPDOWN_TYPES:
            continue
        values = f.get("dropdownValues") or []
        if not values:
            raise ValueError(
                f"Field '{f['code']}' is a dropdown but has no `dropdownValues`. "
                f"QAD requires a non-empty data list for every dropdown field."
            )
        for i, v in enumerate(values):
            if not isinstance(v, dict) or "code" not in v:
                raise ValueError(
                    f"Field '{f['code']}' dropdownValues[{i}] must be an object with a 'code' key."
                )

        safe = naming.sql_safe(f["code"])
        field_list_map[safe] = {"listCode": safe, "defaultValue": str(values[0]["code"])}
        data_lists.append({
            "dataListCode": safe,
            "dataListValues": [
                {"dataValue": str(v["code"]), "dataLabel": str(v.get("label", v["code"]))}
                for v in values
            ],
            "serviceCall": "",
        })

    return data_lists, field_list_map


def patch_dropdown_fields(enriched_payload: Dict[str, Any],
                          field_list_map: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """Patch QAD's enriched entity metadata (from the GET) to wire dropdowns.

    QAD's Entity Builder needs two saves: the first creates the BC and its data
    lists, the second points each dropdown field at its list. Non-dropdown
    fields and QAD-generated fields (concurrencyHash, entityFieldID, uri) are
    untouched. Mutates in place and returns the same object.
    """
    for em in enriched_payload.get("entityMetadatas") or []:
        for field in em.get("entityFields") or []:
            info = field_list_map.get(field.get("entityFieldCode"))
            if info:
                field["dataListCode"] = info["listCode"]
                field["defaultValue"] = info["defaultValue"]
    return enriched_payload


def build_bc_payload(spec: Dict[str, Any],
                     identity: Optional[AppIdentity] = None) -> Dict[str, Any]:
    ident = resolve(identity)
    bc = spec["bc_pascal"]
    description = spec.get("description", "")
    fields = spec["fields"]

    entity_uri = ident.entity_uri(bc)
    module_uri = ident.module_uri

    data_lists, field_list_map = build_data_lists(fields)

    pk_counter = 0
    entity_fields: List[Dict[str, Any]] = []

    for f in fields:
        safe = naming.sql_safe(f["code"])
        max_len = naming.resolve_max_length(f["dataType"], f.get("maxLength"))
        is_pk = f.get("isPrimary") is True
        if is_pk:
            pk_counter += 1
        min_max = naming.resolve_min_max(f["dataType"])
        sub_dt = naming.resolve_sub_data_type(f["dataType"])
        # A label the spec carries is the one the user already reads on the
        # existing screen ("Load address"). Deriving one from the code is a
        # fallback, not the intent: it turns vehRef1 into "Veh Ref1", which is
        # exactly what the owner reported on 2026-09-01.
        spec_label = f.get("label")
        label = spec_label.strip() if isinstance(spec_label, str) and spec_label.strip() \
            else naming.to_display_label(f["code"])

        field_obj: Dict[str, Any] = {
            "primaryKey": pk_counter if is_pk else None,
            "entityFieldCode": safe,
            "fieldLabel": label,
            "physicalFieldName": safe,
            "jsonName": safe,
            "dataType": f["dataType"],
            "isFormula": False,
            "formula": "",
            "hasLookup": False,
            "maxLength": max_len,
            "displayFormat": naming.display_format(f["dataType"], max_len),
            "currencyField": "",
            # Populated in the second-pass update, after QAD creates the list.
            "dataListCode": "",
            "defaultValue": naming.resolve_default_value(f["dataType"]),
            "fieldGroup": "",
            "minValue": min_max,
            "maxValue": min_max,
            "isDescription": False,
            "associatedField": "",
            "isRequired": is_pk or f.get("isRequired") is True,
            "isReadOnly": False,
            "isHidden": False,
            "isHiddenForUI": False,
            "isUserDefinedField": False,
            "isDeployed": False,
            "isDiscriminator": False,
            "isFormattedBy": False,
            "formattedBy": "",
            "hasOverrides": False,
            "__gridLockedDummyColumn": "",
            "uniqueID": str(uuid.uuid4()),
            "fieldURI": ident.field_uri(bc, safe),
        }
        if sub_dt:
            field_obj["subDataType"] = sub_dt

        entity_fields.append(field_obj)

    pk_count = sum(1 for f in entity_fields if f["primaryKey"] is not None)
    if pk_count == 0:
        raise ValueError("No primary key field found.")

    payload = {
        "activityTrackingInfos": [{"activityTracking": False}],
        "entityMetadatas": [{
            "uri": ENTITY_DEPLOYMENT_URI,
            "entityTables": [],
            "fieldGroups": [],
            "dataLists": data_lists,
            "apiUrl": "",
            "cachedBdocumentURI": ident.cached_bdoc_uri(bc),
            "bdocumentURI": ident.bdoc_uri(bc),
            "entityURI": entity_uri,
            "secureResourceURI": entity_uri,
            "moduleURI": module_uri,
            "appURI": module_uri,
            "appName": ident.app_name,
            "entityCode": bc,
            "entityName": bc,
            "bdocumentCode": bc,
            "bdocumentLabel": bc,
            "entityDescription": description,
            "bdocumentDescription": "",
            "scope": "SYSTEM",
            "bcType": "Standard",
            "businessComponentStatus": "INITIAL",
            "isBusinessDocument": True,
            "isFollowable": True,
            "isDataExtensionEnable": True,
            "isFirstDeployed": False,
            "browseSearchOperators": naming.BROWSE_SEARCH_OPERATORS,
            "allowBeRelations": True,
            "entityFields": entity_fields,
        }],
        "entityDeployments": [{
            "initialTableName": bc,
            "appURI": module_uri,
            "entityURI": entity_uri,
            "isDeployed": False,
            "isInitialDataLoaded": False,
            "isEntityBuilderBased": True,
            "isImportedFromDB": False,
            "isAutomaticRedeploy": False,
            "recordsGenerationPending": False,
            "generationStarted": False,
            "dataStoreURI": "",
            "concurrencyHash": "",
            "dataOperation": "",
            "initialDataStoreURI": "",
            "initialFileName": "",
            "allowActivityTracking": False,
        }],
    }

    return {
        "status": "built",
        "payload": payload,
        "field_list_map": field_list_map,
        "entity_uri": entity_uri,
        "summary": {
            "bc_pascal": bc,
            "module": ident.module,
            "app_name": ident.app_name,
            "field_count": len(entity_fields),
            "pk_count": pk_count,
            "pk_codes": [f["entityFieldCode"] for f in entity_fields if f["primaryKey"] is not None],
            "dropdown_count": len(data_lists),
        },
    }
