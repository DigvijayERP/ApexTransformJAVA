"""
Drives Maven in the JEF workspace, and never believes it.

WHY EVERY RESULT HERE IS CHECKED AGAINST THE FILESYSTEM

The QAD VS Code plugin resolves its Maven task as successful whenever the task
FINISHES, regardless of exit code. That produced a cheerful "Updating the
dependencies is successfully completed" while `mvn install:install-file` had
actually failed; Maven then cached the failed resolution and every later build
died with "was not found ... this failure was cached in the local repository".
This project hit exactly that: on 2026-08-13 the owner's local repository held
only `.lastUpdated` markers pointing at Maven Central, and they had to be
cleared before anything would build.

So: exit codes are checked, the produced artifact is confirmed on disk and
opened, and a poisoned cache is detected and cleared rather than reported.

AUX reached the same conclusion for its TypeScript build - `sss/compile.py:101`
fails unless the compiler exits zero AND the expected files exist. Same
instinct, different toolchain.

WHOLE-JAR SEMANTICS

`mvn clean package` compiles everything under src/main/java into ONE jar, and
uploading that jar REPLACES the deployed set entirely (proven live 2026-08-14:
a class absent from the new jar stops firing). So the sources present in the
workspace at build time ARE the deployment. That is why this module offers
source listing and removal: deleting a validation is "rebuild without it".

⚠️ AUX's `_clean_stale_ts` deletes every source but the one being compiled
(sss/compile.py:77-85). Do NOT port that idea here - under whole-jar semantics
it would silently erase every other deployed extension.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from core.logging_setup import get_logger

logger = get_logger("adaptive.maven")

DEPENDENCY_ARTIFACT = "ext-dependencies"
DEPENDENCY_VERSION = "1.0"
DEPENDENCY_JAR_NAME = "qad-ext-dependencies.jar"


class MavenError(RuntimeError):
    """A build step failed, or the workspace is not usable."""


# javac errors reach us through Maven as, e.g.
#   [ERROR] /C:/.../src/main/java/com/yash/digwish/Foo.java:[73,50] incompatible
#           types: Integer cannot be converted to String
# The absolute path is ~110 characters of noise before the part that matters.
_COMPILE_ERROR = re.compile(
    r"^\[ERROR\]\s+(?P<path>[^\s\[]+\.java):\[(?P<line>\d+),(?P<col>\d+)\]\s+(?P<msg>.+)$")


@dataclass
class CompileError:
    file: str        # bare file name; the workspace path adds nothing
    line: int
    column: int
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column} {self.message}"


@dataclass
class BuildResult:
    ok: bool
    jar: Optional[Path]
    classes: List[str]
    exit_code: int
    log_tail: str

    def compile_errors(self) -> List[CompileError]:
        """javac's complaints, deduplicated and stripped of path noise.

        Maven repeats each error (once inline, once in the summary), so the
        same problem would otherwise be shown to the user twice.
        """
        seen, out = set(), []
        for line in self.log_tail.splitlines():
            m = _COMPILE_ERROR.match(line.strip())
            if not m:
                continue
            err = CompileError(
                file=Path(m.group("path")).name,
                line=int(m.group("line")),
                column=int(m.group("col")),
                message=m.group("msg").strip(),
            )
            key = (err.file, err.line, err.column, err.message)
            if key not in seen:
                seen.add(key)
                out.append(err)
        return out

    def summary(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "jar": str(self.jar) if self.jar else None,
            "jar_bytes": self.jar.stat().st_size if self.jar and self.jar.is_file() else 0,
            "classes": self.classes,
            "class_count": len(self.classes),
            "exit_code": self.exit_code,
            "compile_errors": [str(e) for e in self.compile_errors()],
        }


# ── workspace ────────────────────────────────────────────────────────────────
@dataclass
class Workspace:
    """A JEF project folder: the one containing pom.xml."""
    root: Path

    @property
    def pom(self) -> Path:
        return self.root / "pom.xml"

    @property
    def lib(self) -> Path:
        return self.root / "lib"

    @property
    def source_root(self) -> Path:
        return self.root / "src" / "main" / "java"

    @property
    def target(self) -> Path:
        return self.root / "target"

    def problems(self) -> List[str]:
        """What is missing. Empty means usable."""
        out = []
        if not self.root.is_dir():
            return [f"No such folder: {self.root}. Set JEF_WORKSPACE_DIR to the folder "
                    f"containing pom.xml (the plugin names it urn_app_<fullAppName>)."]
        if not self.pom.is_file():
            out.append(f"No pom.xml in {self.root}. This is not a JEF workspace. If the "
                       f"folder holds qad-sss.config.json instead of qad-sse.config.json, "
                       f"it was scaffolded by the wrong plugin.")
        if not self.source_root.is_dir():
            out.append(f"No src/main/java in {self.root}.")
        return out

    def require(self) -> None:
        problems = self.problems()
        if problems:
            raise MavenError(" ".join(problems))

    def final_name(self) -> Optional[str]:
        """<finalName> from the pom, which decides the built jar's name."""
        if not self.pom.is_file():
            return None
        m = re.search(r"<finalName>\s*([^<\s]+)\s*</finalName>",
                      self.pom.read_text(encoding="utf-8", errors="replace"))
        return m.group(1) if m else None

    def expected_jar(self) -> Optional[Path]:
        name = self.final_name()
        return self.target / f"{name}.jar" if name else None

    def group_id(self) -> Optional[str]:
        m = re.search(r"<groupId>\s*([^<\s]+)\s*</groupId>",
                      self.pom.read_text(encoding="utf-8", errors="replace"))
        return m.group(1) if m else None


