import { existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { SCREENS } from "./screens";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "..", "..");
const venv =
  process.platform === "win32"
    ? join(repo, ".venv", "Scripts", "python.exe")
    : join(repo, ".venv", "bin", "python");
const python = existsSync(venv) ? venv : "python";

/**
 * Every permission the registry names must exist in the backend catalogue.
 *
 * A typo here is a screen nobody can open, or a gate that never matches. The
 * backend pins the same property for its report registry
 * (test_every_report_names_a_permission_that_exists); this is the twin.
 */
describe("the registry's permissions", () => {
  it("all exist in backend core/permissions.py", () => {
    const raw = execFileSync(
      python,
      ["-c", "import json;from app.core.permissions import PERMISSIONS;print(json.dumps([c for c,_ in PERMISSIONS]))"],
      { cwd: join(repo, "backend"), encoding: "utf8" },
    );
    const known: string[] = JSON.parse(raw);
    for (const screen of SCREENS) {
      expect(known, `${screen.path} names ${screen.permission}`).toContain(screen.permission);
    }
  });
});
