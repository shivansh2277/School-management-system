# Sunrise ERP — Session Handoff

**Written:** 6 September 2026 · **revised 8 September 2026** (Parts 2, 3, and
Part 4's examinations, report cards, HR, payroll, **transport** and
**communication**)
**Branch:** `part-1-foundation` — **nothing pushed, ever.** Count the commits
with `git log --oneline main..HEAD | wc -l`; a number written here goes stale on
the next commit, including the one that updates this file.
**Repo:** `C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\`
**Remote:** https://github.com/shivansh2277/School-management-system

Every number below was measured on 8 September 2026, not recalled. Anything
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

Measured on 8 September 2026 by running the commands below, not recalled.

| Measure | Value |
|---|---|
| Backend tests | **522 passing**, ~108 s |
| Database tables | **85, plus `alembic_version`** |
| Alembic migrations | **29** (verified from empty **on Postgres**, then seed, then worker) |
| API surface | **210 paths, 259 operations** |
| Permissions / system roles | **77** / 14 |
| Job handlers | `fees.overdue_sweep`, `fees.generate_invoices`, `admission.offer_sweep`, `transport.document_expiry`, `comms.dispatch`, `system.heartbeat` |
| Demo school | 100 students, 10 sections, 12 teachers, 98 guardians — **84 of them with an email address**, and 14 deliberately without |
| Demo fee ledger | 300 invoices, **900 lines** (810 + 90 transport), 170 payments, 410 allocations, 2 sibling concessions |
| Demo attendance | 5,800 rows over 58 working days, plus 2 holidays inside the window |
| Demo timetable | 6 periods, 300 slots, **0 teacher clashes, 0 room clashes**, and **every teacher on exactly 25 periods — spread 0** |
| Demo examinations | 1 CBSE scheme, 8 components over 2 terms, 4 Term 1 exams, 240 papers, **2,400 marks, none over its paper's maximum** |
| Demo grading | 1 active scale (CBSE v1), 8 bands |
| Demo HR | **6 departments** (4 with a head), **16 employees**, 4 leave types (CL 12 / SL 10 / EL 15 / LWP 0) |
| Demo payroll | 11 components, **16 salary structures** (PGT ₹42,000 / TGT ₹32,000 / PRT ₹19,500 / Transport Manager ₹28,000 / Driver ₹16,000 / Attendant ₹11,000). An August run: **16 payslips**, 25 working days, **₹4,82,500 earnings, ₹4,53,081.25 net, ₹5,11,450 employer cost** |
| Demo communication | 4 message templates, and an outbox the nightly jobs fill: one overdue sweep chases **100 families (86 sent, 14 unreachable)** and the expiry sweep notifies 1 |
| Demo transport | 2 vehicles (40 + 32 seats), 2 active routes, 7 stops, 3 fee slabs, **30 children riding** (18 on R1, 12 on R2), both routes roadworthy, 13 compliance documents, 1 paper lapsing inside the 60-day horizon |

> The previous revision recorded **60** tables. The real count on 7 September,
> before any Part 4 work, was **61** plus `alembic_version`. Corrected here
> rather than carried forward.

> **The 900 fee lines are the transport opt-in measured rather than asserted.**
> The ledger held 810 before transport landed; thirty riders over three months
> is ninety more. Had the transport head billed everyone the way it did before
> `generate()` learned what `FeeHeadType.optional` means, it would have been
> three hundred more. That difference is the whole of §9.1's warning, in one
> number.

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
../.venv/Scripts/python.exe -m pytest -q                    # 522 passed
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

### Part 4, 8 September — transport

| Commit | What |
|---|---|
| `Model the bus service on the tables Parts 3 and 4 already built` | Five tables where §5.6.5 lists eleven. No `drivers` (an employee), no `vehicle_documents` (a `document`, using the `OwnerType.vehicle` that had sat unused since Part 1), no trip/fuel/maintenance/incident logs. Four permissions and the Transport Manager role §5.6.8 names. |
| `Refuse to run a bus unsafely, rather than warning about it` | The service, the API and 29 tests. The capacity block and the compliance block, both hard. |
| `Keep uploaded documents out of the repository` | `STORAGE_LOCAL_PATH` was never ignored, so a test run swept 302 stray PDFs into the tree. |
| `Make FeeHeadType.optional mean something, instead of being a label` | The money path. `generate()` learns that an optional head bills only where an opt-in exists. |
| `Run two real bus routes in the demo, through the real service` | The seed, built by calling the service rather than inserting rows. |
| `Register the expiry sweep where the worker will actually find it` | The handler was in the service, where nothing imports it; a scheduled job would have failed nightly. |
| `Give the admission form's transport tick box somewhere to go` | `applications.transport_required` finally reaches a queue. |

