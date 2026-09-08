# Web ERP Slice 0 (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the management web app permission-aware and type-safe against the API, so the remaining eleven backend modules can be added without repeating the same three mistakes per module.

**Architecture:** One `screens.ts` registry declares every screen with its path, permission and module; the sidebar and the router are both derived from it, so a screen cannot be offered to a user the API would refuse. Types are generated from the backend's OpenAPI schema, so a deleted endpoint or renamed field fails `tsc`. Tests are Vitest + React Testing Library + MSW with mocks typed against that same schema, plus a Node smoke script against a live seeded backend.

**Tech Stack:** React 18, TypeScript 5.5, Vite 5, react-router-dom 6 (HashRouter), @tanstack/react-query 5, Tailwind 3. Added in this plan: `openapi-typescript`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `msw`, `jsdom` — all devDependencies.

**Spec:** `docs/superpowers/specs/2026-09-08-web-erp-slice-0-foundation-design.md`

## Global Constraints

- **Working directory for all web commands is `web/`.** Backend commands run from `backend/` using `../.venv/Scripts/python.exe`.
- **Backend test command:** `../.venv/Scripts/python.exe -m pytest -q` from `backend/`. Baseline is **600 passing**. Never let it drop.
- **Money is a string end to end.** Never `Number()` or `parseFloat()` a money value. Display through the existing `money()` helper in `src/api/client.ts`. The API serialises `Numeric` as a string deliberately.
- **`src/api/schema.d.ts` is generated. Never hand-edit it.**
- **No new runtime dependencies.** Everything added in this plan is a devDependency. Ask before any dependency over 100 MB (CLAUDE.md); nothing here approaches that.
- **Do not restyle anything.** The existing Tailwind look and `src/theme.ts` tokens stay. This slice changes structure, not appearance.
- **Existing UI primitives live in `src/components/ui.tsx`** and are already exported: `Card`, `StatCard`, `Pill`, `Empty`, `DataTable`, `Modal`, `FormField`, `inputClass`. Extend that file; do not create a parallel component library.
- **Commit after every task.** Commit messages carry the reasoning — why, not just what (CLAUDE.md).
- **The demo school's id is not 1.** It is whatever `schools` holds; read it, never hardcode.
- Backend demo logins: admin `admin@sunrisepublic.edu` / `Admin@123`; fee counter `counter@sunrisepublic.edu` / `Admin@123`; transport manager `TRM001` / `Admin@123`. All three log in with `role: "admin"`.

---

## Task 1: `/auth/me` returns the school's enabled modules

The only backend change in this slice. Without it the UI cannot hide a
switched-off module for staff who lack `admin.settings.read` — which is the fee
collector, accountant, exam controller and transport manager.

**Files:**
- Modify: `backend/app/schemas/auth.py` (add field to `MeOut`, after `academic_year`)
- Modify: `backend/app/api/auth.py` (populate it in `me()`)
- Test: `backend/tests/test_auth.py` (append)

**Interfaces:**
- Consumes: nothing.
- Produces: `GET /auth/me` response gains `modules: list[str]` — the codes from `app/core/modules.py` whose `feature.<code>` setting is true for the caller's school. Task 4 consumes it.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_auth.py`:

```python
def test_me_reports_which_modules_the_school_has_on(client, admin, db, admin_user):
    """The clients hide a switched-off module, and most staff cannot read the
    configuration screen to find out: `admin.settings.read` is not held by the
    fee collector, accountant, exam controller or transport manager. So the
    fact travels on /auth/me, beside the permissions the nav is already built
    from."""
    from app.services import school_settings

    school_settings.set_many(db, admin_user, {"feature.transport": False, "feature.fees": True})

    body = client.get("/auth/me", headers=admin).json()
    assert "fees" in body["modules"]
    assert "transport" not in body["modules"]

    school_settings.set_many(db, admin_user, {"feature.transport": True})
    assert "transport" in client.get("/auth/me", headers=admin).json()["modules"]


def test_every_reported_module_is_a_real_module(client, admin):
    from app.core.modules import BY_CODE

    for code in client.get("/auth/me", headers=admin).json()["modules"]:
        assert code in BY_CODE
```

- [ ] **Step 2: Run the tests to verify they fail**

Run from `backend/`:
```bash
../.venv/Scripts/python.exe -m pytest tests/test_auth.py -k modules -q
```
Expected: FAIL with `KeyError: 'modules'`.

- [ ] **Step 3: Add the field to the schema**

In `backend/app/schemas/auth.py`, inside `class MeOut`, immediately after the
`academic_year: str | None = None` line:

```python
    # Which modules this school has switched on. It travels here rather than
    # being fetched from /admin/configuration because that route needs
    # `admin.settings.read`, which the fee collector, accountant, exam
    # controller and transport manager do not hold — exactly the staff whose
    # navigation has to hide a module the school does not use.
    modules: list[str] = []
```

- [ ] **Step 4: Populate it in the route**

In `backend/app/api/auth.py`, inside `me()`, add the argument to the `MeOut(...)`
constructor immediately after `academic_year=year.code if year else None,`:

```python
        modules=[
            m.code
            for m in MODULES
            if school_settings.enabled(db, user.school_id, m.code)
        ],
```

Add these imports at the top of the file, beside the existing imports:

```python
from app.core.modules import MODULES
from app.services import school_settings
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
../.venv/Scripts/python.exe -m pytest tests/test_auth.py -q
```
Expected: PASS.

- [ ] **Step 6: Run the whole backend suite**

