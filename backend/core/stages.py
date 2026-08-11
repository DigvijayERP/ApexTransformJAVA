"""
The single source of truth for stage identity.

Everything that needs to know "what are the steps" reads this: the run engine
iterates it, the API serves it at GET /api/run/stages, and the frontend renders
from that response. The frontend keeps NO step table of its own.

That rule exists because of a specific defect in the AUX reference
implementation. AUX defines step identity twice — STEP_LABELS
(aux_web_version/backend/pipeline.py:145-160) and ProgressPanel.tsx:3-18 — and
the two have ALREADY drifted: three embedded labels disagree, and embedded step
8 cannot be rendered at all because it is outside the frontend's list. AUX also
hardcodes TOTAL_STEPS in three places. A gate that shows the wrong stage name
collects approval for the wrong artifact, so identity lives in exactly one
place here.

STAGE SHAPE (owner's design, finalised 2026-08-10):

    1 Requirements   gated, no write            ALWAYS
    2 Fields         gated -> POSTS the BC       ALWAYS
    3 Form           gated -> POSTS the form     ALWAYS
    4 Handler        gated -> POSTS the handler  ONLY IF NEEDED
    5 View                  -> POSTS the view    ALWAYS, no approval
    6 Lookups        gated -> POSTS lookups      ONLY IF ANY FIELD WANTS ONE
    7 Deploy         gated -> DEPLOYS            ALWAYS

So a plain business component runs FIVE stages; a fully-featured one runs seven,
plus a recovery dialog that appears only when QAD rejects the create. THE STAGE
LIST IS PER-RUN. Anything rendering it must read the run's actual list, never a
fixed table — which is the specific thing AUX gets wrong, and why its frontend
cannot render its own embedded step 8.

Stage 4 sits between form and view, matching AUX's ordering (its steps 8-11 run
after the form save at step 7 and before the view at 12-13).

Stage 6 sits before deploy by the owner's decision, so that deploy stays
terminal. This placement is UNVALIDATED: AUX put lookups here too but never
actually POSTed one, and the platform guide's worked example creates a lookup on
an already-deployed BC (class 4, pages 3-15). If QAD rejects a Lookup Definition
against an undeployed BC, stages 6 and 7 swap and deploy stays terminal only for
regeneration. One live run settles it.

The gate sits BEFORE each write, showing the exact payload. Approving is what
fires the write. That is stricter than approving a receipt afterwards, and it
is what makes dry-run meaningful: the same dialog renders whether or not the
call will really go out.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Stage:
    id: str
    number: int
    label: str
    description: str

    # Does this stage stop and wait for a human?
    gated: bool

    # Registry endpoint ids this stage calls, in order. Empty = local only.
    writes: List[str] = field(default_factory=list)

    # How the dialog should render this stage's artifact. The frontend switches
    # on this; an unknown kind must render as raw JSON rather than be dropped
    # silently (AUX drops four SSE frame types it does not recognise).
    artifact_kind: str = "text"

    # May the user edit the artifact directly in the dialog, or only approve /
    # regenerate-with-text? Direct editing is deterministic and instant; text
    # steering is for larger changes.
    editable: bool = False

    # True once this stage's writes have executed: no upstream stage may be
    # regenerated, because QAD has no undo and no delete path was found.
    locks_upstream: bool = False

    # Runs only when a condition holds, so the stage list is per-run, not fixed.
    conditional_on: Optional[str] = None


STAGES: List[Stage] = [
    Stage(
        id="requirements",
        number=1,
        label="Requirement gathering",
        description=(
            "Read what you asked for and restate it as a structured requirement. "
            "If you paste or attach ABL source (.p/.cls), the schema is parsed "
            "deterministically and no LLM call is made."
        ),
        gated=True,
        artifact_kind="text",
        editable=True,
    ),
    Stage(
        id="fields",
        number=2,
        label="Field mapping",
        description=(
            "Design the BC's fields: code, label, data type, primary key, required, "
            "max length, dropdown values. Approving POSTS the Business Component to "
            "QAD, and wires any dropdown fields to their data lists."
        ),
        gated=True,
        writes=["bc.create", "bc.metadata.read", "bc.metadata.write"],
        artifact_kind="field_spec",
        editable=True,
        locks_upstream=True,
    ),
    Stage(
        id="form",
        number=3,
        label="Form creation",
        description=(
            "Group fields into panels and place them on a grid. Approving POSTS the "
            "form design to QAD."
        ),
        gated=True,
        writes=["form.save"],
        artifact_kind="form_layout",
        editable=True,
        locks_upstream=True,
    ),
    Stage(
        id="handler",
        number=4,
        label="Event handler",
        description=(
            "Plan and write the client-extension TypeScript handler, syntax-check it "
            "with the real tsc, and show it for verification. Any lookup or HTTP call "
            "the handler needs appears as a Browse URI you fill in here, so the "
            "handler ships working rather than commented out. Approving compiles it "
            "and POSTs it to QAD."
        ),
        gated=True,
        writes=["eventhandler.register"],
        artifact_kind="handler_code",
        editable=True,
        locks_upstream=True,
        # Not every customisation needs a handler. When ABL source was supplied,
        # the parse tells us whether there is any validation or event logic to
        # port, and that drives the default. With no source, the planner
        # proposes and the user can skip. An empty handler in QAD is noise.
        conditional_on="handler_needed",
    ),
    Stage(
        id="view",
        number=5,
        label="View creation",
        description=(
            "Build and register the browse/maintain/hybrid view. Deterministic — "
            "derived entirely from the approved field spec with no LLM call, so "
            "there is no generated content to review."
        ),
        gated=False,
        writes=["view.register"],
        artifact_kind="view_config",
        locks_upstream=True,
    ),
    Stage(
        id="lookups",
        number=6,
        label="Lookups",
        description=(
            "Create a QAD Lookup Definition for each field marked as needing one at "
            "the field stage. When the lookup points at a business component we "
            "created, the browse URI and the result/search fields are derived — "
            "nothing to type. Pointing at a standard QAD component needs its Browse "
            "URI, which you supply here. Optionally choose other form fields to "
            "auto-populate when a value is picked."
        ),
        gated=True,
        writes=["lookup.create"],
        artifact_kind="lookup_config",
        editable=True,
        locks_upstream=True,
        # Skips itself entirely when no field was marked at the field stage.
        conditional_on="any_field_needs_lookup",
    ),
    Stage(
        id="deploy",
        number=7,
        label="Deploy",
        description=(
            "Show QAD's deployment warnings and the exact deploy payloads, then "
            "deploy on approval. Terminal — nothing can be regenerated afterwards."
        ),
        gated=True,
        writes=["deploy.check_warnings", "deploy.business_entity"],
        artifact_kind="deploy_preview",
        locks_upstream=True,
    ),
]


# Not a numbered stage. Injected only when QAD rejects the stage-2 create, so it
# never appears in a clean run. AUX auto-retries this silently
# (aux_web_version/backend/pipeline.py:458-497); here it surfaces QAD's actual
# error and the proposed correction, and waits.
RECOVERY_STAGE = Stage(
    id="fields.autofix",
    number=2,
    label="Fixing the field design",
    description=(
        "QAD rejected the Business Component. Shows QAD's error and a proposed "
        "correction to the field spec, diffed against what was submitted."
    ),
    gated=True,
    writes=["bc.create"],
    artifact_kind="field_spec_diff",
    editable=True,
    locks_upstream=True,
    conditional_on="stage_2_rejected",
)


_BY_ID: Dict[str, Stage] = {s.id: s for s in STAGES}
_BY_ID[RECOVERY_STAGE.id] = RECOVERY_STAGE


def get(stage_id: str) -> Stage:
    if stage_id not in _BY_ID:
        raise KeyError(
            f"Unknown stage '{stage_id}'. Known: {', '.join(sorted(_BY_ID))}"
        )
    return _BY_ID[stage_id]


def first() -> Stage:
    return STAGES[0]


def next_after(stage_id: str) -> Optional[Stage]:
    """The next stage in the happy path. Recovery stages return to their host."""
    if stage_id == RECOVERY_STAGE.id:
        return next_after("fields")
    ids = [s.id for s in STAGES]
    if stage_id not in ids:
        raise KeyError(f"Unknown stage '{stage_id}'")
    i = ids.index(stage_id)
    return STAGES[i + 1] if i + 1 < len(STAGES) else None


def stages_after(stage_id: str) -> List[Stage]:
    """Every stage downstream of this one — what a regeneration must re-run."""
    ids = [s.id for s in STAGES]
    if stage_id not in ids:
        return []
    return STAGES[ids.index(stage_id) + 1:]


def applies(stage_id: str, artifacts: Dict[str, Any]) -> Optional[bool]:
    """Does this stage apply to THIS run, given what earlier stages produced?

        True   it will run — for a conditional stage, its condition is met
        False  it will skip itself
        None   not yet knowable; the stage it depends on has not run

    THE SINGLE PLACE THIS IS DECIDED. The engine asks it before running a
    conditional stage and the API reports it to the UI, so "will this stage
    run?" cannot be answered one way by the rail and another by the engine.
    That divergence is the exact defect this project keeps designing against.

    It also lets the UI stop calling a stage "optional" once its condition is
    met: a lookup stage with a marked field is REQUIRED for that run, and
    labelling it optional invites the user to skip work they actually need.
    """
    stage = get(stage_id)
    if not stage.conditional_on:
        return True

    if stage.conditional_on == "handler_needed":
        req = artifacts.get("requirements")
        if req is None:
            return None
        # An absent signal is NOT a no: the planner proposes and the user
        # decides. Only an explicit False skips.
        return req.get("handler_hint") is not False

    if stage.conditional_on == "any_field_needs_lookup":
        spec = (artifacts.get("fields") or {}).get("spec")
        # No spec means the field stage has not produced one — not that no field
        # wants a lookup. Answering False here would tell the UI "not needed" on
        # no evidence at all.
        if not spec:
            return None
        return any(f.get("needsLookup") is True for f in spec.get("fields") or [])

    return None


def total() -> int:
    """Derived, never hardcoded. AUX hardcodes its total in three places."""
    return len(STAGES)


def writes_to_qad(stage_id: str) -> bool:
    return bool(get(stage_id).writes)


def manifest() -> Dict[str, Any]:
    """What GET /api/run/stages returns. The frontend renders from this."""
    return {
        "total": total(),
        "stages": [asdict(s) for s in STAGES],
        "recovery": asdict(RECOVERY_STAGE),
    }