**What the transport module decided, and why:**

- **Two rules are refusals with no override, and that is deliberate.** A route
  may not exceed its vehicle's seating capacity; a bus without valid
  insurance, fitness, permit and PUC may not run, nor may anybody crew it
  without a current licence and a police verification. The timetable's
  comparable ceiling *is* overridable (`timetable.slot.override`) because the
  cost of being wrong there is a tired teacher. Here it is a child on an
  uninsured bus. There is no permission that skips these and no `reason=`
  parameter, and **two tests assert that by inspecting the signatures** — if a
  `force` or `reason` argument ever appears, the suite fails.
- **Missing papers refuse, not only expired ones**, and **a blank expiry
  refuses too**. Somebody uploads the permit and leaves the date empty; a
  check that only compares dates would read that as valid forever.
- **The compliance check sits on `set_crew` as well as on activation.**
  Guarding only activation would leave the back door open — swapping a
  compliant driver for a lapsed one on a running route is exactly as unsafe.
- **The capacity block guards both directions.** `assign` refuses the fifth
  child onto a four-seat bus; `set_crew` refuses to put a two-seater under
  four children already on board.
- **`requested` and `suspended` count against capacity.** A seat somebody is
  coming back to is taken. Counting only `active` would fill a bus twice over
  on paper and turn children away at the door.
- **A route with no vehicle refuses rather than waving children through.** A
  capacity check that cannot run must not read as unlimited.
- **`routes` has no `direction` column** although §5.6.4 asks for one: a stop
  carries both a pickup and a drop time, so one route covers morning and
  afternoon rather than two mirror-image routes that drift apart.
- **`uq_transport_assignment_live` is a billing guarantee before it is a data
  rule.** One live assignment per enrolment means the month's transport charge
  is one slab, so nothing downstream arbitrates between two buses. That is
  stricter than §5.6.9 — see §8 item P.
- **Transport is priced from the stop's slab, never from the plan item.** That
  is what lets one head serve a dozen stops instead of needing a plan per slab.
- **The expiry sweep reports rather than acts.** Grounding a bus at 03:00
  because a certificate lapsed overnight would strand a hundred children at
  their stops with no warning. The refusal already sits on every path that
  assigns; what was missing was the office knowing in time to renew.

### Part 4, 8 September — communication

| Commit | What |
|---|---|
| `Model an outbox with a delivery record, and nothing else yet` | Four tables where §5.9.5 lists nine. `notices` gains one nullable `message_id`. |
| `Move the defaulter list into the service, so the chase and the screen agree` | It lived in the route; the chase became the second caller. |
| `Send email from the worker, with an opt-out that knows what it may refuse` | The service, the provider seam, the API, 30 tests, and the first two senders wired. |
| `Let the notice board put a notice in people's inboxes` | Publishing can now also send. |

**What communication decided, and why:**

- **Dispatch happens in the worker, and a test proves it.** §5.9.9: a gateway
  timeout must never fail the action that triggered the message. A test
  installs a provider that raises on any send and drives the whole
  compose-and-send path through it.
- **`MANDATORY_CATEGORIES` is the opt-out line, in one place.** A parent may
  opt out of a circular and may not opt out of "your child is absent" or "the
  school is closed". The preference is **stored either way** rather than
  refused at the checkbox — it is what they asked for, and the override
  belongs where the school's obligation is.
- **No family's data reaches another family, by construction.** The render is
  handed one recipient's `context` and has nothing else to reach for. The fee
  chase is the worst case and a test renders every recipient to prove it.
- **`string.Template`, not `str.format`.** A template body is typed into a text
  box by office staff; `format_map` would let `{x.__class__.__mro__}` walk out
  of the values it was handed.
- **`smtplib`, not a provider SDK.** Brevo and Resend both speak SMTP.
  Switching provider is four environment variables, not a dependency.
