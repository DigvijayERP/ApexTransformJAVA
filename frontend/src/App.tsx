import { useState } from "react";
import { type RunMode as Mode } from "./api";
import { useRun } from "./RunContext";
import { ApexLogo } from "./components/ApexLogo";
import { SettingsMenu } from "./components/SettingsMenu";
import { Payload } from "./components/Artifact";
import { StageGate } from "./components/StageGate";
import { StageRail } from "./components/StageRail";

const EXAMPLE_PROMPTS: Record<Mode, string[]> = {
  standard: [
    "Create a Dealer Order Header BC with fields: dealer code, PO number, order date, due date, total amount, and status.",
    "Create a Vendor Master BC with vendor code (PK), vendor name, country, payment terms, and active flag.",
  ],
  embedded: [
    "Extend Items with shipping details: a handling class, a customs code, and a hazard flag.",
    "Add order notes to Sales Order Headers: a sequence number per note, the note text, and an author.",
  ],
  serverside: [
    "Block saving a Purchase Order unless Remarks is filled in.",
    "Require a description on every DigSmokeTest record.",
    "Remove the remarks validation from purchase orders.",
  ],
};

function Health() {
  const { state } = useRun();
  const h = state.health;
  if (!h || h.ok) return null;
  return (
    <div className="banner">
      {h.warnings.map((w, i) => <p key={i}>{w}</p>)}
    </div>
  );
}

function Start() {
  const { state, start } = useRun();
  const [prompt, setPrompt] = useState("");
  const [dryRun, setDryRun] = useState(true);
  const [mode, setMode] = useState<Mode>("standard");
  const working = state.busy !== null;
  const canSend = !working && prompt.trim().length > 0;

  const send = () => canSend && start(prompt, dryRun, mode);

  return (
    <section className="start">
      <h2 className="hero-title">
        <strong>Adaptive</strong>&nbsp;<span className="brand-suffix">(Java)</span>
      </h2>
      <p className="hero-sub">
        Describe the business component you need, or paste Progress 4GL source.
        Every stage pauses and shows you exactly what it produced. Nothing
        reaches QAD without your approval.
      </p>

      {/* The mode changes the stage list, so it is chosen up front, not
          inferred from the prompt. The rail then renders that mode's manifest. */}
      <div className="segmented-toggle" role="tablist" aria-label="Run mode">
        <button role="tab" aria-selected={mode === "standard"}
                className={`segmented-toggle-btn ${mode === "standard" ? "active" : ""}`}
                onClick={() => setMode("standard")}>
          Standalone BC
        </button>
        <button role="tab" aria-selected={mode === "embedded"}
                className={`segmented-toggle-btn ${mode === "embedded" ? "active" : ""}`}
                onClick={() => setMode("embedded")}>
          Embedded BC (extends a parent)
        </button>
        <button role="tab" aria-selected={mode === "serverside"}
                className={`segmented-toggle-btn ${mode === "serverside" ? "active" : ""}`}
                onClick={() => setMode("serverside")}>
          Server-side rule (Java)
        </button>
      </div>

      <div className="composer">
        <textarea
          rows={3}
          value={prompt}
          placeholder={mode === "embedded"
            ? "e.g. extend Items with shipping details: a handling class and a customs code…"
            : "e.g. a training room BC with a class name, location, start and end dates…"}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
          }}
        />
        <div className="composer-foot">
          <label className={`dry-pill ${dryRun ? "on" : "off"}`} title="Dry run builds and shows every payload but sends nothing to QAD.">
            <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
            {dryRun ? "Dry run: sends nothing" : "LIVE: writes to QAD on approval"}
          </label>
          <span className="spacer" />
          {/* Naming the mode on the button itself. A round arrow says nothing
              about whether this run will touch QAD, and the dry-run default
              resets on every New run. */}
          <button className={`start-btn ${dryRun ? "" : "live"}`}
                  disabled={!canSend} onClick={send}>
            {working ? "Starting…" : dryRun ? "Start rehearsal" : "Start and write to QAD"}
          </button>
        </div>
      </div>

      <div className="example-prompts">
        {EXAMPLE_PROMPTS[mode].map((p) => (
          <button key={p} className="example-prompt" onClick={() => setPrompt(p)}>
            {p}
          </button>
        ))}
      </div>

      {/* The API token moved to the header's settings menu. A credential field
          does not belong in the primary flow, and there it was also unreachable
          once a run had started. */}
    </section>
  );
}

