# Phase 5 / Case 4 — parent-view event handler validations (embedded fields)

**Written 2026-08-31, after the live probe settled Q-L.** Design is evidence-first: every
load-bearing claim below is tagged [CONFIRMED] with a source, or [INFERRED] with the test that
settles it. Owner decisions from 2026-08-31 are baked in: standalone flow first, BEFORE timing
default, merge = byte-preserve outside delimited insertion points.

## 1. What this case does

A save-time validation on a STANDARD parent screen (e.g. Purchase Orders) whose rule reads
fields of an embedded child BC (e.g. DigPoInspection) and/or parent fields, blocks the save,
and shows an error in the QAD Web UI error grid. Client-side TypeScript event handler on the
parent view, owned by our app. Delete of a rule = same stages, marker block removed.

## 2. Wire contract — all [CONFIRMED] live 2026-08-31 (`backend/probe_eventhandler.py`, PROGRESS entry)

| Act | Contract |
|---|---|
| Read | `GET eventhandler?appURI&viewURI&eventHandlerType&appliesTo` → `data.eventHandlerV2s[]`: `uri`, `concurrencyHash`, `typeScriptCode`, `javaScriptCode`, `mappingCode`, `disallowedActions`, `isActive` |
| Absence | HTTP 200 + `ok=false` + "…does not exist" — BRANCH to create, do not fail |
| Create | POST without `uri`/`concurrencyHash` (Case-1 `eventhandler.register` contract, proven by DigOrderTesting) |
| Update | POST echoing `uri` + `concurrencyHash` → true in-place update, one row after, byte-identical round-trip |
| Identity | row `uri` percent-encodes the 4-tuple (app, view, timing, appliesTo) → one row per tuple |
| Scoping | endpoint is app-scoped; other apps' and QAD's own handlers are invisible → unclobberable by us |
| Hash | does NOT rotate on identical content; stale-hash rejection UNOBSERVED (D11) → always GET immediately before POST |
| PurchaseOrders view URI | `urn:view:viewmeta:com.qad.erp.purchasing.PurchaseOrders` [CONFIRMED — returned a real row] |

## 3. The code shape — from QAD's own scaffold + class-7's worked example

The training guide's "Using of data from the extension" (class 7 pp.18-23) is EXACTLY this
case: Countries parent + CountryExtension embedded form + CountryIndustries embedded grid,
validated at save. [CONFIRMED]

- Module name encodes view namespace + app + timing:
  `com.qad.erp.purchasing.EventHandler.PurchaseOrders.ComYashDigwish.Maint_BEFORE`
  [CONFIRMED — read from our own scaffold row]
- Class names are LOAD-BEARING (`<View>MaintHandler`, `<View>FormHandler`): "Do not change
  this class name or the event handler will no longer run" [CONFIRMED — scaffold + docs]
- Base classes: `QraViewTSHandlerWithViewFormTSHandler<DTO.<View>Maint, <View>FormHandler>`
  overriding `createViewFormTSHandler()`; `QraViewFormTSHandlerV2<DTO.<View>Maint>` [CONFIRMED]
- Save hook: `onBeforeUpdate(eventData, processEvent)` — fires "for either a create or update
  operation" [CONFIRMED — API reference:26-31]. Delete rules use `onBeforeDelete`. There is no
  onBeforeCreate.
- Blocking: `eventData.eventProcessed = true` + build `Qad.Common.DTO.Error` objects
  (`{message, fieldName, severity: 1}`) + `ViewController.ErrorGroupPanel.clearErrorGrid() /
  addErrorsToErrorGrid(errors) / showErrorGrid()` [CONFIRMED — class 7 p.23 verbatim example]
- Import needed beyond scaffold: `import Error = Qad.Common.DTO.Error;` [CONFIRMED — same]
- Parent record: `this.NgData.<rootCollection>[0]` (guide: `trainings[0]`) — root collection
  name for PurchaseOrders [INFERRED]
- Embedded child rows: `this.NgData._com_extensions_training_CountryIndustries` pattern →
  ours: `_com_yash_digwish_DigPoInspection` [INFERRED — the scaffold's JS bundle contains no
  DigPo* strings, so unverified]. MITIGATION: the generated code resolves the key at runtime:
  `Object.keys(this.NgData).find(k => k.endsWith("_DigPoInspection"))`, with a clear error
  when absent. The first behavioural test settles the rule.