- **An automated send skips the bulk-approval gate.** The gate stops a person
  mailing the whole school by accident; a nightly chase on a template the
  school wrote and a schedule it enabled was approved once, deliberately.
- **An unreachable family gets a delivery row saying so**, rather than being
  silently absent from the list.

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

**`jobs.run_one` rolls the transaction back when a handler raises**, so
anything a handler does *after* its real work is undone by a later failure.
Wiring the fee chase onto the end of `fees.overdue_sweep` meant an exception
from a mail server would silently reverse the overdue marking and the late fees
the sweep had just computed — a communication failure undoing money work, which
is the coupling §5.9.9 exists to prevent one layer in from the gateway timeout
it names. Both wired handlers now catch and report in their result.
`tests/test_comms.py::test_a_broken_chase_does_not_undo_the_late_fees` fails
without the guard.

**A job handler must be defined in `app/jobs.py`, not beside the service it
calls.** Importing that one module is what registers every handler, and it is
what the worker and the tests import. `transport.document_expiry` was first
written inside `services/transport.py`, which reads well and does not work: a
worker process never imports that service, so the job would have failed nightly
with "No handler registered" until somebody read a log. Nothing caught it
because the schedule had not been added yet either.
`tests/test_jobs.py::test_every_default_schedule_has_a_handler` now pins it.

**`ScheduledJob.at_hour` is compared against the UTC hour, not the school's.**
The comments beside the two original schedules claimed IST, so
`fees.overdue_sweep` actually fires at 07:30 in Lucknow and
`admission.offer_sweep` at 11:30 — mid-morning, not "before the office opens"
as its comment said. It is also why
`test_the_scheduler_queues_a_due_job_once_per_slot` failed for exactly one hour
a day and passed for the other twenty-three, on a machine whose clock nobody
would think to blame. The comment is fixed; **the hours are deliberately
unchanged**, because moving a school's nightly sweep is a decision, not a
tidy-up. See §8 item R.

**`STORAGE_LOCAL_PATH` defaults to `./var/documents` and was not ignored by
git.** The first commit that ran the transport tests swept 302 stray PDFs into
the tree. Test artefacts here; in a real checkout they would be children's
birth certificates. `.gitignore` now covers `backend/var/`.

**Fixtures that invent demo-shaped data collide with a seed that has grown.**
The transport tests originally used registration `UP32AB1234`, route codes
`R1`/`R2` and a `0-5 km` slab — every one of which the seed then created for
real, and each collision is a unique-constraint error in a fixture rather than
a legible failure. They now live in their own namespace (`UP32TT…`, `T1`…), and
`riders` deliberately selects children the seed has *not* already put on a bus.

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
| Transport Manager | `TRM001` | `Admin@123` |

`TCH001` still class-teaches 10-A and teaches it Mathematics — the walkthrough
depends on it, and the seed pins that deliberately. `2024000001` is roll 1 of
10-A. The demo parent still has exactly two children so the child switcher has
something to switch between.

`TRM001` is new in Part 4 and holds the `transport_manager` role — the only
account that can work the transport module without being the admin. **The two
drivers (`DRV001`, `DRV002`) and the attendant (`ATT001`) deliberately cannot
log in**: their `users` rows exist only because `employees.user_id` is not
nullable, they are marked inactive, and `_assign_roles` skips them. Without
that skip the legacy role map would hand a demo password `super_admin`, because
a staff `users.role` has to be `admin` to be staff at all.

**Guardian email addresses are new**, and they matter for Communication:
§0.11 made email the only v1 channel and the demo previously had none at all.
84 of 98 guardians now have `parentNNN@example.com`, and **every seventh
deliberately has none**, so §5.9.10's unreachable list is a real number on a
fresh install rather than an empty screen that looks like it works.

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

### Part 4 transport — what is not built

Deliberately, and each would be a table nothing reads yet:

- **GPS tracking and the route map view.** `vehicles.gps_device_id` is
  recorded because §5.6.4 asks for it and a school that later buys tracking
  needs somewhere to put the id. Nothing reads it.
- **Attendance-on-bus**, the daily trip log, the fuel and maintenance logs and
  the incident register. None is needed for a school to run a bus service
  safely.
- **Cost per route** (§5.6.10) — it needs the fuel and maintenance figures
  above. Route utilisation, which does not, is built (`transport.seats`).