```bash
../.venv/Scripts/python.exe -m pytest -q
```
Expected: **602 passed** (600 baseline + 2 new).

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/auth.py backend/app/api/auth.py backend/tests/test_auth.py
git commit -m "Tell the clients which modules this school actually has

The web app has to hide a switched-off module, and the only place that fact
lived was /admin/configuration, behind admin.settings.read - a permission the
fee collector, accountant, exam controller and transport manager do not hold.
So precisely the staff whose navigation needs narrowing could not discover what
to narrow.

It now travels on /auth/me beside the permissions, which MeOut's own comment
already says the clients are meant to render their navigation from.

Additive, no migration.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: Generate types from the OpenAPI schema

**Files:**
- Modify: `web/package.json` (devDependency + two scripts)
- Create: `web/scripts/generate-api-types.mjs`
- Create: `web/src/api/schema.d.ts` (generated output, committed)

**Interfaces:**
- Consumes: nothing.
- Produces: `web/src/api/schema.d.ts` exporting a `paths` interface keyed by URL path, each with per-method `responses` and `requestBody`. Task 3 builds the typed client on it.

- [ ] **Step 1: Add the dependency and scripts**

From `web/`:
```bash
npm install --save-dev openapi-typescript@7
```

Then in `web/package.json`, add to `"scripts"`:

```json
    "api:types": "node scripts/generate-api-types.mjs",
    "api:check": "node scripts/generate-api-types.mjs --check"
```

- [ ] **Step 2: Write the generator script**

Create `web/scripts/generate-api-types.mjs`:

```js
/**
 * Regenerate src/api/schema.d.ts from the backend's OpenAPI schema.
 *
 * The schema comes from the FastAPI app directly rather than from a running
 * server, so CI needs no service and no port. Pass --check to fail instead of
 * writing when the committed file is out of date: codegen that only ever runs
 * on one laptop drifts exactly like the hand-written types it replaced.
 */
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "..", "..");
const out = join(here, "..", "src", "api", "schema.d.ts");
const check = process.argv.includes("--check");

const python =
  process.platform === "win32"
    ? join(repo, ".venv", "Scripts", "python.exe")
    : join(repo, ".venv", "bin", "python");

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
```

> **Unverified at plan-writing time:** `openapi-typescript` v7 returns a TypeScript
> AST and pairs `openapiTS()` with `astToString()`, which is what the script
> above uses. v6 returned a string directly and had no `astToString`. If the
> import fails after installing, check the installed major version
> (`npm ls openapi-typescript`) and either pin v7 or drop `astToString` and use
> the returned string. Everything else in this task is unaffected.

- [ ] **Step 3: Generate the types**

```bash
npm run api:types
```
Expected: `wrote .../src/api/schema.d.ts`. Confirm the file exists and contains
`"/admin/students"` and `"/auth/me"`:

```bash
grep -c "\"/admin/students\"" src/api/schema.d.ts
grep -c "\"/auth/me\"" src/api/schema.d.ts
```
Expected: `1` for each.

- [ ] **Step 4: Confirm the drift check passes, then that it can fail**

```bash
npm run api:check
```
Expected: `schema.d.ts is up to date`.

Now prove the check works:
```bash
echo "// deliberate drift" >> src/api/schema.d.ts
npm run api:check
```
Expected: exit code 1 with "out of date".

Restore it:
```bash
npm run api:types && npm run api:check
```
Expected: up to date.

- [ ] **Step 5: Commit**

```bash
git add web/package.json web/package-lock.json web/scripts/generate-api-types.mjs web/src/api/schema.d.ts
git commit -m "Generate the web app's API types from the backend schema

npx tsc --noEmit exits 0 today while the Settings page calls
/admin/fees/structures, which returns 404. The types are hand-written, so the
compiler cannot see the backend and a passing typecheck proves nothing.

schema.d.ts is now generated from the FastAPI app itself - no running server,
so CI needs no service - and committed. api:check fails when the committed file
is stale, because codegen that only runs on one laptop drifts exactly like the
hand-written types it replaced.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 3: Type the API client, and handle refresh and errors

**Files:**
- Modify: `web/src/api/client.ts` (rewrite `request`, keep the exported surface)
- Create: `web/src/api/errors.ts`

**Interfaces:**
- Consumes: `paths` from `src/api/schema.d.ts` (Task 2).
- Produces:
  - `api.get<P>(path)`, `api.post<P>(path, body)`, `api.patch<P>(path, body)`, `api.del<P>(path)` — `P` is a literal path from `paths`; return types are inferred from the schema.
  - `ApiError` with `status: number`, `detail: string`, `fields: Record<string, string>`.
  - `tokenStore.get()`, `.set(access, refresh)`, `.clear()`, `.refresh()`.
  - `money(v: string | number): string` — unchanged, still exported from this module.
  - `newIdempotencyKey(): string`.

- [ ] **Step 1: Write the failing test**

Create `web/src/api/client.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { ApiError, money, newIdempotencyKey } from "./client";

describe("money", () => {
  it("formats a decimal string without going through a float", () => {
    expect(money("2800.00")).toBe("₹2,800.00");
  });

  it("keeps paise that a float would lose", () => {
    expect(money("4453081.25")).toBe("₹44,53,081.25");
  });
});

describe("newIdempotencyKey", () => {
  it("is long enough for the API, which demands at least 8 characters", () => {
    expect(newIdempotencyKey().length).toBeGreaterThanOrEqual(8);
  });

  it("differs each call, so two separate payments are two payments", () => {
    expect(newIdempotencyKey()).not.toBe(newIdempotencyKey());
  });
});

