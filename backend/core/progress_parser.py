"""
Progress ABL (.p / .cls) schema parser for pasted-source grounding.

Adaptive's requirements stage accepts pasted ABL source as deterministic
grounding: instead of asking the LLM to reverse-engineer a field list from raw
Progress code, this module extracts it directly. Two run modes consume the
output: standalone BCs (one temp-table) and embedded child BCs under a parent,
where one file naturally defines SEVERAL temp-tables.

Ported from AUX: aux_web_version/backend/core/progress_parser.py.

PRESERVED FROM AUX UNCHANGED
  - Parser strategy: comment-stripped, case-insensitive regex extraction; a
    full ABL grammar is overkill for these constructs (aux:10-14).
  - Block comment stripping (aux:129-135).
  - Temp-table blocks end at the next structural boundary, not at the next
    period, because ABL statements span lines and embed periods in string
    literals (aux:144-152, 179-182).
  - ABL -> QAD type map, lossy-type warnings, QAD default display formats
    (aux:26-59), unknown types default to character with a warning
    (aux:321-327).
  - Per-field look-ahead window (up to the next FIELD/INDEX keyword) for
    FORMAT / LABEL extraction (aux:185-215).
  - PRIMARY INDEX membership marks fields required (aux:217-233).
  - PROCEDURE / FUNCTION / FOR EACH-FIND referenced-table extraction
    (aux:294-316).
  - .cls handling: PUBLIC PROPERTY declarations become one synthetic table,
    PUBLIC methods join the procedures list (aux:243-290).
  - Source case is preserved exactly on every extracted name.
  - Fail-soft rule: malformed ABL yields warnings, never exceptions.

CHANGED FROM AUX, AND WHY
  1. ALL temp-tables are returned. AUX's extractor already finds every table
     (aux:165-176) but its downstream renderer keeps only tables[0]
     (aux:379-380), so multi-table files lost every table but the first.
     Adaptive's embedded-BC mode needs the parent and every child, in source
     order.
  2. Public API is parse_abl(source) plus looks_like_abl(text). AUX's
     parse_progress_file took a Path or text and sniffed .cls from the
     filename (aux:67-92); Adaptive only ever receives pasted text, so .cls
     is detected from a CLASS header in the source itself.
  3. Field dicts say "data_type" (AUX said "type", aux:208-215) and now carry
     "initial", "extent" and "validate", which AUX ignored.
  4. LIKE support, which AUX had none of: a table-level LIKE is recorded as
     "like_table" and, when it names a temp-table defined earlier in the same
     source, the referenced fields are inherited (declared indexes are NOT
     inherited); a field-level FIELD x LIKE t.f is recorded as "like_source"
     and resolved against tables already parsed. Unresolvable references
     default to character with a warning, matching AUX's unknown-type policy.
  5. Zero temp-tables produces a warning entry instead of a silent empty list
     (AUX deferred that message to its renderer, aux:370-377).
  6. Result key is "warnings", not AUX's "parse_warnings" (aux:124).
  7. No lookup detection. AUX imports core.lookup_detector (aux:22, 105-106);
     Adaptive's lookup pipeline runs on the generated BC in
     builders/lookup_builder.py, not on the pasted source. Dropping the
     import keeps this module dependency-free: no network, no identity, no
     environment reads.
  8. Robustness fixes found while porting the tests: hyphenated field and
     table names (cust-num) now parse (AUX's \\w+ silently dropped them,
     aux:154-157); FORMAT/LABEL accept single-quoted strings (AUX only
     matched double quotes, aux:202-203); an index marked PRIMARY without
     the optional IS keyword is recognised (AUX required IS PRIMARY,
     aux:221); FIND NEXT/PREV no longer records NEXT/PREV as a table name
     (aux:296-299).
"""
from __future__ import annotations

import re
from typing import Any

__all__ = ["parse_abl", "looks_like_abl"]


# -- ABL type -> QAD type mapping (aux:26-48) ------------------------------
_ABL_TO_QAD_TYPE = {
    "CHARACTER":   "character",
    "CHAR":        "character",
    "INTEGER":     "integer",
    "INT":         "integer",
    "INT64":       "integer",
    "DECIMAL":     "decimal",
    "DEC":         "decimal",
    "LOGICAL":     "logical",
    "LOG":         "logical",
    "DATE":        "date",
    "DATETIME":    "datetime",
    "DATETIME-TZ": "datetime",
    "RECID":       "integer",
    "ROWID":       "character",
    "BLOB":        "character",
    "CLOB":        "character",
    "RAW":         "character",
    "MEMPTR":      "character",
}
# Mapped, but with a warning: the ABL semantics do not cleanly fit any QAD type.
_LOSSY_MAPPED = {"BLOB", "CLOB", "RAW", "MEMPTR"}

