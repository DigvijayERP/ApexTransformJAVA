"""
The single transport layer to QAD. Nothing else in the codebase builds a QAD URL.

Every call names an endpoint by its registry `id`; the URL is resolved from
config/endpoints.json. That is what keeps the Phase 1 exit criterion true — no
endpoint literals anywhere in application code.

Three things this does that the AUX reference implementation does not:

  1. CACHES THE TOKEN. AUX calls get_token() immediately before every write —
     seven times per standard run (aux_web_version/backend/pipeline.py:434,475,
     514,596,684,708,737). Harmless for a run that finishes in one burst;
     wasteful and fragile once a run pauses at a human gate.

  2. REFRESHES ON 401 AND RETRIES ONCE. AUX has no refresh at all — a 401
     mid-run aborts the run. A gated run can sit at a dialog for hours, so token
     expiry stops being a corner case and becomes the normal path. The
     refresh-once-then-403-is-permissions behaviour matches the confirmed
     qad-java-sse-vscode contract.

  3. URL-ENCODES CREDENTIALS. AUX interpolates the password raw into a query
     string (qad_client.py:44), so a password containing & or # corrupts the
     request. Encoding happens in config.resolve_url().

DRY RUN: every write path accepts dry_run. When set, nothing leaves the process
and the returned QadResult carries the exact request that WOULD have been sent —
url, method, headers, payload — per working rule 5. The bearer value is masked;
the header is still shown so the shape is verifiable.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

from core import config
from core.logging_setup import get_logger

logger = get_logger("adaptive.qad")

# Refresh this many seconds before the token actually expires, so a call that
# starts just under the wire doesn't land just over it.
_EXPIRY_MARGIN_SECONDS = 60


@dataclass
class QadResult:
    """Outcome of one QAD call.

    `ok` means the HTTP call succeeded AND QAD's own submitResult envelope
    reports success. QAD returns HTTP 200 with success:false for business
    errors, so HTTP status alone is never sufficient.
    """
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    status_code: Optional[int] = None
    error: str = ""
    messages: list = field(default_factory=list)
    dry_run: bool = False
    request: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "status_code": self.status_code,
            "error": self.error,
            "messages": self.messages,
            "dry_run": self.dry_run,
            "request": self.request,
        }


# ── Token cache ───────────────────────────────────────────────────────────────
class _TokenCache:
    def __init__(self) -> None:
        self.access_token: str = ""
        self.refresh_token: str = ""
        self.expires_at: float = 0.0

    def valid(self) -> bool:
        return bool(self.access_token) and time.time() < (self.expires_at - _EXPIRY_MARGIN_SECONDS)

    def store(self, body: Dict[str, Any]) -> None:
        self.access_token = str(body.get("access_token", ""))
        self.refresh_token = str(body.get("refresh_token", ""))
        try:
            ttl = float(body.get("expires_in", 0))
        except (TypeError, ValueError):
            ttl = 0.0
        # A missing/zero expires_in means "assume short" rather than "assume
        # forever" — a stale token that looks fresh is the worse failure.
        self.expires_at = time.time() + (ttl if ttl > 0 else 300.0)

    def clear(self) -> None:
        self.access_token = ""
        self.refresh_token = ""
        self.expires_at = 0.0


_tokens = _TokenCache()


async def _post_token(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        return resp.json()


async def get_token(force: bool = False) -> str:
    """Return a valid bearer token, using the cache when possible."""
    if not force and _tokens.valid():
        return _tokens.access_token

    missing = config.missing_required_keys()
    if missing:
        raise RuntimeError(
            "Cannot authenticate to QAD — missing " + ", ".join(missing) +
            ". Set them in backend/.env."
        )

    url = config.resolve_url("auth.token.password")
    logger.info("[AUTH] acquiring token (password grant)")
    _tokens.store(await _post_token(url))
    return _tokens.access_token


async def refresh_token() -> str:
    """Refresh using the cached refresh_token; fall back to a full re-login.

    The confirmed plugin contract refreshes once on 401 and treats 403 as a
    permissions failure rather than an expiry.
    """
    if _tokens.refresh_token:
        try:
            url = config.resolve_url(
                "auth.token.refresh", {"refresh_token": _tokens.refresh_token}
            )
            logger.info("[AUTH] refreshing token")
            _tokens.store(await _post_token(url))
            return _tokens.access_token
        except Exception as exc:
            logger.warning("[AUTH] refresh failed (%s) — falling back to full login", exc)
    _tokens.clear()
    return await get_token(force=True)


def clear_token_cache() -> None:
    """Drop the cached token. Call after changing credentials or environment."""
    _tokens.clear()


# ── Response handling ─────────────────────────────────────────────────────────
def _error_messages(body: Dict[str, Any]) -> list:
    """Plain-English messages out of QAD's submitResult envelope, so a user sees
    'Entity metadata already exists (EntityURI)' rather than a raw JSON dump."""
    errs = (body or {}).get("submitResult", {}).get("errors") or []
    out = []
    for e in errs:
        if isinstance(e, dict):
            msg = (e.get("message") or "").strip()
            fld = (e.get("fieldName") or "").strip()
            if msg:
                out.append(f"{msg} ({fld})" if fld and fld.lower() not in msg.lower() else msg)
        elif e:
            out.append(str(e))
    return out


def is_submit_success(body: Dict[str, Any]) -> bool:
    """QAD's own success envelope. Absent envelope = treat as success, since the
    read endpoints do not return one."""
    if "submitResult" not in (body or {}):
        return True
    sr = body.get("submitResult") or {}
    return (
        sr.get("success") is True
        and sr.get("errorSeverity", 1) == 0
        and not sr.get("errors")
    )


def is_duplicate_entity_error(result: QadResult) -> bool:
    """True when QAD rejected a create because the name is already taken.

    This is a NAME COLLISION, not a schema problem — editing fields can never
    fix it. It is also the reason an already-executed BC create cannot simply be
    re-run, which is what makes upstream regeneration unsafe after stage 2.
    """
    return "already exist" in " ".join(result.messages).lower()


def _headers(token: str, content_type: bool = False) -> Dict[str, str]:
    h = {"Authorization": f"Bearer {token}"}
    if content_type:
        h["Content-Type"] = "application/json"
    return h


def _redacted(headers: Dict[str, str]) -> Dict[str, str]:
    out = dict(headers)
    if "Authorization" in out:
        out["Authorization"] = "Bearer <token>"
    return out


def _describe(method: str, url: str, headers: Dict[str, str],
              payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Exactly what would be sent — working rule 5's dry-run contract."""
    return {
        "method": method,
        "url": url,
        "headers": _redacted(headers),
        "payload": payload,
    }


