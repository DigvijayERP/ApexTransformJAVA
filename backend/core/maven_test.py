"""
Tests for the Maven runner.

The live sections drive the REAL workspace: generate a class, write it, build,
then remove it and build again. That last pair is exactly how "delete a
validation" works, so it is tested as a first-class path rather than an
afterthought.

Nothing here deploys. Every step is local.

Run:  python core/maven_test.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from core import jar_inspector as ji   # noqa: E402
from core import maven                 # noqa: E402
from builders import extension_builder as eb  # noqa: E402

FAILURES: list = []


def check(name, actual, expected):
    if actual == expected:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}\n          expected: {expected!r}\n          actual:   {actual!r}")
        FAILURES.append(name)


def section(title):
    print(f"\n{title}\n" + "-" * len(title))


WS_ROOT = Path(r"C:\Users\digvijay.parmar\Desktop\Python_Snake\JAVA_SSS"
               r"\urn_app_com.yash.digwish")
PROBE_CLASS = "MavenTestProbe"


def main() -> int:
    section("1. A bad workspace is diagnosed, not crashed into")
    missing = maven.Workspace(Path("/definitely/not/here"))
    check("nonexistent root reports a problem", len(missing.problems()) >= 1, True)
    check("and names the setting", "JEF_WORKSPACE_DIR" in " ".join(missing.problems()), True)
    try:
        maven.list_sources(missing)
        check("using it raises", False, True)
    except maven.MavenError:
        check("using it raises", True, True)

    section("2. Compile errors are parsed out of Maven's noise")
    fake = maven.BuildResult(
        ok=False, jar=None, classes=[], exit_code=1,
        log_tail=(
            "[INFO] Compiling 1 source file\n"
            "[ERROR] /C:/very/long/path/src/main/java/com/yash/digwish/Foo.java:[73,50] "
            "incompatible types: java.lang.Integer cannot be converted to java.lang.String\n"
            "[ERROR] /C:/very/long/path/src/main/java/com/yash/digwish/Foo.java:[73,50] "
            "incompatible types: java.lang.Integer cannot be converted to java.lang.String\n"
            "[ERROR] BUILD FAILURE\n"))
    errs = fake.compile_errors()
    check("duplicates collapsed", len(errs), 1)
    check("path noise stripped", errs[0].file, "Foo.java")
    check("line and column kept", (errs[0].line, errs[0].column), (73, 50))
    check("message intact", "cannot be converted" in errs[0].message, True)
    check("non-compile ERROR lines ignored",
          any("BUILD FAILURE" in e.message for e in errs), False)

    ok, detail = maven.toolchain_ready()
    if not ok:
        print(f"\nSKIPPED sections 3-5: Maven unavailable ({detail})")
        return _finish()
    ws = maven.Workspace(WS_ROOT)
    if ws.problems():
        print(f"\nSKIPPED sections 3-5: {' '.join(ws.problems())}")
        return _finish()
    jar = ws.lib / maven.DEPENDENCY_JAR_NAME
    if not jar.is_file():
        print(f"\nSKIPPED sections 3-5: no dependency jar at {jar}")
        return _finish()

    section("3. The workspace reads its own pom, never a hardcoded name")
    check("groupId read", ws.group_id(), "com.yash.digwish")
    check("finalName read", ws.final_name(), "com.yash.digwish-ext-cust")
    check("expected jar derived from finalName",
          ws.expected_jar().name, "com.yash.digwish-ext-cust.jar")
    check("dependency verified by artifacts, not markers",
          maven.dependency_installed(ws.group_id()), True)

    before = set(maven.list_sources(ws))

    section("4. Generate, write, build")
    bc = ji.inspect(jar, "DigSmokeTest")
    built = eb.build_extension_source(bc, eb.ValidationSpec(
        class_name=PROBE_CLASS,
        description="Temporary probe written by maven_test. Never deployed.",
        body='String d = record.getDescription();\n'
             'if (d != null && d.length() > 4000) {\n'
             '    addValidationError("Description is too long.");\n'
             '}'))
    maven.write_source(ws, built["relative_path"], built["source"])
    check("source appears in the deployment set",
          built["relative_path"].replace("/", "\\") in
          [str(p) for p in maven.list_sources(ws)], True)

    result = maven.package(ws)
    check("build succeeds", result.ok, True)
    check("exit code checked, not assumed", result.exit_code, 0)
    check("jar verified on disk", result.jar.is_file(), True)
    check("the probe is in the jar",
          f"com.yash.digwish.{PROBE_CLASS}" in result.classes, True)
    check("no compile errors reported", result.compile_errors(), [])

    section("5. Remove and rebuild — this is how DELETE works")
    # Removal must take out exactly one file. Under whole-jar semantics a
    # broader sweep would silently un-deploy every other extension.
    check("removing a source reports success",
          maven.remove_source(ws, built["relative_path"]), True)
    check("removing it twice is honest about the second time",
          maven.remove_source(ws, built["relative_path"]), False)
    after_build = maven.package(ws)
    check("rebuild still succeeds", after_build.ok, True)
    check("the probe is GONE from the jar",
          f"com.yash.digwish.{PROBE_CLASS}" in after_build.classes, False)
    check("and nothing else was disturbed", set(maven.list_sources(ws)), before)

    return _finish()


def _finish() -> int:
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s) — {', '.join(FAILURES)}")
        return 1
    print("All checks passed. Nothing was deployed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