describe("ApiError", () => {
  it("maps FastAPI 422 detail onto field names", () => {
    const e = new ApiError(422, [
      { type: "missing", loc: ["body", "amount"], msg: "Field required" },
    ]);
    expect(e.fields.amount).toBe("Field required");
  });

  it("carries a plain string detail through", () => {
    expect(new ApiError(403, "This role does not have permission: fees.invoice.read").detail).toContain(
      "does not have permission",
    );
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
npx vitest run src/api/client.test.ts
```
Expected: FAIL — vitest is not installed yet (Task 6 installs it). If so, this
task's tests are written now and **run in Task 6**; mark this step done once
the test file exists. Do not install vitest here — Task 6 owns that setup so it
is reviewed as one change.

- [ ] **Step 3: Write the error type**

Create `web/src/api/errors.ts`:

```ts
/** FastAPI's 422 body: one entry per rejected field. */
type ValidationItem = { type: string; loc: (string | number)[]; msg: string };

export class ApiError extends Error {
  readonly detail: string;
  /** field name -> message, for 422s. Empty for every other status. */
  readonly fields: Record<string, string>;

  constructor(
    readonly status: number,
    body: string | ValidationItem[] | undefined,
  ) {
    super(typeof body === "string" ? body : `Request failed with ${status}`);
    this.fields = {};
    if (Array.isArray(body)) {
      for (const item of body) {
        // loc is ["body", "amount"] or ["query", "year"]; the field is last.
        const field = String(item.loc[item.loc.length - 1]);
        this.fields[field] = item.msg;
      }
      this.detail = body.map((i) => i.msg).join("; ");
    } else {
      this.detail = body ?? `Request failed with ${status}`;
    }
  }
}
```

- [ ] **Step 4: Rewrite the client**

Replace the whole of `web/src/api/client.ts` with:

```ts
/** The only HTTP code in the web client, typed against the generated schema. */
import type { paths } from "./schema";
import { ApiError } from "./errors";

export { ApiError };

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "sunrise.token";
const REFRESH_KEY = "sunrise.refresh";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh?: string) => {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/** Paths that support a given method, as literal strings from the schema. */
type GetPaths = { [P in keyof paths]: paths[P] extends { get: unknown } ? P : never }[keyof paths];
type PostPaths = { [P in keyof paths]: paths[P] extends { post: unknown } ? P : never }[keyof paths];
type PatchPaths = { [P in keyof paths]: paths[P] extends { patch: unknown } ? P : never }[keyof paths];
type DeletePaths = { [P in keyof paths]: paths[P] extends { delete: unknown } ? P : never }[keyof paths];

/** The 200 body of one operation. `unknown` where the route is untyped. */
type Ok<T> = T extends { responses: { 200: { content: { "application/json": infer R } } } }
  ? R
  : T extends { responses: { 201: { content: { "application/json": infer R } } } }
    ? R
    : unknown;

/**
 * Ask the API for a new access token.
 *
 * The refresh token was previously thrown away at login, so staff were bounced
 * to the login screen whenever the access token expired
 * (ACCESS_TOKEN_EXPIRE_MINUTES = 1440). One retry, then give up: a refresh loop
 * on a genuinely dead session is worse than a login prompt.
 */
async function refreshAccessToken(): Promise<boolean> {
  const refresh_token = tokenStore.getRefresh();
  if (!refresh_token) return false;
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  if (!res.ok) return false;
  const body = (await res.json()) as { access_token: string };
  tokenStore.set(body.access_token);
  return true;
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const token = tokenStore.get();
  return fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await send(path, init);

  if (res.status === 401 && (await refreshAccessToken())) {
    res = await send(path, init);
  }
  if (res.status === 401) {
    tokenStore.clear();
    window.location.hash = "#/login";
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/**
 * A key that makes a retried request one transaction rather than two.
 *
 * The API requires it on POST /admin/fees/payments (minimum 8 characters)
 * precisely so a double-click or a retry after a dropped connection cannot take
 * the money twice. Generate ONE key per logical transaction and reuse it across
 * retries; a fresh key per click defeats the whole mechanism.
 */
export function newIdempotencyKey(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

export const api = {
  get: <P extends GetPaths>(path: P, query?: string) =>
    request<Ok<paths[P]["get"]>>(`${path}${query ?? ""}`),
  post: <P extends PostPaths>(path: P, body?: unknown) =>
    request<Ok<paths[P]["post"]>>(path, { method: "POST", body: JSON.stringify(body ?? {}) }),
  patch: <P extends PatchPaths>(path: P, body: unknown) =>
    request<Ok<paths[P]["patch"]>>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: <P extends DeletePaths>(path: P) =>
    request<Ok<paths[P]["delete"]>>(path, { method: "DELETE" }),
};

/**
 * Money arrives from the API as a string and stays one.
 *
 * `Numeric` is serialised as a string deliberately; parsing it into a JS number
 * puts a concession a paisa away from the printed fee card. This formats for
 * display and nothing else ever converts.
 */
export const money = (v: string | number) =>
  `₹${Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
```

- [ ] **Step 5: Typecheck**

```bash
npx tsc --noEmit
```
Expected: errors **only** in `src/pages/*.tsx` where paths are now checked —
in particular `src/pages/Settings.tsx` for `/admin/fees/structures`. That is the
proof the codegen works. Task 7 fixes the pages. Record the error list; do not
fix pages here.

- [ ] **Step 6: Commit**

```bash
git add web/src/api/client.ts web/src/api/errors.ts web/src/api/client.test.ts
git commit -m "Type the API client, keep the session, and read 422s properly

Three things the client could not do.

It could not be checked against the backend: paths are now literal keys of the
generated schema, so a deleted endpoint fails tsc. Settings.tsx's call to
/admin/fees/structures stops compiling, which is exactly the point.

It threw the refresh token away at login, so staff were returned to the login
screen every time the access token expired. It now stores both and refreshes
once on a 401 before giving up.

It reported a 422 as a bare status. ApiError now maps FastAPI's detail[].loc
onto field names so a validation failure can land on the input that caused it.

Also newIdempotencyKey, with the rule written next to it: one key per logical
transaction, reused across retries. A fresh key per click would defeat the
protection the API demands the key for.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 4: Auth context reads everything `/auth/me` returns

**Files:**
- Modify: `web/src/auth/AuthContext.tsx`
- Modify: `web/src/layout/Shell.tsx:38` (the hardcoded academic year)

**Interfaces:**
- Consumes: `api`, `tokenStore` (Task 3); `modules` on `/auth/me` (Task 1).
- Produces: `useAuth()` returning `{ me, loading, login, logout, can, hasModule }` where `can(permission: string): boolean` and `hasModule(code: string): boolean`. Task 5 consumes both.

- [ ] **Step 1: Rewrite the context**

Replace `web/src/auth/AuthContext.tsx` with:

```tsx
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, tokenStore } from "../api/client";

/**
 * Everything /auth/me returns. The previous version declared only `user` and
 * discarded the rest, which is why every role saw the same nine menu items -
 * MeOut's own comment says the clients are meant to render navigation from
 * these.
 */
export type Me = {
  user: { id: number; role: string; full_name: string; login_id: string };
  permissions: string[];
  roles: string[];
  school_code: string | null;
  school_name: string | null;
  academic_year: string | null;
  modules: string[];
};

type AuthValue = {
  me: Me | null;
  loading: boolean;
  login: (loginId: string, password: string) => Promise<void>;
  logout: () => void;
  can: (permission: string) => boolean;
  hasModule: (code: string) => boolean;
};

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then((m) => setMe(m as Me))
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (loginId: string, password: string) => {
    // Staff log in through the admin tab: the office, accountant, principal,
    // exam controller and transport manager are all users.role == admin.
    // Teachers, students and guardians use the mobile app (spec section 3.5).
    const res = await api.post("/auth/login", {
      role: "admin",
      login_id: loginId,
      password,
    });
    const pair = res as { access_token: string; refresh_token: string };
    tokenStore.set(pair.access_token, pair.refresh_token);
    setMe((await api.get("/auth/me")) as Me);
  };

  const logout = () => {
    tokenStore.clear();
    setMe(null);
  };

  const value = useMemo<AuthValue>(() => {
    const held = new Set(me?.permissions ?? []);
    const on = new Set(me?.modules ?? []);
    return {
      me,
      loading,
      login,
      logout,
      can: (permission) => held.has(permission),
      hasModule: (code) => on.has(code),
    };
  }, [me, loading]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
```

- [ ] **Step 2: Replace the hardcoded academic year**

In `web/src/layout/Shell.tsx`, change the header line. Find:

```tsx
          <span className="text-sm text-ink-soft">Academic year 2025-26</span>
```

Replace with:

```tsx
          <span className="text-sm text-ink-soft">
            {me?.school_name}
            {me?.academic_year ? ` · Academic year ${me.academic_year}` : ""}
          </span>
```

- [ ] **Step 3: Typecheck**

```bash
npx tsc --noEmit
```
Expected: the same page errors as Task 3 Step 5, and no new ones in
`AuthContext.tsx` or `Shell.tsx`.

- [ ] **Step 4: Commit**

```bash
git add web/src/auth/AuthContext.tsx web/src/layout/Shell.tsx
git commit -m "Read the permissions and modules /auth/me has always returned

MeOut's comment says the clients render their navigation from permissions
rather than from the role name, so that adding a role needs no web deploy. The
web app declared only \`user\` and discarded permissions, roles, school name,
academic year and now modules - so all fourteen roles saw the same nine menu
items and the header printed a hardcoded 'Academic year 2025-26' while the API
was serving the real value.

The context now exposes can() and hasModule(), which the screen registry gates
on next.

The refresh token is stored at login, so a session survives the access token
expiring.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 5: The screen registry, and nav and routes derived from it

The heart of the slice.

**Files:**
- Create: `web/src/screens.ts`
- Create: `web/src/auth/RequirePermission.tsx`
- Modify: `web/src/App.tsx` (routes derived from the registry)
- Modify: `web/src/layout/Shell.tsx` (nav derived from the registry)

**Interfaces:**
- Consumes: `useAuth().can`, `.hasModule` (Task 4).
- Produces:
  - `type Screen = { path: string; label: string; group: string; permission: string; module?: ModuleCode; element: React.LazyExoticComponent<() => JSX.Element> }`
  - `SCREENS: Screen[]`
  - `visibleScreens(can, hasModule): Screen[]`
  - `groupedNav(can, hasModule): { group: string; screens: Screen[] }[]`
  Slices 1–6 add entries to `SCREENS` and nothing else.

- [ ] **Step 1: Write the registry**

Create `web/src/screens.ts`:

```ts
/**
 * Every screen in the app, declared once.
 *
 * The sidebar and the router are both derived from this list, so a menu item
 * cannot point at a route that refuses you and a route cannot exist without
 * declaring the permission its API requires. They cannot disagree, because
 * there is only one statement of the fact.
 *
 * This is the same shape the backend already uses to stop things drifting
 * apart: core/permissions.py, core/modules.py, core/message_templates.py and
 * core/report_registry.py. Adding a screen in a later slice is one entry here
 * plus the component - navigation, routing, permission gating and module
 * hiding all follow.
 */
import { lazy } from "react";

/** The eleven codes in backend app/core/modules.py. */
export type ModuleCode =
  | "students"
  | "attendance"
  | "examinations"
  | "fees"
  | "homework"
  | "communication"
  | "admission"
  | "timetable"
  | "hr"
  | "transport"
  | "reports";

export type Screen = {
  path: string;
  label: string;
  group: string;
  /** Must be a code in backend app/core/permissions.py. Pinned by a test. */
  permission: string;
  /** Hidden entirely when the school has this module switched off. */
  module?: ModuleCode;
  element: React.LazyExoticComponent<() => JSX.Element>;
};

export const SCREENS: Screen[] = [
  {
    path: "/",
    label: "Dashboard",
    group: "Overview",
    permission: "admin.settings.read",
    element: lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard }))),
  },
  {
    path: "/students",
    label: "Students",
    group: "People",
    permission: "students.profile.read",
    module: "students",
    element: lazy(() => import("./pages/Students").then((m) => ({ default: m.Students }))),
  },
  {
    path: "/teachers",
    label: "Staff",
    group: "People",
    permission: "hr.employee.read",
    element: lazy(() => import("./pages/Teachers").then((m) => ({ default: m.Teachers }))),
  },
  {
    path: "/classes",
    label: "Classes",
    group: "Academics",
    permission: "academics.class.read",
    element: lazy(() => import("./pages/Classes").then((m) => ({ default: m.Classes }))),
  },
  {
    path: "/attendance",
    label: "Attendance",
    group: "Academics",
    permission: "attendance.record.read",
    module: "attendance",
    element: lazy(() => import("./pages/Attendance").then((m) => ({ default: m.Attendance }))),
  },
  {
    path: "/exams",
    label: "Exams",
    group: "Academics",
    permission: "exam.definition.read",
    module: "examinations",
    element: lazy(() => import("./pages/Exams").then((m) => ({ default: m.Exams }))),
  },
  {
    path: "/fees",
    label: "Fees",
    group: "Money",
    permission: "fees.invoice.read",
    module: "fees",
    element: lazy(() => import("./pages/Fees").then((m) => ({ default: m.Fees }))),
  },
  {
    path: "/notices",
    label: "Notices",
    group: "Communication",
    permission: "comms.notice.read",
    module: "communication",
    element: lazy(() => import("./pages/Notices").then((m) => ({ default: m.Notices }))),
  },
  {
    path: "/settings",
    label: "Settings",
    group: "Administration",
    permission: "admin.settings.read",
    element: lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings }))),
  },
];