# ── sources ──────────────────────────────────────────────────────────────────
def list_sources(ws: Workspace) -> List[Path]:
    """Every .java in the workspace, relative to src/main/java.

    This IS the deployment set: whatever is here ends up in the jar, and
    whatever is not here is removed from QAD on the next deploy.
    """
    ws.require()
    if not ws.source_root.is_dir():
        return []
    return sorted(p.relative_to(ws.source_root) for p in ws.source_root.rglob("*.java"))


def write_source(ws: Workspace, relative_path: str, source: str) -> Path:
    ws.require()
    target = ws.source_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    logger.info("[MVN] wrote %s (%d bytes)", relative_path, len(source))
    return target


def remove_source(ws: Workspace, relative_path: str) -> bool:
    """Delete one source. Returns False if it was not there.

    Deliberately removes ONLY the named file: under whole-jar semantics a
    broader sweep would silently un-deploy unrelated extensions.
    """
    ws.require()
    target = ws.source_root / relative_path
    if not target.is_file():
        return False
    target.unlink()
    logger.info("[MVN] removed %s", relative_path)
    # Tidy now-empty package folders, but never the source root itself.
    parent = target.parent
    while parent != ws.source_root and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent
    return True


# ── running maven ────────────────────────────────────────────────────────────
def mvn_executable() -> Optional[str]:
    """The absolute path to Maven's launcher.

    On Windows `mvn` is `mvn.cmd`, and subprocess does NOT apply PATHEXT the
    way a shell does: passing the bare name raises WinError 2 even though the
    same word works in a terminal. shutil.which does consult PATHEXT, so
    resolving here keeps the call shell-free (no quoting hazards) and portable.
    """
    return shutil.which("mvn")


