# PHASE 0 SUMMARY — the readable layer

`PHASE0_AUDIT.md` is ~580 KB and is the **reference appendix**: full citations, full step tables, full
doc digests. It is not meant to be read front to back. **This file is.** Everything here is a
condensation of it, with a pointer to the section that carries the evidence.

**Tags on every claim:**

| Tag | Meaning |
|---|---|
| ✅ | Independently citation-verified — a second agent re-opened the cited files |
| ⚠️ | First-pass, self-cited — **not** independently verified |
| 🔴 | **Corrected** — the first pass was wrong; this is the corrected statement |

Read `🔴` items first: those are places the audit initially told you something untrue.

---

## Verification state

| Sections | State |
|---|---|
| A1–A6 | ✅ verified — `minor-issues` (arithmetic/scope slips; findings intact) |
| A7 read-back | 🔴 verified — `major-issues`, **one conclusion overturned** |
| **B1 event handlers** | 🔴 verified 2026-08-10 — `major-issues`. **Verdict survives, five design inputs changed** |
| **A8 frontend** | ✅ verified 2026-08-10 — `minor-issues`. **"No Zustand" confirmed** |
| **B2 Java docs, B4 tools/security** | ✅ verified 2026-08-10 — `minor-issues`, nothing overturned |
| A9 docs-loader, A10 settings, A3 lookup-progress, B3 docs-bc-ext | ⚠️ **still unverified** — session limit |
| Completeness critic | ⚠️ **never ran** |

⚠️ **The round-2 corrections are not yet applied to this file or to `PHASE0_AUDIT.md`.** Where a ⚠️ tag
below covers B1, A8, B2 or B4, read `VERIFICATION_ROUND2.md` alongside it — that file carries the
flag-by-flag verdicts and the replacement text. The most consequential changes: the grid-claiming risk is
framed backwards (`ViewGridsToHandleList` is an opt-**out** filter — `[APIREF]:832`), B1's
"three separate compilation units" citation is false, and the Pre/Post-unavailable restriction is
narrower than stated (platform-BC **and** same-app, not same-app generally).

**Nothing here was verified against a live QAD platform.** No QAD call was made, read or write, at any
point in Phase 0. Every platform claim comes from source code or documentation.

---

# Item 1 — the three cases, one line per step

## Case 1: new business component from scratch ✅

Linear async generator, `run_pipeline` (`backend/pipeline.py:381`). Not a state machine — no step table,
no dispatch, no cursor, no persistence. Every failure is `yield` + bare `return`.

