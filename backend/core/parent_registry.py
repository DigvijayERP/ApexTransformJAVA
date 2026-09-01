"""
The parent-entity registry for Case 2 (embedded BC).

Replaces AUX's qad_entity_registry.py, which had three defects this module is
designed against:

  1. Its five builtin rows were hand-typed from the OLD environment and never
     validated even there. A live probe of eeadaptive (2026-08-12) found two of
     them wrong: InventoryMasters is doNotExtend here, and WorkOrderMasters has
     THREE primary keys.
  2. It modelled the parent link as a single `fk_field`, but the captured
     relation save maps EVERY parent PK (captures/2026-08-12_embedded_
     EmbeddedExmpl2.md), so a multi-key parent was structurally unmappable.
  3. The LLM picked the parent and the user learned about a wrong pick only
     from a failed write. Here the registry serves a menu the USER confirms at
     the requirements gate.

Data lives in config/parents.json. `verify_live()` re-reads a parent from QAD
at gate time; when file and live disagree, the live answer wins and the
difference is REPORTED, never silently patched.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logging_setup import get_logger

logger = get_logger("adaptive.parents")

PARENTS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "parents.json"


@dataclass(frozen=True)
class Parent:
    key: str
    label: str
    uri: str
    entity_code: str
    domain_field: str
    # ORDERED and COMPLETE: the relation must map every one of these.
    pk_fields: List[Dict[str, str]]
    offerable: bool
    description: str = ""
    not_offerable_because: str = ""
    # The parent's maintain-view URI, needed to attach a screen event handler.
    # Empty until confirmed live for that parent; the screen validation stage
    # skips itself when it is empty rather than guessing a URI.
    view_uri: str = ""

    @property
    def non_domain_pks(self) -> List[Dict[str, str]]:
        return [f for f in self.pk_fields if f["code"] != self.domain_field]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key, "label": self.label, "uri": self.uri,
            "entity_code": self.entity_code, "domain_field": self.domain_field,
            "pk_fields": self.pk_fields, "offerable": self.offerable,
            "description": self.description,
            "not_offerable_because": self.not_offerable_because,
            "view_uri": self.view_uri,
        }


_cache: Optional[List[Parent]] = None


def _load() -> List[Parent]:
    global _cache
    if _cache is None:
        doc = json.loads(PARENTS_PATH.read_text(encoding="utf-8"))
        _cache = [Parent(
            key=p["key"], label=p.get("label", p["key"]), uri=p["uri"],
            entity_code=p["entity_code"], domain_field=p["domain_field"],
            pk_fields=p["pk_fields"], offerable=bool(p.get("offerable")),
            description=p.get("description", ""),
            not_offerable_because=p.get("not_offerable_because", ""),
            view_uri=p.get("view_uri", ""),
        ) for p in doc["parents"]]
    return _cache


def reload() -> None:
    """Drop the cache. Tests use this after pointing PARENTS_PATH elsewhere."""
    global _cache
    _cache = None


def all_parents() -> List[Parent]:
    return list(_load())


def offerable() -> List[Parent]:
    return [p for p in _load() if p.offerable]


def get(key: str) -> Parent:
    for p in _load():
        if p.key == key:
            return p
    known = ", ".join(p.key for p in _load())
    raise KeyError(f"Unknown parent entity '{key}'. Known: {known}")


def entity_menu_for_prompt() -> str:
    """The parent menu injected into EMBEDDED_REQUIREMENTS_GATHERING.

    Only offerable parents appear: showing the model a parent QAD will reject
    (InventoryMasters) invites a choice that can only fail at the write.
    """
    lines = []
    for p in offerable():
        pks = ", ".join(f["code"] for f in p.pk_fields)
        lines.append(f"- {p.key}: {p.description or p.label} (primary keys: {pks})")
    return "\n".join(lines)


async def verify_live(key: str) -> Dict[str, Any]:
    """Re-read one parent from QAD and diff it against the file entry.

    Returns {parent, live_ok, mismatches, do_not_extend}. A transport failure
    reports live_ok False rather than raising: the gate can still render from
    the file entry, it just says so.
    """
    import qad_client

    p = get(key)
    out: Dict[str, Any] = {"parent": p.to_dict(), "live_ok": False,
                           "mismatches": [], "do_not_extend": False}
    r = await qad_client.call("bc.metadata.read", params={"entity_uri": p.uri})
    if not r.ok:
        out["error"] = r.error
        return out

    body = r.data.get("data") if isinstance((r.data or {}).get("data"), dict) else r.data
    ems = (body or {}).get("entityMetadatas") or []
    if not ems:
        out["error"] = "QAD returned no entityMetadatas for this parent."
        return out

    em = ems[0]
    out["live_ok"] = True
    out["do_not_extend"] = bool(em.get("doNotExtend"))
    if out["do_not_extend"]:
        out["mismatches"].append(
            f"QAD says '{key}' is doNotExtend - it cannot be a parent.")

    live_pks = sorted(
        (f for f in em.get("entityFields") or [] if f.get("primaryKey")),
        key=lambda f: f["primaryKey"])
    live_codes = [f["entityFieldCode"] for f in live_pks]
    file_codes = [f["code"] for f in p.pk_fields]
    if live_codes != file_codes:
        out["mismatches"].append(
            f"Primary keys differ: config/parents.json says {file_codes}, "
            f"QAD says {live_codes}. The live list is authoritative.")
        out["live_pk_fields"] = [
            {"code": f["entityFieldCode"], "dataType": f.get("dataType", "character")}
            for f in live_pks]
    return out
