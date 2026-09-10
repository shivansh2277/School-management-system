/**
 * The typed-request-body guarantee, proven at compile time.
 *
 * `npm test` runs the one runtime assertion; the real proof is `tsc --noEmit`,
 * which fails if any `@ts-expect-error` below stops being an error. That is the
 * point: before this, `api.post(path, body)` took `body?: unknown`, so a write
 * with a misspelled or wrongly shaped field compiled cleanly and 422'd in front
 * of a clerk. Nothing here is executed - a call would hit the network.
 */
import { describe, expect, it } from "vitest";

import { api } from "./client";

// Never called. Declared only so the compiler checks every line.
async function _typeCases() {
  // A correct body compiles.
  await api.post("/auth/login", { role: "admin", login_id: "x", password: "y" });

  // @ts-expect-error - `login_id` misspelt as `login`.
  await api.post("/auth/login", { role: "admin", login: "x", password: "y" });

  // @ts-expect-error - `password` is required and missing.
  await api.post("/auth/login", { role: "admin", login_id: "x" });

  // @ts-expect-error - `role` is an enum, not any string.
  await api.post("/auth/login", { role: "headmaster", login_id: "x", password: "y" });

  // @ts-expect-error - a required body cannot be omitted entirely.
  await api.post("/auth/login");

  // @ts-expect-error - the path itself is still checked.
  await api.post("/admin/not-a-route", {});
}

describe("the api client's request bodies", () => {
  it("is proven by tsc, not by this assertion", () => {
    // Keeps _typeCases referenced so no lint pass deletes the file's point.
    expect(typeof _typeCases).toBe("function");
  });
});
