# SESSION HANDOFF — read this first

**Updated 2026-09-02.** For a session with an empty context window picking this project up.
A new chat inherits NOTHING except these files. This one is the entry point; read it fully,
then read only what it points you at.

---

## What this project is

`adaptive_java_version` ("Adaptive", branded **ApexTransform** in the UI) generates QAD
artifacts through **human-gated stages**: a dialog before every write, showing the exact
payload, and dry-run is the default. It was ported from `aux_web_version` ("AUX"), which is
**read-only reference — never modify it**.

Python/FastAPI backend, React + Vite frontend. Live environment
`https://eeadaptive.yash.com:33005/clouderp`, app `digwish`, module `com.yash.digwish`.

GitHub: https://github.com/DigvijayERP/ApexTransformJAVA (**public**). Local branch is
`master`, it tracks `origin/main`. Plain `git push` works.

## 🔴 START HERE: the one open problem

**Pasted ABL gives a wrong field list.** The owner pasted two real QAD files and the
generated BC got **9 fields out of the 23 the source describes**, with the wrong primary
key and a line-item field mixed into the header.

Full analysis is the last entry in `PROGRESS.md` ("OPEN, START HERE NEXT"). The short
version: neither file contains `DEFINE TEMP-TABLE`, so nothing parses deterministically and
the model guesses from raw text. **The first move is to ASK THE OWNER for the include file
that holds `define temp-table ttEkDc_mstr`.** Do not design around its absence before asking.

Sample files, still on disk:
`C:\Users\digvijay.parmar\Downloads\gpekpohu.p.txt` and `...\gpekpohu.i.txt`.

## Status: four cases, all built, all proven live

| Case | Mode | What it does | State |
|---|---|---|---|
| 1 | `standard` | Standalone BC: fields, form, event handler, view, lookups, deploy | Working live |
| 2 | `embedded` | Child BC embedded under a parent, via a BERelation | Working live |
| 3 | `serverside` | Java server-side validation: generate, compile, deploy | Working live |
| 4 | stage 5 of `embedded` | Screen validation: rules on the parent screen's event handler | Working live |

Case 4 detail is in `PHASE5_CASE4_BUILD_PLAN.md`. It was proven on 2026-09-01: a weight rule
and a date rule both blocked bad saves on the Sales Orders screen, and the second run kept
the first rule.

## Run it

Two terminals (the owner runs servers in their own cmd windows; do not background them):

```
cd /d D:\WEB_AUX\adaptive_java_version\backend && python -m uvicorn main:app --reload --port 8000
cd /d D:\WEB_AUX\adaptive_java_version\frontend && npm run dev
```

Then **http://localhost:5174** (5173 is AUX; the port is pinned deliberately).
Adding a NEW route file needs a real backend restart; the reloader misses those.

Tests, all offline. **Always set `ADAPTIVE_OFFLINE=1`:**

```
cd /d D:\WEB_AUX\adaptive_java_version\backend
set ADAPTIVE_OFFLINE=1
python smoke_test.py && python pipeline_test.py && python api_test.py && python store_test.py
python core/progress_parser_test.py && python core/browse_catalog_test.py
python routers/browses_test.py && python builders/screen_rule_builder_test.py
python core/jar_inspector_test.py && python core/maven_test.py && python core/jef_deploy_test.py
python builders/extension_builder_test.py
cd /d D:\WEB_AUX\adaptive_java_version && frontend\node_modules\.bin\tsc -p frontend/tsconfig.json --noEmit
```

## What is deployed on QAD right now

- BCs created by this app: `DigSmokeTest`, `DigOrderTesting`, `DigPoInspection`,
  `DigSoPacking`, `DigWoTracking`, `OrderNotes`, `SalesOrderPalletDetails`, `PalletDetails`,
  `HungaryOne`, `EntityURI`, `DeliveryReq`, `PoInspect`, plus older failed leftovers.
- ⚠️ **Junk awaiting the owner's go to delete**: `PoInspect` (created by a review agent's
  test harness by accident), `EntityURI` and `DeliveryReq` (fallout from the name-clash bug).
  **No delete path is proven.** Step one is a read-only look at what QAD offers.
- Event handlers under our app: Sales Orders (active, carries our rules), Purchase Orders
  (active, carries a weight rule).
- **Java extensions: only `ExtensionsPlaceholder`** — an inert class. QAD rejects an EMPTY
  jar, so "no extensions" must be expressed as a jar holding that one placeholder. Keep it.
- The store's `jef_deploys` and `handler_writes` tables are the ONLY record of what is
  deployed. QAD cannot be asked.

## Read these, in this order, and skip the rest

1. **`PROGRESS.md`** (1600+ lines) — the running narrative, newest at the bottom. **Read the
   last ~400 lines.** Everything from 2026-08-31 onward is Case 4 and the tooling around it.
2. **`PHASE5_CASE4_BUILD_PLAN.md`** — the screen-validation design and its wire contract.
3. **`captures/2026-08-13_jef_live_probe_and_jar.md`** — the Case 3 wire contract.
4. **`captures/2026-08-12_embedded_EmbeddedExmpl2.md`** — the Case 2 wire contract.

⚠️ **Do NOT read `PHASE0_AUDIT.md` (583 KB), `QUESTIONS.md`, `VERIFICATION_ROUND2.md` or
`SERVERSIDE_HANDOFF.md` end to end.** Grep them. Reading them eats the context window for
very little.

## The hard-won facts that are easy to get wrong

1. **Wire JSON keys are camelCase.** Entity metadata reports field CODES in PascalCase;
   those are different things.
