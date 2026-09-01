"""
Case 4 merge engine: put save-time validation rules into a QAD screen event
handler without touching any code the user wrote.

HOW THE MERGE WORKS

A QAD screen has one TypeScript event handler per (app, view, timing). Each
rule we add lives between marker comments, so we can find, replace and remove
our own blocks later. Everything outside our markers is preserved byte for
byte, including line endings (input may be CRLF and is never normalized).

TS side: rule blocks plus one dispatcher block are inserted into the body of
the <View>MaintHandler class, right before its closing brace. The brace search
ignores braces inside string literals and comments, because a stray "}" in a
string or a comment must not move the insertion point.

JS side: the stored JavaScript is a compiled bundle we cannot rebuild, so we
only APPEND blocks at the end. Exported classes are attached to the namespace
object (confirmed live 2026-08-31), so an appended IIFE can reach
<module_path>.<View>MaintHandler and patch its prototype.

THE DISPATCHER

One reserved block (slug 'adaptive-dispatch') defines onBeforeUpdate. It calls
every rule method in slug order, collects the problems, and only if there are
any does it block the save and drive the error grid. The dispatcher is
regenerated from the current rule list on every apply. Nothing ever wraps or
chains a previous onBeforeUpdate, which is what makes re-runs idempotent.

Rule methods themselves never touch the error panel. They take eventData and
return a list of {message, fieldName} problem objects; an empty list means the
rule passed.

All generated code is plain ES5 (var, no arrow functions, no let/const, no
template strings) so the JS mirror of a TS method body is the same text.

See PHASE5_CASE4_BUILD_PLAN.md for the full design and the evidence behind it.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# The real TypeScript compiler, relative to this file. On Windows a bare
# command name does not resolve the way a shell resolves it, so node is found
# with shutil.which and tsc is run as a script file (same lesson as
# core/maven.py).
_TSC_JS = (Path(__file__).resolve().parents[2]
           / "frontend" / "node_modules" / "typescript" / "lib" / "tsc.js")

# The vendored QAD compile kit (see backend/qad_compile/README.md). When it is
# installed it is the primary check, because it uses QAD's real typings. The
# any-typed stub check below stays as the last resort. Tests monkeypatch this
# path to force the fallback.
_QAD_KIT_DIR = Path(__file__).resolve().parents[1] / "qad_compile"

DISPATCH_SLUG = "adaptive-dispatch"

_SLUG_RE = re.compile(r"[a-z0-9-]+")
_TS_MARK = re.compile(r"// === RULE: ([a-z0-9-]+) (START|END) ===")
_JS_MARK = re.compile(r"// === RULE-JS: ([a-z0-9-]+) (START|END) ===")

# One tsc error line, e.g.  handler.ts(21,17): error TS2322: Type ...
_TSC_ERR = re.compile(
    r"^(?P<file>\S+?)\((?P<line>\d+),\d+\):\s+error\s+TS\d+:\s+(?P<msg>.*)$")


def _check_slug(slug: str) -> None:
    if not _SLUG_RE.fullmatch(slug or ""):
        raise ValueError(
            "Rule slug %r is not allowed. Use only lowercase letters, digits "
            "and hyphens." % (slug,))
    if slug == DISPATCH_SLUG:
        raise ValueError(
            "The slug '%s' is reserved for the dispatcher. Pick a different "
            "slug." % DISPATCH_SLUG)


@dataclass(frozen=True)
class ScreenRule:
    """One validation rule.

    method_ts is the full TypeScript method source, named rule_<slug with
    underscores>. method_js is the same method body as plain ES5 statements;
    apply_rules_js wraps it in the prototype assignment itself.
    """
    slug: str
    method_ts: str
    method_js: str

    def __post_init__(self) -> None:
        _check_slug(self.slug)
        if self.method_name not in (self.method_ts or ""):
            raise ValueError(
                "The TS method for rule '%s' must be named %s."
                % (self.slug, self.method_name))
        for field_name, src in (("method_ts", self.method_ts),
                                ("method_js", self.method_js)):
            for ln in (src or "").splitlines():
                s = ln.strip()
                if _TS_MARK.fullmatch(s) or _JS_MARK.fullmatch(s):
                    raise ValueError(
                        "The %s of rule '%s' contains a line that looks like "
                        "a rule marker comment. Marker lines are not allowed "
                        "inside a rule body, because they would break the "
                        "merged file." % (field_name, self.slug))

    @property
    def method_name(self) -> str:
        return "rule_" + self.slug.replace("-", "_")


@dataclass(frozen=True)
class HandlerIdentity:
    """Which handler we are talking to, e.g. PurchaseOrders BEFORE."""
    view_pascal: str      # "PurchaseOrders"
    view_namespace: str   # "com.qad.erp.purchasing"
    app_pascal: str       # "ComYashDigwish"
    timing: str           # "BEFORE"

    @property
    def module_path(self) -> str:
        return "%s.EventHandler.%s.%s.Maint_%s" % (
            self.view_namespace, self.view_pascal, self.app_pascal, self.timing)


@dataclass(frozen=True)
class CompileResult:
    ok: bool
    errors: List[str]
    # Which check produced this verdict: "qad-kit" when the vendored QAD kit
    # ran (real typings), "stub-fallback" when only the any-typed stubs did.
    checker: str = "stub-fallback"


# ── text scanning ────────────────────────────────────────────────────────────
# Words after which a '/' starts a regex literal, not a division.
_REGEX_PREFIX_WORDS = frozenset((
    "return", "typeof", "instanceof", "in", "of", "new", "delete", "void",
    "throw", "case", "do", "else", "yield", "await"))


def _regex_ahead(out: List[str], i: int) -> bool:
    """True when a '/' at position i starts a regex literal.

    Judged by what comes before it in the masked-so-far text: after a value
    (a name, a number, ')', ']' or a closing quote) a '/' is division;
    anywhere else it starts a regex."""
    j = i - 1
    while j >= 0 and out[j] in " \t\r\n":
        j -= 1
    if j < 0:
        return True
    c = out[j]
    if c.isalnum() or c == "_":
        k = j
        while k >= 0 and (out[k].isalnum() or out[k] == "_"):
            k -= 1
        return "".join(out[k + 1:j + 1]) in _REGEX_PREFIX_WORDS
    return c not in ')]"\'`'


def _mask(text: str, keep_comments: bool = False) -> str:
    """Same text, same length, but the INSIDES of string literals, comments
    and regex literals are replaced with spaces. Braces, quotes and marker
    text hidden in them then cannot fool the brace counter, the classifier
    or the marker scanner.

    With keep_comments=True the comment text stays visible. That is used to
    tell a real marker comment line from marker shaped text pasted inside a
    string literal."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in ('"', "'", "`"):
            quote = c
            i += 1
            while i < n:
                if text[i] == "\\":
                    out[i] = " "
                    if i + 1 < n and text[i + 1] not in "\r\n":
                        out[i + 1] = " "
                    i += 2
                    continue
                if text[i] == quote:
                    break
                if quote != "`" and text[i] in "\r\n":
                    break  # unterminated single-line string, stop at the line
                if text[i] not in "\r\n":
                    out[i] = " "
                i += 1
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] not in "\r\n":
                if not keep_comments:
                    out[i] = " "
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            start = i
            i += 2
            while i < n:
                if text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    i += 2
                    break
                i += 1
            if not keep_comments:
                for p in range(start, i):
                    if text[p] not in "\r\n":
                        out[p] = " "
        elif c == "/" and _regex_ahead(out, i):
            # regex literal: blank the inside so a brace or a quote in the
            # pattern cannot fool the scanners
            i += 1
            in_class = False
            while i < n:
                ch = text[i]
                if ch in "\r\n":
                    break  # unterminated regex, stop at the line
                if ch == "\\":
                    out[i] = " "
                    if i + 1 < n and text[i + 1] not in "\r\n":
                        out[i + 1] = " "
                    i += 2
                    continue
                if not in_class and ch == "/":
                    break
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                out[i] = " "
                i += 1
            i += 1  # step past the closing slash (flags are plain letters)
        else:
            i += 1
    return "".join(out)


