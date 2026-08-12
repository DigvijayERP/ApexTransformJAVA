# Adaptive (Java) — Progress

Building `adaptive_java_version`: a separate application generating QAD **Adaptive (Java)** artifacts,
ported from `aux_web_version`, with step-gated human approval across all three cases plus event-handler
generation for embedded grids. See `PLAN.md` for the phase plan and standing constraints.

---

## ▶ RESUME POINT (new session, start here)

> **New session? Read [SESSION_HANDOFF.md](SESSION_HANDOFF.md) first.** It is the short
> read-this-first file: current phase, exact next action, who decided what, and the traps.
> This file is the full log behind it.

**Where we are (2026-08-11):** Case 1 is **built end to end and verified offline** — backend
(274 assertions), 12-route API, and an APEX-styled chat-first frontend rendered live in the browser.
First live contact with `eeadaptive` **confirmed the URL shape** (no `/qad-central/`) but QAD rejected
the supplied credentials (`invalid_grant`), so live runs are blocked on the owner verifying them.

**2026-08-11, later:** owner updated the credentials — **authentication now WORKS** (real bearer
token acquired from eeadaptive, read-only check). Owner also ran the full dry-run in the UI with the
real LLM and approved the result. **Cleared for the first live test**: small throwaway BC, no lookup
fields, every gate approved by hand. Environment may still 500 on entity-metadata (known-degraded);
a failed write does not lock, so that outcome is diagnostic, not fatal.

**Read-order note:** `PHASE0_AUDIT.md` at 583 KB is not readable end to end and is not meant to be.
`PHASE0_SUMMARY.md` carries one section per audit item, one line per pipeline step, every claim tagged
✅ verified / ⚠️ unverified / 🔴 corrected. The audit remains the citation reference behind it.

**Verification: 11 of 15 sections done, 4 outstanding + critic.** A1–A7 were citation-checked in the
first pass. The prioritised round (2026-08-07 → 2026-08-10, workflow `wf_b8b49cee-c90`) landed **B1,
A8, B2 (docs-java) and B4 (docs-tools-sec)** before the session limit hit again. Still outstanding:
**A9 docs-loader · A10 settings · A3/lookup-progress · B3 docs-bc-ext · the completeness critic.**

Resume command for the remaining four + critic (replays the four landed verdicts from cache):

```bash
Workflow({scriptPath: "C:\\Users\\digvijay.parmar\\.claude\\projects\\D--WEB-AUX-adaptive-java-version\\4fe1e254-103a-471c-ae35-4efc4c23b905\\workflows\\scripts\\phase0-verify-priority-wf_b8b49cee-c90.js", resumeFromRunId: "wf_b8b49cee-c90"})
```

⚠️ **`resumeFromRunId` is same-session only.** That run belongs to CLI session
`4fe1e254-103a-471c-ae35-4efc4c23b905`, which has ended — a new session cannot replay its cache and
must re-run the four verifiers from scratch. The **raw verdicts are preserved** and do not need
re-deriving: see `VERIFICATION_ROUND2.md` (full flag-by-flag text, extracted from the task output
before it expired).

✅ **The two §0.4 findings that were resting on unverified sections have now been verified** — see the
2026-08-10 log entry below. Both survive; both need corrections applied.

**Verification already overturned one conclusion.** A7 came back `major-issues`: the first pass claimed
AUX never reads artifacts back from QAD, and it does — `backend/probe_parent_eh.py` GETs an existing
event handler on a **standard QAD parent view**, reads its TS/JS/`concurrencyHash`, POSTs it back as a
no-op update, and re-GETs to confirm the hash rotated. Corrected in `PHASE0_AUDIT.md` §0.4 finding 5,
confirmed by direct read of the file. Root cause worth remembering: the audit inventoried "what talks to
QAD" by grepping for HTTP *library* imports, and that probe reaches QAD via `qad_client` instead. The
correct sweep is `grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py`.

**Blocking questions:**
- **Q-L** — did `probe_parent_eh.py` ever run, and what did it return? Only the commissioner can answer.
  If Shape A succeeded, read-modify-write on a handler at a standard parent view is **proven** rather
  than inferred, which is worth more to Phase 5 than anything else in the audit.
- **Q-F** — permission to run the grid-claiming experiment, and on which environment. The last
  unresolved point in the Pre/Post hypothesis.