# QAD default display formats when the source does not specify FORMAT (aux:52-59).
_DEFAULT_FORMAT = {
    "character": "x(80)",
    "integer":   "->,>>>,>>9",
    "decimal":   "->,>>>,>>9.99",
    "logical":   "yes/no",
    "date":      "99/99/9999",
    "datetime":  "99/99/9999 HH:MM:SS.SSS",
}

_INDEX_KEYWORDS = {"IS", "PRIMARY", "UNIQUE", "ASCENDING", "DESCENDING", "ASC",
                   "DESC", "WORD", "AREA", "INDEX"}

# ABL identifier: starts with a word character, may contain hyphens, never
# ends on one. Wider than AUX's \w+ (change 8: cust-num style names).
_IDENT = r"[A-Za-z_]\w*(?:-+\w+)*"

# DEFINE statement modifiers. AUX handled only NEW [GLOBAL] SHARED (aux:140,
# 145); .cls members add PRIVATE/PROTECTED/PUBLIC/STATIC and parameters add
# INPUT/OUTPUT.
_DEF_MODS = (r"(?:(?:NEW|GLOBAL|SHARED|PRIVATE|PROTECTED|PUBLIC|STATIC|"
             r"SERIALIZABLE|NON-SERIALIZABLE|INPUT|OUTPUT|INPUT-OUTPUT)\s+)*")


# -- ABL detection ---------------------------------------------------------
# Conservative: every pattern here is a construct that does not occur in
# plain English. "FOR EACH customer" alone is prose; "FOR EACH customer
# NO-LOCK" is ABL.
_STRONG_ABL_SIGNALS = [
    re.compile(r"\bDEFINE\s+" + _DEF_MODS + r"TEMP-TABLE\s+" + _IDENT, re.IGNORECASE),
    re.compile(r"\bDEFINE\s+" + _DEF_MODS + r"(?:VARIABLE|VAR)\s+" + _IDENT
               + r"\s+AS\s+" + _IDENT, re.IGNORECASE),
    re.compile(r"\bDEFINE\s+" + _DEF_MODS + r"PARAMETER\s+" + _IDENT
               + r"\s+(?:AS|LIKE)\s", re.IGNORECASE),
    re.compile(r"\bDEFINE\s+" + _DEF_MODS + r"BUFFER\s+" + _IDENT
               + r"\s+FOR\s+" + _IDENT, re.IGNORECASE),
    re.compile(r"\bNO-UNDO\b", re.IGNORECASE),
    re.compile(r"\bFOR\s+EACH\s+" + _IDENT
               + r"\s+(?:NO-LOCK|EXCLUSIVE-LOCK|SHARE-LOCK)\b", re.IGNORECASE),
    re.compile(r"\bEND\s+(?:PROCEDURE|FUNCTION|METHOD|CLASS)\s*\.", re.IGNORECASE),
    re.compile(r"\bMETHOD\s+(?:PUBLIC|PROTECTED|PRIVATE)\s", re.IGNORECASE),
    re.compile(r"&(?:SCOPED|GLOBAL)-DEFINE\s", re.IGNORECASE),
    re.compile(r"\{&" + _IDENT + r"\}"),
    # Class header: dotted type name ending in a colon before any period.
    re.compile(r"\bCLASS\s+\w+(?:\.\w+)+[^.:]*:", re.IGNORECASE),
]

# Weaker constructs that could conceivably appear in technical prose; two
# distinct hits are required before they count as ABL.
_MEDIUM_ABL_SIGNALS = [
    re.compile(r"\bPROCEDURE\s+" + _IDENT + r"\s*:", re.IGNORECASE),
    re.compile(r"\bFUNCTION\s+" + _IDENT + r"\s+RETURNS\s+" + _IDENT, re.IGNORECASE),
    re.compile(r"\bFIND\s+(?:FIRST|LAST|NEXT|PREV)\s+" + _IDENT, re.IGNORECASE),
    re.compile(r"\bASSIGN\s+" + _IDENT + r"\s*=", re.IGNORECASE),
]


