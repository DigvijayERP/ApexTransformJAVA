# SESSION HANDOFF — read this first

**Purpose:** this project runs across multiple Claude Code sessions and more than one account, because
sessions hit usage limits mid-task. This file exists so a **fresh session with zero context** can resume
in minutes. Keep it current. If you change what you're doing, change this file in the same turn.

**Last updated:** 2026-08-10 · **Phase 0 closed, Phase 1 in progress**

---

## 1. What this project is

Build `adaptive_java_version` (Adaptive) — a **separate** application that generates QAD **Adaptive
(Java)** artifacts, ported from the working `aux_web_version` (AUX) app, adding a step-gated human
approval flow across three generation cases plus event-handler generation for embedded grids.

**Adaptive and AUX stay permanently separate.** Different products, different customers. Do not merge
them, do not add a mode toggle, do not refactor AUX to share code. **AUX is read-only reference.**

| Path | Role |
|---|---|
| `D:\WEB_AUX\adaptive_java_version` | This project. Git repo (initialised 2026-08-10) |
| `D:\WEB_AUX\aux_web_version` | Reference implementation — **read-only, never modify** |
| `adaptive_java_version/Docs/` | QAD platform training guides, classes 2–8 |

The authoritative brief is the "Adaptive Java version — build brief" the owner pastes at session start.
`PLAN.md` restates its phases. **The brief wins over anything in this file.**

---

## 2. ▶ EXACT NEXT ACTION

**Building Case 1 (standalone BC creation), 5 stages, step-gated.** Server-side/JEF comes later.
Background and the full inventory: **[PHASE2_CASE1_BUILD_PLAN.md](PHASE2_CASE1_BUILD_PLAN.md)**.
Note that plan's 16-gate table is **superseded** — the owner has since defined a 5-stage shape, which
`backend/core/stages.py` now implements and is authoritative.

### Done — backend foundation, verified

`core/config.py` · `core/stages.py` · `qad_client.py` · `builders/{identity,naming,bc,form,view,deploy}`
· `smoke_test.py`. **45 offline assertions pass** (`cd backend && python smoke_test.py`) — no network,
no credentials needed. Run it after any change to config, identity or the builders.

### Next — the run engine

1. Per-stage artifact store (SQLite, keyed `run_id` + `stage_id`) — nothing can be shown at a gate or
   regenerated from without it.
2. The five stage functions, each reading/writing that store.
3. `POST /api/run/{id}/stage/{stage}` + approve / regenerate-with-input endpoints.
4. Frontend `RunContext` (`useReducer`, no Zustand) + the stage dialog.

**Dry-run is the default and stays so until the owner greenlights live writes.**

### Blocked on the owner

| # | Needed | Blocks |
|---|---|---|
| 1 | `QAD_PASSWORD` → `backend/.env` | Any live call. Everything else can be built and dry-run |
| 2 | `OPENAI_API_KEY` → `backend/.env` | Stages 1, 2, 3 are LLM calls |
| 3 | ❓ **Are event handlers dropped from Case 1?** AUX generates a TypeScript handler (its steps 8–11); the owner's 5-stage design has no such stage | Whether `event_handler_builder` gets ported |
| 4 | Confirm the Phase 1 static/dynamic classification | Settings panel shape |
| 5 | **Q-L** — did `probe_parent_eh.py` ever run, and what did it return? | Phase 5 design |
| 6 | **Q-F** — permission + which environment for the grid-claiming experiment | Phase 5 design |

**Settled by the owner:** identity values (`digwish`, `urn:datastore:com.yash.extension`); the
regeneration rule (free before a write executes, blocked after); the 5-stage shape with stage 4 ungated.

**Phase 1's settings panel is deferred behind Case 1**, at the owner's direction. The config layer it
would edit already exists and works without a UI.

---

## 3. Decisions — who made them

Mark every decision as **owner** or **delegated**. A delegated decision is mine to revisit if evidence
changes; an owner decision is not.

| ID | Decision | By |
|---|---|---|
| Q-H | Environment values supplied (see §4) | **owner** |
| — | Phase 0 closed; proceed to Phase 1 | **owner** |
| Q-A | **No Zustand.** Run state = `useReducer`-based `RunContext` alongside `AuthProvider`. AUX has no Zustand — three runtime deps only, verified twice | delegated |
| Q-D | **Sub-step ids** (`3a`, `13a`), preserving the existing 14-step numbering, rather than renumbering 14→16 | delegated |
| Q-F | Grid-claiming experiment deferred to live testing, and must run **two arms** (see §6) | delegated |
| Q-B | Phase 2 transport = **per-step request/response**, modelled on SSS, not a paused SSE stream | delegated *(proposed, not yet exercised)* |
| Q-C | Gate every step, but with a per-step `gated` flag; QAD-write steps gate **before** the write, showing the payload | delegated *(proposed)* |
| — | `git init` the repo; `.gitignore` before first commit | delegated |
| — | `QAD_CLIENT_ID` in `backend/.env`, not committed config — matches AUX (rule 7). Flagged for owner override | delegated |

