> **SUPERSEDED — 12 September 2026.** Superseded by **`SESSION-HANDOFF-3.md`**
> and **`SINGLE_SOURCE_OF_TRUTH.md`**. Packet 1 (Admission), Academics & Examination
> Depth, Reports Library, and UI Standardization are all complete.

# Session handoff — Packet 0 and Packet 2 are done

**Written 10 September 2026**, at the end of the session that built the write
layer and the money path.

## What this supersedes, and what it does not

`FRONTEND-HANDOFF.md` is still the brief. Read it — but **Part One's status is
now stale** and this file replaces it. Everything else there remains canonical
and you should follow it exactly:

- **Part Two — the three contracts.** Unchanged. Still binding.
- **Part Three — what "clean and easy" means.** Unchanged.
- **Part Four — the packets.** Packet 0 and Packet 2 are done; 1, 3, 4 and the
  "Later" list are not.
- **Part Five — the report format.** Unchanged. `reports/packet-2-fees.md` is a
  worked example.
- **Part Six — traps.** Still true, plus the new ones in Part Five below.
- **Part Zero — cold start.** Partly wrong. Use Part Zero *here* instead.

`CLAUDE.md` now points at this file first, and `FRONTEND-HANDOFF.md` carries a
banner saying which of its parts are stale. Both were changed at the end of the
session, after checking what a fresh session would actually read: without them
it would have gone CLAUDE.md → FRONTEND-HANDOFF Part One, been told the app
cannot take a payment and that Packet 0 is blocking and undone, branched off
`main` as its git protocol says, and rebuilt work that already exists.

`CLAUDE.md`'s 615/31 figures are `main`'s and are still correct for `main`; the
branch figures are noted beside them.

---

# PART ZERO — cold start that actually works

Branch is **`slice/office-feedback`**, 10 commits ahead of `main`, working tree
clean apart from `SESSION-HANDOFF.md` and `reports/README.md`, which were
already modified/untracked before this session began, plus
`.claude/launch.json`, which this session added so the in-editor preview can
start the dev server.

**Nothing has been pushed.** No PR. That is deliberate and waiting on the owner.

> **Branch off `slice/office-feedback`, not off `main`.** `FRONTEND-HANDOFF.md`
> Part Zero and Part Four both say "branch off `main`" — that was right when
> they were written and is wrong now: `main` is at `232a791` and has none of
> these commits. A session that follows it literally rebuilds Packet 0.
>
> Two intermediate branches still exist and are **not** where the work is:
> `slice/packet-0` (`61a01f6`) and `slice/packet-2` (`e8d2aef`). They are
> ancestors of `slice/office-feedback`, kept only so the packet boundaries stay
> legible. Delete them once this is merged.

```bash
cd "C:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system"
git checkout slice/office-feedback

.venv/Scripts/python.exe --version      # 3.13.7
npm --prefix web ci                     # only if node_modules is missing
```

### The database

Postgres runs natively. `sunrise_test` already exists. **`psql` will hang
waiting for a password** unless you pass one:

```bash
export PGPASSWORD=sunrise
psql -U sunrise -h localhost -d sunrise_test -c '\dt' | head
```

To reset the demo data to a known state — do this, rather than re-running the
seed over a dirty database:

```bash
cd backend
export PGPASSWORD=sunrise
psql -U sunrise -h localhost -d sunrise_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
export DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test
../.venv/Scripts/python.exe -m alembic upgrade head
BCRYPT_ROUNDS=4 ../.venv/Scripts/python.exe seed.py
```

> **`alembic upgrade head` fails if you have run pytest against `sunrise_test`
> first** — `DuplicateTable: relation "exams" already exists`. The suite builds
> its schema with `create_all` and leaves no alembic stamp, so the migration
> tries to create tables that are already there. Drop the schema first, as
> above. `FRONTEND-HANDOFF.md` Part Zero omits this and its seed block fails in
> the normal working order.

### The stack

```bash
# terminal 1 — the API. The env var is not optional.
cd backend
DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test \
  ../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8078

# terminal 2 — the web app
cd web && npm run dev          # http://localhost:5173
```

