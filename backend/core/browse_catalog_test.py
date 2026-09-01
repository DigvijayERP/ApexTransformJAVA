"""
Offline tests for core.browse_catalog. No network, no credentials, no pytest.

Run from the backend directory:

    python core/browse_catalog_test.py

Nothing here calls QAD. The catalog is a file, and the ranking is deterministic
by design, so every answer below is reproducible on a machine with no network.
The live evidence behind the URI form (cm007 -> 111 fields, ad057 -> 36, and a
made-up code -> nothing) was collected once by hand on 2026-09-01 and is
recorded in PROGRESS.md, not re-run here.
"""
from __future__ import annotations

import os
import sys

# Runnable both as `python core/browse_catalog_test.py` and as a module.
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from core import browse_catalog as bc

FAILURES: list = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def codes(browses) -> list:
    return [b.code for b in browses]


def main() -> int:
    print("browse_catalog: offline checks")

    section("1. The file loads")
    rows = bc.all_browses()
    check("row count", len(rows), 3357)
    check("every code is unique", len({b.code for b in rows}), len(rows))
    check("no blank codes", [b.code for b in rows if not b.code.strip()], [])

    section("2. One known browse")
    cm007 = bc.get("cm007")
    check("uri", cm007.uri, "urn:browse:mfg:cm007")
    check("description", cm007.description, "Customer")
    check("term", cm007.term, "CUSTOMER")
    check("to_dict carries the uri", cm007.to_dict()["uri"], "urn:browse:mfg:cm007")
    try:
        bc.get("zz999")
        check("unknown code raises", "no error", "KeyError")
    except KeyError as e:
        check("unknown code raises a plain message", "zz999" in str(e), True)

    section("3. URI round trip")
    check("by_uri finds cm007", bc.by_uri("urn:browse:mfg:cm007"), cm007)
    check("by_uri round trip", bc.by_uri(cm007.uri).code, "cm007")
    # zz999 is the control: it is not in the export, and the live endpoint
    # returned nothing for it on 2026-09-01.
    check("unknown uri is None", bc.by_uri("urn:browse:mfg:zz999"), None)
    check("another scheme is None", bc.by_uri("urn:be:com.qad.base.item.IItem"), None)
    check("empty uri is None", bc.by_uri(""), None)

    section("4. The two browses QAD's own class-4 guide uses")
    top5 = codes(bc.suggest_for_field("BillToCustomer"))
    check("suggest_for_field('BillToCustomer') offers cm007", "cm007" in top5, True)
    check("and offers at most 5", len(top5) <= 5, True)
    check("search('address') offers ad057", "ad057" in codes(bc.search("address")), True)

    section("5. The Lookup=No trap")
    # This test exists to stop anyone adding a filter on the Lookup column
    # later. cm007 is marked Lookup=No in the export, and QAD's own guide still
    # uses it as a customer lookup browse. If a filter is ever added, the second
    # and third checks here fail, which is the whole point of them.
    check("cm007 really is flagged Lookup=No", cm007.is_lookup, False)
    check("and it is still returned by search", "cm007" in codes(bc.search("customer", limit=8)), True)
    check("and still by suggest_for_field", "cm007" in codes(bc.suggest_for_field("BillToCustomer")), True)
    flagged = [b for b in bc.search("customer", limit=8) if b.is_lookup]
    check("results are not all Lookup=Yes", len(flagged) < 8, True)

    section("6. Field codes with nothing to search on")
    check("suggest_for_field('orderCode') finds something",
          len(bc.suggest_for_field("orderCode")) > 0, True)
    check("suggest_for_field('code') is empty", bc.suggest_for_field("code"), [])
    check("'id' alone is empty", bc.suggest_for_field("id"), [])
    check("an empty code is empty", bc.suggest_for_field(""), [])
    # An attribute on its own says what is held, never which thing it is held
    # about, so it is as empty a question as "code".
    check("'name' alone is empty", bc.suggest_for_field("name"), [])
    check("'date' alone is empty", bc.suggest_for_field("date"), [])
    check("'status' alone is empty", bc.suggest_for_field("status"), [])
    check("suggest_for_field('supplierName') finds something",
          len(bc.suggest_for_field("supplierName")) > 0, True)

    section("7. The same question gets the same answer")
    check("suggest_for_field is stable",
          codes(bc.suggest_for_field("customerCode")),
          codes(bc.suggest_for_field("customerCode")))
    check("search is stable", codes(bc.search("order")), codes(bc.search("order")))
    check("a reload changes nothing", codes(bc.search("order")),
          (bc.reload(), codes(bc.search("order")))[1])

    section("8. Every result is a result for a reason")
    for b in bc.search("customer", limit=8):
        words = set(bc._words(b.description)) | set(bc._words(b.term))
        check(f"{b.code} mentions customer", "customer" in words, True)
    for b in bc.suggest_for_field("orderCode"):
        words = set(bc._words(b.description)) | set(bc._words(b.term))
        check(f"{b.code} mentions order", "order" in words, True)
    # A field code ending in an attribute word is the case that used to break:
    # "name" took the head weight and every candidate came back about names.
    for b in bc.suggest_for_field("supplierName"):
        words = set(bc._words(b.description)) | set(bc._words(b.term))
        check(f"{b.code} mentions supplier", "supplier" in words, True)
    for b in bc.suggest_for_field("customerDescription"):
        words = set(bc._words(b.description)) | set(bc._words(b.term))
        check(f"{b.code} mentions customer", "customer" in words, True)

    section("9. Limits are respected")
    check("search limit", len(bc.search("order", limit=3)), 3)
    check("suggest limit", len(bc.suggest_for_field("customerCode", limit=2)), 2)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("All checks passed. No network call was made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
