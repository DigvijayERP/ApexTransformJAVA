# VERIFICATION ROUND 2 — raw verdicts, preserved verbatim

Independent citation-verification of the Phase 0 audit sections that the first pass left unchecked.
Workflow `phase0-verify-priority` / run `wf_b8b49cee-c90`, launched 2026-08-07, completed 2026-08-10.
Order was forced: **B1 first, A8 second, strictly sequentially**, so a session limit could not take both.

**This file is the raw agent output, extracted from the task result before it expired.** It is evidence,
not narrative — `PHASE0_SUMMARY.md` is the readable layer. Corrections listed here have **not yet been
applied** to `PHASE0_AUDIT.md` unless `PROGRESS.md` says otherwise.

## What landed and what did not

| Section | Subject | Verdict |
|---|---|---|
| **B1** | Event handlers — the Phase 5 Pre/Post verdict | 🔴 `major-issues` — 12 flags, 7 missed |
| **A8** | Frontend — the "no Zustand" claim | ⚠️ `minor-issues` — 10 flags, 5 missed |
| **B2** (docs-java) | Class-6 Java extensions guide | ⚠️ `minor-issues` — 4 flags, 5 missed |
| **B4** (docs-tools-sec) | Platform tools / data admin / security | ⚠️ `minor-issues` — 12 flags, 5 missed |
| A9 docsloader · A10 settings · A3 lookup-progress · B3 docs-bc-ext | — | ❌ never ran (session limit / mid-stream stall) |
| completeness critic | — | ❌ never ran (session limit) |

**Central verdicts both survive.** B1: the Phase 5 Pre/Post hypothesis still **PARTIALLY HOLDS** — the
verifier independently re-tested all three load-bearing absence claims and all three hold. A8: Zustand is
**not** a dependency of the project; only the wording "zero matches" is refuted.

Cost: 9 agents, 1,260,014 subagent tokens, 413 tool calls.

## Severity vocabulary

`wrong` = the claim is false · `overstated` = true in substance, too strong as written ·
`mislabelled-inference` = presented as [CONFIRMED], actually inferred · `bad-citation` = the claim is
sound but the cited line does not say it.

---


---

# B1 — Event handlers (Phase 5 Pre/Post) — verdict: major-issues

## flag 1 — [wrong]

**Claim as written:** §7 'What AUX currently does [CONFIRMED]' inventory of AUX's QAD event-handler traffic lists only pipeline.py:685 (post_qad) plus 'A GET twin already exists: qad_client.py:64-66'.

**Cited:** aux_web_version/backend/pipeline.py:685; aux_web_version/backend/qad_client.py:57, :64-66

**What is actually there:** The prescribed sweep (grep -rn "qad_client|get_qad|post_qad" backend --include=*.py) shows an omitted module: aux_web_version/backend/probe_parent_eh.py (untracked). It imports qad_client at :22 and ALREADY performs a live read-back of a PARENT QAD-standard handler — GET at :51 and :100 against endpoint `eventhandler?appURI=urn:app:com.extensions.customapp&viewURI=urn:view:viewmeta:com.qad.erp.sales.SalesOrders&eventHandlerType=BEFORE&appliesTo=WEB` (:44-50) — and a POST update round-trip at :91 carrying `uri` + `concurrencyHash` (:74-89). This is the exact known systematic defect: the inventory was built from the modules the author already had in view, not from a qad_client sweep. It is the most material omission in the section, because §7 is titled 'including the read-back question' and this file answers it empirically.

## flag 2 — [overstated]

**Claim as written:** 'the literal URI value is not in the `.d.ts`, so the concrete `urn:be:...` string must be recovered from the live platform' — i.e. the read path for handler records is not yet known.

**Cited:** aux_web_version/backend/sss_template/lib/qracoregen.d.ts:2019 (EventHandlerV2sComm.static ENTITY_URI)

**What is actually there:** :2019 does declare `static ENTITY_URI: string` with no literal. But a working read path already exists in-repo and needs no `urn:be:` at all: probe_parent_eh.py:44-51 reads handlers via the qracore `eventhandler` endpoint with four query params. The 'must be recovered from the live platform' framing is true only of the urn:be: form, not of read-back generally.

## flag 3 — [wrong]

**Claim as written:** 'No REST endpoint for reading handler source appears in any qad_docs file. A grep of every `api/…` path across `aux_web_version/backend/qad_docs` yields only `api/bdoc/`, `api/bsvc/`, `api/qracore/{apps,browses,be,roles}`, `api/ng/service/`, `api/postapi`, `api/qraview/attachments`, `api/erp/sites/`, `api/webshell/clearAllCaches`.'

**Cited:** aux_web_version/backend/qad_docs (whole tree)

**What is actually there:** My own sweep (grep -rhoE "api/[A-Za-z0-9_./{}:-]+") returns: api/acme/items, api/bdoc/, api/bdoc/qad, api/bsvc/, api/com/extensions, api/erp/sites, api/ng/service, api/postapi, api/qracore/apps, api/qracore/be, api/qracore/browses, api/qracore/roles, api/qraview/attachments. `api/webshell/clearAllCaches` appears NOWHERE in aux_web_version (grep -rn clearAllCaches returns zero hits repo-wide); `api/acme/items` and `api/com/extensions` were omitted. The enumeration presented as a grep result is partly invented.

## flag 4 — [wrong]

**Claim as written:** 'The Primary handler is not edited: each timing is a separate module with its own class instances… `[C7]:427` … `[C7]:466` … `[C7]:625` … Three separate compilation units, same BC.'

**Cited:** Docs/qad_enterprise_platform_class_7_Event_Handlers_training_guide.pdf.md:427, :466, :625

**What is actually there:** :427 = `...EventHandler.Country.ComExtensionsTraining.Maint_BEFORE`; :466 = `...EventHandler.Country.ComExtensionsTraining.Maint_AFTER`; :625 = `com.extensions.training.EventHandler.Training.ComExtensionsTraining.Maint_PRIMARY` — a DIFFERENT BC (Training), not Country. So 'same BC' is false for the third. Worse, the section itself states at §3 ([INFERRED], audit line 3461) that :427 and :466 are the SAME Country handler before and after 'Select Post timing' (:446) — i.e. one row regenerated, not two coexisting modules. The trio therefore demonstrates zero coexisting compilation units on one BC. The underlying conclusion is still supportable from [FBEH]:87-89 and [DEBUG]:32, but not from this citation.

## flag 5 — [overstated]

**Claim as written:** §1: 'Grid claiming is the real risk… Whether a Primary module and a Post module can both list the same `gridId` and both receive grid events is nowhere stated in any file read.' and §6.1 framed as 'the single point on which Phase 5 lives or dies'.

**Cited:** aux_web_version/backend/qad_docs/Client scripting/Grid UI event handler.txt:143

**What is actually there:** :143 is quoted accurately, and my own greps for 'same grid', 'multiple handlers', 'two event handlers', 'both handlers', 'conflict' across BOTH Docs/ and qad_docs/ confirm the absence claim — no doc anywhere addresses two modules claiming one grid. BUT the section missed the governing default, one line above the cited declaration: `Event handlers API reference.txt`:832 — 'get/set list of view grid handlers that need to be created. If not set, all view grids will be handled.' A Post module that omits ViewGridsToHandleList receives ALL grids by default. That materially changes the risk framing and the §6.1 test design (the test must cover both the explicit-list and the omitted-list cases). The section presents the array as the only gate.

## flag 6 — [overstated]

**Claim as written:** 'Nothing anywhere ties a handler to a single field. There is a `ViewFieldTSHandler` base class (`[APIREF]:468`, `[APIREF]:727`) but no per-field registration row.'

**Cited:** aux_web_version/backend/qad_docs/UI Event Handlers/Event handlers API reference.txt:468, :727

