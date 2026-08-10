"""
The one place the pipeline talks to a language model.

Two reasons it is a module rather than an inline client:

  1. TESTS MUST NOT NEED AN API KEY. `set_stub()` swaps the call for a canned
     responder, so the end-to-end dry run exercises every real builder, the real
     store and the real gating logic with no network and no key. That is what
     lets the whole flow be rehearsed before credentials arrive.

  2. One place to change the model. AUX pins models per step in a MODEL_MATRIX
     (aux_web_version/backend/pipeline.py:136-140) but its settings model
     selector does NOT affect the BC pipeline at all - the matrix is hardcoded,
     so choosing a model in the UI silently does nothing. Here the configured
     model is the default and a stage may override it explicitly.
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Optional

from core import config
from core.logging_setup import get_logger

logger = get_logger("adaptive.llm")

# Per-stage tiers. A stage passes a role, not a model name, so retuning is one
# edit here rather than a hunt through the pipeline.
MODEL_TIERS = {
    "planning": "gpt-4o-mini",
    "generation": "gpt-4o",
}

_stub: Optional[Callable[..., Awaitable[str]]] = None


class LLMError(RuntimeError):
    """The model call failed or returned something unusable."""


def set_stub(fn: Optional[Callable[..., Awaitable[str]]]) -> None:
    """Swap the model for a canned responder. Pass None to restore."""
    global _stub
    _stub = fn


def is_stubbed() -> bool:
    return _stub is not None


async def complete(system: str, user: str, *, role: str = "generation",
                   json_mode: bool = False, model: Optional[str] = None) -> str:
    if _stub is not None:
        return await _stub(system=system, user=user, role=role, json_mode=json_mode)

    missing = config.missing_llm_keys()
    if missing:
        raise LLMError(
            "Cannot call the model - missing " + ", ".join(missing) +
            ". Set it in backend/.env, or run with a stub."
        )

    # Refuse to spend a real call on a placeholder prompt. A prompt that is 80%
    # right does not fail - it silently produces a plausible, wrong design.
    from agents import prompts
    prompts.assert_ported()

    from openai import AsyncOpenAI

    chosen = model or MODEL_TIERS.get(role) or config.openai_model()
    client = AsyncOpenAI(api_key=config.openai_api_key())
    kwargs: Dict[str, Any] = {
        "model": chosen,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    if not chosen.startswith("gpt-5"):
        kwargs["max_tokens"] = 15000
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    logger.info("[LLM] %s via %s", role, chosen)
    try:
        resp = await client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise LLMError(f"Model call failed: {exc}") from exc
    return resp.choices[0].message.content or ""


def parse_json(raw: str) -> Any:
    """Parse a model's JSON, tolerating fences and surrounding prose.

    Ported from aux_web_version/backend/pipeline.py:195-206 - the same
    defences, because the same failure modes apply.
    """
    text = (raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:] if lines[0].startswith("```") else lines)
        if text.endswith("```"):
            text = text[: text.rfind("```")].rstrip()
    start = next((i for i, c in enumerate(text) if c in "{["), 0)
    end = max(text.rfind("}"), text.rfind("]")) + 1
    if end <= start:
        raise LLMError(f"No JSON found in the model's reply: {text[:200]!r}")
    try:
        return json.loads(text[start:end])
    except ValueError as exc:
        raise LLMError(f"Model returned invalid JSON: {exc}") from exc
