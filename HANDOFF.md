# Sunrise ERP — Session Handoff

**Written:** 6 September 2026 · **revised 7 September 2026** (Parts 2 and 3)
**Branch:** `part-1-foundation` — **35 commits ahead of `main`, nothing pushed**
**Repo:** `C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\`
**Remote:** https://github.com/shivansh2277/School-management-system

Every number below was measured on 7 September 2026, not recalled. Anything
unverified says so.

> This supersedes `Sunrise-HANDOFF.md` (in the parent AGENTS folder) for
> everything about the ERP work. That document still describes the v0 demo
> accurately, **except the demo logins, which have changed** — see §5.

---

## 1. What this project now is

A **multi-tenant School ERP sold to separate, independent schools** — not
branches of one school. That distinction was confirmed explicitly and shapes
the whole data model: a tenant is a customer.

The design document is `docs/ERP_BLUEPRINT.md`. **§0 holds the 21 locked
product decisions and wins over anything else in that document.** Read §0 first;
the rest was written before those answers.

Delivery is **four checkpointed parts** (§12). Four checkpoints is not four
sessions — Parts 3 and 4 will each span several.

| Part | Scope | State |
|---|---|---|
| 1 | Foundation: tenancy, enrolments, RBAC, audit, jobs, documents | **backend complete** |
| 2 | Admission, including the public online portal | **backend complete; Checkpoint 2 passes in tests** |
| 3 | Fees rebuild + attendance + timetable | **backend complete; Checkpoint 3 passes in tests** |
| 4 | Examinations, HR/payroll, transport, communication, reports | not started |

---

## 2. Verified current state

Measured on 7 September 2026 by running the commands below, not recalled.

| Measure | Value |
|---|---|
| Backend tests | **292 passing**, ~78 s |
| Database tables | 60, plus `alembic_version` |
| Alembic migrations | 19 (verified from empty **on Postgres**, then seed, then worker) |
| API surface | 139 paths, 174 operations |
| Permissions / system roles | 51 / 13 |
| Job handlers | `fees.overdue_sweep`, `fees.generate_invoices`, `admission.offer_sweep`, `system.heartbeat` |
| Demo school | 100 students, 10 sections, 12 teachers, 98 guardians |
| Demo fee ledger | 300 invoices, 810 lines, 170 payments, 410 allocations, 2 sibling concessions |
| Demo attendance | 5,800 rows over 58 working days, plus 2 holidays inside the window |
| Demo timetable | 6 periods, 300 slots, **0 teacher clashes, 0 room clashes**, heaviest load 30/week |

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q                    # 292 passed
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe seed.py
../.venv/Scripts/python.exe worker.py --once                # runs due jobs
```

---

## 3. The commits, and why each exists

### Part 1, 6 September

1. **`2df73e8` Tenancy + academic years** — `schools` is the tenant root and
   replaces `school_settings` (which was reached via a hardcoded `id=1`).
   `academic_years` replaces the `String(9)` that was denormalised onto two
   tables with nothing keeping them in agreement. A partial unique index allows
   at most one current year per school.
2. **`965f1e6` Enrolments** — the largest change. `class_section_id` and
   `roll_no` moved off `students` onto `enrolments`. A student's class is a fact
   about a *year*; promotion used to overwrite it and silently re-parent all
   history.
3. **`c37687d` Promotion** — year-end rollover that only creates rows. Preview
   is separate from commit and writes nothing.
4. **`f490044` RBAC** — 33 permissions, 10 system roles, scoped grants,
   replacing four hardcoded roles.
5. **`e6a2186` Audit + sequences** — append-only log with mandatory reasons on
   destructive actions; gapless document numbering under a row lock.
6. **`2ca4dd7` Demo school + Assignments retired** — 10 classes × 10 students;
   web Assignments removed per §0.17 (kept in the mobile app).
7. **`843250a` Worker + CI** — Postgres-backed job queue, worker process,
   GitHub Actions, Dockerfile, compose stack, `DEPLOY.md`.
8. **`02c5f56` Documents** — polymorphic documents + object storage. This is
   what Part 2 was blocked on.