def _body_span(masked: str, start: int) -> Tuple[int, int]:
    """Indexes of the opening and closing brace of the next { ... } block.

    Works on masked text, so braces in strings and comments are invisible."""
    i = masked.find("{", start)
    if i < 0:
        raise ValueError("no opening brace")
    depth = 0
    for j in range(i, len(masked)):
        if masked[j] == "{":
            depth += 1
        elif masked[j] == "}":
            depth -= 1
            if depth == 0:
                return i, j
    raise ValueError("no closing brace")


# ── marker blocks ────────────────────────────────────────────────────────────
def _strip_marked(text: str, mark_re: re.Pattern) -> str:
    """Remove every marker block. Whole lines only, so everything outside the
    blocks keeps its exact bytes and line endings.

    Marker lines are matched on masked text with the comments kept, so a
    marker shaped line inside a user string literal is user data and stays
    untouched. Only a real marker comment starts or ends a block."""
    masked_lines = _mask(text, keep_comments=True).splitlines(keepends=True)
    out: List[str] = []
    inside = False
    last_block_had_no_newline = False
    for ln, masked_ln in zip(text.splitlines(keepends=True), masked_lines):
        bare = ln.rstrip("\r\n")
        m = mark_re.fullmatch(masked_ln.rstrip("\r\n").strip())
        if not inside:
            if m and m.group(2) == "START":
                inside = True
                continue
            if m and m.group(2) == "END":
                raise ValueError(
                    "Found a rule END marker with no START marker before it. "
                    "The marker lines look damaged.")
            out.append(ln)
        else:
            if m and m.group(2) == "END":
                inside = False
                last_block_had_no_newline = (ln == bare)
    if inside:
        raise ValueError(
            "Found a rule START marker with no END marker after it. The "
            "marker lines look damaged.")
    result = "".join(out)
    if last_block_had_no_newline:
        # The block sat at the very end of the file with no newline after it,
        # so the newline that introduced it was ours too. Remove it so the
        # user's original bytes come back exactly.
        if result.endswith("\r\n"):
            result = result[:-2]
        elif result.endswith("\n"):
            result = result[:-1]
    return result