| # | Step | What it does | Calls QAD |
|---|---|---|---|
| 0 | *(unnumbered)* ABL parse | Detects pasted/attached `.p`/`.cls` source and parses the temp-table schema deterministically, to skip the step-1 LLM call | — |
| 1 | Understanding your requirements | Uses the parsed text verbatim if present, else calls `REQUIREMENTS_GATHERING`. Output is **plain text, not JSON** | — |
| 2 | Designing BC fields | **The `FIELD_CREATOR` step.** Plain text → strict JSON `spec` (`bc_pascal`, `description`, `fields[]`) | — |
| 3 | Creating Business Component in QAD | `build_bc_payload` → single POST. **First QAD write of the run** | `POST entitymetadatas` |
| 4 | Fixing errors automatically | *Conditional* — only on a step-3 rejection. `VALIDATOR_AND_CORRECTOR` returns `fixed` or `failed`; on `fixed`, re-runs step 3 | *(retries step 3)* |
| **3.5** | dropdown → data-list wiring | **No step number of its own — emits under `step: 3`.** QAD's Entity Builder needs two saves: GET the enriched metadata, mutate, POST it back | `GET` + `POST entitymetadatas` |
| 5 | Planning form panels | `FORM_PLANNER` → plain-text panel plan (PKs first, 2 columns, ≤6 fields/panel) | — |
| 6 | Building panel layout | **The form-field normalization step.** `FORM_FIELD_BUILDER` → `_normalize_placements` → diffs placed fields against the spec and reports `missing` | — |
| 7 | Saving form design to QAD | Groups placements into GroupPanel→Grid→Field trees, one per panel | `POST viewMetadataV2` |
| 8 | Planning event handler logic | Injects the `client_extension_event_handler` docs bundle; produces a 6-section plain-text plan | — |
| 9 | Writing event handler code | Generates TypeScript, then a **real `tsc` syntax gate** (the only true compiler check in the run) | — |
| 10 | Compiling TypeScript to JavaScript | ⚠️ **An LLM stand-in, not a compiler** — asks the model to emit ES5. The output is never syntax-checked | — |
| 11 | Registering event handlers in QAD | Strips markdown fences, POSTs one handler. **Hardcoded `eventHandlerType: "BEFORE"`, `appliesTo: "WEB"`** | `POST eventhandler` |
| 12 | Building view configuration | Pure local build, **no network call** — browse columns, key fields, sort positions | — |
| 13 | Registering view in QAD | Single POST of step 12's payload | `POST viewResourceMetadatas` |
| **13.5** | lookup detection | **No step number, no label, no `STEP_LABELS` entry.** Classifies candidates; statics go to `create_lookup(dry_run=True)`. **No QAD call is reachable** — the live path is guarded | *(none — dry-run only)* |
| 14 | Deploying Business Component | Two POSTs in sequence. ⚠️ The warnings response is **discarded** — never assigned, never checked | `POST deployCheckForWarnings` then `POST deployBusinessEntity` |
| — | post-run | Final summary frame → entity-registry persistence → history row written **in the router**, after the generator is exhausted | — |

**The two bolded rows are the Phase 2 problem** — see item 6 of this summary.

## Case 2: embedded ✅

`run_embedded_pipeline` (`backend/pipeline_embedded.py`). Same linear shape. **Produces a grid only — it
generates no event handler at all.**

| # | Step | What it does | Calls QAD |
|---|---|---|---|
| 1 | Understanding Embedded BC requirements | Requirements for a child BC that will hang off a parent | — |
| 2 | Designing Embedded BC fields | Field spec; PKs include `domaincodeEx` + the parent FK | — |
| 3 | Creating Business Component metadata | Child BC create | `POST entitymetadatas` |
| 4 | Handling duplicates & auto-fix | *Conditional.* ⚠️ Named but **not LLM-driven** — `VALIDATOR_AND_CORRECTOR` is imported and never called | *(retries step 3)* |
| **3.5** | dropdown wiring | **Re-uses step id 3** — same duplicate-identity defect as Case 1 | `GET` + `POST entitymetadatas` |
| 5 | Building relations to parent entity | The step that makes it *embedded*. `cardinality: MANYTOONE`; ⚠️ `relationID` uses a **hardcoded UUID prefix** | `POST berelation` |
| 6 | Checking deployment warnings | ⚠️ Response discarded, same as Case 1 | `POST deployCheckForWarnings` |
| 7 | Deploying Business Component | | `POST deployBusinessEntity` |
| 8 | Registering standalone view | *Optional.* ⚠️ **The frontend cannot render this step** — it is outside the client's step list | `POST viewResourceMetadatas` |