/** Whether this run is a rehearsal must be impossible to miss.
 *
 *  A completed dry run previously looked IDENTICAL to a real one — every stage
 *  ticked, "Deploy ✓" — with only a small badge in the corner to say otherwise.
 *  The owner reasonably concluded a component had been created and went looking
 *  for it in QAD. A rehearsal that reads as an accomplishment is worse than no
 *  feedback at all. */
function RunMode() {
  const { state } = useRun();
  const run = state.run;
  if (!run) return null;
  const done = run.status === "complete";

  if (run.dry_run) {
    return (
      <div className="banner mode-dry">
        <p>
          <strong>{done ? "Rehearsal complete. Nothing was created in QAD." : "Dry run: nothing is being sent to QAD."}</strong>{" "}
          {done
            ? "Every payload below was built and checked but never sent. To create this for real, start a new run and switch the dry-run pill off first."
            : "Every payload is built and shown exactly as it would be sent, then discarded."}
        </p>
      </div>
    );
  }

  return (
    <div className={`banner mode-live${done ? " done" : ""}`}>
      <p>
        <strong>{done ? "Created in QAD." : "Live: approving a stage writes to QAD."}</strong>{" "}
        {done
          ? run.mode === "embedded"
            ? `${run.bc_pascal} was deployed as an embedded extension. Open the parent component's screen in QAD and refresh: the extension grid and tab appear there.`
            : run.mode === "serverside"
              ? "The extension jar was uploaded. A successful upload is not proof the rule fires: open the screen in QAD and try to save a record that breaks it. You should be blocked, with a JEF error id."
              : `${run.bc_pascal} was deployed. Verify it by opening the view in QAD and saving a record.`
          : "QAD has no undo, so each gate shows the exact payload before it is sent."}
      </p>
    </div>
  );
}

function Writes() {
  const { state } = useRun();
  if (!state.writes.length) return null;
  return (
    <details className="writes">
      <summary>{state.writes.length} QAD call{state.writes.length === 1 ? "" : "s"} so far</summary>
      {/* Each call carries the exact request AND QAD's actual response body,
          straight from the qad_writes audit table. Dry-run calls have no
          response — nothing was sent — and Payload renders nothing for them. */}
      {state.writes.map((w, i) => (
        <details className="payload" key={i}>
          <summary>
            <code>{w.endpoint_id}</code>{" "}
            <span className={w.ok ? "ok" : "bad"}>{w.ok ? "ok" : "failed"}</span>
            {w.dry_run && <em className="tag">dry run</em>}
            {!w.locking && <em className="tag" title="fired while rendering a gate; does not lock regeneration">probe</em>}
          </summary>
          <Payload value={w.request} label="Request sent" />
          <Payload value={w.response} label="QAD's response" />
        </details>
      ))}
    </details>
  );
}

export default function App() {
  const { state, reset, dismissError } = useRun();
  const started = state.runId !== null;

  return (
    <div className="app">
      {/* Brand lockup copied from AUX's Header.tsx so both APEX apps present
          the same mark and wordmark. The app label after it is what separates
          this tab from the other one. */}
      <header className="app-header">
        <div className="app-header-brand">
          <ApexLogo size={26} />
          <span className="app-header-wordmark">
            <strong>Apex</strong>
            <span className="brand-suffix">Transform</span>
          </span>
          <span className="app-header-app"></span>
        </div>

        <div className="app-header-right">
          {started && (
            <div className="run-meta">
              <span>{state.run?.bc_pascal ?? "unnamed"}</span>
              {state.run?.mode === "embedded" && <em className="tag">embedded</em>}
              <em className={`tag ${state.run?.dry_run ? "" : "write"}`}>
                {state.run?.dry_run ? "dry run" : "live"}
              </em>
              <button className="ghost" onClick={reset}>New run</button>
            </div>
          )}
          <SettingsMenu />
        </div>
      </header>

      <div className="main-card">
        <Health />

        {state.error && (
          <div className="banner error" role="alert">
            <p>{state.error}</p>
            <button className="ghost" onClick={dismissError}>Dismiss</button>
          </div>
        )}

        {!started ? <Start /> : (
          <>
            <RunMode />
            <div className="user-bubble">
              <div className="user-bubble-label">Your request</div>
              {state.run?.user_input}
            </div>
            <main className="run">
              <aside><StageRail /><Writes /></aside>
              <StageGate />
            </main>
          </>
        )}
      </div>
    </div>
  );
}
