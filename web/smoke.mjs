/**
 * Smoke the running API as three staff roles.
 *
 * The unit tests prove the registry gates correctly against permissions given
 * to them. This proves the permissions themselves are what the real backend
 * hands out, and that every screen's endpoint answers - the gap that let the
 * Settings page call a deleted endpoint for weeks while tsc stayed green.
 *
 * Usage: node smoke.mjs [base-url]        (default http://127.0.0.1:8000)
 */
const BASE = process.argv[2] ?? "http://127.0.0.1:8000";

/**
 * Credentials come from the environment. This file holds none.
 *
 * A password committed to a public repository is a password in a search index,
 * and this script is the only place in the web app that needs a real one. It is
 * required rather than defaulted: a default is still a committed password, and
 * a script that silently falls back to a well-known one is the thing that ends
 * up pointed at staging.
 *
 *   SMOKE_PASSWORD='...' node smoke.mjs http://127.0.0.1:8077
 *
 * The demo values live in PASSWORDS.md, which is gitignored. Login ids are
 * overridable too, so this runs against any deployment.
 */
const env = process.env;
const PASSWORD = env.SMOKE_PASSWORD;
if (!PASSWORD) {
  console.error(
    [
      "SMOKE_PASSWORD is not set.",
      "",
      "This script signs in as three staff roles and deliberately holds no",
      "password of its own. Pass the seeded demo password (see the local,",
      "gitignored PASSWORDS.md) or the password for whatever you are pointing",
      "it at:",
      "",
      `  SMOKE_PASSWORD='...' node smoke.mjs ${BASE}`,
      "",
    ].join("\n"),
  );
  process.exit(2);
}

const STAFF = [
  { who: "admin", login_id: env.SMOKE_ADMIN_ID ?? "admin@sunrisepublic.edu" },
  { who: "fee counter", login_id: env.SMOKE_COUNTER_ID ?? "counter@sunrisepublic.edu" },
  { who: "transport manager", login_id: env.SMOKE_TRANSPORT_ID ?? "TRM001" },
].map((s) => ({ ...s, password: PASSWORD }));

/**
 * Endpoints the current screens depend on, with the module each sits behind.
 * Mirrors src/screens.ts. Extend as slices add screens.
 *
 * The module matters because a 404 now has two meanings. It used to have one -
 * the endpoint is gone - which is the failure this script was written to catch.
 * Since every router that declares a module actually enforces it, a school that
 * has not bought a module gets 404 from its endpoints by design, and the demo
 * school has HR switched off. So the check below is two-sided: with the module
 * off the endpoint MUST 404, and with it on it must not.
 */
const SCREEN_ENDPOINTS = {
  Dashboard: { path: "/admin/dashboard/stats" },
  Students: { path: "/admin/students", module: "students" },
  Staff: { path: "/admin/teachers", module: "hr" },
  Classes: { path: "/admin/classes" },
  Attendance: { path: "/admin/attendance/summary", module: "attendance" },
  Exams: { path: "/admin/exams", module: "examinations" },
  Fees: { path: "/admin/fees/invoices", module: "fees" },
  // Path is a function because this route 404s for an unknown student as well
  // as for a missing endpoint, and those must not be confused - that confusion
  // is the exact thing this script exists to catch. Resolved from the roster,
  // and skipped honestly when the role cannot read it.
  "Student fees": {
    path: (ctx) => (ctx.studentId === null ? null : `/admin/fees/ledger/${ctx.studentId}`),
    module: "fees",
  },
  Defaulters: { path: "/admin/fees/defaulters", module: "fees" },
  "Fee setup": { path: "/admin/fees/plans", module: "fees" },
  "Period close": { path: "/admin/fees/periods", module: "fees" },
  Notices: { path: "/admin/notices", module: "communication" },
  Settings: { path: "/admin/settings" },
  Configuration: { path: "/admin/configuration" },
};

let failures = 0;
const check = (ok, what, detail = "") => {
  if (!ok) failures++;
  console.log(`  [${ok ? "PASS" : "FAIL"}] ${what}${detail ? ` — ${detail}` : ""}`);
};

for (const staff of STAFF) {
  console.log(`\n== ${staff.who}`);
  const login = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role: "admin", login_id: staff.login_id, password: staff.password }),
  });
  if (!login.ok) {
    check(false, "login", `${login.status}`);
    continue;
  }
  const { access_token, refresh_token } = await login.json();
  check(Boolean(access_token), "login returns an access token");
  check(Boolean(refresh_token), "login returns a refresh token");

  const auth = { Authorization: `Bearer ${access_token}` };
  const me = await (await fetch(`${BASE}/auth/me`, { headers: auth })).json();
  check(Array.isArray(me.permissions) && me.permissions.length > 0, "me carries permissions",
        `${me.permissions?.length} held`);
  check(Array.isArray(me.modules), "me carries modules", (me.modules ?? []).join(", "));
  check(Boolean(me.academic_year), "me carries the academic year", me.academic_year);

  const modulesOn = new Set(me.modules ?? []);

  // One real student id, for the routes that take one. A role that cannot read
  // the roster gets null and those checks are skipped rather than counted as
  // passes they did not earn.
  let studentId = null;
  const roster = await fetch(`${BASE}/admin/students?page_size=1`, { headers: auth });
  if (roster.ok) studentId = (await roster.json()).items?.[0]?.id ?? null;
  const ctx = { studentId };

  for (const [label, { path: spec, module }] of Object.entries(SCREEN_ENDPOINTS)) {
    const path = typeof spec === "function" ? spec(ctx) : spec;
    if (path === null) {
      console.log(`  [SKIP] ${label} — no student id readable by this role`);
      continue;
    }
    const res = await fetch(`${BASE}${path}`, { headers: auth });
    const off = module !== undefined && !modulesOn.has(module);
    if (off) {
      // The gate, seen from outside: this school did not buy the module.
      check(res.status === 404, `${label} -> ${path} (${module} off)`, String(res.status));
    } else {
      // 200 or 403 are both correct answers; 404 means the endpoint is gone,
      // which is the failure this script exists to catch.
      check(res.status !== 404, `${label} -> ${path}`, String(res.status));
    }
  }

  const refreshed = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  check(refreshed.ok, "the refresh token yields a new access token", String(refreshed.status));
}

console.log(failures === 0 ? "\nAll smoke checks passed" : `\n${failures} smoke check(s) FAILED`);
process.exit(failures === 0 ? 0 : 1);