**The API is on 8078, not 8077.** `web/.env` (gitignored) holds
`VITE_API_URL=http://127.0.0.1:8078`. Vite reads `.env` only at startup, so
changing the port means restarting the dev server.

> **Why 8078:** a uvicorn process got stuck holding 8077 and kept serving stale
> code after `taskkill` reported it gone — `netstat` showed two listeners on the
> same port. It cost real time: a fix that was correct in the file and green in
> the tests looked broken in the browser. If a change is green in pytest but the
> running API disagrees, check for a zombie before you doubt the code:
> `netstat -ano | grep :8078`.

Logins are in the gitignored `PASSWORDS.md`. `admin@sunrisepublic.edu` and
`counter@sunrisepublic.edu`, both `Admin@123`.

### The checks

```bash
cd web && npx tsc --noEmit && npm test && npm run api:check && npm run build
cd ../backend && ../.venv/Scripts/python.exe -m pytest -q
cd ../web && SMOKE_PASSWORD='Admin@123' node smoke.mjs http://127.0.0.1:8078
```

Expected, and true at the last commit:

| Check | Value |
|---|---|
| `tsc --noEmit` | 0 errors |
| `npm test` | **43 passed, 11 files** (baseline was 31 in 7) |
| `npm run api:check` | up to date |
| `npm run build` | clean |
| `pytest -q` | **623 passed** (baseline was 615) |
| `node smoke.mjs` | all checks pass, three roles |

---

# PART ONE — where the frontend stands now

**13 screens** are registered, up from 9. The four new ones are all Money.

| Route | Label | State |
|---|---|---|
| `/fees/ledger` | Student fees | New. Search a child, read their fee account, reverse a payment. **Does not take payments** — see below |
| `/fees/defaulters` | Defaulters | New. Chase list with a number to ring |
| `/fees/setup` | Fee setup | New. Fee plans, concessions, the approval step |
| `/fees/periods` | Period close | New. Close/reopen a month |

**Fee collection is NOT on the web app.** It was built here — Packet 2 existed
to make "the app can take a payment" true — and then removed on the owner's
decision: collection is handled in the mobile app, in the hands of whoever is
facing the parent. The web keeps the ledger.

The backend never changed. `POST /admin/fees/payments` is live, idempotent and
allocates oldest-invoice-line-first; the mobile app calls it. Do not rebuild a
payment form on the web without asking the owner first — it was removed
deliberately, not overlooked.

## Packet 0's write layer — what exists to build on

Do not reinvent any of this:

- **Typed request bodies.** `api.post`/`patch`/`put` take the body the schema
  declares. A wrong or missing field is a compile error. `api.put` exists now —
  14 routes are PUT, including `/admin/configuration` that Packet 3 needs.
- **`<ActionButton permission="…">`** — disables itself and names the missing
  permission in `title`. Always `type="button"`.
- **`<Can permission="…">`** — hides a section. No `useCan`; `useAuth()` already
  exposes `can`.
- **`<ConfirmDialog>`** — will not submit without a typed reason, returns it
  trimmed. Use for anything `services/audit.py` audits.
- **`FormField error=…` and `<FormError>`** — a 422's field messages next to
  their inputs, everything else still visible.
- **`useWrite`** — thin over react-query's `useMutation`; invalidates the keys
  you name, exposes `.fields` for the 422 case.

## Contract 3 — precisely how far it got

Contract 3 says no page should render a write control the caller cannot use.
That is now true of **five** pages and false of **three**:

| Wired | Not wired, but has write controls |
|---|---|
| FeeLedger, FeePeriods, FeeSetup, Settings, Students | **Notices** (2 writes), **Fees** (1 write), **Exams** (2 writes) |

Dashboard, Classes, Attendance, Teachers and Defaulters have no write calls at
all, so there is nothing to gate on them.

**Wiring those three is small, self-contained, and a good first task** — swap
their raw `<button>`s for `ActionButton` with the right permission, and put
`ConfirmDialog` on the Notices delete.

---

# PART TWO — what is verified, and what is not

