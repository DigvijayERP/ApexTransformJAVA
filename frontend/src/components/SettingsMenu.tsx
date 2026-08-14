import { useEffect, useRef, useState } from "react";
import { token } from "../api";
import { useRun } from "../RunContext";

/**
 * Header settings: a gear button and the panel it opens.
 *
 * The API token used to sit in the middle of the start screen, which put a
 * credential field in the primary flow and made it unreachable once a run had
 * started. It lives here instead, available at every point in a run.
 *
 * Status rows are read-only and come from the health report already loaded at
 * boot, so opening this panel costs no request. Status dot language is AUX's
 * (--status-* tokens), same as its settings surface.
 */

/** Feather-style gear, matching the icon set AUX uses in its sidebar. */
function GearIcon() {
  return (
    <svg
      width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"
    >
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

function StatusRow({ ok, on, off }: { ok: boolean; on: string; off: string }) {
  return (
    <div className="settings-status-row">
      <span className={`settings-status-dot ${ok ? "ok" : "bad"}`} aria-hidden="true" />
      <span className="settings-status-label">{ok ? on : off}</span>
    </div>
  );
}

export function SettingsMenu() {
  const { state } = useRun();
  const [open, setOpen] = useState(false);
  const [tok, setTok] = useState(token.get());
  const [reveal, setReveal] = useState(false);

  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Dismissal. pointerdown rather than click so the panel closes on the press
  // that starts an interaction elsewhere, not after it completes.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
    else setReveal(false);   // never leave a token on screen after closing
  }, [open]);

  const health = state.health;
  const enforced = health?.auth_enforced ?? false;

  return (
    <div className="settings-menu" ref={wrapRef}>
      <button
        type="button"
        className={`icon-btn ${open ? "on" : ""}`}
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="Settings"
        title="Settings"
      >
        <GearIcon />
      </button>

      {open && (
        <div className="settings-pop" role="dialog" aria-label="Settings">
          <div className="settings-section">
            <div className="settings-section-title">API token</div>

            <div className="settings-token-row">
              <input
                ref={inputRef}
                type={reveal ? "text" : "password"}
                value={tok}
                placeholder="ADAPTIVE_API_TOKEN"
                autoComplete="off"
                spellCheck={false}
                onChange={(e) => { setTok(e.target.value); token.set(e.target.value); }}
              />
              <button
                type="button"
                className="ghost"
                onClick={() => setReveal((r) => !r)}
                aria-pressed={reveal}
              >
                {reveal ? "Hide" : "Show"}
              </button>
            </div>

            <p className="settings-note">
              Stored in this browser and sent to the Adaptive backend as a bearer
              token. It never goes to QAD.
            </p>

            {enforced && !tok.trim() ? (
              <p className="settings-warn">
                This backend enforces a token. Writes will be rejected until one is set.
              </p>
            ) : (
              <p className="settings-note">
                {enforced
                  ? "This backend enforces a token on every write."
                  : "This backend is not enforcing a token, so one is optional."}
              </p>
            )}
          </div>

          <div className="settings-section last">
            <div className="settings-section-title">Backend</div>

            <StatusRow
              ok={health?.config.qad_configured ?? false}
              on="QAD connection configured"
              off="QAD connection not configured"
            />
            <StatusRow
              ok={health?.config.llm_configured ?? false}
              on="Language model configured"
              off="Language model not configured"
            />

            <div className="settings-readonly-value">
              {health?.config.base_url || "no QAD base URL set"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
