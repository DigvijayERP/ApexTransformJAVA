"""
Structured logging.

Writes to BOTH backend/logs/app.log (rotating) and stdout, so every operation is
visible in the terminal and in log aggregators.

ASCII-ONLY MESSAGES. A Windows cp1252 console raises UnicodeEncodeError on
characters like arrows and em-dashes, which crashes the log call itself. AUX
learned this the hard way in its SSS pipeline; do not reintroduce it. Keep log
strings ASCII even where the surrounding code uses unicode freely.

Nothing here logs a credential. `qad_client` masks the bearer before any request
is described, and config never hands raw secrets to a caller that logs.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotent root-logger setup: rotating file + stdout."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    root = logging.getLogger()
    root.setLevel(level)

    # Drop handlers we previously added, so reload/tests don't stack duplicates.
    for handler in list(root.handlers):
        if getattr(handler, "_adaptive", False):
            root.removeHandler(handler)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler._adaptive = True  # type: ignore[attr-defined]

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler._adaptive = True  # type: ignore[attr-defined]

    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # httpx logs every request URL at INFO — including the oauth/token call,
    # whose QUERY STRING carries the username and password. Our own code never
    # prints that URL; the library must not either. WARNING keeps real
    # transport errors visible.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_operation(logger: logging.Logger, operation: str, ok: bool, detail: str = "") -> None:
    """Uniform outcome line: [OK]/[FAIL] operation :: detail. ASCII-safe."""
    msg = f"[{'OK' if ok else 'FAIL'}] {operation}"
    if detail:
        msg += f" :: {detail}"
    (logger.info if ok else logger.error)(msg)