def _list_marked(text: str, mark_re: re.Pattern) -> List[str]:
    slugs: List[str] = []
    for ln in _mask(text, keep_comments=True).splitlines():
        m = mark_re.fullmatch(ln.strip())
        if m and m.group(2) == "START" and m.group(1) != DISPATCH_SLUG \
                and m.group(1) not in slugs:
            slugs.append(m.group(1))
    return sorted(slugs)


def _dedent(lines: List[str]) -> str:
    """Undo _reindent: drop the common leading indent, keep blank lines empty."""
    non_blank = [l for l in lines if l.strip()]
    common = min((len(l) - len(l.lstrip()) for l in non_blank), default=0)
    return "\n".join((l[common:] if l.strip() else "") for l in lines)


def _extract_marked(text: str, mark_re: re.Pattern) -> Dict[str, str]:
    """slug -> the dedented lines between that block's markers.

    The dispatcher block is ours but not a rule, so it is left out. Marker
    lines are matched on masked text with the comments kept, the same way
    _strip_marked tells a real marker from marker shaped user data."""
    masked_lines = _mask(text, keep_comments=True).splitlines()
    out: Dict[str, str] = {}
    current: Optional[str] = None
    buf: List[str] = []
    for ln, masked_ln in zip(text.splitlines(), masked_lines):
        m = mark_re.fullmatch(masked_ln.strip())
        if m and m.group(2) == "START":
            current, buf = m.group(1), []
            continue
        if m and m.group(2) == "END":
            if current is not None and current != DISPATCH_SLUG \
                    and current not in out:
                out[current] = _dedent(buf)
            current = None
            continue
        if current is not None:
            buf.append(ln)
    return out


