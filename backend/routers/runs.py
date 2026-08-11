"""
The run API — everything the frontend needs to drive a gated run.

SHAPE: per-stage request/response, not one long stream.

AUX runs the whole pipeline inside a single `StreamingResponse`
(aux_web_version/backend/routers/client_extensions.py:168-212) whose only client
control is `abort()`. That cannot survive a human pause: holding an SSE
connection open across an indefinite wait invites proxy and idle timeouts, and
nothing survives a browser refresh.

Here each stage is its own request. Run a stage, get its artifact, show the
dialog, then approve or regenerate as a separate call. State lives in SQLite, so
a refresh mid-flow restores exactly where you were — which is what the brief's
Phase 3 asks for, obtained as a property of the transport rather than bolted on.

EVERY MUTATING ROUTE DEPENDS ON require_auth. See core/auth.py for why that is
here now rather than later.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core import engine, stages, store
from core.auth import require_auth
from core.logging_setup import get_logger

logger = get_logger("adaptive.api.runs")

router = APIRouter(prefix="/api/run", tags=["run"])


# ── Request bodies ────────────────────────────────────────────────────────────
class CreateRun(BaseModel):
    user_input: str = Field(min_length=1)
    mode: str = "standard"
    # Dry-run is the DEFAULT and must be opted out of explicitly. The brief's
    # working rule 5: nothing writes to QAD without a greenlight.
    dry_run: bool = True


class RunStage(BaseModel):
    instruction: str = ""
    # Stage 4 collects Browse URIs; stage 6 collects lookup configuration.
    # Passed straight through to the stage function.
    browse_uris: Optional[Dict[str, str]] = None
    configs: Optional[List[Dict[str, Any]]] = None


class SkipStage(BaseModel):
    reason: str = ""


def _kwargs(body: RunStage) -> Dict[str, Any]:
    """Only forward what a stage actually accepts, so an irrelevant field on the
    request body cannot become an unexpected-keyword TypeError deep in a stage."""
    out: Dict[str, Any] = {}
    if body.browse_uris is not None:
        out["browse_uris"] = body.browse_uris
    if body.configs is not None:
        out["configs"] = body.configs
    return out


def _stage_or_404(stage_id: str):
    try:
        return stages.get(stage_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _run_or_404(run_id: str) -> Dict[str, Any]:
    run = await store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"No run '{run_id}'.")
    return run


# ── The manifest ──────────────────────────────────────────────────────────────
@router.get("/stages")
async def get_stages() -> Dict[str, Any]:
    """The stage manifest. THE FRONTEND RENDERS FROM THIS and keeps no table.

    AUX defines its step list twice — pipeline.py:145-160 and
    ProgressPanel.tsx:3-18 — and they have already drifted: three embedded
    labels disagree and embedded step 8 cannot be rendered at all. One source.
    """
    return stages.manifest()


# ── Lifecycle ─────────────────────────────────────────────────────────────────
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(body: CreateRun, _=Depends(require_auth)) -> Dict[str, Any]:
    run_id = await store.create_run(body.user_input, mode=body.mode, dry_run=body.dry_run)
    logger.info("[RUN %s] created (dry_run=%s)", run_id, body.dry_run)
    return {"run_id": run_id, "dry_run": body.dry_run,
            "first_stage": stages.first().id}


@router.get("")
async def list_runs(limit: int = 50) -> Dict[str, Any]:
    return {"runs": await store.list_runs(limit=limit)}


@router.get("/{run_id}")
async def get_run(run_id: str) -> Dict[str, Any]:
    """Everything needed to restore the UI after a refresh."""
    run = await _run_or_404(run_id)
    return {
        "run": run,
        "stages": await store.run_stages(run_id),
        "current_stage": run["current_stage"],
        "writes": await store.writes_for_run(run_id),
    }


@router.get("/{run_id}/writes")
async def get_writes(run_id: str, live_only: bool = False) -> Dict[str, Any]:
    """The audit trail: every QAD call this run made, request and response.

    In dry-run this is the rehearsal transcript — exactly what WOULD be sent.
    """
    await _run_or_404(run_id)
    return {"writes": await store.writes_for_run(run_id, live_only=live_only)}


# ── Stages ────────────────────────────────────────────────────────────────────
@router.get("/{run_id}/stage/{stage_id}")
async def get_stage(run_id: str, stage_id: str) -> Dict[str, Any]:
    """The stored artifact for a stage, plus whether it may be regenerated."""
    await _run_or_404(run_id)
    stage = _stage_or_404(stage_id)
    row = await store.get_stage(run_id, stage_id)
    if not row:
        raise HTTPException(status_code=404,
                            detail=f"Stage '{stage_id}' has not run yet.")
    allowed, reason = await store.can_regenerate(run_id, stage_id)
    return {
        "stage": stage_id,
        "label": stage.label,
        "gated": stage.gated,
        "artifact_kind": stage.artifact_kind,
        "editable": stage.editable,
        "status": row["status"],
        "attempt": row["attempt"],
        "artifact": row["artifact"],
        "can_regenerate": allowed,
        "regenerate_blocked_because": reason,
        "history": await store.stage_history(run_id, stage_id),
    }


@router.post("/{run_id}/stage/{stage_id}")
async def run_stage(run_id: str, stage_id: str, body: RunStage,
                    _=Depends(require_auth)) -> Dict[str, Any]:
    """Run a stage and return its artifact. WRITES NOTHING — approve does that."""
    await _run_or_404(run_id)
    _stage_or_404(stage_id)
    try:
        return await engine.run_stage(run_id, stage_id,
                                      instruction=body.instruction, **_kwargs(body))
    except engine.StageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[RUN %s] stage '%s' failed", run_id, stage_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{run_id}/stage/{stage_id}/approve")
async def approve_stage(run_id: str, stage_id: str,
                        _=Depends(require_auth)) -> Dict[str, Any]:
    """Approve a stage. THIS IS WHAT FIRES THE QAD WRITES."""
    await _run_or_404(run_id)
    _stage_or_404(stage_id)
    try:
        result = await engine.approve_stage(run_id, stage_id)
    except engine.StageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # A rejected write is a real outcome, not a server fault — 200 with the
    # detail, so the dialog can show QAD's own message and offer a retry.
    return result


@router.post("/{run_id}/stage/{stage_id}/regenerate")
async def regenerate_stage(run_id: str, stage_id: str, body: RunStage,
                           _=Depends(require_auth)) -> Dict[str, Any]:
    """Re-run a stage with a free-text steer, if the lock permits it."""
    await _run_or_404(run_id)
    _stage_or_404(stage_id)
    allowed, reason = await store.can_regenerate(run_id, stage_id)
    if not allowed:
        # 409, not 403: the request is well-formed and the caller is entitled to
        # make it — it conflicts with what has already happened in QAD.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=reason)
    try:
        return await engine.regenerate_stage(run_id, stage_id,
                                             instruction=body.instruction,
                                             **_kwargs(body))
    except engine.StageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{run_id}/stage/{stage_id}/skip")
async def skip_stage(run_id: str, stage_id: str, body: SkipStage,
                     _=Depends(require_auth)) -> Dict[str, Any]:
    """Skip a conditional stage. Only handler and lookups may be skipped."""
    await _run_or_404(run_id)
    _stage_or_404(stage_id)
    try:
        return await engine.skip_stage(run_id, stage_id, reason=body.reason)
    except engine.StageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
