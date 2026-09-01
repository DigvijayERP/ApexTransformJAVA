"""
Tests for the Case 4 merge engine.

The fixture below is the EXACT handler QAD generated on the live system
(read back 2026-08-31), trailing spaces and dead console.log included. The
byte-for-byte round-trip tests run against it, and the compile tests run the
real tsc from frontend/node_modules through Node.

Compile sections are skipped with a loud note when node is missing, but on
this machine node is available so they should really run.

Run:  python builders/screen_rule_builder_test.py
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders import screen_rule_builder as srb  # noqa: E402

FAILURES: list = []


def check(name, actual, expected):
    if actual == expected:
        print("  ok    " + name)
    else:
        print("  FAIL  %s\n          expected: %r\n          actual:   %r"
              % (name, expected, actual))
        FAILURES.append(name)


def section(title):
    print("\n" + title + "\n" + "-" * len(title))


NODE = shutil.which("node")

# The vendored QAD compile kit. Installed by the integration work; when it is
# missing the kit sections below are skipped LOUDLY, never silently.
KIT_DIR = Path(srb.__file__).resolve().parents[1] / "qad_compile"
KIT_OK = ((KIT_DIR / "qadCompile.js").is_file()
          and (KIT_DIR / "node_modules" / "typescript").is_dir())


def skip_kit(what: str) -> None:
    print("  SKIPPED %s: the QAD compile kit is NOT installed at %s. "
          "It is expected to be installed on this machine. Run "
          "'npm install' in that folder to get the real check."
          % (what, KIT_DIR))

# The real scaffold, verbatim. Note the trailing spaces on two doc-comment
# lines and the blank 8-space line in the FormHandler body: byte-for-byte
# preservation must survive them.
FIXTURE = (
    'module com.qad.erp.purchasing.EventHandler.PurchaseOrders.ComYashDigwish.Maint_BEFORE {\n'
    '    "use strict";\n'
    '\n'
    '    import QraViewTSHandlerWithViewFormTSHandler = Qad.QraView.TSHandler.QraViewTSHandlerWithViewFormTSHandler;\n'
    '    import QraViewFormTSHandlerV2 = Qad.QraView.TSHandler.QraViewFormTSHandlerV2;\n'
    '    import IViewField = Qad.QraView.TSHandler.IViewField;\n'
    '    import DTO = com.qad.erp.purchasing.EventHandler.PurchaseOrders.DTO;\n'
    '    import Constants = com.qad.erp.purchasing.EventHandler.PurchaseOrders.Constants;\n'
    '\n'
    '    /**\n'
    '     * PurchaseOrdersMaintHandler : Maint TS handler class. \n'
    '     * \n'
    '     * Do not change this class name or the event handler will no longer run.\n'
    '     *\n'
    '     */\n'
    '    export class PurchaseOrdersMaintHandler extends QraViewTSHandlerWithViewFormTSHandler<DTO.PurchaseOrdersMaint, PurchaseOrdersFormHandler> {\n'
    '        protected createViewFormTSHandler(): PurchaseOrdersFormHandler {\n'
    '            return new PurchaseOrdersFormHandler(this);\n'
    '            console.log("hello");\n'
    '        }\n'
    '    }\n'
    '\n'
    '    export class PurchaseOrdersFormHandler extends QraViewFormTSHandlerV2<DTO.PurchaseOrdersMaint> {\n'
    '        \n'
    '    }\n'
    '}\n'
)

IDENTITY = srb.HandlerIdentity(
    view_pascal="PurchaseOrders",
    view_namespace="com.qad.erp.purchasing",
    app_pascal="ComYashDigwish",
    timing="BEFORE",
)

MODULE_PATH = ("com.qad.erp.purchasing.EventHandler.PurchaseOrders"
               ".ComYashDigwish.Maint_BEFORE")

RULE_A = srb.ScreenRule(
    slug="remarks-required",
    method_ts=(
        "public rule_remarks_required(eventData: any): any {\n"
        "    var problems = [];\n"
        "    return problems;\n"
        "}"),
    method_js=(
        "var problems = [];\n"
        "return problems;"),
)

RULE_B = srb.ScreenRule(
    slug="amount-check",
    method_ts=(
        "public rule_amount_check(eventData: any): any {\n"
        "    var problems = [];\n"
        "    return problems;\n"
        "}"),
    method_js=(
        "var problems = [];\n"
        "return problems;"),
)

# Test 13: a realistic rule. It finds the embedded child collection key by
# suffix at runtime, then checks each row.
RULE_REAL = srb.ScreenRule(
    slug="inspection-complete",
    method_ts=(
        "public rule_inspection_complete(eventData: any): any {\n"
        "    var problems = [];\n"
        "    var key = null;\n"
        "    var k;\n"
        "    for (k in this.NgData) {\n"
        '        if (k.indexOf("_DigPoInspection", k.length - "_DigPoInspection".length) !== -1) {\n'
        "            key = k;\n"
        "        }\n"
        "    }\n"
        "    if (key === null) {\n"
        "        return problems;\n"
        "    }\n"
        "    var rows = this.NgData[key];\n"
        "    var i;\n"
        "    for (i = 0; i < rows.length; i++) {\n"
        "        if (!rows[i].inspectionComplete) {\n"
        "            problems.push({\n"
        '                message: "Inspection is not complete on row " + (i + 1) + ".",\n'
        '                fieldName: "inspectionComplete"\n'
        "            });\n"
        "        }\n"
        "    }\n"
        "    return problems;\n"
        "}"),
    method_js=(
        "var problems = [];\n"
        "var key = null;\n"
        "var k;\n"
        "for (k in this.NgData) {\n"
        '    if (k.indexOf("_DigPoInspection", k.length - "_DigPoInspection".length) !== -1) {\n'
        "        key = k;\n"
        "    }\n"
        "}\n"
        "if (key === null) {\n"
        "    return problems;\n"
        "}\n"
        "var rows = this.NgData[key];\n"
        "var i;\n"
        "for (i = 0; i < rows.length; i++) {\n"
        "    if (!rows[i].inspectionComplete) {\n"
        "        problems.push({\n"
        '            message: "Inspection is not complete on row " + (i + 1) + ".",\n'
        '            fieldName: "inspectionComplete"\n'
        "        });\n"
        "    }\n"
        "}\n"
        "return problems;"),
)


def main() -> int:
    section("1. build_scaffold_ts regenerates the real scaffold shape")
    scaffold = srb.build_scaffold_ts(IDENTITY)
    check("module path present", MODULE_PATH in scaffold, True)
    check("Maint class name present",
          "export class PurchaseOrdersMaintHandler" in scaffold, True)
    check("Form class name present",
          "export class PurchaseOrdersFormHandler" in scaffold, True)
    check("factory method present",
          "return new PurchaseOrdersFormHandler(this);" in scaffold, True)
    if NODE:
        res = srb.compile_check(scaffold)
        if not res.ok:
            print("  tsc said: " + "; ".join(res.errors)[:800])
        check("scaffold compiles clean with the ambient stub", res.ok, True)
    else:
        print("  SKIPPED compile: node is NOT on PATH. This machine is "
              "expected to have it. Install Node.js to run the real check.")

    section("2. Round trip: strip after apply gives the fixture back")
    merged = srb.apply_rules(FIXTURE, [RULE_A], IDENTITY)
    check("rule block was inserted",
          "// === RULE: remarks-required START ===" in merged, True)
    check("dispatcher block was inserted",
          "// === RULE: adaptive-dispatch START ===" in merged, True)
    check("strip_rules(apply_rules(fixture)) == fixture byte for byte",
          srb.strip_rules(merged) == FIXTURE, True)

    section("3. CRLF input is preserved and round trips")
    crlf = FIXTURE.replace("\n", "\r\n")
    merged_crlf = srb.apply_rules(crlf, [RULE_A], IDENTITY)
    check("no lone LF anywhere in the merged CRLF file",
          "\n" in merged_crlf.replace("\r\n", ""), False)
    check("CRLF round trip is byte for byte",
          srb.strip_rules(merged_crlf) == crlf, True)

    section("4. Re-running apply_rules is idempotent")
    once = srb.apply_rules(FIXTURE, [RULE_A, RULE_B], IDENTITY)
    twice = srb.apply_rules(once, [RULE_A, RULE_B], IDENTITY)
    check("apply(apply(x)) == apply(x)", twice == once, True)

    section("5. Two rules: both blocks, dispatcher calls both, sorted listing")
    both = once
    check("rule block A present",
          "// === RULE: remarks-required START ===" in both, True)
    check("rule block B present",
          "// === RULE: amount-check START ===" in both, True)
    check("dispatcher calls rule A",
          "this.rule_remarks_required(eventData);" in both, True)
    check("dispatcher calls rule B",
          "this.rule_amount_check(eventData);" in both, True)
    check("list_rules returns both slugs sorted",
          srb.list_rules(both), ["amount-check", "remarks-required"])

    section("6. Applying with one rule removed drops its block only")
    removed = srb.apply_rules(both, [RULE_A], IDENTITY)
    check("removed rule block is gone", "amount-check" in removed, False)
    check("kept rule block is intact",
          "// === RULE: remarks-required START ===" in removed, True)
    check("dispatcher no longer calls the removed rule",
          "rule_amount_check" in removed, False)
    check("dispatcher still calls the kept rule",
          "this.rule_remarks_required(eventData);" in removed, True)
    check("list_rules shows only the kept rule",
          srb.list_rules(removed), ["remarks-required"])

    section("7. A hand written save hook stops the merge")
    own_hook = FIXTURE.replace(
        "        }\n    }",
        "        }\n\n"
        "        public onBeforeUpdate(eventData: any, processEvent: any): void {\n"
        "        }\n"
        "    }", 1)
    check("classify sees the hand written hook",
          srb.classify(own_hook), "has_own_save_hook")
    try:
        srb.apply_rules(own_hook, [RULE_A], IDENTITY)
        check("apply_rules refuses to merge over it", False, True)
    except ValueError as exc:
        check("apply_rules refuses to merge over it", True, True)
        check("the refusal names the save hook",
              "onBeforeUpdate" in str(exc), True)

    section("8. Braces in strings and comments do not fool the insertion")
    trap = FIXTURE.replace(
        "return new PurchaseOrdersFormHandler(this);",
        'var s = "}";\n'
        "            // }\n"
        "            return new PurchaseOrdersFormHandler(this);")
    merged_trap = srb.apply_rules(trap, [RULE_A], IDENTITY)
    rule_at = merged_trap.index("rule_remarks_required")
    form_at = merged_trap.index("export class PurchaseOrdersFormHandler")
    check("rule lands inside the Maint class, before the FormHandler class",
          rule_at < form_at, True)
    check("trap file still round trips",
          srb.strip_rules(merged_trap) == trap, True)

    section("9. JS side: append only, byte for byte round trip")
    bundle = "var a = 1;\nvar b = 2;\nconsole.log(a + b);\n"
    merged_js = srb.apply_rules_js(bundle, [RULE_A], IDENTITY)
    check("blocks are appended after the whole bundle",
          merged_js.index("// === RULE-JS: remarks-required START ===")
          > merged_js.index("console.log(a + b);"), True)
    check("dispatcher patches through the full module path",
          MODULE_PATH + ".PurchaseOrdersMaintHandler" in merged_js, True)
    check("dispatcher block is present",
          "// === RULE-JS: adaptive-dispatch START ===" in merged_js, True)
    check("prototype method is defined",
          "_cls.prototype.rule_remarks_required = function (eventData) {"
          in merged_js, True)
    check("strip_rules_js(apply_rules_js(bundle)) == bundle byte for byte",
          srb.strip_rules_js(merged_js) == bundle, True)
    check("list_rules_js finds the slug",
          srb.list_rules_js(merged_js), ["remarks-required"])
    no_nl = "var a = 1;\nvar b = 2;"
    check("a bundle without a final newline also round trips",
          srb.strip_rules_js(srb.apply_rules_js(no_nl, [RULE_A], IDENTITY))
          == no_nl, True)

    section("10. compile_check reports a real error with its line number")
    if NODE:
        bad = srb.build_scaffold_ts(IDENTITY).replace(
            "return new PurchaseOrdersFormHandler(this);",
            'var n: number = "text";\n'
            "            return new PurchaseOrdersFormHandler(this);")
        res = srb.compile_check(bad)
        check("a broken file is not ok", res.ok, False)
        check("at least one error line", len(res.errors) >= 1, True)
        check("the error carries a line number",
              any(re.search(r"line \d+:", e) for e in res.errors), True)
    else:
        print("  SKIPPED: node is NOT on PATH. This machine is expected to "
              "have it. Install Node.js to run the real check.")

    section("11. Slug validation")
    for slug in ("Bad_Slug!", "adaptive-dispatch"):
        try:
            srb.ScreenRule(slug=slug, method_ts="x", method_js="x")
            check("rejects slug %r" % slug, False, True)
        except ValueError:
            check("rejects slug %r" % slug, True, True)

    section("12. classify on the fixture and on real logic")
    check("the live fixture (dead console.log included) is scaffold_only",
          srb.classify(FIXTURE), "scaffold_only")
    with_method = FIXTURE.replace(
        "        }\n    }",
        "        }\n\n"
        "        public helper(): void {\n"
        "        }\n"
        "    }", 1)
    check("an extra custom method means has_logic",
          srb.classify(with_method), "has_logic")
    check("a merged file classifies like its stripped self",
          srb.classify(srb.apply_rules(FIXTURE, [RULE_A], IDENTITY)),
          "scaffold_only")

    section("13. Fixture plus a realistic rule compiles clean")
    if NODE:
        merged_real = srb.apply_rules(FIXTURE, [RULE_REAL], IDENTITY)
        res = srb.compile_check(merged_real)
        if not res.ok:
            print("  tsc said: " + "; ".join(res.errors)[:1200])
        check("merged handler compiles clean", res.ok, True)
    else:
        print("  SKIPPED: node is NOT on PATH. This machine is expected to "
              "have it. Install Node.js to run the real check.")

    section("14. Regex literals with braces or quotes do not move the insertion")
    regex_trap = FIXTURE.replace(
        "return new PurchaseOrdersFormHandler(this);",
        'var m = ("x").match(/[}]/);\n'
        "            return new PurchaseOrdersFormHandler(this);")
    merged_rx = srb.apply_rules(regex_trap, [RULE_A], IDENTITY)
    check("rule lands before the FormHandler class despite the regex brace",
          merged_rx.index("rule_remarks_required")
          < merged_rx.index("export class PurchaseOrdersFormHandler"), True)
    check("regex trap file still round trips",
          srb.strip_rules(merged_rx) == regex_trap, True)
    if NODE:
        res = srb.compile_check(merged_rx)
        if not res.ok:
            print("  tsc said: " + "; ".join(res.errors)[:800])
        check("merged regex trap file compiles clean", res.ok, True)
    else:
        print("  SKIPPED compile: node is NOT on PATH.")
    quote_rx = FIXTURE.replace(
        "return new PurchaseOrdersFormHandler(this);",
        'var r = ("x").replace(/"/g, "y");\n'
        "            return new PurchaseOrdersFormHandler(this);")
    merged_qx = srb.apply_rules(quote_rx, [RULE_A], IDENTITY)
    check("rule lands before the FormHandler class despite the regex quote",
          merged_qx.index("rule_remarks_required")
          < merged_qx.index("export class PurchaseOrdersFormHandler"), True)
    check("quote-in-regex file still round trips",
          srb.strip_rules(merged_qx) == quote_rx, True)

    section("15. Marker text inside a user string literal is user data")
    tpl = FIXTURE.replace(
        "return new PurchaseOrdersFormHandler(this);",
        "var help = `\n"
        "// === RULE: fake START ===\n"
        "user text that must survive\n"
        "// === RULE: fake END ===\n"
        "`;\n"
        "            return new PurchaseOrdersFormHandler(this);")
    check("strip_rules leaves the template literal alone",
          srb.strip_rules(tpl) == tpl, True)
    check("list_rules does not see the fake block", srb.list_rules(tpl), [])
    merged_tpl = srb.apply_rules(tpl, [RULE_A], IDENTITY)
    check("user text inside the template survives the merge",
          "user text that must survive" in merged_tpl, True)
    check("template literal file round trips byte for byte",
          srb.strip_rules(merged_tpl) == tpl, True)
    js_tpl = ("var t = `\n"
              "// === RULE-JS: fake START ===\n"
              "bundle bytes that must survive\n"
              "// === RULE-JS: fake END ===\n"
              "`;\n")
    merged_js_tpl = srb.apply_rules_js(js_tpl, [RULE_A], IDENTITY)
    check("JS bundle bytes inside a template literal survive the merge",
          "bundle bytes that must survive" in merged_js_tpl, True)
    check("JS template literal bundle round trips byte for byte",
          srb.strip_rules_js(merged_js_tpl) == js_tpl, True)

    section("16. A marker shaped line inside a rule body is rejected up front")
    evil_ts = ("public rule_evil(eventData: any): any {\n"
               "    // === RULE: evil END ===\n"
               "    return [];\n"
               "}")
    try:
        srb.ScreenRule(slug="evil", method_ts=evil_ts, method_js="return [];")
        check("marker line in method_ts is rejected", False, True)
    except ValueError:
        check("marker line in method_ts is rejected", True, True)
    evil_js = "// === RULE-JS: evil END ===\nreturn [];"
    try:
        srb.ScreenRule(
            slug="evil",
            method_ts="public rule_evil(eventData: any): any { return []; }",
            method_js=evil_js)
        check("marker line in method_js is rejected", False, True)
    except ValueError:
        check("marker line in method_js is rejected", True, True)

    section("17. extract_rules gives back exactly what went in")
    both2 = srb.apply_rules(FIXTURE, [RULE_A, RULE_B], IDENTITY)
    got = srb.extract_rules(both2)
    check("both slugs extracted, dispatcher excluded",
          sorted(got), ["amount-check", "remarks-required"])
    check("method_ts A comes back verbatim",
          got["remarks-required"], RULE_A.method_ts)
    check("method_ts B comes back verbatim",
          got["amount-check"], RULE_B.method_ts)
    check("untouched fixture extracts nothing", srb.extract_rules(FIXTURE), {})

    bundle2 = "var a = 1;\n"
    merged_js2 = srb.apply_rules_js(bundle2, [RULE_A, RULE_B], IDENTITY)
    got_js = srb.extract_rules_js(merged_js2)
    check("JS slugs extracted, dispatcher excluded",
          sorted(got_js), ["amount-check", "remarks-required"])
    check("method_js A comes back verbatim",
          got_js["remarks-required"], RULE_A.method_js)
    check("method_js B comes back verbatim",
          got_js["amount-check"], RULE_B.method_js)
    check("untouched JS bundle extracts nothing",
          srb.extract_rules_js(bundle2), {})

    section("18. Kit path: the merged fixture passes the real QAD check")
    if NODE and KIT_OK:
        merged_real = srb.apply_rules(FIXTURE, [RULE_REAL], IDENTITY)
        res = srb.compile_check(merged_real)
        if not res.ok:
            print("  kit said: " + "; ".join(res.errors)[:1200])
        check("merged handler passes the kit check", res.ok, True)
        check("the kit ran, not the fallback", res.checker, "qad-kit")
    else:
        skip_kit("kit compile")

    section("19. Kit catches what the stub check cannot")
    # The handoff's TS2550 case: Number.isInteger does not exist in QAD's
    # ES5 runtime, and the kit flags it with the same error as the editor.
    rule_es6 = srb.ScreenRule(
        slug="es6-trap",
        method_ts=("public rule_es6_trap(eventData: any): any {\n"
                   "    var bad = Number.isInteger(5);\n"
                   "    var problems = [];\n"
                   "    return problems;\n"
                   "}"),
        method_js=("var bad = Number.isInteger(5);\n"
                   "var problems = [];\n"
                   "return problems;"),
    )
    merged_es6 = srb.apply_rules(FIXTURE, [RULE_REAL, rule_es6], IDENTITY)
    # A hallucinated method on a framework object the stub types as `any`.
    # THIS is the case only the kit can catch: the stub check sees
    # ViewController as any and waves it through, the kit has the real
    # IErrorGroupPanel type from base.json and rejects it (TS2339).
    rule_halluc = srb.ScreenRule(
        slug="halluc-trap",
        method_ts=("public rule_halluc_trap(eventData: any): any {\n"
                   "    this.ViewController.ErrorGroupPanel"
                   ".noSuchPanelMethod();\n"
                   "    return [];\n"
                   "}"),
        method_js="return [];",
    )
    merged_halluc = srb.apply_rules(FIXTURE, [RULE_REAL, rule_halluc],
                                    IDENTITY)
    if NODE and KIT_OK:
        res = srb.compile_check(merged_es6)
        check("kit rejects Number.isInteger", res.ok, False)
        check("an error mentions isInteger",
              any("isInteger" in e for e in res.errors), True)
        res = srb.compile_check(merged_halluc)
        check("kit rejects the hallucinated panel method", res.ok, False)
        check("an error names the missing method",
              any("noSuchPanelMethod" in e for e in res.errors), True)
    else:
        skip_kit("kit error cases")
    if NODE:
        # The same hallucination through the OLD stub check passes, which
        # documents exactly why the kit exists. (Note: the spec expected the
        # stub check to also pass Number.isInteger, but plain tsc at ES5
        # flags that one too; the any-typed framework stubs are the real gap,
        # shown here.)
        old_dir = srb._QAD_KIT_DIR
        srb._QAD_KIT_DIR = Path(tempfile.gettempdir()) / "no-such-kit-dir"
        try:
            res = srb.compile_check(merged_halluc)
        finally:
            srb._QAD_KIT_DIR = old_dir
        check("the stub check misses the hallucinated method (the kit gap)",
              res.ok, True)
        check("that run reports the fallback", res.checker, "stub-fallback")
    else:
        print("  SKIPPED stub comparison: node is NOT on PATH.")

    section("20. Kit catches a method that does not exist on the class")
    if NODE and KIT_OK:
        rule_ghost = srb.ScreenRule(
            slug="ghost-call",
            method_ts=("public rule_ghost_call(eventData: any): any {\n"
                       "    this.someMethodThatDoesNotExist();\n"
                       "    return [];\n"
                       "}"),
            method_js="return [];",
        )
        merged_ghost = srb.apply_rules(FIXTURE, [RULE_REAL, rule_ghost],
                                       IDENTITY)
        res = srb.compile_check(merged_ghost)
        check("kit rejects the missing method call", res.ok, False)
        check("an error names someMethodThatDoesNotExist",
              any("someMethodThatDoesNotExist" in e for e in res.errors),
              True)
    else:
        skip_kit("kit missing-method case")

    section("21. Missing kit falls back to the stub check and says so")
    if NODE:
        merged_real = srb.apply_rules(FIXTURE, [RULE_REAL], IDENTITY)
        old_dir = srb._QAD_KIT_DIR
        srb._QAD_KIT_DIR = Path(tempfile.gettempdir()) / "no-such-kit-dir"
        try:
            res = srb.compile_check(merged_real)
        finally:
            srb._QAD_KIT_DIR = old_dir
        check("fallback is reported", res.checker, "stub-fallback")
        if not res.ok:
            print("  tsc said: " + "; ".join(res.errors)[:800])
        check("merged fixture still passes on the fallback", res.ok, True)
    else:
        print("  SKIPPED: node is NOT on PATH.")

    section("22. A half-installed kit is a broken environment, never a pass")
    if NODE:
        merged_real = srb.apply_rules(FIXTURE, [RULE_REAL], IDENTITY)
        with tempfile.TemporaryDirectory() as tmp:
            half = Path(tmp) / "half_kit"
            half.mkdir()
            # qadCompile.js is there, node_modules is not.
            (half / "qadCompile.js").write_text("// placeholder\n",
                                                encoding="utf-8")
            old_dir = srb._QAD_KIT_DIR
            srb._QAD_KIT_DIR = half
            try:
                res = srb.compile_check(merged_real)
            finally:
                srb._QAD_KIT_DIR = old_dir
        check("a broken kit environment is not a pass", res.ok, False)
        check("the kit path was chosen, not the fallback",
              res.checker, "qad-kit")
        check("the message talks about the environment, not a type error",
              any("environment" in e for e in res.errors), True)
        check("no message looks like a type error line",
              any(re.match(r"^line \d+:", e) for e in res.errors), False)
    else:
        print("  SKIPPED: node is NOT on PATH.")

    return _finish()


def _finish() -> int:
    print()
    if FAILURES:
        print("FAILED: %d check(s) - %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