def _reindent(src: str, indent: str) -> List[str]:
    """Shift a code snippet to the given indent, keeping its own relative
    indentation. Blank lines stay empty."""
    raw = src.strip("\n").splitlines()
    non_blank = [l for l in raw if l.strip()]
    common = min((len(l) - len(l.lstrip()) for l in non_blank), default=0)
    return [(indent + l[common:]).rstrip() if l.strip() else "" for l in raw]


def _block(start_line: str, end_line: str, body_src: str,
           indent: str, nl: str) -> str:
    lines = [indent + start_line] + _reindent(body_src, indent) + [indent + end_line]
    return nl.join(lines) + nl


def _check_rules(rules: List[ScreenRule]) -> List[ScreenRule]:
    seen = set()
    for r in rules:
        _check_slug(r.slug)
        if r.slug in seen:
            raise ValueError(
                "Rule slug '%s' appears more than once. Slugs must be unique."
                % r.slug)
        seen.add(r.slug)
    return sorted(rules, key=lambda r: r.slug)


# ── the dispatcher ───────────────────────────────────────────────────────────
def _dispatcher_body(slugs: List[str]) -> List[str]:
    """Shared between TS and JS: plain ES5 statements, no type annotations."""
    lines = ["var problems = [];", "var found;", "var i;"]
    for slug in slugs:
        lines.append("found = this.rule_%s(eventData);" % slug.replace("-", "_"))
        lines.append("for (i = 0; i < found.length; i++) { problems.push(found[i]); }")
    lines += [
        "if (problems.length === 0) {",
        "    return;",
        "}",
        "eventData.eventProcessed = true;",
        "var errors = [];",
        "for (i = 0; i < problems.length; i++) {",
        "    errors.push(new Qad.Common.DTO.Error({",
        "        message: problems[i].message,",
        "        fieldName: problems[i].fieldName,",
        "        severity: 1",
        "    }));",
        "}",
        "var panel = this.ViewController.ErrorGroupPanel;",
        "panel.clearErrorGrid();",
        "panel.addErrorsToErrorGrid(errors);",
        "panel.showErrorGrid();",
    ]
    return lines


def _dispatcher_ts(slugs: List[str]) -> str:
    lines = ["public onBeforeUpdate(eventData: any, processEvent: any): void {"]
    for l in _dispatcher_body(slugs):
        lines.append(("    " + l) if l else "")
    lines.append("}")
    return "\n".join(lines)


# ── public API: classify and scaffold ────────────────────────────────────────
def classify(ts_code: str) -> str:
    """What is in this handler, once our own blocks are set aside.

    "scaffold_only": the class bodies hold nothing but the generated
        createViewFormTSHandler. Dead statements after its return (like a
        console.log line) do not count as logic.
    "has_logic": anything else outside our markers.
    "has_own_save_hook": onBeforeUpdate or onBeforeDelete exists outside our
        markers. The caller must stop and tell the user; we never merge into
        hand written save code.
    """
    code = strip_rules(ts_code)
    masked = _mask(code)
    if re.search(r"\bonBeforeUpdate\b|\bonBeforeDelete\b", masked):
        return "has_own_save_hook"

    m = re.search(r"export\s+class\s+(\w+?)MaintHandler\b", masked)
    if not m:
        return "has_logic"
    view = m.group(1)
    try:
        m_open, m_close = _body_span(masked, m.end())
    except ValueError:
        return "has_logic"
    maint_body = masked[m_open + 1:m_close]

    mm = re.search(r"(?:protected|public|private)?\s*createViewFormTSHandler\s*\(",
                   maint_body)
    if not mm:
        return "has_logic"
    try:
        f_open, f_close = _body_span(maint_body, mm.end())
    except ValueError:
        return "has_logic"
    if (maint_body[:mm.start()] + maint_body[f_close + 1:]).strip():
        return "has_logic"
    inner = maint_body[f_open + 1:f_close].strip()
    # The first statement must be the generated return. Anything after it
    # never runs, so it is ignored.
    if not re.match(r"return\s+new\s+" + re.escape(view)
                    + r"FormHandler\s*\(\s*this\s*\)\s*;", inner):
        return "has_logic"

    fm = re.search(r"export\s+class\s+" + re.escape(view) + r"FormHandler\b",
                   masked)
    if not fm:
        return "has_logic"
    try:
        fb_open, fb_close = _body_span(masked, fm.end())
    except ValueError:
        return "has_logic"
    if masked[fb_open + 1:fb_close].strip():
        return "has_logic"

    # Module level: only the module header, "use strict", import lines and
    # braces may remain once the two class declarations are blanked out.
    top = list(masked)
    for a, b in ((m.start(), m_close), (fm.start(), fb_close)):
        for i in range(a, b + 1):
            if top[i] not in "\r\n":
                top[i] = " "
    for line in "".join(top).splitlines():
        s = line.strip()
        if not s or s in ("{", "}"):
            continue
        if re.fullmatch(r"module\s+[\w.]+\s*\{", s):
            continue
        if re.fullmatch(r"import\s+\w+\s*=\s*[\w.]+\s*;", s):
            continue
        if re.fullmatch(r'"\s*"\s*;', s):  # a masked "use strict";
            continue
        return "has_logic"
    return "scaffold_only"


