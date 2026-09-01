// check.js - thin CLI over qadCompile.js for the Python backend.
// Usage: node check.js <handler.ts> [extra1.d.ts extra2.ts ...]
// stdout is one JSON doc; exit 0 OK, 1 ERRORS, 2 FATAL (never a pass).
"use strict";

var fs = require("fs");
var path = require("path");

function fatal(message) {
  console.error(JSON.stringify({ status: "FATAL", message: message }));
  process.exit(2);
}

var handlerPath = process.argv[2];
if (!handlerPath) {
  fatal("usage: node check.js <handler.ts> [extra.d.ts ...]");
}

var compileHandler;
try {
  compileHandler = require("./qadCompile").compileHandler;
} catch (e) {
  fatal("could not load qadCompile.js: " + e.message);
}

var source;
try {
  source = fs.readFileSync(handlerPath, "utf8");
} catch (e) {
  fatal("could not read handler file: " + e.message);
}

// compileHandler expects extraTypings as { "<basename>": "<content>" },
// merged over base.json exactly like the component DTO/Constants files.
var extra = {};
var i;
for (i = 3; i < process.argv.length; i++) {
  try {
    extra[path.basename(process.argv[i])] = fs.readFileSync(process.argv[i], "utf8");
  } catch (e) {
    fatal("could not read extra typing file: " + e.message);
  }
}

var errors;
try {
  errors = compileHandler(source, extra);
} catch (e) {
  fatal("type check crashed: " + e.message);
}

if (errors.length === 0) {
  console.log(JSON.stringify({ status: "OK", errors: [] }));
} else {
  console.log(JSON.stringify({ status: "ERRORS", errors: errors }));
  process.exitCode = 1;
}
