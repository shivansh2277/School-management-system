# Sunrise ERP — Functions and Features, Tested

**What this is.** Every function and feature the system exposes, what it is
supposed to do, and the result of actually running it. Written while testing,
on **8 September 2026**, against a real running server and a freshly seeded
database — not read off the code and not recalled.

**What this is not.** It is not `CONFIGURATION-GUIDE.md` (how a school changes
a rule) and not `EXTENSION-GUIDE.md` (how a developer adds a module). Neither
is written yet.

---

## 1. How this was tested

| | |
|---|---|
| Server | `uvicorn app.main:app --port 8077`, a real HTTP server, not a test client |
| Database | PostgreSQL `sunrise_test`, dropped by schema, migrated from empty through all 29 revisions, then seeded |
| Demo school id | **2** — *not 1*; `seed.py::wipe()` truncates without `RESTART IDENTITY` |
| Roles exercised | all six demo logins: admin, fee counter, transport manager, teacher, student, parent |
| Automated suite | `pytest -q` → **600 passed in 161.87 s** |
| Live sweep | every GET operation, called as all six roles |
| Live workflows | 47 behaviour checks — money arithmetic, permission refusals, reconciliation |

The method mattered more than the total. **Three defect classes were found that
the 578-test suite could not see**, because a test suite only exercises what
somebody thought to call:

1. endpoints nothing ever called (three of the mobile app's core screens),
2. endpoints nothing ever *questioned* (a headline number that was wrong),
3. permissions that pass a role check and skip the row check.

### Surface measured

**214 paths, 263 operations.** By area:

| Ops | Area | Ops | Area |
|---:|---|---:|---|
| 50 | `/admin/admission` | 9 | `/admin/staff-leave` |
| 21 | `/admin/fees` | 8 | `/admin/exams` |
| 18 | `/admin/transport` | 8 | `/admin/attendance` |
| 18 | `/teacher` | 7 | `/admin/employees` |
| 16 | `/parent` | 6 | `/admin/students` |
| 15 | `/admin/payroll` | 6 | `/admin/report-cards` |
| 14 | `/admin/timetable` | 4 | `/auth`, `/admin/teachers`, `/admin/classes`, `/admin/grading-scales`, `/admin/assessment-schemes` |
| 11 | `/admin/comms` | 3 | `/admin/departments`, `/admin/staff-attendance`, `/admin/notices`, `/admin/custom-fields`, `/admin/reports`, `/public` |
| 10 | `/student` | 2 | `/admin/settings`, `/admin/configuration` |

---

## 2. Scoreboard

| Area | Checked | Result |
|---|---|---|
| Authentication | 5 | **all pass** |
| Fees / money | 15 | **all pass** (one apparent failure explained and verified as correct) |
| Attendance | 4 | **all pass** |
| Timetable | 2 | **all pass** |
| Examinations | 2 | **all pass** |
| HR & payroll | 6 | **all pass** |
| Transport | 3 | **all pass** |
| Communication | 4 | **all pass** |
| Reports | 3 | **all pass** |
| Public portal | 2 | **all pass** |
| Tenant isolation | 1 | **all pass** |
| Mobile app endpoints | 8 | **5 defects found and fixed** |
| Role sweep (112 GETs × 6 roles) | 672 calls | **2 leaks found and fixed** |
| Web dashboard | 12 endpoints | **1 broken** (known, unfixed) |

**Defects found this session: 8. Fixed: 8.** All have regression tests, and
every fix was confirmed load-bearing by reverting it and watching tests fail.

---

## 3. Defects found by this testing

Each was found live, reproduced, fixed, and pinned with a test that fails
without the fix.

### 3.1 `/teacher/profile` — 500 for every teacher
`Employee.employee_id` does not exist; the column is `employee_code`. The
endpoint had never worked. **Fixed.**

### 3.2 `/teacher/classes/{id}/students` — 500 for every teacher
`roster()` returns `Enrolment` rows, deliberately, because a roll number
belongs to the year and not to the child. The handler iterated them as though
they were `Student` rows. Had it not raised, it would have returned **enrolment
ids where the app follows student ids** — the kind of wrong that shows up only
when something clicks the link. **Fixed**, and a test now follows the id
through to `/admin/students/{id}` to prove it resolves.

### 3.3 `/student/profile` — 500 for every student
Referenced `enrolment`, a name never defined in the function. **Fixed.**

### 3.4 `/parent/profile` — 500 for anyone who is not a guardian
`parent_only` is `students.profile.read`, which clerks and teachers also hold,
so non-guardians reach the route; the bare query returned `None` and the next
line raised. The answer is "you are not a parent", not a 500. Now uses
`scoping.guardian_for`. **Fixed.**

### 3.5 `/teacher/classes` — every class reported 1000 students
```
"student_count": db.query(Student).filter(Enrolment.class_section_id == section_id).count()
```
Two tables named, neither joined → a cartesian product. 100 students × 10
enrolments = **1000 for a class of 10**, on the teacher's home screen.
SQLAlchemy had been printing a cartesian-product warning into the server log
the whole time. **Fixed**; a test now asserts the count equals the roster it
links to.

### 3.6 Whole-school attendance readable by any class teacher
`/admin/attendance/shortage` and `/admin/attendance/absentees`. Measured:
`TCH001` class-teaches 10-A (10 children) and received **all 100**, with names,
admission numbers and attendance percentages, across all ten classes.

Cause: both gated on `attendance.record.read` school-wide — which a teacher
*holds*. `require_permission(school_wide=True)` stops a guardian and nobody
else. **Fixed** via `scoping.narrow_to_own_sections()`, the same helper the
report gate uses. Omitting the section is refused, not widened.

### 3.7 Whole-school student roster readable by any teacher
`/admin/students` and `/admin/students/{id}`. Measured: `TCH001` opened a child
of 9-A — a class they do not teach — and read **full name, admission number,
date of birth, home address, guardian name and guardian phone**. Same cause as
3.6, on more sensitive data. **Fixed** (owner's decision: a teacher sees only
their own sections). The detail route now uses `scoping.assert_can_read_student`,
because narrowing only the list would be no narrowing — an id is guessable.

### 3.8 The Transport Manager counted as a teacher
The dashboard's headline `teachers` figure counted every employee with an
active login: **13 for a school with 12 teachers**. Found by running the
student:teacher ratio report and not recognising the number.

The existing test agreed with the bug — it recomputed "every active employee"
and checked the code matched, mirroring the implementation rather than the
intent. **Fixed** in `stats.totals()`, so the dashboard and the ratio move
together.

---

## 4. Module by module

Legend: **PASS** = run and verified this session.

### 4.1 Authentication and access — `/auth` (4 ops)

| Function | Behaviour | Result |
|---|---|---|
| `POST /auth/login` | Issues a JWT for a role + login id + password | **PASS** — all six demo logins |
| Wrong password | Refused | **PASS** — 401 |
| Unauthenticated call | Refused | **PASS** — 401 |
| Forged token | Refused | **PASS** — 401 |
| Right password, wrong role | Refused | **PASS** — 401 |
| `GET /auth/me` | The caller's identity and permissions | **PASS** |

**Model:** 77 permissions, 14 system roles. Permission at the route
(`require_permission`), scope in the service (`services/scoping.py`).

### 4.2 Students and enrolment — `/admin/students` (6 ops)

| Function | Behaviour | Result |
|---|---|---|
| List roster | Paged, searchable by name or admission number | **PASS** — 100 students |
| Filter by section | | **PASS** |
| Student detail | Profile + attendance % + latest result % | **PASS** |
| Create student | Allocates a gapless admission number (`YYYY` + 6 digits) | Covered by suite |
| Update / deactivate | Deactivation demands a reason, audited | Covered by suite |
| **Export CSV** | `students.profile.export`, school-wide, audited | **PASS** |
| Tenant isolation | Another school's child invisible and uneditable | **PASS** |
| Teacher scope | Own sections only | **PASS** *(fixed — 3.7)* |

The export omits date of birth, address and custom fields on purpose: an export
is where over-collection becomes permanent.

### 4.3 Fees — `/admin/fees` (21 ops)

The money path, verified arithmetically rather than by status code.

| Function | Behaviour | Result |
|---|---|---|
| Invoice register | 300 invoices, 900 lines | **PASS** |
| Collection report | Billed vs collected by month | **PASS** — billed ₹972,930 |
| `billed − collected == outstanding` | | **PASS** — exact |
| Months sum to the year total | | **PASS** — 972,930 = 972,930 |
| No fabricated zero months | 3 months present, none zero-billed | **PASS** |
| Defaulter list | Worst first, with a contact to ring | **PASS** — 100 families, top owes ₹11,700 |
| Every defaulter has a contact | | **PASS** |
| Student ledger | Invoices, payments, outstanding, credit | **PASS** |
| **Collect a payment** | Clerk takes ₹500, receipt `SPS/RCP/2026/000172` | **PASS** — 201 |
| **Idempotency** | Same key replayed → no double charge | **PASS** — outstanding unchanged |
| **Ledger reconciles** | Σ invoice balances == outstanding | **PASS** — 12,100 = 12,100 |
| Daybook sees the money | | **PASS** — ₹600 today |
| Teacher cannot take money | | **PASS** — 403 |
| Parent cannot take money at the counter | | **PASS** — 403 |
| **Clerk cannot reverse a payment** | Segregation of duties (§5.5.9) | **PASS** — 403 |

**One check needed explaining rather than fixing.** Paying ₹500 made outstanding
*rise* by ₹3,700. `collect()` assesses the fine before allocating, so three
overdue invoices were fined at the moment of payment. Verified exactly:

```
invoice ...000203  base 2800  fine 1400  cap 1400  -> AT CAP
invoice ...000103  base 2800  fine 1400  cap 1400  -> AT CAP
invoice ...000003  base 2800  fine 1400  cap 1400  -> AT CAP
                        total fines 4200 − 500 paid = +3700
```
₹4,200 in fines, every one exactly at the 50%-of-invoice cap. **The cap holds
and the arithmetic is correct.** Policy comes from settings, not code:
grace 5 days, initial ₹300, ₹100/day, cap 50%.

### 4.4 Attendance — `/admin/attendance` (8 ops)

| Function | Behaviour | Result |
|---|---|---|
| School summary | | **PASS** — present 5,309 / absent 294 / leave 197 = **91.5%** |
| Absentees on a day | With a guardian to telephone | **PASS** |
| Shortage list | Below the school's threshold, worst first | **PASS** — 0 under 75% |
| **Threshold is a setting** | `attendance.shortage_threshold`, default 75 | **PASS** *(new)* |
| Explicit threshold overrides without changing policy | | **PASS** |
| Teacher without a section | Refused, not widened | **PASS** — 403 *(fixed — 3.6)* |
| Teacher with their own section | Allowed | **PASS** |
| Teacher with another's section | Refused | **PASS** — 403 |
| Office reads the whole school | Unchanged | **PASS** — 100 |
| Holidays, leave requests | | **PASS** |

### 4.5 Timetable — `/admin/timetable` (14 ops)

| Function | Behaviour | Result |
|---|---|---|
| Workload | Periods per teacher vs ceiling | **PASS** — 12 teachers, 300 periods, limit 30, **every teacher on 25, spread 0**, none over limit, none unassigned |
| Completeness | Sections with unfilled periods | **PASS** — 10 sections |
| Conflict detection | Teacher and room clashes | Covered by suite |
| Substitution / cover | Refuses a substitute who is on leave | Covered by suite |

### 4.6 Examinations and report cards — 8 + 6 ops

| Function | Behaviour | Result |
|---|---|---|
| Exam list | | **PASS** — 4 exams |
| Datesheet / papers | | **PASS** |
| Marks entry | Teacher limited to own subjects | Covered by suite |
| Marks lock + audited override | | Covered by suite |
| Report card publications | | **PASS** — none published on a fresh seed |
| Frozen at publication | Grade + scale version snapshotted | Covered by suite |
| Withheld for unpaid dues | §0.6b | Covered by suite |

### 4.7 HR and payroll — 7 + 15 + 9 + 3 ops

| Function | Behaviour | Result |
|---|---|---|
| Employee register | | **PASS** — 16 employees (12 teaching, 1 administrative, 3 support) |
| Statutory details (PAN/PF/ESI/bank) | Behind `hr.salary.read` | **PASS** |
| **Fee counter cannot read bank details** | `NOT_BLANKET_READ` | **PASS** — 403 |
| Salary components | Zero hardcoded rates | **PASS** — 11 components |
| Payroll runs | | **PASS** |
| **Teacher cannot see payroll** | | **PASS** — 403 |
| Run lifecycle | draft → calculated → approved → paid; approved is immutable | Covered by suite |
| Leave, staff register, loss of pay | One definition of absent days | Covered by suite |

### 4.8 Transport — `/admin/transport` (18 ops)

| Function | Behaviour | Result |
|---|---|---|
| Vehicles, routes, stops, slabs | | **PASS** — 2 vehicles, 2 routes |
| Roadworthiness | Refusal with no override | **PASS** — R1 roadworthy, no gaps |
| Seat utilisation | | **PASS** |
| Expiring compliance papers | | **PASS** |
| **Transport manager cannot read the fee ledger** | | **PASS** — 403 |
| Optional fee head billed only to riders | The `FeeHeadType.optional` money bug | Covered by suite |

### 4.9 Communication — `/admin/comms` (11 ops)

| Function | Behaviour | Result |
|---|---|---|
| Templates, versioned | | **PASS** — 4 templates |
| Audience preview | Counts reach *and* unreachable before sending | **PASS** |
| Unreachable families | The honest counterweight to a delivery report | **PASS** — **14 families with no email** |
| Outbox + delivery record | Dispatched from the worker, never in a request | Covered by suite |
| Emergency broadcast | Own permission, own endpoint | **PASS** — gated |
| Opt-out honoured / overridden for mandatory categories | | Covered by suite |
| A mail failure cannot roll back money work | | Covered by suite |

The 14 unreachable families are the number that decides open question T: §0.11
chose email only, and a Lucknow school collects mobile numbers.

### 4.10 Reports — `/admin/reports` (3 ops, 21 reports)

| Function | Behaviour | Result |
|---|---|---|
| Library | Only what the caller could actually run | **PASS** — **21 reports, 9 categories** |
| Run a report | | **PASS** |
| Every report runs | Registry/runner parity | **PASS** — all 21 |
| Context on output | Year, filters, timestamp, who | **PASS** |
| Export CSV, audited | | **PASS** — `# Fee defaulters \| academic year 2025-26 \| filters: none \| generated 2026-09-08T14:06:45+00:00 by Office Admin` |
| Guardian refused a school report | | **PASS** — 403 |
| Teacher refused a school-wide report | | **PASS** — 403 |
| Fee clerk refused a payroll report | | **PASS** — 403 |
| Numbers reconcile with the module screens | | **PASS** |
| Student:teacher ratio | | **PASS** — 100 / 12 = **8.3** *(after fix 3.8)* |

Categories: Fees, Attendance, Academics, Timetable, Payroll, Transport,
Communication, Admission, Management.

### 4.11 Admission — `/admin/admission` (50 ops) and `/public` (3 ops)

The largest module. Public portal verified live; the internal pipeline is
covered by the suite.

| Function | Behaviour | Result |
|---|---|---|
| Public: open cycles | No login required | **PASS** |
| Public: unknown school | 404, deliberately indistinguishable from other failures | **PASS** |
| Cycle dashboard, funnel, seats, reports | | **PASS** |
| Enquiries, applications, documents, assessments, interviews | | **PASS** (GET); writes covered by suite |
| Decision, offer, offer response, expiry sweep | | Covered by suite |
| Conversion to an enrolled student | Allocates the admission number | Covered by suite |
| Every admission endpoint refuses all five non-admin roles | | **PASS** — 403 across the board |

### 4.12 The mobile app's own endpoints — `/teacher` 18, `/student` 10, `/parent` 16

**This is where the sweep earned its keep.** Five of these were broken.

| Function | Result |
|---|---|
| `/teacher/classes` | **PASS** *(fixed — count was 1000)* |
| `/teacher/classes/{id}/students` | **PASS** *(fixed — was 500)* |
| `/teacher/profile` | **PASS** *(fixed — was 500)* |
| `/teacher/timetable` | **PASS** |
| `/student/dashboard` | **PASS** |
| `/student/profile` | **PASS** *(fixed — was 500)* |
| `/student/timetable`, `/student/results/{exam_id}` | **PASS** |
| `/parent/children` and per-child attendance, homework, results, summary, transport, profile | **PASS** |
| `/parent/profile` | **PASS** *(fixed — 500 for non-guardians)* |
| A parent reading another family's child | **PASS** — 403 |
| A student reading another student | **PASS** — 403 |

### 4.13 Administration — settings, configuration, custom fields, audit

| Function | Behaviour | Result |
|---|---|---|
| `/admin/settings` | School profile and branding | **PASS** |
| `/admin/configuration` | The setting store and module switches | **PASS** |
| Setting validation | Wrong type refused, all-or-nothing | **PASS** — 422 |
| Unknown setting key refused | | Covered by suite |
| Feature flags enforced at the API | Not just in the UI | **PASS** — transport off ⇒ 404 |
| Custom fields | School-invented attributes, validated | Covered by suite |
| Audit log | Destructive actions demand a reason | Covered by suite |
| **Export audit** | Who, what, when, how many rows | **PASS** |

### 4.14 Background jobs

| Handler | Purpose | Result |
|---|---|---|
| `system.heartbeat` | Liveness | **PASS** — ran live |
| `fees.overdue_sweep` | Marks overdue, charges fines, chases defaulters | Covered by suite |
| `fees.generate_invoices` | Bills a month for a school | Covered by suite |
| `admission.offer_sweep` | Expires lapsed offers, moves the waitlist | Covered by suite |
| `transport.document_expiry` | Nightly compliance pass | Covered by suite |
| `comms.dispatch` | Sends queued messages | Covered by suite |

Verified live: migrate from empty → seed → `worker.py --once` → **1 job ran**.

---

## 5. The web dashboard — the honest part

TypeScript compiles clean (`npx tsc --noEmit`, exit 0), **but that proves
nothing**: the web app hand-declares its own API types rather than generating
them, so a passing typecheck cannot see a backend change.

Every endpoint it calls, checked live:

| Endpoint | Status |
|---|---|
| `/auth/login`, `/auth/me` | OK |
| `/admin/dashboard/stats` | OK |
| `/admin/students`, `/admin/classes`, `/admin/subjects`, `/admin/teachers` | OK |
| `/admin/exams`, `/admin/grade-bands`, `/admin/notices`, `/admin/settings` | OK |
| `/admin/fees/invoices/generate` | OK |
| **`/admin/fees/structures`** | **404 — the endpoint no longer exists** |

**11 of 12 work; the Fees page is broken.** It calls a deleted endpoint.

More important than that one 404: the web app has **8 pages** (Dashboard,
Students, Classes, Teachers, Attendance, Exams, Fees, Notices, Settings) against
a **214-path** API. It knows nothing about admission, timetable, HR, payroll,
transport, communication or reports — all of which have landed since anyone
last opened it.

---

## 6. What was not tested, and why

Stated so nothing here is mistaken for a broader claim.

- **Load, concurrency and performance.** No endpoint has been measured under
  load. "No query is slow" is an assumption at 100 students, which is the
  stated reason the four report summary tables were not built.
- **The mobile app itself.** Its API endpoints are now exercised; the app is not.
- **Real email delivery.** The provider sits behind a seam; no message has been
  sent to a real inbox.
- **PDF rendering.** Receipt and report-card PDFs generate; nobody has read one
  as a document.
- **Browser testing of the web app.** Endpoints were checked, screens were not
  opened.
- **Destructive and edge-case write paths** on the live server — void, reverse,
  discard, promotion, year rollover. These are covered by the suite, not by
  this sweep, because the sweep ran against a database I wanted to keep
  readable.
- **CI.** Has still never run. 79 commits, nothing pushed.
- **Multi-tenant at scale.** Isolation is tested with one planted rival school,
  not with many.

---

## 7. Open questions this testing did not answer

These are product decisions, not defects. Full list in `HANDOFF.md` §8.

| # | Question |
|---|---|
| E | Is a six-day week right, and are Saturdays half days? |
| F | Who may reopen a closed fee period? |
| G | Should an unpaid invoice ever be written off? |
| H | What makes a result a fail or a compartment? Nothing computes it — there is no pass mark in the scheme |
| I | Does an absent paper lower a percentage, or stay out of it? |
| J | Who may reopen a locked paper? |
| M–O | TDS computation; earned-leave accrual; mid-month joiner proration |
| P–R | Split-route riders; sibling concession on bus fare; the hour the nightly sweeps run |
| S | Should fee reminders override an opt-out? |
| T | **Is email-only viable?** 14 of 98 guardians are unreachable — measured, not assumed |

*(U and V — teacher scope and the attendance threshold — were answered and
built this session.)*

---

## 8. Summary

- **600 automated tests pass** in 161.87 s, on PostgreSQL.
- **Migrations verified from empty**: 29 revisions → seed → worker ran a job.
- **214 paths / 263 operations**; every GET called as all six roles.
- **8 defects found, 8 fixed**, each with a regression test proved to fail
  without its fix.
- **1 known break left**: the web dashboard's Fees page calls a deleted
  endpoint. Unfixed because the web app is a rewrite waiting to happen, not a
  patch.

The finding worth carrying forward: **a green suite is not a working system.**
Every defect here lived behind a passing suite — three in endpoints nothing
called, one in a number nothing questioned, two in permission checks that
looked correct because the role check passed and the row check was missing.