def looks_like_abl(text: str) -> bool:
    """True when `text` is Progress ABL source rather than plain English.

    Conservative by design: one unambiguous ABL construct (DEFINE TEMP-TABLE,
    NO-UNDO, FOR EACH ... NO-LOCK, ...) is enough; constructs that could
    plausibly appear in prose (PROCEDURE x:, FUNCTION x RETURNS y) need two
    distinct hits. Plain English must never return True.
    """
    if not text or not text.strip():
        return False
    stripped = _strip_comments(text)
    if any(p.search(stripped) for p in _STRONG_ABL_SIGNALS):
        return True
    return sum(1 for p in _MEDIUM_ABL_SIGNALS if p.search(stripped)) >= 2


# -- Public API ------------------------------------------------------------

def parse_abl(source: str) -> dict[str, Any]:
    """Parse pasted Progress ABL source into a structured dict.

    Returns:
        {
          "source_type": "p" | "cls",
          "tables": [                       # ALL temp-tables, source order
            {
              "name":        str,           # source case preserved
              "fields": [
                {
                  "name":        str,
                  "data_type":   str,       # ABL type, upper-cased
                  "qad_type":    str,       # mapped QAD type
                  "format":      str,
                  "label":       str,
                  "initial":     str | None,
                  "extent":      int | None,
                  "required":    bool,      # True for PRIMARY-index members
                  "like_source": str | None,  # FIELD x LIKE <this>
                  "validate":    str | None,  # raw VALIDATE(...) expression
                },
              ],
              "primary_key": [field names],
              "indexes": [
                {"name": str, "primary": bool, "unique": bool,
                 "word": bool, "fields": [field names]},
              ],
              "like_table": str | None,     # DEFINE TEMP-TABLE x LIKE <this>
            },
          ],
          "procedures": [...], "functions": [...],
          "source_tables_referenced": [...],
          "warnings": [...],
        }

    Never raises on malformed ABL; problems become entries in "warnings".
    """
    text = source or ""
    stripped = _strip_comments(text)
    warnings: list[str] = []

    tables = _extract_temp_tables(stripped, warnings)
    procedures = _extract_procedures(stripped)
    functions = _extract_functions(stripped)
    referenced = _extract_referenced_tables(stripped)

    source_type = "p"
    cls_info = _extract_class_shape(stripped, warnings)
    if cls_info:
        source_type = "cls"
        tables.append(cls_info["table"])
        procedures.extend(cls_info["methods"])

    if not tables:
        warnings.append(
            "No DEFINE TEMP-TABLE block was found in the source. "
            "Describe the desired component in plain English instead."
        )

    return {
        "source_type":              source_type,
        "tables":                   tables,
        "procedures":               sorted(set(procedures)),
        "functions":                sorted(set(functions)),
        "source_tables_referenced": sorted(set(referenced)),
        "warnings":                 warnings,
    }


# -- Comment stripping (aux:129-135) ---------------------------------------
_BLOCK_COMMENT_RE = re.compile(r"/\*[\s\S]*?\*/")


def _strip_comments(src: str) -> str:
    """Progress comments are block-only `/* ... */`. Strip them so keywords
    inside comments never reach the extractors."""
    return _BLOCK_COMMENT_RE.sub(" ", src)


# -- TEMP-TABLE extraction (aux:139-239) -----------------------------------
_TEMP_TABLE_HDR_RE = re.compile(
    r"\bDEFINE\s+" + _DEF_MODS + r"TEMP-TABLE\s+(" + _IDENT + r")",
    re.IGNORECASE,
)

_BOUNDARY_RE = re.compile(
    r"\bDEFINE\s+" + _DEF_MODS +
    r"(?:TEMP-TABLE|VARIABLE|PARAMETER|BUFFER|WORKFILE|DATASET|QUERY|STREAM)\b"
    r"|\bPROCEDURE\s+" + _IDENT + r"\s*:"
    r"|\bFUNCTION\s+" + _IDENT + r"\s+RETURNS\b"
    r"|\bCLASS\s+[\w.]+"
    r"|\bMETHOD\s+(?:PUBLIC|PROTECTED|PRIVATE)\b",
    re.IGNORECASE,
)