- **A stop cannot be suggested from a child's address.** §5.6.6 wants distance
  to drive stop suggestion; nothing geocodes, so the office chooses from the
  work queue.
- **A driver has no login.** §5.6.8 says "if given app access later", and the
  seeded drivers' user rows exist only because `employees.user_id` is not
  nullable. They are marked inactive and `_assign_roles` skips them — without
  that, the legacy role map would have handed a demo password `super_admin`.
- **Nothing notifies.** Route changes, delays and the expiry alerts all want
  Communication, which is the next module. The expiry sweep already produces
  the payload; it has nowhere to send it.

### Part 4 communication — what is not built

Deliberately, and each for a stated reason:

- **`parent_queries`.** Two-way messaging is its own feature with its own
  inbox; it is not what "an outbox with a delivery record" means.
- **`device_tokens` and push.** §0.11 is email only for v1.
- **`communication_credits`.** Nothing to meter on a free email tier, and a
  ledger that always reads zero teaches a school to ignore the screen.
- **`delivery_receipts`, and with them `delivered` / `read` / `bounced`.** All
  three need a provider webhook to observe. Three statuses nothing can ever set
  would be a delivery report that lies by omission, so `DeliveryStatus` stops
  at `queued / sent / failed / opted_out`. `provider_ref` is stored so a bounce
  reported later can be matched back to the row that caused it — the webhook
  has a landing place when somebody builds it.
- **SMS and WhatsApp.** Wired behind the same provider interface and refused at
  the send until `comms.channel.sms` / `.whatsapp` is switched on, which needs
  DLT registration. §8 item T is whether email-only survives contact with a
  real school's contact list.
- **Scheduled/recurring messages.** `messages.scheduled_for` exists and quiet
  hours use it, but there is no "send this every Monday" — that would be
  `services/jobs.py` plus a schedule row, not a new mechanism.
- **Per-person quiet hours and preferred language.** §5.9.4 lists both;
  quiet hours are per-school, and §0.19 says localisation is not required.
- **Custody restrictions (§5.9.9).** "Messages to a specific child's guardian
  must respect custody restrictions where recorded" — nothing records them.
  The guardian model has no custody field, so this rule has nothing to read
  and is not enforced. Worth naming before somebody assumes it is.
- **Four of the six senders.** Admission, fee receipts, results published,
  leave cover and payslips still have nothing that sends them. See §9.

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
- **`students.profile.export` is granted and enforced by nothing.** Grep
  `app/api/` for it: no hits. The permission exists precisely to separate "may
  see this on screen" from "may download two thousand of them" — §10.2 makes a
  point of it — and today it gates no route. Verified 8 September 2026.
- **`AuditAction.export` has never been written.** Referenced zero times in
  `app/`. §5.10.9 requires exports of personal data to be audited; the enum
  member has been waiting since Part 1. Both of these are Reports' first job
  (§9.1), and both are the same shape as the `FeeHeadType.optional` defect —
  a control that exists in the vocabulary and is enforced nowhere.
- **`core/modules.py` still marks `admission` and `hr` as `built=False`.** Both
  are built. It is the honest-bookkeeping field, so it is currently lying.
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

Raised by transport, none blocking:

| # | Question | Needed by |
|---|---|---|
| P | **May a child use one route for pickup and a different one for drop?** §5.6.9 allows one active assignment *per direction*; the build is stricter and allows one per child, full stop. The stricter rule is what makes the month's transport charge one slab rather than a sum of two that something would have to arbitrate between. Loosening it means deciding how a split rider is billed. | Before a school with two campuses' worth of geography signs |
| Q | **Should the sibling concession come off the bus fare?** §0.6's 10% is stored with a null `fee_head_id`, meaning every head, so it now does — transport is the first optional head anything bills. Defensible either way, and it fell out of an existing rule meeting a new line rather than anybody choosing it. A school wanting the other answer can already scope a concession to a head. Pinned by `test_a_sibling_concession_comes_off_the_bus_fare_too`. | Before a real school's first transport invoice |
| R | **What hour should the nightly sweeps actually run at?** `at_hour` is UTC, so `fees.overdue_sweep` fires at 07:30 in Lucknow and `admission.offer_sweep` at 11:30 — not the 02:00 and 06:00 their comments claimed. The new `transport.document_expiry` is set at 01:00 UTC / 06:30 local. The existing two are left alone on purpose: moving a school's nightly sweep is a decision, not a tidy-up. | Before go-live |

