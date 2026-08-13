// Run state as a reducer-backed state machine.
//
// No Zustand, deliberately: AUX has three runtime dependencies and records the
// decision in its own authStore header ("No Zustand added"). A gated run IS a
// state machine — idle -> running -> awaiting_approval(stage) -> approved — and
// useReducer is what that shape wants.
//
// The reducer holds NO stage list of its own. Stage identity comes from the
// backend manifest, which is the whole point: AUX defines its steps twice and
// the two have already drifted.

import {
  createContext, useCallback, useContext, useEffect, useMemo, useReducer, type ReactNode,
} from "react";
import {
  api, ApiError,
  type Health, type Manifest, type QadWrite, type Run, type RunMode,
  type StageInput, type StageRun, type StageStatus, type StoredStage,
} from "./api";

interface State {
  manifest: Manifest | null;
  health: Health | null;
  runId: string | null;
  run: Run | null;
  stages: StageStatus[];
  writes: QadWrite[];
  activeStage: string | null;
  gate: (StageRun & Partial<StoredStage>) | null;
  busy: string | null;
  error: string | null;
}

type Action =
  | { t: "boot"; manifest: Manifest; health: Health }
  | { t: "run"; runId: string; run: Run; stages: StageStatus[]; writes: QadWrite[]; current: string | null }
  | { t: "gate"; stage: string; gate: State["gate"] }
  | { t: "busy"; what: string | null }
  | { t: "error"; message: string | null }
  | { t: "reset" };

const initial: State = {
  manifest: null, health: null, runId: null, run: null,
  stages: [], writes: [], activeStage: null, gate: null, busy: null, error: null,
};

function reducer(s: State, a: Action): State {
  switch (a.t) {
    case "boot":   return { ...s, manifest: a.manifest, health: a.health };
    case "run":    return { ...s, runId: a.runId, run: a.run, stages: a.stages,
                            writes: a.writes, activeStage: a.current, error: null };
    case "gate":   return { ...s, activeStage: a.stage, gate: a.gate, error: null };
    case "busy":   return { ...s, busy: a.what };
    case "error":  return { ...s, error: a.message, busy: null };
    case "reset":  return { ...initial, manifest: s.manifest, health: s.health };
  }
}

interface Api {
  state: State;
  stageMeta: (id: string) => Manifest["stages"][number] | undefined;
  start: (prompt: string, dryRun: boolean, mode?: RunMode) => Promise<void>;
  open: (stage: string) => Promise<void>;
  run: (stage: string, input?: StageInput) => Promise<void>;
  approve: (stage: string) => Promise<void>;
  regenerate: (stage: string, input: StageInput) => Promise<void>;
  skip: (stage: string, reason?: string) => Promise<void>;
  resume: (runId: string) => Promise<void>;
  reset: () => void;
  dismissError: () => void;
}

const Ctx = createContext<Api | null>(null);

const RUN_KEY = "adaptive.runId";

