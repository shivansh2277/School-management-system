# Web ERP — Slice 0: Foundation

**Date:** 8 September 2026
**Status:** approved design, not yet implemented
**Workstream:** Web ERP integration / expansion
**Scope:** the foundation every later web slice depends on. No new module screens.

---

## 1. The problem

The backend is a 12-module ERP. The management web app covers about a fifth of
it.

| | |
|---|---|
| API surface | **214 paths, 263 operations** |
| Staff-facing surface (excludes `/parent`, `/student`, `/teacher`, `/public`) | **~200 operations** |
| Web app | **9 pages, ~1,840 lines**, reaching **12 endpoints** |
| Web app tests | **0** |
| Backend modules | students, attendance, examinations, fees, homework, communication, admission, timetable, hr, transport, reports |
| Web app modules | students, attendance, examinations, fees, communication (notices only), plus classes/teachers/settings |

Nothing in `web/` knows that admission, timetable, HR, payroll, transport or
reports exist. The system is a large backend ERP behind a small frontend.

### Three faults that must not be carried forward

**1. The UI is blind to the permission model.** The backend has 77 permissions
and 14 roles. `/auth/me` already returns `permissions`, `roles`, `school_name`
and `academic_year`, and `MeOut`'s own comment states the intent:

> *"The clients render their navigation from these rather than from the role
> name, so adding a role never requires a web deploy or an app release
> (§14)."*

The web app's `Me` type declares only `user` and discards the rest. Every role
sees the same nine menu items, and the header renders the hardcoded string
`"Academic year 2025-26"` while the API is serving the real value.

**2. Types are hand-written, so `tsc` cannot see the backend.** `npx tsc
--noEmit` exits 0 while `/admin/fees/structures` — which the Settings page
calls at `src/pages/Settings.tsx:35` — returns **404**. The endpoint was deleted; the frontend never found out. A
passing typecheck currently proves nothing.

**3. There are no tests.** For a target of "a real school could run on it",
that is a gap in its own right.

---

## 2. Goal and non-goals

**Goal.** Make the web app safe and cheap to expand across the remaining
modules, by fixing the three faults above once rather than in every later
slice.

**Definition of done.**
- `npm run typecheck` and `npm test` pass.
- The live smoke script passes against a seeded backend.
- Three different demo logins each see a correct and *different* sidebar.
- **No screen exists that the API would refuse.**

**Non-goals for this slice.**
- No new module screens (slices 1–6).
- No visual redesign. The existing Tailwind look stays; relayout is not what is
  blocking.
- No offline support.
- No printing — that is Slice 2a, a backend prerequisite (§8).
- Keyboard-first data entry is *recorded as a rule* here and applied when the
  data-entry screens are built.

---

## 3. Decisions taken

| # | Decision | Rationale |
|---|---|---|
| 1 | **"Done" means a real school can run on it** | Owner's decision. Drives full CRUD ambition across slices and makes role-aware navigation mandatory, not cosmetic. |
| 2 | **Decompose into Slice 0 + six module slices** | ~200 operations across 12 modules is a programme, not a spec. Each slice ships working software. |
| 3 | **Generate types from OpenAPI; typed fetch wrapper** | `openapi-typescript` as a dev dependency. No runtime dependency added. Fits this codebase's registry-over-magic style. Rejected: generated react-query hooks (large generated surface, heavier dep, hard to debug); contract-test-only (catches deletions but not renamed or retyped fields). |
| 4 | **Vitest + RTL + MSW, plus a live smoke script** | Mirrors what demonstrably worked on the backend: a fast suite plus a live sweep. Avoids Playwright's ~300 MB of browsers, which CLAUDE.md requires asking about. |
| 5 | **Web is staff-only; teachers stay on mobile** | The mobile app (Expo, 44 files) already owns `(parent)`, `(student)` and teacher flows. §0.17 already put homework there. Login continues to send `role: "admin"`, which covers office, accountant, principal, exam controller and transport manager — all of whom are `users.role == admin`. |
| 6 | **Screen registry (approach B)** | One declaration per screen drives nav *and* router. Chosen over hand-maintained nav because nav, routing and permission checks otherwise drift across six slices. Matches the existing precedent: `core/permissions.py`, `core/modules.py`, `core/message_templates.py`, `core/report_registry.py`. Rejected: Next.js/Remix rewrite — discards working plumbing, adds a server tier the architecture does not need. |

---

## 4. Architecture

### 4.1 The screen registry

`src/screens.ts` declares every screen exactly once:

```ts
export type Screen = {
  path: string;          // "/fees/defaulters"
  label: string;         // "Defaulters"
  group: string;         // "Fees" — sidebar grouping
  permission: string;    // "fees.invoice.read" — must exist in the backend catalogue
  module?: ModuleCode;   // "fees" — hidden when the school has the module off
  element: LazyComponent;
};
```