type Can = (permission: string) => boolean;
type HasModule = (code: string) => boolean;

/** Screens this caller may actually open. Both gates, in order. */
export function visibleScreens(can: Can, hasModule: HasModule): Screen[] {
  return SCREENS.filter(
    (s) => (s.module === undefined || hasModule(s.module)) && can(s.permission),
  );
}

/** The sidebar: visible screens, in registry order, grouped by `group`. */
export function groupedNav(
  can: Can,
  hasModule: HasModule,
): { group: string; screens: Screen[] }[] {
  const out: { group: string; screens: Screen[] }[] = [];
  for (const screen of visibleScreens(can, hasModule)) {
    const existing = out.find((g) => g.group === screen.group);
    if (existing) existing.screens.push(screen);
    else out.push({ group: screen.group, screens: [screen] });
  }
  return out;
}
```

- [ ] **Step 2: Write the route guard**

Create `web/src/auth/RequirePermission.tsx`:

```tsx
import type { ReactNode } from "react";

import { useAuth } from "./AuthContext";
import type { Screen } from "../screens";

/**
 * The third gate. Hiding a menu item is not access control - typing /payroll in
 * the address bar has to hit the same check the sidebar applied.
 *
 * It renders an in-page refusal rather than redirecting: a redirect on a
 * permission failure reads as a crash to the person it happens to.
 */
