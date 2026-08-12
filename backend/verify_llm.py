"""
One cheap call to the configured model. Confirms a provider works before a run
depends on it.

    cd backend && python verify_llm.py

Writes nothing to QAD and costs a handful of tokens. Run it after switching
LLM_PROVIDER or changing a model id - a wrong model name otherwise surfaces
halfway through stage 1, after the user has already typed their request.

It tests the two things the pipeline actually needs:

  1. PLAIN TEXT   - stages 1, 3 and 4 read prose.
  2. STRICT JSON  - stages 2 and 3 parse it. Not every model supports
     response_format; llm.complete retries without it and leans on the prompt,
     so this check confirms the FALLBACK works, not just the happy path.
"""
from __future__ import annotations

import asyncio
import sys

from core import config, llm
from core.logging_setup import configure_logging


async def main() -> int:
    configure_logging()
    print("\nLLM CHECK - writes nothing to QAD\n" + "=" * 62)

    try:
        s = config.llm_settings("generation")
    except config.ConfigError as exc:
        print(f"  config error: {exc}")
        return 1

    print(f"  provider      {s['provider']}")
    print(f"  model         {s['model']}")
    print(f"  base url      {s['base_url'] or '(provider default)'}")
    print(f"  token cap     {s['max_tokens']}")

    missing = config.missing_llm_keys()
    if missing:
        print(f"\n  Cannot call the model - {', '.join(missing)} is not set in backend/.env")
        return 1
    print(f"  key           present ({len(str(s['api_key']))} chars)")

    ok = True

    print("\n1. Plain text")
    print("-" * 62)
    try:
        out = await llm.complete(
            "You are a terse assistant. Answer in exactly one short sentence.",
            "Name the capital of France.", role="planning")
        print(f"  reply: {out.strip()[:110]}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        ok = False

    print("\n2. Strict JSON (the shape stages 2 and 3 depend on)")
    print("-" * 62)
    try:
        raw = await llm.complete(
            'Reply with ONLY raw JSON, no prose and no code fences: '
            '{"spec": {"bc_pascal": "Probe", "fields": [{"code": "testCode", '
            '"dataType": "character", "isPrimary": true}]}}',
            "Return exactly that object.", role="generation", json_mode=True)
        parsed = llm.parse_json(raw)
        spec = parsed.get("spec") or {}
        good = bool(spec.get("bc_pascal")) and bool(spec.get("fields"))
        print(f"  parsed ok: {good}   bc_pascal={spec.get('bc_pascal')!r} "
              f"fields={len(spec.get('fields') or [])}")
        if not good:
            print(f"  raw reply: {raw[:220]}")
            ok = False
    except Exception as exc:
        print(f"  FAILED: {exc}")
        ok = False

    print()
    print("=" * 62)
    if ok:
        print(f"{s['provider']} is usable. Stages 1-4 will run against {s['model']}.")
        return 0
    print("Not usable yet. Check the model id in your provider's console - a bad")
    print("id and a bad key fail differently, and the error above says which.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
