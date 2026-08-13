"""
Payloads for Case 2: the embedded entity save and the child-to-parent relation.

BUILT FROM THE CAPTURE, NOT FROM AUX. The owner hand-created EmbeddedExmpl2
(embedded under Items) in eeadaptive's own UI on 2026-08-12 and captured every
request off the Network tab: captures/2026-08-12_embedded_EmbeddedExmpl2.md.
All four calls returned 200 and the extension grid appeared on the Items form,
so that capture is the authority for every key below.

WHAT THE CAPTURE KILLED FROM AUX'S VERSION (aux embedded_builder.py):

  * The percent-encoded IEntityDeployment URI scheme ('com%2Eextensions%2E...')
    for entity, deployment, table and per-field uris - the new env's UI sends
    NONE of it. Top-level uri is the generic 'urn:be:com.qad.qra.app.IApp:'.
  * The modelId-from-4 sequence - does not exist on the wire.
  * The hardcoded 'domaincodeEx' domain field name - the capture's was
    'DomainCodee', so only the ROLE is fixed (PK #1, character, mapped to the
    parent's domain field). We default to mirroring the parent's own field
    names, the pattern the capture half-proves with ItemCode -> ItemCode.
  * The magic relationID prefix '8c9676c6-0c12-13a3-f114-' - the capture's is
    a plain UUID, so any client-generated one serves.
  * The single-fk_field model - the captured relation maps EVERY parent PK.

SPEC SHAPE consumed here (produced by the embedded field stage):
  {bc_pascal, description, parent_key, wants_separate_view,
   fields: [{code, label, dataType, primaryKey (1-based ordinal or None),
             isRequired, maxLength?, dropdownValues?, defaultValue?}]}
Field codes are PascalCase, per the capture ('ItemCode', 'DomainCodee'),
unlike Case 1's camelCase. physicalFieldName equals the code.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from builders.identity import AppIdentity, resolve

# Echoed verbatim from the capture. Reads like server data the UI sends back;
# reproduced rather than tidied away, the same call made for
# __gridLockedDummyColumn in the lookup payload.
BROWSE_SEARCH_OPERATORS: Dict[str, List[str]] = {
    "date": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
             "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "character": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
                  "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS",
                  "CONTAINS", "STARTS_WITH", "ENDS_WITH"],
    "datetime": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
                 "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "int64": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
              "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "datetime-tz": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
                    "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "integer": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
                "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "decimal": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL",
                "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "logical": ["EQUALS", "IS_NOT_NULL", "IS_NULL", "NOT_EQUALS"],
}

# The capture's decimal field carried this; character fields carried "".
_DEFAULT_DISPLAY_FORMAT = {
    "decimal": "->>,>>9.99<<<<",
    "date": "99/99/9999",
}

_NUMERIC_TYPES = {"integer", "int64", "decimal"}


def _blank(data_type: str) -> Optional[str]:
    """The capture uses "" for character-ish empties and null for numeric ones."""
    return None if data_type in _NUMERIC_TYPES else ""


def physical_table(bc_pascal: str) -> str:
    """'xx' prefix is the platform convention (capture: 'xxembedded'); the rest
    is free, so bc lowercase keeps it derivable and collision-poor."""
    return "xx" + bc_pascal.lower()


def _entity_field(f: Dict[str, Any], bc: str, table: str,
                  ident: AppIdentity) -> Dict[str, Any]:
    code = str(f["code"])
    dt = str(f.get("dataType", "character"))
    is_pk = f.get("primaryKey") is not None
    return {
        "primaryKey": f.get("primaryKey"),
        "entityFieldCode": code,
        "fieldLabel": f.get("label") or code,
        "physicalFieldName": code,
        "isFormula": False,
        "hasLookup": False,
        "dataType": "character" if dt.startswith("dropdown") else dt,
        "maxLength": f.get("maxLength"),
        "displayFormat": f.get("displayFormat", _DEFAULT_DISPLAY_FORMAT.get(dt, "")),
        "currencyField": "",
        # Dropdowns start empty and are wired by the same GET-patch-POST second
        # save Case 1 uses; QAD assigns the list code server-side at create.
        "dataListCode": "",
        "defaultValue": f.get("defaultValue", _blank(dt)),
        "fieldGroup": "",
        "minValue": _blank(dt),
        "maxValue": _blank(dt),
        "isDescription": False,
        "associatedField": "",
        # QAD forces required on PKs; sending it ourselves keeps the payload
        # honest about what will be true after the save.
        "isRequired": bool(f.get("isRequired")) or is_pk,
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
        # Capture shape: urn:field:{module}.{EntityName}.I{EntityName}:{table}.{Code}.
        # We keep entityName == entityCode == bc (the capture's differed only
        # because the UI tracks a display name separately).
        "fieldURI": f"urn:field:{ident.module}.{bc}.I{bc}:{table}.{code}",
    }


def build_embedded_entity_payload(spec: Dict[str, Any],
                                  identity: Optional[AppIdentity] = None) -> Dict[str, Any]:
    """The one-shot Entity Builder save for an embedded child BC."""
    ident = resolve(identity)
    bc = spec["bc_pascal"]
    table = physical_table(bc)
    entity_uri = ident.entity_uri(bc)

    fields = [_entity_field(f, bc, table, ident) for f in spec["fields"]]

    # Dropdown second-save map, same contract as Case 1's bc_builder: QAD
    # assigns dataListCodes at create, the enriched GET is patched and POSTed
    # back. Keyed by the exact entityFieldCode we sent, sidestepping the
    # sql_safe key mismatch AUX's embedded flow had (PHASE0_AUDIT.md:957-958).
    field_list_map: Dict[str, Dict[str, Any]] = {}
    for f in spec["fields"]:
        dt = str(f.get("dataType", ""))
        if dt.startswith("dropdown") and f.get("dropdownValues"):
            field_list_map[str(f["code"])] = {
                "values": f["dropdownValues"],
                "defaultValue": f.get("defaultValue")
                                 or f["dropdownValues"][0].get("code", ""),
            }

    entity_meta = {
        "customData": None,
        "uri": "urn:be:com.qad.qra.app.IApp:",       # verbatim from the capture
        "entityTables": [],
        "entityRelationships": [],
        "dataLists": [],
        "fieldGroups": [],
        "appURI": ident.module_uri,
        "disallowedActions": "",
        "disallowedActionsMessage": "",
        "moduleURI": ident.module_uri,
        "entityCode": bc,
        "entityDescription": spec.get("description", ""),
        "dataOperation": "",
        "entityURI": entity_uri,
        "businessComponentStatus": "INITIAL",
        "sharedSetType": "",
        "apiUrl": "",
        "bdocumentCode": "",
        "bdocumentURI": "",
        "bdocumentDescription": "",
        "bdocumentBrowseURI": "",
        "bdocumentLabel": "",
        "secureResourceURI": entity_uri,
        "registrationCode": None,
        "isAllowApproval": False,
        "isBusinessDocument": False,
        "isFollowable": True,
        # The two flags that make it an extension child rather than a
        # standalone BC.
        "isDataExtensionOnly": True,
        "isControlFile": False,
        "cachedBdocumentURI": ident.cached_bdoc_uri(bc),
        "isQadStandard": False,
        "isBusinessDocumentCompatible": False,
        "isUseOptimisticLocking": False,
        "doNotExtend": False,
        "doNotExtendReason": "",
        "entityName": bc,
        "scope": "SYSTEM",
        "appName": ident.app_name,
        "entityFields": fields,
        "isDataExtensionEnable": True,
        "isFirstDeployed": False,
        "bcType": "STANDARD",
        "browseSearchOperators": BROWSE_SEARCH_OPERATORS,
        "allowBeRelations": True,
    }

    payload = {
        "entityMetadatas": [entity_meta],
        "lookupBERelations": [],
        "relatedLookups": [],
        "javaExtensionsInfo": [],
        "activityTrackingInfos": [{"activityTracking": False}],
        "entityDeployments": [{
            "entityURI": "",
            "dataStoreURI": "",
            "isDeployed": False,
            "initialDataStoreURI": "",
            "initialTableName": table,
            "isInitialDataLoaded": False,
            "initialFileName": "",
            "isEntityBuilderBased": True,
            "isImportedFromDB": False,
            "allowActivityTracking": False,
            "concurrencyHash": "",
            "dataOperation": "",
            "recordsGenerationPending": False,
            "generationStarted": False,
        }],
    }

    return {
        "payload": payload,
        "entity_uri": entity_uri,
        "field_list_map": field_list_map,
        "summary": {
            "bc_pascal": bc,
            "entity_uri": entity_uri,
            "physical_table": table,
            "field_count": len(fields),
            "pk_codes": [f["entityFieldCode"] for f in
                         sorted((x for x in fields if x["primaryKey"]),
                                key=lambda x: x["primaryKey"])],
        },
    }


def build_relation_payload(spec: Dict[str, Any], parent: Any,
                           identity: Optional[AppIdentity] = None,
                           relation_id: Optional[str] = None) -> Dict[str, Any]:
    """The child-to-parent BERelation - the write that makes it embedded.

    `parent` is a core.parent_registry.Parent. Every parent PK gets a mapping;
    the child field carries the SAME code as the parent field (the capture's
    ItemCode -> ItemCode pattern, with the domain field free-named but here
    also mirrored). The embedded field stage guarantees those child fields
    exist, so a missing one is a programming error and raises.
    """
    ident = resolve(identity)
    bc = spec["bc_pascal"]
    rid = relation_id or str(uuid.uuid4())

    child_codes = {str(f["code"]) for f in spec["fields"]}
    mappings = []
    for pk in parent.pk_fields:
        code = pk["code"]
        if code not in child_codes:
            raise ValueError(
                f"The child spec has no '{code}' field to map onto the parent's "
                f"'{code}' primary key. The embedded field stage must mirror every "
                f"parent PK; parent '{parent.key}' needs: "
                + ", ".join(p["code"] for p in parent.pk_fields))
        mappings.append({
            "sourceFieldCode": code,
            "relatedFieldCode": code,
            "isSourceFieldLiteral": False,
            "sourceFieldLiteral": None,
        })

    relation = {
        "uri": f"urn:be:com.qad.qra.berelation.IBERelation:{rid}",
        "BERelationFields": mappings,
        "BERelationFilterConditions": [],
        "sourceEntityURI": ident.entity_uri(bc),
        "relationID": rid,
        "isExtension": True,
        "moduleURI": ident.module_uri,
        "sourceEntityCode": bc,
        "isLookup": False,
        "relationType": "child",
        "isCascadeDelete": False,
        "isDrill": False,
        # Counterintuitive but capture-confirmed for an embedded extension;
        # the docs screenshot showing the grid checkbox checked describes a
        # different option set (discovery, contradiction C3).
        "isEmbedded": False,
        "isIncludeOnParent": False,
        "isParent": False,
        "isVisualizedAsDropDown": False,
        "sourceAppName": ident.app_name,
        "isCascadeDeleteForBD": True,
        "relationCode": bc,
        "relationLabel": bc,
        "cardinality": "MANYTOONE",
        "relatedEntityCode": parent.entity_code,
        "relatedEntityURI": parent.uri,
        "isUseInBusinessDocument": True,
    }

    return {
        "payload": {"supplementaryMessages": [], "BERelations": [relation]},
        "relation_id": rid,
        "summary": {
            "bc_pascal": bc,
            "parent_key": parent.key,
            "parent_uri": parent.uri,
            "cardinality": "MANYTOONE",
            "mappings": [{"child": m["sourceFieldCode"], "parent": m["relatedFieldCode"]}
                         for m in mappings],
        },
    }
