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
 * Every permission and every module the registry names must exist in the
 * backend catalogues.
 *
 * A typo here is a screen nobody can open, or a gate that never matches. The
 * backend pins the same property for its report registry
 * (test_every_report_names_a_permission_that_exists); this is the twin.
 */
function backendList(expr: string): string[] {
  return JSON.parse(
    execFileSync(python, ["-c", `import json;${expr}`], {
      cwd: join(repo, "backend"),
      encoding: "utf8",
    }),
  );
}

describe("the registry's permissions", () => {
  it("all exist in backend core/permissions.py", () => {
    const known = backendList(
      "from app.core.permissions import PERMISSIONS;print(json.dumps([c for c,_ in PERMISSIONS]))",
    );
    for (const screen of SCREENS) {
      for (const permission of screen.permissions) {
        expect(known, `${screen.path} names ${permission}`).toContain(permission);
      }
    }
  });

  it("all module codes exist in backend core/modules.py", () => {
    const known = backendList(
      "from app.core.modules import MODULES;print(json.dumps([m.code for m in MODULES]))",
    );
    for (const screen of SCREENS) {
      for (const code of screen.modules ?? []) {
        expect(known, `${screen.path} names module ${code}`).toContain(code);
      }
    }
  });
});
