# PHASE 4 — Case 3 (Java Server-Side Extensions) Build Plan

**Written 2026-08-14**, after the JEF chain was proven end to end on `eeadaptive`. Unlike the Case 2
plan, which was written from a document sweep and then corrected by captures, **every load-bearing
fact here was observed live**. Evidence: `captures/2026-08-13_jef_live_probe_and_jar.md`.

## What Case 3 produces

A **Java class that intercepts a Business Component's lifecycle on the server**, compiled into the
app's single extension jar and uploaded to QAD. Two validations already run in production this way:
`DigSmokeTestValidation` (our own BC) and `PurchaseOrderRemarksValidation` (a QAD-shipped BC).

It differs from Cases 1 and 2 in three ways that drive the whole design:

| | Cases 1 & 2 | Case 3 |
|---|---|---|
| Artifact | JSON payloads POSTed per artifact | **One jar per APP**, containing every extension |
| Deploy semantics | Additive; each write creates one thing | **Whole-jar replacement** — absent classes are DELETED |
| Undo | none found | **Rollback works**: redeploy without a class removes it |
| Structure source | LLM + builders | **`javap` on the dependency jar** — no inference at all |

## The five stages

Mirrors the Case 1/2 pattern: server-owned manifest, gate before every write, dry-run default,
regeneration free until a live write lands.

### Stage 1 — Requirements and target selection  *(gated, no write)*

The user says what rule they want. The model proposes the **target BC** and the **rule**; the user
confirms or overrides the BC from a picker.

The picker is **not** LLM-generated: it is read from the dependency jar, which holds **289
`*BaseService` classes** including all of ours and QAD's standard components. Selection is by
entity, not free text.

- **No write.** Downloading the jar (`jef.dependency_jar`, GET, 3.2 MB) writes only to local disk.
- Cache the jar per app with an explicit refresh, since it changes when BCs are added.
- Fixes AUX's biggest UX gap for the analogous SSS flow, where the target was inferred and errors
  surfaced only afterwards.

### Stage 2 — Target analysis  *(gated, no write, NO LLM)*

`javap` the chosen `<BC>BaseService`, `<BC>DataSet` and `<BC>Record` and present the truth:

1. **Every save path the base class exposes.** This is the stage's whole reason for existing.
   Standard BCs expose `create`/`update`/`delete` **and** `createWithConfirmation`/
   `updateWithConfirmation`/`deleteWithConfirmation`; entity-builder BCs expose only the plain trio.
   **Overriding only the plain pair on a coded BC produces a rule that compiles, deploys, returns
   200 and never fires** — observed distinction, not theory.
2. **The exact signatures**, which differ by BC family: standard take a bare `DataSet`, generated
   take `InputOutput<DataSet>`.
3. **The record's real fields and Java types**, e.g. `getRemarks(): String`,
   `getTestDate(): java.time.LocalDate`, including SQL-safe renames like `getStatusCode()`.
4. **The DataSet accessor**, `getTt<BC>()`, returning an **array** (not a `List`).

Gate shows the fields and asks which save paths to guard. Default: **all of them**.

### Stage 3 — Code generation  *(gated, editable, LLM writes only the body)*

Port `sss/templates.py`'s central insight verbatim: **the LLM produces only the validation body;
every structural element is generated deterministically so the output always compiles.**

Deterministic: `package com.yash.digwish;` (app package, no BC segment — proven), imports derived
from the jar, `@Extension`, `extends <BC>BaseService`, one override per selected save path each
calling `super`, the null-safe array loop, and `throwAddedValidationErrors()`.

LLM-authored: only the per-record predicate and its message.

Identity comes from `render()` substitution, never a literal — the discipline that keeps AUX's
`com.extensions.customapp` out of generated output.

### Stage 4 — Build  *(gated, no QAD contact — the highest-value rehearsal available)*

`mvn clean package` in the workspace. Fully dry-runnable and the strongest signal before anything
leaves the machine: it proves the code compiles against the real generated types.

⚠️ **Check the exit code and the filesystem, never a tool's success message.** The VS Code plugin
reports Maven success without checking exit codes, and Maven caches failed resolutions
(`.lastUpdated` markers that must be cleared before retrying). Verify `target/<fullAppName>-ext-cust.jar`
exists and inspect it with `jar tf`.

Gate shows the compile result, the jar path, and its class list.

### Stage 5 — Deploy  *(gated, IRREVERSIBLE in effect, terminal)*

```
POST {base}/api/qracore/sse/upload-packages?appURI={app_uri}
Authorization: Bearer <token>
multipart/form-data, ONE part:
    name="files"; filename="<fullAppName>-ext-cust.jar"
    Content-Type: application/java-archive
→ 200, content-length: 0, empty body
```

Success is the **HTTP status alone**: no `submitResult` envelope. Any non-2xx must be surfaced with
raw status and body — **no failure mode has ever been observed**, so pattern-matching would be
invention.

**The gate must show, because whole-jar replacement is silent:**

1. **Every class that will exist after this deploy** — the full list, not a diff.
2. 🔴 **A loud warning for any class in the last deploy but absent now.** It will be **deleted**,
   with no warning from QAD and a 200 either way. This is Case 3's sharpest hazard.
3. The resolved URL, the multipart part list, and the verified jar on disk.

**This requires a persisted deploy manifest per app.** There is no read-back endpoint, so the tool
can only diff against its own record of what it last deployed. Build it before the first gated
deploy, not after.

⚠️ **Do not depend on the VS Code plugin.** It fails on this environment (`socket hang up`) while
our client succeeds, so direct deployment is the only working path, not a convenience.

### Stage 6 — Verify  *(gated, no write)*

A 200 proves QAD accepted an upload, nothing more. The gate states the manual test explicitly:
open the screen, trigger the rejection path, then the accept path. Expect the message in the Web UI
**Errors** grid with a `JEF…` Error ID.

## Design decisions worth stating

**Case 3 runs are app-scoped, not artifact-scoped.** Cases 1 and 2 create one thing per run. Here
the unit of deployment is the whole app. The store must therefore track extensions per app across
runs, and Stage 5 must consider classes it did not create in this run.

**The workspace is real, external and shared.** `JEF_WORKSPACE_DIR` points at the folder holding
`pom.xml`, `lib/`, `src/`, `config/`. It survives runs and may contain hand-written classes. Never
adopt AUX's `_clean_stale_ts` pattern of deleting other sources: under whole-jar semantics that
would silently erase deployed behaviour.

**No `…WithConfirmation` guessing.** The save-path set comes from `javap` per target, every time.

## Open items, named

| # | Item | Effect |
|---|---|---|
| 1 | What a REJECTED deploy looks like | Unknown; treat any non-2xx as failure, surface raw |
| 2 | Whether two extension classes may target one BC | Deck says yes, owner's rule is one until tested |
| 3 | Whether the extension jar may hold non-extension helper classes | Untested; assume yes, verify |
| 4 | `data/` in the scaffold | Purpose never documented |

## Suggested build order

1. `core/jar_inspector.py` — run `javap`/`jar tf`, parse into save paths, fields and types. Pure,
   testable, no network. Everything else depends on it.
2. `builders/extension_builder.py` — deterministic class scaffolding.
3. `core/maven.py` — build with real exit-code and filesystem verification.
4. Deploy manifest in the store, plus the erase-warning logic.
5. Stage functions and manifest entries; `mode="serverside"`.
6. Prompts, frontend artifact kinds, tests.

Steps 1-4 are fully testable offline against the jar we already have.
