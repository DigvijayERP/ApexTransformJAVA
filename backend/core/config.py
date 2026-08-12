"""
Single source of truth for configuration.

Reads three sources and merges them with clear precedence:
  1. os.environ                  - highest. Docker/CI injection wins over files.
  2. backend/.env                - secrets, per-machine values.
  3. config/environment.json     - non-secret environment identity (committed).
  4. config/endpoints.json       - the endpoint registry (committed, static).

Files are re-read when their mtime changes, so editing a value is picked up
without a server restart.

Two deliberate differences from the AUX reference implementation:

  * AUX uses `dotenv_values()` alone, which reads a PHYSICAL FILE and ignores
    `os.environ` entirely. That is confirmed trap #4 in the build brief — it
    breaks Docker `env_file:` injection. Here the file is the FALLBACK and the
    real environment wins, so both work.

  * AUX hardcodes `/qad-central/` into the URL in three places
    (aux_web_version/backend/qad_client.py:44,:57,:65). Here the URL shape comes
    from the registry, because the Adaptive base URL already carries its own
    context root (/clouderp) in that slot.

Secrets are held server-side only. `public_status()` returns non-secret values
and boolean "is it configured" flags; raw secrets never go to the browser.
"""
from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote

from dotenv import dotenv_values

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
CONFIG_DIR = _REPO_ROOT / "config"

ENV_PATH = _BACKEND_DIR / ".env"
ENDPOINTS_PATH = CONFIG_DIR / "endpoints.json"
ENVIRONMENT_PATH = CONFIG_DIR / "environment.json"

# Keys the app needs non-empty before it can do anything against QAD.
REQUIRED_ENV_KEYS = ("QAD_CLIENT_ID", "QAD_USERNAME", "QAD_PASSWORD")

_lock = threading.Lock()
_caches: Dict[str, Dict[str, Any]] = {
    "env": {"mtime": None, "data": {}},
    "endpoints": {"mtime": None, "data": {}},
    "environment": {"mtime": None, "data": {}},
}


class ConfigError(RuntimeError):
    """Configuration is missing or malformed. Message is user-facing."""


def _read_cached(path: Path, key: str, parser: Callable[[Path], Dict[str, Any]]) -> Dict[str, Any]:
    """Re-read `path` only when its mtime changes (live pickup, no restart)."""
    cache = _caches[key]
    with _lock:
        try:
            mtime = path.stat().st_mtime if path.exists() else None
        except OSError:
            mtime = None
        if mtime != cache["mtime"]:
            cache["mtime"] = mtime
            cache["data"] = parser(path) if mtime is not None else {}
        return dict(cache["data"])


def _parse_json(p: Path) -> Dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigError(f"{p.name} is not valid JSON: {exc}") from exc


def _env_file() -> Dict[str, str]:
    return _read_cached(
        ENV_PATH, "env",
        lambda p: {k: v for k, v in dotenv_values(p).items() if v is not None},
    )


def _secret(key: str, default: str = "") -> str:
    """os.environ wins over backend/.env — this is the trap-4 fix."""
    from_environ = os.environ.get(key)
    if from_environ not in (None, ""):
        return from_environ
    return _env_file().get(key, default)


def endpoints() -> Dict[str, Any]:
    return _read_cached(ENDPOINTS_PATH, "endpoints", _parse_json)


def environment() -> Dict[str, Any]:
    return _read_cached(ENVIRONMENT_PATH, "environment", _parse_json)


def _active_env() -> Dict[str, Any]:
    doc = environment()
    name = doc.get("active")
    envs = doc.get("environments") or {}
    if name not in envs:
        raise ConfigError(
            f"config/environment.json: active environment '{name}' is not defined. "
            f"Available: {', '.join(envs) or '(none)'}"
        )
    return envs[name]


# ── Environment identity ──────────────────────────────────────────────────────
def active_environment_name() -> str:
    return str(environment().get("active", ""))


def base_url() -> str:
    return str(_active_env().get("base_url", "")).rstrip("/")


def app_uri() -> str:
    return str(_active_env().get("app_uri", ""))


def context_root() -> str:
    return str(_active_env().get("context_root", "")).strip("/")