Verified by clicking against a running API as two roles, with network status
codes recorded — see `reports/packet-2-fees.md` for the full table.

**Not verified, and you should not assume it works:**

1. **The Add plan form on `/fees/setup`.** Built, type-checks, never submitted
   against the live API. The one control in Packet 2 that was never exercised.
2. **Enter-to-submit anywhere.** The browser automation's synthetic Return does
   not trigger form submission — proven on the *pre-existing* login form too,
   so it is the harness, not the app. Every click path is verified. A human
   should press Enter on the Student fees search box;
   keyboard-first is Part Three rule 3 and it is currently unproven.
3. **Anything on the seven screens this session did not touch.**

---

# PART THREE — open defects, none of them fixed

Found while building, deliberately left for the packet that owns the file:

1. **`PATCH /admin/settings` always 422s — Settings → Save has never worked.**
   `academic_year` is returned by the GET and forbidden by the PATCH
   (`extra="forbid"`), and the page posts the whole response back. Pre-existing
   on `main`. **Packet 3's territory.** This is the highest-value one-line fix
   on the list.
2. **`DELETE /admin/notices/{id}` writes no audit row.** Every other destructive
   path is audited with a reason; this one commits silently. Either audit it or
   write down why it is exempt.
3. **`money()` renders `₹NaN`** for an absent value instead of failing. It hid a
   wrong field name on a live fee screen with `tsc` perfectly green. A money
   helper that can print NaN on a fee screen deserves a decision.
4. **A write gated on a read permission.** `POST /admin/exams/{id}/schedule`
   declares no permission dependency and inherits `admin_only` =
   `exam.definition.read`. Anyone who can look at the exam calendar can add a
   paper to it. Every sibling route in that file declares
   `exam.definition.write`.
5. **Dates render US-style** on any screen using bare `toLocaleDateString()` —
   Notices shows `9/10/2026` for 10 September. Part Three rule 6 wants
   `dd/mm/yyyy`. The screens this session touched use `"en-GB"`.

## The blocked dependency that shapes several things

**No endpoint maps a student to their `enrolment_id`.** `/admin/students` and
`/admin/students/{id}` both omit it; only rows that already carry money
(`invoices`, `defaulters`, `ledger.invoices`) have it. Live consequences:

- A student with **no invoices** shows an empty ledger, and the screen says
  so rather than leaving the reader guessing.
- Concession rows are named by joining through `/admin/fees/invoices`, which
  works only because every seeded student has one.
- **Plan assignment and concession *requests* are not built** because of it.

The fix is backend: `enrolment_id` on the student row, or a small
`/admin/enrolments?student_id=` lookup. Cheap, and it unblocks three things.

**Also still true:** there is **no admin-side receipt PDF**. The only PDF route
is `/parent/fees/receipts/{payment_id}.pdf`. A counter clerk cannot print. The
ledger screen offers no print button rather than opening the parent route.
Printing a receipt is the mobile app's problem now, not the web's.

---

# PART FOUR — what to do next, in order

1. **Wire Contract 3 into Notices, Fees and Exams.** Small, uses what Packet 0
   already built, and closes the contract. Half a session. The five controls
   and the permission each needs, read off the routers so you do not have to:

   | Page | Control | Route | Permission |
   |---|---|---|---|
   | Notices | Publish | `POST /admin/notices` | `comms.notice.publish` |
   | Notices | Delete | `DELETE /admin/notices/{id}` | `comms.notice.publish` |
   | Fees | Generate invoices | `POST /admin/fees/invoices/generate` | `fees.invoice.generate` |
   | Exams | Create exam | `POST /admin/exams` | `exam.definition.write` |
   | Exams | Add paper | `POST /admin/exams/{id}/schedule` | **see below** |

   The Notices delete is destructive and currently has no confirmation — give
   it `ConfirmDialog`. Note that `services/notices.py::delete` writes no audit
   row, so it will not demand the reason the dialog collects; that asymmetry is
   defect 2 in Part Three and is worth fixing at the same time.

   **`POST /admin/exams/{exam_id}/schedule` declares no write permission at
   all** — it falls through to `admin_only`, which is
   `exam.definition.read` (`api/admin/exams.py:26`). So adding a paper to an
   exam is a write gated on a read. Every other write in that router declares
   `exam.definition.write`. Gate the button on `exam.definition.write` and
   report the route as a backend defect; do not gate it on the read permission
   just because that is what the route currently accepts.
