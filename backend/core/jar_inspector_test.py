"""
Tests for the jar inspector.

Two halves, deliberately:

  PURE      parsing tests that need no jar and no JDK. They run everywhere and
            cover the fiddly parts (generic-aware splitting, type shortening).

  LIVE      inspection against the real dependency jar, SKIPPED with a clear
            message when it is absent. The jar is 3.2 MB and environment
            specific, so it is not committed; skipping is honest where a mock
            would only assert that the mock matches itself.

Run:  python core/jar_inspector_test.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from core import jar_inspector as ji  # noqa: E402

FAILURES: list = []


def check(name, actual, expected):
    if actual == expected:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(name)


def section(title):
    print(f"\n{title}\n" + "-" * len(title))


# Where the jar lands for this project. Absent on a fresh clone, by design.
JAR = Path(r"C:\Users\digvijay.parmar\Desktop\Python_Snake\JAVA_SSS"
           r"\urn_app_com.yash.digwish\lib\qad-ext-dependencies.jar")


def main() -> int:
    section("1. Parameter splitting respects generics")
    # A naive split on "," breaks InputOutput<X> into two bogus parameters, and
    # the whole WithConfirmation detection rests on reading these correctly.
    check("plain single param",
          ji._split_params("com.qad.Foo"), ["com.qad.Foo"])
    check("two plain params",
          ji._split_params("com.qad.Foo, com.qad.Bar"), ["com.qad.Foo", "com.qad.Bar"])
    check("generic param is not split at its comma",
          ji._split_params("com.qad.Foo, com.qad.ipc.dto.InputOutput<com.qad.Conf>"),
          ["com.qad.Foo", "com.qad.ipc.dto.InputOutput<com.qad.Conf>"])
    check("empty list", ji._split_params(""), [])

    section("2. Type names shorten for humans, without losing shape")
    check("plain class", ji._simple("java.lang.String"), "String")
    check("generic", ji._simple("com.qad.ipc.dto.InputOutput<com.qad.x.FooDataSet>"),
          "InputOutput<FooDataSet>")
    check("array", ji._simple("com.qad.x.FooRecord[]"), "FooRecord[]")
    check("primitive untouched", ji._simple("void"), "void")

    section("3. Member regex reads real javap output")
    lines = [
        "  public void create(com.qad.p.FooDataSet) throws com.qad.ipc.dto.BCExecutionError;",
        "  public void createWithConfirmation(com.qad.p.FooDataSet, "
        "com.qad.ipc.dto.InputOutput<com.qad.p.FooConfDataSet>) throws com.qad.ipc.dto.BCExecutionError;",
        "  public java.lang.String getRemarks();",
        "  public com.qad.p.FooRecord[] getTtFoo();",
        "  protected void notPublic();",
    ]
    matched = [m for m in (ji._MEMBER.match(l) for l in lines) if m]
    check("four public members matched, protected ignored", len(matched), 4)
    check("method name", matched[0].group("name"), "create")
    check("throws captured", matched[0].group("throws").strip(),
          "com.qad.ipc.dto.BCExecutionError")
    check("array return type", matched[3].group("returns"), "com.qad.p.FooRecord[]")

    section("4. SavePath classifies correctly")
    plain = ji.SavePath(name="create", param_types=["com.qad.p.FooDataSet"],
                        returns="void", throws="", root="create", with_confirmation=False)
    wrapped = ji.SavePath(
        name="create", param_types=["com.qad.ipc.dto.InputOutput<com.qad.p.FooDataSet>"],
        returns="void", throws="", root="create", with_confirmation=False)
    fetch = ji.SavePath(name="fetch", param_types=["java.lang.String"],
                        returns="void", throws="", root="fetch", with_confirmation=False)
    check("create is mutating", plain.mutating, True)
    check("fetch is not mutating", fetch.mutating, False)
    check("bare DataSet is not io-wrapped", plain.takes_input_output, False)
    check("InputOutput<> is io-wrapped", wrapped.takes_input_output, True)

    if not JAR.is_file():
        print(f"\nSKIPPED sections 5-6: no dependency jar at\n  {JAR}")
        print("Fetch it with the jef.dependency_jar endpoint to run them.")
    else:
        ok, detail = ji.toolchain_ready()
        if not ok:
            print(f"\nSKIPPED sections 5-6: no JDK on PATH ({detail})")
        else:
            section("5. Live: the standard-vs-generated distinction")
            # THE regression that matters. Overriding only create/update on a
            # coded BC deploys cleanly and never fires (observed 2026-08-14).
            po = ji.inspect(JAR, "PurchaseOrderHeader")
            check("standard BC is not app-owned", po.is_app_owned, False)
            check("standard BC HAS confirmation variants",
                  po.has_confirmation_variants, True)
            check("standard BC exposes 6 mutating paths", len(po.mutating_paths), 6)
            check("standard create takes a BARE DataSet",
                  [p.takes_input_output for p in po.mutating_paths if p.name == "create"],
                  [False])
            check("record derived, not assumed", po.record.endswith("PurchaseOrderHeaderRecord"), True)
            check("accessor derived", po.accessor, "getTtPurchaseOrderHeader")
            check("the remarks field is found",
                  [(f.getter, f.simple_type) for f in po.fields if f.name == "remarks"],
                  [("getRemarks", "String")])

            ours = ji.inspect(JAR, "DigSmokeTest")
            check("generated BC is app-owned", ours.is_app_owned, True)
            check("generated BC has NO confirmation variants",
                  ours.has_confirmation_variants, False)
            check("generated BC exposes 3 mutating paths", len(ours.mutating_paths), 3)
            check("generated create is io-WRAPPED",
                  [p.takes_input_output for p in ours.mutating_paths if p.name == "create"],
                  [True])
            check("its SQL-safe rename survives into Java",
                  sorted(f.name for f in ours.fields),
                  ["description", "statusCode", "testCode", "testDate"])
            check("a date field maps to LocalDate",
                  [f.simple_type for f in ours.fields if f.name == "testDate"], ["LocalDate"])

            section("6. Live: listing and lookup failures are helpful")
            comps = ji.list_components(JAR)
            check("the jar exposes many components", len(comps) > 200, True)
            check("app-owned components sort first",
                  comps[0].is_app_owned, True)
            try:
                ji.find(JAR, "NoSuchComponentAnywhere")
                check("unknown BC raises", False, True)
            except ji.JarInspectionError as exc:
                check("unknown BC raises", "No BaseService" in str(exc), True)
            try:
                ji.find(JAR, "PurchaseOrderHead")
                check("near-miss suggests alternatives", False, True)
            except ji.JarInspectionError as exc:
                check("near-miss suggests alternatives", "Did you mean" in str(exc), True)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