`ModuleCode` is the union of the eleven codes in `app/core/modules.py`:
`students | attendance | examinations | fees | homework | communication |
admission | timetable | hr | transport | reports`.

Both the sidebar and the router are **derived** from this array. A screen
cannot be listed without declaring the permission its API requires, and cannot
be routed to without the same check being applied. They cannot disagree,
because there is only one statement of the fact.

Adding a screen in a later slice is one registry entry plus the component;
navigation, routing, permission gating and module hiding all follow.

### 4.2 Three gates, in order

1. **Module enabled** — a school with `feature.transport` off sees no Transport
   group at all, even for a super admin holding every permission.
2. **Permission held** — checked against `/auth/me`'s `permissions`.
3. **Route re-check on direct navigation** — typing `/payroll` in the address
   bar hits the same gate. Hiding a menu item is not access control.

The guarantee: **the UI never offers a person something the API would refuse.**
This is the frontend mirror of a rule the backend already follows — the report
library lists only what the caller can actually run, because "a library that
lists a report and then refuses it teaches people to ignore it."

### 4.3 Backend change required

`/auth/me` must also return the school's enabled modules.

Today the only source is `GET /admin/configuration`, gated on
`admin.settings.read` — a permission the fee collector, accountant, exam
controller and transport manager **do not hold**. Without this addition, gate 1
is impossible for exactly the staff who need it.

Change: add `modules: list[str]` to `MeOut`, populated from the existing
settings registry (`feature.<code>` keys). Additive, no migration, one test.

### 4.4 The typed API layer

- `npm run api:types` runs `openapi-typescript` against `/openapi.json`,
  producing `src/api/schema.d.ts` — **generated, committed, never hand-edited.**
- The existing `src/api/client.ts` gains path-and-method generics over that
  schema. Its shape (one `request()`, `api.get/post/patch/del`) is retained; it
  is already the only HTTP code in the app.
- Calling a deleted endpoint or reading a renamed field then **fails `tsc`**.
  `/admin/fees/structures` would not compile.
- **CI check:** regenerate and fail if the result differs from the committed
  file. Codegen that runs only on one laptop drifts exactly like hand-written
  types. See §5 for where this lands in the existing workflow.

### 4.5 Data flow

React-query is retained, with conventions the current pages lack:

- **Query keys mirror the URL path**: `["admin", "students", { page, q }]`.
- **Mutations invalidate by prefix**, so a payment refreshes the ledger, the
  daybook and the defaulter list without naming each.
- **Money is a string end to end.** The API serialises `Numeric` as a string
  deliberately; it is parsed only at the point of display, through the existing
  `money()` helper, and never into a JS number. Floating point has no place
  near a fee ledger.
- **Idempotency keys.** Every money-mutating request generates one key per
  logical transaction and reuses it on retry. The backend requires the key on
  `POST /admin/fees/payments` (min 8 chars) precisely so a retried request at
  the counter cannot take the money twice; the UI must not defeat that by
  generating a fresh key per click.

### 4.6 Authentication