Established facts worth carrying into Phase 5: the grid is **structural** for `MANYTOONE` (a panel would
need a `ONETOONE` redesign — tested live, recorded in AUX's own `PROGRESS.md`), and the embedded flow
**never reads the parent's handler or form/view metadata back**.

## Case 3: server-side (SSS) ✅ — a separate flow

Not a pipeline. Six discrete stages behind `/api/sss/*`, driven by the frontend one request at a time.

| # | Stage | What it does | Endpoint |
|---|---|---|---|
| 0 | scaffold | Auto-creates the workspace at startup from bundled templates + tsc 3.5.3 | *(local)* |
| 1 | readiness | Gates every SSS route on typedefs being present | `GET /api/sss/connection` |
| 2 | discover | Reads `.d.ts` typedefs from the workspace to list available BCs | `GET /api/sss/bcs` |
| 3 | generate | LLM writes TypeScript, grounded on the `server_side_rule` docs bundle | `POST /api/sss/generate` |
| 4 | **HUMAN APPROVAL** | **This already exists.** Review → edit → Approve / Regenerate / Discard | *(frontend)* |
| 5 | deploy | `tsc` compile then multipart POST | `POST /api/sss/deploy` → QAD `sss?appSeq=0&fileSeq=3` |

**This is the template for Phase 2.** It is the only place in the codebase where a human already gates a
generated artifact before it is written.

---

# Item 2 — client-extension vs server-side ✅

**Answered definitively.**

- **Client-extension (event handler) generation is INSIDE the new-BC pipeline** — steps 8–11, ending at
  `pipeline.py:685`. There is no separate route and no way to run it alone.
- **Server-side is a SEPARATE flow** — `routers/sss.py:35` declares `APIRouter(prefix="/api/sss")`, with
  its own five endpoints and its own frontend feature.
- The embedded pipeline generates **no** event handler.

---

# Item 3 — QAD endpoints ✅

Every qracore call goes through one transport layer, `backend/qad_client.py`, which builds
`{base}/qad-central/api/qracore/{endpoint}` and sets `Authorization: Bearer`.

| Endpoint | Verb(s) | Used by |
|---|---|---|
| `entitymetadatas` | POST (create), GET+POST (dropdown wiring) | Cases 1 & 2, steps 3 and 3.5 |
| `viewMetadataV2` | POST only | Case 1 step 7 |
| `eventhandler` | POST (pipeline) · 🔴 **GET+POST** (probe, see item 6) | Case 1 step 11 |
| `viewResourceMetadatas` | POST only | Case 1 step 13, Case 2 step 8 |
| `berelation` | POST only | Case 2 step 5 |
| `deployCheckForWarnings` | POST — ⚠️ **response discarded in both pipelines** | Cases 1 & 2 |
| `deployBusinessEntity` | POST | Cases 1 & 2 |
| `lookups` | *never called* — dry-run guard blocks it | Case 1 step 13.5 |
| `oauth/token` | POST, credentials **in the query string** | every write, re-fetched each time |
| `sss?appSeq=0&fileSeq=3` | POST multipart | SSS deploy |

⚠️ `appSeq=0&fileSeq=3` are unexplained literals copied verbatim from the VS Code extension. Nothing in
the repo derives them.

---

# Item 4 — auth ✅

- One flow: `POST /qad-central/oauth/token` with `client_id`, `username`, `password`, `grant_type=password`
  **as query parameters**.
- **No token cache and no 401 refresh.** `get_token()` is re-called immediately before *every* write —
  seven times per Case-1 run. A 401 mid-run is not retried; the run aborts.
- **Nothing is persisted.** Each token is fetched fresh into a new client and discarded.
- Credentials come from `.env`, with a legacy fallback that reads them from the **git-tracked**
  `settings.json` when `.env` is blank. All three commits were checked: **no credential has ever been
  committed.** Latent risk, not a current leak.
- ⚠️ `core/qad_session.get_bearer_token()` is **dead code** — a better implementation (correct URL
  encoding, typed errors) with zero callers. The live path has an unencoded password in a URL.

---

# Item 5 — run state ✅

| Question | Answer |
|---|---|
| What is stored? | One row per **completed** run in `history.db` — `runs` (19 rows) and `parent_entities` (22 rows) |
| When? | **After the generator is exhausted**, in the router |
| Step outputs? | **None.** Only the terminal summary |
| What survives a refresh mid-run? | **Nothing — zero rows.** The save never happens |

**What Phase 3 requires:** a per-step artifact store keyed `(run_id, step)`, written as each step
completes rather than at the end. That is a prerequisite for Phase 2's UI, not a follow-on — without it
there is nothing to display at a gate and nothing to regenerate from.

---

# Item 6 — reading artifacts back from QAD 🔴 **CORRECTED**

**The first pass said AUX never reads anything back from QAD, on any path. That was wrong.**

**Corrected answer, confirmed by direct read of the file:**

- **The pipelines never read back** — that part stands. Each run authors a handler from scratch and POSTs
  it as a full replace.
- **But `backend/probe_parent_eh.py` does exactly this.** Untracked, and the newest file in `backend/`.
  Its own docstring: *"confirms whether we can: 1. GET an existing event handler 2. POST it back (with
  concurrencyHash) as an update."*
  - `:44-51` GET `eventhandler?appURI=…&viewURI=…&eventHandlerType=BEFORE&appliesTo=WEB`
  - `:58-63` reads `uri`, `concurrencyHash`, `isActive`, `typeScriptCode`
  - `:74-89` POSTs it back as a no-op update, echoing `uri` + `concurrencyHash`
  - `:100-107` re-GETs to confirm the hash rotated