Five more later the same day:

9. **`71be808` Test-schema reset** — the suite would not start: `sunrise_test`
    still held the v0 schema and `drop_all` orders drops from the model
    metadata, so a leftover `students.class_section_id` FK blocked it. Postgres
    now drops and recreates the schema.
10. **`0a4a846` Notice scope leak** — the parent branch of `notices.visible_to`
    selected enrolment sections without joining `Student`, a cartesian product
    that showed every parent every class's notices. SQLAlchemy had warned about
    it on every run.
11. **`45dcb69` Admin student CRUD** — the enrolment split had broken both
    halves and nothing tested them: create raised `NameError` (missing imports),
    and moving a child to another section wrote `class_section_id` onto
    `Student`, where the column no longer exists, and returned 200.
12. **`cdf89e4` Settings, module flags, custom fields** — §3.15 levels 1-3 plus
    the module-registry seam. Endpoints under `/admin/configuration`;
    `/admin/settings` was already the school profile.
13. **`2c7107e` Employees and guardians** — `teachers` -> `employees`
    (`employee_id` -> `employee_code`, plus `employee_type`), `parents` ->
    `guardians` with the §0.7 cross-link, `parent_student` ->
    `student_guardian` with a closed `relation` list and one primary contact
    per child under a partial unique index. `class_teacher_id`,
    `class_subject_teacher.teacher_id` and the /teacher and /parent URL
    prefixes deliberately kept.

---

### Part 2, 7 September

| Commit | What |
|---|---|
| `cb41e5d` | Cycles, seat configuration, enquiry register with a follow-up log |
| `487228b` | Applications: drafts, submission, the soft-warning rules |
| `b1fea5d` | The public portal — the only unauthenticated surface |
| `ce475c5` | Document checklist and the gate before a decision |
| `7e07107` | Assessments and interviews, panel scores kept independent |
| `bdd958d` | Merit list, decisions, offers, waitlist, expiry job |
| `e03576d` | Atomic conversion — **Checkpoint 2** |
| `4af03bd` | Dashboard, funnel, seat utilisation, rejection analysis |

**Checkpoint 2 is a test, not a claim:**
`tests/test_admission_conversion.py::test_checkpoint_2_portal_to_enrolled_student`
applies on the public portal, verifies documents, admits, offers, collects the
fee, converts — then logs in as the new student, checks the enrolment, the
guardian link, the migrated documents and an invoice from the next billing run.
No manual database work anywhere in it.

Design decisions in Part 2 that a later session should not undo:

- **Address, previous school and declarations are JSON columns on
  `applications`.** A form step writes and reads each whole and nothing queries
  inside them; a column each would be forty columns and three tables for
  nothing. Medical is the exception — its own table, its own permission (§15).
- **Applicant documents reuse the polymorphic `documents` table**, and are
  re-pointed at the student at conversion rather than copied.
- **`admission_decisions.reason` and `admission_offers.expires_on` are NOT
  NULL.** Both are §5.1.9 rules expressed as constraints rather than
  intentions.
- **The public portal returns identical 404s** for an unknown school, a
  suspended one, and one with the module off — and for a wrong application
  number versus a wrong date of birth. Weakening that turns it into an
  enumeration oracle.
- **Assessment and interview are their own tables, not `exams`/`marks`.** Those
  hang off an enrolment, which an applicant does not have.

---

### Part 3, 7 September

| Commit | What |
|---|---|
| `5159205` | Fee catalogue: heads, plans, per-student assignment, concessions |
| `972d096` | The ledger rebuild — invoices with lines, allocation-based payments |
| `caa8861` | The late fee, and the §8C answer that the clock runs until payment |
| `da674ad` | Period close, the day book — **Checkpoint 3** |
| `efbbd1a` | Attendance re-keyed to the enrolment; corrections, holidays, leave |
| `e58ce1e` | Timetable made editable with conflict detection, plus substitutions |

