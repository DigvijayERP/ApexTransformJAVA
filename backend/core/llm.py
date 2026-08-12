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

# Model choice lives in config.PROVIDERS, per provider. A stage passes a ROLE
# ("planning" / "generation"), never a model name, so switching providers or
# retuning a tier is one edit there rather than a hunt through the pipeline.

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

    s = config.llm_settings(role)
    chosen = model or s["model"]
    # NVIDIA NIM speaks the OpenAI protocol, so the same client serves both -
    # only base_url and the key differ.
    #
    # max_retries is raised well above the SDK's default of 2. A free NIM tier
    # rate-limits on calls seconds apart, and the form stage alone fires three
    # in a row; the SDK's sub-second backoff gives up long before the window
    # reopens. Losing a stage to a 429 costs the user a whole gate.
    client = AsyncOpenAI(api_key=s["api_key"], base_url=s["base_url"],
                         max_retries=s["max_retries"], timeout=s["timeout"])

    kwargs: Dict[str, Any] = {
        "model": chosen,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    if not chosen.startswith("gpt-5"):
        kwargs["max_tokens"] = s["max_tokens"]
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    logger.info("[LLM] %s via %s (%s)", role, chosen, s["provider"])
    try:
        resp = await _with_rate_limit_retry(client, kwargs, s)
    except Exception as exc:
        # NOT every model supports response_format. OpenAI does; several NIM
        # models reject it outright. Retry once without it rather than failing
        # the stage - parse_json already tolerates fences and surrounding prose,
        # and the prompts themselves demand raw JSON.
        if json_mode and _looks_like_json_mode_rejection(exc):
            logger.warning("[LLM] %s rejected response_format; retrying without it", chosen)
            kwargs.pop("response_format", None)
            kwargs["messages"][0]["content"] += (
                "\n\nCRITICAL: reply with RAW JSON only. No markdown, no fences, "
                "no prose before or after."
            )
            try:
                resp = await client.chat.completions.create(**kwargs)
            except Exception as exc2:
                raise LLMError(f"Model call failed: {exc2}") from exc2
        else:
            raise LLMError(f"Model call failed ({s['provider']}/{chosen}): {exc}") from exc
    return resp.choices[0].message.content or ""


async def _with_rate_limit_retry(client: Any, kwargs: Dict[str, Any],
                                 settings: Dict[str, Any]) -> Any:
    """Retry a 429 with real backoff, on top of the SDK's own retries.

    Free NIM tiers answer one call and refuse the next a few seconds later. The
    SDK backs off in fractions of a second and gives up; the window is longer
    than that. Waiting is cheap here because a gated run is already paced by a
    human, and losing the stage is not.
    """
    import asyncio

    delays = settings["rate_limit_backoff"]
    last: Exception | None = None
    for attempt, wait in enumerate([0.0, *delays]):
        if wait:
            logger.warning("[LLM] rate limited; waiting %.0fs before retry %d/%d",
                           wait, attempt, len(delays))
            await asyncio.sleep(wait)
        try:
            return await client.chat.completions.create(**kwargs)
        except Exception as exc:
            if not _is_rate_limit(exc):
                raise
            last = exc
    raise LLMError(
        f"Rate limited after {len(delays)} retries over "
        f"{int(sum(delays))}s. The provider's free tier allows very few calls "
        f"per minute; wait a moment and re-run this stage, or switch "
        f"LLM_PROVIDER. Nothing was written to QAD. ({last})"
    )


def _is_rate_limit(exc: Exception) -> bool:
    if getattr(exc, "status_code", None) == 429:
        return True
    blob = str(exc).lower()
    return "429" in blob or "too many requests" in blob or "rate limit" in blob


def _looks_like_json_mode_rejection(exc: Exception) -> bool:
    blob = str(exc).lower()
    return any(t in blob for t in
               ("response_format", "json_object", "json mode", "not supported"))


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