2. **`sql_safe` renames SQL reserved words.** `DomainCode` → `domainCd`, `status` →
   `statusCode`. Codes are normalized ONCE, at the field stage.
3. **Standard QAD BCs expose `createWithConfirmation`/`updateWithConfirmation`; generated
   ones do not.** For Java (Case 3), `javap` the target and override EVERY save path.
4. **A JEF deploy replaces the WHOLE jar.** Classes absent from the upload are deleted,
   silently, with 200 either way.
5. **Embedded BCs cannot have a standalone menu view.** Proven three ways. Stage removed.
6. **On Windows, resolve executables with `shutil.which`.** `mvn` is `mvn.cmd`.
7. **A QAD screen loads its handler once.** After registering a handler you must refresh the
   QAD screen (Ctrl+F5) or it keeps running the old code. This caused a whole "the validation
   does not work" investigation; the code was fine.
8. **QAD's Compile button is a client-side type check.** No network call, produces no code.
   Our own checker (`backend/qad_compile/`) reproduces it with QAD's real typings.
9. **Browse field names come back complete and their shape varies per browse**:
   `digSmokeTest.testCode`, `debtor.DebtorCode`, but bare `pt_part` and `changeStatus`.
   **Never compose `<entity>.<column>`.** Use QAD's list verbatim.
10. **`urn:browse:mfg:<code>` is a real browse URI.** 3,357 of them are in
    `config/browses.json`. The export's `Lookup` column is NOT a usable filter: QAD's own
    guide uses a browse marked `Lookup=No` as a lookup.
11. **`bc.metadata.read` is a reliable name-availability check.** One row means taken, none
    means free. Used before every field-stage write now.
12. **Numeric fields need a real display format.** An empty one is accepted for character and
    rejected for integer (error 393).
13. **The concurrency hash does not rotate on an identical update**, so a stored hash is
    never safe to reuse. GET immediately before every POST.
14. **Screen names (view URIs) cannot be derived or guessed.** A wrong one returns "does not
    exist" exactly like a right one with no handler, so a wrong guess fails silently. Only
    Purchase Orders and Sales Order Headers are confirmed, both from the owner's DevTools
    capture. Items and Work Order Masters are NOT on record.

## Working rules the owner expects

- **NEVER ASSUME. Read the code first.** Do not start work on a claim you have not checked in
  the actual files. If something is unclear, **stop and ask, and include your own suggested
  answer** so the owner can just say yes or no.
- **Nothing writes to QAD without an explicit greenlight.** Dry-run is the default and must
  report exactly what it would send. Reads (GETs) are free.
- **Verify against the filesystem or a read-back, never a success message.** This has caught
  real bugs repeatedly, including in this project's own test suites.
- Distinguish `[CONFIRMED]` from `[INFERRED]` and cite `file:line`.
- **Plain, simple language.** No fancy words, in chat and in docs. No em-dashes in
  user-visible product copy.
- Named deferrals, not silent omissions.
- `aux_web_version` is READ-ONLY.
- Record every meaningful finding in `PROGRESS.md` as you go.
- **Set `ADAPTIVE_OFFLINE=1` in every test process.** A review agent's harness once deployed
  a real BC to QAD by stubbing one endpoint and forgetting the rest.

## Tooling built recently, worth knowing about

- `backend/qad_compile/` — QAD's own TypeScript typings and compiler settings, extracted by
  the owner. The screen-rule compile gate uses it. TypeScript is pinned to **exactly 5.7.2**;
  `base.json` is frozen. A half-installed kit is reported as a broken environment, never as a
  pass.
- `config/browses.json` + `backend/core/browse_catalog.py` — 3,357 browses, deterministic
  scored search, wired into the lookup gate and the handler `{{BROWSE_URI:...}}` placeholders.
- `backend/routers/browses.py` — `GET /api/browses/fields?uri=` returns the real field list
  for a browse so the lookup gate offers a dropdown instead of a text box.
- `backend/probe_eventhandler.py` — the event-handler read/write probe that settled Q-L.

## Open items, honestly

- 🔴 **The pasted-ABL field list** (top of this file). Everything else is smaller.
- Junk BCs to clean up, no proven delete path, needs the owner's go.
- Screen names for Items and Work Order Masters, one DevTools capture each.
- Labels stop at the BC: the browse view and the lookup display list still derive labels from
  the field code, so a field can read "Vehicle 1" on the form and "Veh Ref1" in the browse.
- D12: using our own standalone BCs as embedded parents. Analysed, not built.
- D11: a stale concurrency hash has never been observed being rejected.
- The rest of the Deferrals table at the end of `PROGRESS.md`.

## Paste this into the new chat

> Read `D:\WEB_AUX\adaptive_java_version\SESSION_HANDOFF.md` in full, then the last 400 lines
> of `PROGRESS.md`. Do not read PHASE0_AUDIT.md, QUESTIONS.md, VERIFICATION_ROUND2.md or
> SERVERSIDE_HANDOFF.md end to end; grep them if you need something specific.
>
> Work rules for this project, follow them exactly:
> - Never assume anything. Before you answer or change anything, read the actual code and
>   config in the repo and confirm what is really there. "I think it works like X" is not
>   acceptable; "I read file:line and it does X" is.
> - Never start work without the full context of the part you are touching. Read the whole
>   function or file, not a grep hit.
> - If you have any doubt, stop and ask me. Always include your own suggested answer with the
>   question so I can just agree or correct you.
> - Use plain simple language, no fancy words.
> - Nothing is written to QAD without my explicit go. Reads are free.
> - Verify by reading back from the filesystem or QAD, never by trusting a success message.
>
> Then tell me what you understand the current state to be, what the open problem is, and what
> you think the next step is, before doing anything.
