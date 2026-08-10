"""
QAD Lookup Definition payload for the `lookups` endpoint.

Rewritten against the worked example in the platform docs rather than ported
from AUX, because AUX's version derives several values independently and gets
one of them wrong.

CONFIRMED REFERENCE RECORD — Docs/qad_enterprise_platform_class_4...md:180-221,
a lookup created and shown working in the guide:

    Field URI      urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.ClassName
    Field Label    Class Name
    Reference      (empty)
    Browse URI     urn:browse:bebrowse:com.extensions.training.training
    Browse Label   Training
    Result Field   training.className
    Search Field   training.className
    Search Cond.   (empty)
    Addl Result    training.location -> TrainingRoom_locationAutoField1

WHAT THAT SETTLES, AND WHERE AUX GETS IT WRONG

1. FIELD URI CASE. The suffix keeps ORIGINAL case on both entity and field
   ('TrainingRoom.ClassName'). AUX lowercases both
   (aux_web_version/backend/core/lookup_generator.py:142-145, building
   '{bc_name.lower()}.{target.lower()}') and flags its own rule as uncertain.
   We do not need a rule at all: bc_builder ALREADY emits this exact URI for
   every field it creates, so the lookup reuses that value. That also guarantees
   the lookup points at the field the BC actually has, rather than at a
   separately-derived string that might not match.

2. BROWSE URI IS DERIVABLE FOR OUR OWN BCs.
   'urn:browse:bebrowse:com.extensions.training.training' is exactly what
   view_builder generates for BC 'Training' in module 'com.extensions.training'.
   Only a lookup pointing at a STANDARD QAD BC needs a user-supplied URI, and
   C4:132 documents how to find one: read `browseId` off the browser's Network
   tab while refreshing the target browse.

3. RESULT/SEARCH FIELDS are dotted '<browseEntity>.<fieldCode>'.

4. ADDITIONAL RESULT FIELDS ARE AUTO-POPULATE. The Target is the FORM field
   name, '{BC}_{field}AutoField{panel}' — precisely what form_builder generates.
   C4:238: "note that Location value was populated automatically."

STILL UNCONFIRMED — flagged, never fabricated:
  - searchFieldOperator wire value. The UI shows a display string ("greater or
    equal to", "equals"); the value that goes over the wire is unverified.
  - Whether 'uri' / 'modelId' / 'concurrencyHash' are required on create. All
    three are omitted here, as AUX does.
  - Whether QAD accepts a Lookup Definition against a BC that exists but is NOT
    yet deployed. The class-4 walkthrough builds one on an already-deployed BC.
    The owner's decision is to attempt it before deploy and swap the stage order
    if QAD rejects it.

Both remaining unknowns are settled by one live POST, which is why this stage
stays dry-run-locked until then.

NOT THIS MODULE: Lookup RELATION (class 3) is a different feature — the Lookup
checkbox on a BC field plus a Related Business Component (C3:1746-1748). It sets
hasLookup=True on the entity field and is configured in the BC, not here.
A Lookup DEFINITION leaves hasLookup alone, which is why bc_builder's
hasLookup=False is correct.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

from builders.identity import AppIdentity, resolve
from builders import naming


@dataclass
class BrowseTarget:
    """Where a lookup gets its values from."""
    uri: str
    label: str
    entity: str          # dotted-path prefix, e.g. "training"
    result_field: str    # e.g. "training.className"
    search_field: str    # e.g. "training.className"

    @classmethod
    def for_own_bc(cls, bc_pascal: str, field_code: str,
                   identity: Optional[AppIdentity] = None,
                   label: Optional[str] = None) -> "BrowseTarget":
        """Derive everything for a lookup pointing at a BC WE created.

        Nothing to type: the browse URI is what view_builder registered, and the
        dotted paths follow the entity's lowercase name. Verified against
        C4:199-202, where BC 'Training' in module 'com.extensions.training'
        yields 'urn:browse:bebrowse:com.extensions.training.training' with
        result/search field 'training.className'.
        """
        ident = resolve(identity)
        entity = bc_pascal.lower()
        dotted = f"{entity}.{field_code}"
        return cls(
            uri=ident.browse_uri(bc_pascal),
            label=label or naming.to_view_label(bc_pascal),
            entity=entity,
            result_field=dotted,
            search_field=dotted,
        )

    def problems(self) -> List[str]:
        """What is missing before this can be POSTed. Empty means usable."""
        out = []
        if not self.uri.strip():
            out.append(
                "Browse URI is required. For a standard QAD business component, read "
                "`browseId` off the browser's Network tab while refreshing that browse "
                "(the platform guide documents this method at class 4, page 9)."
            )
        elif not self.uri.startswith("urn:browse:"):
            out.append(
                f"Browse URI '{self.uri}' does not look like a browse urn. Expected the form "
                f"'urn:browse:bebrowse:<module.path>.<browseName>' or 'urn:browse:mfg:<code>'."
            )
        if not self.result_field.strip():
            out.append("Result Field is required - the column the lookup returns.")
        elif "." not in self.result_field:
            out.append(
                f"Result Field '{self.result_field}' must be a dotted browse path such as "
                f"'training.className', not a bare column name."
            )
        if not self.search_field.strip():
            out.append("Search Field is required - the column the lookup searches.")
        elif "." not in self.search_field:
            out.append(
                f"Search Field '{self.search_field}' must be a dotted browse path such as "
                f"'training.className', not a bare column name."
            )
        return out


@dataclass
class LookupSpec:
    """One field's lookup, as configured at the lookup stage."""
    field_code: str
    browse: BrowseTarget
    # Auto-populate: browse column -> form field name. The target must be a name
    # form_builder generated, which is why they are offered as a pick list
    # rather than typed.
    additional_results: List[Dict[str, str]] = dc_field(default_factory=list)
    search_conditions: List[Dict[str, Any]] = dc_field(default_factory=list)
    operator: str = "eq"