**What is actually there:** The narrow half ('no per-field registration row') is correct. The broad half is contradicted at :862-864: `ViewFieldsToHandleList(): string[]` with doc comment 'List of view fields that will be handled but the view form ts handler. If not set, all fields are handled.', and at :875 `ViewField: IViewField` on IViewFieldTSHandler. Handlers CAN be scoped to specific fields — in code, not via a registration row.

## flag 7 — [mislabelled-inference]

**Claim as written:** 'the record key is the 4-tuple `(appURI, viewURI, eventHandlerType, appliesTo)` … So per form, per app, per Web/Mobile, per timing = exactly one row. [CONFIRMED]'

**Cited:** aux_web_version/backend/sss_template/lib/qracoregen.d.ts:2009

**What is actually there:** :2009 declares `fetch(appURI, viewURI, eventHandlerType, appliesTo): EventHandlerV2sDTO`. That is a four-argument lookup, not a declared uniqueness constraint — and the returned DTO is a dataset whose payload is an ARRAY (`ttEventHandlerV2: EventHandlerV2Record[]`, :1969), which is consistent with more than one row. 'Exactly one row' is deduced from a method signature, then labelled [CONFIRMED].

## flag 8 — [mislabelled-inference]

**Claim as written:** '`onBindData` … Fires on every record selection in a hybrid browse (`[APIREF]:24`).' — stated under the heading 'PARENT-SCREEN events relevant to populating an embedded grid [CONFIRMED]'.

**Cited:** aux_web_version/backend/qad_docs/UI Event Handlers/Event handlers API reference.txt:24

**What is actually there:** :24 reads in full: 'Called when the view screen binds new data to its model/fields. Fired after the new data is bound.' It says nothing about hybrid browses or record selection. The nearest support is [C7]:349 ('each time when data from the selected record should be displayed'), which is also not hybrid-browse-specific.

## flag 9 — [overstated]

**Claim as written:** §1: 'If the active developer app **is** the app that owns the target BC, Pre/Post is unavailable and you are forced onto the Primary handler.'

**Cited:** aux_web_version/backend/qad_docs/Business Components - Form Builder/Form Builder - Event Handlers.txt:22-28, :88

**What is actually there:** :22-28 and :88 are quoted correctly, but BOTH are scoped to 'Is platform BC = yes'. The same table at :46-52 says Add pre/post + platform BC = no + same app = yes → 'Possible', and :87 says a coded BC gets 'one Pre and Post Event Handlers for each App which is active at the moment'. The restriction is platform-BC-and-same-app, not same-app generally. (Note also an unsurfaced doc conflict: `Platform Scripting - TypeScript/Client scripting.txt`:22 states the flat, unqualified version and contradicts FBEH:46-52.) Operationally harmless for AUX, which only creates platform BCs — but the section states it unconditionally.

## flag 10 — [bad-citation]

**Claim as written:** §3: 'The generated main class is `<BCName>MaintHandler` (`[C7]:435` `TrainingMaintHandler`; `[MAINVH]:29` `CountryMaintHandler`; `[EX12-A]:32` `ItemMaintHandler`).'

**Cited:** Docs/qad_enterprise_platform_class_7_Event_Handlers_training_guide.pdf.md:435

**What is actually there:** C7:435 is the bare code-listing line '9' inside the Country BEFORE snippet. `TrainingMaintHandler` is at C7:635. (MAINVH:29 and EX12-A:32 both verify correctly.)

## flag 11 — [bad-citation]

**Claim as written:** '`setRowFieldValue(rowData, fieldId, value, withoutRefresh = false): boolean` — `[DGRID]:416-417`, `[APIREF]:1643-1652`'

**Cited:** aux_web_version/backend/qad_docs/UI Event Handlers/Event handlers API reference.txt:1643-1652

**What is actually there:** DGRID:417 does give the 4-parameter form. APIREF:1652 declares only three parameters: `setRowFieldValue (rowData: kendo.data.ObservableObject, fieldId: string, value: any): boolean`. The two sources disagree and APIREF does not support the quoted signature; the disagreement is not noted.

## flag 12 — [overstated]

**Claim as written:** §3 preamble: '`[C7]:169-176` lists **four**; `[APIREF]` documents **five**.'

**Cited:** aux_web_version/backend/qad_docs/UI Event Handlers/Event handlers API reference.txt

**What is actually there:** C7:169-176 does list exactly four ✓. APIREF carries base-class sections for at least seven distinct classes: QraViewTSHandler (:821), QraViewTSHandlerWithViewFormTSHandler (:852), QraViewFormTSHandler (:199, :844), ViewFieldTSHandler (:468, :727, :867), ViewGridTSHandler (:233, :879), QraBrowseTSHandler (:1892), QraBrowseTSHandlerV2 (:1906). Relatedly, §3 row 1 attributes `ViewGridsToHandleList` (:834) and `createViewGridTSHandler` (:839) to QraViewTSHandlerWithViewFormTSHandler; both sit in the `QraViewTSHandler` section (:821-843) and are inherited.

## Missed — material items the section omitted

- backend/probe_parent_eh.py (untracked, aux_web_version) — omitted from §7's 'What AUX currently does' inventory despite reaching QAD via qad_client (:22). It is the single most relevant artefact in the repo to this section: it registers/reads a BEFORE (Pre) handler from app urn:app:com.extensions.customapp against the QAD-standard parent BC urn:view:viewmeta:com.qad.erp.sales.SalesOrders (:24-27), proving empirically what §1 only argues from docs — that a Pre handler can be attached to a foreign parent BC. It also demonstrates a working GET read-back endpoint and a POST update requiring `uri` + `concurrencyHash`.
- Event handlers API reference.txt:832 — 'get/set list of view grid handlers that need to be created. If not set, all view grids will be handled.' Directly governs §1's grid-claiming risk and §6.1's test design; omitted entirely.
- Event handlers API reference.txt:862-864 — ViewFieldsToHandleList(): string[], 'If not set, all fields are handled.' Contradicts §2's 'Nothing anywhere ties a handler to a single field.'
- Form Builder - Event Handlers.txt:46-52 — the table row (coded BC, same app → pre/post 'Possible') that qualifies the §1 'Pre/Post unavailable in same app' finding, and its conflict with Client scripting.txt:22.
- Main view UI event handler.txt:73 — 'createViewGridTSHandler: this method is called for every grid that is initialized, and in the list of grids that have an event handler.' A second, differently-worded statement of the grid gate that should have been weighed against GRIDVH:143.
- The wire DTO carries `uri` and `concurrencyHash` fields (probe_parent_eh.py:60-61, :77, :83) that are load-bearing for any update-in-place flow. §7's 'Exact stored record shape' is drawn only from the .d.ts and never confronts the actual wire shape AUX has already observed.
- Event handlers API reference.txt:1906-1918 — QraBrowseTSHandlerV2 has its own section. §3 row 4 and §6.5 describe :1905 as the only statement / a dead reference, but :1905 belongs to QraBrowseTSHandler (V1); the V2 section is separate and equally sparse.

## Corrections to B1

**Overall:** the central verdict **PARTIALLY HOLDS** survives. I independently re-tested the three load-bearing absence claims and all three hold: (a) no doc in `Docs/` or `qad_docs/` states whether two modules can claim the same grid; (b) no tie-break rule for two Pre handlers from different apps; (c) `[UIEH]:21` is indeed the only multi-app ordering example. The doc quotations are, with the exceptions below, verbatim and correctly line-numbered — [C7]:62-64/60, :402-406, :443-446, :461, :501, :427, :466, :625, :439/:479, :349, :353, :548; [UIEH]:8/:12/:14/:16-18/:21/:65/:91; [FBEH]:7/:22-28/:87-90/:101-103; [EX2]:7-8; [EX12-B]:111/:121/:128-130/:154-170; [GRIDVH]:43-44/:113-128/:143; [GRIDEV]:5/:23/:32-38; [BCVIEW]:140/:395/:405-406/:425-426; [C2]:916-924/:1018; [C3]:244/:319-321/:493/:534/:597; and every AUX code citation (`event_handler_builder.py:8,:25-37,:29,:30`; `form_builder.py:127,:216`; `view_builder.py:157`; `pipeline.py:685`; `qad_client.py:57,:64-66`; `prompts.py:259`; `qracoregen.d.ts:1965-1985,:2001-2012,:2019`). The ~55 APIREF event line numbers I spot-checked (:18,:22,:26,:33,:38,:42,:47,:52,:55,:58,:63,:72-77,:191,:206-232,:246,:253,:260,:271,:276,:286,:318-325,:410,:418-428,:461,:468-488,:727-747) are all exact.

