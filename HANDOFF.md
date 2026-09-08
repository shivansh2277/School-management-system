# Sunrise ERP — Session Handoff

**Written:** 6 September 2026 · **revised 8 September 2026** (Parts 2, 3, and
Part 4's examinations, report cards, HR and payroll)
**Branch:** `part-1-foundation` — **nothing pushed, ever.** Count the commits
with `git log --oneline main..HEAD | wc -l`; a number written here goes stale on
the next commit, including the one that updates this file.
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
| 4 | Examinations, HR/payroll, transport, communication, reports | **examinations, report cards, HR and payroll done — both halves of Checkpoint 4 pass; transport, communication and reports not started** |

---

## 2. Verified current state

Measured on 7 September 2026 by running the commands below, not recalled.

| Measure | Value |
|---|---|
| Backend tests | **452 passing**, ~104 s |
| Database tables | **76, plus `alembic_version`** |
| Alembic migrations | **27** (verified from empty **on Postgres**, then seed, then worker) |
| API surface | **185 paths, 229 operations** |
| Permissions / system roles | **68** / 13 |
| Job handlers | `fees.overdue_sweep`, `fees.generate_invoices`, `admission.offer_sweep`, `system.heartbeat` |
| Demo school | 100 students, 10 sections, 12 teachers, 98 guardians |
| Demo fee ledger | 300 invoices, 810 lines, 170 payments, 410 allocations, 2 sibling concessions |
| Demo attendance | 5,800 rows over 58 working days, plus 2 holidays inside the window |
| Demo timetable | 6 periods, 300 slots, **0 teacher clashes, 0 room clashes**, and **every teacher on exactly 25 periods — spread 0** |
| Demo examinations | 1 CBSE scheme, 8 components over 2 terms, 4 Term 1 exams, 240 papers, **2,400 marks, none over its paper's maximum** |
| Demo grading | 1 active scale (CBSE v1), 8 bands |
| Demo HR | 5 departments (4 with a head), 12 staff placed, 4 leave types (CL 12 / SL 10 / EL 15 / LWP 0) |
| Demo payroll | 11 components, 12 salary structures (PGT ₹42,000 / TGT ₹32,000 / PRT ₹19,500). An August run: 12 payslips, 25 working days, ₹4,11,500 earnings, ₹3,86,663.75 net, ₹4,36,190 employer cost |

> The previous revision recorded **60** tables. The real count on 7 September,
> before any Part 4 work, was **61** plus `alembic_version`. Corrected here
> rather than carried forward.

**How the suite is wired**, because the two URLs are easy to confuse:

- The **suite runs on Postgres**, not SQLite. `TEST_DATABASE_URL` defaults to
  `postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test`, and
  `conftest.py` drops and recreates the `public` schema once per session, then
  seeds once. Do not assume SQLite from `DATABASE_URL`.
- **`tests/test_migrations.py` is the exception**: it shells out with
  `DATABASE_URL` pointed at SQLite, which is why a migration using `now()`,
  `true`, `ALTER COLUMN` or `ADD CONSTRAINT` fails there and passes everywhere
  else. Use `op.batch_alter_table` and SQLAlchemy Core, not raw SQL.
- Each test runs inside a transaction that is rolled back, so writes do not
  leak between tests — **except** where a service commits internally
  (`fees.generate()` does; see §9.6).
- The fixtures worth knowing: `client` and `db` (sharing one session),
  `admin` / `cashier` / `teacher` / `other_teacher` / `student` / `parent` as
  auth headers, `admin_user` as a `User` row for calling services directly, and
  `ids` for the handful of primary keys most tests need — including
  `ids["school"]` and `ids["year"]`.

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q                    # 452 passed
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe seed.py
../.venv/Scripts/python.exe worker.py --once                # runs due jobs
```

Seeding costs ~12 s at `BCRYPT_ROUNDS=4`, measured on Postgres.

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

### Part 4, 7–8 September — examinations, report cards, HR, payroll

| Commit | What |
|---|---|
| `51f0eb2` | Tenant key actually filtered, not merely carried |
| `24a76b5` | Grading scales versioned, so a published grade can be frozen |
| `2d90a21` | Assessment schemes: a subject can carry more than one mark a term |
| `1be8acd` | Marks lock, absent/exempted/zero, and the audited post-lock change |
| `1f1165b` | CBSE report cards, frozen at publication, withheld for dues |
| `c02d2ca` | Departments and the employee profile HR and payroll hang off |
| `1882f23` | Staff leave, and the cover approving it must raise |
| `99c0b31` | The staff register, and loss of pay answered in one place |
| `bf38896` | Three owner decisions, and an evenly loaded timetable |
| `dfeb08b` | Payroll, from components a school edits rather than rates in code |

**Both halves of Checkpoint 4 are tests, not claims.**
`tests/test_payroll.py::test_a_payroll_run_completes_for_the_demo_school` opens
August, calculates twelve payslips, approves and marks it paid; and:
`tests/test_report_cards.py::test_a_published_card_does_not_re_grade_when_a_band_is_edited`
publishes a card, then revises the grading scale so 91 is no longer an A1, and
finds the issued document unchanged while the live preview has moved.
`test_a_published_card_does_not_move_when_a_mark_is_corrected` does the same
with a mark. **What Checkpoint 4 still lacks is `CONFIGURATION-GUIDE.md`.**

**The two product answers this part depended on.** Both given by the owner on
7 September 2026, before any code was written against them:

- **§8 item D — the report card layout:** *standard CBSE, kept
  template-configurable.* Two terms; per subject Periodic Test 10, Notebook 5,
  Subject Enrichment 5, Term Examination 80, totalling 100; grade from a
  versioned scale; attendance line. Built as `assessment_schemes` +
  `scheme_components`, so 10/5/5/80 is seed data a school edits, not a number
  in code.
- **§8 items A and B — payroll:** *blueprint §3.16 defaults, professional tax
  shipped disabled because Uttar Pradesh does not levy it.* Built and tested.

Three more answered later the same day, once the code reached them:

- **§8 item K — unused leave does not carry forward.** Already what the code
  did, now stated and pinned by a test, because carry-forward is the kind of
  thing a later session adds as a helpful omission.
- **§8 item L — a half day costs no pay.** `lop_days()` charged 0.5; it now
  charges nothing, and the mark is still recorded and still shows in the counts.
- **The teacher load chart.** Asked for, and the check found both that the
  existing chart hid teachers with no periods and that the allocation was
  genuinely uneven — six at the 30-period ceiling, four on 18. Now every
  teacher carries exactly 25, and the chart reports the spread.

**The §5.3.9 rule HR exists to enforce**, and the reason HR came before
payroll: approving a teacher's leave now walks their timetable and raises a
`pending` substitution for every period they were due to teach. §5.3.9 calls
approving leave that silently leaves classes unattended the single most common
real-world HR/timetable failure. **And the gap Part 3 recorded as impossible is
closed**: `timetable.arrange()` can now ask whether a substitute is themselves
on leave — which is not a clash the timetable can see, because they have no
lesson that period precisely for that reason.

Design decisions in Part 4 that a later session should not undo:

- **A grading scale is a version, not a setting.** Bands hang off
  `grading_scales`; reusing a name creates the next version rather than a second
  scale. Publication freezes the scale it cited, so revising it *must* become a
  new version and the issued card still reads against the old one. This is the
  whole mechanism §0.8 asks for, and removing the version column removes it.
- **The lowest grade band must start at 0.** Otherwise a child on 40% earns no
  grade and the card prints a blank.
- **An exam cites a scheme component; the component is not on the paper.** An
  exam already carries a term, so a periodic test is simply an exam that *is* a
  component — which is why marks and `exam_schedule` needed no change at all.
  Putting the link on `exam_schedule` instead would have been three times the
  diff for the same capability.
- **`scheme_component_id` is nullable, deliberately.** An exam without one is an
  ordinary class test: marked, readable, and not printed. Requiring it would
  mean amending the scheme before holding a surprise test.
- **Components cannot be restated once an exam is marked against them.** The
  marks are out of the old number; changing it turns an 8/10 into an 8/5 without
  touching the mark.
- **A paper is locked, not a mark.** §5.4.7 closes entry per subject, so the
  lock is on `exam_schedule` and a paper cannot be half shut.
- **There is no `mark_change_log` table.** `audit_log` is append-only, refuses a
  `status_change` without a reason, is indexed on (entity_type, entity_id), and
  its own docstring already names "changing a published mark" as its case. A
  second log is a second thing to keep honest. §5.4.5 lists the table; this
  deliberately does not build it.
- **The exam controller has a route of their own.** `/teacher/marks` reaches
  only the papers a teacher owns, which made an override impossible for the very
  person §5.4.8 puts in charge of it. It is gated on `exam.marks.manage_any`,
  **not** on `exam.marks.enter` — a teacher holds that one unscoped, and reusing
  it would have let any teacher mark any section.
- **`marks.entered_by` points at `users`, not `employees`.** The actor is a user
  everywhere else here, the audit log included, and an exam controller may hold
  no teaching post.
- **Preview and issued card are separate endpoints returning different things.**
  A preview recomputes; an issued card is read straight back. One route with a
  flag is how a frozen document quietly starts moving again.
- **Withholding asks the fee ledger.** `fees.ledger()["outstanding"]` — the
  number the counter clerk collects against — rather than examinations keeping
  its own idea of who has paid. It is a setting
  (`exams.withhold_results_for_dues`), because §5.4.9 says the policy is
  configurable.
- **Releasing a withholding moves the status and not the marks.** They were
  frozen at publication and stay frozen.
- **There is no `designations` table.** A designation has no attributes and no
  relationships — salary structures attach to the employee, not the grade
  (§3.16) — so it is a string until the day it carries a pay band.
- **An employee cannot be exited while they hold an active timetable
  allocation** (§5.3.9). The row and its `employee_code` survive forever, which
  is what keeps an old payslip or an old mark resolvable; the login does not.
- **Salary information is gated by absence, not by discipline.** No profile
  shape carries PAN, PF, ESI or bank; `/employees/{id}/statutory` is the only
  route that serves them. A test asserts the keys are missing from both the
  list and the detail shape.
- **Leave types are rows, not an enum.** The student `LeaveType` enum is
  student-shaped and carries no entitlement.
- **Leave days come from the school calendar**, stored at application time
  rather than recomputed — a holiday declared later must not silently restate
  an approved request.
- **Approving leave writes the staff register**, and leaves an already-marked
  day alone; cancelling removes only the rows the approval wrote, identified by
  their null `marked_by`. Same bargain student leave already makes.
- **`staff_attendance.lop_days()` is the only place loss of pay is answered.**
  Two sources — a day marked `absent`, and approved leave against an unpaid
  type — counted once when a day is both, and never for a Sunday or a holiday.
  §3.16 multiplies salary by this number, and two definitions would put two
  figures on two screens.
- **`AttendanceStatus` is shared between the student and staff registers.** The
  six states are the same six; a second enum would be two lists to keep in
  step.
- **Payroll holds no rate.** The code knows the methods — percent of basic,
  percent of gross, balancing figure, loss of pay — and the numbers are rows.
  `DEFAULT_COMPONENTS` is what the setup screen is pre-filled with, nothing
  more.
- **Earnings always come to exactly the gross**, via the balancing figure.
  If that drifts, somebody is paid the wrong amount on a payslip that still
  looks arithmetically tidy — which is why every payslip in a run is checked.
- **`payslip_lines` is a table, not a frozen JSON payload.** Unlike a report
  card, payroll is asked questions *across* documents; the PF register and
  cost-by-department of §5.3.10 are queries over lines.
- **Payroll does NOT reuse `fee_periods` as its month lock.** This reverses a
  suggestion in an earlier revision of this document: §5.3.6 keeps the ledgers
  separate, and closing June for fees is not the same decision as closing June
  for payroll. The run's own status is the lock, and `run_no` lets a month have
  a supplementary run.
- **An approved run is immutable** and a correction is a supplementary run
  standing on its own. The first run's payslips are untouched by the second.
- **Whoever prepares the payroll does not sign it off.** Accountant holds
  `payroll.run.manage`, Principal `.approve`.
- **The teacher load is even by construction.** Teachers are assigned *by
  subject*, two per subject splitting the ten sections, and the placement loop
  fills whichever subject a section is furthest behind on. Three teachers per
  section taking two subjects each cannot balance — thirty assignments over
  twelve people is 2.5 each.

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

**Carrying `school_id` is not the same as filtering on it.** Four read paths
never did, and two of them genuinely leaked: `/admin/exams` and
`/admin/subjects` returned every school's rows, and `grade_for()` graded a child
against every customer's bands at once. Fixed by making `section_labels`,
`subject_names` and `grade_for` *require* a `school_id` argument, so a caller
cannot forget it. **When you add a query, check the tenant filter is on it** —
`tests/test_tenant_isolation.py` plants a rival school and is the place to add
the next such check.

**A teacher's permissions are unscoped; the restriction is in the service.**
`exam.marks.enter` is held school-wide by a teacher, and "own subjects only"
comes from `assert_teaches_subject_in_section`. So a route that passes
`school_wide=True` to skip service scoping **must be gated on a permission a
teacher does not hold**, or it is a privilege escalation. This nearly shipped;
`exam.marks.manage_any` exists for exactly that reason.

**`audit.snapshot()` used to be unable to serialise a Decimal.** It stringified
anything with `isoformat` or `value`, which covered dates and enums, and let a
Decimal through into a JSON column — raising at commit rather than at the edit.
It now allow-lists what JSON accepts. **Payroll would have hit this on its first
audited amount.**

**Batch `alter_column` is unavoidable on SQLite and it rebuilds the table.**
That rebuild is what once dropped a `server_default`. Both Part 4 migrations
that use it were checked on Postgres afterwards rather than assumed, and the
`grade_bands` backfill was exercised against real data by downgrading and
re-upgrading a seeded database. **Do the same for the next one.**

**An unnamed foreign key has a different name on each engine.** Postgres
auto-names it `<table>_<column>_fkey`; SQLite reflects it with no name at all,
so batch mode needs a `naming_convention` before it can be addressed. The
`marks.entered_by` migration branches on the dialect for this reason — a
migration that only spells the SQLite name passes the test suite and fails on
the engine that matters.

**`READ_ONLY` in `core/permissions.py` collects every permission ending in
`.read`.** Naming a sensitive one `hr.salary.read` would therefore have handed a
records clerk every colleague's bank account, as a side effect of a role that
can read everything else. `NOT_BLANKET_READ` now excludes it and the auditor is
granted it deliberately. **Check that list before naming any new `.read`
permission over sensitive data.**

**Anything ending in `.read` over sensitive data needs `NOT_BLANKET_READ`.**
This has now bitten twice — `hr.salary.read` and `payroll.run.read` — and each
time the effect was the same: the Admin Officer, a records clerk, would have
read every colleague's bank account and salary as a side effect of a role that
reads everything else. Add the permission to that set and grant it explicitly to
whoever genuinely needs it. **Note the Principal must then be granted it back**,
because an approver has to see what they are approving.

**A service that stands the old row down before inserting the new one leaves a
gap on the failure path.** `set_structure()` deactivated the current salary
structure and *then* hit the unique constraint, so the employee was momentarily
on no terms at all and an ordinary mistake surfaced as a 500. Check first, write
second.

**`employees` and `departments` point at each other**, which has bitten twice.
SQLAlchemy cannot infer `Employee.department` without explicit `foreign_keys`,
and `sorted_tables` cannot order a cycle — it silently drops those foreign keys
from the sort and warns that it may raise instead in a later release, which made
`seed.py::wipe()` correct only by luck. Wipe now issues one `TRUNCATE ...
CASCADE` on Postgres, which needs no order at all.

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
- **`FeeHeadType.optional` is declared and unread.** `fees.generate()` bills
  every monthly item on a plan to every enrolment on it, with no filter on head
  type, so an `optional` head placed on a plan would charge every child — the
  outcome the enum's own docstring warns about. The seeded `TRANSPORT` head sits
  on no plan and has never been billed, so nothing is wrong today, but there is
  **no opt-in mechanism at all** and transport cannot bill until one exists.
  Verified 8 September 2026; see §9.1 for the shape it should take.
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

### Part 4 — what is not built

Of the five Part 4 modules, **examinations and report cards are done and the
other four are not started**: HR, payroll, transport, communication, reports.
Within examinations, what §5.4 asks for and this does not do:

- **No datesheet conflict checking.** §5.4.9 wants the builder to reject two
  papers for one section at the same time and warn on a teacher invigilating two
  rooms. `services/timetable.py::conflicts()` is the thing to reach for and it
  has not been wired in. Papers are also not checked against `holidays`.
- **No rooms, seating or hall tickets.** `exam_schedule.room` exists as a column
  and nothing sets it. `exam_rooms` and `seat_allocations` are not built.
- **No moderation step.** Marks go `entered → locked`; §5.4.7's `verified`
  state between them has no screen and no column. The lock and the audited
  override cover the integrity requirement; a second pair of eyes does not.
- **No re-tests.** §5.4 lists `retests` for absentees. An absence is now
  recorded distinctly, which is the data a re-test needs, but nothing consumes
  it.
- **No co-scholastic areas.** The CBSE card prints them; `co_scholastic_areas`
  and `co_scholastic_marks` are not built. The scheme model would carry them
  as components of a different kind, which is the cheap way in.
- **No class-teacher or principal remark on the card**, and no PDF. The card is
  JSON; nothing renders it.
- **No result status beyond pass/withheld.** `fail` and `compartment` are
  named in §5.4.7 and nothing computes them — there is no pass mark anywhere in
  the scheme yet. See §8 item H.
- **No section-wide publication.** Cards publish one child at a time; an exam
  controller publishing 10-A does it forty times.
- **No examinations UI**, like every part before it.
- **Nothing withholds the Transfer Certificate.** §0.6b withholds the TC as well
  as the report card; only the card is done.

### Part 4 HR — what is not built

Departments, the staff profile, leave and the staff register are done.
Recruitment is not, and it is the larger half of §5.3:

- **No recruitment at all.** `job_postings`, `candidates`, `interview_rounds`,
  `interview_scores`, `job_offers` — none of it. `EmployeeStatus` deliberately
  omits `applicant`, `offered` and `onboarding` for that reason; adding them now
  would be three statuses nothing can set.
- **No appraisals and no exit clearance checklist.** The exit refuses on an
  active timetable allocation, which is §5.3.9's rule; a clearance list is not
  built.
- **No document expiry alerts** for a teaching licence or police verification.
  The polymorphic `documents` table already accepts an `employee` owner, so this
  is a job handler and a query rather than a schema change.
- **No biometric import** for the staff register. Marking is by hand.
- **No employee self-service.** §5.3.8 gives an employee their own profile,
  leave and payslips; every HR route is admin-side.
- **No department scoping enforced yet.** `ScopeType.department` exists and
  departments now have heads, but no route restricts a Department Head to their
  own department.
- **No HR UI**, like every part before it.

### Part 4 payroll — what is not built

A run completes, is immutable once approved, and produces registers. What §3.16
and §5.3 ask for that this does not do:

- **No slab-based TDS.** It needs an annual projection this system does not
  hold, and inventing one puts a wrong number on a payslip. TDS ships as a
  `fixed` component, inactive, entered per employee by whoever computed it.
  See §8 item M.
- **No `formula` calculation method.** An expression evaluator behind a screen a
  records clerk uses is an injection surface. The four methods plus the
  balancing figure cover §3.16's default set exactly.
- **No arrears or mid-month joiners.** A structure effective mid-month is paid
  as though it applied all month; nothing prorates.
- **No payslip PDF and no bank transfer file.** The payslip is JSON, and
  `bank_account_no` is captured and unused.
- **No annual statutory returns** — the registers are per run, so PF and ESI
  come out a month at a time rather than as a quarterly or annual filing.
- **Nothing tells an employee they have been paid.** Payslips are admin-side
  only; §5.3.8's employee self-service does not exist, and communication is not
  built.
- **No payroll UI.**

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
- **Nothing is pushed.** Every commit on this branch exists only on this
  laptop. The owner wants the exact file list shown before any push.
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
  Part 4 widened the gap again: `/admin/exams` now returns `scheme_component_id`
  and `marks_locked`, a report card row carries `is_absent`, `is_exempted` and
  per-component columns, and marks may now be null. Nothing in `web/` knows any
  of that.
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
| ~~A~~ | ~~A real Lucknow school's payroll structure~~ | **Answered 7 Sep 2026: use the blueprint §3.16 default component set. Recorded, not yet built.** |
| ~~B~~ | ~~Confirm Uttar Pradesh levies no professional tax~~ | **Answered 7 Sep 2026: UP does not levy it. Ship the component, disabled by default.** |
| ~~C~~ | ~~Does the late-fee clock stop when the next invoice generates?~~ | **Answered 7 Sep 2026: it keeps accruing until the invoice is paid.** Built and tested. |
| ~~D~~ | ~~The exact CBSE report card layout~~ | **Answered 7 Sep 2026: standard CBSE (PT 10 / NB 5 / SE 5 / Term 80 over two terms), kept template-configurable. Built and tested.** |

New questions this part surfaced, none blocking:

| # | Question | Needed by |
|---|---|---|
| E | Is a six-day week right for this school, and are Saturdays half days? The attendance denominator assumes Mon-Sat working with Sunday off. | Before a real school's first month |
| F | Who may reopen a closed fee period? Currently anyone holding `fees.payment.void`, which is Principal and Accountant. | Before go-live |
| G | Should an unpaid invoice ever be written off? `written_off` exists in the status enum and nothing sets it — §0.6 says no refunds and no carry-forward, which leaves old dues visible forever. | Part 4, with §0.6b |

Raised by the Part 4 work, none blocking:

| # | Question | Needed by |
|---|---|---|
| H | **What makes a result a `fail` or a `compartment`?** §5.4.7 names both statuses and nothing computes them, because there is no pass mark anywhere in the scheme. Is it a percentage of the term total, a per-subject minimum, or both? A `pass_marks` column on `scheme_components` is the obvious home. | Before a term is published for real |
| I | **Does an absent paper lower the percentage, or leave it out?** It is currently left out of both halves, which is the v0 rule §5.4.9 says to keep for a subject with no mark — but it means an absent child reads *higher* than one who sat the paper and scored zero. Defensible either way; currently a consequence of an inherited rule rather than a decision. | Before a term is published for real |
| J | **Who may reopen a locked paper?** Currently anyone holding `exam.marks.lock`, which is the Principal and the Exam Controller. Same shape as item F for fee periods. | Before go-live |
| ~~K~~ | ~~Do staff leave balances carry forward?~~ | **Answered 7 Sep 2026: no. Unused leave lapses.** Already the behaviour; now stated and pinned by a test. *Whether earned leave should accrue monthly rather than open at the full quota is still open — see N.* |
| ~~L~~ | ~~Is a half-day absence half a day's pay?~~ | **Answered 7 Sep 2026: no deduction at all — a half day is paid as a full day.** Built and tested. |

Raised by payroll, none blocking:

| # | Question | Needed by |
|---|---|---|
| M | **How should TDS be computed?** It ships as a `fixed` per-employee amount, inactive, because slab-based TDS needs an annual projection the system does not hold. Is entering a monthly figure what the school's accountant actually does, or should the system project? | Before the first April payroll |
| N | **Does earned leave accrue monthly?** A balance currently opens at the full year's quota on day one, so somebody could take fifteen earned days in April. | Before a real school's first year |
| O | **Should a mid-month joiner or leaver be prorated?** Nothing does; a structure effective the 20th pays the full month. | Before the first real hire mid-month |

---

## 9. Where to start next session — transport, communication, reports

**Examinations, report cards, HR and payroll are done, and both halves of
Checkpoint 4 pass as tests.** What remains of Part 4 is **transport,
communication and reports**.

**`CONFIGURATION-GUIDE.md` and `EXTENSION-GUIDE.md` are deliberately held back**
until the owner has looked over the three modules below and given the go-ahead.
They describe what the other modules built, so writing them before those modules
settle means writing them twice. Checkpoint 4 does not close until the
configuration guide exists — it is the only thing standing between here and the
end of Part 4 — but it is the last thing to write, not the next.

**Nothing is blocked on the owner.** Every §8 item that gated work has been
answered; the open ones (M, N, O and the earlier E–J) are refinements.

---

### 9.1 Transport (§5.6) — do this first

The biggest of the three, the only one with genuine safety rules, and the one
the other two will want to notify and report on.

**Correcting something an earlier revision of this document got wrong.** It said
the fee side was "nearly free" because `fee_heads` already has an `optional`
type. **That is not true, and following it would charge every child in the
school for the bus.** Verified on 8 September 2026:

- The seed has a `TRANSPORT` head of type `optional`. It sits on **no plan** and
  has **never been billed** — it is a label nothing reads.
- `fees.generate()` bills `[i for i in plan.items if i.frequency is monthly]`
  with **no filter on head type**. Put the transport head on a plan and every
  child on that plan is billed for it. The enum's own docstring warns about
  precisely this outcome, and nothing implements the protection.

So **transport billing needs a real opt-in, and it is the one piece of new
money-path code this module needs.** Two shapes, and the second is right:

- A per-student plan override through `student_fee_plans`, which already exists.
  Rejected: it needs one plan per stop slab, so a school with twelve stops keeps
  twelve near-identical plans and the fee catalogue becomes unreadable.
- **`generate()` learns that an `optional` head bills only where an opt-in
  exists** — for transport, an active `transport_assignments` row for that
  enrolment covering that month, priced from that stop's slab. One targeted
  change in one place, and it finally makes `FeeHeadType.optional` mean
  something.

Treat that as a change to the money path: `assert_period_open()`, the
idempotency index on (enrolment, period) and the existing fee tests all sit
around it, and `seed.py` runs the real biller, so a mistake there breaks seeding
rather than only a test.

**The two hard blocks — refusals, not warnings.** §5.6.9 is explicit, and both
are child-safety rules with the second also a legal one:

- **A route may not exceed its vehicle's seating capacity.**
- **A vehicle with expired insurance, fitness, permit or PUC cannot be assigned
  to an active route**, and a driver with an expired licence or missing police
  verification cannot be assigned at all.

Neither should be expressible as an override with a reason, unlike the timetable
workload ceiling. Keeping that distinction deliberate is the point.

**What to reuse rather than build:**

- **Drivers and attendants are `employees`**, already carrying department,
  status and the exit rule. Do not create a `drivers` table holding a name and a
  phone number; put the licence and verification on the employee record or hang
  them off `documents`.
- **Vehicle papers are `documents`.** `OwnerType.vehicle` already exists in the
  enum, unused, waiting for exactly this. Expiry alerts are then a scheduled job
  handler over one query — `services/jobs.py` has `@handler`, `enqueue()` and a
  schedule table — not a new alerting mechanism.
- **Stop timings must increase monotonically along a route**, and two routes
  cannot use one vehicle at overlapping times. The second is the same shape as
  `timetable.conflicts()`; read that before writing a fresh clash checker.
- **Ending an assignment stops future billing and preserves history** (§5.6.9),
  which sits correctly with §0.6's no-refunds rule: a mid-year departure stops
  the next invoice and refunds nothing already paid.
- **`applications.transport_required` is captured at admission and goes
  nowhere.** It should seed the assignment request rather than being asked
  again from scratch.

Leave out of this module: GPS tracking, the route map view, attendance-on-bus,
and the fuel and maintenance logs. None is needed for a school to run a bus
service safely, and each is a table nothing would read yet.

---

### 9.2 Communication (§5.9)

Smaller, and mostly a matter of doing one thing properly: an outbox with a
delivery record.

**The rule that shapes it: dispatch happens in the worker.** §5.9.9 is direct —
a gateway timeout must never fail the action that triggered the message.
`services/jobs.py` is the queue and already survives a restart, so sending is
`enqueue()` plus a handler, never an inline HTTP call from a route.

**Email only for v1** (§0.11), behind a provider interface so SMS and WhatsApp
can be wired later and stay disabled per school until DLT registration exists.
The owner's address is the reply-to.

**Every module before this has notifications it wants and cannot send.** They
were deliberately not stubbed, so expect to go back and wire each one:

| Where | What it wants to send |
|---|---|
| Admission (§5.1.6) | acknowledgement, document reminder, hall ticket, offer letter, expiry warning |
| Fees | the defaulter chase, and a receipt |
| Examinations | report card published |
| Staff leave | a colleague has been assigned to cover a lesson |
| Payroll | a payslip is available |
| Transport | route change, delay |

**Design points worth settling before writing:**

- **The recipient model must accept a bare phone number or email**, because an
  applicant is not a user (CLAUDE.md's rule) and most applicants never become
  one.
- **Templates are versioned**, so the exact text sent stays reproducible — the
  same shape as grading scales and report cards, and `services/grading.py`
  already shows the versioning-plus-freeze pattern.
- **Opt-out is respected for informational messages and overridden for
  statutory or emergency ones.** A parent cannot opt out of "your child is
  absent" or "the school is closed".
- **No family's data may appear in another family's message.** A careless bulk
  merge is the realistic way that happens.
- `notices` already exists, with an audience enum and no delivery record.
  Extend it rather than adding a parallel concept beside it.

---

### 9.3 Reports (§5.10)

Last, because it describes what everything else built.

**The rule with teeth: a report obeys the same permission and scope as the
screen.** §5.10.9 calls a report becoming a way to see rows you cannot see
directly the most common data-leak path in an ERP. The seam already exists here
— `require_permission()` at the route, `services/scoping.py` over the rows — so
a report must go through both and never assemble its own query outside them.
`tests/test_tenant_isolation.py` is the shape of the test that proves it.

**Numbers must reconcile.** One definition, not two queries that drift. This has
already bitten once this part: `stats.exam_percentages()` and `report_card()`
had to be held to the same arithmetic when absent marks arrived, and a test now
pins them together. The same applies to fee collection, the attendance
percentage and payroll totals.

**Exports containing personal data are audited** — who, what, when, how many
rows. `students.profile.export` is already separate from `.read` for this
reason, and `audit_log` takes an `export` action it has never been given.

**No fabricated data points**: a month with no invoices shows no bar rather than
a zero bar. `fees.collection` already does this deliberately; §5.10.9 makes it a
system-wide rule.

Most of what management asks for already exists as service functions —
`services/stats.py`, `fees.day_book()`, `attendance.section_summary()`,
`timetable.workload()`, `payroll.register()` and `payroll.cost_by_department()`.
Reports is mostly a matter of giving those a governed, permission-checked home
and a report library, not of writing new arithmetic.

---

### 9.4 What Parts 3 and 4 built that these three should reuse

| Reach for | Rather than |
|---|---|
| `services/jobs.py` (`@handler`, `enqueue`, schedules) | any inline send, or a new alerting mechanism |
| `documents` and the unused `OwnerType.vehicle` | a new table for vehicle papers |
| `employees` | a `drivers` table |
| `services/timetable.py::conflicts()` | a fresh clash checker for vehicle timings |
| `holidays` and `attendance.working_days()` | a second calendar, anywhere |
| `services/grading.py` versioning + freeze | a second frozen-document mechanism for message templates |
| `audit.next_number()` | any `max(seq) + 1` for a document number |
| `fees.primary_contact()` | a third way to find who to ring |
| `core/settings_registry.py` | new columns for policy switches (§3.15) |
| `services/school_settings.py::module_enabled` | a UI-only feature switch |
| `NOT_BLANKET_READ` | naming a sensitive permission `.read` and hoping |
| `tests/test_tenant_isolation.py` | writing a new cross-tenant check from scratch |

### 9.5 Checkpoint 4

- ~~A CBSE report card publishes and stays frozen~~ — **done and tested**
  (`tests/test_report_cards.py`).
- ~~A payroll run completes for the demo school~~ — **done and tested**
  (`tests/test_payroll.py::test_a_payroll_run_completes_for_the_demo_school`).
- A non-technical reader can change a fee rule using only
  `CONFIGURATION-GUIDE.md` — **held until the owner clears the three modules
  above.**

### 9.6 Before starting

1. `git log --oneline main..HEAD` — read them; the messages carry the
   reasoning deliberately.
2. Run the suite (§2) and the by-hand Postgres check (§4). Believe neither
   number until you have seen it. SQLite hid three Postgres defects already.
3. Decide with the owner whether to push first. Nothing has ever been pushed and
   CI has never run, so the first push is also the first CI run — expect it to
   find something, and it grows with every part that lands.
4. The web dashboard is further behind than ever: known broken against the fee
   API (§7), and examinations, HR and payroll have all landed since anyone last
   opened it.

**One warning from writing this section.** `fees.generate()` commits internally.
Poking at it from a throwaway script does **not** roll back — doing so left a
stray fee head, a plan item and a hundred December invoices in `sunrise_test`
before that was noticed. Reset the schema after experimenting rather than
trusting a `rollback()`.

The memory file `sunrise-erp-build.md` carries the same state in short form for
a session that starts cold.