Raised by communication, none blocking:

| # | Question | Needed by |
|---|---|---|
| S | **Should fee reminders be unrefusable?** `MANDATORY_CATEGORIES` holds `emergency` and `attendance` — the two §5.9.9 names. A school that wants its dues reminders to override an opt-out is making a policy choice somebody should make out loud; it is one line. | Before go-live |
| T | **Is email-only viable for this school?** §0.11 chose it, and the demo showed the assumption underneath: a Lucknow school collects mobile numbers, not addresses. 84 of 98 seeded guardians have an email only because the seed now gives them one. If a real school's parents are 40% reachable, SMS stops being a v2 nicety. `/admin/comms/unreachable` is the number to look at first. | Before the first real circular |

Raised by payroll, none blocking:

| # | Question | Needed by |
|---|---|---|
| M | **How should TDS be computed?** It ships as a `fixed` per-employee amount, inactive, because slab-based TDS needs an annual projection the system does not hold. Is entering a monthly figure what the school's accountant actually does, or should the system project? | Before the first April payroll |
| N | **Does earned leave accrue monthly?** A balance currently opens at the full year's quota on day one, so somebody could take fifteen earned days in April. | Before a real school's first year |
| O | **Should a mid-month joiner or leaver be prorated?** Nothing does; a structure effective the 20th pays the full month. | Before the first real hire mid-month |

---

## 9. Where to start next session — reports, then the two guides

**Transport and communication are both done.** What remains of Part 4 is
**reports**, and then `CONFIGURATION-GUIDE.md` and `EXTENSION-GUIDE.md`.

Communication shipped as an outbox with a delivery record, an email provider
behind a seam, versioned templates, opt-out with a stated override, quiet
hours, bulk approval, and an emergency broadcast on its own permission and its
own endpoint. **Two of the six senders in the wiring table are connected** —
the fee defaulter chase and the transport compliance alert — plus the notice
board. The other four are the first thing to pick up if you want more of
communication before reports:

| Where | Still to wire |
|---|---|
| Admission (§5.1.6) | acknowledgement, document reminder, hall ticket, offer letter, expiry warning |
| Fees | the receipt (the chase is done) |
| Examinations | report card published |
| Staff leave | a colleague has been assigned to cover a lesson |
| Payroll | a payslip is available |

Each is the same three lines the fee chase is — a template in
`core/message_templates.py`, a `comms.notify()` call, and the guard that stops
a mail failure rolling back the work it was attached to (§4). **Read that trap
before wiring the next one**: it is the one thing here that can silently
corrupt something that matters.

---

### 9.1 Reports (§5.10) — the last module

Last on purpose, because it describes what everything else built. Most of the
arithmetic already exists; what does not exist is a governed home for it.

**Before anything else, two things this brief checked rather than assumed.**
Both are the same shape as the `FeeHeadType.optional` defect transport found —
a control that exists in the vocabulary and is enforced nowhere:

- **`AuditAction.export` is referenced zero times in `app/`.** The enum member
  has been there since Part 1. §5.10.9 requires that exports of personal data
  be audited — who, what, when, how many rows — and nothing has ever written
  one.
- **`students.profile.export` is granted to the Admin Officer and required by
  no route.** Grep `app/api/` for it and there are no hits. The permission that
  exists specifically to separate "may see this on screen" from "may download
  two thousand of them" currently gates nothing, so the separation §10.2 is
  proud of is decorative. Reports is the module that either makes it real or
  should delete it.

Fixing those two is the smallest useful first commit, and it is worth doing
before any report exists to leak through.

---

**The rule with teeth: a report obeys the same permission and scope as the
screen.** §5.10.9 calls a report becoming a way to see rows you cannot see
directly *the most common data-leak path in an ERP*. The seam already exists —
`require_permission()` at the route, `services/scoping.py` over the rows — so a
report must go through both and never assemble its own query outside them.

The realistic failure is not malice, it is convenience: a report service that
takes `school_id` and builds its own `select()` is faster to write than one
that goes through the scoping helpers, and it silently serves a class teacher
the whole school. **CLAUDE.md §4 already records this happening once** — four
read paths carried `school_id` without filtering on it, and two genuinely
leaked. `tests/test_tenant_isolation.py` plants a rival school and is where the
next such check belongs. Add a guardian and a class teacher to it for the
report routes, not only a second tenant.