- `POST /auth/login` returns both an access token and a refresh token. The web
  client currently **stores only the access token and discards the refresh
  token**, so staff are bounced to the login screen when the access token
  expires (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440`, refresh 30 days).
- Slice 0 stores both and refreshes through `POST /auth/refresh` on a 401,
  retrying the original request once. A failed refresh clears both and returns
  to login.
- `/auth/me`'s `permissions`, `roles`, `school_name` and `academic_year` are
  loaded into auth context and used by the shell — replacing the hardcoded
  `"Academic year 2025-26"`.

### 4.7 Error handling

The client currently handles only 401. It gains:

| Status | Behaviour |
|---|---|
| 401 | Attempt refresh once, retry, else clear and redirect to login |
| 403 | In-page "you do not have permission" state. **Not** a redirect — a redirect on 403 reads as a crash |
| 404 | "Not found", distinct from 403, and never made more helpful |
| 422 | Field-level errors mapped from FastAPI's `detail[].loc`, landing on the input that caused them |
| 5xx | Error boundary showing what failed, with a retry |

### 4.8 Shared primitives

Enough for slices 1–6 to be built without re-inventing:

- Paged, searchable, filterable table.
- Form fields bound to generated types.
- **Confirm-with-reason dialog.** The API refuses `void`, `status_change` and
  `delete` without a reason; the UI demands it up front rather than surfacing a
  422 after the fact.
- Money and date formatting (`money()` retained).
- Empty, loading, error and permission-denied states.
- **Keyboard-first rule, recorded here for later slices:** search focuses on
  load, Enter submits, tab order follows the form, and bulk screens
  (attendance for a section, marks for a class) are grids rather than repeated
  forms. A clerk takes ~200 payments a day; mouse-driven single-record forms
  are how an ERP gets abandoned.

---

## 5. Testing

**Unit and component — Vitest + React Testing Library + MSW.** MSW handlers are
typed against `schema.d.ts`, so a mock returning a shape the API no longer
returns fails to compile. This closes the usual hole where a suite passes
against fiction.

The tests that carry this slice are the gates:

- A fee collector's nav contains no Payroll, HR or Transport entry.
- A transport manager's nav contains no Fees entry.
- Direct navigation to `/payroll` as a fee collector is refused, not merely
  hidden.
- A school with `feature.transport` off shows no Transport group even for a
  super admin.
- **Every `permission` string in the registry exists in the backend
  catalogue.** The frontend twin of
  `test_every_report_names_a_permission_that_exists`; a typo'd permission is a
  screen nobody can open, or a gate that never matches.

**Live smoke — `web/smoke.mjs`** (Node, no browser), run against a seeded
backend: log in as three roles, fetch `/auth/me`, assert the derived nav
matches what that role should see, and confirm each screen's endpoint answers.
This is the piece that would have caught the Fees 404, and the technique that
found eight defects during the 8 September sweep.

**CI.** `.github/workflows/ci.yml` already exists and already has a `web` job
running `npm ci`, typecheck and build — it has simply **never executed**,
because nothing has ever been pushed. Slice 0 extends that job with `npm test`
and the schema-drift check rather than creating a new workflow.

The drift check needs the API's schema to compare against. Two options, to be
settled during implementation: generate from the FastAPI app directly in CI
(`python -c "import json, app.main; print(json.dumps(app.main.app.openapi()))"`,
no server needed), or have the backend job publish `openapi.json` as an
artifact the web job consumes. The first is simpler and has no cross-job
ordering; it is the default unless it proves awkward.

---

## 6. Delivery

Seven independently committable steps, in order:

1. **Backend:** `modules` on `/auth/me`, with a test.
2. **Codegen:** `openapi-typescript` dev dependency, `npm run api:types`,
   committed `schema.d.ts`, typed client.
3. **Auth:** refresh-token storage and use; `/auth/me` fields into context;
   real school name and academic year in the header.
4. **Registry and shell:** `screens.ts`, derived nav and router, three gates.
5. **Primitives:** table, forms, confirm-with-reason, formatting, error and
   empty states, idempotency-key convention.
6. **Test setup:** Vitest + RTL + MSW, the gate tests, `smoke.mjs`, CI drift
   check.
7. **Migrate the existing nine pages** onto the registry and typed client —
   including the Settings page's dead endpoint, which the compiler will now
   point at.

---

## 7. Risks

- **Migrating nine pages onto generated types will surface more drift than the
  one known 404.** That is the purpose, but it makes Slice 0 larger than it
  looks. Better discovered here than in Slice 3.
- **Generated type quality depends on the FastAPI schema.** Routes annotated
  `-> dict` will type as loose objects. Those spots want response models
  backend-side over time; this slice records which they are and does not fix
  them all.
- **The nine existing pages have no tests**, so migrating them is unguarded.
  Mitigation: the smoke script covers their endpoints before migration begins.

---

## 8. The rest of the workstream

Amended after the "is this good for real school operation" review, which found
three verified gaps.

| Slice | Contents |
|---|---|
| **0** | *This spec* — foundation |
| **1** | Office desk: Students (deepen) + Admission (50 ops) |
| **2a** | **Printing (backend prerequisite).** Admin-side receipt PDF and report card PDF. Today the only PDF route in the API is `/parent/fees/receipts/{payment_id}.pdf`; there is **no admin route**, so the counter clerk who takes the cash cannot print a receipt. `app/pdf/` contains only `receipt.py`. An Indian school runs on paper; Slice 2 is not shippable without this. |
| **2** | Money: fee setup, invoices, collection, defaulters, periods, concessions |
| **3** | Academics: attendance, exams, marks, report cards, grading, timetable |
| **4** | Staff: HR, departments, leave, staff attendance, payroll |
| **5** | Operations: transport, communication/outbox |
| **6** | Insight and admin: dashboards, the 21-report library, settings, audit |

### Known to be outside this workstream entirely

Stated so that "a real school could run on it" is not overclaimed. **Nothing is
deployed. CI has never run. 81 commits, nothing pushed.** There is no hosting,
no backup, no restore drill and no monitoring. A school's fee ledger existing
only on a development laptop is not an operations story, and no amount of
frontend work changes that. It is a separate workstream and should be named as
one.
