// qadCompile.js — QAD Adaptive UX event-handler type check
// Requires: npm install typescript@5.7.2 (exact pin)
"use strict";

let ts;
try { ts = require("typescript"); }
catch (e) { console.error(JSON.stringify({ status: "FATAL", message: "typescript not installed. Run: npm install typescript@5.7.2" })); process.exit(2); }
if (!ts.ModuleKind || !ts.createProgram) { console.error(JSON.stringify({ status: "FATAL", message: "typescript module invalid" })); process.exit(2); }

const fs = require("fs");
const path = require("path");

const BASE = JSON.parse(fs.readFileSync(path.join(__dirname, "qad-typecheck", "typings", "base.json"), "utf8"));
// Vendored copy note: generateTypings.js is NOT shipped in v1 (see README.md),
// so its require is moved into the CLI fallback below. compileHandler and the
// compiler options are unchanged from the original kit.

// Exact options captured from the QAD Monaco editor
const compilerOptions = {
  target: ts.ScriptTarget.ES5,                        // 1
  module: ts.ModuleKind.None,                          // 0
  moduleResolution: ts.ModuleResolutionKind.Classic,   // 1
  allowNonTsExtensions: true,
  noEmit: true,
  noLib: true, // lib.es5/lib.dom come from base.json, same versions as the editor
};

const HANDLER = "handler.ts";

function compileHandler(source, extraTypings = {}) {
  const files = { ...BASE, ...extraTypings, [HANDLER]: source };

  const host = {
    getSourceFile: (name, langVersion) =>
      files[name] !== undefined ? ts.createSourceFile(name, files[name], langVersion) : undefined,
    getDefaultLibFileName: () => "../lib.es5.d.ts",
    writeFile: () => { },
    getCurrentDirectory: () => "",
    getCanonicalFileName: (f) => f,
    getNewLine: () => "\n",
    useCaseSensitiveFileNames: () => true,
    fileExists: (name) => files[name] !== undefined,
    readFile: (name) => files[name],
  };

  const program = ts.createProgram(Object.keys(files), compilerOptions, host);
  const diagnostics = ts
    .getPreEmitDiagnostics(program)
    .filter((d) => d.file && d.file.fileName === HANDLER);

  return diagnostics.map((d) => {
    const pos = d.file.getLineAndCharacterOfPosition(d.start);
    return {
      line: pos.line + 1,
      column: pos.character + 1,
      code: "TS" + d.code,
      message: ts.flattenDiagnosticMessageText(d.messageText, "\n"),
    };
  });
}

// ---- CLI: node qadCompile.js <handler.ts> ----
if (require.main === module) {
  const file = process.argv[2];
  if (!file) { console.error(JSON.stringify({ status: "FATAL", message: "usage: node qadCompile.js <handler.ts>" })); process.exit(2); }

  const source = fs.readFileSync(file, "utf8");

  // DigWish metadata for now; your agent passes real metadata per component
  const digwishMeta = {
    appNamespace: "com.yash.digwish",
    componentName: "DigOrderTesting",
    fields: [
      { name: "statusCode", type: "string" },
      { name: "customerReference", type: "string" },
      { name: "quantity", type: "number" },
      { name: "orderCode", type: "string" },
      { name: "orderDate", type: "Date" },
    ],
  };

  // Belt-and-braces for testing DigWish handlers: use the ORIGINAL captured
  // DTO/Constants (ground truth) instead of generated ones, so this test
  // validates the compiler — not the generator.
  let extra;
  try {
    extra = {
      "com_yash_digwish_DTO.ts": fs.readFileSync(path.join(__dirname, "qad-typecheck", "templates", "dto.reference.ts"), "utf8"),
      "com_yash_digwish_Constants.ts": fs.readFileSync(path.join(__dirname, "qad-typecheck", "templates", "constants.reference.ts"), "utf8"),
    };
  } catch (e) {
    // Vendored copy note: neither templates/ nor generateTypings.js ship in
    // v1, so this fallback reports a broken environment instead of guessing.
    try {
      extra = require("./qad-typecheck/generateTypings").buildExtraTypings(digwishMeta);
    } catch (e2) {
      console.error(JSON.stringify({ status: "FATAL", message: "no reference typings and no generator in this vendored kit; use check.js instead" }));
      process.exit(2);
    }
  }

  const errors = compileHandler(source, extra);
  if (errors.length === 0) {
    console.log(JSON.stringify({ status: "OK", errors: [] }));
  } else {
    console.log(JSON.stringify({ status: "ERRORS", errors }, null, 2));
    process.exitCode = 1;
  }
}

module.exports = { compileHandler };