_SCAFFOLD = '''module {module_path} {{
    "use strict";

    import QraViewTSHandlerWithViewFormTSHandler = Qad.QraView.TSHandler.QraViewTSHandlerWithViewFormTSHandler;
    import QraViewFormTSHandlerV2 = Qad.QraView.TSHandler.QraViewFormTSHandlerV2;
    import IViewField = Qad.QraView.TSHandler.IViewField;
    import DTO = {view_namespace}.EventHandler.{view}.DTO;
    import Constants = {view_namespace}.EventHandler.{view}.Constants;

    /**
     * {view}MaintHandler : Maint TS handler class.
     *
     * Do not change this class name or the event handler will no longer run.
     *
     */
    export class {view}MaintHandler extends QraViewTSHandlerWithViewFormTSHandler<DTO.{view}Maint, {view}FormHandler> {{
        protected createViewFormTSHandler(): {view}FormHandler {{
            return new {view}FormHandler(this);
        }}
    }}

    export class {view}FormHandler extends QraViewFormTSHandlerV2<DTO.{view}Maint> {{
    }}
}}
'''


def build_scaffold_ts(identity: HandlerIdentity) -> str:
    """Regenerate QAD's scaffold for a view that has no handler yet.

    Matches the shape QAD itself generates. The class names are load bearing:
    rename them and the handler stops running."""
    return _SCAFFOLD.format(module_path=identity.module_path,
                            view_namespace=identity.view_namespace,
                            view=identity.view_pascal)


# ── public API: TypeScript side ──────────────────────────────────────────────
def list_rules(ts_code: str) -> List[str]:
    """Slugs of the rule blocks in the code, sorted. The dispatcher block is
    ours but is not a rule, so it is not listed."""
    return _list_marked(ts_code, _TS_MARK)


def strip_rules(ts_code: str) -> str:
    """Remove ALL our TS blocks. Exact inverse of apply_rules: everything the
    user wrote comes back byte for byte."""
    return _strip_marked(ts_code, _TS_MARK)


def extract_rules(ts_code: str) -> Dict[str, str]:
    """slug -> that rule's method_ts, read back out of a merged handler.

    The exact inverse of what apply_rules put in: a later run can rebuild a
    ScreenRule from this and re-apply it without regenerating the code. The
    dispatcher block is not a rule and is not returned."""
    return _extract_marked(ts_code, _TS_MARK)