**Checkpoint 3 is a test, not a claim:**
`tests/test_fee_period.py::test_checkpoint_3_bill_part_pay_fine_chase_collect_close`
bills a month, part-pays ₹1,000, lets the fine reach ₹1,000 at twelve days
overdue, finds the family on the defaulter list with that fine, collects the
balance, sees the invoice settle, reads the day book, closes the month, and
watches the next payment come back 409. No manual database work anywhere in it.
`tests/test_attendance_rules.py` covers the second half of the checkpoint — a
week marked and corrected with an audit trail.

**The one product answer this part depended on.** §8 item C, answered by the
owner on 7 September 2026: **the late-fee clock runs until the invoice is
paid**, and generating the next month's invoice does not stop it. The
consequence is that the fine is a pure function of the due date, the invoice
amount and one other date — today while unpaid, `settled_on` once cleared — so
it can be recomputed in front of a parent at the counter. Reversing that answer
now fails `test_the_clock_keeps_running_after_the_next_invoice_is_generated`
rather than quietly changing every parent's bill.

Design decisions in Part 3 that a later session should not undo:

- **Payments allocate to invoice lines, never to invoices.** This is what makes
  part payment, advance payment, over-payment and head-wise reporting one
  mechanism instead of four. An invoice balance is a SUM over
  `payment_allocations`, never a stored column.
- **A reversal is a contra payment with negative allocations.** Both rows and
  both receipt numbers survive, and every balance still comes out of a plain
  SUM. A gap in the receipt sequence is what an auditor asks about.
- **The late fee is an ordinary line against an ordinary head** (`LATE`,
  created on demand per school). It is therefore allocated against, receipted,
  reported head-wise and part-payable with no special case anywhere.
- **It only ever moves upward.** Lowering `fees.late_fee.initial` does not
  refund a fine already charged — that is a waiver, which is a concession,
  which needs an approver.
- **A closed period refuses billing into the month, money dated inside it, and
  voiding one of its invoices — but not collecting an old due today.** A
  receipt belongs to the day it was issued, so that money lands in the current
  period, which is §5.5.9's "late entry into the current open period". Refusing
  it would make closing June mean a June defaulter can never pay.
- **`overdue` outranks `partially_paid`** when an invoice is both. The
  defaulter list is what the office acts on; the balance carries the other half
  of the truth, and a test pins each.
- **The attendance percentage denominator is working days since the child
  joined**, not days someone happened to mark. §5.8.9 calls getting this wrong
  the most common attendance-reporting bug, and v0 had it wrong.
- **Correcting an earlier day needs a reason and is audited; fixing today's
  roll does not.** A teacher fixing a tap while the register is open is not
  amending a record.
- **Approving leave writes the register**, and leaves an already-marked day
  alone. Otherwise "approved leave" and what the register says disagree, and
  only whoever remembers reconciles them.
- **The seed builds the timetable through the same validator the API enforces.**
  v0 seeded it blindly and shipped 144 teacher double-bookings, which would
  make every conflict report look like noise.
- **Substitutions are a row per date, not an edit to the slot**, and an
  unfilled one is recorded rather than dropped — §5.7.10 calls that the
  operational number that matters most.

---

## 4. Things that would be expensive to rediscover

**The migration test runs on SQLite, and SQLite hides Postgres bugs.** It does
not enforce foreign keys and it accepts `1` for a boolean; both cost time on
6 September. The Postgres path is exercised only by CI (which has still never
run) or by hand:

```bash
cd backend
export DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test
../.venv/Scripts/python.exe -c "
from sqlalchemy import create_engine, text
import os
with create_engine(os.environ['DATABASE_URL']).begin() as c:
    c.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public'))"
../.venv/Scripts/python.exe -m alembic upgrade head     # 14 revisions
BCRYPT_ROUNDS=4 ../.venv/Scripts/python.exe seed.py
../.venv/Scripts/python.exe worker.py --once            # should run 1 job
```

Run this before believing any migration works. It caught three defects on
6 September that the whole test suite could not see.