export function RunProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initial);

  // One wrapper around every call, so no component ever hand-rolls
  // busy/error handling and they cannot drift apart.
  const guard = useCallback(async <T,>(what: string, fn: () => Promise<T>): Promise<T | null> => {
    dispatch({ t: "busy", what });
    try {
      const out = await fn();
      dispatch({ t: "busy", what: null });
      return out;
    } catch (e) {
      dispatch({ t: "error", message: e instanceof ApiError ? e.message : String(e) });
      return null;
    }
  }, []);

  const sync = useCallback(async (runId: string) => {
    const s = await api.getRun(runId);
    dispatch({ t: "run", runId, run: s.run, stages: s.stages,
               writes: s.writes, current: s.current_stage });
    return s;
  }, []);

  const open = useCallback(async (stage: string) => {
    await guard("Loading", async () => {
      try {
        const stored = await api.getStage(state.runId!, stage);
        dispatch({ t: "gate", stage, gate: stored });
      } catch (e) {
        // Not run yet is the normal case for the next stage, not an error.
        if (e instanceof ApiError && e.status === 404) dispatch({ t: "gate", stage, gate: null });
        else throw e;
      }
    });
  }, [guard, state.runId]);

  const runStage = useCallback(async (stage: string, input: StageInput = {}) => {
    const out = await guard("Working", () => api.runStage(state.runId!, stage, input));
    if (!out) return;
    if (out.skipped) {
      await sync(state.runId!);
      // The server names the next stage; it knows the run's mode and manifest.
      // Recomputing locally was a review finding: the local fallback assumes
      // the standard stage list and answers wrongly for embedded runs.
      const next = out.next ?? nextOf(state, stage);
      if (next) await open(next);
      return;
    }
    dispatch({ t: "gate", stage, gate: out });
    await sync(state.runId!);
  }, [guard, open, state, sync]);

  const value = useMemo<Api>(() => ({
    state,

    // Same-named stages differ between modes (the embedded view is gated, the
    // standard one is not), so metadata comes from the RUN's manifest.
    stageMeta: (id) => stagesOf(state).find((s) => s.id === id),

    start: async (prompt, dryRun, mode = "standard") => {
      const created = await guard("Starting", () => api.createRun(prompt, dryRun, mode));
      if (!created) return;
      localStorage.setItem(RUN_KEY, created.run_id);
      await sync(created.run_id);
      dispatch({ t: "gate", stage: created.first_stage, gate: null });
    },

    open,
    run: runStage,

    approve: async (stage) => {
      const res = await guard("Approving", () => api.approve(state.runId!, stage));
      if (!res) return;
      await sync(state.runId!);
      if (!res.approved) {
        dispatch({ t: "error", message: res.error ?? "QAD rejected this step." });
        return;
      }
      if (res.next) await open(res.next);
    },

    regenerate: async (stage, input) => {
      const out = await guard("Regenerating", () => api.regenerate(state.runId!, stage, input));
      if (!out) return;
      dispatch({ t: "gate", stage, gate: out });
      await sync(state.runId!);
    },

    skip: async (stage, reason = "") => {
      const res = await guard("Skipping", () => api.skip(state.runId!, stage, reason));
      if (!res) return;
      await sync(state.runId!);
      if (res.next) await open(res.next);
    },

    resume: async (runId) => {
      const s = await guard("Restoring", () => sync(runId));
      if (s?.current_stage) await open(s.current_stage);
    },

    reset: () => { localStorage.removeItem(RUN_KEY); dispatch({ t: "reset" }); },
    dismissError: () => dispatch({ t: "error", message: null }),
  }), [guard, open, runStage, state, sync]);

  // Boot: manifest + health, then restore an in-flight run if there is one.
  // Surviving a refresh is why state lives server-side; this is just the
  // client remembering which run it was looking at.
  useEffect(() => {
    (async () => {
      try {
        const [manifest, health] = await Promise.all([api.manifest(), api.health()]);
        dispatch({ t: "boot", manifest, health });
        const saved = localStorage.getItem(RUN_KEY);
        if (saved) {
          const s = await api.getRun(saved).catch(() => null);
          if (s) {
            dispatch({ t: "run", runId: saved, run: s.run, stages: s.stages,
                       writes: s.writes, current: s.current_stage });
            if (s.current_stage) {
              const stored = await api.getStage(saved, s.current_stage).catch(() => null);
              dispatch({ t: "gate", stage: s.current_stage, gate: stored });
            }
          } else localStorage.removeItem(RUN_KEY);
        }
      } catch (e) {
        dispatch({ t: "error", message: `Cannot reach the backend. ${String(e)}` });
      }
    })();
  }, []);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

/** The stage list for the CURRENT run's mode, falling back to standard. */
function stagesOf(s: State): Manifest["stages"] {
  const mode = s.run?.mode ?? "standard";
  return s.manifest?.modes?.[mode]?.stages ?? s.manifest?.stages ?? [];
}

function nextOf(s: State, stage: string): string | null {
  const ids = stagesOf(s).map((x) => x.id);
  const i = ids.indexOf(stage);
  return i >= 0 && i + 1 < ids.length ? ids[i + 1] : null;
}

export function useRun(): Api {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useRun must be used inside <RunProvider>");
  return ctx;
}
