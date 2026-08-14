// Typed client for the run API. One place that knows about HTTP.
//
// The token, when set, is the ADAPTIVE_API_TOKEN the backend enforces on every
// mutating route. Reads work without it.

const TOKEN_KEY = "adaptive.token";

export const token = {
  get: () => localStorage.getItem(TOKEN_KEY) ?? "",
  set: (v: string) => v ? localStorage.setItem(TOKEN_KEY, v) : localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
  /** A blocked regeneration. The message carries the reason and the way out. */
  get isConflict() { return this.status === 409; }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const t = token.get();
  if (t) headers.Authorization = `Bearer ${t}`;

  const resp = await fetch(path, { ...init, headers: { ...headers, ...init?.headers } });
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = body?.detail;
    throw new ApiError(
      resp.status,
      typeof detail === "string" ? detail
        : Array.isArray(detail) ? detail.map((d: any) => d.msg ?? String(d)).join("; ")
        : `Request failed (${resp.status})`,
    );
  }
  return body as T;
}

const post = <T,>(path: string, body?: unknown) =>
  call<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });

// ── Types mirroring the backend ──────────────────────────────────────────────
export type ArtifactKind =
  | "text" | "field_spec" | "field_spec_diff" | "form_layout"
  | "handler_code" | "view_config" | "lookup_config" | "deploy_preview"
  | "embedded_requirements" | "relation_config"
  | "serverside_target" | "serverside_code" | "serverside_build"
  | "serverside_deploy";

export type RunMode = "standard" | "embedded" | "serverside";

export interface Stage {
  id: string;
  number: number;
  label: string;
  description: string;
  gated: boolean;
  writes: string[];
  artifact_kind: ArtifactKind;
  editable: boolean;
  conditional_on: string | null;
}

// Per-mode since Case 2. The legacy top-level stage list mirrors "standard";
// everything here reads modes[run.mode] so the embedded rail renders its own
// manifest, never a fixed table.
export interface Manifest {
  modes: Record<RunMode, { total: number; stages: Stage[] }>;
  total: number;
  stages: Stage[];
  recovery: Stage;
}

export interface StageStatus {
  id: string;
  number: number;
  label: string;
  gated: boolean;
  conditional: boolean;
  /** Does this stage apply to THIS run? true = it will run, false = it will
   *  skip itself, null = not yet knowable. */
  applies: boolean | null;
  writes_to_qad: boolean;
  status: "pending" | "running" | "awaiting_approval" | "approved" | "skipped" | "failed";
  attempts: number;
}

export interface QadWrite {
  stage_id: string;
  endpoint_id: string;
  dry_run: boolean;
  ok: boolean;
  locking: boolean;
  request: { method: string; url: string; headers: Record<string, string>; payload: unknown } | null;
  /** QAD's actual response body. Null for dry-run calls — nothing was sent. */
  response: unknown;
}

export interface Run {
  id: string;
  status: string;
  mode: RunMode;
  current_stage: string | null;
  bc_pascal: string | null;
  dry_run: boolean;
  user_input: string;
  error: string | null;
}

export interface RunState {
  run: Run;
  stages: StageStatus[];
  current_stage: string | null;
  writes: QadWrite[];
}

/** What `POST .../stage/{id}` returns — the gate's content. */
export interface StageRun {
  stage: string;
  gated?: boolean;
  artifact?: Record<string, any>;
  warnings?: string[];
  writes?: string[];
  skipped?: boolean;
  reason?: string;
  /** On a skip the server names the mode-correct next stage; null = run complete. */
  next?: string | null;
}

/** What `GET .../stage/{id}` returns — the stored artifact, after a refresh. */
export interface StoredStage extends StageRun {
  label: string;
  artifact_kind: ArtifactKind;
  editable: boolean;
  status: string;
  attempt: number;
  can_regenerate: boolean;
  regenerate_blocked_because: string;
}

export interface ApproveResult {
  stage: string;
  approved: boolean;
  writes: { endpoint: string; ok: boolean; dry_run: boolean; error: string }[];
  next: string | null;
  complete?: boolean;
  error?: string;
}

export interface Health {
  ok: boolean;
  warnings: string[];
  auth_enforced: boolean;
  config: { qad_configured: boolean; llm_configured: boolean; base_url: string; app_identity: Record<string, string> };
  docs: { all_grounded: boolean; ungrounded: string[] };
}

export interface StageInput {
  instruction?: string;
  browse_uris?: Record<string, string>;
  configs?: Record<string, any>[];
  /** Embedded requirements gate: override the LLM's parent choice. */
  parent_key?: string;
  /** Server-side target gate: override the component, or name the validation
   *  to remove. Explicit, like parent_key, because each is one deterministic
   *  override the gate offers by name. */
  bc_name?: string;
  target_class?: string;
  /** Server-side code gate: hand-edited Java, taken verbatim. */
  source?: string;
}

// ── The API ──────────────────────────────────────────────────────────────────
export const api = {
  health: () => call<Health>("/api/health"),
  manifest: () => call<Manifest>("/api/run/stages"),

  createRun: (user_input: string, dry_run = true, mode: RunMode = "standard") =>
    post<{ run_id: string; dry_run: boolean; mode: RunMode; first_stage: string }>(
      "/api/run", { user_input, dry_run, mode }),

  getRun: (id: string) => call<RunState>(`/api/run/${id}`),
  getStage: (id: string, stage: string) => call<StoredStage>(`/api/run/${id}/stage/${stage}`),

  runStage: (id: string, stage: string, input: StageInput = {}) =>
    post<StageRun>(`/api/run/${id}/stage/${stage}`, input),

  approve: (id: string, stage: string) =>
    post<ApproveResult>(`/api/run/${id}/stage/${stage}/approve`),

  regenerate: (id: string, stage: string, input: StageInput) =>
    post<StageRun>(`/api/run/${id}/stage/${stage}/regenerate`, input),

  skip: (id: string, stage: string, reason = "") =>
    post<{ stage: string; skipped: boolean; next: string | null }>(
      `/api/run/${id}/stage/${stage}/skip`, { reason }),
};