**The test suite does not exercise the migrations.** `tests/conftest.py` builds
its schema with `Base.metadata.create_all`, straight from the models. A batch
`alter_column` in the tenancy migration dropped `updated_at`'s `server_default`,
leaving a NOT NULL column nothing could insert into — and no test could see it.
`tests/test_migrations.py` now migrates, seeds and runs a worker for real, and
CI does the same. **Do not delete that test to make the suite faster.**

**`BCRYPT_ROUNDS` is configurable and tests use 4.** Seeding 210 accounts at the
production work factor was ~70 s of every run. This changes the work factor, not
the behaviour. Never lower it outside tests.

**Reads must not write.** v0's `fees.refresh_overdue()` committed from inside a
GET. That is gone: `presented_status()` computes how an invoice reads *now*, and
the scheduled `fees.overdue_sweep` job moves the stored value.

**Scope is not the same as permission.** A guardian and an office clerk both
hold `students.profile.read`. The guardian holds it at `self` scope; admin
routes pass `school_wide=True`. Getting this wrong once already exposed the
whole student roster to a parent in development.

**The seed now runs the real biller and the real conflict checker.** It calls
`fees.generate()` and `fees.collect()` rather than inserting invoice rows, and
builds the timetable through the same rules the API enforces. That is
deliberate — a seed that fabricates its data cannot catch a defect in the code
that will produce it in production — but it has a consequence: **a bug in the
fee or timetable service breaks `seed.py`, not just a test.** If seeding starts
failing, look there first.

**Seeded invoices carry late fees.** `collect()` assesses the fine before
allocating, so paying an overdue seeded invoice charges one. A test that picks
an arbitrary seeded invoice and expects a clean amount will be wrong; clear the
ledger and generate a fresh month first, the way
`tests/test_late_fee.py::a_clean_invoice` does.

**SQLite returns naive datetimes** even for `timestamptz` columns, and comparing
one against an aware `now` raises rather than returning False. `services/jobs.py`
normalises with `_utc()`.

---

## 5. Demo logins — **these changed**

Admission numbers now come from a sequence in the format decided in §0.21:
`YYYY` + a six-digit counter. The old `SPS2024001` no longer exists.

| Role | Login | Password |
|---|---|---|
| Admin | `admin@sunrisepublic.edu` | `Admin@123` |
| Fee counter clerk | `counter@sunrisepublic.edu` | `Admin@123` |
| Teacher | `TCH001` | `Teacher@123` |
| Student | `2024000001` | `Student@123` |
| Parent | `9876500001` | `Parent@123` |

`TCH001` still class-teaches 10-A and teaches it Mathematics — the walkthrough
depends on it, and the seed pins that deliberately. `2024000001` is roll 1 of
10-A. The demo parent still has exactly two children so the child switcher has
something to switch between.

The counter clerk is new in Part 3 and holds the `fee_collector` role: it may
take money and may not void or approve a concession. It exists so §5.5.9's
segregation of duties is demonstrable rather than asserted.

Tests no longer hard-code these: `conftest._login_id_in()` resolves a student by
where they sit, so seed ordering can change without breaking the suite.

---

## 6. Open work

### Part 2 — what is not built

- **No admission UI at all.** The whole module is API-only; §5.1.3 lists
  eighteen screens and the web dashboard has none of them.
- **No communication.** §5.1.6 wants every stage transition to trigger a
  notification — acknowledgement, document reminder, hall ticket, offer letter,
  expiry warning. Email is a Part 4 deliverable, so the triggers have nowhere
  to go yet and are not stubbed.
- **No hall tickets or offer letters as documents.** The data is all there;
  nothing renders a PDF.
- **Transport interest is captured and goes nowhere** — `transport_required` is
  stored, and Part 4 builds the assignment request it should seed.
- **Reapplication linking exists as a column** (`previous_application_id`) but
  no endpoint sets it.

### Part 3 — what is not built

- **No fee, attendance or timetable UI beyond what v0 had.** The whole of Part
  3 is API-only. The web dashboard's Fees page still calls
  `/admin/fees/structures`, which no longer exists, and reads an `amount` field
  invoices no longer carry (§7).