def apply_rules(ts_code: str, rules: List[ScreenRule],
                identity: HandlerIdentity) -> str:
    """Put the given rules (and a fresh dispatcher) into the handler.

    Old blocks are stripped first, then each rule block plus the regenerated
    dispatcher block is inserted into the Maint class body, right before that
    class's closing brace. Running it twice with the same rules gives the same
    bytes."""
    rules = _check_rules(rules)
    base = strip_rules(ts_code)
    if classify(base) == "has_own_save_hook":
        raise ValueError(
            "This handler already has its own onBeforeUpdate or onBeforeDelete "
            "outside our rule markers. We do not merge rules into hand written "
            "save code. Please move or remove that code first.")
    if not rules:
        return base

    masked = _mask(base)
    m = re.search(r"export\s+class\s+" + re.escape(identity.view_pascal)
                  + r"MaintHandler\b", masked)
    if not m:
        raise ValueError(
            "Could not find 'export class %sMaintHandler' in the handler "
            "code, so there is nowhere to put the rules."
            % identity.view_pascal)
    try:
        _open, close = _body_span(masked, m.end())
    except ValueError:
        raise ValueError(
            "The class %sMaintHandler has no matching closing brace. The "
            "handler code looks broken." % identity.view_pascal)

    nl = "\r\n" if "\r\n" in base else "\n"
    line_start = base.rfind("\n", 0, close) + 1
    indent = re.match(r"[ \t]*", base[line_start:]).group(0) + "    "

    parts = []
    for r in rules:
        parts.append(_block("// === RULE: %s START ===" % r.slug,
                            "// === RULE: %s END ===" % r.slug,
                            r.method_ts, indent, nl))
    parts.append(_block("// === RULE: %s START ===" % DISPATCH_SLUG,
                        "// === RULE: %s END ===" % DISPATCH_SLUG,
                        _dispatcher_ts([r.slug for r in rules]), indent, nl))
    return base[:line_start] + "".join(parts) + base[line_start:]


# ── public API: JavaScript side ──────────────────────────────────────────────
def list_rules_js(js_code: str) -> List[str]:
    return _list_marked(js_code, _JS_MARK)


def strip_rules_js(js_code: str) -> str:
    """Remove ALL our JS blocks. Exact inverse of apply_rules_js."""
    return _strip_marked(js_code, _JS_MARK)


def extract_rules_js(js_code: str) -> Dict[str, str]:
    """slug -> that rule's method_js, read back out of a merged JS bundle.

    Each block holds the IIFE wrapper apply_rules_js built around the body;
    this digs the body back out, so what went in as method_js comes back
    exactly. A block that is not our wrapper shape is returned whole rather
    than dropped. The dispatcher block is not a rule and is not returned."""
    out: Dict[str, str] = {}
    for slug, inner in _extract_marked(js_code, _JS_MARK).items():
        lines = inner.splitlines()
        start = None
        for i, ln in enumerate(lines):
            if ".prototype." in ln and "= function" in ln:
                start = i
                break
        end = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "};":
                end = i
                break
        if start is None or end is None or end <= start:
            out[slug] = inner
            continue
        out[slug] = _dedent(lines[start + 1:end])
    return out


def _js_wrapper(slug: str, identity: HandlerIdentity, fn_name: str,
                params: str, body_src: str, nl: str) -> str:
    lines = ["// === RULE-JS: %s START ===" % slug,
             "(function () {",
             '    "use strict";',
             "    var _cls = %s.%sMaintHandler;"
             % (identity.module_path, identity.view_pascal),
             "    _cls.prototype.%s = function (%s) {" % (fn_name, params)]
    lines += _reindent(body_src, "        ")
    lines += ["    };",
              "})();",
              "// === RULE-JS: %s END ===" % slug]
    return nl.join(lines) + nl


