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

STAGE SHAPE (owner's design, 2026-08-10):

    1 Requirements   gated, no write
    2 Fields         gated -> approving POSTS the BC
    3 Form           gated -> approving POSTS the form
    4 Handler        gated -> approving POSTS the event handler
    5 View                  -> POSTS the view, NO approval
    6 Deploy         gated -> approving DEPLOYS

Stage 4 sits between form and view, matching AUX's ordering (its steps 8-11 run
after the form save at step 7 and before the view at 12-13).

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
        id="deploy",
        number=6,
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
