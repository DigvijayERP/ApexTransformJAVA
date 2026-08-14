"""
Tests for the extension source generator.

The live sections regenerate the two classes that were hand-written, deployed
and OBSERVED WORKING against QAD on 2026-08-14, then compile them with javac
against the real dependency jar. That is the strongest check available short of
deploying: known-good targets, real types, a real compiler.

Skipped with a clear message when the jar or a JDK is absent.

Run:  python builders/extension_builder_test.py
"""
from __future__ import annotations

import io
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from core import jar_inspector as ji           # noqa: E402
from builders import extension_builder as eb   # noqa: E402

FAILURES: list = []


def check(name, actual, expected):
    if actual == expected:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(name)


def section(title):
    print(f"\n{title}\n" + "-" * len(title))


JAR = Path(r"C:\Users\digvijay.parmar\Desktop\Python_Snake\JAVA_SSS"
           r"\urn_app_com.yash.digwish\lib\qad-ext-dependencies.jar")

REMARKS_BODY = (
    'String remarks = record.getRemarks();\n'
    'if (remarks == null || remarks.trim().isEmpty()) {\n'
    '    addValidationError("Remarks is required on a Purchase Order.");\n'
    '}'
)


def main() -> int:
    section("1. Specs are validated before anything is generated")
    for bad, why in [("", "empty"), ("lowercase", "not PascalCase"), ("9Bad", "leading digit")]:
        try:
            eb.ValidationSpec(class_name=bad, description="d", body="x;").sanity()
            check(f"rejects class name {why}", False, True)
        except eb.ExtensionBuildError:
            check(f"rejects class name {why}", True, True)
    try:
        eb.ValidationSpec(class_name="Ok", description="d", body="   ").sanity()
        check("rejects an empty body", False, True)
    except eb.ExtensionBuildError:
        check("rejects an empty body", True, True)

    if not JAR.is_file():
        print(f"\nSKIPPED sections 2-4: no dependency jar at\n  {JAR}")
        print("Fetch it with the jef.dependency_jar endpoint to run them.")
        return _finish()

    ok, detail = ji.toolchain_ready()
    if not ok:
        print(f"\nSKIPPED sections 2-4: no JDK on PATH ({detail})")
        return _finish()

    po = ji.inspect(JAR, "PurchaseOrderHeader")
    ours = ji.inspect(JAR, "DigSmokeTest")

    section("2. Every save path is covered by default")
    built = eb.build_extension_source(po, eb.ValidationSpec(
        class_name="PurchaseOrderRemarksValidation",
        description="Requires a non-blank Remarks on a Purchase Order header.",
        body=REMARKS_BODY))
    s = built["summary"]
    check("all six PO mutating paths guarded", len(s["guarded_paths"]), 6)
    check("confirmation variants are covered", s["covers_confirmation_variants"], True)
    check("no warnings when everything is covered", built["warnings"], [])
    src = built["source"]
    check("package has no BC segment", "package com.yash.digwish;" in src, True)
    check("bare DataSet param is passed straight through",
          "validate(dataSet);" in src, True)
    check("confirmation param is passed to super untouched",
          "super.createWithConfirmation(dataSet, confirmation);" in src, True)
    check("the template owns the throw",
          src.count("throwAddedValidationErrors();"), 1)

    section("3. THE SILENT-FAILURE GUARD")
    # Overriding only create/update on a coded BC compiles, deploys, returns
    # 200 and never fires. The generator must say so, loudly.
    partial = eb.build_extension_source(po, eb.ValidationSpec(
        class_name="PartialValidation", description="d", body=REMARKS_BODY,
        guarded_paths=["create", "update"]))
    check("partial coverage produces warnings", len(partial["warnings"]) >= 1, True)
    check("it names the unguarded paths",
          any("createWithConfirmation" in w for w in partial["warnings"]), True)
    check("it warns the rule will likely never fire",
          any("never fire" in w for w in partial["warnings"]), True)
    # The same partial selection on a generated BC is complete, so silent.
    ours_partial = eb.build_extension_source(ours, eb.ValidationSpec(
        class_name="OursValidation", description="d",
        body='addValidationError("x");', guarded_paths=["create", "update"]))
    check("no false alarm on a BC that has no confirmation variants",
          any("never fire" in w for w in ours_partial["warnings"]), False)

    section("4. Generated sources COMPILE against the real jar")
    ours_built = eb.build_extension_source(ours, eb.ValidationSpec(
        class_name="DigSmokeTestValidation",
        description="Requires a non-blank Description on a smoke test.",
        body='String description = record.getDescription();\n'
             'if (description == null || description.trim().isEmpty()) {\n'
             '    addValidationError("Description is required.");\n'
             '}'))
    check("io-wrapped DataSet is unwrapped with getValue()",
          "validate(io.getValue());" in ours_built["source"]
          or "validate(dataSet.getValue());" in ours_built["source"], True)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg_dir = root / "src" / "com" / "yash" / "digwish"
        pkg_dir.mkdir(parents=True)
        for b in (built, ours_built):
            (pkg_dir / f"{b['class_name']}.java").write_text(b["source"], encoding="utf-8")
        sources = [str(p) for p in pkg_dir.glob("*.java")]
        proc = subprocess.run(
            ["javac", "-cp", str(JAR), "-d", str(root / "out"), *sources],
            capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            print("  javac said:\n" + (proc.stderr or "")[:1500])
        check("javac compiles both generated classes", proc.returncode, 0)
        check("both class files produced",
              len(list((root / "out").rglob("*.class"))), 2)

    return _finish()


def _finish() -> int:
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