def apply_rules_js(js_code: str, rules: List[ScreenRule],
                   identity: HandlerIdentity) -> str:
    """Append the rule blocks and a fresh dispatcher block to the JS bundle.

    The stored bundle is compiled code we cannot rebuild, so nothing inside it
    is ever changed: old blocks are stripped, new blocks go at the end. Each
    block is an IIFE that patches the Maint class prototype through the
    namespace object."""
    rules = _check_rules(rules)
    base = strip_rules_js(js_code)
    if not rules:
        return base

    nl = "\r\n" if "\r\n" in base else "\n"
    parts = [_js_wrapper(r.slug, identity, r.method_name, "eventData",
                         r.method_js, nl) for r in rules]
    parts.append(_js_wrapper(
        DISPATCH_SLUG, identity, "onBeforeUpdate", "eventData, processEvent",
        "\n".join(_dispatcher_body([r.slug for r in rules])), nl))
    text = "".join(parts)

    if base and not base.endswith("\n"):
        # Start our blocks on a fresh line but leave the file without a
        # trailing newline, so strip_rules_js can give back the original
        # bytes exactly.
        return base + nl + text[:-len(nl)]
    return base + text


# ── public API: compile check ────────────────────────────────────────────────
def _view_stub(ts_code: str) -> str:
    """Only the view's DTO and Constants namespaces, any-typed, derived from
    the module header of the code itself. The kit's base.json has the real
    Qad.* framework typings but knows nothing about these per-view
    namespaces, so the kit path needs this stub too or the scaffold's import
    lines fail."""
    m = re.search(r"\bmodule\s+([A-Za-z_][\w.]*)\s*\{", ts_code)
    if not (m and ".EventHandler." in m.group(1)):
        return ""
    ns, rest = m.group(1).split(".EventHandler.", 1)
    view = rest.split(".")[0]
    lines = [
        "declare namespace %s.EventHandler.%s {" % (ns, view),
        "    namespace DTO { type %sMaint = any; }" % view,
        "    namespace Constants { type _stub = any; }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def _ambient_stub(ts_code: str) -> str:
    """Just enough ambient declarations, all any-typed, for the scaffold plus
    our blocks to type check. The view's DTO and Constants namespaces are
    derived from the module header of the code itself."""
    lines = [
        "declare namespace Qad.QraView.TSHandler {",
        "    class QraViewTSHandlerWithViewFormTSHandler<A, B> {",
        "        constructor(...args: any[]);",
        "        NgData: any;",
        "        ViewController: any;",
        "        protected createViewFormTSHandler(): B;",
        "    }",
        "    class QraViewFormTSHandlerV2<A> {",
        "        constructor(...args: any[]);",
        "    }",
        "    interface IViewField<A> {",
        "    }",
        "}",
        "declare namespace Qad.Common.DTO {",
        "    class Error {",
        "        constructor(values: any);",
        "    }",
        "}",
    ]
    return "\n".join(lines) + "\n" + _view_stub(ts_code)


def _kit_check(node: str, ts_code: str) -> CompileResult:
    """Run the vendored QAD kit: node check.js handler.ts view_stub.d.ts.

    Only the view-namespace stub goes along; base.json in the kit provides
    the real Qad.* typings. A FATAL exit, a timeout or output we cannot read
    is a broken checker environment and is NEVER treated as a pass."""
    def broken(detail: str) -> str:
        return ("The QAD compile check environment is broken (%s). Fix the "
                "kit in %s, or remove qadCompile.js there to fall back to "
                "the simple stub check." % (detail, _QAD_KIT_DIR))

    if not (_QAD_KIT_DIR / "node_modules" / "typescript").is_dir():
        return CompileResult(ok=False, errors=[
            broken("typescript is not installed; run npm install there")],
            checker="qad-kit")

    with tempfile.TemporaryDirectory() as tmp:
        handler = Path(tmp) / "handler.ts"
        handler.write_bytes(ts_code.encode("utf-8"))
        stub = Path(tmp) / "view_stub.d.ts"
        stub.write_bytes(_view_stub(ts_code).encode("utf-8"))
        try:
            # cwd is the kit folder so require() inside check.js resolves.
            proc = subprocess.run(
                [node, "check.js", str(handler), str(stub)],
                cwd=str(_QAD_KIT_DIR), capture_output=True, text=True,
                timeout=60)
        except subprocess.TimeoutExpired:
            return CompileResult(ok=False, errors=[
                broken("the check did not finish within 60 seconds")],
                checker="qad-kit")
        except Exception as exc:  # noqa: BLE001
            return CompileResult(ok=False, errors=[
                broken("could not run node: %s" % exc)], checker="qad-kit")

    try:
        data = json.loads((proc.stdout or "").strip())
    except ValueError:
        data = None

    if proc.returncode == 0 and isinstance(data, dict) \
            and data.get("status") == "OK":
        return CompileResult(ok=True, errors=[], checker="qad-kit")
    if proc.returncode == 1 and isinstance(data, dict) \
            and data.get("status") == "ERRORS":
        errors = ["line %s: %s" % (e.get("line", "?"), e.get("message", ""))
                  for e in (data.get("errors") or [])]
        if not errors:
            errors = ["The check reported errors but listed none."]
        return CompileResult(ok=False, errors=errors, checker="qad-kit")

    # Exit 2, a FATAL doc, or stdout we cannot read: the environment failed.
    detail = ""
    for text in (proc.stderr, proc.stdout):
        try:
            doc = json.loads((text or "").strip())
        except ValueError:
            continue
        if isinstance(doc, dict) and doc.get("status") == "FATAL":
            detail = doc.get("message") or ""
            break
    if not detail:
        detail = ((proc.stderr or proc.stdout or "").strip()[:400]
                  or "exit code %d with no output" % proc.returncode)
    return CompileResult(ok=False, errors=[broken(detail)],
                         checker="qad-kit")


def compile_check(ts_code: str) -> CompileResult:
    """Type check the merged handler.

    Primary path: the vendored QAD compile kit in backend/qad_compile, which
    reruns the exact check the QAD editor's Compile button does (real
    typings, real compiler options). Used whenever qadCompile.js is there; a
    half-installed kit is reported as a broken environment, never as a pass.

    Fallback path: when the kit is not installed at all, the old check runs
    node tsc.js --noEmit --target ES5 against any-typed ambient stubs. The
    checker field says which one ran.

    Never raises for a missing toolchain: if node or tsc is not there, ok is
    False and the error says what is missing. Line numbers in the errors
    refer to the merged file as given."""
    node = shutil.which("node")
    if not node:
        return CompileResult(ok=False, errors=[
            "Node.js was not found. Install Node.js and make sure 'node' is "
            "on PATH, then try again."])
    if (_QAD_KIT_DIR / "qadCompile.js").is_file():
        return _kit_check(node, ts_code)
    if not _TSC_JS.is_file():
        return CompileResult(ok=False, errors=[
            "The TypeScript compiler was not found at %s. Run 'npm install' "
            "in the frontend folder to get it." % _TSC_JS])

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "handler.ts").write_bytes(ts_code.encode("utf-8"))
        (Path(tmp) / "stubs.d.ts").write_bytes(
            _ambient_stub(ts_code).encode("utf-8"))
        try:
            proc = subprocess.run(
                [node, str(_TSC_JS), "--noEmit", "--target", "ES5",
                 "handler.ts", "stubs.d.ts"],
                cwd=tmp, capture_output=True, text=True, timeout=300)
        except Exception as exc:  # noqa: BLE001
            return CompileResult(ok=False, errors=[
                "Could not run the TypeScript compiler: %s" % exc])

    if proc.returncode == 0:
        return CompileResult(ok=True, errors=[])

    errors: List[str] = []
    for raw in (proc.stdout or "").splitlines() + (proc.stderr or "").splitlines():
        m = _TSC_ERR.match(raw.strip())
        if m:
            prefix = "" if m.group("file").endswith("handler.ts") \
                else m.group("file") + " "
            errors.append("%sline %s: %s" % (prefix, m.group("line"),
                                             m.group("msg").strip()))
        elif "error TS" in raw:
            errors.append(raw.strip())
    if not errors:
        errors = ["The TypeScript compiler failed (exit code %d) but printed "
                  "no error lines." % proc.returncode]
    return CompileResult(ok=False, errors=errors)