**Why this matters for Phase 5.** It targets `urn:view:viewmeta:com.qad.erp.sales.SalesOrders` — a
**standard QAD parent view** — from `urn:app:com.extensions.customapp`. That is the Phase 5
configuration. Consequences:

1. **The GET contract is already known in-repo**: params `appURI`, `viewURI`, `eventHandlerType`,
   `appliesTo` — note camelCase `viewURI`, unlike the `?viewUri=` the entity endpoints use. Response
   `data.eventHandlerV2s[]`. This retires the "recover the URI by network capture" item.
2. **`concurrencyHash` is the optimistic-locking token** that makes read-modify-write possible.
3. **It does not undercut the Pre/Post strategy** — it fetches *our own* `BEFORE` row on the parent's
   view, not QAD's Primary.

**Still unknown: whether it was ever run.** See item 1 of the report and `QUESTIONS.md` Q-L.

**Platform side (unchanged):** the generated typedef declares `fetch(appURI, viewURI, eventHandlerType,
appliesTo)` and `exists(...)` on `IEventHandlerV2s`, corroborating the probe's parameter list exactly.

---

# Item 7 — frontend ⚠️

**Three premises in the brief are contradicted by the files.**

| Premise | Reality |
|---|---|
| Zustand | ⚠️ **There is no Zustand anywhere.** Three runtime deps: `react`, `react-dom`, `react-router-dom`. State is React Context + component-local `useState`. `authStore.tsx` records the decision in its own header: *"No Zustand added."* |
| `authStore` is a store | It is a React Context, and says so |
| `progress_parser.py` relates to `ProgressPanel` | Pure name collision. It parses **OpenEdge ABL source** |

**Reusable for a gated UI:** the SSS review component (approve/regenerate/discard triad), the free-text
instruction control, the segmented toggle, the stale-response guard, the design tokens.

**Structurally in the way:** the fire-and-forget single-shot stream; no step-output storage; the
step-display component is a stateless view of a flat event log; the **duplicated step tables**; a 455-line
god component; a single `running` boolean as the entire lifecycle; silent dropping of unknown SSE frames.

⚠️ **Security:** exactly one backend endpoint enforces identity and exactly one frontend call sends a
token. `/api/run`, `/api/sss/generate`, `/api/sss/deploy` are open. An approve/deploy button that any
unauthenticated caller can invoke by hand is a worse posture than today's.

---

# Item 8 — docs-bundle loader ⚠️

One dict (`BUNDLES`) over `.txt` files, grouped by their **immediate parent directory name**. Three
bundles today across 285 files. No cache, no size cap, no token budget.

**Adding a bundle is four changes:** drop `.txt` files in a uniquely-named folder → add a `BUNDLES` entry
→ put `{QAD_DOCS_CONTEXT}` in the prompt → wire three lines at the call site. Nothing else exists to
change: no enum, no schema, no migration, no frontend, no tests.

