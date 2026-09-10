# Frontend handoff — building the ERP the office actually uses

> **PARTLY SUPERSEDED — read `SESSION-HANDOFF-2.md` first.**
>
> Packet 0 and Packet 2 are **done**, on branch `slice/office-feedback`
> (10 commits, unpushed). **Part One's status below is stale** — the app can
> take a payment now — and **Part Zero's cold start does not work as written**
> on this machine.
>
> The git protocol in Part Zero says to branch off `main`. **Do not.** `main`
> has none of this work; branch off `slice/office-feedback`.
>
> Parts Two (contracts), Three (design rules), Four (the remaining packets),
> Five (report format) and Six (traps) are all still binding.

**Written 10 September 2026.** This is the brief for the next session, and that
session's work is executed by **subagents**. It is written to be handed to them
whole: a subagent that reads only its own packet still has the contracts, the
design rules and the report format it must satisfy.

`HANDOFF.md` stays canonical for backend architecture and history. `CLAUDE.md`
has the house rules. The old `SESSION-HANDOFF.md` is **complete and
superseded** — its three fixes shipped, the branch is merged.

---

# PART ZERO — cold start, on this machine

Do this before reading further. Every command here was run on 10 Sep 2026 and
works; the README's `make up` path does **not** — it calls `docker compose`,
and **Docker is not installed on this machine**. Postgres runs natively.

```bash
# The repo. main IS the ERP as of 10 Sep 2026 (PR #1 merged).
cd "C:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system"
git checkout main && git pull

# Python deps already live in .venv at the repo root. Never `activate` it;
# call it by path, which is what every command below and in CLAUDE.md does.
.venv/Scripts/python.exe --version          # 3.13.7

# Node deps
npm --prefix web ci

# The test database, by hand (make testdb uses Docker and fails here).
# If sunrise_test already exists this is a no-op.
psql -U sunrise -c "CREATE DATABASE sunrise_test" 2>/dev/null || true
```

**Confirm the baseline is green before you change anything.** If any of these
is already failing, that is a finding to report, not something to work around:

```bash
cd backend && ../.venv/Scripts/python.exe -m pytest -q      # 615 passed
cd ../web && npx tsc --noEmit && npm test                   # 0 errors, 31 passed
npm run api:check && npm run build
```

**The running stack, for the click-through Contract 2 requires.** Two
terminals:

```bash
# terminal 1 — the API. The env var is not optional: without it uvicorn talks
# to the stale dev database, which is several parts behind and looks exactly
# like a bug in whatever you are probing.
cd backend
DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test   ../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8077

# terminal 2 — the web app, pointed at it
cd web
VITE_API_URL=http://127.0.0.1:8077 npm run dev     # http://localhost:5173
```

Seed data, if the database is empty or you want it reset:

```bash
cd backend
export DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test
../.venv/Scripts/python.exe -m alembic upgrade head
BCRYPT_ROUNDS=4 ../.venv/Scripts/python.exe seed.py
```

**Logins are in `PASSWORDS.md` at the repo root.** It is gitignored and local
only, so it is not in the repo you cloned — ask the owner if it is missing.
The login screens no longer print credentials.

**Git protocol for this work:** branch off `main` as `slice/<packet>`, never
commit to `main` directly, and do not merge or push without the owner saying
so. Show the exact file list first — that is a standing rule in `CLAUDE.md`.

---

# PART ONE — where the frontend actually stands

Re-measure before trusting any of this; the commands are given so you can.

## The gap, in one table

The backend exposes **211 admin operations**. The web app reaches **20 paths**.
Measured 10 Sep 2026 by walking `app.openapi()` against the endpoints the
pages actually call:

| Area | Admin operations | Paths with a UI | What that means |
|---|---:|---:|---|
| **Admission** | 50 | **0** | The entire enquiry → application → assessment → offer → conversion pipeline is API-only |
| **HR + payroll** | 41 | 1 | A read-only staff list. No departments, leave, register, salary, payslips |
| **Examinations** | 22 | 2 | Exams and their schedule. No marks entry, grading scales, schemes, report cards |
| **Fees** | 21 | 4 | Invoice list, collection total, generate. **No way to take a payment** |
| **Config + core** | 20 | 8 | `/admin/configuration` — settings, module switches, custom fields — has **no UI at all** |
| **Transport** | 18 | 0 | Nothing |
| **Timetable** | 14 | 1 | A read-only grid on the Classes screen |
| **Communication** | 14 | 2 | Notice list and publish. No outbox, no delivery report |
| **Attendance** | 8 | 2 | Roll and summary, read-only |
| **Reports** | 3 | 0 | The 21-report library is unreachable |

