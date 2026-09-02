"""
Read-only questions about a browse, answered before a run needs the answer.

WHY THIS ROUTE EXISTS

At the lookup gate the user has to name the field on a browse that supplies the
value. Until now that was a free-text box, and there is no way to know what to
type: QAD's own names differ per browse and have no shape you can derive.
Confirmed live on 2026-09-01, bebrowse digsmoketest offers `digSmokeTest.testCode`,
cm001 offers `debtor.DebtorCode`, pp125 offers a bare `pt_part`, and cm007 offers
`changeStatus`. A typo was only caught when the stage ran, and only on a live run.

`/api/browses/fields` hands the UI the same list QAD's own picker uses, so the
user chooses instead of guessing.

READS ARE FREE, AND THAT IS DELIBERATE

This is a GET against QAD and it changes nothing, so the UI may call it on a
rehearsal run too. That is a departure from `stage_lookups`, which still does not
resolve on a dry run, and it is intentional: a dry run is meant to be a full
rehearsal of the decisions, and a field the user cannot see is a decision made
blind. The UI copy says so.

`/api/browses/search` never leaves the process: it reads config/browses.json
through core.browse_catalog. No auth, because it exposes nothing that is not
already in the repository.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

import qad_client
from core import browse_catalog
from core.auth import require_auth
from core.logging_setup import get_logger

logger = get_logger("adaptive.api.browses")

router = APIRouter(prefix="/api/browses", tags=["browses"])

# Every browse URI QAD accepts starts with this, both the mfg ones
# (urn:browse:mfg:cm007) and the bebrowse ones
# (urn:browse:bebrowse:com.yash.digwish.digsmoketest).
URI_PREFIX = "urn:browse:"

# A browse code that does not exist is NOT an error to QAD: it answers 200 with
# no rows. Proven with urn:browse:mfg:zz999 on 2026-09-01. So zero rows has to
# be reported as its own outcome, otherwise the UI shows an empty picker and
# says nothing about why.
NO_FIELDS_NOTE = "QAD does not know this browse, or it has no fields. Check the URI."

SEARCH_LIMIT_MAX = 25

# The uri reaches us straight from the query string, so it must be cleaned
# before it goes anywhere near a log line. Two reasons, both real:
#   - a newline in the value lets a caller write a whole extra line into
#     backend/logs/app.log and forge a record that reads like ours.
#   - a non-ASCII character kills the stdout handler on a cp1252 console, which
#     is the exact trap core/logging_setup.py warns about at the top.
LOG_URI_MAX = 200


def _log_safe(text: str) -> str:
    """One ASCII line, short enough to read, safe to hand to the logger."""
    flat = text.replace("\r", " ").replace("\n", " ")
    return flat.encode("ascii", "backslashreplace").decode("ascii")[:LOG_URI_MAX]


def _mapped(rows: List[Any]) -> List[Dict[str, str]]:
    """QAD's rows, renamed to the three keys the UI needs and nothing else.

    `field` is carried through VERBATIM. It is the string that ends up in the
    lookup payload, and reshaping it is exactly the bug this route exists to
    stop: prefixing turned debtor.DebtorCode into cm001.debtor.DebtorCode and
    QAD rejected it.
    """
    out: List[Dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("field")
        if not name:
            continue
        out.append({
            "field": str(name),
            "label": str(row.get("fieldLabel") or ""),
            "data_type": str(row.get("fieldDataType") or ""),
        })
    return out


@router.get("/fields")
async def browse_fields(uri: str, _=Depends(require_auth)) -> Dict[str, Any]:
    """The fields QAD lists for one browse. Reads QAD, writes nothing.

    Depends on require_auth because it reaches QAD with our credentials, which
    is the same reason the mutating routes do.
    """
    text = (uri or "").strip()
    if not text.startswith(URI_PREFIX):
        raise HTTPException(
            status_code=400,
            detail=f"A Browse URI has to start with '{URI_PREFIX}'. Got '{text}'.",
        )

    # The transport RAISES on the most common failures rather than answering
    # with ok=False: no credentials in backend/.env, a rejected login, an
    # endpoint id the registry cannot resolve. Those messages are the only
    # actionable thing the user gets, and letting them escape turns them into a
    # bare 500 "Internal Server Error". Same 502 as the ok=False branch below.
    try:
        r = await qad_client.call("lookup.browse_fields", params={"browse_uri": text})
    except Exception as exc:
        logger.warning("browse %s could not be read: %s",
                       _log_safe(text), _log_safe(str(exc)))
        raise HTTPException(
            status_code=502,
            detail=str(exc) or f"QAD refused to list the fields on {text}.",
        ) from exc

    if not r.ok:
        # QAD's own words, not a generic message. The user can act on
        # "permissions failure" or "could not reach QAD"; they cannot act on
        # "upstream error".
        raise HTTPException(
            status_code=502,
            detail=r.error or f"QAD refused to list the fields on {text}.",
        )

    rows = (r.data or {}).get("data") or []
    fields = _mapped(rows) if isinstance(rows, list) else []
    logger.info("browse %s lists %d field(s)", _log_safe(text), len(fields))

    answer: Dict[str, Any] = {"uri": text, "fields": fields}
    if not fields:
        answer["note"] = NO_FIELDS_NOTE
    return answer


@router.get("/search")
async def search_browses(q: str = "", limit: int = 8) -> Dict[str, Any]:
    """Browses whose name matches a plain query, best first.

    Local only. The per-field suggestions the lookup gate already shows come
    from the same catalog and the same ranking; this lets the user look past
    them when the field code did not describe the thing well enough.

    An out-of-range limit is CLAMPED rather than rejected. This feeds a picker
    that types as the user types, and a 422 in the middle of a search box is a
    dead end for someone who did not choose the number in the first place.
    """
    capped = max(1, min(limit, SEARCH_LIMIT_MAX))
    return {"browses": [b.to_dict() for b in browse_catalog.search(q, limit=capped)]}
