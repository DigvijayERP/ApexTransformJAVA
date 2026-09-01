"""
The catalog of legacy QAD browses, and a deterministic way to suggest one.

Two places in the app need a Browse URI the app cannot produce on its own:

  1. `stage_lookups` (core/engine.py): pointing a lookup at a standard QAD
     component needs that component's Browse URI, and until now the user had to
     go and find it by hand.
  2. The `{{BROWSE_URI:field}}` placeholders a generated event handler carries
     (builders/event_handler_builder.py): same problem, same manual hunt.

Data lives in config/browses.json, converted once from the legacy browse export
the owner supplied. `urn:browse:mfg:<code>` was confirmed live on eeadaptive
(2026-09-01) through lookup.browse_fields: cm007 returned 111 fields, ad057 36,
so805 37, pt001 13, while a made-up code returned nothing. So a URI built from
this file can be VERIFIED before it is used, which `verify()` below does.

ONE TRAP, kept deliberately: the export's `Lookup` column is NOT a filter.
cm007 is marked Lookup=No, yet QAD's own class-4 guide uses it as a lookup
browse. The flag is carried as `is_lookup` and used only as a small ranking
hint. Nothing here may ever exclude a row by it.

Ranking is deterministic on purpose - no model call, no network - so the same
field always offers the same candidates and a wrong suggestion can be traced to
this file rather than to a sampling temperature.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.logging_setup import get_logger

logger = get_logger("adaptive.browses")

BROWSES_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "browses.json"

# Words that carry no meaning in a field code. Two kinds, both dropped:
#   - key words: "customerCode" and "customerId" both want browses about
#     customers, not about codes.
#   - attribute words: "supplierName" wants browses about suppliers, not the
#     handful of browses that happen to be called "Code Name" or "Group Name".
#     The attribute says what is held about the thing, never which thing it is.
# Dropping them also makes a field code that is nothing but an attribute
# ("name", "date") return no candidates, the same way "code" already does.
NOISE_WORDS = frozenset({
    "code", "id", "number", "no", "num", "ref",
    "name", "description", "desc", "date", "status", "type",
    "amount", "qty", "text", "label", "value", "flag",
})

# Joining words. "BillToCustomer" is about bills and customers; the "to" would
# otherwise match every browse with "to" in its title and drown both.
STOP_WORDS = frozenset({"to", "of", "for", "and", "or", "the", "a", "an",
                        "from", "in", "on", "at", "by", "with", "per"})

# Table endings the legacy schema repeats everywhere. Stripping them lets the
# query word "customer" reach a table called customer_mstr. It does NOT teach
# the code that cm_mstr means customer - that would be a guess.
TABLE_SUFFIXES = frozenset({"mstr", "det", "ctrl", "hist", "ref", "wkfl", "wkly", "sum"})

# ── How a browse is scored ───────────────────────────────────────────────────
# For each word of the query (plurals folded, see _fold), times that word's
# weight:
#   + DESC_WORD  the word is a whole word of the description
#   + TERM_WORD  the word is a whole word of the term (underscores separate)
#   + TABLE_WORD the word is one of the browse's tables, or that table minus a
#                common suffix - but ONLY for a browse that already matched on
#                description or term, so a table name can refine an order and
#                can never be the sole reason a browse appears.
# Then + CODE_EXACT when the whole query is the browse code, which beats
# everything else.
# Weights are all 1 for a plain search. suggest_for_field gives the LAST word of
# a field code HEAD_WEIGHT instead, because that word is what the field is: a
# BillToCustomer field is a kind of customer, not a kind of bill. That only
# holds once the noise words are gone: in "supplierName" the last word is the
# attribute, not the thing, so "name" is dropped first and the weight lands on
# "supplier".
# Ties break on the shorter description first (a browse called "Customer" is a
# better answer for "customer" than "Customer Order Line Detail"), then on code.
#
# The Lookup flag deliberately scores NOTHING. It is carried into every result
# so the UI can show it, and that is all. Eight browses in this file describe
# themselves as exactly "Customer" (cm001, cm004, cm005, cm007, cm114, cm300,
# cm301, wh039) and three of them are flagged. Letting the flag move rows - as
# a point of score or as a tie-break - pushes cm007 down past them, and cm007 is
# the browse QAD's own class-4 guide uses for a customer lookup while being
# marked Lookup=No. The flag would have hidden the right answer, which is the
# same trap as filtering by it, so it stays out of the ordering.
CODE_EXACT = 100
DESC_WORD = 10
TERM_WORD = 6
TABLE_WORD = 2
HEAD_WEIGHT = 2

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_CAMEL_RE = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")


@dataclass(frozen=True)
class Browse:
    code: str
    description: str
    view: str
    tables: Tuple[str, ...]
    term: str
    is_lookup: bool
    is_power: bool
    is_drilldown: bool

    @property
    def uri(self) -> str:
        return f"{_prefix()}{self.code}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code, "description": self.description, "view": self.view,
            "tables": list(self.tables), "term": self.term,
            "is_lookup": self.is_lookup, "is_power": self.is_power,
            "is_drilldown": self.is_drilldown, "uri": self.uri,
        }


_cache: Optional[List[Browse]] = None
_by_code: Optional[Dict[str, Browse]] = None
_uri_prefix: str = "urn:browse:mfg:"


def _load() -> List[Browse]:
    global _cache, _by_code, _uri_prefix
    if _cache is None:
        doc = json.loads(BROWSES_PATH.read_text(encoding="utf-8"))
        _uri_prefix = doc.get("uri_prefix", "urn:browse:mfg:")
        _cache = [Browse(
            code=b["code"], description=b.get("description", ""),
            view=b.get("view", ""), tables=tuple(b.get("tables") or []),
            term=b.get("term", ""), is_lookup=bool(b.get("is_lookup")),
            is_power=bool(b.get("is_power")), is_drilldown=bool(b.get("is_drilldown")),
        ) for b in doc["browses"]]
        _by_code = {b.code.lower(): b for b in _cache}
    return _cache


def _prefix() -> str:
    _load()
    return _uri_prefix


def reload() -> None:
    """Drop the cache. Tests use this after pointing BROWSES_PATH elsewhere."""
    global _cache, _by_code
    _cache = None
    _by_code = None


# ── Word handling ────────────────────────────────────────────────────────────
def _fold(word: str) -> str:
    """Fold an obvious plural so "addresses" reaches the query word "address".

    This is not a stemmer and is not meant to be one: it strips a trailing "es"
    only when what is left already ends in a hissing letter, otherwise a plain
    trailing "s". "address" is left alone because it ends in a double s.
    """
    w = word.lower()
    if len(w) > 4 and w.endswith("es") and w[:-2].endswith(("s", "x", "z", "ch", "sh")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _words(text: str) -> List[str]:
    return [_fold(w) for w in _WORD_RE.findall(text or "")]


def _split_field_code(code: str) -> List[str]:
    """customerCode -> ["customer", "code"], BILL_TO_ADDR -> ["bill","to","addr"]."""
    out: List[str] = []
    for chunk in re.split(r"[^A-Za-z0-9]+", code or ""):
        out.extend(m.group(0).lower() for m in _CAMEL_RE.finditer(chunk))
    return out


def _table_words(b: Browse) -> Set[str]:
    out: Set[str] = set()
    for t in b.tables:
        name = t.lower()
        out.add(_fold(name))
        head, _, tail = name.rpartition("_")
        if head and tail in TABLE_SUFFIXES:
            out.add(_fold(head))
    return out


def _score(b: Browse, weighted: List[Tuple[str, int]], raw_query: str) -> int:
    desc = set(_words(b.description))
    term = set(_words(b.term))
    score = 0
    hits = 0
    for word, weight in weighted:
        if word in desc:
            score += DESC_WORD * weight
            hits += 1
        if word in term:
            score += TERM_WORD * weight
            hits += 1
    if hits:
        tables = _table_words(b)
        score += TABLE_WORD * sum(w for word, w in weighted if word in tables)
    if raw_query.strip().lower() == b.code.lower():
        score += CODE_EXACT
    return score


def _ranked(weighted: List[Tuple[str, int]], raw_query: str,
            limit: int) -> List[Browse]:
    if not weighted:
        return []
    scored = []
    for b in _load():
        s = _score(b, weighted, raw_query)
        if s > 0:
            scored.append((-s, len(b.description), b.code.lower(), b))
    scored.sort(key=lambda row: row[:3])
    return [row[3] for row in scored[:limit]]


# ── Public API ───────────────────────────────────────────────────────────────
def all_browses() -> List[Browse]:
    return list(_load())


def get(code: str) -> Browse:
    _load()
    b = (_by_code or {}).get((code or "").strip().lower())
    if b is None:
        raise KeyError(
            f"Unknown browse '{code}'. config/browses.json holds "
            f"{len(_load())} browses, none of them with that code."
        )
    return b


def by_uri(uri: str) -> Optional[Browse]:
    """Look a browse up from a full urn:browse:mfg:<code>, or from a bare code."""
    text = (uri or "").strip()
    if not text:
        return None
    prefix = _prefix()
    if text.lower().startswith(prefix.lower()):
        text = text[len(prefix):]
    elif ":" in text:
        # Some other URI scheme entirely - this catalog only knows mfg browses.
        return None
    try:
        return get(text)
    except KeyError:
        return None


def search(query: str, limit: int = 8) -> List[Browse]:
    """The best matching browses for a plain query, best first."""
    words = [w for w in _words(query) if w]
    return _ranked([(w, 1) for w in words], query, limit)


def suggest_for_field(field_code: str, field_label: str = "",
                      limit: int = 5) -> List[Browse]:
    """Candidate browses for one form field, best first.

    The field code is split into words (customerCode -> customer, code) and the
    noise and joining words are dropped. Noise covers both key words ("code",
    "id") and attribute words ("name", "date"), since neither says which thing
    the field is about. A field whose code is nothing but noise ("code",
    "name") tells us nothing to search on, so it gets an empty list rather than
    the catalog's first few rows.

    The last word left from the CODE carries the extra weight, since it is what
    the field is about; words that only came from the label follow it.
    """
    from_code: List[str] = []
    from_label: List[str] = []
    for source, out in ((field_code, from_code), (field_label, from_label)):
        for raw in _split_field_code(source):
            w = _fold(raw)
            # Both spellings are checked, because folding can bend a noise word
            # out of the list: "status" folds to "statu".
            if not w or raw in NOISE_WORDS or w in NOISE_WORDS \
                    or raw in STOP_WORDS or w in STOP_WORDS \
                    or w in from_code or w in from_label:
                continue
            out.append(w)
    if not from_code and not from_label:
        return []

    weighted = [(w, HEAD_WEIGHT if from_code and w == from_code[-1] else 1)
                for w in from_code + from_label]
    return _ranked(weighted, field_code, limit)


async def verify(uri: str) -> Tuple[bool, int, str]:
    """Ask QAD whether a browse URI resolves, and how many fields it offers.

    A read-only GET through the same endpoint the lookup stage already uses, so
    it costs nothing and changes nothing. Callers must not run it on a dry run.
    qad_client is imported here so that importing this catalog stays offline.
    """
    import qad_client

    text = (uri or "").strip()
    if not text:
        return False, 0, "No Browse URI was given."

    r = await qad_client.call("lookup.browse_fields", params={"browse_uri": text})
    if not r.ok:
        return False, 0, f"QAD could not be asked about this browse: {r.error}"

    fields = (r.data or {}).get("data") or []
    if not isinstance(fields, list) or not fields:
        return False, 0, f"QAD returned no fields for {text}, so it is not a real browse."
    logger.info("browse %s resolves with %d fields", text, len(fields))
    return True, len(fields), f"{text} resolves and offers {len(fields)} fields."