**This is the whole job.** The backend is not the constraint and has not been
for weeks. A school cannot run on this yet because the office cannot reach it.

## What is solid and must not be re-litigated

These were built and reviewed in Slice 0 and are the seams everything else
hangs off. Extend them; do not replace them.

- **`web/src/screens.ts`** — every screen declared once. The sidebar, the
  router and the permission gate all derive from it, so a menu item cannot
  point at a route that refuses you. `permissions[]` and `modules[]` are both
  lists and **all** entries are required. Read its header comment before
  adding an entry; it explains which calls belong on a screen and which gate
  themselves at the widget.
- **`web/src/api/schema.d.ts`** — generated from FastAPI's own schema by
  `npm run api:types`, drift-checked in CI by `npm run api:check`. **Never
  hand-edit it.** A deleted endpoint is now a compile error rather than a
  silent 404 — which is exactly how the Settings page called a dead route for
  weeks while `tsc` stayed green.
- **`web/src/api/client.ts`** — paths and *responses* are typed off the schema.
  Tokens, refresh and `ApiError` are handled centrally. Money arrives as a
  string and must stay one (`money()`); parsing a `Numeric` into a JS float is
  how a fee ledger loses a paisa.
- **`web/src/components/ui.tsx`** — `Card`, `StatCard`, `Pill`, `Empty`,
  `DataTable`, `Modal`, `FormField`, `inputClass`. `DataTable` already handles
  loading, error and empty states; use it rather than writing a `<table>`.
- **`web/src/auth/`** — `AuthContext` exposes `can(permission)` and
  `hasModule(code)`; `RequirePermission` is the in-page gate.

## Verified state — 10 September 2026

| Measure | Value | Command |
|---|---|---|
| Web tests | **31** in 7 files | `cd web && npm test` |
| Backend tests | **615** | `cd backend && ../.venv/Scripts/python.exe -m pytest -q` |
| `tsc --noEmit` | 0 errors | `cd web && npx tsc --noEmit` |
| Schema drift | current | `cd web && npm run api:check` |
| Branch | `main`, merged, **CI green both jobs** | |

The demo school has **`hr` and `transport` switched off** by default
(`core/modules.py`). Any screen behind those modules is invisible until you
turn them on via `PUT /admin/configuration`. A 404 from a module gate looks
exactly like a 404 from a missing route — check `me.modules` first.

---

# PART TWO — the three contracts every subagent obeys

Non-negotiable. A packet that violates one of these is not done, however good
it looks.

## Contract 1 — the registry is the only way to add a screen

One entry in `screens.ts` plus a component. Navigation, routing, permission
gating and module hiding all follow from it. Before writing the entry, **open
the backend router** and read what the endpoints actually require — three of
them are not in the file their name suggests:

- `/admin/subjects` and `/admin/timetable` are served by `api/admin/classes.py`
  on `academics.class.read`
- `/admin/grade-bands` is served by `api/admin/stats.py` on
  `admin.settings.read`

Declaring a permission a screen does not need is as much a bug as omitting one:
it hides the screen from a role whose job it is. The tests in
`screens.test.tsx` pin four such role outcomes. Read them.

## Contract 2 — verify before claiming, with output

The house rule (`CLAUDE.md`), and the reason this project has survived several
green-suite-with-live-defects incidents. For a frontend packet it means:

- `npx tsc --noEmit`, `npm test`, `npm run api:check` and `npm run build` all
  pass, and **you paste the output**, not a summary of it.
- Every new screen is **opened against a running backend** and every control on
  it clicked, as a role that should be able to use it *and* one that should
  not. Start the API on 8077 against the test database (the command is in
  `SESSION-HANDOFF.md` Part Two; without `DATABASE_URL` uvicorn talks to a
  stale dev database that is several parts behind and looks exactly like a bug
  in whatever you are probing).
- "It type-checks" is not "it works". Seven device defects on this project were
  invisible to `tsc`.

## Contract 3 — writes are gated, confirmed and audited

The backend refuses what a caller may not do, but a UI that renders a button
that always 403s is a broken UI. Today **no page checks `can()`** — every write
control renders for everyone. That ends with this work.

- A control that performs a write is **hidden or disabled** unless
  `can(<the write permission>)`. Disabled with a reason beats hidden where the
  user would otherwise wonder if the feature exists.
