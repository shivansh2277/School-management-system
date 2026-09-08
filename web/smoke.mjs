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

const STAFF = [
  { who: "admin", login_id: "admin@sunrisepublic.edu", password: "Admin@123" },
  { who: "fee counter", login_id: "counter@sunrisepublic.edu", password: "Admin@123" },
  { who: "transport manager", login_id: "TRM001", password: "Admin@123" },
];

/** Endpoints the current screens depend on. Extend as slices add screens. */
const SCREEN_ENDPOINTS = {
  Dashboard: "/admin/dashboard/stats",
  Students: "/admin/students",
  Staff: "/admin/teachers",
  Classes: "/admin/classes",
  Attendance: "/admin/attendance/summary",
  Exams: "/admin/exams",
  Fees: "/admin/fees/invoices",
  Notices: "/admin/notices",
  Settings: "/admin/settings",
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

  for (const [label, path] of Object.entries(SCREEN_ENDPOINTS)) {
    const res = await fetch(`${BASE}${path}`, { headers: auth });
    // 200 or 403 are both correct answers; 404 means the endpoint is gone,
    // which is the failure this script exists to catch.
    check(res.status !== 404, `${label} -> ${path}`, String(res.status));
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