**Numbers must reconcile.** One definition, not two queries that drift. This
has now bitten or been deliberately avoided three times, which is why it is the
rule stated most often in this file:

- `stats.exam_percentages()` and `report_card()` had to be held to the same
  arithmetic when absent marks arrived, and a test pins them together;
- `/admin/transport/charges` calls the same `charges_for_month()` the fee run
  uses rather than recomputing it;
- `fees.defaulters()` was moved out of its route this session precisely so the
  chase and the screen could not disagree.

**A report that needs a number must call the function that owns it.** If the
function does not exist yet, write it in the owning service and let the report
call it — never the reverse.

**Every report states its academic year, filter set and generation timestamp on
the output** (§5.10.9). A printed report with no context is a report that will
be misquoted in a board meeting, and this system has already had one document
class that needed freezing for exactly that reason (§0.8, report cards).

**No fabricated data points**: a month with no invoices shows no bar rather
than a zero bar. `fees.collection()` already does this deliberately; §5.10.9
makes it system-wide. `comms.preview()` had to be fixed for this in the same
session it was written — it returned a hardcoded `"unreachable": 0` — so the
temptation is real and recent.

---

**What already exists, and is the actual content of the report library.**
Verified by reading the services on 8 September, not recalled:

| Service | Functions a report would call |
|---|---|
| `services/stats.py` | `totals`, `exam_percentages`, `performance`, `top_performers`, `fee_trend`, `month_attendance`, `today_schedule` |
| `services/fees.py` | `daybook`, `defaulters`, `collection`, `ledger`, `outstanding_invoices`, `late_fee_charged` |
| `services/attendance.py` | `summarise`, `absentees`, `section_summary`, `student_month`, `student_percent`, `shortage`, `working_days` |
| `services/timetable.py` | `workload`, `completeness`, `grid`, `free_teachers`, `day_plan` |
| `services/payroll.py` | `register`, `cost_by_department`, `totals` |
| `services/admission_reports.py` | `funnel`, `by_source`, `seat_utilisation`, `demographics`, `rejections`, `cycle_time`, `dashboard` |
| `services/transport.py` | `seats` (route utilisation), `expiring_papers`, `charges_for_month`, `awaiting_assignment` |
| `services/comms.py` | `delivery_report`, `unreachable_contacts` |

That is most of §5.10.10 already written. **Reports is mostly a matter of
giving these a governed, permission-checked home and a report library — not of
writing new arithmetic.** Where a §5.10.10 KPI has no function above (revenue
versus expense by month, enrolment and retention trend, student:teacher ratio,
chronic absenteeism), write it in the owning service.

---

**Entities: what §5.10.5 lists, and what is likely to earn its table.**

§5.10.5 names `saved_reports`, `report_schedules`, `report_runs`,
`export_audit`, and four summary tables. Apply the same test transport and
communication used — does anything read it yet?

- **`export_audit` should not be a table.** `audit_log` already has the shape,
  the tenant key, the actor and the JSON payload, and `AuditAction.export` is
  the member waiting for it. A second audit trail is a second place to forget
  to look.
- **The four summary tables are a performance answer to a problem nobody has
  measured.** 100 students and 300 invoices do not need `attendance_summary`;
  a materialised summary that can disagree with the ledger it summarises is the
  drift §5.10.9 forbids, bought in exchange for speed nobody has asked for.
  Leave them until a query is actually slow, and say so.
- **`report_runs` earns its table only alongside async running** (§5.10.9's
  heavy-report rule). If reports are synchronous for now, a run row records
  nothing anybody reads.
- **`saved_reports` and `report_schedules` are the two that are probably
  real** — but note that a scheduled report emailing a PDF each Monday is
  `services/jobs.py` plus `comms.notify()`, both of which now exist, rather
  than a new mechanism.

A defensible v1 is: **a report registry in code** (the same shape as
`core/permissions.py`, `core/modules.py`, `core/message_templates.py` and
`fees.OPT_IN_SOURCES` — this codebase has a strong precedent for it), each
entry naming its permission, its parameters and the service function it calls;
plus `saved_reports` if a school genuinely needs to store its own filter sets.
That gives the Report Library of §5.10.3 without four tables nothing reads.

