# Adaptive (Java) — Plan

`adaptive_java_version` generates QAD **Adaptive (Java)** artifacts. It is ported from the working
`aux_web_version` (AUX) app, and it stays **permanently separate** from it: different products,
different customers, different requirements. No merge, no mode toggle, no shared-code refactor of AUX
without explicit approval. Separation of concerns is the point.

**Working rules (from the brief — these override convenience at every point):**
1. Never guess. Read the code. Both repos are available.
2. If still unclear after reading, stop and ask — with a suggested answer and reasoning attached.
3. Distinguish `[CONFIRMED]` from `[INFERRED]` in everything reported. Never present an inference as fact.
4. Phase gates. Do not start a phase until the previous one is approved.
5. Nothing writes to QAD without an explicit greenlight. Every new write path ships dry-run by default,
   and dry-run reports exactly what it *would* send: endpoint, method, headers, payload.
6. Named deferrals, not silent omissions — record them in `PROGRESS.md`.
7. Match the reference in scope and density. Do not expand beyond what exists unless asked.
8. Verify against the filesystem, not against success messages.
9. Environment: Windows `cmd`. PowerShell is not available. Primary IDE is Antigravity.
10. Maintain `PLAN.md` and `PROGRESS.md` for cross-session continuity.

---

## The three cases

| # | Case | Today, in AUX | Adaptive target |
|---|---|---|---|
| 1 | New business component from scratch | Multi-step linear pipeline ending in deployment (`backend/pipeline.py`) | Same, under step-gated approval |
| 2 | Embedded | Embeds a grid only (`backend/pipeline_embedded.py`); generates **no** event handler | Gains event handlers + validations (Phase 5) |
| 3 | Server-side | Separate flow, already approval-based (`/api/sss/*`, `frontend/src/features/sss/`) | Ported SSS (TypeScript) → JEF (Java/Maven) (Phase 6) |

**Confirmed in Phase 0:** client-extension (event handler) generation is a set of steps **inside** the
new-BC pipeline (`pipeline.py:685`), while server-side generation is a **separate flow**
(`routers/sss.py:35`, `APIRouter(prefix="/api/sss")`). See `PHASE0_AUDIT.md` §0.3.

---

## Phases

### Phase 0 — Read-only audit ✅ **CLOSED** (owner greenlight 2026-08-10)
Produce `PHASE0_AUDIT.md` and `QUESTIONS.md`. No application code.

**Exit criteria:** all 8 required items answered with file-path/code references; inferences labelled;
zero application code. → See `PROGRESS.md` for the honest status against each criterion.

### Phase 1 — Endpoint and settings registry 🔄 **IN PROGRESS**
**Done:** config layer — `config/endpoints.json` (20 endpoints, per phase/case, each with `source`
provenance), `config/environment.json`, `backend/.env.example`. See `PHASE1_REGISTRY.md`.
**Outstanding:** owner confirmation of the static-vs-dynamic classification, then the settings panel.

Settings panel holding every endpoint and URI, **segregated by phase/case**. Real values supplied by the
commissioner — none invented. Static-vs-dynamic classification presented for confirmation, not assumed.
Environment identity (base URL, client ID, app URI) lives here. Config safe to commit is separated from
secrets that are not.

**Exit criteria:** panel exists, segregated per phase, reads and writes config, **no endpoint literals
remain anywhere in code**, static-vs-dynamic classification approved.

**Phase 0 inputs to this phase:** the endpoint inventory in `PHASE0_AUDIT.md` A4; the config audit in
A10 (including the live `dotenv_values()` Docker trap and the git-tracked `settings.json` legacy
credential fallback); the value request and proposed classification in `QUESTIONS.md` Q-H.

### Phase 2 — Step-gated approval flow (all three cases)
Each step runs, pauses, and presents **what it actually produced** — real content, not a status line.
Approve advances. Regenerate takes **free-text input** to steer the retry. After the sequence completes,
any individual step can be regenerated; doing so **re-runs all subsequent steps**, each approved again
in order. Available up to deployment only.

**Exit criteria:** all three cases run under this flow; approve advances; regenerate-with-input works;
mid-sequence regenerate re-runs downstream steps in order with approval at each.

**Phase 0 finding that shapes this phase:** this is a **blocking rewrite of the run transport**, not a
UI feature. Today `run_pipeline` is one linear `AsyncGenerator` in one `StreamingResponse` with no
pause/resume/step storage and only a terminal summary persisted. SSS already implements the target
shape. Open decisions: `QUESTIONS.md` Q-A (state library), Q-B (transport), Q-C (which steps gate),
Q-D (step manifest), Q-G (auth gap).

### Phase 3 — Run-state persistence
An in-progress, partially-approved run survives a browser refresh: approvals, step outputs, and current
position restored. Extend the existing `history.db` rather than introducing a parallel mechanism, unless
there is a concrete reason not to — which would be raised first.

**Exit criteria:** refresh mid-flow, return to the same step with prior approvals and outputs intact.

**Phase 0 finding:** an aborted or refreshed run currently leaves **zero rows** — the save happens after
the stream ends. A per-step artifact store keyed `(run_id, step)` is a prerequisite for Phase 2's UI,
not a follow-on.