# ── App identity — replaces AUX's five hardcoded builder constants ────────────
def app_identity() -> Dict[str, str]:
    """module / module_short / app_name / datastore_uri.

    Every urn in every payload derives from `module`. AUX hardcodes these at
    module level in bc_builder, form_builder, view_builder,
    event_handler_builder and deploy_builder; here they are injected so the same
    builder code can target any app.
    """
    ident = _active_env().get("app_identity") or {}
    missing = [k for k in ("module", "module_short", "app_name", "datastore_uri")
               if not str(ident.get(k) or "").strip()]
    if missing:
        raise ConfigError(
            f"config/environment.json: app_identity is missing {', '.join(missing)}. "
            f"These cannot be defaulted: app_name must match QAD's app list and "
            f"datastore_uri is environment-specific."
        )
    return {k: str(v) for k, v in ident.items()}


# ── Secrets (server-side only; never returned to the browser) ─────────────────
def qad_client_id() -> str: return _secret("QAD_CLIENT_ID")
def qad_username() -> str: return _secret("QAD_USERNAME")
def qad_password() -> str: return _secret("QAD_PASSWORD")
def openai_api_key() -> str: return _secret("OPENAI_API_KEY")
def openai_model() -> str: return _secret("OPENAI_MODEL", "gpt-4o")


# ── LLM provider ──────────────────────────────────────────────────────────────
# A NAME, not a pair of booleans. Two flags can both be true, which is a state
# with no correct answer; a name cannot contradict itself.
#
# NVIDIA NIM speaks the OpenAI wire protocol, so switching providers is a
# base_url and a key - not a second client.
PROVIDERS = {
    "openai": {
        "base_url": None,                       # the SDK's own default
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o",
        "planning_model": "gpt-4o-mini",
        "max_tokens": 15000,
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        # The free tier refuses calls seconds apart, and the form stage fires
        # three in a row. Measured: two calls 3s apart already returned 429.
        "max_retries": 5,
        "timeout": 180.0,
        "rate_limit_backoff": (5, 12, 25, 40),
        "key_env": "NVIDIA_API_KEY",
        "model_env": "NVIDIA_MODEL",
        "default_model": "meta/llama-3.3-70b-instruct",
        # Same model for both tiers by default: NVIDIA's pricing is far flatter
        # than OpenAI's, so a cheap-tier swap buys little and costs quality on
        # the JSON-shaped steps.
        "planning_model": "meta/llama-3.3-70b-instruct",
        # Deliberately lower than OpenAI's. Most NIM models cap output far below
        # 15k and reject the request outright rather than truncating.
        "max_tokens": 8192,
    },
}


def llm_provider() -> str:
    name = (_secret("LLM_PROVIDER", "openai") or "openai").strip().lower()
    if name not in PROVIDERS:
        raise ConfigError(
            f"LLM_PROVIDER is '{name}'. Known providers: {', '.join(sorted(PROVIDERS))}."
        )
    return name


def llm_settings(role: str = "generation") -> Dict[str, Any]:
    """Everything one model call needs: key, base_url, model, token cap."""
    name = llm_provider()
    p = PROVIDERS[name]
    configured = _secret(p["model_env"], "")
    return {
        "provider": name,
        "api_key": _secret(p["key_env"]),
        "base_url": p["base_url"],
        "model": configured or (p["planning_model"] if role == "planning"
                                else p["default_model"]),
        "max_tokens": p["max_tokens"],
        "key_env": p["key_env"],
        "max_retries": p.get("max_retries", 2),
        "timeout": p.get("timeout", 120.0),
        # Seconds to wait between 429 retries. NVIDIA's free tier refuses calls
        # seconds apart, and its window is longer than the SDK's sub-second
        # backoff, so these are deliberately generous.
        "rate_limit_backoff": p.get("rate_limit_backoff", (2, 5, 10)),
    }


# ── Endpoint resolution ───────────────────────────────────────────────────────
def _all_endpoint_entries() -> Dict[str, Dict[str, Any]]:
    doc = endpoints()
    out: Dict[str, Dict[str, Any]] = {}
    groups = list((doc.get("phases") or {}).values())
    not_ported = doc.get("not_ported")
    if not_ported:
        groups.append(not_ported)
    for group in groups:
        for entry in group.get("endpoints") or []:
            eid = entry.get("id")
            if eid:
                out[eid] = entry
    return out


