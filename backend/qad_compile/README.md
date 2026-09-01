# QAD compile kit (vendored)

This folder is a vendored copy of the local rebuild of QAD's editor
type-check. Provenance: extracted from the live QAD Adaptive UX editor and
validated against its Compile button. The full contract and the extraction
story live in the handoff document:

    C:\Users\digvijay.parmar\Downloads\QAD_COMPILE_CHECK_HANDOFF.md

## Frozen rule

- `qad-typecheck/typings/base.json` is a byte-for-byte snapshot of the 15
  framework typings the editor loads. Never edit it by hand. Refresh only
  with the procedure in section 8 of the handoff (after a QAD upgrade).
- The compiler options in `qadCompile.js` are captured from the live editor.
  Do not change them or results diverge from QAD.
- `typescript` is pinned exactly to `5.7.2` in `package.json`. Newer majors
  break the script. Verify after install:

      node -e "const ts=require('typescript'); console.log(ts.version, ts.ModuleKind.None)"
      # must print: 5.7.2 0

## What is here

- `qadCompile.js` - `compileHandler(source, extraTypings)` plus the kit's own
  CLI. One local change from the original: the generator require is lazy,
  because the generator is not shipped (see below).
- `check.js` - the shim this backend actually calls:
  `node check.js <handler.ts> [extra1.d.ts ...]`. Same JSON contract as the
  handoff: exit 0 OK, 1 ERRORS, 2 FATAL. FATAL is never a pass.
- `qad-typecheck/typings/base.json` - the frozen framework typings.

## What is NOT here (on purpose)

v1 does not use the per-component DTO/Constants generator
(`generateTypings.js`, `templates/`). It has known gaps (handoff section 7:
the Constants suffix rule is guessed from one component, and grid components
get an empty Row interface). The backend supplies its own any-typed view
namespace stub instead. When per-component typings are wanted, follow the
handoff (fetch the real `<ns>_DTO.ts` / `<ns>_Constants.ts` files per
component instead of generating them).

## Install

    cd backend/qad_compile
    npm install