### Phase 4 — Deployment gating
Deploy is terminal and runs only after explicit approval. A clear final review precedes the call: what
will be sent, where, and what it creates or replaces. After deploy, regenerate affordances lock.
**Dry-run is the default until live deploys are greenlit.**

**Exit criteria:** locking behaviour approved and implemented; dry-run verified against a real payload;
live deploy gated behind explicit approval.

**Proposal awaiting approval** (`QUESTIONS.md` Q-I): lock after BC creation (re-running dead-ends on
duplicate-entity); do **not** lock Java jar deploys (whole-jar replacement is legitimately repeatable)
but require fresh approval each time, showing full jar contents and warning when a previously-deployed
class is absent from this jar — because there is no read-back endpoint and an incomplete copy erases
silently.

### Phase 5 — Embedded: event handlers and validations on the parent BC
Validations and event handlers that make the embedded grid reactive — e.g. populating grid fields when
a parent field changes or another parent event fires.

**Firm safety constraint:** the parent/standard BC's existing event handler is never modified or
replaced. A **new, additional** handler is created alongside it.

**Exit criteria:** mechanism confirmed and reported; approach approved; handler generation working under
approval gating; parent's existing handlers demonstrably unaffected.

**Phase 0 verdict on the Pre/Post hypothesis: PARTIALLY HOLDS.** The timing mechanism is real and works
as read — three timings (Primary / Pre=`BEFORE` / Post=`AFTER`), each a separate module with its own
class instances, registered as a **new row** without opening the parent's handler. QAD documents doing
exactly this to a standard BC. Two caveats: it is **unavailable** when the active app owns the target BC
(only Primary can be created then), and **grid claiming is unproven** — whether two modules can both
claim the same `gridId` via `ViewGridsToHandleList` is documented nowhere. That last point is what
Phase 5 lives or dies on; the experiment that settles it is specified in `PHASE0_AUDIT.md` B1 §6.1 and
requested in `QUESTIONS.md` Q-F.

Also established: AUX templates a **single flat handler** and hardcodes Pre timing
(`event_handler_builder.py:30`). The platform documents **four** base classes (plus a fifth per-field
one), and the parent-field → embedded-grid pattern requires three of them wired together. Phase 5 needs
the richer structure.

**A handler read-back already exists in the repo.** `backend/probe_parent_eh.py` (untracked) GETs an
existing handler at a **standard QAD parent view**, reads its `typeScriptCode` / `javaScriptCode` /
`concurrencyHash`, POSTs it back as a no-op update, and re-GETs to confirm the hash rotated. So the GET
contract is known (`appURI`, `viewURI`, `eventHandlerType`, `appliesTo` — camelCase `viewURI`) and
`concurrencyHash` is the optimistic-locking token any update must echo. Whether it was ever run
successfully is unknown from the filesystem — `QUESTIONS.md` **Q-L**. This does not weaken the "never
modify the parent's handler" constraint: the probe fetches *our own* `BEFORE` row on the parent's view,
not QAD's Primary.

### Phase 6 — Server-side: SSS → JEF port

| AUX (SSS) | Adaptive (JEF) |
|---|---|
| discover — reads `.d.ts` typedefs from the workspace | discover — reads generated `BaseService`/`DataSet`/`Record` classes from the dependency jar |
| generate — LLM writes TypeScript | generate — LLM writes a Java class extending `<BC>BaseService` |
| `tsc --noEmit` syntax gate | `mvn compile` / `mvn clean package` |
| compile | compile |
| deploy — multipart POST | deploy — multipart POST |
| scaffold — bundles `tsc` + typedefs | scaffold — Maven project + dependency jar |

A **Java extension docs bundle** is needed for the generate step.

**Exit criteria:** discover → generate → compile working under the Phase 2 approval flow. Deploy
implemented but dry-run gated.

**Phase 0 findings:** adding a bundle is four mechanical changes (`PHASE0_AUDIT.md` A9.6), but the
loader reads `.txt` only while the Adaptive `Docs/` are `.md`, and the class-6 Java guide is **not
self-sufficient to write a class** — its code listings crop the `package` line and every import. The
bundle must be built from three sources: the deck, `javap` against the real jar, and the confirmed
decompile facts. See `QUESTIONS.md` Q-J.

---

## Standing constraints

- **Live Java deploy cannot be validated yet.** The intended Adaptive environment returns HTTP 500 on
  entity-metadata generation and `build-api-sources`, its dependency jar will not download, and a test
  BC is stuck in `Initial`. Build the path, keep dry-run default, and **do not report it done on the
  basis of dry-run alone.**
- **Rollback is unvalidated.** Removing a class and redeploying *should* erase it, but this is untested
  and there is no undeploy command. Nothing may depend on rollback working.
  (Note: the class-6 guide claims an undeploy command exists — see `PHASE0_AUDIT.md` §0.4 finding 8.)
- **One extension class per BC** until two-subclasses-per-BC resolution is tested. Multiple checks go
  inside one method.
- **Confirmed traps** (do not re-derive): `qad-sss-vscode` shadows the palette search — always search
  `QAD Extension`; the plugin reports Maven success without checking exit codes, so anything built here
  checks exit codes itself; the VS Code terminal caches PATH; `dotenv_values()` reads a physical file
  and ignores `os.environ`.
