"""
Event handler probe — settles Q-L / D4a on THIS environment with Adaptive's own
transport (registry ids, cached token, encoded credentials).

Phase A (default, READ-ONLY):
  1. GET our own handler (DigOrderTesting, BEFORE/WEB) — the row Case 1
     registered live on 2026-08-12. Confirms the GET contract: response shape,
     concurrencyHash, code fields.
  2. Same view, PRIMARY and AFTER — does the GET filter by timing strictly?
  3. Standard parent views under OUR appURI — the exact configuration the
     embedded-validation feature will run in. SalesOrders URI is the shape AUX's
     probe used; the PurchaseOrders URIs are CANDIDATES (inferred by analogy,
     marked as such): an empty result there is INCONCLUSIVE (wrong URI vs no
     handler), only a non-empty result is evidence.

Phase B (--write, ONE deliberate no-op write, greenlit by the owner 2026-08-31):
  4. POST our own handler back byte-identical, echoing uri + concurrencyHash
     (probe_parent_eh.py Shape A). Then re-GET and check:
       - row count: 1 row still = UPDATE semantics; 2 rows = create-only trap
       - concurrencyHash rotated?
       - typeScriptCode byte-identical?
  Targets ONLY the handler this project owns. Never a standard parent's.

Run:
    cd /d D:\WEB_AUX\adaptive_java_version\backend
    python probe_eventhandler.py            (reads only)
    python probe_eventhandler.py --write    (reads + the one no-op update)
"""
from __future__ import annotations

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import qad_client
from core import config

OUR_VIEW = "urn:view:viewmeta:com.yash.digwish.DigOrderTesting"

# (label, view_uri, provenance)
PARENT_VIEWS = [
    ("SalesOrders [shape confirmed on AUX env]",
     "urn:view:viewmeta:com.qad.erp.sales.SalesOrders", "aux probe_parent_eh.py:26"),
    ("PurchaseOrders [CANDIDATE, inferred by analogy]",
     "urn:view:viewmeta:com.qad.erp.purchasing.PurchaseOrders", "guess"),
    ("PurchaseOrderHeaders [CANDIDATE, inferred by analogy]",
     "urn:view:viewmeta:com.qad.erp.purchasing.PurchaseOrderHeaders", "guess"),
]


def rows_of(result) -> list:
    return (result.data or {}).get("data", {}).get("eventHandlerV2s", []) or []


def describe_rows(rows: list) -> None:
    for i, h in enumerate(rows):
        ts = h.get("typeScriptCode") or ""
        js = h.get("javaScriptCode") or ""
        print(f"    row[{i}] uri={h.get('uri')}")
        print(f"           type={h.get('eventHandlerType')} appliesTo={h.get('appliesTo')} "
              f"isActive={h.get('isActive')}")
        print(f"           concurrencyHash={h.get('concurrencyHash')}")
        print(f"           tsLen={len(ts)} jsLen={len(js)}")
        print(f"           extraKeys={sorted(set(h) - {'uri','eventHandlerType','appliesTo','isActive','concurrencyHash','typeScriptCode','javaScriptCode'})}")


async def get_handler(view_uri: str, timing: str):
    return await qad_client.call(
        "eventhandler.read",
        params={"parent_view_uri": view_uri, "timing": timing},
    )


async def main() -> None:
    do_write = "--write" in sys.argv

    print("=" * 72)
    print("PHASE A - reads only")
    print("=" * 72)

    # 1. Our own handler.
    print(f"\n[A1] GET our handler  view={OUR_VIEW}  timing=BEFORE")
    r = await get_handler(OUR_VIEW, "BEFORE")
    print(f"    ok={r.ok} http={r.status_code} error={r.error[:200]}")
    ours = rows_of(r)
    print(f"    rows={len(ours)}")
    describe_rows(ours)

    # 2. Timing filter behaviour on the same view.
    for t in ("PRIMARY", "AFTER"):
        rt = await get_handler(OUR_VIEW, t)
        print(f"[A2] timing={t:<8} ok={rt.ok} http={rt.status_code} rows={len(rows_of(rt))} "
              f"error={rt.error[:120]}")

    # 3. Standard parent views under OUR appURI.
    for label, view, src in PARENT_VIEWS:
        print(f"\n[A3] {label}  ({src})")
        for t in ("BEFORE", "PRIMARY", "AFTER"):
            rp = await get_handler(view, t)
            n = len(rows_of(rp))
            print(f"    timing={t:<8} ok={rp.ok} http={rp.status_code} rows={n} "
                  f"error={rp.error[:120]}")
            if n:
                describe_rows(rows_of(rp))

    if not do_write:
        print("\n(no --write flag: stopping before Phase B)")
        return

    # ── Phase B ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("PHASE B - the one no-op update, OUR OWN handler only")
    print("=" * 72)
    if not ours:
        print("ABORT: our own handler was not found in Phase A; nothing safe to update.")
        return
    if len(ours) > 1:
        print("ABORT: more than one row for our 4-tuple; ambiguity must be understood first.")
        return

    h = ours[0]
    ident_app = config.app_uri()
    payload = {
        "supplementaryMessages": [],
        "eventHandlerV2s": [{
            "uri":               h["uri"],
            "appURI":            ident_app,
            "viewURI":           OUR_VIEW,
            "eventHandlerType":  "BEFORE",
            "appliesTo":         "WEB",
            "isActive":          h["isActive"],
            "concurrencyHash":   h["concurrencyHash"],
            "typeScriptCode":    h.get("typeScriptCode", ""),
            "javaScriptCode":    h.get("javaScriptCode", ""),
            "mappingCode":       h.get("mappingCode", "") or "",
            "disallowedActions": h.get("disallowedActions", "") or "",
        }],
    }
    print("[B1] POST eventhandler (Shape A: uri + concurrencyHash echoed, code unchanged)")
    print(f"    target uri = {h['uri']}")
    w = await qad_client.call("eventhandler.register", payload=payload)
    print(f"    ok={w.ok} http={w.status_code} error={w.error[:300]}")
    print(f"    messages={w.messages}")
    sr = (w.data or {}).get("submitResult")
    print(f"    submitResult={json.dumps(sr)[:400] if sr is not None else '(absent)'}")

    print("[B2] re-GET to verify against a read-back, not the success message")
    r2 = await get_handler(OUR_VIEW, "BEFORE")
    rows2 = rows_of(r2)
    print(f"    rows now = {len(rows2)}  (1 = update semantics, 2 = CREATE-ONLY TRAP)")
    describe_rows(rows2)
    if rows2:
        same_uri = [x for x in rows2 if x.get("uri") == h.get("uri")]
        n = same_uri[0] if same_uri else rows2[0]
        print(f"    hash rotated      : {n.get('concurrencyHash') != h.get('concurrencyHash')}")
        print(f"    ts byte-identical : {n.get('typeScriptCode') == h.get('typeScriptCode')}")
        print(f"    js byte-identical : {n.get('javaScriptCode') == h.get('javaScriptCode')}")

    print("\nProbe done.")


if __name__ == "__main__":
    asyncio.run(main())