---

**Leave out of this module**, and say so rather than half-building:

- Custom/ad-hoc report builder. A query builder behind a records clerk's screen
  is the injection surface §3.16 refused a `formula` calculation method over.
- Board/statutory return formats — nobody has produced the actual form.
- Watermarking (§5.10.9 says "can be"), and download-expiry tracking.
- Drill-down as a stored concept; it is a UI behaviour over the same functions.

---

**One reporting wrinkle transport introduced**, worth deciding rather than
inheriting: a fee plan's `monthly_total` sums its items, and the transport item
carries zero because the real price is on the stop's slab. So class 10's plan
reads ₹2,800 — correct for a child who does not take the bus, and short by the
slab for one who does. `tests/test_fee_setup.py` pins it. A "what does this
child actually pay" figure has to consult the opt-in, which is
`charges_for_month()`.

**And one piece of stale bookkeeping to fix in passing:** `core/modules.py`
still says `built=False` for `admission` and `hr`, both of which are built. It
is the honest-bookkeeping field, so it should be honest.

---

### 9.2 What Parts 3 and 4 built that reports should reuse

| Reach for | Rather than |
|---|---|
| `services/jobs.py` (`@handler` **in `app/jobs.py`**, `enqueue`, schedules) | any inline send, or a new alerting mechanism |
| `documents` and `OwnerType.vehicle` | a new table for vehicle papers |
| `employees` | a `drivers` table |
| `services/timetable.py::conflicts()` | a fresh clash checker |
| `holidays` and `attendance.working_days()` | a second calendar, anywhere |
| `services/grading.py` versioning + freeze | a second frozen-document mechanism for message templates |
| `audit.next_number()` | any `max(seq) + 1` for a document number |
| `fees.primary_contact()` | a third way to find who to ring |
| `core/settings_registry.py` | new columns for policy switches (§3.15) |
| `services/school_settings.py::module_enabled` | a UI-only feature switch |
| `fees.OPT_IN_SOURCES` | a second way to say "bill only those who chose this" |
| `comms.notify()` and `core/message_templates.py` | any new way to send anything |
| `fees.defaulters()` | a second defaulter query; it moved out of its route so the chase and the screen could agree |
| `NOT_BLANKET_READ` | naming a sensitive permission `.read` and hoping |
| `tests/test_tenant_isolation.py` | writing a new cross-tenant check from scratch |

### 9.3 Checkpoint 4

- ~~A CBSE report card publishes and stays frozen~~ — **done and tested**
  (`tests/test_report_cards.py`).
- ~~A payroll run completes for the demo school~~ — **done and tested**
  (`tests/test_payroll.py::test_a_payroll_run_completes_for_the_demo_school`,
  now 16 payslips).
- A non-technical reader can change a fee rule using only
  `CONFIGURATION-GUIDE.md` — **held until the owner clears the modules above.**

### 9.4 Before starting

1. `git log --oneline main..HEAD` — read them; the messages carry the
   reasoning deliberately.
2. Run the suite (§2) and the by-hand Postgres check (§4). Believe neither
   number until you have seen it. SQLite hid three Postgres defects already.
3. Decide with the owner whether to push first. Nothing has ever been pushed
   and CI has never run, so the first push is also the first CI run — expect it
   to find something, and it grows with every part that lands.
4. The web dashboard is further behind than ever: known broken against the fee
   API (§7), and examinations, HR, payroll, transport and communication have all landed
   since anyone last opened it. Nothing in `web/` knows transport or the
   outbox exists.

**Two warnings from this session.**

`fees.generate()` commits internally. Poking at it from a throwaway script does
**not** roll back — doing so left a stray fee head, a plan item and a hundred
December invoices in `sunrise_test` before that was noticed. Reset the schema
after experimenting rather than trusting a `rollback()`.

And **the demo school's id is not reliably 1.** `seed.py::wipe()` truncates
without `RESTART IDENTITY`, so a reseed over an existing database produces
id 2. A throwaway probe that hardcodes `school_id=1` returns empty results and
looks exactly like a bug in the code it is probing — it cost twenty minutes
this session. Read the id from `schools`.

The memory file `sunrise-erp-build.md` carries the same state in short form for
a session that starts cold.
