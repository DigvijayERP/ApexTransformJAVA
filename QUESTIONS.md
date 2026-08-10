# QUESTIONS — Phase 0 output, awaiting your answers

Every item carries **my suggested answer and my reasoning**, so you can approve or correct rather than
start from scratch, per working rule 2.

**Part 1** is the short list: decisions that change what gets built, and that I will not proceed past
without you. **Part 2** is the full set raised by each audit section — lower-stakes, mostly things I
would otherwise decide myself, recorded so nothing is silently assumed.

Nothing here is a request to re-litigate a settled decision. Where the brief already decided something
(three cases stay separate, regeneration re-runs downstream, deploy is terminal, run state persists,
parent handlers are never modified, AUX keeps SSS, OAuth as in AUX, endpoints live in settings), I have
taken it as given and only asked about consequences the code revealed.

---

## Triage — answer by what it blocks

You do not need to answer all twelve. Answering the **five in the first two rows** unblocks Phases 1
and 2; the Phase 5 row can wait until that design starts, except **Q-L**, which is cheap and may already
be answered in your head.

| Blocks | Questions | Why now |
|---|---|---|
| **Phase 1** | **Q-H** real endpoint values + static/dynamic split | Phase 1 cannot start without values; nothing else in Phase 1 is contested |
| **Phase 2** | **Q-D** step identity 🔴 *formal blocker* · **Q-B** transport · **Q-A** Zustand · **Q-C** which steps gate · **Q-G** auth gap | Each changes the architecture, not the implementation. Deciding after code exists means rewriting it |
| **Phase 5** | **Q-L** did the probe run 🔴 · **Q-F** grid experiment permission · **Q-E** Pre vs Post timing | Q-L and Q-F are the two unknowns the whole embedded-handler design rests on |
| **Answerable later** | **Q-I** deploy lock (Phase 4) · **Q-J** Java bundle sources (Phase 6) · **Q-K** environment permissions | Proposals are recorded; none blocks work starting |

**If you answer only three:** Q-L, Q-D, Q-H.

---

# Part 1 — Decisions I need from you

## Q-A. Zustand: hard requirement, or a premise that turned out wrong?

**The finding.** There is no Zustand in AUX. `frontend/package.json:10-14` has exactly three runtime
dependencies — `react`, `react-dom`, `react-router-dom` — and a repo-wide grep returns zero matches.
State is React Context plus component-local `useState`. `features/auth/authStore.tsx:1-4` records the
decision in its own header comment: *"No Zustand added."*

**My suggested answer:** do not add Zustand. Build run state as a `useReducer`-based `RunContext`
alongside the existing `AuthProvider`.

**Reasoning:** a gated run is exactly a state machine (`idle → running → awaiting_approval(step) →
approved → …`), which is what `useReducer` is for; it needs no new dependency; and it keeps Adaptive
consistent with the reference implementation instead of diverging from it on day one. If you do want
Zustand, that is fine — but it is a **new dependency and a reversal of a documented decision**, not a
continuation, and I want that to be your call rather than my assumption.

**Blocks:** Phase 2 design.

---

## Q-B. Phase 2 transport: per-step request/response, or a stream that pauses?

**The finding.** Today the run is one linear `AsyncGenerator` inside one `StreamingResponse`
(`pipeline.py:381`, `client_extensions.py:168-212`). No pause, no resume, no step storage — grep for
pause/approve/resume returns zero hits. The only client control is `abort()`. Meanwhile **SSS already
implements the shape the brief asks for**: per-step request/response with an
approve / regenerate / discard review UI (`ReviewDeploy.tsx:63-101`, `RulePrompt.tsx`).

**My suggested answer:** per-step request/response, modelled on SSS. Keep SSE *inside* a step for live
progress, and end each stream at a gate with a terminal `{type:"awaiting_approval", step, artifact_id}`
frame.

**Reasoning:** holding an SSE connection open across an indefinite human pause invites proxy and idle
timeouts and cannot survive a browser refresh — which Phase 3 requires. Per-step request/response makes
each step's artifact naturally addressable, which is what both the approval dialog and the
"return to any step and regenerate" requirement need. And the team has already shipped this shape once.

**Blocks:** Phases 2 and 3.

---

## Q-C. Does "each step" mean all ~16, including the ones with nothing to show?

**The finding.** The brief says each step pauses and presents *"what that step actually gathered or
produced — the real content, not a status line."* Read literally that is every step. But the pipeline
has steps whose entire output is a QAD acknowledgement — there is no artifact a human can meaningfully
review, only "the POST succeeded."

**My suggested answer:** gate every step as instructed, but let the pipeline declare a `gated` flag per
step. Steps with a reviewable artifact (field design, panel layout, handler code, view config) stop and
wait. Steps whose output is a QAD write get their gate **before** the write, showing the exact payload
that is about to be sent — which is more useful than approving the receipt afterwards.

**Reasoning:** this honours "nothing goes to QAD without review" more strictly than gating after the
fact, and avoids ~16 dialogs of which several say nothing. If you want a hard stop on all sixteen
regardless, say so and I will build it that way — it is a one-flag difference, not a design change.

---

## Q-D. Step identity — 🔴 **formal Phase 2 blocker**, reclassified from observation

**Status change.** This was reported as an observation. It is a **blocker**: Phase 2 cannot be built
correctly on the current step model, and no amount of UI work routes around it.

**Why it blocks, precisely.** A step-gated approval flow needs a **stable identity per gate** — to render
the dialog, to record the approval, to key the stored artifact, and to know which downstream steps a
regeneration must re-run. The current model cannot supply one:

| Defect | Evidence | Consequence for a gate |
|---|---|---|
| Two real work units have **no step identity at all** | dropdown wiring emits under `step: 3` (`pipeline.py:529`); lookup detection emits frames with **no step/total/name keys** at all | Neither can be gated. Dropdown wiring *hard-fails the run*, so it is exactly the kind of step a human should see |
| A step number is **re-used** | dropdown wiring re-emits `step: 3`, producing a duplicated "step 3 done" | An approval keyed on step number would be ambiguous — which step 3 was approved? |
| Identity is defined in **two places that have already drifted** | `STEP_LABELS` (`pipeline.py:145-160`) vs `ProgressPanel.tsx:3-18`; the frontend **ignores the `name` the backend sends on every frame** | Live today: embedded step 8 is unrenderable, and three embedded labels disagree with the backend. A UI that shows the wrong step name will collect approval for the wrong artifact |
| `TOTAL_STEPS = 14` is hardcoded in **three** places | `pipeline.py:142`, `models.py:33`, and the frontend list | Progress and gate counts can disagree |

**What resolving it requires** (recorded per your instruction — this is scope, not a plan to execute):

1. **Promote the two unnumbered units to real steps.** Either renumber (14 → 16) or add sub-step ids
   (`3a`, `13a`). Sub-steps are the smaller change and keep the existing public numbering stable.
2. **Make the backend the single source of step identity.** A manifest —
   `GET /api/run/steps?mode=standard|embedded` → `[{id, label, gated, writes_to_qad}]` — generated from
   the same constant the pipeline iterates, so the two cannot diverge.
3. **Delete the frontend step tables** (`STANDARD_STEP_NAMES`, `EMBEDDED_STEP_NAMES`, `VISIBLE_STEPS`)
   and render from the manifest plus the `name` already present on every frame.
4. **Collapse the three `TOTAL_STEPS` definitions to one**, derived from the manifest.
5. **Give every emitted frame a step id**, including the lookup frames that currently have none — an
   approval UI must never receive a frame it cannot place.
6. **Then** the gate table (`gated: true/false`) becomes expressible, which is what Q-C asks about.

Items 1–5 are mechanical and touch no generation logic. They are cheap now and expensive once fourteen
gates exist that key on the current numbering.

**My suggested answer:** do items 1–5 as the first work of Phase 2, before any approval UI. Use sub-step
ids rather than renumbering, unless you regard the 14-step list as disposable.

**One thing I need from you:** whether the 14-step numbering is a **public contract** — anything users,
docs, or saved history rows depend on. If it is, sub-steps are required rather than merely preferred.
The 19 existing `runs` rows store only a terminal summary, so history does not appear to depend on it,
but you would know if anything outside the repo does.

---

## Q-E. Phase 5 timing: switch from Pre to Post?

**The finding.** AUX hardcodes Pre — `event_handler_builder.py:30` emits `"eventHandlerType": "BEFORE"`,
and the prompt bakes `Maint_BEFORE` into the module name (`agents/prompts.py:259`).

**My suggested answer:** Post (`AFTER`) for Phase 5.

**Reasoning:** to populate embedded-grid fields you want the parent's own logic and data binding to have
already run; the docs define Post as running *"after the existing application code."* QAD's only
authored example of extending a **standard** BC's UI uses Post. This is a product decision, not just a
test, which is why I am asking rather than choosing.

---

## Q-F. May I run the grid-claiming experiment, and against which environment?

**This is the one that blocks Phase 5 design.** Everything else in the Pre/Post hypothesis checks out;
this does not, and cannot be settled from documents — 7 Adaptive guides and 285 AUX docs are silent.

**The question.** `createViewGridTSHandler` is only called for grids listed in that handler's
`ViewGridsToHandleList`. Can a Primary module and a Post module **both** claim the same `gridId` and
both receive grid events? If yes, your merge-free approach works for grids. If no, embedded-grid
reactivity cannot be done without touching the parent's Primary handler, and Phase 5 needs a different
design.

