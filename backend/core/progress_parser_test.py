"""
Offline tests for core.progress_parser. No network, no credentials, no pytest.

Run from the backend directory:

    python core/progress_parser_test.py

Sections 1-4 port the AUX suite
(aux_web_version/backend/core/progress_parser_test.py:24-207) onto the new
parse_abl API. Sections 5-9 cover what changed in the port: every temp-table
is returned (AUX kept only the first downstream, aux progress_parser.py:379-380),
LIKE references, the zero-table warning, initial/extent/validate extraction,
and the looks_like_abl detector.
"""
from __future__ import annotations

import os
import sys

# Runnable both as `python core/progress_parser_test.py` and as a module.
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from core.progress_parser import parse_abl, looks_like_abl

FAILURES: list = []


def check(label: str, actual, expected) -> None:
    if actual == expected:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


SRC_SIMPLE = """
/* Invoice header, used by INV update. */
DEFINE TEMP-TABLE ttInvoice NO-UNDO
    FIELD InvoiceNumber AS CHARACTER FORMAT "x(20)" LABEL "Invoice #"
    FIELD CustomerId    AS INTEGER
    FIELD Amount        AS DECIMAL FORMAT ">>,>>>,>>9.99"
    FIELD DueDate       AS DATE
    INDEX PK IS PRIMARY UNIQUE InvoiceNumber ASCENDING.

FOR EACH cust NO-LOCK: END.
"""

SRC_COMPOSITE = """
DEFINE TEMP-TABLE ttOrderLine NO-UNDO
    FIELD OrderNum   AS INTEGER
    FIELD LineNum    AS INTEGER
    FIELD ItemCode   AS CHARACTER FORMAT "x(30)"
    FIELD Quantity   AS DECIMAL
    FIELD IsShipped  AS LOGICAL
    FIELD Notes      AS BLOB
    INDEX PK IS PRIMARY UNIQUE OrderNum ASCENDING LineNum ASCENDING.

PROCEDURE compute-total: END PROCEDURE.
FUNCTION lookup-price RETURNS DECIMAL: END FUNCTION.
"""

SRC_CLASS = """
/* Customer entity class. */
CLASS acme.crm.Customer INHERITS acme.crm.EntityBase:
    DEFINE PUBLIC PROPERTY CustomerId AS INTEGER   NO-UNDO GET. SET.
    DEFINE PUBLIC PROPERTY CustomerName AS CHARACTER NO-UNDO GET. SET.
    DEFINE PUBLIC PROPERTY IsActive AS LOGICAL NO-UNDO GET. SET.
    DEFINE PUBLIC PROPERTY CreatedAt AS DATETIME NO-UNDO GET. SET.

    METHOD PUBLIC VOID Deactivate():
    END METHOD.

    METHOD PUBLIC INTEGER GetOrderCount():
    END METHOD.

    METHOD PROTECTED VOID InternalHelper():
    END METHOD.
END CLASS.
"""

SRC_TWO_TABLES = """
DEFINE TEMP-TABLE ttOrder NO-UNDO
    FIELD OrderNum  AS INTEGER
    FIELD OrderDate AS DATE
    INDEX PK IS PRIMARY UNIQUE OrderNum ASCENDING.

DEFINE TEMP-TABLE ttOrderLine NO-UNDO
    FIELD OrderNum AS INTEGER
    FIELD LineNum  AS INTEGER
    FIELD ItemCode AS CHARACTER FORMAT "x(30)"
    INDEX PK IS PRIMARY UNIQUE OrderNum ASCENDING LineNum ASCENDING.
"""

SRC_PARENT_CHILD = """
DEFINE TEMP-TABLE ttParent NO-UNDO
    FIELD ParentId   AS INTEGER
    FIELD ParentName AS CHARACTER FORMAT "x(40)" LABEL "Parent Name"
    INDEX PK IS PRIMARY UNIQUE ParentId ASCENDING.

DEFINE TEMP-TABLE ttChild NO-UNDO LIKE ttParent
    FIELD ChildSeq  AS INTEGER
    FIELD ParentRef LIKE ttParent.ParentId
    INDEX PK IS PRIMARY UNIQUE ChildSeq ASCENDING.
"""