Remaining open: **Q-E** (Pre vs Post timing), **Q-G** (auth gap), **Q-I** (deploy lock), **Q-J** (Java
bundle sources), **Q-K** (environment permissions). All have suggested answers in `QUESTIONS.md`.

---

## 4. Environment (non-secret)

```
base_url   https://eeadaptive.yash.com:33005/clouderp
app_uri    urn:app:com.yash.digwish
URL shape  {base_url}/api/qracore/{endpoint}   and   {base_url}/oauth/token
```

**No `/qad-central/`.** AUX uses `{bare-host}/qad-central/api/qracore/…`; the Adaptive base already
carries its context root (`/clouderp`), which occupies the same slot. Derived from a confirmed fact in
the brief — **not yet validated against a live call.**

⚠️ **This environment is known-degraded**: HTTP 500 on entity-metadata generation and
`sse/build-api-sources`, dependency jar will not download, a test BC is stuck in `Initial`. The network
team is investigating. **Build anyway; dry-run stays the default; never report deploy as done on the
strength of a dry-run.**

Secrets live in `backend/.env` (gitignored). `QAD_CLIENT_ID` is set; username, password and the OpenAI
key are still blank.

---

## 5. Read order for a fresh session

| # | File | Why |
|---|---|---|
| 1 | **this file** | Where things stand |
| 2 | [PROGRESS.md](PROGRESS.md) | Full log, deferrals, resume point |
| 3 | [PHASE0_SUMMARY.md](PHASE0_SUMMARY.md) (18 KB) | The audit's findings, readable |
| 4 | [PHASE1_REGISTRY.md](PHASE1_REGISTRY.md) | What Phase 1 built and what it's waiting on |
| 5 | [QUESTIONS.md](QUESTIONS.md) | 12 decisions, triaged by what they block |
| 6 | [VERIFICATION_ROUND2.md](VERIFICATION_ROUND2.md) | Which audit claims survived checking |
| — | `PHASE0_AUDIT.md` (583 KB) | **Do not read front to back.** Citation appendix — grep it |

---

## 6. Traps — things this project has already been bitten by

1. **Absence claims built from HTTP-library greps are wrong.** Two audit sections claimed AUX never
   reads back from QAD. It does — `probe_parent_eh.py` reaches QAD via `qad_client`, not `httpx`
   directly. **The correct sweep is** `grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py`.
   This defect recurred in the section where it mattered most. Re-test every "X does not exist" claim.
2. **`ViewGridsToHandleList` is an opt-OUT filter, not an opt-in claim.** `[APIREF]:832` — *"If not set,
   all view grids will be handled."* The Q-F experiment needs **two arms**: Post-with-explicit-list and
   Post-with-no-list.
3. **A tool reporting success is not evidence.** Verify against the filesystem. The QAD VS Code plugin
   reports Maven success without checking the exit code, and it has already produced a false pass here.
4. **`dotenv_values()` reads a physical file, not `os.environ`** — breaks Docker `env_file:`. Bind-mount
   the `.env`. AUX has this live at `core/config.py:73`.
5. **JEF deploy is whole-jar replacement.** Deploying from an incomplete copy **silently erases**
   everything not in that copy. No undeploy command exists. No rollback path is validated.
6. **Session limits kill background workflows mid-flight.** `resumeFromRunId` is **same-session only** —
   a new session cannot replay another session's cache. Write results to a file as they land, not at the
   end. This has already cost one full verification round.

---

## 7. Standing rules (digest — the brief is authoritative)

1. Never guess — read the code. Both repos are available.
2. Still unclear after reading? **Stop and ask**, with your suggested answer and reasoning.
3. Label **confirmed** vs **inferred** in everything. Cite `file:line`.
4. **Phase gates** — do not start a phase before the previous one is approved.
5. **Nothing writes to QAD without explicit greenlight.** Dry-run is the default and must report exactly
   what it would send: endpoint, method, headers, payload.
6. Named deferrals, never silent omissions — record them in `PROGRESS.md`.
7. Match the reference in scope and density. Don't expand beyond what AUX does.
8. **Verify against the filesystem, not success messages.**
9. Environment is Windows `cmd`. **PowerShell is not available to the owner.** IDE is Antigravity.
10. Keep `PLAN.md`, `PROGRESS.md` and this file current for cross-session continuity.

---

## 8. Housekeeping for whoever is holding this

- **Update this file every turn that changes state.** It is the only thing a fresh account reads first.
- **Commit early.** The repo exists now; a lost session shouldn't cost work.
- Task list is session-local and **does not survive** a handoff — this file is the durable record.
- Do not open a PR unless asked.
