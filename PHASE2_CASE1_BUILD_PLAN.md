# CASE 1 — standalone BC creation, step-gated. Build inventory.

**Scope:** the "new business component from scratch" pipeline, ported from AUX to Adaptive, with a
confirmation dialog after every step. Embedded (Case 2) and server-side/JEF (Case 3) come later.

**Nothing here is inferred from the audit summary.** Everything below was re-read this session from the
AUX source: `pipeline.py` (802 lines, in full), `bc_builder.py`, `form_builder.py`, `view_builder.py`,
`event_handler_builder.py`, `deploy_builder.py`, `qad_client.py`, `core/config.py`.

---

## 1. What is already there

### Ports almost as-is (pure functions, no I/O)

| Module | Lines | Produces | Change needed |
|---|---|---|---|
| `builders/bc_builder.py` | 292 | `entitymetadatas` payload + `field_list_map` | Parameterise `MODULE`/`APP_NAME` |
| `builders/form_builder.py` | 250 | `viewMetadataV2` payload (GroupPanel→Grid→Field tree) | Same |
| `builders/view_builder.py` | 181 | `viewResourceMetadatas` payload (browse + maint + hybrid) | Same |
| `builders/event_handler_builder.py` | 48 | `eventhandler` payload | Same, **plus** timing/base-class (Phase 5) |
| `builders/deploy_builder.py` | 28 | `deployCheckForWarnings` + `deployBusinessEntity` | Same, **plus** `DATASTORE_URI` |
| `agents/prompts.py` | 515 | 8 LLM system prompts | None for Case 1 |
| `core/ts_compiler.py` | 119 | Real `tsc` syntax gate | None |
| `core/qad_docs_loader.py` | 129 | Docs bundles for prompt grounding | `.txt`-only → needs `.md` for Adaptive Docs |

**That is ~1,560 lines of working, proven payload-construction logic that does not need reinventing.**

### Needs real change

| Module | Why |
|---|---|
| `qad_client.py` | Hardcodes `/qad-central/` in 3 places; no token cache; no 401 refresh |
| `core/config.py` | Reads `.env` + `settings.json`; must read the Phase 1 registry instead |
| `pipeline.py` | **This is the rewrite.** See §3 |
| `database.py` | Stores one row per *completed* run. Needs a per-step artifact store |
| Frontend `ClientExtPanel.tsx` (454 lines) | Fire-and-forget SSE, single `running` boolean. Not reusable as-is |

---

## 2. The reconfiguration you asked about

You were right that endpoints and payloads both need finding. Endpoints are done
(`config/endpoints.json`, 20 of them). **Payloads carry hardcoded identity that must become config.**

`com.extensions.customapp` is hardcoded in **five files, ten places**:

```
bc_builder.py:4,5,6        MODULE / MODULE_SHORT / APP_NAME
form_builder.py:3,4        MODULE / MODULE_SHORT
view_builder.py:4,5,6      MODULE / MODULE_SHORT / APP_NAME
event_handler_builder.py:3 MODULE
deploy_builder.py:3,4      MODULE / DATASTORE_URI
pipeline.py:39-43,770,787  lookup metadata, run summary, entity-registry write
```

Every URI in every payload is derived from it:

| Derived URI | Pattern | AUX value |
|---|---|---|
| entity | `urn:be:{MODULE}.{BC}.I{BC}` | `urn:be:com.extensions.customapp.Foo.IFoo` |
| module/app | `urn:app:{MODULE}` | `urn:app:com.extensions.customapp` |
| bdoc | `urn:bd:{MODULE}.{BC}.{BC}` | — |
| view meta | `urn:view:viewmeta:{MODULE}.{BC}` | — |
| hybrid browse | `urn:view:hybridbrowse:{MODULE}.{bc_lower}` | — |
| browse datasource | `urn:browse:bebrowse:{MODULE}.{bc_lower}` | — |
| field | `urn:field:{MODULE}.{BC}.I{BC}:{BC}.{field}` | — |

For Adaptive, `MODULE` = `com.yash.digwish` (from your `urn:app:com.yash.digwish`), and
`MODULE_SHORT` = `yash.digwish`. Both derive mechanically from the app URI you gave me — **no input
needed.** Two others do not derive:

### ⚠️ INPUT NEEDED — 1. `APP_NAME`

AUX uses `CustomApp` for `com.extensions.customapp`. It goes into the BC payload as `appName`
(`bc_builder.py:242`) and the view payload as `app` (`view_builder.py:149`).