**The experiment** (cheap, read-mostly, ~15 minutes): on a BC with an existing Primary that handles grid
`G`, register a Post handler that also lists `G` and overrides `onAutoGridBindData` with a
`console.log`. Open devtools. Observe whether both modules log.

**What I need from you:** (a) permission to run it, and (b) **which environment** — the brief says to
ask before pointing anything at the working sandbox, and the intended Adaptive environment is currently
returning HTTP 500s. It does write one event-handler row, so it is not read-only; it is reversible by
deleting that row.

**My suggested answer:** run it on the working sandbox, on a disposable BC, before Phase 5 design is
frozen. **Reasoning:** designing Phase 5 on an unverified inference and discovering it is wrong midway
is the expensive outcome, and this is the single cheapest test that removes that risk.

---

## Q-G. Fix the auth gap before Phase 2, or during Phase 4?

**The finding.** Exactly one backend endpoint checks identity (`/api/auth/me`, `routers/auth.py:69`) and
exactly one frontend call sends a token (`features/auth/api.ts:53`). `/api/run`, `/api/sss/generate` and
`/api/sss/deploy` are open — a bare `curl` to `/api/sss/deploy` writes to QAD. `ProtectedRoute` is
client-side only.

**My suggested answer:** fix it before Phase 2 ships. Smallest version: a shared `authedFetch` wrapper
plus `Depends(get_current_user)` on the mutating routes.

**Reasoning:** an "approve & deploy" button that any unauthenticated caller can invoke by hand is a
**worse** posture than today's, because the UI now implies a gate that does not exist. If the deployment
is internal-network-only that lowers the urgency but does not remove it.

---

## Q-H. Phase 1 needs real values from you — here is exactly what, and in what shape

Per the brief I have not invented any of these. The registry will be built to receive them.

**Environment identity** (one block per environment; I suggest `adaptive` and, if you want it,
`sandbox`):

| Key | Shape | Notes |
|---|---|---|
| `QAD_BASE_URL` | `http://host:port` | **host:port only** — AUX appends `/qad-central` in code. No trailing slash. |
| `QAD_CLIENT_ID` | string | for the `oauth/token` call |
| `QAD_APP_URI` | `urn:app:com.extensions.<name>` | AUX default is `urn:app:com.extensions.customapp` |
| `QAD_USERNAME` / `QAD_PASSWORD` | string | **secrets — `.env` only, never committed** |

**Java/JEF additions Adaptive needs that AUX has no equivalent for:**