def endpoint(endpoint_id: str) -> Dict[str, Any]:
    """Look an endpoint up by id. Raises rather than returning a default —
    a silently-wrong endpoint is worse than a loud failure."""
    entry = _all_endpoint_entries().get(endpoint_id)
    if entry is None:
        raise ConfigError(
            f"No endpoint '{endpoint_id}' in config/endpoints.json. "
            f"Known ids: {', '.join(sorted(_all_endpoint_entries()))}"
        )
    return entry


def list_endpoints() -> List[str]:
    return sorted(_all_endpoint_entries())


def _join(*parts: str) -> str:
    return "/".join(p.strip("/") for p in parts if p and p.strip("/"))


def resolve_url(endpoint_id: str, params: Optional[Dict[str, str]] = None) -> str:
    """Build the absolute URL for an endpoint id, substituting {placeholders}.

    Placeholders resolved automatically: {client_id} {username} {password}
    {app_uri}. Anything else must be supplied in `params`.

    Query values are URL-encoded — AUX does NOT encode the password
    (aux_web_version/backend/qad_client.py:44), so a password containing '&' or
    '#' silently corrupts the request there.
    """
    entry = endpoint(endpoint_id)
    doc = endpoints()
    shape = doc.get("url_shape") or {}

    supplied = dict(params or {})
    auto = {
        "client_id": qad_client_id(),
        "username": qad_username(),
        "password": qad_password(),
        "app_uri": app_uri(),
    }
    for k, v in auto.items():
        supplied.setdefault(k, v)

    path = str(entry.get("path", ""))
    is_oauth = path.startswith("oauth/")
    root = "" if is_oauth else str(shape.get("api_root", "api/qracore"))

    url = base_url() + "/" + _join(context_root(), root, path)

    # Substitute {placeholders} ANYWHERE in a value, not only when the value is
    # exactly "{name}". lookup.browse_fields embeds one mid-string
    # ("browseURI,eq,{browse_uri},literal"); the whole-value-only check sent
    # the braces to QAD literally, which matched nothing and returned 200 with
    # zero rows - so the failure was silent.
    def _substitute(match: "re.Match[str]") -> str:
        name = match.group(1)
        if name not in supplied:
            raise ConfigError(
                f"Endpoint '{endpoint_id}' needs a value for '{name}' and none was supplied."
            )
        return str(supplied[name])

    query = entry.get("query") or {}
    pairs = []
    for key, raw in query.items():
        value = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", _substitute, str(raw))
        pairs.append(f"{quote(key, safe='')}={quote(value, safe='')}")

    return f"{url}?{'&'.join(pairs)}" if pairs else url


# ── Readiness ─────────────────────────────────────────────────────────────────
def missing_required_keys() -> List[str]:
    return [k for k in REQUIRED_ENV_KEYS if not str(_secret(k) or "").strip()]


def missing_llm_keys() -> List[str]:
    """Only the ACTIVE provider's key matters. Complaining about an OpenAI key
    while running on NVIDIA would be noise."""
    s = llm_settings()
    return [] if str(s["api_key"] or "").strip() else [s["key_env"]]


def public_status() -> Dict[str, Any]:
    """Browser-safe view: NO raw secrets. Non-secret values + configured flags."""
    try:
        ident = app_identity()
        identity_error = ""
    except ConfigError as exc:
        ident = {}
        identity_error = str(exc)
    return {
        "environment": active_environment_name(),
        "base_url": base_url(),
        "app_uri": app_uri(),
        "app_identity": ident,
        "identity_error": identity_error,
        "qad_username": qad_username(),
        "llm_provider": llm_provider(),
        "llm_model": llm_settings()["model"],
        "has_qad_password": bool(qad_password().strip()),
        "has_qad_client_id": bool(qad_client_id().strip()),
        "has_llm_key": bool(str(llm_settings()["api_key"] or "").strip()),
        "qad_configured": not missing_required_keys(),
        "llm_configured": not missing_llm_keys(),
        "endpoint_count": len(_all_endpoint_entries()),
    }