- **No reminder or receipt communication.** §5.5.9 wants the defaulter chase to
  send something; email is Part 4, so the defaulter list is a screen the office
  works from by hand.
- **No bank or gateway reconciliation.** §5.5.9 asks for it as a first-class
  screen. There is no gateway (§0.10) and no bank feed, so the day book is
  where cash reconciliation stops for now.
- **No refunds.** §0.6 says none, so nothing is built. `is_refundable` on a fee
  head is recorded and unused.
- **No instalment plans.** §5.5.3 lists them; §0.6 locks monthly billing, so
  they were not built.
- **Nothing sets `written_off`.** The status exists; see §8 item G.
- **No timetable versioning.** §5.7.9 wants a published version superseded
  rather than replaced, so historical attendance resolves against the version
  in force on that date. §0.4 locks attendance to **daily**, not period-wise,
  so nothing historical resolves against a slot and the requirement has no
  teeth today. **If period-wise attendance is ever adopted, this becomes
  expensive** — that is the moment to add versioning, not later.
- **No subject-period allocation table.** `/completeness` reports gaps against
  "every teaching period on every day", not against "six Maths periods a week".
  §5.7.9 wants the latter; it needs an allocation table that does not exist.
- **No staff attendance and no teacher-availability table.** Substitution
  therefore checks "already teaching" and "already covering", but cannot check
  "on leave" — staff leave is HR, in Part 4.
- **No month lock for attendance.** §5.8.9 mentions locking; corrections are
  audited instead, which is what Checkpoint 3 asks for.

### Part 1 — infrastructure still owed

**The backend list from §12 is now done.** What Part 1 still owes is
infrastructure and proof rather than code: a real `docker compose up` on the
Oracle box, a backup whose restore has actually been performed, and CI that has
run at least once. Checkpoint 1 does not pass until the restore happens — see
§7.

The web dashboard and the mobile app are also not caught up; the API shapes they
read have moved (§7).

---

## 7. Known limits and things not verified

- **Docker is not installed on this machine.** `docker-compose.yml` and
  `backend/Dockerfile` are syntax-checked only. They need a real
  `docker compose up` on the Oracle box before anyone trusts them.
- **Nothing is pushed.** All 35 commits exist only on this laptop. The owner
  wants the exact file list shown before any push.
- **CI has never run.** The workflow is written but no push has triggered it.
- **The web dashboard has not been opened** against the new backend, and after
  Part 3 it is now **known broken**, not merely suspect. `npx tsc --noEmit` was
  clean on 7 September 2026 — but the web app declares its own `Invoice` type
  by hand rather than generating it from the API, so TypeScript cannot see the
  problem. Specifically:
  - `src/pages/Fees.tsx` calls `/admin/fees/structures`, **which no longer
    exists** (410 Gone in practice: the route was removed with
    `fee_structures`), and renders `invoice.amount`, `status` and `receipt_no`
    — invoices now carry `payable`, `balance`, `paid` and `lines`.
  - `src/pages/Attendance.tsx` and `Dashboard.tsx` read the roll and summary
    shapes, which gained `corrected` and changed how the percentage is
    computed; they will render, but the percentage a page shows and the one the
    API now computes are different numbers.
  A green typecheck here means nothing. Treat the dashboard as Part 4 work.
- **The mobile app has not been touched or tested** since the enrolment change,
  and Part 3 moved more ground under it: `/parent/fees/{id}/pay` is gone
  (payment is now against a student, with an amount and an idempotency key) and
  the receipt URL is `/parent/fees/receipts/{payment_id}.pdf`. Its attendance
  calls should still work — the API deliberately still speaks in `student_id`
  even though the table is keyed by enrolment.
- **`/admin/configuration` has no UI at all.** Settings, module switches and
  custom fields are API-only; §0.18 says the configuration screens must be
  usable by a records clerk, and that screen does not exist yet.
- **Zero frontend tests** still. Unchanged from v0 and still a real gap.
- **The old Vercel/Neon deployment is now stale** — the schema there predates
  all nineteen migrations. Hosting moves to Oracle Cloud (`DEPLOY.md`).

---

## 8. Still open for product discussion