**This must match the app's name as QAD holds it** — it is not free text and I will not guess it.
Where to find it: QAD → app list, or `GET {base}/api/qracore/browses?browseId=urn:browse:be:com.qad.qra.app.IApp&pageSize=1000`.

### ⚠️ INPUT NEEDED — 2. `DATASTORE_URI`

AUX uses `urn:datastore:com.extensions.extension` (`deploy_builder.py:4`). It is sent in the final
deploy call (`deployBusinessEntity`). **Environment-specific** — the Adaptive environment will have its
own. Nothing in the repo derives it.

### Not input — platform constants, already correct

`urn:be:com.qad.qra.metadatav3.IEntityDeployment:` (`bc_builder.py:231`), all
`viewUri=urn:be:com.qad.qra.*` query params, `appModuleName: "qracore"`, `platformName: "webui"`,
`BROWSE_SEARCH_OPERATORS`. These name QAD's own platform objects — same on every install.

---

## 3. The step-gated flow — and the honest size of it

### Yes, I'm clear on what you want

Each step runs → **pauses** → shows a dialog with **the real content it produced** (not a status line) →
you either **Approve** (advance) or **Regenerate with free-text** (steer and retry that step).
After the sequence, you can return to any step and regenerate; that re-runs everything downstream, each
gated again. All of this up to deployment only.

### Why this is a rewrite, not a UI feature

`run_pipeline` (`pipeline.py:381`) is **one async generator**. Every artifact lives in a local variable —
`requirements`, `spec`, `current_spec`, `panel_plan`, `placements`, `ts_code`, `js_code`, `token` — and
every failure is `yield` + bare `return`. A generator cannot be suspended across HTTP requests.

So each step becomes a **standalone function** that reads its inputs from a per-step artifact store and
writes its output back. That store is the prerequisite: **without it there is nothing to show at a gate
and nothing to regenerate from.** It is Phase 3 work that Phase 2 cannot start without.

### The 16 gates for Case 1

`W` = writes to QAD. Gate goes **before** every write, showing the exact payload — stricter than
approving the receipt afterwards, and it makes dry-run meaningful.

| # | Step | Dialog shows | W |
|---|---|---|---|
| 1 | Understanding requirements | The requirements text | |
| 2 | Designing BC fields | Field table: code, type, PK, required, dropdown values | |
| 3 | Creating BC in QAD | **The `entitymetadatas` payload** | ✅ |
| 3a | Dropdown → data-list wiring | The GET result and the patch about to be POSTed | ✅ |
| 4 | Auto-fix *(conditional)* | QAD's error + the corrected spec, diffed | |
| 5 | Planning form panels | The panel plan text | |
| 6 | Building panel layout | Grid preview + any unplaced fields | |
| 7 | Saving form design | **The `viewMetadataV2` payload** | ✅ |
| 8 | Planning event handler logic | The 6-section plan | |
| 9 | Writing event handler code | The TypeScript + the real `tsc` result | |
| 10 | Compiling TS → JS | The JavaScript | |
| 11 | Registering event handlers | **The `eventhandler` payload** | ✅ |
| 12 | Building view configuration | Browse columns, key fields, sort order | |
| 13 | Registering view | **The `viewResourceMetadatas` payload** | ✅ |
| 13a | Lookup detection | Candidates + classification | |
| 14 | Deploying | **Both deploy payloads** — terminal | ✅ |

**The step list is variable, not fixed at 16.** Step 4 fires only on a step-3 rejection; 3a only when
the spec has dropdown fields; 13a only when lookups were detected. The UI must render the run's actual
step list, not a hardcoded table — which is exactly the defect AUX has today (`TOTAL_STEPS = 14`
hardcoded in three places, and a frontend table that has already drifted).

### Step identity — resolved per Q-D

Backend owns it. `GET /api/run/steps?mode=standard` returns
`[{id, label, gated, writes_to_qad}]`, generated from the same constant the pipeline iterates. The
frontend renders from that plus the `name` already on every frame. Sub-step ids `3a` / `13a` keep your
14-step numbering intact. **No step tables in the frontend.**

---

## 4. 🔴 The one thing that blocks the design — needs your call

**Regeneration after a QAD write has already happened.**

Decision 2 says regenerating a step re-runs all subsequent steps. That works cleanly for steps 1→2.
It does **not** work once step 3 has executed: the BC now exists in QAD, and re-running step 3 fails.

This is not speculation — AUX's own code proves it. `pipeline.py:226-231`:

```python
def _is_duplicate_entity_error(result):
    """True when QAD rejected the create because the BC name is already taken.
    This is a NAME COLLISION, not a schema problem — editing fields can never fix
    it, so the pipeline must stop and ask for a new name instead of retrying."""
```