- Grid EVENT handlers (`ViewGridsToHandleList` — an opt-OUT filter per API ref:832 — and
  `createViewGridTSHandler`) are NOT needed for save-time validation. D3/Q-F stays deferred
  and no longer blocks this case. [CONFIRMED — class-7 example uses neither]

## 4. The merge algorithm — deterministic, uniform, no LLM near existing code

1. GET the handler at stage time. Classify: `absent` | `scaffold-only` | `has-logic`.
2. TS: insertions at exactly three deterministic points, each wrapped in
   `// ── ADAPTIVE MANAGED <slug> ── (do not edit inside)` markers:
   imports (after last `import`), rule method(s) into the Maint class body (before its closing
   brace), optional helpers. Everything outside markers is BYTE-PRESERVED. Re-runs replace
   only our own marker blocks (idempotent). `absent` → the whole file is generated from the
   scaffold template above.
3. JS: the stored bundle is NEVER re-transpiled (it holds compiled DTO/Constants we do not
   have sources for). We append one delimited ES5 IIFE that prototype-patches the Maint class:
   `com...Maint_BEFORE.<View>MaintHandler.prototype.onBeforeUpdate = function …`.
   Feasible because exported classes are attached to the namespace object
   [CONFIRMED — observed `Maint_BEFORE.PurchaseOrdersFormHandler = …` in the bundle].
4. Both our TS block and our JS patch come from REAL tsc (frontend/node_modules/typescript),
   compiled against generated ambient stubs (`declare namespace Qad…`), never from the LLM
   transpile path Case 1 uses. The LLM writes ONLY the rule body inside a fixed method
   skeleton — Case 3's "model writes only the check" discipline.
5. The gate shows a DIFF (old TS vs merged TS, old JS vs appended JS): "untouched" is
   verifiable, not promised.

## 5. Stages — four gates, mirrors Case 3

| # | Stage | Writes | Content |
|---|---|---|---|
| 1 | Target & rule | no | Parent view + child BC + fields; rule in plain English; fetch existing handler (read) and show classification + `isActive` + current code |
| 2 | Handler code | no | Merged TS + JS patch, diff view, marker blocks visible; steer regenerates rule body only |
| 3 | Compile | no | tsc on merged TS (--noEmit) + tsc emit of the patch; readable one-line errors |
| 4 | Register | YES | POST create/update. Gate must state: activation change (`isActive` false→true is part of adopting the scaffold), full diff again, and that the pre-merge original is stored for one-POST rollback |

Store: new `handler_writes` table — view URI, timing, pre-write TS/JS verbatim, post-write
hash, rule slugs present after the write. The only record of what we changed; rollback = POST
the stored original (update semantics proven).

## 6. Safety rails

- Dry-run default; stage 4 shows exact endpoint/method/payload (working rule 5).
- GET immediately before every POST; never reuse a stored hash (D11).
- Wrong-app clobbering is structurally impossible (app-scoped endpoint) [CONFIRMED].
- Non-2xx and `submitResult` errors surface raw; absence-error branch never masks a real error.
- A handler with existing logic that FAILS our tsc gate on its own code → STOP and surface;
  never "fix" code we did not write.

## 7. Live verification sequence (each write owner-gated)

1. Offline: builder unit tests — marker idempotency, byte-preservation, absent/scaffold/logic
   classification, tsc gate, ambient stubs.
2. Dry run end to end on PurchaseOrders + DigPoInspection rule.
3. Live register (adopts + activates the owner's inactive scaffold — owner confirmed adoption).
4. Behavioural: owner saves a PO violating the rule in the QAD UI → expect blocked save +
   error grid message; then a conforming save succeeds. This single test also settles the
   NgData naming inference and "does onBeforeUpdate see child-grid edits".

## 8. Out of scope, named

- Grid EVENT handling (live per-cell reactions) — D3/Q-F unchanged, needs its own two-arm
  experiment (SERVERSIDE_HANDOFF G.2).
- Deleting a whole handler ROW (no DELETE observed; deactivation via `isActive=false` covers
  retreat).
- MOBILE appliesTo; PRIMARY/AFTER timings (parameterised already, untested here).
- Wiring the stage into embedded-mode runs — second increment after the standalone flow works.