def main() -> int:
    section("1. Simple temp-table (ported from AUX SimpleTempTable)")
    r = parse_abl(SRC_SIMPLE)
    check("source_type", r["source_type"], "p")
    check("one table", len(r["tables"]), 1)
    t = r["tables"][0]
    check("table name keeps source case", t["name"], "ttInvoice")
    check("field names in order, source case",
          [f["name"] for f in t["fields"]],
          ["InvoiceNumber", "CustomerId", "Amount", "DueDate"])
    check("qad types", {f["name"]: f["qad_type"] for f in t["fields"]},
          {"InvoiceNumber": "character", "CustomerId": "integer",
           "Amount": "decimal", "DueDate": "date"})
    check("data types are the ABL types",
          [f["data_type"] for f in t["fields"]],
          ["CHARACTER", "INTEGER", "DECIMAL", "DATE"])
    check("primary key", t["primary_key"], ["InvoiceNumber"])
    by_name = {f["name"]: f for f in t["fields"]}
    check("PK field is required", by_name["InvoiceNumber"]["required"], True)
    check("non-PK field is not", by_name["CustomerId"]["required"], False)
    check("explicit FORMAT preserved", by_name["InvoiceNumber"]["format"], "x(20)")
    check("explicit LABEL preserved", by_name["InvoiceNumber"]["label"], "Invoice #")
    check("default label is title-cased", by_name["CustomerId"]["label"], "Customer Id")
    check("default format applied", by_name["CustomerId"]["format"], "->,>>>,>>9")
    check("index detail extracted", t["indexes"],
          [{"name": "PK", "primary": True, "unique": True, "word": False,
            "fields": ["InvoiceNumber"]}])
    check("FOR EACH table referenced", "cust" in r["source_tables_referenced"], True)
    check("no warnings", r["warnings"], [])

    section("2. Composite PK, lossy types, procedures (AUX CompositePrimaryKey)")
    r = parse_abl(SRC_COMPOSITE)
    t = r["tables"][0]
    check("composite primary key", t["primary_key"], ["OrderNum", "LineNum"])
    by_name = {f["name"]: f for f in t["fields"]}
    check("both PK fields required",
          [by_name["OrderNum"]["required"], by_name["LineNum"]["required"]],
          [True, True])
    check("non-PK not required", by_name["ItemCode"]["required"], False)
    check("LOGICAL maps cleanly", by_name["IsShipped"]["qad_type"], "logical")
    check("BLOB maps to character", by_name["Notes"]["qad_type"], "character")
    check("BLOB carries a warning", any("BLOB" in w for w in r["warnings"]), True)
    check("hyphenated procedure captured", "compute-total" in r["procedures"], True)
    check("hyphenated function captured", "lookup-price" in r["functions"], True)

    section("3. Class file with properties (AUX ClassFileWithProperties)")
    r = parse_abl(SRC_CLASS)
    check("cls detected from the source itself", r["source_type"], "cls")
    check("one synthetic table", len(r["tables"]), 1)
    t = r["tables"][0]
    check("named after the class, package stripped", t["name"], "Customer")
    check("properties become fields", sorted(f["name"] for f in t["fields"]),
          sorted(["CustomerId", "CustomerName", "IsActive", "CreatedAt"]))
    types = {f["name"]: f["qad_type"] for f in t["fields"]}
    check("property types mapped",
          [types["CustomerId"], types["CustomerName"], types["IsActive"], types["CreatedAt"]],
          ["integer", "character", "logical", "datetime"])
    check("PUBLIC methods captured",
          [("Deactivate" in r["procedures"]), ("GetOrderCount" in r["procedures"])],
          [True, True])
    check("PROTECTED helper excluded", "InternalHelper" in r["procedures"], False)

    section("4. Fail-soft edge cases (AUX FailSoftEdgeCases)")
    src = """
    DEFINE TEMP-TABLE ttMisc NO-UNDO
        FIELD Zzz AS BOGUS-TYPE
        INDEX PK IS PRIMARY UNIQUE Zzz ASCENDING.
    """
    r = parse_abl(src)
    f = r["tables"][0]["fields"][0]
    check("unknown type defaults to character", f["qad_type"], "character")
    check("original type kept on data_type", f["data_type"], "BOGUS-TYPE")
    check("and is warned about", any("BOGUS-TYPE" in w for w in r["warnings"]), True)

    src = """
    /* DEFINE TEMP-TABLE ttFake NO-UNDO FIELD Should-Not-Match AS CHARACTER. */
    DEFINE TEMP-TABLE ttReal NO-UNDO
        FIELD Foo AS INTEGER
        INDEX PK IS PRIMARY UNIQUE Foo ASCENDING.
    """
    r = parse_abl(src)
    check("commented-out table ignored", len(r["tables"]), 1)
    check("real table found", r["tables"][0]["name"], "ttReal")

    section("5. Multi-table files return EVERY table (the rework)")
    r = parse_abl(SRC_TWO_TABLES)
    check("both tables returned", len(r["tables"]), 2)
    check("source order preserved", [t["name"] for t in r["tables"]],
          ["ttOrder", "ttOrderLine"])
    check("first table has its complete field list",
          [f["name"] for f in r["tables"][0]["fields"]], ["OrderNum", "OrderDate"])
    check("second table has its complete field list",
          [f["name"] for f in r["tables"][1]["fields"]],
          ["OrderNum", "LineNum", "ItemCode"])
    check("each table keeps its own primary key",
          [t["primary_key"] for t in r["tables"]],
          [["OrderNum"], ["OrderNum", "LineNum"]])
    check("field detail intact on the second table",
          {f["name"]: f["format"] for f in r["tables"][1]["fields"]}["ItemCode"],
          "x(30)")
    check("no warnings", r["warnings"], [])

    section("6. Parent + child with LIKE references")
    r = parse_abl(SRC_PARENT_CHILD)
    check("both tables parsed", [t["name"] for t in r["tables"]],
          ["ttParent", "ttChild"])
    child = r["tables"][1]
    check("table-level LIKE recorded", child["like_table"], "ttParent")
    check("parent fields inherited, own fields appended",
          [f["name"] for f in child["fields"]],
          ["ParentId", "ParentName", "ChildSeq", "ParentRef"])
    by_name = {f["name"]: f for f in child["fields"]}
    check("inherited field keeps the parent's format",
          by_name["ParentName"]["format"], "x(40)")
    check("inherited field does not inherit required",
          by_name["ParentId"]["required"], False)
    check("field-level LIKE recorded",
          by_name["ParentRef"]["like_source"], "ttParent.ParentId")
    check("field-level LIKE resolves the type",
          [by_name["ParentRef"]["data_type"], by_name["ParentRef"]["qad_type"]],
          ["INTEGER", "integer"])
    check("child primary key is its own", child["primary_key"], ["ChildSeq"])
    check("resolvable LIKEs produce no warnings", r["warnings"], [])

    src = """
    DEFINE TEMP-TABLE ttCust NO-UNDO LIKE customer
        FIELD Extra AS CHARACTER
        FIELD Amt LIKE invoice.amount.
    """
    r = parse_abl(src)
    t = r["tables"][0]
    check("unresolvable table LIKE still recorded", t["like_table"], "customer")
    check("only inline fields listed", [f["name"] for f in t["fields"]],
          ["Extra", "Amt"])
    check("and it is warned about",
          any("LIKE customer" in w for w in r["warnings"]), True)
    check("unresolvable field LIKE defaults to character",
          t["fields"][1]["qad_type"], "character")
    check("with its own warning",
          any("LIKE invoice.amount" in w for w in r["warnings"]), True)

    section("7. Zero temp-tables warns instead of raising")
    r = parse_abl("MESSAGE 'hello'.")
    check("tables is empty", r["tables"], [])
    check("exactly one warning", len(r["warnings"]), 1)
    check("warning names the missing construct",
          "No DEFINE TEMP-TABLE" in r["warnings"][0], True)
    r = parse_abl("")
    check("empty input follows the same path",
          [r["tables"], len(r["warnings"])], [[], 1])

    section("8. INITIAL / EXTENT / VALIDATE and syntax widenings")
    src = """
    DEFINE TEMP-TABLE ttCfg NO-UNDO
        FIELD Qty      AS INTEGER INITIAL 5 EXTENT 3
        FIELD Status   AS CHARACTER INITIAL "OPEN" VALIDATE(Status <> "", "Status is required")
        FIELD Active   AS LOGICAL INITIAL yes
        FIELD cust-num AS INTEGER
        FIELD Nm       AS CHARACTER FORMAT 'x(15)'
        INDEX PK PRIMARY cust-num.
    """
    r = parse_abl(src)
    t = r["tables"][0]
    by_name = {f["name"]: f for f in t["fields"]}
    check("numeric INITIAL", by_name["Qty"]["initial"], "5")
    check("EXTENT", by_name["Qty"]["extent"], 3)
    check("quoted INITIAL", by_name["Status"]["initial"], "OPEN")
    check("keyword INITIAL", by_name["Active"]["initial"], "yes")
    check("absent INITIAL is None", by_name["Nm"]["initial"], None)
    check("absent EXTENT is None", by_name["Status"]["extent"], None)
    check("VALIDATE expression captured", by_name["Status"]["validate"],
          'Status <> "", "Status is required"')
    check("no VALIDATE means None", by_name["Qty"]["validate"], None)
    check("hyphenated field name parses (dropped by AUX)",
          "cust-num" in by_name, True)
    check("single-quoted FORMAT accepted (AUX double-quote only)",
          by_name["Nm"]["format"], "x(15)")
    check("PRIMARY without IS recognised (AUX required IS PRIMARY)",
          t["primary_key"], ["cust-num"])

    section("9. looks_like_abl: real ABL yes, plain English never")
    check("temp-table source", looks_like_abl(SRC_SIMPLE), True)
    check("class source", looks_like_abl(SRC_CLASS), True)
    check("bare variable definition",
          looks_like_abl("DEFINE VARIABLE cName AS CHARACTER NO-UNDO."), True)
    check("FOR EACH with a lock",
          looks_like_abl("FOR EACH customer NO-LOCK:\n  DISPLAY customer.\nEND."), True)
    check("two medium signals suffice",
          looks_like_abl("FIND FIRST order WHERE order.num = 1.\nASSIGN total = 0."), True)
    check("plain requirements prose",
          looks_like_abl("Please create a business component for invoices with "
                         "fields for number, customer and amount."), False)
    check("prose using ABL-ish words",
          looks_like_abl("For each invoice, define variable pricing rules and "
                         "find the first customer."), False)
    check("prose with a colon after 'procedure'",
          looks_like_abl("The procedure follows: for each step, assign an owner."),
          False)
    check("prose mentioning a class",
          looks_like_abl("Class notes: remember to define variables for the demo."),
          False)
    check("empty text", looks_like_abl(""), False)
    check("whitespace only", looks_like_abl("   \n  "), False)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("All checks passed. No network call was made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
