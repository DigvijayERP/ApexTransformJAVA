# SESSION HANDOFF — read this first

**Updated 2026-08-14.** For a Claude session with an empty context window picking this project up.
A new chat inherits NOTHING except these files. This one is the entry point; read it fully, then
read only what it points you at.

---

## What this project is

`adaptive_java_version` ("Adaptive") generates QAD Adaptive artifacts through **human-gated stages**:
a dialog before every write, showing the exact payload, and dry-run is the default. It was ported
from `aux_web_version` ("AUX"), which is **read-only reference — never modify it**.

Python/FastAPI backend, React + Vite frontend. Live environment
`https://eeadaptive.yash.com:33005/clouderp`, app `digwish`, module `com.yash.digwish`.

## Status: three cases, all built and PROVEN LIVE against real QAD

| Case | Mode | What it does | State |
|---|---|---|---|
| 1 | `standard` | Standalone BC: fields, form, event handler, view, lookups, deploy | Working live |
| 2 | `embedded` | Child BC embedded under a parent, via a BERelation | Working live |
| 3 | `serverside` | Java server-side validation: generate, compile, deploy | Working live |

Nothing is half-finished. The next work is refinement, not construction.

## Run it

Two terminals (the owner runs servers in their own cmd windows; do not background them):

```
cd /d D:\WEB_AUX\adaptive_java_version\backend && python -m uvicorn main:app --reload --port 8000
cd /d D:\WEB_AUX\adaptive_java_version\frontend && npm run dev
```

Then **http://localhost:5174** (5173 is AUX; the port is pinned deliberately).

Tests, all offline, none contact QAD:

```
cd /d D:\WEB_AUX\adaptive_java_version\backend
python smoke_test.py && python pipeline_test.py && python core/jar_inspector_test.py && python core/maven_test.py && python core/jef_deploy_test.py && python builders/extension_builder_test.py && python core/progress_parser_test.py
```

## What is deployed on QAD right now

- BCs created by this app, all live: `DigSmokeTest`, `DigOrderTesting`, `DigPoInspection`,
  `DigSoPacking`, plus failed leftovers (`DigOrderTest`, `DigLookupTest`, `DigLookupTest2`) that are
  harmless and undeployed.
- **Java extensions: only `ExtensionsPlaceholder`** — an inert class with no `@Extension` and no
  BaseService parent. QAD rejects an EMPTY jar (400, "does not contain any signed entries"), so
  "no extensions" has to be expressed as a jar holding that one placeholder. Keep it in the
  workspace permanently.
- The store's `jef_deploys` table is the ONLY record of what is deployed. QAD cannot be asked.

## Read these, in this order, and skip the rest

1. **`PROGRESS.md`** (1100+ lines) — the running narrative, newest at the bottom. The last ~250
   lines cover Cases 2 and 3. **Read the bottom first.**
2. **`captures/2026-08-13_jef_live_probe_and_jar.md`** — the Case 3 wire contract, all of it
   observed, including the deploy multipart shape and both failure modes.
3. **`captures/2026-08-12_embedded_EmbeddedExmpl2.md`** — the Case 2 wire contract.
4. **`PHASE4_CASE3_BUILD_PLAN.md`** and **`PHASE3_CASE2_DISCOVERY.md`** — only if changing those cases.

⚠️ **Do NOT read `PHASE0_AUDIT.md` (583 KB), `QUESTIONS.md`, or `VERIFICATION_ROUND2.md` end to
end.** They are Phase 0 archaeology. Grep them for a specific question; reading them will eat the
context window for very little.

`SERVERSIDE_HANDOFF.md` (83 KB) is a document from another session about the Java side. It was
useful and is now largely superseded by the capture in item 2, which is evidence rather than
inference. Grep, do not read.

## The hard-won facts that are easy to get wrong

1. **Wire JSON keys are camelCase.** Entity metadata reports field CODES in PascalCase; those are
   different things. Asking an entity to describe itself tells you about the entity, not the wire.
2. **`sql_safe` renames SQL reserved words.** `DomainCode` → `domainCd`, `status` → `statusCode`.
   Codes are normalized ONCE, at the field stage; every consumer reads the spec verbatim after.
3. **Standard QAD BCs expose `createWithConfirmation`/`updateWithConfirmation`; generated ones do
   not.** The QAD UI saves through the confirmation path. An extension overriding only
   `create`/`update` on a coded BC compiles, deploys, returns 200 and **never fires**. Always read
   the save paths with `javap` (`core/jar_inspector.py` does this) and override every one.
4. **Sibling components are a trap.** `PurchaseOrder` and `PurchaseOrderHeader` both have a
   `remarks` field; only the latter has confirmation variants. The target gate flags this.
5. **A JEF deploy replaces the WHOLE jar.** Classes absent from the upload are deleted, silently,
   with 200 either way. Rollback works and is proven; the hazard is that it is invisible.
6. **Embedded BCs cannot have a standalone menu view.** Proven three ways. The stage was removed.
7. **The VS Code plugin cannot deploy on this environment** ("socket hang up", its own HTTP layer).
   Adaptive's direct upload works and is the only working path.
8. **On Windows, resolve executables with `shutil.which`.** `mvn` is `mvn.cmd` and `subprocess` does
   not apply PATHEXT, so a bare name works in a terminal and fails from code.

## Working rules the owner expects

- **Nothing writes to QAD without an explicit greenlight.** Dry-run is the default and must report
  exactly what it would send: endpoint, method, headers, payload. Reads (GETs) are free.
- **Never guess.** Read the code; if still unclear, stop and ask, with a suggested answer.
- Distinguish `[CONFIRMED]` from `[INFERRED]` and cite `file:line`.
- **Verify against the filesystem or a read-back, never a success message.** This has caught real
  bugs repeatedly: a tool reporting success is not evidence.
- Named deferrals, not silent omissions.
- `aux_web_version` is READ-ONLY.
- **No em-dashes in user-visible product copy.**
- Record every meaningful finding in `PROGRESS.md` as you go, so the next session can continue.

## Open items, honestly

- **Case 3 has never been driven live from the browser.** The backend is proven and a full dry run
  passes end to end; the UI is exercised but no live deploy has been made through it.
- **No in-place Java editor** at the code gate. The backend accepts hand-edited source; the UI only
  regenerates via the steer box.
- `lookupResultFields` element VALUE formats (D8) and a few Phase 0 questions (Q-L, Q-F) remain
  open. See the Deferrals table at the end of `PROGRESS.md`.
- Leftover undeployed test BCs in QAD, and an empty duplicate scaffold at
  `Desktop\Python_Snake\urn_app_com.yash.digwish` that should be deleted (deploying from it would
  upload a classless jar).

## Paste this into the new chat

> Read `D:\WEB_AUX\adaptive_java_version\SESSION_HANDOFF.md` in full, then the last 250 lines of
> `PROGRESS.md`. Do not read PHASE0_AUDIT.md, QUESTIONS.md or VERIFICATION_ROUND2.md — grep them if
> you need something specific. Then tell me what you understand the current state to be, and what
> you think the next step is, before doing anything.
