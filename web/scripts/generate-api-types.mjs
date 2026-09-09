/**
 * Regenerate src/api/schema.d.ts from the backend's OpenAPI schema.
 *
 * The schema comes from the FastAPI app directly rather than from a running
 * server, so CI needs no service and no port. Pass --check to fail instead of
 * writing when the committed file is out of date: codegen that only ever runs
 * on one laptop drifts exactly like the hand-written types it replaced.
 */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "..", "..");
const out = join(here, "..", "src", "api", "schema.d.ts");
const check = process.argv.includes("--check");

const venv =
  process.platform === "win32"
    ? join(repo, ".venv", "Scripts", "python.exe")
    : join(repo, ".venv", "bin", "python");
const python = existsSync(venv) ? venv : "python";

const schema = execFileSync(
  python,
  ["-c", "import json, app.main; print(json.dumps(app.main.app.openapi()))"],
  { cwd: join(repo, "backend"), encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
);

const banner =
  "/**\n * GENERATED FILE — do not edit by hand.\n" +
  " * Regenerate with `npm run api:types`. See docs/superpowers/specs/\n" +
  " * 2026-09-08-web-erp-slice-0-foundation-design.md section 4.4.\n */\n";
const generated = banner + astToString(await openapiTS(JSON.parse(schema)));

if (check) {
  const current = readFileSync(out, "utf8");
  if (current !== generated) {
    console.error(
      "src/api/schema.d.ts is out of date. Run `npm run api:types` and commit the result.",
    );
    process.exit(1);
  }
  console.log("schema.d.ts is up to date");
} else {
  writeFileSync(out, generated);
  console.log(`wrote ${out}`);
}
