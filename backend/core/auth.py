"""
The auth seam for every route that can change something.

WHY THIS EXISTS AT ALL, THIS EARLY

The Phase 0 audit found that in AUX exactly ONE endpoint enforces identity.
`/api/run`, `/api/sss/generate` and `/api/sss/deploy` are open to any caller —
`main.py:66-94` adds CORS and rate limiting and includes every router with no
`dependencies=`, so nothing else is gated. That is survivable for a tool that
runs to completion in one burst on a developer's machine.

It is NOT survivable here. This application has an approve-and-deploy button
that writes business components into a live QAD environment, and QAD has no
undo. An unauthenticated caller who can POST to the approve endpoint can deploy.

HOW IT BEHAVES

  ADAPTIVE_API_TOKEN set    -> every mutating route requires
                              `Authorization: Bearer <token>`. Wrong or missing
                              token is a 401.
  ADAPTIVE_API_TOKEN unset  -> routes work, and every mutating request logs a
                              warning. `/api/health` reports
                              `auth_enforced: false` so the gap is VISIBLE
                              rather than assumed-handled.

Permissive-when-unset is a deliberate compromise, not an oversight: failing
closed with no token configured would make the app unusable out of the box, and
a developer would work around it by disabling auth entirely. Loud and visible
beats locked and bypassed. The moment a token is set, it is enforced.

This is a SEAM. Swapping in real JWT/OAuth later means changing this file only —
every route already depends on `require_auth`.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, status

from core import config
from core.logging_setup import get_logger

logger = get_logger("adaptive.auth")

_warned = False


def configured_token() -> str:
    return config._secret("ADAPTIVE_API_TOKEN")


def is_enforced() -> bool:
    return bool(configured_token().strip())


async def require_auth(authorization: Optional[str] = Header(default=None)) -> None:
    """FastAPI dependency. Attach to every route that changes state."""
    global _warned
    expected = configured_token().strip()

    if not expected:
        if not _warned:
            logger.warning(
                "ADAPTIVE_API_TOKEN is not set - mutating endpoints are UNAUTHENTICATED. "
                "Set it in backend/.env before this is reachable by anything but localhost."
            )
            _warned = True
        return

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supplied = authorization.split(" ", 1)[1].strip()
    # Constant-time compare: a naive == leaks token length and prefix through
    # timing, which is cheap to avoid and awkward to retrofit.
    import hmac
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