and at `:450` it stops the run and tells the user to rename. **QAD has no undo, and Phase 0 found no
delete path.**

### My suggested answer

Because every QAD write is gated **before** it fires, there is a clean line:

- **Before a write executes** → regenerate anything freely. Nothing has left the machine.
- **After a write executes** → upstream regeneration is **blocked**, with the reason named and two
  offers: *start a new run with a different BC name*, or *delete the BC in QAD yourself, then re-run*.

**Reasoning:** it is the only rule that can't silently corrupt state, it needs no undo path we don't
have, and it costs nothing in practice — the steps you'll most want to steer (fields, panels, handler
code) all sit before or between writes, and their payload gate is your real checkpoint.

**Open sub-question I will not guess at:** of the five writes, only `bc.create` is definitely
create-only. Whether `viewMetadataV2`, `eventhandler`, `viewResourceMetadatas` and the deploy pair are
**idempotent** (safe to re-send) is **untested**. `eventhandler` carries a `concurrencyHash`, which
suggests update-in-place. If some are idempotent the rule above relaxes for those steps. **This needs
one live test run to settle** — I'd rather find out than assume.

---

## 5. What I need from you

| # | Item | Why blocked |
|---|---|---|
| 1 | **`APP_NAME`** for `com.yash.digwish` | Goes in every BC and view payload; must match QAD |
| 2 | **`DATASTORE_URI`** for the Adaptive env | Final deploy call; environment-specific |
| 3 | **`QAD_USERNAME`** + **`QAD_PASSWORD`** | No call can authenticate |
| 4 | **`OPENAI_API_KEY`** | Steps 1, 2, 5, 6, 8, 9, 10 are LLM calls |
| 5 | **Your call on §4** (regeneration after a write) | Determines the state machine |
| 6 | Confirm the Phase 1 classification (`PHASE1_REGISTRY.md`) | Settings panel shape |

### Not blocking, but decide when convenient

- **Which LLM.** AUX pins `gpt-4o` / `gpt-4o-mini` per step in `MODEL_MATRIX` (`pipeline.py:136-140`),
  and the settings model selector **does not affect the BC pipeline** — a real defect in AUX. Adaptive
  should honour the setting. Tell me if you want a different model or provider.
- **A test BC to build first.** Something small — 5–6 fields, one dropdown, one PK — exercises steps 3,
  3a and 6 without a large surface.

---

## 6. Build order

Each item is independently committable, so a session limit costs at most one step.

| # | Deliverable | Depends on |
|---|---|---|
| 1 | `core/config.py` reading the Phase 1 registry; `qad_client.py` with configurable URL shape, token cache, 401 refresh | inputs 3 |
| 2 | Builders ported with `MODULE`/`APP_NAME`/`DATASTORE_URI` injected, not hardcoded | inputs 1, 2 |
| 3 | Step manifest + per-step artifact store (`run_id`, `step_id`) in SQLite | §4 decision |
| 4 | Each of the 16 steps as a standalone function reading/writing the store | 1–3 |
| 5 | Per-step HTTP transport: `POST /api/run/{id}/step/{step}` → SSE within a step, terminal `awaiting_approval` frame | 4 |
| 6 | Approve / regenerate-with-input endpoints + the downstream re-run rule | 5, §4 |
| 7 | Frontend `RunContext` (`useReducer`, no Zustand — Q-A) | 5 |
| 8 | Step dialog + per-artifact-type viewers (text, field table, code+diagnostics, JSON payload) | 7 |
| 9 | Dry-run mode: every write renders endpoint, method, headers, payload and sends nothing | 2 |

**Dry-run is the default and stays so until you greenlight live writes.**

---

## 7. Carried over — do not lose

- **Live QAD validation has not happened.** The `{base_url}/api/qracore/…` shape (no `/qad-central/`)
  is derived from a confirmed fact but unproven against `eeadaptive`, and that environment is
  known-degraded (HTTP 500s).
- **`deployCheckForWarnings` responses are discarded in AUX** (`pipeline.py:739`, never assigned). The
  Phase 4 gate must surface them.
- **Step 10 is not a compiler.** It asks an LLM to emit ES5 and never syntax-checks the result. Step 9's
  `tsc` gate is the only real compiler check in the run.
- **Four SSE frame types the AUX frontend never renders:** `warning`, `lookup_candidate`,
  `lookup_needs_review`, `lookup_summary`. In a gated UI an unrenderable frame is a silent gap.
