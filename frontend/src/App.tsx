import { useState } from "react";
import { token } from "./api";
import { useRun } from "./RunContext";
import { Payload } from "./components/Artifact";
import { StageGate } from "./components/StageGate";
import { StageRail } from "./components/StageRail";

const EXAMPLE_PROMPTS = [
  "Create a Dealer Order Header BC with fields: dealer code, PO number, order date, due date, total amount, and status.",
  "Create a Vendor Master BC with vendor code (PK), vendor name, country, payment terms, and active flag.",
];

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
  const [tok, setTok] = useState(token.get());
  const working = state.busy !== null;
  const canSend = !working && prompt.trim().length > 0;

  const send = () => canSend && start(prompt, dryRun);

  return (
    <section className="start">
      <h2 className="hero-title">
        <strong>Adaptive</strong>&nbsp;<span className="brand-suffix">(Java)</span>
      </h2>
      <p className="hero-sub">
        Describe the business component you need, or paste Progress 4GL source.
        Every stage pauses and shows you exactly what it produced — nothing
        reaches QAD without your approval.
      </p>

      <div className="composer">
        <textarea
          rows={3}
          value={prompt}
          placeholder="e.g. a training room BC with a class name, location, start and end dates…"
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
          }}
        />
        <div className="composer-foot">
          <label className={`dry-pill ${dryRun ? "on" : "off"}`} title="Dry run builds and shows every payload but sends nothing to QAD.">
            <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
            {dryRun ? "Dry run — sends nothing" : "LIVE — writes to QAD on approval"}
          </label>
          <span className="spacer" />
          {/* Naming the mode on the button itself. A round arrow says nothing
              about whether this run will touch QAD, and the dry-run default
              resets on every New run. */}
          <button className={`start-btn ${dryRun ? "" : "live"}`}
                  disabled={!canSend} onClick={send}>
            {working ? "Starting…" : dryRun ? "Start rehearsal" : "Start — writes to QAD"}
          </button>
        </div>
      </div>

      <div className="example-prompts">
        {EXAMPLE_PROMPTS.map((p) => (
          <button key={p} className="example-prompt" onClick={() => setPrompt(p)}>
            {p}
          </button>
        ))}
      </div>

      {state.health?.auth_enforced && (
        <label className="field" style={{ width: "100%", maxWidth: 560 }}>
          <span>API token</span>
          <input type="password" value={tok} placeholder="ADAPTIVE_API_TOKEN"
                 onChange={(e) => { setTok(e.target.value); token.set(e.target.value); }} />
        </label>
      )}
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
          <strong>{done ? "REHEARSAL COMPLETE — nothing was created in QAD." : "DRY RUN — nothing is being sent to QAD."}</strong>{" "}
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
        <strong>{done ? "CREATED IN QAD." : "LIVE — approving a stage writes to QAD."}</strong>{" "}
        {done
          ? `${run.bc_pascal} was deployed. Verify it by opening the view in QAD and saving a record.`
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
      <header className="top">
        <h1 className="wordmark">
          Adaptive <span className="brand-suffix">(Java)</span>
        </h1>
        {started && (
          <div className="run-meta">
            <span>{state.run?.bc_pascal ?? "unnamed"}</span>
            <em className={`tag ${state.run?.dry_run ? "" : "write"}`}>
              {state.run?.dry_run ? "dry run" : "live"}
            </em>
            <button className="ghost" onClick={reset}>New run</button>
          </div>
        )}
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