export function RequirePermission({ screen, children }: { screen: Screen; children: ReactNode }) {
  const { can, hasModule } = useAuth();

  if (screen.module !== undefined && !hasModule(screen.module)) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">Not enabled</p>
        <p className="text-sm text-ink-soft mt-1">
          The {screen.module} module is not switched on for this school.
        </p>
      </div>
    );
  }
  if (!can(screen.permission)) {
    return (
      <div className="rounded-card bg-surface border border-rule p-8">
        <p className="font-medium text-ink">You do not have permission</p>
        <p className="text-sm text-ink-soft mt-1">
          {screen.label} needs <code>{screen.permission}</code>, which your role does not hold.
        </p>
      </div>
    );
  }
  return <>{children}</>;
}
```

- [ ] **Step 3: Derive the routes**

Replace `web/src/App.tsx` with:

```tsx
import { Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import { LoginPage } from "./auth/LoginPage";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RequirePermission } from "./auth/RequirePermission";
import { Shell } from "./layout/Shell";
import { SCREENS } from "./screens";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Shell />
          </ProtectedRoute>
        }
      >
        {SCREENS.map((screen) => (
          <Route
            key={screen.path}
            path={screen.path}
            element={
              <RequirePermission screen={screen}>
                <Suspense fallback={<div className="text-ink-faint">Loading...</div>}>
                  <screen.element />
                </Suspense>
              </RequirePermission>
            }
          />
        ))}
      </Route>
    </Routes>
  );
}
```

- [ ] **Step 4: Derive the sidebar**

In `web/src/layout/Shell.tsx`, delete the whole `const NAV = [...] as const;` block
and its comment, and replace the `<nav>` element with:

```tsx
        <nav className="space-y-4 flex-1">
          {groupedNav(can, hasModule).map(({ group, screens }) => (
            <div key={group}>
              <p className="px-3 pb-1 text-[11px] uppercase tracking-wide text-white/50">{group}</p>
              <div className="space-y-1">
                {screens.map((screen) => (
                  <NavLink
                    key={screen.path}
                    to={screen.path}
                    end={screen.path === "/"}
                    className={({ isActive }) =>
                      `block rounded-input px-3 py-2 text-sm ${
                        isActive ? "bg-white text-primary font-medium" : "hover:bg-white/10"
                      }`
                    }
                  >
                    {screen.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
```

Update the imports and the destructure at the top of `Shell.tsx`:

```tsx
import { groupedNav } from "../screens";
```
```tsx
  const { me, logout, can, hasModule } = useAuth();
```

- [ ] **Step 5: Typecheck**

```bash
npx tsc --noEmit
```
Expected: still only the page-level path errors from Task 3.

- [ ] **Step 6: Commit**

```bash
git add web/src/screens.ts web/src/auth/RequirePermission.tsx web/src/App.tsx web/src/layout/Shell.tsx
git commit -m "Declare every screen once, and derive the nav and router from it

The sidebar was a hardcoded list of nine items shown to all fourteen roles, and
the router was a second hardcoded list beside it. Two statements of the same
fact drift; across the six module slices still to come they would drift once per
slice.

screens.ts now declares each screen with its path, permission and module, and
both the sidebar and the routes are derived from it. A screen cannot be listed
without naming the permission its API requires, and RequirePermission applies
the same check on direct navigation - hiding a menu item is not access control.

Same shape as core/permissions.py, core/modules.py and core/report_registry.py:
when this project needs things to stop drifting apart, it declares them in one
list.

Adding a screen in a later slice is one entry here plus the component.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 6: Test setup, and the gate tests

**Files:**
- Modify: `web/package.json` (devDependencies + `test` script)
- Create: `web/vitest.config.ts`
- Create: `web/src/test/setup.ts`
- Create: `web/src/test/renderWithAuth.tsx`
- Create: `web/src/screens.test.tsx`

**Interfaces:**
- Consumes: `SCREENS`, `visibleScreens`, `groupedNav` (Task 5); `Me` (Task 4).
- Produces: `renderWithAuth(ui, me)` test helper; `npm test`.

- [ ] **Step 1: Install the test dependencies**

From `web/`:
```bash
npm install --save-dev vitest@2 jsdom@25 @testing-library/react@16 @testing-library/jest-dom@6 @testing-library/user-event@14 msw@2
```

Add to `web/package.json` `"scripts"`:
```json
    "test": "vitest run",
    "test:watch": "vitest"
```

- [ ] **Step 2: Configure vitest**

Create `web/vitest.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

Create `web/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 3: Write the render helper**

Create `web/src/test/renderWithAuth.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import type { Me } from "../auth/AuthContext";

/** A signed-in staff member with exactly the permissions and modules given. */
export function makeMe(permissions: string[], modules: string[], name = "Test Staff"): Me {
  return {
    user: { id: 1, role: "admin", full_name: name, login_id: "test@example.com" },
    permissions,
    roles: [],
    school_code: "SPS",
    school_name: "Sunrise Public School",
    academic_year: "2025-26",
    modules,
  };
}

/**
 * Render with a fixed `me`, bypassing the network.
 *
 * The real AuthProvider fetches /auth/me on mount; these tests are about what
 * the registry does with a given set of permissions, so the identity is
 * injected rather than mocked over HTTP.
 */
export function renderWithAuth(ui: ReactElement, me: Me, route = "/") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}
```

- [ ] **Step 4: Write the gate tests**

Create `web/src/screens.test.tsx`:

```tsx
import { describe, expect, it } from "vitest";

import { SCREENS, groupedNav, visibleScreens } from "./screens";

/** The permissions the backend's fee_collector role holds (core/permissions.py). */
const FEE_COLLECTOR = ["students.profile.read", "fees.invoice.read", "fees.payment.collect"];

/** The transport_manager role. */
const TRANSPORT_MANAGER = [
  "students.profile.read",
  "academics.class.read",
  "transport.setup.read",
  "transport.setup.write",
  "transport.assignment.read",
  "transport.assignment.manage",
  "hr.employee.read",
  "comms.notice.read",
  "comms.message.send",
];

const ALL_MODULES = [
  "students",
  "attendance",
  "examinations",
  "fees",
  "homework",
  "communication",
  "admission",
  "timetable",
  "hr",
  "transport",
  "reports",
];

const can = (held: string[]) => (p: string) => held.includes(p);
const hasModule = (on: string[]) => (c: string) => on.includes(c);

describe("the two gates", () => {
  it("shows a fee collector the fee screen and not the staff register", () => {
    const labels = visibleScreens(can(FEE_COLLECTOR), hasModule(ALL_MODULES)).map((s) => s.label);
    expect(labels).toContain("Fees");
    expect(labels).toContain("Students");
    expect(labels).not.toContain("Staff");
    expect(labels).not.toContain("Settings");
  });

  it("shows a transport manager no Fees entry", () => {
    const labels = visibleScreens(can(TRANSPORT_MANAGER), hasModule(ALL_MODULES)).map(
      (s) => s.label,
    );
    expect(labels).not.toContain("Fees");
    expect(labels).toContain("Staff");
  });

  it("hides a module the school has switched off, even from someone holding every permission", () => {
    const everyPermission = () => true;
    const withoutFees = ALL_MODULES.filter((m) => m !== "fees");
    const labels = visibleScreens(everyPermission, hasModule(withoutFees)).map((s) => s.label);
    expect(labels).not.toContain("Fees");
    // ...and the permission alone is not enough to bring it back.
    expect(visibleScreens(everyPermission, hasModule(ALL_MODULES)).map((s) => s.label)).toContain(
      "Fees",
    );
  });

  it("groups the sidebar in registry order without empty groups", () => {
    const groups = groupedNav(can(FEE_COLLECTOR), hasModule(ALL_MODULES));
    expect(groups.every((g) => g.screens.length > 0)).toBe(true);
    expect(groups.map((g) => g.group)).toEqual([...new Set(groups.map((g) => g.group))]);
  });
});

describe("the registry itself", () => {
  it("gives every screen a path, label, group and permission", () => {
    for (const s of SCREENS) {
      expect(s.path, `${s.label} path`).toBeTruthy();
      expect(s.label, `${s.path} label`).toBeTruthy();
      expect(s.group, `${s.path} group`).toBeTruthy();
      expect(s.permission, `${s.path} permission`).toBeTruthy();
    }
  });

  it("has no duplicate paths", () => {
    const paths = SCREENS.map((s) => s.path);
    expect(paths).toEqual([...new Set(paths)]);
  });
});
```

- [ ] **Step 5: Write the permission-catalogue test**

This is the frontend twin of the backend's
`test_every_report_names_a_permission_that_exists`. A typo'd permission is a
screen nobody can open.

Create `web/src/screens.permissions.test.ts`:

```ts
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { SCREENS } from "./screens";

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, "..", "..");
const python =
  process.platform === "win32"
    ? join(repo, ".venv", "Scripts", "python.exe")
    : join(repo, ".venv", "bin", "python");

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
```

> **If `crypto.randomUUID` is undefined** in the jsdom environment on an older
> Node, add `import { webcrypto } from "node:crypto";` and
> `globalThis.crypto ??= webcrypto as Crypto;` to `src/test/setup.ts`. Node 20
> (the version CI pins) has it, so this is a local-machine fallback only.

- [ ] **Step 6: Run the tests**

```bash
npm test
```
Expected: all pass, including the `client.test.ts` written in Task 3.

- [ ] **Step 7: Write the live smoke script**

Create `web/smoke.mjs`:

```js
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
```

- [ ] **Step 8: Run the smoke script against a live backend**

In one terminal, from `backend/`:
```bash
DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test ../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8077
```
In another, from `web/`:
```bash
node smoke.mjs http://127.0.0.1:8077
```
Expected: `All smoke checks passed`. If a screen endpoint reports 404, that is a
real finding — record it for Task 7.

- [ ] **Step 9: Extend CI**

In `.github/workflows/ci.yml`, in the `web` job, after the `Typecheck` step and
before `Build`, insert:

```yaml
      - name: API types are up to date
        run: npm run api:check
      - name: Tests
        run: npm test
```

The `api:check` and permission-catalogue steps both shell out to
`../.venv/Scripts/python.exe`, which does not exist on the CI runner. Add a
Python setup to the `web` job immediately after `actions/checkout@v4`:

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Backend deps for schema generation
        working-directory: backend
        run: pip install -r requirements.txt
```

and change `generate-api-types.mjs` and `screens.permissions.test.ts` to fall
back to `python` on PATH when the venv binary is absent. In both files, replace
the `const python = ...` assignment with:

```js
const venv =
  process.platform === "win32"
    ? join(repo, ".venv", "Scripts", "python.exe")
    : join(repo, ".venv", "bin", "python");
const python = existsSync(venv) ? venv : "python";
```

adding `import { existsSync } from "node:fs";` to each file (in
`generate-api-types.mjs`, extend the existing `node:fs` import to
`import { existsSync, readFileSync, writeFileSync } from "node:fs";`).

- [ ] **Step 10: Re-run everything**

```bash
npm run api:check && npm test && npx tsc --noEmit
```
Expected: the first two pass; `tsc` still shows only the page path errors.

- [ ] **Step 11: Commit**

```bash
git add web/package.json web/package-lock.json web/vitest.config.ts web/src/test web/src/screens.test.tsx web/src/screens.permissions.test.ts web/smoke.mjs web/scripts/generate-api-types.mjs .github/workflows/ci.yml
git commit -m "Test the gates, and smoke the real API as three staff roles

The web app had no tests at all, which for a target of a school running on it
is a gap in its own right.

The tests that matter here are the gates, because they are the slice's promise:
a fee collector sees no Staff or Settings entry, a transport manager sees no
Fees entry, and a module the school switched off is hidden even from someone
holding every permission.

screens.permissions.test.ts is the frontend twin of the backend's
test_every_report_names_a_permission_that_exists: every permission the registry
names must exist in core/permissions.py, because a typo is a screen nobody can
open or a gate that never matches.

smoke.mjs covers what unit tests structurally cannot - that the permissions the
real backend hands out are the ones the gates were tested against, and that no
screen's endpoint has been deleted underneath it. That is the failure that hid
the Settings page's dead call while tsc stayed green, and the technique that
found eight defects in the backend sweep.

CI already had a web job running typecheck and build; it now also checks the
generated schema is current and runs the tests.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 7: Migrate the nine existing pages onto the typed client

**Files:**
- Modify: `web/src/pages/Settings.tsx:32-37` (the dead endpoint)
- Modify: whichever of `web/src/pages/*.tsx` `tsc` reports, one page per commit

**Interfaces:**
- Consumes: `api` (Task 3), `SCREENS` (Task 5).
- Produces: a `tsc --noEmit` clean tree.

- [ ] **Step 1: List the damage**

```bash
npx tsc --noEmit 2>&1 | grep "^src/pages" | sort
```
Record every file and line. This is the drift the codegen exists to find; expect
more than the one known 404.

- [ ] **Step 2: Fix the known dead endpoint**

In `web/src/pages/Settings.tsx`, replace the `structures` query (lines 32–37):

```tsx
  const structures = useQuery({
    queryKey: ["fee-structures"],
    queryFn: () => api.get<{ id: number; class_name: string; monthly_amount: string }[]>(
      "/admin/fees/structures",
    ),
  });
```

with:

```tsx
  // `/admin/fees/structures` was deleted when Part 3 rebuilt fees, and this
  // call has been a silent 404 ever since - the reason this slice generates
  // types. The replacement is the fee plan, which carries its own monthly
  // total summed from the items that recur monthly.
  const structures = useQuery({
    queryKey: ["fee-plans"],
    queryFn: () => api.get("/admin/fees/plans"),
  });
```

Then update the render below it to read `class_name`, `name` and `monthly_total`
(the plan shape) rather than `monthly_amount`. Inspect the current JSX and adjust
field names to match; `monthly_total` is the field that replaces
`monthly_amount`.

- [ ] **Step 3: Typecheck the one file**

```bash
npx tsc --noEmit 2>&1 | grep "Settings.tsx"
```
Expected: no output.

- [ ] **Step 4: Commit that page**

```bash
git add web/src/pages/Settings.tsx
git commit -m "Point the settings screen at a fee endpoint that exists

/admin/fees/structures was deleted when Part 3 rebuilt fees around heads, plans
and invoice lines. The settings screen has called it ever since and got a 404,
and nothing noticed because the types were hand-written - npx tsc --noEmit
exited 0 the whole time.

The generated types made it a compile error, which is the entire argument for
generating them. The replacement is /admin/fees/plans, whose monthly_total is
summed from the items that actually recur monthly.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Repeat for each remaining page**

For every other file from Step 1, in this order — `Dashboard.tsx`,
`Students.tsx`, `Classes.tsx`, `Teachers.tsx`, `Attendance.tsx`, `Exams.tsx`,
`Fees.tsx`, `Notices.tsx`:

1. Read the `tsc` error.
2. If the path is wrong, find the real one: `grep '"/admin/<area>' src/api/schema.d.ts`.
3. If a field name is wrong, read the shape in `schema.d.ts` and use the real name.
4. **If money is being parsed into a number, stop and fix it** — keep the string, format with `money()`.
5. Run `npx tsc --noEmit 2>&1 | grep "<that file>"` and expect no output.
6. Commit that page alone, with a message naming what was actually wrong.

- [ ] **Step 6: Full verification**

```bash
npx tsc --noEmit && npm test && npm run api:check && npm run build
```
Expected: all four succeed.

Then, with the backend running on 8077:
```bash
node smoke.mjs http://127.0.0.1:8077
```
Expected: `All smoke checks passed`.

- [ ] **Step 7: Manual check of the slice's promise**

Start the dev server (`npm run dev`) and log in as each of the three staff
accounts in turn. Confirm by eye:

- `admin@sunrisepublic.edu` sees the full sidebar, grouped.
- `counter@sunrisepublic.edu` sees Students and Fees, and **no** Staff or Settings.
- `TRM001` sees Staff and **no** Fees.
- The header shows "Sunrise Public School · Academic year 2025-26" from the API.
- Navigating directly to `#/settings` as the fee counter shows the in-page
  refusal, not a blank screen or a redirect.

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "Finish migrating the existing screens onto generated types

Every page now types its paths and fields against the backend schema, so the
next endpoint to be deleted or renamed fails the build instead of a user.

Verified by hand as well as by test: three staff logins each get a different,
correct sidebar, and a direct navigation to a screen the role cannot open is
refused in place rather than redirected.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review notes

**Spec coverage.** §4.1 registry → Task 5. §4.2 three gates → Tasks 5, 6.
§4.3 backend `modules` → Task 1. §4.4 typed API → Tasks 2, 3. §4.5 data flow
(money-as-string, idempotency key) → Task 3 and the Global Constraints; query
key conventions are applied per page in Task 7 rather than as a separate task,
since there is no shared code to change. §4.6 auth/refresh → Tasks 3, 4.
§4.7 error handling → Task 3 (`ApiError`) and Task 5 (`RequirePermission` for
403). §4.8 primitives → **partially deferred**: `src/components/ui.tsx` already
exports `DataTable`, `Modal`, `FormField` and `Empty`, which cover the spec's
list except the confirm-with-reason dialog. That dialog has no caller until
Slice 2 introduces void/reverse, so building it here would be speculative;
**it is listed as the first task of Slice 2** rather than built blind. §5
testing → Task 6. §6 delivery → Tasks 1–7 in order.

**Deviation from the spec, recorded deliberately:** the spec's step 5 lists the
confirm-with-reason dialog inside Slice 0. Deferred to Slice 2 for the reason
above — YAGNI, and a dialog built with no caller is a dialog built to the wrong
shape.

**Known risk carried:** Task 7 Step 1 will list more errors than the one known
404. That is the purpose of the slice, but it makes Task 7 the largest task
here. If it proves larger than one sitting, split it: pages are already
committed one at a time.
