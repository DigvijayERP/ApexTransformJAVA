# PHASE 0 AUDIT — Adaptive (Java) build, read-only audit of `aux_web_version`

**Status:** Phase 0 deliverable, submitted for review.
**Date:** 2026-08-06.
**Application code written: none.** This phase was read-only by instruction. Nothing in
`adaptive_java_version` exists yet except `Docs/` and the four markdown files produced by this phase
(`PHASE0_AUDIT.md`, `QUESTIONS.md`, `PLAN.md`, `PROGRESS.md`).

---

## 0.1 What was audited, and how

| | |
|---|---|
| Reference implementation read | `D:\WEB_AUX\aux_web_version` — full `backend/`, full `frontend/src/` (all 28 files), `PROGRESS.md`, `.env.example`, `settings.json`, `requirements.txt`, `package.json`, `.gitignore` |
| Platform documentation read | `D:\WEB_AUX\adaptive_java_version\Docs\*.md` — all 7 guides (classes 2–8), in full |
| Corroborating documentation read | `aux_web_version/backend/qad_docs/**` — 285 `.txt` files, consulted where they cover the same subject as the Adaptive `Docs/` |
| Working-tree state | The **uncommitted** on-disk state was audited, not `HEAD`. Uncommitted edits exist in `backend/pipeline.py`, `backend/agents/prompts.py`, `backend/core/progress_parser.py`, `backend/routers/client_extensions.py`; untracked files `backend/core/lookup_detector.py`, `backend/core/lookup_generator.py`, `backend/probe_parent_eh.py`. Verified with `git status --short` / `git diff`. |
| Method | 15 independent read-only agents, one per subject area, each required to cite `path:line` for every claim and to tag every statement `[CONFIRMED]` (read in the file) or `[INFERRED]` (deduced). |

### Reading this document

- **`[CONFIRMED]`** means the agent opened the file and read the cited lines. Line numbers are real.
- **`[INFERRED]`** means deduced from naming, convention, or documentation — **not verified**. Every
  inference carries what would confirm it.
- Where a section reports that something is **absent**, that absence is itself a finding and was
  established by an explicit search, not by failure to look.

### ⚠️ Verification status — read this before relying on a citation

The audit design included a second, independent citation-verification pass per section (a different
agent re-opening every cited file to confirm the line numbers and the claims) and a final completeness
critic. **7 of the 15 sections have now been verified. 8 have not, and the critic has not run** — the
remainder were killed by account session limits and an expired token across three attempts.

| Section | Verification |
|---|---|
| A1 new-BC pipeline, A2 embedded, A3 SSS, A4 endpoints, A5 auth, A6 persistence | ✅ verified — verdict `minor-issues` |
| A7 read-back | ✅ verified — verdict **`major-issues`**, one finding overturned (see §0.4 finding 5) |
| A8 frontend, A9 docs loader, A10 settings, A11 work-in-flight, B1 event handlers, B2 Java extensions, B3 BCs/extensions, B4 tools/security | ❌ **not verified** |
| Completeness critic | ❌ did not run |

**Every verified section retains its findings.** What verification changed: one overturned conclusion
(A7), and a set of arithmetic and scope slips — counts stated as "four" alongside six enumerated items,
"eleven steps later" where the answer is four, and in one case a **reported grep output that did not
match reality** even though its conclusion was correct and in fact stronger than stated. Corrections
are in **Part V, the verification appendix**, and supersede the section text where they conflict.

**Two of the load-bearing sections are among the unverified eight:** A8 (the "no Zustand" finding) and
B1 (the Phase 5 Pre/Post verdict). Both are cited in §0.4. Treat them as first-pass until that pass
runs. Before any Phase 1 code depends on a specific line, re-open that line.

**One systematic weakness, worth knowing because it recurs.** Several sections built their
"what talks to QAD" inventory by grepping for HTTP *library* imports (`httpx`, `requests`). A module
needs no such import to reach QAD — it only needs to import `qad_client`. That is exactly how
`backend/probe_parent_eh.py` fell out of three separate inventories and produced the one overturned
conclusion. The correct sweep is `grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py`.
Any absence claim in an unverified section should be re-checked against that command before it is
relied on.

---

## 0.2 Coverage against the eight required items

| # | Required item | Where answered | State |
|---|---|---|---|
| 1 | Full ordered step inventory for each of the three cases | A1 (new BC), A2 (embedded), A3 (server-side) | Answered, with `path:line` per step |
| 2 | Are client-extension and server-side generation steps inside the new-BC pipeline, or separate flows? | §0.3 below + A1, A3 | **Answered definitively** |
| 3 | Every QAD endpoint AUX calls | A4 | Answered — full table |
| 4 | The auth flow as implemented | A5 | Answered |
| 5 | How run state is stored; what must change to persist a partially-approved run | A6 | Answered |
| 6 | Any path that reads existing artifacts back from QAD, especially event handler code | A7 (AUX side) + B1 §7 (platform side) | **Answered — and the answer changed the Phase 5 picture** |
| 7 | Frontend architecture; what is reusable for a step-gated approval UI | A8 | Answered — includes three corrections to the brief |
| 8 | How the docs-bundle loader works; what adding a bundle type involves | A9 | Answered — exact four-step change list |

Additional sections beyond the eight, produced because they bear directly on Phases 1–6:
**A10** settings/config registry (feeds Phase 1) · **A11** uncommitted lookup/parser work in flight ·
**B1** Adaptive Docs, event handlers (feeds Phase 5) · **B2** Adaptive Docs, Java extensions (feeds
Phase 6) · **B3** Adaptive Docs, BCs/extensions/relations/formulas/lookups · **B4** Adaptive Docs,
platform tools, data administration, security and permissions.

---

## 0.3 Item 2, answered directly

**Client-extension (event handler) generation is a set of steps INSIDE the new-BC pipeline.
Server-side (SSS) generation is a SEPARATE flow.** [CONFIRMED]

- The event-handler write is a step in the main pipeline — `backend/pipeline.py:685`:
  `eh_result = await post_qad("eventhandler", eh_data["payload"], token)`. It is reached in normal
  sequence at steps 8–11 of `run_pipeline`; there is no separate route, no separate request, and no
  way to run it on its own.
- SSS is a distinct router with its own prefix and its own endpoints —
  `backend/routers/sss.py:35`: `router = APIRouter(prefix="/api/sss")`, exposing
  `GET /bcs`, `GET /bcs/{name}`, `POST /generate`, `POST /deploy`, `GET /connection`
  (`sss.py:55,73,83,99,123`). It has its own frontend feature (`frontend/src/features/sss/`) and its
  own approval UI.
- The embedded pipeline does **not** generate an event handler at all: `post_qad("eventhandler", …)`
  does not appear in `pipeline_embedded.py`. *(Corrected by the item-2 sweep: `eventhandler` is a
  network target at **five** sites, not one — `pipeline.py:685` plus `probe_parent_eh.py:51`, `:91`,
  `:100`, `:126`. The conclusion here is unaffected: none of them is in the embedded pipeline.)*

This matters for Phase 2: **SSS already has the approval flow the brief wants, and the new-BC
pipeline has nothing resembling it.** See §0.4 finding 6.

---

## 0.4 Findings that change the plan

These are the results a reader should not miss. Each is expanded, with citations, in the section named.

**1. There is no Zustand in this project.** [CONFIRMED — A8]
`frontend/package.json:10-14` lists exactly three runtime dependencies: `react`, `react-dom`,
`react-router-dom`. A repo-wide grep for `zustand` across `package.json`, `package-lock.json`,
`frontend/src/**` and `frontend/node_modules/` returns **zero** matches. State is React Context
(`features/auth/authStore.tsx`) plus component-local `useState`. The file's own header comment records
this as a deliberate decision: *"No Zustand added."* The brief's premise is inverted — adopting Zustand
for Adaptive would be a **new dependency and a reversal**, not a continuation. That is a decision for
you, and it is Q-A in `QUESTIONS.md`.

**2. `backend/core/progress_parser.py` has nothing to do with UI progress.** [CONFIRMED — A8]
It parses OpenEdge Progress 4GL / ABL `.p` and `.cls` source to extract temp-table schema
(`progress_parser.py:1-15`). Pure name collision with `ProgressPanel.tsx`. Worth stating because the
brief pairs them.

**3. Phase 5's Pre/Post hypothesis PARTIALLY HOLDS — and the part that is unproven is precisely the
part Phase 5 needs.** [CONFIRMED mechanism; the gap is a documented absence — B1]
The timing mechanism is real and works as you read it. Three timings are documented — Primary, Pre
(DB value `BEFORE`), Post (DB value `AFTER`) — and each timing is a **separate module with its own
class instances**, evidenced by three distinct module names for the same BC
(`Maint_BEFORE` / `Maint_AFTER` / `Maint_PRIMARY`, class 7 guide lines 427, 466, 625). Registration is
a **new row** in the Form → Event Handlers grid, created with `New`; **the parent's Primary handler is
never opened or edited.** QAD's own documentation contains a worked example of doing exactly this to a
standard BC. So the strategic claim — *we never need to read or merge the parent's source* — is
supported **for form and field logic**.

Two things block a clean "HOLDS":

- **Blocked in one configuration.** If the active developer app *is* the app that owns the target BC,
  Pre/Post is unavailable and only Primary can be created — i.e. you are forced into merge territory.
  (Form-Builder event-handler doc, lines 22-28 and 88.) Whether the Phase 5 target falls in this case
  is checkable in one look: if the New row offers a **Timing** dropdown, you are safe.
- **Grid claiming is unproven, and Phase 5 lives or dies on it.** `createViewGridTSHandler` is only
  called for grids listed in the handler's `ViewGridsToHandleList` array. Whether a Primary module and
  a Post module can **both** claim the same `gridId` and both receive grid events is **stated nowhere
  in any document read** — 7 Adaptive guides and 285 AUX docs. This is the single highest-risk
  inference in the audit and it is labelled as such. B1 §6 specifies the exact experiment that settles
  it, and it is cheap: register a Post handler that lists an already-claimed grid, override
  `onAutoGridBindData` with a `console.log`, and see whether both modules log.

**4. Your instinct about the flat handler shape was right.** [CONFIRMED — B1]
AUX templates a single flat handler and hardcodes Pre timing: `event_handler_builder.py:30` emits
`"eventHandlerType": "BEFORE"`, and the prompt bakes `Maint_BEFORE` into the module name
(`agents/prompts.py:259`). The platform documents **four** base classes (view, view-form, view-grid,
browse) — plus a fifth, `ViewFieldTSHandler`, that the brief does not mention — and the
parent-field → embedded-grid pattern requires **three of them wired together**: the main handler holds
a reference to the grid handler, injects itself into the form handler, and the form handler's
`onFieldChange` calls into the grid handler. QAD documents this pattern end to end, and states the
reason plainly: *"these fields change events fire in the form handler and not in the grid handler."*
Phase 5 needs the richer structure. Knowing it now, as you asked.

**5. ⚠️ CORRECTED — AUX already reads event handlers back from QAD. A working probe exists.**
[CONFIRMED by direct read of the file; the first-pass audit got this wrong and verification caught it]

This is the item flagged as mattering for Phase 5, and the first-pass answer — *"AUX never reads
artifacts back from QAD, not on any path"* — **is wrong.** The corrected answer:

- *AUX pipelines:* the original finding **stands, scoped to the pipelines.** Neither `run_pipeline` nor
  `run_embedded_pipeline` reads a handler back; each run authors one from scratch and POSTs it as a
  full replace (`pipeline.py:685`).
- *But the backend contains a working handler read-back.* `backend/probe_parent_eh.py` — untracked, and
  the newest file in `backend/` — does exactly this, and its docstring says so:
  *"confirms whether we can: 1. GET an existing event handler 2. POST it back (with concurrencyHash) as
  an update."*
  - `:44-51` GETs `eventhandler?appURI=…&viewURI=…&eventHandlerType=BEFORE&appliesTo=WEB`
  - `:58-63` unwraps `data.eventHandlerV2s[0]` and reads `uri`, `concurrencyHash`, `isActive`, `typeScriptCode`
  - `:74-89` POSTs it back as a **no-op update** echoing `uri` + `concurrencyHash`
  - `:100-107` re-GETs to confirm the hash rotated

**Why this matters more than the error does — it is aimed squarely at Phase 5.** The probe targets
`viewURI = urn:view:viewmeta:com.qad.erp.sales.SalesOrders` (`:25`), a **standard QAD parent view**,
with `appURI = urn:app:com.extensions.customapp` (`:24`). That is precisely the Phase 5 configuration.
Three consequences:

1. **The GET contract is already known and written down in-repo** — params `appURI`, `viewURI`,
   `eventHandlerType`, `appliesTo` (note camelCase `viewURI`, *not* the `?viewUri=` convention the
   entity/view endpoints use), response `data.eventHandlerV2s[]`. This retires the "recover the
   `urn:be:` value by network capture" deferral: the endpoint is simply `eventhandler` on the existing
   `qracore` prefix.
2. **`concurrencyHash` is the optimistic-locking token** that makes read-modify-write possible on a
   handler. Nothing else in the audit identified it as such.
3. **Read carefully, it does not contradict the Pre/Post strategy — it supports it.** The probe fetches
   *the custom app's own `BEFORE` handler on the parent's view*, not QAD's Primary. So it is read-back
   of our own Pre-timing row, which is exactly what a safe "update our handler without touching the
   parent's" flow needs.

**What is still unknown:** whether the probe has ever been *run successfully*. It A/B tests two payload
shapes (with `uri` at `:74-89`, without at `:111-125`), which suggests the update contract was still
being pinned down when it was written. The filesystem cannot tell us the outcome. **This is a question
for you** — you will know whether it ran and what it returned, and the answer is worth more to Phase 5
than anything else in this audit.

*Platform side, unchanged and still valid:* the generated typedef declares
`fetch(appURI, viewURI, eventHandlerType, appliesTo)` and `exists(...)` on `IEventHandlerV2s`
(`backend/sss_template/lib/qracoregen.d.ts:2005-2012`) with the full stored record shape
(`EventHandlerV2Record`, `:1971-1985`) — corroborating the probe's parameter list exactly. Handler TS
is stored in the database and served to the browser as a named script source, so devtools enumerates
every active handler and its timing. And the docs state the parent's *coded* TS handlers **are not
stored in the database — they are part of the application code itself**, which argues *for* Pre/Post
rather than against it.

**6. Phase 2 is a blocking rewrite of the run transport, not a UI feature.** [CONFIRMED — A1, A6, A8]
`run_pipeline` is a single linear `AsyncGenerator` streamed inside one `StreamingResponse`
(`pipeline.py:381`, `client_extensions.py:168-212`). There is no state machine, no step table, no step
cursor, no persistence of step outputs — **only the terminal summary is saved**
(`client_extensions.py:185-197`). A grep for pause/approve/resume across the pipeline and router
returns **zero hits**. The only client control is `abort()`. So at a gate today there is nothing to
show and nothing to regenerate from.

The good news is that the shape you want already exists in this codebase: **SSS is per-step
request/response with an approve/regenerate/discard review UI** (`ReviewDeploy.tsx:63-101`,
`RulePrompt.tsx`). The recommendation in A8.6 is to build Phase 2 on that proven shape rather than
hold an SSE stream open across an indefinite human pause. Also note the persistence consequence: an
aborted or refreshed run currently leaves **zero rows** — the save happens after the stream ends.

**7. The 14-step contract is wrong, and the frontend has already drifted from it.** [CONFIRMED — A1, A8]
`TOTAL_STEPS = 14` (`pipeline.py:142`) undercounts: dropdown wiring and lookup detection run as real,
failure-capable work units with no step identity of their own, and one of them re-emits `step: 3`,
producing a duplicated "step 3 done" in the UI. The label list is duplicated client-side
(`ProgressPanel.tsx:3-18`) and the frontend **ignores the `name` the backend sends on every frame**.
Live consequences: embedded step 8 is unrenderable, and three embedded labels disagree with the
backend. A gated UI cannot ship while client and server disagree about what step 5 is. Fix direction:
a backend-supplied step manifest, deleting the frontend tables.

**8. The Java extensions guide contradicts a confirmed fact — it claims an undeploy command exists.**
[CONFIRMED as a doc claim — B2, finding F1]
The class-6 guide asserts undeploy **three times**: in the capability list (*"undeploying an
extension"*), in the Command Palette screenshot (`QAD Extension: Undeploy urn_app_com.extensions.training`),
and in the command table. Your confirmed set — decompile of plugin 1.0.10 plus a live deploy — says
there is no undeploy command. These cannot both be true as stated. B2 ranks the reconciliations; the
most likely is a command registered in `package.json` whose handler is local-only or stubbed, which a
decompile hunting HTTP calls would correctly report as "no undeploy". **Action taken: none. The
generator will not emit undeploy tooling and nothing will be designed to depend on rollback.**
Flagging it because you asked to be told loudly.

**9. The Java guide is not self-sufficient to write a class.** [CONFIRMED — B2, finding F3]
Both code listings begin at source line 6 — **the `package` declaration and all imports are cropped
out**. There is no import shown for `@Extension`, `Output`, or `TrainingBaseService`: the three symbols
an LLM most needs. The doc also points at *"the file provided in materials for current class"*, an
external handout not present. An LLM grounded only on this deck will emit a file that does not compile.
B2 §6 gives a concrete 11-page bundle outline, tagging each page with whether this doc can supply it;
the highest-value page (`01_IMPORTS_AND_PACKAGE.md`) is precisely the one it cannot. A second
self-contradiction: the prose mandates JDK 17 while the screenshots show JDK 8, and the confirmed POM
targets `1.8`.

**10. Adding a docs bundle is four mechanical changes — but no Java docs exist in the required form.**
[CONFIRMED — A9]
Bundles are one dict (`BUNDLES`, `core/qad_docs_loader.py:46-64`) over `.txt` files grouped by their
immediate parent directory name. Adding one: drop `.txt` files in a uniquely-named folder, add a
`BUNDLES` entry, put `{QAD_DOCS_CONTEXT}` in the prompt, and wire three lines at the call site. No
enum, no schema, no migration, no frontend change, no test. Two traps: a misspelled folder name
**fails silently**, and the loader reads `.txt` **only** — the Adaptive `Docs/` are `.md`, so they are
invisible to it as they stand. Also: `grep -rin "java"` across the backend returns **zero** hits. Any
Java bundle is greenfield.

**11. Security posture, stated plainly, because Phase 2 and 4 make it worse before better.**
[CONFIRMED — A5, A8]
Exactly one backend endpoint enforces identity (`/api/auth/me`, `routers/auth.py:69`) and exactly one
frontend call sends a bearer token (`features/auth/api.ts:53`). `/api/run`, `/api/sss/generate` and
`/api/sss/deploy` are **open** — a bare `curl` to `/api/sss/deploy` writes to QAD. `ProtectedRoute` is
client-side only. An "approve & deploy" button that any unauthenticated caller can invoke by hand is a
worse posture than today's, because the UI implies a gate that does not exist. Recommendation: fix
before Phase 2 ships, not during Phase 4.

**12. Config traps present in the reference implementation.** [CONFIRMED — A10]
- **Trap #4 from the brief is live**: `dotenv_values()` at `core/config.py:73` reads a physical file
  and ignores `os.environ`, so Docker `env_file:` injection does not reach it.
- `backend/settings.json` is **git-tracked** and `config.py:113-121` still reads `qad_password` /
  `qad_username` from it as a legacy fallback. All three commits were checked: **no credential has
  ever been committed.** This is a latent risk, not a current leak — but it is the one mechanism by
  which a QAD password can enter a tracked file.
- `backend/sss_template/qad-sss.config.json` commits a live-looking internal hostname that
  **disagrees** with `.env`'s `QAD_BASE_URL`. Nothing reads it; it is inert and misleading.

**13. The model selector in the settings panel does not affect the main pipeline.** [CONFIRMED — A10]
`settings.json` sets `openai_model: gpt-5-mini`, but the BC pipeline ignores it —
`MODEL_MATRIX` (`pipeline.py:136-140`) hardcodes `gpt-4o` / `gpt-4o-mini`. Only SSS honours the
setting. Worth knowing before the Phase 1 settings panel presents that control as meaningful.

**14. The reference repo cannot currently be cloned and run.** [CONFIRMED — A11]
`backend/core/progress_parser.py:22` imports `core.lookup_detector` at module scope, and
`lookup_detector.py` is **untracked**. A fresh clone therefore fails to import `main`. `PROGRESS.md`
already records Phase 11 as done, so the repo claims a state it does not contain. Not an Adaptive
blocker — flagged because it affects anyone using AUX as the reference.

---

## 0.5 What Phase 0 did not settle

Named deferrals, per working rule 6. None of these were silently dropped.

1. **8 of 15 sections are unverified and the completeness critic did not run** — including A8 and B1,
   which carry two §0.4 findings. Queued as the first item in `PROGRESS.md`.
2. **Nothing was verified against a live platform.** No QAD call was made, read or write. Every
   platform claim is from source code or documentation.
3. **The grid-claiming question (finding 3)** cannot be settled from documents at all. It needs the
   experiment in B1 §6.1 against a live environment.
4. ~~**The `urn:be:` value for `EventHandlerV2sComm.ENTITY_URI`** must be recovered by network
   capture.~~ **RESOLVED by finding 5** — `probe_parent_eh.py:44-51` already establishes the working
   endpoint and its parameters. What replaces it as an open item: **whether that probe was ever run
   successfully**, which the filesystem cannot answer.
5. **The Adaptive environment's HTTP 500s** were not investigated — out of Phase 0 scope. B4 records
   one high-value diagnostic the docs suggest: the UI's Package action dispatches an OS Script and
   surfaces its error text in the Inbox, so running the script directly may reveal the error the 500
   swallows.
6. **`aux_web_version/PROGRESS.md` (75 KB) was not read end to end**, only the sections relevant to a
   given question.

---

# Part A — the AUX reference implementation

## A1. Case 1 — New Business Component from scratch: full step inventory

**Audited tree:** `D:/WEB_AUX/aux_web_version` (the working directory reported by the env is `D:/WEB_AUX/adaptive_java_version`, which contains only a `Docs/` folder — the code under audit is in `aux_web_version`). All paths below are relative to that root. Working-tree state audited (uncommitted edits present in `backend/pipeline.py`, `backend/agents/prompts.py`, `backend/core/progress_parser.py`, `backend/routers/client_extensions.py`, plus untracked `backend/core/lookup_detector.py`, `backend/core/lookup_generator.py`) — verified via `git status --short` / `git diff`.

---

### A1.0 Shape of the pipeline (answer up front)

**[CONFIRMED] It is a linear async generator (streaming SSE), not a state machine and not a plain function.** There is no step table, no dispatch dict, no `while` over a step index, and no persisted step cursor. `run_pipeline` is one long straight-line coroutine that `yield`s SSE strings; every step is hard-coded inline in source order, and every failure is `yield` + bare `return`.

Signature — `backend/pipeline.py:381-385`:

```python
async def run_pipeline(
    user_message: str,
    parsed_requirements: str | None = None,
    lookup_candidates: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
```

**[CONFIRMED] The only driving loop in the whole flow lives in the router, not the pipeline** — `backend/routers/client_extensions.py:158-180`:

```python
        pipeline_gen = (
            run_embedded_pipeline(req.message)
            if req.mode == "embedded"
            else run_pipeline(
                req.message,
                parsed_requirements=parsed_requirements,
                lookup_candidates=lookup_candidates,
            )
        )

        async for chunk in pipeline_gen:
            yield chunk
            # parse to track final state for history
            try:
                data = json.loads(chunk.removeprefix("data: ").strip())
                if data.get("type") == "complete":
                    summary = data.get("summary")
                    final_status = "success"
                elif data.get("type") == "error":
                    last_error = data.get("error", "Pipeline error")
            except Exception:
                # SSE chunk that isn't the terminal JSON we track - expected; ignore.
                pass
```

**[CONFIRMED] Step count and labels are two hard-coded constants** — `backend/pipeline.py:142` (`TOTAL_STEPS = 14`) and `backend/pipeline.py:145-160` (`STEP_LABELS`, 14 entries). `models.py:33` independently hard-codes `total: int = 14` on `SSEEvent`. `frontend/src/features/client_ext/components/ProgressPanel.tsx:3-18` duplicates all 14 labels client-side (drift risk: two copies of the same list).

**[CONFIRMED] Every SSE frame is built by one helper** — `backend/pipeline.py:163-177`:

```python
def _evt(type_: str, step: int = 0, status: str = "running",
         message: str = "", summary: Any = None, error: str = "") -> str:
    d: Dict[str, Any] = {
        "type": type_, "step": step, "total": TOTAL_STEPS,
        "name": STEP_LABELS.get(step, ""), "status": status, "message": message,
    }
```

**[CONFIRMED] Model tiering** — `backend/pipeline.py:136-140`: `MODEL_MATRIX = {"planning": "gpt-4o-mini", "generation": "gpt-4o", "compile": "gpt-4o-mini"}`. All LLM calls go through `_llm()` at `backend/pipeline.py:180-192` (`max_tokens=15000` unless the model id starts with `gpt-5`).

**[CONFIRMED] All QAD POST/GET calls resolve to** `{config.qad_base_url()}/qad-central/api/qracore/{endpoint}` — `backend/qad_client.py:56-61` (POST) and `backend/qad_client.py:64-69` (GET). Endpoint suffixes are listed per step below. Auth is re-fetched per step: `get_token()` → `POST {base}/qad-central/oauth/token?client_id=…&username=…&password=…&grant_type=password` (`backend/qad_client.py:42-53`).

---

### A1.1 Ordered step inventory

#### Step 0 — pre-pipeline Progress/ABL parse (NOT a numbered step; no `STEP_LABELS` entry)

| Field | Value |
|---|---|
| Identifier in code | `_extract_progress_attachment` → `parse_progress_file` → `parsed_to_requirements_text` (`backend/routers/client_extensions.py:88-111`, `:129-146`) |
| User-visible label | none — emits raw `{"type":"warning","message":…}` frames only (`client_extensions.py:155-156`) |
| What it does | **[CONFIRMED]** Detects `.p`/`.cls` source either from the frontend marker `File: <name>.p\n\n<content>` (`_FILE_MARKER_RE`, `client_extensions.py:34-37`) **or** from source pasted with no marker, recognised by ≥ 2 ABL signals (`_ABL_SIGNALS`, `_MIN_ABL_SIGNALS = 2`, `client_extensions.py:44-57`). Then deterministically parses the temp-table schema, bypassing the LLM for step 1. Skipped entirely when `req.mode == "embedded"` (`client_extensions.py:129`). |
| Produces | **[CONFIRMED]** `parsed` dict with keys including `tables`, `lookups`, `parse_warnings`, `source_type` (`backend/core/progress_parser.py:123-124`, `:344-345`); `parsed_requirements` plain-text string shaped like `REQUIREMENTS_GATHERING` output (`progress_parser.py:366-406`); `parse_warnings: list[str]`; `lookup_candidates: list[dict]` |
| QAD endpoints | none |
| LLM calls | none — this exists specifically to *avoid* one (`progress_parser.py:369`, `pipeline.py:402-403`) |
| State written | Local vars in the request handler only: `parsed_requirements`, `parse_warnings`, `lookup_candidates` (`client_extensions.py:126-128`). Nothing persisted. |
| Failure/retry | **[CONFIRMED]** Fully swallowed: `except Exception` → `logger.error("[FAIL] client_ext.progress_parse :: %s", exc)` → `parsed_requirements = None` and the run continues into the LLM path (`client_extensions.py:144-146`). No retry. |

#### Step 1 — `STEP_LABELS[1] = "Understanding your requirements"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:399-414` |
| What it does | **[CONFIRMED]** Two mutually exclusive branches. If `parsed_requirements` is truthy: uses it verbatim, **no LLM call**, emits `"Requirements read directly from your file"` (`pipeline.py:401-406`). Else calls `REQUIREMENTS_GATHERING` with `MODEL_MATRIX["planning"]` (`pipeline.py:409`). |
| Produces | **[CONFIRMED]** `requirements`: a **plain-text string**, not JSON. The prompt explicitly forbids JSON (`backend/agents/prompts.py:34`: `Do NOT produce any JSON…`). Structure requested: purpose line, PascalCase BC name ≤32 chars, field count, per-field type/PK/required/maxLength/dropdownValues (`prompts.py:14-28`). |
| QAD endpoints | none |
| LLM calls | `REQUIREMENTS_GATHERING` (`prompts.py:5-35`), model `gpt-4o-mini`, `json_mode=False` |
| State written | in-memory `state["requirements"]` (`pipeline.py:405` or `:410`) |
| Failure/retry | **[CONFIRMED]** No retry. `except Exception` → `_evt("error", 1, …, error=f"Requirements gathering failed: {e}")` then `return` (`pipeline.py:411-413`). |

#### Step 2 — `STEP_LABELS[2] = "Designing BC fields"` — **this is the FIELD_CREATOR step**

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:416-426` |
| What it does | **[CONFIRMED]** Sole `FIELD_CREATOR` call site in this pipeline (`pipeline.py:419`; imported at `pipeline.py:8`). Converts the plain-text requirements into the strict JSON `spec`. Prompt enforces: Hungarian-prefix stripping, camelCase, exact-match SQL-reserved renames, `maxLength` only for `character`/`url`, mandatory `dropdownValues` (≥2, ≤20) for every dropdown type, ≥1 `isPrimary: true` (`prompts.py:45-84`). |
| Produces | **[CONFIRMED]** `parsed["spec"]` → `spec` dict with exactly: `bc_pascal`, `description`, `fields[]`; each field: `code`, `dataType`, `isPrimary`, `isRequired`, optional `maxLength`, optional `dropdownValues[{code,label}]` (`prompts.py:86-97`). Raw LLM text is de-fenced/trimmed by `_parse_json_output` (`pipeline.py:195-206`). |
| QAD endpoints | none |
| LLM calls | `FIELD_CREATOR` (`prompts.py:38-97`), model `gpt-4o`, **`json_mode=True`** |
| State written | in-memory `state["spec"]` (`pipeline.py:422`); local `current_spec = spec` (`pipeline.py:431`) — this alias is what every later step reads |
| Failure/retry | **[CONFIRMED]** No retry. Any exception (including `KeyError` on a missing `"spec"` key) → `_evt("error", 2, …, error=f"Field design failed: {e}")` → `return` (`pipeline.py:423-425`). |

> **[CONFIRMED] Placement answer for the commissioner:** `FIELD_CREATOR` is **step 2**, and it is *not* the same thing as the form-field normalization. The normalization the commissioner heard about is **step 6** (`_normalize_placements`), eleven steps' worth of code later. `grep -rn FIELD_CREATOR` across the repo returns only: `prompts.py:38` (definition), `pipeline.py:8` (import), `pipeline.py:419` (the one call), plus the *separate* `EMBEDDED_FIELD_CREATOR` used by the embedded pipeline (`prompts.py:453`, `pipeline_embedded.py:9`, `:122`) and doc/comment mentions in `progress_parser.py:5,109,369,371` and `PROGRESS.md`. **[CONFIRMED]** There is no `FIELD_CREATOR` involvement anywhere in steps 5-7.

#### Step 3 — `STEP_LABELS[3] = "Creating Business Component in QAD"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:428-441` (first attempt), `:443-499` (failure handling + `done`) |
| What it does | **[CONFIRMED]** `build_bc_payload(current_spec)` → fresh `get_token()` → single POST. |
| Produces | **[CONFIRMED]** `bc_data` from `backend/builders/bc_builder.py:280-292` with keys `status`, `payload`, `field_list_map`, `entity_uri`, `summary`. `summary` keys: `bc_pascal`, `module`, `field_count`, `pk_count`, `pk_codes` (`bc_builder.py:285-291`). `payload` top-level keys: `activityTrackingInfos`, `entityMetadatas[0]{…, dataLists, entityURI, moduleURI, appName, entityCode, entityFields[…], browseSearchOperators, bcType:"Standard", businessComponentStatus:"INITIAL", scope:"SYSTEM"}`, `entityDeployments[0]{initialTableName, entityURI, isDeployed:False, …}` (`bc_builder.py:228-278`). Each `entityFields[]` element carries ~35 keys incl. `primaryKey`, `entityFieldCode`, `fieldLabel`, `physicalFieldName`, `jsonName`, `dataType`, `displayFormat`, `dataListCode` (deliberately `""` on first save — `bc_builder.py:198`), `uniqueID` (uuid4), `fieldURI` (`bc_builder.py:185-218`). URI templates: `entity_uri = urn:be:com.extensions.customapp.{bc}.I{bc}`, `module_uri = urn:app:com.extensions.customapp` (`bc_builder.py:165-168`). |
| QAD endpoint | **[CONFIRMED]** `POST entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` (`pipeline.py:436`) |
| LLM calls | none |
| State written | `state["bc_summary"] = bc_data["summary"]` — **[CONFIRMED]** written at `pipeline.py:500`, i.e. *after* the `step 3 done` event at `:499`, and after the auto-fix branch |
| Failure/retry | **[CONFIRMED]** Three distinct paths. (a) Transport/build exception → `_evt("error", 3, …, "QAD connection failed: {e}")` + `return` (`pipeline.py:439-441`). (b) **Duplicate-name short-circuit (uncommitted addition):** `_is_duplicate_entity_error(bc_result)` (substring `"already exist"` over `_qad_error_messages`, `pipeline.py:226-231`) → hard stop with rename guidance, **no** LLM auto-fix, **no** retry (`pipeline.py:447-455`). (c) Any other QAD failure → falls through into step 4. `is_qad_success` requires `submitResult.success is True and errorSeverity == 0 and not errors`, and treats the `{"error","raw"}` envelope as failure (`qad_client.py:72-82`). |

#### Step 4 — `STEP_LABELS[4] = "Fixing errors automatically"` (conditional; only reachable on a step-3 QAD rejection)

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:457-497` |
| What it does | **[CONFIRMED]** Builds a fix prompt from requirements + submitted spec + the QAD error envelope (`pipeline.py:460-464`), calls `VALIDATOR_AND_CORRECTOR`. If `status == "fixed"`: replaces `current_spec`, re-emits `step 3 running`, rebuilds payload, re-tokens, **re-POSTs the same endpoint exactly once** (`pipeline.py:468-479`). If `status != "fixed"`: emits the model's `reason` as a step-4 error and returns (`pipeline.py:491-494`). |
| Produces | **[CONFIRMED]** `fix_parsed` with either `{status:"fixed", fix_summary, spec}` or `{status:"failed", reason}` (`prompts.py:133-148`) |
| QAD endpoint | **[CONFIRMED]** the retry re-POSTs `entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` (`pipeline.py:477`) |
| LLM calls | `VALIDATOR_AND_CORRECTOR` (`prompts.py:100-155`), model `gpt-4o`, `json_mode=True` |
| State written | `state["spec"] = current_spec` (overwrites step 2's spec) — `pipeline.py:471` |
| Failure/retry | **[CONFIRMED] Exactly one retry, no loop.** Second failure → error attributed to **step 3** (not 4) with plain-English messages via `_qad_error_messages` and, for a name collision, appended rename advice (`pipeline.py:480-490`). This is uncommitted work: pre-change the message was the raw `json.dumps(err)` (`git diff backend/pipeline.py`). |

#### Step 3.5 — dropdown→data-list wiring (**[CONFIRMED] no step number of its own; emits under `step: 3`**)

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:502-540` |
| User-visible label | reuses `STEP_LABELS[3]`; distinguished only by `message: "Wiring dropdown fields to data lists..."` (`pipeline.py:511`) and a **second** `step 3 done` frame `"Wired N dropdown field(s)"` (`pipeline.py:540`) |
| Gate | **[CONFIRMED]** runs only `if field_list_map:` — i.e. only when at least one field has a dropdown `dataType` (`pipeline.py:509-510`; map built in `bc_builder.build_data_lists`, `bc_builder.py:114-157`) |
| What it does | **[CONFIRMED]** QAD's Entity Builder needs two saves. 1) URL-encode `bc_data["entity_uri"]` via `urllib.parse.quote(..., safe="")`; 2) GET the enriched metadata; 3) unwrap `{"data": {...}}` if present (`pipeline.py:521`); 4) hard-fail if `entityMetadatas` is absent (`pipeline.py:522-525`); 5) `patch_dropdown_fields(enriched, field_list_map)` sets `dataListCode` + `defaultValue` per matching `entityFieldCode`, in place (`bc_builder.py:98-111`); 6) POST the patched body back. |
| Produces | **[CONFIRMED]** mutated `enriched` dict; `wire_result` QAD envelope. No new artifact keys, no `state` entry. |
| QAD endpoints | **[CONFIRMED]** `GET entitymetadatas?entityURI={quoted}&viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` (`pipeline.py:517`) then `POST` the identical path (`pipeline.py:530`) |
| LLM calls | none |
| State written | none in `state` |
| Failure/retry | **[CONFIRMED]** No retry. Three error exits, all labelled `step 3`: missing `entityMetadatas` (`:523-525`), exception (`:533-535`), QAD non-success (`:536-539`). |

#### Step 5 — `STEP_LABELS[5] = "Planning form panels"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:542-552` |
| What it does | **[CONFIRMED]** Feeds `json.dumps(current_spec["fields"])` to `FORM_PLANNER`. Prompt rules: PKs in Panel 1 first, 2 columns, max 6 fields/panel, semantic grouping, never a 1-field panel (`prompts.py:165-174`). |
| Produces | **[CONFIRMED]** `panel_plan`: a **plain-text** string, one line per panel, e.g. `Panel 1 - Order Identity: dealPONumber, dealDomainCode` (`prompts.py:176-181`, explicitly "No JSON"). |
| QAD endpoints | none |
| LLM calls | `FORM_PLANNER` (`prompts.py:158-181`), model `gpt-4o-mini`, `json_mode=False` |
| State written | in-memory `state["panel_plan"]` (`pipeline.py:548`); plus a new `logger.info("[STEP5] panel plan …")` line added uncommitted (`pipeline.py:547`) |
| Failure/retry | **[CONFIRMED]** No retry. `_evt("error", 5, …, "Form planning failed: {e}")` → `return` (`pipeline.py:549-551`). |

#### Step 6 — `STEP_LABELS[6] = "Building panel layout"` — **this is the form-field normalization step**

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:554-590`; helpers `_build_placements` `:354-378`, `_normalize_placements` `:256-313`, `_flatten_panels` `:234-253`, `_deep_collect_placements` `:316-351` |
| What it does | **[CONFIRMED]** (1) `expected_codes = [str(f["code"]) for f in current_spec.get("fields", [])]` (`:557`). (2) `_build_placements` calls `FORM_FIELD_BUILDER`, `_parse_json_output`, then `_normalize_placements`, then diffs placed field names (lower-cased) against `expected_codes` to compute `missing` (`:373-378`). (3) **If `missing`: exactly one corrective retry** whose user message names the omitted codes verbatim (`:561-573`). (4) **If still missing: raise → hard stop before any QAD write** (`:577-584`). |
| The normalization itself | **[CONFIRMED]** `_normalize_placements` coerces six observed LLM shapes into the flat list `[{fieldName, panel, panelName, gridColumn, gridRow}]`: bare array; array of panel objects (`_is_panels` → `_flatten_panels`); **a single bare placement object** (the uncommitted fix at `:279-286`, which previously "silently became a 1-field form"); a nested value that is a list of panel objects; a nested value that is already flat (`_is_flat`); a dict grouped by panel name (`:296-308`). Last resort: `_deep_collect_placements` walks arbitrary nesting, carries down the nearest panel name, and assigns panel numbers by first-appearance order (`:312-313`, `:316-351`). The reason is documented in the docstring at `:261-264`: `json_mode` forces a top-level object, so `gpt-4o` will not return the bare array the prompt asks for. |
| Produces | **[CONFIRMED]** `placements: list[dict]` with keys exactly `fieldName`, `panel`, `panelName`, `gridColumn`, `gridRow`; and `missing: list[str]` |
| QAD endpoints | none |
| LLM calls | `FORM_FIELD_BUILDER` (`prompts.py:184-215`), model `gpt-4o`, `json_mode=True` — **1 call normally, 2 when the first layout is incomplete** |
| State written | in-memory `state["placements"]` (`pipeline.py:586`). Also two `logger.info` and one `logger.warning` diagnostic (`:364`, `:375-377`, `:563-564`). |
| Failure/retry | **[CONFIRMED] Exactly one retry.** Three failure causes, all surfaced as `step 6` `"Panel layout failed: {e}"` (`:587-589`): normalization yielding no list (`ValueError` at `:371`, message includes the parsed shape), residual `missing` after the retry (`ValueError` at `:578-584`), or any LLM/parse exception. |

#### Step 7 — `STEP_LABELS[7] = "Saving form design to QAD"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:592-606` |
| What it does | **[CONFIRMED]** `build_form_payload(placements, current_spec)` groups placements by `p["panel"]` into `panels_map` (`form_builder.py:130-137`), builds one `GroupPanel`→`Grid`→`Field` tree per panel, wraps in `OuterGrid` with a `QraSummaryPanel` + `QraGroupPanelNavigator` (`form_builder.py:138-212`). Field element names follow `f"{bc_pascal}_{safe}AutoField{panel_idx}"` (`form_builder.py:58`); `lookupVisibility` is `"Hidden"` for PK fields else `"Visible"` (`form_builder.py:63`); grid rows string is `",".join(["27"] * (max_row+1))` (`form_builder.py:21-23`); columns `"50%,50%"` (`form_builder.py:75`). |
| Produces | **[CONFIRMED]** `form_data` = `{status, payload, summary}` (`form_builder.py:238-249`). `payload.viewMetadatas[0]` keys: `viewURI` (`urn:view:viewmeta:com.extensions.customapp.{bc}`), `platformName:"webui"`, `viewName`, `moduleURI`, `parentURI`, `moduleName`, `dataOperation`, `entityURI`, `isEligibleForMenu`, `viewMetadata{name,entityURI,childElements}`, `disallowedActions`, `disallowedActionsMessage`, `viewMetadataAdjusted`, `labelFontFactor:1.8`, `defaultLabelWidth:166` (`form_builder.py:214-236`). `summary` keys: `bc_pascal`, `panel_count`, `field_count`, `panels[{panel,panelName,fields}]`. |
| QAD endpoint | **[CONFIRMED]** `POST viewMetadataV2` (`pipeline.py:597`) — note: no `viewUri` query param, unlike steps 3 and 13 |
| LLM calls | none |
| State written | `state["form_summary"] = form_data["summary"]` (`pipeline.py:606`, again *after* the `done` event at `:605`) |
| Failure/retry | **[CONFIRMED]** No retry. Exception → `"Form save failed: {e}"` (`:598-600`); QAD non-success → `"Form registration failed: {json.dumps(err)}"` (raw JSON, **not** run through `_qad_error_messages`) (`:601-604`). |

#### Step 8 — `STEP_LABELS[8] = "Planning event handler logic"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:608-630` |
| What it does | **[CONFIRMED]** Builds a prompt of `BC Name` / `Description` / `Fields` (`:611-615`), loads the docs bundle `"client_extension_event_handler"` and injects it into the prompt by replacing the literal `{QAD_DOCS_CONTEXT}` placeholder via `str.replace` (`:619-624`). The comment at `:616-618` states the planner shares the writer's bundle so it can't sketch behaviours the writer can't produce. Bundle folders: "UI Event Handlers", "UI elements list of events and Properties_Functions", "Platform Scripting - TypeScript", "TypeScript recommended coding standards" (`core/qad_docs_loader.py:47-52`). |
| Produces | **[CONFIRMED]** `eh_plan`: plain text, 6 numbered sections — purpose / `onInit` / `onFieldChange` / `onButtonClick` / private helpers / API calls (`prompts.py:235-244`) |
| QAD endpoints | none |
| LLM calls | `EVENT_HANDLER_PLANNER` (`prompts.py:218-244`), model `gpt-4o-mini`, `json_mode=False` |
| State written | in-memory `state["eh_plan"]` (`pipeline.py:626`) |
| Failure/retry | **[CONFIRMED]** No retry → `"Event handler planning failed: {e}"` (`:627-629`). A missing/failed docs bundle is *not* an error: `get_bundle` returns `""` and never raises (`qad_docs_loader.py:106-122`). |

#### Step 9 — `STEP_LABELS[9] = "Writing event handler code"` (+ a non-LLM `tsc` gate)

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:632-664` |
| What it does | **[CONFIRMED]** Prompt = `BC Name` + the step-8 plan + `json.dumps(placements)` ("use for correct AutoField panel numbers", `:636-639`). Docs injected the same way (`:642-647`). Then a **real compiler gate**: `check_typescript_syntax(ts_code)` (`:657`) writes the code to a temp file and runs `tsc --noEmit --target ES5 --module none --strict false --skipLibCheck --pretty false` with `shell=False`, 45 s timeout (`core/ts_compiler.py:59-99`). Only TS1xxx syntax errors fail; TS2xxx type errors are tolerated because the handler references QAD deploy-time types (`pipeline.py:654-656`, `ts_compiler.py:63-67`). |
| Produces | **[CONFIRMED]** `ts_code` (string, possibly markdown-fenced — fences are stripped later in `event_handler_builder.py:10-17`); `(ok, ts_diag)` from the gate |
| QAD endpoints | none |
| LLM calls | `TS_CODE_WRITER` (`prompts.py:247-…`), model `gpt-4o`, `json_mode=False` |
| State written | in-memory `state["ts_code"]` (`pipeline.py:649`). **[CONFIRMED]** A `.ts` file *is* written to disk, but only inside a `tempfile.TemporaryDirectory()` that is deleted on exit (`ts_compiler.py:74-76`) — nothing durable. |
| Failure/retry | **[CONFIRMED]** No retry, two exits: LLM exception → `"TypeScript code writing failed: {e}"` (`:650-652`); syntax gate failure → `"Generated TypeScript has syntax errors — not deploying:\n{ts_diag}"` (`:658-663`). **[CONFIRMED]** If `tsc` is not installed the gate returns `ok=True` with a "skipped" message (`ts_compiler.py:69-71`) — the gate silently degrades to a no-op. |

#### Step 10 — `STEP_LABELS[10] = "Compiling TypeScript to JavaScript"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:666-678` |
| What it does | **[CONFIRMED]** Asks an LLM to emit ES5 JS: user message is `f"Compile this TypeScript to ES5 JavaScript:\n\n{ts_code}"` (`:671`). **[CONFIRMED] This is an LLM stand-in, not a compiler** — `pipeline.py:139` labels the tier `"compile": "gpt-4o-mini",  # TS -> JS translation step (LLM stand-in)`. The real `tsc` in step 9 runs `--noEmit` and produces no JS (`ts_compiler.py:79`). |
| Produces | `js_code` string (fences stripped downstream) |
| QAD endpoints | none |
| LLM calls | `TS_COMPILER` (`prompts.py:389`, a one-line prompt), model `gpt-4o-mini` |
| State written | in-memory `state["js_code"]` (`pipeline.py:674`) |
| Failure/retry | **[CONFIRMED]** No retry, no validation of the produced JS → `"TypeScript compilation failed: {e}"` (`:675-677`). |

#### Step 11 — `STEP_LABELS[11] = "Registering event handlers in QAD"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:680-693` |
| What it does | **[CONFIRMED]** `build_event_handler_payload(bc_pascal, ts_code, js_code)` strips markdown fences from both blobs, then POSTs. |
| Produces | **[CONFIRMED]** `eh_data = {status, payload, summary}` (`event_handler_builder.py:39-47`). `payload` = `{"supplementaryMessages": [], "eventHandlerV2s": [{appURI, viewURI, eventHandlerType:"BEFORE", appliesTo:"WEB", isActive:True, typeScriptCode, javaScriptCode, mappingCode:""}]}` (`event_handler_builder.py:25-37`). `summary` = `{bc_pascal, view_uri, ts_code_length, js_code_length}`. |
| QAD endpoint | **[CONFIRMED]** `POST eventhandler` (`pipeline.py:685`) |
| LLM calls | none |
| State written | **[CONFIRMED] none** — `eh_data["summary"]` is *not* stored on `state` and never reaches the final `summary`. Compare steps 3/7/12, which do store theirs. |
| Failure/retry | **[CONFIRMED]** No retry: exception (`:686-688`) or QAD non-success with raw `json.dumps(err)` (`:689-692`). |

#### Step 12 — `STEP_LABELS[12] = "Building view configuration"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:695-703` |
| What it does | **[CONFIRMED]** Pure local build, **no network call at all**. `build_view_payload(current_spec)` derives `key_fields` from `isPrimary` fields, one `browse_columns[]` entry per field with `sortPosition = i`, `isSortable: True`, `dataType` capitalised (`view_builder.py:59-100`), and a `view_label` via `to_view_label` (strips trailing `Headers`/`Mgmt`, spaces on capitals, `:40-47`). |
| Produces | **[CONFIRMED]** `view_data = {status, payload, summary}` (`view_builder.py:170-180`). `payload.viewResourceMetadatas[0]` keys include `isEligibleForMenu`, `isSecure`, `isUseBEBrowse`, `browseView{browseDatasourceUri, showExcelImport, browseColumns, drillDowns, initialSortFields, tshandlersV2, browseActions, …}`, `maintView{viewMetadata, viewModule, allowEdit, allowAddNew, allowDelete, …}`, `hybridBrowseView{browseViewUri, maintViewUri}`, `entityViewParameters{usesDomain, tableName, appModuleName:"qracore", dataResourceName, entityModule, keyFields}`, `moduleUri`, `app`, `metaURI`, `viewURI`, `primarySecureURI`, `entityURI`, `browseURI`, `typeField:"HYBRID_BROWSE"`, `mobileCompatibility:"BROWSEANDREADONLYFORM"`, `nameStringCode`, `initialBrowseURI` (`view_builder.py:104-167`). `summary` keys: `bc_pascal`, `bc_lower`, `pk_count`, `pk_codes`, `field_count`, `view_label`. |
| QAD endpoints | **none** |
| LLM calls | none |
| State written | `state["view_summary"] = view_data["summary"]` (`pipeline.py:699`) |
| Failure/retry | **[CONFIRMED]** No retry. Only realistic failure is `ValueError("No primary key fields found.")` (`view_builder.py:60-61`) → `"View configuration failed: {e}"` (`:700-702`). |

#### Step 13 — `STEP_LABELS[13] = "Registering view in QAD"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:705-720` |
| What it does | **[CONFIRMED]** Fresh token, single POST of step 12's payload. |
| Produces | `view_result` QAD envelope |
| QAD endpoint | **[CONFIRMED]** `POST viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` (`pipeline.py:710`) |
| LLM calls | none |
| State written | none |
| Failure/retry | **[CONFIRMED]** No retry; exception and QAD-failure branches carry the *same* message text `"View registration failed: …"` (`:714` and `:718`), which makes the two causes indistinguishable in the UI. |

#### Step 13.5 — lookup detection / dry-run emission (**[CONFIRMED] no step number, no label, no `STEP_LABELS` entry**)

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:722-731` (call site), `:54-131` (`_emit_lookup_events`), `:34-51` (`_lookup_bc_metadata`), `:29-31` (`_sse`) — **entirely uncommitted (Phase 11)** |
| Position | **[CONFIRMED]** After step 13 (`view registered`) and **before** step 14 (`deploy`). Rationale in the comment at `:722-723`: after the view/fields are saved so Lookup Definitions can reference them. |
| Gate | **[CONFIRMED]** `if lookup_candidates:` — a strict no-op when the `.p` parse found none (`:725`) |
| What it does | **[CONFIRMED]** For each candidate dict → `LookupCandidate.from_dict`. `classification == "static"` → build metadata from pipeline constants + `current_spec` and call `create_lookup(cand, meta, dry_run=True)`, then emit a `lookup_candidate` frame; if `payload["_needs_verification"]` is non-empty also emit a `lookup_needs_review` with `reason:"payload_gap"`. Otherwise (`"dependent"` / `"uncertain"`) → emit `lookup_needs_review` with that classification as `reason`. |
| Produces | **[CONFIRMED]** SSE frames outside the `_evt` schema (no `step`/`total`/`name` keys): `{"type":"lookup_candidate", source_table, target_field, evidence_line, confidence, dry_run:True, payload}` (`:81-89`); `{"type":"lookup_needs_review", reason, source_table, target_field, evidence_line, notes[, needs_verification]}` (`:93-103`, `:106-116`); `{"type":"lookup_summary", message, detected, static_dry_run, needs_manual_setup, static_payload_gaps}` (`:124-131`) |
| QAD endpoints | **[CONFIRMED] NONE are called.** `create_lookup` guards with `if dry_run is not False:` → logs and returns without any network call (`core/lookup_generator.py:266-273`). The live path exists but is unreachable from the pipeline: it would `POST lookups?viewUri=urn:be:com.qad.qra.lookup.ILookup` (`lookup_generator.py:70`, `:276-282`). The docstring at `:259-260` states dry-run=False must only be reached by an explicit human-initiated trial. |
| LLM calls | none |
| State written | in-memory `state["lookup_summary"] = {detected, static_dry_run, needs_manual_setup, static_payload_gaps}` (`pipeline.py:118-123`) |
| Failure/retry | **[CONFIRMED]** Non-fatal by design, twice over: a per-candidate payload-build failure is logged and `continue`d (`:75-78`); the whole block is wrapped in `try/except Exception` that only logs `"Lookup detection step failed (non-fatal): %s"` (`:729-731`). No error frame ever reaches the user from this step. |

#### Step 14 — `STEP_LABELS[14] = "Deploying Business Component"`

| Field | Value |
|---|---|
| Code location | `backend/pipeline.py:733-750` |
| What it does | **[CONFIRMED]** `build_deploy_payload(bc_pascal)`, one token, then **two POSTs in sequence**. |
| Produces | **[CONFIRMED]** `deploy_data = {status, step4a, step4b, summary}` (`deploy_builder.py:11-27`). `step4a` = `{entityURI, isInitialDataLoaded:False}`. `step4b` = `{entityURI, appURI, dataStoreURI:"urn:datastore:com.extensions.extension", isInitialDataLoaded:False, allowActivityTracking:False}`. `summary` = `{bc_pascal, entityURI}`. |
| QAD endpoints | **[CONFIRMED]** `POST deployCheckForWarnings` (`pipeline.py:739`) then `POST deployBusinessEntity` (`pipeline.py:741`) |
| LLM calls | none |
| State written | **[CONFIRMED] none** — `deploy_data["summary"]` is never stored on `state` |
| Failure/retry | **[CONFIRMED]** No retry. **The warning-check response is discarded** — `await post_qad("deployCheckForWarnings", …)` at `:739` is not assigned and never passed to `is_qad_success`, so warnings (and a failed pre-check) cannot block or surface. Only `deploy_result` is checked (`:745-748`). |

#### Post-14a — final `summary` + `complete` frame (**[CONFIRMED] not a numbered step**)

**[CONFIRMED]** `backend/pipeline.py:753-776` assembles the artifact that actually leaves the process. Exact keys: `bc_pascal`, `description`, `field_count`, `fields[{code, dataType, isPrimary, isRequired}]`, `panel_count`, `panels`, `pk_codes`, `view_label`, `module` (hard-coded `"com.extensions.customapp"`), `lookups` (Phase 11, defaulted to `{"detected":0,"static_dry_run":0,"needs_manual_setup":0,"static_payload_gaps":0}` — `:772-775`). Emitted as `_evt("complete", 14, "done", "All done!", summary=summary)` at `:802`.

#### Post-14b — entity-registry persistence (**[CONFIRMED] not a numbered step; runs after `deploy done`, before `complete`**)

**[CONFIRMED]** `backend/pipeline.py:778-800`. Local import of `register_and_persist_custom_bc, infer_fk_field` from `qad_entity_registry` (`:782`), then persists `entity_code=bc_pascal`, `entity_uri=f"urn:be:com.extensions.customapp.{bc_pascal}.I{bc_pascal}"`, `pk_fields=state["bc_summary"]["pk_codes"]`, `fk_field=infer_fk_field(pk_codes)` (first PK that is not `domaincode`/`domaincodeex` — `qad_entity_registry.py:125-134`), `fk_type="character"`, `description=f"Custom BC: …"`. That writes **two** places: the in-memory `QAD_STANDARD_ENTITIES` cache via `register_custom_bc`, and the SQLite `parent_entities` table via `upsert_parent_entity` (`qad_entity_registry.py:176-195` → `database.py:140-177`, `ON CONFLICT(entity_code) DO UPDATE`, columns `entity_code, uri, pk_fields (JSON), fk_field, fk_type, description, source='custom', created_at, updated_at`). **[CONFIRMED]** Failure is swallowed with a warning only — `"Failed to persist custom parent '%s': %s"` (`:793-800`).

#### Post-14c — history row + `run_id` (**[CONFIRMED] in the router, after the generator is exhausted**)

**[CONFIRMED]** `backend/routers/client_extensions.py:184-203`. Builds `HistoryItem` and calls `save_run` → `INSERT INTO runs (id, created_at, user_input, bc_pascal, description, field_count, panel_count, status, summary_json, error_message, mode)` (`database.py:56-69`; table DDL `database.py:13-27`). `status` is `"success"` only if a `complete` frame was seen, else `"failed"` (`client_extensions.py:151`, `:174-177`). Then emits `{"type":"run_id","run_id":…}`. Persistence failure is logged, not raised (`:199-200`).

---

### A1.2 State-write map (single view)

**[CONFIRMED] The `state` dict is a plain local variable, created at `pipeline.py:397` (`state: Dict[str, Any] = {}`), never returned, never yielded, and never persisted.** It is scratch memory for one generator invocation and dies with it. Keys, in write order: `requirements` (`:405`/`:410`), `spec` (`:422`, overwritten `:471`), `bc_summary` (`:500`), `panel_plan` (`:548`), `placements` (`:586`), `form_summary` (`:606`), `eh_plan` (`:626`), `ts_code` (`:649`), `js_code` (`:674`), `view_summary` (`:699`), `lookup_summary` (`:118`).

Everything durable is written outside `state`:

| Sink | Written by | Keys/columns |
|---|---|---|
| SQLite `runs` | `database.save_run` (`database.py:56-69`), called from `client_extensions.py:198` | `id, created_at, user_input, bc_pascal, description, field_count, panel_count, status, summary_json, error_message, mode` |
| SQLite `parent_entities` | `database.upsert_parent_entity` (`database.py:140-177`), via `pipeline.py:785-792` | `entity_code, uri, pk_fields, fk_field, fk_type, description, source, created_at, updated_at` |
| In-memory registry | `qad_entity_registry.register_custom_bc` (`:137-…`, called `:176-184`) | `QAD_STANDARD_ENTITIES[entity_code] = {uri, pk_fields, fk_field, fk_type, …}` |
| QAD server | steps 3, 3.5, 7, 11, 13, 14 | see per-step rows |
| Disk (transient) | `ts_compiler.check_typescript_syntax` (`ts_compiler.py:74-76`) | `generated_handler.ts` inside a deleted `TemporaryDirectory` |

**[CONFIRMED] No file on disk is written durably by the pipeline. There is no per-run artifact directory, no cached spec/TS/JS on disk.** `state["ts_code"]` / `state["js_code"]` are lost the moment the generator returns; the only copy that survives is whatever QAD stored in step 11.

**[CONFIRMED] LLM-call budget per run:** 7 on the happy path (steps 1, 2, 5, 6, 8, 9, 10); 6 when `parsed_requirements` skips step 1; up to 9 with the step-4 auto-fix and the step-6 retry. The rate-limit comment at `client_extensions.py:118` says `# each run spawns 8 LLM calls` — **[CONFIRMED]** that number matches none of the actual paths; it is stale documentation. **[CONFIRMED] Token fetches:** up to 7 per run, one per QAD-calling step, no caching (`pipeline.py:434, 475, 514, 596, 684, 708, 737`).

---

### A1.3 Where a human approval gate could attach

**[CONFIRMED] There is no approval gate anywhere in this pipeline today.** `grep -rni "approv|human.in.the.loop|await_user|pause"` over `backend/` returns only: a dropdown *example value* named `approval` (`prompts.py:76`), an unrelated QAD payload flag `isAllowApproval: False` (`embedded_builder.py:189`), and three hits in the **separate** SSS feature (`routers/sss.py:4, 21, 101`). The only "Approve" button in the product is SSS's (`frontend/src/features/sss/ReviewDeploy.tsx:92`, `"Approve & Deploy"`).

**[CONFIRMED] Current control flow between steps** is uniform and gives a gate exactly one natural shape: each step is a `try` block that either `yield`s `_evt("step", n, "done", …)` and falls through to the next block, or `yield`s `_evt("error", n, "error", …)` and `return`s. There is no shared step boundary, no callback, no `await` on any external signal — the generator only ever *pushes*.

**[CONFIRMED] The structural fact that decides everything:** the transport is a one-way `StreamingResponse` over a single POST (`client_extensions.py:205-212`), and the frontend consumes it with `fetch` + `AbortController` (`frontend/src/features/client_ext/api.ts:74-83`). There is **no channel back into a running generator** — the only client→server action mid-run is abort. So an in-place gate is not just unimplemented, it is unreachable without a transport change.

**[CONFIRMED] The three cleanest attachment points, ordered by how much they'd protect:**

1. **Between step 6 (`done`, `pipeline.py:590`) and step 7 (`pipeline.py:593`)** — the last moment before the *form* is written to QAD. Everything up to here is local (`spec`, `panel_plan`, `placements` are all in `state`); step 7 is the first irreversible form write. Note that step 3 has *already* created the BC by this point.
2. **Between step 2 (`done`, `pipeline.py:426`) and step 3 (`pipeline.py:429`)** — the only point before **any** QAD mutation at all. `state["spec"]` is fully formed and nothing has been POSTed. **[INFERRED]** This is the correct place for a spec-approval gate if the goal is "nothing lands in QAD without a human OK"; the code structure supports it (steps 3+ read only `current_spec`), but no mechanism exists. Confirmable by checking whether product intent is spec-approval or layout-approval.
3. **Between step 13.5 and step 14 (`pipeline.py:731` → `:734`)** — a deploy gate. Also the natural home for approving the Phase 11 static lookup payloads, since `_emit_lookup_events` deliberately stops at `dry_run=True` precisely because a human must verify `_needs_verification` before a live POST (`lookup_generator.py:23-25`, `:259-260`).

**[INFERRED] Mechanically, the least invasive route** is to split `run_pipeline` at the chosen boundary and persist the intermediate `state` (today it is process-local and lost), so a second request can resume — because a gate cannot be inserted as a mere `await` inside the current generator without also giving the client a way to reply. What would confirm the intended shape: whether the commissioner wants resume-across-requests (needs a new table + a `/api/run/{id}/approve` route) or a same-connection gate (needs a WebSocket or a polled server-side flag).

**[CONFIRMED] One live obstacle to any gate:** the UI cannot currently render mid-run decision data. `frontend/src/features/client_ext/api.ts:6` types `SSEEvent.type` as `"step" | "error" | "complete" | "run_id"` only, and `ProgressPanel.tsx:51-58` filters `if (e.type === "step" && e.step)`. So the `warning`, `lookup_candidate`, `lookup_needs_review`, and `lookup_summary` frames are pushed into the events array (`ClientExtPanel.tsx:99`) and then **silently dropped** — and `summary.lookups` is never rendered either (`grep -rn "lookup" frontend/src/` matches nothing outside an unrelated embedded label and CSS tokens). Any gate would need this plumbing built first.

---

### A1.4 Audit item 2 — is client-extension / server-side generation a step *inside* this pipeline?

**[CONFIRMED] Client-extension generation IS inside this pipeline — steps 8→11, four of the fourteen steps.** Evidence:

- The whole pipeline is *served by the client-extensions router*: `routers/client_extensions.py:1-3` docstring ("the custom / embedded Business Component pipeline"), `POST /api/run` at `:117-119`, importing `run_pipeline` from `pipeline` at `:21`.
- Steps 8 and 9 both load the docs bundle literally named `"client_extension_event_handler"` (`pipeline.py:619` and `:642`; bundle defined at `core/qad_docs_loader.py:47-52`).
- Step 9's prompt is `TS_CODE_WRITER` = `"You are a QAD TypeScript Event Handler developer."` (`prompts.py:247`).
- Step 11 POSTs to `eventhandler` a payload whose object is `eventHandlerV2s[0]` with `"appliesTo": "WEB"`, `"eventHandlerType": "BEFORE"`, `typeScriptCode`, `javaScriptCode` (`builders/event_handler_builder.py:25-37`; POST at `pipeline.py:685`). `appliesTo: "WEB"` is the client-side marker.

So the answer is unambiguous: the CE handler is generated (step 9), pseudo-compiled (step 10) and registered (step 11) as ordinary inline steps of the same generator, with no separate route, no separate approval, and no way to skip them.

**[CONFIRMED] Server-side generation is a SEPARATE flow. It shares nothing with `run_pipeline`.** Evidence:

- Different router and prefix: `router = APIRouter(prefix="/api/sss")` (`routers/sss.py:35`), registered independently in `main.py`'s `ROUTERS` tuple alongside `client_extensions_router`.
- Different shape: SSS routes are **sync `def`**, request/response, **not** generators and **not** SSE — and the docstring says why: "they call blocking libraries (OpenAI SDK, subprocess tsc, requests), so FastAPI runs them in a threadpool" (`sss.py:9-12`). Routes: `GET /bcs`, `GET /bcs/{name}`, `POST /generate`, `POST /deploy`, `GET /connection` (`sss.py:55, 73, 83, 99, 123`).
- Different code tree: `backend/sss/{discover,generate,compile,deploy,appconfig,readiness,templates}.py`, imported only by `routers/sss.py` (`sss.py:31-34`). `run_pipeline` imports none of it.
- Different docs bundle: `"server_side_rule"` (`qad_docs_loader.py:53-58`) — never requested by `pipeline.py`, which only ever asks for `"client_extension_event_handler"`.
- Different model policy, stated in `pipeline.py`'s own comment at `:137-138`: *"The SSS pipeline keeps using config.openai_model() because SSS is intentionally one-model."*
- **And crucially: SSS already has the human gate this pipeline lacks.** Generation and deployment are two separate HTTP calls — `POST /api/sss/generate` explicitly *"No disk write, no deploy"* (`sss.py:86`), and `POST /api/sss/deploy` *"Write the approved .ts, compile with tsc, then upload to QAD"* (`sss.py:101`), driven by the `"Approve & Deploy"` button at `ReviewDeploy.tsx:92`. SSS also uses the *real* `tsc` to emit JS and rolls back the `.ts` on compile failure (`sss.py:105-111`), where the BC pipeline uses an LLM for the same job.

**[CONFIRMED] Absence worth stating plainly: `run_pipeline` never touches server-side rules at all.** No step generates, compiles, or deploys a server-side script; there is no `/api/sss` call from `pipeline.py`; the two features only meet in `main.py`'s router tuple and in the shared `core/` plumbing (`config`, `qad_docs_loader`, `rate_limit`, `logging_setup`, `ts_compiler`).

---

### A1.5 Findings and absences (things that are notably *not* there)

1. **[CONFIRMED] Step numbering is not injective.** `TOTAL_STEPS = 14` but there are **16 distinct work units**: the two extras (dropdown wiring, lookup detection) have no numbers. Dropdown wiring emits a *second* `step:3 running` and `step:3 done` (`pipeline.py:511`, `:540`), so a client keying state by step number sees step 3 complete twice. Lookup frames carry no `step` key at all (`_sse`, `pipeline.py:29-31`).
2. **[CONFIRMED] Step numbers move backwards.** The auto-fix path yields `step 4 running` → `step 4 done` → `step 3 running` → `step 3 done` (`pipeline.py:458, 469, 473, 499`). Any monotonic-progress assumption in a consumer is wrong.
3. **[CONFIRMED] Only 9 of 14 steps are shown to the user.** `STANDARD_VISIBLE_STEPS = [1, 2, 3, 5, 7, 9, 11, 13, 14]` (`ProgressPanel.tsx:20`) — steps 4, 6, 8, 10, 12 are never rendered (4 is additionally hidden when pending, `:68`). Yet an *error* raised in a hidden step still surfaces, via the separate error box that prints `errorEvent.name` (`ProgressPanel.tsx:91-98`) — so a user can see "Failed at: Building panel layout" for a step that was never in the list.
4. **[CONFIRMED] The failing step is never marked failed in the step list.** `ProgressPanel.tsx:51-58` only records `e.type === "step"`; error frames go to a separate `errorEvent` prop. The step that died stays visually `running` (spinner) beside the red box.
5. **[CONFIRMED] `deployCheckForWarnings` is fire-and-forget.** `pipeline.py:739` discards the response; deploy warnings can never block the deploy or reach the user.
6. **[CONFIRMED] Error-message quality is inconsistent.** The uncommitted `_qad_error_messages` humaniser (`pipeline.py:209-223`) is wired into **only** step 3 (`:481`); steps 7, 11, 13, 14 still emit raw `json.dumps(err)` (`:603, :691, :718, :747`).
7. **[CONFIRMED] Step 13's two failure branches emit identical text** (`"View registration failed: …"` at `:714` and `:718`), so a network failure and a QAD rejection are indistinguishable.
8. **[CONFIRMED] The step-10 "compile" is an LLM, not a compiler**, and its output is never validated — the real `tsc` runs `--noEmit` in step 9 (`ts_compiler.py:79`) and produces no JS. Unverified JS is POSTed to QAD as `javaScriptCode` (`event_handler_builder.py:33`).
9. **[CONFIRMED] The step-9 syntax gate silently no-ops when `tsc` is absent** — returns `(True, "…syntax check skipped.")` (`ts_compiler.py:69-71`), and the pipeline treats that as a pass (`pipeline.py:657-658`).
10. **[CONFIRMED] `STEP_LABELS` is duplicated verbatim in the frontend** (`pipeline.py:145-160` vs `ProgressPanel.tsx:3-18`), and `TOTAL_STEPS` a third time in `models.py:33`. Three copies, no shared source.
11. **[CONFIRMED] QAD credentials travel in the OAuth **query string**, and a fresh token is fetched per step** (`qad_client.py:43-49`; 7 call sites). Username/password in a URL is logged by most reverse proxies.
12. **[CONFIRMED] Steps 11 and 14 write nothing to `state`**, so `ts_code_length`/`js_code_length` and the deploy `entityURI` never reach the history row, unlike every other builder's summary.

---

---

## A2. Case 2 — Embedded: full step inventory

*Audited tree: `D:/WEB_AUX/aux_web_version`. All paths below are relative to that root. Line numbers are from the working tree as read (note: `backend/pipeline_embedded.py`, `backend/builders/embedded_builder.py`, and `backend/builders/event_handler_builder.py` are unmodified since commit `84d209b`; `git status` shows them clean).*

### A2.0 Entry point and transport

- **[CONFIRMED]** HTTP entry: `POST /api/run`, declared at `backend/routers/client_extensions.py:117-119`, rate-limited `5/minute` (`backend/routers/client_extensions.py:118`). Router is mounted with no prefix at `backend/main.py:82,89,93-94`.
- **[CONFIRMED]** Mode dispatch: `run_embedded_pipeline(req.message)` is selected when `req.mode == "embedded"`, otherwise `run_pipeline(...)` — `backend/routers/client_extensions.py:158-166`. Only `req.message` is passed to the embedded pipeline; `parsed_requirements` and `lookup_candidates` are standard-mode only.
- **[CONFIRMED]** `mode` is a plain string on the request model, default `"standard"` (`backend/models.py:11-14`). Frontend sends `{message, mode}` to `${BASE}/run` (`frontend/src/features/client_ext/api.ts:78-83`), with `mode` held in `useState<"standard" | "embedded">` (`frontend/src/features/client_ext/ClientExtPanel.tsx:47`, toggle option at `:223`, passed at `:97`).
- **[CONFIRMED]** Embedded mode explicitly **bypasses** the deterministic Progress (.p/.cls) parser: `if req.mode != "embedded":` at `backend/routers/client_extensions.py:129`, with the stated reason in the comment at `:122-125` ("Embedded mode doesn't currently benefit (it picks a parent entity from a fixed registry)").
- **[CONFIRMED]** Transport is a one-way `StreamingResponse` of `text/event-stream` (`backend/routers/client_extensions.py:205-212`). The wrapper generator `event_stream()` (`:148-203`) re-parses each chunk only to capture `summary` / `error` for history (`:170-180`), then saves a `HistoryItem` (`:184-200`) and finally emits `{"type":"run_id","run_id":...}` (`:203`).
- **[CONFIRMED]** SSE frame shape for every embedded event, built by `_evt()` at `backend/pipeline_embedded.py:44-59`: keys `type`, `step`, `total`, `name`, `status`, `message`, plus optional `summary` and `error`. `name` is resolved from `STEP_LABELS` (`:32-41`).
- **[CONFIRMED]** `total` is dynamic: `BASE_TOTAL_STEPS = 7` (`backend/pipeline_embedded.py:30`), raised to `8` when `wants_separate_view` is true (`:104-105`).
- **[CONFIRMED]** QAD URL shape for every call below: `{QAD_BASE_URL}/qad-central/api/qracore/<endpoint>` (`backend/qad_client.py:57` for POST, `:65` for GET). Token: `POST {QAD_BASE_URL}/qad-central/oauth/token?client_id=…&username=…&password=…&grant_type=password` (`backend/qad_client.py:43-53`), re-fetched per step via `await get_token()`.
- **[CONFIRMED]** Success test is `is_qad_success()` — requires `submitResult.success is True`, `errorSeverity == 0`, and empty `errors` (`backend/qad_client.py:72-82`).
- **[CONFIRMED]** LLM plumbing is imported from the standard pipeline: `from pipeline import _llm, _parse_json_output, MODEL_MATRIX` (`backend/pipeline_embedded.py:20`). `MODEL_MATRIX` = `{"planning":"gpt-4o-mini","generation":"gpt-4o","compile":"gpt-4o-mini"}` (`backend/pipeline.py:136-140`). `_llm` at `backend/pipeline.py:180-192`; `_parse_json_output` at `:195-206`.
- **[CONFIRMED]** Docs grounding helper: `_docs_context(bundle_name)` (`backend/pipeline_embedded.py:24-27`) wraps `docs_loader.get_bundle(...)`. The embedded pipeline only ever requests the `"business_component"` bundle (`:76`, `:123`), which maps to folders `Business Components - Form Builder`, `App Development Concepts`, `Platform Scripting - TypeScript` (`backend/core/qad_docs_loader.py:59-63`). Fail-soft: unknown/unloaded → `""` (`backend/core/qad_docs_loader.py:106-122`).

### A2.1 Ordered step inventory

| id | `STEP_LABELS` name (verbatim) | Kind | LLM prompt | QAD call (method + path) | Produces / writes |
|---|---|---|---|---|---|
| 1 | `Understanding Embedded BC requirements` | LLM + local registry lookup | `EMBEDDED_REQUIREMENTS_GATHERING` | none | `requirements`; `state["requirements"]`; `parent_key`, `entity_info`, `wants_separate_view`, `total_steps` |
| 2 | `Designing Embedded BC fields` | LLM + deterministic PK guard | `EMBEDDED_FIELD_CREATOR` | none | `spec` (`bc_pascal`,`description`,`fields[]`); `state["spec"]` |
| 3 | `Creating Business Component metadata` | builder + mutation | none | `POST entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` | `bc_data` = `{status,payload,field_list_map,entity_uri,summary}`; BC entity metadata + entityDeployment + entityTable + dataLists in QAD |
| 4 | `Handling duplicates & auto-fix` | conditional LLM + retry mutation | `VALIDATOR_AND_CORRECTOR` | same `POST entitymetadatas?viewUri=…IEntityBuilderCRUD` (retry) | `fix_parsed`; replaces `current_spec`; `state["spec"]` |
| 3.5 (re-emits step id **3**) | `Creating Business Component metadata` | read-back + patch mutation | none | `GET entitymetadatas?entityURI=<url-encoded CHILD uri>&viewUri=…IEntityBuilderCRUD` then `POST` the same path | dropdown `dataListCode` + `defaultValue` wired onto the child's own fields |
| 5 | `Building relations to parent entity` | builder + mutation | none | `POST berelation?viewUri=urn:be:com.qad.qra.berelation.IBERelation` | `relation_data` = `{payload}`; one `BERelations[0]` record in QAD |
| 6 | `Checking deployment warnings` | builder + mutation | none | `POST deployCheckForWarnings` (body `deploy_data["stepA"]`) | `deploy_data` = `{stepA, stepB}`; **result discarded** |
| 7 | `Deploying Business Component` | mutation | none | `POST deployBusinessEntity` (body `deploy_data["stepB"]`) | deployed BE (physical table) |
| 8 (optional) | `Registering standalone view in QAD` | builder + mutation | none | `POST viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` | `view_data`; `state["view_label"]`; hybrid-browse view metadata in QAD |
| — | `complete` event | terminal | none | none | `summary` (10 keys, see A2.1.9) |

All rows above are **[CONFIRMED]** from `backend/pipeline_embedded.py:32-41` (labels) and the per-step code cited below.

#### A2.1.1 Step 1 — `Understanding Embedded BC requirements`
- **[CONFIRMED]** Emitted running at `backend/pipeline_embedded.py:69`.
- **[CONFIRMED]** Prompt assembled by two `.replace()` calls (not `.format`, per the comment at `:71-73`): `{QAD_DOCS_CONTEXT}` ← `_docs_context("business_component")`, `{ENTITY_MENU}` ← `entity_menu_for_prompt()` — `backend/pipeline_embedded.py:74-78`. Template at `backend/agents/prompts.py:391-451`; the two placeholders live at `prompts.py:403` and `:406`.
- **[CONFIRMED]** Call: `_llm(client, prompt_with_menu, user_message, model=MODEL_MATRIX["generation"], json_mode=True)` (`:79-82`) → `gpt-4o`, JSON mode.
- **[CONFIRMED]** Exact output keys the prompt demands (`backend/agents/prompts.py:433-450`): `parent_entity_key`, `bc_pascal`, `description`, `wants_separate_view`, `child_pk` (`{code, dataType}`), `custom_fields[]` (`{code, dataType}` + `dropdown_values[{code,label}]` for dropdown types).
- **[CONFIRMED]** State written: `state["requirements"] = requirements` (`:84`).
- **[CONFIRMED]** Parent resolution is a **local, in-memory registry lookup**: `parent_key = requirements.get("parent_entity_key","")`; `entity_info = get_entity(parent_key)` (`:90-91`). On miss, hard error listing `supported_entity_codes()` (`:95-102`).
- **[CONFIRMED]** `wants_separate_view` read at `:104`; `total_steps` set at `:105`; step-1 `done` message is `f"Target: {parent_key} | Separate view: {wants_separate_view}"` (`:107-109`).

#### A2.1.2 Step 2 — `Designing Embedded BC fields`
- **[CONFIRMED]** Input to the LLM is `json.dumps({**requirements, "fk_field": entity_info["fk_field"], "fk_type": entity_info["fk_type"]})` (`backend/pipeline_embedded.py:115-121`).
- **[CONFIRMED]** System prompt `EMBEDDED_FIELD_CREATOR` with `{QAD_DOCS_CONTEXT}` replaced (`:122-124`); template at `backend/agents/prompts.py:453-515`, placeholder at `:456`. `gpt-4o`, `json_mode=True` (`:125-128`).
- **[CONFIRMED]** Mandated PK ordering in the prompt (`backend/agents/prompts.py:468-474`): `1. domaincodeEx`, `2. <fk_field>`, `3. <child_pk.code>`, then custom fields with `isPrimary:false`. Rationale quoted in the prompt at `:477` — the QAD rule that the extension entity's full PK cannot be contained in the N-1 FK.
- **[CONFIRMED]** Deterministic guard after parse (`:132-149`): `fk_codes = {"domaincodeex", entity_info["fk_field"].lower()}`; if no PK exists outside `fk_codes`, a fallback child PK is **inserted at index 2**:
```python
fallback_code = requirements.get("child_pk", {}).get("code") or f"{spec['bc_pascal']}Code"
fallback_type = requirements.get("child_pk", {}).get("dataType", "character")
spec["fields"].insert(2, {
    "code":       fallback_code,
    "dataType":   fallback_type,
    "isPrimary":  True,
    "isRequired": True,
})
```
(`backend/pipeline_embedded.py:141-149`)
- **[CONFIRMED]** State written: `state["spec"] = spec` (`:151`).

#### A2.1.3 Step 3 — `Creating Business Component metadata`
- **[CONFIRMED]** `bc_data = build_embedded_schema_payload(current_spec)` (`:165`); `token = await get_token()` (`:166`); `POST entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` with `bc_data["payload"]` (`:167-170`).
- **[CONFIRMED]** Builder return keys: `status`, `payload`, `field_list_map`, `entity_uri`, `summary{bc_pascal, module, field_count, pk_count, pk_codes}` (`backend/builders/embedded_builder.py:233-245`).
- **[CONFIRMED]** Payload top-level keys (`backend/builders/embedded_builder.py:224-231`): `activityTrackingInfos`, `entityDeployments`, `entityMetadatas`, `lookupBERelations` (`[]`), `relatedLookups` (`[]`), `viewResourceInfos`.
- **[CONFIRMED]** Identity constants: `MODULE = "com.extensions.customapp"` (`:13`); `entity_uri = f"urn:be:{MODULE}.{bc_pascal}.I{bc_pascal}"` (`:48`); `table_low = f"xx{bc_pascal.lower()}"` (`:49`).
- **[CONFIRMED]** Extension-specific metadata flags: `"isDataExtensionEnable": True`, `"isDataExtensionOnly": True` (`:192-193`), `"bcType": "Standard"` (`:167`), `"scope": "SYSTEM"` (`:200`), `"isAllowApproval": False` (`:189`).
- **[CONFIRMED]** `viewResourceInfos[0]` is a stub asserting **no** UI artifacts: `"eventHandlerInfos": []`, `"existingForm": "No"`, `"existingGridForm": "No"`, `"gridViewURI": None`, `"parentEntity": "none"`, `"viewURI": None`, `"isVirtualBE": True`, `"dataExtensionOnly": True` (`backend/builders/embedded_builder.py:206-222`). Note `parentEntity` is the literal string `"none"` here — the real parent linkage happens only in step 5.
- **[CONFIRMED]** Per-field record keys are fully enumerated at `backend/builders/embedded_builder.py:74-127` (incl. `entityFieldCode`, `fieldURI`, `jsonName`, `primaryKey` as a 1-based counter `:63-67`, `dataListCode: ""` deliberately blank per the comment at `:79`, and `"overrideContextType": "Domain" if f["code"] == "domaincodeEx" else None` at `:116`).
- **[CONFIRMED]** `tableKeyFields` is the comma-joined PK codes (`:130`); `entityTables[0].jsonName = f"{table_low}s"` (`:155`).
- **[CONFIRMED]** Dropdown data lists come from the shared standard-BC helper: `data_lists, field_list_map = build_data_lists(fields)` (`:52`), defined at `backend/builders/bc_builder.py:114-157`; it raises `ValueError` when a dropdown field lacks `dropdownValues` (`bc_builder.py:132-137`).
- **[CONFIRMED]** No success check happens inside step 3's `try`; the result is evaluated by step 4's `if not is_qad_success(bc_result):` at `:176`.

#### A2.1.4 Step 4 — `Handling duplicates & auto-fix` (conditional)
- **[CONFIRMED]** Entered only on failure (`:176-179`). Prompt `VALIDATOR_AND_CORRECTOR` (`backend/agents/prompts.py:100-155`) — note this is the **shared** standard-pipeline recovery prompt, with **no** `{QAD_DOCS_CONTEXT}` placeholder and no embedded-specific rules (it never mentions `domaincodeEx`, FK fields, or the child-PK constraint).
- **[CONFIRMED]** User message is a 3-part blob: `Requirements Summary` + `Spec that was submitted` + `Error from QAD server` (`:181-185`); `gpt-4o`, `json_mode=True` (`:186-189`).
- **[CONFIRMED]** On `status == "fixed"`: `current_spec = fix_parsed["spec"]`, `state["spec"] = current_spec` (`:196-197`), then step 3 is **re-emitted as running** (`:200-202`) and the same endpoint is re-POSTed (`:203-208`). A second failure is terminal (`:209-214`). On `status != "fixed"` → error with `fix_parsed.get("reason", …)` (`:215-218`).
- **[CONFIRMED]** On the happy path step 4 emits `done` with `"No conflicts — proceeding"` (`:222-223`), then step 3 `done` is emitted at `:225-227`.
- **[CONFIRMED]** Unlike the standard pipeline, the embedded pipeline has **no** duplicate-name short-circuit: `_is_duplicate_entity_error` / `_qad_error_messages` exist only in `backend/pipeline.py:209-231` and are not imported by `backend/pipeline_embedded.py:20`.

#### A2.1.5 Step 3.5 — dropdown wiring (re-uses step id 3)
- **[CONFIRMED]** Gate: `field_list_map = bc_data.get("field_list_map") or {}` then `if field_list_map:` (`:234-235`).
- **[CONFIRMED]** Sequence: URL-encode `bc_data["entity_uri"]` (`:238`) → `GET entitymetadatas?entityURI={entity_uri_q}&viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` (`:239-243`) → unwrap `{"data": {...}}` (`:244`) → guard on missing `entityMetadatas` (`:245-249`) → `patch_dropdown_fields(enriched, field_list_map)` (`:250`) → `POST` the same path with the enriched body (`:251-254`).
- **[CONFIRMED]** `patch_dropdown_fields` sets `field["dataListCode"] = info["listCode"]` and `field["defaultValue"] = info["defaultValue"]`, keyed on `field.get("entityFieldCode")` (`backend/builders/bc_builder.py:98-111`).
- **[CONFIRMED]** Step-id collision: this block emits step `3` `running` at `:236` **after** step 3 was already emitted `done` at `:225`, then emits step 3 `done` again at `:262`. A UI keyed on step id sees 3 → done → running → done.

#### A2.1.6 Step 5 — `Building relations to parent entity`
- **[CONFIRMED]** Call args (`backend/pipeline_embedded.py:269-275`): `bc_pascal=current_spec["bc_pascal"]`, `fields=current_spec["fields"]`, `parent_entity_code=parent_key`, `parent_entity_uri=entity_info["uri"]`, `fk_field_code=entity_info["fk_field"]`.
- **[CONFIRMED]** `POST berelation?viewUri=urn:be:com.qad.qra.berelation.IBERelation` with `relation_data["payload"]` (`:277-280`), success-checked at `:284-289`.
- **[CONFIRMED]** Payload (`backend/builders/embedded_builder.py:280-321`): `supplementaryMessages: []` plus one `BERelations` entry with `BERelationFields` = exactly **two** mappings — `{sourceFieldCode: domaincodeEx → relatedFieldCode: <parent domain field>}` and `{sourceFieldCode: fk_field → relatedFieldCode: fk_field}` (`:283-295`).
- **[CONFIRMED]** The parent's domain field name is derived **from the local registry**, not from QAD: `parent_info = get_entity(parent_entity_code)`; first `pk_fields` entry containing `"domain"`, default `"DomainCode"` (`:268-276`).
- **[CONFIRMED]** Relation flags: `"cardinality": "MANYTOONE"` (`:298`), `isCascadeDelete: False`, `isCascadeDeleteForBD: True`, `isDrill: False`, `isEmbedded: False`, `isExtension: True`, `isIncludeOnParent: False`, `isLookup: False`, `isParent: False`, `isUseInBusinessDocument: True`, `isVisualizedAsDropDown: False`, `relationType: "child"` (`:299-315`).
- **[CONFIRMED]** `relationID` is a partially fixed, partially random string: `"8c9676c6-0c12-13a3-f114-" + uuid_str().replace("-","")[:12]` (`:278`) — i.e. the first three UUID groups are hardcoded.

#### A2.1.7 Step 6 — `Checking deployment warnings`
- **[CONFIRMED]** `deploy_data = build_embedded_deploy_payload(current_spec["bc_pascal"])` (`:297`) returns `{"stepA": {...}, "stepB": {...}}` (`backend/builders/embedded_builder.py:326-341`). `stepA` keys: `entityURI`, `isInitialDataLoaded`. `stepB` keys: `entityURI`, `appURI`, `dataStoreURI` (`"urn:datastore:com.extensions.extension"`), `isInitialDataLoaded`, `allowActivityTracking`.
- **[CONFIRMED]** `await post_qad("deployCheckForWarnings", deploy_data["stepA"], token)` — **the return value is not assigned and never inspected** (`backend/pipeline_embedded.py:299`). Only a raised exception can fail this step (`:300-302`). Warnings/errors returned in the body are silently dropped.

#### A2.1.8 Step 7 — `Deploying Business Component`
- **[CONFIRMED]** `deploy_result = await post_qad("deployBusinessEntity", deploy_data["stepB"], token)` (`:309`), success-checked at `:313-316`, `done` at `:317`.

#### A2.1.9 Step 8 — `Registering standalone view in QAD` (optional)
- **[CONFIRMED]** Gated on `if wants_separate_view:` (`:320`). `build_view_payload` is imported **locally inside the branch** (`from builders.view_builder import build_view_payload`, `:325`) — i.e. `view_builder` is not a module-level dependency of the embedded pipeline.
- **[CONFIRMED]** `POST viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` with `view_data["payload"]` (`:328-331`), success-checked at `:332-337`.
- **[CONFIRMED]** This is the **same** builder the standard pipeline uses (`backend/pipeline.py:698,709-712`), producing a `HYBRID_BROWSE` view: `"typeField": "HYBRID_BROWSE"` (`backend/builders/view_builder.py:161`), `browseView` + `maintView` + `hybridBrowseView` + `entityViewParameters` (`view_builder.py:109-147`), `isEligibleForMenu: True` (`:106`).
- **[CONFIRMED]** State written: `state["view_label"] = view_data.get("summary", {}).get("view_label", "")` (`:339`); `view_label` computed by `to_view_label()` (`backend/builders/view_builder.py:40-47,102`).
- **[CONFIRMED]** The frontend has **no row for step 8** in embedded mode: `EMBEDDED_STEP_NAMES` covers ids 1-7 only and `EMBEDDED_VISIBLE_STEPS = [1,2,3,4,5,6,7]` (`frontend/src/features/client_ext/components/ProgressPanel.tsx:22-32`), and `visibleSteps` is never extended (`:49`, `:64`). So the optional view-registration step runs invisibly in the UI.

#### A2.1.10 Terminal `complete` event
- **[CONFIRMED]** `summary` keys, verbatim (`backend/pipeline_embedded.py:345-364`): `bc_pascal`, `description`, `field_count`, `fields` (each `{code, dataType, isPrimary, isRequired}`), `panel_count` (**hardcoded `0`**, `:358`), `panels` (**hardcoded `[]`**, `:359`), `pk_codes`, `parent_entity` (= `parent_key`), `view_label`, `module` (`"com.extensions.customapp"`).
- **[CONFIRMED]** Emitted as `_evt("complete", total_steps, "done", "All embedded steps complete!", summary=summary, total=total_steps)` (`:365-368`).
- **[CONFIRMED]** Persistence: the router maps this summary into `HistoryItem` with `mode=req.mode` (`backend/routers/client_extensions.py:185-197`), so `panel_count` is stored as `0` for every embedded run.

#### A2.1.11 Complete state-key inventory
- **[CONFIRMED]** `state` is a plain local dict created at `backend/pipeline_embedded.py:64` and never persisted or returned. Only four keys are ever written: `state["requirements"]` (`:84`), `state["spec"]` (`:151` and `:197`), `state["view_label"]` (`:339`).
- **[CONFIRMED]** Only `state["view_label"]` is ever read back (`:362`). `state["requirements"]` and `state["spec"]` are **write-only** — the live values flow through the locals `requirements` and `current_spec` instead.

### A2.2 Answers to the commissioner's questions

#### Q1. What does "embedded" produce today? Is it a GRID only?

**[CONFIRMED] Artifact types actually created (exhaustive — these are the only QAD-mutating calls in the file):**
1. **BC entity metadata + entity deployment + entity table + dropdown data lists** — `POST entitymetadatas?viewUri=…IEntityBuilderCRUD` (`backend/pipeline_embedded.py:167-170`; payload keys `entityDeployments` / `entityMetadatas` / `viewResourceInfos` / `activityTrackingInfos` / `lookupBERelations` / `relatedLookups` at `backend/builders/embedded_builder.py:224-231`).
2. **A second-pass patch of the same entity metadata** to wire `dataListCode`/`defaultValue` on dropdown fields (`:239-254`).
3. **One BERelation** child→parent record — `POST berelation?viewUri=…IBERelation` (`:277-280`).
4. **A deploy-warnings probe** — `POST deployCheckForWarnings` (`:299`).
5. **A deployed business entity** (physical `xx<bcname>` table) — `POST deployBusinessEntity` (`:309`).
6. **Optionally, one standalone hybrid-browse view resource** — `POST viewResourceMetadatas?viewUri=…IViewResourceMetadata`, only when `wants_separate_view` is true (`:320-331`).

**[CONFIRMED] It does NOT create:**
- **No form / panel layout.** `build_form_payload` is never imported or called in `backend/pipeline_embedded.py` (imports at `:1-21`); the `viewMetadataV2` endpoint used by the standard pipeline (`backend/pipeline.py:597`) appears nowhere in the embedded flow. `panel_count` is hardcoded `0` and `panels` `[]` (`backend/pipeline_embedded.py:358-359`).
- **No event handler.** `build_event_handler_payload` is not imported by the embedded pipeline, and the `eventhandler` endpoint is only POSTed from `backend/pipeline.py:685`. `viewResourceInfos[0]["eventHandlerInfos"]` is shipped as `[]` (`backend/builders/embedded_builder.py:212`).
- **No TypeScript/JavaScript at all.** `TS_CODE_WRITER`, `TS_COMPILER`, `EVENT_HANDLER_PLANNER`, `check_typescript_syntax` are absent from the embedded imports (`backend/pipeline_embedded.py:7-21`). Corroborated by the project's own note: "`pipeline_embedded.py` confirmed NOT to use TS_CODE_WRITER (no leak)" (`PROGRESS.md:197`).
- **No lookups.** `lookup_detector` / `lookup_generator` are not imported by the embedded pipeline, and the router skips the parser for embedded mode (`backend/routers/client_extensions.py:129`).
- **No registry self-registration.** The standard pipeline registers its new BC as a future parent via `register_and_persist_custom_bc(...)` (`backend/pipeline.py:781-792`); **there is no equivalent call anywhere in `backend/pipeline_embedded.py`** (grep for `register_and_persist` / `register_custom_bc` in that file returns nothing). So an embedded child BC never becomes selectable as a parent entity.

**Grid-only claim — [CONFIRMED as to the code, and as to the authors' recorded live test]:**
The BERelation is written with `"cardinality": "MANYTOONE"` (`backend/builders/embedded_builder.py:298`), `isEmbedded: False`, `isIncludeOnParent: False`, `isUseInBusinessDocument: True` (`:302-307`). The file carries an explicit dated finding block:

```
# ── Panel-vs-grid: FINDING (2026-07-15) ─────────────────────────────────
# We tested whether the "Composition Relation" / "Include Grid on Parent Form"
# BERelation flags could make an embedded BC render as a PANEL instead of a GRID.
# Result: they cannot. QAD derives those UI checkboxes from a combination of
# fields (isEmbedded + isUseInBusinessDocument), not 1:1, and every combination
# still rendered a grid. The grid is inherent to `cardinality: "MANYTOONE"`
# (many child rows per parent). A panel would require a ONETOONE redesign
# (child PK = domaincodeEx + parent FK only, no separate child identifier).
```
(`backend/builders/embedded_builder.py:15-24`; independently corroborated in `PROGRESS.md:186-189`, which records live tests on disposable BCs `PanelTest`/`PanelTestPavan`.)

**[INFERRED]** That the deployed artifact *renders* as a grid on the parent form is a QAD runtime behaviour I cannot verify from source — I am relying on the authors' recorded live test. What the code *guarantees* is `MANYTOONE` + a mandatory third child PK (`backend/agents/prompts.py:468-474`, enforced by the fallback at `backend/pipeline_embedded.py:132-149`), which is structurally incompatible with the ONETOONE panel shape the comment describes. **Confirmation would require** one live run plus a screenshot of the parent form, or a GET of the parent view metadata after deploy (which the pipeline never does — see Q3).

**Net answer: CONFIRMED — embedded produces a data extension whose parent-side UI is a grid, and nothing else UI-wise; the only optional extra artifact is a *separate standalone* hybrid-browse view, which is not on the parent form at all.**

#### Q2. Does `event_handler_builder.py` template ONE flat handler shape?

**YES — one flat shape, and only one. [CONFIRMED].** The whole file is 48 lines; the only signature is:

```python
def build_event_handler_payload(bc_pascal: str, ts_code: str, js_code: str) -> Dict[str, Any]:
```
(`backend/builders/event_handler_builder.py:6`)

There is no parameter for handler type, timing, base class, target, or scope. Every discriminating field is a hardcoded literal:

```python
    payload = {
        "supplementaryMessages": [],
        "eventHandlerV2s": [{
            "appURI": app_uri,
            "viewURI": view_uri,
            "eventHandlerType": "BEFORE",
            "appliesTo": "WEB",
            "isActive": True,
            "typeScriptCode": ts_clean,
            "javaScriptCode": js_clean,
            "mappingCode": "",
        }],
    }
```
(`backend/builders/event_handler_builder.py:25-37`)

- **[CONFIRMED]** `eventHandlerType` is the string literal `"BEFORE"` (`:30`) — there is no `AFTER`, no `INSTEAD`, no alternative timing anywhere in the file.
- **[CONFIRMED]** `appliesTo` is the literal `"WEB"` (`:31`) — no mobile/server variant.
- **[CONFIRMED]** Exactly one element in the `eventHandlerV2s` array (`:27-36`) — the builder cannot emit multiple handlers per call.
- **[CONFIRMED]** The target is derived purely from the BC name: `app_uri = f"urn:app:{MODULE}"` and `view_uri = f"urn:view:viewmeta:{MODULE}.{bc_pascal}"` with `MODULE = "com.extensions.customapp"` (`:3, :7-8`). There is no way to point it at a parent BC's view, a browse view, or a grid view.
- **[CONFIRMED]** The remaining ~20 lines are markdown-fence stripping for `ts_code` and `js_code` (`:10-23`), and a `summary` of `{bc_pascal, view_uri, ts_code_length, js_code_length}` (`:39-48`). No logic branches on anything.
- **[CONFIRMED]** The *class* shape is not templated here at all — it is templated in the **prompt**, also as a single fixed shape: module `com.extensions.customapp.EventHandler.{BCName}.ComExtensionsCustomapp.Maint_BEFORE`, one `{BCName}MaintHandler extends QraViewTSHandlerWithViewFormTSHandler<...>` and one `{BCName}FormHandler extends QraViewFormTSHandlerV2<...>` (`backend/agents/prompts.py:259-277`, header literally "FIXED MODULE/CLASS STRUCTURE" at `:257-258`). Only three callbacks are specified: `onInit`, `onFieldChange`, `onButtonClick` (`prompts.py:283-295`). Note the module name itself hardcodes `Maint_BEFORE` (`prompts.py:259`), matching the builder's `"BEFORE"`.
- **[CONFIRMED — and directly relevant to Phase 5]** This builder is **not reachable from the embedded pipeline at all**. Its only call site in the entire repo is `backend/pipeline.py:683` (import at `backend/pipeline.py:16`); a repo-wide grep for `build_event_handler_payload` returns exactly those two lines plus the definition.

**Answer to the commissioner, plainly: YES — the current generator templates a single flat handler shape (one `eventHandlerV2s` entry, `eventHandlerType:"BEFORE"`, `appliesTo:"WEB"`, one fixed `Maint_BEFORE` / `QraViewFormTSHandlerV2` class pair), it supports no other base class and no other timing, and it is wired only into the standard pipeline — the embedded pipeline never calls it.**

#### Q3. Does the embedded flow ever READ the parent BC's existing event handler or form/view metadata back from QAD?

**NO. [CONFIRMED] — stated plainly.**

- **[CONFIRMED]** `backend/pipeline_embedded.py` contains exactly **one** GET, at `:239-243`:
```python
get_response = await get_qad(
    f"entitymetadatas?entityURI={entity_uri_q}&viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD",
    token
)
```
and `entity_uri_q` is `urllib.parse.quote(bc_data["entity_uri"])` (`:238`), where `bc_data["entity_uri"]` is the **child's own** URI `urn:be:com.extensions.customapp.<BcPascal>.I<BcPascal>` (`backend/builders/embedded_builder.py:48`, returned at `:237`). It reads back the child BC it just created, solely to patch dropdown `dataListCode` (`:250`).
- **[CONFIRMED]** A repo-wide grep for `get_qad(` returns only three call sites: `backend/pipeline.py:516`, `backend/pipeline_embedded.py:240`, and the definition at `backend/qad_client.py:64`. There is no GET of `eventhandler`, no GET of `viewMetadataV2`, no GET of `viewResourceMetadatas`, and no GET of `berelation` anywhere in the codebase.
- **[CONFIRMED]** Everything the flow "knows" about the parent comes from the **static local registry**, never from QAD: `uri`, `pk_fields`, `fk_field`, `fk_type`, `description` in `_BUILTIN_ENTITIES` (`backend/qad_entity_registry.py:37-82`), read synchronously via `get_entity()` (`:94-96`). The parent's domain PK field is likewise guessed from that local `pk_fields` list (`backend/builders/embedded_builder.py:268-276`).
- **Consequence [INFERRED, from the above CONFIRMED absences]:** the pipeline cannot detect that the parent already has an event handler, cannot detect an existing extension grid on the parent form, and cannot detect a parent PK/FK drift between the hardcoded registry and the live QAD instance. A wrong `uri` or `fk_field` in the registry surfaces only as a QAD rejection at step 5. **Confirmation would require** nothing further on the read side — the absence is definitive; the failure-mode characterisation is my inference.

#### Q4. Where does the parent-BC identity come from, and what is done with it?

**Origin — [CONFIRMED]:** it is chosen by the **LLM**, from a menu injected into its prompt, then resolved against an in-process dict.
1. `entity_menu_for_prompt()` renders `- {key}: {description}` for every registry entry (`backend/qad_entity_registry.py:114-122`) and is spliced into `{ENTITY_MENU}` (`backend/pipeline_embedded.py:77`; placeholder at `backend/agents/prompts.py:406`).
2. The LLM returns `parent_entity_key` (contract at `backend/agents/prompts.py:437`); the pipeline reads `requirements.get("parent_entity_key", "")` (`backend/pipeline_embedded.py:90`).
3. `entity_info = get_entity(parent_key)` — a `dict.get` on the module-level `QAD_STANDARD_ENTITIES` cache (`backend/pipeline_embedded.py:91`; `backend/qad_entity_registry.py:94-96`). That cache is seeded from the 5 hardcoded built-ins `SalesOrderHeaders`, `PurchaseOrderHeaders`, `ItemMaster`, `InventoryMaster`, `WorkOrderMaster` (`backend/qad_entity_registry.py:37-82,87-89`) and overlaid at startup from the DB `parent_entities` table via `hydrate()` (`:198-212`, called from `backend/main.py` startup — migration/version guard commented at `backend/main.py:97-101`).
4. Unresolvable key → terminal step-1 error naming `supported_entity_codes()` (`backend/pipeline_embedded.py:95-102`).

**What is done with it — [CONFIRMED], five uses and no more:**
- `entity_info["fk_field"]` and `["fk_type"]` are injected into the step-2 field-creator input (`backend/pipeline_embedded.py:117-118`), which makes the FK a mandatory PK #2 (`backend/agents/prompts.py:471`).
- `entity_info["fk_field"].lower()` forms the `fk_codes` exclusion set used by the child-PK safety guard (`backend/pipeline_embedded.py:134`).
- `parent_key` + `entity_info["uri"]` + `entity_info["fk_field"]` are passed to `build_relation_payload` (`:271-274`), landing in the BERelation as `relatedEntityCode` / `relatedEntityURI` and the second `BERelationFields` mapping (`backend/builders/embedded_builder.py:290-294, 310-311`).
- `entity_info["pk_fields"]` is re-fetched *inside* the builder to guess the parent's domain field name (`backend/builders/embedded_builder.py:269-276`).
- `parent_key` is echoed in user-facing messages (`backend/pipeline_embedded.py:108, 266, 291`) and stored on the summary as `"parent_entity"` (`:361`).

**Not done with it — [CONFIRMED]:** never validated against live QAD (see Q3); never used to select a handler target, form, or view; the child BC's own `viewResourceInfos[0]["parentEntity"]` is left as the literal `"none"` (`backend/builders/embedded_builder.py:216`).

#### Q5. Where could a per-step approval gate attach?

**[CONFIRMED] structural facts that constrain the design:**
- The pipeline is a single `AsyncGenerator[str, None]` (`backend/pipeline_embedded.py:62`) consumed by `async for chunk in pipeline_gen:` inside `event_stream()` (`backend/routers/client_extensions.py:168-180`), returned as a one-way `StreamingResponse` (`:205-212`). There is **no inbound channel** on this route once the stream starts — the generator never `yield`s a value it can receive back (no `.asend(...)` anywhere; the router only iterates).
- There is **no approval/pause/resume machinery anywhere in the backend today**. A case-insensitive grep for `approval|approve|pause|resume|gate|confirm` across `backend/**/*.py` returns only: unrelated `tsc`/readiness/auth "gate" comments (`backend/core/ts_compiler.py:61`, `backend/sss/readiness.py:2`, `backend/core/auth.py:17`), the QAD payload literal `"isAllowApproval": False` (`backend/builders/embedded_builder.py:189`), SSS's `WithConfirmation` method discovery (`backend/sss/discover.py:43,109-113`), and prompt text. **Absence of any gate is a finding.**
- There is **no run correlation id available during the run**: `run_id` is generated server-side at `backend/routers/client_extensions.py:120` and only emitted **after** the pipeline generator is exhausted (`:203`). `RunRequest.run_id` exists (`backend/models.py:13`) but is **never read** — grep for `run_id` in the router shows `:120` (assign) and `:186,200,203` (use); `req.run_id` appears nowhere.

**[CONFIRMED] The clean seams, in execution order.** Everything before `backend/pipeline_embedded.py:165` is non-mutating (2 LLM calls + a dict lookup); the first irreversible QAD write is the POST at `:167`. So:

| Gate | Insert immediately after | What the user would be approving | First mutation it protects |
|---|---|---|---|
| **G1 (highest value — single gate covers the whole design)** | `:157` (step-2 `done`) | the full `spec`: `bc_pascal`, PK triple (`domaincodeEx`, `fk_field`, child PK), field list + dropdown values, chosen `parent_entity_key`, `wants_separate_view` | `POST entitymetadatas` at `:167` |
| G1a | `:109` (step-1 `done`) | parent-BC choice + BC name + `wants_separate_view` before field design burns a `gpt-4o` call | — (LLM cost only) |
| G2 | `:227` (step-3 `done`, post-`current_spec` finalisation incl. any step-4 auto-fix) | the LLM-corrected spec produced at `:196` | the retry `POST` at `:205` / the wiring POST at `:251` |
| G3 | `:262` / before `:269` | the BERelation shape (`MANYTOONE`, FK mapping, parent URI) | `POST berelation` at `:277` |
| G4 | `:292` (step-5 `done`) | deploy of the physical table | `POST deployCheckForWarnings` `:299` + `POST deployBusinessEntity` `:309` |
| G5 | inside the `if wants_separate_view:` branch, before `:328` | standalone menu view registration | `POST viewResourceMetadatas` `:328` |

**[INFERRED] What has to be built for any of these to work** (deduced from the CONFIRMED transport facts above, not read anywhere):
1. A run id known to the client **before** step 1 — either honour the already-existing-but-unused `RunRequest.run_id` (`backend/models.py:13`) or emit the server-generated one as the *first* SSE frame instead of the last (`backend/routers/client_extensions.py:120` → move the `:203` yield to the top of `event_stream`).
2. A new inbound route (e.g. `POST /api/run/{run_id}/approve`) plus shared in-process state, since `StreamingResponse` gives no upstream channel.
3. The gate itself as an `await` on an `asyncio.Event`/queue keyed by run id, placed at the seams above, preceded by a new SSE event type (e.g. `{"type":"approval_required", ...}`) — the frame builder `_evt()` (`backend/pipeline_embedded.py:44-59`) already tolerates arbitrary `type` values, and the frontend already ignores unknown types (`frontend/src/features/client_ext/ClientExtPanel.tsx:98-134` handles only `complete`/`error`/`run_id`/step), so adding a type is non-breaking on the display path but the UI would need new controls.
4. A timeout/abort story: the frontend aborts via `AbortController` (`frontend/src/features/client_ext/api.ts:74,82`), and a gate that blocks forever would hold an httpx-free but open ASGI connection plus the `5/minute` limiter slot (`backend/routers/client_extensions.py:118`).

**Confirmation for the inferred items would come from** a decision by the commissioner on transport (block-in-generator vs. split the pipeline into resumable phases persisted in SQLite) — nothing in the current code picks either.

### A2.3 Additional findings worth stating plainly

1. **[CONFIRMED]** `deployCheckForWarnings` response is discarded in embedded mode (`backend/pipeline_embedded.py:299`); the standard pipeline does the same (`backend/pipeline.py:739`). Warnings never reach the user.
2. **[CONFIRMED]** `sql_safe` and `DROPDOWN_TYPES` are imported into `backend/builders/embedded_builder.py:5,8` but **never used** in that file (grep returns only the import lines). Consequence: embedded field codes are written raw into `entityFieldCode` / `physicalFieldName` / `fieldURI` (`:84,88,117`), with SQL-reserved-word renaming enforced only as a prompt instruction (`backend/agents/prompts.py:483`).
3. **[CONFIRMED]** Related key-mismatch risk: `build_data_lists` keys `field_list_map` on `sql_safe(f["code"])` (`backend/builders/bc_builder.py:144-146`), while `patch_dropdown_fields` looks the map up by `field["entityFieldCode"]` (`bc_builder.py:107`), which the embedded builder sets to the **raw** `f["code"]` (`backend/builders/embedded_builder.py:84`). **[INFERRED]** For any dropdown field whose code is in `SQL_RESERVED` (`bc_builder.py:8-16`, e.g. `status`), the two keys differ and the dropdown wiring silently no-ops — the field would deploy with an empty `dataListCode`. **Confirmation would require** a run with a dropdown field literally named `status`.
4. **[CONFIRMED]** Step-3 event id is reused by the dropdown-wiring pass, producing `3:done → 3:running → 3:done` (`backend/pipeline_embedded.py:225, 236, 262`).
5. **[CONFIRMED]** `VALIDATOR_AND_CORRECTOR` is shared verbatim with the standard pipeline and contains **no** embedded-specific knowledge (`backend/agents/prompts.py:100-155`): its fixable-error list never mentions the `domaincodeEx` / FK / child-PK constraint that the embedded flow depends on, and unlike the two embedded prompts it has no `{QAD_DOCS_CONTEXT}` placeholder.
6. **[CONFIRMED]** The rate-limit comment on the shared route claims "each run spawns 8 LLM calls" (`backend/routers/client_extensions.py:118`), but an embedded run makes **2** LLM calls (`backend/pipeline_embedded.py:79, 125`), or **3** if step 4 triggers (`:186`). Corroborated by `PROGRESS.md:215` ("3 sites" in `pipeline_embedded.py`).
7. **[CONFIRMED]** `SSEEvent.total` defaults to `14` in the shared model (`backend/models.py:34`), which never matches an embedded run's 7 or 8 — harmless only because the pipeline always sets `total` explicitly (`backend/pipeline_embedded.py:46,109…`).

---

## A3. Case 3 — Server-side (SSS): full step inventory and flow separation

**Scope read in full:** `backend/sss/__init__.py`, `appconfig.py`, `discover.py`, `generate.py`, `compile.py`, `deploy.py`, `readiness.py`, `templates.py`; `backend/routers/sss.py`; `backend/core/sss_scaffold.py`, `ts_compiler.py`, `qad_session.py`, `config.py`, `health.py`, `qad_docs_loader.py`, `auth.py`; `backend/main.py`; `backend/routers/client_extensions.py`, `settings.py`; `backend/pipeline.py` (steps + TS gate regions); `backend/sss_template/*` + `backend/sss_workspace/*` config; `frontend/src/App.tsx`, `features/sss/*`, `shared/components/Header.tsx`.

---

### A3.1 The real ordered step inventory

[CONFIRMED] The commissioner's assumed order (`discover → generate → compile → deploy → scaffold`) is **wrong in two ways**: (a) **scaffold runs FIRST**, at app startup, not last; (b) **compile and deploy are NOT separate steps or separate endpoints** — they are two sequential blocks inside the single `POST /api/sss/deploy` handler.

The actual order is:

| # | Step (real name) | Trigger / endpoint | LLM? |
|---|---|---|---|
| 0 | `scaffold_sss_workspace()` | FastAPI `startup` event (not an endpoint) | no |
| 1 | `readiness()` / `ensure_ready()` | per-request FastAPI dependency | no |
| 2 | `discover_bcs()` / `get_bc()` | `GET /api/sss/bcs`, `GET /api/sss/bcs/{name}` | no |
| 3 | `generate_validation()` (+ `build_sss()`) | `POST /api/sss/generate` | **yes — the only LLM call in SSS** |
| 4 | **HUMAN APPROVAL** (frontend only) | no endpoint — a React render branch | no |
| 5 | `write_ts()` → `compile_app()` → `deploy()` | `POST /api/sss/deploy` (one handler, three calls) | no |
| — | `check_connection()` | `GET /api/sss/connection` (out-of-band, ungated) | no |

There are exactly **5 SSS endpoints** (`backend/routers/sss.py:55,73,83,99,123`). There is **no** `/api/sss/compile`, no `/api/sss/scaffold`, no `/api/sss/status`, no SSE stream. [CONFIRMED — absence verified by reading the whole router file.]

---

#### Step 0 — `scaffold_sss_workspace(app_dir)` — `backend/core/sss_scaffold.py:20`

- **What it does:** idempotently materialises the compile workspace at `QAD_APP_DIR`. Creates `lib/`, `src/`, `dist/` (`sss_scaffold.py:29-32`); copies `package.json`, `tsconfig.json`, `qad-sss.config.json` from `backend/sss_template/` **only if absent** (`sss_scaffold.py:34-39`); copies `lib/*.d.ts` (`:41-47`); installs TypeScript from the bundled `sss_template/node_modules_typescript` copy, else falls back to `npm install` (`:49-93`); then warns if `tsconfig.json`'s `outFile` disagrees with `appconfig.app_script_name()` (`:95-112`). [CONFIRMED]
- **Produces:** a ready `QAD_APP_DIR` tree + `node_modules/typescript` + a hand-written `node_modules/.bin/tsc.cmd` shim (`sss_scaffold.py:58-63`).
- **Entry point:** `backend/main.py:183-192`, inside `@app.on_event("startup")`:
```python
    try:
        from core.sss_scaffold import scaffold_sss_workspace
        from core import config as _cfg
        _app_dir = _cfg.qad_app_dir()
        if _app_dir:
            scaffold_sss_workspace(_app_dir)
    except Exception as exc:
        logger.error("SSS workspace scaffold failed: %s", exc)
```
- **State written:** disk only (`QAD_APP_DIR`). No DB, no in-memory registry.
- **Failure mode:** returns `False` or raises; `main.py:191-192` swallows it into a log line. Startup never fails. The user only learns via `GET /api/health` (`core/health.py:74-139`). [CONFIRMED]
- **[CONFIRMED — DEFECT] The scaffolded `tsc.cmd` shim is broken on Windows.** `sss_scaffold.py:61-63` writes `@"%~dp0\..\typescript\bin\tsc" %*`. `backend/sss_workspace/node_modules/typescript/bin/tsc` is a 45-byte extension-less Node script (`#!/usr/bin/env node` / `require('../lib/tsc.js')`), which `cmd.exe` cannot execute. Verified read-only by invoking the shim with `-v`: output `'"…\.bin\\..\typescript\bin\tsc"' is not recognized as an internal or external command`, exit code non-zero. A real npm-generated `tsc.cmd` wraps the script in `node`; this one does not. Consequence in A3.4/A3.8.

---

#### Step 1 — `readiness()` / `ensure_ready()` — `backend/sss/readiness.py:27,52`

- **What it does:** checks `QAD_APP_DIR` is set, exists, and contains `lib/salesgen.d.ts` (`readiness.py:21` — `PRIMARY_TYPEDEF = "salesgen.d.ts"`).
- **Applied as:** `GATED = [Depends(ensure_ready)]` (`routers/sss.py:38`) on `/bcs` (`:55`), `/bcs/{name}` (`:73`), `/generate` (`:83`), `/deploy` (`:99`). `/connection` is deliberately exempt (`:123`, documented `:8-9`).
- **Failure mode:** structured **HTTP 503** with body `{error:"sss_not_configured", message, missing, action, docs_url}` (`readiness.py:40-49,52-56`). Never a 500/traceback.
- **[CONFIRMED] The `docs_url` is a dead link.** `core/config.py:50` sets `SSS_SETUP_DOCS_URL = "/docs/setup-sss"`; no FastAPI route serves it, and `docs/` contains only `BC_PROMPT_TEMPLATE.md`. The frontend surfaces it as a "Setup Guide" link.
- **[CONFIRMED] Gate asymmetry:** the 503 gate keys on `salesgen.d.ts` alone (`readiness.py:35`), while `core/health.py:101` requires **both** `salesgen.d.ts` and `purchasinggen.d.ts`. Documented as intentional (`readiness.py:19-21`).

---

#### Step 2 — `discover_bcs()` — `backend/sss/discover.py:211`

- **What it does:** parses standard QAD `.d.ts` typedefs into targetable Business Components. See A3.6 for the exact mechanism.
- **Produces:** a sorted list of dicts with keys `name, namespace, module, source, data_type, ds_prop, tt_prop, record_type, fields, methods, with_confirmation` (`discover.py:50-64`).
- **Endpoints:**
  - `GET /api/sss/bcs` → projection `{name, field_count, methods, module}` (`routers/sss.py:55-70`).
  - `GET /api/sss/bcs/{name}` → the full BC dict (`routers/sss.py:73-79`).
- **LLM prompt:** none. Purely deterministic regex parsing.
- **State written:** in-memory only — `discover._cache = {"key":…, "bcs":…}` keyed on `(path, st_mtime)` per file (`discover.py:46,220-231`). Never persisted.
- **Failure mode:** `FileNotFoundError` when no `*gen.d.ts` present (`discover.py:216-218`), caught in the router and downgraded to the same 503 shape (`routers/sss.py:68-70`). Unknown name → **404** (`routers/sss.py:78`).
- **[CONFIRMED] Hard-coded scope:** `STANDARD_SOURCES = [("salesgen","Sales"), ("purchasinggen","Purchasing")]` (`discover.py:31-34`). Custom-app BCs (`lib/customappgen.d.ts`) are deliberately **not** parsed (`discover.py:10-11`) even though the file is present in the workspace (183 KB).

---

#### Step 3 — `generate_validation(bc, prompt)` — `backend/sss/generate.py:175`

- **What it does:** one OpenAI chat-completion call, then a hallucination guard, then deterministic TS assembly.
- **Endpoint:** `POST /api/sss/generate`, rate-limited `@limiter.limit("10/minute")` (`routers/sss.py:83-95`). Request body `GenerateReq{bc_name(≤200), prompt(≤20_000)}` (`routers/sss.py:44-46`, cap at `:20`).
- **LLM prompt (the only one in SSS):** `SYSTEM_PROMPT` at `backend/sss/generate.py:28-70`. Verbatim opening + the load-bearing rules:
```
You are a QAD Enterprise Platform server-side-scripting (SSS) expert who writes record-level validation in TypeScript.
...
3. Report a problem with: this.addValidationError("clear user-facing message");
   You may call it multiple times. Do NOT call throwAddedValidationErrors() - the wrapper does that for you.
4. Write ONLY statements that belong inside the per-record loop. Do NOT write the class, imports, `super.` calls, function signatures, or the for-loop itself.
8. TypeScript target is ES6 (tsc 3.5). Use const/let, ===, template literals. No optional chaining (?.), no nullish coalescing (??).
```
  Required response shape (`generate.py:63-69`): `{"methods":[...], "validation_code":"...", "summary":"...", "fields_used":[...]}`.
  `{QAD_DOCS_CONTEXT}` (`generate.py:36`) is substituted at call time via `str.replace` (not `.format`, because the prompt contains literal JSON braces) with `docs_loader.get_bundle("server_side_rule")` (`generate.py:118-123`). That bundle = folders `Server scripting using TypeScript`, `Setting up a server scripting development environment`, `Platform Scripting - TypeScript`, `TypeScript recommended coding standards` (`core/qad_docs_loader.py:53-58`).
  Call params: `model=appconfig.openai_model()`, `response_format={"type":"json_object"}`, no temperature, client `timeout=90.0, max_retries=4` (`generate.py:86,127-134`). Effective model here is `gpt-5-mini` (`backend/settings.json`).
- **Produces:** `{ts, summary, methods, validation_code, file_name}` where `file_name = f"{bc['name']}.ts"` (`generate.py:186-192`).
- **Guard (this is the real safety net):** `_validate_spec` (`generate.py:154-172`) rejects any hallucinated field:
```python
    referenced = set(re.findall(r"\brec\.(\w+)", code))
    unknown = referenced - valid_fields
    if unknown:
        raise GenerationError(
            "Model referenced unknown field(s): "
            f"{sorted(unknown)}. Valid fields: {sorted(valid_fields)}"
        )
```
- **Deterministic assembly:** `templates.build_sss()` (`backend/sss/templates.py:27`) writes ALL structure — the three `/// <reference>` lines, `namespace {app_ns}.dev`, the subclass `extends {parent_ns}.gen.bc.{name}`, the per-method overrides, the `validateRecords` loop with `this.throwAddedValidationErrors()`, the `{name}Factory`, and both registrations (`templates.py:84-116`). The LLM body is indented 16 spaces into the loop (`templates.py:53-55`). Notably it also expands `createWithConfirmation` / `updateWithConfirmation` overrides when the BC has them (`templates.py:70-79`), with the documented rationale that the QAD Web UI saves through those variants, "Otherwise a deployed rule may silently never fire" (`templates.py:15-17`).
- **State written:** **NONE.** Docstring `routers/sss.py:86`: `"prompt + bc_name -> LLM-generated validation .ts. No disk write, no deploy."` [CONFIRMED — no file write, no DB row, no cache entry.]
- **Failure modes:** unknown BC → 404 (`routers/sss.py:89`); empty prompt → 400 (`:91`); `GenerationError` (no API key / OpenAI failure / non-JSON / empty body / unknown field) → **422** with the message verbatim (`routers/sss.py:94-95`).

---

#### Step 4 — HUMAN APPROVAL (frontend only) — see A3.2

---

#### Step 5 — `POST /api/sss/deploy` — `backend/routers/sss.py:99-119`

This single handler performs three sub-actions. Body: `DeployReq{bc_name(≤200), ts(≤200_000)}` (`routers/sss.py:49-51`, cap `:21`). **No rate limit decorator** (contrast `/generate`).

**5a. `write_ts(bc_name, ts_content)`** — `backend/sss/compile.py:41`
- Writes to `_bc_dir()/f"{bc_name}.ts"` where `_bc_dir()` = `{app_dir}/src/com/extensions/{app_script_name}/dev/bc` (`compile.py:29-38`). On this machine: `backend/sss_workspace/src/com/extensions/customapp/dev/bc/` — the directory exists and is **empty**. [CONFIRMED]

**5b. `compile_app(bc_name)`** — `backend/sss/compile.py:88` — see A3.4.
- `ensure_deps()` runs `npm install` **only if `node_modules` is missing** (`compile.py:67-74`).
- **[CONFIRMED — significant] `_clean_stale_ts()` deletes every other `.ts` under `src/`:**
```python
    for ts_file in src_root.rglob("*.ts"):
        if ts_file.stem != keep_bc:
            ts_file.unlink()
            logger.info("Removed stale TS: %s", ts_file.name)
```
  (`compile.py:82-85`, called `compile.py:95-96`). Combined with `tsconfig.json`'s single `"outFile": "dist/customappdev.js"`, this means **rules do not accumulate**: deploying a rule for `SalesOrderHeaders` deletes any previously deployed `PurchaseOrders.ts` and re-uploads a bundle containing only the newest rule. One live rule at a time per app.
- Failure → `CompileError` → router **rolls the `.ts` back** then returns **422**:
```python
    except sss_compile.CompileError as e:
        sss_compile.reset_bc(req.bc_name)
        raise HTTPException(status_code=422, detail=str(e))
```
  (`routers/sss.py:109-111`; `reset_bc` at `compile.py:125-130`).

**5c. `deploy()`** — `backend/sss/deploy.py:75` — see A3.5. Failure → **502** (`routers/sss.py:116-117`).

- **Success response:** `{"success": True, "compile": {...}, "deploy": {...}}` (`routers/sss.py:119`).
- **State written:** disk (`src/…/{BC}.ts`, `dist/customappdev.{js,js.map,d.ts}`) + the remote QAD app. **No DB row, no run history.** The SSS router never imports `database`; `save_run` is called only from `routers/client_extensions.py:198`. [CONFIRMED — absence]

---

### A3.2 "Server-side is already approval-based" — **CONFIRMED, with an important qualification**

[CONFIRMED] Yes, SSS is approval-based. **But the gate is 100% client-side.** There is no server-side approval state, no approval token, no persisted "pending" record, and nothing on the backend links a `/generate` result to a subsequent `/deploy`.

**Where the gate lives — `frontend/src/features/sss/ReviewDeploy.tsx`.** The gate *is* the render branch at line 63 (`) : gen ? (`): the deploy button exists only when a generation result is in state. The approval control, `ReviewDeploy.tsx:90-100`:
```jsx
          <div className="sss-actions">
            <button className="sss-btn sss-btn-primary" disabled={deploying} onClick={onDeploy}>
              {deploying ? "Compiling & deploying…" : "Approve & Deploy"}
            </button>
            <button className="sss-btn sss-btn-ghost" disabled={deploying} onClick={onRegenerate}>
              Regenerate
            </button>
            <button className="sss-btn sss-btn-ghost" disabled={deploying} onClick={onDiscard}>
              Discard
            </button>
          </div>
```
The pre-approval placeholder states the contract explicitly (`ReviewDeploy.tsx:102-108`): `"The generated TypeScript will appear here for your review before anything is deployed."`

**What the human is shown (four things, all from the `/generate` response):**
1. **Plain-English intent** — `<strong>What this enforces</strong>` + `{gen.summary}` (`ReviewDeploy.tsx:65-69`).
2. **Which save operations are guarded** — `Runs on:` + a badge per method (`ReviewDeploy.tsx:70-76`).
3. **The filename** — `{gen.file_name}` with the label `editable before deploy` (`ReviewDeploy.tsx:79-82`).
4. **The complete generated TypeScript, in an editable `<textarea>`** (`ReviewDeploy.tsx:83-88`):
```jsx
          <textarea
            className="sss-code"
            value={editedTs}
            onChange={(e) => onTsChange(e.target.value)}
            spellCheck={false}
          />
```

**What the human approves:** the **exact TS string that will be compiled and deployed** — including any hand edits. The state wiring in `frontend/src/features/sss/SssPanel.tsx` proves the edited buffer (not the LLM original) is what ships:
```jsx
      const g = await generate(selected, prompt);
      setGen(g);
      setEditedTs(g.ts);          // SssPanel.tsx:71-73
...
      const r = await deploy(selected, editedTs);   // SssPanel.tsx:85
```

**The three-way exit:** Approve & Deploy → `POST /api/sss/deploy`; Regenerate → `onGenerate` again (`SssPanel.tsx:139`); Discard → `setGen(null)` (`SssPanel.tsx:94-97`), which drops the TS and returns to the placeholder. Nothing was written server-side, so Discard needs no server call. [CONFIRMED]

**Mechanism summary for the Phase 2 port — precisely:**
1. Generation endpoint is **read-only and side-effect-free** — no disk write, no DB row (`routers/sss.py:86`). This is what makes Discard free.
2. The full deployable artifact is returned **in the response body** (`ts` field) and held in **client state**, not server state.
3. The deploy endpoint is a **separate POST that requires the artifact to be re-supplied in its body** (`DeployReq.ts`). The human's click is the only thing that supplies it.
4. Approval semantics = "the bytes I send are the bytes you deploy". Human edits are first-class, not an override path.
5. A three-way UI exit: Approve / Regenerate / Discard.

**[CONFIRMED] Caveats a port must not inherit blindly:**
- **The gate is not enforceable server-side.** Any caller can `POST /api/sss/deploy` with arbitrary TS (up to 200 000 chars) and skip `/generate` entirely. There is no approval ID, nonce, or hash binding the two calls.
- **`/api/sss/deploy` is unauthenticated.** `core/auth.py:16-18` states it plainly: *"Existing routes are intentionally NOT protected in this phase — the login page is the only gate today, enforced client-side."* No SSS route uses `Depends(get_current_user)`.
- **The frontend cannot reject bad TS.** The human is the only reviewer between the LLM and a QAD write; the only automated checks are the `rec.X` field guard at generate-time (`generate.py:161-167`) and `tsc` at deploy-time — and the latter is currently broken (A3.4).
- The BC-name field is *not* re-derived from the TS: `deploy(selected, editedTs)` sends the sidebar's `selected` (`SssPanel.tsx:85`), so a human who edits the class name inside the textarea creates a filename/content mismatch that nothing detects.
- `auto_deploy` exists in config (`core/config.py:34,103,176`) and in the settings API (`routers/settings.py:28`) but is **hardcoded `False` and read by nothing except `public_status()`**. It is dead — there is no auto-deploy bypass to worry about. [CONFIRMED — absence]

---

### A3.3 Is SSS a step inside the new-BC pipeline, or a separate flow? — **SEPARATE. Fully.**

[CONFIRMED] Two independent features sharing only config, logging, QAD auth, and the docs loader.

**Backend routing evidence:**
- Distinct routers registered side by side in `backend/main.py:80-94`: `client_extensions_router.router` and `sss_router.router`.
- Prefixes never overlap: SSS is `APIRouter(prefix="/api/sss")` (`routers/sss.py:35`); Client Extensions is `APIRouter()` with explicit `/api/run`, `/api/history*`, `/api/entities` (`routers/client_extensions.py:113,117,216,221,229,238`).
- **`backend/pipeline.py` never imports anything from `sss`.** Its only overlap is `from core.ts_compiler import check_typescript_syntax` (`pipeline.py:14`) — a *shared core utility*, not the SSS compile step. Repo-wide grep for `from sss|import sss` outside the SSS package returns exactly one hit: `main.py:83` (the router import) and `core/sss_scaffold.py:98` (a local `from sss import appconfig` for the outFile sanity check). [CONFIRMED]
- The CE pipeline's step list is closed at 14 and contains **no SSS step**: `TOTAL_STEPS = 14` (`pipeline.py:142`) and `STEP_LABELS` (`pipeline.py:145-160`) run `1 Understanding your requirements` … `14 Deploying Business Component`. Its TS handling is steps 9–11 (`pipeline.py:633,667,681`) and uses an **LLM as the "compiler"** (`pipeline.py:669-673`, `TS_COMPILER` prompt) — not `npm run compile`, not `tsc`, not the SSS deploy endpoint.
- Different QAD auth surfaces: CE uses OAuth2 password-grant Bearer (`core/qad_session.py:43`, `/qad-central/oauth/token`); SSS uses form-login JSESSIONID (`core/qad_session.py:70`, `/qad-central/api/login`). Documented at `qad_session.py:4-8`.

**Frontend routing evidence:**
- `FeatureKey = "client-extensions" | "server-side-rules"` (`shared/components/Header.tsx:9`) driving a `SegmentedToggle` in the header (`Header.tsx:11-14,40-45`).
- `App.tsx:81-91` renders both panes permanently mounted, toggling only CSS `display`; `ClientExtPanel` and `SssPanel` are siblings with no data flow between them.
- The health gate is explicitly one-directional (`App.tsx:62-66`): *"ONLY the SSS pane consults this — the Client Extensions pane is never gated on SSS health."*
- `features/sss/api.ts:1-3`: `"Feature-scoped: nothing here is imported by Client Extensions or the shell."` `const BASE = "/api/sss";`

**Conclusion:** [CONFIRMED] SSS is a peer feature reached by a header toggle, not a pipeline step. The only coupling is `core/ts_compiler.py`, which borrows the SSS workspace's `tsc` binary for the CE pipeline's step-9 syntax gate (`ts_compiler.py:46-56`).

---

### A3.4 The exact `tsc` invocation and version pinning

**Version pinning — the commissioner is CORRECT, and it is pinned in three independent places.** [CONFIRMED]

| Location | Value |
|---|---|
| `backend/sss_template/package.json:12` | `"devDependencies": { "typescript": "3.5" }` |
| `backend/sss_workspace/package.json:12` | `"devDependencies": { "typescript": "3.5" }` (identical file) |
| Installed on disk | `backend/sss_workspace/node_modules/typescript/package.json` → **3.5.3** |
| Bundled template copy | `backend/sss_template/node_modules_typescript/package.json` → **3.5.3** |
| Runtime health check | `core/health.py:133` → `if not version.startswith("3.5")` → WARN `"TypeScript {version} found, but QAD requires 3.5."` |
| Documented rationale | `VERSIONS.md:14` — *"tsc | 3.5.3 (pinned; NOT latest) | QAD's `p2js` runtime is compiled against TypeScript 3.5…"* |

Note the spec is `"3.5"`, not `"3.5.3"` or `"=3.5.3"` — as an npm range that resolves to `3.5.x`, so `npm install` may float the patch. Only the *bundled* copy is byte-pinned. [CONFIRMED]

**The invocation — `backend/sss/compile.py`.** SSS never calls `tsc` directly; it calls npm:
```python
    proc = _run("npm run compile", app_dir)          # compile.py:97
```
`_run` (`compile.py:56-64`):
```python
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        shell=True,  # Windows: resolves npm.cmd / tsc.cmd via PATH
        capture_output=True,
        text=True,
        timeout=600,
    )
```
`npm run compile` resolves to `package.json:16` → **`"compile": "tsc -v && tsc"`**. There are no CLI flags — every option comes from `tsconfig.json`, identical in template and workspace:
```json
  "compilerOptions": {
    "sourceMap": true, "noImplicitAny": false, "removeComments": true,
    "rootDir": "src/", "target": "es6", "noEmitOnError": true,
    "declaration": true, "outFile": "dist/customappdev.js"
  },
  "include": ["src/**/*.ts"], "exclude": ["dist"], "compileOnSave": false
```
`noEmitOnError: true` is the load-bearing setting (called out at `compile.py:7-8`). `outFile: dist/customappdev.js` matches `app_script_name()` = `"customapp"` (`appconfig.py:25-28`, from `QAD_APP_URI = urn:app:com.extensions.customapp` in `backend/settings.json`), so the scaffold's outFile warning (`sss_scaffold.py:104-110`) does not fire here.

**How the exit code is checked — `backend/sss/compile.py:100-103`, verbatim:**
```python
    produced = [p for p in dist_files() if p.exists()]
    if proc.returncode != 0 or len(produced) < 3:
        logger.error("[SSS] compile FAILED (rc=%s, produced=%d)", proc.returncode, len(produced))
        raise CompileError(_clean_tsc_log(log) or "Compilation failed (no diagnostics).")
```
So it is a **double check**: non-zero return code **OR** fewer than 3 emitted artifacts. `dist_files()` (`compile.py:49-53`) demands exactly `dist/customappdev.js`, `dist/customappdev.js.map`, `dist/customappdev.d.ts`. `log` = `stdout + stderr` (`compile.py:98`), scrubbed by `_clean_tsc_log` which drops blank lines, npm's `>` echo lines, and the `Version …` line from `tsc -v` (`compile.py:113-122`).

**[CONFIRMED — DEFECT, high impact] `npm run compile` cannot currently succeed on this machine.** `ensure_deps()` skips `npm install` because `node_modules` exists (`compile.py:69-70`); `npm run` prepends `node_modules/.bin` to PATH, so `tsc` resolves to the broken scaffolded shim (A3.1). Direct read-only invocation of that shim returns a non-zero exit and `is not recognized as an internal or external command`. `dist/` in `sss_workspace` is **empty** and `src/…/dev/bc/` is **empty**, consistent with SSS never having compiled here. `PROGRESS.md:17` independently records SSS end-to-end as *"UNVERIFIED"*. A global `tsc` does exist on PATH (`C:\Users\…\AppData\Roaming\npm\tsc`) but `npm run` gives the local `.bin` precedence, so the fallback is not reached.

**[CONFIRMED — collateral defect] The Client Extensions TS syntax gate silently fails open because of the same shim.** `core/ts_compiler.py:46-56` prefers `{app_dir}/node_modules/.bin/tsc.cmd`, which exists, so `shutil.which("tsc")` is never consulted. Verified read-only:
```
resolved tsc = D:\WEB_AUX\aux_web_version\backend\sss_workspace\node_modules\.bin\tsc.cmd
check_typescript_syntax('class A { let x = ;;; }')  ->  ok = True, diag = ''
```
Deliberately broken TypeScript passes. The mechanism: the shim's stderr contains no `error TS1\d{3}:` match, so `_TS_SYNTAX_ERROR.search` (`ts_compiler.py:42,108`) misses and control falls to `ts_compiler.py:118-119` → `logger.info("[TS] syntax gate passed (rc=%s)")` → `return True, ""`. Note it returns the *clean pass* (`""`), **not** the honest `"…syntax check skipped."` string — so neither the log nor the SSE stream reveals that no checking occurred. `pipeline.py:657-663` therefore lets broken TS through step 9.

---

### A3.5 The deploy call

All in `backend/sss/deploy.py`.

- **URL builder — `_upload_url()` (`deploy.py:36-46`):**
```python
    return (
        f"{base}/qad-central/api/qracore/sss"
        f"?appURI={quote(app_uri, safe='')}"
        f"&filename={quote(filename, safe='')}"
        f"&appSeq=0&fileSeq=3"
    )
```
  `base = config.qad_base_url().rstrip("/")`; `app_uri = appconfig.app_uri()`; `filename = f"{appconfig.app_script_name()}dev"`. Resolved here: `http://qadee.yash.com:81/qad-central/api/qracore/sss?appURI=urn%3Aapp%3Acom.extensions.customapp&filename=customappdev&appSeq=0&fileSeq=3`. `appSeq=0` and `fileSeq=3` are **hardcoded literals**.
- **Method:** `POST` (`deploy.py:62`).
- **Multipart field name: `"files"` — one name, three parts** (`deploy.py:55-60`):
```python
    fields = []
    for p in files:
        ctype = "application/javascript" if p.suffix == ".js" else "application/octet-stream"
        fields.append(("files", (p.name, p.read_bytes(), ctype)))
    enc = MultipartEncoder(fields=fields)
```
  Order and names come from `dist_files()`: `customappdev.js` (`application/javascript`), `customappdev.js.map` (`application/octet-stream`), `customappdev.d.ts` (`application/octet-stream`). Note `.js.map` → `Path.suffix` is `.map`, so it is octet-stream. Comment `deploy.py:55`: *"three parts all named "files", matching the extension exactly."*
- **Headers (`deploy.py:64-70`):** `Content-Type: <MultipartEncoder.content_type>`, `Cookie: JSESSIONID={session_id}`, `Connection: Keep-Alive`, `Accept-Encoding: gzip,deflate`. **No `Authorization` header** — SSS deploy is cookie-auth, not Bearer. Timeout 600 s.
- **Auth + one retry (`deploy.py:81-87`):**
```python
        sid = get_session_cookie()
        resp = _upload(sid)
        if resp.status_code == 401:  # session expired between login and upload
            logger.info("[SSS] upload 401 -> re-authenticating and retrying once")
            sid = get_session_cookie()
            resp = _upload(sid)
```
  `get_session_cookie()` (`core/qad_session.py:70-93`) POSTs JSON `{username,password}` to `/qad-central/api/login` and takes `resp.json()["sessionId"]`.
- **Pre-flight:** missing dist files → `DeployError(f"Compiled files missing - compile must run first: {missing}")` (`deploy.py:51-53`).
- **What is judged as success — `deploy.py:94-105`, verbatim:**
```python
    body = resp.text[:1000]
    if not resp.ok:
        logger.error("[SSS] deploy rejected HTTP %s", resp.status_code)
        raise DeployError(f"QAD rejected the deployment (HTTP {resp.status_code}). {body}")

    logger.info("[SSS] deploy OK (HTTP %s)", resp.status_code)
    return {
        "success": True,
        "status": resp.status_code,
        "response": body,
        "files": [p.name for p in dist_files()],
    }
```
- **[CONFIRMED] Success = `requests.Response.ok` only, i.e. `status_code < 400`.** The response **body is never inspected** — it is truncated to 1000 chars and passed through. A QAD `200 OK` carrying an error payload, or a `302` redirect to a login page, is reported to the user as *"Deployed to QAD"* (`ReviewDeploy.tsx:50-58` renders `deployResult?.deploy?.response || "OK"`). Contrast the CE pipeline, which does parse QAD's body via `is_qad_success(...)` (`pipeline.py:689-692`).
- **Error mapping:** `QadAuthError` → `DeployError` (`deploy.py:88-90`); `requests.RequestException` → `DeployError` (`:91-92`); router turns either into **502** (`routers/sss.py:116-117`).

---

### A3.6 How discover reads the `.d.ts` typedefs, and what it hands the LLM

**Where it looks — `_gen_paths()` (`discover.py:202-208`):** `appconfig.lib_dir()` = `Path(config.qad_app_dir()) / "lib"` (`appconfig.py:36-38`), filtered to the two hardcoded stems in `STANDARD_SOURCES` that actually exist on disk. Resolved here: `backend/sss_workspace/lib/salesgen.d.ts` (712 613 bytes) and `purchasinggen.d.ts` (335 431 bytes). `api.d.ts`, `p2js.d.ts` are referenced by generated TS but never parsed; `basegen.d.ts`, `qracoregen.d.ts`, `customappgen.d.ts` are ignored entirely. [CONFIRMED]

**The parse, exactly (all `discover.py`):**
1. `path.read_text(encoding="utf-8", errors="replace")` — whole file into memory (`:154`).
2. `_split_namespaces` (`:67-84`) finds `declare namespace ([\w.]+)\s*\{` (`_NS_RE`, `:36`) and extracts each body by **manual brace-depth counting**, not regex. Duplicate namespace names are deliberately kept (`:68-69`).
3. Namespaces ending `.gen.dto` are merged into one interface map per namespace (`:157-161`), because standard files repeat the block.
4. For each `.gen.bc` namespace, `_CLASS_RE = re.compile(r"class (\w+) extends BaseBC implements")` (`:41`) finds the public BC class. The literal `BaseBC implements` is the discriminator that excludes the `BaseBCComm` / `_BaseBC` variants in the same block (comment `:39-40`).
5. The DTO root is found from the block's own import: `re.search(rf"import {re.escape(cls)}DTO\s*=\s*([\w.]+)\s*;", body)` (`:173`). No import → BC skipped (`:174-175`).
6. **`_resolve_chain` (`:118-148`) walks the five-hop DTO chain** — this is the core mechanism:
   `<Data>` → `ds<Y>: <Y>DataSet` (`:126`) → `tt<Z>: <Z>Record[]` (`:133`) → `<Z>Record` interface → fields via `_FIELD_RE = ^\s*(\w+)\s*:\s*([\w.<>\[\]]+)\s*;` (`:38`). When several temp-tables exist it prefers the one whose Record name matches the Data name, else the first (`:136-141`). Any broken hop → the BC is silently dropped (`:127,131,135,143,147`).
7. `_parse_methods` (`:108-115`) intersects the class body against `_CRUD = ["initialize","create","update","delete","fetch","exists"]` (`:42`) and separately detects `{m}WithConfirmation(` for `create`/`update` (`_CONFIRMABLE`, `:43`) → `with_confirmation`. Falls back to `["create","update"]` if nothing matched.
8. Results de-duplicated on `(namespace, class)` via `seen` (`:152,169-170,183`), sorted by `name` (`:228`), cached on `(path, mtime)` (`:220-231`).

The resulting DTO access path is documented at `discover.py:15-16`: `dsEntity.<ds_prop>.<tt_prop>[N].<field>` — exactly what `templates.py:99` emits (`const rows = dsEntity.{ds_prop}.{tt_prop} || [];`).

**What is handed to the LLM — `_bc_context(bc)` at `backend/sss/generate.py:97-106`, verbatim:**
```python
def _bc_context(bc: dict) -> str:
    fields = [{"name": f["name"], "type": f["type"]} for f in bc["fields"]]
    ctx = {
        "business_component": bc["name"],
        "record_access": f"rec.<FieldName>  (rec = one row of {bc['tt_prop']})",
        "fields": fields,
        "available_methods": [m for m in bc["methods"] if m in ("create", "update")]
        or ["create", "update"],
    }
    return json.dumps(ctx, indent=2)
```
[CONFIRMED] So the LLM receives a deliberately **narrowed** four-key JSON object: the BC name, a one-line English description of the row-access idiom, a flat `[{name,type}]` field list, and the create/update subset of methods. It is **not** given `namespace`, `ds_prop`, `tt_prop` (except inside the prose string), `record_type`, `data_type`, `source`, or `with_confirmation` — all of those are consumed only by `templates.build_sss()`. The user message wrapping it (`generate.py:110-115`):
```python
        f"Business Component context:\n{_bc_context(bc)}\n\n"
        f"Validation rule requested by the user:\n\"{prompt.strip()}\"\n\n"
        f"Return the strict JSON described in the system prompt."
```
This narrowing is the architectural point stated at `generate.py:5-8`: *"The structural TS is added by templates.build_sss(), so the model cannot break compilation structurally - the worst it can do is reference a bad field, which we guard against here."*

---

### A3.7 Dry-run mode? Read-back of what is deployed?

**Dry-run: NO. None. Anywhere in SSS.** [CONFIRMED — absence verified by repo-wide grep for `dry_run|dryRun|dry-run|DRY_RUN`]
- The only `dry_run` machinery in the codebase belongs to the **Client Extensions lookup feature**: `core/lookup_generator.py:248` (`create_lookup(..., dry_run: bool = True)`) wired from `pipeline.py:74` (`dry_run=True`) and emitted as SSE at `pipeline.py:87`. That is a different feature and never touches SSS.
- `backend/sss/deploy.py` has exactly one network write path and no flag guarding it. `deploy()` (`:75`) always uploads. There is no `if dry_run` equivalent to `lookup_generator.py`'s `if dry_run is not False:` guard.
- The nearest thing to a dry run is `POST /api/sss/generate`, which is genuinely side-effect-free (`routers/sss.py:86`) — but it stops **before** `tsc`, so it cannot tell you whether the approved TS compiles. A "compile without deploying" capability does not exist: `compile_app()` is only ever reached from `deploy_route` (`routers/sss.py:108`), and there is no `/api/sss/compile` endpoint.
- The one non-mutating QAD call is `check_connection()` (`deploy.py:108-114`) behind `GET /api/sss/connection` — a login probe only, no upload.

**Read-back of what is deployed: NO.** [CONFIRMED — absence]
- `qracore/sss` appears in exactly three places in the repo, all in `backend/sss/deploy.py` (`:6`, `:37`, `:42`), and all on the single `requests.post` path. There is no `GET` against it, no download, no list, no diff.
- Post-deploy verification is limited to `resp.status_code < 400` (`deploy.py:95`). The body is not parsed. Nothing re-fetches the uploaded `customappdev.js` to confirm QAD stored it, and nothing hashes the local dist against a server copy.
- There is no local ledger either: no DB row, no `deployed_at`, no record of which BC or which rule text is currently live. Combined with `_clean_stale_ts` (A3.1 step 5b), the **only** way to know what rule is live is to read `src/…/dev/bc/*.ts` on the server's filesystem.
- The UI reports success from the HTTP status alone: `const deployed = deployResult?.success === true;` (`ReviewDeploy.tsx:31`) → renders `🚀 Deployed to QAD` / *"{selected} validation is live"* (`ReviewDeploy.tsx:50-57`).

---

### A3.8 Findings worth carrying into Phase 2

1. [CONFIRMED] The approval mechanism is clean and portable — **but it is presentation-layer only**. Port the UX (side-effect-free generate, artifact in client state, editable pre-deploy buffer, three-way exit) *and* add the server-side binding SSS lacks (approval ID / content hash) plus route auth.
2. [CONFIRMED] `compile` and `deploy` are not separate steps. If Phase 2 wants a "compiles cleanly?" signal before the human approves, that endpoint **does not exist today** and must be built.
3. [CONFIRMED — DEFECT] The scaffolded `tsc.cmd` (`core/sss_scaffold.py:61-63`) is not executable by `cmd.exe`. It breaks SSS compile outright and silently neuters the CE pipeline's step-9 syntax gate (`core/ts_compiler.py`), which returns `(True, "")` for syntactically invalid TypeScript. Verified empirically, read-only.
4. [CONFIRMED] Deploy success is `status_code < 400` with the body discarded (`deploy.py:94-97`) — weaker than the CE pipeline's `is_qad_success()` body inspection.
5. [CONFIRMED] Only one SSS rule can be live at a time (single `outFile` + `_clean_stale_ts`). Any multi-rule Phase 2 design must change both.
6. [CONFIRMED] SSS writes **no** persistent state — no history, no audit trail of who approved what.

---

---

## A4. Every QAD endpoint AUX calls

Scope audited: `backend/` in full (`qad_client.py`, `core/*`, `routers/*`, `sss/*`, `builders/*`, `pipeline.py`, `pipeline_embedded.py`, `main.py`, `qad_entity_registry.py`, `settings.json`, `.env`, `.env.example`, `sss_template/qad-sss.config.json`) plus a negative sweep of `frontend/`. All line numbers verified by reading the files.

**[CONFIRMED] There is exactly ONE HTTP transport layer for the qracore APIs: `backend/qad_client.py`.** Every qracore call goes through `post_qad()` / `get_qad()`, which prefix a caller-supplied `endpoint` string onto `f"{config.qad_base_url()}/qad-central/api/qracore/{endpoint}"` (`backend/qad_client.py:57`, `backend/qad_client.py:65`). Two calls bypass it: the SSS multipart upload (`requests`, `backend/sss/deploy.py:62`) and the health reachability ping (`httpx.get`, `backend/core/health.py:170`).

### A4.1 Endpoint table

`{BASE}` = `config.qad_base_url()` (from `QAD_BASE_URL`, host:port only — `backend/.env.example:6-8`). All 15 rows are [CONFIRMED] — each read at the cited line.

| # | Method | Path (exact, with {placeholders}) | Query params | Request payload shape (top-level keys) | Response shape (top-level keys / what is read out of it) | Which step/case uses it | Source cite (file:line) |
|---|---|---|---|---|---|---|---|
| 1 | POST | `{BASE}/qad-central/oauth/token` | `client_id`, `username`, `password`, `grant_type=password` — **built into the URL f-string, not urlencoded** | none (no body) | `access_token` (read as `resp.json()["access_token"]`) | Auth. Called freshly before EVERY QAD write in both pipelines | `backend/qad_client.py:42-53`; URL f-string `backend/qad_client.py:44-49`; `resp = await client.post(url)` `:51` |
| 2 | POST | `{BASE}/qad-central/oauth/token` | same four, passed as `params={...}` dict (properly encoded) | none | `access_token` via `.get("access_token")`; raises `QadAuthError` if absent | **DEAD — defined, never called** (see A4.5) | `backend/core/qad_session.py:28`, `:43-67`; params `:46-51`; post `:54`; read `:56` |
| 3 | POST | `{BASE}/qad-central/api/login` | none | JSON `{username, password}`; header `Content-Type: application/json;charset=UTF-8` | `sessionId` via `.get("sessionId")` → used as `JSESSIONID` cookie | Auth (server-side rules / SSS case). Called by SSS deploy + connection test | `backend/core/qad_session.py:29`, `:70-93`; payload `:73`; post `:76-80`; read `:82` |
| 4 | POST | `{BASE}/qad-central/api/qracore/entitymetadatas` | `viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` (urn **not** encoded) | new-BC: `activityTrackingInfos`, `entityMetadatas`, `entityDeployments`. embedded: `activityTrackingInfos`, `entityDeployments`, `entityMetadatas`, `lookupBERelations`, `relatedLookups`, `viewResourceInfos` | `submitResult.success` / `.errorSeverity` / `.errors` (via `is_qad_success`); on failure `submitResult.errors[].message` + `.fieldName` | **STEP 3** "Creating Business Component in QAD" (new-BC) and its post-auto-fix retry; **STEP 3** "Creating Business Component metadata" (embedded) + retry | `backend/pipeline.py:435-438`, retry `:476-479`; `backend/pipeline_embedded.py:167-170`, retry `:205-208`; payloads `backend/builders/bc_builder.py:228-278`, `backend/builders/embedded_builder.py:224-231` |
| 5 | GET | `{BASE}/qad-central/api/qracore/entitymetadatas` | `entityURI={urllib.parse.quote(entity_uri, safe="")}` **&** `viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` | none | `data` (unwrapped: `get_response.get("data")` if dict else the response itself), then `entityMetadatas` must be non-empty or the step hard-fails | **STEP 3.5** "Wiring dropdown fields to data lists" — only when `bc_data["field_list_map"]` is non-empty. Both cases | `backend/pipeline.py:513`, `:516-522`; `backend/pipeline_embedded.py:238`, `:240-245` |
| 6 | POST | `{BASE}/qad-central/api/qracore/entitymetadatas` | `entityURI={quoted}` **&** `viewUri=urn:be:...IEntityBuilderCRUD` | the **unwrapped GET body from row 5, mutated in place** — top-level `entityMetadatas`; `entityMetadatas[].entityFields[].dataListCode` and `.defaultValue` set by `patch_dropdown_fields` | `submitResult.success/.errors` | **STEP 3.5** second-pass dropdown update. Both cases | `backend/pipeline.py:527`, `:529-532`; `backend/pipeline_embedded.py:250-254`; patcher `backend/builders/bc_builder.py:98-111` |
| 7 | POST | `{BASE}/qad-central/api/qracore/viewMetadataV2` | none | `viewMetadatas` (single element: `viewURI`, `platformName`, `viewName`, `moduleURI`, `parentURI`, `moduleName`, `dataOperation`, `entityURI`, `isEligibleForMenu`, `viewMetadata`, `disallowedActions`, `disallowedActionsMessage`, `viewMetadataAdjusted`, `labelFontFactor`, `defaultLabelWidth`) | `submitResult.errors` | **STEP 7** "Saving form design to QAD" — new-BC ONLY | `backend/pipeline.py:597`; payload `backend/builders/form_builder.py:214-236` |
| 8 | POST | `{BASE}/qad-central/api/qracore/eventhandler` | none | `supplementaryMessages`, `eventHandlerV2s` (`appURI`, `viewURI`, `eventHandlerType:"BEFORE"`, `appliesTo:"WEB"`, `isActive`, `typeScriptCode`, `javaScriptCode`, `mappingCode`) | `submitResult.errors` | **STEP 11** "Registering event handlers in QAD" — new-BC ONLY | `backend/pipeline.py:685`; payload `backend/builders/event_handler_builder.py:25-37` |
| 9 | POST | `{BASE}/qad-central/api/qracore/viewResourceMetadatas` | `viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` | `viewResourceMetadatas` (single element: `isEligibleForMenu`, `isSecure`, `isUseBEBrowse`, `browseView`, `maintView`, `hybridBrowseView`, `entityViewParameters`, `moduleUri`, `app`, `appURI`, `isEntityVirtual`, `canUseBEBrowse`, `isShowCriteriaInSearch`, `sortingRestrictedTable`, `isBrowseNotExtensibleBC`, `metaURI`, `viewURI`, `primarySecureURI`, `entityURI`, `browseURI`, `typeField`, `mobileCompatibility`, `entityDescription`, `nameStringCode`, `bcBrowseSearchCondition`, `initialBrowseURI`) | `submitResult.errors` | **STEP 13** "Registering view in QAD" (new-BC); **STEP 8** "Registering standalone view in QAD menu" (embedded, only when `wants_separate_view`) | `backend/pipeline.py:709-712`; `backend/pipeline_embedded.py:328-331`; payload `backend/builders/view_builder.py:104-168` |
| 10 | POST | `{BASE}/qad-central/api/qracore/berelation` | `viewUri=urn:be:com.qad.qra.berelation.IBERelation` | `supplementaryMessages`, `BERelations` (`BERelationFields`, `BERelationFilterConditions`, `cardinality:"MANYTOONE"`, `isCascadeDelete`, `isCascadeDeleteForBD`, `isDrill`, `isEmbedded`, `isExtension`, `isIncludeOnParent`, `isLookup`, `isParent`, `isUseInBusinessDocument`, `isVisualizedAsDropDown`, `moduleURI`, `relatedEntityCode`, `relatedEntityURI`, `relationCode`, `relationID`, `relationLabel`, `relationType`, `sourceAppName`, `sourceEntityCode`, `sourceEntityURI`, `uri`) | `submitResult.errors` | **STEP 5** "Building relations to parent entity" — embedded ONLY | `backend/pipeline_embedded.py:277-280`; payload `backend/builders/embedded_builder.py:280-321` |
| 11 | POST | `{BASE}/qad-central/api/qracore/deployCheckForWarnings` | none | `entityURI`, `isInitialDataLoaded` | **response is DISCARDED — not assigned, not checked** (`await post_qad(...)` with no variable) | **STEP 14** "Deploying Business Component" step-4a (new-BC); **STEP 6** "Checking deployment warnings" (embedded) | `backend/pipeline.py:739`; `backend/pipeline_embedded.py:299`; payloads `backend/builders/deploy_builder.py:13-16`, `backend/builders/embedded_builder.py:330-333` |
| 12 | POST | `{BASE}/qad-central/api/qracore/deployBusinessEntity` | none | `entityURI`, `appURI`, `dataStoreURI`, `isInitialDataLoaded`, `allowActivityTracking` | `submitResult.success/.errors` | **STEP 14** step-4b (new-BC); **STEP 7** "Deploying Business Entity" (embedded) | `backend/pipeline.py:741`; `backend/pipeline_embedded.py:309`; payloads `backend/builders/deploy_builder.py:17-23`, `backend/builders/embedded_builder.py:334-340` |
| 13 | POST | `{BASE}/qad-central/api/qracore/lookups` | `viewUri=urn:be:com.qad.qra.lookup.ILookup` | `lookups` (each: `appName`, `browseName`, `browseURI`, `fieldLabel`, `fieldSet`, `moduleURI`, `namespace`, `reference`, `resultField`, `searchField`, `searchFieldOperator`, `lookupQualifiers`, `lookupResultFields`, `lookupSearchConditions`). `_`-prefixed keys stripped before POST | logged in full at INFO; not otherwise parsed | Phase-11 lookup step, between STEP 13 and STEP 14 — **but gated: `dry_run=True` is hardcoded at the only call site, so this POST is NEVER reached** | endpoint const `backend/core/lookup_generator.py:70`; POST `:280`; strip `:241-244`; guard `:266`; call site `backend/pipeline.py:74` |
| 14 | POST | `{BASE}/qad-central/api/qracore/sss` | `appURI={quote(app_uri)}`, `filename={quote(app_script_name()+"dev")}`, `appSeq=0`, `fileSeq=3` | **multipart/form-data**, three parts ALL named `files` (dev.js, dev.js.map, dev.d.ts); headers `Content-Type` (encoder), `Cookie: JSESSIONID={sid}`, `Connection: Keep-Alive`, `Accept-Encoding: gzip,deflate`; `timeout=600` | `resp.status_code`, `resp.ok`, `resp.text[:1000]` — no JSON parsing at all | Server-side rules case: `POST /api/sss/deploy` step 2 | `backend/sss/deploy.py:36-46` (URL), `:49-72` (upload), `:57-60` (parts), `:62-72`; route `backend/routers/sss.py:99-119` |
| 15 | GET | `{BASE}` (bare base URL, no path) | none | none | `resp.status_code` only (`<500` → ok, `>=500` → warn) | Startup self-check / `GET /api/health`. Explicitly NOT a login, no creds | `backend/core/health.py:162-177`, call `:170` |

### A4.2 Grouped by case (feeds the phase-segregated settings registry)

**auth (shared)**
- Row 1 — `POST /qad-central/oauth/token` (Bearer, used by everything qracore) — `backend/qad_client.py:42`
- Row 2 — `POST /qad-central/oauth/token` (duplicate, dead) — `backend/core/qad_session.py:43`
- Row 3 — `POST /qad-central/api/login` (JSESSIONID, SSS only) — `backend/core/qad_session.py:70`

**shared / both BC cases** (identical endpoint literal appears in both pipelines)
- Rows 4, 5, 6 — `entitymetadatas` create + GET-enrich + update
- Row 9 — `viewResourceMetadatas`
- Rows 11, 12 — `deployCheckForWarnings`, `deployBusinessEntity`

**new-BC only** (`backend/pipeline.py`, 14 steps, `TOTAL_STEPS = 14` at `backend/pipeline.py:142`)
- Row 7 — `viewMetadataV2` (STEP 7)
- Row 8 — `eventhandler` (STEP 11)
- Row 13 — `lookups` (dry-run gated)

**embedded only** (`backend/pipeline_embedded.py`, `BASE_TOTAL_STEPS = 7` at `:30`, 8 when `wants_separate_view`)
- Row 10 — `berelation` (STEP 5)

**server-side (SSS)**
- Row 14 — `qracore/sss` multipart upload
- Row 3 is its auth; `check_connection()` (`backend/sss/deploy.py:108-114`) hits row 3 alone and is exposed at `GET /api/sss/connection` (`backend/routers/sss.py:123-135`)

**health / infra**
- Row 15 — bare-base GET

[CONFIRMED] **No QAD endpoint is called from `backend/routers/*`, `backend/builders/*`, `backend/main.py`, or `backend/agents/prompts.py`.** Routers delegate; builders are pure payload constructors (verified: `grep requests|httpx|urlopen|http` over `sss/compile.py`, `sss/generate.py`, `sss/templates.py`, `sss/readiness.py`, `core/qad_docs_loader.py`, `core/ts_compiler.py`, `core/auth.py` returns **zero** matches).

[CONFIRMED] **The frontend contains no QAD literals.** `grep "qad-central|oauth/token|urn:be:|qracore"` over `frontend/src/` and `frontend/index.html` returns nothing; the only `https://` hits in `frontend/` are npm-registry URLs in `package-lock.json`. The browser talks only to the AUX backend.

### A4.3 Hardcoded literals NOT read from config — the Phase 1 work-list

**(a) URL / path literals**

| file:line | literal | built by |
|---|---|---|
| `backend/qad_client.py:44` | `/qad-central/oauth/token` | f-string |
| `backend/qad_client.py:45-48` | `?client_id=…&username=…&password=…&grant_type=password` | f-string (creds concatenated into URL, **unencoded**) |
| `backend/qad_client.py:57` | `/qad-central/api/qracore/{endpoint}` | f-string |
| `backend/qad_client.py:65` | `/qad-central/api/qracore/{endpoint}` | f-string |
| `backend/core/qad_session.py:28` | `OAUTH_PATH = "/qad-central/oauth/token"` | **constant** |
| `backend/core/qad_session.py:29` | `LOGIN_PATH = "/qad-central/api/login"` | **constant** |
| `backend/sss/deploy.py:42` | `/qad-central/api/qracore/sss` | f-string |
| `backend/sss/deploy.py:43-45` | `?appURI=…&filename=…&appSeq=0&fileSeq=3` | f-string; `appSeq=0&fileSeq=3` are hardcoded magic numbers |
| `backend/pipeline.py:436` | `entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` | plain literal |
| `backend/pipeline.py:477` | same literal (duplicated for the retry) | plain literal |
| `backend/pipeline.py:517` | `entitymetadatas?entityURI={entity_uri_q}&viewUri=urn:be:…IEntityBuilderCRUD` | f-string |
| `backend/pipeline.py:530` | same as `:517` (duplicated) | f-string |
| `backend/pipeline.py:597` | `viewMetadataV2` | plain literal |
| `backend/pipeline.py:685` | `eventhandler` | plain literal |
| `backend/pipeline.py:710` | `viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` | plain literal |
| `backend/pipeline.py:739` | `deployCheckForWarnings` | plain literal |
| `backend/pipeline.py:741` | `deployBusinessEntity` | plain literal |
| `backend/pipeline_embedded.py:168` | `entitymetadatas?viewUri=urn:be:…IEntityBuilderCRUD` | plain literal |
| `backend/pipeline_embedded.py:206` | same (retry duplicate) | plain literal |
| `backend/pipeline_embedded.py:241` | `entitymetadatas?entityURI={entity_uri_q}&viewUri=…` | f-string |
| `backend/pipeline_embedded.py:252` | same as `:241` | f-string |
| `backend/pipeline_embedded.py:278` | `berelation?viewUri=urn:be:com.qad.qra.berelation.IBERelation` | plain literal |
| `backend/pipeline_embedded.py:299` | `deployCheckForWarnings` | plain literal |
| `backend/pipeline_embedded.py:309` | `deployBusinessEntity` | plain literal |
| `backend/pipeline_embedded.py:329` | `viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` | plain literal |
| `backend/core/lookup_generator.py:70` | `LOOKUP_ENDPOINT = "lookups?viewUri=urn:be:com.qad.qra.lookup.ILookup"` | **constant** |
| `backend/sss_template/qad-sss.config.json:2` | `"envUrl": "http://qadee.yash.com:22010/qad-central/"` | **a real hostname + port committed to the repo**, copied into every scaffolded workspace (`backend/core/sss_scaffold.py:34-38`) |
| `backend/core/config.py:50` | `SSS_SETUP_DOCS_URL = "/docs/setup-sss"` | constant (AUX-internal route, not QAD) |
| `backend/main.py:68` | `"http://localhost:5173"` CORS default | literal fallback for `ALLOWED_ORIGINS` |
| `backend/.env.example:37` | `ALLOWED_ORIGINS=http://localhost:5173` | example value |
| `backend/agents/prompts.py:362` | `api/TODO/provide-endpoint` | **not an endpoint** — a deliberate placeholder inside the TS-writer prompt's "comment this out" template (`backend/agents/prompts.py:354-366`) |

**(b) URN / identity literals** (all `com.extensions.customapp`-family; none read from `qad_app_uri()` even though that config key exists)

- Module constants: `backend/builders/bc_builder.py:4-6`, `backend/builders/deploy_builder.py:3-4`, `backend/builders/embedded_builder.py:13`, `backend/builders/event_handler_builder.py:3`, `backend/builders/form_builder.py:3-4`, `backend/builders/view_builder.py:4-6`
- `bc_builder.py`: `:165` `urn:be:{MODULE}.{bc}.I{bc}`, `:166` `urn:app:{MODULE}`, `:167` `urn:bd:{MODULE}.{bc}.{bc}`, `:168` `urn:bd:{MODULE}.{bc}.I{bc}`, `:217` `urn:field:{MODULE}.{bc}.I{bc}:{bc}.{safe}`, `:231` `"urn:be:com.qad.qra.metadatav3.IEntityDeployment:"` (bare literal with trailing colon)
- `deploy_builder.py:4` `urn:datastore:com.extensions.extension`; `:8`, `:9`
- `embedded_builder.py`: `:48`, `:88`, `:124` (percent-escaped `com%2Eextensions%2Ecustomapp` inline), `:131`, `:134`, `:164`, `:173`, `:198`, `:208`, `:218`, `:309`, `:318`, `:319`, `:327`, `:336`, `:337` (`urn:datastore:com.extensions.extension` re-hardcoded, diverging from `deploy_builder.DATASTORE_URI`)
- `view_builder.py`: `:53`, `:56`, `:110`, `:137`, `:138`, `:143` (`"appModuleName": "qracore"`), `:144` (`f"be/{entity_uri}"`), `:156`, `:157`, `:160`, `:166`
- `form_builder.py`: `:125`, `:126`, `:127`
- `event_handler_builder.py`: `:7`, `:8`
- `qad_entity_registry.py` parent-entity URIs: `:41` `urn:be:com.qad.sales.salesorder.ISalesOrderHeader`, `:50` `urn:be:com.qad.purchasing.purchaseorders.IPurchaseOrderHeader`, `:59` `urn:be:com.qad.base.item.IItem`, `:67` `urn:be:com.qad.inventory.inv.IInventoryMaster`, `:76` `urn:be:com.qad.pushproduction.workorder.IWorkOrderMaster`
- `pipeline.py:42` `"module_uri": "urn:app:com.extensions.customapp"`, `:770` `"module": "com.extensions.customapp"`, `:787` `f"urn:be:com.extensions.customapp.{bc_pascal}.I{bc_pascal}"`; also `:39-40` `"namespace": "com.extensions"` / `"app": "customapp"` and `:43` `"app_name": "CustomApp"`
- `main.py:149` `f"urn:be:{module}.{bc}.I{bc}"` with fallback literal `"com.extensions.customapp"` at `:146`
- `backend/settings.json:3` `"qad_app_uri": "urn:app:com.extensions.customapp"`; `backend/.env.example:20` same; `backend/sss_template/qad-sss.config.json:4` same

### A4.4 Constants vs string-built

- **Named constants (3 only):** `OAUTH_PATH`, `LOGIN_PATH` (`backend/core/qad_session.py:28-29`) and `LOOKUP_ENDPOINT` (`backend/core/lookup_generator.py:70`). Two of the three belong to code paths that never execute (A4.5).
- **Everything actually on the hot path is a plain inline literal or f-string** at the call site, duplicated per call: the `entitymetadatas?viewUri=…IEntityBuilderCRUD` string appears **6 times** across two files (`pipeline.py:436`, `:477`, `:517`, `:530`; `pipeline_embedded.py:168`, `:206`, `:241`, `:252` — 8 occurrences counting the `entityURI` variants), and `viewResourceMetadatas?viewUri=…` appears twice (`pipeline.py:710`, `pipeline_embedded.py:329`).
- **f-string paths:** `qad_client.py:44-49`, `:57`, `:65`; `sss/deploy.py:42-46`; `pipeline.py:517`, `:530`; `pipeline_embedded.py:241`, `:252`.
- **Encoding is inconsistent within a single URL:** `entityURI` is `urllib.parse.quote(..., safe="")`-encoded (`pipeline.py:513`, `pipeline_embedded.py:238`) while the `viewUri` urn in the same query string is left raw (colons unencoded). SSS encodes both its params (`sss/deploy.py:43-44`). OAuth in `qad_client.py:45-48` encodes nothing — a password containing `&` or `#` would corrupt the request. [INFERRED] that this is a latent bug rather than intent; confirming it needs a credential with a reserved character, which I did not test (read-only audit).

### A4.5 Defined but never called

1. **[CONFIRMED] `core.qad_session.get_bearer_token()` is dead code.** `backend/core/qad_session.py:43-67`. A repo-wide grep for `get_bearer_token` returns only the definition (`:43`) and its own docstring mention (`:6`). Consequently `OAUTH_PATH` (`:28`) is dead too. The live Bearer path is `qad_client.get_token()` (`backend/qad_client.py:42`), called at `backend/pipeline.py:434, 475, 514, 596, 684, 708, 737`, `backend/pipeline_embedded.py:166, 204, 239, 276, 298, 308, 327`, `backend/core/lookup_generator.py:279`. The file's own docstring at `backend/core/qad_session.py:4-8` claims it is "the single place both features authenticate to QAD" — **that claim is false today**; only the SSS half (`get_session_cookie`) is wired. `backend/qad_client.py:4-7` names this pending migration explicitly ("the deferred qad_client -> core.qad_session auth-flow migration is separate").
2. **[CONFIRMED] Row 13 (`qracore/lookups`) is never POSTed.** The only caller passes `dry_run=True` (`backend/pipeline.py:74`) and the guard is `if dry_run is not False:` (`backend/core/lookup_generator.py:266`), so the live branch at `:276-282` is unreachable from the app.
3. **[CONFIRMED] `qad_client._safe_body()` is dead** — `backend/qad_client.py:11-17`; grep finds only the definition.
4. **[CONFIRMED] `envUrl` in `backend/sss_template/qad-sss.config.json:2` is never read by Python** — grep for `envUrl` matches only that line. The file is copied verbatim into the workspace by `backend/core/sss_scaffold.py:34-38`; only `outFile` in `tsconfig.json` is inspected (`:96-110`).

### A4.6 `urn:` patterns used for entity identity

- **`urn:be:{module}.{Bc}.I{Bc}`** — the primary entity identity. Used as `entityURI`, `secureResourceURI`, `primarySecureURI`, and as the `entityURI` query param on rows 5/6. `backend/builders/bc_builder.py:165`, `backend/builders/embedded_builder.py:48`, `backend/builders/deploy_builder.py:8`, `backend/builders/view_builder.py:56`, `backend/builders/form_builder.py:125`, `backend/pipeline.py:787`, `backend/main.py:149`
- **`urn:app:{module}`** — `moduleURI` / `appURI`. `backend/builders/bc_builder.py:166`, `backend/builders/embedded_builder.py:134`
- **`urn:bd:{module}.{Bc}.{Bc}` / `urn:bd:{module}.{Bc}.I{Bc}`** — `bdocumentURI` / `cachedBdocumentURI`. `backend/builders/bc_builder.py:167-168`
- **`urn:field:{module}.{Bc}.I{Bc}:{table}.{field}`** — field identity; also the `fieldSet` rule for lookups. `backend/builders/bc_builder.py:217`, `backend/builders/embedded_builder.py:88`, `backend/core/lookup_generator.py:143-145`
- **`urn:be:com.qad.qra.metadatav3.IEntityDeployment:<percent-escaped inner urn>`** — deployment identity. `backend/builders/embedded_builder.py:124`, `:131`, `:157`; bare-colon variant `backend/builders/bc_builder.py:231`
- **`urn:be:com.qad.qra.berelation.IBERelation:{relation_id}`** — relation identity, `relation_id` = fixed prefix `8c9676c6-0c12-13a3-f114-` + 12 hex chars of a fresh uuid4 (`backend/builders/embedded_builder.py:278`, `:319`)
- **`urn:datastore:com.extensions.extension`** — `dataStoreURI` on deploy. `backend/builders/deploy_builder.py:4`, `backend/builders/embedded_builder.py:337`
- **`urn:browse:bebrowse:{module}.{bc_lower}`**, **`urn:view:browse|maint|meta|hybridbrowse|viewmeta:{module}.{bc_lower}`** — view/browse identities. `backend/builders/view_builder.py:110, 137, 138, 156, 157, 160, 166`; `backend/builders/form_builder.py:127`; `backend/builders/event_handler_builder.py:8`
- **`viewUri=` urns in query strings** (the API-surface selector, not entity identity): `…adapter.entity.IEntityBuilderCRUD`, `…qra.meta.IViewResourceMetadata`, `…qra.berelation.IBERelation`, `…qra.lookup.ILookup`
- **Parent-entity identity for embedded BCs:** the 5 `urn:be:com.qad.*` values in `backend/qad_entity_registry.py:41, 50, 59, 67, 76`, consumed as `entity_info["uri"]` → `relatedEntityURI` (`backend/pipeline_embedded.py:273`, `backend/builders/embedded_builder.py:311`)

### A4.7 Retry / 401-refresh / error handling

**Token handling — [CONFIRMED] there is no token cache and no 401 refresh on the qracore path.** `get_token()` is re-called immediately before every single write (7 sites in `pipeline.py`, 7 in `pipeline_embedded.py`, 1 in `lookup_generator.py`). A 401 mid-run is therefore not refreshed — it falls through `_handle()` as `{"error": "QAD HTTP 401", "raw": …}` and the step reports a failure. `get_token()` itself calls `resp.raise_for_status()` (`backend/qad_client.py:52`) so an auth failure raises `httpx.HTTPStatusError`, caught by the enclosing `try` and surfaced as e.g. `"QAD connection failed: {e}"` (`backend/pipeline.py:440`) — a **raw exception string reaching the user**, unlike the SSS path which maps to plain English.

**Response normalisation — `_handle()` (`backend/qad_client.py:20-39`).** `raise_for_status()` → on `HTTPStatusError` returns `{"error": f"QAD HTTP {status}", "raw": text[:500]}`; on non-JSON body returns `{"error": "QAD returned a non-JSON response", "raw": …}`. So `post_qad`/`get_qad` never raise for HTTP status — failures are dict envelopes.

**Success gate — `is_qad_success()` (`backend/qad_client.py:72-82`).** Requires `submitResult.success is True` **and** `errorSeverity == 0` (default `1` if absent) **and** falsy `errors`. The envelope check at `:75-76` (`"error" in result and "submitResult" not in result → False`) prevents an HTTP-error envelope being read as silent success.

**Retries:**
- **One LLM auto-fix retry on the BC-create call only.** New-BC: failure → STEP 4 `VALIDATOR_AND_CORRECTOR` → if `status == "fixed"`, re-POST row 4 once (`backend/pipeline.py:457-497`). A second failure ends the run (`:488-490`). Embedded: same shape at `backend/pipeline_embedded.py:176-221`.
- **Duplicate-name short-circuit (new-BC only).** `_is_duplicate_entity_error()` (`backend/pipeline.py:226-231`) matches `"already exist"` in the joined error messages and skips the auto-fix entirely, emitting rename guidance (`:447-455`). It is re-checked after the fix to append a rename hint (`:484-487`). **[CONFIRMED] `pipeline_embedded.py` has no equivalent** — an embedded duplicate burns an LLM call plus a second round-trip.
- **SSS 401-retry — the only true auth retry in the codebase.** `backend/sss/deploy.py:82-87`: `get_session_cookie()` → upload → `if resp.status_code == 401` re-login and upload **exactly once**.
- **No other retries.** No backoff, no idempotency keys, no circuit breaker anywhere.

**Unchecked responses:** row 11 (`deployCheckForWarnings`) is awaited and discarded in both pipelines (`backend/pipeline.py:739`, `backend/pipeline_embedded.py:299`) — a warnings failure is invisible. Row 6's result IS checked (`backend/pipeline.py:536-539`).

**Timeouts:** `get_token` 30s (`backend/qad_client.py:50`); `post_qad`/`get_qad` 60s (`:59`, `:67`); `get_bearer_token` 30s default, `get_session_cookie` 60s default (`backend/core/qad_session.py:43`, `:70`); SSS upload 600s (`backend/sss/deploy.py:71`); health ping 5s (`backend/core/health.py:162`).

**Error-message quality:** the SSS/session path converts every exception into a user-facing `QadAuthError` with plain English and logs via `log_operation` (`backend/core/qad_session.py:61-67`, `:87-93`); `DeployError` wraps `requests.RequestException` (`backend/sss/deploy.py:91-92`). The qracore path instead interpolates raw `{e}` / `json.dumps(err)` into SSE error events (e.g. `backend/pipeline.py:440`, `:603`, `:691`, `:718`, `:747`), except where `_qad_error_messages()` is used — and that helper is applied at exactly **one** site (`backend/pipeline.py:481`).

### A4.8 Config keys and shapes

`backend/.env` keys present (values `<redacted>`): `OPENAI_API_KEY`, `QAD_BASE_URL`, `QAD_USERNAME`, `QAD_PASSWORD`, `QAD_CLIENT_ID`, `ALLOWED_ORIGINS`, `QAD_DOCS_DIR`, `QAD_APP_DIR`, `APEX_ADMIN_EMAIL`, `APEX_ADMIN_PASSWORD`, `APEX_JWT_SECRET`.

[CONFIRMED] **`QAD_APP_URI` and `OPENAI_MODEL` are absent from `backend/.env`** even though `.env.example:20` and `:32` document them. `qad_app_uri` therefore resolves via the `settings.json` override branch (`backend/core/config.py:34`, `:106-109`) from `backend/settings.json:3` = `urn:app:com.extensions.customapp`. `backend/settings.json` full contents: `qad_app_dir: ""`, `qad_app_uri`, `openai_model: "gpt-5-mini"` — no endpoint/URL keys, no secrets.

Endpoint-relevant config surface, and what it does NOT cover:
- `QAD_BASE_URL` → `config.qad_base_url()` — host:port only; `/qad-central` is appended in code (`.env.example:6-7`). **The only endpoint component that is configurable.**
- `QAD_APP_URI` → consumed ONLY by the SSS upload's `appURI` query param (`backend/sss/appconfig.py:15-17` → `backend/sss/deploy.py:39`) and to derive `filename` (`backend/sss/appconfig.py:25-28`). **The BC builders ignore it entirely and use their own `MODULE` constants** — so `urn:app:com.extensions.customapp` is configurable for SSS and hardcoded for Client Extensions.
- `_UI_KEYS = ("qad_base_url", "qad_app_uri", "openai_model", "auto_deploy")` (`backend/core/config.py:34`) — the settings.json override allow-list; contains no endpoint paths.
- Legacy settings.json fallbacks honoured only when `.env` is blank: `qad_server_url`, `qad_client_id`, `qad_username`, `qad_password` (`backend/core/config.py:113-121`). **This is a credential-in-plaintext-JSON path** — `save_ui_settings` won't write them (`:185-197`) but `_merged()` will read them.
- `public_status()` (`backend/core/config.py:164-182`) returns `qad_base_url`, `qad_username`, `qad_app_uri`, `qad_app_dir` in the clear plus `has_openai_key`/`has_qad_password` booleans — no password, no client_id, no JWT secret.

---

I have everything needed.

## A5. Auth flow as implemented

Two completely separate auth systems exist. They share nothing but the `core.config` module.

| | APP-LEVEL (APEX login) | QAD-ENVIRONMENT |
|---|---|---|
| Credential source | `.env` (`APEX_ADMIN_EMAIL`/`APEX_ADMIN_PASSWORD`) compared against UI login form | `.env` / `settings.json` only — never the UI |
| Mechanism | HS256 JWT, 8h TTL | OAuth2 password grant (Bearer) **and** form login (JSESSIONID) |
| Storage | browser `localStorage["apex_token"]` | nothing persisted; re-fetched per call |
| Protects | nothing server-side except `GET /api/auth/me` | all QAD writes |

---

### 1. TOKEN ACQUISITION

**1a. QAD Bearer token — the path actually used by the pipeline** is `qad_client.get_token()`, **not** `core/qad_session.py`.

`backend/qad_client.py:42-53` [CONFIRMED] — every parameter is interpolated into the **query string** by raw f-string concatenation, `POST` with an empty body:

```python
async def get_token() -> str:
    url = (
        f"{config.qad_base_url()}/qad-central/oauth/token"
        f"?client_id={config.qad_client_id()}"
        f"&username={config.qad_username()}"
        f"&password={config.qad_password()}"
        f"&grant_type=password"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        return resp.json()["access_token"]
```

- Method/URL: `POST {QAD_BASE_URL}/qad-central/oauth/token` [CONFIRMED `backend/qad_client.py:44`]
- `client_id`, `username`, `password`, `grant_type=password`: **all four in the query string**, no JSON body, no form body [CONFIRMED `backend/qad_client.py:45-49`]
- No `urllib.parse.quote` / no `params=` dict — values are not URL-encoded [CONFIRMED, by absence at `backend/qad_client.py:42-49`]. [INFERRED] A password containing `&`, `+`, `#`, `%` or a space corrupts the request; `+` would silently decode as a space server-side. Confirm by testing a password with `&` in it.
- `resp.json()["access_token"]` uses subscript, not `.get()` — a malformed response raises `KeyError`, not a typed auth error [CONFIRMED `backend/qad_client.py:53`].

**1b. `core/qad_session.py` — the "unified" manager — contains a second, better implementation of the same call that is DEAD CODE.**

`backend/core/qad_session.py:43-54` [CONFIRMED]:

```python
async def get_bearer_token(timeout: float = 30.0) -> str:
    base = _base()
    params = {
        "client_id": config.qad_client_id(),
        "username": config.qad_username(),
        "password": config.qad_password(),
        "grant_type": "password",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(base + OAUTH_PATH, params=params)
```

Same endpoint (`OAUTH_PATH = "/qad-central/oauth/token"`, `backend/core/qad_session.py:28`), but passes `params=` so httpx URL-encodes correctly, and uses `.get("access_token")` with a typed `QadAuthError` (`backend/core/qad_session.py:56-58`). **`get_bearer_token` has zero callers anywhere in the repo** — a repo-wide grep for the symbol returns only its own definition (`backend/core/qad_session.py:43`) and its docstring mention (`:6`) [CONFIRMED]. Its module docstring claim that this is "the single place both features authenticate to QAD" (`backend/core/qad_session.py:2`) is false for the Bearer half; `backend/qad_client.py:4-7` admits the migration is deferred.

**1c. QAD JSESSIONID (SSS deploy only)** — different endpoint, different transport: JSON body, not query string. `backend/core/qad_session.py:70-83` [CONFIRMED]:

```python
def get_session_cookie(timeout: float = 60.0) -> str:
    base = _base()
    payload = {"username": config.qad_username(), "password": config.qad_password()}
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(base + LOGIN_PATH, json=payload,
                           headers={"Content-Type": "application/json;charset=UTF-8"})
    sid = resp.json().get("sessionId")
```

`LOGIN_PATH = "/qad-central/api/login"` (`backend/core/qad_session.py:29`). No `client_id`, no `grant_type` [CONFIRMED, by absence].

**1d. APP-LEVEL login** — `POST /api/auth/login`, **JSON body** `{email, password}`. `frontend/src/features/auth/api.ts:25-29` [CONFIRMED]:

```ts
const r = await fetch(`${BASE}/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
```
`BASE = "/api/auth"` (`frontend/src/features/auth/api.ts:5`); router prefix `/api/auth` (`backend/routers/auth.py:27`); body model `LoginRequest{email,password}` (`backend/routers/auth.py:30-32`). Rate-limited `10/minute` per client IP (`backend/routers/auth.py:52`).

### 2. REFRESH

**There is no refresh anywhere, for either auth system.** [CONFIRMED]

- App-level: stated explicitly at `backend/routers/auth.py:5-6` — "No refresh flow — an expired token forces the user through the login page again." No `/refresh` route exists in `backend/routers/auth.py` (only `/login` at `:51` and `/me` at `:68`) [CONFIRMED]. No refresh token is issued — `LoginResponse` is `{access_token, token_type, email}` only (`backend/routers/auth.py:35-38`).
- **No 401 interception on the frontend.** `frontend/src/shared/api.ts` and `frontend/src/features/client_ext/api.ts` have no 401 branch and attach no token at all. `apiMe` returns `null` on any non-ok (`frontend/src/features/auth/api.ts:54-55`) — that is the only 401 handling, and it runs once at mount.
- QAD Bearer: no retry. Every `get_token()` call site is a fresh full login, and a QAD 401 becomes an `{"error": "QAD HTTP 401", "raw": ...}` envelope (`backend/qad_client.py:26-32`) which `is_qad_success` reports as plain failure (`backend/qad_client.py:75-76`) — the pipeline aborts, it does not re-auth.
- **The one and only 401 retry in the codebase** is in the SSS deploy path, and it re-logs-in rather than refreshing — `backend/sss/deploy.py:81-87` [CONFIRMED]:

```python
sid = get_session_cookie()
resp = _upload(sid)
if resp.status_code == 401:  # session expired between login and upload
    logger.info("[SSS] upload 401 -> re-authenticating and retrying once")
    sid = get_session_cookie()
    resp = _upload(sid)
```

A repo-wide case-insensitive grep for `401|refresh|expire|retry` across `backend/**/*.py` returns no other auth retry [CONFIRMED].

### 3. TOKEN STORAGE / SESSION HOLDING

**No server-side session object, no in-memory session dict, no session table, no cookie set by this app.** [CONFIRMED — `backend/database.py` defines exactly two tables, `runs` (`:14`) and `parent_entities` (`:34`); a grep for `CREATE TABLE|users|user_id` returns nothing else.]

**App-level (JWT, stateless):**
- Signed HS256 (`backend/core/auth.py:33`), TTL `timedelta(hours=8)` (`backend/core/auth.py:32`), PyJWT 2.8.0 (`backend/requirements.txt:11`).
- Claims are exactly `sub` (email), `iat`, `exp` — no roles, no jti, no env scope (`backend/core/auth.py:69-73`) [CONFIRMED]. No revocation list exists, so a leaked token is valid for its full 8h [INFERRED from absence of any jti/denylist].
- Signing secret from `APEX_JWT_SECRET` via `config.apex_jwt_secret()`; missing secret raises `AuthError` (`backend/core/auth.py:40-44`).
- Browser storage key: **`localStorage["apex_token"]`** — `const STORAGE_KEY = "apex_token"` (`frontend/src/features/auth/authStore.tsx:22`), written at `:49-53`, read at `:41`. Not sessionStorage, not a cookie. Storage exceptions are swallowed (`:52`).
- Expiry handling is **once, at mount only**: `init()` calls `apiMe(stored)` and clears the key if the server rejects it (`frontend/src/features/auth/authStore.tsx:65-87`). Server side, `jwt.ExpiredSignatureError` → `AuthError("Your session has expired. Please sign in again.")` (`backend/core/auth.py:86-87`) → HTTP 401 (`backend/core/auth.py:109-113`).
- **A token that expires mid-session is never noticed.** [CONFIRMED by absence] Nothing re-validates after mount, no timer, and no other request carries the token, so the SPA keeps rendering as authenticated until reload. `logout()` only clears React state + localStorage (`frontend/src/features/auth/authStore.tsx:98-102`); there is no server-side logout route.

**QAD (both flavours): nothing is stored at all.** "Nothing is persisted; each token/cookie is fetched fresh" (`backend/core/qad_session.py:11-12`) — matched by implementation: `get_token()` opens a new `AsyncClient` per call with no cache (`backend/qad_client.py:50-53`), and the pipeline calls it **seven separate times per run** (`backend/pipeline.py:434, 475, 514, 596, 684, 708, 737`) [CONFIRMED]. No module-level token variable exists in `backend/qad_client.py` [CONFIRMED].

### 4. CREDENTIAL SOURCE

`.env` keys that actually exist in `backend/.env` (**names only, values not read**): `OPENAI_API_KEY`, `QAD_BASE_URL`, `QAD_USERNAME`, `QAD_PASSWORD`, `QAD_CLIENT_ID`, `ALLOWED_ORIGINS`, `QAD_DOCS_DIR`, `QAD_APP_DIR`, `APEX_ADMIN_EMAIL`, `APEX_ADMIN_PASSWORD`, `APEX_JWT_SECRET` [CONFIRMED via key-name extraction only; all values `<redacted>`]. `.env.example` documents the same set plus `QAD_APP_URI` and `OPENAI_MODEL` (`backend/.env.example:8-49`). Note `QAD_APP_URI` is **absent** from the live `.env`; `backend/settings.json` supplies `qad_app_dir`, `qad_app_uri`, `openai_model` [CONFIRMED via key extraction].

| Credential | Source | Citation |
|---|---|---|
| `QAD_BASE_URL`, `QAD_USERNAME`, `QAD_PASSWORD`, `QAD_CLIENT_ID` | `.env`, merged in `_merged()` | `backend/core/config.py:91-94` |
| same, legacy fallback | `settings.json` keys `qad_server_url`, `qad_client_id`, `qad_username`, `qad_password` — used **only when `.env` is blank** | `backend/core/config.py:113-121` |
| `qad_base_url`, `qad_app_uri`, `openai_model`, `auto_deploy` | `settings.json` **overrides `.env`** (`_UI_KEYS`) | `backend/core/config.py:34, 107-109` |
| `APEX_ADMIN_EMAIL` / `APEX_ADMIN_PASSWORD` / `APEX_JWT_SECRET` | `.env` only | `backend/core/config.py:100-102` |
| UI login form email+password | typed by user, compared to the two `.env` values | `frontend/src/features/auth/LoginPage.tsx:147,159` → `backend/core/auth.py:53-62` |
| **per-request headers** | **none** — no QAD credential ever arrives from the browser | [CONFIRMED by absence] |

`POST /api/settings` accepts only `qad_app_uri`, `qad_app_dir`, `openai_model`, `auto_deploy` — QAD credentials cannot be set from the UI (`backend/routers/settings.py:23-28`, mirrored `frontend/src/shared/api.ts:42-47`). `public_status()` returns `has_qad_password` as a bool, never the value (`backend/core/config.py:178`).

Config is re-read on mtime change without restart, guarded by a `threading.Lock` (`backend/core/config.py:52, 57-67`).

### 5. APP-LEVEL vs QAD-ENVIRONMENT AUTH

Both exist and are **entirely independent**. [CONFIRMED]

- **App-level** — `backend/core/auth.py` + `backend/routers/auth.py`. Self-described: "Single-tenant hardcoded admin", "NOT a production identity story" (`backend/core/auth.py:4-7`).
- **No user table or user model exists.** [CONFIRMED] `backend/models.py` contains only `RunRequest` (`:11`), `HistoryItem` (`:17`), `SSEEvent` (`:31`) — no `User`. `backend/database.py` has no users table (see §3). The single identity is `APEX_ADMIN_EMAIL` compared in `verify_credentials` (`backend/core/auth.py:47-62`).
- **The API surface is effectively unauthenticated.** `get_current_user` is used by **exactly one route**, `GET /api/auth/me` (`backend/routers/auth.py:69`) — a repo-wide grep for `get_current_user|Depends(auth` finds no other call site [CONFIRMED]. Stated intentionally at `backend/core/auth.py:16-18`: "Existing routes are intentionally NOT protected in this phase — the login page is the only gate today, enforced client-side." Confirmed on the wire: `POST /api/run` sends only `Content-Type` (`frontend/src/features/client_ext/api.ts:78-83`), the SSS client builds headers with no `Authorization` (`frontend/src/features/sss/api.ts:52-58`), and `shared/api.ts` calls `/api/health`, `/api/settings`, `/api/sss/connection` bare (`:21, 55, 63, 76`). **Anyone who can reach the port can run the pipeline and deploy to QAD without logging in.**
- **Relationship between the two:** none, beyond both reading `core.config`. The JWT `sub` is never mapped to a QAD user; QAD always authenticates as the single `QAD_USERNAME`. Every APEX user's QAD actions are indistinguishable in QAD audit logs [INFERRED from the single global `QAD_USERNAME` — confirm by inspecting QAD-side audit records].
- Client-side gate wiring: `AuthProvider` wraps `Routes`, `/login` is public, `/*` is wrapped in `ProtectedRoute` (`frontend/src/main.tsx:16-26`); `ProtectedRoute` redirects to `/login` when `!token` (`frontend/src/features/auth/ProtectedRoute.tsx:22`); sign-out is in the sidebar (`frontend/src/features/client_ext/components/Sidebar.tsx:20-23`).

**Credential-comparison defect** [CONFIRMED code, `backend/core/auth.py:59-61`]: `hmac.compare_digest(email.strip().lower(), expected_email)` is called on `str`. [INFERRED — Python stdlib contract] `hmac.compare_digest` accepts `str` only when both are ASCII-only, otherwise raises `TypeError`; a login attempt with a non-ASCII character in email or password would raise inside `login` and surface as HTTP 500, not a clean 401. Confirm by POSTing `{"email":"é@x.com","password":"x"}` to `/api/auth/login`. The comment at `:57-58` claims bytes are compared explicitly — they are not.

### 6. HOW A QAD TOKEN REACHES PIPELINE STEPS AND THE SSS DEPLOY CALL

**Bearer path (Client Extensions pipeline).** No dependency injection, no context object — each step calls `get_token()` inline and passes the string as the third positional arg to `post_qad` / `get_qad`.

Plumbing: `POST /api/run` (`backend/routers/client_extensions.py:117-119`) → `run_pipeline(...)` (`:161-165`) → import `from qad_client import get_token, post_qad, get_qad, is_qad_success` (`backend/pipeline.py:19`) → per-step `token = await get_token()`.

Full list of QAD-calling steps in `run_pipeline`, with the exact endpoint each token is used for [all CONFIRMED]:

| Step | Line | Token fetch → endpoint |
|---|---|---|
| 3 create BC | `pipeline.py:434-438` | `entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` |
| 3 retry after auto-fix (step 4) | `pipeline.py:475-479` | same endpoint, **new token** |
| 3.5 dropdown wiring | `pipeline.py:514-531` | GET then POST `entitymetadatas?entityURI=…&viewUri=…IEntityBuilderCRUD` (one token reused for both) |
| 7 save form | `pipeline.py:596-597` | `viewMetadataV2` |
| 11 event handlers | `pipeline.py:684-685` | `eventhandler` |
| 13 register view | `pipeline.py:708-712` | `viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` |
| 14 deploy | `pipeline.py:737-741` | `deployCheckForWarnings` then `deployBusinessEntity` (one token, two POSTs) |

`post_qad`/`get_qad` build `{qad_base_url}/qad-central/api/qracore/{endpoint}` and set `Authorization: Bearer {token}` (`backend/qad_client.py:56-69`). The embedded pipeline repeats the identical pattern at `backend/pipeline_embedded.py:18, 166, 204, 239, 276, 298, 308, 327`. `core/lookup_generator.py:276-280` also imports `get_token`/`post_qad` directly, but only on the `dry_run is False` branch which is never wired on (`backend/core/lookup_generator.py:259-266`).

**Cookie path (SSS deploy).** `POST /api/sss/deploy` (`backend/routers/sss.py:99-100`) → `sss_deploy.deploy()` (`:115`) → `get_session_cookie()` (`backend/sss/deploy.py:82`) → `_upload(sid)` sets `"Cookie": f"JSESSIONID={session_id}"` (`backend/sss/deploy.py:67`) on a multipart POST to `{base}/qad-central/api/qracore/sss?appURI=…&filename=…dev&appSeq=0&fileSeq=3` (`backend/sss/deploy.py:36-46`). `QadAuthError` → `DeployError` → HTTP 502 (`backend/sss/deploy.py:88-90`, `backend/routers/sss.py:116-117`). `GET /api/sss/connection` does the same login as a liveness probe (`backend/sss/deploy.py:108-114`).

**The APEX JWT never reaches the pipeline.** [CONFIRMED] `run()` takes only `request: Request, req: RunRequest` (`backend/routers/client_extensions.py:119`); `RunRequest` is `{message, run_id, mode}` (`backend/models.py:11-14`). No identity or environment selector crosses the boundary.

### 7. WHAT BREAKS WITH A SECOND QAD ENVIRONMENT (Adaptive) — Phase 1 blockers

Ranked by how hard each is to work around.

1. **Config is a process-global singleton with exactly one slot per key.** `_merged()` returns one flat dict (`backend/core/config.py:86-122`) backed by two module-level caches, `_env_cache` / `_settings_cache` (`backend/core/config.py:53-54`). Accessors take **no arguments**: `qad_base_url()`, `qad_username()`, `qad_password()`, `qad_client_id()`, `qad_app_uri()`, `qad_app_dir()` (`backend/core/config.py:132-145`) [CONFIRMED]. There is no environment id, no dict-of-environments, no `env=` parameter anywhere. Supporting two QAD targets requires changing the shape of `core.config` and every call site.

2. **Every auth function reads that global directly, so it cannot be pointed at a second env.** `qad_client.get_token()` (`backend/qad_client.py:44-48`), `qad_session.get_bearer_token()` (`backend/core/qad_session.py:46-50`), `qad_session.get_session_cookie()` (`backend/core/qad_session.py:73`), `qad_session._base()` (`backend/core/qad_session.py:37`) — none accept a base URL or credential argument [CONFIRMED]. Same for the URL builders `post_qad`/`get_qad` (`backend/qad_client.py:57, 65`) and `sss/deploy.py:_upload_url()` (`backend/sss/deploy.py:38`).

3. **`/qad-central/` is hardcoded in four places.** `backend/core/qad_session.py:28` (`OAUTH_PATH`), `:29` (`LOGIN_PATH`), `backend/qad_client.py:44, 57, 65`, `backend/sss/deploy.py:43` [CONFIRMED]. If the Adaptive env uses a different context root or a token endpoint that is not `oauth/token` password-grant, each must be parameterised. `.env.example:6-7` warns the context path is code-appended, not configurable.

4. **No environment selector reaches the backend from the UI.** `RunRequest` has no `env` field (`backend/models.py:11-14`); `DeployReq` is `{bc_name, ts}` (`backend/routers/sss.py:49-51`); `GenerateReq` is `{bc_name, prompt}` (`:44-46`). A per-run target choice needs new request fields and new plumbing through `run_pipeline`'s signature (`backend/pipeline.py:161-165` call site) [CONFIRMED].

5. **The "one-token" assumption is per-call, which helps — but the token is a bare positional string with no env tag.** Seven independent `get_token()` calls per run (`backend/pipeline.py:434, 475, 514, 596, 684, 708, 737`) means there is no cached token to invalidate — but equally nothing binds a token to an environment, so a mid-run env switch would be silently accepted and the wrong instance written to [INFERRED from the untyped `token: str` parameter at `backend/qad_client.py:56`; confirm by adding an env field and observing that nothing validates it].

6. **`missing_required_keys()` / health checks assume one env.** `REQUIRED_ENV_KEYS` is a flat 4-tuple (`backend/core/config.py:37`), `_REQUIRED_MAP` a flat dict (`:40-45`), `check_qad_reachable()` pings the single `config.qad_base_url()` (`backend/core/health.py:164-170`), `public_status()` returns one `qad_base_url` (`backend/core/config.py:171`), and `GET /api/sss/connection` gates on the flat `_QAD_KEYS` (`backend/routers/sss.py:41, 126`). The frontend `SettingsStatus` mirrors that single-env shape (`frontend/src/shared/api.ts:29-38`). All need to become per-env or the health panel will report only one environment.

7. **`settings.json` can override `qad_base_url` globally, creating a second silent source of truth.** `_UI_KEYS` includes `qad_base_url` (`backend/core/config.py:34`) and the legacy fallback block accepts `qad_server_url`, `qad_username`, `qad_password`, `qad_client_id` from `settings.json` when `.env` is blank (`backend/core/config.py:113-121`) [CONFIRMED]. With two environments, whichever writes `settings.json` last wins for both. `save_ui_settings` persists `_UI_KEYS` unconditionally (`backend/core/config.py:185-197`).

8. **SSS is hard-bound to one workspace and one app URI.** `qad_app_dir()` resolves a single path (`backend/core/config.py:137-144`), `app_uri()`/`app_script_name()`/`app_namespace()` derive from the single `QAD_APP_URI` (`backend/sss/appconfig.py:15-33`), and the compile workspace is scaffolded once at startup from `_cfg.qad_app_dir()` (`backend/main.py:186-190`). Two environments deploying different compiled bundles would collide in the same `sss_workspace` [INFERRED from the single-path accessor; confirm by checking whether `dist_files()` in `backend/sss/compile.py` is env-parameterised].

9. **The dead `get_bearer_token` is a trap.** Refactoring `core/qad_session.py` for multi-env would appear to fix the Bearer path while the live path in `backend/qad_client.py:42` stays single-env [CONFIRMED — it has no callers, §1b]. Delete it or make it the real implementation before Phase 1, not after.

10. **Credentials-in-query-string blocks credential-per-env hygiene.** Unencoded interpolation (`backend/qad_client.py:44-49`) means a second env with a stronger/differently-charactered password may fail non-obviously, and both envs' passwords land in QAD access logs and any proxy in between [CONFIRMED construction; INFERRED logging consequence — confirm against the QAD/reverse-proxy access log].

11. **Not a blocker but a Phase 1 decision:** the JWT carries no environment claim (`sub`/`iat`/`exp` only, `backend/core/auth.py:69-73`) and no route except `/api/auth/me` is protected (§5). If Adaptive is a production instance, "anyone on the port can deploy" becomes a materially different risk than it is today.

---

---

## A6. Run-state storage today, and what partial-run persistence would need

All paths are relative to `D:/WEB_AUX/aux_web_version/`. Every line number below was read from the file in this session.

### A6.0 Headline finding (read this first)

**[CONFIRMED] There is no approval mechanism in the Client-Extensions run flow at all.** `run_pipeline` (`backend/pipeline.py:381-802`) executes all 14 steps linearly with zero human gates; the only thing that halts it is an error path that does `return`. Grep for `approv|pause|resume|awaiting|checkpoint` across `backend/**/*.py` produced no run-gating code — the only hits are the string `"isAllowApproval": False` in `backend/builders/embedded_builder.py:189`, an `approval` dropdown example in `backend/agents/prompts.py:76`, and doc/comment uses of "gate" for the tsc syntax check and the SSS readiness check.

The only user-facing "approve" in the product is the SSS feature's **"Approve & Deploy"** button (`frontend/src/features/sss/ReviewDeploy.tsx:92`) → `POST /api/sss/deploy` (`backend/routers/sss.py:99-119`). That gate is entirely client-side and stateless: the generated TS lives in `useState` (`frontend/src/features/sss/SssPanel.tsx:31-33`) and is re-sent in the deploy body (`DeployReq.ts`, `backend/routers/sss.py:49-51`). Nothing about it is persisted, and it has no run id.

So Phase 3 must **add** approvals, not merely persist them. "Partially-approved run" is not a state this codebase can currently be in.

---

### A6.1 Exact schema (dumped read-only from `backend/history.db`)

`PRAGMA user_version = 1`. `journal_mode = delete`, `busy_timeout = 5000`, `foreign_keys = 0`, `synchronous = 2` — **[CONFIRMED]** none of these are set anywhere in code (grep for `journal_mode|WAL|busy_timeout|isolation_level` over `backend/**/*.py` returns only httpx/subprocess timeouts), so all four are SQLite defaults.

`sqlite_master` contains exactly **two tables, two PK autoindexes, zero explicit indexes, zero FKs, zero triggers, zero views**.

#### Table `runs` — 19 rows

Live DDL (from `sqlite_master`), which differs from the source DDL in one telling way:

```
CREATE TABLE runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                user_input TEXT NOT NULL,
                bc_pascal TEXT,
                description TEXT,
                field_count INTEGER,
                panel_count INTEGER,
                status TEXT NOT NULL,
                summary_json TEXT,
                error_message TEXT
            , mode TEXT DEFAULT 'standard')
```

**[CONFIRMED]** `mode` is appended after the closing-paren position of the original DDL — the signature of `ALTER TABLE ADD COLUMN`. That is the migration at `backend/database.py:49`, wrapped in `try/except Exception: pass` (`backend/database.py:48-51`). The original `CREATE TABLE` is `backend/database.py:14-27`.

`PRAGMA table_info(runs)` — `(cid, name, type, notnull, default, pk)`:

| cid | column | type | notnull | default | pk |
|---|---|---|---|---|---|
| 0 | `id` | TEXT | 0 | — | 1 |
| 1 | `created_at` | TEXT | 1 | — | 0 |
| 2 | `user_input` | TEXT | 1 | — | 0 |
| 3 | `bc_pascal` | TEXT | 0 | — | 0 |
| 4 | `description` | TEXT | 0 | — | 0 |
| 5 | `field_count` | INTEGER | 0 | — | 0 |
| 6 | `panel_count` | INTEGER | 0 | — | 0 |
| 7 | `status` | TEXT | 1 | — | 0 |
| 8 | `summary_json` | TEXT | 0 | — | 0 |
| 9 | `error_message` | TEXT | 0 | — | 0 |
| 10 | `mode` | TEXT | 0 | `'standard'` | 0 |

Index: `sqlite_autoindex_runs_1` (unique, PK-derived) only. `PRAGMA foreign_key_list(runs)` → empty.

Observed data: `status` ∈ {`success`: 17, `failed`: 2}; `mode` ∈ {`standard`: 16, `embedded`: 3}; `summary_json IS NULL` on exactly 2 rows (the 2 failed). `created_at` range `2026-06-05T12:20:48.827156+00:00` → `2026-07-27T09:11:10.849987+00:00`, ISO-8601 with UTC offset (written at `backend/routers/client_extensions.py:187` via `datetime.now(timezone.utc).isoformat()`).

**[CONFIRMED]** `status` is only ever `'success'` or `'failed'` — set at `backend/routers/client_extensions.py:151` (`final_status = "failed"` initial) and `:175` (`final_status = "success"` on the `complete` event). `backend/models.py:25` documents exactly that: `status: str  # success | failed`. There is no `running`, `paused`, or `aborted` value.

#### Table `parent_entities` — 22 rows (`builtin`: 5, `custom`: 17)

DDL matches `backend/database.py:34-44` verbatim. Columns: `entity_code TEXT PK`, `uri TEXT NN`, `pk_fields TEXT NN` (JSON array), `fk_field TEXT NN`, `fk_type TEXT NN DEFAULT 'character'`, `description TEXT NN DEFAULT ''`, `source TEXT NN DEFAULT 'custom'`, `created_at TEXT NN`, `updated_at TEXT NN`. Index: `sqlite_autoindex_parent_entities_1` only. No FK to `runs` — deliberately, per the comment at `backend/database.py:29-32` ("decoupled from the `runs` history so pruning history never de-registers a parent").

#### Which code writes each

| Statement | Site | Called from |
|---|---|---|
| `CREATE TABLE runs` | `backend/database.py:13-27` | `init_db()` ← `backend/main.py:164` |
| `ALTER TABLE runs ADD COLUMN mode` | `backend/database.py:49` | same (idempotent, swallowed) |
| `CREATE TABLE parent_entities` | `backend/database.py:33-45` | same |
| `INSERT INTO runs` (11 cols) | `backend/database.py:58-68`, commit `:69` | `save_run()` ← **only** `backend/routers/client_extensions.py:198` |
| `DELETE FROM runs WHERE id=?` | `backend/database.py:92` | `delete_run()` ← `backend/routers/client_extensions.py:231` (`DELETE /api/history/{run_id}`) |
| `SELECT * FROM runs ORDER BY created_at DESC LIMIT ?` | `backend/database.py:76` | `list_runs()` ← `backend/routers/client_extensions.py:218` |
| `SELECT * FROM runs WHERE id=?` | `backend/database.py:85` | `get_run()` ← `backend/routers/client_extensions.py:223` |
| `SELECT summary_json FROM runs WHERE status='success' AND mode='standard'` | `backend/main.py:132-134` | `_backfill_parents_from_runs()` ← `backend/main.py:173` |
| `INSERT … ON CONFLICT(entity_code) DO UPDATE` on `parent_entities` | `backend/database.py:157-176` | `backend/main.py:109` (seed), `backend/main.py:147` (backfill), `backend/qad_entity_registry.py:187` ← `backend/pipeline.py:785` |
| `PRAGMA user_version = N` | `backend/database.py:125` | `backend/main.py:176` |

**[CONFIRMED — absence is the finding] There is no `UPDATE` statement against `runs` anywhere in the backend.** A run row is written exactly once and is immutable thereafter. Any mid-flow persistence design must add the first-ever `UPDATE runs` path.

**[CONFIRMED]** Every DB function opens its own connection (`async with aiosqlite.connect(DB_PATH)` at `backend/database.py:12, 57, 73, 83, 91, 116, 124, 131, 156`) and closes it. No pool, no long-lived handle, no `app.state` DB object. `DB_PATH = Path(__file__).parent / "history.db"` (`backend/database.py:8`).

#### `backend/history.db.bak-tier1`

**[CONFIRMED]** It is an SQLite database, 167,936 bytes, mtime `Jul 8 17:02`, containing **only the `runs` table** (9 rows) — `parent_entities` is absent — and `PRAGMA user_version = 0`. Its `created_at` range is `2026-06-05T12:20:48` → `2026-06-12T06:22:08`. `freelist_count = 11` (vs 3 in the live DB). It is untracked by git and matched by the `.gitignore` rule `backend/history.db.bak*` (`.gitignore`, "Runtime generated" block).

**[INFERRED]** It is a hand-made pre-migration snapshot taken during the "Tier 1 refactor" referenced at `PROGRESS.md:66` ("the Tier 1 refactor's `main.py` edit dropped …"). Supporting evidence: its mtime (`Jul 8 17:02`) is 13 minutes before `backend/database.py`'s mtime (`Jul 8 17:15`), the commit that added `parent_entities` + `user_version`; and it lacks both of those. What would confirm it: asking the author, or a shell-history/commit record of the `copy` — the file is untracked so git cannot tell us.

**[CONFIRMED, incidental]** One row exists in the backup but **not** in the live DB: `id=22edfab0-b390-4ab9-b806-c902a7b1e6cd`, `bc_pascal='DealerOrderHeadersV2'`, `created_at=2026-06-12T06:22:08.918172+00:00`. **[INFERRED]** it was removed via `DELETE /api/history/{run_id}` (`backend/routers/client_extensions.py:229-234`), the only delete path in the code.

---

### A6.2 WHEN rows are written

**[CONFIRMED] Exactly one row per run, written after the pipeline generator is fully exhausted. Nothing at run start. Nothing per step.**

The flow inside `POST /api/run` (`backend/routers/client_extensions.py:117-212`):

1. `:120` — `run_id = str(uuid.uuid4())`. **Not persisted, not yet sent to the client.**
2. `:129-146` — optional deterministic `.p`/`.cls` parse (request-scope locals only).
3. `:148` — `async def event_stream()` defined; `:149-151` initialise `summary = None`, `last_error = None`, `final_status = "failed"`.
4. `:158-166` — pick `run_embedded_pipeline(...)` or `run_pipeline(...)`. **`run_id` is not passed in.**
5. `:168-180` — the streaming loop. Each chunk is yielded to the browser, then re-parsed only to capture `summary` / `last_error`:

```python
        async for chunk in pipeline_gen:
            yield chunk
            # parse to track final state for history
            try:
                data = json.loads(chunk.removeprefix("data: ").strip())
                if data.get("type") == "complete":
                    summary = data.get("summary")
                    final_status = "success"
                elif data.get("type") == "error":
                    last_error = data.get("error", "Pipeline error")
            except Exception:
                pass
```

6. `:184-198` — **the single write**, positioned *after* the loop: `HistoryItem(...)` then `await save_run(item)`. Wrapped in `try/except` that logs but does not fail the request (`:199-200`).
7. `:203` — **only now** is `run_id` emitted to the browser: `yield f"data: {json.dumps({'type': 'run_id', 'run_id': run_id})}\n\n"`, with the comment "send run_id so frontend can link to history".

Consequences, all load-bearing for Phase 3:

- **[CONFIRMED] The browser does not learn the run_id until the run has already finished and been saved.** A refresh mid-run leaves the client with no identifier for the work in flight. (Frontend side: `frontend/src/features/client_ext/ClientExtPanel.tsx:125-128` sets `activeHistoryId` only on the `run_id` event.)
- **[CONFIRMED] A failed run *does* get a row** (`status='failed'`, `error_message` set) — provided the generator returns normally. Every error path in `pipeline.py` does `yield _evt("error", …)` then `return`, e.g. `backend/pipeline.py:412-413, 424-425, 588-589`, so the loop drains and the save runs.
- **[INFERRED, high confidence] An aborted run gets NO row.** The frontend aborts via `controller.abort()` (`frontend/src/features/client_ext/api.ts:120`, invoked from `ClientExtPanel.tsx:64` on "New" and `:167` on selecting a history item). Starlette/anyio cancels the `StreamingResponse` generator task; cancellation is raised at the `yield` inside the `async for` at `:169`, so `:184-198` never executes and the `try/except Exception` at `:184` cannot catch it (it is after the loop, and `CancelledError` is not an `Exception` subclass in py3.8+). What would confirm it: an opt-in live test — start a run, hit refresh at step 5, then check `select count(*) from runs`. **A browser refresh today therefore destroys the run *and* leaves no trace of it.**
- **[CONFIRMED] `RunRequest.run_id` is dead code.** `backend/models.py:13` declares `run_id: Optional[str] = None`, but grep for `run_id` across the backend shows it is never read — `:120` unconditionally mints a fresh uuid4. A client cannot supply or re-target a run id today.
- **[CONFIRMED] No log line correlates to a run.** Pipeline logging (`backend/pipeline.py:364, 375, 449, 547, 563, 731`) carries no run id; `run_id` appears in a log statement only at `backend/routers/client_extensions.py:200` (the save-failure line).

---

### A6.3 What is stored per run — a final artifact only

**[CONFIRMED] Only a terminal summary. No per-step output is persisted anywhere.**

`summary_json` is built once at `backend/pipeline.py:753-776` and emitted with the `complete` event at `:802`. Dumped structurally from the **2 most recent rows** (both `status='success'`, `mode='standard'`, 902 and 901 chars): a JSON object whose top-level keys are, in both rows, exactly:

`bc_pascal` (str), `description` (str), `field_count` (int), `fields` (list, 5), `lookups` (dict, 4), `module` (str), `panel_count` (int), `panels` (list, 2), `pk_codes` (list, 1), `view_label` (str).

The `lookups` sub-object's shape is `{detected, static_dry_run, needs_manual_setup, static_payload_gaps}` (`backend/pipeline.py:118-123`, defaulted at `:772-775`). The 4 scalar columns `bc_pascal` / `description` / `field_count` / `panel_count` are duplicated out of the same summary at `backend/routers/client_extensions.py:189-192`.

**What is NOT stored — every one of these lives only in the generator frame:**

| `state` key | Set at | Content |
|---|---|---|
| `requirements` | `backend/pipeline.py:405` (parser) / `:410` (LLM) | step-1 output |
| `spec` | `backend/pipeline.py:422`, re-set `:471` after auto-fix | step-2/4 field spec |
| `bc_summary` | `backend/pipeline.py:500` | step-3 BC payload summary |
| `panel_plan` | `backend/pipeline.py:548` | step-5 raw LLM text |
| `placements` | `backend/pipeline.py:586` | step-6 grid placements |
| `form_summary` | `backend/pipeline.py:606` | step-7 panels |
| `eh_plan` | `backend/pipeline.py:626` | step-8 plan text |
| `ts_code` | `backend/pipeline.py:649` | step-9 generated TypeScript |
| `js_code` | `backend/pipeline.py:674` | step-10 compiled JS |
| `view_summary` | `backend/pipeline.py:699` | step-12 view config |
| `lookup_summary` | `backend/pipeline.py:118` | lookup counts |

Only `panel_count`/`panels` (from `form_summary`), `pk_codes` (from `bc_summary`) and `view_label` (from `view_summary`) survive, as scalars. **`ts_code`, `js_code`, `placements`, `requirements`, `spec`, `panel_plan`, `eh_plan` are lost the moment the generator exits.** The embedded pipeline is the same: `state` at `backend/pipeline_embedded.py:64`, summary at `:362`.

Also not stored: the SSE event stream itself (the `{type, step, total, name, status, message}` frames built at `backend/pipeline.py:163-177` that the UI renders), the step number reached, per-step timestamps, the parser-warning frames (`backend/routers/client_extensions.py:155-156`), and the `lookup_candidate` / `lookup_needs_review` / `lookup_summary` dry-run payloads (`backend/pipeline.py:81-131`) — those are emitted to the browser and never written down.

**Verdict for Phase 3: with today's schema, mid-flow step outputs cannot be restored. Not partially, not approximately.** The `runs` row does not exist until the run is over, and even then it holds none of the intermediate artifacts.

**[CONFIRMED] Logs are not a viable fallback.** `backend/logs/app.log` (195,232 bytes; `RotatingFileHandler(maxBytes=5_000_000, backupCount=5)` at `backend/core/logging_setup.py:44`) does contain two step outputs, but both are truncated and neither is run-correlated: `backend/pipeline.py:364` logs `raw[:1000]` of the step-6 builder output, `backend/pipeline.py:547` logs `panel_plan[:500]`. No `ts_code`, no `spec`, no run id.

---

### A6.4 Run state held ONLY in memory — full enumeration

Every item in group A is lost on browser refresh **and** on backend restart. Group B is lost on restart but rebuilds from a durable source.

**Group A — genuinely volatile run state (the whole problem):**

| # | Store | file:line | Lost on |
|---|---|---|---|
| A1 | `state: Dict[str, Any] = {}` — the standard pipeline's entire working memory (all 11 keys in §A6.3) | `backend/pipeline.py:397` | refresh + restart |
| A2 | `state: Dict[str, Any] = {}` — embedded pipeline equivalent | `backend/pipeline_embedded.py:64` | refresh + restart |
| A3 | `summary`, `last_error`, `final_status` — closure locals of `event_stream()` | `backend/routers/client_extensions.py:149-151` | refresh + restart |
| A4 | `run_id` — request-scope local, unpersisted until `:198` | `backend/routers/client_extensions.py:120` | refresh + restart |
| A5 | `parsed_requirements`, `parse_warnings`, `lookup_candidates` — request-scope locals holding the deterministic `.p` parse | `backend/routers/client_extensions.py:126-128` | refresh + restart |
| A6 | The `asyncio` task executing the `StreamingResponse` generator — **and no registry of it** | `backend/routers/client_extensions.py:205-212` | refresh + restart |
| A7 | Frontend: `view` (which carries the `events: SSEEvent[]` array), `input`, `running`, `activeHistoryId`, `mode`, `pipelineSummary`, `summaryRef`, `attachedFile`, `abortRef` | `frontend/src/features/client_ext/ClientExtPanel.tsx:42-57` | refresh |
| A8 | Frontend SSS: `selected`, `bcDetail`, `prompt`, `gen`, `editedTs`, `deployResult` — includes the not-yet-approved generated TypeScript | `frontend/src/features/sss/SssPanel.tsx:21-36` | refresh |

**A6 deserves emphasis. [CONFIRMED by absence]** there is no in-flight-run registry of any kind: grep for `app.state` across the backend yields exactly one hit, `app.state.limiter = limiter` (`backend/main.py:43`). There is no `dict[run_id] → task`, no `asyncio.Queue` per run, no pub/sub. The SSE channel is bound 1:1 to the `POST /api/run` request, so a refresh both loses the client's view *and* (per §A6.2) cancels the server-side work. **There is nothing to re-attach to.**

**Group B — in-memory caches that do rebuild (listed for completeness; none is run state):**

| # | Store | file:line | Rebuilt from |
|---|---|---|---|
| B1 | `QAD_STANDARD_ENTITIES` module dict | `backend/qad_entity_registry.py:87` | write-through to `parent_entities` (`:187`) + `hydrate()` at `backend/main.py:177` |
| B2 | `_report` health global | `backend/core/health.py:37`, set via `:204-206` from `backend/main.py:204` | recomputed at startup |
| B3 | `_env_cache`, `_settings_cache` (mtime-keyed) | `backend/core/config.py:53-54` | `.env` / `settings.json` on disk |
| B4 | `docs_loader._cache` (folder → text) | `backend/core/qad_docs_loader.py:70`, loaded at `backend/main.py:197` | `qad_docs/` on disk |
| B5 | `_cache = {"key": None, "bcs": None}` (SSS BC discovery) | `backend/sss/discover.py:46`, used `:221-231` | `lib/*.d.ts` on disk |
| B6 | slowapi in-memory rate-limit counters | `backend/main.py:43`, `backend/core/rate_limit.py` | reset on restart — **note:** `POST /api/run` is `5/minute` (`backend/routers/client_extensions.py:118`), which a resume flow will consume |

---

### A6.5 Any other persistence?

**On disk (backend):**
- `backend/history.db` — the only database. Discussed above.
- `backend/history.db.bak-tier1` — snapshot, §A6.1.
- `backend/logs/app.log` — `backend/core/logging_setup.py:23-24, 44`. Partial, truncated, uncorrelated (§A6.3).
- `backend/settings.json` (112 bytes) — written by `backend/core/config.py:195` (`SETTINGS_PATH.write_text(...)`) via `POST /api/settings` (`backend/routers/settings.py:37`). Non-secret UI keys only. No run data.
- **[CONFIRMED] The CE pipeline writes no run artifacts to disk.** The one file write in its path is `backend/core/ts_compiler.py:74-76`, `generated_handler.ts` inside a `tempfile.TemporaryDirectory()` — deleted on context exit. The generated TypeScript is *not* saved.
- `backend/sss_workspace/` — SSS only, and only via `POST /api/sss/deploy`: `backend/sss/compile.py:43-44` (`dest.write_text(ts_content)`) and `:51` (`dist/`). On disk now: `sss_workspace/src/com/` exists, `sss_workspace/dist/` is **empty**. Not CE run state.
- `frontend/dist/` — static build served by `backend/main.py:212-214`. Build artifact only. **[CONFIRMED, incidental]** `frontend/dist/index.html` mtime `Jul 17 23:08` is older than `frontend/index.html` (`Jul 21 15:17`), so the served bundle is stale relative to source; irrelevant to run state but relevant if Phase 3 ships frontend changes without rebuilding.

**Frontend browser storage — exactly three keys, none run-related:**
- `apex_active_feature` — `frontend/src/App.tsx:20` (read), `:31` (write)
- `apex-theme` — `frontend/src/App.tsx:52`
- `apex_token` — `frontend/src/features/auth/authStore.tsx:41, 49-50` (`STORAGE_KEY`, documented `:6`)

**[CONFIRMED] No `sessionStorage`, no `indexedDB`, no Zustand, no persist middleware.** Grep for `localStorage|sessionStorage|indexedDB|persist|zustand` across `frontend/src` returns only the three keys above plus one prose comment. `frontend/package.json` dependencies are exactly `react`, `react-dom`, `react-router-dom` — no state library. `frontend/src/features/auth/authStore.tsx:3` states outright that the codebase uses hooks + localStorage rather than a store lib.

**[CONFIRMED] The URL carries no run identity.** Routes are `/login` and `/*` → `App`, plus a catch-all `Navigate to="/"` (`frontend/src/main.tsx:17-30`). There is no `/run/:id`, so today there is not even an anchor a refresh could restore from.

**[CONFIRMED] The only rehydration that exists anywhere** is the sidebar's history list: `fetchHistory().then(setItems)` on mount and on `refreshTick` (`frontend/src/features/client_ext/components/Sidebar.tsx:29-31`). It shows *completed* runs only.

---

### A6.6 Concrete gap list

**Is extending `history.db` viable? Yes — I found no reason it is not.** Positive evidence: `aiosqlite` with connection-per-operation (`backend/database.py:12, 57, 73, …`) means there is no long-lived handle or pool to migrate around; `init_db()` is already `CREATE TABLE IF NOT EXISTS` plus a swallowed `ALTER TABLE` (`backend/database.py:13-51`), so additive migration is the established, proven pattern (the live `runs` DDL proves it ran); and `PRAGMA user_version` is already wired as a one-time migration marker (`backend/database.py:114-126`, gated at `backend/main.py:100, 172-176`). Two caveats to fix rather than reasons to abandon it, both **[CONFIRMED]**: (i) `journal_mode = delete` with default `busy_timeout = 5000` — per-step writes during a run concurrent with a `GET /api/history` read will contend; set WAL. (ii) `PRAGMA foreign_keys = 0` — a declared FK on a new child table will not be enforced unless enabled per-connection.

#### (a) Schema additions

1. `runs` — new nullable columns via the existing `try/except ALTER` idiom (`backend/database.py:48-51`): `updated_at TEXT`, `current_step INTEGER`, `total_steps INTEGER`, `awaiting_gate TEXT`. Widen the `status` vocabulary beyond `success|failed` (`backend/models.py:25`) to include `running`, `awaiting_approval`, `aborted`.
2. New `run_steps(run_id TEXT, step INTEGER, name TEXT, status TEXT, message TEXT, output_json TEXT, started_at TEXT, finished_at TEXT, PRIMARY KEY(run_id, step))` — one row per `state[...]` assignment in §A6.3, plus `CREATE INDEX ix_run_steps_run ON run_steps(run_id)`. This is the table that makes "restore per-step outputs" possible; nothing today can substitute for it.
3. New `run_approvals(run_id TEXT, gate_id TEXT, decision TEXT, decided_by TEXT, decided_at TEXT, payload_json TEXT, PRIMARY KEY(run_id, gate_id))` — "approvals given" has no representation at all today.
4. New `run_side_effects(run_id TEXT, step INTEGER, endpoint TEXT, entity_uri TEXT, committed_at TEXT)`. **This one is non-negotiable:** the pipeline makes irreversible QAD POSTs at step 3 (`backend/pipeline.py:435`), 3.5 dropdown wiring (`:529`), 7 form save (`:597`), 11 event handlers (`:685`), 13 view (`:709`), and 14 deploy check + deploy (`:739`, `:741`). Only step 3 has a collision guard (`_is_duplicate_entity_error`, `backend/pipeline.py:226-231`, used at `:447` and `:484`); the other five have none. Without a committed-side-effects ledger, any resume double-POSTs to QAD.
5. Add explicit indexes — there are none today beyond PK autoindexes.

#### (b) Write-site additions

1. **Insert the `runs` row at run start**, at `backend/routers/client_extensions.py:120` (right after the uuid4), with `status='running'`. Today the only insert is at `:198`, after the loop.
2. **Move the `run_id` frame to the front of the stream.** It is currently emitted at `:203`, after the save — so the client cannot know its own run's id mid-flight.
3. **Pass `run_id` into `run_pipeline` / `run_embedded_pipeline`** (`backend/pipeline.py:381-385`, `backend/pipeline_embedded.py:62`) — they take no run identity at all today.
4. **Persist each step output.** Add a `run_steps` upsert next to each of the 11 `state[...]` assignments (`backend/pipeline.py:405/410, 422, 471, 500, 548, 586, 606, 626, 649, 674, 699` and `:118`), and a `runs.current_step`/`updated_at` bump next to each `_evt("step", n, "done", …)`.
5. **Add the first-ever `UPDATE runs` function** in `backend/database.py` and convert the terminal `save_run` (`backend/database.py:56-69`, called at `client_extensions.py:198`) into a final update. `save_run`'s bare `INSERT` will otherwise raise on the PK.
6. **Persist a side-effect row immediately after each successful QAD POST** (the six sites in (a)(4)).
7. **Honour `RunRequest.run_id`** (`backend/models.py:13`, currently dead) so a resume can target an existing run instead of minting a new one at `:120`.
8. **Make the cancellation path write.** Wrap the `async for` at `client_extensions.py:168-180` in `try/except asyncio.CancelledError` (or `finally`) so a disconnect records `status='aborted'` and `current_step` rather than vanishing.

#### (c) Resume / read endpoint

1. `GET /api/runs/{run_id}/state` → `{run, steps[], approvals[], side_effects[], current_step, awaiting_gate}`. The existing `GET /api/history/{run_id}` (`backend/routers/client_extensions.py:221-226`) cannot serve this: it returns a bare `HistoryItem` and raises `HTTPException(404, "Run not found")` for anything mid-flight, because no row exists.
2. `POST /api/runs/{run_id}/approve` with `{gate_id, decision}` — no such route exists (full route inventory: `/api/run`, `/api/history`, `/api/history/{run_id}` GET+DELETE, `/api/entities`, `/api/settings` GET+POST, `/api/health`, `/api/auth/login`, `/api/auth/me`, `/api/sss/{bcs,bcs/{name},generate,deploy,connection}`).
3. A **re-attach channel** — `GET /api/runs/{run_id}/events` (SSE) or polling. Note the ordering problem: per §A6.4/A6, there is no in-flight registry, so re-attach requires *first* introducing one (run_id → task + event buffer), or accepting a poll-the-DB design where the browser reads `run_steps` instead of a live stream.
4. **A resumable executor — this is the real work.** `run_pipeline` is one ~420-line linear async generator (`backend/pipeline.py:381-802`) with hardcoded sequential steps and no dispatch table; `state` is its frame-local dict (`:397`). "Resume at step 8" therefore requires either (i) decomposing it into per-step functions keyed by step number that take/return a serialisable `state`, or (ii) reconstructing `state` from `run_steps` and re-entering at an offset. Neither is a wrapper — budget for a genuine refactor of `pipeline.py`, and mirror it in `pipeline_embedded.py` (7 steps, `BASE_TOTAL_STEPS = 7` at `:30`).

#### (d) Frontend rehydration

1. **Persist the active run id.** Either a fourth localStorage key alongside the existing three (`frontend/src/App.tsx:31, 52`; `authStore.tsx:49`) or — better — a `/run/:id` route, which requires adding it to `frontend/src/main.tsx:17-30` (no such route today).
2. **Rehydrate on mount.** `ClientExtPanel` initialises `view` to `{kind:"empty"}` unconditionally (`frontend/src/features/client_ext/ClientExtPanel.tsx:42`); it needs a mount effect that calls the new state endpoint and reconstructs `{kind:"running", input, events}` (and a new `awaiting_approval` view kind).
3. **One piece of good news: `ProgressPanel` needs no change.** It derives its entire display by folding an `SSEEvent[]` into a step map (`frontend/src/features/client_ext/components/ProgressPanel.tsx:51-58`), so a server-rebuilt array of step events renders identically. Likewise `SummaryCard` is already fed from parsed `summary_json` on the history path (`ClientExtPanel.tsx:305`).
4. **Re-attach or poll after rehydration**, and handle the `running`-but-backend-restarted case (steps done in DB, no live task) as a distinct, user-visible state rather than a stuck spinner.
5. **New approval UI** in the CE panel. The SSS pattern (`frontend/src/features/sss/ReviewDeploy.tsx:92`) is a usable visual precedent but not reusable logic — it holds the pending payload in `useState` (`SssPanel.tsx:31-33`) and re-POSTs it, which is exactly the volatility Phase 3 is meant to eliminate.

---

---

I have complete coverage. Here is the audit section.

## A7. Does AUX ever read artifacts back from QAD?

### A7.1 Complete outbound HTTP inventory

[CONFIRMED] The backend has exactly **four** modules that open a socket to QAD. Grep for `httpx|requests\.|urllib|aiohttp` across `backend/**/*.py` returns hits only in `backend/qad_client.py`, `backend/core/qad_session.py`, `backend/core/health.py:169-170`, and `backend/sss/deploy.py`. There is no other HTTP client in the backend.

[CONFIRMED] `backend/qad_client.py` exposes exactly three network helpers and they are the only path to the `qracore` API surface:
- `get_token()` — `backend/qad_client.py:42-53`, POST `{base}/qad-central/oauth/token`
- `post_qad(endpoint, payload, token)` — `backend/qad_client.py:56-61`, POST `{base}/qad-central/api/qracore/{endpoint}`
- `get_qad(endpoint, token)` — `backend/qad_client.py:64-69`, GET `{base}/qad-central/api/qracore/{endpoint}`

#### WRITE calls (POST)

| # | Endpoint (appended to `/qad-central/api/qracore/`) | Purpose | file:line |
|---|---|---|---|
| 1 | `entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` | Step 3 create BC | `backend/pipeline.py:435-438` |
| 2 | same as #1 | Step 3 retry after LLM auto-fix | `backend/pipeline.py:476-479` |
| 3 | `entitymetadatas?entityURI={q}&viewUri=…IEntityBuilderCRUD` | Step 3.5 dropdown write-back | `backend/pipeline.py:529-532` |
| 4 | `viewMetadataV2` | Step 7 save form | `backend/pipeline.py:597` |
| 5 | `eventhandler` | **Step 11 register event handler** | `backend/pipeline.py:685` |
| 6 | `viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata` | Step 13 register view | `backend/pipeline.py:709-712` |
| 7 | `deployCheckForWarnings` | Step 14a | `backend/pipeline.py:739` |
| 8 | `deployBusinessEntity` | Step 14b | `backend/pipeline.py:741` |
| 9 | `entitymetadatas?…IEntityBuilderCRUD` | Embedded step 3 (+retry :205) | `backend/pipeline_embedded.py:167,205` |
| 10 | `entitymetadatas?entityURI={q}&…` | Embedded dropdown write-back | `backend/pipeline_embedded.py:251-254` |
| 11 | `berelation?viewUri=urn:be:com.qad.qra.berelation.IBERelation` | Embedded step 5 relation | `backend/pipeline_embedded.py:277-280` |
| 12 | `deployCheckForWarnings` / `deployBusinessEntity` | Embedded steps 6/7 | `backend/pipeline_embedded.py:299,309` |
| 13 | `viewResourceMetadatas…` | Embedded view | `backend/pipeline_embedded.py:328` |
| 14 | `lookups?viewUri=urn:be:com.qad.qra.lookup.ILookup` | Lookup create — **dry-run by default, no network** | `backend/core/lookup_generator.py:280`; endpoint const at `:70` |
| 15 | `{base}/qad-central/api/qracore/sss?appURI=…&filename=…&appSeq=0&fileSeq=3` | SSS multipart upload of `dev.js`/`.js.map`/`.d.ts` | `backend/sss/deploy.py:62-72`, URL built at `:36-46` |

[CONFIRMED] #14 never reaches the network unless `dry_run is False`, and the guard is inverted defensively — `if dry_run is not False:` returns early (`backend/core/lookup_generator.py:266-273`). The docstring at `:259-260` states it "is never defaulted or wired on in the pipeline".

#### AUTH calls (not artifact traffic)

[CONFIRMED] POST `{base}/qad-central/oauth/token` (`backend/qad_client.py:42-53`; duplicate impl `backend/core/qad_session.py:43-67`, path const `OAUTH_PATH` at `:28`) and POST `{base}/qad-central/api/login` returning `sessionId` (`backend/core/qad_session.py:70-93`, `LOGIN_PATH` at `:29`).

### A7.2 Definitive table of every READ-from-QAD call

[CONFIRMED] `get_qad` is the only GET helper against the QAD API, and grep for `get_qad` across the backend yields exactly **two** call sites. There are no others.

| Method | Full path | What it returns | Who consumes it | file:line |
|---|---|---|---|---|
| GET | `/qad-central/api/qracore/entitymetadatas?entityURI={urlquoted bc_data["entity_uri"]}&viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD` | `{"data": {"entityMetadatas": [{… "entityFields": [{entityFieldCode, dataListCode, defaultValue, concurrencyHash, entityFieldID, uri …}]}]}}` — the *enriched* metadata of the BC created seconds earlier in the same run | Unwrapped at `pipeline.py:521`, existence-checked at `:522`, mutated by `patch_dropdown_fields(enriched, field_list_map)` (`backend/builders/bc_builder.py:98-111`), then POSTed straight back at `:529` | `backend/pipeline.py:516-519` |
| GET | identical path/shape | identical | Same three-step unwrap/patch/POST at `pipeline_embedded.py:244`, `:250`, `:251` | `backend/pipeline_embedded.py:240-243` |
| GET | `{QAD_BASE_URL}` — **bare base URL, no API path, no auth header** | HTTP status code only; body discarded | `check_qad_reachable()` compares `resp.status_code < 500` and returns an OK/WARN health tile | `backend/core/health.py:162-177` (call at `:170`) |

[CONFIRMED] The health GET carries no credentials and requests no artifact. Its own docstring, `backend/core/health.py:163`: `"""QAD base URL reachable - a plain GET, NOT a login (no creds, no write)."""`

[CONFIRMED] Both `entitymetadatas` GETs are gated behind `if field_list_map:` (`backend/pipeline.py:510`, `backend/pipeline_embedded.py:235`) — they do not execute at all for a BC with no dropdown fields. The `entityURI` they target comes from `bc_data["entity_uri"]`, i.e. the payload AUX itself constructed and POSTed at step 3 (`backend/pipeline.py:513`). Comment at `backend/pipeline.py:505-506`: "We fetch the freshly-saved (enriched) entity metadata from QAD".

### A7.3 Verdict

**NO. AUX never reads existing event handler code back from QAD.** Not once, on any path.

Stated plainly and specifically:

1. [CONFIRMED] **No GET is ever issued against the `eventhandler` endpoint.** `eventhandler` appears exactly once as a network target in the whole backend — as a POST at `backend/pipeline.py:685`: `eh_result = await post_qad("eventhandler", eh_data["payload"], token)`. There is no `get_qad("eventhandler"...)` anywhere.

2. [CONFIRMED] **The handler payload is authored from scratch every run and is a full replace, not a merge.** `build_event_handler_payload(bc_pascal, ts_code, js_code)` (`backend/builders/event_handler_builder.py:6-48`) constructs a single-element `eventHandlerV2s` array with hardcoded `"eventHandlerType": "BEFORE"`, `"appliesTo": "WEB"`, `"isActive": True`, `"mappingCode": ""`, and sets `typeScriptCode`/`javaScriptCode` purely from its two string arguments. It takes no prior-state parameter and reads nothing.

3. [CONFIRMED] **Those two strings are LLM output, not fetched source.** `ts_code` comes from the `TS_CODE_WRITER` LLM call at `backend/pipeline.py:648`; `js_code` from the `TS_COMPILER` LLM call at `backend/pipeline.py:669-673`. The step 8 planner input is only the BC name, description and field JSON (`backend/pipeline.py:611-615`) — no existing-handler context is assembled or available.

4. [CONFIRMED] **No form/view metadata containing handler references is read back either.** `viewMetadataV2` (`:597`) and `viewResourceMetadatas` (`:709-712`) are POST-only. The one field that would carry handler references on the view payload, `"eventHandlerInfos"`, is hardcoded to an empty list in the outbound write — `backend/builders/embedded_builder.py:213`: `"eventHandlerInfos": [],`. It is never populated from a read.

5. [CONFIRMED] **The single genuine artifact read that does exist is a same-run read-back of AUX's own just-written entity**, restricted to dropdown wiring, and its response is consumed only for `dataListCode` and `defaultValue` (`backend/builders/bc_builder.py:109-110`). It is never pointed at a pre-existing, human-authored BC.

6. [CONFIRMED] **Duplicate-name handling is not a read.** AUX discovers that a BC already exists by POSTing and pattern-matching the rejection: `_is_duplicate_entity_error` does `return "already exist" in blob` over the flattened error messages (`backend/pipeline.py:226-231`). It then stops and tells the user to rename or "delete/rename the existing '{_bc}' in QAD first" (`backend/pipeline.py:450-454`). AUX cannot see what that existing BC contains.

7. [CONFIRMED] **`backend/qad_entity_registry.py` is a local static registry — it makes no network call of any kind.** Read in full (212 lines): no import of httpx/requests, no `qad_client` import. `_BUILTIN_ENTITIES` is a hand-maintained dict of five hardcoded entries (`:37-82`) — `SalesOrderHeaders`, `PurchaseOrderHeaders`, `ItemMaster`, `InventoryMaster`, `WorkOrderMaster` — each with a literal `uri`/`pk_fields`/`fk_field` typed into the source. Its own docstring names the durable source as the local DB, `:10-13`: "The DURABLE source of truth is the `parent_entities` table in the database". `hydrate()` (`:198-212`) merges rows from that table; `register_and_persist_custom_bc()` (`:164-195`) writes to it via `database.upsert_parent_entity`. The URIs in this file are transcribed from QAD by a human, per the "HOW TO ADD A NEW BUILT-IN ENTRY" instructions at `:17-24` — never fetched.

8. [CONFIRMED] **The frontend "Registered BCs" page is local history, not a QAD browse.** `RegisteredBCsPage.tsx:9` calls `fetchEntities()`, which is `GET /api/entities` (`frontend/src/features/client_ext/api.ts:137-147`). That backend route (`backend/routers/client_extensions.py:238-256`) returns `await list_parent_entities()` — a plain SQLite `SELECT * FROM parent_entities` (`backend/database.py:129-137`) — falling back to the in-memory `registry.all_entities()` at `:253-256`. The page's own copy confirms the scope, `RegisteredBCsPage.tsx:28-31`: "Parent entities a new **Embedded BC** can be built on… custom parents you create are registered here". [CONFIRMED] No frontend file talks to QAD directly — every `fetch()` in `frontend/src` targets `/api`, `/api/sss`, or `/api/auth`.

### A7.4 If NO: nearest extensible capability, and what is genuinely absent

**Nearest existing capability (three things already in place):**

1. [CONFIRMED] **A working authenticated GET helper.** `get_qad(endpoint, token)` (`backend/qad_client.py:64-69`) already handles Bearer auth, 60s timeout, and error-envelope normalisation via `_handle` (`:20-39`). Reading any `qracore` resource needs no new transport code — only a new endpoint string.

2. [CONFIRMED] **A proven GET→patch→POST round-trip pattern.** `backend/pipeline.py:513-532` is a complete, working read-modify-write cycle against `entitymetadatas`, including the `{"data": {...}}` unwrap idiom (`:521`) that QAD GETs require, and in-place mutation via a dedicated patch function (`backend/builders/bc_builder.py:98-111`). This is the exact shape a "read existing handler, amend, re-post" flow would take.

3. [CONFIRMED] **A schema-discovery precedent for existing components** — though file-based, not QAD-based. `backend/sss/discover.py` already models "inspect a component that someone else authored" and returns structured `name/namespace/module/fields/methods/with_confirmation` (`:49-65`), surfaced at `GET /api/sss/bcs` and `/api/sss/bcs/{name}` (`backend/routers/sss.py:55-79`).

**What is genuinely absent:**

- [CONFIRMED] Any GET against the `eventhandler` endpoint, and therefore any way to retrieve an existing `typeScriptCode` / `javaScriptCode` / `mappingCode` body.
- [CONFIRMED] Any read of `viewMetadataV2` or `viewResourceMetadatas`, so `eventHandlerInfos` on an existing view is never observed.
- [CONFIRMED] Any merge or amend semantics in the handler builder — `backend/builders/event_handler_builder.py` has no parameter for prior code and unconditionally emits one `BEFORE`/`WEB` handler.
- [CONFIRMED] Any listing/browse of BCs that exist in the QAD instance. Every "what exists" surface in AUX is fed by the hardcoded five-entry dict, the local `parent_entities` table, or local `.d.ts` files.
- [INFERRED] The `entitymetadatas` GET would very likely work against an arbitrary pre-existing `entityURI`, since nothing in `get_qad` or the call site special-cases newly created entities — the URI is just a query parameter. **What would confirm it:** one manual `get_qad("entitymetadatas?entityURI=<uri of a standard BC>&viewUri=…IEntityBuilderCRUD", token)` against a live instance, e.g. using the `urn:be:com.qad.base.item.IItem` URI already recorded at `backend/qad_entity_registry.py:59`. I have not executed this (read-only audit, and it would require live credentials).
- [INFERRED] Retrieving handler code probably requires a different endpoint and `viewUri` than the entity CRUD one — plausibly a GET on `eventhandler` filtered by the `viewURI` that `build_event_handler_payload` writes, `urn:view:viewmeta:com.extensions.customapp.{BcPascal}` (`backend/builders/event_handler_builder.py:8`). **What would confirm it:** capturing the QAD Event Handler screen's own GET from the browser Network tab — the same technique `backend/core/lookup_generator.py:50` documents for validating the lookup payload.

### A7.5 Separately: code that reads LOCAL files back (NOT a QAD read-back)

[CONFIRMED] These are filesystem reads. None contacts QAD, and none should be counted as a read-back of a deployed artifact.

| What is read | Source | Consumer | file:line |
|---|---|---|---|
| `lib/salesgen.d.ts`, `lib/purchasinggen.d.ts` — standard BC typedefs, parsed for namespaces/interfaces/fields/CRUD methods | Local `lib/` dir via `appconfig.lib_dir()` | `discover_bcs()` → `GET /api/sss/bcs`, `/api/sss/bcs/{name}`, and `generate_route` | `backend/sss/discover.py:154` (read), `:202-208` (paths), `:211-232`, `:235-239` |
| `dist/{script}dev.js`, `.js.map`, `.d.ts` — tsc output, read as bytes for multipart upload | Local `dist/` via `dist_files()` | `_upload()` outbound multipart body | `backend/sss/deploy.py:59`; `dist_files()` at `backend/sss/compile.py:49-53` |
| Exported QAD developer docs `.txt` — LLM prompt grounding | `QAD_DOCS_DIR` | `docs_loader.get_bundle("client_extension_event_handler")` at `backend/pipeline.py:619,642` | `backend/core/qad_docs_loader.py:94` |
| `settings.json` | Local | `core.config` accessors | `backend/core/config.py:80`, `:189` |
| `package.json` (version string) | Local | health tile | `backend/core/health.py:130` |
| User-supplied `.p` / `.cls` Progress source | Upload/paste | `parse_progress_file` → deterministic schema + lookup extraction | `backend/core/progress_parser.py:82` |
| `tsconfig.json` | Local | SSS scaffold | `backend/core/sss_scaffold.py:100` |

[CONFIRMED] The distinction matters most for `discover.py`: its docstring (`backend/sss/discover.py:4-6`) says it parses typedefs that "QAD SSS: Update app dependency" **downloaded** into `lib/` — i.e. a *different tool* (the VS Code extension) fetched them from QAD; AUX only reads the resulting files off disk. [CONFIRMED] It also yields field/method signatures only — there is no handler-code or handler-body content in that data model (`BusinessComponent` dataclass, `:49-61`).

---

## A8. Frontend architecture and reusability for a step-gated approval UI

**Scope read in full:** all 28 files under `frontend/src/**`, plus `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html` (on-disk state), and — for the transport/step questions — `backend/routers/client_extensions.py`, `backend/pipeline.py`, `backend/pipeline_embedded.py`, `backend/core/progress_parser.py`.

---

### A8.0 Headline corrections to the commissioning brief

Three premises in the brief are contradicted by the files. Stating these first because they change the Phase 1/2 plan.

| Premise | Verdict | Evidence |
|---|---|---|
| "The commissioner says Zustand" | **FALSE. There is no Zustand in this project at all.** | `frontend/package.json:10-14` lists exactly three runtime deps: `react`, `react-dom`, `react-router-dom`. A repo-wide grep for `zustand` across `package.json`, `package-lock.json`, `frontend/src/**` and `frontend/node_modules/` returns **zero matches**. |
| "`authStore.tsx` — if it is actually React Context rather than Zustand, say so" | **It is React Context.** The file says so in its own header comment. | `frontend/src/features/auth/authStore.tsx:1-4` |
| "`backend/core/progress_parser.py` relates to ProgressPanel" | **FALSE. Pure name collision.** `progress_parser.py` parses **OpenEdge Progress 4GL / ABL source code** (`.p` / `.cls` files). It has nothing to do with UI progress, steps, or SSE. | `backend/core/progress_parser.py:1-15` docstring: *"Parses OpenEdge Progress ABL .p and .cls files to extract schema information for BC generation."* |

`authStore.tsx:1-4` verbatim [CONFIRMED]:

```
// AuthContext — same behavioural shape as the spec's `authStore` (login,
// logout, init, token, email) but implemented as a React Context because the
// codebase already uses hooks + localStorage everywhere (see App.tsx's
// `feature` state — same try/catch pattern). No Zustand added.
```

---

### A8.1 App shell + routing

**Routing is a two-route shell; there is no per-feature route.** [CONFIRMED]

`frontend/src/main.tsx:13-34` — `BrowserRouter` → `AuthProvider` → `Routes` with exactly three entries:

- `main.tsx:18` — `<Route path="/login" element={<LoginPage />} />`
- `main.tsx:19-26` — `<Route path="/*" element={<ProtectedRoute><App /></ProtectedRoute>} />`
- `main.tsx:29` — `<Route path="*" element={<Navigate to="/" replace />} />`

`react-router-dom@^6.30.4` is a real dependency (`package.json:13`) but is used **only** for the login gate and for `useNavigate` on sign-out (`Sidebar.tsx:19,21-23`) and login (`LoginPage.tsx:13,25,48`). **No URL exists for any in-app view.** Settings, Registered BCs, a history item, and the SSS flow are all at path `/`. [CONFIRMED — the `View` union in `ClientExtPanel.tsx:11-17` is `useState`, never a route.]

**Feature switching is a persisted `useState` toggle, not routing.** [CONFIRMED]

- `App.tsx:18-26` — `feature` state seeded from `localStorage.getItem("apex_active_feature")`, accepting only `"client-extensions" | "server-side-rules"`, defaulting to `"client-extensions"`.
- `App.tsx:28-35` — `changeFeature(next)` sets state and writes the same localStorage key.
- `Header.tsx:9` — `export type FeatureKey = "client-extensions" | "server-side-rules"`; `Header.tsx:11-14` — `FEATURE_OPTIONS` maps them to labels `"Client Extensions"` / `"Server-Side Rules"`.
- `Header.tsx:40-45` — the header renders `<SegmentedToggle options={FEATURE_OPTIONS} value={feature} onChange={onFeatureChange} ariaLabel="Active feature" />`.

**Both panes stay mounted; only CSS `display` toggles.** [CONFIRMED] `App.tsx:81-91` renders both `.feature-pane` divs unconditionally, adding `" active"` to the current one. `index.css:128-136`: `.feature-pane { display: none; … } .feature-pane.active { display: flex; }`. The stated reason (`App.tsx:12-14`, `index.css:121-122`) is that an in-progress CE run survives a feature switch.

**`SegmentedToggle` is genuinely generic and used in two places.** [CONFIRMED] `SegmentedToggle.tsx:23-48` is generic over `<T extends string>`, renders `role="tablist"` / `role="tab"` with `aria-selected`. Consumers: `Header.tsx:40-45` (feature switch) and `ClientExtPanel.tsx:220-228` (Standard BC / Embedded BC mode). The older `.mode-toggle` CSS class was deleted in favour of it (`index.css:738`, `index.css:1428` both carry removal comments).

**Navigation to settings / registered BCs is via sidebar callbacks that set the `View` union.** [CONFIRMED] `Sidebar.tsx:17` props include `onSettings`, `onEntities`, `onNew`, `onSelect`; `ClientExtPanel.tsx:196-203` wires them to `setView({kind:"settings"})` / `setView({kind:"entities"})`. Rendered at `ClientExtPanel.tsx:334` and `:337`.

**Login/logout.** `ProtectedRoute.tsx:13-19` renders a `.auth-loading` spinner while `initializing`; `:22` `if (!token) return <Navigate to="/login" replace />`. Sign-out lives in the CE sidebar only (`Sidebar.tsx:164-173` → `handleSignOut` at `:20-23` → `logout()` + `nav("/login", {replace:true})`). **There is no sign-out control in the SSS pane or the header** [CONFIRMED — `Header.tsx:29-50` renders brand, toggle, and a `right` slot which `App.tsx:74-79` fills with `<HealthChip>` only].

**Theme.** Owned by `App.tsx:44-60`; pre-paint bootstrap in `index.html:17-31` sets `data-theme` on `<html>` from `localStorage["apex-theme"]` before first paint. `App.tsx:44-47` reads that attribute back so React's first render matches.

**`index.html` uncommitted change is cosmetic only.** [CONFIRMED] `git diff frontend/index.html` shows a single line: `<title>APEX-Transform</title>` → `<title>ApexTransform</title>` (`index.html:6`). No script, no mount, no CSP change.

---

### A8.2 STATE — every store, enumerated

**There is exactly ONE store-like abstraction in the entire frontend, and it is React Context.** Everything else is component-local `useState`/`useRef`. There is no persist middleware anywhere (no library provides one; persistence is three hand-rolled `localStorage` calls). [CONFIRMED]

#### Store 1 (and only) — `frontend/src/features/auth/authStore.tsx`

- **Mechanism:** `createContext` (`:37`) + `AuthProvider` component (`:56-110`) + `useAuth()` hook (`:112-116`, throws `"useAuth must be used inside <AuthProvider>"` when unmounted).
- **State shape** (`:24-28`):
  | key | type | source |
  |---|---|---|
  | `token` | `string \| null` | `:57` `useState(() => readStoredToken())` |
  | `email` | `string \| null` | `:58` |
  | `initializing` | `boolean` | `:59`, true until `init()` completes |
- **Context value** adds (`:30-35`): `login: (email, password) => Promise<string \| null>` (returns `null` on success, error message on failure), `logout: () => void`.
- **Actions:**
  - init — `useEffect` at `:65-87`, guarded by `initRan` ref (`:60`) against StrictMode double-invoke. Reads stored token, validates via `apiMe(stored)`, clears it on failure.
  - `login` — `:89-96`, `useCallback`; calls `apiLogin`, sets `token`/`email`, `writeStoredToken`.
  - `logout` — `:98-102`, clears both and the storage key.
  - value memoised at `:104-107`.
- **Persistence:** hand-rolled, not middleware. `STORAGE_KEY = "apex_token"` (`:22`); `readStoredToken` (`:39-45`) and `writeStoredToken` (`:47-54`) both wrap `localStorage` in try/catch and swallow errors.

#### Non-store persisted keys [CONFIRMED]

| key | written at | read at |
|---|---|---|
| `apex_token` | `authStore.tsx:49-50` | `authStore.tsx:41` |
| `apex_active_feature` | `App.tsx:31` | `App.tsx:20` |
| `apex-theme` | `App.tsx:52` | `App.tsx` reads the DOM attr at `:45`; `index.html:20` reads the key |

Note the inconsistent naming: two underscore keys and one hyphen key.

#### All other state, by owner (component-local, dies with unmount) [CONFIRMED]

- `App.tsx` — `feature` (`:18`), `health: HealthReport \| null` (`:39`), `theme` (`:44`). Derived: `sssSetup` (`:66`) = `health?.checks.find(c => c.docs_url && c.status !== "ok") ?? null`.
- `ClientExtPanel.tsx:42-57` — `view: View` (union at `:11-17`), `input`, `running`, `refreshTick`, `activeHistoryId`, `mode: "standard"|"embedded"`, `pipelineSummary`, `attachedFile: {name, content} | null`; refs `summaryRef`, `abortRef`, `bottomRef`, `textareaRef`.
- `SssPanel.tsx:21-36` — `bcs`, `loadError`, `selected`, `bcDetail`, `detailLoading`, `detailError`, `prompt`, `generating`, `gen`, `editedTs`, `deploying`, `deployResult`, `error`.
- `Sidebar.tsx:24-27` — `items`, `hoveredId`, `deletingId`, `isCollapsed`.
- `SettingsPage.tsx:30-37` — `status`, `form`, `saving`, `saved`, `testing`, `conn`.
- `BcPicker.tsx:32-33` — `query`, `fieldQuery`. `HealthChip.tsx:31` — `state`. `HealthPanel.tsx:20` — `showGuide`. `RegisteredBCsPage.tsx:5-6` — `entities`, `error`. `LoginPage.tsx:15-18` — `email`, `password`, `submitting`, `error`.

**Consequence for Phase 2:** SSS pane state (`selected`, `prompt`, `gen`, `editedTs`) survives a feature switch **only** because `App.tsx:81-91` keeps both panes mounted — it is not persisted. A reload loses it. [CONFIRMED]

---

### A8.3 How the client-extension run is driven — the transport

**Initiator:** `ClientExtPanel.handleSubmit()` (`ClientExtPanel.tsx:73-164`), called from the send button (`:446`) or Enter-without-Shift (`:176-181`).

**Transport: server-sent-events *format* delivered over a POST `fetch` body, hand-parsed with a `ReadableStream` reader. It is NOT `EventSource`, not polling, not WebSocket.** [CONFIRMED] `features/client_ext/api.ts:68-121`. Verbatim, `api.ts:78-83` and `:99-110`:

```ts
      const resp = await fetch(`${BASE}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, mode }),
        signal: controller.signal,
      });

      const reader = resp.body!.getReader();
```

```ts
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          if (buf.trim()) parseAndFire(buf);
          break;
        }
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) parseAndFire(part);
      }
```

Frame parsing (`api.ts:89-97`): trims, requires the literal prefix `"data: "`, `JSON.parse(line.slice(6))`, and **silently swallows parse failures** (`catch (_) {}`). Cancellation: `streamPipeline` returns `() => controller.abort()` (`api.ts:120`), stored in `abortRef` (`ClientExtPanel.tsx:95`) and called by `handleNew` (`:64`) and `handleSelectHistory` (`:167`).

`EventSource` was necessarily avoided because the request is a POST with a JSON body. [INFERRED — the code never says why; the constraint is intrinsic to `EventSource` being GET-only. Confirmable only by asking the author.]

**Server side** (`backend/routers/client_extensions.py:117-212`): `@router.post("/api/run")` with `@limiter.limit("5/minute")` (`:118`), returning `StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})` (`:205-212`). `event_stream()` (`:148-203`) simply `async for chunk in pipeline_gen: yield chunk` (`:168-169`) over `run_pipeline(...)` / `run_embedded_pipeline(...)` (`:158-166`), then emits a terminal `run_id` frame (`:203`).

**Event vocabulary — frontend type vs. what the backend actually emits.** [CONFIRMED]

Frontend union, `client_ext/api.ts:5-15`: `type: "step" | "error" | "complete" | "run_id"`, plus optional `step`, `total`, `name`, `status: "running"|"done"|"error"`, `message`, `summary`, `error`, `run_id`.

Backend emits **three additional types the frontend type does not declare and no component renders**:
- `"warning"` — `client_extensions.py:156`, `yield f"data: {json.dumps({'type': 'warning', 'message': w})}\n\n"` (Progress-parser warnings, emitted before step 1).
- `"lookup_candidate"` — `pipeline.py:81-89`.
- `"lookup_needs_review"` — `pipeline.py:93-103` and `:106-114`.

These fall through `ClientExtPanel.tsx:131-136`'s "normal step event" branch (they are appended to `events` and force a re-render) and are then **dropped** by `ProgressPanel.tsx:51-58`, which only reads `e.type === "step"`. **Parser warnings and every lookup finding are currently invisible in the UI.** [CONFIRMED — no component in `frontend/src/**` references `"warning"`, `"lookup_candidate"`, or `"lookup_needs_review"`.]

**How `ProgressPanel` learns about step progress.** [CONFIRMED] It does **not** subscribe to anything. It is a pure function of props (`ProgressPanel.tsx:39-45`): `{ events: SSEEvent[]; errorEvent?: SSEEvent; mode?: "standard"|"embedded" }`. On every render it rebuilds a `stepMap` from scratch (`:46`, `:51-58`):

```ts
  for (const e of events) {
    if (e.type === "step" && e.step) {
      stepMap[e.step] = { status: e.status as StepState["status"], message: e.message };
    }
  }
```

Last-write-wins per step number; nothing is stored between renders. `ClientExtPanel.tsx:132-136` pushes a fresh array (`{...prev, events: [...events]}`) on each event so the panel re-renders.

**Step labels are hardcoded in the frontend and duplicated from the backend — and they have already drifted.** [CONFIRMED]

- `ProgressPanel.tsx:3-18` `STANDARD_STEP_NAMES` (14 entries) is currently **character-identical** to `backend/pipeline.py:145-160` `STEP_LABELS`.
- `ProgressPanel.tsx:20` `STANDARD_VISIBLE_STEPS = [1, 2, 3, 5, 7, 9, 11, 13, 14]` — steps 4, 6, 8, 10, 12 are **never rendered** even though the backend emits them (`pipeline.py:458,555,609,667,696`). Step 4 has a second guard at `ProgressPanel.tsx:68`: `if (n === 4 && status === "pending") return null;` — dead code, since 4 is not in the visible list.
- `ProgressPanel.tsx:22-30` `EMBEDDED_STEP_NAMES` has **7** entries; `backend/pipeline_embedded.py:32-41` `STEP_LABELS` has **8**. Step 8 `"Registering standalone view in QAD"` is emitted by the backend and **cannot be displayed** (`EMBEDDED_VISIBLE_STEPS = [1..7]`, `ProgressPanel.tsx:32`). Three labels also disagree:

  | # | backend (`pipeline_embedded.py`) | frontend (`ProgressPanel.tsx`) |
  |---|---|---|
  | 1 | `Understanding Embedded BC requirements` (:33) | `Understanding requirements for Embedded BC` (:23) |
  | 4 | `Handling duplicates & auto-fix` (:36) | `Handling duplicates & Retrying` (:26) |
  | 5 | `Building relations to parent entity` (:37) | `Building relations to parent order` (:27) |

  The backend *does* send the authoritative label on every frame — `_evt` sets `"name": STEP_LABELS.get(step, "")` (`pipeline.py:169`, `pipeline_embedded.py:51`) — but `ProgressPanel` **ignores `e.name` entirely** except in the error box (`:94`). The drift is therefore user-visible.

**Backend event frame shape** (`pipeline.py:163-177`), which any step-gated design must extend:

```python
def _evt(type_: str, step: int = 0, status: str = "running",
         message: str = "", summary: Any = None, error: str = "") -> str:
    d: Dict[str, Any] = {
        "type": type_, "step": step, "total": TOTAL_STEPS,
        "name": STEP_LABELS.get(step, ""), "status": status, "message": message,
    }
    if summary is not None: d["summary"] = summary
    if error: d["error"] = error
    return f"data: {json.dumps(d)}\n\n"
```

**There is no pause point anywhere.** [CONFIRMED] `run_pipeline` (`pipeline.py:381`) is a one-shot `AsyncGenerator` with 58 `yield _evt(...)` sites; a grep for `approve|approval|pause|resume|await_input|gate` across `backend/pipeline.py` and `backend/routers/client_extensions.py` returns exactly one hit — the word "gate" in an unrelated comment about `tsc` (`pipeline.py:654`). The generator runs start-to-finish inside a single HTTP response. The **only** control the client has is `controller.abort()`, which kills the run outright.

**Step outputs are never stored.** [CONFIRMED] The only persisted artefact is the terminal `summary` (`client_extensions.py:185-197` builds `HistoryItem` with `summary_json=json.dumps(summary)`). No per-step spec, panel plan, or generated TS is written to the DB or returned to the client for review. `ClientExtPanel` keeps `events` in a local array that is discarded by `handleNew` (`:65`).

---

### A8.4 The SSS approval UI — the closest existing template

`SssPanel` is a **three-step wizard rendered all at once in a 2-column grid**, with a genuine human-in-the-loop approval gate between generation and deployment. This is the nearest thing in the codebase to the Phase 2 target. [CONFIRMED]

**Layout** (`SssPanel.tsx:107-143`): `.sss-panel` (grid `1fr 1.15fr`, `sss.css:7-15`, collapsing to one column under 900px at `sss.css:16-18`) containing `.sss-col-group` with `BcPicker` + `RulePrompt` stacked in the left column, and `ReviewDeploy` occupying the right column. All three steps are visible simultaneously — steps are **disabled**, never hidden.

**Step 1 — `BcPicker.tsx`.** A deliberately custom listbox rather than `<select>` (`BcPicker.tsx:4-9` explains why: a filter that hides the selected option would swallow the next click). `:35-38` filters `bcs` by lowercase substring; `:61-77` renders `role="listbox"` with `role="option"` + `aria-selected`. Below it, once `bcDetail` loads, a field browser (`:88-119`) with its own filter (`:96-101`) and clickable chips (`:102-117`) that call `onInsertField(f.name)` — which appends the exact case-sensitive field name into the rule prompt via `SssPanel.insertField` (`SssPanel.tsx:61-63`, with space-normalisation). `shortType()` (`:21-27`) abbreviates `string→str`, `number→num`, `boolean→bool`, `Date→date`.

**Step 2 — `RulePrompt.tsx`.** 45 lines. A single textarea (`:27-37`) disabled unless `selected`, whose placeholder seeds an example from the BC's first field: `` `e.g. "block save if ${bcDetail.fields[0]?.name} is empty"` `` (`:31`). Gate at `:19`: `const canGenerate = !!selected && !!prompt.trim() && !generating;`. Button label flips to `"Generating…"` (`:40`). **This is the free-text-instruction control the Phase 2 "regenerate with free text" flow needs — it already exists, correctly gated.**

**Step 3 — `ReviewDeploy.tsx`.** The approval gate proper. Three mutually exclusive render branches driven by `deployed` (`:31`, `deployResult?.success === true`) and `gen`:

1. **Error card** (`:40-48`), always rendered above the branches when `error` is non-empty. `role="alert"`, title `"Couldn't generate a valid rule"`, body `{error}` verbatim from the backend. The header comment (`:3-11`) states the design rule explicitly: inline card using `--status-error`, *"never a toast/console"*, and it carries the exact offending field names from the backend's field-guard 422.
2. **Deployed** (`:50-62`) — 🚀, `"Deployed to QAD"`, the raw server log in `<pre className="sss-server-log">`, and an `"Add another rule"` button → `onReset`.
3. **Review** (`:63-101`) — the approval surface:
   - `.sss-summary` block (`:65-77`): heading **"What this enforces"**, the model's plain-English `gen.summary`, and a `"Runs on:"` badge row mapping `gen.methods` (`:72-74`).
   - Code header (`:79-82`): `{gen.file_name}` on the left, the literal hint `"editable before deploy"` on the right.
   - **An editable `<textarea className="sss-code">` bound to `editedTs`** (`:83-88`, `spellCheck={false}`). The user can hand-edit the generated TypeScript before approving. `sss.css:269-286` styles it monospace, `white-space: pre`, `min-height: 320px`, `resize: vertical`, `tab-size: 4`.
   - **Three actions** (`:90-100`), all disabled while `deploying`:
     | label | handler | parent implementation |
     |---|---|---|
     | `"Approve & Deploy"` / `"Compiling & deploying…"` | `onDeploy` | `SssPanel.tsx:81-92` |
     | `"Regenerate"` | `onRegenerate` | wired to **`onGenerate`** — `SssPanel.tsx:140` |
     | `"Discard"` | `onDiscard` | `SssPanel.tsx:94-97` |
4. **Placeholder** (`:102-108`) when neither `gen` nor `error`.

**Critically: what "Approve & Deploy" sends is the *edited* text, not the generated text.** `SssPanel.tsx:85` — `const r = await deploy(selected, editedTs);`. `editedTs` is seeded from `g.ts` at generation time (`:73`) and thereafter owned by the textarea. [CONFIRMED]

**Transport is plain request/response — no streaming in SSS.** [CONFIRMED] `features/sss/api.ts:85-99`:

```ts
export const listBcs = () => req<SssBcSummary[]>("/bcs");
export const getBc = (name: string) => req<SssBcDetail>(`/bcs/${encodeURIComponent(name)}`);
export const generate = (bc_name: string, prompt: string) =>
  req<SssGenerateResult>("/generate", { method: "POST", body: JSON.stringify({ bc_name, prompt }) });
export const deploy = (bc_name: string, ts: string) =>
  req<SssDeployResult>("/deploy", { method: "POST", body: JSON.stringify({ bc_name, ts }) });
```

Base is `/api/sss` (`sss/api.ts:3`). Payload keys are exactly `{bc_name, prompt}` and `{bc_name, ts}`.

**Response shapes** (`sss/api.ts:31-43`):
- `SssGenerateResult` = `{ ts: string; summary: string; methods: string[]; validation_code: string; file_name: string }`. Note `validation_code` is **declared but never read by any component** [CONFIRMED — no reference in `ReviewDeploy.tsx` or `SssPanel.tsx`].
- `SssDeployResult` = `{ success: boolean; compile: {success, log, dist[]}; deploy: {success, status, response, files[]} }`. Only `deploy.response` is rendered (`ReviewDeploy.tsx:58`); **`compile.log` is never shown, even on failure.** [CONFIRMED]

**Error handling** (`sss/api.ts:52-83`): `req<T>` throws `SssApiError` (`:50`) on non-2xx, unwrapping FastAPI's `{detail: string | {message}}` (`:71-80`), and converts network failure into `"Cannot reach the backend (…). Is it running?"` (`:59-61`). `SssPanel` catches into a single `error` string (`:75-76`, `:87-88`).

**Race-condition guard worth copying** (`SssPanel.tsx:45-59`): the BC-detail effect resets all downstream state, then uses an `active` flag closure so an out-of-order response can never populate fields belonging to a stale selection.

**Gap vs. the Phase 2 target:** this is a **single** approval gate at the end of a **synchronous** generate call. There is no notion of step *N of M*, no resume token, no way to feed free-text back in *scoped to one step* — "Regenerate" re-runs the whole `generate(selected, prompt)` with the same prompt unless the user first edits the step-2 textarea, and it **discards any hand-edits to `editedTs`** (`SssPanel.tsx:73` overwrites it on every successful generate). [CONFIRMED]

---

### A8.5 `SettingsPage.tsx` (feeds Phase 1)

**What it edits:** exactly **two** free-text fields. Everything else is read-only status. [CONFIRMED] The header comment (`SettingsPage.tsx:10-19`) states the principle: *"Secrets never reach the browser"*, sourced from `core.config.public_status()`.

**Read** — `SettingsPage.tsx:39-46`, `fetchSettings()` → `GET /api/settings` (`shared/api.ts:54-58`). Response `SettingsStatus` (`shared/api.ts:28-38`), 9 keys:

| key | type | rendered as |
|---|---|---|
| `qad_base_url` | `string` | read-only value, `:123` |
| `qad_username` | `string` | read-only value, `:128` |
| `qad_app_uri` | `string` | **never rendered** [CONFIRMED] |
| `qad_app_dir` | `string` | **editable input**, `:140-144` |
| `openai_model` | `string` | **editable input**, `:149-153` |
| `auto_deploy` | `boolean` | **never rendered** [CONFIRMED] |
| `has_openai_key` | `boolean` | `<StatusRow>` dot, `:100` |
| `has_qad_password` | `boolean` | `<StatusRow>` dot, `:101` |
| `qad_configured` | `boolean` | `<StatusRow>` dot, `:102` |

On load it copies two keys into local form state: `setForm({ qad_app_dir: s.qad_app_dir, openai_model: s.openai_model })` (`:43`).

**Write** — `handleSave` (`:53-67`) calls `saveSettings({ qad_app_dir: form.qad_app_dir, openai_model: form.openai_model })` (`:56-59`) → `POST /api/settings`, `Content-Type: application/json`, body = that object (`shared/api.ts:61-69`). **The POST payload is exactly two keys**, even though the declared `UiSettingsUpdate` type (`shared/api.ts:42-47`) permits four optional keys: `qad_app_uri?`, `qad_app_dir?`, `openai_model?`, `auto_deploy?`. The response is the refreshed `SettingsStatus`, which is re-seeded into both `status` and `form` (`:60-61`). Success feedback: `setSaved(true)` + `setTimeout(() => setSaved(false), 3000)` (`:62-63`) rendering `"✓ Saved"` (`:160`).

**Connection test** — `handleTest` (`:69-77`) → `testConnection()` → `GET /api/sss/connection` (`shared/api.ts:74-93`). Never throws; always resolves to `ConnectionResult = {ok: boolean; message: string}` (`shared/api.ts:49-52`), handling the structured 503 `detail.message` (`:84-88`).

**Notable weaknesses for Phase 1** [CONFIRMED]:
- `fetchSettings().catch(() => {})` (`:45`) — a failed load leaves `status === null` forever, so the page renders `"Loading configuration…"` (`:79-86`) with **no error state and no retry**.
- `handleSave` has `try/finally` but **no `catch`** (`:54-66`) — `saveSettings` throws on non-2xx (`shared/api.ts:67`), producing an unhandled rejection and a silent no-op for the user. The spinner clears; nothing else happens.
- There is no dirty-state guard and no validation on either field.

---

### A8.6 REUSABLE vs NOT — blunt two-column judgement

#### ✅ Reuse as-is or with light extension

| Asset | Why it carries a step-gated flow |
|---|---|
| `SegmentedToggle.tsx:23-48` | Generic over `<T extends string>`, correct `tablist`/`tab`/`aria-selected` semantics, token-styled. Drop-in for a step-status filter or a per-step mode switch. **Zero changes needed.** |
| `ReviewDeploy.tsx:63-101` (the review branch) | **This is the Phase 2 template.** Summary + "what this enforces" + editable artefact + `Approve / Regenerate / Discard` triad, all disabled during the in-flight action. Generalise `gen`/`editedTs` from one artefact to a per-step artefact and it fits. |
| `ReviewDeploy.tsx:40-48` + `sss.css:187-217` | Inline `role="alert"` error card carrying the backend's verbatim message. The stated no-toast convention is right for a gated UI where the error must persist next to the thing that failed. |
| `RulePrompt.tsx` (whole file, 45 lines) | Already *is* the "free-text instruction + gated submit" control. Rename props, bind to a step id, done. |
| `BcPicker.tsx:102-117` (chips → `onInsertField`) + `SssPanel.tsx:61-63` | Click-to-insert-exact-token into a free-text box. Directly reusable for "insert field name into your regenerate instruction". |
| `SssPanel.tsx:45-59` | The `active`-flag stale-response guard. **Mandatory to copy** — a step-gated UI issues far more per-step fetches than this one does. |
| `authStore.tsx` (whole) | Context + hook + hand-rolled persist works and is only ~117 lines. It is *not* a general store, but it does not need to be. |
| `shared/design-tokens.css` (whole) | Genuine single source of truth. New UI must consume it. |
| `sss.css` scoping discipline (`sss.css:1-5`) | `.sss-` prefix on every class prevents collision with the unscoped CE stylesheet. **Adopt the same prefixing for any new pane.** |
| `HealthChip.tsx:35-37, 38-61` | The `onReportRef` pattern (ref-latched callback so the poll effect never re-subscribes) is the correct idiom and will be needed for any per-step poll. |
| `App.tsx:81-91` + `index.css:128-136` | Keep-both-mounted pane strategy. Preserves in-flight work across a feature switch — useful, keep. |

#### ❌ Structurally in the way — must be replaced

| Blocker | Evidence | What it forces |
|---|---|---|
| **Fire-and-forget single-shot run.** `run_pipeline` is one `AsyncGenerator` inside one `StreamingResponse`; the only client control is `abort()`. | `client_extensions.py:168-169, 205-212`; `pipeline.py:381`; `client_ext/api.ts:120`. Grep for pause/approve/resume across pipeline + router: **zero hits**. | **Blocking rewrite.** A step-gated UI needs the run to be a resumable server-side resource — either a per-step request/response loop (SSS-style, per step) or a run with a durable state row that a `POST /api/run/{id}/step/{n}/approve` can advance. Streaming-with-a-pause is the hard version; per-step request/response is the version this codebase already knows how to build. |
| **No step-output storage.** Only the terminal `summary` is persisted. | `client_extensions.py:185-197` (`summary_json` only); `HistoryItem` at `client_ext/api.ts:42-54` has no per-step field. | Nothing to *show* at a gate and nothing to regenerate *from*. Needs a new per-step artefact store keyed by `(run_id, step)` before any UI work starts. |
| **`ProgressPanel` is a stateless display of a flat event log.** Rebuilds `stepMap` from scratch each render; no per-step artefact, no actions, no pending/approved distinction, `errorEvent` is a single prop not a per-step field. | `ProgressPanel.tsx:46, 51-58, 60-101` | Rewrite. Salvage the visual vocabulary (`.step-row`/`.step-icon`/`.step-label`/`.step-message`, `index.css:825-890`) and the four-state `StepState` (`:34-37`), then extend to `pending | running | awaiting_approval | approved | rejected | error` with a per-step expandable body. |
| **Hardcoded, already-drifted step tables.** Frontend duplicates backend labels and ignores the `name` the backend sends on every frame. Embedded step 8 is unrenderable; three embedded labels disagree. | `ProgressPanel.tsx:3-18, 20, 22-32` vs `pipeline.py:145-160` and `pipeline_embedded.py:32-41`; label ignored at `ProgressPanel.tsx:83` (uses local `stepNames[n]`) | Delete `STANDARD_STEP_NAMES` / `EMBEDDED_STEP_NAMES` / the `VISIBLE_STEPS` arrays. Render from a backend-supplied step manifest (the `name` + `total` fields already exist in the frame). A gated UI cannot ship with the client and server disagreeing about what step 5 is. |
| **`ClientExtPanel` is a 455-line god component.** 8 `useState` + 4 `useRef`, the whole SSE callback tree, four render branches, plus two nested presentational components. | `ClientExtPanel.tsx:42-57, 73-164, 210-337, 345-454` | Extract run orchestration into a hook/reducer before adding gates. Adding 14 pause points to this file directly will not survive review. |
| **`View` union has no room for a gate; no URL for any view.** | `ClientExtPanel.tsx:11-17`; `main.tsx:18-29` (two routes only) | A user cannot link to, bookmark, or reload back into "run X paused at step 7". Needs either a `{kind:"awaiting", runId, step}` variant plus routes, or a real route table. |
| **The `running` boolean is the entire run lifecycle.** | `ClientExtPanel.tsx:44`; input bar hard-disabled while running (`:256-265`, placeholder `"Pipeline running…"` at `:414`) | A gated run is *paused, not running* — the user must be able to type at exactly the moment this flag currently locks the input. Replace with a status enum. |
| **Fragile summary recovery.** `summaryRef` + a `fetchHistory()` "last resort" that grabs `items[0]` and assumes it is this run. | `ClientExtPanel.tsx:49-51, 101-103, 137-162` (`const latest = items[0]`) | Symptomatic of the stream being the only source of truth. Once step outputs are server-stored and fetchable by `run_id`, delete this entirely. |
| **Silent event loss.** Unknown frame types are dropped; malformed frames are swallowed by `catch (_) {}`. | `client_ext/api.ts:95`; `ProgressPanel.tsx:52`; `warning`/`lookup_candidate`/`lookup_needs_review` unrendered (`client_extensions.py:156`, `pipeline.py:81-114`) | An approval UI must never silently discard a frame — a dropped `awaiting_approval` frame would hang the run with no user-visible cause. Needs an explicit exhaustive switch with a visible fallback. |
| **No auth on any data call.** `Authorization: Bearer` appears at exactly **one** site in the whole frontend. | `features/auth/api.ts:53` (only). `client_ext/api.ts`, `sss/api.ts`, `shared/api.ts` send **no** token. Backend confirms: only `/api/auth/me` uses `Depends(auth.get_current_user)` (`backend/routers/auth.py:69`); `sss.py:38`'s `GATED = [Depends(ensure_ready)]` is a **readiness** gate (`backend/sss/readiness.py:52-56`), not auth. | Login is decorative — `ProtectedRoute` is client-side only and every `/api/*` endpoint is open. **An approve/deploy action is a privileged mutation; shipping a gate without a server-side identity check is worse than no gate.** Fix before Phase 2. |
| **`SettingsPage` has no error path.** | `SettingsPage.tsx:45` (`.catch(() => {})`), `:53-67` (no `catch`) | Phase 1 must add load-failure and save-failure states. |

---

### A8.7 Styling system — conventions new UI must follow

**Cascade** [CONFIRMED]: `main.tsx:4` imports `./index.css` once, globally. `index.css:1` pulls Inter + Outfit from Google Fonts; `index.css:7` `@import './shared/design-tokens.css';`. Feature stylesheets are imported by their panel: `sss.css` at `SssPanel.tsx:9`, `login.css` at `LoginPage.tsx:9`. **There is no CSS-Modules, no CSS-in-JS, no Tailwind, no PostCSS config** — global stylesheets with class-name discipline only.

**`design-tokens.css` is the contract.** `:1-14` states it: *"This file is the single source of truth… New components MUST consume these tokens: no hardcoded hex, no inline styles."* Structure:
- `:root` (`:16-140`) — dark values. Palette `:18-33` (`--bg`, `--sidebar-bg`, `--border`, `--text`, `--text-muted`, `--text-dim`, `--accent: #8b5cf6`, `--input-bg`, `--hover`, `--success`, `--error`, `--warning`, `--running`, `--pill-bg`, `--tag-primary`, `--tag-text`); derived `--accent-soft-border` (`:37`); logo chevrons (`:40-41`); surfaces `--surface-1/2/3`, `--border-strong` (`:44-47`); **status aliases `--status-ok`/`--status-warn`/`--status-error`/`--status-neutral` (`:51-53`)**; `--on-accent` (`:56`).
- Typography `:59-82` — `--font-body`/`--font-display`/`--font-mono`; sizes `--fs-2xs` (10px) … `--fs-display` (40px); weights, `--lh-tight`/`--lh-base`, `--ls-caps`/`--ls-label`.
- Spacing `:85-97` — `--space-2` … `--space-40`. Radius `:100-112` — `--radius-xs` … `--radius-pill`/`--radius-circle`. Shadows `:115-120`. Motion `:123-134` — `--dur-xfast` … `--dur-spin`, `--ease-out`/`--ease-standard`. Z-index `:137-139` — `--z-base:1`, `--z-raised:10`, `--z-sticky:100`.
- `[data-theme="light"]` (`:143-178`) re-points **the same token names** to light values. **Theming is therefore automatic for any component that only uses `var(--*)`.**

**`design-tokens.css:180-237` is a documented "INTERACTIVE PATTERN REFERENCE"** — a comment block naming, for each pattern, the existing element it derives from and its exact rest/hover/disabled recipe: PRIMARY BUTTON (`.send-btn`/`.save-btn`), SECONDARY BUTTON (`.new-run-btn`/`.settings-btn`), DANGER, SEGMENTED TOGGLE, STATUS DOT/CHIP, CARD/PANEL, INPUT FIELD, FOCUS-RING GLOW, LOADING, ERROR STATE, ENTRANCE. **New UI should be written against this block rather than by copying arbitrary existing CSS.**

**Rules a new step-gated pane must follow:**
1. Token-only. No hex, no inline styles.
2. Prefix every class with a feature namespace, per `sss.css:1-5`. The CE stylesheet is unscoped and its class names (`.step-row`, `.summary-card`, `.error-box`) are global — collisions are real.
3. Status colour goes through `--status-*` (`design-tokens.css:51-53`), never `--success`/`--error` directly.
4. Errors are inline cards with `role="alert"`, not toasts (`ReviewDeploy.tsx:3-11`, `sss.css:187-217`).
5. Card recipe: `background: var(--input-bg); border: 1px solid var(--border); border-radius: var(--radius-12)`, hover → `border-color: var(--accent)` + `translateY(-2px)` + `--shadow-pop` (`design-tokens.css:216-219`; live at `.health-setup-card`, `index.css:178-190`).
6. Focus: no OS outline — use `--glow-accent` (`design-tokens.css:226-227`).
7. Responsive: single breakpoint precedent at 900px (`sss.css:16-18`).

**The convention is already violated in the legacy CE stylesheet.** [CONFIRMED] `index.css` contains hardcoded colours that will not theme, including `.step-row.running { background: #1a1a1a; }` (`:849`), `.error-box` `background: #1a0000; border: 1px solid #5a0000` (`:894-895`), `.error-box-msg { color: #e57373 }` (`:907`), `.field-group input:focus { border-color: #555 }` (`:1272`), `.save-btn:hover { background: #ccc }` (`:1344`), scrollbar `#333`/`#444` (`:1378-1379`), `.detail-failed` `#1a0000`/`#5a0000`/`#e57373` (`:1395-1401`). Light mode compensates with a `[data-theme="light"]` override block (`index.css:1409+`, e.g. `:1431-1443`) — i.e. the same colour is specified twice in two places instead of once as a token. **New components must not extend this pattern**, and the light-mode override block is the thing to delete if `.step-row` is ever retokenised. There are also inline `style={{...}}` props in TSX, contrary to `Header.tsx:27`'s stated rule — e.g. `ProgressPanel.tsx:79, 81`, `ClientExtPanel.tsx:277, 312`, `SummaryCard.tsx:46, 107, 111, 114`.

---

---

## A9. Docs-bundle loader and LLM prompt assembly

### A9.1 The exact mechanism

**[CONFIRMED] There is exactly one loader:** `backend/core/qad_docs_loader.py` (130 lines total). It defines one class `QADDocsLoader` and one module-level singleton `docs_loader = QADDocsLoader(config.QAD_DOCS_DIR)` (`backend/core/qad_docs_loader.py:129`).

**[CONFIRMED] Keying is by *bundle name string* → *list of directory basenames*.** There is no enum, no artifact-type class, no step-id mapping, no filename convention. The whole key space is a hardcoded dict literal at `backend/core/qad_docs_loader.py:46-64`:

```python
    # bundle name -> immediate-parent folder names (as found under QAD_DOCS_DIR)
    BUNDLES: Dict[str, List[str]] = {
        "client_extension_event_handler": [
            "UI Event Handlers",
            "UI elements list of events and Properties_Functions",
            "Platform Scripting - TypeScript",
            "TypeScript recommended coding standards",
        ],
        "server_side_rule": [
            "Server scripting using TypeScript",
            "Setting up a server scripting development environment",
            "Platform Scripting - TypeScript",
            "TypeScript recommended coding standards",
        ],
        "business_component": [
            "Business Components - Form Builder",
            "App Development Concepts",
            "Platform Scripting - TypeScript",
        ],
    }
```

**[CONFIRMED] Discovery + read + grouping** — `load()` at `backend/core/qad_docs_loader.py:73-104`. Core lines verbatim (`:90-104`):

```python
        file_count = 0
        grouped: Dict[str, List[str]] = {}
        for txt in sorted(self._docs_dir.rglob("*.txt")):
            try:
                content = txt.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.warning("Skipping unreadable docs file %s: %s", txt, exc)
                continue
            grouped.setdefault(txt.parent.name, []).append(content)
            file_count += 1

        self._cache = {folder: "\n\n".join(parts) for folder, parts in grouped.items()}
        self._loaded = True
```

Mechanics, all [CONFIRMED] from those lines:
- **Glob:** `rglob("*.txt")` — recursive, `.txt` only. Any other extension (`.md`, `.pdf`, `.json`) is invisible to the loader.
- **Order:** `sorted(...)` over full paths — deterministic, lexicographic by path.
- **Encoding:** `utf-8, errors="replace"` — a bad byte becomes U+FFFD, never an exception.
- **Filter:** none beyond the `*.txt` glob. No size filter, no per-file cap, no content filter.
- **Grouping key:** `txt.parent.name` — the *immediate parent directory basename*, flattened across the whole tree. Depth is discarded.
- **Concatenation (intra-folder):** `"\n\n".join(parts)`.
- **Truncation / chunking:** **none anywhere in the file.** There is no slice, no `[:N]`, no chunker, no summariser.

**[CONFIRMED] Assembly** — `get_bundle()` at `backend/core/qad_docs_loader.py:106-122`:

```python
        try:
            if not self._loaded:
                return ""
            folders = self.BUNDLES.get(bundle_name)
            if not folders:
                logger.warning("Unknown docs bundle requested: %s", bundle_name)
                return ""
            return "\n\n".join(self._cache[f] for f in folders if f in self._cache)
        except Exception as exc:
            logger.warning("get_bundle(%s) failed: %s", bundle_name, exc)
            return ""
```

Bundle text = folders concatenated in **BUNDLES-list order**, `"\n\n"`-joined. A folder name in BUNDLES that does not exist on disk is **silently skipped** (`if f in self._cache`, `:119`) — no warning, no error. An unknown *bundle name* logs a WARNING and returns `""` (`:117-118`).

**[CONFIRMED] Path resolution** — `_resolve_docs_dir()` at `backend/core/qad_docs_loader.py:31-36`: relative values resolve against `_BACKEND_DIR` (= `backend/`, computed at `:28`). `.env` sets `QAD_DOCS_DIR=./qad_docs` (`backend/.env:15`; same default in `backend/.env.example:41`), so the effective dir is `backend/qad_docs/`.

**[CONFIRMED] When it loads:** once, at FastAPI startup — `docs_loader.load()` inside a `try/except` at `backend/main.py:197`, imported at `backend/main.py:28`. Never reloaded; there is no watcher and no reload endpoint anywhere in the tree.

**[CONFIRMED] Fail-soft:** unset dir → WARNING + `_loaded=False` (`:83-85`); missing dir → WARNING + `_loaded=False` (`:86-88`). `get_bundle()` then returns `""` and the prompt simply gets an empty docs block.

#### On-disk convention (measured)

- **[CONFIRMED]** `backend/qad_docs/` top level = **53 directories + 1 loose file** (`QAD Enterprise Platform Developers Guide - March 2023.txt`, 2626 bytes). Directory names are human-readable Confluence page/section titles with spaces, hyphens and `_` (e.g. `UI elements list of events and Properties_Functions`).
- **[CONFIRMED]** Inside a directory: flat `.txt` files, one per Confluence page. No nesting was observed in the 8 bundle folders inspected. Example: `backend/qad_docs/UI Event Handlers/` holds 5 files (`Event handlers API reference.txt` 89,924 B, `Event handlers _How To_.txt`, `Handling grid events.txt`, `TypeScript Best Practices.txt`, `TypeScript recommended coding standards.txt`).
- **[CONFIRMED]** Corpus totals: **285 `.txt` files, 1,242,281 bytes, 54 distinct parent-folder keys** (53 dirs + the key `qad_docs` for the loose top-level file). This matches `PROGRESS.md:198` ("285 .txt files, 54 folders") and `PROGRESS.md:208` (`docs_folder_count=54`).
- **[CONFIRMED]** No two directories anywhere in the tree share a basename (`find -type d -printf "%f\n" | sort | uniq -d` returned empty), so the flat basename-keyed cache currently has **no collisions**. This is a property of the current data, not an invariant the code enforces.

**[CONFIRMED] File format** (read end-to-end: all 3 files of `backend/qad_docs/Server scripting using TypeScript/`). Each file is plain text with a 3-line comment header then flattened Confluence prose:

```
# TITLE: Developing and deploying server scripts
# PAGE ID: 378516250
# URL: https://team.qad.com/spaces//pages/378516250

Introduction
 These pages describe how to develop server scripts:
 ...
```

Body lines are single-space-indented, tables are flattened to one cell per line (see `TypeScript recommended coding standards/Never use var.txt`, which renders a Summary table as `ID` / `TYPESCRIPT-0004` / `Version` / `1` on consecutive lines). Images become `[IMAGE:image2021-2-3_13-58-34.png]` markers. Code blocks are fenced with ```` ```js ````. **No YAML front-matter, no JSON, no per-file metadata beyond the 3 header lines.**

### A9.2 Caching, size cap, token budget

| Question | Answer | Citation |
|---|---|---|
| Caching | **Yes** — one in-process `Dict[str, str]` `self._cache`, folder-basename → concatenated text, populated once at startup | `backend/core/qad_docs_loader.py:70`, `:101`, `backend/main.py:197` |
| Cache invalidation / reload | **None.** No mtime check, no TTL, no reload route. (Contrast: `core/config.py` *does* do mtime-based live re-read, `backend/core/config.py:57-67` — the docs loader deliberately does not; see the comment at `backend/core/config.py:151-153`) | — |
| Per-bundle memoisation | **No** — `get_bundle()` re-joins the strings on every call (`:119`) | `backend/core/qad_docs_loader.py:119` |
| Size cap on docs | **None.** No byte cap, no file cap, no folder cap, no truncation | whole of `backend/core/qad_docs_loader.py` |
| Token budget / counting | **None.** `tiktoken` is not imported anywhere; no token estimate is computed before injection | grep over `backend/` |
| Output-token cap | `max_tokens = 15000`, applied **only** when the model id does not start with `gpt-5` | `backend/pipeline.py:187-188` |
| Output-token cap (SSS) | **None** — `client.chat.completions.create` is called with no `max_tokens` | `backend/sss/generate.py:127-134` |

**[CONFIRMED] Measured bundle sizes** (sum of `.txt` bytes in the folders each bundle lists):

| Bundle | Folders | Files | Bytes |
|---|---|---|---|
| `client_extension_event_handler` | 4 | 27 | **243,273** |
| `server_side_rule` | 4 | 15 | **49,466** |
| `business_component` | 3 | 22 | **90,956** |

Per-folder: `UI Event Handlers` 99,013 B / 5 files; `UI elements list of events and Properties_Functions` 116,999 B / 14; `Platform Scripting - TypeScript` 20,387 B / 3; `TypeScript recommended coding standards` 6,874 B / 5; `Server scripting using TypeScript` 3,319 B / 3; `Setting up a server scripting development environment` 18,886 B / 4; `Business Components - Form Builder` 47,694 B / 7; `App Development Concepts` 22,875 B / 12.

**[INFERRED]** At the usual ~4 bytes/token English heuristic that is roughly **61k input tokens for `client_extension_event_handler`, 12k for `server_side_rule`, 23k for `business_component`, injected in full on every single call.** The CE bundle is injected twice per standard run (steps 8 and 9, `backend/pipeline.py:619` and `:642`), i.e. ~120k input tokens of docs per BC run. Confirming this exactly requires running a tokenizer over the concatenated bundle — nothing in the repo does that today.

### A9.3 Complete list of bundle keys and their consumers

**[CONFIRMED] Three keys exist. There are exactly 5 `get_bundle(...)` call sites** (verified by grep across `backend/`, excluding `qad_docs/`):

| Bundle key | Consumed at | Pipeline / step | Prompt it lands in |
|---|---|---|---|
| `client_extension_event_handler` | `backend/pipeline.py:619` | Standard BC pipeline, **step 8** "Planning event handler logic" (`backend/pipeline.py:154`) | `EVENT_HANDLER_PLANNER` |
| `client_extension_event_handler` | `backend/pipeline.py:642` | Standard BC pipeline, **step 9** "Writing event handler code" (`backend/pipeline.py:155`) | `TS_CODE_WRITER` |
| `business_component` | `backend/pipeline_embedded.py:76` (via `_docs_context()`, `:24-27`) | Embedded BC pipeline, **step 1** "Understanding Embedded BC requirements" (`backend/pipeline_embedded.py:34`) | `EMBEDDED_REQUIREMENTS_GATHERING` |
| `business_component` | `backend/pipeline_embedded.py:123` (via `_docs_context()`) | Embedded BC pipeline, **step 2** "Designing Embedded BC fields" (`backend/pipeline_embedded.py:35`) | `EMBEDDED_FIELD_CREATOR` |
| `server_side_rule` | `backend/sss/generate.py:118` | SSS (Server-Side Rules) flow — not a numbered step; single call from `POST /api/sss/generate` (`backend/routers/sss.py:83-95`) | `SYSTEM_PROMPT` in `backend/sss/generate.py:28-70` |

**[CONFIRMED] Absence findings worth stating plainly:**
- `business_component` is **never used by the standard 14-step pipeline** — only by the embedded pipeline. The standard pipeline's `FIELD_CREATOR`/`REQUIREMENTS_GATHERING` get **zero docs grounding**.
- No bundle is consumed by any router, builder, or health module. `core/health.py:142-159` (`check_qad_docs`) only checks that the *directory* exists; it never resolves a bundle.
- `config.public_status()` exposes `docs_loaded` and `docs_folder_count` (`backend/core/config.py:180-181`) — note `docs_folder_count` reaches into the private `docs_loader._cache` and counts **folders (54), not bundles (3)**. Grep found **no frontend consumer** of `docs_loaded` / `docs_folder_count`.
- There is **no unit test for the loader**. The only `*_test.py` files under `backend/` are `core/lookup_detector_test.py` and `core/progress_parser_test.py`. Nothing asserts that the folder names in `BUNDLES` exist on disk.

### A9.4 How bundle text reaches the model

**[CONFIRMED] Slot: always the SYSTEM message.** The docs block is `str.replace`-substituted into the system prompt string, which is passed as `system` and becomes `{"role": "system", ...}`:

```python
# backend/pipeline.py:180-192
async def _llm(client: AsyncOpenAI, system: str, user: str,
               model: str = MODEL_MATRIX["generation"], json_mode: bool = False) -> str:
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
```

**[CONFIRMED] The wrapper text is duplicated in 3 places, not centralised.** All three produce the identical header, `""` when the bundle is empty:
- `backend/pipeline.py:620-623` (step 8) and `:643-646` (step 9): `f"## QAD Platform Reference Docs\n\n{bundle}" if bundle else ""`
- `backend/pipeline_embedded.py:24-27`: the only named helper, `_docs_context(bundle_name)`
- `backend/sss/generate.py:119-122`: same f-string inline

**[CONFIRMED] Substitution is `str.replace`, never `str.format`** — deliberate, because the prompts contain literal `{` braces (JSON shapes, TS module blocks). Comments say so at `backend/pipeline.py:641`, `backend/pipeline_embedded.py:72-73`, `backend/sss/generate.py:117`. All 5 substitution sites: `backend/pipeline.py:624`, `:647`; `backend/pipeline_embedded.py:76`, `:123`; `backend/sss/generate.py:123`.

**[CONFIRMED] Template variables that actually exist (the complete set):**

| Variable | Declared in | Substituted at | Value |
|---|---|---|---|
| `{QAD_DOCS_CONTEXT}` | `backend/agents/prompts.py:225`, `:254`, `:403`, `:456`; `backend/sss/generate.py:36` | `pipeline.py:624`, `:647`; `pipeline_embedded.py:76`, `:123`; `sss/generate.py:123` | `## QAD Platform Reference Docs\n\n<bundle>` or `""` |
| `{ENTITY_MENU}` | `backend/agents/prompts.py:406` | `backend/pipeline_embedded.py:77` | `entity_menu_for_prompt()` from `qad_entity_registry` |

**[CONFIRMED] `{BCName}`, `{fieldName}`, `{panelNumber}` in `TS_CODE_WRITER` (`backend/agents/prompts.py:259-266`, `:294`, `:326`, `:329`, `:338`, `:362-364`) are NOT template variables.** Grep for `BCName` across `backend/**/*.py` returns hits only inside `agents/prompts.py` — nothing ever replaces them. They are literal placeholders the model is instructed to fill in.

#### Full prompt inventory — `backend/agents/prompts.py` (on-disk state, including uncommitted edits)

10 module-level constants. All are used as the **system** message.

| # | Constant (line) | Purpose | Consumed by | Model tier | JSON mode | Docs context |
|---|---|---|---|---|---|---|
| 1 | `REQUIREMENTS_GATHERING` (`:5`) | 4GL/plain-English → plain-text requirements summary | Standard step 1, `pipeline.py:409` (skipped entirely when `parsed_requirements` came from the Progress parser, `pipeline.py:401-406`) | `planning` = gpt-4o-mini | no | **none** |
| 2 | `FIELD_CREATOR` (`:38`) | Summary → `{"status","spec":{bc_pascal,description,fields[]}}` | Standard step 2, `pipeline.py:419` | `generation` = gpt-4o | yes | **none** |
| 3 | `VALIDATOR_AND_CORRECTOR` (`:100`) | QAD error + spec → `{"status":"fixed"|"failed"}` auto-fix | Standard step 4, `pipeline.py:465`. Imported but **never called** in `pipeline_embedded.py` (import at `:10`, no call site) | `generation` | yes | **none** |
| 4 | `FORM_PLANNER` (`:158`) | Fields JSON → plain-text panel plan | Standard step 5, `pipeline.py:546` | `planning` | no | **none** |
| 5 | `FORM_FIELD_BUILDER` (`:184`) | Panel plan → `{"placements":[…]}` grid layout | Standard step 6, `pipeline.py:362` inside `_build_placements()`; retried once at `pipeline.py:573` | `generation` | yes | **none** |
| 6 | `EVENT_HANDLER_PLANNER` (`:218`) | BC spec → plain-text handler plan | Standard step 8, `pipeline.py:625` | `planning` | no | **`client_extension_event_handler`** |
| 7 | `TS_CODE_WRITER` (`:247`) | Plan + placements → QAD TS event handler | Standard step 9, `pipeline.py:648` | `generation` | no | **`client_extension_event_handler`** |
| 8 | `TS_COMPILER` (`:389`) | TS → ES5 JS (one-line prompt) | Standard step 10, `pipeline.py:669` | `compile` = gpt-4o-mini | no | **none** |
| 9 | `EMBEDDED_REQUIREMENTS_GATHERING` (`:391`) | Request → parent entity + child PK + custom fields JSON | Embedded step 1, `pipeline_embedded.py:79-82` | `generation` | yes | **`business_component`** |
| 10 | `EMBEDDED_FIELD_CREATOR` (`:453`) | Requirements + FK info → 3-PK field spec JSON | Embedded step 2, `pipeline_embedded.py:125-128` | `generation` | yes | **`business_component`** |

Plus one prompt **outside** `prompts.py`: **[CONFIRMED]** `SYSTEM_PROMPT` at `backend/sss/generate.py:28-70` — SSS record-level validation writer, consumed at `backend/sss/generate.py:127-134`, model = `config.openai_model()`, JSON mode on, docs = `server_side_rule`. This is the only prompt not centralised in `agents/prompts.py`, despite that file's header claiming "single place to edit them" (`backend/agents/prompts.py:1-3`).

**[CONFIRMED] Uncommitted diff in `prompts.py`:** `git diff --stat` = 16 insertions / 9 deletions, **entirely within `FORM_FIELD_BUILDER`** (output shape changed from a bare JSON array to `{"placements":[…]}`, plus a COMPLETENESS-IS-MANDATORY rule). **No docs-injection code was touched by the uncommitted change.**

### A9.5 OpenAI model / API surface / params

**[CONFIRMED] API surface: `client.chat.completions.create` only.** Exactly two call sites in the whole backend:

**(a) BC pipelines — async.** `backend/pipeline.py:180-192` (quoted above). Client constructed at `backend/pipeline.py:396` and `backend/pipeline_embedded.py:63`, both identically:

```python
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

- Model: from `MODEL_MATRIX`, `backend/pipeline.py:136-140`:
  `{"planning": "gpt-4o-mini", "generation": "gpt-4o", "compile": "gpt-4o-mini"}`
- `temperature`: **never set** — no `temperature` key appears in `kwargs` (`backend/pipeline.py:182-190`) [CONFIRMED].
- `max_tokens`: `15000`, guarded by `if not model.startswith("gpt-5")` (`backend/pipeline.py:187-188`).
- `response_format`: `{"type": "json_object"}` only when the caller passes `json_mode=True` (`backend/pipeline.py:189-190`).
- Retries/timeout: **not specified** at the call site or constructor. [INFERRED] the SDK defaults apply — verified in the *installed* package `openai==1.59.6`: `DEFAULT_TIMEOUT = httpx.Timeout(timeout=600.0, connect=5.0)`, `DEFAULT_MAX_RETRIES = 2` (`site-packages/openai/_constants.py:9-10`). Note `requirements.txt:3` pins `openai==1.55.3` while the interpreter has 1.59.6 — a version drift worth flagging.
- **No application-level retry wrapper.** An exception propagates to the step's `try/except`, which emits an SSE `error` event and `return`s (e.g. `backend/pipeline.py:627-629`, `:650-652`).

**(b) SSS — sync.** `backend/sss/generate.py:127-134`:

```python
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )
```

- Client: `OpenAI(api_key=key, timeout=90.0, max_retries=4)` — `backend/sss/generate.py:86`, imported lazily at `:83`.
- Model: `appconfig.openai_model()` → `config.openai_model()` → `OPENAI_MODEL` env, **default `"gpt-4o"`** (`backend/core/config.py:90`, `backend/sss/appconfig.py:45-46`). `backend/.env.example:32` sets `OPENAI_MODEL=gpt-4o`. Overridable at runtime via `settings.json` — `openai_model` is in `_UI_KEYS` (`backend/core/config.py:34`, `:106-109`).
- `temperature`: **never set** [CONFIRMED]. `max_tokens`: **never set** [CONFIRMED]. `response_format`: always JSON mode.

**[CONFIRMED] Key source is inconsistent:** the BC pipelines read `os.getenv("OPENAI_API_KEY")` directly (`backend/pipeline.py:396`, `backend/pipeline_embedded.py:63`), bypassing `core.config`; SSS goes through `config.openai_api_key()` (`backend/sss/generate.py:78`). `backend/core/config.py:16-18` documents this as intentional back-compat (`main.py` also calls `load_dotenv()`).

**[CONFIRMED] Rate limits at the HTTP edge:** `POST /api/run` is `@limiter.limit("5/minute")` with the comment "each run spawns 8 LLM calls" (`backend/routers/client_extensions.py:117-118`); `POST /api/sss/generate` is `@limiter.limit("10/minute")` (`backend/routers/sss.py:83-84`).

### A9.6 EXACTLY what adding a NEW bundle type involves

**[CONFIRMED] Four things must change; nothing else exists to change.** There is no enum, no registry, no schema, no migration, no test fixture, no frontend list, and no health check tied to bundle names. Step-by-step:

1. **Put the docs on disk.** Create `backend/qad_docs/<Folder Name>/` (or several) containing `.txt` files.
   - The extension **must** be `.txt` — `rglob("*.txt")`, `backend/core/qad_docs_loader.py:92`. `.md`/`.json`/`.pdf` are invisible.
   - The **directory basename must be globally unique** across the whole `qad_docs/` tree, because grouping is by `txt.parent.name` (`backend/core/qad_docs_loader.py:98`). Reusing an existing basename silently merges two unrelated folders into one cache key.
   - Nesting is allowed but pointless: only the immediate parent name becomes the key, so `A/B/x.txt` keys under `B`, not `A/B`.
   - [INFERRED] the 3-line `# TITLE: / # PAGE ID: / # URL:` header is convention only — the loader does not parse or require it. Confirmed by the absence of any header parsing in `load()`.

2. **Add the key to `BUNDLES`** — `backend/core/qad_docs_loader.py:46-64`. Insert one entry, e.g. after the `business_component` block ending at `:63`:
   ```python
       "java_extension": [
           "<Folder Name 1>",
           "<Folder Name 2>",
       ],
   ```
   Order in this list is the concatenation order in the final prompt (`:119`). **A misspelled folder name here fails silently** — `if f in self._cache` drops it with no log.

3. **Add the `{QAD_DOCS_CONTEXT}` placeholder to the target prompt.** Either a new constant in `backend/agents/prompts.py` (follow `EVENT_HANDLER_PLANNER`'s pattern — the placeholder sits on its own line at `backend/agents/prompts.py:225`), or a new prompt module like `backend/sss/generate.py:36`. The placeholder text must be exactly `{QAD_DOCS_CONTEXT}` — matching is literal `str.replace`.

4. **Wire the call site.** Three lines at whichever pipeline step consumes it:
   ```python
   bundle = docs_loader.get_bundle("java_extension")
   docs_context = f"## QAD Platform Reference Docs\n\n{bundle}" if bundle else ""
   system = MY_PROMPT.replace("{QAD_DOCS_CONTEXT}", docs_context)
   ```
   plus `from core.qad_docs_loader import docs_loader` (pattern: `backend/pipeline.py:13`, `backend/pipeline_embedded.py:21`, `backend/sss/generate.py:22`). If the new step lives in `pipeline_embedded.py` the helper already exists — just call `_docs_context("java_extension")` (`backend/pipeline_embedded.py:24-27`). **Use `.replace`, not `.format`** — `.format` will raise `KeyError` on the literal `{` braces in the prompt bodies.

**[CONFIRMED] What you do NOT need to touch:**
- `backend/core/config.py` — no per-bundle config; `QAD_DOCS_DIR` already covers it (`:97`, `:145`, `:154`).
- `backend/main.py` — `docs_loader.load()` (`:197`) picks up new folders automatically at next startup.
- `backend/core/health.py:142-159` — directory-existence check only, bundle-agnostic.
- `backend/.env` / `.env.example` — unchanged (`./qad_docs`).
- Frontend — nothing consumes bundle names.
- Tests — none exist for this module.

**[CONFIRMED] Consequences to plan for:** a restart is mandatory (no hot reload); `docs_folder_count` in `/api/health` will increase by the number of new folders (`backend/core/config.py:181`); and the new bundle's full byte weight is added to every call of the consuming step, with no cap.

**[INFERRED] Recommended (not currently present) hardening:** a startup assertion that every folder named in `BUNDLES` exists in `_cache`, logged once. Right now a renamed docs folder degrades the prompt to silence. Confirming that this is genuinely absent: I grepped `BUNDLES` across the repo — only `qad_docs_loader.py:46`, `:115`, and a `PROGRESS.md:194` description.

### A9.7 Coupling between the docs bundle and the SSS/TypeScript case

**[CONFIRMED] There is no Java anything in the backend today.** `grep -rin "java" backend/**/*.py` (excluding the word "javascript") returns **zero** hits, and no `qad_docs/` folder name contains "java". Any Java bundle is greenfield.

The TypeScript coupling that a Java analogue would have to mirror:

1. **[CONFIRMED] Bundle contents are TS-specific by construction.** `server_side_rule` (`backend/core/qad_docs_loader.py:54-58`) is 4 folders, all TypeScript: `Server scripting using TypeScript`, `Setting up a server scripting development environment`, `Platform Scripting - TypeScript`, `TypeScript recommended coding standards`. `client_extension_event_handler` (`:47-52`) likewise ends with `Platform Scripting - TypeScript` + `TypeScript recommended coding standards`. A Java bundle needs its own folder set — none of these four are language-neutral, and `TypeScript recommended coding standards` would actively mislead a Java writer.

2. **[CONFIRMED] The consuming prompts hardcode TS syntax and toolchain rules**, so the docs bundle alone cannot be swapped:
   - `backend/sss/generate.py:54-55`: "TypeScript target is ES6 (tsc 3.5). Use const/let, ===, template literals. No optional chaining (?.), no nullish coalescing (??)."
   - `backend/sss/generate.py:41-42`: field access `rec.FieldName`, error reporting `this.addValidationError(...)`.
   - `backend/agents/prompts.py:256-277`: a fixed TS `module … { }` / `export class … extends QraViewFormTSHandlerV2<…>` skeleton.
   - `backend/agents/prompts.py:280-333`: 11 numbered "CRITICAL API RULES" naming `.Value` (capital V), `viewField.Name`, `blockUIAndDoHttpPost`, `doHttpGet`, `DisplayMessageManager.showFlashMessage`, `Qad.Qracore.Service.Context.QraContextManager.getDomain()`.
   - `backend/agents/prompts.py:369-378`: a FORBIDDEN list of TS-specific mistakes.

3. **[CONFIRMED] Downstream of the docs-grounded call, the toolchain is TS-only:**
   - `check_typescript_syntax(ts_code)` gate at `backend/pipeline.py:657`, implemented in `backend/core/ts_compiler.py` — shells out to `tsc`, tolerates TS2xxx type errors, fails on TS1xxx syntax errors (`backend/core/ts_compiler.py:1-22`).
   - Step 10 "compiles" TS→ES5 with an LLM (`backend/pipeline.py:669-673`, prompt `backend/agents/prompts.py:389`).
   - SSS wraps the LLM's validation body in deterministic TS via `build_sss()` (`backend/sss/generate.py:180-185`, `backend/sss/templates.py:26-40`); the LLM "only produces the *validation body*" (`backend/sss/templates.py:4-5`).
   - Workspace scaffolding pins `typescript@3.5` (`backend/core/health.py:133-138`, `backend/core/sss_scaffold.py`).

4. **[CONFIRMED] Model selection differs between the two docs consumers.** The CE pipeline uses `MODEL_MATRIX` (`backend/pipeline.py:136-140`); SSS deliberately uses the single `config.openai_model()` — comment at `backend/pipeline.py:134-135`: "The SSS pipeline keeps using config.openai_model() because SSS is intentionally one-model." A Java flow must pick one of these two conventions explicitly.

5. **[CONFIRMED] Output-shape contract differs too.** SSS asks for strict JSON `{methods, validation_code, summary, fields_used}` (`backend/sss/generate.py:63-69`) and then hard-validates every `rec.X` reference against real BC fields, raising `GenerationError` on a hallucinated field (`backend/sss/generate.py:160-167`). `TS_CODE_WRITER` by contrast returns raw code with no JSON envelope (`backend/agents/prompts.py:380-386`). A Java analogue needs a decision on which contract it follows — the SSS field-validation guard is the stronger pattern and is language-independent in spirit.

6. **[CONFIRMED] `docs/BC_PROMPT_TEMPLATE.md` is user-facing and does not mention docs grounding at all.** It documents the two BC prompt templates, the supported field types (`docs/BC_PROMPT_TEMPLATE.md:30-45`), the step counts ("Standard BC (14 steps)" `:149`, "Embedded BC (7-8 steps)" `:157`), and a troubleshooting table (`:167-173`). It contains **no** reference to `QAD_DOCS_DIR`, bundles, or `{QAD_DOCS_CONTEXT}`. **Note a discrepancy:** `:151-155` numbers the standard pipeline "1, 2, 3, 3.5, 5-13, 14" — it lists no step 4; the code does have a step 4 ("Fixing errors automatically", `backend/pipeline.py:149`) which only runs when step 3 fails. Also `:153` labels dropdown wiring "3.5" while the code emits it as step **3** events (`backend/pipeline.py:511`, `:540`) — there is no 3.5 on the wire.

---

---

I have everything needed. Writing the audit section.

## A10. Current settings/config mechanism (Phase 1 baseline)

### A10.1 Config layering and precedence

**[CONFIRMED]** There are exactly **two** config files, not five layers. There is **no DB settings layer** and **no UI-override layer separate from `settings.json`**. `backend/core/config.py:1-19` states the contract:

```
Reads two files and merges them with clear precedence:
  1. backend/.env          - secrets + environment-specific values (machine/QA/prod)
  2. backend/settings.json - non-secret, UI-editable overrides
```

**[CONFIRMED] Effective precedence (highest wins), from `_merged()` at `backend/core/config.py:86-122`:**

| Rank | Source | Applies to | Citation |
|---|---|---|---|
| 1 (wins) | `settings.json` keys in `_UI_KEYS` | `qad_base_url`, `qad_app_uri`, `openai_model`, `auto_deploy` — only when value is not `None`/`""` | `backend/core/config.py:106-109` |
| 2 | `backend/.env` values | all 12 merged keys | `backend/core/config.py:88-104` |
| 3 | hardcoded literal defaults in `_merged()` | `openai_model` → `"gpt-4o"`; everything else → `""`; `auto_deploy` → `False` | `backend/core/config.py:90`, `:103` |
| 4 (last resort) | `settings.json` **legacy** key names | only when the resolved value is blank/whitespace | `backend/core/config.py:110-121` |

Verbatim precedence logic, `backend/core/config.py:105-121`:

```python
    # settings.json overrides for UI-editable, non-secret keys only.
    s = _settings()
    for k in _UI_KEYS:
        if k in s and s[k] not in (None, ""):
            cfg[k] = s[k]
    legacy = {
        "qad_base_url": s.get("qad_server_url"),
        "qad_client_id": s.get("qad_client_id"),
        "qad_username": s.get("qad_username"),
        "qad_password": s.get("qad_password"),
    }
    for k, v in legacy.items():
        if not str(cfg.get(k) or "").strip() and v:
            cfg[k] = v
```

**[CONFIRMED] The legacy fallback can inject secrets from `settings.json`.** `qad_password`, `qad_username`, `qad_client_id` are read from `settings.json` under `qad_password` / `qad_username` / `qad_client_id` whenever `.env` is blank (`backend/core/config.py:113-121`). `settings.json` is git-tracked (see A10.4) — so this path is a live secret-in-git hazard even though today's file contains no such keys.

**[CONFIRMED] `dotenv_values()` vs `os.environ` — both are used, on different paths, and they disagree.**

- `backend/core/config.py:27` imports `from dotenv import dotenv_values`; `backend/core/config.py:70-74` reads the file directly:
  ```python
  def _env() -> Dict[str, str]:
      return _read_cached(
          ENV_PATH, _env_cache,
          lambda p: {k: v for k, v in dotenv_values(p).items() if v is not None},
      )
  ```
  `ENV_PATH = _BACKEND_DIR / ".env"` where `_BACKEND_DIR = Path(__file__).resolve().parent.parent` (`backend/core/config.py:29-30`). **`dotenv_values` never consults `os.environ`.**
- `backend/main.py:19` separately calls `load_dotenv(Path(__file__).parent / ".env")` to populate `os.environ` "for legacy consumers" (`backend/main.py:16-18`).
- Direct `os.environ`/`os.getenv` consumers that bypass `core.config` entirely: `backend/main.py:68` (`ALLOWED_ORIGINS`), `backend/pipeline.py:396` (`os.getenv("OPENAI_API_KEY")`), `backend/pipeline_embedded.py:63` (`os.getenv("OPENAI_API_KEY")`).

**[CONFIRMED] The Docker trap is real and present in this repo.** `docker-compose.yml:13-14` supplies config only via `env_file: backend/.env`, i.e. into the **container environment**. But `.dockerignore:13-15` excludes the file from the build context:

```
# Secrets — never bake into image
backend/.env
**/.env
```

`Dockerfile:27` does `COPY backend/ .` into `WORKDIR /app` (`Dockerfile:20`), so `/app/.env` **does not exist** in the image. Inside the container `config.py` lives at `/app/core/config.py`, so `_BACKEND_DIR` = `/app` and `ENV_PATH` = `/app/.env`. `_read_cached` returns `{}` when `mtime is None` (`backend/core/config.py:60-67`). **Net effect: in Docker every `core.config` accessor (`qad_base_url()`, `qad_username()`, `qad_password()`, `qad_client_id()`, `openai_api_key()`, `apex_jwt_secret()`, …) returns `""`, while `os.getenv("OPENAI_API_KEY")` in `pipeline.py:396` and `os.environ.get("ALLOWED_ORIGINS")` in `main.py:68` work fine.** Login (`core/auth.py:41`), QAD OAuth (`core/qad_session.py:47-49`) and health (`core/health.py:63`) would all report unconfigured. `settings.json` is *not* in `.dockerignore`, so it **is** baked into the image and its three keys still apply.

**[CONFIRMED] Live pickup / no-restart behaviour.** `_read_cached` re-parses a file only when its `st_mtime` changes (`backend/core/config.py:57-67`), and `save_ui_settings` forces `_settings_cache["mtime"] = None` after writing (`backend/core/config.py:196`). So `.env` and `settings.json` edits are picked up without a restart **for `core.config` consumers only** — `os.environ` consumers (`pipeline.py:396`, `pipeline_embedded.py:63`, `main.py:68`) are snapshotted at process start and **do** require a restart.

**[CONFIRMED] One value is snapshotted at import time:** `QAD_DOCS_DIR = qad_docs_dir()` at `backend/core/config.py:154`, with the rationale in `backend/core/config.py:151-153`.

### A10.2 Complete key inventory

**[CONFIRMED]** Every key below was read from the cited file. "UI editable" means reachable through `POST /api/settings` **and** actually persisted by `save_ui_settings`.

| Key (merged name) | Env var | Type | Default | Where read (declaration) | Consumers | In `.env` today | In `settings.json` today | UI editable? |
|---|---|---|---|---|---|---|---|---|
| `openai_api_key` | `OPENAI_API_KEY` | str | `""` | `core/config.py:89` | `core/config.py:130`, `sss/appconfig.py:41-42`, `sss/generate.py:78`; **bypass:** `pipeline.py:396`, `pipeline_embedded.py:63` | yes (line 1, non-empty) | no | **No** (secret) |
| `openai_model` | `OPENAI_MODEL` | str | `"gpt-4o"` | `core/config.py:90` | `core/config.py:131`, `sss/appconfig.py:45-46`, `sss/generate.py:86` | **no** | **yes** = `"gpt-5-mini"` (`backend/settings.json:4`) | **Yes** |
| `qad_base_url` | `QAD_BASE_URL` | str | `""` | `core/config.py:91` | `qad_client.py:44,57,65`, `core/qad_session.py:37`, `sss/deploy.py:38`, `core/health.py:164` | yes (line 4, non-empty) | no | **No** — see defect D1 |
| `qad_username` | `QAD_USERNAME` | str | `""` | `core/config.py:92` | `qad_client.py:46`, `core/qad_session.py:48,73` | yes (line 5, non-empty) | no | **No** (shown read-only) |
| `qad_password` | `QAD_PASSWORD` | str | `""` | `core/config.py:93` | `qad_client.py:47`, `core/qad_session.py:49,73` | yes (line 6, non-empty) | no | **No** (secret) |
| `qad_client_id` | `QAD_CLIENT_ID` | str | `""` | `core/config.py:94` | `qad_client.py:45`, `core/qad_session.py:47` | yes (line 7, non-empty) | no | **No** |
| `qad_app_uri` | `QAD_APP_URI` | str | `""` | `core/config.py:95` | `sss/appconfig.py:15-17` → `app_script_name()` `:25-28`, `app_namespace()` `:31-33`; `sss/deploy.py:39` | **no** | **yes** = `"urn:app:com.extensions.customapp"` (`backend/settings.json:3`) | **Yes** (API accepts; no UI control) |
| `qad_app_dir` | `QAD_APP_DIR` | str | `""` | `core/config.py:96`; resolved to abs path at `:137-144` | `core/health.py:76,115`, `core/ts_compiler.py:48`, `sss/appconfig.py:20-22`, `sss/compile.py:31,51,69,90`, `main.py:189` | yes (line 19, non-empty) | yes = `""` (`backend/settings.json:2`) — inert | **No** — see defect D2 |
| `qad_docs_dir` | `QAD_DOCS_DIR` | str | `""` | `core/config.py:97` | `core/config.py:145,154`, `core/health.py:149`, `core/qad_docs_loader.py:20` | yes (line 15, non-empty) | no | **No** |
| `apex_admin_email` | `APEX_ADMIN_EMAIL` | str | `""` | `core/config.py:100` | `core/auth.py:53` | yes (line 21, non-empty) | no | **No** (secret) |
| `apex_admin_password` | `APEX_ADMIN_PASSWORD` | str | `""` | `core/config.py:101` | `core/auth.py:54` | yes (line 22, non-empty) | no | **No** (secret) |
| `apex_jwt_secret` | `APEX_JWT_SECRET` | str | `""` | `core/config.py:102` | `core/auth.py:41` | yes (line 25, non-empty) | no | **No** (secret) |
| `auto_deploy` | *(none)* | bool | `False` (literal) | `core/config.py:103` | **none** — only re-emitted at `core/config.py:176` and typed in `frontend/src/shared/api.ts:34,46` | n/a | no | **Yes** (API accepts) — **dead config** |
| `ALLOWED_ORIGINS` | `ALLOWED_ORIGINS` | csv str | `"http://localhost:5173"` | `main.py:66-70` — **not in `core.config` at all** | `main.py:71-76` CORS | yes (line 11, non-empty) | no | **No** (restart required) |

**[CONFIRMED] Keys declared but absent from `.env`:** `QAD_APP_URI` and `OPENAI_MODEL` are documented in `backend/.env.example:20` and `:32` but are **not present** in `backend/.env` (11 keys only). Both therefore resolve from `settings.json`.

**[CONFIRMED] `backend/.env` key inventory (existence only, no values):** `OPENAI_API_KEY` (line 1), `QAD_BASE_URL` (4), `QAD_USERNAME` (5), `QAD_PASSWORD` (6), `QAD_CLIENT_ID` (7), `ALLOWED_ORIGINS` (11), `QAD_DOCS_DIR` (15), `QAD_APP_DIR` (19), `APEX_ADMIN_EMAIL` (21), `APEX_ADMIN_PASSWORD` (22), `APEX_JWT_SECRET` (25). All 11 have non-empty values. `backend/.env.example` additionally documents `QAD_APP_URI` and `OPENAI_MODEL` and ships all credential fields blank (`.env.example:8,11,14,17,28,45,46,49` — no `<redacted>` needed; they are empty).

**[CONFIRMED] `backend/settings.json` full contents (3 keys, none a credential):**
```json
{ "qad_app_dir": "", "qad_app_uri": "urn:app:com.extensions.customapp", "openai_model": "gpt-5-mini" }
```
(`backend/settings.json:1-5`)

**[CONFIRMED] Required-key gate:** `REQUIRED_ENV_KEYS = ("OPENAI_API_KEY", "QAD_BASE_URL", "QAD_USERNAME", "QAD_PASSWORD")` at `backend/core/config.py:37`, mapped via `_REQUIRED_MAP` (`:40-45`) and evaluated against the **merged** config by `missing_required_keys()` (`backend/core/config.py:157-161`).

**[CONFIRMED] Absence finding: the frontend has no config layer at all.** No `import.meta.env` / `VITE_*` usage anywhere in `frontend/src`, and no `frontend/.env*` file exists. The API base is the hardcoded literal `const BASE = "/api";` at `frontend/src/shared/api.ts:3`.

### A10.3 Read/write path from the UI

**[CONFIRMED] Read.**

- Endpoint: `GET /api/settings` → `backend/routers/settings.py:31-34`, returning `config.public_status()`.
- Router mounted with no prefix (`backend/routers/settings.py:20`), wired at `backend/main.py:81,88,93-94`.
- Response keys (`backend/core/config.py:170-182`): `qad_base_url`, `qad_username`, `qad_app_uri`, `qad_app_dir`, `openai_model`, `auto_deploy` (bool), `has_openai_key` (bool), `has_qad_password` (bool), `qad_configured` (bool), `docs_loaded` (bool), `docs_folder_count` (int).
- Frontend caller: `fetchSettings()` at `frontend/src/shared/api.ts:54-58`; TS interface `SettingsStatus` at `frontend/src/shared/api.ts:28-38`. **[CONFIRMED] The TS interface omits `docs_loaded` and `docs_folder_count`** that the server returns.
- Consumed on mount at `frontend/src/shared/components/SettingsPage.tsx:39-46`.

**[CONFIRMED] Write.**

- Endpoint: `POST /api/settings` → `backend/routers/settings.py:37-40`.
- Payload model `UiSettingsUpdate` (`backend/routers/settings.py:23-28`): `qad_app_uri: Optional[str]`, `qad_app_dir: Optional[str]`, `openai_model: Optional[str]`, `auto_deploy: Optional[bool]`.
- Validation: **Pydantic type-coercion only.** No format, range, allow-list, path-existence or URL validation anywhere. Unknown body keys are silently dropped (default Pydantic `model_config`); `model_dump(exclude_none=True)` at `backend/routers/settings.py:40` strips unset fields.
- Persistence target: `backend/settings.json`, rewritten whole via `SETTINGS_PATH.write_text(json.dumps(current, indent=2), ...)` (`backend/core/config.py:195`).
- Response: the refreshed `public_status()` (`backend/core/config.py:197`).
- Frontend: `saveSettings()` at `frontend/src/shared/api.ts:61-69`; the page posts exactly `{qad_app_dir, openai_model}` at `frontend/src/shared/components/SettingsPage.tsx:56-59`.
- **Restart required? No** for `core.config` consumers — `save_ui_settings` resets `_settings_cache["mtime"] = None` (`backend/core/config.py:196`) forcing a re-read on next access. **Yes** for `ALLOWED_ORIGINS` and the `os.getenv` OpenAI-key consumers (see A10.1).
- **[CONFIRMED] No auth on either route.** `backend/routers/settings.py:31,37` carry no `Depends(get_current_user)`, and `backend/core/auth.py:16-18` states routes are intentionally unprotected. No rate-limit decorator either (only `/api/auth/login` `10/minute` at `backend/routers/auth.py:52`, `/api/run` `5/minute` at `backend/routers/client_extensions.py:118`, `/api/sss/generate` `10/minute` at `backend/routers/sss.py:84`; app default `30/minute` at `backend/core/rate_limit.py:21`). **Anyone who can reach the host can rewrite `settings.json`.**

**[CONFIRMED] Two live defects in the write path:**

- **D1 — `qad_base_url` is in `_UI_KEYS` but not in the API model.** `backend/core/config.py:34` lists it as UI-editable and `save_ui_settings` would persist it (`:192-194`), but `UiSettingsUpdate` (`backend/routers/settings.py:23-28`) has no `qad_base_url` field, so the value is stripped before it reaches `save_ui_settings`. It can only be set by hand-editing `settings.json`.
- **D2 — `qad_app_dir` is editable in the UI but silently discarded.** `SettingsPage.tsx:138-145` renders an input labelled `SSS App Folder (QAD_APP_DIR)`, `SettingsPage.tsx:56-59` posts it, `routers/settings.py:26` accepts it — but `_UI_KEYS` (`backend/core/config.py:34`) does **not** contain `qad_app_dir`, so the `for k in _UI_KEYS` loop at `backend/core/config.py:192-194` never writes it. The POST returns 200 and the UI shows "✓ Saved" (`SettingsPage.tsx:160`) while nothing was persisted.

**[CONFIRMED] Related endpoint used by the settings page:** `GET /api/sss/connection` (`backend/routers/sss.py:123`, router prefix `/api/sss` at `:35`), called by `testConnection()` (`frontend/src/shared/api.ts:74-93`) from `SettingsPage.tsx:69-77`. Its 503 body carries `docs_url: config.SSS_SETUP_DOCS_URL` (`backend/routers/sss.py:133`).

### A10.4 Secret handling

**[CONFIRMED] Values classified as secrets by the code itself** (never returned by `public_status()`, `backend/core/config.py:164-182`): `OPENAI_API_KEY`, `QAD_PASSWORD`, `QAD_CLIENT_ID`, `APEX_ADMIN_PASSWORD`, `APEX_JWT_SECRET`. Only booleans are exposed: `has_openai_key`, `has_qad_password` (`backend/core/config.py:177-178`). **[CONFIRMED] `qad_username` IS returned in plaintext** (`backend/core/config.py:172`) and rendered at `SettingsPage.tsx:128`. **[CONFIRMED] `apex_admin_email` is never exposed.** **[CONFIRMED] `qad_client_id` is never exposed** — but it is also never listed in `REQUIRED_ENV_KEYS`, so a missing client-id does not fail the health gate despite `core/qad_session.py:47` needing it.

**[CONFIRMED] Git tracking — verified with `git ls-files --error-unmatch`:**

| Path | Result |
|---|---|
| `backend/.env` | **NOT TRACKED** |
| `backend/settings.json` | **TRACKED** |
| `backend/.env.example` | **TRACKED** |
| `backend/history.db` | **NOT TRACKED** |
| `.claude/launch.json` | **NOT TRACKED** |
| `backend/sss_template/qad-sss.config.json` | **TRACKED** |
| `backend/sss_workspace/qad-sss.config.json` | **NOT TRACKED** |

**[CONFIRMED] Ignore-file coverage:**

| Item | `.gitignore` | `.dockerignore` |
|---|---|---|
| `.env` | covered — `.env` (`.gitignore:24`), `*.env.local` (`:25`) | covered — `backend/.env` (`.dockerignore:14`), `**/.env` (`:15`) |
| `backend/settings.json` | **NOT covered — no entry anywhere in `.gitignore`** | **NOT covered — baked into the image by `Dockerfile:27`** |
| `backend/history.db` | covered (`.gitignore:44-45`) | covered (`.dockerignore:18-19`) |
| `backend/logs/`, `backend/sss_workspace/` | covered (`.gitignore:46-47`) | covered (`.dockerignore:20-21`) |
| `.claude/` | covered (`.gitignore:2`) | covered (`.dockerignore:26`) |

**[CONFIRMED] Plainly stated:** `backend/.env` is **not** tracked by git. `backend/settings.json` **is** tracked by git (committed in `84d209b`; `git show HEAD:backend/settings.json` is byte-identical to the working copy, and `git diff` is empty).

**[CONFIRMED] No secret is currently committed** — the tracked `settings.json` holds only `qad_app_dir`, `qad_app_uri`, `openai_model`, and the tracked `.env.example` ships every credential field blank.

**[CONFIRMED] But a secret IS committable, today, with no code change.** `save_ui_settings` writes into the git-tracked `settings.json`, and `_merged()` reads `qad_password`, `qad_username`, `qad_client_id` back out of that same file as a legacy fallback (`backend/core/config.py:113-121`). Anyone who hand-edits `settings.json` to restore the legacy shape (which the code explicitly still honours) puts a QAD password into version control on the next `git add`. **This is the single highest-severity finding in this section.**

**[CONFIRMED] A real environment hostname is already committed.** `backend/sss_template/qad-sss.config.json:2` is tracked and contains:
```json
{ "envUrl": "http://qadee.yash.com:22010/qad-central/", "id": "<redacted>", "appURI": "urn:app:com.extensions.customapp" }
```
This file is copied verbatim into every scaffolded workspace by `backend/core/sss_scaffold.py:34-39` and is **never templated from `QAD_BASE_URL`**. `id` is an opaque numeric identifier of unknown sensitivity — redacted here per instruction.

**[CONFIRMED] Secondary leak surface:** `core/qad_session.py:47-49` and `qad_client.py:44-47` put `password` into **query-string parameters** on the OAuth call, e.g. `qad_client.py:44-47`:
```python
    f"{config.qad_base_url()}/qad-central/oauth/token"
    f"?client_id={config.qad_client_id()}"
    f"&username={config.qad_username()}"
    f"&password={config.qad_password()}"
```
Credentials in a URL are logged by proxies and servers. Not a settings-registry defect per se, but it is where the secret ends up.

### A10.5 PROPOSAL — STATIC vs DYNAMIC classification

> **This entire item A10.5 is a PROPOSAL for human confirmation, not a finding.** The static/dynamic split is my judgement; only the "where defined" column is [CONFIRMED].

| Value | Where defined today | Proposed class | Rationale | Confidence |
|---|---|---|---|---|
| `QAD_BASE_URL` | `.env` line 4 | **DYNAMIC** | Per-environment QAD host:port; dev/QA/prod differ by definition | High |
| `QAD_USERNAME` | `.env` line 5 | **DYNAMIC** | Service account differs per environment | High |
| `QAD_PASSWORD` | `.env` line 6 | **DYNAMIC (secret)** | Rotates independently per env | High |
| `QAD_CLIENT_ID` | `.env` line 7 | **DYNAMIC (secret-ish)** | Issued by each QAD instance | Medium — could be static if one OAuth client is registered org-wide |
| `OPENAI_API_KEY` | `.env` line 1 | **DYNAMIC (secret)** | Per-env key for cost/quota separation | High |
| `OPENAI_MODEL` | `settings.json:4` (`gpt-5-mini`) | **STATIC** | A product decision, not an environment fact; should be identical everywhere | Medium — teams sometimes downgrade the model in dev to save cost |
| `MODEL_MATRIX` (`planning`/`generation`/`compile`) | `pipeline.py:136-140` (hardcoded) | **STATIC** | Per-step model tiering is product behaviour | High |
| `QAD_APP_URI` | `settings.json:3` | **STATIC** | The extension app's identity — same URN in every env | Medium — a customer-specific deployment could rename it |
| `QAD_APP_DIR` | `.env` line 19, `.env.example:24` (`./sss_workspace`) | **DYNAMIC** | Filesystem path; differs Windows dev vs `/app/sss_workspace` container | High |
| `QAD_DOCS_DIR` | `.env` line 15, `.env.example:41` (`./qad_docs`) | **STATIC** | Relative `./qad_docs` ships with the image; resolved portably at `core/qad_docs_loader.py:31-36` | Medium — an absolute override would make it dynamic |
| `ALLOWED_ORIGINS` | `.env` line 11; default `main.py:68` | **DYNAMIC** | Prod frontend origin differs from `http://localhost:5173` | High |
| `APEX_ADMIN_EMAIL` | `.env` line 21 | **DYNAMIC** | Per-deployment demo account | High |
| `APEX_ADMIN_PASSWORD` | `.env` line 22 | **DYNAMIC (secret)** | Must differ per deployment | High |
| `APEX_JWT_SECRET` | `.env` line 25 | **DYNAMIC (secret)** | `.env.example:47-48` explicitly says "Generate a fresh 32-byte hex per deploy" | High |
| `auto_deploy` | `config.py:103` (literal `False`) | **STATIC** | Currently dead; if revived it is a behaviour flag, not an env fact | Low — unused, intent unknown |
| `MODULE = "com.extensions.customapp"` | `builders/*.py` ×7 (see A10.6) | **STATIC** | Same URN namespace as `QAD_APP_URI` | Medium |
| `SSS_SETUP_DOCS_URL` | `config.py:50` | **STATIC** | Comment at `config.py:47-49` says "Structural route (NOT an environment-specific setting)" | High |
| `OAUTH_PATH`, `LOGIN_PATH` | `core/qad_session.py:28-29` | **STATIC** | QAD platform route shape, fixed by the vendor | High |
| `/qad-central/api/qracore/…` path fragments | `qad_client.py:57,65`, `sss/deploy.py:42` | **STATIC** | Vendor API contract | High |
| `TOKEN_TTL = 8h`, `ALGORITHM = "HS256"` | `core/auth.py:32-33` | **STATIC** | Security policy, uniform across envs | Medium — prod may want a shorter TTL |
| Rate limits `30/min`, `5/min`, `10/min` | `rate_limit.py:21`, `client_extensions.py:118`, `sss.py:84`, `auth.py:52` | **DYNAMIC** | Prod usually needs different ceilings than a dev laptop | Medium |
| Log level `logging.INFO`, rotation `5 MB × 5` | `logging_setup.py:30,44` | **DYNAMIC** | DEBUG in dev, INFO/WARN in prod is normal practice | Medium |
| `LOG_DIR` = `backend/logs` | `logging_setup.py:23` | **DYNAMIC** | Container mounts a volume at `/app/logs` (`docker-compose.yml:17`) | Medium |
| `DB_PATH` = `backend/history.db` | `database.py:8` | **DYNAMIC** | `docker-compose.yml:19-24` documents an intended external bind mount | High |
| Port `8000` | `Dockerfile:39,44`, `docker-compose.yml:12` | **DYNAMIC** | Host port mapping varies per deployment | High |
| Vite proxy `http://localhost:8000` | `frontend/vite.config.ts:8` | **STATIC** | Dev-only; never used in the built bundle | High |
| `envUrl: http://qadee.yash.com:22010/qad-central/` | `sss_template/qad-sss.config.json:2` | **DYNAMIC** | It is literally a QAD host URL, and it is committed | High |
| `id: <redacted>` in same file | `sss_template/qad-sss.config.json:3` | **DYNAMIC** | Instance-issued identifier | Low — semantics unverified |
| `outFile: dist/customappdev.js` | `sss_template/tsconfig.json:10` | **STATIC (derived)** | Must equal `f"dist/{app_script_name()}dev.js"`; `sss_scaffold.py:99-110` already warns on drift | High |
| `typescript: "3.5"` | `sss_template/package.json:12` | **STATIC** | `core/health.py:133-138`: "QAD requires 3.5" | High |
| `TOTAL_STEPS = 14`, `STEP_LABELS` | `pipeline.py:142,145-…` | **STATIC** | Pipeline shape is product behaviour | High |

### A10.6 What is currently HARDCODED (registry migration candidates)

**[CONFIRMED]** All entries below were located by grepping for URL/path/URN literals and then read in place.

**Highest priority — a real environment hostname baked into a tracked file:**

- `backend/sss_template/qad-sss.config.json:2` — `"envUrl": "http://qadee.yash.com:22010/qad-central/"`. Copied unmodified to every workspace by `backend/core/sss_scaffold.py:34-39`. Nothing in the codebase ever rewrites it from `QAD_BASE_URL`. The already-scaffolded (untracked) `backend/sss_workspace/qad-sss.config.json:2` carries the same value.

**QAD app namespace duplicated 7× instead of deriving from `qad_app_uri`:**

- `MODULE = "com.extensions.customapp"` at `backend/builders/bc_builder.py:4`, `backend/builders/deploy_builder.py:3`, `backend/builders/embedded_builder.py:13`, `backend/builders/event_handler_builder.py:3`, `backend/builders/form_builder.py:3`, `backend/builders/view_builder.py:4`; plus `MODULE_SHORT = "extensions.customapp"` at `bc_builder.py:5`, `form_builder.py:4`, `view_builder.py:5`.
- `backend/pipeline.py:42` — `"module_uri": "urn:app:com.extensions.customapp"`, alongside `"namespace": "com.extensions"` and `"app": "customapp"` (`pipeline.py:39-40`).
- `backend/main.py:150` — `module = data.get("module", "com.extensions.customapp")` (default in the backfill migration).
- `backend/builders/embedded_builder.py:124,131` — the same namespace **percent-encoded** as `com%2Eextensions%2Ecustomapp`, which no simple string substitution will catch.
- `backend/sss_template/package.json:2` — `"name": "urn_app_com.extensions.customapp"`.
- **[CONFIRMED]** `core.config.qad_app_uri()` already holds this value (`settings.json:3`), and `sss/appconfig.py:31-33` already derives `app_namespace()` from it — the builders simply do not use it.

**QAD platform route literals (vendor contract; candidates for a `routes` section rather than per-env settings):**

- `backend/core/qad_session.py:28-29` — `OAUTH_PATH = "/qad-central/oauth/token"`, `LOGIN_PATH = "/qad-central/api/login"`.
- `backend/qad_client.py:44` — `f"{config.qad_base_url()}/qad-central/oauth/token"`; `:57` and `:65` — `f"{config.qad_base_url()}/qad-central/api/qracore/{endpoint}"`.
- `backend/sss/deploy.py:42` — `f"{base}/qad-central/api/qracore/sss"` with `?appURI=…&filename=…&appSeq=0&fileSeq=3` (`:43-45`).
- `backend/core/lookup_generator.py:70` — `LOOKUP_ENDPOINT = "lookups?viewUri=urn:be:com.qad.qra.lookup.ILookup"`.
- `backend/pipeline.py:436,477,517,530` — `entitymetadatas?viewUri=urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD`; `pipeline.py:710` — `viewResourceMetadatas?viewUri=urn:be:com.qad.qra.meta.IViewResourceMetadata`.
- `backend/builders/bc_builder.py:231` — `"urn:be:com.qad.qra.metadatav3.IEntityDeployment:"`; `backend/builders/embedded_builder.py:124,131,319` — further `urn:be:com.qad.qra.*` literals.
- `backend/core/lookup_generator.py:32` — a **different** app URN in a docstring: `urn:app:com.extensions.sdapp`.

**Filesystem paths derived from `__file__`, none overridable:**

- `backend/core/config.py:29-31` — `_BACKEND_DIR`, `ENV_PATH`, `SETTINGS_PATH`.
- `backend/database.py:8` — `DB_PATH = Path(__file__).parent / "history.db"`.
- `backend/core/logging_setup.py:23-24` — `LOG_DIR`, `LOG_FILE`.
- `backend/core/sss_scaffold.py:17` — `TEMPLATE_DIR`.
- `backend/core/qad_docs_loader.py:28` — `_BACKEND_DIR`.
- `backend/main.py:212` — `FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"`.

**Network/port/origin literals:**

- `frontend/src/shared/api.ts:3` — `const BASE = "/api";`.
- `frontend/vite.config.ts:8` — `"/api": "http://localhost:8000"`.
- `backend/main.py:68` — default `"http://localhost:5173"`.
- `docker-compose.yml:12` — `"8000:8000"`; `docker-compose.yml:26` and `Dockerfile:42` — healthcheck `http://localhost:8000/api/health`; `Dockerfile:39` — `EXPOSE 8000`.
- `.claude/launch.json:9` — frontend dev port `5173` (untracked, local tooling only).

**Behaviour constants with no config path:**

- `backend/pipeline.py:136-140` `MODEL_MATRIX`; `pipeline.py:142` `TOTAL_STEPS = 14`; `pipeline.py:188` `max_tokens = 15000`.
- `backend/core/auth.py:32-33` `TOKEN_TTL = timedelta(hours=8)`, `ALGORITHM = "HS256"`.
- `backend/core/rate_limit.py:21` `default_limits=["30/minute"]`; `backend/routers/client_extensions.py:118` `5/minute`; `backend/routers/sss.py:84` `10/minute`; `backend/routers/auth.py:52` `10/minute`.
- `backend/core/logging_setup.py:30` `level=logging.INFO`; `:44` `maxBytes=5_000_000, backupCount=5`.
- `backend/core/health.py:101` `needed = ["salesgen.d.ts", "purchasinggen.d.ts"]`; `:133` `version.startswith("3.5")`; `:162` `timeout=5.0`.
- `backend/sss/generate.py:86` `timeout=90.0, max_retries=4`; `backend/core/sss_scaffold.py:81` npm-install `timeout=120`.
- `backend/sss_template/tsconfig.json:10` `"outFile": "dist/customappdev.js"` — must track `qad_app_uri`; `sss_scaffold.py:99-110` only *warns* on mismatch, it does not fix it.

---

---

## A11. Uncommitted work in flight: lookup detector/generator and progress parser

### A11.0 Scope of the working tree vs HEAD

[CONFIRMED] `git diff --stat` against HEAD (`af0286b` "Fix step-6 form-field normalization", `backend/pipeline.py | 127 +++`, dated Tue Jul 21 2026):

```
 PROGRESS.md                          | 246 +++++++++++++++++++++++-
 backend/agents/prompts.py            |  25 ++--
 backend/core/progress_parser.py      |  30 +++-
 backend/pipeline.py                  | 256 +++++++++++++++++++++++++--
 backend/routers/client_extensions.py |  88 ++++++++--
 frontend/index.html                  |   2 +-
 6 files changed, 608 insertions(+), 39 deletions(-)
```

[CONFIRMED] `git status --porcelain -uall` shows exactly four untracked paths: `backend/core/lookup_detector.py`, `backend/core/lookup_detector_test.py`, `backend/core/lookup_generator.py`, `frontend.zip`. Nothing else.

[CONFIRMED] `backend/core/progress_parser_test.py` is **already tracked** (it does not appear in `git status`); `VERSIONS.md` is tracked (`git ls-files` lists it); `debug_run.txt` and `graphify-out/` are **ignored**, not untracked — `.gitignore:50` (`debug_run.txt`) and `.gitignore:5` (`graphify-out/`). `frontend.zip` (19,307,862 bytes, dated Jul 22) is untracked and **not** ignored — it is a 19 MB blob one `git add -A` away from entering history. That is a finding, not a recommendation.

---

### A11.1 `lookup_detector.py` and `lookup_generator.py` — what they do and who calls them

#### `backend/core/lookup_detector.py` (586 lines, untracked)

**What it detects** [CONFIRMED]: `FIND [FIRST|LAST|NEXT|PREV] <table>` and `FOR EACH|FIRST|LAST <table>` statements that carry a `WHERE` clause, via `_LOOKUP_HEAD_RE` (`backend/core/lookup_detector.py:128-133`) and `_WHERE_RE` (`:134`). A `FIND`/`FOR` with no `WHERE` is skipped outright — `backend/core/lookup_detector.py:486-487` (`if not wm: continue  # unfiltered FIND/FOR — not a lookup`).

**Input** [CONFIRMED]: `detect_lookups(source: str)` — one argument, raw ABL text (`:466`). Not a Path, not a dict.

**Output** [CONFIRMED]: `list[LookupCandidate]` sorted by `evidence_line` (`:526-527`). `LookupCandidate` is a dataclass with exactly these fields (`:47-56`):

```python
source_table: str; target_field: str; classification: str
confidence: float; filters: list[dict]; result_field: str
evidence_line: int; matched_rule: str; notes: str
```

`to_dict()`/`from_dict()` round-trip those same nine keys (`:58-83`).

**Classification** [CONFIRMED]: three values only — `"static"`, `"dependent"`, `"uncertain"` (`:50`, and the `_CONCERN` ranking `{"static": 1, "uncertain": 2, "dependent": 3}` at `:87`). A candidate's class is the **worst case across its filters**, and `confidence`/`matched_rule` come from the highest-confidence filter *within* that worst class (`_aggregate`, `:530-564`).

**Rule registry** [CONFIRMED] — `_RULES` at `:409-414`, exactly four entries, and `rule_count()` returns `len(_RULES)` (`:417-419`):

| Rule fn | Line | Emits | Confidence |
|---|---|---|---|
| `rule_literal_find_filter` | `:317` | `static` / `value_source="literal"` | 0.95 quoted, 0.92 numeric |
| `rule_traced_local_constant` | `:327` | `static` / `"local_constant"` | 0.85 direct, 0.70 via `INITIAL` |
| `rule_cascading_field_dependency` | `:344` | `dependent` / `"screen_field"` | 0.85 / 0.80 / 0.75 / 0.70 / 0.65 / 0.60 |
| `rule_unresolvable_filter_source` | `:394` | `uncertain` / `"unknown"` | 0.30 |

Every rule runs on every filter and `max(..., key=confidence)` wins (`:507-510`).

**Filter dict shape** [CONFIRMED] (`:512-518`): `{"field", "operator", "value_source", "value"}` — `field` is the LHS column with any `table.` prefix stripped (`_parse_condition`, `:461`).

**Notable behaviours actually in the code** [CONFIRMED]:
- `result_field` is **always** `""` — hardcoded at `:557-560` with the comment that a bare FIND selects the whole record.
- `_TRACE_MAX_LOOKBACK = 4000` characters (`:149`) bounds the backward variable trace; `_enclosing_proc_start` (`:179-186`) floors at `offset - 4000`.
- `_find_stmt_end` (`:152-176`) treats `:` as a terminator **only** when followed by whitespace/EOF, so `custId:SCREEN-VALUE` is not truncated. This is the HIGH-severity fix PROGRESS.md:386-391 describes.
- `_mask_quotes` (`:108-124`) is used for the AND-split (`:438`), trailing-clause cut (`:491`), and operator detection (`:453`).
- `_split_filters` splits on `AND` only (`:438`) — **there is no `OR` handling anywhere in the file**. That matches the recorded limitation at PROGRESS.md:348-354.
- `detect_lookups` swallows **all** exceptions and returns `[]` (`:469-472`). A detector crash is therefore indistinguishable from "no lookups found" — no warning is emitted on that path.

**Where it is called from** [CONFIRMED], full grep of the repo:
1. `backend/core/progress_parser.py:22` — `from core.lookup_detector import detect_lookups, build_lookup_warnings`; invoked at `backend/core/progress_parser.py:105-106`.
2. `backend/pipeline.py:22` — `from core.lookup_detector import LookupCandidate`; used at `backend/pipeline.py:70` (`LookupCandidate.from_dict(d)`).
3. `backend/core/lookup_detector_test.py:22`.

So it **is** wired in — it is not dead code.

#### `backend/core/lookup_generator.py` (283 lines, untracked)

**What it builds** [CONFIRMED]: `generate_lookup_payload(candidate, bc_metadata) -> dict` (`backend/core/lookup_generator.py:99`), returning `{"lookups": [ <one lookup obj> ], "_needs_verification": [str, ...]}`. It **raises `LookupGenerationError` for any non-static candidate** (`:111-115`).

**Emitted lookup object keys** [CONFIRMED] (`:218-235`), verbatim: `appName, browseName, browseURI, fieldLabel, fieldSet, moduleURI, namespace, reference, resultField, searchField, searchFieldOperator, lookupQualifiers, lookupResultFields, lookupSearchConditions`. `reference` is hardcoded `""`; `searchFieldOperator` hardcoded `"eq"`; `lookupQualifiers` and `lookupResultFields` hardcoded `[]`. `uri`, `modelId`, `concurrencyHash` are deliberately absent (comment at `:233-234`).

**Search-condition shape** [CONFIRMED] (`:185-193`): `{"fieldName", "operator", "fieldValue1", "fieldValue1Type": "LITERAL", "fieldValue2": None, "fieldValue2Type": None, "dataType"}`.

**Operator mapping** [CONFIRMED] `_map_operator` (`:83-96`): only exact `CONTAINS` returns `confirmed=True`; `BEGINS`/`MATCHES` → `CONTAINS` unconfirmed; `=` → `"EQ"` unconfirmed; anything else passes through uppercased, unconfirmed.

**Endpoint** [CONFIRMED]: `LOOKUP_ENDPOINT = "lookups?viewUri=urn:be:com.qad.qra.lookup.ILookup"` (`:70`). `backend/qad_client.py:57` builds `f"{config.qad_base_url()}/qad-central/api/qracore/{endpoint}"`, so the full URL matches the docstring claim at `:9`. `post_qad(endpoint, payload, token)` signature (`backend/qad_client.py:56`) matches the call at `backend/core/lookup_generator.py:280`.

**Live-POST guard** [CONFIRMED]: `if dry_run is not False:` at `:266` — only an explicit `False` reaches the network. The `qad_client` import is deferred inside that branch (`:276`).

**Finding — `_needs_verification` can never be empty** [CONFIRMED]: line `:236` appends the `uri / modelId / concurrencyHash` flag **unconditionally**, outside every `if`. Consequence, traced through the pipeline: `backend/pipeline.py:91-92` (`needs = payload.get("_needs_verification", []); if needs:`) is therefore always true, so **every** static candidate emits both a `lookup_candidate` and a `lookup_needs_review` (reason `"payload_gap"`) event. PROGRESS.md:538 is consistent with this ("drops from 9 flags to 2", never to 0).

**Where it is called from** [CONFIRMED]: exactly one production call site — `backend/pipeline.py:23` (`from core.lookup_generator import create_lookup`), invoked at `backend/pipeline.py:74` with `dry_run=True` hardcoded. **`generate_lookup_payload` has no direct external caller** and **no test file references `lookup_generator` at all** (grep over the whole repo returns only `pipeline.py`, its own module, and PROGRESS.md). Absence of a `lookup_generator_test.py` is a real gap: the payload builder — the piece closest to a QAD write — is the untested one.

---

### A11.2 `progress_parser.py` — what it parses, and the step-identity question

**Naming caution** [CONFIRMED]: `backend/core/progress_parser.py` parses **OpenEdge Progress ABL source** (`.p` / `.cls`). It has nothing to do with UI progress or pipeline steps. The module docstring (`:1-15`) says so explicitly.

**Source** [CONFIRMED]: `parse_progress_file(source: str | Path, *, filename: str = "")` (`:67`). A `Path` is read with `encoding="utf-8", errors="replace"` and an `OSError` degrades to `_empty_result` (`:80-89`). `.cls` vs `.p` is decided purely by filename suffix (`:92`).

**Output shape** [CONFIRMED] (`:117-125`), seven keys:

```python
{"source_type", "tables", "procedures", "functions",
 "source_tables_referenced", "lookups", "parse_warnings"}
```

`tables[i]` = `{"name", "fields", "primary_key"}`; each field = `{"name", "type", "label", "format", "required", "qad_type"}` (`:208-215`). `_empty_result` (`:337-346`) mirrors the same seven keys.

**Consumers** [CONFIRMED], complete grep:
- Backend: `backend/routers/client_extensions.py:25` imports `parse_progress_file, parsed_to_requirements_text`; called at `:133-136`. `parse_warnings` → streamed as `{'type': 'warning', 'message': w}` SSE frames **before** the pipeline generator starts (`backend/routers/client_extensions.py:155-156`). `parsed["lookups"]` → `lookup_candidates`, passed to `run_pipeline` (`:136`, `:161-165`).
- Tests: `backend/core/progress_parser_test.py:18`, `backend/core/lookup_detector_test.py:23`.
- Frontend: **none.** Grep for `warning|lookup` across `frontend/src` returns only CSS token names (`design-tokens.css:29,51,155`) and the embedded step label `"Checking deployment warnings"` (`ProgressPanel.tsx:28`). No frontend code reads a parse result, a `warning` event, or any lookup event.

#### Is progress parsing the source of step identity? No.

[CONFIRMED] Step identity comes entirely from `_evt()` in `backend/pipeline.py:163-177`, which emits:

```python
{"type": type_, "step": step, "total": TOTAL_STEPS,
 "name": STEP_LABELS.get(step, ""), "status": status, "message": message}
```

`TOTAL_STEPS = 14` (`backend/pipeline.py:142`); `STEP_LABELS` maps 1–14 (`:145-160`). The only thing `progress_parser` affects about steps is that a non-empty `parsed_requirements` makes step 1 skip its LLM call and emit `"Requirements read directly from your file"` instead (`backend/pipeline.py:401-406`).

**How robust is that step identity for a step-gated UI?** [CONFIRMED] — four concrete weaknesses, all readable in the code:

1. **Step numbers are not monotonic.** Step 3 is emitted `done` at `backend/pipeline.py:499`, then `running` again at `:511` ("Wiring dropdown fields to data lists..."), then `done` again at `:540`. On the error path, step 4 runs at `:458` and then step 3 goes back to `running` at `:473`. A consumer that assumes "step N done ⇒ N is finished" is wrong.
2. **The frontend hides 5 of the 14 steps.** `frontend/src/features/client_ext/components/ProgressPanel.tsx:20` — `const STANDARD_VISIBLE_STEPS = [1, 2, 3, 5, 7, 9, 11, 13, 14];`. Steps 4, 6, 8, 10, 12 are never rendered in standard mode. The `if (n === 4 && status === "pending") return null;` guard at `:68` is unreachable in standard mode (4 is not in the list) and only applies to embedded mode, whose `EMBEDDED_VISIBLE_STEPS = [1..7]` (`:32`).
3. **Step labels are duplicated, not derived.** `ProgressPanel.tsx:3-18` hardcodes its own 1–14 label map; the `name` field the backend sends in every event (`pipeline.py:169`) is ignored by `ProgressPanel` and used only in the error box (`ProgressPanel.tsx:94`). Two independent sources of truth for the same 14 strings.
4. **The embedded pipeline can emit a step the UI cannot render.** `backend/pipeline_embedded.py:321` and `:338` emit `step 8` with `total_steps = 8` (`:105`), but `EMBEDDED_VISIBLE_STEPS` stops at 7 (`ProgressPanel.tsx:32`).

[CONFIRMED] Additionally, the four non-`step` event types the backend now emits — `warning` (`client_extensions.py:156`), `lookup_candidate`, `lookup_needs_review`, `lookup_summary` (`pipeline.py:82`, `:94`, `:107`, `:125`) — are **absent from the frontend's type union**: `frontend/src/features/client_ext/api.ts:6` declares `type: "step" | "error" | "complete" | "run_id"`. In `ClientExtPanel.tsx:98-135` they fall through every branch into the generic "Normal step event" handler (`:131-135`), get pushed into `events`, and are then filtered out by `ProgressPanel.tsx:52` (`if (e.type === "step" && e.step)`). They are received and silently discarded. Likewise `summary.lookups` (added at `pipeline.py:772-775`) is not in the `PipelineSummary` interface (`api.ts:17-27`) and is rendered nowhere.

---

### A11.3 What the uncommitted diffs actually change, per file

#### `backend/core/progress_parser.py` (+30/-1)

Two independent changes.

(a) Lookup wiring [CONFIRMED]: new import at `:22`; new block at `:104-106`:

```python
    lookups = detect_lookups(text)
    warnings.extend(build_lookup_warnings(lookups))
```

Note it runs on `text` (raw), not `stripped` — deliberate, per the comment at `:102-104`. New `"lookups"` key in both the success return (`:123`) and `_empty_result` (`:345`).

(b) Explicit BC-name precedence [CONFIRMED]: `_EXPLICIT_NAME_RE` (`:352-355`) and `_explicit_bc_name()` (`:358-363`); the one-line behavioural change at `:384`:

```python
    bc_name = _explicit_bc_name(user_note) or _pascal(t["name"])
```

(was `bc_name = _pascal(t["name"])`).

[CONFIRMED] Structural consequence: `progress_parser` now has a hard module-level import dependency on `lookup_detector` (`:22`). Since `lookup_detector.py` is **untracked**, a clean checkout of HEAD-plus-tracked-changes would fail to import `core.progress_parser`, and therefore `routers/client_extensions` and `main`. The three untracked files are load-bearing, not optional.

#### `backend/pipeline.py` (+256)

Four distinct changes bundled in one uncommitted diff:

1. **Phase 11 lookup emission** [CONFIRMED]: imports `:22-23`; `_sse()` `:29-31`; `_lookup_bc_metadata()` `:34-51`; `_emit_lookup_events()` `:54-131`; new kwarg `lookup_candidates: list[dict] | None = None` at `:384`; the emission block at `:722-731`, positioned after `yield _evt("step", 13, "done", ...)` (`:720`) and before `yield _evt("step", 14, "running", ...)` (`:734`); summary key at `:772-775`. `_lookup_bc_metadata` hardcodes `namespace="com.extensions"`, `app="customapp"`, `module_uri="urn:app:com.extensions.customapp"`, `app_name="CustomApp"` (`:39-43`) and **never supplies** `browse_uri`, `browse_entity`, `result_field`, `search_field`, or `field_set` — the six optional keys `generate_lookup_payload` accepts (`lookup_generator.py:132-139`). So in-pipeline, every static payload carries the full flag set.
2. **Duplicate-BC short-circuit** [CONFIRMED]: `_qad_error_messages()` `:209-223`, `_is_duplicate_entity_error()` `:226-231` (substring test `"already exist" in blob`), and the step-3 early return at `:444-455`; post-retry error rewritten at `:481-489`.
3. **Step-6 completeness** [CONFIRMED]: bare-single-placement wrapping in `_normalize_placements` `:276-285`; new `_build_placements()` returning `(placements, missing)` `:354-378`; step 6 rewritten to build → one corrective retry naming the omissions → **raise** if still incomplete (`:557-587`). The failure text at `:580-586` explicitly stops before step 7.
4. **Observability** [CONFIRMED]: step-5 panel-plan log at `:547`.

[CONFIRMED] `run_pipeline`'s docstring (`:386-395`) documents `user_message` and `parsed_requirements` but **not** `lookup_candidates` — the new parameter is undocumented in the signature it belongs to.

#### `backend/routers/client_extensions.py` (+88)

[CONFIRMED] Pasted-source detection. `_ABL_SIGNALS` — ten regexes at `:44-56`; `_MIN_ABL_SIGNALS = 2` at `:57`; `_SRC_FILENAME_RE` at `:58`; `_count_abl_signals` `:61-62`; `_find_source_start` `:65-76`; `_guess_source_filename` `:79-85` (falls back to `pasted.cls` / `pasted.p`). `_extract_progress_attachment` (`:88-111`) now takes the marker path first, then the ≥2-signal path, then returns `(None, None, message)`. Plus `lookup_candidates: list[dict] = []` at `:128`, populated at `:136`, forwarded at `:161-165`.

#### `backend/agents/prompts.py` (+25/-10)

[CONFIRMED] `FORM_FIELD_BUILDER` (`:184`) output contract changed from a bare JSON array to `{"placements": [...]}`, and three new rules added (`:207-212`), verbatim:

```
- Return ONE object: starts with { ends with }
- "placements" MUST be an ARRAY, even when the plan has only one field.
  NEVER return a single placement object on its own.
- COMPLETENESS IS MANDATORY: if the plan lists N fields, "placements" MUST
  contain exactly N entries — one per field. Never stop after the first field,
  never truncate, never summarise.
```

#### `frontend/index.html` (+1/-1)

[CONFIRMED] `<title>APEX-Transform</title>` → `<title>ApexTransform</title>` (`frontend/index.html:6`). Nothing else.

#### `PROGRESS.md` (+246)

[CONFIRMED] Three single-line edits (lines 15, 17, 57) plus a 241-line append starting at line 301, adding five sections: "Phase 11 — Automated Lookup Detection & Generation", "Step-6 completeness fix (2026-07-27)", "Step-3 duplicate-BC handling (2026-07-27)", "Pasted-source detection + explicit-name precedence (2026-07-27)", "Validation trial, pass 1 — real saved lookup record (2026-07-28)".

---

### A11.4 Project state per PROGRESS.md / VERSIONS.md — doc claims vs code

#### What the docs claim

[CONFIRMED] `PROGRESS.md:42-57` status table — Phases 0, 1, 2, 3, 4, 4+ (×3), 6, 7, 8, 9, 11 all `✅`. Phase 5 is `✅ Superseded — folded into Phase 7`. **There is no Phase 10 row at all** — the table jumps 9 → 11.

[CONFIRMED] `PROGRESS.md:15`: "Phases 0–4 done & approved. Phase 6 … Phase 7 … 2026-07-17. Phase 8 … Phase 9 … 2026-07-19. **Phase 11 … done & verified 2026-07-24** … detector suite 14/14, parser 7/7."

[CONFIRMED] `PROGRESS.md:17` next action: "**Restart the running backend**"; two items opt-in/UNVERIFIED — SSS end-to-end, and the lookup live-validation trial. "`create_lookup` stays `dry_run=True` everywhere until then."

**Stated known issues / deferrals** [CONFIRMED]:
- `PROGRESS.md:31-36` — Phase 3 settings unification; `qad_client` → `core.qad_session` migration; Phase 5 pinning; SSS end-to-end unverified.
- `PROGRESS.md:325-344` — five payload known-unknowns: top-level `uri`, nested condition `uri`, `modelId`, `concurrencyHash`, and the browse-identity gap.
- `PROGRESS.md:348-354` — known-unknown #6: `OR` in WHERE clauses is not split; explicitly recorded as a limitation, not a bug.
- `PROGRESS.md:525-529` — still open after the 2026-07-28 trial: wire-level casing (`equals`/`Literal` vs `eq`/`EQ`/`LITERAL`), and `uri`/`modelId`/`concurrencyHash` not visible in the UI.
- `PROGRESS.md:269` — "Existing routes still open": `/api/*` is unauthenticated.
- `PROGRESS.md:111` — Phase 2's "Pause for user review ← HERE" is still unticked even though `PROGRESS.md:114` says Phase 2 was approved.

[CONFIRMED] `VERSIONS.md` (64 lines, tracked, unmodified, dated Jul 17): Python 3.11.x (`:12`), Node 18/20 LTS (`:13`), tsc **3.5.3 pinned** with the p2js rationale (`:14`, `:45-56`); backend pins fastapi 0.115.5, uvicorn 0.32.1, openai 1.55.3, httpx 0.28.0, aiosqlite 0.20.0, python-dotenv 1.0.1, pydantic 2.10.3, requests 2.32.3, requests-toolbelt 1.0.0, slowapi 0.1.9 (`:22-31`).

#### Where doc and code disagree

| # | Doc claim | Code / repo reality | Verdict |
|---|---|---|---|
| 1 | `PROGRESS.md:57` + `:15`: Phase 11 "✅ Done & verified 2026-07-24" | `PROGRESS.md:304` heading in the *same file*: "Phase 11 — … (🚧 **in progress** 2026-07-23)" | [CONFIRMED] doc-internal contradiction; heading is stale |
| 2 | `PROGRESS.md:15`/`:57` mark Phase 11 done | All three Phase 11 source files are **untracked** and every consumer edit is **uncommitted** | [CONFIRMED] "done" ≠ committed |
| 3 | `PROGRESS.md:267`: "**No Docker verification**: no `Dockerfile` in the repo" | `Dockerfile` (1511 B), `docker-compose.yml` (951 B), `.dockerignore` all present; commit `f9a4111` is literally "Add Docker configuration" | [CONFIRMED] stale; true when Phase 8 was written, false now |
| 4 | `PROGRESS.md:359-361` plan: "(2) `core/lookup_detector_test.py` **7 fixtures**" | File has 11 `Case*` classes + `RegistryShape`, 14 test methods | [CONFIRMED] plan superseded by `:405` ("14/14"), original line never corrected |
| 5 | `PROGRESS.md:366` step-2 entry: "**8/8 pass**" | 14 test methods exist | [CONFIRMED] historical, superseded at `:405`; both lines coexist in the file |
| 6 | `VERSIONS.md:24`: `openai 1.55.3` pinned | `backend/pipeline.py:187` branches on `if not model.startswith("gpt-5")` to set `max_tokens` | [INFERRED] a `gpt-5` code path exists that `MODEL_MATRIX` (`pipeline.py:136-140`, all `gpt-4o*`) never reaches. Confirm by checking whether any config path can override `MODEL_MATRIX` — I found none in `pipeline.py`. |
| 7 | `PROGRESS.md:311-314`: lookup events are "surfaced" / "not just a silent dict flag" | `frontend/src/features/client_ext/api.ts:6` has no such event types; `ProgressPanel.tsx:52` filters to `type === "step"` | [CONFIRMED] the events reach the browser and are dropped. Surfaced in the SSE stream and the server log — **not** in the UI. |
| 8 | Status table has no Phase 10 | No Phase 10 section anywhere in `PROGRESS.md` | [CONFIRMED] absence stated plainly; nothing indicates whether Phase 10 was skipped or renumbered |

Everything else I checked lines up: `dry_run=True` is genuinely the only mode wired (`pipeline.py:74`), the live guard is genuinely `is not False` (`lookup_generator.py:266`), `rule_count()==4` is genuinely 4 (`lookup_detector.py:409-419`), and the lookup step genuinely sits between 13 and 14 (`pipeline.py:720/725/734`).

---

### A11.5 Test coverage and runnability (not run)

**Runner** [CONFIRMED]: stdlib `unittest`. Both files carry `if __name__ == "__main__": unittest.main(verbosity=2)` (`progress_parser_test.py:210-211`, `lookup_detector_test.py:315-316`) and both prepend the `backend/` directory to `sys.path` so they work as script *or* module (`progress_parser_test.py:14-16`, `lookup_detector_test.py:18-20`).

**Documented invocations** [CONFIRMED], from the file docstrings:
```
python -m unittest core.progress_parser_test      (from backend/)
python backend/core/progress_parser_test.py       (from repo root)
python -m unittest core.lookup_detector_test      (from backend/)
python backend/core/lookup_detector_test.py       (from repo root)
```

**Dependencies** [CONFIRMED]: zero third-party. `progress_parser_test.py` imports only `os, sys, unittest` + `core.progress_parser`. `lookup_detector_test.py` imports only `os, sys, unittest` + `core.lookup_detector` + `core.progress_parser`. No pytest, no fixtures, no network, no OpenAI, no QAD. `core.progress_parser` pulls in `core.lookup_detector` (`progress_parser.py:22`), which imports only `re`, `collections`, `dataclasses`, `typing` — so no transitive third-party dependency either. [INFERRED] These are runnable on any Python ≥3.10 with no venv; the only requirement is that `backend/` is importable, which both files handle themselves.

**`backend/core/progress_parser_test.py` — 7 test methods** [CONFIRMED]:
| Class:method | Line | Covers |
|---|---|---|
| `SimpleTempTable.test_extracts_fields_types_and_pk` | `:39` | 4-field TEMP-TABLE, type map, PK→required, FORMAT/LABEL retention, `_titlecase` default, `FOR EACH` reference capture, zero warnings |
| `CompositePrimaryKey.test_composite_pk_and_special_types` | `:92` | composite PK `["OrderNum","LineNum"]`, LOGICAL, BLOB→character + warning, PROCEDURE + FUNCTION capture |
| `CompositePrimaryKey.test_requirements_text_shape` | `:116` | `parsed_to_requirements_text` — user note preserved, `BC name: OrderLine`, PK flags, "Parse notes:" |
| `ClassFileWithProperties.test_class_extraction` | `:153` | `.cls` → synthetic table; PUBLIC methods in, PROTECTED out |
| `FailSoftEdgeCases.test_no_temp_table_returns_empty` | `:179` | no-TEMP-TABLE fallback string |
| `FailSoftEdgeCases.test_unknown_type_becomes_character_with_warning` | `:187` | `BOGUS-TYPE` → character + warning |
| `FailSoftEdgeCases.test_comments_do_not_confuse_extractor` | `:198` | commented-out TEMP-TABLE ignored |

Matches PROGRESS.md's "7/7" (`:227`, `:233`, `:405`).

**`backend/core/lookup_detector_test.py` — 14 test methods across 12 classes** [CONFIRMED]: Case1 literal→static conf ≥0.9 (`:43`); Case2 `BEGINS "ABC"`→static, operator recorded as `BEGINS` (`:69`); Case3 traced constant→static, 0.7 ≤ conf < 0.95, value `PLATINUM` (`:94`); Case4 cascading chain→2 candidates, `inventory` dependent with notes naming both `wSite` and `warehouse.whSite` (`:121`); Case5 unresolvable parameter→uncertain, conf <0.5 (`:153`); Case6 no-lookup file→`[]` **and** via `parse_progress_file` asserts `parsed["lookups"] == []` with no lookup warnings (`:174-180`); Case7 three independent statics, distinct ordered evidence lines (`:194`); Case8 inline `custId:SCREEN-VALUE`→dependent (`:218`) + `SELF:ScreenValue`→dependent (`:228`); Case9 clause keyword inside literal (`"BY"`, `"BILL OF LADING"`) stays static (`:248`); Case10 `"SMITH AND SONS"` not split (`:267`); Case11 `EQ` word operator (`:286`) + AND-split alongside `"A AND B"` (`:295`); `RegistryShape.test_rule_count` asserts `rule_count() == 4` (`:311`).

**Coverage gaps, stated plainly** [CONFIRMED]:
- **No test file for `lookup_generator.py`.** `generate_lookup_payload`, `_map_operator`, `_strip_private`, the `dry_run is not False` guard, and the `LookupGenerationError` on non-static input are all untested by any file in the repo.
- **No test for `_emit_lookup_events`** (`pipeline.py:54-131`) or for the SSE event shapes. PROGRESS.md:369 describes a "full MOCKED pipeline" verification, but no such harness exists as a checked-in file — it was a session-time script, not a repository artifact.
- **No test for the new `client_extensions.py` paste-detection** (`_count_abl_signals`, `_find_source_start`, `_guess_source_filename`). PROGRESS.md:487-493 describes verification against real `history.db` prompts; again, not a repository artifact.
- **No test for `_explicit_bc_name`**, `_is_duplicate_entity_error`, `_qad_error_messages`, or `_build_placements`.
- **No `OR`-clause test**, consistent with the recorded limitation.

---

### A11.6 Does the code's step sequence match PROGRESS.md?

**Matches** [CONFIRMED]:
- "adds NO 15th numbered step" (`PROGRESS.md:311-314`) — `TOTAL_STEPS = 14` (`pipeline.py:142`), `STEP_LABELS` stops at 14 (`:159`), and `_emit_lookup_events` uses `_sse()` (`:29-31`) which never sets a `step`/`total`/`name` key.
- "lookup step runs AFTER step 13 (view registered) and BEFORE step 14 (deploy)" (`PROGRESS.md:368`) — `pipeline.py:720` → `:725-731` → `:734`. Exact.
- "True no-op when a BC has no lookups" (`PROGRESS.md:313-314`) — guarded by `if lookup_candidates:` (`pipeline.py:725`); zeroed summary default at `:772-775`.
- "`client_extensions` passes the already-parsed lookups (no re-parse)" (`PROGRESS.md:368`) — `client_extensions.py:136` then `:164`. Confirmed, one parse only.
- Step 6 "STOP with an actionable error rather than saving a partial form. Step 7 never runs" (`PROGRESS.md:428-430`) — the `raise` at `pipeline.py:580-586` is inside the `try` whose `except` yields `_evt("error", 6, ...)` and `return`s (`:588-589`), before step 7 at `:593`.
- Step 3 "short-circuits a collision BEFORE the auto-fix" (`PROGRESS.md:454-457`) — `pipeline.py:444-455` returns before the step-4 emission at `:458`.

**Discrepancies** [CONFIRMED]:

1. **PROGRESS.md never enumerates the 14 steps.** There is no canonical step list in the doc; the only complete lists are `pipeline.py:145-160` and the duplicate at `ProgressPanel.tsx:3-18`. The doc describes step *transitions* (3, 4, 5, 6, 7, 13, 14) only in prose.
2. **The code has an unnumbered "STEP 3.5".** `pipeline.py:502` is commented `── STEP 3.5: Wire dropdown fields to their data lists (if any) ─` and re-emits step **3** (`:511`, `:540`). PROGRESS.md documents the dropdown feature (`:50`, "QAD dropdown-list support") but nowhere records that it reuses step 3's number after step 3 has already reported `done`. A step-gated UI built on `status === "done"` will regress to `running` here.
3. **Step numbering has a gap at 4 in the happy path.** The sequence a successful run emits is 1, 2, 3, (3), 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 — step 4 ("Fixing errors automatically") only ever fires on an error (`pipeline.py:458`). The doc does not state this; the frontend encodes it only by omitting 4 from `STANDARD_VISIBLE_STEPS` (`ProgressPanel.tsx:20`).
4. **The lookup events are described as user-visible but are not.** `PROGRESS.md:311-317` frames `lookup_candidate` / `lookup_needs_review` as the visible surfacing mechanism; no frontend code handles them (§A11.2). The doc claim is true of the SSE stream, false of the UI.
5. **`PROGRESS.md:304` still marks Phase 11 in progress** while `:15`/`:57` mark it done (see §A11.4 #1).

---

---

# Part B — the Adaptive platform documentation

## B1. Adaptive Docs — Event Handlers: testing the Pre/Post timing hypothesis

**Source legend** (all paths relative to their repo root; every line number below was read directly):

| Tag | Path |
|---|---|
| `[C7]` | `adaptive_java_version/Docs/qad_enterprise_platform_class_7_Event_Handlers_training_guide.pdf.md` |
| `[C3]` | `adaptive_java_version/Docs/qad_enterprise_platform_class_3_Extensions_Relations_Formulas_training_guide.pdf.md` |
| `[C2]` | `adaptive_java_version/Docs/qad_enterprise_platform_class_2_Business_Component_training_guide.pdf.md` |
| `[UIEH]` | `aux_web_version/backend/qad_docs/Extending the UI/UI Event Handlers.txt` |
| `[FBEH]` | `aux_web_version/backend/qad_docs/Business Components - Form Builder/Form Builder - Event Handlers.txt` |
| `[APIREF]` | `aux_web_version/backend/qad_docs/UI Event Handlers/Event handlers API reference.txt` |
| `[GRIDEV]` | `aux_web_version/backend/qad_docs/UI Event Handlers/Handling grid events.txt` |
| `[HOWTO]` | `aux_web_version/backend/qad_docs/UI Event Handlers/Event handlers _How To_.txt` |
| `[CLISCR]` | `aux_web_version/backend/qad_docs/Platform Scripting - TypeScript/Client scripting.txt` |
| `[MAINVH]` | `aux_web_version/backend/qad_docs/Client scripting/Main view UI event handler.txt` |
| `[GRIDVH]` | `aux_web_version/backend/qad_docs/Client scripting/Grid UI event handler.txt` |
| `[DEBUG]` | `aux_web_version/backend/qad_docs/Client scripting/Debugging UI event handlers.txt` |
| `[BCVIEW]` | `aux_web_version/backend/qad_docs/App Development Tools and Resources/Business Components view.txt` |
| `[DGRID]` | `aux_web_version/backend/qad_docs/UI elements list of events and Properties_Functions/Data Grid ( ViewGrid ).txt` |
| `[VFIELD]` | `aux_web_version/backend/qad_docs/UI elements list of events and Properties_Functions/Form Field ( ViewField ).txt` |
| `[EX12-A]` | `aux_web_version/backend/qad_docs/Example 1.2_ Adding new functionality to item maintenance with a Many-to-one relationship/Add event handler to retrieve electrical plug info.txt` |
| `[EX12-B]` | `aux_web_version/backend/qad_docs/Example 1.2_ Adding new functionality to item maintenance with a Many-to-one relationship/Add event handler to update electrical requirements panel.txt` |
| `[EX2]` | `aux_web_version/backend/qad_docs/Example 2 - Extend the UI_ Extending standard functionality with extra UI validation/Add an event handler to SupplierV2s maintenance UI.txt` |

---

### 1. VERDICT on the hypothesis

**PARTIALLY HOLDS.** The timing mechanism is real, documented, and works exactly as the commissioner reads it. The second limb — *"we never need to read or merge the parent's source at all"* — is **supported for form/field logic but NOT established by the docs for embedded-grid handler claiming**, and it is **flatly blocked in one configuration**.

**What holds [CONFIRMED]:**

- `[C7]:62-64` — "**Primary** – primary event handler for corresponding business component"; "**Pre** – runs before Primary or coded event handler."; "**Post** – runs after Primary or coded event handler." Under the heading `# Run time order of Event Handlers` (`[C7]:60`).
- `[UIEH]:12` — "Event handlers always run before or after the existing application code" (heading: *Introduction / What is an Event Handler?*).
- `[UIEH]:14` (heading *Event handler timing*) — "If an event handler is a PRE type, it runs before the existing TS handlers."
- `[FBEH]:102-103` (heading *UI Quick Reference > Main panel > Timing*) — "Pre — runs before the existing application code (TS handler). DB value: BEFORE." / "Post — runs after the existing application code (TS handler). DB value: AFTER."
- The Primary handler is **not edited**: each timing is a **separate module with its own class instances**. `[C7]:427` shows `module com.qad.erp.base.EventHandler.Country.ComExtensionsTraining.Maint_BEFORE`, `[C7]:466` shows the same BC as `...Maint_AFTER`, `[C7]:625` shows `...Maint_PRIMARY`. Three separate compilation units, same BC.
- Worked precedent on a **QAD standard BC** without touching QAD source: `[EX2]:7-8` — "Open Business Components, select SupplierV2s (base app)" … "click the New button, select the Active checkbox, and then change the timing to Post."

**What does NOT hold / is unproven [CONFIRMED as a documented restriction]:**

- `[FBEH]:22-28` — intended action "Add 'pre/post' event handler", *Is platform BC* = yes, *Definition is in same App* = yes → "**Not possible**". Restated at `[FBEH]:88`: "then the developer can create only Primary Event Handler."
  → If the active developer app **is** the app that owns the target BC, Pre/Post is unavailable and you are forced onto the Primary handler — i.e. into merge territory.
- **Grid claiming is the real risk.** `[GRIDVH]:143` — "createViewGridTSHandler will ONLY be called for the grids that are in the array `ViewGridsToHandleList`". This is a property of *the main handler class of one module*. Whether a Primary module and a Post module can **both** list the same `gridId` and both receive grid events is **nowhere stated** in any file read. This is the single point on which Phase 5 lives or dies.
- **A Pre handler can suppress downstream processing.** `[APIREF]:27` — `eventData.eventProcessed` "designates that the subscriber has taken control of the event processing"; `[APIREF]:224` — "necessary for the subscriber to call `processEvent(false)`". So "the Primary continues to run untouched" is true only if your Pre code does not cancel. The converse (does a Primary that sets `eventProcessed` suppress your Post?) is **not documented**.

**Honest note on doc quality:** `[C7]` contradicts itself on the Country example. `[C7]:446` says "Select Post timing", `[C7]:461` shows "Timing Post ▾ Runs after any other event handlers", but `[C7]:501` tabulates the same handler as "**Timing | Pre**". Treat `[C7]`'s Pre/Post labels as unreliable; `[FBEH]` and `[UIEH]` are the authoritative statements.

---

### 2. Exact timing options, meanings, execution order, and where registration lives

**The three options and their DB values [CONFIRMED]** (`[FBEH]:100-103`, corroborated verbatim at `[UIEH]:16-18`):

| UI label | Meaning (quoted) | DB value | Source |
|---|---|---|---|
| `Primary` | "primary event handler for the corresponding business component. It can be created only for platform BC" | `PRIMARY` | `[FBEH]`:101 |
| `Pre` | "runs before the existing application code (TS handler)" | `BEFORE` | `[FBEH]`:102 |
| `Post` | "runs after the existing application code (TS handler)" | `AFTER` | `[FBEH]`:103 |

Corroborated by the runtime artefact name: `[DEBUG]:32` — "the name of the UI event handler sources is `com_extensions_oneforce_TIMING.ts`" and "Timing can be BEFORE, AFTER, or PRIMARY."

**Documented execution order [CONFIRMED]** — `[UIEH]:21` gives the only multi-app ordering example in any source:
`"App1-EventHandler-Pre","App2-EventHandler-Pre","StandardApp-TShandler","App3-EventHandler-Post","App1-EventHandler-Post"`
Note what this does **and does not** say: it shows Pre-block → application TS handler → Post-block. It does **not** state how App1-Pre and App2-Pre are ordered relative to each other.

Also note the semantic drift between sources — `[C7]:461` tooltip reads "Runs after any other event handlers" (all handlers), while `[FBEH]:103` says "after the existing application code (TS handler)" and `[BCVIEW]:406` says "run after any other application TS handlers". These are three different scopes. [INFERRED] `[FBEH]`/`[BCVIEW]` are correct and `[C7]:461` is loose slide copy; **not confirmed**.

**Does registering Pre/Post require modifying the entity that carries the Primary? NO. [CONFIRMED]**
Registration is a **new row in the Event Handlers grid**, created with `New`:
- `[C7]:402-406` (heading *Using of data from the extension*) — "Open Business Components." / "Select Countries." / "Scroll to Form and click New in Event Handlers grid."
- `[EX2]:8` — "Go to Form > Event Handlers, click the New button".
- `[C7]:443-446` — "Pay attention that Timing option is available now." / "Select Post timing." (the Timing dropdown only appears for the New row on a foreign BC).

**Where the registration lives — on the FORM, addressed by a view-metadata URI [CONFIRMED]:**
- Panel location is under **Form**, not the View and not the field: `[BCVIEW]:395` is `Form panel`, `[BCVIEW]:405-406` is `Event Handlers panel` — "Edit event handlers for the form. You can specify whether the event handlers are active and the timing as Pre (run before any other application TS handlers) or Post…". Same placement in `[C7]:237-241` ("Scroll to the Form panel." / "Click Details in Event Handlers grid.") and `[C2]:916-924` (Event Handlers grid with columns **Timing, Active, Applies To, App, App URI**, shown directly under the Form panel).
- The grid columns are exactly `Timing | Active | Applies To | App | App URI` — `[C7]:230-232`, `[C2]:922-923`.
- **The wire-level key is the form's view-metadata URI.** `aux_web_version/backend/builders/event_handler_builder.py:8` builds `view_uri = f"urn:view:viewmeta:{MODULE}.{bc_pascal}"` and puts it in `"viewURI"` at `:29`. The **form** payload uses the identical URI (`aux_web_version/backend/builders/form_builder.py:127` and `:216` inside `"viewMetadatas"`), whereas the **hybrid-browse view** uses a different scheme, `urn:view:hybridbrowse:` (`aux_web_version/backend/builders/view_builder.py:157`). So "viewURI" in the event-handler payload = the form, not the menu view. [CONFIRMED]
- Separately, `[C2]:1018` describes the **View** configuration screen as having "sections for Main, Options, Browse, and **TS Handlers**" — a *different* panel from Form > Event Handlers. Nothing in any file read explains that panel. Flagged as an open question.

**Nothing anywhere ties a handler to a single field.** There is a `ViewFieldTSHandler` base class (`[APIREF]:468`, `[APIREF]:727`) but no per-field registration row.

---

### 3. The handler base classes

`[C7]:169-176` lists **four**; `[APIREF]` documents **five**. Reproduced exactly.

| # | Documented class name | Purpose (quoted) | Required methods / lifecycle hooks | Source |
|---|---|---|---|---|
| 1 | `QraViewTSHandlerWithViewFormTSHandler<TNgData, TQraViewFormTSHandler>` | "Base class for the View TS event handlers." / "main event handler which is reacting on page lifecycle events" | **Required:** `createViewFormTSHandler(): TFormHandler`. **Optional:** `init()`, `onDestroy()`, `createViewGridTSHandler(viewGrid: IViewGrid)`, `ViewGridsToHandleList: string[]`, `onViewGridCreated(viewGrid)` | `[C7]`:169-170, `[C7]`:76-77; `[MAINVH]`:44, :53-73, :62; `[APIREF]`:10, :839, :834 |
| 2 | `QraViewFormTSHandlerV2<TNgData>` | "Base class for the ViewForm event handlers." / acts "on UI events related to form elements (such as labels, input fields or buttons)" | No required override. Hooks: `constructor(creator: TSHandlerCreator)`, `onDestroy()`, plus event overrides | `[C7]`:171-172, :108-109; `[GRIDVH]`:69-87; `[CLISCR]`:107-113 |
| 3 | `ViewGridTSHandlerV2<TNgData, TGridNgData[], TGridRecord>` | `[C7]:174` says "Base class for the ViewForm event handlers" — **this is a documentation error in `[C7]`**; correct purpose per `[C7]:130-131`: "responsible for processing of grid events" | Must be instantiated by the main handler: `ViewGridsToHandleList` in `init()`, returned from `createViewGridTSHandler`. Constructor signature `new XGridHandler(viewGrid, this)` | `[C7]`:173-174, :130-131, :683; `[GRIDEV]`:5, :23, :32-38; `[GRIDVH]`:43-44, :113-128 |
| 4 | `QraBrowseTSHandlerV2` | "Base class for the Browse event handlers." / "responsible for browse events… execute code when browse record is selected and implement own click handlers for toolbar items, including Actions drop-down" | **Not documented in any file read.** `[APIREF]:1905` only says "It also implements empty overridable methods for QraBrowseTSHandler events" — the referenced list is a dead cross-reference | `[C7]`:175-176, :158-159; `[APIREF]`:1892-1918 |
| 5 | `ViewFieldTSHandler<TNgData>` — **not mentioned by the commissioner** | per-field handler | Events: `onFieldChange`, `onFieldLeave` only | `[APIREF]`:468-488, :727-747, :867-877 |

Fully-qualified import names [CONFIRMED] — all live in `Qad.QraView.TSHandler`: `[C7]:430-431`, `[C7]:628-630`, `[GRIDEV]:5` ("The class must inherit from `Qad.QraView.TSHandler.ViewGridTSHandlerV2`").

**Hard constraint on class naming [CONFIRMED]:** `[C7]:439` and `[C7]:479`, repeated at `[MAINVH]:26` and `[EX12-A]:29` — "Do not change this class name or the event handler will no longer run." The generated main class is `<BCName>MaintHandler` (`[C7]:435` `TrainingMaintHandler`; `[MAINVH]:29` `CountryMaintHandler`; `[EX12-A]:32` `ItemMaintHandler`).

**Module naming pattern [CONFIRMED, observed across 6 samples]:**
`<bc-owning-namespace>.EventHandler.<BC>.<ActiveAppPascal>.Maint_<TIMING>`
- `[C7]:427` `com.qad.erp.base.EventHandler.Country.ComExtensionsTraining.Maint_BEFORE`
- `[C7]:466` same, `Maint_AFTER`
- `[C7]:625` `com.extensions.training.EventHandler.Training.ComExtensionsTraining.Maint_PRIMARY`
- `aux_web_version/backend/qad_docs/Example 2 …/Ref_ complete event handler code for SupplierV2s BC.txt:6` — `com.qad.erp.base.EventHandler.SupplierV2.ComQadQadextensions.Maint_AFTER`
[INFERRED] The `Maint_<TIMING>` suffix is regenerated by the platform when Timing changes — `[C7]` shows the same Country handler as `_BEFORE` at :427 (template state) and `_AFTER` at :466 after "Select Post timing" at :446. Confirm by changing Timing on a saved handler and re-opening the editor.

---

### 4. Available events — and specifically field-change / parent-screen events

**View handler (`QraViewTSHandlerWithViewFormTSHandler`) — `[APIREF]:18-197`:**
`init()` :18 · `onBindData` :22 · `onBeforeUpdate` :26 · `onAfterUpdate` :33 · `onCancelChange` :38 · `onBeforeDelete` :42 · `onAfterDelete` :47 · `onBeforeInit` :52 and `onBeforeInit` (V2, FD22.2) :55 · `onAfterInit` :58 · `onButtonClick` :63 · `onBeforeToolbarInitialized` :66 · `onToolbarInitialized` :69 · `onActionChange` :72 · `onConfirmData` :78 · `onBeforeViewInit` :85 · `onAfterViewInit` :89 · `onAutoGridBeforeInit` :93 · `onBeforeRequery` :100 · `onBeforeSendData` :104 · `onGetKeyData` :111 · `onAttachmentsDataBound` :114 · `onBeforeAttachmentDataBound` :121 · `onActivityFeedDataBound` :124 · group-panel events `onGroupPanelSelectorClick` :153, `onGroupPanelToggleExpand` :160, `onErrorGroupPanelToggleExpand` :166, `onGroupPanelsConfigOpen` :172, `onGroupPanelsConfigApply` :175, `onGroupPanelsInit` :179 · `onHybridBrowseViewStateChange` :191. Plus `onViewGridCreated` (`[MAINVH]:62`, `[C7]:669`).

**Form handler (`QraViewFormTSHandlerV2`) — `[APIREF]:206-232`, `[CLISCR]:70-93`:**
`onHandlerAddedToViewField` · `onButtonClick` · `onFirstFieldChange` · `onFieldChange` · `onFieldLeave` · `onFieldClick` · `onDestroy`.

**Grid handler (`ViewGridTSHandlerV2`) — `[APIREF]:246-467`:**
`onAutoGridBindData` :246 · `onAutoGridRowChange` :253 · `onAutoGridFieldChangeEvent` :260 · `onAutoGridFieldLeaveEvent` :271 · `onAutoGridNewButtonClick` :276 · `onAutoGridBeforeEdit` :286 · `onAutoGridAfterEdit` :318 · `onAutoGridEditButtonClick` :331 · `onAutoGridCancelButtonClick` :338 · `onAutoGridBeforeAddNew` :344 · `onAutoGridBeforeUpdate` :350 · `onAutoGridAfterUpdate` :359 · `onAutoGridBeforeDelete` :369 · `onAutoGridAfterDelete` :377 · `onAutoGridDetailsLinkClick` :382 · `onAutoGridDetailsLinkClose` :392 · `onAutoGridAfterInit` :410 · `onAutoGridToolbarSetState` :418 · `onAutoGridSelectionStateChange` :430 · `onAutoGridButtonClick` :437 · `onAutoGridSchemaDefined` :445 · `onAutoGridConfirmDataEvent` :450 · `onAutoGridGetFieldSchema` :461. Also `onBrowseGridBeforeDataGridInit` (`[DGRID]:901,904`).

**Browse handler:** list **absent** from every file read (see §3 row 4). Stated plainly as a gap.

#### FIELD CHANGE — exactly which event fires where [CONFIRMED]

| Where the field lives | Event | Handler class | Source |
|---|---|---|---|
| Parent form field (non-grid) | `onFieldChange(viewField, eventData, processEvent)` | **Form** handler | `[APIREF]`:217-224; `[VFIELD]`:16,:49 |
| Parent form, *first* change only | `onFirstFieldChange(viewField, eventData)` | Form handler | `[APIREF]`:209-215 |
| Parent form field, focus loss regardless of change | `onFieldLeave` | Form handler | `[APIREF]`:228-232 |
| **Cell inside an (embedded) grid** | `onAutoGridFieldChangeEvent(eventData, processEvent)` | **Grid** handler | `[APIREF]`:260-268 |
| Grid cell focus loss | `onAutoGridFieldLeaveEvent` | Grid handler | `[APIREF]`:271-275 |

Firing semantics [CONFIRMED]: `[APIREF]:222` — "Called when a field value is changed in a standalone (non-data-grid) field", "Fired as soon as the UI focus is moved away". `[C7]:353` says the same in plainer words: "it will be triggered when modified field lost focus, not immediately". `[APIREF]:223` — "only fired in response to field changes in the UI … not when fields are bound to data from the model."

`eventData` payload keys for field change [CONFIRMED, `[APIREF]:218-220`]: `eventData.fieldName`, `eventData.fieldValue`, `eventData.fieldValueOrig`. Grid variant adds `eventData.gridId` and `eventData.dataRow` (`[APIREF]:261-264`).

#### PARENT-SCREEN events relevant to populating an embedded grid [CONFIRMED]

- `onBindData` — `[C7]:349`: "Event which happens each time when data from the selected record should be displayed". Fires on every record selection in a hybrid browse (`[APIREF]:24`).
- `onAutoGridBindData` — `[APIREF]:250`: "Called when the view screen binds new data to its auto grid."
- `onAutoGridNewButtonClick` — `[APIREF]:281`: "Called when the New button is clicked on an auto grid"; used for exactly this pattern in `[C7]:673-675`.
- `onAutoGridAfterEdit` — `[APIREF]:325`: fires after the server initialize call for a new row, so defaults are available on `eventData.dataRow`.
- `onBeforeUpdate` — `[C7]:548`: "Standard event which happens each time before sending of data to the server"; abortable via `eventData.eventProcessed = true`.
- `onAfterViewInit`, `onActionChange` (CREATE↔UPDATE switch, `[APIREF]:77`), `onBeforeRequery`.

#### The Phase 5 pattern is documented end-to-end and is the closest existing precedent [CONFIRMED]

`[EX12-B]:111` states the crux plainly: **"these fields change events fire in the form handler and not in the grid handler"** — so the parent-field → embedded-grid path must be wired manually. The documented wiring:
1. Main handler holds a public reference to the grid handler (`[EX12-B]:121,135-136`).
2. Main handler injects itself into the form handler (`[EX12-B]:128-130`: `itemFormHandler.mainTSHandler=this;`).
3. Form handler's `onFieldChange` branches on `viewField.Name` and calls into the grid handler (`[EX12-B]:154-170`).

APIs for writing into embedded grid cells [CONFIRMED]:
- `setRowFieldValue(rowData, fieldId, value, withoutRefresh = false): boolean` — `[DGRID]:416-417`, `[APIREF]:1643-1652`; used live at `[EX12-A]:86-88`.
- `setCurrentRowFieldValue(fieldId, value)` — `[APIREF]:1660`.
- `this.ViewGrid.DataSource.addRecord({...})` / `insertRecord` / `removeRecord` / `getRecords` / `refresh` / `sync()` — `[DGRID]:40-123`.
- Hierarchical child forms: `setChildViewGridFormFieldValue(gridFormName, dataRow, fieldName, fieldValue)` — `[DGRID]:1289`.
- Server fetch inside a handler: `this.ViewController.doHttpGet(...)` against `api/qracore/be/urn:be:<...>?k=v` — `[EX12-A]:75,80`; blocking variant `blockUIAndDoHttpGet` — `[HOWTO]:39`.

Structural background for embedded grids: a Many-to-One extension with *Include Grid on Parent Form* is auto-rendered as an embedded grid on the parent (`[C3]:244`, `[C3]:534`, `[C3]:597`), and no form/view need be built for it (`[C3]:319-321`).

---

### 5. Multiple handlers on the same entity — allowed? ordering? conflicts? existing validations?

**Allowed — yes, with a documented cardinality [CONFIRMED]:**
- `[FBEH]:87` — "the developer can create one Pre and Post Event Handlers for each App which is active at the moment."
- `[FBEH]:88` — platform BC + same app → "the developer can create only Primary Event Handler."
- `[FBEH]:89` — platform BC + different app → "then the developer can create Pre and Post Event Handlers."
- Confirmed at the data level: the record key is the 4-tuple `(appURI, viewURI, eventHandlerType, appliesTo)` — `aux_web_version/backend/sss_template/lib/qracoregen.d.ts:2009` declares `fetch(appURI: string, viewURI: string, eventHandlerType: string, appliesTo: string)`. So per form, per app, per Web/Mobile, per timing = exactly one row. [CONFIRMED]
- `[CLISCR]:22` gives the intent in one line: "Other apps will be able to run scripts before or after this logic."

**Ordering across apps [CONFIRMED as partial]:** only the block ordering is documented (`[UIEH]:21`). **Ordering among two Pre handlers from two different apps is nowhere stated.** Absence of any tie-break rule is a real finding.

**Conflicts / disturbing existing validations — the docs give warnings, not guarantees [CONFIRMED]:**
- The cancel channel is shared: `[APIREF]:27` (`eventData.eventProcessed` — "designates that the subscriber has taken control of the event processing"), `[APIREF]:224` ("call `processEvent(false)`" to cancel a field change and restore the prior value). A Pre handler using either **can** change what the Primary sees.
- `[APIREF]:428` — explicit performance warning on `onAutoGridToolbarSetState`: "Do not do any other kind of processing in this event handler."
- `[UIEH]:91` — JQuery DOM manipulation "needs to be done with care so that the standard UI logic is not broken."
- `[FBEH]:90` — "the developer can edit and delete any Event Handler without any restrictions." **This is a hazard, not a reassurance**: nothing prevents an agent from overwriting a parent app's Primary row.
- **No statement anywhere** that a Pre/Post handler cannot break the Primary's validations. The docs simply never make that promise.

---

### 6. What the docs do NOT answer — and the exact test that would settle each

| # | Unanswered | Precise test to settle it |
|---|---|---|
| 6.1 | Can a Post/Pre handler claim a `gridId` that the Primary handler already lists in `ViewGridsToHandleList`? (`[GRIDVH]:143` — "createViewGridTSHandler will ONLY be called for the grids that are in the array") | On a standard BC with an existing Primary that handles grid `G`, register a Post handler that also lists `G` and overrides `onAutoGridBindData` with `console.log`. Set a breakpoint per `[DEBUG]:41-52`. Observe whether **both** modules' grid handlers log. If only one does, the merge-free approach is dead for grids. |
| 6.2 | Ordering among multiple Pre handlers from different apps | Register Pre handlers in two apps, each logging its app name in `onBindData`; read console order. |
| 6.3 | Does a Primary setting `eventData.eventProcessed = true` suppress a Post handler on the same event? | Post handler logs in `onBeforeUpdate`; trigger a save where the Primary aborts. Check whether the Post log appears. |
| 6.4 | Does `processEvent(false)` in a Pre `onFieldChange` prevent the Primary's `onFieldChange` from firing? | Pre handler calls `processEvent(false)` unconditionally; instrument the Primary. |
| 6.5 | Browse handler (`QraBrowseTSHandlerV2`) event list — completely undocumented in these sources (`[APIREF]:1905` is a dead reference) | Clear the editor and re-save/re-open to force template regeneration (`[CLISCR]:28`), then use the "Overriding an event handler base class method" editor completion trick (`[CLISCR]:125`) to enumerate overridable methods. |
| 6.6 | What the **View > TS Handlers** panel (`[C2]:1018`) is, vs Form > Event Handlers | Open a View's Details in Business Components and capture the network POST; compare its payload key against `eventHandlerV2s`. |
| 6.7 | Is `Maint_<TIMING>` module suffix regenerated when Timing is switched, and does a stale suffix break execution? | Save a handler as Post, switch Timing to Pre, save, reopen editor; diff the module line. |
| 6.8 | Does the embedded-grid `gridId` remain stable across parent BC redeploys? Docs only say IDs "can be found in the html" (`[UIEH]:65`) | Capture `viewGrid.GridID` via `onViewGridCreated` before and after a parent redeploy. |
| 6.9 | Whether an embedded (Many-to-One) extension's own auto-built form can carry its own event handler at all — `[C3]:321` says extensions get no View, `[C3]:493` says "Embedded Business Components cannot be extended", and `[BCVIEW]:140` warns "you cannot create certain types of extensions, unless the environment is in the owning namespace" | Open the embedded BC in Business Components and check whether a Form > Event Handlers panel with a New button is present and enabled. |
| 6.10 | Does compile happen client-side or server-side, and is the compiler version pinned? `[C7]:52` says "compiled into JavaScript and is saved to the database" but `[FBEH]:7` says "compiled into JavaScript **at runtime**" — these conflict | Click Compile with devtools Network open; see whether a POST carries the TS and returns JS. |

---

### 7. How handler code is stored and retrieved — including the read-back question

**Storage [CONFIRMED]:**
- `[C7]:52` — an event handler "is compiled into JavaScript and is saved to the database. It's assigned to the business component". Same claim at `[UIEH]:8` and `[FBEH]:7`.
- `[UIEH]:8` draws the distinction the whole strategy rests on: TS handlers "are not stored in the database, instead they are part of the application code itself." **So the parent's Primary/coded logic may not be readable at all from the DB — which is an argument *for* the Pre/Post approach, not against it.**

**Exact stored record shape [CONFIRMED]** — `aux_web_version/backend/sss_template/lib/qracoregen.d.ts:1971-1985`, namespace `com.qad.qra.adapter.eventhandlerv2.gen.dto`:

```ts
interface EventHandlerV2Record {
    AppURI: string;  ViewURI: string;  IsActive: boolean;
    EventHandlerType: string;  JavaScriptCode: any;  TypeScriptCode: any;
    MappingCode: any;  Properties: any;  AppliesTo: string;
    ConcurrencyHash: string;  DataOperation: string;
    DisallowedActions: string;  DisallowedActionsMessage: string;
}
```
Dataset wrapper: `dsEventHandlerV2 → ttEventHandlerV2[]` (`:1965-1970`).

**A READ-BACK EXISTS. [CONFIRMED]** — same file, `:2005-2012`, interface `IEventHandlerV2s`:
```ts
fetch(appURI: string, viewURI: string, eventHandlerType: string, appliesTo: string): EventHandlerV2sDTO;
exists(appURI: string, viewURI: string, eventHandlerType: string, appliesTo: string): boolean;
```
plus `create` / `update` / `delete` / `initialize` (`:2006-2010`) and the server-side CRUD hooks `_fetch` / `_exists` at `:2001,:2003`. `EventHandlerV2sComm` declares `static ENTITY_URI: string` (`:2019`) — **the literal URI value is not in the `.d.ts`**, so the concrete `urn:be:...` string must be recovered from the live platform.

**What AUX currently does [CONFIRMED]:**
- `aux_web_version/backend/pipeline.py:685` — `eh_result = await post_qad("eventhandler", eh_data["payload"], token)`
- `aux_web_version/backend/qad_client.py:57` — `url = f"{config.qad_base_url()}/qad-central/api/qracore/{endpoint}"` → the concrete write URL is **`{base}/qad-central/api/qracore/eventhandler`**
- A GET twin already exists: `aux_web_version/backend/qad_client.py:64-66` — `get_qad(endpoint, token)` on the same `/qad-central/api/qracore/{endpoint}` prefix.
- Payload built at `aux_web_version/backend/builders/event_handler_builder.py:25-37`, root key `"eventHandlerV2s"`, item keys `appURI`, `viewURI`, `eventHandlerType`, `appliesTo`, `isActive`, `typeScriptCode`, `javaScriptCode`, `mappingCode`.
- **AUX hard-codes Pre timing today:** `event_handler_builder.py:30` — `"eventHandlerType": "BEFORE"`. Matching the prompt template at `aux_web_version/backend/agents/prompts.py:259` (`...Maint_BEFORE`).

**Other retrieval surfaces [CONFIRMED]:**
- Runtime: the compiled handler is served as a named browser script source. `[DEBUG]:32` — "Your event handler will start with your app uri, but ':' replaced with `_`… `com_extensions_oneforce_TIMING.ts`". A devtools Sources listing or network capture on any screen therefore **enumerates every active handler and its timing**, including other apps'.
- `[BCVIEW]:425-426` — *Source File Generation panel*: "Click Download to generate the business component source code files and download them in a .zip file." Whether the zip includes handler TS is **not stated**.
- **No REST endpoint for reading handler source appears in any qad_docs file.** A grep of every `api/…` path across `aux_web_version/backend/qad_docs` yields only `api/bdoc/`, `api/bsvc/`, `api/qracore/{apps,browses,be,roles}`, `api/ng/service/`, `api/postapi`, `api/qraview/attachments`, `api/erp/sites/`, `api/webshell/clearAllCaches` — none handler-related. Absence stated plainly.

---

---

## B2. Adaptive Docs — Java extensions

**Source read in full (892 lines / 32,464 bytes).** Absolute path: `D:\WEB_AUX\adaptive_java_version\Docs\qad_enterprise_platform_class_6_java_extensions_training_guide.pdf.md`

Throughout this section **`DOC:` = `adaptive_java_version/Docs/qad_enterprise_platform_class_6_java_extensions_training_guide.pdf.md`** (line numbers are real, 1-indexed, verified against the read).

**What this document actually is** [CONFIRMED]: a Markdown/OCR conversion of a PowerPoint training deck — "Class 6: QAD Enterprise Platform – Java Extensions", by Don Springer (`DOC:5-9`), 43 slides (`DOC:893`). Agenda: Java Extension Overview / Initial Configuration / Extension Example (`DOC:17-21`). It is a **screen-by-screen IDE tutorial, not an API reference**. Large parts are OCR'd screenshot captions ("Screenshot of…", `DOC:511`, `DOC:541`, `DOC:618`), which means much of the technical substance is described rather than shown. This shapes everything below: the doc is strong on *click-path*, near-empty on *contract*.

---

### 1. Documented development workflow, end to end

| # | Stage | What the doc names | Cite | Label |
|---|---|---|---|---|
| 0 | Concept | "Java Extension is a Maven-based Java project that contains custom code." | `DOC:55` | [CONFIRMED] |
| 1 | Install JDK | `https://www.openlogic.com/openjdk-downloads`; choose **Version 17, Windows, x64, Package JDK**, click the **MSI** download | `DOC:139`, `DOC:143-145`, `DOC:151-158` | [CONFIRMED] |
| 2 | Install Maven | `https://maven.apache.org/` → link "Download, Install, Configure, Run" → "Download Latest Binary Zip file" | `DOC:197-199` | [CONFIRMED] |
| 3 | Extract Maven | "Maven does not require installation. Just extract the archive"; example `C:\Program Files\Maven\apache-maven-x.x.x` | `DOC:237-242` | [CONFIRMED] |
| 4 | Env vars | Verify `JAVA_HOME` points at the installed JDK; create/edit `MAVEN_HOME`; ensure `%MAVEN_HOME%\bin` is on `Path` | `DOC:285`, `DOC:306`, `DOC:326`, `DOC:334` | [CONFIRMED] |
| 5 | Verify | Run `java –version` and `mvn - version` (sic, spacing as printed) in Command Prompt | `DOC:394-398` | [CONFIRMED] |
| 6 | Install VS Code | `https://code.visualstudio.com/`, "Download For Windows" | `DOC:419-424` | [CONFIRMED] |
| 7 | Install Java tooling | Extensions panel → search **"Extension pack for Java"** → the one **by Microsoft** → Install | `DOC:438-444` | [CONFIRMED] |
| 8 | Get the QAD plugin | Download plugin **"Visual Studio Code plugin for Java Extensions"** (a ZIP); extract it; **inside the extracted contents extract `data.zip`**; locate `qad-java-sse-vscode-x.x.x.vsix` | `DOC:456-462` | [CONFIRMED] |
| 9 | Install the plugin | Gear icon → Extensions → ellipsis `(...)` → **"Install from VSIX…"** → select the `.vsix` → Install. "It is recommended to restart Visual Studio Code after the plugin installation." | `DOC:464`, `DOC:472`, `DOC:487`, `DOC:490-494` | [CONFIRMED] |
| 10 | Init project | Command Palette (**F1**) → **"QAD Extension: Init app"** (also written "QAD: Init app command") | `DOC:541-543`, `DOC:760` | [CONFIRMED] |
| 11 | Init prompt 1 | Environment URL, e.g. `https://aldpqjavaext01.environments.qad.com/clouderp`; found on the **My Development Settings** page, field **"VS Code Plugin Connection URL"** | `DOC:553-557` | [CONFIRMED] |
| 12 | Init prompt 2 | **Client ID** — "You can find it on the appropriate page or ask about it your environment Administrator"; screenshot is the **Client IDs management page showing Client ID, Client Secret, and Description fields** | `DOC:568-574` | [CONFIRMED] |
| 13 | Init prompts 3–4 | User email (example `mfg@qad.com`) then "Enter QAD password". "credentials of active webui user… user should have **Developer role**" | `DOC:582-592` | [CONFIRMED] |
| 14 | Init prompt 5 | "If login was successful, you should see a **list of apps** in which you can add Java extension. Let's select **Training**." | `DOC:602-604` | [CONFIRMED] |
| 15 | Result | "After saving of selected app, you should achieve an **empty project structure**" — folders `config`, `data`, `lib`, `src`, `target`; files `.gitignore`, `pom.xml`; workspace folder `urn_app_com.extensions.training` | `DOC:616-618` | [CONFIRMED] |
| 16 | Dependencies | Command Palette → **"QAD: Update app dependency"** (palette label: "QAD Extension: Update app dependency"). "Progress will be displayed below in the Terminal." | `DOC:628`, `DOC:634`, `DOC:642`, `DOC:759` | [CONFIRMED] |
| 17 | Dependency result | "Result of the command execution you can find in the **list of app dependencies**. It will include **services for each BC from the current app**." | `DOC:652` | [CONFIRMED] |
| 18 | Write the class | "Expand `src/main/java` path and via the right button click add a new class file into the **`training` folder**. Set **`Training.java`** as a name." | `DOC:664-666` | [CONFIRMED] |
| 19 | Paste code | "Copy code from the file, which provided in materials for current class. Put that code into your Training.java file." — **the real source is an external handout, not this doc** | `DOC:706-708` | [CONFIRMED] |
| 20 | Build + deploy | Command Palette (**F1**) → **"QAD Extension: Build and Deploy"** (prose: "QAD: Build and Deploy") | `DOC:752`, `DOC:758`, `DOC:775` | [CONFIRMED] |
| 21 | Build internals | Terminal shows `Executing task in folder urn_app_com.extensions.training: **mvn clean package**`; artifactId `training-server-side-extension`; `jar:3.3.0:jar`; `Building jar: …\urn_app_com.extensions.training\target\**com.extensions.training-ext-cust.jar**`; `BUILD SUCCESS` | `DOC:804`, `DOC:807`, `DOC:813-816` | [CONFIRMED] |
| 22 | Deploy confirmation | "no errors in the Terminal and the notification about successful deploy of extension" / "Extension building and deploying is successfully completed" | `DOC:824-826` | [CONFIRMED] |
| 23 | Test | Open Training screen, click **New** → StartDate prefilled with current date; set Capacity to 0, save → error "Capacity is mandatory"; restore → saves | `DOC:836-838`, `DOC:878-881` | [CONFIRMED] |
| — | Undeploy | Palette command **"QAD Extension: Undeploy"** exists; plugin capability list includes "undeploying an extension" | `DOC:81`, `DOC:634`, `DOC:761` | [CONFIRMED] — **see §5 finding F1** |

**Tools/commands/files named anywhere in the doc** [CONFIRMED]: OpenLogic OpenJDK (`DOC:139`), Apache Maven (`DOC:197`), VS Code (`DOC:421`), "Extension Pack for Java" v0.29.0 by Microsoft (`DOC:450`), `qad-java-sse-vscode-x.x.x.vsix` (`DOC:462`), `data.zip` (`DOC:460`), `pom.xml` (`DOC:618`), `.gitignore` (`DOC:618`), `Training.java` (`DOC:666`), `java -version` / `mvn -version` (`DOC:396-398`), `mvn clean package` (`DOC:804`), `com.extensions.training-ext-cust.jar` (`DOC:814`), env vars `JAVA_HOME`/`MAVEN_HOME`/`Path` (`DOC:290-291`, `DOC:334`).

**Reference build environment printed in the doc** [CONFIRMED]: `openjdk version "17.0.18" 2026-01-20`, `Apache Maven 3.9.12`, Maven home `C:\Program Files\Maven\apache-maven-3.9.12`, JDK runtime `C:\Program Files\OpenLogic\jdk-17.0.18.8-hotspot`, Windows 11 amd64 (`DOC:377-388`). **Contradicted by its own screenshots** — see §3.

**ABSENT — stated plainly** [CONFIRMED by absence, whole-file read]: the doc contains **zero HTTP endpoints, zero URL paths, zero payload keys, zero header names, zero `pom.xml` content, zero `MANIFEST.MF` content, zero `mvn install:install-file` invocation, and zero dependency-jar filename**. Nothing in the file matches `oauth`, `api/`, `qracore`, `upload-packages`, `appURI`, `install-file`, or `MANIFEST`. Every server interaction is hidden behind a palette command name.

---

### 2. Class / API surface as described

Everything below is derived from exactly two code blocks (`DOC:710-748`, the full listing; `DOC:785-800`, a shorter repeat) plus one prose slide (`DOC:108-118`).

| Element | Exact form in the doc | Cite | Label |
|---|---|---|---|
| Marker annotation | `@Extension` (on the class, no attributes) | `DOC:718`, `DOC:793` | [CONFIRMED] |
| Class declaration | `public class Training extends TrainingBaseService` | `DOC:719`, `DOC:794` | [CONFIRMED] |
| Base-class naming | `<BC>BaseService` — only the single instance `TrainingBaseService` for BC `Training` | `DOC:719` | [CONFIRMED] pattern is [INFERRED] from n=1 |
| `initialize` | `public void initialize(Output<TrainingDataSet> dsTraining) throws BCExecutionError` | `DOC:720`, `DOC:795` | [CONFIRMED] |
| `create` | `@Override`<br>`public void create(InputOutput<TrainingDataSet> dsTraining) throws BCExecutionError` | `DOC:725-726` | [CONFIRMED] |
| `update` | `@Override`<br>`public void update(InputOutput<TrainingDataSet> dsTraining) throws BCExecutionError` | `DOC:733-734` | [CONFIRMED] |
| `delete` / `fetch` / `exists` | **never appear anywhere in the file** | — | [CONFIRMED absent] |
| Super calls | `super.initialize(dsTraining);` · `super.create(dsTraining);` · `super.update(dsTraining);` | `DOC:721`, `DOC:730`, `DOC:738` | [CONFIRMED] |
| Wrapper types | `Output<T>` (initialize) vs `InputOutput<T>` (create/update) | `DOC:720`, `DOC:726` | [CONFIRMED] |
| Unwrap | `dsTraining.getValue()` → the DataSet | `DOC:722`, `DOC:742` | [CONFIRMED] |
| Temp-table accessor | `getTtTraining()` returns an **array**: `getTtTraining()[0]` assigned to `TrainingRecord training` | `DOC:722`, `DOC:742` | [CONFIRMED] |
| Record setter | `.setStartDate(LocalDateTime.now())` | `DOC:722` | [CONFIRMED] |
| Record getter | `training.getCapacity()`, compared `== null \|\| == 0` → boxed numeric, nullable | `DOC:743` | [CONFIRMED] (`Integer` vs `Long` [INFERRED]) |
| Validation add | `this.addValidationError("Capacity is mandatory");` — single String arg, `this.`-qualified | `DOC:744` | [CONFIRMED] |
| Validation throw | `throwAddedValidationErrors();` — no args, **unqualified**, called *before* `super.create/update` | `DOC:728`, `DOC:736` | [CONFIRMED] |
| Declaring class of those two | **never stated** — no `BaseBC` mention in the file | — | [CONFIRMED absent]; inherited from `TrainingBaseService`'s hierarchy [INFERRED] |
| Checked exception | `BCExecutionError`, imported `com.qad.ipc.dto.BCExecutionError` | `DOC:713`, `DOC:788` | [CONFIRMED] |
| Imports shown | `com.extensions.training.training.TrainingDataSet`<br>`com.extensions.training.training.TrainingRecord`<br>`com.qad.ipc.dto.BCExecutionError`<br>`com.qad.ipc.dto.InputOutput`<br>`java.time.LocalDateTime` | `DOC:711-716` | [CONFIRMED] |
| Imports **missing** | Listing starts at **source line 6** → the `package` statement and lines 1–5 are cropped. **No import shown for `Extension`, `Output`, or `TrainingBaseService`.** | `DOC:711` (gutter "6"), `DOC:786` | [CONFIRMED absent] — `Output` is probably `com.qad.ipc.dto.Output` by symmetry with `InputOutput` [INFERRED] |
| Error surfacing (runtime) | Web UI "Errors" grid with columns **Field / Error / Error ID**; row: (blank), `Capacity is mandatory`, `JEF202606035.` | `DOC:871-875`, `DOC:887` | [CONFIRMED] — `JEF` prefix + date-ish body; scheme not explained [INFERRED] |

**"Java Extension APIs" — named as capabilities only, with no types or signatures** [CONFIRMED]: `DOC:110-118` says the framework provides "a library of helper classes, known as the Java Extension APIs" that let you (verbatim bullets) "execute SQL Queries: securely fetch data directly from the database", "access Session Context: get the current user ID, role, and domain", "get translations: retrieve localized labels and messages", "**log Messages: write custom messages to the extension log file**", "make HTTP Calls: interact with external web services and APIs". **Not one class name, method name, or import is given for any of these five, including logging.** Also at `DOC:95-98`: "reading, creating, and modifying data in the target Business Component", "creating extensions for both coded and platform Business Components", "creating multiple extensions for the same Business Component", "calling other Business Components to orchestrate complex processes" — again with no API shown.

---

### 3. Constraints and rules the doc actually states

| Rule | Doc says | Cite | Label |
|---|---|---|---|
| Call `super` | Never stated as a rule. Implied twice: workflow row "Extension code calls Progress BL back with **super.create() method call**" (`DOC:67`) and the example's three `super.*` calls (`DOC:721`, `730`, `738`). | `DOC:67`, `DOC:721`, `DOC:730`, `DOC:738` | [INFERRED] — doc contains no "must", "always", or "required" statement about `super`. Confirmed only by decompiling the base service or by testing an override that omits it. |
| Ordering | `initialize`: `super` **first**, then mutate defaults. `create`/`update`: validate → `throwAddedValidationErrors()` → **then** `super`. | `DOC:721-722`, `DOC:727-730`, `DOC:735-738` | [CONFIRMED from the example]; that this ordering is *mandatory* is [INFERRED] |
| `@Override` usage | `create` and `update` carry `@Override`; **`initialize` does not** (`@Extension` at `DOC:718`, class at `719`, `initialize` at `720` with no annotation between). Repeated identically in the second listing. | `DOC:718-720`, `DOC:725`, `DOC:733`, `DOC:793-795` | [CONFIRMED] — likely a slide sloppiness rather than a rule [INFERRED] |
| One class per BC | **Never stated.** The opposite is stated as a *capability*: "creating **multiple extensions for the same Business Component**". | `DOC:97` | [CONFIRMED] |
| Coded vs platform BCs | "supported by platform and coded BCs"; "creating extensions for both coded and platform Business Components" | `DOC:44`, `DOC:96` | [CONFIRMED] |
| Upgrade safety | "are separated from the core QAD application and, as a result, are **upgrade-safe**" | `DOC:45` | [CONFIRMED] |
| Java version | **Internally contradictory.** Prose instructs **Java 17** (`DOC:135`, `DOC:143`, `DOC:158` "17.0.18+8") and the verify transcript shows 17.0.18 (`DOC:378-385`). But the installer screenshot says "OpenLogic-OpenJDK JDK with Hotspot **8u432-b06** (x64)" (`DOC:179-181`) and **both** env-var tables show `JAVA_HOME = C:\Program Files\OpenLogic\jdk-**8.0.432.06**-hotspot\` (`DOC:290`, `DOC:312`), with a directory listing of `jdk-8.0.412.08-hotspot` / `jdk-8.0.432.06-hotspot` (`DOC:298`). | as cited | [CONFIRMED contradiction] |
| `pom.xml` `java.version` / source-target level | **Never shown.** `pom.xml` appears only as a filename in the project tree. | `DOC:618`, `DOC:634` | [CONFIRMED absent] |
| Packaging / manifest rules | **Nothing.** No `MANIFEST.MF`, no `App-Name`, no `Low-Code-Artifact-Type`, no shading/relocation rules, no "don't bundle dependencies" guidance. | — | [CONFIRMED absent] |
| Naming — file/class | Class file **`Training.java`** placed in the **`training` folder** under `src/main/java` — i.e. class simple name == BC name. | `DOC:664-666`, `DOC:719` | [CONFIRMED] |
| Naming — package | Generated types live in `com.extensions.training.training` (app package + BC segment, both lowercase) | `DOC:711-712` | [CONFIRMED]; extension class's own package [CONFIRMED absent] (cropped line 1) |
| Naming — workspace folder | `urn_app_com.extensions.training` (`urn_app_` + full app name) | `DOC:618`, `DOC:634`, `DOC:805` | [CONFIRMED] |
| Naming — Maven artifactId | `training-server-side-extension` | `DOC:807`, `DOC:810`, `DOC:813` | [CONFIRMED] |
| Naming — output jar | `target\com.extensions.training-ext-cust.jar` = `target/<fullAppName>-ext-cust.jar` | `DOC:814` | [CONFIRMED] |
| Forbidden things | **Nothing is declared forbidden anywhere in the file.** | — | [CONFIRMED absent] |
| Required user role | webui user must have **Developer role** to init/login | `DOC:592` | [CONFIRMED] |

---

### 4. Deployment semantics

| Question | Doc answer | Cite | Label |
|---|---|---|---|
| Whole-jar replacement vs incremental | **Silent.** Only "Build and Deploy" and a success notification. | `DOC:775`, `DOC:824-826` | [CONFIRMED absent] |
| Undeploy | **Documented as existing.** Plugin capability list: "undeploying an extension" (`DOC:81`); palette entries "QAD Extension: Undeploy" (`DOC:634`, `DOC:761`). **No semantics, no confirmation screen, no worked example.** | `DOC:81`, `DOC:634`, `DOC:761` | [CONFIRMED that the doc claims it] |
| Rollback / versioning | **Silent.** No mention of versions, history, or reverting. | — | [CONFIRMED absent] |
| Multiple extensions per BC | Explicitly listed as a supported capability: "creating multiple extensions for the same Business Component". **No ordering/precedence/chaining rules given.** | `DOC:97` | [CONFIRMED] |
| App dependencies → which BaseService stubs exist | "Result of the command execution you can find in the list of app dependencies. **It will include services for each BC from the current app.**" Slide caption: "Maven dependencies for a server-side extension"; the app is chosen at Init time from a server-provided app list. | `DOC:650-652`, `DOC:602-604` | [CONFIRMED] — the dependency jar is app-scoped and stubs are per-BC |
| Listing / reading back what is deployed | **Silent.** No palette command, screen, or endpoint for "list deployed extensions". The only four QAD palette commands anywhere in the file are Init app, Update app dependency, Build and Deploy, Undeploy. | `DOC:634`, `DOC:758-761` | [CONFIRMED absent] |
| Runtime dispatch model | Workflow table: Web UI save → request to **Progress BL** → "Java Extension for this BC exists?" → if yes, "Progress BL triggers execution of overridden 'create' method in JEF" → extension runs → "Extension code calls Progress BL back with `super.create()`" → data returned to Web UI. (Table's step numbering is garbled by OCR: two rows numbered 5 and two numbered 6.) | `DOC:59-69` | [CONFIRMED; numbering garble noted] |

---

### 5. RECONCILIATION against the commissioner's confirmed facts

Verdicts are about **this document only**. I did not re-derive any confirmed fact.

| # | Confirmed fact | Verdict | Doc evidence / cite |
|---|---|---|---|
| 1 | Login: `POST {envUrl}oauth/token` with `client_id`, `grant_type=password`, `username`, `password` **in the query string** | **SILENT** (weakly consistent) | Doc shows only the four interactive prompts that supply those values: environment URL `https://aldpqjavaext01.environments.qad.com/clouderp` (`DOC:555`), **Client ID** (`DOC:572`), user email (`DOC:584`), password (`DOC:588`), plus "If login was successful…" (`DOC:604`). No endpoint, no method, no `grant_type`, no statement about query-string vs body. Consistent with the confirmed fact; corroborates nothing. |
| 2 | Dependency jar: `GET {envUrl}api/qracore/sse?appURI={appURI}` → `application/java-archive` | **SILENT** | Only the command name "QAD Extension: Update app dependency" (`DOC:628`, `DOC:759`), "Progress will be displayed below in the Terminal" (`DOC:642`), and the result description (`DOC:652`). No URL, no `appURI`, no content type. A `lib` folder exists in the scaffold (`DOC:618`) but the doc never says a jar lands there. |
| 3 | Deploy: `POST {envUrl}api/qracore/sse/upload-packages?appURI={appURI}`, multipart, form field `"files"` | **SILENT** | Only "QAD Extension: Build and Deploy" (`DOC:758`, `DOC:775`) and the success notification (`DOC:826`). Zero transport detail. |
| 4 | Build: `mvn install:install-file` of `qad-ext-dependencies.jar`, then `mvn clean package` → `target/<fullAppName>-ext-cust.jar` | **PARTIAL AGREE** | **AGREES** on `mvn clean package`: verbatim `Executing task in folder urn_app_com.extensions.training: mvn clean package` (`DOC:804`). **AGREES** on the artifact path/pattern: `Building jar: …\target\com.extensions.training-ext-cust.jar` (`DOC:814`) where fullAppName = `com.extensions.training` (`DOC:618`). **SILENT** on `mvn install:install-file` and on the name `qad-ext-dependencies.jar` — neither string occurs in the file. |
| 5 | `pom.xml` targets `java.version` **1.8**; manifest carries `App-Name` and `Low-Code-Artifact-Type=extension` | **SILENT on both, with a LOUD Java-version contradiction inside the doc itself** | `pom.xml` is only ever a filename (`DOC:618`, `DOC:634`); its content is never shown → SILENT on `java.version`. No manifest content anywhere → SILENT on `App-Name` / `Low-Code-Artifact-Type`. **Finding F2 (below):** the doc's *prose* mandates JDK **17** (`DOC:135`, `DOC:143`, `DOC:158`) and its verify transcript prints 17.0.18 (`DOC:378-385`), while its *screenshots* show JDK **8u432 / `jdk-8.0.432.06-hotspot`** (`DOC:179-181`, `DOC:290`, `DOC:312`). The confirmed `java.version=1.8` aligns with the screenshots and **conflicts with the doc's headline instruction**. |
| 6 | `@Extension` marker; `class extends <BC>BaseService`; override `create`/`update`/`delete`/`initialize`/`fetch`/`exists` | **PARTIAL AGREE** | **AGREES:** `@Extension` (`DOC:718`, `DOC:793`), `extends TrainingBaseService` (`DOC:719`), `create` (`DOC:726`), `update` (`DOC:734`), `initialize` (`DOC:720`). **SILENT:** `delete`, `fetch`, `exists` never appear in the file — the doc gives no hint that the base class has more than these three hooks. |
| 7 | `addValidationError` / `throwAddedValidationErrors` on `BaseBC` | **PARTIAL AGREE** | **AGREES** on the method names and usage: `this.addValidationError("Capacity is mandatory")` (`DOC:744`), `throwAddedValidationErrors()` called at `DOC:728` and `DOC:736` before `super`. **SILENT** on the declaring class — the string `BaseBC` does not occur in the file; both calls are unqualified/`this.`, so the doc only establishes they are inherited. |
| 8 | DataSet exposes records as an **ARRAY** via ABL temp-table naming, e.g. `TrainingDataSet.getTtTraining()` → `TrainingRecord[]` | **AGREE** | `dsTraining.getValue().getTtTraining()[0].setStartDate(...)` (`DOC:722`) and `TrainingRecord training = dsTraining.getValue().getTtTraining()[0];` (`DOC:742`) — array indexing plus assignment to `TrainingRecord` confirms element type. The `tt` prefix is visible in the getter name; the doc never *explains* the ABL temp-table naming convention. |
| 9 | **No undeploy command; no endpoint for listing/reading back what is deployed** | **DISAGREE on undeploy** / SILENT on listing | See **Finding F1** below. |

---

#### 🚩 FINDING F1 — DOC CONTRADICTS CONFIRMED FACT: undeploy

The docs assert an undeploy capability **three separate times**:

- `DOC:76-81` — "This plugin provides all the necessary tools for the development lifecycle, including: setting up the correct project structure. / managing dependencies. / deploying the extension to a QAD environment. / **undeploying an extension.**"
- `DOC:634` (OCR of the Command Palette screenshot) — `QAD Extension: Init app … QAD Extension: Undeploy urn_app_com.extensions.training …`
- `DOC:761` (Command Palette table) — `| QAD Extension: Undeploy | |`

The commissioner's confirmed set (decompile of `qad-java-sse-vscode` **1.0.10** + live deploy) says **no undeploy command**. These cannot both be true as stated. Possible reconciliations, ranked (all [INFERRED]): (a) the palette command is **registered in `package.json` but its handler is a no-op / local-only cleanup**, so a decompile focused on HTTP calls finds no undeploy *endpoint* while the command still appears in the UI; (b) the deck was authored against a **different plugin version** than 1.0.10; (c) the command exists and calls an endpoint that was simply not exercised in the live deploy. **Action for the generator:** do **not** emit undeploy tooling or promise rollback. Confirm by grepping the VSIX `package.json` `contributes.commands` for an undeploy id and tracing its handler.

#### 🚩 FINDING F2 — DOC SELF-CONTRADICTS ON JAVA VERSION (and its headline instruction conflicts with the confirmed `1.8` target)

Prose/instructions: JDK **17** (`DOC:135`, `DOC:143`, `DOC:151-158`, verify transcript `DOC:377-388`). Screenshots/env tables: JDK **8** (`DOC:179-181`, `DOC:290`, `DOC:298`, `DOC:312`). Confirmed fact: `pom.xml` sets `java.version` **1.8**. **A developer following the doc literally installs JDK 17 and builds a project whose POM targets 1.8** — which works (17 can target 1.8 via source/target, modulo `-source 8` deprecation warnings) [INFERRED], but the deck gives the reader no way to know the target level, because it never shows `pom.xml`. This is a real doc defect, not just an OCR artifact: the deck is a Java-8-era deck with the JDK-17 slides swapped in and the screenshots left stale.

#### 🚩 FINDING F3 — THE DOC IS NOT SELF-SUFFICIENT TO WRITE A CLASS

- `DOC:706-708`: "Copy code from the file, which **provided in materials for current class**." The canonical source is an **external handout not present in this file**.
- Both code listings begin at **source line 6** (`DOC:711` gutter "6"; `DOC:786` gutter "6"), so the **`package` declaration and imports 1–5 are cropped**. There is therefore **no import shown for `@Extension`, `Output`, or `TrainingBaseService`** — the three symbols an LLM most needs. A generated file using only this doc will not compile.
- `DOC:743-746` in the listing has **broken brace indentation** (the `if` body and closing braces are mis-indented by OCR), so the listing is not even copy-pasteable verbatim.

#### Minor discrepancies (non-blocking) [CONFIRMED]

- Command names are written inconsistently: "QAD: Init app command" (`DOC:543`) vs "QAD Extension: Init app" (`DOC:760`); "QAD: Build and Deploy" (`DOC:775`) vs "QAD Extension: Build and Deploy" (`DOC:758`); "QAD: Update app dependency" (`DOC:628`) vs "QAD Extension: Update app dependency" (`DOC:759`). The palette screenshots (`DOC:634`, `DOC:758-761`) use the `QAD Extension:` prefix — treat that as authoritative [INFERRED].
- `initialize` lacks `@Override` while `create`/`update` have it (`DOC:718-720` vs `DOC:725`, `DOC:733`).
- The workflow table's step numbers repeat (5, 6, then 5, 6 again — `DOC:64-69`).
- Slide says "let's implement **two** additional requirements" then re-says "let's add two additional requirements" for what is requirement 2 (`DOC:509`, `DOC:526`).
- The scaffold contains `config` and `data` folders (`DOC:618`) whose purpose is **never explained anywhere in the file**.

---

### 6. What a Java-extension DOCS BUNDLE for an LLM must contain

**What this doc contributes that is worth keeping** [CONFIRMED]: the exact worked example (`DOC:710-748`), the palette command names (`DOC:758-761`), the build command + output-jar naming (`DOC:804`, `DOC:814`), the scaffold layout (`DOC:618`), the app-scoped dependency semantics (`DOC:652`), the Developer-role requirement (`DOC:592`), and the runtime error-panel shape Field/Error/Error ID with `JEF…` ids (`DOC:873-875`).

**What it cannot contribute, and must be sourced elsewhere (decompile / live probe)** [CONFIRMED absent from this file]: every HTTP contract, the whole `pom.xml`, the manifest keys, the dependency-jar filename and `install:install-file` step, the `Extension`/`Output`/`TrainingBaseService` imports and package line, the full hook list (`delete`/`fetch`/`exists`), the declaring class of the validation methods, and **all five "Java Extension APIs"** including logging.

Recommended bundle outline (each item tagged with whether this doc can supply it):

1. **`00_CONTRACT_CARD.md`** — one screen, always in context: `@Extension`; `extends <BC>BaseService`; hook signatures verbatim; `Output<T>` for `initialize` vs `InputOutput<T>` for `create`/`update`; `throws BCExecutionError`; call-`super` rule; validate-then-`throwAddedValidationErrors()`-then-`super` ordering. *Doc supplies signatures (`DOC:720`, `726`, `734`) — NOT the super rule as a rule (see §3).*
2. **`01_IMPORTS_AND_PACKAGE.md`** — the literal first 6 lines of a valid file: `package …;` plus fully-qualified imports for `Extension`, `Output`, `InputOutput`, `BCExecutionError`, and the generated `…<bc>.<Bc>DataSet` / `<Bc>Record`. **The single highest-value page, and the one this doc is missing (F3).** *Doc supplies only 5 of them (`DOC:711-716`).*
3. **`02_GOLDEN_EXAMPLE.java`** — a complete, compiling `Training.java` including package + all imports, with a default-value hook, a validation hook, and a comment marking every mandatory line. *Doc's version is truncated and mis-braced (`DOC:710-748`).*
4. **`03_HOOKS.md`** — full table of overridable methods (`initialize`, `fetch`, `exists`, `create`, `update`, `delete`) with exact signatures, wrapper type per hook, when the platform invokes each, and whether `super` goes first or last. *Doc covers 3 of 6.*
5. **`04_DATASET_SHAPE.md`** — the ABL temp-table → Java mapping rule: `getTt<TableName>()` returns `<Table>Record[]`; **arrays not Lists**; nested/child temp tables; nullable boxed scalars; `LocalDateTime` for datetime fields; how to iterate all rows rather than `[0]`. *Doc shows `[0]` only (`DOC:722`, `DOC:742`) — an LLM copying it will write single-row-only code, a real correctness trap worth calling out explicitly.*
6. **`05_VALIDATION_AND_ERRORS.md`** — `addValidationError(String)`, `throwAddedValidationErrors()`, declaring class, any field-scoped overloads, `BCExecutionError` semantics, and how errors render (Field / Error / Error ID, `JEF` prefix). *Doc supplies usage + UI shape (`DOC:744`, `728`, `873-875`); not the declaring class or overloads.*
7. **`06_HELPER_APIS.md`** — the five capability areas from `DOC:112-118` turned into real class + method signatures: SQL query, session context (user id / role / domain), translations, **logging**, HTTP client. *Doc names them and gives nothing else — must be decompiled.*
8. **`07_PROJECT_AND_BUILD.md`** — full `pom.xml` template (parent/artifactId `<bc>-server-side-extension`, `java.version`, manifest `App-Name` + `Low-Code-Artifact-Type=extension`), the `mvn install:install-file` bootstrap for the dependency jar, `mvn clean package`, output `target/<fullAppName>-ext-cust.jar`, scaffold tree (`config`, `data`, `lib`, `src`, `target`, `.gitignore`, `pom.xml`), workspace folder `urn_app_<fullAppName>`. *Doc supplies the tree (`DOC:618`), the build command (`DOC:804`), and the jar name (`DOC:814`) — nothing else.*
9. **`08_SERVER_PROTOCOL.md`** — login, dependency-jar fetch, upload-packages deploy, with exact URLs/params/field names. *Doc is 100% silent; this page exists only because of the decompile.*
10. **`09_LIMITS_AND_GOTCHAS.md`** — no undeploy (**flagging F1: docs claim one, reality says no**), no readback/list endpoint, no rollback, deploy semantics unknown (whole-jar assumed), multiple extensions per BC allowed with unspecified ordering (`DOC:97`), Developer role required (`DOC:592`), JDK-17-toolchain-targeting-1.8 (**F2**).
11. **`10_NAMING.md`** — one deterministic table the generator can key off: BC `Training` → class `Training` → file `src/main/java/.../training/Training.java` → base `TrainingBaseService` → dataset `TrainingDataSet` → record `TrainingRecord` → getter `getTtTraining()` → package `com.extensions.<app>.<bc>` → jar `<fullAppName>-ext-cust.jar`. *All derivable from `DOC:664-666`, `DOC:711-712`, `DOC:719`, `DOC:722`, `DOC:814` — but from a single example, so the generalization is [INFERRED].*

---

---

## B3. Adaptive Docs — Business Components, Extensions, Relations, Formulas, Lookups

**Citation convention for this section.** Two source files were read end-to-end (1446 and 2699 lines respectively). To keep citations short, two aliases are used; every line number below is real and was read:

- `C2` = `adaptive_java_version/Docs/qad_enterprise_platform_class_2_Business_Component_training_guide.pdf.md`
- `C3` = `adaptive_java_version/Docs/qad_enterprise_platform_class_3_Extensions_Relations_Formulas_training_guide.pdf.md`
- AUX-side citations use ordinary relative paths from `aux_web_version/`.

Both docs are Markdown transcriptions of slide decks ("By Don Springer", C2:7, C3:7). Much of the content is OCR'd slide text plus *image captions* (lines beginning "Screenshot of…"). Where a fact exists only inside an image caption, this is flagged, because the caption is a describer's paraphrase, not platform text.

---

### 1. BUSINESS COMPONENT creation — the documented end-to-end sequence

This is the order as the docs walk it. Step numbers are mine; the doc has no numbered master list. [CONFIRMED] unless marked.

**Phase A — App container (prerequisite, done once)**

1. **Create the App.** Menu → "Apps" (C2:45) → click New (C2:55). "App is a container which includes one or several business components according to their business logic" (C2:57).
2. **Fill App fields**: Display Name, Description → Save (C2:69–72). Fields visible on the screen are *App URI, App Label, Description* (C2:65). App URI takes the form `urn:app:com.extensions.training` (C2:80).
3. **App Dependencies**: "By default, all Apps depend on QRA Core" — `urn:app:com.qad.qracore`, shown as **Implicit** (C2:80–84).
4. **Set Active App.** Menu → "My Developer Settings" → Active App dropdown = **"Use Custom"** → search/select the new App → Save (C2:94–98, C2:111, C2:121).
5. *(Optional)* **Saved-To default.** "Save New Artifacts to Configuration Data as Default" checkbox in My Developer Settings (C2:237–241). In Dev you may choose App Data or Configuration Data; "Production or Test Environment: All new artifacts are saved in Configuration Data." (C2:243–251).

**Phase B — Business Component**

6. **Menu → "Business Components" → New** (C2:698, C2:709).
7. **Main tab**: set *Business Component*, *Label*, *Physical Table*, *Description*; set **Scope = System** (C2:737–744). The full Main/Options field set is enumerated at C3:916–935: `Business Component, Status, Business Component Type, Business Component URI, Business Component Label, Secure URI, Physical Table, App, Description, App URI, Scope` plus Options `Embedded, Approvals, Business Document, Not Extensible`.
8. **Fields — Import.** "Select Import to Import Field Definitions from Excel" (C2:756). Dialog: *Data Source Type* = File, *Source File* → Choose file → Import (C2:767–773). Spreadsheet shape: "Column Headings - Field Names / Subsequent Rows - Data Records" (C2:786–787). Fields can also be added one at a time with **New** in the Fields panel (C3:2068, C3:2118).
9. **Set Primary Key ordinals + Length + Format.** "1. Set Primary Key: ClassName is 1; Location is 2. 2. Set Character Fields to Length 32. The format will be set as x(32) automatically. 3. Set DurationDays and Capacity fields format to '>9'." (C2:800–806).
10. **Drop-Down Lists** (optional): "Scroll down to Drop-Down Lists and Create New. List 'Area of Study' with children: Purchasing, Inventory, Financial, Manufacturing, and Distribution. Click Save" (C2:818). Then return to the field line and change its **Data Type to "Drop Down"**, then choose the list (C2:831, C2:837).
11. **Field Groups** (optional, explicitly skipped in the exercise): "1 Create Field Group. 2 Assign Fields." — used to grant per-Role update rights (C2:867–870).
12. **Save the Business Component** (C2:880).
13. **Do NOT Deploy yet.** "if you do that you will get the validation error" — the two errors are verbatim: `There should exist at least one View.` and `There should exist at least one Form.` (C2:894–903). "Next step is to create Form and View." (C2:898).
14. **Form**: scroll to Form panel → **Build Form** (C2:918). "You will find that a Panel was already added, and you can change the label" (C2:938). Then: "1. Expand Fields > Default… 2. Proceed to drag fields into the Training Panel. 3. You can also add fields to the Summary Panel. 4. Save changes and Close Form Builder." (C2:951–957).
15. **Browse**: scroll to Browse panel → New (C2:969). Critical constraint: **"If you don't have any browses, you will be able to create only 'Form Only' views."** (C2:971). Then "1. Set Browse Label… 2. In Fields panel select the Fields you want displayed in the Browse. 3. Click Save and Close" (C2:979–983). Browse Main fields: *Browse Label, Browse URI, Description*, plus a `View Browse Query` button (C3:1083–1089).
16. **View**: scroll to Views panel → New (C2:999). "1. Set View Label… 2. Ensure that check boxes are checked as shown (which is the default). 3. In Browse panel choose earlier created Training browse. 4. Click Save and Close" (C2:1010–1016). View properties observed: *Type = Hybrid Browse*, *Default*, *Eligible for Menu*, *Allow New*, *Allow Edit*, *Allow Delete* (C2:1018; itemised again at C3:1640–1659).
17. **Deployment**: Deployment panel has *Data Store URI* (search icon) and *Import Data* checkbox and a Deploy button (C2:890–892). Select the data store (C2:1032); **"a Data Store must be in Development Mode in order to save a new Business Component"** (C2:1047). Click Deploy (C2:1057).
18. **Run it**: Views panel → **Preview**, or Menu search on the View name (C2:1069–1071).

**BC screen tab order as the docs render it** (image caption, C2:878): `Main, Fields, Relationships, Business Services, Form, Browses, Views, Java Extensions, Deployment`. [CONFIRMED that this string is in the file; it is an image caption, so it describes a screenshot rather than being platform text.]

**Post-deployment mutation rules**

19. "Once Business Component is deployed, you are still able to add fields, but you cannot change a field name, type, length or format" (C2:1240).
20. **Undeploy**: only possible if suspended (C2:1271). Business Components screen → select → **Actions → "Revert to Initial"** (C2:1273). Dialog verbatim: *"The status will be changed to 'Suspended'. To complete the revert to 'Initial' status, run the required YAB command."* (C2:1283). Then on the server: `yab stop`, `yab database-extension-obsolete-schema`, `yab start` (C2:1358–1362), run from `cd /dr01/qadapps/systest` (C2:1330). Afterwards "the Business Component will be in the Initial state" (C2:1375). **Data is destroyed**: "we lost the content data… It happened because DB table was physically removed. If you want to save your data, Export records before the Undeploy." (C2:1427–1433).

**What is NOT in the documented sequence** (plain absences, worth stating):
- **No permissions/role step.** Roles appear only as a note attached to Field Groups (C2:867) and in the Configuration-Data artifact list ("Field Security", C2:188; "Role, Menu, & Permissions", C2:218). No permission artifact is created anywhere in the BC walk-through.
- **No "dataset" / "temp-table" concept.** A grep for `temp-table|temptable|dataset` across both files returns zero hits. The physical-storage concept in these docs is **Physical Table** (C2:741, C3:924) and **Data Store** (C2:1041–1047).
- **No lookup step inside the initial BC creation.** Lookups are introduced only later, as a *field-level* add-on requiring a redeploy (see §5).

---

### 2. FIELD definition

**Fields-grid columns (verbatim, widest instance, C3:799):**
`Primary Key | Field | Field Label | Physical Field | Formula | Lookup | Data Type | Length | Format | Currency | DI`
A **Required** column also exists (C3:127). The Fields panel toolbar is `New | Delete | Details | More | Import` (C3:2044).

**Data types observed** (all [CONFIRMED] from field tables):
| Data Type | Cited at |
|---|---|
| Character | C2:1232, C3:153 |
| Integer | C2:1231, C3:157 |
| Decimal | C3:2145 |
| Date | C3:1009 |
| Datetime | C2:1236 |
| Logical | C3:430 ("Set Logical Data Type for 'Exporter'") |
| Drop Down (Character) | C2:829, C3:2146 |

**Formats observed** (verbatim): `x(32)` C2:1232 · `x(3)` C3:801 · `x(16)` C3:806 · `>9` C2:1231 · `>>9` C3:157 · `>>9.99` C3:2124 · `->,>>>,>>9` C2:1233 · `>>>,>>>,>>9` C3:803 · `99/99/9999` C3:1009 · `99/99/9999 HH:...` C2:1236 (truncated in source).

**Format auto-derivation:** setting Character Length 32 sets format `x(32)` automatically (C2:802–804). Only stated for Character.

**Naming**: every worked example sets *Field* and *Physical Field* to the same PascalCase, space-free token, with *Field Label* being the spaced human form — e.g. "'Field' and 'Physical Field' values are 'StudentCount'. 'Field Label' is 'Student Count'." (C3:2082–2084); same pattern at C3:2120–2122, and throughout the field tables (C3:100–106, C3:799–807). [INFERRED] that this is the required convention — **the docs never state a naming rule**; they only demonstrate it consistently. Confirmation would need the platform's field-name validator or a QAD naming-rules doc.

**Required flag semantics (the one explicit rule about Required):**
> "if parent BC has key-field which could be empty, you should uncheck Required checkbox for appropriate key-filed in your extension." (C3:136)

**Anything resembling form-field normalization?** [CONFIRMED ABSENCE] Neither doc contains any notion of normalizing/canonicalizing field names for a form payload. The closest documented mechanisms are:
- **Field Overrides** — "a mechanism which allow you to modify already existing field. You can make field mandatory, define default value, change label or field format." Reachable "in the Design Layout or from Business Component > Fields > Details > Overrides" (C2:458–462). The override set, verbatim (C2:656–663): `Field Label Override, Required Override, Default Value Override, Length Override, Format Override`, plus `Saved To, Remarks, Last Modified By, Last Modified Date`. Overrides are keyed on the **Field** (`postalFormat`) and note "Changes to these properties affect all layouts for this business component" (C2:649–651).
- **Translations** as label sources: create a String Code (e.g. `ZIP_CODE_POSITION`, C2:592), add per-locale text (C2:602), then pick it in Field Label Override via the lookup icon — stored value shows as `CNFG:ZIP_CODE_POSITION` (C2:657). Standard QAD labels use a `mfg-` prefix, e.g. `mfg-COUNTRY`, `mfg-DESCRIPTION`, `mfg-CURRENCY` (C3:1593–1595), `mfg-ZIP_CODE` (C2:626).
- **Generalized Codes auto-conversion** (the only automatic field mutation documented):
> "Add into Generalized Codes a field that you want to make as a Drop-down list · The field must have Character data type and should not be defined as a lookup. · The Physical Field Name must match the name of the Generalized Code field. System will convert that field into lookup automatically · You can also just use the name of an existing Generalized Code such as 'stat' as the physical field name." (C2:849–855)
Restated at C3:615. Generalized Code record fields: *Field Name, Value, Comments, Group* (Group = `APP` in the example) (C3:644–647). After adding codes you must clear caches (see §7).

---

### 3. EXTENSIONS

**Definition (verbatim, C3:33):**
> "Extensions is a way to add additional information into existing business component. Platform supports different types of extensions which could be useful in different scenarios."

**Kinds available** — three, all [CONFIRMED]:

| Kind | Cardinality | UI result | Cited |
|---|---|---|---|
| Many-to-One extension | Many to one | **Embedded grid** on the parent form | C3:39, C3:242–244 |
| One-to-one extension | One to one | **Panel** with fields on the parent form | C3:41, C3:900 |
| Non-Embedded Grid | Many to one | Grid on parent **and** its own menu View/Form/Browse | C3:1420–1426 |

**How an extension attaches to a parent BC** — the mechanism is identical in all cases: create the child BC, then add a **Relationship** on the *child* whose *Related Business Component* is the parent.

Embedded (Many-to-One) extension, documented order (C3:57–358):
1. New Business Component; **check "Embedded"** — "which means the Extension will not appear on the menu and is accessible from 'Training'" (C3:57–59). For a standard-BC extension: "Check the 'Embedded' checkbox to identify that this is an Extension." (C3:395).
2. Fields via Import (C3:71, C3:405–411).
3. Set primary keys — the child must carry the parent's key fields plus its own (C3:109–113); adjust lengths/formats; Save (C3:160–162).
4. **Relationships panel → New** (C3:176–178).
5. Search-select *Related Business Component* = the parent (C3:200, C3:479).
6. Cardinality is **auto-detected**: "system identify cardinality of relation as many-to-one. As a result, Students extension will be included into the Training form as embedded grid." (C3:242–244). The rule is stated: "The 'Many to One' relationship is possible because the child business component has two primary keys (CountryCode & Industry), while the parent has only CountryCode." (C3:550). For one-to-one: "the Platform already identified this relation as Child and set cardinality as One-to-One. It was done because child and parent components has identical key-fields. **Field Mapping was also defined automatically.**" (C3:850–854).
7. **Field Mapping** — "Field mapping allow to link child records with their parent record" (C3:259). Grid columns `Source | Field/Literal | Related` (C3:289). Save and close (C3:302).
8. **No Form, no View required** (verbatim, C3:319–321):
> "No need to build the form. The system 'understands' that for a 'Many to One' extension a grid should be built automatically. Also, no need to create a View because Extensions are not accessible from the menu, they are 'Embedded' in their parent Business Component."
Restated: "For Extensions, you don't need to define the Form, the Platform automatically build it." (C3:568).
9. **Deploy** the child BC against a data store in development mode (C3:337–341).
10. Result on the parent screen: "Country Industries now appears as the grid at the bottom of the page. It's also present at the Top Navigation as well. If you don't see this, you may need to Refresh your page." (C3:597–599). Also C3:358.

**Hard constraint on what can be extended (verbatim, C3:493):**
> "Pay attention that Embedded Business Components cannot be extended that's why the filter Embedded=NO is set in the search by default."

**EMBEDDING A GRID INTO AN EXISTING SCREEN — the specific question.** Two documented routes:

*Route A — embedded extension (auto-built grid).* Steps 1–10 above. The grid is generated by the platform; there is **no grid-authoring artifact at all**. The only per-field control mentioned is `Include Grid on Parent Form` on the Relationship (C3:207–210). Applied to a *standard* QAD BC (Countries) at C3:373–603, which is the documented pattern for "embed a grid into an existing (QAD-shipped) screen".

*Route B — non-embedded grid (grid IS authored).* C3:906–1426:
1. New BC, **Embedded left unchecked** (C3:932), Save (C3:941).
2. Fields via Import; set keys, lengths, Date types (C3:956–1017).
3. **"As we didn't mark this BC as Embedded, we should build Form, Browse and View before deployment."** (C3:1031) — Build Form (C3:1033), configure it (C3:1045), and per-field set **"Lookup Visibility" option to Visible** on the key field (C3:1059).
4. Browses → New → Browse Label → Save "to create browse with default configuration" (C3:1073–1081).
5. Views → New → View Label, ensure *Eligible for Menu* checked, select the browse, Save & Close (C3:1116–1134).
6. Save BC, Deploy (C3:1152–1154).
7. **Then** attach it: open the child BC → Relationships → New → Related Business Component = parent → **Check "Include Grid on Parent Form"** → map key fields → Save (C3:1194–1204).
8. **Only now does grid authoring unlock**: "Once we created a Relationship with checked 'Include Grid on Parent Form' option you will be able to configure Grid representation of current component. Click on **Edit Grid** button." (C3:1232–1234). The Form panel then shows `Existing Form: No / Existing Grid: Yes` with `Build Form` and `Edit Grid` buttons (C3:1217–1230).
9. Grid editing: reorder columns; "Columns Class Name and Location you can hide in **'Change Grid Definition'** sub-menu." (C3:1257–1258). Grid row toolbar: `New, Edit, Delete, Details, Change Grid Definition` (C3:1251–1255).
10. The grid's **Details** button opens "full view with browse and form… as a Details view… Details view could also include other grids." (C3:1349–1353).

**Non-Embedded Grid capabilities (verbatim, C3:1420–1426):**
> "Can be accessed from the main menu through their own View, and Form as well as through grids on parent BC. · Can have more than one parent (for example: Training and Maintenance). · Can have records that do not relate to any parent records (such as Holiday)."

Export behaviour differs: "Non-embedded grid has own CRUD and will not be available in import by default." (C3:2496) — it becomes exportable/importable only once the parent is flagged **Business Document** (C3:2549, C3:2584).

---

### 4. RELATIONS and FORMULAS

**Relationship types — exactly two (verbatim, C3:1454–1458):**
> "Relationship types: · Child Relationships · Lookup Relationships"

The accompanying diagram (a mermaid block, C3:1443–1452) encodes: `Business Component --Lookup Relation--> Business Component`; `Business Component --Child Relation--> Non-Embedded Grid Business Component`; `--Child Relation--> Embedded Grid Extensions`; Non-Embedded Grid `--Child Relation--> Embedded Grid Extensions`; `One-to-one Extensions --Child Relation--> Business Component`.

**Relationship configuration surface (verbatim field list, C3:190–210 and C3:459–546):**
```
Main:  Source Business Component, Source App, Related Business Component,
       Related App, Relationship, Relationship Label,
       Relationship Type (= Child), Cardinality (= Many to one | One to one)
Composition Relation:      Composition Relation [ ]   Cascade Delete [ ]
Include Grid on Parent Form: Include Grid on Parent Form [ ]   Cascade Delete [x]
Field Mapping:  Source | Field/Literal | Related
```
Relationships-panel toolbar: `New, Edit, Delete, Details, More` (C3:174). Relationship rows list `Relationship, Relationship Label, Source Business Component, Related Business Component` (C3:174). Relationship *types* as displayed in the relationship-hierarchy picker: `Lookup`, `Parent` (C3:1968 — image caption: Training row shows "Countries (Lookup type), TrainingRoom (Parent type), Students (Parent type)").

**When a relationship is needed:** to attach any extension (§3); to expose a parent BC's fields in a child's browse and vice-versa (C3:1466, C3:1552–1598); to source a Lookup (§5); and to reach a child BC's fields from a Formula (below).

**FORMULA FIELDS.** Configuration surface and order (C3:2040–2250):
1. BC → Fields → New. Set *Field* + *Physical Field* to the same token, *Field Label*, *Data Type*, *Format* — e.g. `StudentCount` / "Student Count" / Integer / `>9` (C3:2082–2086); `AverageScore` / "Average Score" / Decimal / `>>9.99` (C3:2120–2124).
2. **"Be sure to check the box for Formula."** (C3:2105); equivalently "Set 'Formula Field' to 'Yes'." (C3:2126). `Formula` is a boolean column in the Fields grid (C3:2145 shows `\[yes]`).
3. Select the field → **Details** → scroll to the **Formula** modal (C3:2150, C3:2162).
4. Modal has two buttons: **`Include Operator`** and **`Include Field`** (C3:2160).
5. `Include Operator` → choose **Average** → editor shows `AVERAGE([])` (C3:2175, C3:2190).
6. Place cursor between the brackets → `Include Field` (C3:2192) → a **"Select Relationship"** window appears "where the hierarchy of relations is represented"; expand to the child relation and Continue (C3:2202–2206) → pick the field (C3:2216).
7. Resulting expression, verbatim (C3:2226):
```
AVERAGE([_com_extensions_training_Students.score])
```
   i.e. the token is `_` + the child BC's package path with `.`→`_` + `.` + the child field name in **camelCase** (`score`, not `Score`). [CONFIRMED as the literal string; the derivation rule is [INFERRED] from this single example — no rule is stated.]
8. Same flow for `COUNT` — "Click 'Include Operator' and choose 'Count'. This is the only difference from the process for 'Average Score'." (C3:2244).
9. Add the formula fields to the Form via Edit Form (C3:2262), Save BC, **Deploy** (C3:2277–2279).
10. **Runtime prerequisite (verbatim, C3:2291–2297):**
> "Formula Fields are based on Activity Feeds mechanism which could be inactive if never used on this environment. To run it, navigates to OS Scripts screen. Select script with name **activity_feed_update**. Open Actions and run Execute Script."
11. To surface formula fields in a browse: Browses → Details → `+ Select` → pick the BC → the unadded fields appear → OK → **Column Order → Configure** → drag → Save & Close → save the BC (C3:2351–2430).

Only two operators are demonstrated: **AVERAGE** and **COUNT** (C3:2175, C3:2244). [CONFIRMED ABSENCE] no complete operator list, no grammar, no precedence rules appear in either doc. A **"Recalculate Formulas"** section exists on the BC screen (C2:754, image caption only) — its behaviour is never described.

---

### 5. LOOKUPS

`Lookup` is a **boolean column in the Fields grid** (C2:1229–1237, C3:100–106, C3:799) and a **checkbox on the field's Details panel** (C3:1748).

**Documented order to define + attach a lookup (C3:1712–1835):**

1. **Why**: "Sometimes it's required to add fields from one business component to another (e.g. we need a Country Description in the Training browse). Lookup Relation helps to resolve this task without duplication of description field in Training table." (C3:1712–1714).
2. **Create the carrier field on the source BC**: "Click 'New' under fields and add 'CountryCode', label 'Country'. Set Character type and Length 3. We need this field to build relation between Training and Country business components. Now Click Details." (C3:1728–1734). The lookup key field must therefore match the target's key field in type/length. [INFERRED that matching is *required*; the doc states the values but not a rule. Confirmation would need the platform's relationship validator.]
3. **Field Details → check the `Lookup` checkbox** (C3:1748).
4. **Lookup panel field list (verbatim, C3:1746, image caption):** `Related Business Component`, `Browse`, `Relationship`, `Relationship Label`, and a **`Visualize as Drop-Down List`** checkbox.
5. Click the search icon → the BC picker opens with the default filter **`Embedded equals No`**, add `Business Component contains Countries`, Search (C3:1758–1760) → choose Countries (C3:1772).
6. **Field mapping is automatic**: "Note that the Platform has already identified the relationship between 'CountryCode' in the Countries Business Component, and 'CountryCode' from Training." (C3:1787).
7. **Choose the Browse that will be used with the Lookup** (C3:1800) → "Select the Countries Browse. Then Click OK at the bottom of the Detail Panel, and Close. Then Click Save at the bottom of the Business Component Page." (C3:1812–1816).
8. **Redeploy**: "Now you need to Deploy the Business Component again so that the new field is applied." (C3:1835).

**Consuming a lookup on a form** (C3:1848–1917):
- Form panel → **Edit Form**; place a `Group` control and put the new field inside (C3:1850–1852).
- "Expand Country field and click **More**. Lookup Relation will allow you to use fields from the browse which was associated with the relationship." (C3:1860–1862) → a **"Select Related Fields"** dialog lists the target's fields with columns `Field | Display Label | Business Component | Detail Table | Relationship` (C3:1876–1883).
- Pick `CountryDescription`, drop it into the same group, "Set Label Visibility to None and State to Read Only" (C3:1872, C3:1897–1898).
- Runtime: "Select US country and you will see that appropriate Description was populated automatically **without any coding**. Pay attention, that **Lookup and Drill-down were automatically added to the field with relation**." (C3:1915–1917).

**Consuming a lookup in a browse** (C3:1932–2012): Browses → Details → Fields `+ Select` → expand the source BC row → select the `Countries` relation (shown with type `Lookup`) → Continue → pick `CountryDescription` → use **Column Order** to position it → Save.

**Second, implicit lookup path** — Generalized Codes auto-conversion (C2:849–855, C3:611–615): a Character field whose *Physical Field Name* matches a Generalized Code field name is converted into a lookup/drop-down automatically, **provided the field is not already defined as a lookup**.

**Form-side lookup control**: a per-field property `Lookup Visibility` with value `Visible` (C3:1059).

[CONFIRMED ABSENCE] Neither doc mentions a **"Lookup Definition"** artifact by that name in an operational context — the only appearance of the term is in the Configuration-Data artifact list "Lookup Definitions" (C2:178). Neither doc shows a lookup **filter/qualifier/where-clause** surface of any kind. This matters for AUX's `lookup_detector` classifications (`static` / `dependent` / cascading filters — see `backend/core/lookup_detector.py:317-394`): **these docs supply no documented place to put such a filter.**

---

### 6. URNs, identifiers, naming conventions — every pattern, verbatim

All entries [CONFIRMED] verbatim from the file at the cited line. `...` marks truncation present in the source (OCR cut-off), not by me.

| URN (verbatim) | Kind | Cited |
|---|---|---|
| `urn:app:com.extensions.training` | App (custom) | C2:80, C3:192, C3:461 |
| `urn:app:com.qad.qracore` | App (implicit dependency of every App) | C2:80 |
| `urn:app:` | App (truncated) | C3:927 |
| `urn:be:com.qad.qra.security.IAccessControlEntryApp` | BC, Type=Standard | C2:717 |
| `urn:be:com.qad.base.coa.IAccountDefault` | BC, Standard | C2:718 |
| `urn:be:com.qad.assetmgmt.finance.accountgroup.IAccountGroup` | BC, Standard | C2:719 |
| `urn:be:com.qad.financials.systemadministration.accounttablefield.IAccountTableField` | BC, Standard | C2:723 |
| `urn:be:com.qad.tam.accrual.IAccrualV2` | BC, Standard | C2:725 |
| `urn:be:com.qad.base.address.ICountry` | BC, Standard (the parent used in all extension examples) | C3:1774 |
| `urn:be:com.qad.base.address.IC...` | same, truncated | C3:1525 |
| `urn:be:c` | BC URI / Secure URI of a *custom* BC — truncated | C3:921, C3:923 |
| `urn:service:com.qad.qra.security.IAccessControlEntry-AccessControlEntries` | BC, Type=**Action** | C2:715 |
| `urn:service:com.qad.qra.sod.ISODValidator-AccessControlEntries` | Action | C2:716 |
| `urn:service:com.qad.financials.generalledger.journalentry.IJournalEntry-AccountInfos` | Action | C2:720 |
| `urn:service:com.qad.sales.pricing.IAcMemberMaint-AcMemberMaints` | Action | C2:726 |
| `urn:datastore:com.extensions.extension` | Data Store (the only one used, everywhere) | C2:890, C3:333, C3:1147, C3:1831, C3:2275 |
| `urn:browse:bebrowse:com.extensions.training.trainingRo...` | Browse (custom, truncated) | C3:1086 |
| `urn:browse:bebrowse:com.extensions.training.countries` | Browse (custom) | C3:1658 |
| `urn:bd:com.extensions.training.Training.Training` | Business Document | C3:2674 |
| `urn:field:` | — | **NOT PRESENT in either doc** |
| `urn:view:` | — | **NOT PRESENT in either doc** |
| `urn:browse:be:` (the `be` browse-type, no `browse` suffix) | — | **NOT PRESENT in either doc** |

**Derived patterns** (each [INFERRED] from the instances above; the docs never state a template):
- App: `urn:app:<reverse-dns package>`; custom apps use the `com.extensions.` prefix.
- BC (Standard type): `urn:be:<package>.I<PascalEntity>` — note the leading `I` on the last segment.
- BC (Action type): `urn:service:<package>.I<Interface>-<Collection>` — note the `-` separator.
- Browse (custom): `urn:browse:bebrowse:<package>.<camelOrLowerBrowseName>` — `com.extensions.training.countries` is lower-case while `com.extensions.training.trainingRo…` is camel-case, so casing of the final segment is **not consistent even within one doc** (C3:1086 vs C3:1658).
- Business Document: `urn:bd:<package>.<Entity>.<Entity>` — the entity name is repeated, with **no** `I` prefix (C3:2674).
- Data Store: `urn:datastore:<package>`.

**Other identifiers/conventions:**
- Formula field reference token: `_com_extensions_training_Students.score` (C3:2226) — package with `_` separators, prefixed `_`, then `.` then the camelCase field.
- Translation string codes: user-created ones are prefixed `CNFG:` once saved to Configuration Data (`CNFG:ZIP_CODE_POSITION`, C2:624, C2:657); QAD-shipped ones use `mfg-` (`mfg-COUNTRY`, `mfg-DESCRIPTION`, `mfg-CURRENCY`, C3:1593–1595; `mfg-COUNTRIES`, C3:1618). String Code is described as "a unique identifier of the translation" (C2:590).
- BC list columns: `Business Component | Label | Business Component URI | Type | Status | Business Document` (C2:713).
- BC `Type` values seen: `Standard`, `Action` (C2:715–726).
- `Scope` value used throughout: `System` (C2:744, C3:393, C3:928).

---

### 7. REST/API surface and status lifecycle

**The only literal HTTP call in either document** (C3:668):
```
$.post("api/webshell/clearAllCaches")
```
Context: after adding Generalized Codes, "To update the cache that is used for the dropdown we need to clear all caches. Open browser console (F12 in Chrome) Then enter the string below… Hit Enter." (C3:664–670). Method **POST**, path **`api/webshell/clearAllCaches`** (relative, no host, no leading slash in the source).

**Business Document → REST API** (C3:2631–2689). What is stated:
- "As it's possible to use Business Document for REST API requests, could be useful to have API documentation." (C3:2635).
- The Business Document panel exposes "fields like **Business Document URI** and **API URL**" (C3:2633 — image caption; the actual API URL value is never shown).
- Navigation to the docs: BC screen → **Business Document** panel → **Drill-down Links** panel → **"Business Document API Documentation"** link (C3:2649) → **Open** (C3:2663) → **"Open API Documentation"** button (C3:2676).
- Methods exposed: "GET, POST, DELETE, HEAD, PATCH, and Query endpoints" (C3:2687 — **image caption only**). "Here you will be able to find a detailed documentation with API definition and examples for each CRUD action." (C3:2689).
- Enabling it: BC → Main → **check the `Business Document` checkbox** → Save (C3:2549–2551). "This can be applied to any Business Component you create in the QAD Enterprise Platform." (C3:2555). Once checked, a Business Document panel appears that "contains and represent information about structure of current Business Document" (C3:2568–2570).

**[CONFIRMED ABSENCE — important]** Neither document contains a single REST **path** for creating or reading a Business Component, Field, Form, Browse, View, Relationship, Lookup, or Formula. Every artifact in both decks is created through the **UI**, plus **Excel import** for fields and **`yab` CLI** for schema removal. There is no `urn:be:com.qad.qra.adapter.entity.IEntityBuilderCRUD`-style endpoint, no `/api/qracore/...` path, and no payload schema anywhere in these two files.

**Status lifecycle (all [CONFIRMED]):**
- `Status` is a column on the BC list (C2:713); the shipped BCs all show **`Released`** (C2:715–726).
- A newly created custom BC shows **`Status: Initial`** (C3:919).
- `Revert to Initial` action → **"The status will be changed to 'Suspended'. To complete the revert to 'Initial' status, run the required YAB command."** (C2:1283).
- "You can undeploy your Business Component only if it was suspended." (C2:1271).
- After `yab database-extension-obsolete-schema`, "the Business Component will be in the **Initial** state" (C2:1375), at which point "You can make any schema changes or delete Business Component in case of need." (C2:1398).
- Deploy validation gate: `There should exist at least one View.` / `There should exist at least one Form.` (C2:900–903).
- Post-deploy field immutability: add-only; name/type/length/format frozen (C2:1240).

So the observed lifecycle is: **Initial → (Deploy) → [deployed] → (Revert to Initial) → Suspended → (yab database-extension-obsolete-schema) → Initial**. `Released` is only ever seen on QAD-shipped components; the docs never show a custom BC reaching it. [INFERRED] that `Released` is a separate, QAD-internal promotion state — confirmation would need a status-model doc.

---

### 8. Differences between these docs and what AUX targets

Note first: **these are not a separate "Adaptive product's" docs.** Both files are titled "QAD Enterprise Platform" throughout (C2:5, C3:5). The word "Adaptive" appears exactly three times in either file, all inside the App-Data-vs-Configuration-Data table — "Adaptive solutions", "configure or personalize Adaptive according to user needs" (C2:145, C2:155, C2:163). [INFERRED] "Adaptive" is QAD's name for the customization/extension layer of the same platform AUX targets, not a different product. **The `adaptive_java_version` directory name is therefore misleading as evidence of a different BC model.** Confirmation would need a product-positioning doc; nothing in these two files states it either way.

Concrete, cited divergences:

**(a) AUX's pipeline has no Browse-creation step; the docs make Browse a hard prerequisite of a usable View.**
AUX's 14 steps are enumerated verbatim in `backend/pipeline.py:145-160`:
```
1 Understanding your requirements      8  Planning event handler logic
2 Designing BC fields                  9  Writing event handler code
3 Creating Business Component in QAD    10 Compiling TypeScript to JavaScript
4 Fixing errors automatically          11 Registering event handlers in QAD
5 Planning form panels                 12 Building view configuration
6 Building panel layout                13 Registering view in QAD
7 Saving form design to QAD            14 Deploying Business Component
```
The word "browse" appears only twice in that file (`backend/pipeline.py:61`, `backend/pipeline.py:696` — "Building browse/maintain view configuration…"). The docs are explicit that a Browse is a **separate artifact created before the View**, and that without one "you will be able to create only 'Form Only' views" (C2:971). [INFERRED] AUX folds browse creation into its view builder — `backend/builders/view_builder.py:110,160,166` emit `browseDatasourceUri` / `browseURI` / `initialBrowseURI` of form `urn:browse:bebrowse:{MODULE}.{bc_lower}` — i.e. AUX **references** a browse URI rather than creating a Browse artifact. Whether the platform auto-creates the BEBrowse row on view registration is not answerable from these two docs; that is the thing to confirm.

**(b) AUX's 14-step pipeline has no Relationships, Formula, or Lookup step.** No such label exists in `backend/pipeline.py:145-160`. Relationships do exist in AUX but on a separate path — `backend/pipeline_embedded.py:278` posts to `urn:be:com.qad.qra.berelation.IBERelation`, and `backend/builders/embedded_builder.py:319` builds `urn:be:com.qad.qra.berelation.IBERelation:{relation_id}`. Lookups are dry-run only: `backend/pipeline.py:21-23` ("Phase 11: lookup detection/generation (dry-run only; never auto-POSTs)") and `backend/pipeline.py:74` (`create_lookup(cand, meta, dry_run=True)`). Given the docs put Relationship creation squarely inside the extension flow (C3:176, C3:444, C3:823, C3:1196) and Lookup creation inside the *field* flow with a mandatory **redeploy** afterwards (C3:1835), AUX's ordering (deploy at step 14, lookups detected but never posted) does not have a documented counterpart. [CONFIRMED on both sides as described; the *consequence* is INFERRED.]

**(c) Field creation mechanism differs entirely.** The docs' primary path is **Excel import** (C2:756, C3:71, C3:405, C3:956) with manual `New` as the secondary (C3:2068). AUX generates the field set with an LLM at step 2 (`backend/pipeline.py:417-426`, "Identifying fields and data types…"). Nothing in these docs describes or constrains a programmatic field-definition payload. [CONFIRMED.]

**(d) URN shape mismatch on `urn:be:`.** Docs, standard components: `urn:be:com.qad.base.address.ICountry` (C3:1774) — package + `.I<Entity>`, entity name appearing **once**. AUX builds `urn:be:{MODULE}.{bc}.I{bc}` (`backend/builders/bc_builder.py:165`, `backend/main.py:149`, `backend/builders/deploy_builder.py:8`) — entity name appearing **twice**. [CONFIRMED as a textual difference.] [INFERRED, and this is the honest reading] that both are correct for their respective cases: QAD-shipped BCs live in deep `com.qad.*` packages, while extension BCs get a per-BC sub-package. **These docs cannot settle it** — the one custom BC URI shown is OCR-truncated to `urn:be:c` (C3:921). However, AUX's own doc corpus does resolve it: `backend/qad_docs/App Development Concepts/Use of URIs in the Platform.txt:16-19` gives `urn:be:<name>` with example `urn:be:com.qad.base.item.IItem` and the note "The `be` in the URI format refers to the original name of business components ('business entity')" — still only the standard-BC form.

**(e) `urn:bd:` — AUX emits two variants, docs show one.** `backend/builders/bc_builder.py:167-168` emits both `urn:bd:{MODULE}.{bc}.{bc}` **and** `urn:bd:{MODULE}.{bc}.I{bc}`. The docs show only the first form: `urn:bd:com.extensions.training.Training.Training` (C3:2674). [CONFIRMED.] Whether the `I`-prefixed variant is a different field (e.g. a "business document *entity*" vs "business document") cannot be determined from these docs.

**(f) `urn:browse:be:` vs `urn:browse:bebrowse:`.** The audit request asked about `urn:browse:be:`. **It does not occur in either Adaptive doc** — only `urn:browse:bebrowse:` does (C3:1086, C3:1658). AUX likewise emits only `bebrowse` (`backend/builders/view_builder.py:110,160,166`). The `be` form is documented in AUX's own corpus with a direct contradiction between two files: `backend/qad_docs/App Development Tools and Resources/Business Components - Views.txt:31` — "The URI of a business component browse has the pattern: `urn:browse:be:*`" — versus `backend/qad_docs/Business Documents and Services/Business Document API Documentation.txt:45` — "Business component browses follow the pattern: `urn:browse:bebrowse:*`". The URI reference resolves it: "'browse type' can be 'fin', 'mfg', 'be' or 'bebrowse', where **only 'be' and 'bebrowse' can be created through the platform**" (`backend/qad_docs/App Development Concepts/Use of URIs in the Platform.txt:25`). [CONFIRMED as a contradiction in the AUX corpus; the Adaptive docs contribute nothing to resolving it.]

**(g) Docs style is UI-procedural; AUX's own `backend/qad_docs/` corpus is API-reference.** The Adaptive decks contain **zero** REST paths for artifact creation (§7). AUX's corpus does — e.g. `backend/qad_docs/Platform Development - REST APIs/Endpoints.txt:15,17-18` gives `https://qmi.qad.com/clouderp/api/qracore/browses?browseId=urn:browse:bebrowse:com.extensions.<app-id>.<business-component-id>`. [CONFIRMED.] Consequence for this audit: **these two decks are usable as an ordering/semantics reference, not as a payload reference.**

**(h) The docs' deploy gate is stricter than AUX's step order suggests.** Docs: Form **and** View must both exist before Deploy (C2:900–903). AUX creates form (step 7) and registers the view (step 13) before deploying (step 14) — consistent. But AUX has no Browse artifact step, and the docs tie View type `Hybrid Browse` to an existing Browse (C2:1014, C2:1018, C3:1654–1658). [INFERRED] AUX's views are viable only if the platform accepts a `browseURI` that names a browse the platform materialises itself. This is the single highest-value thing to verify against a live environment.

**(i) The docs never mention a "form-field normalization" concept, which is what the current AUX working tree changes touch** (`backend/core/progress_parser.py`, `backend/agents/prompts.py` modified per git status; commit `af0286b Fix step-6 form-field normalization`). The nearest documented analogues are Field Overrides (C2:458–462, C2:656–663) and Generalized-Code auto-conversion (C2:849–855) — both are *platform-side* transformations of an already-created field, not a client-side name canonicalisation. [CONFIRMED ABSENCE in the docs.]

---

---

## B4. Adaptive Docs — Platform tools, Data Administration, Security and Permissions

**Files read in full (path aliases used for citations below; all paths relative to `D:\WEB_AUX\`):**

| Alias | Relative path | Lines |
| --- | --- | --- |
| **C4** | `adaptive_java_version/Docs/qad_enterprise_platform_class_4_More_Platform_Tools_training_guide.pdf.md` | 1423 |
| **C5** | `adaptive_java_version/Docs/qad_enterprise_platform_class_5_Data_Administration_Tools_training_guide.pdf.md` | 1061 |
| **C8** | `adaptive_java_version/Docs/qad_enterprise_platform_class_8_Security_And_Permissions_training_guide.pdf.md` | 1034 |

All three are OCR/markdown conversions of slide decks by Don Springer (C4:7, C5:9, C8:7). They are **click-path training material**, not API reference. Several lines are raw OCR noise (e.g. C5:186, C5:427, C5:920) — where I cite those, I quote the exact string and label the reading.

---

### Headline finding (read this first)

**[CONFIRMED] There is not a single HTTP/REST endpoint, URL, HTTP verb, or HTTP status code anywhere in these three documents.** A regex sweep for `http|/api|rest|endpoint|POST |GET |PUT |DELETE |url` over all three files returns only `urn:` values, the words "Delete"/"More" from UI button rows, and prose. There is no `403`, no `500`, no `Forbidden`. The only address-like strings are `urn:*` identifiers and email addresses (`mfg@qad.com` C5:1032, `cfo1@qad.com` C5:976, `trainusr@qad.com` C8:143).

**Consequence for the generator/deployer: these three docs cannot be used to derive any wire contract.** They constrain *what must exist and in what order*, not *what to call*.

---

### 1. Class 4 — the tools documented

**[CONFIRMED] The actual topic list (C4:13–25)** is: Lookup, Conditional Styling, Secondary Indexes & Initial Sorting, Adding of new Browses and Views, Predefined Search, KPIs & Action Center, Exporting and Installing Apps.

**[CONFIRMED] Explicit absences in C4 — each of these was searched for and is NOT present:**
- **App definitions** — no App definition screen is documented. The Apps screen appears only as the launch point for packaging (C4:1351–1357).
- **Dependencies between apps/modules** — completely silent. No dependency, jar, library, or "core libs" text exists in C4 (or C5/C8).
- **API source generation / proxy regeneration** — completely silent in C4. (The nearest thing in the whole set is the OS Script `compile_app_source...` in C5:168, see §2.)
- **Developer settings** — not covered in C4. The only occurrence in the whole set is a menu-bar OCR fragment, C5:159: `QAD logo Developer ▾ 📈 My Developer Settings Development ▾ Logging Options Analytics ▾` — the item exists in the Developer menu; its contents are never shown.
- **App URI** — appears only as a *grid column heading*, never with a documented value or format, at C4:614 (Browses panel columns "Name, Browse URI, App, App URI"), C4:823 (same), and C4:55 (Lookup Definition list, columns "Field URI | Reference | Browse URI | App"). The only actual `urn:app:` value in the set is in C5 (§3).

**[CONFIRMED] Tool-by-tool, what each is for and what it constrains:**

**Lookup Definition** (C4:39–271). Purpose per C4:265: *"to provide simple access to browse with existing records"*. Exact payload/field keys of the definition record (C4:77 lists the form; C4:191–221 shows a saved instance):
- Main section: `Field URI`, `Field Label`, `Reference`, `App`, `App URI`, `Namespace`
- Browse section: `Browse URI`, `Browse Label`, `Result Field`, `Search Field`, `Search Field Operator`
- `Search Conditions` grid, columns: `Field Name | Operator | Value | Type` (C4:209)
- `Additional Result Fields` grid, columns: `Field | Target` (C4:219)

Saved example verbatim (C4:193–221, abridged): Field URI `urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.ClassName`; Browse URI `urn:browse:bebrowse:com.extensions.training.training`; Result Field `training.className`; Search Field `training.className`; Search Field Operator `greater or equal to`; Additional Result Field `training.location` → Target `TrainingRoom_locationAutoField1`.

**[CONFIRMED] Lookup Relation vs Lookup Definition — a hard behavioural difference a generator must respect** (C4:251–269, verbatim):
```
### Lookup Relation
**Goal:** to provide relation between two business components
**Lookup icon:** useful side-effect
**Form:** could not contain field with added relation
VS.
### Lookup Definition
**Goal:** to provide simple access to browse with existing records
**Lookup icon:** goal of adding
**Form:** will always contain field with added lookup
```
[INFERRED] This is the doc-side rule behind any "is this field a lookup-relation or a lookup-definition?" decision: if the form still shows the field, it is a Definition; if the field vanished from the form, it was a Relation. Confirmable by inspecting `backend/core/lookup_detector.py` in this repo against this rule — I did not open it (out of scope of this task).

**Secondary Index + Initial Sort** (C4:388–571). Index record keys: `Index`, `Description`, `Unique` (C4:433–435); Fields grid `Physical Field | Order | Direction` (C4:441). Initial Sort grid: `Field | Display Label | Order | Direction | Warning | Business Component` (C4:544).
**[CONFIRMED] Out-of-band OS step required after adding an index** (C4:466 *"You will get a warning that a yab command is required."*; C4:478–483):
```bash
yab stop database-extension-index-rebuild
yab start
```
C4:483: *"Via the Putty execute next two yab commands exactly as shown on the left."*
**This is a hard constraint on an automated deployer: index creation is not completed by the UI/API path alone; it requires shell access to the app server.**

**New Browse / View** (C4:573–809). Documented limits, verbatim (C4:716): *"For optimal performance, select **50** or fewer columns. When the browse is run, only the first **20** columns display by default."* Browse Fields grid columns: `Select | Field | Field Label | Display Label | Physical Field | Sortable` (C4:720). Browse toolbar actions: `More | + Select | + New Conditional Field | Edit Conditional Field | Configure Joins` (C4:718). View flags: `Allow New`, `Allow Edit`, `Allow Delete`, and `Eligible for Menu` (C4:756, C4:774). C4:805–807 documents a real generation hazard: adding a field from a many-to-one extension relation multiplies parent rows, and *"Open button is displayed instead of New and Edit buttons."*

**Predefined Search** (C4:811–873). Criterion syntax, verbatim (C4:854): `_com_extensions_training_CountryIndustries.Industry isNotNull`. Panel offers `Show in Advanced Search` checkbox and buttons `Include Field`, `Include Operator`, `Include Variable`, `Check Syntax` (C4:837).
[INFERRED] The token form is a leading underscore plus the component package with `.`→`_`, then `.` + field name. Basis: the component is `com.extensions.training.CountryIndustries` (cf. C4:685) and the rendered token is `_com_extensions_training_CountryIndustries.Industry`. Confirmable only by generating one and running `Check Syntax`.

**KPI / Action Center** (C4:876–1315). KPI record keys (C4:950–976): `KPI`, `Filter by Current Workspace`, `Data Source Type` (= `Browse`), `Saved To` (= `Configuration Data`), `Data Source` (= a `urn:browse:bebrowse:...`), `Visual Type`, `Data Source Label`, `Active`, `KPI Type` (= `Current Data`); `Browse By Domain`, `Browse By Entity`; `Group Data`, `Group Dates By`, `Active Fields` / `Max: 20`; `Auto Refresh`, `Refresh Rate`, `Allow Manual Refresh`. **[CONFIRMED] documented failure workaround** (C4:1059): *"If you receive an error related to auto-refresh, uncheck the Auto-Refresh checkbox and click Save again."*

**Exporting / Packaging / Installing an App** (C4:1317–1417). Package form fields (C4:1369): `Major Version`, `Minor Version`, `Patch Version`, `Build`, `Version` (`1.0.0.0`), `Package` (`com-extensions-training-1.0.0.0`). Downloaded artifact: `com-extensions-training-1.0.0.0.zip` (C4:1394). C4:1371: *"Note that the field values are pre-populated."* C4:1377: *"Once you click submit, the App will be packaged and a link sent to your Inbox"* — i.e. **asynchronous, result delivered via Inbox notification, not a synchronous response** (notification titled "OS Script Processing: Create app package", C4:1392).
[INFERRED] Package name = the app URN body with `.` replaced by `-`, suffixed with the 4-part version. Basis: app URN is `urn:app:com.extensions.training` (C5:672) and package is `com-extensions-training-1.0.0.0`.

---

### 2. Class 5 — data administration

**[CONFIRMED] The document is titled "Data Administration Tools" (C5:5–7) but its topic list (C5:17–19) is: Activity Tracking, Alerts, Generic Approval Routing.** There is **no** record-level data import, no data loader, no CSV/spreadsheet load, no bulk data path, and no entity-metadata generation procedure in this file. Stating this plainly because the title invites the opposite assumption.

**[CONFIRMED] The only import/export documented is Configuration Data artifact import/export** (C5:467–506). C5:486: *"If you need to export or import configured Alerts, use the Configuration Data screen."* C5:502: *"Thren, go to Actions and select Export Configuration Data or Import Configuration Data."* Configuration Data grid columns (C5:480): `Type | Artifact | Label | Business Component | View | Status | Date Created | Created By`; example rows: `Artifact | Alert | Training Average Sc... | Training | | Active | 10/16/2023 7:51 PM | mfg` and `Artifact | Activity Tracking | Training | Training | Active`.

**[CONFIRMED] "Saved To: Configuration Data" is the artifact home for generated config.** C5:122: *"Notice that Activity Tracking artifacts are saved to Configuration Data."*; C5:129 `Saved To [Configuration Data]`; same key on KPIs at C4:955.

**[CONFIRMED] The only scripted/bulk execution path documented anywhere in the set: the OS Scripts screen** (C5:157–188). Grid columns: `OS Script | OS Script Label | Description | Type | File | Category` (C5:165). Rows visible (C5:167–171), verbatim including truncation:

| OS Script | Label | Description | Type | Category |
| --- | --- | --- | --- | --- |
| `activity_feed_update` | `ACTIVITY_FEED_UPDAT...` | `Updates activity feed` | Server | Development |
| `compile_app_source...` | `COMPILE_APP_SOURC...` | `Compiles app sourc...` | Server | Development |
| (same name) | | | **Client** | Development |
| `create_app_metadat...` | `CREATE_APP_METADAT...` | `Creates archive with...` | Server | Development |
| `create_app_package` | `CREATE_APP_PACKAGE...` | `Creates a yab packa...` | Server | Development |

Invocation (C5:176–180): *"navigates to OS Scripts screen. Select script with name activity_feed_update. Open Actions and run Execute Script."* Result is asynchronous → Inbox (C5:196: *"Once script is executed you will receive notification in your inbox."*).
[INFERRED] `create_app_metadat...` is `create_app_metadata` and is the metadata-archive producer; `compile_app_source` exists in both **Server** and **Client** variants, which is why a source-generation step can half-succeed. Both are inferences from truncated OCR labels — confirmable by opening the OS Scripts screen in the live environment and reading the untruncated `OS Script` / `File` values.

**[CONFIRMED] Business Component screen anatomy and status field** (C5:636, raw OCR of the BC header + panel tabs; quoted verbatim, wrapping added):
```
Training  Training  Deployed
Business Component  App  Status
Main  Fields  Relationships  Business Services  Form  Views
Source File Generation  Deployment  Approvals
```
So: the BC header carries three labelled values — Business Component, App, **Status** (value shown: `Deployed`) — and the BC has a `Source File Generation` panel and a `Deployment` panel. **[CONFIRMED] Deployment panel keys** (C5:553–557): `Data Store URI` = `urn:datastore:com.extensions.extension`; `Import Data` (checkbox); `Filename` = `BusinessComponentTrai...`; `Deploy` (button).

**[CONFIRMED] Activity Tracking prerequisite — an explicit ordering constraint** (C5:174, verbatim): *"Activity Tracking is based on Activity Feeds mechanism which could be inactive if never used on this environment."* → run `activity_feed_update` first (C5:176–180). Tracking config keys: `Activity Tracking` checkbox, `Saved To`, and a per-field grid `Tracking | Alerts | Field | Field Label | Detail Table` (C5:137).

**[CONFIRMED] Event-handler registration procedure** (C5:630–706) — directly relevant to a deployer:
- Entry point C5:630: *"Now click New on Event Handlers (just below Edit Form)."*
- Grid columns (C5:636): `Timing | Active | Applies To | App | App URI`
- Instance values (C5:669–672): `Active [x]`; `Timing [Pre] Runs before any other event handlers.`; `Applies To [Web]`; `App [Training] urn:app:com.extensions.training`
- Generated module/class skeleton (C5:675–699): module `com.extensions.training.EventHandler.Training.ComExtensionsTraining.Maint_BEFORE`; `export class TrainingMaintHandler extends QraViewTSHandlerWithViewFormTSHandler<DTO.TrainingMaint, TrainingFormHandler>`; `export class TrainingFormHandler extends QraViewFormTSHandlerV2<DTO.TrainingMaint>`
- **Naming constraint, verbatim (C5:687):** *"Do not change this class name or the event handler will no longer run."*
- Finish order (C5:702–706): check `Active` → paste code into the `TrainingFormHandler` class → *"Then click Compile button (bottom right). Save handler and close editor."*

**[CONFIRMED] Generic Approval Routing — a strict, documented setup order** (C5:516–841), which a generator must replicate in sequence:
1. BC → Main panel → check `Approvals` (C5:538–539).
2. BC → Approvals panel → `Approval Configuration: [Configure]` (C5:561–563); set `Approval Label`, select the view, enter email text (C5:575–579); configure Task icon/colour/`Description 1`/`Description 2` (C5:592–600).
3. Edit Form → add a Group, move the field in, add a Button with **Element Name `Route`** and **Button Label `Confirm`** (C5:610–616).
4. Register the event handler with `startApprovalProcess("Route", this.$scope, eventData)` (C5:646–657) — the `case "Route"` must match the Element Name.
5. Main menu → `Approval Configuration` → the BC row *"is not active"*; double-click and check `Enabled`, Save & Close (C5:719–736).
6. `Approval Routes` → New → `Name`, `Description`, `Business Component`, `Currency Code`; `Conditions` grid `Field | Operator | Value1 | Value2`; `Approvers` grid `Sequence | User | User Name | Is Literal | Duration | Duration Unit | Description | Alternate Appr` (C5:777–838).
C5:797–799: *"Routes allow to configure conditions according to which request will be sent to appropriate approver. One business component could have several approval routes, and each route could have several approvers with defined sequence."*

---

### 3. Class 8 — security and permissions

**[CONFIRMED] The authorization model** (C8:41–49, verbatim table):

| Step | Relationship | Target |
| --- | --- | --- |
| User | Assigned | Role |
| Role | Assigned | Permission |
| Permission | Access | Resource |

**[CONFIRMED] The access-scope hierarchy** (C8:60–92): `System → Domain → Entity → Site`. C8:331–333: *"Usually, it will be enough to configure domain level access, but Enterprise Platform also supports the Site level configuration. It could be useful in some specific cases, such as functionality from the EAM app."*

**[CONFIRMED] The permission set is exactly five values** (C8:497–503, and identically C8:880–886 and C5:906–912):

| Permission | Allow |
| --- | --- |
| Full Access | yes |
| Create | yes |
| Delete | yes |
| Read | yes |
| Write | yes |

Permissions are granted **per resource URN**. Example resource for a BC: `urn:be:com.extensions.training.Training.ITraining` (C8:506), with a `Menu Eligible` checkbox alongside (C8:508).

**[CONFIRMED] "approve" is a permission that exists but is NOT in the five-item grid.** C5:847 error text: `User CFO does not have approve permission for entity urn:be:com.extensions.training.Training.ITraining`. The documented remedy is to grant **Full Access** on that BC to the role (C5:915–916: *"For Training (substitute your UserID) grant Full Access."*), after which the save succeeds (C5:935–937).
[INFERRED] `Full Access` subsumes `approve`; there is no separate Approve checkbox exposed. Basis: the grid never shows an Approve row anywhere in three documents, yet the error names an `approve permission`, and granting Full Access resolves it. Confirmable by granting only Create+Delete+Read+Write (no Full Access) and retrying the approver save.

**[CONFIRMED] Permissions needed to CREATE a Business Component, to DEPLOY an extension, or to register an event handler are NOT documented in any of these three files.** Searched all three for `permission` + `create|deploy|event handler` co-occurrence; the only permission requirements stated anywhere are (a) the approver's `approve`/Full Access on the target BC (C5:847, C5:875), and (b) `Full Access|Create|Delete|Read|Write` on BC and view resources for a *runtime* role (C8:485–508). **This is a genuine gap, not an oversight in my reading.**

**[CONFIRMED] What a 403 means operationally: the docs are entirely silent.** No HTTP status code appears. The two permission/precondition failures that ARE documented both surface as **in-form validation errors in a `Field | Error | Error ID` grid**, not as a transport-level code:
- C5:845–847: `| User | User CFO does not have approve permission for entity urn:be:... | |`
- C8:684–686: `| Role | Role has one or more members and cannot be deleted Training |`
[INFERRED, operationally load-bearing] Because documented authorization failures are returned as *named field errors inside a normal save response*, a generator that only checks transport status will see a success-shaped response and mis-report. Confirmable by capturing the raw response of a deliberately under-permissioned save.

**[CONFIRMED] Roles — creation and lifecycle:**
- Create: Roles screen → New → `Role` and `Role Label` both `Training`, `Active` checked (C8:193–199). Roles list also has an `App` column showing `Configuration Data` (C8:182–184).
- Assign: `User Access` screen → select `System` in the Domain tree → check `Access` → *"Pay attention that it will become all Domains selected"* (C8:245–249); set `Default Domain` on a Domain (C8:281).
- **[CONFIRMED] Required extra role for Adaptive UX** (C8:299, verbatim): *"We also need to check "Member can run the WebUI" to allow the trainusr user use the Adaptive UX."* Role name is `webui_user` (C8:812).
- Delete blocked while members exist (C8:682–686); remedy is the `Remove All Role Members` action, C8:702–704: *"Use the "Remove All Role Members" option. This will unassign all the members of the role."*
- Administrator Role is `SuperUser` per Security Control (C8:1009). Approval example uses role `QMISuperNOAC` (C5:814, C5:892).

**[CONFIRMED] Role Menus:** Menus screen → New → `Type: Role`, `Name: Training` → `Add Page` (C8:355–359); menu item `Properties` are `Resource URI` (= `urn:view:hybridbrowse:com.extensions.training.traini...`) and `Include in Mobile App Menu` (C8:426–428). C8:473: *"The permissions button at the bottom of the Role Menu page brings you to the Role Permissions screen, where resources will be filtered according to the options added into the current menu."* C8:535, verbatim: *"Please note that Role Menus are Web UI ONLY!"* and C8:537: *"In the NetUI standard menu options are filtered by your access rights."*
[CONFIRMED] The Role Permissions tree shows, under each component node, a child node `APIs` (C8:485, screenshot description). No further detail on what those API permissions are — the doc never opens that node.

**[CONFIRMED] Field Groups = field-level security** (C8:852–886). C8:854: *"you can allow SuperUser role to have full access for the Training fields and configure Training role to have only read access for Start Date and disallow access for Duration fields."* Grid: `Field Group Code | Field Group Label`, example codes `Main`, `Options` (C8:872–875). C8:878: *"Field Groups will allow you to set permissions for the whole group or for each field separately"*.

**[CONFIRMED] Record Level Security** (C8:919–987). C8:937–939: *"By default, after activation of Record Level Security, a configuration 'Owner' will be applied. It means that user will only see that records which were created by itself."* **Hard limitation, C8:941, verbatim:** *"Please pay attention, that it's impossible to turn-on Record Level Security for legacy .Net browses."* Security Rules record keys (C8:974, OCR): `Rule Code`, `Rule Label`, `Active`, `Scope`, `Business Component` (= `urn:be:com.extensions.training.Training.ITraini..`), `Description`, `Criteria` grid `Field | Operator | Value 1 | Value 2`, `Applies To` grid `Type | Name | Applies To Parents | Permissions` (example: `Group | TrainGroup | No | Full Access`).

**[CONFIRMED] Security Control** (C8:1000–1020): `Idle Timeout Minutes 60`, `Session Expires Minutes 1440`, `Administrator Role SuperUser`, `Maximum Access Failures 10`, `Enabled Reason Type USER_ACT`, `Client ID <REDACTED — 32-hex value, see C8:1011 in the source doc>`, plus password policy keys (`Minimum Length`, `Min Numeric Characters`, `Min Non-Numeric Characters`, `Minimum Reuse Days`, `Minimum Reuse Changes`, `Password Creation Method`, `Password Expiration Days`, `Warning Days`). C8:1023: *"Security Control is another aspect of security that is common for both Web UI and NetUI."*
[CONFIRMED] `Session Expires Minutes 1440` / `Idle Timeout Minutes 60` are the only session-duration numbers in the set — relevant if a long-running generator holds one session.

---

### 4. Every URI / URN pattern in the three docs — verbatim, with location

**[CONFIRMED] Zero REST endpoints / URLs / HTTP verbs.** The complete inventory of identifier strings is below.

**URN schemes observed (7 distinct):**

| Scheme | Shape observed | Example (verbatim) | Location |
| --- | --- | --- | --- |
| `urn:field:` | `urn:field:<pkg>.<Component>.I<Component>:<Component>.<Field>` | `urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.ClassName` | C4:180, C4:193 |
| `urn:browse:bebrowse:` | `urn:browse:bebrowse:<pkg>.<browseName>` | `urn:browse:bebrowse:com.extensions.training.training` | C4:132, C4:199 |
| `urn:browse:mfg:` | `urn:browse:mfg:<legacyProgram>` | `urn:browse:mfg:ad057`, `urn:browse:mfg:cm007` | C4:57, C4:58, C4:65 |
| `urn:be:` | `urn:be:<pkg>.<Component>.I<Component>` | `urn:be:com.extensions.training.Training.ITraining` | C5:847, C5:856, C8:506 |
| `urn:view:hybridbrowse:` | `urn:view:hybridbrowse:<pkg>.<view>` | `urn:view:hybridbrowse:com.extensions.training.training` | C5:920, C8:426 (truncated) |
| `urn:app:` | `urn:app:<pkg>` | `urn:app:com.extensions.training` | C5:672 |
| `urn:datastore:` | `urn:datastore:<pkg>` | `urn:datastore:com.extensions.extension` | C5:555 |

**Full verbatim list, in file order:**

*C4 — Lookup Definition list table (C4:57–66):*
```
urn:field:com.extensions.officesupport.Offices.IOffices:Offices.Address           → urn:browse:mfg:ad057                                (App: OfficeSupport)
urn:field:com.qad.advancedselfbilling.asb.ISelfBillInvoice:SelfBillInvoice.BillToCustomer  → urn:browse:mfg:cm007
...CreditTermsCode  → urn:browse:bebrowse:com.qad.erp.base.creditTerms
...CurrencyCode     → urn:browse:bebrowse:com.qad.erp.base.currencies
...DaybookSetCode   → urn:browse:bebrowse:com.qad.erp.base.daybookSets
...InvoiceLanguage  → urn:browse:bebrowse:com.qad.erp.base.languages
...Project          → urn:browse:bebrowse:com.qad.erp.financials.projects
...SiteCode         → urn:browse:bebrowse:com.qad.erp.base.sites
...SoldToCustomer   → urn:browse:mfg:cm007
...TaxClass         → urn:browse:bebrowse:com.qad.erp.tax.taxClasss
```
(Note the source spelling `taxClasss` with three s's at C4:66 — reproduced as-is.)

- C4:116 — `urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.Class` (mid-selection, truncated form of the C4:180 value)
- C4:132 — `urn:browse:bebrowse:com.extensions.training.training`, described as the **`browseId` value in the Network payload** of the browse Refresh action. **This is the only network-level payload key named anywhere in the three docs: `browseId`.**
- C4:180 / C4:193 — `urn:field:com.extensions.training.TrainingRoom.ITrainingRoom:TrainingRoom.ClassName`
- C4:199 — `urn:browse:bebrowse:com.extensions.training.training`
- C4:956 — `urn:browse:bebrowse:com.extensions.training....` (truncated, KPI `Data Source`)
- C5:555 — `urn:datastore:com.extensions.extension`
- C5:672 — `urn:app:com.extensions.training`
- C5:847, C5:856 — `urn:be:com.extensions.training.Training.ITraining`
- C5:861 — `urn:be:com.extensions.training.Training.ltraining` — **OCR corruption** (lowercase L for capital I) of the same URN; the correct form is at C5:847.
- C5:920 — `urn:view:hybridbrowse:com.extensions.training.training` (Role Permissions detail, OCR line)
- C8:426 — `urn:view:hybridbrowse:com.extensions.training.traini...` (truncated, Role Menu `Resource URI`)
- C8:506 — `urn:be:com.extensions.training.Training.ITraining`
- C8:974 — `urn:be:com.extensions.training.Training.ITraini..` (truncated, Security Rule `Business Component`)

**Non-URN identifier patterns (also load-bearing for a generator):**
- Predefined-search token: `_com_extensions_training_CountryIndustries.Industry isNotNull` (C4:854)
- Auto-generated form-field target name: `TrainingRoom_locationAutoField1` (C4:170, C4:221)
- Browse field path: `training.className`, `training.location`, `training.averageScore`, `training.studentCount`, `training.areaOfStudy`, `training.capacity`, `training.classValue` (C4:201–202, C4:221, C4:1038–1043)
- Auto-generated join alias: `joinTable_9c68b381192b45a.countryDescription` (C4:1044)
- Package artifact name: `com-extensions-training-1.0.0.0`, file `com-extensions-training-1.0.0.0.zip` (C4:1369, C4:1394)
- Event-handler module path: `com.extensions.training.EventHandler.Training.ComExtensionsTraining.Maint_BEFORE` (C5:675); namespaces `com.extensions.training.EventHandler.Training.DTO` and `...Constants` (C5:681–682); framework types `Qad.QraView.TSHandler.QraViewTSHandlerWithViewFormTSHandler`, `Qad.QraView.TSHandler.QraViewFormTSHandlerV2`, `Qad.QraView.TSHandler.IViewField`, `Qad.QraView.TSHandler.IViewButton`, `EventData.QraView.ButtonClickEventData` (C5:647–648, C5:678–680)
- Shell commands: `yab stop database-extension-index-rebuild`, `yab start` (C4:479–480)
- OS Script names: `activity_feed_update`, `compile_app_source...`, `create_app_metadat...`, `create_app_package` (C5:167–171)
- Export file naming: `Export_Config_Data_2023_10_18.zip` (C8:737)

---

### 5. Environments, sandboxes, promotion between environments

**[CONFIRMED] There is no mention of "sandbox" anywhere in the three files.** Searched.

**[CONFIRMED] The documented promotion model — App packaging (C4:1327–1337, verbatim):**
```
Any App created in QAD Enterprise Platform can be Exported, Packaged, and then Installed into another environment
* Export and Package App from DEVL and install it into TEST
* Install same package into PROD after the testing
* Update an existing app with a newer version
* Create app just a backup
Process is easy and it takes only a few minutes
```
Named environments are exactly `DEVL`, `TEST`, `PROD` (C4:1329–1331).

**[CONFIRMED] Who may install — a hard operational constraint (C4:1404–1408, verbatim):**
```
* With QAD Cloud environments a package is installed by QAD Cloud Admins
* Customers do not take this technical action themselves but log a request to install a given package
* These activities are carefully logged by QAD, and strictly controlled for the protection of customer environments.
```
**Consequence: on QAD Cloud, an automated deployer cannot complete the last mile. It can produce and download the package; installation is a ticketed, human, QAD-side action.** [CONFIRMED from the quoted text; the docs do not state whether on-prem/non-cloud differs — silent.]

**[CONFIRMED] The second, finer-grained promotion channel — Configuration Data export/import**, which moves *artifacts* rather than the app:
- What it carries: `Role, Menu & Permissions` artifacts (C8:561), `Alert` artifacts (C5:482), `Activity Tracking` artifacts (C5:483). KPIs are also `Saved To: Configuration Data` (C4:955).
- Export flow (C8:576–629): Configuration Data screen → search → select artifact → `Actions` → `Export Configuration Data` → select artifact checkbox → `Submit` → Inbox notification → `Download` (zip).
- Import flow (C8:739–758): Configuration Data → `Import` action → choose file → *"Review the content of file in the preview, and then click Submit."* → Inbox confirmation (C8:775).
- **[CONFIRMED] Import does NOT restore role membership.** C8:777 verifies role + menu returned, then C8:794–796: *"Go to User Access and find Training User. Assign the Training Role back and click Save."* A deployer promoting roles must re-assign members as a separate step.
- [INFERRED] The Configuration Data screen has a scope/type distinction `Individual` vs `Bulk`. Basis: the OCR of the Actions-open screenshot at C8:605 contains the tokens `Individual Artifact starts with "role"` and `Bulk View`. The clean markdown table at C8:590 shows only columns `Type | Artifact | Label | View | Status`, so these tokens are most likely a `Type` filter dropdown. **This is a weak inference from interleaved OCR — confirmable by opening the Configuration Data screen and reading the Type dropdown.**

---

### 6. The three live-environment symptoms

**Symptom A — HTTP 500 on entity-metadata generation and on build-api-sources.**
**[CONFIRMED SILENT.]** No HTTP status code appears in any of the three files. No screen, action, or button named "entity metadata generation" or "build api sources" is documented. The closest *named artifacts* are the BC panel `Source File Generation` (C5:636) and the OS Scripts `create_app_metadat...` and `compile_app_source...` (C5:168, C5:170) — the docs never describe running either, never state prerequisites for either, and never show an error for either. **I will not offer a cause.**
Adjacent [CONFIRMED] facts that bear on diagnosis without explaining it: `compile_app_source` exists as two separate rows, `Server` and `Client` (C5:168–169); all OS Scripts report outcome asynchronously via Inbox rather than synchronously (C5:196).

**Symptom B — dependency jar download failing with "Downloading of core libs failed".**
**[CONFIRMED SILENT.]** The strings `jar`, `core lib`, `dependen`, and `library` do not occur in any of the three files. There is no dependency-management content at all in this document set. **I will not offer a cause.**

**Symptom C — a created test BC stuck in "Initial" status.**
**[CONFIRMED SILENT on the value "Initial" as a BC status.]** The word `Initial` occurs in these files only in `Initial Sort` / `Initial Sorting` / `Initial Configuration` headings (C4:17, 388, 396, 494, 508–567; C5:518–588) and `Initials: [ ]` on the user form (C8:120). **No BC status lifecycle, no list of status values, and no state-transition rules appear in any of the three documents.**
The **only** BC status value shown anywhere in the set is `Deployed`, at C5:636, in the BC header:
```
Training  Training  Deployed
Business Component  App  Status
```
[INFERRED, and flagged as inference] The existence of a `Status` field on the BC header alongside a `Deployment` panel with a `Deploy` button (C5:553–557) implies status is advanced by the Deploy action. The docs do not say this. Confirmable by observing the Status value on a BC immediately before and immediately after pressing `Deploy`.

**The only "required setup order" statements that exist in the three docs** — quoted in full because they are the closest thing to prerequisites anywhere in this set:
- C5:174: *"Activity Tracking is based on Activity Feeds mechanism which could be inactive if never used on this environment."* (→ run `activity_feed_update` first, C5:176–180)
- C4:466: *"You will get a warning that a yab command is required."* (→ `yab stop database-extension-index-rebuild` / `yab start` via Putty, C4:479–483)
- C5:704: *"Then click Compile button (bottom right). Save handler and close editor."* (compile precedes save for event handlers)
- C5:687: *"Do not change this class name or the event handler will no longer run."*
- C5:721: *"You will see Training record which is not active."* → C5:736: *"Select the Enabled checkbox and then Save & Close."* (approval config must be explicitly enabled after being created by the BC-level Configure step)
- C4:381: *"You may need to refresh a page if you don't immediately see the result as shown."*

---

---

## V. Verification appendix

Each section above was drafted by one agent and then independently citation-checked by a second agent that re-opened the cited files. This appendix records what that check found. Where a verifier issued a correction, the correction supersedes the section text.

### new-bc-pipeline — verification verdict: `minor-issues`

**Claims the verifier could not support:**

- {"claim": "`models.py:33` independently hard-codes `total: int = 14` on `SSEEvent` (repeated in A1.5 #10: \"`TOTAL_STEPS` a third time in `models.py:33`\")", "cited": "backend/models.py:33", "whats_actually_there": "Line 33 is `step: Optional[int] = None`. `total: int = 14` is on line **34**. The substance (a third hard-coded copy of 14) is correct; only the line number is off by one.", "severity": "bad-citation"}
- {"claim": "\"`grep -rn \"lookup\" frontend/src/` matches nothing outside an unrelated embedded label and CSS tokens\"", "cited": "frontend/src/ (grep result asserted in A1.3)", "whats_actually_there": "`grep -rni \"lookup\" frontend/src/` returns **zero** matches \u2014 and zero across all of `frontend/` excluding node_modules/dist. The \"unrelated embedded label and CSS tokens\" hits do not exist. The conclusion (`summary.lookups` is never rendered) is correct and in fact stronger than stated, but the reported grep output is fabricated.", "severity": "wrong"}
- {"claim": "\"The normalization the commissioner heard about is **step 6** (`_normalize_placements`), eleven steps' worth of code later.\"", "cited": "backend/pipeline.py:419 (step 2) vs :554-590 (step 6)", "whats_actually_there": "Step 2 \u2192 step 6 is **four** steps later (and 128 lines: :426 \u2192 :554). \"Eleven steps\" is arithmetically wrong. The load-bearing claim (FIELD_CREATOR is step 2, normalization is step 6, they are different things) is correct.", "severity": "wrong"}
- {"claim": "Step 13's two failure branches \"carry the *same* message text\" / \"emit identical text\", so \"a network failure and a QAD rejection are indistinguishable\" (also A1.5 #7)", "cited": "backend/pipeline.py:714 and :718", "whats_actually_there": ":714 is `f\"View registration failed: {e}\"` (exception text); :718 is `f\"View registration failed: {json.dumps(err)}\"` (QAD error JSON). Identical **prefix**, different payloads \u2014 the two causes are distinguishable from the message body, just not from the leading phrase.", "severity": "overstated"}
- {"claim": "\"[CONFIRMED] ... `json_mode` forces a top-level object, so `gpt-4o` will not return the bare array **the prompt asks for**.\"", "cited": "backend/pipeline.py:261-264 (docstring)", "whats_actually_there": "The docstring says that, but it is stale. The current (uncommitted) `FORM_FIELD_BUILDER` asks for the opposite: \"OUTPUT \u2014 ONE JSON object whose \\\"placements\\\" key holds the ARRAY\" plus \"Return ONE object: starts with { ends with }\" and \"NEVER return a single placement object on its own\" (prompts.py:196, :207-209). `git diff backend/agents/prompts.py` shows the prompt was changed from \"raw JSON array only / Starts with [ ends with ]\". The audit relays the stale comment as a confirmed fact about the prompt.", "severity": "overstated"}
- {"claim": "\"`grep -rni \"approv|human.in.the.loop|await_user|pause\"` over `backend/` returns **only**: prompts.py:76, embedded_builder.py:189, and three hits in the separate SSS feature (routers/sss.py:4, 21, 101).\"", "cited": "backend/ grep result asserted in A1.3", "whats_actually_there": "The same grep also returns `backend/sss/discover.py:30` (\"# Approved scope: standard Sales + Purchasing only.\") \u2014 six hits, not five. The missed hit is also SSS-only, so the conclusion (\"no approval gate anywhere in this pipeline\") is unaffected and independently confirmed by route enumeration (no websocket, no approve/resume route).", "severity": "overstated"}
- {"claim": "\"Different code tree: `backend/sss/{discover,generate,compile,deploy,appconfig,readiness,templates}.py`, imported **only** by `routers/sss.py` (`sss.py:31-34`).\"", "cited": "backend/routers/sss.py:31-34", "whats_actually_there": "The imports are at sss.py:**27-31**; :31-34 is the last import plus blank lines and the logger. Also `sss.appconfig` is imported by `core/sss_scaffold.py:98`, not only by routers/sss.py, and `appconfig`/`templates` are not imported by routers/sss.py at all. The load-bearing part \u2014 `run_pipeline` imports none of `sss/*` \u2014 is confirmed (grep for `sss` in pipeline.py returns nothing).", "severity": "bad-citation"}
- {"claim": "\"[CONFIRMED] Step numbering is not injective. `TOTAL_STEPS = 14` but there are **16 distinct work units**.\"", "cited": "backend/pipeline.py:142, :511, :540, :29-31", "whats_actually_there": "The underlying facts are all confirmed (14 labels; dropdown wiring re-emits step 3; lookup frames carry no step key). But \"16\" is a derived count that silently excludes the audit's own Step 0, Post-14a, Post-14b and Post-14c entries \u2014 by the audit's own inventory the number is not 16. This is a judgment call tagged [CONFIRMED] rather than a value read from a file.", "severity": "mislabelled-inference"}

**Material the verifier found missing:**

- No app-level authentication on `POST /api/run`. `backend/routers/client_extensions.py:117-119` has no `Depends(...)`, `main.py:86-94` registers routers with no auth dependency, and the only middleware is CORS + SlowAPI (`main.py:61, :71`). `backend/routers/auth.py` exists (`/api/auth/login`, `/api/auth/me`, `get_current_user` used only at auth.py:69) but is never applied to the pipeline route. This is directly material to A1.3: there is no server-side notion of *who* is running or would approve a gated step.
- Post-14c failure path is incompletely described. `client_extensions.py:189` and `:191` use bracket indexing (`summary["bc_pascal"]`, `summary["field_count"]`) while the neighbouring fields use `.get()`. A `complete` frame missing either key raises KeyError inside the `try` at `:184`, which is swallowed by the logger at `:199-200` — the run row is silently never written. The `run_id` frame at `:203` is emitted outside that try, so the client is handed a run_id pointing at a nonexistent history row.
- `RunRequest.message` is capped at 200_000 chars (`models.py:8, :12`) — the only input guard on the Step-0 / `_extract_progress_attachment` path, which the Step-0 row does not mention.
- The A1.2 durable-sink table omits the startup path that also writes/reads `parent_entities`: `main.py:97+` runs a one-time seed/backfill/hydrate guarded by `PARENT_BACKFILL_VERSION` / SQLite `PRAGMA user_version`, which merges persisted rows back into the same in-memory `QAD_STANDARD_ENTITIES` cache the pipeline writes at Post-14b.
- The exhaustive `grep -rn FIELD_CREATOR` list also hits `backend/builders/embedded_builder.py:42` (a comment referencing EMBEDDED_FIELD_CREATOR). Immaterial to the conclusion, but the list is stated as complete.

**Corrections:**

## Corrections

**A1.0 / A1.5 #10 — `models.py` line number**
> `models.py:33` independently hard-codes `total: int = 14`

→ `models.py:**34**` hard-codes `total: int = 14` (line 33 is `step: Optional[int] = None`).

**A1.1 Step 2 note — step distance**
> The normalization … is **step 6** (`_normalize_placements`), eleven steps' worth of code later.

→ "…is **step 6** (`_normalize_placements`), four steps later (`pipeline.py:426` → `:554`)."

**A1.1 Step 6 — "the bare array the prompt asks for"**
> The reason is documented in the docstring at `:261-264`: `json_mode` forces a top-level object, so `gpt-4o` will not return the bare array the prompt asks for.

→ "The docstring at `:260-264` gives the original reason (json_mode forces a top-level object, so `gpt-4o` would not return the bare array the prompt then asked for). **That docstring is now stale**: the uncommitted `FORM_FIELD_BUILDER` was rewritten to demand an object — `\"OUTPUT — ONE JSON object whose \\\"placements\\\" key holds the ARRAY\"` (`prompts.py:196`), `\"Return ONE object: starts with { ends with }\"` and `\"NEVER return a single placement object on its own\"` (`prompts.py:207-209`) — so the normalizer now defends against shapes the prompt explicitly forbids rather than against the prompt's own request."

**A1.1 Step 13 / A1.5 #7 — "identical text"**
> exception and QAD-failure branches carry the *same* message text `"View registration failed: …"` (`:714` and `:718`), which makes the two causes indistinguishable in the UI.

→ "…share the same **prefix** `\"View registration failed: \"` but differ in payload — `{e}` at `:714` vs `json.dumps(err)` at `:718`. The two causes are distinguishable from the message body, but not from the leading phrase, and unlike step 3 neither is run through `_qad_error_messages`."

**A1.3 — approval grep**
> returns only: … and three hits in the **separate** SSS feature (`routers/sss.py:4, 21, 101`).

→ "…and **four** hits in the separate SSS feature (`routers/sss.py:4, 21, 101` and `sss/discover.py:30`)."

**A1.3 — dropped lookup frames**
> `grep -rn "lookup" frontend/src/` matches nothing outside an unrelated embedded label and CSS tokens

→ "`grep -rni \"lookup\" frontend/src/` returns **zero matches** — the string does not appear anywhere in the frontend source at all (nor anywhere under `frontend/` excluding `node_modules`). The point stands, more strongly than stated."

**A1.4 — SSS code tree**
> `backend/sss/{…}.py`, imported only by `routers/sss.py` (`sss.py:31-34`). `run_pipeline` imports none of it.

→ "`backend/sss/{discover,generate,compile,deploy,readiness}.py` are imported by `routers/sss.py:27-31`; `sss.appconfig` is additionally imported by `core/sss_scaffold.py:98`. The load-bearing fact is unchanged and independently verified: `run_pipeline` imports nothing from `sss/` (grep for `sss` in `backend/pipeline.py` returns no match)."

**A1.5 #1 — work-unit count**
> **[CONFIRMED]** … there are **16 distinct work units**

→ Retag as **[INFERRED]**. Confirmed: `TOTAL_STEPS = 14`, dropdown wiring re-emits `step:3` running/done, lookup frames carry no `step` key. The total "16" is a counting judgment that excludes the audit's own Step 0, Post-14a/b/c rows.

## Notes (not flagged)

- Header claim that `D:/WEB_AUX/adaptive_java_version` "contains only a `Docs/` folder": it also contains `PLAN.md`, `PROGRESS.md`, `QUESTIONS.md`, `PHASE0_AUDIT.md` — all timestamped within minutes of the audit, so most likely written by this same workflow after the observation.
- **No secrets leaked.** QAD credentials are referenced only as call sites (`config.qad_client_id()`, `qad_username()`, `qad_password()` at `qad_client.py:43-49`); no token, password, client-id or connection string value appears in the section.

## Independently re-verified and confirmed (no correction needed)

Step order and all 14 labels; every QAD endpoint string (steps 3, 3.5, 7, 11, 13, 14) and the absence of a `viewUri` param on `viewMetadataV2`; the `_evt`/`_sse` frame schemas; `state` created at `:397`, all 11 write sites in the stated order, never returned/yielded/persisted; both unnumbered work units and the backwards `4→3` step emission; `deployCheckForWarnings` discarded at `:739`; `_qad_error_messages` wired only into step 3; LLM budget 6/7/9 and the stale `# each run spawns 8 LLM calls` comment; the whole uncommitted-work attribution (verified against `git diff` — including that the pre-change step-4 message was raw `json.dumps(err)`); every builder's return shape and payload keys; `is_qad_success` semantics; `tsc --noEmit` gate and its silent no-op when tsc is absent; `create_lookup`'s `dry_run is not False` guard and the unreachable live POST; all four SSS-separation claims and SSS's two-call approval gate. **Absence claims re-tested by my own greps and all hold**: no approval/pause mechanism in `backend/`; no websocket or resume/approve route (full route enumeration across all five routers); no `while` over a step index and no dispatch table in `run_pipeline`; no token caching in `qad_client.py`; no durable file write anywhere in `pipeline.py` or `builders/*`; no `sss`/server-side-rule reference in `pipeline.py`.
### embedded-pipeline — verification verdict: `minor-issues`

**Claims the verifier could not support:**

- {"claim": "A repo-wide grep for `get_qad(` returns only three call sites: backend/pipeline.py:516, backend/pipeline_embedded.py:240, and the definition at backend/qad_client.py:64.", "cited": "Q3 \u2014 backend/pipeline.py:516, backend/pipeline_embedded.py:240, backend/qad_client.py:64", "whats_actually_there": "`grep -rn \"get_qad(\" backend/` returns five hits: the three cited plus backend/probe_parent_eh.py:51 and backend/probe_parent_eh.py:100. The absence claim was asserted at repo scope but only verified over the two pipelines.", "severity": "wrong"}
- {"claim": "There is no GET of `eventhandler`, no GET of `viewMetadataV2`, no GET of `viewResourceMetadatas`, and no GET of `berelation` anywhere in the codebase.", "cited": "Q3 (no file cited \u2014 asserted from the get_qad grep)", "whats_actually_there": "backend/probe_parent_eh.py:44-51 performs exactly that GET: `eventhandler?appURI=<custom app>&viewURI=urn:view:viewmeta:com.qad.erp.sales.SalesOrders&eventHandlerType=BEFORE&appliesTo=WEB`, then reads `get_result[\"data\"][\"eventHandlerV2s\"][0]` incl. `uri` and `concurrencyHash` (:58-63), and re-GETs at :100. The viewMetadataV2 / viewResourceMetadatas / berelation halves of the claim do hold.", "severity": "wrong"}
- {"claim": "the `eventhandler` endpoint is only POSTed from backend/pipeline.py:685", "cited": "backend/pipeline.py:685 (Q1, \"No event handler\")", "whats_actually_there": "post_qad(\"eventhandler\", ...) also appears at backend/probe_parent_eh.py:91 (shape A: uri + concurrencyHash) and :126 (shape B). pipeline.py:685 is the only *pipeline* call site, not the only repo call site.", "severity": "wrong"}
- {"claim": "Only four keys are ever written: state[\"requirements\"] (:84), state[\"spec\"] (:151 and :197), state[\"view_label\"] (:339).", "cited": "backend/pipeline_embedded.py:64,84,151,197,339", "whats_actually_there": "Three distinct keys across four write sites. All line citations are correct; the count is not.", "severity": "wrong"}
- {"claim": "The LLM returns `parent_entity_key` (contract at backend/agents/prompts.py:437)", "cited": "backend/agents/prompts.py:437", "whats_actually_there": "Line 437 is `\"wants_separate_view\": false,`. `\"parent_entity_key\": \"SalesOrderHeaders\",` is at line 434.", "severity": "bad-citation"}
- {"claim": "\"bcType\": \"Standard\" (:167)", "cited": "backend/builders/embedded_builder.py:167", "whats_actually_there": "Line 167 is `\"bdocumentCode\": \"\",`. `\"bcType\": \"Standard\",` is at line 165.", "severity": "bad-citation"}
- {"claim": "the child BC's own viewResourceInfos[0][\"parentEntity\"] is left as the literal \"none\" (backend/builders/embedded_builder.py:216)", "cited": "backend/builders/embedded_builder.py:216", "whats_actually_there": "Line 216 is `\"gridViewURI\": None,`. `\"parentEntity\": \"none\",` is at line 219. (The claim itself is true; only the line is wrong.)", "severity": "bad-citation"}
- {"claim": "viewResourceInfos[0][\"eventHandlerInfos\"] is shipped as [] (backend/builders/embedded_builder.py:212)", "cited": "backend/builders/embedded_builder.py:212", "whats_actually_there": "Line 212 is `\"entityDescription\": bc_pascal,`. `\"eventHandlerInfos\": [],` is at line 213.", "severity": "bad-citation"}
- {"claim": "isIncludeOnParent: False (backend/builders/embedded_builder.py:303)", "cited": "backend/builders/embedded_builder.py:303 (OPEN QUESTION 1)", "whats_actually_there": "Line 303 is `\"isExtension\": True,`. `\"isIncludeOnParent\": False,` is at line 304. (The earlier range citation :302-307 in Q1 is fine.)", "severity": "bad-citation"}
- {"claim": "embedded field codes are written raw into entityFieldCode / physicalFieldName / fieldURI (:84,88,117)\" and \"the embedded builder sets it to the raw f[\"code\"] (:84)", "cited": "backend/builders/embedded_builder.py:84 (A2.3.2 and A2.3.3)", "whats_actually_there": "Line 84 is `\"entityFieldID\": f_efid,`. `\"entityFieldCode\": f[\"code\"],` is at line 83. The trio is also mis-ordered: fieldURI is :88 and physicalFieldName is :117. The substantive point (raw code, no sql_safe) is correct.", "severity": "bad-citation"}
- {"claim": "A case-insensitive grep for approval|approve|pause|resume|gate|confirm across backend/**/*.py returns only: [ts_compiler.py:61, sss/readiness.py:2, core/auth.py:17, embedded_builder.py:189, sss/discover.py:43,109-113, and prompt text].", "cited": "Q5 \u2014 enumerated grep result", "whats_actually_there": "The same grep also returns backend/routers/sss.py:4, :21, :101 (\"approved route map\", \"the compiled TS a user approves for deploy\", \"Write the approved .ts\"), core/auth.py:5, ts_compiler.py:7,19,21,70,103,118, pipeline.py:654, sss/discover.py:14,30,61,196, sss/templates.py:14,15,36,39,49,70, core/lookup_generator.py (~20 \"confirmed\" hits), core/lookup_detector.py:14, prompts.py:76. The substantive conclusion \u2014 no pause/resume/approval-gate machinery on the run path \u2014 survives, but the enumeration is presented as exhaustive and is not.", "severity": "overstated"}
- {"claim": "grep for run_id in the router shows :120 (assign) and :186,200,203 (use); req.run_id appears nowhere", "cited": "backend/routers/client_extensions.py:120,186,200,203", "whats_actually_there": "`grep -n run_id backend/routers/client_extensions.py` also returns :202 (comment) and :221,222,223,229,230,231 (the /api/history/{run_id} path params). The load-bearing half \u2014 `req.run_id` never read, RunRequest.run_id unused \u2014 is CONFIRMED.", "severity": "overstated"}
- {"claim": "the registry's fk_field contract is \"the single FK field the embedded child BC links on\" (backend/qad_entity_registry.py:22-23)", "cited": "backend/qad_entity_registry.py:22-23", "whats_actually_there": "That sentence is on line 21; :22 is the parenthetical \"(usually the business key, NOT DomainCode)\" and :23 is the fk_type line.", "severity": "bad-citation"}

**Material the verifier found missing:**

- backend/probe_parent_eh.py (untracked, 135 lines) — a standalone probe that GETs the *parent's* existing event handler on a standard QAD view (`urn:view:viewmeta:com.qad.erp.sales.SalesOrders`, :44-51) and POSTs it back as an update (:91, :126). It refutes the audit's repo-scope absence claims AND is the direct evidence for the audit's own OPEN QUESTION 5 ("whether QAD accepts an eventHandlerV2 whose viewURI points at a standard QAD parent view"): its docstring says "Uses the SalesOrders handler we already know exists." It also exposes the update contract — an update must echo `uri` + `concurrencyHash` from the GET (:77,:83) — which build_event_handler_payload emits neither of, so that builder can only CREATE, never UPDATE, an existing handler. This belongs in Q2/Q3/Q5 and materially changes the Phase-5 'what has to be built' list.
- Frontend step labels for embedded mode do not match the backend STEP_LABELS the audit tabulated verbatim, and the UI ignores the SSE `name` field entirely (ProgressPanel.tsx:70 renders `stepNames[n]` from its own map): id 1 = "Understanding requirements for Embedded BC", id 4 = "Handling duplicates & Retrying", id 5 = "Building relations to parent order" (ProgressPanel.tsx:23-29). The audit noted only the missing step 8.
- Step 3.5's own terminal success check on the wiring POST — `if not is_qad_success(wire_result)` at backend/pipeline_embedded.py:258-261 — is absent from the step inventory (the audit's sequence stops at :254). A failed dropdown-wiring POST aborts the run after the BC already exists in QAD, i.e. a partial-state failure mode worth naming next to the step-4 retry analysis.
- The 'No lookups' bullet does not mention that backend/core/lookup_detector.py and backend/core/lookup_generator.py exist as new untracked modules (lookup_generator even builds a QAD POST payload); the claim is correct for the embedded pipeline but reads as if the capability does not exist at all.

**Corrections:**

## Corrections

**Q3 — repo-scope absence claims (rewrite both bullets):**

> - **[CONFIRMED]** `get_qad(` has five call sites: `backend/pipeline.py:516`, `backend/pipeline_embedded.py:240`, `backend/probe_parent_eh.py:51` and `:100`, plus the definition at `backend/qad_client.py:64`. Only the first two are on a pipeline path.
> - **[CONFIRMED]** No pipeline GETs `viewMetadataV2`, `viewResourceMetadatas` or `berelation` anywhere. However, `eventhandler` **is** read back — outside the pipelines — by the standalone probe `backend/probe_parent_eh.py:44-51`, which GETs the *parent's* handler on the standard QAD view `urn:view:viewmeta:com.qad.erp.sales.SalesOrders` and POSTs it back as an update at `:91` / `:126`. That probe already establishes (a) that a handler exists on a standard parent view in the target instance and (b) that an update must echo `uri` + `concurrencyHash` from the GET (`:77`, `:83`).

**Q1 — "No event handler" bullet:**
> the `eventhandler` endpoint is POSTed from `backend/pipeline.py:685` (the only pipeline call site) and from the probe script `backend/probe_parent_eh.py:91,126`.

**OPEN QUESTION 5 — replace "To confirm":**
> **Partially answered already:** `backend/probe_parent_eh.py` was written to test exactly this and targets a standard QAD parent view. Read its recorded outcome (or re-run it) before treating this as open. Note the existing builder emits no `uri`/`concurrencyHash`, so it cannot update an existing parent handler — only create.

**A2.1.11:**
> Only **three** keys are ever written, across four write sites: `state["requirements"]` (`:84`), `state["spec"]` (`:151`, `:197`), `state["view_label"]` (`:339`).

**Q5 — approval grep:**
> A case-insensitive grep for `approval|approve|pause|resume|gate|confirm` across `backend/**/*.py` returns ~50 hits, **none of which is run-gating machinery** — they are tsc/readiness/auth "gate" comments, SSS route-gating and `WithConfirmation` method discovery, the `isAllowApproval: False` payload literal, `lookup_generator`'s "confirmed" annotations, and prompt text. Absence of any per-run approval/pause/resume mechanism is a finding.

**Q5 — run_id:**
> `grep -n run_id backend/routers/client_extensions.py` → `:120` (assign), `:186,200,202,203` (use/comment), `:221-231` (history path params). **`req.run_id` appears nowhere** — `RunRequest.run_id` (`backend/models.py:13`) is never read.

**Citation fixes (line numbers only; claims stand):**
- `parent_entity_key` contract → `backend/agents/prompts.py:434` (not `:437`)
- `"bcType": "Standard"` → `backend/builders/embedded_builder.py:165` (not `:167`)
- `"eventHandlerInfos": []` → `:213` (not `:212`)
- `"parentEntity": "none"` → `:219` (not `:216`)
- `"isIncludeOnParent": False` → `:304` (not `:303`)
- `"entityFieldCode": f["code"]` → `:83` (not `:84`); the trio reads `entityFieldCode :83`, `fieldURI :88`, `physicalFieldName :117`
- fk_field contract sentence → `backend/qad_entity_registry.py:21` (not `:22-23`)
- the single GET is at `backend/pipeline_embedded.py:240-243`; `:239` is `token = await get_token()`

**Additions to the step inventory:**
- Step 3.5 also carries its own terminal success check: `if not is_qad_success(wire_result)` (`backend/pipeline_embedded.py:258-261`) — a wiring failure aborts the run *after* the BC exists in QAD.
- The UI never renders the backend `name` field; `ProgressPanel.tsx:70` uses its own `EMBEDDED_STEP_NAMES` (`:23-29`), whose text differs from `STEP_LABELS` for ids 1, 4 and 5.

**Verified clean (spot-checked and correct):** step order and all `_evt` line refs; the 3→done→running→done step-id collision; `MANYTOONE` + both `BERelationFields`; `relationID` prefix at `:278`; `deployCheckForWarnings` result discarded (`:299`, and `pipeline.py:739`); `VALIDATOR_AND_CORRECTOR` = `prompts.py:100-155` with no `{QAD_DOCS_CONTEXT}` and no embedded rules; PK ordering `prompts.py:468-474` + rationale `:477`; the `sql_safe` key-mismatch finding (`bc_builder.py:144-146` vs `:107`, `SQL_RESERVED` `:8-16`); `view_builder.py` refs (`:40-47`, `:59-61`, `:102`, `:106`, `:109-147`, `:141`, `:161`); `main.py:82,89,93-94`; `PROGRESS.md:186-189,197,215`; no `.asend(`/`.athrow(` anywhere; the three audited files are byte-identical to commit `84d209b` (`git diff` empty). No secret values were leaked — the OAuth query params are correctly redacted.
### sss-pipeline — verification verdict: `minor-issues`

**Claims the verifier could not support:**

- {"claim": "[CONFIRMED] The docs_url is a dead link. ... The frontend surfaces it as a \"Setup Guide\" link.", "cited": "core/config.py:50; docs/ contains only BC_PROMPT_TEMPLATE.md", "whats_actually_there": "The backend half is right (no route serves /docs/setup-sss), but the frontend never navigates there, so nothing dead-ends. frontend/src/shared/components/HealthPanel.tsx:48-57 renders docs_url as a *presence flag* driving a <button type=\"button\"> that toggles an inline 4-step guide (:59-82) \u2014 there is no <a href>. The inline comment at :45-47 says the URL is \"a stable contract marker, not a served page\", and the docstring at :8-10 says it works \"no navigation, so it works identically in dev and prod and can never dead-end on a missing route\". PROGRESS.md:36 records this exact item as struck through and RESOLVED. The audit inferred the UI behaviour from the constant instead of reading HealthPanel.tsx.", "severity": "wrong"}
- {"claim": "OPEN QUESTION 4: \"Is /docs/setup-sss meant to be a backend route or an SPA route? ... My suggested answer: an SPA route that was never built; the SPA StaticFiles(html=True) mount would serve index.html for it, so the user lands on the app, not a guide. To confirm: ask whether a setup-guide page was ever specified.\"", "cited": "core/config.py:47-50; main.py:214; PROGRESS.md:133", "whats_actually_there": "The question is already answered in-repo and should not have been left open. PROGRESS.md:36 states the user chose an in-app panel and the guide was built and verified live; HealthPanel.tsx:48-84 is that guide. It is neither a backend nor an SPA route \u2014 it is a non-navigating marker string, and main.py:214 is never reached for it because nothing links to it.", "severity": "overstated"}
- {"claim": "Different QAD auth surfaces: CE uses OAuth2 password-grant Bearer (core/qad_session.py:43, /qad-central/oauth/token)", "cited": "core/qad_session.py:43", "whats_actually_there": "qad_session.py:43 does define `async def get_bearer_token(...)`, but a repo-wide grep for `get_bearer_token` returns only its own definition and its own docstring \u2014 zero callers. The Client Extensions pipeline authenticates through `qad_client.get_token()` (backend/qad_client.py:42-52), a separate implementation that builds the OAuth URL itself. The CE-vs-SSS distinction (Bearer vs JSESSIONID) is correct; the cited function is dead code and is not the CE auth path.", "severity": "bad-citation"}
- {"claim": "Repo-wide grep for `from sss|import sss` outside the SSS package returns exactly one hit: main.py:83 (the router import) and core/sss_scaffold.py:98 (a local `from sss import appconfig` ...)", "cited": "main.py:83, core/sss_scaffold.py:98", "whats_actually_there": "Internally contradictory (\"exactly one hit\" then two locations) and factually wrong. The grep returns 7 hits outside backend/sss/: routers/sss.py:27,28,29,30,31 (`from sss import discover|generate|compile|deploy`, `from sss.readiness import ...`), core/sss_scaffold.py:98, and main.py:83 \u2014 and main.py:83 is `from routers import sss as sss_router`, i.e. the router module, not the sss package. The load-bearing sub-claim (pipeline.py imports nothing from sss) is independently correct: pipeline.py's only SSS-adjacent import is `from core.ts_compiler import check_typescript_syntax` at pipeline.py:14.", "severity": "wrong"}
- {"claim": "`auto_deploy` ... is hardcoded `False` and read by nothing except public_status(). It is dead \u2014 there is no auto-deploy bypass to worry about. [CONFIRMED \u2014 absence]", "cited": "core/config.py:34,103,176; routers/settings.py:28", "whats_actually_there": "config.py:103 is only the *default*. `auto_deploy` is a member of `_UI_KEYS` (config.py:34), and the settings.json merge loop at config.py:107-109 overwrites it with any persisted value, which `save_ui_settings` (config.py:192-195) will write from `POST /api/settings`. So it is settable, not hardcoded \u2014 the audit's own OPEN QUESTION 5 says exactly that, contradicting A3.2. The absence half is confirmed: I grepped and nothing but `public_status()` reads it (frontend/src/shared/api.ts:34,46 only type it).", "severity": "overstated"}
- {"claim": "Failure mode: returns False or raises; main.py:191-192 swallows it into a log line. Startup never fails. The user only learns via GET /api/health (core/health.py:74-139). [CONFIRMED]", "cited": "core/health.py:74-139", "whats_actually_there": "health.py never observes `scaffold_sss_workspace`'s return value. check_sss_folder (:74-110) and check_tsc (:113-139) independently re-stat the folder, lib/*.d.ts and node_modules/typescript/package.json. A scaffold failure is reported only as `logger.error(\"SSS workspace scaffold failed: %s\")` at main.py:192; health may coincidentally show the same symptoms. That linkage is deduced, not read at the cited lines.", "severity": "mislabelled-inference"}
- {"claim": "outFile: dist/customappdev.js matches app_script_name() = \"customapp\" (appconfig.py:25-28, from `QAD_APP_URI = urn:app:com.extensions.customapp` in backend/settings.json)", "cited": "backend/settings.json", "whats_actually_there": "The resolved value is right, the key name is not. backend/settings.json contains `\"qad_app_uri\": \"urn:app:com.extensions.customapp\"` (lowercase, settings.json naming). `QAD_APP_URI` is the .env key name and does not appear in backend/.env at all \u2014 the effective value comes only from the settings.json override path at config.py:107-109.", "severity": "bad-citation"}

**Material the verifier found missing:**

- core/qad_session.get_bearer_token() has zero callers repo-wide — it is dead code. CE's real token path is backend/qad_client.py:42-52, which puts client_id, username and password in the OAuth **URL query string** (`?client_id=…&username=…&password=…&grant_type=password`) rather than a POST body. For a section that devotes a bullet to "auth mechanics" and "different QAD auth surfaces", credentials-in-a-URL is the more important finding and it is absent.
- GET /api/sss/connection returns HTTP 200 with {"ok": false, "message": …} on an authentication failure (deploy.py:110-114) — it never signals failure via status code. The audit calls it "a login probe only" but does not note that its failure mode mirrors the deploy.py:94-97 weakness it criticises elsewhere.
- The audit's "**No rate limit decorator** (contrast /generate)" on /api/sss/deploy is true but reads as unlimited. core/rate_limit.py:21 constructs `Limiter(key_func=get_remote_address, default_limits=["30/minute"])` and main.py:61 installs SlowAPIMiddleware app-wide, so /deploy is in fact capped at 30/min per IP. Worth stating because A3.2 argues the deploy endpoint is the unguarded surface.
- routers/settings.py:26 exposes `qad_app_dir` on UiSettingsUpdate, but config.py:34 `_UI_KEYS` omits it, so save_ui_settings (config.py:192-194) silently discards it. The one setting that would fix an SSS 503 from the UI cannot actually be set from the UI — directly relevant to the A3.1 readiness/setup story and to OPEN QUESTION 6.
- The step inventory names step 4 as the only frontend step. The SSS UI is a declared three-step flow (SssPanel.tsx:12-13): step 1 BcPicker.tsx (BC selection + field insertion via `insertField`, SssPanel.tsx:61-63) and step 2 RulePrompt.tsx. Neither appears in the table, and BcPicker's field-click-to-insert is the mechanism that keeps user prompts inside the `rec.X` guard's valid-field set.

**Corrections:**

### A3.1, Step 1 — replace the "dead link" bullet

> **[CONFIRMED] `docs_url` is a marker string, not a link.** `core/config.py:50` sets `SSS_SETUP_DOCS_URL = "/docs/setup-sss"`; no FastAPI route serves it and `docs/` holds only `BC_PROMPT_TEMPLATE.md` — but nothing navigates to it. `HealthPanel.tsx:48-57` uses `check.docs_url` purely as a *presence flag* to render a `<button>` that toggles an inline four-step setup guide (`:59-82`); there is no `<a href>`. The component states the intent: *"the URL is a stable contract marker, not a served page"* (`:45-47`) and *"can never dead-end on a missing route"* (`:8-10`). `PROGRESS.md:36` records the stub as **RESOLVED** for exactly this reason. A Phase-2 port should keep the flag-not-URL idiom or drop the string entirely.

**Delete OPEN QUESTION 4** — it is answered in-repo by `PROGRESS.md:36` + `HealthPanel.tsx`.

### A3.3 — replace the auth bullet and the grep bullet

> - Different QAD auth surfaces: CE uses an OAuth2 password-grant Bearer token, minted by `qad_client.get_token()` (`backend/qad_client.py:42-52`) against `/qad-central/oauth/token`; SSS uses form-login JSESSIONID via `core/qad_session.get_session_cookie()` (`qad_session.py:70`) against `/qad-central/api/login`. Note `core/qad_session.get_bearer_token()` (`:43`) is **dead code — zero callers**; the CE path is a separate implementation that passes `client_id`/`username`/`password` in the request **URL query string**.
> - **`backend/pipeline.py` never imports anything from `sss`.** Its only overlap is `from core.ts_compiler import check_typescript_syntax` (`pipeline.py:14`) — a shared core utility, not the SSS compile step. Repo-wide, `from sss|import sss` outside `backend/sss/` resolves to `routers/sss.py:27-31` (the feature's own router) and `core/sss_scaffold.py:98` (a local `from sss import appconfig` for the outFile check). No pipeline/CE module is among them.

### A3.2 — replace the `auto_deploy` bullet

> - `auto_deploy` defaults to `False` (`core/config.py:103`) but is **not** hardcoded: it is in `_UI_KEYS` (`:34`), so a value persisted to `settings.json` by `POST /api/settings` (`routers/settings.py:28` → `config.py:192-195`) overrides the default at `config.py:107-109`. It is nonetheless **inert** — verified by grep, nothing but `public_status()` (`:176`) reads it, so there is no auto-deploy bypass today. [CONFIRMED — absence of any reader]

### A3.1, Step 0 — soften the failure-mode tag

Change `[CONFIRMED]` to a stated inference: `main.py:192` logs the failure and startup continues; `GET /api/health` does **not** report the scaffold result — `check_sss_folder`/`check_tsc` (`health.py:74-139`) re-derive status from the filesystem independently, so they surface *symptoms*, not the scaffold return value.

### A3.4 — key-name fix

`app_script_name()` = `"customapp"` derives from `backend/settings.json`'s **`qad_app_uri`** key (lowercase). `QAD_APP_URI` does not exist in `backend/.env`; the value reaches config only through the `_UI_KEYS` settings.json override.

### Line-drift (correct block, off by 1–3 lines; fix if precision matters)

- `routers/sss.py` `/connection` rationale: `:7-8`, not `:8-9`.
- `generate.py` user message literal: `:111-115`, not `:110-115` (`:110` is `client, model = _client()`).
- `discover.py` broken-hop `return None` lines: `124, 128, 131, 135, 143, 147` (audit listed `127,131,135,143,147` — `:127` is the `if`, and `:124` is missing).
- `discover.py` `seen` usage: `:152` (signature), `:170`, `:183` — not `:169-170`.
- `main.py` scaffold `try` block: `:185-192` (`:183-184` are comments).
- `deploy.py` headers dict: `:65-70` (`:64` is `data=enc`).
- `health.py:136` message is `"TypeScript {version or 'unknown'} found, but QAD requires 3.5."`

### Not flagged, advisory

No credential values were leaked — `QAD_CLIENT_ID`, `QAD_PASSWORD`, `APEX_JWT_SECRET`, `APEX_ADMIN_PASSWORD` and `OPENAI_API_KEY` are all untouched by the section. The numeric `id` quoted from `sss_workspace/qad-sss.config.json` in OPEN QUESTION 3 is a QAD environment identifier from a committed non-secret file, not a client-id; consider redacting it anyway since the surrounding argument only needs the `envUrl` port mismatch (`:22010` vs `.env`'s `:81`), which I confirmed.

### Verified by re-execution (both DEFECT claims stand)

- `node_modules\.bin\tsc.cmd -v` → `'…\.bin\..\typescript\bin\tsc' is not recognized as an internal or external command`, **rc=1**.
- `check_typescript_syntax('class A { let x = ;;; }')` → `ok=True, diag=''`, with `_find_tsc()` = `D:\WEB_AUX\aux_web_version\backend\sss_workspace\node_modules\.bin\tsc.cmd`.
- Global `tsc` on PATH is **5.9.3**, not 3.5.x — worth adding, since it means the `shutil.which("tsc")` fallback in `ts_compiler.py:56` would also violate the 3.5 pin if the shim were ever removed.
### endpoints — verification verdict: `minor-issues`

**Claims the verifier could not support:**

- {"claim": "Scope audited: `backend/` in full \u2026 [CONFIRMED] There is exactly ONE HTTP transport layer for the qracore APIs \u2026 [15-row table] Every QAD endpoint AUX calls", "cited": "backend/ file list in the A4 scope line; A4.1 table (15 rows)", "whats_actually_there": "`backend/probe_parent_eh.py` is never opened or mentioned. It calls `get_qad(ep, token)` at :51 and :100 with `ep` built at :44-50 as `eventhandler?appURI={q}&viewURI={q}&eventHandlerType=BEFORE&appliesTo=WEB` \u2014 a GET on `eventhandler` with a four-param query, which is a method+query shape absent from all 15 rows. It also POSTs `eventhandler` at :91 and :126 with an UPDATE payload shape (`uri` + `concurrencyHash` echoed from the GET) that row 8 does not document, and reads `get_result[\"data\"][\"eventHandlerV2s\"][0]` at :58. It hardcodes `urn:app:com.extensions.customapp` (:24) and `urn:view:viewmeta:com.qad.erp.sales.SalesOrders` (:25). Confirmed by `grep post_qad(|get_qad(` over the repo.", "severity": "overstated"}
- {"claim": "[CONFIRMED] The frontend contains no QAD literals \u2026 the only `https://` hits in `frontend/` are npm-registry URLs in `package-lock.json`.", "cited": "A4.2, negative sweep of frontend/", "whats_actually_there": "The QAD-literal half is correct (my grep for `qad-central|oauth/token|urn:be:|qracore|urn:app:` over all of `frontend/` returns nothing). The `https://` sub-claim is false: 4 non-package-lock files match \u2014 `frontend/vite.config.ts:8` (`\"/api\": \"http://localhost:8000\"`), `frontend/src/index.css:1` (Google Fonts CDN `@import`), `frontend/public/echo-app-icon.svg:1` and `frontend/src/shared/components/ApexLogo.tsx:21` (SVG xmlns).", "severity": "wrong"}
- {"claim": "verified: `grep requests|httpx|urlopen|http` over `sss/compile.py`, `sss/generate.py`, `sss/templates.py`, `sss/readiness.py`, `core/qad_docs_loader.py`, `core/ts_compiler.py`, `core/auth.py` returns **zero** matches", "cited": "A4.2, closing [CONFIRMED] paragraph", "whats_actually_there": "That grep does not return zero. `backend/core/auth.py:26, 99, 102, 103, 110, 111` and `backend/sss/readiness.py:14, 56` all match on `HTTPException` / `HTTP_401_UNAUTHORIZED`. No `requests`, `httpx`, or `urlopen` match, so the architectural conclusion (no outbound HTTP client in those files) survives \u2014 but the grep result as stated is wrong.", "severity": "overstated"}
- {"claim": "the `entitymetadatas?viewUri=\u2026IEntityBuilderCRUD` string appears **6 times** across two files (`pipeline.py:436`, `:477`, `:517`, `:530`; `pipeline_embedded.py:168`, `:206`, `:241`, `:252` \u2014 8 occurrences counting the `entityURI` variants)", "cited": "backend/pipeline.py:436,477,517,530; backend/pipeline_embedded.py:168,206,241,252", "whats_actually_there": "All 8 line numbers are correct, but the count is not. The bare create variant occurs 4 times (pipeline.py:436, :477; pipeline_embedded.py:168, :206) and the `entityURI` variant 4 times (pipeline.py:517, :530; pipeline_embedded.py:241, :252) = 8 total. '6 times' matches neither reading and contradicts the parenthetical in the same sentence.", "severity": "wrong"}
- {"claim": "**No other retries.** No backoff, no idempotency keys, no circuit breaker anywhere.", "cited": "A4.7 Retries", "whats_actually_there": "True for every QAD call path (verified: only auth-retry is sss/deploy.py:82-87; only LLM-fix retries are pipeline.py:457-497 / pipeline_embedded.py:176-221 / pipeline.py:560-573). But `backend/sss/generate.py:86` constructs the OpenAI client with `max_retries=4`, so 'anywhere' is too absolute \u2014 it should be scoped to QAD calls.", "severity": "overstated"}

**Material the verifier found missing:**

- backend/probe_parent_eh.py — an entire QAD-calling module omitted from an audit that claims backend/ coverage. Adds a 16th endpoint shape (GET eventhandler with appURI/viewURI/eventHandlerType/appliesTo, :44-51), an undocumented POST eventhandler UPDATE payload variant carrying `uri` + `concurrencyHash` (:74-89, :111-125), two hardcoded URN literals (:24, :25) belonging in the A4.3 work-list, and a 15th get_token() call site (:36) missing from the A4.5 #1 enumeration.
- frontend/vite.config.ts:8 — the `"/api": "http://localhost:8000"` dev proxy. This is the actual mechanism behind the audit's conclusion 'the browser talks only to the AUX backend'; the conclusion is asserted without citing it.
- frontend/src/index.css:1 — external Google Fonts `@import`. The frontend's one external-host network dependency; directly contradicts the 'only npm-registry URLs' sweep and is worth noting for any locked-down deployment.
- backend/sss_template/qad-sss.config.json:3 — a third committed literal (an `id` field) in the very file Open Question 6 proposes to sanitise. The audit discusses only `envUrl` (:2) and `appURI` (:4), so a sanitisation pass driven by this audit would leave it behind.

**Corrections:**

### Corrected wording

**A4 scope line** — replace:
> Scope audited: `backend/` in full (`qad_client.py`, `core/*`, …)

with:
> Scope audited: `backend/` in full (`qad_client.py`, `core/*`, `routers/*`, `sss/*`, `builders/*`, `pipeline.py`, `pipeline_embedded.py`, `main.py`, `qad_entity_registry.py`, **`probe_parent_eh.py`**, `settings.json`, `.env`, `.env.example`, `sss_template/qad-sss.config.json`) …

**A4.1** — the table is 15 rows for the *app*; add a 16th row (or an explicit out-of-scope note):

| # | Method | Path | Query params | Payload | Response read | Used by | Cite |
|---|---|---|---|---|---|---|---|
| 16 | GET | `{BASE}/qad-central/api/qracore/eventhandler` | `appURI={quote}`, `viewURI={quote}`, `eventHandlerType=BEFORE`, `appliesTo=WEB` | none | `data.eventHandlerV2s[0]` → `uri`, `concurrencyHash`, `isActive`, `typeScriptCode`, `javaScriptCode` | **Not app code** — standalone probe script, run by hand | `backend/probe_parent_eh.py:44-51`, re-GET `:100`, read `:58` |

And qualify row 8:
> Row 8 documents the **create** payload only. `backend/probe_parent_eh.py:74-89` and `:111-125` POST the same endpoint with an **update** shape that additionally carries `uri` and `concurrencyHash` (echoed from the GET). Which shape QAD requires for an update is unverified — the probe exists to find out.

**A4.2** — replace:
> the only `https://` hits in `frontend/` are npm-registry URLs in `package-lock.json`

with:
> Verified by grep over all of `frontend/`: no `qad-central`, `qracore`, `oauth/token`, `urn:be:` or `urn:app:` literal anywhere. Non-QAD external URLs do exist — the dev proxy `frontend/vite.config.ts:8` (`"/api": "http://localhost:8000"`, which is *why* the browser only ever talks to the AUX backend), a Google Fonts `@import` at `frontend/src/index.css:1`, and two SVG `xmlns` namespaces.

**A4.2 closing paragraph** — replace "returns **zero** matches" with:
> `grep requests|httpx|urlopen` over those files returns **zero** matches. (A broader `http` grep matches only FastAPI `HTTPException` / `Header` symbols in `core/auth.py` and `sss/readiness.py` — no outbound client.)

**A4.4** — replace "appears **6 times**" with:
> appears **8 times** across two files — 4 as the bare create variant (`pipeline.py:436`, `:477`; `pipeline_embedded.py:168`, `:206`) and 4 as the `entityURI` variant (`pipeline.py:517`, `:530`; `pipeline_embedded.py:241`, `:252`).

**A4.5 #1** — the `get_token()` call-site list should read:
> …`backend/core/lookup_generator.py:279`, and `backend/probe_parent_eh.py:36` (standalone probe, not app code) — 15 sites total.

**A4.7 Retries** — replace the last bullet with:
> **No other retries on any QAD call.** No backoff, no idempotency keys, no circuit breaker. (The only retry elsewhere in the repo is `max_retries=4` on the OpenAI client at `backend/sss/generate.py:86` — unrelated to QAD.)

### Optional precision notes (not errors)

- A4.7 "`_qad_error_messages()` … applied at exactly **one** site (`pipeline.py:481`)": there are two call sites — `:481` (user-facing text) and `:230` inside `_is_duplicate_entity_error`. Suggest "exactly one *user-facing* site".
- A4 opening: "Two calls bypass it" is correct as scoped to qracore, but `core/qad_session.py:54` and `:76` are also direct `httpx` calls outside `qad_client`. Worth saying "two qracore calls bypass it; two further direct HTTP calls live in `core/qad_session.py` (oauth + login, rows 2-3)" so a transport registry doesn't miss them.
- No `.env` secret values were leaked — values are correctly marked `<redacted>` and `public_status()` is accurately described. Minor hygiene point: Open Question 6 reproduces the committed `envUrl` host:port verbatim; `backend/sss_template/qad-sss.config.json:2` alone conveys the finding. The same file's `id` field (`:3`) is a third committed literal the sanitisation proposal should cover.

### Verified clean (spot-checked at the cited line, all correct)

`qad_client.py:11-17, 20-39, 42-53, 57, 65, 72-82`; `core/qad_session.py:4-8, 28-29, 43-67, 70-93`; `pipeline.py:42, 74, 142, 148, 226-231, 434-441, 447-455, 457-497, 513-539, 596-605, 684-693, 708-720, 737-748, 770, 787`; `pipeline_embedded.py:30, 35-41, 104-105, 166-221, 238-262, 273-292, 298-317, 327-331`; all six `builders/*` payload and MODULE cites; `core/lookup_generator.py:70, 241-244, 266, 276-282`; `core/health.py:162-177`; `sss/deploy.py:36-46, 49-72, 82-92, 108-114`; `sss/appconfig.py:15-17, 25-28`; `core/config.py:34, 50, 106-121, 164-182, 185-197`; `core/sss_scaffold.py:34-38, 96-110`; `routers/sss.py:35, 99-119, 123-135`; `routers/client_extensions.py:156`; `main.py:68, 146, 149`; `agents/prompts.py:354-366`; `settings.json` full contents; `.env` key set (QAD_APP_URI and OPENAI_MODEL confirmed absent); `.env.example:6-8, 20, 32, 37`; dead-code greps for `get_bearer_token`, `_safe_body`, `envUrl`; absence of a duplicate-name short-circuit in `pipeline_embedded.py`.
### auth — verification verdict: `minor-issues`

**Claims the verifier could not support:**

- {"claim": "\"the pipeline calls it [get_token()] seven separate times per run\" / blocker #5 \"Seven independent get_token() calls per run\"", "cited": "backend/pipeline.py:434, 475, 514, 596, 684, 708, 737 [CONFIRMED]", "whats_actually_there": "Those are seven call SITES, not seven calls per run. :475 is inside the step-4 auto-fix retry branch (only reached when the first BC create fails AND the LLM returns status=='fixed', pipeline.py:443-475); :514 is inside `if field_list_map:` (pipeline.py:510), i.e. only when the spec has dropdown fields. A clean run with no dropdowns makes FIVE calls (434, 596, 684, 708, 737). The audit's own step table labels 475 \"retry after auto-fix\" and 514 \"dropdown wiring\", contradicting the flat \"per run\" wording.", "severity": "overstated"}
- {"claim": "\"`/qad-central/` is hardcoded in four places.\"", "cited": "backend/core/qad_session.py:28, :29, backend/qad_client.py:44, 57, 65, backend/sss/deploy.py:43 [CONFIRMED]", "whats_actually_there": "The sentence says four but then enumerates six sites. A repo-wide grep finds six code sites (qad_client.py:44, 57, 65; qad_session.py:28, 29; sss/deploy.py:42) plus a seventh env-specific occurrence in backend/sss_template/qad-sss.config.json:2 (`envUrl` carrying host + /qad-central/ context), which is copied verbatim into each scaffolded workspace by core/sss_scaffold.py:34.", "severity": "wrong"}
- {"claim": "The `/qad-central/` literal in the SSS upload URL is at backend/sss/deploy.py:43", "cited": "backend/sss/deploy.py:43", "whats_actually_there": "Line 42 is `f\"{base}/qad-central/api/qracore/sss\"`; line 43 is `f\"?appURI={quote(app_uri, safe='')}\"`. Off by one.", "severity": "bad-citation"}
- {"claim": "Blocker #4: \"A per-run target choice needs new request fields and new plumbing through `run_pipeline`'s signature (`backend/pipeline.py:161-165` call site) [CONFIRMED]\"", "cited": "backend/pipeline.py:161-165", "whats_actually_there": "pipeline.py:161-165 is the body of the `_evt()` SSE-event helper. `run_pipeline` is DEFINED at backend/pipeline.py:381-385 (`user_message`, `parsed_requirements`, `lookup_candidates`); the 161-165 call site is in backend/routers/client_extensions.py (where \u00a76 cites it correctly). Wrong file for this citation.", "severity": "bad-citation"}
- {"claim": "\"QAD Bearer: no retry. Every `get_token()` call site is a fresh full login, and a QAD 401 becomes an `{\"error\": \"QAD HTTP 401\", \"raw\": ...}` envelope (`backend/qad_client.py:26-32`)\"", "cited": "backend/qad_client.py:26-32, :75-76", "whats_actually_there": "`_handle()` (lines 20-39) is only called by `post_qad`/`get_qad` (:61, :69). `get_token()` calls `resp.raise_for_status()` directly (qad_client.py:52), so a 401 from the TOKEN endpoint raises `httpx.HTTPStatusError` and never produces the envelope \u2014 it is caught by each step's try/except and surfaced as e.g. \"QAD connection failed: ...\" (pipeline.py:439-441). The envelope+`is_qad_success` path applies only to 401s on the qracore API calls. Conclusion (no re-auth, pipeline aborts) is unaffected.", "severity": "overstated"}
- {"claim": "\"`save_ui_settings` persists `_UI_KEYS` unconditionally\"", "cited": "backend/core/config.py:185-197", "whats_actually_there": "Lines 192-194: `for k in _UI_KEYS: if k in updates and updates[k] is not None: current[k] = updates[k]` \u2014 only keys present and non-None in the payload are written. Moreover `POST /api/settings` cannot supply `qad_base_url` at all: `UiSettingsUpdate` (routers/settings.py:23-28) exposes only qad_app_uri/qad_app_dir/openai_model/auto_deploy and is dumped with exclude_none. The \"second silent source of truth\" risk is real only for a hand-edited settings.json, not via the UI.", "severity": "overstated"}
- {"claim": "\"UI login form email+password | typed by user | `frontend/src/features/auth/LoginPage.tsx:147,159`\"", "cited": "frontend/src/features/auth/LoginPage.tsx:147,159", "whats_actually_there": "Both cited lines are `disabled={submitting}`. The email/password bindings are at :145 (`value={email}`) and :157 (`value={password}`); the inputs span :142-149 and :154-160.", "severity": "bad-citation"}

**Material the verifier found missing:**

- backend/sss_template/qad-sss.config.json:2-4 — hardcodes an env-specific `envUrl` (full host + /qad-central/ context) and `appURI`; backend/core/sss_scaffold.py:34 copies this file verbatim into every scaffolded workspace. This is a second, file-based single-env binding that blockers #3 and #8 both miss: a second QAD target needs a different envUrl in each scaffolded workspace, not just a config accessor change.
- CORS is never analysed. §4 lists ALLOWED_ORIGINS as an .env key but §5's "anyone who can reach the port" risk statement omits backend/main.py:66-74 (`CORSMiddleware`, allow_origins from ALLOWED_ORIGINS, default http://localhost:5173) — the only origin-level control on the otherwise unauthenticated API, and directly relevant if the Adaptive env is production. (It gates browsers only, not curl, so the verdict stands — but it belongs in the analysis.)
- Rate limiting as the only other pre-auth control is under-reported: §5 cites only the login limiter. backend/core/rate_limit.py:21 sets a 30/min-per-IP default for every route; /api/run is 5/min (backend/routers/client_extensions.py:118) and /api/sss/generate is 10/min (backend/routers/sss.py:84).
- backend/routers/sss.py:38 `GATED = [Depends(ensure_ready)]`, applied at :55, :73, :83, :99 — /api/sss/generate and /api/sss/deploy DO carry a dependency (SSS folder/typedef readiness, 503 otherwise). It is not authentication, so §5's conclusion holds, but "a bare curl to /api/sss/deploy writes to QAD" is true only once the SSS workspace is scaffolded.
- backend/probe_parent_eh.py:22, 36 is a third `get_token()` consumer (dev probe script) alongside pipeline.py and pipeline_embedded.py; blocker #2's "every auth function reads the global" sweep should list it so a multi-env refactor doesn't leave it behind.

**Corrections:**

## Corrections

**§3 / blocker #5 — get_token() call count**
> ~~"the pipeline calls it **seven separate times per run**"~~
> "the pipeline has **seven `get_token()` call sites**; a clean run makes **five** (`pipeline.py:434, 596, 684, 708, 737`). `:475` fires only on the step-4 auto-fix retry (guarded by `is_qad_success` failure at `:443`), `:514` only when the spec has dropdown fields (`if field_list_map:`, `:510`)."

**Blocker #3 — hardcoded context root**
> ~~"`/qad-central/` is hardcoded in **four** places."~~
> "`/qad-central/` is hardcoded in **six code sites** — `qad_client.py:44, 57, 65`; `core/qad_session.py:28, 29`; `sss/deploy.py:42` — **plus `backend/sss_template/qad-sss.config.json:2`**, whose `envUrl` embeds host *and* context root and is copied verbatim into each workspace by `core/sss_scaffold.py:34`."

(also: `sss/deploy.py:43` → **`:42`**)

**Blocker #4 — run_pipeline citation**
> ~~"new plumbing through `run_pipeline`'s signature (`backend/pipeline.py:161-165` call site)"~~
> "new plumbing through `run_pipeline`'s signature (**defined `backend/pipeline.py:381-385`**; called at **`backend/routers/client_extensions.py:161-165`**)."

**§2 — QAD Bearer 401 behaviour**
> ~~"a QAD 401 becomes an `{"error": "QAD HTTP 401", ...}` envelope (`backend/qad_client.py:26-32`)"~~
> "`get_token()` does **not** use `_handle()` — it calls `resp.raise_for_status()` directly (`qad_client.py:52`), so a 401 from the *token* endpoint raises `httpx.HTTPStatusError` and is surfaced by each step's `except` as e.g. `QAD connection failed: …` (`pipeline.py:439-441`). The `{"error": "QAD HTTP 401"}` envelope (`qad_client.py:26-32`) applies only to `post_qad`/`get_qad`, where `is_qad_success` (`:75-76`) reports it as a plain failure. Either way: no re-auth, the pipeline aborts."

**Blocker #7 — save_ui_settings**
> ~~"`save_ui_settings` persists `_UI_KEYS` unconditionally (`config.py:185-197`)"~~
> "`save_ui_settings` persists only the `_UI_KEYS` **present and non-None in the payload** (`config.py:192-194`), and `POST /api/settings` cannot send `qad_base_url` at all (`routers/settings.py:23-28`). The second-source-of-truth risk is via a **hand-edited `settings.json`**, not the UI."

**§4 table — login form citation**
> `LoginPage.tsx:147,159` → **`:145` (`value={email}`) and `:157` (`value={password}`)** (147/159 are both `disabled={submitting}`).

**Minor citation drift (text is correct, lines off by one)**
- `core/qad_session.py:11-12` "Nothing is persisted; each token/cookie is fetched fresh" → **`:10-11`**
- `shared/api.ts:63` (settings POST) → the `fetch` is at **`:62`**
- `authStore.tsx:52` (storage exceptions swallowed) → the `catch` block is **`:51-53`**

## Verified as stated (spot-checked, no change needed)
`qad_client.py:42-53` query-string interpolation and `KeyError` subscript; `qad_session.py:43-58` params-dict implementation with **zero callers** (repo-wide grep returns only `:6` docstring and `:43` def); `LOGIN_PATH`/`OAUTH_PATH` at `:28-29`; the single 401 retry at `sss/deploy.py:82-87` (case-insensitive grep for `401|refresh|expire|retry` across `backend/**/*.py` finds no other auth retry); no `/refresh` route; `database.py` exactly two tables (`:14`, `:34`), no users/user_id; `get_current_user` used by exactly one route (`routers/auth.py:69`); JWT claims exactly `sub`/`iat`/`exp` (`core/auth.py:69-73`); `localStorage["apex_token"]` and **`features/auth/api.ts:53` is the only `Authorization` header in the whole frontend**; no `env=`/environment-id parameter anywhere in `backend/`; `.env` key list exact (11 keys) and `settings.json` holds only `qad_app_dir`/`qad_app_uri`/`openai_model`, so the legacy fallback at `config.py:113-121` is indeed inert; `lookup_generator` live POST unreachable (`pipeline.py:74` passes `dry_run=True`); `PyJWT==2.8.0` at `requirements.txt:11`. **No secret values were leaked** — key names only, values redacted throughout.
### persistence — verification verdict: `minor-issues`

**Claims the verifier could not support:**

- {"claim": "The embedded pipeline is the same: `state` at `backend/pipeline_embedded.py:64`, summary at `:362`.", "cited": "backend/pipeline_embedded.py:362", "whats_actually_there": "The summary literal is assigned at :345 (`summary = {`); :362 is the `\"view_label\": state.get(...)` entry inside it. (`state` at :64 and `run_embedded_pipeline` at :62 are exact.)", "severity": "bad-citation"}
- {"claim": "Grep for `approv|pause|resume|awaiting|checkpoint` across backend/**/*.py ... the only hits are `isAllowApproval` in embedded_builder.py:189, the `approval` dropdown example in prompts.py:76, and doc/comment uses of 'gate'.", "cited": "backend/builders/embedded_builder.py:189, backend/agents/prompts.py:76", "whats_actually_there": "Those two hits are exact, but the grep also returns backend/routers/sss.py:4 ('Gating (per approved route map)'), :21 ('the compiled TS a user approves for deploy'), :101 ('Write the approved .ts...'), and backend/sss/discover.py:30 ('Approved scope'). All are SSS comments, so the conclusion (no run-gating code in the CE flow) still holds \u2014 the enumeration is just incomplete.", "severity": "overstated"}
- {"claim": "[CONFIRMED by absence] there is no in-flight-run registry of any kind: grep for `app.state` across the backend yields exactly one hit, `app.state.limiter = limiter` (backend/main.py:43).", "cited": "backend/main.py:43", "whats_actually_there": "Two hits: backend/main.py:43 (code) and backend/core/rate_limit.py:5 (docstring, 'Limiter to be attached to app.state (in main.py)'). The underlying finding is independently confirmed and stronger than stated: grep for `asyncio.Queue|asyncio.create_task|ensure_future|BackgroundTask|redis` over backend/**/*.py returns ZERO hits.", "severity": "overstated"}
- {"claim": "`journal_mode = delete`, `busy_timeout = 5000`, `foreign_keys = 0`, `synchronous = 2` \u2014 none of these are set anywhere in code (grep for journal_mode|WAL|busy_timeout|isolation_level over backend/**/*.py returns only httpx/subprocess timeouts), so all four are SQLite defaults.", "cited": "backend/history.db PRAGMAs; grep over backend/**/*.py", "whats_actually_there": "The four PRAGMA values are correct (I re-read them read-only). But (a) `busy_timeout = 5000` is NOT a SQLite default (SQLite's is 0) \u2014 it is the Python `sqlite3` driver default (`connect(timeout=5.0)`) that aiosqlite inherits; (b) only `journal_mode` and `user_version` are stored in the file \u2014 `foreign_keys=0` and `synchronous=2` are per-connection defaults, not file state; (c) that exact grep returns no httpx/subprocess timeouts at all \u2014 its only hits are substring false positives ('swallowed', 'Walk'/'walk'). The claim 'not set anywhere in code' is nonetheless CONFIRMED.", "severity": "overstated"}
- {"claim": "the pipeline makes irreversible QAD POSTs at step 3 (`pipeline.py:435`), 3.5 (`:529`), 7 (`:597`), 11 (`:685`), 13 (`:709`), and 14 (`:739`, `:741`). ... Without a committed-side-effects ledger, any resume double-POSTs to QAD.", "cited": "backend/pipeline.py:435, 529, 597, 685, 709, 739, 741", "whats_actually_there": "All seven cited lines are exact, but the list is incomplete in a load-bearing way: `backend/pipeline.py:476` is a further `post_qad` BC create (the post-auto-fix retry, step 4), and `backend/pipeline_embedded.py` has seven more POST sites (:167, :205, :251, :277, :299, :309, :328) that the ledger design never covers \u2014 despite 3 of the 19 stored runs being mode='embedded'.", "severity": "overstated"}
- {"claim": "`backend/sss_workspace/` \u2014 SSS only, and only via `POST /api/sss/deploy`: `backend/sss/compile.py:43-44` and `:51`.", "cited": "backend/sss/compile.py:43-44, :51", "whats_actually_there": "Those write sites are exact, but 'only via POST /api/sss/deploy' is false: the workspace tree (lib/, src/, dist/, package.json, tsconfig.json, qad-sss.config.json, bundled typescript + tsc shims) is created and populated at STARTUP by `backend/core/sss_scaffold.py:29-67`, called from `backend/main.py:186-190` when QAD_APP_DIR is set. Deploy only adds the .ts and dist output. Still not run state.", "severity": "overstated"}
- {"claim": "mirror it in `pipeline_embedded.py` (7 steps, `BASE_TOTAL_STEPS = 7` at `:30`)", "cited": "backend/pipeline_embedded.py:30", "whats_actually_there": ":30 is exact, but the embedded pipeline is 7 OR 8 steps: `total_steps = 8 if wants_separate_view else BASE_TOTAL_STEPS` (:105), and the comment at :29 says 'may grow to 8 if wants_separate_view is True'. Relevant because a step-keyed `run_steps` PK assumes a fixed step vocabulary.", "severity": "overstated"}
- {"claim": "Grep for localStorage|sessionStorage|indexedDB|persist|zustand across frontend/src returns only the three keys above plus one prose comment.", "cited": "frontend/src (grep)", "whats_actually_there": "Ten hits: the three key sites (App.tsx:20, :31, :52; authStore.tsx:41, :49-50) plus comments at authStore.tsx:3, :6, :33, auth/api.ts:46, and RegisteredBCsPage.tsx:30. The substantive claim \u2014 exactly three localStorage keys, no sessionStorage/indexedDB/zustand/persist middleware \u2014 is CONFIRMED, and package.json deps are exactly react/react-dom/react-router-dom as stated.", "severity": "overstated"}
- {"claim": "`backend/logs/app.log` (195,232 bytes; RotatingFileHandler(maxBytes=5_000_000, backupCount=5) at backend/core/logging_setup.py:44)", "cited": "backend/logs/app.log size", "whats_actually_there": "The handler citation at :44 is exact and the log does contain the STEP5/STEP6 truncated outputs as claimed. The size is currently 200,294 bytes, not 195,232 (live-growing file, mtime Aug 6 12:36).", "severity": "overstated"}

**Material the verifier found missing:**

- Embedded-pipeline QAD write sites are never enumerated: `backend/pipeline_embedded.py:167, 205, 251, 277, 299, 309, 328` are all `post_qad` calls. Since A6.6(a)(4) calls the side-effects ledger 'non-negotiable', omitting the entire embedded path (3 of 19 stored runs) is a real gap.
- `backend/pipeline.py:476` — the second BC-create POST after the step-4 auto-fix — is missing from the irreversible-write inventory.
- `backend/core/sss_scaffold.py` (called from `backend/main.py:186-190`) is an unlisted on-disk write path in A6.5; it mkdirs and populates the SSS workspace on every startup.
- Stronger evidence was available for OPEN QUESTION 1 without any live QAD run: grep for `is_disconnected|CancelledError|BaseException|finally:` over `backend/**/*.py` returns ZERO hits. Nothing anywhere in the backend can observe or handle a client disconnect, which raises 'an aborted run gets no row' from [INFERRED] to a code-level certainty (only the arrival timing of the cancellation is unverified).
- `backend/pipeline_embedded.py:105` makes the embedded step count variable (7 or 8) — material to a step-keyed `run_steps(run_id, step)` schema.
- Not noted: the CE subtree deliberately survives a feature switch — `frontend/src/main.tsx:10-12` ('the app never re-mounts on route changes ... in-progress runs ... stays intact') and the `ClientExtPanel.tsx:35-39` header comment ('This whole subtree stays mounted while the SSS feature is active, so an in-progress run survives a feature switch'). Useful boundary for A6.4 group A: feature switch survives, refresh does not.

**Corrections:**

## Verdict

Substantively accurate. Every architecturally load-bearing claim I re-checked held **exactly**, including: no approval gate anywhere in the CE flow; **no `UPDATE` against `runs` in the backend** (only `INSERT`/`DELETE`/`SELECT`; the `ON CONFLICT DO UPDATE` is on `parent_entities`); one row written after the generator drains; `run_id` emitted last (`client_extensions.py:203`); `RunRequest.run_id` never read; the live `runs` DDL with `mode` appended past the closing paren; `user_version=1`, 19 rows, status/mode/NULL-summary distributions, `summary_json` top-level keys (902/901 chars), the backup DB (9 rows, `user_version=0`, `freelist_count=11`, one extra id `22edfab0…`); the full route inventory; the three localStorage keys; no `/run/:id`; and **all 11 `state[...]` line numbers and all `post_qad` line numbers in `pipeline.py`**. No secret values were leaked.

Fixes below are precision-level except (5), which is materially incomplete.

### 1. `pipeline_embedded.py` summary citation
> The embedded pipeline is the same: `state` at `backend/pipeline_embedded.py:64`, summary at ~~`:362`~~ **`:345`**.

### 2. A6.0 grep enumeration
> …the only hits are `"isAllowApproval": False` (`embedded_builder.py:189`), an `approval` dropdown example (`prompts.py:76`), **and four SSS doc/comment hits (`routers/sss.py:4, :21, :101`; `sss/discover.py:30`)**. None is run-gating code.

### 3. A6.4 / A6 registry absence
> grep for `app.state` yields ~~exactly one hit~~ **two hits — `main.py:43` (code) and `core/rate_limit.py:5` (docstring)**. Stronger corroboration: grep for `asyncio.Queue|asyncio.create_task|ensure_future|BackgroundTask|redis` over `backend/**/*.py` returns **zero** hits.

### 4. A6.1 PRAGMA framing
> `journal_mode = delete`, `busy_timeout = 5000`, `foreign_keys = 0`, `synchronous = 2` — none is set anywhere in code. **`journal_mode` (and `user_version`) are file state; `foreign_keys` and `synchronous` are per-connection defaults; `busy_timeout = 5000` is the Python `sqlite3` driver default (`connect(timeout=5.0)`), which aiosqlite inherits — SQLite's own default is 0.** (Drop the "returns only httpx/subprocess timeouts" aside — that grep's only hits are the substrings "swallowed" and "walk".)

### 5. A6.6(a)(4) / (b)(6) — write-site inventory (fix before using this list)
> …irreversible QAD POSTs at step 3 (`pipeline.py:435`), step 4 auto-fix retry (**`:476`**), 3.5 dropdown wiring (`:529`), 7 (`:597`), 11 (`:685`), 13 (`:709`), 14 (`:739`, `:741`) — **seven sites in the standard pipeline — plus seven more in the embedded pipeline (`pipeline_embedded.py:167, 205, 251, 277, 299, 309, 328`), which 3 of the 19 stored runs used.**

### 6. A6.5 `sss_workspace`
> `backend/sss_workspace/` — SSS only. **The workspace tree is scaffolded at startup by `core/sss_scaffold.py:29-67` (`main.py:186-190`);** `POST /api/sss/deploy` only adds the `.ts` (`sss/compile.py:43-44`) and `dist/` output (`:51`).

### 7. A6.6(c)(4) embedded step count
> …mirror it in `pipeline_embedded.py` (**7 or 8 steps — `BASE_TOTAL_STEPS = 7` at `:30`, `total_steps = 8 if wants_separate_view` at `:105`**).

### 8. Nits
- `app.log` is **200,294** bytes, not 195,232 (live file).
- A6.5 storage grep: say "returns the three keys plus six comment/prose mentions", not "one prose comment".
- OPEN QUESTION 2: the heading at `PROGRESS.md:113` literally reads "(🟡 planning)"; "COMPLETE & APPROVED" is the status line at `:140`. The cited range is right; only the quoted heading is a merge of the two.
- OPEN QUESTION 1 can be upgraded from [INFERRED] toward [CONFIRMED] without the live QAD test: grep for `is_disconnected|CancelledError|BaseException|finally:` over `backend/**/*.py` returns **zero** hits, so no code path anywhere can intercept the cancellation.
### readback — verification verdict: `major-issues`

**Claims the verifier could not support:**

- {"claim": "\"grep for `get_qad` across the backend yields exactly **two** call sites. There are no others.\" (A7.2)", "cited": "backend/pipeline.py:516-519, backend/pipeline_embedded.py:240-243", "whats_actually_there": "There are FOUR `get_qad` call sites. `grep -rn \"get_qad\" backend --include=*.py` returns pipeline.py:516, pipeline_embedded.py:240, and backend/probe_parent_eh.py:51 and :100. The A7.2 table titled \"every READ-from-QAD call\" is therefore incomplete.", "severity": "wrong"}
- {"claim": "\"**No GET is ever issued against the `eventhandler` endpoint.** `eventhandler` appears exactly once as a network target in the whole backend \u2014 as a POST at `backend/pipeline.py:685` \u2026 There is no `get_qad(\"eventhandler\"...)` anywhere.\" (A7.3 #1)", "cited": "backend/pipeline.py:685", "whats_actually_there": "backend/probe_parent_eh.py:44-51 builds `eventhandler?appURI=\u2026&viewURI=\u2026&eventHandlerType=BEFORE&appliesTo=WEB` into a variable `ep` and calls `get_result = await get_qad(ep, token)`; a second GET at :100. It also POSTs `eventhandler` at :91 and :126. The endpoint string is assembled in a variable, which is why a literal grep for `get_qad(\"eventhandler\"` missed it. `eventhandler` is a network target at four sites, not one.", "severity": "wrong"}
- {"claim": "\"**NO. AUX never reads existing event handler code back from QAD.** Not once, on any path.\" (A7.3 verdict)", "cited": "A7.3", "whats_actually_there": "backend/probe_parent_eh.py does exactly this: its module docstring (:1-8) states it \"confirms whether we can: 1. GET an existing event handler 2. POST it back (with concurrencyHash) as an update\" against \"the SalesOrders handler we already know exists\"; :58-63 unwraps `get_result[\"data\"][\"eventHandlerV2s\"][0]` and prints `uri`, `concurrencyHash`, `isActive`, `len(typeScriptCode)`; :84-86 re-sends the fetched `typeScriptCode`/`javaScriptCode`/`mappingCode`. The verdict is defensible only when scoped to the two SSE pipelines, not \"on any path\". The auditor cannot invoke \"untracked file, out of scope\": backend/core/lookup_generator.py is equally untracked and is cited as write-call #14.", "severity": "wrong"}
- {"claim": "\"What is genuinely absent: \u2026 Any GET against the `eventhandler` endpoint, and therefore any way to retrieve an existing `typeScriptCode` / `javaScriptCode` / `mappingCode` body.\" (A7.4)", "cited": "A7.4 bullet 1", "whats_actually_there": "backend/probe_parent_eh.py:51 performs that GET and :84-86 reads precisely `typeScriptCode`, `javaScriptCode`, and `handler.get(\"mappingCode\", \"\")` out of the response. Not absent \u2014 already prototyped.", "severity": "wrong"}
- {"claim": "\"Does the `eventhandler` endpoint support GET at all, and with what query params? \u2026 This is unverified \u2014 **nothing in the repo documents a GET on `eventhandler`**.\" (OQ2)", "cited": "backend/builders/event_handler_builder.py:28-29", "whats_actually_there": "The repo contains a runnable probe that documents the exact params (`appURI`, `viewURI`, `eventHandlerType`, `appliesTo` \u2014 note camelCase `viewURI`, not the `?viewUri=` convention the auditor extrapolated) and the expected response shape `data.eventHandlerV2s[0]` with `uri`/`concurrencyHash`/`isActive`/`typeScriptCode` (backend/probe_parent_eh.py:44-63). The auditor's guessed answer happens to be close, but the premise \"nothing in the repo documents\" is false.", "severity": "wrong"}
- {"claim": "\"Was read-back ever attempted and removed, or never built? \u2014 *Never built.* \u2026 `PROGRESS.md` (75 KB, not read in full for this section) would settle it definitively.\" (OQ3)", "cited": "backend/pipeline.py:503-508; PROGRESS.md", "whats_actually_there": "Read-back against `eventhandler` was built, as a standalone probe (backend/probe_parent_eh.py, mtime Aug 6 14:28 \u2014 the newest file in backend/). Separately, PROGRESS.md would NOT settle it: grep over PROGRESS.md for `probe_parent_eh|GET.*eventhandler|read.back|read-back` returns zero hits, and the file predates the probe (mtime Jul 28 15:30).", "severity": "wrong"}
- {"claim": "\"The backend has exactly **four** modules that open a socket to QAD. Grep for `httpx|requests\\.|urllib|aiohttp` across `backend/**/*.py` returns hits only in `backend/qad_client.py`, `backend/core/qad_session.py`, `backend/core/health.py:169-170`, and `backend/sss/deploy.py`.\" (A7.1)", "cited": "backend/**/*.py grep", "whats_actually_there": "That grep actually also hits backend/main.py:51, backend/pipeline.py:3 and :513, backend/pipeline_embedded.py:3 and :238, and backend/probe_parent_eh.py:16 and :31 \u2014 eight files, not four. More importantly the inference is invalid: a module needs no HTTP-library import to open a socket to QAD, it only needs to import qad_client. `grep -rn qad_client backend --include=*.py` shows pipeline.py:19, pipeline_embedded.py:18, core/lookup_generator.py:276 AND probe_parent_eh.py:22. This methodology error is the root cause of the missed probe.", "severity": "wrong"}
- {"claim": "\"`package.json` (version string) | Local | health tile | `backend/core/health.py:130`\" (A7.5 table)", "cited": "backend/core/health.py:130", "whats_actually_there": "The citation is right but the description is not: health.py:122 defines `pkg = Path(app_dir) / \"node_modules\" / \"typescript\" / \"package.json\"`, so :130 reads the TypeScript compiler's package.json inside the configured SSS app folder (to assert tsc 3.5), not the AUX application's own package.json.", "severity": "overstated"}

**Material the verifier found missing:**

- backend/probe_parent_eh.py in its entirety — the single most material file for the question 'does AUX ever read artifacts back from QAD'. It GETs an existing, human-authored QAD handler (SalesOrders), reads its TS/JS code, and POSTs it back as an update. It is absent from A7.1's HTTP inventory, from A7.2's 'definitive table of every READ-from-QAD call', from the A7.3 verdict, from A7.4's absence list, and from OQ2/OQ3.
- The proven GET→mutate→POST update contract for event handlers. A7.4 offers the entitymetadatas dropdown cycle as the 'nearest existing capability' and calls it 'the exact shape a read-existing-handler-amend-re-post flow would take' — but that exact flow is already written for eventhandler at probe_parent_eh.py:74-108, including the two payload shapes being A/B tested (with vs. without `uri`, :74-89 vs :111-125) and the post-update re-GET that verifies the hash rotated (:100-107).
- `concurrencyHash` as the optimistic-locking token an update POST must echo back. The audit lists it only as an incidental key in the GET response shape and as a field patch_dropdown_fields leaves alone (bc_builder.py:102); it never identifies it as the mechanism that makes read-modify-write possible, which probe_parent_eh.py:83 and :103-107 make explicit.
- The parent-view targeting constant `urn:view:viewmeta:com.qad.erp.sales.SalesOrders` (probe_parent_eh.py:25) — evidence that a *standard QAD parent* view URI, not just the `com.extensions.customapp.{BcPascal}` URI the audit cites from event_handler_builder.py:8, is being exercised against the eventhandler endpoint.

**Corrections:**

## Required corrections

**Root cause:** the outbound-HTTP inventory was built by grepping for HTTP *library* imports. `backend/probe_parent_eh.py` imports no HTTP library — it imports `qad_client` (`:22`) — so it fell out of the inventory, and every downstream absence claim inherited the gap. The completeness sweep should have been `grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py`.

### A7.1 — replace the opening claim

> [CONFIRMED] Four modules construct HTTP clients directly (`backend/qad_client.py`, `backend/core/qad_session.py`, `backend/core/health.py:169-170`, `backend/sss/deploy.py`). Four *further* modules reach QAD through `qad_client`: `backend/pipeline.py:19`, `backend/pipeline_embedded.py:18`, `backend/core/lookup_generator.py:276`, and `backend/probe_parent_eh.py:22`.

Drop "Grep … returns hits only in" — that grep also hits `main.py:51`, `pipeline.py:3,513`, `pipeline_embedded.py:3,238`, `probe_parent_eh.py:16,31`.

### A7.2 — the table is missing two rows

> [CONFIRMED] `get_qad` has **four** call sites: `pipeline.py:516`, `pipeline_embedded.py:240`, `probe_parent_eh.py:51`, `probe_parent_eh.py:100`.

Add:

| Method | Full path | What it returns | Who consumes it | file:line |
|---|---|---|---|---|
| GET | `/qad-central/api/qracore/eventhandler?appURI={q com.extensions.customapp}&viewURI={q com.qad.erp.sales.SalesOrders}&eventHandlerType=BEFORE&appliesTo=WEB` | `{"data": {"eventHandlerV2s": [{uri, concurrencyHash, isActive, typeScriptCode, javaScriptCode, mappingCode, disallowedActions}]}}` — an **existing, QAD-authored** handler | `probe_parent_eh.py:58-63` (inspect), `:84-86` (echo into an update POST at `:91`) | `backend/probe_parent_eh.py:44-51` |
| GET | same endpoint, re-issued after the update | same | hash-rotation check, `:102-107` | `backend/probe_parent_eh.py:100` |

### A7.3 — rewrite the verdict

> **QUALIFIED NO — scoped to the pipelines.** Neither `run_pipeline` nor `run_embedded_pipeline` ever reads an event handler back; on those paths the handler is authored from scratch each run and POSTed as a full replace (`event_handler_builder.py:6-48`, `pipeline.py:685`).
> **However, the backend does contain working handler read-back:** `backend/probe_parent_eh.py` GETs an existing standard-BC handler, reads its `typeScriptCode`/`javaScriptCode`/`concurrencyHash`, and POSTs it back as a no-op update. It is a standalone script (`if __name__ == "__main__"`, `:133`), untracked in git, not imported by any router or pipeline — so it is not part of any user-facing flow, but the capability is demonstrably present and exercised.

Points 2–7 of A7.3 stand as written (verified: `event_handler_builder.py` takes no prior-state parameter; `ts_code`/`js_code` are LLM output from `pipeline.py:648` and `:669-673`; `viewMetadataV2`/`viewResourceMetadatas`/`berelation` are POST-only across the backend; `embedded_builder.py:213` hardcodes `"eventHandlerInfos": []`; `_is_duplicate_entity_error` at `pipeline.py:226-231` is `return "already exist" in blob`; `qad_entity_registry.py` makes no network call). Point 1 must be struck.

### A7.4 — move one bullet from "absent" to "present"

Delete: *"Any GET against the `eventhandler` endpoint, and therefore any way to retrieve an existing `typeScriptCode` / `javaScriptCode` / `mappingCode` body."*

Replace with a fourth "nearest existing capability":

> 4. [CONFIRMED] **A prototyped handler read-modify-write.** `backend/probe_parent_eh.py` already performs GET → mutate → POST against `eventhandler`, including the `uri` + `concurrencyHash` echo QAD requires for an update (`:77`, `:83`) and a post-update re-GET proving the hash rotates (`:100-107`). It A/B tests two payload shapes (with `uri`, `:74-89`; without, `:111-125`), i.e. the update contract was still being pinned down when the probe was written.

The remaining absence bullets (no read of `viewMetadataV2`/`viewResourceMetadatas`; no merge semantics in the *builder*; no BC browse) are verified and stand.

### Open questions

- **OQ2** — strike "This is unverified — nothing in the repo documents a GET on `eventhandler`." Replace: *Answered in-repo.* Params are `appURI`, `viewURI`, `eventHandlerType`, `appliesTo` (`probe_parent_eh.py:44-50`) — note camelCase `viewURI`, **not** the `?viewUri=` convention used by the entity/view endpoints. Response shape `data.eventHandlerV2s[]`.
- **OQ3** — change the answer from "Never built" to: *Built, as an out-of-band probe, after PROGRESS.md was last updated.* And strike "`PROGRESS.md` would settle it definitively": grep of PROGRESS.md for `probe_parent_eh|GET.*eventhandler|read.back|read-back` returns zero hits, and it predates the probe (Jul 28 vs Aug 6).

### A7.5 table

`backend/core/health.py:130` reads `{QAD_APP_DIR}/node_modules/typescript/package.json` (defined at `:122`) for the tsc version — not the AUX app's own `package.json`. Relabel the row.

### No issues found

No secret value is leaked anywhere in the section — credentials appear only as config accessor names (`qad_client_id()`, `qad_username()`, `qad_password()`), never as values. All other spot-checked citations resolve correctly, including `qad_client.py:42-69`, `qad_session.py:28-29/43-93`, `lookup_generator.py:70/259-260/266-273/280` (and `create_lookup` is only ever called with an explicit `dry_run=True`, `pipeline.py:74`), `sss/deploy.py:36-46/59/62-72`, `bc_builder.py:98-111`, `database.py:129-137`, `client_extensions.py:238-256`, `RegisteredBCsPage.tsx:9/28-31`, `client_ext/api.ts:137-147`, and `sss/discover.py:4-6/49-61/154/202-239`. The frontend absence claim is independently verified: every `fetch()` in `frontend/src` (13 sites) uses a relative `BASE`, and the only absolute URLs are a Google Fonts import and an SVG xmlns.

---

