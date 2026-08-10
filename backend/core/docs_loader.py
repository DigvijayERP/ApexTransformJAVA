"""
Platform-docs grounding for the prompts.

Loads QAD platform documentation and exposes named bundles for injection into
prompt templates, so generated handler code follows QAD's real APIs instead of
the model's memory of them.

FOUR DIFFERENCES FROM THE AUX REFERENCE IMPLEMENTATION, EACH DELIBERATE

  1. READS .md AS WELL AS .txt. AUX's loader globs `*.txt` only
     (aux_web_version/backend/core/qad_docs_loader.py:92) while every file in
     Adaptive's Docs/ is `.md`. A straight port would have found zero files and
     said nothing about it.

  2. EXPLICIT SOURCES, NOT DIRECTORY-NAME MAGIC. AUX maps a bundle to a list of
     folder NAMES and silently drops any that do not match (:119,
     `if f in self._cache`). A typo in a folder name therefore degrades the
     prompt with no error anywhere. Here a bundle names file patterns, and a
     pattern that matches nothing is reported.

  3. LOUD DIAGNOSTICS. `diagnose()` returns exactly which bundles are empty and
     why. Grounding that silently vanishes is worse than grounding that was
     never configured, because the output still looks plausible.

  4. A SIZE CAP. AUX has none. The class-3 guide alone is 104 KB — roughly
     26,000 tokens — which would crowd out the actual task and cost real money
     on every call. Bundles are capped and truncation is announced in the text
     itself, so the model is never silently handed half a document.

Fail-soft on read errors, like AUX: a missing file logs and is skipped rather
than breaking a run. But unlike AUX, an empty bundle is visible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.logging_setup import get_logger, log_operation

logger = get_logger("adaptive.docs")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

# Where each root lives. `docs` is the platform training guides that ship with
# the repo; `corpus` is an optional richer export (see the note in diagnose()).
ROOTS: Dict[str, Path] = {
    "docs": _REPO_ROOT / "Docs",
    "corpus": _BACKEND_DIR / "qad_docs",
}

READABLE_SUFFIXES = (".md", ".txt")

# ~20k tokens. Sized so every guide in Docs/ fits WHOLE except class 3
# (104 KB, Extensions/Relations/Formulas), which genuinely should be trimmed
# rather than injected entire. Truncating a document by a few hundred bytes
# helps nobody, so the cap sits above the largest one we actually want intact.
DEFAULT_MAX_BYTES = 80_000


@dataclass(frozen=True)
class Bundle:
    """A named set of documents to inject into a prompt."""
    name: str
    why: str
    sources: List[str] = field(default_factory=list)   # "root:glob"
    max_bytes: int = DEFAULT_MAX_BYTES


BUNDLES: Dict[str, Bundle] = {
    "client_extension_event_handler": Bundle(
        name="client_extension_event_handler",
        why="Grounds the event-handler planner and the TypeScript writer (stage 4).",
        sources=[
            "docs:*class_7_Event_Handlers*",
            # The richer AUX-style corpus, if one is ever placed here. Absent by
            # default, and absence is NOT an error for this bundle - it is
            # additive on top of the class-7 guide.
            "corpus:UI Event Handlers/*",
            "corpus:Platform Scripting - TypeScript/*",
        ],
    ),
    "business_component": Bundle(
        name="business_component",
        why="Field design and form building context (stages 2 and 3).",
        sources=["docs:*class_2_Business_Component*"],
    ),
    "lookup_definition": Bundle(
        name="lookup_definition",
        why="The Lookup Definition screens and the worked example (stage 6).",
        sources=["docs:*class_4_More_Platform_Tools*"],
    ),
    "java_extension": Bundle(
        name="java_extension",
        why="Phase 6, server-side JEF. Not used by Case 1.",
        sources=["docs:*class_6_java_extensions*"],
    ),
}

# Sources that are optional enrichment rather than a requirement. A bundle whose
# ONLY sources are optional and all missing is still reported as empty.
_OPTIONAL_ROOTS = {"corpus"}


class DocsLoader:
    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        self._cache: Dict[str, str] = {}
        self._files: Dict[str, List[str]] = {}
        self._loaded = False
        self._max_bytes = max_bytes

    # ── loading ──────────────────────────────────────────────────────────────
    def _resolve(self, source: str) -> List[Path]:
        if ":" not in source:
            logger.warning("Malformed docs source %r - expected 'root:glob'", source)
            return []
        root_name, pattern = source.split(":", 1)
        root = ROOTS.get(root_name)
        if root is None:
            logger.warning("Unknown docs root %r in source %r", root_name, source)
            return []
        if not root.exists():
            return []
        return [p for p in sorted(root.glob(pattern))
                if p.is_file() and p.suffix.lower() in READABLE_SUFFIXES]

    def load(self) -> None:
        self._cache = {}
        self._files = {}
        for bundle in BUNDLES.values():
            texts: List[str] = []
            names: List[str] = []
            for source in bundle.sources:
                for path in self._resolve(source):
                    try:
                        texts.append(path.read_text(encoding="utf-8", errors="replace"))
                    except OSError as exc:
                        logger.warning("Skipping unreadable docs file %s: %s", path, exc)
                        continue
                    names.append(path.name)
            joined = "\n\n".join(texts)
            cap = bundle.max_bytes or self._max_bytes
            if len(joined) > cap:
                logger.warning("Bundle '%s' is %d bytes, truncating to %d",
                               bundle.name, len(joined), cap)
                joined = (joined[:cap] +
                          "\n\n[TRUNCATED - this bundle exceeded the size cap. "
                          "Content past this point was not supplied.]")
            self._cache[bundle.name] = joined
            self._files[bundle.name] = names
        self._loaded = True
        ok = sum(1 for v in self._cache.values() if v)
        log_operation(logger, "docs.load", ok > 0,
                      f"{ok}/{len(BUNDLES)} bundles have content")

    # ── use ──────────────────────────────────────────────────────────────────
    def get_bundle(self, name: str) -> str:
        """Text for a bundle, or "" if it is unknown or empty.

        Never raises: a run continues without grounding rather than failing.
        Whether grounding is actually present is reported by diagnose(), which
        is what the health endpoint should surface.
        """
        if not self._loaded:
            self.load()
        if name not in BUNDLES:
            logger.warning("Unknown docs bundle requested: %s", name)
            return ""
        return self._cache.get(name, "")

    def as_prompt_context(self, name: str) -> str:
        """Bundle text wrapped with the heading the prompts expect, or "" when
        empty — so an absent bundle leaves no dangling heading behind."""
        text = self.get_bundle(name)
        if not text:
            return ""
        return f"## QAD Platform Reference Docs\n\n{text}"

    def files_for(self, name: str) -> List[str]:
        if not self._loaded:
            self.load()
        return list(self._files.get(name, []))

    def is_loaded(self) -> bool:
        return self._loaded

    # ── diagnostics ──────────────────────────────────────────────────────────
    def diagnose(self) -> Dict[str, object]:
        """Exactly which bundles are grounded and which are not.

        This exists because AUX's loader degrades silently: a misspelled folder
        name yields an empty bundle, the prompt renders without its docs, and
        the generated code still looks plausible. An ungrounded run should be
        visible before it produces output, not inferred from bad output.
        """
        if not self._loaded:
            self.load()
        bundles = []
        empty = []
        for name, bundle in BUNDLES.items():
            text = self._cache.get(name, "")
            missing = [s for s in bundle.sources
                       if not self._resolve(s) and s.split(":", 1)[0] not in _OPTIONAL_ROOTS]
            bundles.append({
                "name": name,
                "why": bundle.why,
                "bytes": len(text),
                "files": self._files.get(name, []),
                "missing_sources": missing,
                "grounded": bool(text),
            })
            if not text:
                empty.append(name)
        return {
            "loaded": self._loaded,
            "roots": {k: {"path": str(v), "exists": v.exists()} for k, v in ROOTS.items()},
            "bundles": bundles,
            "ungrounded": empty,
            "all_grounded": not empty,
        }


docs_loader = DocsLoader()