### 1. §7 — replace the "What AUX currently does" bullet list intro
> **AUX already reads handlers back from QAD, and already targets a parent BC.** In addition to the write path, `aux_web_version/backend/probe_parent_eh.py` (untracked) reaches QAD via `qad_client` (`:22`) and performs a full read/update round-trip against a **QAD-standard parent**: `GET …/qad-central/api/qracore/eventhandler?appURI=urn:app:com.extensions.customapp&viewURI=urn:view:viewmeta:com.qad.erp.sales.SalesOrders&eventHandlerType=BEFORE&appliesTo=WEB` (`:44-51`, re-read at `:100`), then `POST "eventhandler"` with `uri` + `concurrencyHash` echoed from the GET (`:74-91`). This is empirical confirmation of limb 1 of the hypothesis on a real parent BC, and it supplies the concrete read endpoint.

### 2. §7 — replace the ENTITY_URI sentence
> `EventHandlerV2sComm` declares `static ENTITY_URI: string` (`:2019`) with no literal value. That matters only for a `urn:be:`-style call; the read path AUX actually uses (`probe_parent_eh.py:44-51`) is the qracore `eventhandler` endpoint with four query params and needs no `urn:be:`.

### 3. §7 — replace the final "Other retrieval surfaces" bullet
> No REST endpoint for reading handler source appears in any qad_docs *page*. My sweep of `api/…` paths across `aux_web_version/backend/qad_docs` yields `api/acme/items`, `api/bdoc/`, `api/bdoc/qad`, `api/bsvc/`, `api/com/extensions`, `api/erp/sites`, `api/ng/service`, `api/postapi`, `api/qracore/{apps,be,browses,roles}`, `api/qraview/attachments`. **Delete `api/webshell/clearAllCaches` — it does not occur anywhere in `aux_web_version`.** The absence is a gap in the *docs* only; AUX has the working endpoint (see correction 1).

