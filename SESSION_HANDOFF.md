# SESSION HANDOFF — read this first

**Purpose:** this project runs across multiple Claude Code sessions and more than one account, because
sessions hit usage limits mid-task. This file exists so a **fresh session with zero context** can resume
in minutes. Keep it current. If you change what you're doing, change this file in the same turn.

**Last updated:** 2026-08-10 · **Phase 0 closed · Case 1 backend COMPLETE and tested; API + frontend next**

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

**Building Case 1 (standalone BC creation), step-gated. Pipeline shape is FINAL.** Server-side/JEF later.
Background and the full inventory: **[PHASE2_CASE1_BUILD_PLAN.md](PHASE2_CASE1_BUILD_PLAN.md)**.
That plan's 16-gate table is **superseded.** `backend/core/stages.py` is authoritative:

| # | Stage | Gated | Writes on approval | Runs |
|---|---|---|---|---|
| 1 | Requirement gathering | yes | — | always |
| 2 | Field mapping | yes | BC create (+ dropdown wiring if the spec has dropdowns) | always |
| 3 | Form creation | yes | Form save | always |
| 4 | Event handler | yes | Handler register | **only if needed** |
| 5 | View creation | no | View register | always |
| 6 | Lookups | yes | Lookup Definitions | **only if a field wants one** |
| 7 | Deploy | yes | Warnings check, then deploy | always |

**A plain BC runs FIVE stages; a full one runs seven**, plus a recovery dialog that appears only when
QAD rejects the create. The stage list is per-run — anything rendering it must read the run's actual
list, never a fixed table. That is precisely what AUX gets wrong.

Stage 4 is skipped when the ABL parse shows no validation or event logic to port (owner's call: the
`.p` itself tells us). With no source, the planner proposes and the user can skip.
Stage 6 skips itself when nothing was marked at stage 2.

### Done — the whole backend, verified

| Piece | Where |
|---|---|
| Config, QAD client, 6 payload builders, stage manifest | `core/config.py`, `qad_client.py`, `builders/` |
| Per-stage artifact store + regeneration lock | `core/store.py` |
| Run engine — 7 stage functions, run/approve/regenerate/skip | `core/engine.py` |
| All eight prompts, as **templates** | `agents/prompts.py` |
| Docs grounding — all four bundles found | `core/docs_loader.py` |
| Read-only environment check | `verify_environment.py` |
| **API layer** — 12 routes, auth seam on every mutating one | `main.py`, `routers/` |
| **Frontend** — 8 source files, 2 runtime deps, no Zustand | `frontend/src/` |

**274 offline assertions pass. Run all four after any change — no network, no credentials, no key:**

```bash
cd backend && python smoke_test.py && python store_test.py && python pipeline_test.py && python api_test.py
```

### Running it

Two terminals. **The harness's `.claude/launch.json` resolves from `aux_web_version`, not here**, so
`preview_start` will start AUX's dev server rather than this one — run these yourself:

```bash
cd D:\WEB_AUXdaptive_java_versionackend && uvicorn main:app --reload --port 8000
```

```bash
cd D:\WEB_AUXdaptive_java_versionrontend && npm install && npm run dev
```

Then open http://localhost:5173. Vite proxies `/api` to port 8000.

⚠️ **The UI has NOT been verified in a browser yet.** It typechecks clean and builds clean
(36 modules, 51 KB gzipped), and the API beneath it has 49 assertions over real HTTP — but nobody has
watched it render. That is the first thing to do next session.

Three things a fresh session should understand before changing anything here:

**`pipeline_test.py` matters most.** It drives all seven stages end to end through the real engine,
real builders and real store with only the MODEL stubbed. The other two test pieces in isolation;
this one catches **chaining** bugs, and it found two on its first run.

**`store.py` holds the regeneration lock.** A stage may be regenerated only while no *successful,
live, locking* write has fired at that stage or any stage after it. Dry-run writes never lock (nothing
left the process); rejected writes never lock (QAD changed nothing); and calls a stage makes while
merely *rendering* a gate never lock — otherwise opening the deploy dialog would freeze the whole run.

**Prompts are templates, not constants.** AUX hardcodes `com.extensions.customapp` in **four places
inside the TypeScript module the model is told to emit** (`prompts.py:259,265,266,326`). Copying it
verbatim would generate handlers in AUX's namespace on our app — silently, visible only inside QAD.
`render()` substitutes our identity (including the `ComYashDigwish` and `com_yash_digwish` forms), and
a test asserts AUX's namespace never appears in a rendered prompt.

### Next