2. **Packet 3 — Configuration.** `/admin/configuration` has no UI at all;
   enabling a module still needs a `curl`. `api.put` now exists, which was the
   missing piece. Fix the Settings 422 while you are in that file.
3. **Packet 1 — Admission.** The largest gap: 50 operations, zero UI.
4. **Packet 4 — Staff and payroll.** Remember the `hr` module defaults to OFF.
5. **Later:** Academics (marks entry, grading scales, report cards), Transport
   (module off by default), Communication outbox and delivery report, and the
   21-report library.

Before any of it: **ask the owner about pushing.** Eight commits sit unpushed on
`slice/office-feedback` and no PR exists. That is their call, not yours.

---

# PART FIVE — traps this session paid for

Add these to `FRONTEND-HANDOFF.md` Part Six's list.

- **A zombie uvicorn can serve stale code after you kill it.** Two listeners on
  one port, `taskkill` reporting success, and a correct fix looking broken in
  the browser. Check `netstat -ano | grep :<port>` before doubting the code.
- **`alembic upgrade head` fails after pytest has touched the same database.**
  Drop the schema first. Part Zero above.
- **`psql` hangs on a password prompt.** `export PGPASSWORD=sunrise`.
- **A `<button>` with no `type` inside a `<form>` submits it.** One click ran
  the write twice; only the idempotency key stopped a double payment.
  `ActionButton` sets `type="button"` — keep it that way.
- **The query cache used to outlive logout**, showing the next person on a
  shared counter PC the previous user's data — including for queries their role
  may not make, where the request never returns so the stale answer stands.
  Fixed in `AuthContext.logout()`; there is a test. Do not remove `qc.clear()`.
- **Concession status is `requested`, not `pending`.** A guard written against
  `pending` made the whole approval step unreachable while looking fine.
- **Routes without a `response_model` are typed `unknown`**, so hand-written
  types over them are unchecked and drift silently. `/admin/fees/ledger` cost a
  `₹NaN` on a live fee screen. Read the service function, do not guess field
  names.
- **`openapi-typescript` marks defaulted fields as required.** Turned off via
  `defaultNonNullable: false` so request bodies do not demand server defaults;
  the cost is 152 response properties becoming optional, measured at zero new
  `tsc` errors.
- **`.gitattributes` pins `web/src/api/schema.d.ts` to LF.** Without it
  `api:check` can never pass on Windows. Do not remove it.
- **Six subjects per stage is load-bearing, not cosmetic.** Ten sections must be
  taught in all thirty periods a week, so ten of twelve teachers are busy every
  period. Only one-specialist-per-stage-per-subject keeps the grid solvable — an
  uneven split left four periods unfillable by any algorithm. Adding a seventh
  subject divides 30 by 7 and breaks the timetable and two of its tests.

---

## The commits, and why each exists

```
0d88729  Report Packet 2 against what was actually run and clicked
2a24c0f  Finish the money path: fee plans, concessions and closing the books
6f51578  Act on the office's changes: fees column, editing, events, catalogue
f6da429  Order classes 1 to 10, and teach each stage its own subjects
e8d2aef  Add the chase list, and stop the query cache outliving the session
08ad0b7  Let the office actually take a payment
61a01f6  Type the request bodies, and give writes a gate, a reason and a voice
563e7d8  Pin the generated schema to LF so the drift check can run off Linux
```

The middle two (`f6da429`, `6f51578`) are the office's own change requests,
which arrived mid-packet: class ordering, per-stage subjects, a fees column and
editing on Students, Upcoming Events on the Dashboard, and an editable grading
system and fee structure on Settings. They are described in
`reports/packet-2-fees.md` under "The office's change requests".