### 4. §1 — replace the "Primary handler is not edited" bullet
> The Primary handler is **not edited**: each timing is a **separate registration row**, and the platform emits a separately-named source per timing — `[DEBUG]:32` ("`com_extensions_oneforce_TIMING.ts`… Timing can be BEFORE, AFTER, or PRIMARY") and `[FBEH]:87-89` (one Pre and one Post *per active app*, alongside the owning app's Primary). ~~Three separate compilation units, same BC.~~ **Note:** `[C7]:427` and `[C7]:466` are the *same* Country handler before and after "Select Post timing" (`:446`), not two coexisting modules — see §3's own [INFERRED] note; and `[C7]:625` is a different BC (`…EventHandler.**Training**.…`), not Country.

### 5. §1 — replace the "grid claiming" bullet's second sentence
> `[APIREF]:832` gives the default that governs this: "get/set list of view grid handlers that need to be created. **If not set, all view grids will be handled.**" So a Post module that omits `ViewGridsToHandleList` is offered every grid; the array is an opt-*out* filter, not an opt-in claim. Whether *both* a Primary module and a Post module receive grid events for the same `gridId` — whether either lists it explicitly or omits the list — is **nowhere stated** (confirmed by grep of both doc sets). §6.1's test must therefore cover two arms: Post-with-explicit-list, and Post-with-no-list.

### 6. §1 — qualify the "not possible" bullet
> → If the target BC is a **platform** BC **and** the active developer app owns it, Pre/Post is unavailable (`[FBEH]:22-28`, `:88`) and you are forced onto Primary. For a **coded** BC in the same app, `[FBEH]:46-52` and `:87` say Pre/Post *is* possible — though `[CLISCR]:22` states the flat "same app → always Primary" and conflicts with that row. AUX only creates platform BCs, so operationally the restriction bites; the docs are inconsistent for coded BCs.

### 7. §2 — replace the last line
> Handlers can be scoped to specific fields **in code** — `[APIREF]:862-864` `ViewFieldsToHandleList(): string[]`, "If not set, all fields are handled", plus `ViewFieldTSHandler` with a `ViewField` property (`:875`). What does **not** exist is a per-field *registration row*; registration is per form only.

### 8. §5 — downgrade the 4-tuple bullet from [CONFIRMED] to [INFERRED]
> `qracoregen.d.ts:2009` declares `fetch(appURI, viewURI, eventHandlerType, appliesTo)` — a four-argument lookup. [INFERRED] this is the record key, so per form/app/platform/timing there is one row. Not proven by the `.d.ts`: `fetch` returns a dataset whose payload is an array (`ttEventHandlerV2: EventHandlerV2Record[]`, `:1969`). *Corroborated in practice* by `probe_parent_eh.py:58` taking `eventHandlerV2s[0]`.

### 9. §4 — fix the onBindData line
> `onBindData` — `[APIREF]:24`: "Called when the view screen binds new data to its model/fields. Fired after the new data is bound." `[C7]:349` adds "each time when data from the selected record should be displayed". ~~Fires on every record selection in a hybrid browse.~~ [INFERRED, untested] that record selection in a hybrid browse triggers a rebind.

### 10. §3 — three small fixes
- `[C7]:435` → **`[C7]:635`** for `TrainingMaintHandler`.
- Row 1: `ViewGridsToHandleList` is declared at `[APIREF]:834` as a **method** `ViewGridsToHandleList(): String[]` under the `QraViewTSHandler` section (`:821-843`, inherited), while every worked example assigns it as a property array (`[GRIDVH]:114`, `[GRIDEV]:23`). Note the discrepancy.
- Preamble: "`[APIREF]` documents **five**" → "`[APIREF]` documents **seven** base-class sections (`:199, :233, :468/:727, :821, :852, :1892, :1906`); five are relevant here."
- `setRowFieldValue`: the 4-param form with `withoutRefresh = false` is `[DGRID]:417` only; `[APIREF]:1652` declares three parameters. Cite DGRID and flag the disagreement.

### 11. §6.5 — precision
> `[APIREF]:1905` is a dead cross-reference for **QraBrowseTSHandler** (V1). `QraBrowseTSHandlerV2` has its own section at `:1906-1918` and documents only a `ViewController: IQraBrowseControllerV2` property — no event list either.

### 12. Minor quote note (no flag)
`[DEBUG]:32` reads "but ':' replaced with ." — the underscore was lost in text extraction. The section silently reinserts it as `` `_` ``. Correct in substance (the filename example `com_extensions_oneforce_TIMING.ts` is verbatim), but mark the insertion.

**No secret values were leaked in this section.**

---

# A8 — Frontend architecture — verdict: minor-issues

## flag 1 — [wrong]

**Claim as written:** "Step 4 has a second guard at `ProgressPanel.tsx:68`: `if (n === 4 && status === "pending") return null;` — dead code, since 4 is not in the visible list."

**Cited:** frontend/src/features/client_ext/components/ProgressPanel.tsx:68 (with :20)

**What is actually there:** The guard sits inside `visibleSteps.map(...)` (:64), and `visibleSteps` is mode-dependent (:49). `EMBEDDED_VISIBLE_STEPS = [1, 2, 3, 4, 5, 6, 7]` (:32) DOES contain 4, so in embedded mode the guard is live and hides embedded step 4 ("Handling duplicates & Retrying") whenever it is pending. It is dead only in standard mode.

## flag 2 — [wrong]

**Claim as written:** "Backend emits **three additional types the frontend type does not declare and no component renders**" — listing only `warning`, `lookup_candidate`, `lookup_needs_review`. Repeated in the A8.6 "Silent event loss" blocker row.

**Cited:** PHASE0_AUDIT.md A8.3 / A8.6; client_extensions.py:156, pipeline.py:81-114

**What is actually there:** There are FOUR. My sweep `grep -rn "'type':|\"type\":" backend --include=*.py` finds a fourth SSE frame type, `lookup_summary`, emitted at backend/pipeline.py:124-131 via `yield _sse({"type": "lookup_summary", ...})`. `grep -rn lookup_summary frontend/src` returns zero hits, so it is equally undeclared and unrendered. Same incomplete-inventory defect class as the flagged qad_client sweep.

## flag 3 — [overstated]

**Claim as written:** "A repo-wide grep for `zustand` across `package.json`, `package-lock.json`, `frontend/src/**` and `frontend/node_modules/` returns **zero matches**."

**Cited:** frontend/package.json:10-14 + stated repo-wide grep

**What is actually there:** Not zero. `grep -rin zustand frontend/src` returns exactly one match: `frontend/src/features/auth/authStore.tsx:4` — `// \`feature\` state — same try/catch pattern). No Zustand added.` The section quotes that very line four lines later, so it contradicts itself. package.json (3 runtime deps: react, react-dom, react-router-dom), `grep -c zustand frontend/package-lock.json` = 0, and `ls frontend/node_modules/zustand` = No such file — all confirm the substantive conclusion. Only the "zero matches" wording is refuted.

## flag 4 — [overstated]

**Claim as written:** design-tokens.css "`:1-14` states it: *\"This file is the single source of truth… New components MUST consume these tokens: no hardcoded hex, no inline styles.\"*"

**Cited:** frontend/src/shared/design-tokens.css:1-14

**What is actually there:** Lines 6-9 read: "This file is the single source of truth for the header, the feature toggle, the health chip/panel, and the status-only Settings page. New components MUST consume these tokens: no hardcoded hex, no inline styles." The ellipsis elides the scoping clause — the file claims SSOT status for four named surfaces, not project-wide. A8.6 then calls it a "Genuine single source of truth" on the strength of the trimmed quote.

## flag 5 — [bad-citation]

**Claim as written:** "label ignored at `ProgressPanel.tsx:83` (uses local `stepNames[n]`)"

**Cited:** frontend/src/features/client_ext/components/ProgressPanel.tsx:83

**What is actually there:** Line 83 is `{msg && status !== "pending" && (`. The label is assigned at :70 (`const label = stepNames[n];`) and rendered at :82.

## flag 6 — [bad-citation]

**Claim as written:** "| `\"Regenerate\"` | `onRegenerate` | wired to **`onGenerate`** — `SssPanel.tsx:140` |"

**Cited:** frontend/src/features/sss/SssPanel.tsx:140

**What is actually there:** Line 139 is `onRegenerate={onGenerate}`. Line 140 is `onDiscard={onDiscard}`.

## flag 7 — [bad-citation]

**Claim as written:** design-tokens.css structural citations: "status aliases `--status-ok`/`--status-warn`/`--status-error`/`--status-neutral` (`:51-53`)"; "`--on-accent` (`:56`)"; "`[data-theme="light"]` (`:143-178`)"; "`design-tokens.css:180-237` is a documented 'INTERACTIVE PATTERN REFERENCE'". Rule 3 repeats `:51-53`.

**Cited:** frontend/src/shared/design-tokens.css:51-53, :56, :143-178, :180-237

**What is actually there:** Four tokens span :51-54 (--status-neutral is on :54). `--on-accent: #fff;` is on :57 (:56 is its comment). The light block opens on :142. The pattern-reference comment runs :180-240, not :180-237. (Cross-checked against two citations in the same list that ARE exact: CARD/PANEL at :216-219 and FOCUS-RING GLOW at :226-227.)

## flag 8 — [overstated]

**Claim as written:** "**Routing is a two-route shell**" / A8.6 blocker: "`main.tsx:18-29` (two routes only)" — while the body of the same paragraph says "`Routes` with exactly three entries".

**Cited:** frontend/src/main.tsx:18-29

**What is actually there:** Three `<Route>` elements: :18 `/login`, :19-26 `/*`, :29 `*` → `<Navigate to="/" replace />`. The third is a catch-all redirect, so the architectural point stands, but "two routes only" and "exactly three entries" cannot both be stated as fact in the same section.

## flag 9 — [overstated]

**Claim as written:** "persistence is three hand-rolled `localStorage` calls"

**Cited:** PHASE0_AUDIT.md A8.2

**What is actually there:** `grep -rn localStorage frontend/src frontend/index.html` returns 7 actual call sites (App.tsx:20,31,52; authStore.tsx:41,49,50; index.html:20) across 3 keys. The key table immediately below is correct; only the sentence is wrong.

## flag 10 — [overstated]

**Claim as written:** Line-count and code-fence fidelity: "`ClientExtPanel` is a **455-line god component**"; "`RulePrompt.tsx` (whole file, 45 lines)"; "authStore.tsx (whole) … only ~117 lines"; and "Verbatim, `api.ts:78-83` and `:99-110`".

**Cited:** ClientExtPanel.tsx, RulePrompt.tsx, authStore.tsx, client_ext/api.ts:78-83 and :99-110, sss/api.ts:85-99

**What is actually there:** `wc -l` gives 454 / 44 / 116. The fence labelled ":78-83" also contains line 85 (`const reader = resp.body!.getReader();`); the fence labelled ":99-110" silently drops the comment on :102; and the `sss/api.ts:85-99` fence is reflowed (multi-line object literals collapsed onto one line) while presented as source. Substance unaffected in all cases.

## Missed — material items the section omitted

- The fourth undeclared SSE frame type `lookup_summary` (backend/pipeline.py:124-131), unrendered by the frontend — belongs in both the A8.3 event-vocabulary list and the A8.6 "Silent event loss" blocker.
- `backend/pipeline_embedded.py:30` `BASE_TOTAL_STEPS = 7` and the dynamic `total_steps` passed to `_evt` (embedded step 8 is emitted at :321/:338/:341 only when a standalone view is wanted). This is the mechanism behind the "step 8 unrenderable" finding and the section never states that embedded `total` is variable — directly relevant to a step-gated UI that must render "step N of M".
- Corroboration of "only the terminal summary is persisted" at the schema level: `backend/database.py:14-27` `CREATE TABLE runs (...)` has no per-step column, and `backend/models.py:17-28` `HistoryItem` carries only `summary_json`. The section cited only the router write-path; the schema is the stronger evidence and makes the blocker unarguable.
- The section's own scope line claims `frontend/tsconfig.json` and `frontend/vite.config.ts` were read in full, but no finding anywhere in A8 rests on either file — no build-target, path-alias, or proxy detail is reported, which a Phase 2 rewrite would need.
- A8 makes no claims about D:/WEB_AUX/adaptive_java_version/Docs, so there was no Adaptive-platform doc quotation in this section to verify.

## A8.0 — Zustand row

Replace:
> A repo-wide grep for `zustand` across `package.json`, `package-lock.json`, `frontend/src/**` and `frontend/node_modules/` returns **zero matches**.

with:
> `frontend/package.json:10-14` lists exactly three runtime deps: `react`, `react-dom`, `react-router-dom`. `grep -c zustand frontend/package-lock.json` → `0`; `frontend/node_modules/zustand` does not exist. The only occurrence of the string anywhere in `frontend/src/**` is the comment at `authStore.tsx:4` ("No Zustand added"). **Zustand is not a dependency of this project.**

*(The `authStore.tsx:1-4` quote is verbatim — confirmed byte-for-byte, including the em-dashes.)*

## A8.3 — event vocabulary

Replace "**three additional types**" with "**four additional types**" and add to the list:

> - `"lookup_summary"` — `pipeline.py:124-131` (`yield _sse({"type": "lookup_summary", …})`), emitted once after the per-candidate frames.

Apply the same change to the A8.6 "Silent event loss" row: `warning`/`lookup_candidate`/`lookup_needs_review`/**`lookup_summary`** unrendered (`client_extensions.py:156`, `pipeline.py:81-131`).

## A8.3 — step-4 guard

Replace:
> Step 4 has a second guard at `ProgressPanel.tsx:68`: `if (n === 4 && status === "pending") return null;` — dead code, since 4 is not in the visible list.

with:
> `ProgressPanel.tsx:68` `if (n === 4 && status === "pending") return null;` runs inside the mode-dependent `visibleSteps.map` (`:49`, `:64`). It is unreachable in **standard** mode (4 ∉ `STANDARD_VISIBLE_STEPS`) but **live in embedded** mode (4 ∈ `EMBEDDED_VISIBLE_STEPS`, `:32`), where it hides "Handling duplicates & Retrying" until that step actually runs.

Also add: **embedded `total` is variable** — `pipeline_embedded.py:30` `BASE_TOTAL_STEPS = 7`, raised to 8 only when a standalone view is wanted (`:321`, `:338`); the frontend never reads `e.total`.

## A8.6 — blocker table, two citations

- "Hardcoded, already-drifted step tables" row: `label ignored at ProgressPanel.tsx:83` → **`:70` (assigned) / `:82` (rendered)**.
- "View union has no room for a gate" row: `main.tsx:18-29 (two routes only)` → **`main.tsx:18-29` (two real routes plus a catch-all `<Navigate>` at `:29`)**. Fix the same wording in A8.1: "two-route shell" vs "exactly three entries" — pick one.

## A8.4 — SSS action table

`"Regenerate" … SssPanel.tsx:140` → **`SssPanel.tsx:139`**.

## A8.7 — design-tokens citations

- status aliases `:51-53` → **`:51-54`** (both occurrences, incl. Rule 3).
- `--on-accent` `:56` → **`:57`**.
- `[data-theme="light"]` `:143-178` → **`:142-178`**.
- "INTERACTIVE PATTERN REFERENCE" `:180-237` → **`:180-240`**.

## A8.7 — tokens quote

Restore the elided scope:
> `design-tokens.css:6-9`: *"This file is the single source of truth for the header, the feature toggle, the health chip/panel, and the status-only Settings page. New components MUST consume these tokens: no hardcoded hex, no inline styles."*

and soften A8.6's "Genuine single source of truth" to "**Declares itself the single source of truth for the header/toggle/chip/Settings surfaces; the legacy CE stylesheet predates it and does not comply (see A8.7).**"

## Minor numbers / fences

- "455-line god component" → **454**; "RulePrompt.tsx (whole file, 45 lines)" → **44**; "~117 lines" → **116**.
- Drop the word "Verbatim" before the `client_ext/api.ts` fences, or label them `:78-85` and `:99-110 (comment elided)`. The `sss/api.ts:85-99` fence is reflowed, not source — label it "paraphrased for width".
- A8.2: "three hand-rolled `localStorage` calls" → "**three hand-rolled `localStorage` keys across seven call sites**".

## Claims re-verified and standing (no change)

`authStore.tsx:1-4` quote verbatim · state = one React Context + component-local `useState`/`useRef`, enumeration complete (28 files under `frontend/src`, confirmed by `find`) · no pause point (`grep -rniE "approv|\bpause|\bresume|await_input" backend --include=*.py` → 6 hits, all unrelated: prompts.py:76, embedded_builder.py:189, sss.py:4/21/101, discover.py:30; the pipeline+router grep yields only `pipeline.py:654` "tsc syntax gate") · 58 `yield _evt` sites, all inside `run_pipeline` (`pipeline.py:381`) · exactly one `Authorization` header in the whole frontend (`features/auth/api.ts:53`) · exactly one endpoint behind `Depends(auth.get_current_user)` (`routers/auth.py:69`); `sss.py:38` is a readiness gate (`sss/readiness.py:52-56`); `main.py:66-94` adds only CORS + SlowAPI and includes all routers with no `dependencies=`, so every other `/api/*` is open · only the terminal summary persisted (`client_extensions.py:185-197`, and `database.py:14-27` `runs` has no per-step column) · three embedded labels disagree (backend `pipeline_embedded.py:33/36/37` vs frontend `ProgressPanel.tsx:23/26/27`; labels 2,3,6,7 match exactly) and embedded step 8 is unrenderable · `STANDARD_STEP_NAMES` character-identical to `pipeline.py:145-160` · all `client_extensions.py`, `SettingsPage.tsx`, `ReviewDeploy.tsx`, `SssPanel.tsx`, `BcPicker.tsx`, `sss.css` and `index.css` line citations spot-checked correct. **No secret value is leaked anywhere in A8** — `SettingsPage` is correctly described as status-only.

---

# B2 — Class-6 Java extensions guide — verdict: minor-issues

## flag 1 — [overstated]

**Claim as written:** "the doc contains **zero HTTP endpoints, zero URL paths**, zero payload keys, zero header names…" [CONFIRMED by absence, whole-file read]

**Cited:** PHASE0_AUDIT.md:3644 (whole-file absence claim over DOC)

**What is actually there:** The file contains four absolute http(s) URLs, two of which carry paths: DOC:139 `https://www.openlogic.com/openjdk-downloads`, DOC:197 `https://maven.apache.org/`, DOC:421 `https://code.visualstudio.com/`, and DOC:555 `https://aldpqjavaext01.environments.qad.com/clouderp` — the last of which the section itself cites in §5 row 1. The *intended* narrow claim is independently confirmed: my own grep for `oauth`, `api/`, `qracore`, `upload-packages`, `appURI`, `install-file`, `MANIFEST`, `App-Name`, `Low-Code`, `BaseBC`, `qad-ext-dependencies` returns zero hits, and the only `http` hits are those four URLs plus the prose bullet at DOC:118. So the substance (no QAD API endpoint, method, param or header anywhere) stands; only "zero URL paths" is literally falsified.

## flag 2 — [overstated]

**Claim as written:** "`delete` / `fetch` / `exists` — **never appear anywhere in the file**" [CONFIRMED absent]; repeated in §5 row 6 as "`delete`, `fetch`, `exists` never appear in the file"

**Cited:** PHASE0_AUDIT.md:3660 and :3727 (no DOC line given — asserted as a whole-file absence)

**What is actually there:** My grep finds all three words present: `exists` at DOC:63 ("Java Extension for this BC exists?"); `fetch` at DOC:114 ("securely fetch data directly from the database") and DOC:634 ("Add XHR/fetch Breakpoint"); `delete`/`Delete` at DOC:298, DOC:683, DOC:869, DOC:887 (all Windows/VS Code/Web UI chrome). None of them occurs as a BC lifecycle hook or method name, so the load-bearing conclusion (the doc documents only `initialize`/`create`/`update` and gives no hint of further hooks) is confirmed — but the universal wording is refuted by a one-line grep.

## flag 3 — [overstated]

**Claim as written:** Output-jar path quoted as `Building jar: …\target\com.extensions.training-ext-cust.jar`, and §3 naming row `target\com.extensions.training-ext-cust.jar` [CONFIRMED], §5 row 4 "**AGREES** on the artifact path/pattern"

**Cited:** DOC:814

**What is actually there:** DOC:814 is a mangled markdown table row: `…\urn\_app\_com.extensions.training` then a cell break, then `arget\com.extensions.training-ext-cust.jar`. The leading `t` of `target` was eaten by the table pipe — the string `target\` does not appear on that line. The jar *filename* is verbatim; the `target\` directory component is an (almost certainly correct) OCR repair, corroborated only by the scaffold tree at DOC:618. In a section that elsewhere flags OCR damage explicitly (F3), presenting this as a verbatim quote is a shade too confident.

## flag 4 — [overstated]

**Claim as written:** "`create` and `update` carry `@Override`; **`initialize` does not** … **Repeated identically in the second listing.**"

**Cited:** DOC:718-720, DOC:725, DOC:733, DOC:793-795

**What is actually there:** The second listing (DOC:785-800) contains only the five imports, `@Extension`, the class declaration and `initialize`; it closes the class brace at DOC:799 and never shows `create`, `update` or `validateCapacity`. It therefore repeats only the "`initialize` has no `@Override`" half of the observation; the `@Override`-on-create/update half is not repeated anywhere.

## Missed — material items the section omitted

- DOC:43 — "allow modify or **completely override** the default behavior of a specific BC" is never cited. It is the doc's only statement bearing on whether `super` may legitimately be omitted, and it directly qualifies §3's "Call `super`" row ([INFERRED], "no 'must'/'always'/'required' statement") and bundle item 1's proposed "call-`super` rule". The section cites DOC:44 and DOC:45 from the same bullet list but skips DOC:43.
- Maven-version staleness, the exact parallel of F2, is not reported: both env-var tables show `MAVEN_HOME = C:\Program Files\Maven\apache-maven-3.6.3` (DOC:291, DOC:313) while the verify transcript prints `Apache Maven 3.9.12` / `Maven home: …\apache-maven-3.9.12` (DOC:383-384) and the folder listing shows `apache-maven-3.9.9` (DOC:320). This is additional evidence for F2's "screenshots left stale" conclusion, and the deck states no minimum Maven version anywhere.
- DOC:65-66 use `JEF` as the framework's own acronym ("Progress BL triggers execution of overridden 'create' method in **JEF**"). §2's error-surfacing row calls the `JEF202606035.` error-id prefix "scheme not explained [INFERRED]" without connecting it to that in-file definition of the prefix.
- The doc's own name inconsistency for the settings page is missing from the "Minor discrepancies" list: DOC:553 and DOC:557 say "QAD My **Developer** Settings", while DOC:557 also says "My **Development** Settings page". §1 row 11 prints only "My Development Settings" as if the doc were consistent.
- DOC:39 — "The Java Extension Framework is the mechanism that allows a developer to inject custom logic into the lifecycle of Business Components" — the doc's only definition of the framework, uncited (§1 row 0 uses DOC:55 instead). Minor, but it is the sentence a bundle's opening paragraph would quote.

## Corrections

**§1, absence paragraph (PHASE0_AUDIT.md:3644) — "zero URL paths"**
> the doc contains **zero HTTP endpoints, zero URL paths**, zero payload keys, zero header names, …

→ the doc contains **zero API endpoints and zero QAD URL paths**, zero payload keys, zero header names, zero `pom.xml` content, zero `MANIFEST.MF` content, zero `mvn install:install-file` invocation, and zero dependency-jar filename. (The only URLs in the file are the four download/environment links at `DOC:139`, `DOC:197`, `DOC:421` and `DOC:555`.) Nothing in the file matches `oauth`, `api/`, `qracore`, `upload-packages`, `appURI`, `install-file`, or `MANIFEST` — **re-verified by independent grep**.

**§2 table (PHASE0_AUDIT.md:3660) and §5 row 6 (PHASE0_AUDIT.md:3727) — delete/fetch/exists**
> `delete` / `fetch` / `exists` — **never appear anywhere in the file** … [CONFIRMED absent]

→ `delete` / `fetch` / `exists` — **never appear as method or hook names.** The bare words occur only as unrelated UI chrome and prose: `exists` at `DOC:63`, `fetch` at `DOC:114` and `DOC:634`, `Delete` at `DOC:298`, `DOC:683`, `DOC:869`, `DOC:887`. [CONFIRMED absent as hooks]

Same substitution in §5 row 6: "**SILENT:** `delete`, `fetch`, `exists` are never named as overridable methods (the words occur only as UI labels / prose, `DOC:63`, `114`, `683`) — the doc gives no hint that the base class has more than these three hooks."

**§3 naming row and §5 row 4 (PHASE0_AUDIT.md:3696, :3725) — `target\` is an OCR repair**
> `Building jar: …\target\com.extensions.training-ext-cust.jar` (`DOC:814`)

→ `Building jar: …\urn_app_com.extensions.training\[t]arget\com.extensions.training-ext-cust.jar` (`DOC:814` — the markdown table pipe swallows the leading `t` of `target`; the directory name is reconstructed, corroborated by the `target` folder in the scaffold tree at `DOC:618`). The jar filename itself is verbatim.

**§3 `@Override` row (PHASE0_AUDIT.md:3685)**
> Repeated identically in the second listing.

→ The second listing (`DOC:785-800`) shows only imports, `@Extension`, the class declaration and `initialize` (class closed at `DOC:799`); it repeats the missing-`@Override`-on-`initialize` point but contains no `create`/`update` at all.

**§3 "Call `super`" row (PHASE0_AUDIT.md:3683) — add the countervailing citation**
→ Append: The doc's capability bullet `DOC:43` — "allow modify or **completely override** the default behavior of a specific BC" — is the closest the file comes to addressing omission of `super`, and it points the other way. Any "always call `super`" rule in the contract card must therefore be sourced from the decompile, not this deck.

**F2 (PHASE0_AUDIT.md:3746) — add the corroborating Maven mismatch**
→ Append: The same staleness shows in Maven: env tables `apache-maven-3.6.3` (`DOC:291`, `DOC:313`) vs transcript `Apache Maven 3.9.12` (`DOC:383-384`) vs folder listing `apache-maven-3.9.9` (`DOC:320`). No minimum Maven version is stated anywhere.

**Minor discrepancies list (PHASE0_AUDIT.md:3754-3760) — add one**
→ The settings page is named two ways in one caption: "QAD My **Developer** Settings" and "My **Development** Settings page" (`DOC:553`, `DOC:557`).

---

## Notes (not flagged)

- Header says "892 lines"; the file is **893 lines** (`wc -l` reports 892 because there is no trailing newline). The section's own `DOC:893` citation is valid and correct. Byte count 32,464 is exact.
- "43 slides (`DOC:893`)" is tagged [CONFIRMED]; `DOC:893` is `<page_number>43</page_number>`, i.e. the last page number — a one-step inference, and a safe one.
- §4 "Rollback / versioning — **Silent.** No mention of versions, history, or reverting" is loose in isolation (the file mentions JDK/Maven/VSIX versions in many places, e.g. `DOC:242`, `DOC:462`), but correct within the row's deployment scope: my grep for `rollback|revert|history` returns zero.
- Everything else I sampled checks out verbatim at the cited line, including: the whole §1 workflow table rows 0–23 and the Undeploy row; the code-block boundaries `DOC:710-748` / `DOC:785-800`; every §2 signature, super call, wrapper type, `getTtTraining()[0]`, `addValidationError`/`throwAddedValidationErrors` line numbers and ordering; the five "Java Extension APIs" bullets (`DOC:114-118`) and the four capability bullets (`DOC:95-98`), which are **verbatim, not stitched**; the F1 undeploy quote at `DOC:76-81`; the JDK-8-vs-17 contradiction at `DOC:179-181`/`DOC:290`/`DOC:298`/`DOC:312` vs `DOC:135`/`143`/`158`/`377-388`; the F3 gutter-line-6 crop and the mis-braced `DOC:743-746`; the workflow-table duplicate step numbers at `DOC:64-69`; and the "only four QAD palette commands" claim (my grep returns exactly Init app / Update app dependency / Build and Deploy / Undeploy at `DOC:541`, `543`, `628`, `634`, `758-761`, `775`).
- **No secret leaked.** The section reprints the training-environment hostname (`DOC:555`) and the field *names* "Client ID / Client Secret / Description" (`DOC:570`); the doc contains no client-id, secret, token or password value, and the section invents none.
- **Known systematic defect (HTTP-library-import sweep) does not apply here.** B2 makes no inventory or absence claim about AUX backend modules — it is a pure document audit, and its §5 "confirmed facts" are explicitly commissioner-supplied and not re-derived. I ran the prescribed sweep anyway (`grep -rn "qad_client\|get_qad\|post_qad" backend --include=*.py` in `aux_web_version`) and reproduced the ground truth (`get_qad` at pipeline.py:516, pipeline_embedded.py:240, probe_parent_eh.py:51 and :100; qad_client imported at pipeline.py:19, pipeline_embedded.py:18, core/lookup_generator.py:276, probe_parent_eh.py:22). Nothing in B2 depends on it.

---

# B4 — Platform tools / data admin / security — verdict: minor-issues

## flag 1 — [wrong]

**Claim as written:** Security Control key dump (PHASE0_AUDIT.md:4297) reproduces the literal value of the `Client ID` field read from C8:1011.

**Cited:** PHASE0_AUDIT.md:4297 citing C8:1000–1020

**What is actually there:** C8:1011 is a `Client ID` row in the Security Control screenshot table. The audit copies the 32-hex-character value verbatim into the report. Whether or not the training environment is live, this is a credential-shaped identifier propagated out of the source doc into a circulated audit; the surrounding key list (Idle Timeout, Administrator Role, password policy) carries the analytic value without it. Redact the value; keep the key name.

## flag 2 — [wrong]

**Claim as written:** "App URI — appears only as a *grid column heading*, never with a documented value or format, at C4:614, C4:823, and C4:55 (Lookup Definition list, columns 'Field URI | Reference | Browse URI | App')."

**Cited:** PHASE0_AUDIT.md:4151 citing C4:614, C4:823, C4:55

**What is actually there:** Two defects. (a) C4:55 has no `App URI` column at all — its columns are `Field URI | Reference | Browse URI | App`, exactly as the audit itself transcribes, so it cannot be an instance of `App URI`. (b) `App URI` is NOT only a grid heading: C4:77 lists it as a form field in the Lookup Definition Main section ("fields for Field URI, Field Label, Reference, App, App URI, and Namespace under the Main section") and C4:626 lists it as a form field on the Add-new-Browse form ("fields for Browse Label, Browse URI, Description, App, and App URI"). The section contradicts itself: PHASE0_AUDIT.md:4156 cites C4:77 for a Main-section field list that includes `App URI`. Full C4 occurrence set is 77, 614, 626, 823.

## flag 3 — [overstated]

**Claim as written:** "[CONFIRMED] The only import/export documented is Configuration Data artifact import/export (C5:467–506)" — and, in the §2 headline, "There is no record-level data import, no data loader, no CSV/spreadsheet load, no bulk data path."

**Cited:** PHASE0_AUDIT.md:4200, 4202 citing C5:467–506

**What is actually there:** C5:556 documents an `Import Data` checkbox with a `Filename` value (`BusinessComponentTrai...`) on the BC Deployment panel — a second, non-Configuration-Data import affordance. The same section quotes that exact line 24 lines later (PHASE0_AUDIT.md:4226, "Deployment panel keys (C5:553–557): … `Import Data` (checkbox); `Filename` = `BusinessComponentTrai...`"). The defensible claim is that the only import/export *procedure* documented is Configuration Data; a data-import control exists but is never explained.

## flag 4 — [overstated]

**Claim as written:** "**The only 'required setup order' statements that exist in the three docs** — quoted in full because they are the closest thing to prerequisites anywhere in this set" (list of six).

**Cited:** PHASE0_AUDIT.md:4412–4418

**What is actually there:** The list is not exhaustive. At least two further prerequisite statements exist and are omitted: C5:312 — "Check the Category settings and make sure that Alerts are yes for QAD Inbox" (an alert will not reach the Inbox otherwise); and C8:958 — "Of course, initially a Security Group should be defined, and you should define which users will be included there" (precondition for Record Level Security group rules). Neither appears anywhere in B4.

## flag 5 — [bad-citation]

**Claim as written:** Quoted as a single verbatim string: C5:704: "Then click Compile button (bottom right). Save handler and close editor." (same stitch at PHASE0_AUDIT.md:4236, "Finish order (C5:702–706)").

**Cited:** PHASE0_AUDIT.md:4415 citing C5:704

**What is actually there:** C5:704 reads only "Then click Compile button (bottom right)." The second sentence, "Save handler and close editor.", is C5:706 (C5:705 is blank). The quotation is stitched from two non-adjacent lines but presented under a single line citation.

## flag 6 — [overstated]

**Claim as written:** "[CONFIRMED] There is not a single HTTP/REST endpoint, URL, HTTP verb, or HTTP status code anywhere in these three documents … There is no `403`, no `500`, no `Forbidden`."

**Cited:** PHASE0_AUDIT.md:4136

**What is actually there:** I re-ran the sweep: the endpoint/verb/URL half holds (no http://, no /api, no GET/POST/PUT, no `Forbidden`). But the literal string `500` occurs twice in C8 — C8:326 (`Site: 10-500 (2 Roles)`) and C8:1007 (`Email System | 500`) — neither an HTTP status code. The claim is true as "no HTTP status code appears"; false as stated about the token `500`.

## flag 7 — [bad-citation]

**Claim as written:** "Approval example uses role `QMISuperNOAC` (C5:814, C5:892)."

**Cited:** PHASE0_AUDIT.md:4288 citing C5:814

**What is actually there:** C5:814 is the word "Set:". The QMISuperNOAC mention is C5:813 ("add CFO user or any other user with QMISuperNOAC role"). C5:892 is correct; C5:877 is a third instance.

## flag 8 — [bad-citation]

**Claim as written:** "KPI record keys (C4:950–976): … `Auto Refresh`, `Refresh Rate`, `Allow Manual Refresh`."

**Cited:** PHASE0_AUDIT.md:4191 citing C4:950–976

**What is actually there:** C4:950–976 ends at `Active Fields` / `Max: 20`. `Auto Refresh`, `Refresh Rate` and `Allow Manual Refresh` are at C4:1051–1053 (Refresh Options panel), 75 lines outside the cited range.

## flag 9 — [bad-citation]

**Claim as written:** "Configuration Data grid columns (C5:480) … example rows: `Artifact | Alert | Training Average Sc... | Training | | Active | 10/16/2023 7:51 PM | mfg` and `Artifact | Activity Tracking | Training | Training | Active`."

**Cited:** PHASE0_AUDIT.md:4202 citing C5:480

**What is actually there:** The first row matches C5:482. The second does not exist in the clean table: C5:483 is `| | Activity Tracking | Training | | | | |` — no `Artifact` type, no Business Component, no Status. The quoted form (`Artifact Activity Tracking Training Training Active`) comes from the raw OCR line C5:492. Two sources merged under one citation.

## flag 10 — [overstated]

**Claim as written:** "Developer settings — not covered in C4. The only occurrence in the whole set is a menu-bar OCR fragment, C5:159."

**Cited:** PHASE0_AUDIT.md:4150 citing C5:159

**What is actually there:** `My Developer Settings` also appears at C5:186 (the duplicate raw-OCR rendering of the same menu bar). Two occurrences, not one — the substantive point (contents never shown) is unaffected.

## flag 11 — [bad-citation]

**Claim as written:** "Confirmable by inspecting `backend/core/lookup_detector.py` in this repo against this rule — I did not open it."

**Cited:** PHASE0_AUDIT.md:4175

**What is actually there:** No such path exists in the repo hosting PHASE0_AUDIT.md (`D:/WEB_AUX/adaptive_java_version/backend/core/lookup_detector.py` — absent). The file is at `D:/WEB_AUX/aux_web_version/backend/core/lookup_detector.py`. B4's own preamble states "all paths relative to D:\WEB_AUX\", which this citation violates.

## flag 12 — [bad-citation]

**Claim as written:** [INFERRED] Predefined-search token form — "Basis: the component is `com.extensions.training.CountryIndustries` (cf. C4:685)".

**Cited:** PHASE0_AUDIT.md:4189 citing C4:685

**What is actually there:** C4:685 reads only "Select CountryIndustries and hit Enter." The fully-qualified name `com.extensions.training.CountryIndustries` appears nowhere in C4 (occurrences of `CountryIndustries`: 285, 681, 685, 854 — all bare). The inference is properly labelled, but its cited basis supplies only the short name.

## Missed — material items the section omitted

- Conditional Styling (C4:15 topic list; body C4:273–386) is one of C4's seven documented tools and is omitted entirely from the "[CONFIRMED] Tool-by-tool" inventory. It carries a concrete generator-relevant key set: reached via BC → Form panel → Edit Form → select column → Form Layout Properties → Conditional Styling gear (C4:285–291); record keys `Field Name` / `Display Label` and `Style Type` (= `Background Color`) with a `Condition | Preview` grid (C4:303–319); worked example of three operator/value/colour rules (C4:334–338).
- Alerts — one of C5's three stated topics (C5:18) and roughly 265 lines of the file (C5:200–465) — is never enumerated, though B4 enumerates key sets for Activity Tracking, KPIs and Approval Routing. Missing: Alert name, business-component selection, Conditions grid, `Alert Type` = "Send Alert When Conditions are Met" (C5:267–275), Message body with `Include Field` token insertion (C5:283–288), `Notification Options` = "Immediate (when conditions are first met)", alert receivers (C5:290–292), and the per-user prerequisite at C5:312 ("make sure that Alerts are yes for QAD Inbox").
- The Add-new-Browse creation form key set (C4:626: `Browse Label`, `Browse URI`, `Description`, `App`, `App URI`) is not captured, although the section does capture the Browse Fields grid columns. This is the closest thing in C4 to a create-payload shape for a browse and is directly load-bearing for a generator.
- §0.5 item 5 (PHASE0_AUDIT.md:312–315) attributes to B4 a diagnostic B4 does not make: "the UI's Package action dispatches an OS Script and surfaces its error text in the Inbox, so running the script directly may reveal the error the 500 swallows." B4 §6 Symptom A states only that OS Scripts report outcome asynchronously via Inbox (C5:196) and explicitly declines to offer a cause. No document in the set shows an OS Script error surfaced in the Inbox — every Inbox screenshot cited (C5:194, C4:1392, C8:625, C8:775) is a success notification. Either B4 should state the diagnostic and its evidentiary limit, or §0.5 should stop crediting it to B4.
- Not a defect, recorded for the orchestrator: the known systematic HTTP-library-grep defect does not apply to B4. B4 builds no "what talks to QAD" inventory and makes no absence or exhaustiveness claim about the AUX codebase — its single AUX reference (PHASE0_AUDIT.md:4175) is an explicit, correctly-labelled deferral, so there was nothing for the qad_client sweep to overturn here.

**PHASE0_AUDIT.md:4297** — remove the credential value; keep the key.
> …`Enabled Reason Type USER_ACT`, a `Client ID` field (value present at C8:1011 — **redacted here**; read it from the source doc if needed), plus password policy keys…

**PHASE0_AUDIT.md:4151** — replace the `App URI` bullet:
> - **App URI** — present as both a form field and a grid column, but **never with a documented value or format**. As a form field: C4:77 (Lookup Definition → Main section: `Field URI, Field Label, Reference, App, App URI, Namespace`) and C4:626 (Add-new-Browse form: `Browse Label, Browse URI, Description, App, App URI`). As a grid column: C4:614 and C4:823 (Browses panel: `Name, Browse URI, App, App URI`). Note C4:55 is *not* an instance — that list's columns are `Field URI | Reference | Browse URI | App`. The only actual `urn:app:` value in the set is C5:672.

**PHASE0_AUDIT.md:4200/4202** — qualify the import/export claim:
> **[CONFIRMED] The only import/export *procedure* documented is Configuration Data artifact import/export** (C5:467–506). One further import control exists but is never described: the BC Deployment panel's `Import Data` checkbox with `Filename` (C5:556, quoted in full below). There is no record-level data import, no data loader, no CSV/spreadsheet load and no bulk data path anywhere in C5.

**PHASE0_AUDIT.md:4412** — soften "only":
> **The "required setup order" statements in the three docs** — the closest thing to prerequisites anywhere in this set. Two further prerequisites sit outside the tools covered above: C5:312 (*"Check the Category settings and make sure that Alerts are yes for QAD Inbox"*) and C8:958 (*"initially a Security Group should be defined, and you should define which users will be included there"*).

**PHASE0_AUDIT.md:4415** — split the stitched quote:
> - C5:704: *"Then click Compile button (bottom right)."* and C5:706: *"Save handler and close editor."* (compile precedes save for event handlers)

Same fix at **4236**: `Finish order (C5:702, 704, 706): check Active → paste code into the TrainingFormHandler class → compile (C5:704) → save and close (C5:706).`

**PHASE0_AUDIT.md:4136** — narrow the status-code sentence:
> …There is no HTTP status code anywhere in the set — no `403`, no `Forbidden`. (The token `500` does occur twice, at C8:326 `Site: 10-500` and C8:1007 `Email System | 500`; neither is a status code.)

**PHASE0_AUDIT.md:4288** — `(C5:813, C5:877, C5:892)` — not C5:814.

**PHASE0_AUDIT.md:4191** — `…\`Active Fields\` / \`Max: 20\` (C4:950–976); \`Auto Refresh\`, \`Refresh Rate\`, \`Allow Manual Refresh\` (C4:1051–1053).`

**PHASE0_AUDIT.md:4202** — attribute the second row correctly:
> …example rows: `Artifact | Alert | Training Average Sc... | Training | | Active | 10/16/2023 7:51 PM | mfg` (C5:482) and a second row for `Activity Tracking`, which the clean table renders sparsely at C5:483 and the raw OCR at C5:492 renders as `Artifact Activity Tracking Training Training Active`.

**PHASE0_AUDIT.md:4150** — `The only occurrences in the whole set are two OCR renderings of the same menu bar, C5:159 and C5:186; the item exists in the Developer menu, its contents are never shown.`

**PHASE0_AUDIT.md:4175** — `Confirmable by inspecting \`aux_web_version/backend/core/lookup_detector.py\` against this rule — I did not open it (out of scope of this task).`

**PHASE0_AUDIT.md:4189** — `Basis: the component is named \`CountryIndustries\` (C4:285, C4:685); its package \`com.extensions.training\` is taken from the app URN (C5:672), not stated in C4.`

---

*Verified and holding, no change needed:* the complete `urn:` inventory in §4 — my own `grep -oE "urn:[A-Za-z0-9:._-]+"` across all three files returns exactly the 35 occurrences listed, in the order listed, with the 7 schemes correctly distinguished, including the OCR corruption at C5:861 and every truncation marker; `browseId` as the sole network-level payload key (C4:132, unique); the Lookup Relation vs Definition block (C4:251–269, verbatim); the event-handler skeleton and the C5:687 naming constraint; the C4:1327–1337 and C4:1404–1408 packaging blocks (verbatim; DEVL/TEST/PROD correct); the five-permission grid at C8:497–503 / C8:880–886 / C5:906–912; the `approve`-permission finding (C5:847/856/861, remedy C5:915–916, success C5:935–937); C8:812 `webui_user`; C8:485 `APIs` node (sole occurrence in the three files). I independently re-tested every absence claim with my own greps: `sandbox` (0 hits), `jar|core lib|dependen|librar` (0 hits), `permission` co-occurring with `creat|deploy|event handler` (only C5:920 and C8:485, both permission-grid renderings — the "genuine gap" claim at 4276 holds), `Initial` (occurrence set matches the cited ranges exactly), `Status` (the only BC status value in the set is `Deployed` at C5:636), and `metadata|source file|api source|proxy` (only C5:636). The stated line counts 1423/1061/1034 are correct — the files end without a trailing newline, so `wc -l` under-reports each by one.