1. **The frontend** — `RunContext` (`useReducer`, no Zustand) and the stage dialog. Render the stage
   list from `GET /api/run/stages`; keep NO step table in the frontend.
2. **Port the ABL parsers** — `progress_parser.py` (414 lines) and `lookup_detector.py` (585). They
   feed four stages: requirements, the field spec, whether a handler is needed, and lookup candidates.
   Both are untracked in-flight work in AUX. Until then, `handler_hint` comes from the model's
   `HANDLER_NEEDED:` line rather than from the source.
3. **First live call**: `python verify_environment.py <entityURI>` — read-only, writes nothing.

⚠️ **Set `ADAPTIVE_API_TOKEN` in `backend/.env` before this server is reachable by anything but
localhost.** Without it the approve and deploy endpoints are unauthenticated — `GET /api/health`
reports `auth_enforced: false` and says so in `warnings`.

**Dry-run is the default and stays so until the owner greenlights live writes.**

### Blocked on the owner

| # | Needed | Blocks |
|---|---|---|
| 1 | `QAD_PASSWORD` → `backend/.env` | Any live call. Everything else can be built and dry-run |
| 2 | `OPENAI_API_KEY` → `backend/.env` | Stages 1, 2, 3 are LLM calls |
| 3 | **API captures** — see [API_CAPTURES_NEEDED.md](API_CAPTURES_NEEDED.md). None block the build; they settle the lookup unknowns and upgrade free-text boxes to pickers | Live lookup writes only |
| 4 | Confirm the Phase 1 static/dynamic classification | Settings panel shape |
| 5 | **Q-L** — did `probe_parent_eh.py` ever run, and what did it return? | Phase 5 design |
| 6 | **Q-F** — permission + which environment for the grid-claiming experiment | Phase 5 design |

**Settled by the owner:** identity values (`digwish`, `urn:datastore:com.yash.extension`); the
regeneration rule (free before a write executes, blocked after); the 7-stage shape with view ungated;
event handlers stay in Case 1 with user-supplied Browse URIs; lookups added as a conditional stage.

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
| Q-D | ~~Sub-step ids on AUX's 14-step numbering~~ — **superseded.** The owner replaced the whole shape with 7 stages, which dissolves the problem: `core/stages.py` is now the single source of stage identity and the frontend keeps no table | **owner** |
| Q-F | Grid-claiming experiment deferred to live testing, and must run **two arms** (see §6) | delegated |
| Q-B | Phase 2 transport = **per-step request/response**, modelled on SSS, not a paused SSE stream | delegated *(proposed, not yet exercised)* |
| Q-C | Gate every stage except view; QAD-write stages gate **before** the write, showing the payload | **owner** |
| — | **7-stage shape** — requirements/fields/form/handler/view/lookups/deploy. View ungated. Handler and lookups conditional, so a plain BC runs five | **owner** |
| — | Handler need is decided from the **ABL parse**, not asked: the `.p` shows whether there is validation or event logic to port | **owner** |
| — | Lookups marked at stage 2, configured at stage 6; **before deploy**, swap if QAD rejects an undeployed BC | **owner** |
| — | **Browse URIs collected from the user** at stage 4 instead of AUX's commented-out `api/TODO/provide-endpoint` | **owner** |
| — | Regeneration free before a write executes, blocked after (QAD has no undo) | **owner** |
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

```
module        com.yash.digwish        (derived from app_uri)
module_short  yash.digwish            (derived)
app_name      digwish                 (owner-supplied; must match QAD's app list)
datastore_uri urn:datastore:com.yash.extension   (owner-supplied; environment-specific)
```

Secrets live in `backend/.env` (gitignored). **Set:** `QAD_CLIENT_ID`, `QAD_USERNAME`.
**Still blank:** `QAD_PASSWORD`, `OPENAI_API_KEY` — the owner is placing these.

---

## 5. Read order for a fresh session

| # | File | Why |
|---|---|---|
| 1 | **this file** | Where things stand |
| 2 | [PROGRESS.md](PROGRESS.md) | Full log, deferrals, resume point |
| 3 | [PHASE0_SUMMARY.md](PHASE0_SUMMARY.md) (18 KB) | The audit's findings, readable |
| 4 | [PHASE1_REGISTRY.md](PHASE1_REGISTRY.md) | What Phase 1 built and what it's waiting on |
| 5 | [API_CAPTURES_NEEDED.md](API_CAPTURES_NEEDED.md) | What to grab from QAD's Network tab, and when |
| 6 | [QUESTIONS.md](QUESTIONS.md) | 12 decisions, triaged by what they block |
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
