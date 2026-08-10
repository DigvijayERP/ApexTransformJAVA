"""
Client-extension event handler payload for `eventhandler`, plus the Browse-URI
placeholder machinery.

Ported from aux_web_version/backend/builders/event_handler_builder.py with two
changes.

1. TIMING AND SCOPE ARE PARAMETERS, NOT CONSTANTS.
   AUX hardcodes eventHandlerType="BEFORE" and appliesTo="WEB"
   (aux_web_version/backend/builders/event_handler_builder.py:30-31). The
   platform documents three timings (PRIMARY / BEFORE / AFTER) and Phase 5's
   whole design rests on being able to choose one, so they are arguments here.

2. BROWSE URIS ARE COLLECTED FROM THE USER INSTEAD OF COMMENTED OUT.
   AUX's TS_CODE_WRITER prompt instructs the model to comment out every lookup
   and HTTP call behind a TODO with a fake endpoint
   (aux_web_version/backend/agents/prompts.py:354-366), because "any uncommented
   HTTP call without a known working URL" is forbidden (:378). The generated
   handler therefore ships inert and the user hand-edits it in QAD afterwards.

   Here the model emits a PLACEHOLDER inside a string literal instead:

       const browseUri: string = "{{BROWSE_URI:customerCode}}";

   The placeholder is valid TypeScript, so it survives the tsc syntax gate. We
   extract them, ask the user for the real value at the stage-4 gate, and
   substitute TEXTUALLY. Substitution is deterministic: filling in a URI cannot
   change anything else in the generated code, and needs no second LLM call.

   A placeholder the user declines to fill is commented out, which is exactly
   AUX's behaviour — so the fallback is never worse than today.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from builders.identity import AppIdentity, resolve

# Matches {{BROWSE_URI:someFieldName}} inside the generated TypeScript.
PLACEHOLDER_RE = re.compile(r"\{\{BROWSE_URI:([A-Za-z_][A-Za-z0-9_]*)\}\}")

# Sentinel a user can send back to mean "I don't have this one — leave it out".
SKIP = "__SKIP__"

VALID_TIMINGS = ("PRIMARY", "BEFORE", "AFTER")
VALID_APPLIES_TO = ("WEB", "MOBILE")


@dataclass(frozen=True)
class BrowsePlaceholder:
    """One URI the generated handler needs before it can do real work."""
    field: str
    token: str
    occurrences: int
    # The line it appears on, so the dialog can show it in context rather than
    # asking for a URI with no indication of what it is for.
    context: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def strip_fences(code: str) -> str:
    """Remove accidental markdown fences. Models add them despite instructions."""
    out = code.strip()
    if out.startswith("```"):
        lines = out.splitlines()
        out = "\n".join(lines[1:] if lines[0].startswith("```") else lines)
        if out.endswith("```"):
            out = out[: out.rfind("```")].rstrip()
    return out.strip()


def extract_placeholders(ts_code: str) -> List[BrowsePlaceholder]:
    """Every distinct Browse URI the handler is waiting on, in first-appearance
    order so the dialog lists them the way they read in the code."""
    lines = ts_code.splitlines()
    first_line: Dict[str, str] = {}
    counts: Dict[str, int] = {}
    order: List[str] = []

    for line in lines:
        for match in PLACEHOLDER_RE.finditer(line):
            field = match.group(1)
            if field not in counts:
                counts[field] = 0
                order.append(field)
                first_line[field] = line.strip()
            counts[field] += 1

    return [
        BrowsePlaceholder(
            field=f,
            token="{{BROWSE_URI:%s}}" % f,
            occurrences=counts[f],
            context=first_line[f],
        )
        for f in order
    ]


def _comment_out_line(line: str, fields: List[str]) -> str:
    """Neutralise a line that still holds an unfilled placeholder.

    Matches AUX's fallback: the logic survives as a comment carrying a TODO the
    user can act on in QAD, rather than shipping a handler that references a
    browse which does not exist.

    The token itself is replaced with plain words. Leaving `{{BROWSE_URI:x}}` in
    the comment would both read as machine noise to whoever opens the handler in
    QAD, and — worse — keep matching extract_placeholders(), so the pre-POST
    guard would refuse a handler the user had deliberately chosen to skip.
    """
    indent = line[: len(line) - len(line.lstrip())]
    body = PLACEHOLDER_RE.sub(lambda m: f"<BROWSE URI FOR {m.group(1)} NOT SUPPLIED>", line.strip())
    which = ", ".join(fields)
    return f"{indent}// TODO: supply the Browse URI for {which}, then re-enable: {body}"


def substitute_placeholders(ts_code: str, values: Dict[str, str]) -> Dict[str, Any]:
    """Replace each {{BROWSE_URI:field}} with the supplied value.

    A field mapped to SKIP (or missing entirely) has its lines commented out.
    Returns the resulting code plus what was filled and what was skipped, so the
    stage can report it honestly rather than silently degrading.
    """
    filled: List[str] = []
    skipped: List[str] = []
    out_lines: List[str] = []

    for line in ts_code.splitlines():
        matches = PLACEHOLDER_RE.findall(line)
        if not matches:
            out_lines.append(line)
            continue

        unresolved = [f for f in matches
                      if not str(values.get(f, "")).strip() or values.get(f) == SKIP]
        if unresolved:
            for f in unresolved:
                if f not in skipped:
                    skipped.append(f)
            out_lines.append(_comment_out_line(line, unresolved))
            continue

        new_line = line
        for f in matches:
            new_line = new_line.replace("{{BROWSE_URI:%s}}" % f, str(values[f]).strip())
            if f not in filled:
                filled.append(f)
        out_lines.append(new_line)

    return {
        "code": "\n".join(out_lines),
        "filled": filled,
        "skipped": skipped,
        "fully_resolved": not skipped,
    }


def build_event_handler_payload(
    bc_pascal: str,
    ts_code: str,
    js_code: str,
    *,
    timing: str = "BEFORE",
    applies_to: str = "WEB",
    is_active: bool = True,
    identity: Optional[AppIdentity] = None,
) -> Dict[str, Any]:
    """The `eventhandler` POST body.

    `timing` and `applies_to` are validated rather than trusted: a typo would be
    accepted by QAD's JSON and produce a handler registered against a timing
    that never fires, which is close to undiagnosable from the UI.
    """
    ident = resolve(identity)

    timing = str(timing).upper()
    if timing not in VALID_TIMINGS:
        raise ValueError(
            f"eventHandlerType must be one of {', '.join(VALID_TIMINGS)}, got '{timing}'."
        )
    applies_to = str(applies_to).upper()
    if applies_to not in VALID_APPLIES_TO:
        raise ValueError(
            f"appliesTo must be one of {', '.join(VALID_APPLIES_TO)}, got '{applies_to}'."
        )

    ts_clean = strip_fences(ts_code)
    js_clean = strip_fences(js_code)

    leftover = extract_placeholders(ts_clean)
    if leftover:
        raise ValueError(
            "Handler still contains unfilled Browse URI placeholders: "
            + ", ".join(p.field for p in leftover)
            + ". Resolve or skip each one before registering the handler."
        )

    view_uri = ident.view_meta_uri(bc_pascal)
    payload = {
        "supplementaryMessages": [],
        "eventHandlerV2s": [{
            "appURI": ident.module_uri,
            "viewURI": view_uri,
            "eventHandlerType": timing,
            "appliesTo": applies_to,
            "isActive": is_active,
            "typeScriptCode": ts_clean,
            "javaScriptCode": js_clean,
            "mappingCode": "",
        }],
    }

    return {
        "status": "built",
        "payload": payload,
        "summary": {
            "bc_pascal": bc_pascal,
            "view_uri": view_uri,
            "timing": timing,
            "applies_to": applies_to,
            "ts_code_length": len(ts_clean),
            "js_code_length": len(js_clean),
        },
    }