From ERP_BLUEPRINT §16:

| # | Question | Needed by |
|---|---|---|
| A | A real Lucknow school's payroll structure to validate the component model | Part 4 |
| B | Confirm Uttar Pradesh levies no professional tax (assumed, shipped disabled) | Part 4 |
| ~~C~~ | ~~Does the late-fee clock stop when the next invoice generates?~~ | **Answered 7 Sep 2026: it keeps accruing until the invoice is paid.** Built and tested. |
| D | The exact CBSE report card layout the target school expects | Part 4 |

New questions this part surfaced, none blocking:

| # | Question | Needed by |
|---|---|---|
| E | Is a six-day week right for this school, and are Saturdays half days? The attendance denominator assumes Mon-Sat working with Sunday off. | Before a real school's first month |
| F | Who may reopen a closed fee period? Currently anyone holding `fees.payment.void`, which is Principal and Accountant. | Before go-live |
| G | Should an unpaid invoice ever be written off? `written_off` exists in the status enum and nothing sets it — §0.6 says no refunds and no carry-forward, which leaves old dues visible forever. | Part 4, with §0.6b |

---

## 9. Where to start next session — Part 4

Part 4 is **examinations, HR/payroll, transport, communication, reports**
(§12), and it is the largest part. Read `docs/ERP_BLUEPRINT.md` **§0** first
(§0.5, §0.8, §0.9, §0.11, §0.15 and §0.6b all bind here), then **§5.4**
(examinations), **§5.3** (HR), **§3.16** (payroll configurability), **§5.6**
(transport), **§5.9** (communication) and **§5.10** (reports).

**Two product questions block payroll** — §8 items A and B. Ask before writing
a single salary component: a component model validated against a real Lucknow
school's structure is the whole point of §3.16, and building one against a
guess means rebuilding it. Item D blocks the report card layout the same way.

### What Part 3 built that Part 4 should reuse rather than reinvent

| Reach for | Rather than |
|---|---|
| `audit.next_number()` | any `max(seq) + 1` for a payslip or certificate number |
| `services/fees.py` allocation model | a second, simpler ledger for payroll — **payroll stays separate**, but the void/reverse discipline should be copied |
| `fee_periods` and `assert_period_open()` | a new "is this month closed" mechanism for payroll |
| `holidays` | a second calendar table for exams or transport |
| `services/timetable.py::conflicts()` | a fresh clash checker for the exam datesheet — §5.7.9 says exams must not clash with the calendar |
| `core/settings_registry.py` | new columns for grading scales or payroll rates (§3.15) |
| `services/school_settings.py::module_enabled` | a UI-only feature switch |
| `fees.primary_contact()` | a third way to find who to ring |

### Two Part 4 items that touch Part 3 directly

- **Result withholding for unpaid dues (§0.6b, §12).** The ledger already
  answers "what does this enrolment owe" — `fees.ledger(db, enrolment_id)`
  returns `outstanding`. Examinations should ask that question rather than
  keeping its own idea of who has paid.
- **Transport fee head (§5.6).** `fee_heads` already has an `optional` type for
  exactly this: transport bills only the children who opted in, through a plan
  item, with no new billing path.

### Checkpoint 4 passes when

A CBSE report card publishes and stays frozen; a payroll run completes for the
demo school; and a non-technical reader can change a fee rule using only
`CONFIGURATION-GUIDE.md`, which does not exist yet.

### Before starting

1. `git log --oneline main..HEAD` — 35 commits, and the messages carry the
   reasoning deliberately.
2. Run the suite (§2) and the by-hand Postgres check (§4). Believe neither
   number until you have seen it. SQLite hid three Postgres defects already.
3. Decide with the owner whether to push first. Nothing has ever been pushed and
   CI has never run, so the first push is also the first CI run — expect it to
   find something.
4. Consider whether the web dashboard should be caught up before Part 4 rather
   than after. It is now known broken against the fee API (§7), and every part
   that ships API-only widens the gap.

The memory file `sunrise-erp-build.md` carries the same state in short form for
a session that starts cold.