# ── The call ──────────────────────────────────────────────────────────────────
async def call(
    endpoint_id: str,
    *,
    method: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    timeout: float = 60.0,
) -> QadResult:
    """Call a registry endpoint by id.

    `method` defaults to the method recorded in the registry.
    """
    entry = config.endpoint(endpoint_id)
    verb = (method or entry.get("method") or "GET").upper()
    url = config.resolve_url(endpoint_id, params)

    if dry_run:
        headers = _headers("<token>", content_type=(verb == "POST"))
        logger.info("[DRY-RUN] %s %s", verb, url)
        return QadResult(
            ok=True,
            dry_run=True,
            request=_describe(verb, url, headers, payload),
        )

    token = await get_token()
    result = await _execute(verb, url, token, payload, timeout)

    # One refresh-and-retry on 401, matching the confirmed plugin behaviour.
    if result.status_code == 401:
        logger.info("[AUTH] 401 on %s — refreshing and retrying once", endpoint_id)
        token = await refresh_token()
        result = await _execute(verb, url, token, payload, timeout)

    if result.status_code == 403:
        result.error = (
            f"QAD refused the request (HTTP 403) on '{endpoint_id}'. This is a "
            f"permissions failure, not an expired session — the user "
            f"'{config.qad_username()}' may lack rights on this app."
        )

    return result


async def _execute(verb: str, url: str, token: str,
                   payload: Optional[Dict[str, Any]], timeout: float) -> QadResult:
    headers = _headers(token, content_type=(verb == "POST"))
    request = _describe(verb, url, headers, payload)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if verb == "POST":
                resp = await client.post(url, json=payload, headers=headers)
            else:
                resp = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        return QadResult(ok=False, error=f"Could not reach QAD: {exc}", request=request)

    status = resp.status_code
    try:
        body = resp.json()
    except (ValueError, json.JSONDecodeError):
        snippet = (resp.text or "")[:500]
        return QadResult(
            ok=False, status_code=status, request=request,
            error=f"QAD returned a non-JSON response (HTTP {status}): {snippet}",
        )

    if resp.is_error:
        return QadResult(
            ok=False, data=body, status_code=status, request=request,
            messages=_error_messages(body),
            error=f"QAD HTTP {status}",
        )

    messages = _error_messages(body)
    ok = is_submit_success(body)
    return QadResult(
        ok=ok, data=body, status_code=status, request=request, messages=messages,
        error="" if ok else ("; ".join(messages) or "QAD rejected the request"),
    )


async def health() -> Dict[str, Any]:
    """Cheap reachability probe: can we get a token at all?

    Deliberately does NOT touch any business endpoint — it must be safe to call
    against a degraded environment, and this one is known-degraded.
    """
    try:
        await get_token(force=True)
        return {"reachable": True, "error": ""}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}
