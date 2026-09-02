// The gate: what a stage produced, and the decision it is waiting on.
//
// Approving is what fires the QAD writes — running a stage never does. So the
// payload shown here is exactly what is about to be sent, and dry-run looks
// identical to live.

import { useState } from "react";
import { useRun } from "../RunContext";
import { Artifact } from "./Artifact";

export function StageGate() {
  const { state, stageMeta, open, run, approve, regenerate, skip } = useRun();
  const { activeStage, gate, busy, run: runRow } = state;
  const [steer, setSteer] = useState("");

  if (!activeStage) return null;
  const meta = stageMeta(activeStage);
  if (!meta) return null;

  const status = state.stages.find((s) => s.id === activeStage);
  const blocked = gate?.can_regenerate === false;
  const done = status?.status === "approved" || status?.status === "skipped";
  const working = busy !== null;

  // The rail lets a click open ANY stage's gate, approved or not - that is
  // how an embedded run's "view" write once fired before "deploy" did,
  // because the deploy gate was simply left open. The server refuses the
  // approve either way, but naming the real blocker here, before the click,
  // is what stops it from happening at all rather than erroring after.
  const firstUnresolved = state.stages.find(
    (s) => s.status !== "approved" && s.status !== "skipped");
  const outOfOrder = !done && firstUnresolved != null && firstUnresolved.id !== activeStage;

  return (
    <article className="gate">
      <header>
        <h2>{meta.number}. {meta.label}</h2>
        <p className="muted">{meta.description}</p>
        {meta.writes.length > 0 && (
          <p className="writes-note">
            Approving sends {meta.writes.length} call{meta.writes.length === 1 ? "" : "s"} to QAD
            {runRow?.dry_run && <strong> (dry run, nothing will actually be sent)</strong>}.
          </p>
        )}
      </header>

      {outOfOrder ? (
        <div className="empty">
          <p className="warn locked">
            '{stageMeta(firstUnresolved!.id)?.label ?? firstUnresolved!.id}' has not been
            approved yet. Opening this gate from the rail does not let its write
            jump ahead of one still waiting - approve stages in order.
          </p>
          <button disabled={working} onClick={() => open(firstUnresolved!.id)}>
            Go to '{stageMeta(firstUnresolved!.id)?.label ?? firstUnresolved!.id}'
          </button>
        </div>
      ) : !gate ? (
        <div className="empty">
          <p>This stage has not run yet.</p>
          <button disabled={working} onClick={() => run(activeStage)}>
            {working ? "Working…" : `Run ${meta.label.toLowerCase()}`}
          </button>
        </div>
      ) : gate.skipped ? (
        <div className="empty"><p className="muted">Skipped: {gate.reason}</p></div>
      ) : (
        <>
          {(gate.warnings ?? []).map((w, i) => (
            <p key={i} className="warn">{w}</p>
          ))}

          <div className="artifact">
            <Artifact
              kind={meta.artifact_kind}
              artifact={gate.artifact ?? {}}
              onBrowseUris={(browse_uris) => run(activeStage, { browse_uris })}
              onConfigure={(configs) => run(activeStage, { configs })}
              onParentKey={(parent_key) => run(activeStage, { parent_key })}
              onBcName={(bc_name) => run(activeStage, { bc_name })}
              onServersidePick={(v) => run(activeStage, v)}
            />
          </div>

          {!done && (
            <footer className="actions">
              {/* The label must state what the click ACTUALLY does. It used to
                  read "Approve and send" in both modes — in a dry run, "send"
                  is exactly what it does not do, and the owner twice completed
                  a whole rehearsal believing components were being created. The
                  truth belongs at the point of action, not only in a banner. */}
              <button className={`primary ${runRow?.dry_run ? "rehearse" : ""}`}
                      disabled={working}
                      onClick={() => approve(activeStage)}>
                {working ? "Working…"
                  : !meta.writes.length ? "Approve"
                  : runRow?.dry_run ? "Approve (rehearse only, sends nothing)"
                  : "Approve and send to QAD"}
              </button>

              {meta.conditional_on && (
                <button className="ghost" disabled={working}
                        onClick={() => skip(activeStage, "Not needed for this component")}>
                  Skip
                </button>
              )}

              <div className="steer">
                <input
                  value={steer}
                  disabled={working || blocked}
                  placeholder="Tell it what to change, then regenerate…"
                  onChange={(e) => setSteer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && steer.trim() && !blocked) {
                      regenerate(activeStage, { instruction: steer });
                      setSteer("");
                    }
                  }}
                />
                <button
                  className="ghost"
                  disabled={working || blocked || !steer.trim()}
                  onClick={() => { regenerate(activeStage, { instruction: steer }); setSteer(""); }}
                >
                  Regenerate
                </button>
              </div>

              {blocked && (
                <p className="warn locked">{gate.regenerate_blocked_because}</p>
              )}
            </footer>
          )}
        </>
      )}
    </article>
  );
}
