"""
LLM system prompts for the Case-1 stages.

⚠️ NOT YET PORTED. Every prompt below is a PLACEHOLDER.

AUX's `agents/prompts.py` is 515 lines of prompt text tuned against a live QAD,
and porting it is a deliberate, careful job rather than a copy — TS_CODE_WRITER
in particular has to change, replacing AUX's "comment out every lookup behind a
TODO" instruction (aux_web_version/backend/agents/prompts.py:354-366) with the
`{{BROWSE_URI:field}}` convention this project uses.

WHY PLACEHOLDERS RATHER THAN ROUGH APPROXIMATIONS

A prompt that is 80% right does not fail — it silently produces a plausible,
wrong field design, and the wrongness only surfaces when QAD rejects a deploy or,
worse, accepts a bad one. Every prompt therefore starts with the marker below,
and `assert_ported()` refuses to run a real model against one. Tests pass because
they stub the model entirely, which exercises the real builders, the real store
and the real gating without ever consulting a prompt.

TO PORT: read the corresponding constant in
aux_web_version/backend/agents/prompts.py, bring it across, and delete the
marker from that string. `assert_ported()` then stops complaining about it.
"""
from __future__ import annotations

from typing import Dict, List

# Any prompt still carrying this is a placeholder.
UNPORTED = "[[UNPORTED PLACEHOLDER]]"

_SRC = "aux_web_version/backend/agents/prompts.py"

REQUIREMENTS_GATHERING = f"""{UNPORTED}
Port from {_SRC} :: REQUIREMENTS_GATHERING.
Reads a user's request and restates it as a structured requirement summary.
Output is PLAIN TEXT, not JSON."""

FIELD_CREATOR = f"""{UNPORTED}
Port from {_SRC} :: FIELD_CREATOR.
Turns the requirement summary into strict JSON:
  {{"spec": {{"bc_pascal", "description", "fields":[
      {{"code", "label", "dataType", "isPrimary", "isRequired",
        "maxLength", "dropdownValues":[{{"code","label"}}]}}]}}}}
ADAPTIVE ADDITION: each field may also carry "needsLookup": true, which is what
drives the conditional lookup stage."""

VALIDATOR_AND_CORRECTOR = f"""{UNPORTED}
Port from {_SRC} :: VALIDATOR_AND_CORRECTOR.
Given the submitted spec and QAD's rejection, returns either
  {{"status":"fixed", "spec":{{...}}, "fix_summary":"..."}}
or {{"status":"failed", "reason":"..."}}.
In Adaptive this feeds a RECOVERY DIALOG rather than a silent auto-retry."""

FORM_PLANNER = f"""{UNPORTED}
Port from {_SRC} :: FORM_PLANNER.
Groups fields into logical panels. PKs first, two columns, <= 6 fields a panel.
Output is PLAIN TEXT."""

FORM_FIELD_BUILDER = f"""{UNPORTED}
Port from {_SRC} :: FORM_FIELD_BUILDER.
Turns the panel plan into exact grid placements:
  [{{"fieldName","panel","panelName","gridColumn","gridRow"}}]
Must place EVERY field - a missing one makes the record unsaveable in QAD."""

EVENT_HANDLER_PLANNER = f"""{UNPORTED}
Port from {_SRC} :: EVENT_HANDLER_PLANNER.
Plans handler logic as six plain-text sections. Grounded on the
client_extension_event_handler docs bundle via {{QAD_DOCS_CONTEXT}}."""

TS_CODE_WRITER = f"""{UNPORTED}
Port from {_SRC} :: TS_CODE_WRITER, WITH ONE DELIBERATE CHANGE.

AUX instructs the model to COMMENT OUT every lookup and HTTP call behind a TODO
pointing at a fake `api/TODO/provide-endpoint` ({_SRC}:354-366), because ":378"
forbids "any uncommented HTTP call without a known working URL". The handler
therefore ships inert and the user hand-edits it in QAD afterwards.

REPLACE THAT with the placeholder convention:

    Where a browse or lookup URI is needed, emit it as a string literal
    placeholder:  const uri: string = "{{{{BROWSE_URI:fieldName}}}}";
    Do NOT comment the call out. Write the working code around the placeholder.

The placeholder is valid TypeScript, so it survives the tsc syntax gate, and
`event_handler_builder.substitute_placeholders` fills it from what the user
supplies at the stage-4 gate. Anything left unfilled is commented out THEN -
matching AUX's behaviour exactly, so the fallback is never worse."""

TS_COMPILER = f"""{UNPORTED}
Port from {_SRC} :: TS_COMPILER.
NOTE: AUX uses an LLM as a stand-in compiler here and never syntax-checks the
result (aux_web_version/backend/pipeline.py:666-678). We already ship a real
tsc. Prefer invoking it over asking a model to pretend."""


_ALL: Dict[str, str] = {
    "REQUIREMENTS_GATHERING": REQUIREMENTS_GATHERING,
    "FIELD_CREATOR": FIELD_CREATOR,
    "VALIDATOR_AND_CORRECTOR": VALIDATOR_AND_CORRECTOR,
    "FORM_PLANNER": FORM_PLANNER,
    "FORM_FIELD_BUILDER": FORM_FIELD_BUILDER,
    "EVENT_HANDLER_PLANNER": EVENT_HANDLER_PLANNER,
    "TS_CODE_WRITER": TS_CODE_WRITER,
    "TS_COMPILER": TS_COMPILER,
}


def unported() -> List[str]:
    """Which prompts are still placeholders."""
    return sorted(name for name, text in _ALL.items() if UNPORTED in text)


def assert_ported() -> None:
    """Refuse to drive a real model with placeholder prompts.

    Called by the engine before any live LLM call. Fails loudly and early rather
    than producing a plausible-but-wrong field design that only surfaces when
    QAD rejects a deploy.
    """
    pending = unported()
    if pending:
        raise RuntimeError(
            "These prompts are still placeholders and would generate nonsense: "
            + ", ".join(pending)
            + f". Port each from {_SRC}, or run with a stubbed model."
        )