**Key locations:**
- Adaptive (this app): `D:\WEB_AUX\adaptive_java_version`
- AUX reference implementation — **read-only, do not modify**: `D:\WEB_AUX\aux_web_version`
- Adaptive platform docs: `D:\WEB_AUX\adaptive_java_version\Docs\` (7 guides, classes 2–8, `.md`)

---

## Status

| Phase | Scope | State |
|-------|-------|-------|
| 0 | Read-only audit of AUX + Adaptive Docs → `PHASE0_AUDIT.md`, `QUESTIONS.md` | ✅ **Closed** — owner greenlight 2026-08-10. 11/15 sections citation-verified |
| 1 | Endpoint and settings registry, segregated per phase | 🔄 **In progress** — config layer done (20 endpoints); classification awaiting owner confirmation; panel not started |
| 2 | Step-gated approval flow across all three cases | ⬜ Not started — Q-A/Q-B/Q-C/Q-D now have delegated answers (see `SESSION_HANDOFF.md` §3) |
| 3 | Run-state persistence across browser refresh | ⬜ Not started |
| 4 | Deployment gating, dry-run default | ⬜ Not started — lock proposal in Q-I awaiting approval |
| 5 | Embedded: event handlers + validations on the parent BC | ⬜ Not started — **blocked on Q-F experiment** |
| 6 | Server-side SSS → JEF port | ⬜ Not started |

Rule: pause for review after every phase. All QAD-writing tests are opt-in and explicitly greenlit.

---

## Log

### Phase 0 — Read-only audit (✅ delivered 2026-08-06, ⏳ pending review)

**Method.** 15 independent read-only agents, one per subject area, each required to cite `path:line`
for every claim and tag every statement `[CONFIRMED]` or `[INFERRED]`. Read: all of `aux_web_version`
`backend/` and `frontend/src/` (28 files), all 7 Adaptive `Docs/*.md` in full, and the AUX
`backend/qad_docs/` corpus (285 `.txt`) where it covers the same subjects. The **uncommitted working
tree** was audited, not `HEAD`.

**Delivered.**
- `PHASE0_AUDIT.md` — 497 KB. Header (§0.1 method, §0.2 coverage vs the 8 items, §0.3 item 2 answered,
  §0.4 the 14 findings that change the plan, §0.5 what Phase 0 did not settle) + 15 sections:
  A1 new-BC pipeline · A2 embedded · A3 SSS · A4 endpoints · A5 auth · A6 persistence · A7 read-back ·
  A8 frontend · A9 docs loader · A10 settings/config · A11 uncommitted work in flight ·
  B1 event handlers · B2 Java extensions · B3 BCs/extensions/relations/formulas/lookups ·
  B4 platform tools/data admin/security.
- `QUESTIONS.md` — Part 1: 11 decisions needed (Q-A…Q-K), each with suggested answer and reasoning.
  Part 2: every question raised by each section.
- `PLAN.md`, `PROGRESS.md` — this file and the phase plan.

**Against the exit criteria, honestly:**

| Criterion | State |
|---|---|
| All 8 items answered with file-path/code references | ✅ Met — see `PHASE0_AUDIT.md` §0.2 coverage table |
| All inferences explicitly labelled | ✅ Met — `[CONFIRMED]`/`[INFERRED]` throughout; each inference carries what would confirm it |
| Zero application code added | ✅ Met — four `.md` files only |
| Commissioner has read the audit and answered the questions | ⬜ Outstanding |
| *(design intent, not a stated criterion)* independent citation verification | ❌ **Did not run** — session limit, both attempts |

**Headline findings** (full text in `PHASE0_AUDIT.md` §0.4):
1. **No Zustand in AUX at all** — three runtime deps; state is React Context. The brief's premise is
   inverted; adopting it would be a new dependency and a documented reversal.
2. `backend/core/progress_parser.py` parses **ABL source**, not UI progress. Name collision only.
3. **Phase 5 Pre/Post hypothesis: PARTIALLY HOLDS.** Mechanism real; parent never touched; QAD documents
   the same move on a standard BC. Two caveats — unavailable when the active app owns the target BC, and
   **grid claiming via `ViewGridsToHandleList` is documented nowhere**. That is the live risk.
4. AUX templates a **single flat handler** hardcoded to Pre. Platform documents four base classes (plus
   a fifth); the parent-field → grid pattern needs three wired together. The brief's suspicion was right.
5. ⚠️ **CORRECTED after verification.** AUX **does** read event handlers back — `probe_parent_eh.py`
   (untracked, newest file in `backend/`) GETs an existing handler on the standard parent view
   `SalesOrders`, reads its TS/JS/`concurrencyHash`, POSTs it back as a no-op update, and re-GETs to
   confirm the hash rotated. The pipelines still never read back; the standalone probe does. The GET
   contract is therefore already known in-repo (`appURI`, `viewURI`, `eventHandlerType`, `appliesTo` —
   camelCase `viewURI`), and `concurrencyHash` is the optimistic-locking token that makes
   read-modify-write possible. It fetches *our own* `BEFORE` handler on the parent's view, not QAD's
   Primary — so it supports the Pre/Post strategy rather than contradicting it. Docs also say the
   parent's coded TS handlers are *not* in the database, which argues **for** Pre/Post.
6. **Phase 2 is a transport rewrite**, not a UI feature — no pause/resume/step storage anywhere; only a
   terminal summary is persisted; an aborted run leaves zero rows. SSS already has the target shape.
7. `TOTAL_STEPS = 14` undercounts and the frontend has already drifted from it (embedded step 8
   unrenderable; three labels disagree). A gate needs a step identity.
8. **The class-6 Java guide claims an undeploy command exists** — three times — contradicting the
   confirmed decompile. Flagged; nothing will depend on rollback.
9. The same guide is **not self-sufficient to write a class**: code listings crop the `package` line and
   all imports.
10. Adding a docs bundle is four mechanical changes; but the loader reads `.txt` only while `Docs/` are
    `.md`, and there is **zero Java anything** in the AUX backend today.
11. **Only one endpoint enforces identity.** `/api/run`, `/api/sss/generate`, `/api/sss/deploy` are open.
12. Confirmed trap #4 is **live** (`dotenv_values()` at `core/config.py:73`); `settings.json` is
    git-tracked with a legacy credential fallback — **no credential has ever been committed** (all three
    commits checked), so latent risk, not current leak.
13. The settings model selector **does not affect the BC pipeline** — `MODEL_MATRIX` hardcodes the model.
14. The AUX repo **cannot currently be cloned and run** — `progress_parser.py:22` imports an untracked
    module.

**No QAD call was made, read or write, at any point in this phase.**

### Phase 0 follow-up round (2026-08-07) — seven-item work order

1. **Q-L investigated without executing the probe.** `probe_parent_eh.py` never committed, never
   stashed, not in the index (only 3 commits exist, all predating it). It writes **no file and no DB
   row** — every output is `print()` to stdout; it imports no logging and no `database`. So a run leaves
   **no artifact by construction**. `backend/logs/app.log` last wrote 2026-08-06 **12:36:50**; the probe
   was created **14:28:18**, 1h51m later, and nothing in `backend/` has been written since. That rules
   out a run *through the backend server process* but **cannot** rule out a standalone run, which would
   emit httpx logs to a handler-less logger and vanish. **Verdict: no evidence either way, and none
   would exist.** Not executed — it POSTs, and no greenlight was given.
2. **Cheap correctness sweep run.** `grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py`
   re-tested every absence claim across all 15 sections. Four contradicted claims, all in A2/A7 and all
   already caught by their verifiers — **plus one in the audit's own §0.3 summary**, now fixed.
3. **Verification re-prioritised.** B1 then A8 run **strictly sequentially** in a dedicated workflow so a
   session limit cannot take both; six remaining sections in parallel after; critic last.
4. **`PHASE0_SUMMARY.md` created** — the readable layer. Audit retained as the appendix.
5. **`QUESTIONS.md` triaged** by Phase 1 / Phase 2 / Phase 5 / later, with a three-question minimum.
6. **Step identity reclassified** from observation to **formal Phase 2 blocker** (Q-D), with the six-item
   resolution scope recorded.
7. **39 deletions accounted for** — all pre-existing user work, none from this project. See below.

**The 39 deletions (working rule 8 — verified, not assumed).** `git status` at the close of this session
is byte-identical to the session-start snapshot: the same 6 modified and 5 untracked files. Per-file
deletions: `pipeline.py` −15, `client_extensions.py` −11, `prompts.py` −9, `PROGRESS.md` −2,
`progress_parser.py` −1, `index.html` −1. Inspecting the removed lines, every one is a superseded line
from the commissioner's own in-flight work — the old PROGRESS.md "Where we are" paragraph, old
`FORM_FIELD_BUILDER` prompt examples, pre-fix step-6 normalization code, the pre-refactor attachment
extractor, and `<title>APEX-Transform</title>`. **Nothing was deleted by Phase 0.**

**Background shells.** No background shell was launched in the visible portion of this session — every
Bash call ran in the foreground. The reported failure is from the earlier, pre-context portion, and no
shell output survives in the session tree to recover it. **Impact assessment: none on any deliverable.**
All 15 audit sections were produced by workflow subagents whose tool use is journaled separately, and
every claim in `PHASE0_SUMMARY.md` traces to a cited file rather than to shell output. If a specific
claim is doubted, the remedy is re-grepping that claim, not recovering the shell.

### Verification round 2 (landed 2026-08-10) — B1, A8, B2, B4

Full flag-by-flag text in `VERIFICATION_ROUND2.md`. Four of nine agents completed; four verifiers and
the critic died on the session limit. **Both prioritised sections landed, which was the point of forcing
them first and sequentially.**

**B1 — `major-issues`. The Phase 5 verdict survives; the section that argued it does not.**
The central conclusion **PARTIALLY HOLDS** stands — the verifier independently re-tested the three
load-bearing absence claims (no doc states whether two modules can claim one grid; no tie-break rule for
two Pre handlers from different apps; `[UIEH]:21` is the only multi-app ordering example) and **all three
hold**. Five findings change the design inputs:

1. 🔴 **§7 omitted `probe_parent_eh.py` — the same defect A7 was corrected for.** The section built its
   "what talks to QAD" inventory the old way and missed the one file that empirically proves limb 1 of
   the hypothesis: a `BEFORE` handler attached to a **standard QAD parent view** from a different app.
2. 🔴 **The three-module citation was false.** `[C7]:427`/`:466` are the *same* Country handler before
   and after "Select Post timing", and `[C7]:625` is a **different BC** (Training). The trio demonstrates
   **zero** coexisting modules on one BC. The conclusion still holds from `[FBEH]:87-89` and `[DEBUG]:32`.
3. 🔴 **The grid-claiming risk was framed backwards.** `[APIREF]:832` — *"If not set, all view grids will
   be handled."* `ViewGridsToHandleList` is an opt-**out** filter, not an opt-in claim. The Q-F experiment
   must therefore run **two arms**: Post-with-explicit-list and Post-with-no-list.
4. 🔴 **The "one row per 4-tuple" fact was a mislabelled inference.** It was deduced from a `fetch()`
   signature; the returned DTO is an **array**. Corroborated in practice only by `probe_parent_eh.py:58`
   taking `eventHandlerV2s[0]`. Downgrade to `[INFERRED]`.
5. 🔴 **The Pre/Post-unavailable restriction is narrower than reported** — it is platform-BC **and**
   same-app, not same-app generally (`[FBEH]:46-52`, `:87`). AUX only creates platform BCs, so it still
   bites operationally, but the docs are inconsistent for coded BCs (`[CLISCR]:22` conflicts).

Plus: handlers **can** be scoped to specific fields in code (`[APIREF]:862-864`), contradicting §2's
"nothing anywhere ties a handler to a single field"; `api/webshell/clearAllCaches` was **invented** —
it appears nowhere in `aux_web_version`; and `[APIREF]` documents **seven** base-class sections, not five.

**A8 — `minor-issues`. The headline finding is safe.** Zustand is **not** a dependency: three runtime
deps, zero in the lockfile, no `node_modules/zustand`. Only the phrase "a repo-wide grep returns zero
matches" is refuted (one comment at `authStore.tsx:4` says *"No Zustand added."*, which the section
itself quotes). Two real defects: a **fourth** undeclared SSE frame type, `lookup_summary`
(`pipeline.py:124-131`), unrendered by the frontend — the "silent event loss" blocker was undercounted;
and the `ProgressPanel.tsx:68` step-4 guard is **not** dead code — it is live in embedded mode
(`EMBEDDED_VISIBLE_STEPS` contains 4). Also: embedded `total` is **variable** (`BASE_TOTAL_STEPS = 7`,
raised to 8 only when a standalone view is wanted), which a "step N of M" gate must handle. The rest are
off-by-one citations and line counts.

**B2 / B4 — `minor-issues`, no finding overturned.** Both undeployability findings stand. One item needs
action rather than filing:

🔒 **`PHASE0_AUDIT.md:4297` reproduces a 32-hex-character `Client ID` value copied verbatim out of the
class-8 training screenshot (`C8:1011`).** Training material or not, that is a credential-shaped
identifier propagated into a circulated audit, and the brief's rule is "never commit credentials".
`adaptive_java_version` is **not a git repo**, so nothing is committed — but the line should be redacted
before this file goes anywhere. **Not yet redacted.**

**Not yet done from this round:** none of the ~40 corrections have been applied to `PHASE0_AUDIT.md` or
`PHASE0_SUMMARY.md`. They are recorded in `VERIFICATION_ROUND2.md` in ready-to-apply form (each written
as "replace X with Y").

### Phase 0 closed / Phase 1 opened (2026-08-10)

**How Phase 0 closed.** The owner supplied the environment values (Q-H) and delegated the remaining
open questions to my suggested answers, with the standing instruction to flag anything doubtful rather
than proceed silently. Recorded per-decision in `SESSION_HANDOFF.md` §3, marked **owner** vs
**delegated**, so a later session knows which are mine to revisit.

**Context recovery.** This session began by reconstructing the project from an exported transcript after
a usage limit ended the previous one. The B1/A8 verification verdicts had landed but were never
reported; they were recovered from the task output file before it expired and written to
`VERIFICATION_ROUND2.md`. The shared brief was diffed against the transcript copy — **identical**,
241 non-blank lines each, zero hunks.

**Housekeeping done.**
- 🔒 `PHASE0_AUDIT.md:4297` Client ID **redacted** before any commit. Verified: zero occurrences remain
  outside the source training deck, which is left byte-intact so its `C8:` line citations stay valid.
- 📦 **`git init`** + `.gitignore` (modelled on AUX's), then an initial commit of the Phase 0
  deliverables. `git check-ignore` confirms `backend/.env` is excluded.

**Phase 1 — config layer built.** See `PHASE1_REGISTRY.md`.

**Every endpoint was already recoverable — the owner did not need to supply any.** 15 read out of AUX's
code, each cited to `file:line`; 5 from the confirmed JEF decompile. **20 total**, segregated by
phase/case, each entry carrying its own `source` and `status`.

| File | Committed | Holds |
|---|---|---|
| `config/endpoints.json` | ✅ | 20 endpoints, per phase/case, with provenance |
| `config/environment.json` | ✅ | base URL, app URI, context root, known env health issues |
| `backend/.env.example` | ✅ | template, key names only |
| `backend/.env` | ❌ gitignored | real client ID; username/password/OpenAI key still blank |

**One material correction to AUX's shape, and it is unvalidated.** AUX builds
`{bare-host}/qad-central/api/qracore/{endpoint}` (`qad_client.py:57,:65`). The Adaptive base already
carries its context root (`/clouderp`), so `clouderp` occupies the slot `qad-central` does — Adaptive
resolves to `{base_url}/api/qracore/{endpoint}` with **no** extra prefix. That matches the brief's
confirmed `{envUrl}api/qracore/…` form. **[INFERRED from a confirmed fact — no call has been made
against `eeadaptive`.]** AUX hardcodes the prefix in three places; the registry makes it a setting.

**Judgement call flagged for owner override:** `QAD_CLIENT_ID` went to `backend/.env` (gitignored)
rather than committed config. The brief calls the plugin's `id` field "safe to commit", but AUX — the
reference implementation — keeps it in `.env` (`core/config.py:94`), and working rule 7 says match the
reference. One line to move if the owner prefers the JEF convention.

**Not started, deliberately:** the settings **panel**. The brief requires the static-vs-dynamic
classification to be confirmed by the owner *before* it is assumed, so building UI around an
unconfirmed classification would be exactly the assumption rule 2 forbids.

### Case 1 build inventory (2026-08-10)

**Owner direction:** build **Case 1 — standalone BC creation** first, step-gated, and come to
server-side/JEF later. Phase 1's settings *panel* is deferred behind it; the config layer it edits
already exists and works without a UI.

Full inventory in **`PHASE2_CASE1_BUILD_PLAN.md`**. Produced by re-reading the AUX source firsthand this
session — `pipeline.py` in full (802 lines), all five builders, `qad_client.py`, `core/config.py` — not
from the audit summary.

**What ports cleanly:** ~1,560 lines of proven payload-construction logic (5 builders + 8 LLM prompts +
the real `tsc` gate + the docs loader). None of it needs reinventing.

**What must be reconfigured — the owner's instinct was right.** Endpoints were the easy half.
`com.extensions.customapp` is hardcoded in **five files, ten places**, and *every* URI in *every*
payload derives from it (entity, module, bdoc, viewmeta, hybridbrowse, bebrowse, field). `MODULE` and
`MODULE_SHORT` derive mechanically from the supplied app URI; **two values do not derive and are now
blocking inputs — `APP_NAME` and `DATASTORE_URI`.**

**What is a rewrite, not a UI feature.** `run_pipeline` is one async generator holding every artifact in
a local variable; a generator cannot suspend across HTTP requests. Each step becomes a standalone
function reading/writing a per-step artifact store. That store is the prerequisite — without it there is
nothing to display at a gate and nothing to regenerate from.

**Case 1 has 16 gates, and the list is variable, not fixed** — step 4 fires only on a step-3 rejection,
3a only with dropdown fields, 13a only when lookups are detected. Every QAD write gates **before** it
fires, showing the exact payload.

🔴 **Design blocker raised for the owner: regeneration after a QAD write has already executed.**
Decision 2 says regenerating re-runs all downstream steps — but once step 3 has run, the BC exists in
QAD and re-running it fails. AUX's own code proves it (`pipeline.py:226-231`, `:450`: a name collision
"cannot be repaired by editing fields"). QAD has no undo and Phase 0 found no delete path. Suggested
rule recorded in the plan §4. **Sub-question left explicitly untested rather than assumed:** whether
`viewMetadataV2`, `eventhandler`, `viewResourceMetadatas` and the deploy pair are idempotent. One live
run settles it.

### Case 1 backend foundation built (2026-08-10)

**Owner supplied the remaining identity values** — `APP_NAME = digwish`,
`DATASTORE_URI = urn:datastore:com.yash.extension`, `QAD_USERNAME`. Password and OpenAI key are the
owner's to place in `backend/.env`. Owner also **agreed to the regeneration rule** (free before a write
executes, blocked after).

**Owner redefined the pipeline to six stages**, a real simplification of AUX's fourteen:

| # | Stage | Gated | Writes on approval |
|---|---|---|---|
| 1 | Requirement gathering | ✅ | — |
| 2 | Field mapping | ✅ | `bc.create` + dropdown wiring |
| 3 | Form creation | ✅ | `form.save` |
| 4 | Event handler | ✅ | `eventhandler.register` |
| 5 | View creation | ❌ **by owner's design** | `view.register` |
| 6 | Deploy | ✅ | `deploy.check_warnings` + `deploy.business_entity` |

Stage 4 sits between form and view, matching AUX's own ordering (its steps 8–11 run after the form save
at step 7 and before the view at 12–13).

Stage 4 carrying no gate is **sound, not an oversight**: `build_view_payload` is a pure function of the
approved spec with no LLM call, so there is no authored content to review. It still writes, so what it
registered is surfaced at the stage-5 gate.

**Built and verified:**

| File | What |
|---|---|
| `backend/core/config.py` | Registry-aware config. **Fixes confirmed trap #4** — `os.environ` now wins over the `.env` file, so Docker `env_file:` works (AUX's `dotenv_values()` reads the physical file only) |
| `backend/core/stages.py` | The 5-stage manifest — **single source of stage identity**, served at `GET /api/run/stages`. Frontend keeps no table of its own |
| `backend/qad_client.py` | Token cache, 401-refresh-and-retry, URL-encoded credentials, dry-run that reports method/url/headers/payload with the bearer masked |
| `backend/builders/identity.py` | `AppIdentity` + every urn pattern, **defined once** instead of re-spelled in four builders |
| `backend/builders/naming.py` | `sql_safe`, labels, formats, `validate_spec` — **one copy** instead of AUX's three |
| `backend/builders/{bc,form,view,deploy}_builder.py` | Ported, payload shapes byte-identical to AUX, identity injected |
| `backend/smoke_test.py` | **45 offline assertions, all passing.** No network, no credentials |

**Improvements over AUX, each deliberate:**
- Token is cached and refreshed on 401. AUX re-fetches before every write (7× per run) and aborts on a
  mid-run 401 — which becomes the *normal* path once a run pauses at a human gate for hours.
- `deployCheckForWarnings` is returned as a **separate payload** so its response can be shown at the
  stage-5 gate. AUX fires it and discards the response (`pipeline.py:739`, never assigned).
- `validate_spec()` runs on the spec the user approved — necessary now that the dialog can be edited by
  hand, which is not a shape the LLM would have produced.
- The form builder **refuses an incomplete layout** rather than saving a partial form.

**Caught by the smoke test, worth carrying:** `status` is a SQL reserved word, so `sql_safe` renames it
to `statusCode` for the physical column while the label stays "Status". A user who asks for `status`
gets a differently-named QAD column. **The stage-2 dialog must show the safe name whenever it differs**,
or the rename is silent.

### Event handlers are IN Case 1 — and the Browse URI gap is closed (2026-08-10)

**Owner confirmed** event handler generation stays in Case 1, positioned after form creation, with the
user verifying the generated code. They also asked for something AUX never did: **prompt for the
Browse URI** instead of shipping the lookup commented out.

**The AUX behaviour, verified firsthand.** `agents/prompts.py:354-366` instructs the model to comment
out every lookup and HTTP call behind a `TODO` pointing at a fake `api/TODO/provide-endpoint`, and
`:378` forbids *"any uncommented HTTP call without a known working URL"*. Root cause: the generator has
no way to know the real URI, so it defers to the user, who hand-edits in QAD afterwards. The generated
handler ships inert.

**How it works now.** The model emits a placeholder inside a string literal —
`const uri: string = "{{BROWSE_URI:customerName}}";` — which is valid TypeScript and therefore survives
the `tsc` gate. The stage-4 dialog lists every distinct placeholder with the line it appears on, the
user supplies real URIs, and substitution is **textual and deterministic**: filling in a URI cannot
change anything else in the code and costs no second LLM call. A placeholder the user skips is commented
out — **exactly AUX's behaviour, so the fallback is never worse than today.** A handler still holding an
unfilled placeholder cannot be POSTed; the builder refuses.

**Also fixed while porting:** AUX hardcodes `eventHandlerType="BEFORE"` and `appliesTo="WEB"`
(`event_handler_builder.py:30-31`). Both are validated parameters here — a typo would otherwise register
a handler against a timing that never fires, which is close to undiagnosable from the UI. Phase 5's
whole design depends on being able to choose the timing.

**Bug caught by the smoke test, not by review:** commenting out a skipped line originally left the
`{{BROWSE_URI:x}}` token inside the comment, so the pre-POST guard kept refusing a handler the user had
deliberately chosen to skip. The comment now reads in plain words. **77 assertions pass.**

---

### First live contact with eeadaptive (2026-08-11)

Owner placed credentials in `backend/.env`; `verify_environment.py` (read-only, auth only) ran twice.

**✅ THE URL SHAPE IS NOW CONFIRMED, not inferred.** `{base}/oauth/token` with **no `/qad-central/`**
reached a real OAuth endpoint that parsed our password grant — a wrong path would have 404'd, a wrong
host would not have connected. The registry's biggest derived-but-unvalidated assumption is settled.
The client_id was also accepted to the point of credential validation (an unknown client returns
`invalid_client`, not `invalid_grant`).

**❌ Blocked on credentials.** QAD's own body: `{"error":"invalid_grant","error_description":
"Username or password is invalid, please try again."}` The account is the owner's colleague's; only
they can verify it. **Deliberately did not retry** — the class-8 guide documents Security Control
`Maximum Access Failures 10` (`C8:1000-1020`), and repeated failures lock the account. Two attempts
spent. Next step is the owner confirming the same credentials log in to the eeadaptive **web UI**;
if the UI accepts them and the API still refuses, the difference is ours to debug (encoding would be
the first suspect).

**Two fixes that came out of it, both kept:**
1. 🔒 httpx logs every request URL at INFO — **including the oauth query string that carries the
   password**, which our own code carefully never prints. `logging_setup` now caps httpx/httpcore at
   WARNING. The leaked line existed only in the local console/app.log; rotated and gitignored.
2. `_post_token` now surfaces QAD's OAuth error body (never the URL), which is what turned a mute
   HTTP 400 into the exact diagnosis above.

### 🎉 FIRST LIVE BC CREATED (2026-08-11) — `DigSmokeTest`, end to end

Owner ran the pipeline LIVE against eeadaptive. Every write succeeded: `bc.create` (with a dropdown,
so the two-save wiring ran for real), `form.save`, `view.register`, and `deployBusinessEntity`.
**The environment's old HTTP 500 on entity-metadata generation is gone** — deferral D5 can be
considered resolved by observation.

**The audit trail caught a real sequence worth keeping.** The owner opened the Deploy gate before
approving View (the rail permits out-of-order navigation). QAD rejected the deploy with its own
business error — `"There should exist at least one View."` — the failed write correctly did NOT lock,
the owner approved View, re-approved Deploy, and it succeeded. Three things proven at once:

1. QAD's business-error envelope surfaces properly (`success:false, severity:1`, message shown).
2. The failed-write-does-not-lock rule works exactly as designed — recovery needed no new run.
3. **`deployBusinessEntity` is retryable after a rejection** — first idempotency data point.

**Observation, not yet acted on:** stages can be run out of order from the rail. QAD itself caught
this case; a cheap guard (Deploy's gate requiring all prior stages approved/skipped) would prevent
the detour. Owner to decide whether to add it.

**Responses are now visible in the UI.** They were ALWAYS recorded (`qad_writes.response`, live calls
only) and served by the API; the writes panel only rendered requests. Each call now expands to
"Request sent" + "QAD's response". The deploy gate's warnings response was already real.

### Dropdown-vs-reference fix verified live (2026-08-11)

Re-ran the same prompt after the prompt fix. Stage 1 now reports
`smokeTestReference` as **character, REFERENCE: yes — DigSmokeTest**, with no invented values —
where before it emitted a dropdown with `SMOKE_TEST_1/2/3` marked "(assumed values)".

It also answered **`HANDLER_NEEDED: no`** with sound reasoning ("no validation rules, cross-field
checks, or any other behavior beyond storing data"), so **stage 4 will skip itself** — the first live
exercise of a conditional stage. `DigSmokeTest` needed a handler; this one does not. The signal is
discriminating, not constant.

### A completed rehearsal looked exactly like a completed deployment (2026-08-11)

Owner reported a "huge bug": `DigLookupTest` showed Deploy ✓ in the app but did not exist in QAD.
**The pipeline was correct** — that run was a DRY RUN (`live_calls=0, rehearsed_calls=6`), so nothing
was ever sent. The bug was the interface.

**How it happened, from the run table.** `DigSmokeTest` ran LIVE (8 real calls, exists in QAD). The
owner then started `DigLookupTest` LIVE, abandoned it on the dropdown bug, and clicked **New run** —
which resets the dry-run pill to its safe default. Nothing said so loudly, and the finished screen was
*identical to a real success*: seven green ticks, "Deploy ✓", one small corner badge.

**A rehearsal that reads as an accomplishment is worse than no feedback at all.** The run view now
carries a full-width mode stripe that changes with both mode and completion:

| | |
|---|---|
| dry, running | violet — "DRY RUN — nothing is being sent to QAD" |
| dry, complete | violet — "REHEARSAL COMPLETE — nothing was created in QAD", and how to do it for real |
| live, running | amber — "LIVE — approving a stage writes to QAD" |
| live, complete | green — "CREATED IN QAD", naming the component and how to verify it |

The header badge now reads **LIVE** as well as **DRY RUN**, rather than being absent when live —
absence of a warning is not a signal.

The default stays dry-run. Defaulting to safe is right; the fix is making the safety *visible*, not
remembering a dangerous setting across runs.

### 🔴 The lookup payload was substantially invented — QAD settled it (2026-08-11)

First live lookup POST rejected: `Field is mandatory. (ResultField); Field is mandatory.
(TargetFieldSet)`. Rather than guess at names, **asked QAD to describe its own Lookup entity** —
`GET entitymetadatas?entityURI=urn:be:com.qad.qra.lookup.ILookup` — which is read-only and answered
completely:

| Field | |
|---|---|
| `BrowseURI` | **required** |
| `FieldSet` | **required** |
| `ModuleURI` | **required** |
| `ResultField` · `SearchField` · `Reference` | optional |
| `ConcurrencyHash` · `DataOperation` | update-only markers |

**Eight PascalCase fields.** The payload ported from AUX used **camelCase** and carried keys the V1 entity does not have —
`appName`, `browseName`, `fieldLabel`, `namespace`, `searchFieldOperator` — plus three arrays.
**CORRECTION (later the same day):** two of those five are real. QAD also has a **V2** lookup entity,
`urn:be:com.qad.qra.lookupv2.ILookupV2`, which declares `Namespace` and `SearchFieldOperator` (plus
`DisallowedActions`, `DisallowedActionsMessage`). Only `appName`, `browseName` and `fieldLabel` appear
on neither. Calling all five invented was an over-claim on my part. AUX never POSTed a lookup, so none of it was ever contradicted. This is the clearest
vindication of the project's rule that an unexercised payload is a hypothesis, not a fact.

**One ambiguity remains, and both sides are sent.** QAD's *entity* calls the field-set `FieldSet`; the
*validator that rejected us* called it `TargetFieldSet`. Both keys carry the same value — an
unrecognised key is ignored, a missing mandatory one is not. **Which one QAD actually consumes is
still unknown**; if the next POST succeeds we will not learn which, and that is worth settling later
from a captured save.

**Auto-populate and search conditions are no longer sent.** QAD's Lookup entity declares no field for
either, so where they belong is unknown — most likely a child collection with its own endpoint. They
are reported in the stage summary and named in the gate's warnings rather than smuggled under a guessed
key, which is exactly the mistake that produced the invented keys above. Configure them in QAD's Lookup
Definition screen for now.

Two of the three long-standing lookup unknowns are therefore closed by evidence:
`searchFieldOperator` does not exist at all, and `uri`/`modelId` were correctly omitted (the entity has
neither; it has `ConcurrencyHash`, which belongs to an update).

### Lookup blocked on a capture — reading has been exhausted (2026-08-11)

Second live lookup POST got past the field names and failed with **`Invalid URI`** (no field named).
Three URIs are sent; `ModuleURI` is proven good by every other call, so it is `BrowseURI` or the
field set.

**Read QAD to find out, and hit a wall worth recording:** `GET entitymetadatas` returns
**`fieldURI: ''` for every field of every component** — checked on the DEPLOYED `DigSmokeTest` and the
undeployed `DigLookupTest2`, so it is not a deployment-state effect. QAD accepts the `fieldURI` we send
at create time and does not give it back. **Our field-set URI is therefore unverifiable by construction**,
and class 4 (pp. 6–8) shows the real flow is to *pick* the field from a Fields dialog filtering on
"Field URI contains …" — a source we have not located. `viewResourceMetadatas` GET returned zero rows.

**This is the point to stop deriving and capture.** Escalated to the top of
`API_CAPTURES_NEEDED.md`: the Fields picker request, then the Save POST body. One is blocking, the
other closes the last two unknowns at the same time.

**Nothing else is blocked.** Everything before Lookups works live, and the failed write did not lock —
the run can resume at that stage the moment the payload is right.

### The capture landed — and QAD's picker replaces derivation entirely (2026-08-11)

Owner captured the Lookup screen's Result Field picker. It is the same generic `browses` endpoint:

```
GET api/qracore/browses?browseId=urn:browse:custom:lookupBrowseFields
    &page=1&pageSize=25&pageAction=first
    &filter=browseURI,eq,<browse uri>,literal
```

**Exercised ourselves and it works — `page` and `pageAction=first` are REQUIRED**; without them QAD
returns 200 with zero rows, which is exactly the kind of silent-empty that looks like "no data".
`relatedResourceUri` is optional.

**It answers the `Invalid URI` directly.** QAD returns:

```
Test Code    digSmokeTest.testCode
Description  digSmokeTest.description
Status       digSmokeTest.statusCode
```

We were sending **`digsmoketest.testCode`** — derived from the browse URI's last segment, which
`view_builder` lowercases. QAD wants **`digSmokeTest`**, the BC name camelCased. No naming rule was
going to recover that reliably, which is the point: **the lookup stage now RESOLVES the user's input
against QAD's own list** and sends the string QAD authored. Typing `testCode` or `Test Code` both
resolve; anything else fails locally with the real options listed, instead of as a QAD rejection.

**Also learned: there is a V2 lookup entity.** The picker's `relatedResourceUri` names
`com.qad.qra.lookupv2.ILookupV2:Lookup.resultField`, while our POST goes to the V1 entity inherited
from AUX. V2 has four fields V1 lacks. Whether the write should target V2 is **still open** — the Save
POST body would settle it, along with the `FieldSet` vs `TargetFieldSet` ambiguity and where
auto-populate targets live.

### 🔴 The Save capture landed — and corrected a wrong turn of mine (2026-08-11)

Owner captured a real Lookup Definition **Save** off the wire. It settles everything, and reverses a
change I made two rounds earlier.

**The endpoint is V1** — `lookups?viewUri=urn:be:com.qad.qra.lookup.ILookup`. Ours was right; the
LookupV2 entity the picker's `relatedResourceUri` mentions is not what the screen posts to.

**🔴 THE KEYS ARE camelCase. I was wrong.** After reading `entitymetadatas` I rewrote the payload in
PascalCase because QAD reported its field CODES that way. **Entity field codes and wire JSON keys are
different things**, and AUX's camelCase was right all along. Reverted. The lesson is narrow and worth
keeping: *asking an entity to describe itself tells you about the entity, not about the wire.*

**What the earlier "Field is mandatory" really meant.** Not that the keys were wrong — that the
VALUES did not resolve. `resultField` was `digsmoketest.testCode` where QAD holds
`digSmokeTest.testCode`. **QAD reports an unresolvable value as a missing one**, which is why two
rounds of key-renaming chased the wrong thing.

**Now settled by the wire, not by inference:**

| | |
|---|---|
| `searchFieldOperator` | short codes — the UI's "greater or equal to" went out as **`ge`**. So `eq` is right |
| `concurrencyHash` | **present and null** on create, not omitted |
| `modelId` | does not exist at all |
| `lookupResultFields` / `lookupSearchConditions` / `lookupQualifiers` | **real members**, though the entity metadata lists none of them. Auto-populate does have a home — restored |
| `namespace` | the module's **first two segments** (`com.yash`), not the whole module. No rule would have produced that |
| condition shape | `{fieldName, operator, fieldValue1, fieldValue1Type, __gridLockedDummyColumn}` — no `fieldValue2` or `dataType`, and it really does ship a UI grid artefact |

**Two things in the capture deliberately NOT copied:** a malformed `uri`
(`urn:be:...IBERelation:urn:app:com%2Eyash...`) that reads as leftover UI state, and
`searchVariablesDataLists`, a large static list of date/user tokens the UI ships for its own dropdowns
rather than data about the lookup.

**One unknown left, honestly narrow:** `lookupResultFields` is confirmed present but was EMPTY in the
capture, so its element shape `{field, target}` still comes from class 4 p.13's screenshot rather than
the wire.

### NVIDIA NIM works, but the free tier is slow (2026-08-12)

Owner's OpenAI credits ran out, so NVIDIA NIM was added behind `LLM_PROVIDER`. Measured on the free key:

| Model | Result |
|---|---|
| `minimaxai/minimax-m3` | **unusable.** Answers once, then 429s indefinitely. Never cleared, even after 82s of backoff |
| `meta/llama-3.3-70b-instruct` | **works** — but two calls took **four minutes**, succeeding only because the retry ladder waited it out |

A full 7-stage run makes **8 model calls** (requirements 1, fields 1, form 3, handler 3). At free-tier
pacing that is minutes per stage, not seconds. It is genuinely usable for correctness testing, which is
what it is for; it is not something to demo on.

`.env` switched to the working model. The rate-limit ladder (5/12/25/40s, on top of the SDK's own
retries) is per-provider, so OpenAI keeps the SDK defaults rather than inheriting a free-tier tuning.

**Stages 5, 6 and 7 make no model calls at all**, so a lookup or deploy test needs no key and no
waiting. That is how the lookup fix can be tested while credits are out.

## Deferrals — named, not silently dropped (working rule 6)

| # | Deferred | Why | When it must be picked up |
|---|---|---|---|
| D1 | ~~Citation verification of A8–A11 + B1–B4~~ → **narrowed**: A9 docs-loader, A10 settings, A3 lookup-progress, B3 docs-bc-ext, + the completeness critic | Session limits across four attempts; 11 of 15 now done. B1 and A8 — the two that gated design decisions — **are** verified | Still first queued item, but no longer blocking: neither B1 nor A8 rests on it |
| D1a | Applying the ~40 corrections from round 2 to `PHASE0_AUDIT.md` / `PHASE0_SUMMARY.md` | Verdicts landed after the session limit and were recovered from the exported transcript, not written up | Before Phase 0 is signed off. Ready-to-apply text is in `VERIFICATION_ROUND2.md` |
| D1b | Redacting the `Client ID` value at `PHASE0_AUDIT.md:4297` | Flagged by B4's verifier; not a live-environment secret, but credential-shaped and against the brief's rule | Before the audit is shared outside this machine |
| D2 | Nothing verified against a live platform | Phase 0 was read-only by instruction | Phase 5 (Q-F) and Phase 6 need it |
| D3 | Grid-claiming question | Unanswerable from documents — 7 guides + 285 docs silent | Before Phase 5 design is frozen |
| D4 | ~~`EventHandlerV2sComm.ENTITY_URI` via network capture~~ | **RESOLVED** — `probe_parent_eh.py:44-51` already establishes the endpoint and parameters | — |
| D4a | Whether `probe_parent_eh.py` was ever run successfully | Not determinable from the filesystem; it A/B tests two payload shapes, so the update contract was unsettled when written | Q-L — before Phase 5 design |
| D5 | Adaptive environment's HTTP 500s | Out of Phase 0 scope | Before any live Adaptive validation. `PHASE0_AUDIT.md` B4 records a diagnostic the docs suggest: the UI's Package action dispatches an OS Script whose error text lands in the Inbox, so running the script directly may reveal what the 500 swallows |
| D6 | `aux_web_version/PROGRESS.md` (75 KB) not read end to end | Only the parts relevant to specific questions were read | If a question turns on AUX project history |
| D7 | AUX-side defects found during the audit (unrendered lookup events, discarded `deployCheckForWarnings` responses, untracked Phase 11 files, `frontend.zip` unignored) | **Out of scope — this project does not modify AUX** | Recorded in `QUESTIONS.md` Part 2 for the AUX owner |