- Anything destructive — void, reverse, delete, deactivate, status change —
  **asks for confirmation and a reason**, because `services/audit.py` refuses
  to commit those without one. Send the reason the user typed; never a
  hardcoded string.
- Money is never edited. An invoice is **voided and reissued**; a payment is
  **reversed by a contra entry**. Do not build an edit form for either.

---

# PART THREE — what "clean and easy for school administration" means here

The user is a clerk at a counter with a queue in front of them, a principal who
opens the app twice a day, and an accountant at month end. None of them are
technical. The building is in Lucknow; the office runs on paper and a printer.

Concrete rules, not taste:

1. **One primary action per screen, above the fold.** The Fees screen's job is
   *take a payment*. The Students screen's job is *find a child*. Everything
   else is secondary and looks it.
2. **Search is the first control on any list**, and it searches what the clerk
   actually knows: name, admission number, phone. Not an id.
3. **Keyboard-first data entry.** Marks entry, attendance marking and fee
   collection are bulk tasks — Tab moves to the next field, Enter submits,
   nothing requires a mouse. A clerk entering 40 marks with a mouse is a
   feature nobody uses.
4. **Empty states say what to do next**, not "No data". "No fee plan
   configured — add one in Settings" is a working screen; "No records found" is
   a dead end.
5. **Errors name the field and the fix.** `ApiError.message` carries the
   backend's own 422 detail; surface it next to the input, not in a toast that
   vanishes.
6. **Money and dates in Indian formats.** `money()` for every amount —
   ₹1,20,000 not $120000. Dates as `dd/mm/yyyy` on screen, ISO on the wire.
7. **Printing is a first-class action, not an afterthought.** A receipt, a fee
   card, a report card and a defaulter list all end up on paper. Where a PDF
   route exists, link it; where it does not, say so in your report rather than
   inventing a print button that does nothing.
8. **Nothing invented.** An empty state beats a fabricated number — the owner's
   standing rule, and it applies to placeholder rows, fake totals and "—"
   standing in for a value that failed to load. If a query failed, say it
   failed.
9. **The screen tells you whose data it is.** Multi-tenant: the school's name
   is in the shell already; keep it visible. A clerk should never wonder which
   school they are looking at.

---

# PART FOUR — the work, as subagent packets

## How to run these

**Packet 0 is blocking. Everything else can run in parallel after it merges.**

The reason is mechanical: Packets 1–4 all add entries to `screens.ts` and all
import from `components/ui.tsx`. Two agents editing those files concurrently
will conflict, and a merge conflict in the screen registry is a security-shaped
bug rather than a formatting one — a dropped entry silently removes a gate.

**The protocol:**

- Packet 0 lands first, on its own, and is verified before anything else starts.
- Each later packet works on **its own branch off `main`**, named
  `slice/<packet>`, and touches **only** the files its packet names.
- **Only the orchestrator edits `screens.ts`.** A packet reports the entry it
  needs — path, label, group, permissions, modules — as *text in its report*.
  The orchestrator adds all entries in one commit after the packets land. This
  keeps the registry a single reviewed diff.
- `components/ui.tsx` is owned by Packet 0. A later packet needing a new shared
  primitive **reports the need** rather than adding it; a one-off component
  lives in that packet's own folder until a second screen wants it.

---

## Packet 0 — the write layer *(blocking, do first)*

**Why this before features:** the nine existing screens are read-mostly. Every
packet below is write-heavy, and three gaps make writes worse the more of them
you build:

- `api.post`/`api.patch` take **`body?: unknown`**. Paths and responses are
  typed; request bodies are not. A write with a misspelled or wrongly shaped
  field compiles cleanly and fails at runtime — which is the exact class of
  defect the generated schema exists to prevent.
- **No page checks `can()`**, so write controls render for every role and 403.
- There is no shared confirm-with-reason, no toast, no form-error surface, so
  every packet will invent its own and they will disagree.

**Deliver:**

1. Type request bodies off the generated schema, so
   `api.post("/admin/students", {...})` fails to compile when the shape is
   wrong. The `paths` type already carries `requestBody`; extract it the way
   `Ok<>` extracts the response.
2. `<Can permission="...">` and/or a `useCan()` hook, plus an `ActionButton`
   that disables itself with a tooltip when the permission is absent.
3. `<ConfirmDialog>` that **requires a typed reason** and returns it, for the
   destructive paths listed in Contract 3.
4. A toast/inline-error convention wired to `ApiError`, so a 422 lands next to
   the field and a 500 does not vanish.
5. A `useMutation` wrapper that invalidates the right query keys and surfaces
   errors consistently.

