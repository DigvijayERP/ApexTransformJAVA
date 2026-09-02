"""
Field-name and label transforms shared by every builder.

AUX duplicates SQL_RESERVED, sql_safe() and to_display_label() verbatim across
bc_builder.py, form_builder.py and view_builder.py. Three copies of a mapping
that MUST agree — if they ever diverge, a field is named one thing in the BC and
another on the form, and the form silently references a column that does not
exist. One copy here.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Field codes that collide with SQL reserved words, mapped to safe equivalents.
# QAD builds real database columns from these, so a collision is a deploy-time
# failure rather than a cosmetic problem.
SQL_RESERVED: Dict[str, str] = {
    "dir": "dirPath", "key": "keyCode", "value": "fieldValue", "name": "fieldName",
    "type": "fieldType", "date": "fieldDate", "time": "fieldTime", "order": "orderNum",
    "group": "groupCode", "user": "userCode", "table": "tableName", "index": "indexNum",
    "level": "levelNum", "status": "statusCode", "check": "checkFlag", "where": "whereClause",
    "select": "selectCode", "from": "fromCode", "set": "setValue", "by": "byCode",
    "on": "onCode", "in": "inCode", "is": "isCode", "as": "asCode", "or": "orCode",
    "and": "andCode", "domain": "domainFld", "rule": "ruleField", "domaincode": "domainCd",
}

ABBREVIATIONS: Dict[str, str] = {
    "po": "PO", "id": "ID", "cd": "Code", "no": "No",
    "url": "URL", "xml": "XML", "json": "JSON", "api": "API",
    "mgmt": "Management", "dept": "Department",
}

# Search operators QAD offers per data type on a browse.
BROWSE_SEARCH_OPERATORS: Dict[str, List[str]] = {
    "date": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "character": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS", "CONTAINS", "STARTS_WITH", "ENDS_WITH"],
    "datetime": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "int64": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "datetime-tz": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "integer": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "decimal": ["EQUALS", "GREATER_THAN", "GREATER_THAN_EQUALS", "IS_NOT_NULL", "IS_NULL", "LESS_THAN", "LESS_THAN_EQUALS", "NOT_EQUALS"],
    "logical": ["EQUALS", "IS_NOT_NULL", "IS_NULL", "NOT_EQUALS"],
}

DROPDOWN_TYPES = frozenset({"dropdown", "dropdown_integer", "dropdown_int64", "dropdown_logical"})

# Every data type the field designer may emit. Used to validate an edited spec
# before it reaches QAD, so a typo fails in the dialog rather than at the POST.
KNOWN_DATA_TYPES = frozenset({
    "character", "integer", "int64", "decimal", "date", "datetime", "datetime-tz",
    "logical", "percent", "url", *DROPDOWN_TYPES,
})

# Longest BC name the field prompts ask for, and the cap every rename here
# respects. QAD builds a table name and four urns from this string.
MAX_BC_NAME = 32


def name_candidates(base: str, limit: int = 20) -> List[str]:
    """The rename ladder for a BC name: base, base2, base3 ... base<limit>.

    Deterministic and offline - no model, no QAD call. When a candidate would
    run past MAX_BC_NAME the BASE is trimmed and the suffix is kept, never the
    other way round: dropping the '2' off a 32-character name hands back the
    name that was already taken.
    """
    base = (base or "").strip()
    if not base or limit < 1:
        return []
    out: List[str] = []
    for i in range(1, limit + 1):
        suffix = "" if i == 1 else str(i)
        out.append(base[:MAX_BC_NAME - len(suffix)] + suffix)
    return out


def sanitize_bc_name(asked: str) -> str:
    """Force a hand-typed BC name into something validate_spec will accept.

    Letters and digits only, PascalCase, no leading digit (QAD builds a table
    name and a urn from it, and both must start with a letter), capped at
    MAX_BC_NAME. Returns "" when nothing usable is left, which the caller
    reports rather than sends.
    """
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", asked or "") if p]
    pascal = "".join(p[0].upper() + p[1:] for p in parts)
    return re.sub(r"^[0-9]+", "", pascal)[:MAX_BC_NAME]


def sql_safe(code: str) -> str:
    return SQL_RESERVED.get(code.lower(), code)


def to_display_label(code: str) -> str:
    label = re.sub(r"([A-Z])", r" \1", code)
    label = re.sub(r"[_\-]+", " ", label).strip()
    out = []
    for w in label.split():
        out.append(ABBREVIATIONS.get(w.lower(), w[0].upper() + w[1:].lower()))
    return " ".join(out)


def to_view_label(pascal: str) -> str:
    cleaned = re.sub(r"Headers$", "", pascal, flags=re.IGNORECASE)
    cleaned = re.sub(r"Mgmt$", "", cleaned, flags=re.IGNORECASE).strip() or pascal
    label = re.sub(r"([A-Z])", r" \1", cleaned).strip()
    return (label[0].upper() + label[1:].lower()) if label else label


def display_format(data_type: str, max_length: Optional[int]) -> str:
    ml = max_length or 80
    return {
        "character": f"x({ml})", "url": f"x({max_length or 256})",
        "integer": "->,>>>,>>9", "int64": "->,>>>,>>9",
        "decimal": "->>,>>9.99<<<<", "percent": "->>,>>9.99<<<<%",
        "date": "99/99/9999", "datetime": "99/99/9999 HH:MM:SS",
        "datetime-tz": "99/99/9999 HH:MM:SS.SSS+HH:MM",
        "logical": "mfg-YES/mfg-NO", "dropdown": f"x({ml})",
        "dropdown_integer": "->,>>>,>>9", "dropdown_int64": "->,>>>,>>9",
        "dropdown_logical": "mfg-YES/mfg-NO",
    }.get(data_type, f"x({ml})")


def resolve_max_length(data_type: str, provided: Optional[int]) -> Optional[int]:
    if data_type in ("character", "dropdown"):
        return provided or 80
    if data_type == "url":
        return provided or 256
    return None


def resolve_sub_data_type(data_type: str) -> Optional[str]:
    with_sub = {"dropdown", "dropdown_integer", "dropdown_int64", "dropdown_logical", "percent", "url"}
    return data_type if data_type in with_sub else None


def resolve_default_value(data_type: str):
    if data_type == "logical":
        return None
    if data_type == "dropdown_logical":
        return "false"
    if data_type in ("integer", "int64", "decimal", "date", "datetime", "datetime-tz"):
        return None
    return ""


def resolve_min_max(data_type: str):
    null_types = {"integer", "int64", "decimal", "date", "datetime", "datetime-tz", "logical", "percent"}
    return None if data_type in null_types else ""


def validate_spec(spec: Dict[str, Any]) -> List[str]:
    """Check a field spec before anything is built from it.

    Returns a list of human-readable problems; empty means valid. This runs on
    the spec the USER approved (and may have edited by hand in the dialog), so
    it has to catch things the LLM would not have produced on its own.
    """
    problems: List[str] = []

    if not str(spec.get("bc_pascal") or "").strip():
        problems.append("The BC needs a name (bc_pascal).")
    elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", spec["bc_pascal"]):
        problems.append(
            f"BC name '{spec['bc_pascal']}' must be alphanumeric and start with a letter. "
            f"QAD builds urns and a table name from it."
        )

    fields = spec.get("fields") or []
    if not fields:
        problems.append("The BC needs at least one field.")

    seen: Dict[str, int] = {}
    pk_count = 0
    for i, f in enumerate(fields):
        code = str(f.get("code") or "").strip()
        where = f"field {i + 1}" + (f" ('{code}')" if code else "")
        if not code:
            problems.append(f"{where} has no code.")
            continue
        safe = sql_safe(code).lower()
        if safe in seen:
            problems.append(
                f"{where} collides with field {seen[safe] + 1} after SQL-safe renaming "
                f"(both become '{sql_safe(code)}')."
            )
        seen[safe] = i

        dt = f.get("dataType")
        if dt not in KNOWN_DATA_TYPES:
            problems.append(f"{where} has unknown data type '{dt}'.")

        if f.get("isPrimary") is True:
            pk_count += 1

        if dt in DROPDOWN_TYPES and f.get("needsLookup") is True:
            problems.append(
                f"{where} is marked as needing a lookup but has data type '{dt}'. A lookup "
                f"reads live records from another component and cannot be a dropdown, whose "
                f"values are a fixed list. Use 'character' with needsLookup."
            )

        if dt in DROPDOWN_TYPES:
            values = f.get("dropdownValues") or []
            if not values:
                problems.append(
                    f"{where} is a dropdown with no values. QAD rejects deploy when a "
                    f"dropdown field has no data list."
                )
            else:
                for j, v in enumerate(values):
                    if not isinstance(v, dict) or "code" not in v:
                        problems.append(f"{where} dropdownValues[{j}] needs a 'code' key.")

    if fields and pk_count == 0:
        problems.append("No field is marked as a primary key. QAD requires at least one.")

    return problems