# The wire value is unverified; see the module docstring. Kept as a named
# constant so there is exactly one place to change once a live POST settles it.
DEFAULT_SEARCH_OPERATOR = "eq"
UNVERIFIED = [
    "searchFieldOperator: the UI displays a phrase ('equals', 'greater or equal to'); "
    "the wire value is unverified. Sending 'eq' as AUX does.",
    "uri / modelId / concurrencyHash: omitted on create, unconfirmed. Validate against a "
    "real server response before enabling live POSTs.",
]


def build_lookup_payload(
    lookup: LookupSpec,
    spec: Dict[str, Any],
    bc_field_uris: Dict[str, str],
    identity: Optional[AppIdentity] = None,
) -> Dict[str, Any]:
    """Build one Lookup Definition.

    `bc_field_uris` maps a field code to the fieldURI bc_builder generated for
    it. Passing them in rather than re-deriving is the whole point: it is the
    one way to be certain the lookup targets a field the BC actually has.
    """
    ident = resolve(identity)
    bc = spec["bc_pascal"]
    code = lookup.field_code
    safe = naming.sql_safe(code)

    field_uri = bc_field_uris.get(safe) or bc_field_uris.get(code)
    if not field_uri:
        raise ValueError(
            f"No field URI known for '{code}'. It must come from the BC payload built at "
            f"the field stage - known fields: {', '.join(sorted(bc_field_uris)) or '(none)'}."
        )

    problems = lookup.browse.problems()
    if problems:
        raise ValueError(
            f"Lookup on '{code}' is not ready to send:\n  - " + "\n  - ".join(problems)
        )

    source_field = next((f for f in spec.get("fields", []) if f["code"] == code), None)
    field_label = naming.to_display_label(code)
    if source_field and source_field.get("label"):
        field_label = source_field["label"]

    conditions = []
    for cond in lookup.search_conditions:
        name = str(cond.get("field_name", ""))
        # A real record uses the dotted browse path, never a bare column (C4:201).
        if "." not in name and lookup.browse.entity:
            name = f"{lookup.browse.entity}.{name}"
        conditions.append({
            "fieldName": name,
            "operator": str(cond.get("operator", "CONTAINS")).upper(),
            "fieldValue1": cond.get("value", ""),
            "fieldValue1Type": "LITERAL",
            "fieldValue2": None,
            "fieldValue2Type": None,
            "dataType": cond.get("data_type", "character"),
        })

    result_fields = [
        {"field": str(r["field"]), "target": str(r["target"])}
        for r in lookup.additional_results
    ]

    lookup_obj = {
        "appName": ident.app_name,
        "browseName": lookup.browse.label,
        "browseURI": lookup.browse.uri,
        "fieldLabel": field_label,
        "fieldSet": field_uri,
        "moduleURI": ident.module_uri,
        "namespace": ident.module,
        "reference": "",                       # confirmed empty, C4:195
        "resultField": lookup.browse.result_field,
        "searchField": lookup.browse.search_field,
        "searchFieldOperator": lookup.operator or DEFAULT_SEARCH_OPERATOR,
        "lookupQualifiers": [],                # confirmed empty for a static lookup
        "lookupResultFields": result_fields,
        "lookupSearchConditions": conditions,
        # Deliberately omitted, unconfirmed: uri, modelId, concurrencyHash.
    }

    return {
        "status": "built",
        "payload": {"lookups": [lookup_obj]},
        "unverified": list(UNVERIFIED),
        "summary": {
            "bc_pascal": bc,
            "field_code": code,
            "field_uri": field_uri,
            "browse_uri": lookup.browse.uri,
            "result_field": lookup.browse.result_field,
            "auto_populates": [r["target"] for r in result_fields],
        },
    }


def field_uris_from_bc_payload(bc_payload: Dict[str, Any]) -> Dict[str, str]:
    """Pull {fieldCode: fieldURI} out of the BC payload built at the field stage."""
    out: Dict[str, str] = {}
    for em in bc_payload.get("entityMetadatas") or []:
        for f in em.get("entityFields") or []:
            code = f.get("entityFieldCode")
            uri = f.get("fieldURI")
            if code and uri:
                out[code] = uri
    return out


def auto_populate_targets(placements: List[Dict[str, Any]], bc_pascal: str,
                          exclude_field: str = "") -> List[Dict[str, str]]:
    """Form fields a lookup could auto-populate, as a pick list.

    Names must match what form_builder emitted, so they are reconstructed the
    same way rather than typed: '{BC}_{safeField}AutoField{panel}'.
    """
    out = []
    for p in placements:
        code = str(p.get("fieldName", ""))
        if not code or code == exclude_field:
            continue
        safe = naming.sql_safe(code)
        out.append({
            "field_code": code,
            "label": naming.to_display_label(code),
            "target": f"{bc_pascal}_{safe}AutoField{p.get('panel', 1)}",
        })
    return out