**Files:** `web/src/api/client.ts`, `web/src/components/ui.tsx`, new
`web/src/components/` primitives, `web/src/auth/`.
**Tests:** typed-body compile failure proven by a `// @ts-expect-error` case;
`Can` hides/disables for a role lacking the permission; confirm dialog refuses
to submit an empty reason.
**Do not** add screens in this packet.

---

## Packet 1 — Admission *(the largest gap: 50 operations, zero UI)*

The pipeline the office runs every February. Enquiry → application → documents
→ assessment → decision → offer → conversion to a student.

**Screens:** an admission dashboard (funnel counts, today's work), the enquiry
register with follow-up dates, the application list with filters and a detail
view, document checklist, assessment scheduling, the decision and offer
workflow, the waitlist, and conversion.

**Read first:** `app/api/admin/{admission,applications,admission_documents,
admission_assessment,selection,conversion,admission_reports}.py` and
`ERP_BLUEPRINT` §5.1.

**Rules specific to this packet:**
- **An applicant is not a user.** Nothing here may require a `students` or
  `users` row — most applicants never get one. A sibling or staff-parent link
  is a *claim* until verified, and an unverified claim must never influence a
  decision. Show claims as claims.
- Offers expire. A lapsed offer releases the seat and the waitlist moves —
  surface that, do not hide it behind a refresh.
- The public portal (`/public/{school_code}/...`) is unauthenticated and its
  404s are deliberately identical across every failure reason. Do not build an
  admin screen that makes those distinguishable.

---

## Packet 2 — Fees at the counter *(the money path)*

**Today the app cannot take a payment.** It lists invoices and shows a
collection total. That is the single most-used screen in a real school office
and it does not exist.

**Screens:** collect payment (search child → show ledger → take amount →
allocate → print receipt), the student fee ledger, defaulters with the chase
list, fee setup (heads, plans, assignments), concessions with the approval
step, and period close.

**Read first:** `app/api/admin/{fees,fee_setup}.py`, `app/services/fees.py`,
and the money rules in `CLAUDE.md`.

**Rules specific to this packet:**
- Payments allocate to invoice **lines**, never to invoices. A balance is
  always a `SUM`, never a stored field you cache in component state.
- Use `money()` everywhere. Half-up rounding is the backend's job; do not
  re-round in the UI.
- Seeded invoices already carry late fees — do not assume a round amount.
- **Blocked dependency, report it rather than fake it:** there is still **no
  admin-side receipt PDF**. The only PDF route is
  `/parent/fees/receipts/{payment_id}.pdf`. A counter clerk cannot print. If
  your packet needs it, say so in the report; do not add a print button that
  opens the parent route.

---

## Packet 3 — Configuration *(what makes it sellable as multi-tenant)*

`/admin/configuration` — the setting store, the eleven module switches, and
custom fields — has **no UI at all**. §0.18 says a records clerk must be able
to use it. Right now enabling a module needs a `curl`.

**Screens:** module switches with a plain-English description of what each one
turns off; the settings registry grouped by area (late fee, sibling
concession, due day, attendance shortage threshold, teacher load ceiling);
custom field definitions; academic year management.

**Read first:** `app/core/{settings_registry,modules}.py`,
`app/api/admin/settings.py`.

**Rules specific to this packet:**
- **`/admin/settings` is the school's profile and branding.
  `/admin/configuration` is the setting store and module switches.** They are
  different endpoints; the names mislead.
- Turning a module off must warn what disappears, and it takes effect on the
  *next* `/auth/me` — the sidebar will not change until the session refreshes.
  Handle that, or the clerk thinks it failed.
- Money rules are settings, not constants. Changing the late fee here is the
  supported path; editing a number in code is not.

---

## Packet 4 — Staff and payroll *(41 operations, one read-only list)*

**Screens:** the staff register, departments, employee profile (with salary
behind its own permission), leave with balances and the approval flow that
raises cover, the daily staff attendance register, salary structures, and
payroll runs with payslips.

**Read first:** `app/api/admin/{hr,payroll,staff_leave,staff_attendance,
teachers}.py`.

**Rules specific to this packet:**
- **The `hr` module defaults to OFF.** Turn it on before you can see anything.
- Salary sits behind `hr.salary.read`, deliberately separated from the rest of
  the profile — a records clerk must not read colleagues' pay. Do not render it
  in a shared profile component that a lesser role also mounts.
- An approved payroll run is **immutable**. A correction is a supplementary
  run, not an edit. Do not build an edit form.

---

## Later, named so the shape is visible

Academics (marks entry, grading scales, schemes, report cards — 22 ops),
Transport (18 ops, module off by default), Communication (outbox and delivery
report), and the 21-report library. Each is a packet of the same shape.

---

# PART FIVE — the report every subagent submits

This is the deliverable the owner verifies against. A packet without it is not
finished. **Write it as `reports/<packet-name>.md` in the repo** and paste the
summary into your final message.

```markdown
# Packet <n> — <name>

## What I built
One line per screen: route, what a clerk does on it, which endpoints it calls.

## The screens.ts entry the orchestrator must add
Verbatim, ready to paste: path, label, group, permissions[], modules[].
State which backend router you read to determine each permission.

## Verification — commands and their real output
- npx tsc --noEmit          <paste>
- npm test                  <paste: N passed, and the new test names>
- npm run api:check         <paste>
- npm run build             <paste>
- Backend suite if touched  <paste>

## What I clicked, as whom
Every control, against a running backend, as a role that may use it and a
role that may not. State the login used and the observed result. A screen
that was never opened is reported as never opened.

## What I did NOT do
Scope consciously dropped, and why. Anything blocked on a backend gap.
Anything I could not verify.

## Defects found in existing code
Anything you tripped over that was already broken. Do not fix outside your
packet's files — report it.

## Files changed
Exact list.
```

**Two rules about the report**, both learned the hard way on this project:

- **Report what you ran, not what you intended to run.** If a check failed and
  you moved on, that goes in the report. A green summary over a red run is the
  one thing that makes this whole process worthless.
- **A screen you did not open does not work.** Type-checking proves the shape
  of the code, not the behaviour of the product. Say plainly which screens were
  opened and which were not.

---

# PART SIX — traps that will cost a subagent an hour

- **`schema.d.ts` is generated.** Editing it by hand appears to work until CI's
  drift check fails. Run `npm run api:types` instead.
- **`/admin/settings` ≠ `/admin/configuration`.** Profile and branding versus
  the setting store and module switches.
- **`hr` and `transport` default to OFF.** Their screens are invisible until
  switched on. `me.modules` tells you what this school has.
- **The demo school's id is not 1.** Read it from the API, never hardcode it.
- **Demo logins:** admission numbers are `2024000001` (`YYYY` + six digits).
  `SPS2024001` has not existed for some time. Passwords are in the gitignored
  `PASSWORDS.md`; the login screens no longer print them.
- **Start the API with `DATABASE_URL` set to `sunrise_test`.** Without it,
  uvicorn talks to a stale dev database several parts behind, which looks
  exactly like a bug in whatever you are probing.
- **Money is a string on the wire.** Keep it one. `money()` formats it.
- **A teacher holds most `.read` permissions school-wide** with the restriction
  in the service, so a screen gated only on a `.read` permission is not
  necessarily narrow. If you are building a whole-school view, check the
  endpoint narrows it.
- **`web/smoke.mjs` mirrors `screens.ts` by hand.** Add your screen there too,
  with its module, or the smoke run stops proving anything. Deriving it from
  the registry is an open item and a fine thing to fix.
- **The README's cold start is wrong for this machine.** It says
  `make up && make migrate && make seed`, and `make up`/`make testdb` call
  `docker compose`. Docker is not installed here. Use Part Zero above.
- **`main` is the ERP now.** Anything describing `part-1-foundation` as
  unpushed, or the branch as 112 commits ahead, is pre-10-September and stale.
- **Cross-tenant regressions are the live risk.** Eleven were found and fixed
  on 9 Sep; `backend/tests/test_tenant_crossing.py` pins them. If your packet
  adds a backend route, add its check there.

---

# PART SEVEN — what the owner checks before accepting

Run these yourself before submitting; they are the acceptance test.

1. `cd web && npx tsc --noEmit && npm test && npm run api:check && npm run build`
2. `cd backend && ../.venv/Scripts/python.exe -m pytest -q` — still 615+
3. Start the API on 8077 and `node smoke.mjs http://127.0.0.1:8077` — all pass
4. Open every new screen as **at least two roles**, one who may and one who may
   not, and confirm the sidebar, the route guard and the write controls all
   agree
5. Turn off a module the screen depends on and confirm the screen disappears
   cleanly rather than erroring
6. Read the report against the diff — every claim in it should be checkable

**The standing rule above all of these:** never put a claim in a report that
cannot be defended. An honest "not verified" is worth more than a confident
green that turns out to be a summary of something nobody ran.
