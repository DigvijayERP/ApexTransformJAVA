"""
A logging pass-through proxy, for capturing what a tool sends that a browser
cannot show you.

WHY THIS EXISTS
The VS Code plugin's "Build and Deploy" is the only thing that knows the JEF
deploy's multipart shape - part count, field names, filenames, content types.
It is not a browser, so F12 cannot see it, and the shape cannot be derived from
any document. Every other unknown on the JEF critical path has been settled by
reading; this one needs to be watched.

Point the plugin at this proxy instead of QAD:

    config/qad-sse.config.json
      "envUrl": "http://localhost:8899/clouderp/"      <- was https://eeadaptive…

then run the palette command. The plugin speaks plain HTTP to localhost, so
there is no certificate to install; this process re-issues each request over
HTTPS to the real environment and hands the real answer back. The deploy really
happens, which is the point: we capture the response too, not just the request.

    python capture_proxy.py

Writes a markdown transcript to captures/ and prints a live summary. Ctrl-C to
stop. PUT THE URL BACK when you are done.

SAFETY
  * The Authorization header is redacted in everything written to disk.
  * Bodies are summarised, not dumped: a 3 MB jar is reported by size and zip
    magic, never inlined.
  * It proxies to exactly one host, read from the project's own config, so a
    stray request cannot be forwarded somewhere else.
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from core import config

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8899

# Read from the project's endpoint registry rather than hardcoded: one place
# defines where this app may talk to, and the proxy inherits it.
TARGET = config.base_url().rstrip("/")
if TARGET.endswith("/clouderp"):
    # The plugin sends the context root as part of the path, so strip it from
    # the origin or it would be doubled.
    TARGET = TARGET[: -len("/clouderp")]

OUT_DIR = Path(__file__).resolve().parent.parent / "captures"
OUT_FILE = OUT_DIR / f"proxy_capture_{datetime.now(timezone.utc):%Y-%m-%d_%H%M%S}.md"

_lock = threading.Lock()
_seq = 0

# Headers we must not forward: hop-by-hop, or ones httpx recomputes.
_SKIP_REQUEST_HEADERS = {"host", "connection", "content-length", "accept-encoding",
                         "transfer-encoding", "keep-alive", "proxy-connection"}
_SKIP_RESPONSE_HEADERS = {"connection", "content-length", "transfer-encoding",
                          "content-encoding", "keep-alive"}


_SECRET_PARAMS = {"password", "client_secret", "refresh_token", "access_token",
                  "token", "pwd", "secret"}


def _redact_path(path: str) -> str:
    """Strip credentials out of a URL's query string.

    QAD's OAuth password grant puts username and password in QUERY PARAMETERS,
    not a body or header, so a proxy that only redacts headers would write the
    password to disk in clear text. Anything secret-shaped is masked before it
    reaches the console or the transcript.
    """
    head, sep, query = path.partition("?")
    if not sep:
        return path
    out = []
    for pair in query.split("&"):
        key, eq, value = pair.partition("=")
        if key.lower() in _SECRET_PARAMS and value:
            out.append(f"{key}={eq and ''}<redacted {len(value)} chars>")
        else:
            out.append(pair)
    return head + "?" + "&".join(out)


def _redact(headers: Dict[str, str]) -> Dict[str, str]:
    out = {}
    for k, v in headers.items():
        if k.lower() == "authorization":
            out[k] = f"<redacted, {len(v)} chars, starts {v[:12]!r}>"
        elif k.lower() == "cookie":
            out[k] = "<redacted>"
        else:
            out[k] = v
    return out


def _describe_body(body: bytes, content_type: str) -> str:
    """What a body IS, without inlining megabytes of it."""
    if not body:
        return "(empty)"
    ct = (content_type or "").lower()

    if "multipart/form-data" in ct:
        return _describe_multipart(body, content_type)

    if body[:2] == b"PK":
        return f"binary, {len(body)} bytes, ZIP/JAR magic (PK)"

    if any(t in ct for t in ("json", "text", "xml", "javascript", "urlencoded")):
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:
            return f"binary, {len(body)} bytes"
        if len(text) > 4000:
            return f"```\n{text[:4000]}\n… truncated, {len(body)} bytes total\n```"
        return f"```\n{text}\n```"

    return f"binary, {len(body)} bytes, content-type {content_type!r}"


def _describe_multipart(body: bytes, content_type: str) -> str:
    """THE POINT OF THIS WHOLE SCRIPT.

    Reports each part's field name, filename, content type and byte size, which
    together are the unproven half of the JEF deploy contract.
    """
    boundary = ""
    for chunk in (content_type or "").split(";"):
        chunk = chunk.strip()
        if chunk.lower().startswith("boundary="):
            boundary = chunk[len("boundary="):].strip().strip('"')
    if not boundary:
        return f"multipart, {len(body)} bytes, but no boundary in content-type {content_type!r}"

    sep = b"--" + boundary.encode()
    chunks = [c for c in body.split(sep) if c not in (b"", b"--", b"--\r\n", b"\r\n")]

    lines: List[str] = [f"**multipart/form-data**, boundary `{boundary}`, "
                        f"{len(chunks)} part(s), {len(body)} bytes total\n"]
    lines.append("| # | field name | filename | content-type | bytes | leading magic |")
    lines.append("|---|---|---|---|---|---|")
    for i, chunk in enumerate(chunks, 1):
        head, _, payload = chunk.partition(b"\r\n\r\n")
        head_text = head.decode("utf-8", errors="replace")
        field = filename = ctype = ""
        for line in head_text.splitlines():
            low = line.lower()
            if low.startswith("content-disposition:"):
                for piece in line.split(";"):
                    piece = piece.strip()
                    if piece.lower().startswith("name="):
                        field = piece[5:].strip().strip('"')
                    elif piece.lower().startswith("filename="):
                        filename = piece[9:].strip().strip('"')
            elif low.startswith("content-type:"):
                ctype = line.split(":", 1)[1].strip()
        payload = payload.rstrip(b"\r\n")
        magic = payload[:4].hex() if payload else ""
        note = " (PK/zip)" if payload[:2] == b"PK" else ""
        lines.append(f"| {i} | `{field}` | `{filename}` | `{ctype}` | {len(payload)} | `{magic}`{note} |")

    lines.append("\n<details><summary>raw part headers</summary>\n")
    for i, chunk in enumerate(chunks, 1):
        head, _, _ = chunk.partition(b"\r\n\r\n")
        lines.append(f"\npart {i}:\n```\n{head.decode('utf-8', errors='replace').strip()}\n```")
    lines.append("\n</details>")
    return "\n".join(lines)


def _record(text: str) -> None:
    with _lock:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with OUT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(text)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silence the default per-request noise
        pass

    def _proxy(self, method: str) -> None:
        global _seq
        with _lock:
            _seq += 1
            n = _seq

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        url = TARGET + self.path
        fwd = {k: v for k, v in self.headers.items()
               if k.lower() not in _SKIP_REQUEST_HEADERS}

        started = datetime.now(timezone.utc)
        try:
            with httpx.Client(timeout=600, follow_redirects=False) as client:
                resp = client.request(method, url, headers=fwd, content=body or None)
            err: Optional[Exception] = None
        except Exception as exc:  # noqa: BLE001 - report anything, then re-raise upstream
            resp, err = None, exc

        elapsed = (datetime.now(timezone.utc) - started).total_seconds()

        # ── console summary ────────────────────────────────────────────────
        status = f"{resp.status_code}" if resp is not None else f"FAILED {type(err).__name__}"
        ctype = self.headers.get("Content-Type", "")
        flag = "  <<< MULTIPART" if "multipart" in ctype.lower() else ""
        safe_path = _redact_path(self.path)
        print(f"[{n:03d}] {method} {safe_path[:80]} -> {status}  {elapsed:.2f}s{flag}", flush=True)

        # ── transcript ─────────────────────────────────────────────────────
        parts = [
            f"\n\n---\n\n## [{n:03d}] {method} {safe_path}\n",
            f"`{started.isoformat()}` &middot; {elapsed:.2f}s &middot; forwarded to "
            f"`{_redact_path(url)}`\n",
            "\n### Request headers\n```\n"
            + "\n".join(f"{k}: {v}" for k, v in _redact(dict(self.headers)).items())
            + "\n```\n",
            "\n### Request body\n" + _describe_body(body, ctype) + "\n",
        ]
        if resp is None:
            parts.append(f"\n### Result\n**REQUEST FAILED**: `{type(err).__name__}: {err}`\n")
        else:
            parts.append(f"\n### Response {resp.status_code}\n```\n"
                         + "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
                         + "\n```\n")
            parts.append("\n### Response body\n"
                         + _describe_body(resp.content, resp.headers.get("content-type", ""))
                         + "\n")
        _record("".join(parts))

        # ── hand the real answer back to the plugin ────────────────────────
        if resp is None:
            self.send_error(502, "capture proxy could not reach QAD")
            return
        self.send_response(resp.status_code)
        for k, v in resp.headers.items():
            if k.lower() not in _SKIP_RESPONSE_HEADERS:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(resp.content)))
        self.end_headers()
        self.wfile.write(resp.content)

    def do_GET(self):     self._proxy("GET")
    def do_POST(self):    self._proxy("POST")
    def do_PUT(self):     self._proxy("PUT")
    def do_DELETE(self):  self._proxy("DELETE")
    def do_PATCH(self):   self._proxy("PATCH")
    def do_HEAD(self):    self._proxy("HEAD")


def main() -> int:
    header = (
        f"# Capture proxy transcript\n\n"
        f"Started `{datetime.now(timezone.utc).isoformat()}`  \n"
        f"Listening `http://{LISTEN_HOST}:{LISTEN_PORT}` and forwarding to `{TARGET}`\n\n"
        f"Authorization headers are redacted. Bodies are summarised, not dumped.\n"
    )
    _record(header)

    print("=" * 68)
    print(f"  capture proxy  ->  {TARGET}")
    print(f"  listening on   ->  http://{LISTEN_HOST}:{LISTEN_PORT}")
    print(f"  transcript     ->  {OUT_FILE}")
    print("=" * 68)
    print("\nSet config/qad-sse.config.json:")
    print(f'    "envUrl": "http://{LISTEN_HOST}:{LISTEN_PORT}/clouderp/"')
    print("\nthen run the VS Code palette command. Ctrl-C when done.\n")

    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nstopped. {_seq} request(s) captured -> {OUT_FILE}")
        print("REMEMBER to put envUrl back to the real environment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