**Three traps:** a misspelled folder name **fails silently**; the loader reads `.txt` **only**, so the
Adaptive `Docs/*.md` are invisible as they stand; and a restart is mandatory.

⚠️ `grep -rin "java"` across the backend returns **zero** hits. Any Java bundle is greenfield.

---

# Phase 5 — the Pre/Post verdict ⚠️ *(verification in progress, prioritised)*

**PARTIALLY HOLDS.**

**What holds:** three timings — Primary, Pre (`BEFORE`), Post (`AFTER`). Each timing is a **separate
module with its own class instances**, evidenced by three distinct module names for one BC. Registration
is a **new row** in the Form → Event Handlers grid; the parent's Primary is never opened or edited. QAD's
own docs contain a worked example of doing this to a standard BC.

**What blocks a clean "holds":**

1. **Unavailable in one configuration** — if the active developer app *owns* the target BC, only Primary
   can be created. Checkable in one look: if the New row offers a **Timing** dropdown, you are safe.
2. **Grid claiming is unproven, and Phase 5 lives or dies on it.** `createViewGridTSHandler` fires only
   for grids listed in that handler's `ViewGridsToHandleList`. Whether a Primary module and a Post module
   can **both** claim the same `gridId` is **stated nowhere** across 7 Adaptive guides and 285 AUX docs.

**AUX's generator is not shaped for this.** It templates a **single flat handler** hardcoded to `BEFORE`.
The platform documents **four** base classes (plus a fifth per-field one), and the parent-field →
embedded-grid pattern requires **three wired together** — QAD states why: *"these fields change events
fire in the form handler and not in the grid handler."*

---

# Phase 6 — Java extensions ⚠️

**Two findings that change how the docs bundle must be built:**

1. 🚩 **The class-6 guide claims an undeploy command exists** — three separate times — contradicting your
   confirmed decompile of plugin 1.0.10. Both cannot be true. **Nothing will be built that depends on
   rollback.**
2. 🚩 **The guide is not self-sufficient to write a class.** Both code listings begin at source line 6, so
   the `package` declaration and **every import is cropped** — including `@Extension`, `Output`, and
   `TrainingBaseService`, the three symbols an LLM most needs. It also points at an external handout not
   in the repo. A model grounded only on this deck emits a file that does not compile.
3. It also self-contradicts on Java version: prose mandates JDK 17, screenshots show JDK 8, your confirmed
   POM targets `1.8`.

**Consequence:** the bundle must be built from three sources — the deck (workflow, worked example),
`javap` against the real dependency jar (actual API surface), and your confirmed decompile facts (HTTP
contract).

---

# The blockers, in one place

| # | Blocker | Blocks | Where |
|---|---|---|---|
| 1 | Did `probe_parent_eh.py` ever run? | Phase 5 | `QUESTIONS.md` Q-L |
| 2 | Grid-claiming experiment — permission + environment | Phase 5 | Q-F |
| 3 | Zustand: hard requirement or wrong premise? | Phase 2 | Q-A |
| 4 | Gated transport: per-step request/response vs pausing stream | Phases 2, 3 | Q-B |
| 5 | **Step identity — no gate can attach to an unnumbered step** | Phase 2 | Q-D, and item 6 of the report |
| 6 | Real endpoint values | Phase 1 | Q-H |
| 7 | Auth gap — fix before Phase 2? | Phases 2, 4 | Q-G |

---

# What Phase 0 did not settle

1. 8 of 15 sections still unverified; the completeness critic has not run.
2. Nothing verified against a live platform.
3. The grid-claiming question is unanswerable from documents.
4. Whether `probe_parent_eh.py` ever ran.
5. The Adaptive environment's HTTP 500s — out of scope. One diagnostic the docs suggest: the UI's Package
   action dispatches an OS Script whose error text lands in the Inbox, so running the script directly may
   reveal what the 500 swallows.
