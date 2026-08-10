# Adaptive (Java) — Progress

Building `adaptive_java_version`: a separate application generating QAD **Adaptive (Java)** artifacts,
ported from `aux_web_version`, with step-gated human approval across all three cases plus event-handler
generation for embedded grids. See `PLAN.md` for the phase plan and standing constraints.

---

## ▶ RESUME POINT (new session, start here)

**Where we are:** Phase 0 **not closed**. Deliverables: `PHASE0_SUMMARY.md` (18 KB — **read this one**),
`PHASE0_AUDIT.md` (583 KB reference appendix), `QUESTIONS.md` (12 decisions, triaged by what they block),
`PLAN.md`, this file. No application code exists.

**Next action:** read `PHASE0_SUMMARY.md`, then answer the triaged blocking subset in `QUESTIONS.md` —
**Q-L, Q-D, Q-H** if answering only three. Do not start Phase 1 before that.

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
| 0 | Read-only audit of AUX + Adaptive Docs → `PHASE0_AUDIT.md`, `QUESTIONS.md` | ✅ Delivered — ⏳ pending review; verification pass outstanding |
| 1 | Endpoint and settings registry, segregated per phase | ⬜ Not started — blocked on Phase 0 approval + real values (Q-H) |
| 2 | Step-gated approval flow across all three cases | ⬜ Not started — blocked on Q-A/Q-B/Q-C/Q-D |
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

---

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
