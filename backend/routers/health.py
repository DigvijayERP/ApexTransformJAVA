"""
Health and diagnostics.

Deliberately answers the questions that are otherwise only discoverable by
watching a run fail:

  - Is QAD reachable, and does auth work?
  - Are the prompts actually GROUNDED, or is a docs bundle silently empty?
  - Is the API enforcing auth, or is it wide open?
  - Are we in dry-run, and what would a write look like?

`/api/health` never touches QAD. `/api/health/qad` does — a token request only,
which is safe against the known-degraded Adaptive environment and writes
nothing.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import qad_client
from core import auth, config, stages
from core.docs_loader import docs_loader

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health() -> Dict[str, Any]:
    """Offline health: configuration, grounding, and the auth posture.

    Makes NO network call, so it is safe to poll and safe to call when the
    environment is down.
    """
    docs = docs_loader.diagnose()
    status = config.public_status()

    warnings = []
    if not auth.is_enforced():
        warnings.append(
            "ADAPTIVE_API_TOKEN is not set - the approve and deploy endpoints are "
            "UNAUTHENTICATED. Anyone who can reach this server can deploy."
        )
    if docs["ungrounded"]:
        warnings.append(
            "Ungrounded prompt bundles: " + ", ".join(docs["ungrounded"]) +
            ". Generation will still run, but on model memory rather than the "
            "platform docs - judge its output more carefully."
        )
    if not status["qad_configured"]:
        warnings.append(
            "QAD credentials incomplete: " + ", ".join(config.missing_required_keys()))
    if not status["llm_configured"]:
        warnings.append(
            "LLM key missing: " + ", ".join(config.missing_llm_keys()) +
            " - stages 1, 2 and 3 cannot run.")

    return {
        "ok": not warnings,
        "warnings": warnings,
        "config": status,
        "auth_enforced": auth.is_enforced(),
        "docs": {
            "all_grounded": docs["all_grounded"],
            "ungrounded": docs["ungrounded"],
            "bundles": [
                {"name": b["name"], "bytes": b["bytes"], "files": b["files"],
                 "grounded": b["grounded"]}
                for b in docs["bundles"]
            ],
        },
        "pipeline": {
            "total_stages": stages.total(),
            "always_run": [s.id for s in stages.STAGES if not s.conditional_on],
            "conditional": [s.id for s in stages.STAGES if s.conditional_on],
        },
    }


@router.get("/qad")
async def qad_health() -> Dict[str, Any]:
    """Can we authenticate against QAD? Requests a token and nothing else.

    Touches no business endpoint on purpose: this environment is known-degraded
    (HTTP 500 on entity-metadata generation), and a health check that trips over
    that would report a false failure.
    """
    result = await qad_client.health()
    return {
        **result,
        "base_url": config.base_url(),
        "resolved_example": config.resolve_url("bc.create"),
    }