def _mvn(ws: Workspace, args: List[str], timeout: int = 900) -> subprocess.CompletedProcess:
    exe = mvn_executable()
    if not exe:
        raise MavenError(
            "'mvn' is not on PATH. Case 3 needs Maven (3.9 verified) and a JDK. "
            "Note VS Code caches PATH per terminal: a fully restarted terminal may be "
            "needed after installing it.")
    try:
        return subprocess.run([exe, *args], cwd=str(ws.root), capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise MavenError(f"Maven timed out after {timeout}s") from exc


def local_repo_path(group_id: str) -> Path:
    home = Path.home() / ".m2" / "repository"
    return home.joinpath(*group_id.split(".")) / DEPENDENCY_ARTIFACT / DEPENDENCY_VERSION


def dependency_installed(group_id: str) -> bool:
    """Real artifacts present, not just failure markers.

    A failed resolution leaves only `.lastUpdated` files, which Maven then
    serves from cache. Checking for the jar and pom specifically is the
    difference between "installed" and "known to be broken".
    """
    d = local_repo_path(group_id)
    return (d / f"{DEPENDENCY_ARTIFACT}-{DEPENDENCY_VERSION}.jar").is_file() and \
           (d / f"{DEPENDENCY_ARTIFACT}-{DEPENDENCY_VERSION}.pom").is_file()


def clear_poisoned_cache(group_id: str) -> int:
    """Remove cached-failure markers so Maven will retry the resolution."""
    d = local_repo_path(group_id)
    if not d.is_dir():
        return 0
    stale = list(d.glob("*.lastUpdated"))
    for f in stale:
        f.unlink()
    if stale:
        logger.warning("[MVN] cleared %d cached-failure marker(s) in %s", len(stale), d)
    return len(stale)


def install_dependency_jar(ws: Workspace, jar: Optional[Path] = None) -> Path:
    """Install QAD's dependency jar into the local repo, verifying afterwards.

    `jar` defaults to lib/qad-ext-dependencies.jar, which is where the plugin's
    "Update app dependency" leaves it and where our own fetch should write it.
    """
    ws.require()
    group = ws.group_id()
    if not group:
        raise MavenError(f"No <groupId> in {ws.pom}")
    jar = Path(jar) if jar else ws.lib / DEPENDENCY_JAR_NAME
    if not jar.is_file():
        raise MavenError(
            f"No dependency jar at {jar}. Fetch it from QAD first "
            f"(jef.dependency_jar returns application/java-archive).")

    # Always clear first: a cached failure would otherwise defeat the install.
    clear_poisoned_cache(group)

    proc = _mvn(ws, ["install:install-file", f"-Dfile={jar}", f"-DgroupId={group}",
                     f"-DartifactId={DEPENDENCY_ARTIFACT}",
                     f"-Dversion={DEPENDENCY_VERSION}", "-Dpackaging=jar"])
    if proc.returncode != 0:
        raise MavenError(
            f"mvn install-file failed (exit {proc.returncode}):\n"
            + _tail(proc.stdout, proc.stderr))

    # The plugin trusted a zero-ish outcome here and was wrong. Confirm on disk.
    if not dependency_installed(group):
        raise MavenError(
            f"Maven reported success but {local_repo_path(group)} does not contain "
            f"{DEPENDENCY_ARTIFACT}-{DEPENDENCY_VERSION}.jar and .pom. This is the "
            f"failure mode that silently breaks later builds.")
    logger.info("[MVN] dependency installed for %s", group)
    return local_repo_path(group)


def package(ws: Workspace, ensure_dependency: bool = True) -> BuildResult:
    """`mvn clean package`, verified against the filesystem.

    Local and free: this is the strongest rehearsal available before anything
    is sent to QAD, because it proves the generated Java actually compiles
    against the real platform types.
    """
    ws.require()
    group = ws.group_id()
    if ensure_dependency and group and not dependency_installed(group):
        logger.info("[MVN] dependency missing for %s; installing", group)
        install_dependency_jar(ws)

    proc = _mvn(ws, ["clean", "package"])
    tail = _tail(proc.stdout, proc.stderr)

    if proc.returncode != 0:
        return BuildResult(ok=False, jar=None, classes=[], exit_code=proc.returncode,
                           log_tail=tail)

    jar = ws.expected_jar()
    if not jar or not jar.is_file():
        # Exit zero without the artifact: precisely what "trust the message"
        # would have missed.
        return BuildResult(
            ok=False, jar=None, classes=[], exit_code=proc.returncode,
            log_tail=f"Maven exited 0 but no jar at {jar}.\n\n{tail}")

    classes = jar_classes(jar)
    logger.info("[MVN] built %s (%d bytes, %d class(es))", jar.name,
                jar.stat().st_size, len(classes))
    return BuildResult(ok=True, jar=jar, classes=classes,
                       exit_code=proc.returncode, log_tail=tail)


def jar_classes(jar: Path) -> List[str]:
    """Fully-qualified class names inside a jar, inner classes excluded."""
    with zipfile.ZipFile(jar) as z:
        return sorted(
            n[:-len(".class")].replace("/", ".")
            for n in z.namelist()
            if n.endswith(".class") and "$" not in n
        )


def _tail(stdout: str, stderr: str, lines: int = 40) -> str:
    """The end of a Maven log: where the reason lives."""
    blob = (stdout or "") + ("\n" + stderr if stderr else "")
    kept = [l for l in blob.splitlines() if l.strip()]
    return "\n".join(kept[-lines:])


def toolchain_ready() -> tuple[bool, str]:
    """Is Maven reachable, and which JDK does it use? Reported, never assumed."""
    exe = mvn_executable()
    if not exe:
        return False, "'mvn' is not on PATH"
    try:
        proc = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=120)
    except Exception as exc:  # noqa: BLE001
        return False, f"mvn -version failed: {exc}"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "").strip()[:200]
    first = (proc.stdout or "").splitlines()
    java = next((l for l in first if l.startswith("Java version:")), "")
    return True, "; ".join(x for x in (first[0] if first else "", java) if x)
