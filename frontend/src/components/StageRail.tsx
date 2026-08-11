// The run's stages, rendered ENTIRELY from the backend manifest.
//
// There is no step table in this file, and there must never be one. AUX keeps
// its labels in both pipeline.py and ProgressPanel.tsx; they have already
// drifted, and one of its stages cannot be rendered at all because it falls
// outside the frontend's hardcoded list.

import { useRun } from "../RunContext";

const MARK: Record<string, string> = {
  approved: "✓", skipped: "–", failed: "✕",
  awaiting_approval: "●", running: "●", pending: "",
};

export function StageRail() {
  const { state, open } = useRun();
  const { stages, activeStage } = state;
  if (!stages.length) return null;

  return (
    <nav className="rail" aria-label="Stages">
      {stages.map((s) => {
        const active = s.id === activeStage;
        return (
          <button
            key={s.id}
            className={`rail-item ${s.status} ${active ? "active" : ""}`}
            onClick={() => open(s.id)}
            aria-current={active ? "step" : undefined}
          >
            <span className="mark" aria-hidden>{MARK[s.status] ?? ""}</span>
            <span className="rail-label">
              {s.number}. {s.label}
              {s.conditional && <em className="tag">optional</em>}
              {s.writes_to_qad && <em className="tag write" title="writes to QAD">writes</em>}
            </span>
            {s.attempts > 1 && <span className="attempts">{s.attempts} attempts</span>}
          </button>
        );
      })}
    </nav>
  );
}