# A type or LIKE reference: word chunks joined by single dots or hyphens, so
# the statement-ending period is never swallowed into the name.
_REF = r"\w+(?:[.-]\w+)*"

_FIELD_RE = re.compile(
    r"\bFIELD\s+(" + _IDENT + r")\s+(AS|LIKE)\s+(" + _REF + r")",
    re.IGNORECASE,
)

_INDEX_RE = re.compile(
    r"\bINDEX\s+(" + _IDENT + r")((?:(?!\bINDEX\b|\bFIELD\b).)*?)"
    r"(?=\bINDEX\b|\bFIELD\b|\Z)",
    re.IGNORECASE | re.DOTALL,
)

_TABLE_LIKE_RE = re.compile(r"\bLIKE\s+(" + _REF + r")", re.IGNORECASE)

_FORMAT_RE = re.compile(r"""\bFORMAT\s+(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)
_LABEL_RE = re.compile(r"""\bLABEL\s+(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)
_INITIAL_RE = re.compile(
    r"""\bINITIAL\s+(?:"([^"]*)"|'([^']*)'|(\[[^\]]*\])|(-?""" + _REF + r"))",
    re.IGNORECASE,
)
_EXTENT_RE = re.compile(r"\bEXTENT\s+(\d+)", re.IGNORECASE)
_VALIDATE_RE = re.compile(r"\bVALIDATE\s*\(", re.IGNORECASE)


def _extract_temp_tables(src: str, warnings: list[str]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for hdr in _TEMP_TABLE_HDR_RE.finditer(src):
        name = hdr.group(1)
        block_end = _find_block_end(src, hdr.end())
        body = src[hdr.end():block_end]
        # AUX kept every parsed table here too (aux:165-176); the single-table
        # loss happened downstream (aux:379-380) and is deliberately not ported.
        tables.append(_parse_temp_table_body(name, body, warnings, tables))
    return tables


def _find_block_end(src: str, start: int) -> int:
    """First structural boundary after `start`, or end-of-source (aux:179-182)."""
    match = _BOUNDARY_RE.search(src, start)
    return match.start() if match else len(src)


def _parse_temp_table_body(name: str, body: str, warnings: list[str],
                           prior_tables: list[dict[str, Any]]) -> dict[str, Any]:
    field_positions = [(m.start(), m.end(), m.group(1), m.group(2).upper(), m.group(3))
                       for m in _FIELD_RE.finditer(body)]
    idx_positions = [m.start() for m in re.finditer(r"\bINDEX\b", body, re.IGNORECASE)]

    # Table-level LIKE lives before the first FIELD/INDEX keyword; anything
    # after that region is a field-level LIKE and must not be mistaken for it.
    prologue_end = min([p[0] for p in field_positions] + idx_positions + [len(body)])
    like_m = _TABLE_LIKE_RE.search(body, 0, prologue_end)
    like_table = like_m.group(1) if like_m else None

    fields: list[dict[str, Any]] = []
    if like_table:
        parent = _find_table(prior_tables, like_table)
        if parent:
            # Copies start not-required: the parent's flag came from ITS
            # primary index, and declared indexes are not inherited.
            fields.extend({**f, "required": False} for f in parent["fields"])
        else:
            warnings.append(
                f"table {name}: LIKE {like_table} could not be expanded, "
                f"{like_table} is not defined earlier in this source. Only "
                f"fields declared inline are listed."
            )

    # Per-field look-ahead window up to the next FIELD/INDEX (aux:185-215).
    all_stops = sorted([p[0] for p in field_positions[1:]] + idx_positions + [len(body)])
    for start, end, f_name, f_kind, f_ref in field_positions:
        next_stop = next((s for s in all_stops if s > end), len(body))
        window = body[end:next_stop]
        fields.append(_build_field(name, f_name, f_kind, f_ref, window,
                                   warnings, prior_tables, fields))

    indexes = _parse_indexes(body, fields)
    primary_pk = [fn for idx in indexes if idx["primary"] for fn in idx["fields"]]
    for f in fields:
        if f["name"] in primary_pk:
            f["required"] = True

    return {
        "name":        name,
        "fields":      fields,
        "primary_key": primary_pk,
        "indexes":     indexes,
        "like_table":  like_table,
    }


def _build_field(table: str, f_name: str, f_kind: str, f_ref: str, window: str,
                 warnings: list[str], prior_tables: list[dict[str, Any]],
                 current_fields: list[dict[str, Any]]) -> dict[str, Any]:
    like_source: str | None = None
    inherited_format: str | None = None
    inherited_label: str | None = None

    if f_kind == "LIKE":
        like_source = f_ref
        resolved = _resolve_like_field(f_ref, prior_tables, current_fields)
        if resolved:
            data_type = resolved["data_type"]
            qad_type = resolved["qad_type"]
            inherited_format = resolved["format"]
            inherited_label = resolved["label"]
        else:
            data_type, qad_type = "CHARACTER", "character"
            warnings.append(
                f"table {table}.{f_name}: LIKE {f_ref} could not be resolved "
                f"in this source, type defaulted to character"
            )
    else:
        data_type = f_ref.upper()
        qad_type, warn = _map_type(f_ref)
        if warn:
            warnings.append(f"table {table}.{f_name}: {warn}")

    fmt_m = _FORMAT_RE.search(window)
    label_m = _LABEL_RE.search(window)
    init_m = _INITIAL_RE.search(window)
    extent_m = _EXTENT_RE.search(window)

    fmt = (_first_group(fmt_m) if fmt_m else None) or inherited_format \
        or _DEFAULT_FORMAT.get(qad_type, "x(80)")
    label = (_first_group(label_m) if label_m else None) or inherited_label \
        or _titlecase(f_name)

    return {
        "name":        f_name,
        "data_type":   data_type,
        "qad_type":    qad_type,
        "format":      fmt,
        "label":       label,
        "initial":     _first_group(init_m) if init_m else None,
        "extent":      int(extent_m.group(1)) if extent_m else None,
        "required":    False,   # patched from PRIMARY-index membership
        "like_source": like_source,
        "validate":    _extract_validate(window, table, f_name, warnings),
    }


def _extract_validate(window: str, table: str, f_name: str,
                      warnings: list[str]) -> str | None:
    m = _VALIDATE_RE.search(window)
    if not m:
        return None
    expr = _balanced_paren(window, m.end() - 1)
    if expr is None:
        warnings.append(f"table {table}.{f_name}: VALIDATE expression is "
                        f"unbalanced and was skipped")
        return None
    return expr.strip()


def _balanced_paren(text: str, open_idx: int) -> str | None:
    """Content of the parenthesised group starting at `open_idx`, honouring
    nested parens and quoted strings; None when unbalanced."""
    depth = 0
    in_str: str | None = None
    for i in range(open_idx, len(text)):
        ch = text[i]
        if in_str:
            if ch == in_str:
                in_str = None
        elif ch in "\"'":
            in_str = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i]
    return None


def _parse_indexes(body: str, fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """All INDEX blocks: name, PRIMARY/UNIQUE/WORD flags, member fields in
    declaration order with the field's source case (aux:217-233, widened per
    change 8: IS is optional before PRIMARY)."""
    indexes: list[dict[str, Any]] = []
    for m in _INDEX_RE.finditer(body):
        idx_body = m.group(2)
        member: list[str] = []
        for w in re.findall(r"\b[\w-]+\b", idx_body):
            if w.upper() in _INDEX_KEYWORDS:
                continue
            for f in fields:
                if f["name"].upper() == w.upper() and f["name"] not in member:
                    member.append(f["name"])
        indexes.append({
            "name":    m.group(1),
            "primary": bool(re.search(r"\bPRIMARY\b", idx_body, re.IGNORECASE)),
            "unique":  bool(re.search(r"\bUNIQUE\b", idx_body, re.IGNORECASE)),
            "word":    bool(re.search(r"\bWORD\b", idx_body, re.IGNORECASE)),
            "fields":  member,
        })
    return indexes


def _find_table(tables: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    target = name.split(".")[-1].upper()
    for t in tables:
        if t["name"].upper() == target:
            return t
    return None


def _resolve_like_field(ref: str, prior_tables: list[dict[str, Any]],
                        current_fields: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Resolve `FIELD x LIKE ref` against tables already parsed from this
    source. Dotted refs (ttParent.Amount) name table and field; bare refs may
    name an earlier field of the same table."""
    parts = ref.split(".")
    if len(parts) >= 2:
        table = _find_table(prior_tables, ".".join(parts[:-1]))
        if not table:
            return None
        candidates = table["fields"]
    else:
        candidates = current_fields
    target = parts[-1].upper()
    for f in candidates:
        if f["name"].upper() == target:
            return f
    return None


# -- CLASS (.cls) extraction (aux:243-290) ---------------------------------
# AUX gated this on the filename (aux:92, 111-115); pasted text has none, so
# the trigger is a class header in the source: a name followed by a colon
# before any statement-ending period, which a FIELD named "class" cannot fake.
_CLASS_RE = re.compile(
    r"\bCLASS\s+([\w.]+)(?:\s+INHERITS\s+[\w.]+)?[^.:]*:",
    re.IGNORECASE,
)
_PROPERTY_RE = re.compile(
    r"\bDEFINE\s+PUBLIC\s+PROPERTY\s+(" + _IDENT + r")\s+AS\s+([\w-]+)",
    re.IGNORECASE,
)
_METHOD_RE = re.compile(
    r"\bMETHOD\s+PUBLIC\s+(?:VOID|[\w-]+)\s+(" + _IDENT + r")\s*\(",
    re.IGNORECASE,
)


def _extract_class_shape(src: str, warnings: list[str]) -> dict[str, Any] | None:
    """A .cls source becomes one synthetic 'table' whose fields are its
    PUBLIC PROPERTY declarations; PUBLIC methods are collected alongside
    procedures. PROTECTED/PRIVATE members are intentionally skipped."""
    cls_m = _CLASS_RE.search(src)
    if not cls_m:
        return None
    class_name = cls_m.group(1).split(".")[-1]

    fields = []
    for m in _PROPERTY_RE.finditer(src):
        p_name, p_type = m.group(1), m.group(2)
        qad_type, warn = _map_type(p_type)
        if warn:
            warnings.append(f"class {class_name}.{p_name}: {warn}")
        fields.append({
            "name":        p_name,
            "data_type":   p_type.upper(),
            "qad_type":    qad_type,
            "format":      _DEFAULT_FORMAT.get(qad_type, "x(80)"),
            "label":       _titlecase(p_name),
            "initial":     None,
            "extent":      None,
            "required":    False,
            "like_source": None,
            "validate":    None,
        })

    return {
        "table": {
            "name":        class_name,
            "fields":      fields,
            "primary_key": [],
            "indexes":     [],
            "like_table":  None,
        },
        "methods": [m.group(1) for m in _METHOD_RE.finditer(src)],
    }


# -- PROCEDURE / FUNCTION / referenced tables (aux:294-316) ----------------
_PROC_RE = re.compile(r"\bPROCEDURE\s+(" + _IDENT + r")\s*:", re.IGNORECASE)
_FUNC_RE = re.compile(r"\bFUNCTION\s+(" + _IDENT + r")\s+RETURNS\b", re.IGNORECASE)
_REF_TABLE_RE = re.compile(
    r"\bFOR\s+EACH\s+(" + _IDENT + r")"
    r"|\bFIND\s+(?:FIRST\s+|LAST\s+|NEXT\s+|PREV\s+)?(" + _IDENT + r")",
    re.IGNORECASE,
)


def _extract_procedures(src: str) -> list[str]:
    return [m.group(1) for m in _PROC_RE.finditer(src)]


def _extract_functions(src: str) -> list[str]:
    return [m.group(1) for m in _FUNC_RE.finditer(src)]


def _extract_referenced_tables(src: str) -> list[str]:
    out: list[str] = []
    for m in _REF_TABLE_RE.finditer(src):
        name = m.group(1) or m.group(2)
        if name:
            out.append(name)
    return out


# -- Helpers ---------------------------------------------------------------

def _map_type(abl_type: str) -> tuple[str, str | None]:
    key = abl_type.upper()
    if key in _ABL_TO_QAD_TYPE:
        warn = (f"ABL type {key} has no exact QAD equivalent, mapped to "
                f"'{_ABL_TO_QAD_TYPE[key]}'") if key in _LOSSY_MAPPED else None
        return _ABL_TO_QAD_TYPE[key], warn
    return "character", f"Unknown ABL type '{abl_type}', defaulted to 'character'"


def _titlecase(identifier: str) -> str:
    """`invoiceNumber` / `invoice-number` / `invoice_number` -> `Invoice Number`."""
    s = re.sub(r"[-_]", " ", identifier)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    return " ".join(w.capitalize() for w in s.split())


def _first_group(m: re.Match | None) -> str | None:
    if not m:
        return None
    return next((g for g in m.groups() if g is not None), None)
