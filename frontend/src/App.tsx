import { useState } from "react";
import { token } from "./api";
import { useRun } from "./RunContext";
import { Artifact } from "./components/Artifact";
import { StageGate } from "./components/StageGate";
import { StageRail } from "./components/StageRail";

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

  return (
    <section className="start">
      <h2>Create a business component</h2>
      <p className="muted">
        Describe what you need, or paste Progress 4GL source. Each stage stops and
        shows you what it produced before anything reaches QAD.
      </p>

      <textarea
        rows={8}
        value={prompt}
        placeholder="e.g. a training room BC with a class name, location, start and end dates…"
        onChange={(e) => setPrompt(e.target.value)}
      />

      <label className="check">
        <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
        Dry run — build and show every payload, send nothing
      </label>

      {state.health && !state.health.auth_enforced ? null : (
        <label className="field">
          <span>API token</span>
          <input type="password" value={tok} placeholder="ADAPTIVE_API_TOKEN"
                 onChange={(e) => { setTok(e.target.value); token.set(e.target.value); }} />
        </label>
      )}

      <button className="primary" disabled={working || !prompt.trim()}
              onClick={() => start(prompt, dryRun)}>
        {working ? "Starting…" : "Start"}
      </button>
    </section>
  );
}

function Writes() {
  const { state } = useRun();
  if (!state.writes.length) return null;
  return (
    <details className="writes">
      <summary>{state.writes.length} QAD call{state.writes.length === 1 ? "" : "s"} so far</summary>
      <ul className="plain">
        {state.writes.map((w, i) => (
          <li key={i}>
            <code>{w.endpoint_id}</code>
            <span className={w.ok ? "ok" : "bad"}>{w.ok ? "ok" : "failed"}</span>
            {w.dry_run && <em className="tag">dry run</em>}
            {!w.locking && <em className="tag" title="does not lock regeneration">probe</em>}
          </li>
        ))}
      </ul>
      <Artifact kind={undefined} artifact={{ calls: state.writes.map((w) => w.request) }} />
    </details>
  );
}

export default function App() {
  const { state, reset, dismissError } = useRun();
  const started = state.runId !== null;

  return (
    <div className="app">
      <header className="top">
        <h1>Adaptive <small>(Java)</small></h1>
        {started && (
          <div className="run-meta">
            <span>{state.run?.bc_pascal ?? "unnamed"}</span>
            {state.run?.dry_run && <em className="tag">dry run</em>}
            <button className="ghost" onClick={reset}>New run</button>
          </div>
        )}
      </header>

      <Health />

      {state.error && (
        <div className="banner error" role="alert">
          <p>{state.error}</p>
          <button className="ghost" onClick={dismissError}>Dismiss</button>
        </div>
      )}

      {!started ? <Start /> : (
        <main className="run">
          <aside><StageRail /><Writes /></aside>
          <StageGate />
        </main>
      )}
    </div>
  );
}