| Key | Shape | Why |
|---|---|---|
| `envUrl` for JEF | `https://host/clouderp/` **with** trailing slash | the JEF contract composes `{envUrl}api/…` directly, unlike AUX's `qad-central` convention — these two base URLs are **not** the same shape and I do not want to conflate them |
| `fullAppName` | `com.extensions.<app>` | drives package, jar name `<fullAppName>-ext-cust.jar`, and the workspace folder `urn_app_<fullAppName>` |
| Maven/JDK paths | absolute paths | build must check exit codes itself (confirmed trap #2) |

**My proposed static-vs-dynamic split, for your confirmation** (this is the classification the brief
asked me to present rather than assume):

- **STATIC — identical across environments, safe to commit:** every endpoint *path template*
  (`api/qracore/sse`, `api/qracore/sse/upload-packages`, `oauth/token`, `api/qracore/browses`, …);
  URN *patterns*; `grant_type=password`; the multipart form field name `files`; Maven coordinates and
  the `1.8` bytecode target; manifest keys.
- **DYNAMIC — per environment, `.env`/settings:** `QAD_BASE_URL`, JEF `envUrl`, `QAD_CLIENT_ID`,
  `QAD_APP_URI`, `fullAppName`.
- **SECRET — `.env` only, gitignored, never in `settings.json`:** `QAD_USERNAME`, `QAD_PASSWORD`,
  `OPENAI_API_KEY`, `APEX_*`.

One item I could not classify with confidence: `appSeq=0&fileSeq=3` in the AUX SSS upload URL
(`sss/deploy.py:45`). Nothing in the repo explains them and they were copied verbatim from the VS Code
extension. **My suggestion:** endpoint-template defaults, not config keys, until a live deploy proves
otherwise.

---

## Q-I. Phase 4 deploy-lock semantics — my proposal, per your instruction to propose then ask

The brief asked me to read the code, consider both cases, and propose. I have; here it is.

**BC creation — lock after success.** Re-running is not merely redundant, it dead-ends: AUX already has
`_is_duplicate_entity_error` handling (`pipeline.py:447-455`) because the BC exists afterwards. Lock the
run and offer "start a new run" instead.

**Java extension jar — do NOT lock, but gate every deploy individually.** Whole-jar replacement is
inherently repeatable and a second deploy is a legitimate operation, so a lock would block normal work.
Instead: each deploy requires its own fresh approval showing (a) the exact jar contents — every class
that will exist after this deploy — and (b) an explicit warning when a class present in the previously
deployed jar is **absent** from this one.

**Reasoning for (b):** this is the trap in your own confirmed facts — *"deploying from an incomplete
copy silently erases everything not in that copy — no warning, no conflict, no error."* Since there is
no read-back endpoint for what is currently deployed, the tool cannot diff against the server. It can
only diff against **its own record of what it last deployed**, which means Adaptive must persist a
deploy manifest per app. I would rather build that now than discover the erasure later. Rollback is
explicitly not designed for, per your instruction, since it is unverified and there is no undeploy.

**What I need:** approval of this split, or a correction.

---

## Q-J. Where does the Java docs bundle come from?

**The finding.** Two independent problems. (1) The loader reads `.txt` **only**
(`qad_docs_loader.py:92`), grouped by immediate parent folder name — the Adaptive `Docs/` are `.md`, so
they are invisible to it as they stand. (2) The class-6 Java guide is **not self-sufficient to write a
class**: both code listings start at source line 6, so the `package` line and all imports are cropped,
including `@Extension`, `Output`, and `TrainingBaseService`. It also points at an external handout not
present in the repo.

**My suggested answer:** build the bundle from three sources, not one — the class-6 deck for workflow
and the worked example; **`javap` output against the real dependency jar** for the actual API surface;
and your confirmed decompile facts for the HTTP contract. Convert to `.txt` in uniquely-named folders
rather than changing the loader (it is a one-glob change either way, but `.md` would then need
per-extension parsing).

**Reasoning:** an LLM grounded only on the deck will emit a file that does not compile — that is not a
prediction, it is a direct consequence of the missing imports. B2 §6 contains a concrete 11-page bundle
outline; the highest-value page is exactly the one the deck cannot supply.

**What I need:** confirmation that I may run `javap` against the dependency jar, and **where that jar
is** — the Adaptive environment currently cannot serve it (*"Downloading of core libs failed"*).

---

## Q-L. Did `probe_parent_eh.py` ever run, and what did it return?

**This is the highest-value question in the document, and only you can answer it.**

**The finding.** `backend/probe_parent_eh.py` is untracked and the newest file in `backend/`. It GETs an
existing event handler from QAD, reads its `typeScriptCode` / `javaScriptCode` / `concurrencyHash`,
POSTs it back as a no-op update, and re-GETs to confirm the hash rotated. It targets
`urn:view:viewmeta:com.qad.erp.sales.SalesOrders` — a **standard QAD parent view** — with
`appURI = urn:app:com.extensions.customapp`. That is exactly the Phase 5 configuration.

The first-pass audit missed this file entirely and concluded AUX never reads back from QAD.
Verification caught it; §0.4 finding 5 is the correction.

**What I cannot tell from the filesystem:** whether it was ever run, and what QAD said. The script A/B
tests two payload shapes — with `uri` (`:74-89`) and without (`:111-125`) — which reads as *"the update
contract was not yet settled when this was written."*

**My suggested answer:** it was written to answer the Phase 5 update question and either has not been
run yet, or was run against the AUX environment and the result was not recorded anywhere in the repo —
`PROGRESS.md` has zero mentions of it and predates it (Jul 28 vs Aug 6).

**Why it matters:** if it ran and Shape A succeeded, then read-modify-write on a handler at a standard
parent view is **proven**, and Phase 5 has a confirmed update path rather than an inferred one. If it
failed, the failure mode tells us what QAD requires. Either outcome is worth more to Phase 5 than
anything else in this audit — including, arguably, the grid experiment in Q-F, since this one may
already be answered and just not written down.

**What I need:** the output, or "never ran it." If the latter and you want it run, it needs your
greenlight — it POSTs, so it is a write, though a deliberately no-op one.

---

## Q-K. Which environment may I point things at, and when?

The brief says to ask before using the working sandbox. Collecting the asks in one place:

| Purpose | Reads or writes | Environment I would use |
|---|---|---|
| Q-F grid-claiming experiment | writes one event-handler row (deletable) | working sandbox, disposable BC |
| Q-L re-running `probe_parent_eh.py` | **writes** (a deliberate no-op update) | only if you greenlight |
| `javap` against the dependency jar (Q-J) | read-only, local | wherever the jar can be obtained |
| ~~Recover `EventHandlerV2sComm.ENTITY_URI`~~ | — | **no longer needed** — `probe_parent_eh.py:44-51` already establishes the endpoint and its parameters |
| Phase 6 discover → generate → compile | local only, no QAD writes | none needed |
| Phase 6 deploy | **writes** | none until you greenlight; dry-run default |

**My suggested answer:** authorise the `javap` read now, and the Q-F experiment on the sandbox. Answer
Q-L from memory if you can, rather than re-running anything. Leave every other write path dry-run.

---

# Part 2 — questions raised by each audit section

Each carries the drafting agent's suggested answer and reasoning. These are things I would
otherwise decide myself; they are recorded so nothing is silently assumed. Answer only the ones
you care about.

Sections marked ⚠️ *not verified* have not had their citations independently re-checked.

---

## A1. New business component from scratch — pipeline ✅ *citation-verified*

1. **Is the correct total 14, 16, or something else?** — *My suggested answer:* the honest count of work units is 16, and the two unnumbered ones (dropdown wiring, lookup detection) should get real identifiers rather than borrowing `step: 3` / no step at all. *Reasoning:* both can fail (wiring hard-fails the run at `pipeline.py:523-539`), both take user-visible time, and a duplicated `step 3 done` is already a UI defect. *What would confirm:* whether the commissioner treats the 14-step list as a stable public contract (in which case add sub-steps like `3a`/`13a` instead of renumbering).
2. **Which boundary should the approval gate use — after step 2 or after step 6?** — *My suggested answer:* after step 2. *Reasoning:* it is the only boundary before *any* QAD mutation; a gate after step 6 still leaves an orphaned BC in QAD from step 3 if the human rejects, which is exactly the state that triggers the `_is_duplicate_entity_error` dead-end on re-run (`pipeline.py:447-455`). *What would confirm:* whether reviewers need to see the *panel layout* (only available after step 6) to make the call, in which case two gates are warranted.
3. **Was omitting `eh_data["summary"]` and `deploy_data["summary"]` from `state` deliberate?** — *My suggested answer:* an oversight. *Reasoning:* every other builder's `summary` is captured (`bc_summary` `:500`, `form_summary` `:606`, `view_summary` `:699`) and the pattern breaks only at steps 11 and 14. *What would confirm:* whether `SummaryCard` was ever intended to show handler size / deployed URI.
4. **Is the discarded `deployCheckForWarnings` response intentional?** — *My suggested answer:* no; it should at least be surfaced as a `warning` frame. *Reasoning:* the endpoint's only purpose is to report warnings, and calling it while throwing the result away means the call has zero effect. *What would confirm:* whether QAD's own UI treats those warnings as blocking.
5. **Should the Phase 11 lookup frames be visible before this work is called done?** — *My suggested answer:* yes, and this is the highest-value small fix in the audit. *Reasoning:* `_emit_lookup_events` exists specifically so a human can review `_needs_verification` before any live POST (`lookup_generator.py:23-25`), but the frontend's `SSEEvent` union (`api.ts:6`) and `ProgressPanel`'s `type === "step"` filter drop every one of those frames, so the review it was built for cannot happen. *What would confirm:* whether a separate reviewer surface (outside the run panel) is planned instead.
6. **Is the `# each run spawns 8 LLM calls` rate-limit rationale (`client_extensions.py:118`) still the intended budget?** — *My suggested answer:* update it to "6-9 depending on the `.p`-parse and retry paths". *Reasoning:* the actual counts are 6 / 7 / up to 9 and the comment matches none of them; the `5/minute` limit itself looks unaffected. *What would confirm:* whether the two retry paths (step 4, step 6) were counted when the limit was chosen.
7. **Is the LLM "compile" at step 10 a known accepted risk or scheduled for replacement?** — *My suggested answer:* replace it with real `tsc` emit; SSS already does exactly that (`sss.py:107-108`, `sss_compile.compile_app`), so the capability is in-tree. *Reasoning:* step 9 already invokes `tsc`; dropping `--noEmit` and reading the emitted `.js` removes an LLM call, a failure mode, and the unvalidated-JS write in step 11. *What would confirm:* whether the ES5/`--module none` constraints QAD imposes are fully expressible in the `tsc` invocation already used at `ts_compiler.py:84-93`.

---

## A2. Embedded pipeline ✅ *citation-verified*

1. **Is the parent-side grid actually rendered, and does `isIncludeOnParent: False` (`backend/builders/embedded_builder.py:303`) contradict "grid on parent form"?**
   *My suggested answer:* The grid does render, and `isIncludeOnParent:False` is not a contradiction. *Reasoning:* the in-file finding at `:15-24` and `PROGRESS.md:186-189` record live tests across flag combinations, all of which still produced a grid, and the comment states QAD derives those checkboxes from a *combination* of fields rather than 1:1. The current values are explicitly labelled "known-working defaults" (`:23-24`). I cannot verify runtime rendering from source. **To confirm:** one live embedded run + screenshot of the parent maintenance form.

2. **Does step 8's standalone view (`build_view_payload`) actually work for an embedded child BC, given the child's PKs include `domaincodeEx` + the parent FK?**
   *My suggested answer:* It builds and probably POSTs successfully but is semantically odd. *Reasoning:* `build_view_payload` requires ≥1 PK (`backend/builders/view_builder.py:59-61`) — satisfied — and emits `"usesDomain": False` (`:141`) plus browse columns for *all* fields including `domaincodeEx` and the parent FK (`:66-100`). Nothing validates that the entity is a data extension. But the frontend never shows step 8 (`frontend/src/features/client_ext/components/ProgressPanel.tsx:22-32`), which suggests this path may never have been exercised end-to-end. **To confirm:** search run history for an embedded run with a non-empty `view_label`, or run one with "standalone view" in the prompt.

3. **Should the embedded child BC register itself as a parent entity (the way `backend/pipeline.py:781-792` does)?**
   *My suggested answer:* No — leave it out. *Reasoning:* the registry's `fk_field` contract is "the single FK field the embedded child BC links on" (`backend/qad_entity_registry.py:22-23`), and `infer_fk_field` picks the first non-domain PK (`:125-134`), which for an embedded child would return the *parent's* FK (PK #2) rather than the child's own identifier — producing a broken parent definition. The omission looks deliberate, though no comment says so. **To confirm:** the commissioner's intent for nested extensions.

4. **Is `relationID`'s hardcoded prefix `"8c9676c6-0c12-13a3-f114-"` (`backend/builders/embedded_builder.py:278`) safe?**
   *My suggested answer:* Probably safe but should be a full `uuid4`. *Reasoning:* only the last 12 hex chars vary, so collision risk is ~2^48 — negligible in practice, but the fixed prefix is almost certainly a copy from one captured working request rather than a QAD requirement (nothing in the file says QAD constrains the prefix). **To confirm:** POST a relation with a plain `uuid4()` `relationID` against a disposable BC and check QAD accepts it.

5. **For Phase 5, should the embedded flow gain event-handler generation at all — and if so, whose view does the handler target?**
   *My suggested answer:* It would need a new builder, not the existing one. *Reasoning:* `build_event_handler_payload` hardcodes `viewURI = f"urn:view:viewmeta:{MODULE}.{bc_pascal}"` (`backend/builders/event_handler_builder.py:8`) — i.e. the *child's* own maintenance view, which for a grid-only data extension may not be the surface where validation must run; targeting the parent's view would require both a `viewURI` parameter and the parent-metadata read the flow does not currently perform (Q3). *Also:* the fixed `eventHandlerType:"BEFORE"` (`:30`) and the `Maint_BEFORE` module name baked into the prompt (`backend/agents/prompts.py:259`) mean adding a second timing touches both the builder and the prompt. **To confirm:** the commissioner's target surface (child grid vs. parent form) and whether QAD accepts an `eventHandlerV2` whose `viewURI` points at a standard QAD parent view.

---

## A3. Server-side (SSS) flow ✅ *citation-verified*

1. **Does QAD's `POST /qad-central/api/qracore/sss` return a non-2xx on rejection, or a 200 with an error body?** Unresolvable from these files — nothing captures a real response. *My suggested answer:* assume 200-with-error-body is possible and treat `deploy.py:94-97` as insufficient. *Reasoning:* every other QAD API in this codebase returns structured errors inside a 200 (`pipeline.py:689-692` exists precisely for that, via `is_qad_success`), and `deploy.py:12-14` admits *"the live deploy path is not yet verified against QAD"*. **To confirm:** one deploy against a disposable QAD app with the raw response logged.
2. **What do `appSeq=0` and `fileSeq=3` mean, and is `fileSeq=3` a file count or an index?** Hardcoded at `deploy.py:45` with no explanation. *My suggested answer:* `fileSeq=3` is the number of parts in the multipart body (3 files) and `appSeq=0` is a single-app-revision marker. *Reasoning:* the value 3 exactly matches `dist_files()`'s three entries, and both were copied verbatim from the `qad-sss-vscode` extension (`deploy.py:3-7`). **To confirm:** capture the extension's own request in a proxy, or grep the extension source.
3. **Should `sss_workspace` be committed at all?** It contains a 3.5.3 `node_modules/typescript` plus 2.2 MB of QAD typedefs and a machine-specific `qad-sss.config.json` (`envUrl: http://qadee.yash.com:22010/qad-central/`, `id: 126758264977`) that **disagrees with `.env`'s `QAD_BASE_URL=http://qadee.yash.com:81`**. *My suggested answer:* keep `sss_template/` as the tracked seed, gitignore `sss_workspace/`, and delete `qad-sss.config.json` from the template — nothing in the Python code reads it. *Reasoning:* repo-wide grep shows `qad-sss.config.json` is only ever *copied* (`sss_scaffold.py:34`) and never parsed, so the stale `envUrl`/`id` are inert but misleading. **To confirm:** check whether the QAD VS Code extension is expected to run against this same folder.
4. **Is `/docs/setup-sss` meant to be a backend route or an SPA route?** `core/config.py:50` defines it; nothing serves it. *My suggested answer:* an SPA route that was never built; the SPA `StaticFiles(html=True)` mount (`main.py:214`) would serve `index.html` for it, so the user lands on the app, not a guide. *Reasoning:* it is described as a *"Structural route (NOT an environment-specific setting)"* at `config.py:47-50`, and `PROGRESS.md:133` treats it as a UI "Setup Guide" link. **To confirm:** ask whether a setup-guide page was ever specified.
5. **Should `auto_deploy` be removed or implemented?** It is settable via `POST /api/settings` and persisted to `settings.json` (`config.py:34,192-194`) but read by nothing except `public_status()`. *My suggested answer:* remove it. *Reasoning:* a live-but-unread "auto deploy" toggle in a product whose entire safety story is human approval is a liability — a future reader may wire it up believing it was designed. If Phase 2 wants it, it should be re-introduced deliberately with an explicit gate.
6. **Why does `readiness.py` gate on `salesgen.d.ts` alone while `health.py` requires both typedefs?** *My suggested answer:* intentional, as documented (`readiness.py:19-21`) — Purchasing is a bonus. *Reasoning:* the comment is explicit. But the consequence is undocumented: with only `salesgen.d.ts` present, `/api/sss/bcs` returns Sales BCs and works, while the health chip shows `not_configured` and `App.tsx:89` hides `SssPanel` behind the setup card — so a *working* SSS is rendered unreachable. **To confirm:** ask whether the frontend should gate on the 503 instead of on health.

---

## A4. QAD endpoints ✅ *citation-verified*

1. **Are rows 4 and 6 one endpoint or two?** They share the path `entitymetadatas`; only the query differs (`viewUri` alone = create, `entityURI` + `viewUri` = update). *My answer:* register them as **two** registry entries (`entitymetadatas.create`, `entitymetadatas.update`) sharing one path template. *Reasoning:* the query params differ, the payload shapes are unrelated (constructed vs GET-echo), and the phase-1 registry has to express "which params does this call need" — collapsing them would force a param-set union that is wrong for both.

2. **Should `core.qad_session` become the single auth module, deleting `qad_client.get_token`?** *My answer:* yes, and Phase 1 is the right moment. *Reasoning:* `backend/qad_client.py:4-7` already names this as the deferred migration; `get_bearer_token` is the better implementation (encoded `params=`, `QadAuthError` with user-facing text, `log_operation`); and `qad_client.py:44-49` puts an unencoded password in a URL, which is both an encoding bug and a log-leak risk. Behavioural delta to check first: `get_token` raises `httpx.HTTPStatusError` and callers interpolate it raw, so swapping in `QadAuthError` changes the SSE error text at `backend/pipeline.py:440` and 6 sibling sites.

3. **Is `qracore/lookups` in scope for the registry given it has never been POSTed?** *My answer:* include it, flagged `verified: false`. *Reasoning:* the endpoint string is a real code literal (`backend/core/lookup_generator.py:70`) and Phase 1's exit criterion is "no endpoint literals remain anywhere in code" — leaving it out leaves a literal behind. `backend/core/lookup_generator.py:16-53` documents exactly which fields are unconfirmed; carry that into the registry entry rather than dropping the row.

4. **What owns `appSeq=0&fileSeq=3` (`backend/sss/deploy.py:45`)?** Not derived from anything in the repo; `backend/sss/deploy.py:4-13` says the multipart upload was kept "BYTE-FOR-BYTE as the aux-agent version" because the live path is unverified. *My answer:* treat them as endpoint-template defaults in the registry, not config keys, until an SSS deploy is verified against a live server. *Reasoning:* [INFERRED] from the vscode-extension lineage that they are fixed protocol constants; nothing in the repo confirms they ever vary. Confirmation requires one successful upload with the values altered.

5. **Should `com.extensions.customapp` (7 separate `MODULE` constants) be folded into the endpoint registry or a separate identity registry?** *My answer:* separate — an `identity`/URN-template registry keyed off `qad_app_uri()`, distinct from the endpoint registry. *Reasoning:* these are payload identities, not endpoints; and `QAD_APP_URI` config already exists and is already honoured by SSS, so the fix is to make the builders read it too. Note the divergence to reconcile: `backend/builders/deploy_builder.py:4` defines `DATASTORE_URI` while `backend/builders/embedded_builder.py:337` re-hardcodes the same string inline.

6. **Is the committed hostname in `backend/sss_template/qad-sss.config.json:2` (`http://qadee.yash.com:22010/qad-central/`) safe to leave?** No Python reads it (A4.5 #4), but `backend/core/sss_scaffold.py:34-38` copies it into every scaffolded workspace. *My answer:* blank the `envUrl` value in the template. *Reasoning:* it is a live-looking internal host committed to a repo and it can silently disagree with `QAD_BASE_URL`; since nothing reads it, blanking it is behaviour-neutral. I did not verify whether an external `qad-sss` CLI run inside `sss_workspace/` would read it — that is the one way this could regress.

7. **Should `deployCheckForWarnings` responses be checked?** Both pipelines discard them (`backend/pipeline.py:739`, `backend/pipeline_embedded.py:299`). *My answer:* capture and surface as a non-fatal `warning` SSE event, do not gate the deploy. *Reasoning:* the step is named "check for warnings", so warnings are expected and must not fail a run; but silently discarding the response means a genuine `submitResult` error there is invisible. The SSE `warning` frame already exists (`backend/routers/client_extensions.py:156`), so the plumbing is there.

---

## A5. Auth flow ✅ *citation-verified*

1. **Is `core/qad_session.get_bearer_token` dead by intent or by accident?**
   Suggested answer: accident-then-deferred. `backend/qad_client.py:4-7` explicitly calls the migration "deferred", and `backend/core/qad_session.py:2` already claims to be the single place. Reasoning: the SSS half of the same module *was* wired in (`backend/sss/deploy.py:25`), so only the Bearer half was left behind. Recommend making `get_bearer_token` the sole implementation as the first Phase 1 change, since it already encodes params correctly.

2. **Does the Adaptive QAD env expose the same `/qad-central/oauth/token` password grant and `/qad-central/api/login`?**
   Suggested answer: assume yes for QAD Adaptive on the same platform, but treat it as unverified. Reasoning: nothing in these files documents a second env; `backend/.env.example:6-7` only says the base is host:port. Confirm by curling both paths on the Adaptive host before designing the config shape.

3. **Is there a `settings.json` legacy QAD block in the live file that would silently win?**
   Suggested answer: no. Key extraction on `backend/settings.json` shows only `qad_app_dir`, `qad_app_uri`, `openai_model` — no `qad_server_url`/`qad_username`/`qad_password` — so the fallback at `backend/core/config.py:113-121` is currently inert. Reasoning: key names read directly; values not inspected. Worth re-checking on any machine other than this one.

4. **Should Phase 1 keep one shared APEX login across both environments, or scope sessions per environment?**
   Suggested answer: keep one login, add an explicit `env` field to `RunRequest`/`DeployReq` and a per-env credential block in config. Reasoning: the JWT has no room for env scope today (`backend/core/auth.py:69-73`) and there is no user table to hang per-env grants off (`backend/database.py` has only `runs` and `parent_entities`), so env selection belongs in the request, not the token.

5. **Does `hmac.compare_digest` on `str` actually 500 on non-ASCII input here?**
   Suggested answer: yes. Reasoning: `backend/core/auth.py:59-61` passes `str` unconverted, and the stdlib restricts `str` comparison to ASCII-only. Cheap fix: `.encode("utf-8")` both sides. Confirm with one POST to `/api/auth/login` containing a non-ASCII character.

6. **Is the unauthenticated API surface acceptable once a production QAD env is reachable?**
   Suggested answer: no — add `Depends(get_current_user)` to `/api/run`, `/api/sss/generate`, `/api/sss/deploy` before Phase 1 ships, and attach `Authorization` in `frontend/src/features/client_ext/api.ts:78` and `frontend/src/features/sss/api.ts:53`. Reasoning: `backend/core/auth.py:16-18` names this a follow-up, and today a bare `curl` to `/api/sss/deploy` writes to QAD.

---

## A6. Run-state persistence ✅ *citation-verified*

1. **Does an aborted/refreshed run really leave zero rows?** — My reasoning is in §A6.2 (save is positioned after the `async for`; `CancelledError` is not caught by the `except Exception` at `client_extensions.py:184`). *My suggested answer: yes, zero rows.* Confirm with one opt-in live test — start a run, refresh at step 5, then `select count(*) from runs` before/after. I did not run it because it would POST to QAD (`backend/pipeline.py:435` fires at step 3) and `PROGRESS.md:74` records the standing rule: "no QAD-writing verification without explicit opt-in."
2. **Which "Phase 3" is meant?** — `PROGRESS.md:113-140` describes a *completed* "Phase 3 — Frontend shell + settings/secrets migration (COMPLETE & APPROVED)". *My suggested answer: the audit's "Phase 3" is a new roadmap item unrelated to that one, and the numbering collides.* Worth renaming in PHASE0_AUDIT.md to avoid ambiguity against `PROGRESS.md`.
3. **Where should approval gates sit?** — Not answerable from the files; no gate exists. *My suggested answer: before each irreversible QAD write — steps 3, 7, 11, 13, 14 (`backend/pipeline.py:435, 597, 685, 709, 741`) — with step 3.5 dropdown wiring (`:529`) folded into the step-3 gate since it is a continuation of the same entity save.* Needs a product decision.
4. **Should step outputs be stored inline in `run_steps.output_json`, or externalised?** — `ts_code` (`backend/pipeline.py:649`) and `js_code` (`:674`) can be large; the request-side cap is 200,000 chars (`backend/models.py:8`, `_MAX_MESSAGE_CHARS`) and `backend/routers/sss.py:21` uses the same figure for TS. *My suggested answer: inline in SQLite is fine at this scale (the whole DB is 168 KB after 19 runs), but add a per-column length cap and a retention/prune policy, since `runs` currently has none and `list_runs` only clips the read side (`LIMIT 50`, `backend/database.py:72`).*
5. **Is `history.db.bak-tier1` still needed?** — It holds one run absent from the live DB (§A6.1). *My suggested answer: keep it read-only until Phase 3's migration is proven, then delete; it is gitignored and its 9 rows are a strict subset of the live DB except that one row.* Confirm with whoever created it.
6. **Multi-user semantics.** Auth is a single hardcoded admin (`backend/routers/auth.py:4`) and `runs` has no owner column. *My suggested answer: add `created_by TEXT` to `runs` now while the migration is already being written — it is free today and a breaking backfill later.*

---

## A7. Reading artifacts back from QAD ✅ *citation-verified*

> **⚠️ Superseded in part.** Verification overturned this section's core conclusion. Questions 2
> and 3 below are answered by `backend/probe_parent_eh.py`, which the first pass missed: the GET
> contract on `eventhandler` **is** documented in-repo, and read-back **was** built. See
> `PHASE0_AUDIT.md` §0.4 finding 5 and Part V. The live question is now Q-L: did that probe ever
> run, and what did it return?

1. **Can `entitymetadatas` GET retrieve a pre-existing, non-AUX-created BC?**
   *My suggested answer:* Yes. *Reasoning:* `get_qad` does no filtering and `entityURI` is an opaque query param (`backend/qad_client.py:64-69`); the call site's only assumption is the `{"data":…}` wrapper and a non-empty `entityMetadatas` (`backend/pipeline.py:521-522`). Nothing ties it to freshly created entities. Confirm with one live GET using a known standard URI from `backend/qad_entity_registry.py:41-80`.

2. **Does the `eventhandler` endpoint support GET at all, and with what query params?**
   *My suggested answer:* Probably yes, filtered by `viewURI` and/or `appURI`, mirroring the POST body keys `appURI`/`viewURI` at `backend/builders/event_handler_builder.py:28-29`. *Reasoning:* every other `qracore` resource AUX touches follows a `?viewUri=urn:be:…` convention, and `entitymetadatas` demonstrably supports both verbs. This is unverified — nothing in the repo documents a GET on `eventhandler`.

3. **Was read-back ever attempted and removed, or never built?**
   *My suggested answer:* Never built. *Reasoning:* `get_qad` exists and is used, so there was no aversion to GETs; the dropdown-wiring comment (`backend/pipeline.py:503-508`) frames GET as a workaround for QAD's two-step save, not as a general capability. `PROGRESS.md` (75 KB, not read in full for this section) would settle it definitively.

4. **Is the `berelation` write (`backend/pipeline_embedded.py:277-280`) preceded anywhere by a read of existing relations?**
   *My suggested answer:* No. *Reasoning:* the two `get_qad` call sites are fully enumerated above and neither targets `berelation`; `build_relation_payload` is fed only local values — `bc_pascal`, `fields`, `parent_entity_code`, `parent_entity_uri`, `fk_field_code` (`backend/pipeline_embedded.py:269-275`), all sourced from the local registry.

5. **Does the SSS upload endpoint (`?appSeq=0&fileSeq=3`) overwrite or version prior uploads?**
   *My suggested answer:* Overwrites at a fixed slot. *Reasoning:* both sequence numbers are hardcoded literals in the URL builder (`backend/sss/deploy.py:45`), so consecutive deploys post to an identical target; AUX never reads back to learn the next sequence. Confirm against QAD's SSS API docs or the `qad-sss-vscode` extension the module says it mirrors (`backend/sss/deploy.py:4-5`).

---

## A8. Frontend architecture ⚠️ *not verified*

1. **Which architecture for the gated run: per-step request/response, or resumable stream?**
   *My answer:* per-step request/response, modelled on SSS (`POST /api/run/{id}/step/{n}/generate` → returns artefact → user approves or sends free-text → `POST .../regenerate`). *Reasoning:* the team has already built and shipped exactly this shape in `sss/api.ts:85-99` + `ReviewDeploy.tsx`, it needs no long-lived connection, it survives a page reload, and it makes each step's artefact naturally addressable. Holding an SSE generator open across an indefinite human pause (`client_extensions.py:205-212`) invites proxy/idle timeouts and cannot survive a refresh. *To confirm:* whether any deployment sits behind a proxy with a response-idle timeout.

2. **Do we keep SSE for the non-gated steps?**
   *My answer:* yes — keep `streamPipeline` (`client_ext/api.ts:68-121`) for intra-step progress, and end each stream at a gate with a new terminal frame (e.g. `{type:"awaiting_approval", step, artifact_id}`). *Reasoning:* the streaming parser already works and users get live feedback; only the *boundary* semantics change. *To confirm:* the intended granularity — gate all 14 steps, or only the 5 currently-visible-and-consequential ones (`ProgressPanel.tsx:20`)?

3. **Which of the 14 steps actually need a gate?**
   *My answer:* the ones producing a reviewable artefact — 2 (field design), 6 (panel layout), 9 (TypeScript handler), 12 (view config). *Reasoning:* these are the four with a concrete inspectable output, and step 9's output is the same kind of artefact SSS already gates. Steps 3/7/11/13/14 are QAD writes — gate *before* them, not on them. *To confirm:* with the product owner; nothing in the files states an intent.

4. **Introduce a real state library, or extend the Context pattern?**
   *My answer:* add a `useReducer`-based `RunContext` alongside the existing `AuthProvider`, no new dependency. *Reasoning:* `authStore.tsx:1-4` records a deliberate, documented decision to avoid Zustand; the run state is one tree consumed by one subtree. A reducer gives the explicit state machine a gated run needs (`idle → running → awaiting_approval(step) → …`) without a dependency argument. *To confirm:* whether the "commissioner says Zustand" instruction is a hard requirement — if so it is a **new** dependency and a reversal of a documented decision, not a description of the codebase.

5. **Where does the free-text regenerate instruction go in the backend contract?**
   *My answer:* a new optional `feedback: str` on the per-step regenerate request, appended to that step's LLM user message. *Reasoning:* mirrors how SSS threads `prompt` through `generate(bc_name, prompt)` (`sss/api.ts:89-93`). *To confirm:* the prompt files under `backend/agents/prompts.py` (uncommitted per git status, **not read in this audit — frontend scope**) may already have a slot for this.

6. **Should step outputs be persisted, or held in server memory for the run's lifetime?**
   *My answer:* persisted, next to the existing history row. *Reasoning:* `client_extensions.py:185-197` already writes a run row; adding a `run_steps` table keyed `(run_id, step)` lets the UI reload into a paused run, which memory-only cannot. *To confirm:* the DB layer in `backend/database.py` (not read — outside frontend scope).

7. **Fix the auth gap before or during Phase 2?**
   *My answer:* before. *Reasoning:* the frontend sends `Authorization` on exactly one endpoint (`features/auth/api.ts:53`) and the backend enforces identity on exactly one (`backend/routers/auth.py:69`). An "approve & deploy" button that any unauthenticated caller can invoke by hand is a worse security posture than today's, because the UI will imply a gate that does not exist. Smallest fix: a shared `authedFetch` wrapper reading `localStorage["apex_token"]` (`authStore.tsx:22`), plus a `Depends` on the mutating routes. *To confirm:* whether the deployment is internal-network-only, which would lower (not remove) the urgency.

8. **Backend step-manifest endpoint?**
   *My answer:* yes — `GET /api/run/steps?mode=standard|embedded` returning `[{n, label, gated}]`, and delete the frontend tables. *Reasoning:* the standard/embedded label drift documented in A8.3 (embedded step 8 unrenderable; steps 1/4/5 mislabelled) is already live in the product and is caused solely by duplication. *To confirm:* nothing — this one is unambiguous from the files.

9. **Are the unrendered `warning` / `lookup_candidate` / `lookup_needs_review` events meant to be shown?**
   *My answer:* yes, and a gated UI is the natural home — `lookup_needs_review` (`pipeline.py:93-114`) is literally a request for human review, carrying `reason`, `source_table`, `target_field`, `evidence_line`, `notes`, `needs_verification`. *Reasoning:* the backend goes to real trouble to build these payloads and the frontend discards all of them (`ProgressPanel.tsx:52`). That looks like an unfinished feature, not a decision. *To confirm:* with whoever wrote Phase 11 (`backend/core/lookup_detector.py`, untracked per git status).

---

## A9. Docs-bundle loader ⚠️ *not verified*

1. **Is the ~61k-token `client_extension_event_handler` bundle actually helping, or is it drowning the instructions?** It is injected in full into both step 8 and step 9. — *My suggested answer:* it is over-large; `UI elements list of events and Properties_Functions` alone is 117 KB and `Event handlers API reference.txt` is 90 KB. *Reasoning:* the entire prompt-critical API surface is already restated as 11 explicit rules in `backend/agents/prompts.py:280-333`; the bundle is mostly redundant reference. I would measure with a tokenizer and A/B one run with the bundle trimmed to `UI Event Handlers` + `TypeScript recommended coding standards` before adding a fourth bundle on top.

2. **Should a Java bundle reuse the `{QAD_DOCS_CONTEXT}` placeholder name?** — *My suggested answer:* yes. *Reasoning:* the substitution is per-prompt-string, not global; two prompts can both carry `{QAD_DOCS_CONTEXT}` and receive different bundles (this already happens — `business_component` vs `client_extension_event_handler` vs `server_side_rule`). Introducing `{JAVA_DOCS_CONTEXT}` would fragment the convention for no gain.

3. **Does the Java docs corpus exist in `.txt` Confluence-export form?** Nothing in this repo contains it. — *My suggested answer:* it must be exported into the same 3-header-line `.txt` shape before step 2 of A9.6 is meaningful. *Reasoning:* the loader has no other reader; a `.md`/PDF corpus would need a loader change (`backend/core/qad_docs_loader.py:92`) that is currently a single-glob edit but would then need per-extension parsing.

4. **Should the standard (non-embedded) pipeline's `FIELD_CREATOR` also get the `business_component` bundle?** Today it gets nothing (`backend/pipeline.py:419`). — *My suggested answer:* probably yes but not in Phase 6. *Reasoning:* the embedded pipeline already grounds the same class of decision with `business_component` (`backend/pipeline_embedded.py:123`); the asymmetry looks unintentional rather than designed. But it adds ~23k tokens to a step that currently works, so it should be a separate measured change.

5. **Was `VALIDATOR_AND_CORRECTOR`'s import into `pipeline_embedded.py` (`backend/pipeline_embedded.py:10`) meant to be used?** No call site exists in that file. — *My suggested answer:* dead import; the embedded pipeline has no auto-fix step (its `STEP_LABELS[4]` is "Handling duplicates & auto-fix", `backend/pipeline_embedded.py:36`, so the step is *named* but not LLM-driven). *Reasoning:* worth confirming with the author before deleting, since the label implies the step was planned.

6. **`requirements.txt:3` pins `openai==1.55.3` but the running interpreter has `1.59.6`.** — *My suggested answer:* bump the pin to match, or pin the venv down. *Reasoning:* retry/timeout defaults I cite (2 retries, 600 s) were read from the *installed* 1.59.6; if a deploy honours the pin the numbers could differ. Low risk, but it means my A9.5 retry figures describe the dev machine, not necessarily production.

---

## A10. Settings and config registry ⚠️ *not verified*

1. **Should the legacy `settings.json` credential fallback (`backend/core/config.py:110-121`) be deleted in Phase 1?**
   *My suggested answer: yes, delete it.* Reasoning: it is the only mechanism by which a QAD password can enter a git-tracked file, the current `settings.json` uses none of the four legacy keys (`backend/settings.json:1-5`), and its own comment says it exists only "until creds are migrated into .env" — `.env` lines 4-7 show that migration is already done.

2. **Is defect D2 (`qad_app_dir` editable in the UI but never persisted) intended, or a regression?**
   *My suggested answer: a regression.* Reasoning: `UiSettingsUpdate` explicitly declares `qad_app_dir` (`backend/routers/settings.py:26`) and `SettingsPage.tsx:138-145` renders a labelled input for it; the only thing missing is the string in `_UI_KEYS` (`backend/core/config.py:34`). That reads as an omission, not a deliberate block. Confirm by asking whether the SSS app folder is meant to be operator-editable at runtime — if yes it belongs in `_UI_KEYS`; if no, remove the field and the input.

3. **Should `qad_base_url` remain in `_UI_KEYS` (`backend/core/config.py:34`) at all?**
   *My suggested answer: remove it.* Reasoning: it is unreachable via the API today (defect D1), the UI already renders it read-only with the note "Credentials are configured in `.env`" (`SettingsPage.tsx:123,131`), and in the proposed classification it is DYNAMIC/environment-owned — which argues for `.env`-only.

4. **What is `id: <redacted>` in `backend/sss_template/qad-sss.config.json:3`?**
   *My suggested answer: a QAD-instance-issued app/deployment sequence identifier, environment-specific, and it should move out of the tracked template.* Reasoning: it sits beside `envUrl` and `appURI` in a vendor config file. I could not confirm this — nothing in the Python source reads `qad-sss.config.json` (the scaffolder only `shutil.copy2`s it, `sss_scaffold.py:37-38`). Confirm with whoever generated the file from the QAD SSS CLI.

5. **Is `auto_deploy` (`backend/core/config.py:103`) dead by design or an unfinished feature?**
   *My suggested answer: unfinished, and it should be dropped from the registry until there is a consumer.* Reasoning: it is hardcoded `False`, has no env var, has no UI control, and appears only in `public_status()` (`:176`) and the TS types (`api.ts:34,46`). Zero read sites in backend logic.

6. **Should the Docker `.env` trap be fixed by making `core.config` fall back to `os.environ`, or by mounting `.env` as a volume?**
   *My suggested answer: make `_env()` merge `os.environ` on top of `dotenv_values(ENV_PATH)`.* Reasoning: it fixes container, Kubernetes, and CI in one change; keeps `.env` out of the image (`.dockerignore:13-15` is correct as written); and matches what `main.py:19` already implies. The cost is losing live no-restart pickup for env-supplied values — but those are precisely the ones a container redeploy replaces anyway. Needs sign-off because it changes the documented precedence in `backend/core/config.py:4-10`.

7. **Should `backend/settings.json` stay git-tracked?**
   *My suggested answer: no — ship `settings.json.example` and gitignore the live file.* Reasoning: it is a runtime-mutable file (`backend/core/config.py:195` rewrites it on every UI save), so every operator save shows up as a dirty working tree, and the legacy-fallback path (Q1) makes tracking it a standing secret risk. Counter-argument to weigh: it currently carries `qad_app_uri` and `openai_model`, which I classified STATIC in A10.5 — those genuinely want to be in git, just not in the same file as anything writable.

8. **Does `/docs/setup-sss` (`backend/core/config.py:50`) still need to exist as a URL constant?**
   *My suggested answer: keep the constant but reclassify it as a UI hint, not a route.* Reasoning: I found no route registered at that path anywhere in `backend/routers/` or the frontend, and `PROGRESS.md:36` records that the "Setup Guide" was deliberately changed to an in-app toggle button with "no navigation". The string is still emitted to clients at `core/health.py:82,90,98,108` and `routers/sss.py:133`, so removing it is a breaking API change; confirm whether the frontend keys off its presence or its value.

---

## A11. Uncommitted work in flight ⚠️ *not verified*

1. **Should the three untracked Phase 11 files be committed before anything else?**
   Suggested answer: yes, and as the very next action. Reasoning: `backend/core/progress_parser.py:22` imports `core.lookup_detector` at module scope, so the tracked tree as it stands cannot import `main` — a clone would break. PROGRESS.md:15/:57 already call Phase 11 done, so the repo is claiming a state it does not contain. [CONFIRMED premise: the import is unconditional and the file is untracked.]

2. **Is `frontend.zip` (19 MB, untracked, not gitignored) meant to be in the repo?**
   Suggested answer: no — add it to `.gitignore`. Reasoning: `.gitignore:44` already ignores `frontend/dist/` and `.gitignore:57-58` shows the author is size-conscious about `node_modules_typescript/`. A 19 MB zip dated Jul 22 next to the live `frontend/` tree reads as a manual backup. I cannot confirm intent from the files. [INFERRED]

3. **Was there ever a Phase 10, and is Phase 11's number a placeholder?**
   Suggested answer: Phase 10 was likely planned and folded away like Phase 5 was (`PROGRESS.md:52`, "Superseded — folded into Phase 7"), but unlike Phase 5 nobody recorded it. Reasoning: the status table (`:42-57`) is otherwise contiguous 0→9 and Phase 5 sets the precedent of leaving a row with a superseded note. Nothing in the repo confirms this. [INFERRED]

4. **Should `lookup_candidate` / `lookup_needs_review` / `lookup_summary` / `warning` be rendered in the UI, or is log-only the intended end state?**
   Suggested answer: they were intended to be rendered — `PROGRESS.md:316-317` insists on "surfaced **visibly** … not just a silent dict flag", and `pipeline.py:88-101` goes to real trouble to emit a second event purely for human visibility. My reading is that the backend half landed and the frontend half was never started (`api.ts:6` has no lookup types, `PipelineSummary` has no `lookups` key). Confirm by asking whether a frontend Phase 11 task exists that PROGRESS.md doesn't record. [INFERRED, from the mismatch between doc intent and `frontend/src` grep returning zero hits.]

5. **Given `_needs_verification` can never be empty (`lookup_generator.py:236`), is the `payload_gap` event meant to fire on every single static lookup?**
   Suggested answer: probably not — the intent at `pipeline.py:91-92` (`if needs:`) reads as "warn only when something is actually missing", and the unconditional append at `:236` defeats that. A cleaner shape would separate "omitted-by-design internals" from "missing inputs". But this is currently harmless because nothing renders the event. Worth deciding before the UI is built. [CONFIRMED that it always fires; INFERRED that this was not the intent.]

6. **Is `pipeline.py:187` (`if not model.startswith("gpt-5")`) live code or dead?**
   Suggested answer: dead today — `MODEL_MATRIX` (`:136-140`) contains only `gpt-4o` and `gpt-4o-mini`, and I found no override path in `pipeline.py`. It is forward-compat scaffolding. Confirm by grepping `core/config.py` for a model-override key that could reach `_llm`'s `model` argument; I did not audit `config.py` in this pass. [INFERRED]

7. **Does the "restart the running backend" action at `PROGRESS.md:17` still apply?**
   Suggested answer: yes, and more so than when written — every Phase 11 change plus the step-6, step-3 and paste-detection fixes are uncommitted working-tree edits, so any long-running backend process started before them is serving stale code. I cannot observe process state from the filesystem. [INFERRED]

8. **Should `PROGRESS.md:267` ("no `Dockerfile` in the repo") be corrected, or left as a dated Phase 8 record?**
   Suggested answer: leave the Phase 8 line as history but add a one-line "superseded by commit `f9a4111`" note, matching how `PROGRESS.md:36` handles the resolved Setup Guide item with strikethrough + **RESOLVED**. The file already has a convention for this. [INFERRED, from the existing strikethrough precedent at `:36`.]

---

## B1. Adaptive Docs — event handlers (Phase 5) ⚠️ *not verified*

1. **Can Primary and Post both handle the same embedded grid?** *My answer: probably yes.* Reasoning: each timing is a **separate module with separate class instances** (`[C7]:427/466/625`), and `ViewGridsToHandleList` is an instance property of each module's own main handler (`[GRIDVH]:113-115`). The controller instantiates each module independently, so each should get its own `createViewGridTSHandler` pass. **[INFERRED — this is the highest-risk inference in this document.]** Settle with test 6.1 before Phase 5 design is frozen.

2. **Is the AUX target BC a "platform BC in the same app"?** *My answer: no — AUX writes into `com.extensions.customapp` (`event_handler_builder.py:3`) while parent BCs are QAD-owned (e.g. `com.qad.erp.base…` per `[EX2]:7`), so Pre/Post is available.* Reasoning: `[FBEH]:89` — different app → Pre and Post allowed. **[INFERRED for the specific Phase 5 parent; CONFIRMED as a rule.]** Verify by checking whether the New button in Form > Event Handlers offers a Timing dropdown on the actual target BC (`[C7]:443` — the dropdown's presence *is* the signal).

3. **Should AUX switch from `BEFORE` to `AFTER` for Phase 5?** *My answer: yes, AFTER (Post).* Reasoning: to populate embedded-grid fields you want the parent's own logic and data binding to have already run; `[FBEH]:103` — Post "runs after the existing application code". `[EX2]:8` (the only QAD-authored example of extending a standard BC's UI) uses Post. Current code is `BEFORE` (`event_handler_builder.py:30`). **[INFERRED from doc intent — needs a product decision, not just a test.]**

4. **Which event should drive "parent field changed → populate embedded grid"?** *My answer: `onFieldChange` on the **form** handler, delegating into the grid handler via a main-handler reference.* Reasoning: this is the exact documented pattern, stated because "these fields change events fire in the form handler and not in the grid handler" (`[EX12-B]:111`), wired at `[EX12-B]:128-130,154-170`. **[CONFIRMED pattern; INFERRED that it applies unchanged at Post timing.]**

5. **Which event for "another parent event fires"?** *My answer: `onBindData` for record-selection/refresh, `onAutoGridNewButtonClick` for new-row defaulting, `onBeforeUpdate` for save-time cross-checks.* Reasoning: `[C7]:349`, `[APIREF]:281`, `[C7]:548` respectively. **[CONFIRMED as event semantics; INFERRED as the right choice for Phase 5.]**

6. **Do we need a read-back before writing?** *My answer: yes, and it is buildable today.* Reasoning: `fetch(appURI, viewURI, eventHandlerType, appliesTo)` exists (`qracoregen.d.ts:2009`), `get_qad` already targets the right prefix (`qad_client.py:64-66`), and `[FBEH]:90` warns "the developer can edit and delete any Event Handler without any restrictions" — meaning a blind POST could clobber. **[CONFIRMED that the operation exists; INFERRED that the REST shape is a GET on the same `/api/qracore/eventhandler` path.]** Settle by capturing the network call the platform itself makes when the Event Handlers grid loads.

7. **Is `[C7]:501`'s "Timing | Pre" a transcription error?** *My answer: yes.* Reasoning: the same example is instructed as "Select Post timing" (`[C7]:446`), rendered with the Post tooltip (`[C7]:461`), and its module is `Maint_AFTER` (`[C7]:466`). **[INFERRED — three-to-one on internal evidence.]**

8. **Is `[C7]:174` ("ViewGridTSHandlerV2 — Base class for the ViewForm event handlers") a copy-paste error?** *My answer: yes, it should read "ViewGrid".* Reasoning: contradicted by `[C7]:130-131`, `[C7]:683`, and `[GRIDEV]:5`. **[INFERRED, high confidence.]**

9. **Does the browse handler matter for Phase 5?** *My answer: no.* Reasoning: `[CLISCR]:6` — client scripts "can only act on UI events of the maintenance view, not the browse part of a hybrid view"; embedded grids live on the maintenance form. **[CONFIRMED scope statement; INFERRED that Phase 5 needs nothing from the browse handler.]** Note this also means the browse-handler documentation gap (6.5) is **not** on the Phase 5 critical path.

---

## B2. Adaptive Docs — Java extensions (Phase 6) ⚠️ *not verified*

1. **Does the undeploy palette command actually exist in 1.0.10?** *Suggested:* yes as a registered VS Code command, no as a server operation — the deck's palette screenshots (`DOC:634`, `DOC:761`) are UI evidence, and a decompile hunting HTTP calls would legitimately report "no undeploy" if the handler is local-only or stubbed. *Confirm by:* grep the VSIX `package.json` `contributes.commands` for an undeploy id and follow its handler. Until confirmed, the generator must not emit undeploy tooling.
2. **`java.version` — 1.8 or 17?** *Suggested:* the POM targets **1.8** (confirmed fact) while the documented toolchain is JDK **17**; the JDK-8 screenshots (`DOC:290`, `DOC:312`) are stale leftovers from an earlier revision of the same deck. Generator should emit `1.8` and require JDK 17 at build time. *Confirm by:* reading the scaffolded `pom.xml` from a real `Init app`.
3. **Which package does the extension class itself declare?** *Suggested:* `com.extensions.training` (parent of the generated `com.extensions.training.training` at `DOC:711`), matching the `training` folder instruction at `DOC:664`. *Confirm by:* line 1 of the handout `Training.java`, which is cropped out of this deck.
4. **Where do `@Extension`, `Output`, and `TrainingBaseService` live?** *Suggested:* `Output` is `com.qad.ipc.dto.Output` by direct symmetry with `com.qad.ipc.dto.InputOutput` (`DOC:714`); `TrainingBaseService` is in the app-generated tree, most likely `com.extensions.training.training.TrainingBaseService` alongside its DataSet/Record (`DOC:711-712`) — which would also explain why it needs no visible import if the class sits in that package; `@Extension` is in a QAD framework package, plausibly `com.qad.ipc.*`. *Confirm by:* `jar tf` / javap on the dependency jar.
5. **Which class declares `addValidationError` / `throwAddedValidationErrors`?** *Suggested:* a shared base above every `<BC>BaseService` — the commissioner's `BaseBC`. The doc's unqualified `throwAddedValidationErrors()` at `DOC:728` proves only inheritance, not the level. *Confirm by:* javap the class hierarchy.
6. **Do `fetch` / `exists` / `delete` really exist as overridable hooks?** *Suggested:* yes (confirmed set), and the deck simply never exercises them. Their wrapper types are the real unknown — `fetch`/`exists` plausibly take `InputOutput` or a filter-plus-`Output` pair rather than the `Output<T>` shape used by `initialize` (`DOC:720`). *Confirm by:* javap `<BC>BaseService`.
7. **Is `getTtTraining()` guaranteed non-empty in `initialize`?** *Suggested:* yes for `initialize` (the platform hands you exactly one fresh row, which is why `[0]` is safe at `DOC:722`), but **not** guaranteed for `create`/`update`, where `[0]` at `DOC:742` is an example-grade shortcut. The generator should iterate the array and null-guard rather than copy `[0]`. *Confirm by:* multi-row save test.
8. **What are the `config/` and `data/` scaffold folders for?** *Suggested:* `config/` holds the plugin's per-project connection settings (env URL / client id / app URI captured during Init at `DOC:553-604`) and `data/` holds the downloaded app metadata; `lib/` holds the dependency jar. Purely positional reasoning from the Init flow — the doc never says (`DOC:618`). *Confirm by:* inspect a scaffolded project on disk.
9. **When multiple extensions exist for one BC (`DOC:97`), what determines execution order?** *Suggested:* undefined/unspecified — likely load order of the deployed jars. The generator should assume no ordering guarantee and never emit two extensions for the same BC in one app. *Confirm by:* deploy two extensions on one BC and observe.
10. **Deploy semantics — whole-jar or incremental?** *Suggested:* whole-jar replacement keyed by `App-Name` in the manifest (which is why the manifest carries it), so each deploy fully supersedes the previous jar for that app. Doc is silent (`DOC:824-826`). *Confirm by:* deploy a two-class jar then a one-class jar and check whether the removed class's behavior disappears.

---

## B3. Adaptive Docs — BCs, extensions, relations, formulas, lookups ⚠️ *not verified*

1. **Does AUX need an explicit Browse-creation step?** The docs make Browse a first-class artifact created before the View (C2:969–983, C3:1073–1081), and AUX has no such step (`backend/pipeline.py:145-160`).
   *My suggested answer:* Probably not as a separate LLM step, but AUX must be creating the BEBrowse row somewhere. My reasoning: `backend/builders/view_builder.py:110,160,166` emit a browse URI of exactly the documented shape, and the pipeline deploys successfully enough to have shipped. Most likely the view-registration POST to `urn:be:com.qad.qra.meta.IViewResourceMetadata` (`backend/pipeline.py:710`) carries the browse definition inline. *To confirm:* read the payload built by `view_builder.py` in full and check whether it includes a `fields`/`columns` list (a real browse definition) or only URI references (a dangling pointer).

2. **Is `urn:be:{MODULE}.{bc}.I{bc}` (AUX) correct, or should it be `urn:be:{MODULE}.I{bc}` (docs' standard-BC shape)?**
   *My suggested answer:* AUX's form is correct for extension BCs. My reasoning: the docs' only fully-legible `urn:be:` examples are QAD-shipped components in deep packages; the one custom example is truncated to `urn:be:c` (C3:921). The `urn:bd:com.extensions.training.Training.Training` example (C3:2674) shows the platform *does* insert a per-BC path segment for custom artifacts under `com.extensions.<app>`, which supports AUX's shape. *To confirm:* `backend/qad_docs/App Development Concepts/Use of URIs in the Platform.txt` or a live GET of a deployed custom BC.

3. **Where does a lookup's filter/qualifier live?** AUX's `lookup_detector` classifies candidates as static / dependent / cascading (`backend/core/lookup_detector.py:317-394`), but neither doc shows any filter surface on the Lookup panel — its only fields are `Related Business Component, Browse, Relationship, Relationship Label, Visualize as Drop-Down List` (C3:1746).
   *My suggested answer:* the filter lives on the **Browse**, not the Lookup — the docs say "Choose the Browse that will be used with the Lookup" (C3:1800), and the Browse editor has a `Predefined Search Criteria` section (C3:2361) plus `View Browse Query` (C3:1089). So a "static" lookup filter is expressible as a browse with predefined criteria; a "dependent"/cascading one probably is not, which would justify AUX routing those to `lookup_needs_review` (`backend/pipeline.py:107`). *To confirm:* `backend/qad_docs/App Development Tools and Resources/Lookup Definitions view.txt`, which the earlier grep shows documents a browse-URI field for lookups.

4. **Is `Released` reachable for a custom BC, and does AUX ever need it?** Docs show custom BCs only in `Initial` (C3:919) and `Suspended` (C2:1283); every `Released` row is QAD-shipped (C2:715–726).
   *My suggested answer:* `Released` is a QAD-internal promotion state tied to shipping a component in a product release, irrelevant to extension BCs, which stay effectively "Initial + deployed". Reasoning: the docs' own lifecycle (Initial → Deploy → Revert → Suspended → Initial) never passes through it, and the deploy step never mentions it. *To confirm:* a status-model doc or a GET on a deployed custom BC's `Status`.

5. **Does the `activity_feed_update` OS-script prerequisite (C3:2291–2297) apply to AUX-generated BCs?** AUX has no formula step today, so this is latent.
   *My suggested answer:* only if/when AUX starts generating formula fields; it is a **per-environment one-time activation**, not per-BC ("could be inactive if never used on this environment", C3:2291). *To confirm:* whether the target environment has ever run it.

6. **Is the `Formula` field-reference token derivable, or must it be picked through the UI?** Only one instance exists: `AVERAGE([_com_extensions_training_Students.score])` (C3:2226), and the docs always obtain it via `Include Field` → Select Relationship → Select Fields (C3:2192–2216).
   *My suggested answer:* derivable as `_` + app/BC package with `.`→`_` + `.` + camelCase field name — but with one sample this is a guess, and the leading `_` and the camelCase downshift of `Score`→`score` are exactly the kind of detail that breaks silently. *To confirm:* a second formula example, or the platform's formula-parser docs.

---

## B4. Adaptive Docs — platform tools, data administration, security ⚠️ *not verified*

1. **What are the full, untruncated OS Script names and file names for `compile_app_source...` and `create_app_metadat...`?** (C5:168, C5:170)
   *My suggested answer:* `compile_app_sources` / `create_app_metadata`, with `File` values of the same name plus a script extension. *Reasoning:* the labels are `COMPILE_APP_SOURC...` and `CREATE_APP_METADAT...`, and the sibling row `create_app_package` is shown untruncated with `File` = `create_app_package...` (same stem). *To confirm:* widen the OS Script and File columns on the OS Scripts screen.

2. **Does executing `compile_app_source` (Server) and `create_app_metadata` via the OS Scripts screen exercise the same code path as the in-BC "Source File Generation" panel and whatever the app calls "build-api-sources"?**
   *My suggested answer:* Probably yes, with the UI panel being a wrapper that submits the same OS Script. *Reasoning:* C4:1392 shows the UI `Package` action producing an Inbox notification literally titled *"OS Script Processing: Create app package"*, i.e. a UI button demonstrably dispatches the corresponding OS Script. *To confirm:* trigger Source File Generation from the BC panel and check whether the resulting Inbox notification is titled "OS Script Processing: ...". **If it is, running the OS Script directly is a viable diagnostic bypass for the HTTP 500 — because the script's own error text would land in the Inbox instead of being swallowed by a 500.** This is the single highest-value experiment suggested by these docs.

3. **What are the complete BC `Status` values and their transitions (is "Initial" the pre-deploy state)?**
   *My suggested answer:* likely `Initial` → (generate/compile) → some intermediate → `Deployed`, advanced by the `Deploy` button on the BC Deployment panel. *Reasoning:* `Deployed` is confirmed as a terminal-looking value (C5:636) and `Deploy` is a confirmed button (C5:557); "Initial" as the fresh-record state is the natural complement. **This is pure inference — the docs contain zero lifecycle information.** *To confirm:* Class 1–3/6–7 guides (not in this task's scope) or the BC screen's Status dropdown/filter in the live environment.

4. **Which permission (if any) gates creating a Business Component, deploying an extension, and registering an event handler?**
   *My suggested answer:* not a BC-resource permission at all, but membership in a developer/admin role that grants access to the `Development` / `Developer` menu group and the `Development`-category OS Scripts. *Reasoning:* every permission in C8 is scoped to a runtime resource URN (`urn:be:`, `urn:view:`) for end-user CRUD; the developer surfaces (C5:159 `Developer ▾ … Development ▾`, C5:167–171 OS Scripts `Category: Development`) are menu-gated, and C8:1009 names a single `Administrator Role SuperUser`. *To confirm:* open Role Permissions for `SuperUser` vs a plain role and diff which resources appear; also expand the `APIs` child node visible in the Role Permissions tree (C8:485), which the docs never open.

5. **Does an authorization failure on a generator API call return an HTTP 403, or a 200 with a `Field | Error | Error ID` payload?**
   *My suggested answer:* both are possible, but the documented permission failures are payload-level field errors (C5:845–847, C8:684–686), so **a generator must parse the error grid and not trust transport status alone.** *Reasoning:* both permission-related failures in the entire doc set render as named field errors inside a save response. *To confirm:* capture the raw response of a deliberately under-permissioned save (e.g. an approver save with only Read granted) in the browser Network tab.

6. **On this specific environment, is package installation self-service or QAD-ticketed?**
   *My suggested answer:* if it is a QAD Cloud tenant, the deployer's pipeline must terminate at "package produced + downloaded" and hand off (C4:1404–1406). *Reasoning:* C4:1404–1408 is unambiguous for Cloud and silent for on-prem. *To confirm:* ask whether the target is QAD Cloud; if yes, the "deployer" scope should be re-cut before further engineering.

7. **Is `urn:datastore:com.extensions.extension` a fixed, shared datastore for all extensions, or per-app?**
   *My suggested answer:* shared/fixed — note it says `com.extensions.extension`, not `com.extensions.training`, on a Training BC (C5:555). *Reasoning:* every other URN on that screen is app-specific; this one is not, which suggests a single extension datastore. *To confirm:* open the Deployment panel on a BC from a different app and compare the Data Store URI.
