"""
Offline tests for routers/browses.py. No network, no credentials, no pytest.

Run from the backend directory:

    python routers/browses_test.py

qad_client.call is REPLACED for the whole file, so nothing here can reach QAD
even by accident, and ADAPTIVE_OFFLINE is set as a second belt: a call that
escaped the stub and tried to change QAD would raise instead of sending.

The auth section drives core.auth.configured_token directly, the same way
api_test.py does, so the result does not depend on whether the developer running
this happens to have ADAPTIVE_API_TOKEN set.

The live shapes quoted below (dotted names on cm001, a bare pt_part on pp125, a
made-up code answering 200 with no rows) were collected by hand on 2026-09-01
and recorded in PROGRESS.md. They are not re-fetched here.
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

# Runnable both as `python routers/browses_test.py` and as a module.
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Belt and braces before anything imports qad_client.
os.environ.setdefault("ADAPTIVE_OFFLINE", "1")

# Point the store at a throwaway database BEFORE the app imports it, so running
# this test cannot touch the real runs.db.
from core import store as _store  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="adaptive_browses_")) / "browses.db"
_store.DB_PATH = _TMP

from fastapi.testclient import TestClient  # noqa: E402

import qad_client  # noqa: E402
from core import auth  # noqa: E402

_TEST_TOKEN = {"value": ""}
auth.configured_token = lambda: _TEST_TOKEN["value"]

FAILURES: list = []

# What the stub will answer, and what it was asked. Set per section.
_STUB = {"result": None, "raises": None, "calls": []}


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


async def _fake_call(endpoint_id: str, **kwargs):
    """Stands in for qad_client.call. Records the ask, returns the canned answer.

    It can also RAISE, because the real transport does: no credentials, a
    rejected login and an unresolvable endpoint id all come out as an exception
    rather than a QadResult.
    """
    _STUB["calls"].append((endpoint_id, kwargs.get("params")))
    if _STUB["raises"] is not None:
        raise _STUB["raises"]
    return _STUB["result"]


qad_client.call = _fake_call


def _answer(**kw) -> None:
    _STUB["result"] = qad_client.QadResult(**kw)
    _STUB["raises"] = None
    _STUB["calls"] = []


def _raises(exc: BaseException) -> None:
    _STUB["result"] = None
    _STUB["raises"] = exc
    _STUB["calls"] = []


def main() -> int:
    print("routers/browses: offline checks")
    _TEST_TOKEN["value"] = ""   # unauthenticated for sections 1-5

    from main import app
    with TestClient(app) as c:

        section("1. A good uri returns the mapped shape")
        # Both spellings QAD really uses, in one list: a dotted name (cm001) and
        # a bare one (pp125). Neither may be reshaped on the way out.
        _answer(ok=True, status_code=200, data={"data": [
            {"field": "debtor.DebtorCode", "fieldLabel": "Debtor Code",
             "fieldDataType": "character"},
            {"field": "pt_part", "fieldLabel": "", "fieldDataType": "character"},
            {"field": "changeStatus", "fieldDataType": "logical"},
        ]})
        r = c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:cm001"})
        check("200", r.status_code, 200)
        body = r.json()
        check("uri echoed", body["uri"], "urn:browse:mfg:cm001")
        check("mapped to field/label/data_type", body["fields"], [
            {"field": "debtor.DebtorCode", "label": "Debtor Code",
             "data_type": "character"},
            {"field": "pt_part", "label": "", "data_type": "character"},
            {"field": "changeStatus", "label": "", "data_type": "logical"},
        ])
        check("dotted name verbatim", body["fields"][0]["field"], "debtor.DebtorCode")
        check("bare name verbatim", body["fields"][1]["field"], "pt_part")
        check("no note when there are rows", "note" in body, False)
        check("asked the lookup endpoint", _STUB["calls"],
              [("lookup.browse_fields", {"browse_uri": "urn:browse:mfg:cm001"})])

        section("2. Zero rows is 200 with a note, not an error")
        # A browse code that does not exist answers 200 with no rows. Proven
        # with urn:browse:mfg:zz999 on 2026-09-01.
        _answer(ok=True, status_code=200, data={"data": []})
        r = c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:zz999"})
        check("200", r.status_code, 200)
        check("empty list", r.json()["fields"], [])
        check("note explains it", r.json()["note"],
              "QAD does not know this browse, or it has no fields. Check the URI.")

        _answer(ok=True, status_code=200, data={})
        check("a body with no data key is the same outcome",
              c.get("/api/browses/fields",
                    params={"uri": "urn:browse:mfg:zz999"}).json()["fields"], [])

        section("3. A QAD failure is 502 carrying QAD's own words")
        _answer(ok=False, status_code=403,
                error="QAD refused the request (HTTP 403) on 'lookup.browse_fields'.")
        r = c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:cm007"})
        check("502", r.status_code, 502)
        check("QAD's text, not a generic message", r.json()["detail"],
              "QAD refused the request (HTTP 403) on 'lookup.browse_fields'.")

        section("4. A uri that is not a browse uri is refused before QAD is asked")
        _answer(ok=True, status_code=200, data={"data": [{"field": "x"}]})
        r = c.get("/api/browses/fields", params={"uri": "cm007"})
        check("400", r.status_code, 400)
        check("says what a uri looks like",
              "urn:browse:" in r.json()["detail"], True)
        check("QAD was never asked", _STUB["calls"], [])
        check("empty uri is 400 too",
              c.get("/api/browses/fields", params={"uri": ""}).status_code, 400)
        check("a different scheme is 400 too",
              c.get("/api/browses/fields",
                    params={"uri": "urn:entity:mfg:cm007"}).status_code, 400)
        check("still nothing asked of QAD", _STUB["calls"], [])

        section("5. The search route reads the local catalog only")
        r = c.get("/api/browses/search", params={"q": "customer"})
        check("200", r.status_code, 200)
        hits = r.json()["browses"]
        check("default limit is 8", len(hits), 8)
        check("every hit mentions customer",
              all("customer" in (b["description"] + " " + b["term"]).lower()
                  for b in hits), True)
        check("cm007 is among them", "cm007" in [b["code"] for b in hits], True)
        check("carries the uri the picker needs",
              [b["uri"] for b in hits if b["code"] == "cm007"],
              ["urn:browse:mfg:cm007"])
        check("limit respected",
              len(c.get("/api/browses/search",
                        params={"q": "customer", "limit": 3}).json()["browses"]), 3)
        check("limit capped at 25",
              len(c.get("/api/browses/search",
                        params={"q": "order", "limit": 500}).json()["browses"]), 25)
        check("an empty query returns nothing rather than the whole catalog",
              c.get("/api/browses/search", params={"q": ""}).json()["browses"], [])
        check("no QAD call was made for any search", _STUB["calls"], [])

        section("6. Auth, once a token is configured")
        _TEST_TOKEN["value"] = "s3cret-token"
        _answer(ok=True, status_code=200, data={"data": [
            {"field": "pt_part", "fieldLabel": "Part", "fieldDataType": "character"}]})
        check("fields without a token is 401",
              c.get("/api/browses/fields",
                    params={"uri": "urn:browse:mfg:pp125"}).status_code, 401)
        check("a wrong token is 401",
              c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:pp125"},
                    headers={"Authorization": "Bearer wrong"}).status_code, 401)
        check("QAD is never asked on a rejected request", _STUB["calls"], [])
        check("the right token works",
              c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:pp125"},
                    headers={"Authorization": "Bearer s3cret-token"}).status_code, 200)
        check("search stays open - it reads only the local file",
              c.get("/api/browses/search", params={"q": "customer"}).status_code, 200)
        _TEST_TOKEN["value"] = ""

        section("7. A transport that RAISES is 502 too, not a bare 500")
        # These are the real ones. qad_client.get_token raises when the three
        # credential keys are missing, _post_token raises on a rejected login,
        # and config raises when the endpoint id cannot be resolved. None of
        # them produce a QadResult, so section 3 alone never covered them.
        _raises(RuntimeError(
            "Cannot authenticate to QAD, missing QAD_CLIENT_ID, QAD_USERNAME, "
            "QAD_PASSWORD. Set them in backend/.env."))
        r = c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:cm007"})
        check("502, not 500", r.status_code, 502)
        check("the actionable sentence survives", r.json()["detail"],
              "Cannot authenticate to QAD, missing QAD_CLIENT_ID, QAD_USERNAME, "
              "QAD_PASSWORD. Set them in backend/.env.")

        _raises(RuntimeError("QAD login failed (HTTP 401). Server said: bad password."))
        check("a rejected login is 502 as well",
              c.get("/api/browses/fields",
                    params={"uri": "urn:browse:mfg:cm007"}).status_code, 502)
        check("its words survive too",
              c.get("/api/browses/fields",
                    params={"uri": "urn:browse:mfg:cm007"}).json()["detail"],
              "QAD login failed (HTTP 401). Server said: bad password.")

        _raises(ValueError("unknown endpoint id 'lookup.browse_fields'"))
        r = c.get("/api/browses/fields", params={"uri": "urn:browse:mfg:cm007"})
        check("a config failure is 502 as well", r.status_code, 502)
        check("never the generic body",
              r.json()["detail"] != "Internal Server Error", True)

        section("8. The uri cannot forge a log line or break the console")
        # backend/logs/app.log is the audit trail for writes into a live QAD.
        # An unauthenticated GET must not be able to plant a line in it, and it
        # must not send non-ASCII to a cp1252 stdout handler either. Records
        # are captured here rather than read back off disk.
        records: list = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        captured = _Capture()
        browses_logger = logging.getLogger("adaptive.api.browses")
        browses_logger.addHandler(captured)
        try:
            _answer(ok=True, status_code=200, data={"data": [{"field": "pt_part"}]})
            forged = ("urn:browse:mfg:cm007\n2026-09-01T09:00:00 | ERROR   | "
                      "adaptive.deploy | [OK] deploy.approved :: by admin")
            check("the crafted uri is still answered",
                  c.get("/api/browses/fields", params={"uri": forged}).status_code, 200)
            check("one record, not two", len(records), 1)
            check("no newline left to start a fake line",
                  "\n" in records[0] or "\r" in records[0], False)

            records.clear()
            _answer(ok=True, status_code=200, data={"data": [{"field": "pt_part"}]})
            check("a non-ASCII uri is answered too",
                  c.get("/api/browses/fields",
                        params={"uri": "urn:browse:mfg:\u00e9\u4e2d\U0001f600"}
                        ).status_code, 200)
            check("what was logged is pure ASCII",
                  records[0].encode("ascii", "strict").decode("ascii"), records[0])

            records.clear()
            _answer(ok=True, status_code=200, data={"data": [{"field": "pt_part"}]})
            check("a very long uri is answered too",
                  c.get("/api/browses/fields",
                        params={"uri": "urn:browse:mfg:" + "x" * 5000}
                        ).status_code, 200)
            check("the logged uri is truncated",
                  len(records[0]) < 300, True)
        finally:
            browses_logger.removeHandler(captured)

        check("the uri still reaches QAD unchanged",
              _STUB["calls"][0][1]["browse_uri"], "urn:browse:mfg:" + "x" * 5000)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print(f"All checks passed. No network call was made. Temp db: {_TMP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
