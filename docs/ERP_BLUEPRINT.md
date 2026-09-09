# Sunrise School ERP — Design Blueprint

**Status:** Decisions locked 6 September 2026. Design document, not an implementation plan.
**Written:** 4 September 2026 · **Decisions folded in:** 6 September 2026
**Scope:** the management **web application** and the domain architecture behind it. The mobile app is out of scope here, except where a decision made now would block it later (§14).
**Companion documents:** `docs/BLUEPRINT.md` (the v0 build contract, still authoritative for what exists today), `Sunrise-HANDOFF.md` (deployment state and known defects).

---

## How to read this document

Every claim about the **existing system** in §2 was read out of the repository on 4 September 2026 — model files, service files, route files, `vercel.json`, `requirements.txt`. Where something is asserted without having been read, it is marked **Needs verification**. Nothing about the current implementation here is recalled or assumed.

Everything from §3 onward is **proposal**, not fact. It is written to be argued with. §16 lists what must be decided before any of it is built.

This document deliberately challenges parts of the existing design. That is not a criticism of v0 — v0 was built to a different brief (a college viva deliverable and a client-facing demo template) and it met that brief. An ERP is a different product with different failure modes, and the honest finding is that several v0 decisions that are *correct for a demo* become *structurally wrong for an ERP*. Those are named in §2.5.

---


---

## 0. Decision register (authoritative)

Settled with the product owner on 6 September 2026. **Where anything later in this
document disagrees with this table, this table wins** — the analysis in §2 and the
module specifications in §5 were written before these answers and have been corrected
only where they would otherwise mislead implementation.

| # | Question | Decision |
|---|---|---|
| 1 | Hosting and background processing | **Oracle Cloud Always Free** (ARM, 2 OCPU / 12 GB after the July 2026 halving) running Docker: API + worker + PostgreSQL + MinIO. Migrate to paid hosting (~₹500/mo VPS) before the first paying school's data lands. Vercel is abandoned. |
| 2 | One school or a product? | **Product, sold to many separate schools.** Multi-tenant: `school_id` on every table from Phase 0. A tenant is one independent school — *not* a branch. |
| 2b | Multi-branch (one school, many campuses) | **Out of scope.** No `branch_id`. Revisit only if a real prospect needs it. |
| 2c | Per-school customization model | **Configuration + custom fields + feature flags now; plugin _seams_ now; plugin _runtime_ deferred** until a real school presents a requirement config cannot express. See §3.15. |
| 3 | Migrate existing data or start fresh | **Start fresh.** Demo data expanded to 10 classes × 10 students (100 students), one demo school. Import from Excel/SQL is built when a real school is signed, not before. |
| 4 | Attendance granularity | **Daily only.** No period-wise attendance. |
| 4b | Geography | **Lucknow first**, other cities later. Statutory defaults follow Uttar Pradesh. |
| 5 | Board and assessment pattern | **CBSE.** Report card designed for CBSE but kept configurable. |
| 6 | Fee policy | Monthly billing · **student-level** invoicing (not family) · **10% sibling concession** · late fee **₹300 once 5 days overdue, then +₹100 per further day, capped at 50% of the invoice** · **no refunds** · dues **not carried forward** across years · **result withholding permitted** for non-payment. |
| 6b | Unpaid dues at year end | **Withhold the Transfer Certificate and the report card** until cleared. Dues are not written off and not carried into the next year's ledger. |
| 7 | Shared `persons` supertype | **No.** Students, guardians and employees stay separate, with a nullable cross-link for the staff-whose-child-studies-here case. |
| 8 | Grade snapshotting | **Published report cards are frozen.** Grade and grading-scale version are snapshotted at publication; live screens keep computing from `grade_bands`. This supersedes BLUEPRINT §7.5 for published documents only. |
| 9 | Payroll in scope? | **Yes**, built as configurable salary components so each school defines its own structure as data. Zero hardcoded rates. See §5.3 and §3.16. |
| 10 | Payment gateway | **Deferred to V2.** No gateway integration. Offline collection (cash/cheque/UPI reference) only, recorded manually. |
| 11 | Communication channels | **Email only for v1**, through a pluggable transactional provider (Brevo/Resend free tier) with the owner's address as reply-to. SMS and WhatsApp are wired behind the same interface and enabled per school once permission and DLT registration exist. |
| 12 | Aadhaar and sensitive identifiers | **Store the last 4 digits plus a `verified` flag only.** The full 12-digit number is never stored. |
| 13 | Admission channel | **Public online portal**, with an admin login gate before an application is acted on. Bot/spam protection is in scope for Part 2. |
| 14 | Data retention | **Academic and financial records retained indefinitely.** Portal access for a departed student and their guardians ends **3 months** after leaving. Nothing is deleted on a timer. |
| 15 | Report card format | CBSE-shaped, **template-configurable** per school. |
| 16 | Section allocation | **Automatic** at conversion, with a preview before commit. |
| 17 | Homework / Assignments | **Removed from the web admin dashboard. Retained in the mobile app.** Tables and teacher/student endpoints stay; the admin screen and admin routes are retired. |
| 18 | Day-to-day system administrator | A **receptionist or dedicated records clerk** at each school. Configuration screens must be usable by a non-technical person. |
| 19 | Localisation | **Not required.** English only. |
| 20 | Library / hostel / inventory / health room | **Out of scope.** Foundation entities anticipated in the extension guide only. |
| 21 | Admission number format | **10 digits: 4-digit joining year + 6-digit sequence** (e.g. `2026000147`). Permanent and immutable for life. Unique **per school**, gapless per year, allocated at conversion. |

### Deliverables added by these decisions

- **`CONFIGURATION-GUIDE.md`** — non-technical: how a school changes fee rules, late fees, grading scales, report card layout, payroll components, custom fields, enabled modules.
- **`EXTENSION-GUIDE.md`** — technical: how to add a module through the seams, where Library/Hostel/Inventory would attach, how to wire the V2 payment gateway, how to switch email → SMS/WhatsApp.

### Still open

| # | Question | Needed by |
|---|---|---|
| A | A real Lucknow school's payroll structure, to validate the component model against | Part 4 |
| B | Confirmation that Uttar Pradesh levies no professional tax (assumed; to be verified before payroll is written) | Part 4 |
| C | Whether the late-fee clock stops when the next month's invoice is generated, or keeps accruing on the old invoice | Part 3 |
| D | Exact CBSE report card layout the target school expects | Part 4 |


## 1. The thesis

If a real school hired us to build its ERP, the answer is not "the current app plus more screens". Three structural facts would have to change first, and most of the rest follows from them.

**1. A student is not a row. A student is a person with a history.**
Today `students.class_section_id` is a direct foreign key — a student *is in* exactly one section, and the row has no memory. When the school promotes 10-A to 11-A in April, that column is overwritten and last year's attendance, marks and fee records silently re-attach to the new class. There is then no way to answer "what was this child's attendance in Class 9" or "print the 2025-26 nominal roll". **This single field is the largest structural blocker in the system.** §3.2 proposes replacing it with an enrolment record.

**2. An academic year is not a string.**
Today `academic_year` is a `String(9)` denormalised onto `class_sections` and again onto `school_settings`. Nothing enforces that the two agree, nothing marks one year as current, nothing closes a year, and the transactional tables — `attendance`, `marks`, `fee_invoices` — have no academic year at all; they infer it from dates. An ERP runs *sessions*: the school works in 2026-27 while still reading 2025-26 and simultaneously admitting for 2027-28. That needs a first-class entity (§3.1).

**3. Money needs a ledger, not a status column.**
Today `fee_payments.invoice_id` is **unique** — one payment per invoice, full amount only. A parent paying ₹5,000 against a ₹12,000 term fee has nowhere to be recorded. There are no fee heads (tuition vs transport vs lab), no concessions, no fines, no refunds, no cancellations. `fee_invoices.status` is a stored enum mutated in place with no record of who changed it. For a school this is not a missing feature, it is a correctness problem — fee data is the data the school gets audited on (§3.9).

Everything else in this document — admission pipelines, transport, HR, permissions — is comparatively ordinary ERP work. These three decide whether the system survives its second academic year.

---

## 2. Existing system analysis

### 2.1 What exists today (verified)

21 tables across 5 model modules, a three-layer backend (`api → services → models`), and a React admin dashboard with 10 screens.

| Model module | Tables |
|---|---|
| `user.py` | `users`, `students`, `teachers`, `parents`, `parent_student` |
| `academic.py` | `class_sections`, `subjects`, `class_subject_teacher`, `timetable_slots` |
| `assessment.py` | `exams`, `exam_schedule`, `marks`, `grade_bands` |
| `fees.py` | `fee_structures`, `fee_invoices`, `fee_payments`, `school_settings` |
| `ops.py` | `attendance`, `homework`, `homework_submissions`, `notices` |

Backend surface: `api/auth.py` plus role-partitioned packages `api/admin/` (classes, exams, fees, notices, stats, students, teachers), `api/teacher/` (announcements, attendance, classes, dashboard, homework, marks), `api/student/` (academics, dashboard), `api/parent/` (children, fees). Services: `assessment`, `attendance`, `common`, `fees`, `homework`, `notices`, `scoping`, `stats`.

Web dashboard pages: Assignments, Attendance, Classes, Dashboard, Exams, Fees, Notices, Settings, Students, Teachers.

Deployment: Vercel (dashboard as a static Vite build; API as a Python serverless function via `backend/api/index.py` with legacy `builds`/`routes` config) against Neon-hosted PostgreSQL 18.6. Backend dependencies are deliberately few: FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, `psycopg`, `python-jose`, `passlib`/`bcrypt`, `reportlab`.

### 2.2 What can be retained as-is

These are good decisions. The ERP should keep them rather than re-litigate them.

| Retained | Why it holds up at ERP scale |
|---|---|
| **Single `users` table with a `role` discriminator plus role profile tables** (`students`, `teachers`, `parents`, each with a unique `user_id`) | Correct shape. One identity, one login namespace, one password policy, role-specific attributes in their own tables. Extends cleanly to more roles (§3.4). |
| **Service-layer access scoping** (`services/scoping.py`) | The single best architectural decision in v0. Authorisation lives below the routes, so a new endpoint cannot forget it. The *contents* must change (§3.5) but the *placement* is right and should be preserved exactly. |
| **VARCHAR-backed enums** (`enum_col`, `native_enum=False`) | Adding a status value never needs an `ALTER TYPE` migration. An ERP adds status values constantly. Keep. |
| **Computed-not-stored grades** (`common.grade_for` reads `grade_bands` at read time) | Correct. Changing a grade band re-grades history rather than leaving stale letters behind. |
| **Business rules as database constraints** — `uq_attendance_student_date`, `uq_mark`, `uq_invoice_period`, `uq_parent_student`, `uq_class_section`, `uq_timetable_slot` | Enforcing rules in the database rather than only in Python is exactly right, and should be the house style for every new table. |
| **`Decimal` / `Numeric(10,2)` for money** | Correct type, never floats. Keep, and extend to every new financial column. |
| **Empty-state honesty and the `DataTable` `loading` prop** | A screen must not assert "none exist" when it means "not yet known". This is a product principle, not a UI detail, and belongs in the ERP's UI contract. |
| **Three-layer separation** (`api` thin, `services` holds rules, `models` holds schema) | Standard, correct, already followed consistently. |

### 2.3 Entities that become ERP foundations, with modification

| Existing | Required change | Reason |
|---|---|---|
| `users` | Add a `status` lifecycle (beyond boolean `is_active`), `must_change_password`, `last_login_at`, and a nullable `person_id` if the person/user split in §3.4 is adopted | An applicant's parent and an enrolled student's parent are the same human; a staff member who resigns is not the same as one deactivated by mistake. |
| `students` | **Remove `class_section_id` and `roll_no`** — move both to a new `enrolments` table keyed by academic year (§3.2). Add `status`, `admission_id`, `house`, `category`, `religion`, `mother_tongue`, `blood_group`, `is_rte` | A student's class is a fact *about a year*, not about the student. |
| `class_sections` | Replace the `academic_year` string with an `academic_year_id` FK; add `capacity`, `stream` (classes 11–12), `room` | Needed to open next year's sections while this year is still live. |
| `subjects` | Add a `class_subject_offering` join (which subjects are offered to which class/stream/year), plus `is_elective`, `is_scholastic` | Today a subject is a global row with no class scoping. Class 10 Sanskrit and Class 4 Sanskrit are different offerings with different syllabi and different mark schemes. |
| `teachers` | Generalise to `employees` (§3.4). Teaching is a *role*, not the only kind of staff a school employs | Recruitment/HR cannot be built on a table that only models teachers. |
| `parents` + `parent_student` | Restructure into `guardians` + `student_guardian` with a structured `relation` enum, `is_primary`, `is_emergency_contact`, `has_portal_access`, `custody_note`; add an optional household/family grouping | `relation` is currently free-text `String(20)`. Sibling discovery, one-invoice-per-family, and "who may collect the child" all need structure. |
| `attendance` | Unique key is `(student_id, date)` — **daily only**. Key on `enrolment_id` rather than `student_id`. **Daily attendance is confirmed as the only mode (§0.4)** — no period-wise, no sessions | Keeps the existing constraint shape; only the key changes. |
| `fee_invoices` / `fee_payments` | Replace with a real billing model: fee heads, invoice lines, part-payments, concessions, adjustments (§3.9) | `fee_payments.invoice_id` is unique — the current model **cannot represent a partial payment**. |
| `notices` | Generalise into Communication: channel (in-app/SMS/email/push), delivery records, scheduling, read receipts | Today a notice is in-app only with no delivery evidence. |
| `school_settings` | Split into school identity/branding, per-year configuration, and feature flags. Also stop accepting an unvalidated `dict` on `PATCH /admin/settings` | Already a known defect; becomes a security problem once settings drive financial behaviour. |

### 2.4 New entities the ERP will require

Indicative rather than final; the entity model is developed properly in §4.

- **Foundation:** `academic_years`, `enrolments`, `persons` (optional, §3.4), `documents`, `audit_log`, `number_sequences`, `addresses`
- **Admission:** `admission_cycles`, `enquiries`, `applications`, `application_guardians`, `application_documents`, `assessments`, `interviews`, `admission_offers`, `waitlist_entries`, `application_fee_payments`
- **HR:** `employees`, `employment_contracts`, `departments`, `designations`, `job_postings`, `candidates`, `interview_rounds`, `leave_types`, `leave_balances`, `leave_requests`, `staff_attendance`, `payroll_runs`, `salary_components`, `payslips`
- **Examinations:** `assessment_schemes`, `grading_scales`, `exam_terms`, `report_card_templates`, `report_card_publications`, `co_scholastic_marks`, `remarks`
- **Fees:** `fee_heads`, `fee_plans`, `fee_plan_items`, `student_fee_assignments`, `concessions`, `invoices`, `invoice_lines`, `payments`, `payment_allocations`, `adjustments`, `refunds`, `fines`, `gateway_transactions`
- **Transport:** `vehicles`, `drivers`, `routes`, `route_stops`, `transport_assignments`, `vehicle_documents`, `trip_logs` (optional, §16)
- **Timetable:** `periods`, `timetable_versions`, `teacher_availability`, `substitutions`, `academic_calendar`, `holidays`
- **Communication:** `message_templates`, `message_campaigns`, `message_recipients`, `delivery_receipts`, `notification_preferences`, `device_tokens`
- **Administration:** `roles`, `permissions`, `role_permissions`, `user_roles`, `settings`, `saved_reports`

### 2.5 Architectural weaknesses that matter at ERP scale

Ordered by damage. Items 1–5 are structural; 6–11 are serious but locally fixable.

**1. No academic-year architecture.**
`academic_year` is a string on `class_sections` and a second string on `school_settings`, with no table, no current-year flag, no year-close process, and no year column on `attendance`, `marks` or `fee_invoices`. Consequence: the school cannot run two sessions at once, cannot open next year's admissions while this year is live, and cannot produce a defensible year-end archive. *This blocks the ERP outright.*

**2. Student-to-class is a mutable pointer, not history.**
`students.class_section_id`, with `uq_student_roll` on `(class_section_id, roll_no)`. Promotion overwrites it. All historical academic data — joined through `student_id` — silently re-parents to the new class. Consequence: no transfer certificate, no historical nominal roll, no year-on-year progress reporting, no correct answer to "who was in 10-A last year". *This blocks the ERP outright.*

**3. The fee model cannot represent how schools actually bill.**
`fee_payments.invoice_id` is unique: one payment, full amount, no partial. `fee_structures.class_name` is globally unique, so fees cannot vary by year, stream, category or concession. There are no fee heads, so transport fees have nowhere to live — which means the Transport module has no billing path at all. `fees.pay()` has two further integrity problems: `_next_receipt_no` computes `max(seq)+1` in Python with no lock, so two concurrent payments race and the unique constraint turns that into a 500 rather than a correct retry; and there is no idempotency key, so a retried request can double-charge. *Fee data is the data schools get audited on.*

**4. No audit trail.**
`TimestampedBase` gives `created_at` and `updated_at` only — no `created_by`, no `updated_by`, no change history. Marks can be edited, invoice status mutated, students deactivated, and settings PATCHed with an unvalidated `dict`, and none of it leaves a trace. For a system holding children's academic and financial records this is the most serious *governance* gap. Note also that `updated_at` has `onupdate` but no `server_default`, so it stays NULL until the first update.

**5. Soft delete is inconsistent and under-modelled.**
The only deletion concept is `users.is_active`, and `common.roster()` is documented as returning "Active students" while its query has no `is_active` filter — a deactivated student still appears on attendance sheets and marks rosters (an already-recorded defect). The deeper problem: `is_active` conflates *left the school*, *suspended*, *created in error* and *portal access revoked*. An ERP needs a status lifecycle, not a boolean.

**6. RBAC is hardcoded, not modelled.**
`require_role(UserRole.admin)` and four enum values. There is no `roles` table and no permissions, so there is no way to create a Principal who sees everything but changes nothing, an Accountant restricted to Fees, or a Class Teacher with extra rights over their own section only. Every real school needs 10–20 distinct roles. `scoping.py` is correctly *placed* but encodes role logic in `if user.role == ...` branches that will not scale.

**7. The deployment target forbids background work.**
Vercel functions are stateless and time-limited, and the current config has no scheduler. The ERP needs nightly invoice generation, bulk student import, report-card PDF generation for a thousand students, SMS/email dispatch, overdue sweeps and data exports. None of that fits in a request/response function. Note also that `fees.refresh_overdue()` **writes and commits inside a GET read path** — a side effect on a read, exactly the pattern that breaks under concurrency. This constraint is why Vercel is abandoned in favour of an Oracle Cloud instance running a worker and scheduler (§0.1).

**8. No document or file storage anywhere.**
Not one table or column models an uploaded file (`photo_url` and `logo_url` are bare `Text`). Admission cannot function without documents — birth certificate, transfer certificate, Aadhaar, photographs, caste and income certificates. There is no object storage in the stack.

**9. No pagination, search or filtering discipline.**
Only `/admin/students` accepts a page parameter; the other list endpoints return everything. Invisible at 24 students; at 2,000 students with twelve years of history it *is* the user experience.

**10. Single-tenant with no `school_id`.**
**Decided (§0.2): this is a multi-tenant product.** Every table therefore needs a `school_id` from Phase 0, every query needs a tenant filter that cannot be forgotten, and `users.login_id` — currently globally unique — must become unique *per school*, since two schools will both have an `admin` and both may issue admission number `2026000001`. Tenant isolation is enforced in the same service layer that already enforces scoping (§3.5), never left to individual queries.

**11. One baseline migration, and no CI.**
`alembic/versions/` holds a single initial revision, and nothing runs the 68 backend tests before a deploy. An ERP churns schema constantly; migration discipline and a test gate stop being optional the moment real school data exists.

### 2.6 Deployment and technical constraints that must shape the design

| Constraint (verified) | Design consequence |
|---|---|
| API runs as a Vercel Python serverless function | No in-process background jobs, no cron, no websockets, no local file writes, cold starts. **Resolved (§0.1): moving to an Oracle Cloud container host with its own worker and scheduler.** |
| Neon free tier suspends when idle | Acceptable for a demo, unacceptable when a parent pays fees at 22:00. A paid tier or another host is a prerequisite for go-live. |
| No object storage in the stack | Must be chosen before Admission is built. |
| `reportlab` is the only document generator present | Report cards and receipts are feasible; *bulk* generation is not, without a worker. |
| Zero automated frontend tests; 68 backend tests | The test gate must expand with the ERP, especially around fees and permissions. |
| The backend dependency list is deliberately small | A virtue worth keeping. New dependencies should justify themselves — but a job queue and an object-storage client are genuinely required, not optional. |

**Needs verification:** the mobile application's internals; the exact contents of the 10 web pages; the coverage boundaries of the 68 tests; whether `reportlab` generation currently succeeds inside the Vercel function's memory and time limits; and the exact route count (the handoff states 79 — not re-counted for this document).

---

## 3. Foundational architecture decisions

These are cross-cutting. Every module in §5 depends on them, so they must be settled first. Where a decision is genuinely open, it is flagged and repeated in §16.

### 3.1 Academic year and session architecture

**Proposal: `academic_years` becomes a first-class entity, and every transactional row carries an `academic_year_id`.**

```
academic_years
  id, code ("2026-27"), start_date, end_date,
  status: planning | admissions_open | active | closing | closed | archived,
  is_current (exactly one true, enforced by a partial unique index),
  promotion_completed_at, result_published_at
```

Rules:
- **Exactly one year is `current`.** Enforced by `CREATE UNIQUE INDEX ... WHERE is_current` — a database constraint, not application code.
- **Several years may be open at once.** 2026-27 `active` while 2027-28 is `admissions_open` and 2025-26 is `closing` is the normal state of a school in January.
- **Every transactional table gets `academic_year_id`,** even where it looks derivable from a date. Deriving a year from a date requires knowing the year boundaries at query time and breaks the moment a school shifts its session dates or runs an extended year.
- **Closing a year is an explicit operation,** not the calendar rolling over. It runs result publication, promotion, fee reconciliation, and then freezes the year against writes.
- **Closed years are read-only** except through an explicit, audited "reopen" that only a named role can perform.

Challenge to a tempting shortcut: it will be proposed that the current year is read from `school_settings.academic_year` and used as an implicit filter everywhere. **Reject that.** An implicit global filter makes every historical query a special case, and makes the "two years open at once" state unrepresentable. The year should be an explicit parameter on queries that need it, defaulting to current at the API boundary — not hidden inside the data layer.

### 3.2 Student lifecycle and the enrolment model

**Proposal: split the permanent person from the yearly enrolment.**

```
students                          enrolments
  id                                id
  admission_no  (permanent)         student_id
  person/demographic fields         academic_year_id
  status                            class_section_id
  admission_id (origin)             roll_no
                                    section_change_history?
                                    status: active | transferred_out |
                                            struck_off | promoted | detained | passed_out
                                    joined_on, left_on
```

- `students` holds what is true for life: admission number, name, date of birth, blood group, the admission that created them.
- `enrolments` holds what is true for a year: class, section, roll number, house, and how the year ended.
- **Unique constraint moves** from `(class_section_id, roll_no)` on `students` to `(class_section_id, roll_no)` on `enrolments` — scoped by year automatically, because `class_sections` is year-scoped.
- **Everything that happens in a year points at the enrolment, not the student:** attendance, marks, invoices, transport assignment. Anything that is true for life — documents, guardians, the student's identity — points at the student.

Student status lifecycle:

```
       (from Admission)
             │
        enrolled ──► active ──┬──► promoted ──► active (next year)
                              ├──► detained ──► active (same class, next year)
                              ├──► transferred_out (TC issued)  ──► alumni
                              ├──► struck_off (non-payment / disciplinary)
                              └──► passed_out ──► alumni
        (any state) ──► suspended (temporary, reversible)
```

Why this matters more than it looks: **promotion becomes a data-creating operation rather than a data-destroying one.** Promoting 10-A creates 40 new enrolment rows for 2027-28 and marks 40 existing rows `promoted`. Nothing is overwritten, so last year stays queryable forever, and a promotion run can be reversed.

**Decided (§0.21):** `admission_no` is **permanent and immutable for life**, formatted as `YYYY` + 6-digit sequence (`2026000147`), unique per school and gapless per year. A student who leaves and rejoins keeps the original number.

### 3.3 Family, guardian and household model

**Proposal: guardians are people related to students, not "parent users".**

```
guardians                         student_guardian
  id, person fields                 student_id, guardian_id
  occupation, employer,             relation: father|mother|grandfather|
  annual_income_band,                         grandmother|uncle|aunt|
  qualification                               brother|sister|legal_guardian|other
  has_portal_access                 is_primary          (exactly one per student)
                                    is_emergency_contact
                                    receives_communication
                                    is_authorised_for_pickup
                                    custody_note
```

Decisions embedded here:
- **`relation` becomes an enum, not free text.** Today it is `String(20)`, which makes "father", "Father", "FATHER" and "papa" four different relations and makes any report on parents unreliable.
- **A guardian may have many students, and a student may have many guardians.** Already true structurally in `parent_student`; what is missing is the qualifiers.
- **Portal access is a property of the guardian, not a consequence of existing.** Today creating a parent creates a login. In a real school, a father may hold the portal login while the mother and a grandparent are recorded as contacts without accounts.
- **Siblings are derived, not stored:** two students sharing a primary guardian are siblings. A stored `sibling_id` would need constant repair.
- **Household/family grouping is not built.** Invoicing is student-level (§0.6), so the one use that would have justified it is gone. The 10% sibling concession is resolved through shared-primary-guardian sibling detection at invoice time, which needs no extra entity.

Challenge: it is tempting to keep `parents` as-is and just add columns. Do not — the table is named for one of the several relations it will hold, and every report written against it will inherit that confusion.

### 3.4 Employee and staff model

**Proposal: `employees` replaces `teachers`; teaching becomes an assignment, not an identity.**

```
employees
  id, user_id (nullable — a driver may have no login),
  employee_code, department_id, designation_id,
  employment_type: permanent | contract | probation | part_time | visiting,
  date_of_joining, date_of_leaving,
  status: applicant | onboarding | active | on_leave | notice_period | exited,
  reporting_to_id, qualification, experience_years
```

- **A teacher is an employee whose designation is teaching** and who appears in `class_subject_teacher`. Drivers, accountants, librarians, lab assistants and security staff are employees too, and Transport and HR both need them.
- **`user_id` is nullable.** Not every employee gets a login. Forcing one creates dormant accounts, which are a security liability.
- **Existing `teachers` rows migrate to `employees`** with designation "Teacher"; `class_subject_teacher.teacher_id` and `timetable_slots.teacher_id` become `employee_id`. This is a mechanical migration and should be done early, before HR is built, because every later table referencing staff would otherwise point at the wrong parent.

**Recommended: do NOT introduce a separate `persons` supertype** unifying students, guardians and employees, despite the theoretical appeal. It is a real pattern in large ERPs, but here it would add a join to nearly every query to serve a genuinely rare case (a teacher whose child studies at the school). Handle that case with a nullable cross-link (`guardians.employee_id`) instead. **Decided (§0.7): no shared supertype.**

### 3.5 Role-based access control and permissions

**Proposal: replace four hardcoded roles with a modelled permission system, keeping the service-layer enforcement that already exists.**

```
roles          permissions              role_permissions   user_roles
  id, code       id, code                 role_id            user_id
  name           ("fees.invoice.create")  permission_id      role_id
  is_system      module, action                              scope_type
  description    description                                 scope_id
```

Three layers, and they must stay distinct — conflating them is the usual way permission systems become unmaintainable:

1. **Authentication** — who are you (already exists, `deps.get_current_user`).
2. **Permission** — may this role perform this action at all (`fees.invoice.void`). Coarse, checked at the route.
3. **Scope** — over *which rows* (this section, this department, this year). Fine, checked in the service layer. **This is what `scoping.py` already does correctly** and it should keep doing it; only the inputs change from `user.role` to the user's resolved role-and-scope set.

Scope types: `global`, `academic_year`, `class_section`, `department`, `self`. A Class Teacher is not a separate role — it is the `teacher` role plus a `class_section`-scoped grant.

Indicative roles a real school needs: Super Admin, Principal, Vice Principal, Admin Officer, Admission Officer, Accountant, Fee Collector, Exam Controller, HR Manager, Transport Manager, Librarian, Class Teacher, Subject Teacher, Student, Guardian, Auditor (read-only, everything).

Two rules worth fixing now:
- **Permissions are additive only.** No "deny" rules. Deny-overrides systems are where permission bugs hide, and no school requirement needs them.
- **A read-only role must be genuinely read-only,** enforced by permission checks rather than by hiding buttons. The Auditor role is the test case for whether the model is real.

### 3.6 Audit logging

**Proposal: an append-only `audit_log`, written in the service layer, never truncated.**

```
audit_log
  id, occurred_at, actor_user_id, actor_role, ip, user_agent,
  entity_type, entity_id, action: create|update|delete|status_change|
                                  login|export|print|void,
  before (JSONB), after (JSONB), reason (text, required for some actions),
  academic_year_id, request_id
```

- **Not everything is audited.** Auditing every read produces noise nobody reads. Audit: money, marks, permissions, student status changes, document access, exports, and logins. Explicitly decide the list rather than letting it grow by accident.
- **Some actions require a typed reason** before they commit: voiding an invoice, changing a published mark, striking off a student, reopening a closed year. The reason field is the point of the audit entry, not the timestamp.
- **Add `created_by` / `updated_by` to `TimestampedBase`** as well. The audit log answers "what happened"; the row columns answer "who owns this record" cheaply, without a join.
- Audit rows are written by services, not by database triggers, because the actor is an application concept. This does mean a direct SQL edit bypasses the audit — accepted, and mitigated by restricting production database access.

### 3.7 Soft deletion

**Proposal: replace `is_active` with explicit lifecycle status per entity, and reserve deletion for genuine mistakes.**

Three different things are currently one boolean:
- **Lifecycle transition** (student left, employee resigned) → an entity `status` value. The record stays, fully queryable, and is *excluded from operational lists by default but included in historical reports*.
- **Created in error** (duplicate student entered twice) → `deleted_at` + `deleted_by` + `delete_reason`. Excluded everywhere except audit.
- **Access revoked** (portal login disabled, person still enrolled) → `users.is_active`, which keeps its current meaning and *only* that meaning.

The rule that fixes the current `roster()` defect: **every query that lists people goes through a shared, tested helper that applies the status filter.** The defect exists because the filter was a convention rather than a code path. A convention will be forgotten again at ERP scale; a single function will not.

### 3.8 Document management

**Proposal: one polymorphic `documents` table plus object storage. This is a prerequisite for Admission, not a later enhancement.**

```
documents
  id, owner_type (student|application|employee|vehicle|guardian),
  owner_id, doc_type_id, file_key (object storage), file_name,
  mime_type, size_bytes, checksum,
  uploaded_by, uploaded_at,
  verification_status: pending | verified | rejected | resubmit_required,
  verified_by, verified_at, rejection_reason,
  expires_on (for licences, insurance, medical certificates),
  is_confidential
```

- **Files never go in the database.** Object storage (S3-compatible), with the row holding the key.
- **The browser never gets a permanent public URL.** Access is via short-lived signed URLs issued after a permission check — otherwise a leaked link exposes a child's birth certificate indefinitely.
- **`doc_type` is configurable data, not an enum,** because required-document lists change by class, by category and by state regulation.
- **Expiry matters for compliance:** vehicle insurance, driver licences and fitness certificates expiring is an operational alert, and Transport depends on it.
- Deleting a document is a soft delete with reason. Storage objects are removed only by a retention job, never by the request that "deleted" it.

### 3.9 Financial transaction integrity

The largest redesign in this document. **Proposal: a proper billing model with allocation-based payments.**

```
fee_heads          fee_plans              invoices              payments
  id, name           id, academic_year_id    id, enrolment_id      id, payer,
  code               class/stream/category   academic_year_id      amount, method,
  type: recurring|   applicability           period                received_at,
        one_time|  fee_plan_items            invoice_no (sequence) instrument_ref,
        optional     fee_head_id, amount,    status                gateway_txn_id,
  is_refundable      frequency, due_rule     total, paid, balance  idempotency_key
  gl_code                                  invoice_lines           receipt_no
                   concessions               invoice_id,         payment_allocations
                     student/criteria based  fee_head_id,          payment_id,
                     amount or percent       amount, discount      invoice_line_id,
                     approved_by             tax?                  amount
```

Non-negotiable rules:
1. **Payments allocate to invoice lines; they do not "pay an invoice".** This is what makes part-payment, over-payment, advance payment and head-wise reporting all work with one mechanism. It is the single most important change in the fee model.
2. **Invoice balance is derived from allocations,** not stored as a mutable column — or if stored for query performance, it is stored as a maintained projection with a reconciliation job that proves it against the ledger.
3. **Nothing financial is ever hard-deleted or silently edited.** A wrong invoice is *voided* (with reason, audited) and reissued. A wrong payment is *reversed* by a contra entry, never by an UPDATE.
4. **Every payment carries an idempotency key.** The current `pay()` has none; a retried request can double-charge. This becomes urgent the moment a real payment gateway is introduced.
5. **Receipt and invoice numbers come from a database sequence with a locked counter,** not `max(seq)+1` computed in Python. The current implementation races under concurrency and produces a 500 on collision. Financial document numbers must be gapless per year — a school's auditor will ask about gaps.
6. **Concessions are approved records, not ad-hoc discounts typed into an amount box.** Who approved a fee waiver is exactly the question an audit asks.
7. **Reconciliation is a first-class screen,** not a report: gateway settlements versus recorded payments, with a visible unmatched queue.

**Locked fee rules for v1 (§0.6):**

| Rule | Value |
|---|---|
| Billing frequency | Monthly |
| Invoicing level | Per student (not per family) |
| Sibling concession | 10%, applied to siblings sharing a primary guardian |
| Late fee trigger | Invoice 5 days past due |
| Late fee amount | ₹300 at day 5, then +₹100 per further day |
| Late fee cap | 50% of the invoice amount |
| Refunds | None |
| Carry-forward of dues | None across academic years |
| Non-payment consequence | Report card and Transfer Certificate withheld until cleared |
| Payment gateway | Deferred to V2 — offline collection recorded manually |

Every one of these is a configuration value per school, not a constant in code. The
late-fee cap in particular exists because ₹100/day uncapped exceeds a monthly fee
within two months.

Challenge to a likely proposal: it will be suggested that the existing `fee_invoices`/`fee_payments` tables be extended with a few columns. **This will not work** — the `UNIQUE` on `fee_payments.invoice_id` is the model's core assumption, and the absence of fee heads means transport fees have nowhere to go. This is a rebuild with a data migration, and it is better done in Phase 3 than retrofitted in year two.

### 3.10 Notifications and communication

**Proposal: an outbox with delivery records, channel-agnostic from the start.**

- A domain event (invoice generated, absence marked, result published) creates a **message**, which fans out into **message_recipients**, which are dispatched per channel and produce **delivery_receipts**.
- **Sending happens in a worker, never in the request.** A teacher marking 40 absences must not wait on an SMS gateway, and a gateway timeout must not fail the attendance save.
- **Delivery is evidence.** "We informed the parent" is a claim a school makes to parents and sometimes to authorities; it needs a record with a status and a timestamp, not a fire-and-forget call.
- **Per-guardian channel preferences and quiet hours** are required, not optional — schools get complaints about 6am SMS.
- **Templates are data with variables,** versioned, so the exact text sent last March can be reproduced.
- SMS costs money per message. **A cost estimate before a bulk send** is a real product requirement, and so is a send log the school can audit against its SMS bill.

### 3.11 Reporting and analytics

**Proposal: separate operational reads from analytical reads early, but do not build a warehouse.**

- Operational lists (today's absentees, pending fees) are indexed queries against the transactional tables.
- Analytical aggregates (attendance trends, collection efficiency by month, year-on-year performance) run against **pre-computed summary tables** refreshed by scheduled jobs.
- Reason: the v0 dashboard already taught this lesson expensively — the N+1 fix (8.58s → 0.93s in production, recorded as BLUEPRINT §19 #21) happened because per-row computation was acceptable on localhost and fatal over a network. At ERP data volumes, computing analytics on read will reproduce that failure at a larger scale.
- **Every report is exportable** (CSV/XLSX/PDF) and every export is audited — reports contain children's personal data.
- **Report definitions should be data where practical** (saved filters, scheduled email delivery) so that a new management question does not require a deployment.

### 3.12 Search, filtering and data validation

- **One global search** across students, guardians, applications and employees, respecting permissions. This is the primary navigation tool in a real ERP; office staff search far more than they browse.
- Every list: server-side pagination, sortable columns, saved filters, and consistent query parameters across all endpoints. The current inconsistency (only students paginate) becomes unusable at scale.
- **Validation lives in three places, deliberately:** Pydantic schemas at the API boundary (shape and type), service functions (business rules that need database state), and database constraints (invariants that must hold regardless of code path). The last of these is what actually protects the data, and v0 already does it well.
- **Indian-context validation rules** must be explicit: phone numbers, Aadhaar handling (see §15 — storing it at all is a decision, not a default), age-on-cut-off-date for admission eligibility, and academic year format.

### 3.13 Multi-module relationships

Two rules to keep the module graph from becoming a knot:

- **Foundation entities are shared; module entities are not.** Anything in Admission that Fees needs must be promoted into a foundation entity (student, enrolment) rather than read across module boundaries. Modules read foundation data freely; they do not reach into each other's tables.
- **Cross-module effects go through events, not direct calls,** where the effect is asynchronous or optional. Admission creating a student is synchronous and direct. Attendance triggering an absence SMS is an event. Getting this wrong in the direction of direct calls produces a system where marking attendance can fail because the SMS provider is down.

### 3.14 Future scalability

Honest scale assessment: a single school of 2,000 students generates roughly 400,000 attendance rows and 24,000 invoices per year. **This is small.** A single well-indexed PostgreSQL instance handles it comfortably for a decade. The scaling risks here are not row counts:

- **Report generation** (1,200 report card PDFs in one afternoon) — needs a worker, not a bigger database.
- **Bulk communication** (5,000 SMS at exam results) — needs a queue with rate limiting.
- **Concurrent fee payment at deadline** — needs correct locking and idempotency, which §3.9 provides.
- **Multi-school** — confirmed (§0.2), so `school_id` lands in Part 1 rather than being retrofitted.

Resist premature distribution. Microservices, sharding and read replicas would
all be over-engineering for this workload and would multiply the operational burden on
a small team.

### 3.15 Multi-tenancy and per-school customization

**Tenancy.** One deployment, one database, `school_id` on every table, enforced by a
tenant filter in the service layer rather than remembered per query. A tenant is one
independent school; branches are out of scope (§0.2b). `users.login_id` becomes unique
per school, not globally.

**Customization is a four-level ladder, and almost everything a school asks for stops
at the first three:**

| Level | Mechanism | Examples |
|---|---|---|
| 1 | **Settings** — typed key/value per school | Fee amounts, late-fee rule, grading scale, academic year dates, branding, payroll component rates |
| 2 | **Custom fields** — school-defined attributes on students, guardians, employees, applications | "Father's occupation", "Bus pass number", "Previous board roll no" |
| 3 | **Feature flags** — modules and workflow steps on or off | Transport disabled; admission with 5 stages instead of 7; payroll off |
| 4 | **Plugins** — per-school code | Tally export, biometric device sync, a bespoke module |

Levels 1–3 are built in Part 1 because a multi-tenant product needs them regardless.
**Level 4 is deliberately not built yet (§0.2c).** What *is* built now are the seams:

- a **module registry** — modules declare themselves rather than being hardcoded in a list,
- **defined hook points** at the events a plugin would want (student enrolled, invoice
  generated, payment received, result published, attendance marked),
- **no assumption anywhere that the module set is fixed**, in navigation, permissions or
  reporting.

Adding a plugin runtime later then slots into existing seams. Building the runtime now
would consume the whole of Part 1 and would be designed against zero real plugin
requirements — which is how you build the wrong plugin system and rebuild it after the
first real request.

### 3.16 Payroll configurability

Payroll is built as **components, not rules**. A salary component is a row:
`code`, `name`, `type` (earning | deduction | employer contribution), `calculation`
(fixed | percent-of-basic | percent-of-gross | slab | formula), `value`, `taxable`,
`statutory`, `active`. A school assembles its own salary structure from components and
sets its own rates; the system ships no hardcoded percentage.

Default component set for a Lucknow private CBSE school (all editable, all disableable):

| Component | Type | Default rule |
|---|---|---|
| Basic | earning | 50% of gross |
| HRA | earning | 40% of basic (non-metro) |
| Conveyance | earning | fixed ₹1,600 |
| Special Allowance | earning | balancing figure |
| DA | earning | **disabled by default** — most private schools do not pay it |
| PF (employee) | deduction | 12% of basic |
| PF (employer) | employer contribution | 12% of basic |
| ESI (employee) | deduction | 0.75%, applies only when gross ≤ ₹21,000 |
| Professional Tax | deduction | **disabled by default** — Uttar Pradesh is understood not to levy it (§0.B, verify before writing payroll) |
| TDS | deduction | slab |
| Loss of Pay | deduction | gross ÷ working days × absent days |

---

## 4. Domain and entity model

### 4.1 Layered view

```
┌─ FOUNDATION ────────────────────────────────────────────────────┐
│  academic_years  ·  school/settings  ·  documents  ·  audit_log  │
│  users  ·  roles/permissions  ·  number_sequences  ·  addresses  │
└─────────────────────────────────────────────────────────────────┘
        │                    │                      │
┌─ PEOPLE ──────────┐ ┌─ ACADEMIC STRUCTURE ──┐ ┌─ STAFF ─────────┐
│ students          │ │ class_sections        │ │ employees       │
│ enrolments  ◄─────┼─┤ subjects              │ │ departments     │
│ guardians         │ │ class_subject_offering│ │ designations    │
│ student_guardian  │ │ class_subject_teacher │ │ contracts       │
└───────────────────┘ └───────────────────────┘ └─────────────────┘
        │                    │                      │
┌─ OPERATIONAL MODULES ───────────────────────────────────────────┐
│ Admission │ Attendance │ Timetable │ Examinations │ Fees │       │
│ Transport │ HR/Payroll │ Communication │ Homework             │
└─────────────────────────────────────────────────────────────────┘
        │
┌─ DERIVED ───────────────────────────────────────────────────────┐
│  summary tables  ·  saved reports  ·  dashboards  ·  exports     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 The spine

Almost every operational query in the ERP walks this path:

```
academic_year → class_section → enrolment → student → guardian
                                    │
        ┌───────────────┬───────────┼───────────────┬──────────────┐
    attendance       marks      invoices      transport_       timetable
                                              assignment        (via section)
```

The single most important consequence: **`enrolment_id` is the join key for year-scoped facts, and `student_id` is the join key for lifetime facts.** Getting this distinction wrong in any one table reintroduces the problem in §2.5(2) locally.

### 4.3 Entity inventory by module

| Module | Core entities | Reuses from foundation |
|---|---|---|
| Admission | `admission_cycles`, `enquiries`, `applications`, `application_guardians`, `application_documents`, `assessments`, `interviews`, `admission_offers`, `waitlist_entries` | `academic_years`, `documents`, `class_sections`, `number_sequences` |
| Student/Academic | `students`, `enrolments`, `guardians`, `student_guardian`, `promotions`, `transfer_certificates` | `documents`, `audit_log`, `addresses` |
| HR/Recruitment | `employees`, `departments`, `designations`, `contracts`, `job_postings`, `candidates`, `leave_*`, `staff_attendance`, `payroll_*` | `users`, `documents`, `academic_years` |
| Examinations | `assessment_schemes`, `exam_terms`, `exams`, `exam_schedule`, `marks`, `grading_scales`, `report_card_*`, `co_scholastic_marks` | `enrolments`, `class_subject_offering` |
| Fees | `fee_heads`, `fee_plans`, `fee_plan_items`, `concessions`, `invoices`, `invoice_lines`, `payments`, `payment_allocations`, `adjustments`, `refunds`, `fines` | `enrolments`, `number_sequences`, `audit_log` |
| Transport | `vehicles`, `drivers`, `routes`, `route_stops`, `transport_assignments`, `vehicle_documents` | `employees`, `documents`, `fee_heads`, `enrolments` |
| Timetable | `periods`, `timetable_versions`, `timetable_slots`, `teacher_availability`, `substitutions`, `academic_calendar`, `holidays` | `class_sections`, `employees`, `subjects` |
| Attendance | `attendance`, `attendance_sessions`, `leave_requests` (student) | `enrolments`, `academic_calendar` |
| Communication | `message_templates`, `messages`, `message_recipients`, `delivery_receipts`, `notification_preferences`, `device_tokens` | `users`, `guardians`, `class_sections` |
| Reports | `saved_reports`, `report_schedules`, summary tables | everything, read-only |
| Administration | `roles`, `permissions`, `role_permissions`, `user_roles`, `settings`, `audit_log` | `users` |

---

## 5. Module specifications

Each module is specified against the same ten points: purpose, real-world workflow, screens, fields and forms, entities, relationships, statuses, roles, validations and business rules, and reports/KPIs.

---

### 5.1 ADMISSION — specified in depth

Admission is the module most often reduced to an "Add Student" form, and doing so is the difference between a demo and an ERP. In a real school, admission is a **sales-and-selection pipeline that runs for six months before the student exists**, involves people who are not yet in the system, handles money before there is a fee account, and must produce a defensible record of why one child was admitted and another was not.

#### 5.1.1 Purpose

Convert an unknown enquirer into an enrolled student, while:
- capturing every enquiry so the school can measure and improve conversion,
- collecting and verifying documents before a decision, not after,
- recording assessment and interview evidence for each applicant,
- making the admission decision auditable and defensible,
- collecting admission fees safely,
- and creating the student, enrolment, guardians and fee assignment **in one atomic operation** at the end.

#### 5.1.2 Real-world workflow

```
  ENQUIRY ──► APPLICATION ──► DOCUMENT ──► ASSESSMENT ──► INTERVIEW ──► DECISION ──► FEE ──► ENROLMENT
                              VERIFICATION    /TEST                                   PAYMENT
     │              │              │             │            │            │          │         │
  walk-in,      form filled,   originals      written      parent +    admit /     admission  student +
  phone,        fee paid,      checked        test or      child       waitlist /  fee +      enrolment
  website,      number         against        readiness    meeting     reject      first      created,
  referral      issued         checklist      check                                instalment portal access
```

The seven realities that shape the design:

1. **Most enquiries never become applications.** A school takes 800 enquiries to fill 120 seats. Enquiry is a genuine funnel stage with follow-up tasks, not a formality, and conversion rate by source is a number the management actually asks for.
2. **The applicant is not a user.** They have no login, no student record, and may never get one. Every Admission entity must stand alone without depending on `students` or `users`.
3. **Documents arrive late and incomplete.** The workflow must proceed with a partial document set and block only at defined gates. A design that requires all documents at application will be worked around by staff entering junk.
4. **Assessment differs sharply by age.** Nursery admission is a parent interaction and an informal readiness observation; Class 6 is a written test with marks; Class 11 is previous-board-result-driven with a stream choice. One rigid "test marks" field fits none of them well.
5. **Decisions are made in batches against seat capacity,** not one at a time. The Admission Officer sits with a ranked list per class and allocates seats — so the system needs a comparison view, not just a per-application decision button.
6. **A waitlist is a real, ordered, offer-expiring queue.** When an admitted child does not pay by the deadline, the seat returns to the pool and the next waitlisted applicant is offered it. This automation is a large part of the module's value.
7. **Sibling and staff-ward priority are real policies** with real fee concessions attached, and they must be visible at decision time, not discovered afterwards.

#### 5.1.3 Main screens

| # | Screen | Purpose |
|---|---|---|
| 1 | **Admission Dashboard** | Funnel by stage, seats filled vs capacity per class, today's interviews and tests, applications awaiting action, conversion by source |
| 2 | **Enquiry List** | Filterable/searchable enquiry register with follow-up status and owner |
| 3 | **Enquiry Form** | Quick capture — designed for a receptionist on the phone, under 60 seconds |
| 4 | **Enquiry Detail** | Interaction log, follow-up scheduling, convert-to-application action |
| 5 | **Application List** | The main working queue: filter by class, stage, cycle, document status, priority flags |
| 6 | **Application Form (multi-step)** | The comprehensive entry form — §5.1.4 |
| 7 | **Application Detail (360°)** | All tabs for one applicant: details, guardians, documents, assessment, interview, fees, decision, timeline |
| 8 | **Document Verification** | Checklist per applicant, upload, verify/reject with reason, resubmission tracking |
| 9 | **Assessment Scheduling** | Assign applicants to test slots/rooms, generate hall tickets, capacity per slot |
| 10 | **Assessment Marks Entry** | Per-slot roster, subject-wise marks, absent marking |
| 11 | **Interview Scheduling & Panel** | Slot allocation, panel assignment, structured feedback capture |
| 12 | **Selection / Merit View** | Ranked comparison per class against seats, side-by-side scoring, batch decisions |
| 13 | **Offer Management** | Issue offers, set expiry, track acceptance, auto-release lapsed seats |
| 14 | **Admission Fee Collection** | Collect application/admission fee, issue receipt, link to the applicant |
| 15 | **Enrolment Conversion** | The final step: applicant → student, with section allocation and preview |
| 16 | **Waitlist Management** | Ordered list per class, promote on decline, expiry rules |
| 17 | **Admission Cycle Setup** | Define cycle, classes, seats, fees, required documents, key dates, eligibility rules |
| 18 | **Admission Reports** | Funnel, source, demographics, seat utilisation, rejection analysis |

#### 5.1.4 The comprehensive application form

Multi-step, saveable as draft at every step, with a visible completeness indicator. Steps 1–3 are mandatory to submit; the rest may complete later, gated per §5.1.9.

**Step 1 — Applicant details**
`first_name`*, `middle_name`, `last_name`*, `date_of_birth`*, `gender`*, `nationality`, `religion`, `caste_category` (General/OBC/SC/ST/EWS), `mother_tongue`, `blood_group`, `aadhaar_number` (see §15 — collect only if policy requires), `place_of_birth`, `photograph`, `identification_marks`, `is_single_child`, `is_rte_candidate`

**Step 2 — Admission sought**
`admission_cycle`*, `academic_year`* (derived from cycle), `class_applying_for`*, `stream` (classes 11–12), `second_language_preference`, `optional_subject_preference`, `preferred_section` (a request, never a guarantee), `admission_category` (General / Sibling / Staff Ward / Management / RTE / Sports / Alumni Child), `transport_required` (boy/girl), `hostel_required` (if applicable)

**Step 3 — Parents and guardians** (repeatable; father, mother, guardian)
Per guardian: `relation`*, `full_name`*, `date_of_birth`, `qualification`, `occupation`, `designation`, `organisation`, `annual_income_band`, `office_address`, `mobile`*, `alternate_mobile`, `email`, `aadhaar` (optional), `photograph`, `is_primary_contact`*, `is_emergency_contact`, `is_authorised_for_pickup`, `is_school_alumnus`, `is_school_staff` (→ triggers staff-ward verification)
Form rules: at least one guardian required; exactly one primary contact; if the child does not live with both parents, a `custody_note` and supporting document become required.

**Step 4 — Siblings and family**
`has_sibling_in_school`* → if yes: sibling search against enrolled students (`admission_no` / name lookup, **not** free text), auto-links the family and flags sibling concession eligibility for the Fees module. Also: other siblings not in the school (name, age, school), `family_size`.

**Step 5 — Address and contact**
Current address (`line1`*, `line2`, `city`*, `district`, `state`*, `pincode`*, `landmark`), permanent address with a "same as current" toggle, `residence_type` (owned/rented), `distance_from_school_km` (used for transport route suggestion), `nearest_bus_stop`.

**Step 6 — Previous school** (mandatory for Class 1 and above)
`school_name`*, `board` (CBSE/ICSE/State/IB/Other), `medium_of_instruction`, `last_class_attended`*, `last_class_result` / `percentage` / `grade`, `year_of_passing`, `school_address`, `city`, `reason_for_leaving`*, `tc_number`, `tc_date`, `tc_document`, `previous_marksheet`, `was_ever_detained`, `disciplinary_record_declaration`.

**Step 7 — Medical and special needs**
`blood_group`, `known_allergies`, `chronic_conditions`, `regular_medication`, `physical_disability` + `disability_certificate`, `learning_needs` / `special_education_requirement`, `vision_hearing_notes`, `emergency_doctor_name_and_phone`, `vaccination_record`, `consent_for_emergency_treatment`*.
This section is confidential and must be permission-gated separately from the rest of the application (§15).

**Step 8 — Documents upload**
Driven by the cycle's configured checklist. Typical: birth certificate*, transfer certificate (class ≥ 1)*, previous report card*, Aadhaar (child), Aadhaar (parents), passport photographs*, caste/category certificate (if claimed)*, income certificate (if EWS/RTE claimed)*, medical certificate, disability certificate (if declared), address proof*, migration certificate (other boards), sibling proof (if sibling category claimed), staff proof (if staff-ward claimed).
Each: upload, `original_seen` flag, verification status, verifier, reason on rejection.

**Step 9 — Declarations and consent**
`information_accuracy_declaration`*, `school_rules_acceptance`*, `fee_policy_acknowledgement`*, `photo_media_usage_consent` (explicit yes/no — not a pre-ticked box), `data_processing_consent`*, `transport_terms` (if opted), `signature_of_parent`, `date`, `place`, `how_did_you_hear_about_us` (source attribution, feeds the funnel report).

#### 5.1.5 Entities

```
admission_cycles      id, academic_year_id, name, status, starts_on, ends_on,
                      application_fee, late_fee, allow_online_applications

cycle_class_config    cycle_id, class_name, stream, total_seats, reserved_seats(by
                      category), min_age_on, max_age_on, requires_test, requires_interview,
                      required_document_types[]

enquiries             id, cycle_id, enquirer_name, mobile*, email, child_name,
                      child_dob, class_of_interest, source, status, assigned_to,
                      next_follow_up_on, converted_application_id

enquiry_interactions  enquiry_id, occurred_at, channel, notes, by_user_id, outcome

applications          id, cycle_id, application_no (sequence), class_applying_for,
                      stream, status, admission_category, priority_flags,
                      submitted_at, applicant demographic fields..., source,
                      created_by, current_stage, completeness_pct

application_guardians  application_id, relation, name, mobile, email, occupation,
                      income_band, is_primary, is_alumnus, is_staff, employee_id?

application_addresses  application_id, type(current|permanent), lines, city,
                      state, pincode, distance_km

application_previous_school   application_id, school_name, board, last_class,
                              result, tc_no, reason_for_leaving

application_medical   application_id, blood_group, allergies, conditions,
                      disability, special_needs, emergency_contact  [confidential]

application_siblings  application_id, student_id (if enrolled), name, age, school

application_documents application_id, doc_type_id, document_id → documents,
                      original_seen, status, verified_by, verified_at, reason

assessments           id, application_id, assessment_type, scheduled_at, venue,
                      seat_no, status, total_marks, obtained_marks, is_absent,
                      evaluated_by, remarks
assessment_subjects   assessment_id, subject, max_marks, obtained

interviews            id, application_id, scheduled_at, venue, panel_member_ids[],
                      status, child_rating, parent_rating, structured_scores(JSONB),
                      recommendation: strong_admit|admit|waitlist|reject,
                      notes, conducted_by

admission_decisions   id, application_id, decision, decided_by, decided_at,
                      reason*, seat_category, conditions

admission_offers      id, application_id, offered_at, expires_on, offer_amount,
                      status: issued|accepted|declined|expired|withdrawn,
                      accepted_at, released_at

waitlist_entries      id, cycle_id, class_name, application_id, rank,
                      status: waiting|offered|converted|lapsed|withdrawn

application_payments  id, application_id, purpose(application_fee|admission_fee),
                      amount, method, receipt_no, paid_at, idempotency_key,
                      gateway_txn_id, status
```

#### 5.1.6 Relationships with other modules

| Direction | Relationship |
|---|---|
| Admission → **Student/Academic** | On conversion, creates `students`, `enrolments`, `guardians`, `student_guardian`, and migrates `application_documents` to the student. This is the module's terminal output. |
| Admission → **Fees** | Admission category and sibling/staff flags determine the fee plan and concession assigned at enrolment. Admission fee payments must be traceable into the fee ledger. |
| Admission → **Transport** | `transport_required` and address/distance seed a transport assignment request, not an assignment. |
| Admission → **Communication** | Every stage transition is a notification trigger — acknowledgement, document reminder, hall ticket, interview call, offer letter, expiry warning. |
| Admission ← **Academic structure** | Seat capacity is per `class_section` per `academic_year`; sections must exist for next year before offers are issued. |
| Admission ← **HR** | Staff-ward verification checks `employees`. |
| Admission → **Reports** | Funnel, source ROI, demographic mix, seat utilisation, rejection reasons. |

#### 5.1.7 Statuses and lifecycle

**Enquiry:** `new → contacted → interested → application_form_issued → converted` with terminal `not_interested`, `lost_to_competitor`, `invalid`.

**Application:**
```
draft → submitted → under_document_verification → documents_verified
      → assessment_scheduled → assessment_completed
      → interview_scheduled → interview_completed
      → decision_pending → { admitted | waitlisted | rejected }
      → offer_issued → offer_accepted → fee_paid → enrolled
```
Terminal/exception states: `withdrawn_by_parent`, `offer_expired`, `rejected`, `cancelled_after_admission`, `documents_rejected`.

Rules on transitions: forward transitions are permission-gated; **backward transitions are allowed but always audited with a reason** (real admissions offices do reopen decisions, and a system that forbids it gets bypassed with a second application record). `enrolled` is terminal and irreversible from within Admission — undoing it is a Student-module withdrawal, not an admission edit.

**Offer:** `issued → accepted | declined | expired | withdrawn`.
**Document:** `pending → submitted → verified | rejected → resubmitted`.

#### 5.1.8 Roles

| Role | Capability |
|---|---|
| Receptionist / Front Desk | Create and follow up enquiries; cannot see decisions or scores |
| Admission Officer | Full pipeline: applications, scheduling, offers, waitlist |
| Document Verifier (clerk) | Verify/reject documents only |
| Assessor / Teacher | Enter marks for assigned assessment slots only |
| Interview Panel Member | Enter structured feedback for assigned interviews only; sees no other panelist's score until submitted |
| Principal / Vice Principal | Final decisions, batch selection, override with reason |
| Accountant | Admission and application fee collection, refunds |
| Admin Officer | Cycle setup, seat configuration, document checklists |
| Auditor | Read-only across the module |

#### 5.1.9 Validations and business rules

**Eligibility and identity**
1. Age is validated against the class's `min_age_on` / `max_age_on` **cut-off date**, not against today. Out-of-range requires an explicit, audited management override with a reason.
2. Duplicate detection on submission: same child name + DOB, or same guardian mobile, raises a soft warning with the matching records shown. Never a hard block — genuine twins exist, and blocking creates workarounds.
3. A rejected applicant may reapply in a later cycle; the system links the applications rather than hiding the history.

**Documents and gates**
4. An application cannot move to `decision_pending` until all documents marked **mandatory for that class and claimed category** are `verified`. Category-conditional documents (income certificate for EWS) are only required when the category is claimed.
5. A rejected document sets the application back to `under_document_verification` and notifies the guardian with the reason.
6. Sibling and staff-ward categories require verification against actual records (`students`, `employees`) before the priority is applied at selection. An unverified claim must not silently influence a decision.

**Assessment and interview**
7. Assessment marks cannot be entered before the scheduled datetime, and cannot exceed `max_marks`.
8. `is_absent` and a score of 0 are different states and must not be conflated — the same rule the existing marks module already gets right.
9. An interview panel member sees only their own scoring until submission, to keep panel scores independent.
10. Editing a submitted assessment or interview score requires a reason and is audited.

**Decision and seats**
11. Admissions cannot exceed `total_seats` for the class **without an explicit over-allocation approval** by a permitted role, with reason. Silent over-admission is one of the more damaging failures possible here.
12. Category-reserved seats are tracked separately, and a General-category admission cannot consume a reserved seat.
13. Every decision requires a `reason` — including admits. This is what makes the process defensible if challenged.
14. An offer must have an expiry. On expiry the seat automatically returns to the pool and the highest-ranked waitlisted applicant is offered it (subject to a configurable manual-confirm setting).

**Money and conversion**
15. Application fee is payable at submission and is **non-refundable**; admission fee is refundable per policy, and the policy must be recorded on the cycle, not decided ad hoc.
16. Conversion to a student runs as **one database transaction**: create student, enrolment, guardians, links, fee assignment, portal credentials, document migration. Partial conversion — the failure mode that produces a student with no fee account — must be impossible.
17. `admission_no` is allocated from a gapless sequence at conversion, never at application.
18. Section allocation at conversion respects section capacity and may be automatic (balance by count/gender/performance) or manual, but is always previewable before commit.
19. A student created by conversion retains an immutable pointer to the originating application for audit.

#### 5.1.10 Reports and KPIs

- **Funnel:** enquiries → applications → tested → interviewed → admitted → enrolled, with conversion percentage at each step and drop-off analysis
- **Source effectiveness:** conversion and cost per admission by source (walk-in, referral, digital, hoarding, alumni)
- **Seat utilisation:** filled vs capacity per class and category, waitlist depth, offer-acceptance rate, offer-expiry rate
- **Cycle time:** median days per stage; the stage where applications stall
- **Demographics:** gender ratio, category mix, feeder-school analysis, geographic distribution of admissions
- **Rejection analysis:** reasons grouped, to expose whether the criteria are being applied consistently
- **Sibling and staff-ward share** of intake
- **Revenue:** application fee collected, admission fee collected vs expected, refunds
- **Comparison to prior cycles** on every one of the above — the number management actually asks for is "how are we doing versus last year at this date"

---

### 5.2 STUDENT / ACADEMIC MANAGEMENT

**1. Purpose.** Hold the authoritative record of every student across their entire time at the school, and manage the year-to-year academic structure they sit inside. This is the module every other module joins to.

**2. Real-world workflows.** Enrol (from Admission) → allocate section and roll number → maintain profile and guardians through the year → mid-year section transfer → issue certificates on request → year-end: publish results, promote/detain, roll over → handle transfer-out with a TC → maintain alumni.

**3. Main screens.** Student List (the ERP's most-used screen — search, filter by class/section/status/category/transport, saved filters, bulk actions) · Student 360° Profile (tabs: personal, guardians, enrolment history, attendance, marks, fees, transport, documents, communication log, timeline) · Add/Edit Student · Bulk Import · Class & Section Setup · Section Allocation · Subject Offering Setup · Promotion Workbench · Transfer Certificate issue · Certificate generation (bonafide, character, conduct) · Alumni register · Student ID card generation.

**4. Important fields.** Student: `admission_no`, name parts, `dob`, `gender`, `category`, `religion`, `mother_tongue`, `blood_group`, `house`, `is_rte`, photo, status. Enrolment: `academic_year`, `class_section`, `roll_no`, `joined_on`, `left_on`, `outcome`. Guardian links with relation and contact flags. Addresses. Documents.

**5. Entities.** `students`, `enrolments`, `guardians`, `student_guardian`, `addresses`, `promotions`, `transfer_certificates`, `student_status_history`, `class_sections`, `subjects`, `class_subject_offering`, `class_subject_teacher`, `houses`.

**6. Relationships.** Receives students from **Admission**. Supplies `enrolment_id` to **Attendance, Examinations, Fees, Transport**. Consumes **Timetable** for the student's schedule. Feeds **Communication** its recipient lists and **Reports** its denominators. Section structure comes from Academic setup, which **Timetable** and **Examinations** both depend on.

**7. Statuses.** Student: `enrolled → active → {promoted | detained | transferred_out | struck_off | passed_out} → alumni`; plus `suspended` (reversible) and `deleted` (created-in-error only). Enrolment: `active | completed | withdrawn`. Section: `planned | active | closed`.

**8. Roles.** Admin Officer (full), Principal (full + overrides), Class Teacher (own section, read + limited edit), Subject Teacher (read, own sections), Accountant (read, for fee context), Front Desk (read + contact update), Guardian (own children, read), Student (self, read).

**9. Validations and business rules.**
- Roll number unique within `(class_section, academic_year)` — enforced on `enrolments`, not `students`.
- A student has **exactly one active enrolment** per academic year. Enforce with a partial unique index; this is the constraint that keeps §3.2 honest.
- Section transfer mid-year **closes** the old enrolment row and opens a new one with a reason, so attendance and marks stay attached to the period they belong to. It must not mutate `class_section_id` in place — that is the v0 mistake at a smaller scale.
- Promotion is a **batch operation with a preview and a reversible run id**; it must never partially apply.
- Detained students keep the same class in the new year with a fresh enrolment and a new roll number.
- TC issue requires fee clearance (configurable) and sets the student `transferred_out` on the TC date.
- A student cannot be struck off with an unreconciled fee balance without an explicit financial write-off entry.
- Deactivating a student must remove them from operational rosters everywhere — the shared roster helper in §3.7 is what guarantees this.

**10. Reports/KPIs.** Strength by class/section/gender/category, with movement (joined, left, net) per month · retention and attrition rate by class · promotion/detention rate · alumni count by passing year · RTE and category compliance counts · demographic distribution · students with incomplete documents or profiles · sibling groups · new admissions versus withdrawals trend.

---

### 5.3 RECRUITMENT / HR

**1. Purpose.** Manage staff from job posting through exit: hiring, records, contracts, attendance, leave, and payroll. Today only `teachers` exists, with four fields; this is the module built most from scratch.

**2. Real-world workflows.** Department raises a vacancy → posting → applications → shortlist → demo class / written test → interview rounds → offer → document collection → onboarding → active service (leave, attendance, appraisal, increments) → exit (resignation, notice period, clearance, relieving letter, final settlement).

**3. Main screens.** HR Dashboard · Employee Directory · Employee 360° Profile · Add/Edit Employee · Department & Designation setup · Job Postings · Candidate Pipeline (kanban by stage) · Interview scheduling and scorecards · Offer management · Onboarding checklist · Staff Attendance (with biometric import) · Leave Types & Balances · Leave Requests & Approval queue · Substitution arrangement (links to Timetable) · Payroll Setup (salary components) · Payroll Run · Payslips · Appraisal cycles · Exit & clearance · Statutory reports.

**4. Important fields.** Employee: `employee_code`, personal details, `department`, `designation`, `employment_type`, `date_of_joining`, `reporting_to`, qualification, experience, subjects qualified to teach, bank account, PAN, UAN/PF, ESI, emergency contact, documents. Leave: type, from/to, half-day flag, reason, approver, status. Payroll: earnings and deduction components, LOP days, gross, net.

**5. Entities.** `employees`, `departments`, `designations`, `employment_contracts`, `employee_qualifications`, `job_postings`, `candidates`, `candidate_documents`, `interview_rounds`, `interview_scores`, `job_offers`, `leave_types`, `leave_balances`, `leave_requests`, `staff_attendance`, `salary_structures`, `salary_components`, `payroll_runs`, `payslips`, `appraisals`, `exit_records`.

**6. Relationships.** Supplies teachers to **Timetable**, **Examinations** (evaluators), **Attendance** (markers), **Admission** (assessors, panels) and **Transport** (drivers, attendants). Leave approval creates **Timetable** substitutions. Payroll is financially adjacent to **Fees** but must stay a separate ledger — mixing staff payroll into the student fee ledger would be a serious modelling error. Staff-ward admission verification reads `employees`.

**7. Statuses.** Employee: `applicant → offered → onboarding → active → {on_leave | notice_period} → exited`. Candidate: `applied → screened → shortlisted → interviewing → offered → {joined | declined | rejected}`. Leave: `draft → applied → approved | rejected | cancelled | withdrawn`. Payroll run: `draft → calculated → approved → paid → locked`.

**8. Roles.** HR Manager (full), Principal (approvals, all staff), Department Head (own department), Accountant (payroll only), Employee (self-service: own profile, leave, payslips), Auditor (read-only).

**9. Validations and business rules.**
- `employee_code` unique and never reused, even after exit.
- Leave cannot exceed the balance without an explicit approved exception; balances accrue per policy and carry forward per policy.
- Overlapping leave requests for one employee are rejected.
- Approving a teacher's leave must surface the affected timetable periods and require a substitution decision — approving leave that silently leaves classes unattended is the single most common real-world HR/timetable failure.
- A payroll run, once `approved`, is immutable; corrections are a supplementary run, never an edit.
- Salary information is permission-gated separately from the rest of the employee profile.
- An employee cannot be exited with pending clearance items or an active timetable allocation.
- Document expiry (teaching licence, police verification, medical) raises alerts before lapse.

**10. Reports/KPIs.** Headcount by department/type, sanctioned versus filled · attrition rate and reasons · time-to-hire and offer-acceptance rate by role · student:teacher ratio by class · staff attendance and punctuality · leave utilisation by type and department · substitution load per teacher · payroll cost per month and per department, cost per student · statutory: PF, ESI, TDS, professional tax registers · qualification and experience distribution · appraisal completion.

---

### 5.4 TESTS / EXAMINATIONS

**1. Purpose.** Define assessment schemes, conduct examinations, capture marks with integrity, compute results against a configurable grading scheme, and publish report cards. The existing `exams`/`exam_schedule`/`marks`/`grade_bands` is the strongest v0 module and is a genuine foundation here.

**2. Real-world workflows.** Define the year's assessment scheme (terms, weightages, scholastic vs co-scholastic) → schedule the exam and produce a datesheet → allocate rooms and seats → issue hall tickets → conduct → evaluate → enter marks → moderate → lock → compute results → generate report cards → publish to parents → analyse → conduct re-tests for absentees.

**3. Main screens.** Exam Dashboard · Assessment Scheme Setup (terms and weightages) · Grading Scale Setup · Exam Creation · Datesheet Builder (conflict-aware) · Room & Seating Allocation · Hall Ticket generation · Marks Entry (per exam/section/subject, keyboard-optimised grid) · Marks Verification & Moderation · Result Processing · Report Card Designer/Preview · Result Publication control · Re-test management · Answer-script/re-evaluation requests · Result Analysis (subject, section, teacher, trend).

**4. Important fields.** Exam: term, type, weightage, max marks, start/end. Schedule: class, subject, date, time, duration, room, max/pass marks. Mark: obtained, `is_absent`, `is_exempted`, grade (computed), remarks, entered_by, verified_by, locked_at. Report card: attendance summary, scholastic table, co-scholastic grades, class teacher remark, principal remark, result status.

**5. Entities.** `assessment_schemes`, `scheme_components`, `exam_terms`, `exams`, `exam_schedule`, `exam_rooms`, `seat_allocations`, `marks`, `mark_change_log`, `grading_scales`, `grade_bands`, `co_scholastic_areas`, `co_scholastic_marks`, `remarks`, `report_card_templates`, `report_card_publications`, `retests`.

**6. Relationships.** Reads `enrolments` and `class_subject_offering` for who sits which paper. Reads **Attendance** for the attendance line on the report card. Uses **HR** for evaluators and invigilators. Requires **Timetable**'s calendar to avoid clashing with holidays. Publication triggers **Communication**. Results drive **Student** promotion and feed **Reports**.

**7. Statuses.** Exam: `draft → scheduled → in_progress → evaluation → marks_locked → result_processed → published → archived`. Mark entry per subject: `pending → entered → verified → locked`. Student result: `pass | fail | compartment | absent | withheld` (withheld covers fee dues or malpractice, and is a real requirement).

**8. Roles.** Exam Controller (full), Principal (approve, publish, override), Subject Teacher (enter marks for own subject/section only, before lock), Class Teacher (view own section, add remarks), Admin (setup), Guardian/Student (published results only), Auditor (read-only).

**9. Validations and business rules.**
- Marks cannot exceed `max_marks`; negative marks rejected.
- **Absent, exempted and zero are three distinct states.** v0 already handles the absent/zero distinction correctly for report-card totals; the ERP must preserve that and add exemption.
- Marks entry closes at a deadline; entry after lock requires an Exam Controller override with a reason and is written to `mark_change_log` — **every post-lock change is audited without exception**.
- A subject with no marks is excluded from the total rather than counted as zero (existing v0 rule, correct, keep).
- Results cannot be published until every subject in the section is `locked`.
- Grading scale is versioned per academic year — changing it must not silently re-grade published historical report cards, which is the risk created by computing grades at read time (§2.2). **Report card publication snapshots the grade and the scale version used (decided, §0.8).** A published report card is a frozen document: reopening it months later shows exactly what was issued, even if a grade band was edited since. Live screens continue computing from `grade_bands`. This supersedes BLUEPRINT §7.5 for published documents only.
- Withholding a result for fee dues is a configurable policy, not hardcoded.
- Datesheet builder must reject two papers for the same section at the same time, and warn on a teacher invigilating two rooms at once.

**10. Reports/KPIs.** Result summary by class/section/subject · pass percentage and grade distribution · subject-wise average, highest, lowest, standard deviation · topper lists · failure and compartment analysis · teacher-wise result comparison (handle with care politically, but management asks for it) · progress of a student across terms and years · comparison against previous years · attendance-versus-performance correlation · consolidated tabulation sheet · board-format outputs.

---

### 5.5 FEES

**1. Purpose.** Define what each student owes, bill it, collect it through multiple channels, track dues, and produce financially defensible records. §3.9 covers the architecture; this covers the module.

**2. Real-world workflows.** Define fee heads and plans for the year → assign plans to students (by class/category, with concessions) → generate invoices for a period → notify → collect (cash, cheque, UPI, card, online gateway, bank transfer) → issue receipt → handle part payment and advance → apply late fines → chase defaulters → handle refunds and adjustments → reconcile with bank/gateway → close the period → report.

**3. Main screens.** Fee Dashboard (collection vs target, ageing, today's collection by mode) · Fee Head Setup · Fee Plan Setup · Student Fee Assignment · Concession Management (request → approve) · Invoice Generation (batch, with preview) · Invoice List and Detail · Fee Collection counter screen (fast, search-by-admission-no first) · Receipt print/reprint · Part-payment and instalment plans · Defaulter List with follow-up tracking · Fine configuration and waiver · Refunds · Adjustments/write-offs · Daily Collection Register (day-book) · Bank/Gateway Reconciliation · Fee reports · Period close.

**4. Important fields.** Fee head: name, code, type, refundable, GL code. Plan item: head, amount, frequency, due rule, applicable class/category. Invoice: number, enrolment, period, lines, total, concession, fine, paid, balance, due date, status. Payment: amount, mode, instrument details, received by, receipt number, idempotency key, gateway reference. Concession: type, value, reason, approver, validity.

**5. Entities.** As listed in §3.9, plus `fee_periods`, `instalment_plans`, `fine_rules`, `daybook_entries`, `bank_deposits`, `gateway_settlements`.

**6. Relationships.** Bills against `enrolments`, so a student who leaves mid-year stops being billed automatically. **Transport** contributes a fee head driven by route/stop. **Admission** determines the initial plan and concession. **Examinations** may withhold results on dues. **Communication** sends reminders and receipts. **Reports** consumes collection data. Payroll stays deliberately separate.

**7. Statuses.** Invoice: `draft → issued → partially_paid → paid | overdue → voided | written_off`. Payment: `initiated → success | failed | pending_confirmation → reversed`. Concession: `requested → approved | rejected → expired`. Refund: `requested → approved → paid`. Period: `open → closed → locked`.

**8. Roles.** Accountant (full), Fee Collector/Cashier (collect and receipt only — cannot void, waive or edit invoices), Principal (approve concessions, waivers, refunds), Admin Officer (setup), Guardian (own children: view, pay online, download receipts), Auditor (read-only), Transport Manager (read transport-head dues).

**9. Validations and business rules.**
- **Payments allocate to lines; the invoice balance is derived.** (§3.9 rule 1.)
- Payment amount must be positive; over-payment becomes a credit balance rather than being rejected — parents do round up.
- **Idempotency key required on every payment.** A duplicate key returns the original receipt rather than creating a second payment.
- Receipt numbers are gapless per financial year, from a locked sequence. Cancelled receipts keep their number and are marked cancelled — a gap is what an auditor asks about.
- Nothing financial is edited or deleted: void and reissue, or reverse with a contra entry.
- A cashier cannot void their own transaction; segregation of duties is the point.
- Concessions require approval before affecting an invoice; the approver is recorded.
- Fines apply by rule after the due date, and any waiver is an approved, audited exception.
- **A closed period is immutable.** Late entries go into the current open period with a reference to the original.
- Refunds only against actually received money, never against an unpaid invoice.
- Cash collection must be reconciled to a bank deposit; unreconciled cash beyond a threshold is an alert.

**10. Reports/KPIs.** Collection vs demand (day/month/year, class, head) · collection efficiency percentage · ageing of receivables (0-30/31-60/61-90/90+) · defaulter list with amounts and contact status · daily collection register by mode and by cashier · head-wise revenue · concession and waiver register (the report management scrutinises most) · advance and credit balances · refund register · projected versus actual annual revenue · bank/gateway reconciliation status · student-wise fee ledger.

---

### 5.6 TRANSPORT

**1. Purpose.** Operate the school bus service safely: vehicles, drivers, routes, stops, student assignments, transport fees, and compliance. Nothing for this exists in v0.

**2. Real-world workflows.** Register vehicles and their compliance documents → hire and record drivers/attendants → design routes and stops with timings → assign students to a stop → bill transport fees → run daily trips → handle route changes and breakdowns → track document expiry → handle incidents.

**3. Main screens.** Transport Dashboard · Vehicle Register · Vehicle Documents & Expiry alerts · Driver/Attendant Register · Route Setup · Stop Setup with timings · Route Map view · Student Transport Assignment (by stop, with capacity check) · Transport Fee Setup (by stop/distance/slab) · Daily Trip Log · Attendance-on-bus (optional) · Maintenance & fuel log · Incident register · Transport reports.

**4. Important fields.** Vehicle: registration number, type, capacity, model, ownership (owned/hired), insurance/fitness/permit/PUC with expiry, GPS device id. Driver: employee link, licence number and expiry, police verification, medical fitness, experience. Route: code, name, direction, vehicle, driver, attendant, distance, active days. Stop: sequence, name, landmark, pickup and drop time, fee slab, coordinates. Assignment: enrolment, route, stop, direction (pickup/drop/both), start and end date.

**5. Entities.** `vehicles`, `vehicle_documents`, `drivers`, `routes`, `route_stops`, `transport_assignments`, `transport_fee_slabs`, `trip_logs`, `maintenance_records`, `fuel_logs`, `incidents`.

**6. Relationships.** Drivers and attendants are **HR** employees. Assignment is against an `enrolment`, and generates a **Fees** line under a transport fee head — this is the dependency that cannot work until the fee-head redesign lands. Address and distance from **Student/Admission** drive stop suggestion. Route changes and delays notify through **Communication**. Student transport status appears on the Student 360°.

**7. Statuses.** Vehicle: `active | under_maintenance | grounded | retired`. Document: `valid | expiring_soon | expired`. Route: `planned | active | suspended | closed`. Assignment: `requested → active → suspended → ended`. Trip: `scheduled → started → completed | cancelled`.

**8. Roles.** Transport Manager (full), Admin Officer (setup), Accountant (transport fees), Class Teacher (read own students' details), Guardian (own child's route, stop, timing), Driver (own trip only, if given app access later), Auditor (read-only).

**9. Validations and business rules.**
- Students assigned to a route cannot exceed the vehicle's seating capacity — a hard block, not a warning. This is a child-safety rule and a legal one.
- **A vehicle with an expired insurance, fitness, permit or PUC cannot be assigned to an active route.** The system should refuse, not warn.
- A driver with an expired licence or missing police verification cannot be assigned. Police verification is a legal requirement for school transport in India.
- Stop timings within a route must be monotonically increasing; overlapping route timings for the same vehicle are rejected.
- Transport fee is computed from the assigned stop's slab and prorated on mid-year start or stop.
- Ending a transport assignment must stop future billing but preserve history.
- Document expiry raises alerts at configurable intervals (60/30/7 days) to the Transport Manager.
- One student may hold at most one active assignment per direction per period.

**10. Reports/KPIs.** Route utilisation (assigned vs capacity) · cost per route and per student (fuel + salary + maintenance vs transport fee collected) · vehicle document compliance dashboard, with anything expiring in 30 days front and centre · maintenance cost and downtime by vehicle · fuel efficiency trend · students by route and stop (the list a driver actually needs) · transport fee collection versus demand · incident log and trend · on-time performance if trip logging is used.

---

### 5.7 TIMETABLE

**1. Purpose.** Allocate teachers, subjects, periods and rooms into a conflict-free weekly schedule, and manage the daily deviations from it. `timetable_slots` exists in v0 with a good unique constraint but is seeded and read-only.

**2. Real-world workflows.** Define the academic calendar and period structure → set teacher availability and workload limits → allocate subject periods per class → build the timetable (manually, assisted, or generated) → validate for conflicts → publish → handle daily substitutions for absent teachers → issue revisions mid-term → produce class, teacher and room views.

**3. Main screens.** Academic Calendar & Holidays · Period Structure Setup (bell timings, possibly different for primary and senior) · Subject Period Allocation (periods per subject per class per week) · Teacher Availability & Max Load · Timetable Builder (drag-and-drop grid with live conflict detection) · Class Timetable view · Teacher Timetable view · Room/Lab Timetable view · Substitution Management (daily, driven by HR leave) · Timetable Publication & Versioning · Workload Report.

**4. Important fields.** Period: number, start, end, type (teaching/break/assembly/games), applicable days. Slot: class section, day, period, subject, teacher, room, effective-from, version. Availability: teacher, day, period, available flag, reason. Substitution: date, original slot, absent teacher, substitute teacher, reason, notified flag.

**5. Entities.** `academic_calendar`, `holidays`, `periods`, `timetable_versions`, `timetable_slots`, `subject_period_allocations`, `teacher_availability`, `teacher_workload_limits`, `substitutions`, `room_resources`.

**6. Relationships.** Depends on **Academic structure** (sections, subject offerings) and **HR** (teachers, availability, leave). Drives **Attendance** (which periods exist to mark) and the teacher and student dashboards. **HR** leave approval creates substitutions here. **Examinations** must not clash with the calendar. **Communication** notifies substitutions.

**7. Statuses.** Timetable version: `draft → validated → published → superseded`. Slot: `active | cancelled | substituted`. Substitution: `pending → assigned → completed | unfilled`.

**8. Roles.** Timetable Coordinator/Vice Principal (full), Principal (approve and publish), Class Teacher (view own section), Teacher (own schedule, accept substitutions), Student/Guardian (published class timetable), Admin (setup).

**9. Validations and business rules.**
- **A teacher cannot be in two places in the same period.** Hard constraint, enforced on save, and the reason the builder needs live validation rather than a validate-at-the-end button.
- A class section cannot have two subjects in one period (`uq_timetable_slot` already enforces this in v0 — keep it).
- A room cannot host two classes at once.
- Teacher weekly load must stay within the configured maximum; exceeding it needs an override with reason.
- Subject period counts must match the allocation (six Maths periods allocated means six placed) — an incomplete timetable must be visibly incomplete rather than quietly short.
- Publishing supersedes the previous version but never deletes it; **historical attendance must resolve against the version that was in force on that date**. This is a subtle requirement that is very expensive to add later.
- Substitutions cannot assign a teacher who is on leave or already teaching.
- No teaching slots on holidays or during exams.

**10. Reports/KPIs.** Teacher workload distribution and fairness · free-period analysis · room and lab utilisation · substitution frequency by teacher and by reason (a proxy for absenteeism) · unfilled substitutions (classes left unattended — the operational number that matters most) · subject-hour compliance against the syllabus plan · daily class-wise schedule for the notice board.

---

### 5.8 ATTENDANCE

**1. Purpose.** Record who was present, reliably and defensibly, for students and staff, and turn it into the alerts and statistics that the school and parents act on. v0's daily student attendance is solid and should be extended rather than replaced.

**2. Real-world workflows.** Class teacher marks the roll each morning → subject teachers optionally mark period-wise → late arrivals recorded → leave applications from parents recorded and approved → absentee SMS to parents by a cut-off time → correction of mistakes with a reason → monthly consolidation → shortage warnings before exams → attendance line on the report card.

**3. Main screens.** Daily Attendance Marking (roster with fast present/absent/late/leave toggles, one tap for all-present, offline-tolerant) · Period-wise Marking (if adopted) · Attendance Register (month grid per section) · Absentee List (today, with contact actions) · Student Leave Requests & Approval · Attendance Correction (with reason) · Staff Attendance (biometric import + manual) · Attendance Reports · Shortage/Defaulter view · Attendance Dashboard.

**4. Important fields.** Enrolment, date, session/period, status (`present | absent | late | half_day | leave | excused | holiday`), reason, marked_by, marked_at, corrected_by, correction_reason. Leave request: from, to, type (sick/planned/emergency), reason, document, approver, status.

**5. Entities.** `attendance` (re-keyed to `enrolment_id`), `attendance_sessions`, `student_leave_requests`, `attendance_corrections`, `staff_attendance`, `attendance_summary` (pre-computed per §3.11).

**6. Relationships.** Roster comes from `enrolments`; the calendar of valid days from **Timetable**; period structure from **Timetable** if period-wise. Absence triggers **Communication**. Attendance percentage appears on **Examinations** report cards and can gate exam eligibility. Staff attendance feeds **HR** payroll (loss of pay) and substitutions.

**7. Statuses.** Attendance record: `marked | corrected | locked`. Day: `open | closed | holiday`. Leave request: `applied → approved | rejected | cancelled`.

**8. Roles.** Class Teacher (mark and correct own section, within the correction window), Subject Teacher (period-wise for own periods), Admin Officer (all sections, corrections), Principal (all, plus lock/unlock), Guardian (own child's record, apply for leave), Student (own record), HR (staff attendance), Auditor (read-only).

**9. Validations and business rules.**
- One record per student per date per session — the existing `uq_attendance_student_date` generalised. Keep the constraint, widen the key.
- **Attendance cannot be marked for a future date,** nor for holidays or non-working days.
- A correction after the day closes requires a reason and is audited — attendance is evidence, and in disputes about a child's whereabouts it is the record the school relies on.
- Marking is idempotent: re-submitting the same roster must not create duplicates. (Relevant for the mobile app on a poor connection.)
- Absentee notification runs after a configurable cut-off, once per day, and must be **deduplicated** — parents receiving three SMS for one absence is a real and frequent complaint.
- Attendance percentage counts only working days for that section, and a student who joined mid-year is measured only from their joining date. Getting this denominator wrong is the most common attendance-reporting bug.
- Approved leave counts distinctly from unexcused absence in reports, even where both are "not present".
- Locking a month prevents further edits without an override.

**10. Reports/KPIs.** Daily attendance percentage school-wide and by class · monthly register (printable, board-format) · chronic absentee list (below threshold) · students at risk of exam-eligibility shortage, flagged *early enough to act* · absence patterns (Mondays, post-holiday, specific periods) · attendance versus academic performance · staff attendance and punctuality · attendance-marking compliance by teacher (which class teachers are not marking on time) · defaulter notices generated.

---

### 5.9 COMMUNICATION

**1. Purpose.** Deliver the right message to the right people over the right channel, with evidence that it was delivered. v0 has in-app `notices` with an audience enum and no delivery record.

**2. Real-world workflows.** Publish a notice or circular → send targeted messages (a class, a route, defaulters, a single parent) → automated event-driven alerts (absence, fee due, result published, holiday) → emergency broadcast (school closed due to weather — the case where reliability matters most) → two-way parent queries → track delivery and read → audit what was sent.

**3. Main screens.** Communication Dashboard (sent, delivered, failed, credits remaining) · Notice Board / Circulars · Compose Message (audience builder with live recipient count and cost estimate) · Templates · Scheduled Messages · Delivery Report per campaign · Emergency Broadcast (deliberately separate, with confirmation) · Parent Query Inbox · Notification Preferences · Communication Log per student/guardian (visible on the 360° profile) · Channel/gateway configuration.

**4. Important fields.** Message: title, body, template, channel(s), audience definition, scheduled time, priority, attachments, created_by, approved_by. Recipient: user/guardian, resolved contact, channel, status, sent_at, delivered_at, read_at, failure reason, cost. Preference: channel opt-in per category, quiet hours, preferred language.

**5. Entities.** `message_templates`, `messages`, `message_recipients`, `delivery_receipts`, `notification_preferences`, `device_tokens`, `communication_credits`, `parent_queries`, `notices`.

**6. Relationships.** Audience is resolved from **Student/Academic** (class, section, category), **Transport** (route), **Fees** (defaulters), **HR** (staff), **Admission** (applicants — who are not users, so the recipient model must accept a bare phone number). Triggered by events across every module. Feeds the Communication Log on **Student 360°**.

**7. Statuses.** Message: `draft → scheduled → sending → sent → completed | failed | cancelled`. Recipient delivery: `queued → sent → delivered → read | failed | bounced | opted_out`.

**8. Roles.** Principal (all, including emergency broadcast), Admin Officer (general communication), Class Teacher (own section only), Accountant (fee-related only), Transport Manager (route-related only), Front Desk (query handling), Guardian/Student (receive, and ask), Auditor (read-only log).

**9. Validations and business rules.**
- **Dispatch happens in a worker.** A gateway timeout must never fail the action that triggered the message. This is a direct consequence of §2.5(7) and is the main reason the hosting decision cannot be deferred.
- Bulk sends above a threshold require approval and always show recipient count and estimated cost first.
- Quiet hours are enforced for non-emergency messages; emergency broadcast bypasses them and says so on the confirmation.
- Opt-out is respected for informational messages and **overridden for statutory/emergency ones** — a parent cannot opt out of "your child is absent" or "the school is closed".
- Every send is logged with resolved recipient and status; failures are retried with backoff and then surfaced, not silently dropped.
- Templates are versioned; the exact text sent is reproducible later.
- Messages to a specific child's guardian must respect custody restrictions where recorded.
- No personal data of one family may appear in a message to another (a genuine risk with careless bulk merges).

**10. Reports/KPIs.** Delivery rate by channel · failure reasons · SMS/email credits consumed versus budget, and cost per message type · read rate for in-app and push · unreachable contacts (the list that drives a data-cleanup drive) · response time on parent queries · most-used templates · audit trail of emergency broadcasts.

---

### 5.10 REPORTS / ANALYTICS

**1. Purpose.** Answer the questions management asks, without a developer. Provide operational lists to staff and trend analysis to leadership, from one governed source.

**2. Real-world workflows.** A principal opens a dashboard each morning → a section head pulls an operational list (today's absentees, this week's defaulters) → management reviews monthly numbers → the board asks for a year-on-year comparison → a report is scheduled to arrive by email each Monday → a regulator or affiliating board asks for a formatted return.

**3. Main screens.** Executive Dashboard · Module dashboards (Admission, Fees, Attendance, Academics, HR, Transport) · Report Library by category · Report Viewer with filters, drill-down and export · Saved/Custom Reports · Scheduled Reports · Statutory/Board report formats · Data export centre (audited).

**4. Important fields.** Report definition: name, category, base query/view, parameters, permission, output formats. Schedule: frequency, recipients, format. Every report: academic year, date range, class/section scope as standard parameters.

**5. Entities.** `saved_reports`, `report_schedules`, `report_runs`, `export_audit`, plus summary tables (`attendance_summary`, `fee_collection_summary`, `result_summary`, `admission_funnel_summary`).

**6. Relationships.** Reads from every module; writes nothing except its own audit. This one-way rule is what keeps reporting from becoming a back door around business rules.

**7. Statuses.** Report run: `queued → running → completed | failed`. Schedule: `active | paused`. Export: `requested → generated → downloaded → expired`.

**8. Roles.** Principal/Management (all), Module heads (own module), Class Teacher (own section), Accountant (financial), Auditor (all, read-only), Guardian/Student (own data only — their dashboards are reports too).

**9. Validations and business rules.**
- **Every report obeys the same permission and scope rules as the underlying screens.** A report must never become a way to see rows a user cannot see directly. This is the most common data-leak path in ERPs.
- Every report states its academic year, filter set and generation timestamp on the output — a printed report with no context is a report that will be misquoted.
- Heavy reports run asynchronously and notify on completion rather than blocking a request.
- **Exports containing personal data are audited** (who, what, when, how many rows) and can be restricted or watermarked.
- Numbers must reconcile across reports: the fee dashboard total and the fee report total must agree, which means one shared definition, not two queries.
- No fabricated data points — a month with no invoices shows no bar rather than a zero bar. (v0 already does this deliberately in `fees.collection`; it should be a system-wide rule.)

**10. Reports/KPIs (management-level).** Enrolment and retention trend · admission funnel and seat utilisation · fee collection efficiency and receivables ageing · academic performance trend by class and subject · attendance trend and chronic absenteeism · staff attrition, workload and student:teacher ratio · transport utilisation and cost recovery · revenue versus expense by month · a small set of "school health" indicators on one screen for the principal.

---

### 5.11 ADMINISTRATION / ROLES / PERMISSIONS

**1. Purpose.** Configure the system, control who can do what, and keep an auditable record of both. This module is what makes the ERP maintainable by the school rather than by us.

**2. Real-world workflows.** Set up school identity and branding → open an academic year → configure modules, numbering and policies → define roles and grant permissions → create user accounts and assign roles with scope → onboard and offboard staff accounts → review the audit log after an incident → manage backups and data retention → close and archive an academic year.

**3. Main screens.** School Profile & Branding · Academic Year Management (create, set current, close, archive) · Module Settings · Numbering/Sequence Setup (admission no, receipt no, invoice no) · Role Management · Permission Matrix (roles × permissions grid — the screen that makes the model comprehensible) · User Management · User–Role–Scope assignment · Password & Session Policy · Audit Log Viewer (filter by actor, entity, date, action) · Login History · Data Import/Export centre · Backup & Restore status · Document Type configuration · Holiday/Calendar setup · System Health.

**4. Important fields.** Role: code, name, description, is_system. Permission: module, action, code. Assignment: user, role, scope type, scope id, valid from/to. Settings: key, value, data type, scope, editable-by. Audit entry as per §3.6.

**5. Entities.** `roles`, `permissions`, `role_permissions`, `user_roles`, `settings`, `number_sequences`, `audit_log`, `login_history`, `document_types`, `academic_years`, `import_jobs`, `backup_records`.

**6. Relationships.** Governs every module. Academic year state gates what other modules will accept. Audit log receives writes from all services.

**7. Statuses.** User: `invited → active → locked → disabled`. Role assignment: `active | expired | revoked`. Academic year: per §3.1. Import job: `uploaded → validated → previewed → applied | failed | rolled_back`.

**8. Roles.** Super Admin (full, including permission editing — deliberately a small number of people), Principal (most settings, cannot edit their own permissions), Admin Officer (operational settings), Auditor (audit log, read-only), everyone else (own profile and password only).

**9. Validations and business rules.**
- **A user cannot escalate their own permissions.** Editing your own role assignment is blocked, not merely discouraged.
- At least one Super Admin must exist at all times — the last one cannot be deleted or demoted.
- System roles cannot be deleted; they may be copied and customised.
- Permission changes are audited with before/after, and take effect on the next token refresh (§3.5).
- **The audit log is append-only.** No delete, no edit, no truncate — through the application or otherwise.
- Bulk import runs validate → preview → apply, is transactional, and is reversible by run id. An import that half-applies is the fastest way to corrupt a live school's data.
- Closing an academic year requires a checklist to pass (results published, fees reconciled, promotions run) and is irreversible without a Super Admin override.
- Sequence numbers are gapless per year per type, and the counter is never editable through the UI.
- Password policy, session timeout and forced-change-on-first-login are enforced centrally — the current default passwords (`Student@123`) with no forced change are a known v0 gap that this module must close.

**10. Reports/KPIs.** Active users by role · login activity and failed-login attempts (an early signal of attack) · permission changes over time · audit activity by module and actor · dormant accounts (staff who left but whose accounts live on) · data export activity · import history and failures · backup success and last-restore-test date · academic year status overview.

---

## 6. ERP module hierarchy and navigation

The navigation is organised by **what a person is trying to do**, not by database structure. The current dashboard's flat list of ten pages does not survive 11 modules.

```
Sunrise ERP
│
├── Dashboard                       role-specific landing (§9)
│
├── Admissions
│   ├── Dashboard · Enquiries · Applications · Document Verification
│   ├── Assessments · Interviews · Selection & Offers · Waitlist
│   └── Setup: Cycles · Seats · Document checklists · Reports
│
├── Students
│   ├── All Students · Add Student · Bulk Import · Guardians
│   ├── Promotions · Transfer Certificates · Certificates · Alumni
│   └── Reports
│
├── Academics
│   ├── Classes & Sections · Subjects · Subject Offerings
│   ├── Class–Subject–Teacher allocation · Houses
│   └── Academic Calendar · Holidays
│
├── Attendance
│   ├── Mark Attendance · Register · Absentees · Leave Requests
│   └── Corrections · Reports
│
├── Timetable
│   ├── Period Structure · Builder · Class / Teacher / Room views
│   └── Substitutions · Workload
│
├── Examinations
│   ├── Assessment Schemes · Grading Scales · Exams · Datesheet
│   ├── Seating & Hall Tickets · Marks Entry · Moderation
│   └── Results · Report Cards · Publication · Analysis
│
├── Fees
│   ├── Collection (counter) · Invoices · Payments · Defaulters
│   ├── Concessions · Fines · Refunds · Adjustments
│   ├── Setup: Fee Heads · Fee Plans · Assignments
│   └── Day Book · Reconciliation · Period Close · Reports
│
├── Transport
│   ├── Vehicles · Drivers · Routes & Stops · Student Assignments
│   └── Compliance & Documents · Trip Logs · Reports
│
├── HR
│   ├── Employees · Departments & Designations
│   ├── Recruitment: Postings · Candidates · Interviews · Offers
│   ├── Attendance · Leave · Substitution support
│   ├── Payroll: Structures · Runs · Payslips
│   └── Appraisals · Exits · Reports
│
├── Communication
│   ├── Notices · Compose · Templates · Scheduled
│   ├── Delivery Reports · Parent Queries · Emergency Broadcast
│   └── Preferences · Channel setup
│
├── Reports
│   ├── Executive · By module · Saved · Scheduled · Statutory
│   └── Export centre
│
└── Administration
    ├── School Profile · Academic Years · Settings · Sequences
    ├── Roles & Permissions · Users · Sessions
    └── Audit Log · Import/Export · Backups · System Health
```

Three navigation rules:
1. **Menus are permission-filtered**, not disabled. A Fee Collector should not see an HR menu greyed out; they should not see it.
2. **Global search is the primary navigation** for anything about a person. Office staff search; they do not browse to a student through four menus.
3. **The academic year is a persistent global control** in the header, visible on every screen, because "which year am I looking at?" is the question that causes the most expensive mistakes in a school ERP.

---

## 7. Major workflows

### 7.1 Admission to enrolled student (the spine)

```
Enquiry ──► Application ──► Documents verified ──► Assessment ──► Interview
                                                                     │
                                            ┌────────────────────────┘
                                            ▼
                                    Decision (audited, reasoned)
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
                    Admitted            Waitlisted           Rejected
                        │                   │
                  Offer issued        (promoted on
                  (with expiry)        seat release)
                        │
                  Offer accepted
                        │
                  Admission fee paid
                        │
        ╔═══════════════▼═══════════════════════════════════════╗
        ║  CONVERSION — ONE TRANSACTION                          ║
        ║  create student · create enrolment (year, section,     ║
        ║  roll no) · create/link guardians · migrate documents  ║
        ║  · assign fee plan + concession · create portal login  ║
        ║  · allocate admission_no from sequence · audit         ║
        ╚═══════════════┬═══════════════════════════════════════╝
                        ▼
              Student active in current year
```

### 7.2 The daily operating loop

```
Timetable (published) ─► defines periods for the day
        │
        ▼
Teacher marks attendance ─► absentee list ─► Communication (deduplicated SMS)
        │                                            │
        ▼                                            ▼
attendance rows (enrolment_id)              delivery receipts (evidence)
        │
        ├──► Attendance % ──► exam eligibility check ──► Examinations
        └──► report card attendance line
```

### 7.3 The money loop

```
Fee plan (year, class, category) + concession (approved)
        │
        ▼
Invoice generation (batch, per period) ──► invoice_lines per fee head
        │                                        ▲
        │                                        │ transport head from
        │                                        │ Transport assignment
        ▼
Communication: due reminder
        │
        ▼
Payment received (any amount, idempotent) ──► allocations to lines
        │                                              │
        ▼                                              ▼
Receipt (gapless sequence)                    balance derived, not stored
        │
        ├──► overdue sweep (scheduled job, not on read) ──► fines ──► reminders
        ├──► reconciliation against bank/gateway
        └──► period close (immutable)
```

### 7.4 Year-end rollover — the workflow that proves the architecture

```
1. Publish all results                 (Examinations)
2. Reconcile and close fee periods     (Fees)
3. Create next academic year + sections (Administration/Academics)
4. Run promotion in preview            (Students)
      per student: promote | detain | pass out | transfer out
5. Review preview, then commit         → creates next year's enrolments
6. Carry forward: guardians, documents, transport, fee plans
7. Carry forward outstanding dues as opening balances
8. Close the old year → read-only
9. Switch current year
```

If this workflow is easy, the architecture is right. If it requires overwriting `class_section_id` on every student row, the architecture is the one we have today.

### 7.5 Staff absence to covered class

```
Teacher applies for leave (HR)
        │
        ▼
Approver sees affected timetable periods  ◄── Timetable
        │
        ├──► approve leave AND assign substitutes (blocked if unfilled, or
        │    explicitly accepted as unfilled with a reason)
        ▼
Substitution records ──► Communication to substitute teacher + class
        │
        ▼
Staff attendance ──► payroll LOP if unpaid leave
```

---

## 8. Cross-module dependency map

`→` means "depends on / reads from". The arrow direction is the constraint that matters at build time.

```
                        ┌─────────────────────────┐
                        │  FOUNDATION             │
                        │  academic_years         │
                        │  users/roles/permissions│
                        │  documents · audit_log  │
                        │  sequences · settings   │
                        └───────────┬─────────────┘
                                    │ everything depends on this
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
   ┌─────────┐              ┌──────────────┐            ┌────────────┐
   │ ACADEMIC│◄─────────────│   STUDENTS   │───────────►│    HR      │
   │STRUCTURE│              │  + enrolments│            │ employees  │
   └────┬────┘              └───┬───┬───┬──┘            └──┬───┬─────┘
        │                       │   │   │                  │   │
        │  ┌────────────────────┘   │   └──────────┐       │   │
        ▼  ▼                        ▼              ▼       ▼   ▼
   ┌──────────┐             ┌────────────┐   ┌──────────┐ ┌──────────┐
   │TIMETABLE │────────────►│ ATTENDANCE │   │   FEES   │ │TRANSPORT │
   └────┬─────┘             └──────┬─────┘   └────┬─────┘ └────┬─────┘
        │                          │              ▲            │
        │                          │              └────────────┘
        │                          │            transport fee head
        ▼                          ▼
   ┌──────────────┐         ┌─────────────┐
   │ EXAMINATIONS │◄────────│  (att. %)   │
   └──────┬───────┘         └─────────────┘
          │
          ▼
   ┌──────────────────────────────────────────────┐
   │ COMMUNICATION  ◄── events from every module  │
   └──────────────────────────────────────────────┘
          │
          ▼
   ┌──────────────────────────────────────────────┐
   │ REPORTS  ◄── reads everything, writes nothing│
   └──────────────────────────────────────────────┘

   ADMISSION ──────► STUDENTS (creates) ──► FEES (plan) ──► TRANSPORT (request)
             ──────► reads: academic structure (seats), HR (staff-ward)
```

**Hard dependencies (cannot build the dependent before the dependency):**

| Dependent | Requires first | Why |
|---|---|---|
| Everything | `academic_years`, `enrolments` | The year and enrolment keys appear in nearly every table |
| Admission conversion | students, enrolments, guardians, fee plans, sequences, documents | Conversion is one transaction across all of them |
| Transport billing | Fee heads redesign | Transport fees have nowhere to go in the current fee model |
| Attendance % on report card | Attendance with correct denominators | Wrong denominator silently corrupts a published document |
| Substitutions | Timetable + HR leave | Neither alone is enough |
| Any report | Permission scopes | Reports must not bypass row-level access |
| Bulk anything (import, PDF, SMS) | Worker infrastructure | Cannot run in a serverless request |

**Deliberately loose couplings** (should stay events, not calls): attendance → SMS, result publication → notification, fee due → reminder, admission stage change → email. If any of these become synchronous calls, an outage in the messaging provider takes down attendance marking.

---

## 9. Management dashboard concept

The current dashboard shows aggregate counts. A school ERP dashboard has a different job: **surface what needs a decision today, and what is drifting over the term.**

### 9.1 Design principles

1. **Role-specific landing pages, not one dashboard with hidden tiles.** A Principal, an Accountant and a Class Teacher open different screens.
2. **Every number is clickable and drills to the rows behind it.** A count with no drill-through invites disbelief.
3. **Exceptions above averages.** "94% attendance" is less useful than "3 sections have not marked attendance today".
4. **Comparison is mandatory context.** A number without last month or last year beside it cannot be judged.
5. **No fabricated data.** An empty state says "no data for this period", never a zero bar. (v0's existing rule, made system-wide.)
6. **Loading is not emptiness.** The `DataTable` `loading` prop rule applies to every tile.
7. **Aggregates come from summary tables** refreshed on schedule, with the refresh time shown. Computing them per request is the N+1 lesson repeating at a larger scale (§3.11).

### 9.2 Principal / Management dashboard

```
┌──────────────────────────────────────────────────────────────────┐
│ Academic Year 2026-27 ▾        Sunrise Public School     [search]│
├──────────────────────────────────────────────────────────────────┤
│  NEEDS ATTENTION TODAY                                           │
│  • 3 sections have not marked attendance      → [view]           │
│  • 2 vehicle documents expire in 7 days       → [view]           │
│  • 14 offers expire tomorrow, 9 unpaid        → [view]           │
│  • ₹4.2L overdue > 60 days                    → [view]           │
│  • 1 class unattended (substitution unfilled) → [view]           │
├───────────────────┬───────────────────┬──────────────────────────┤
│ STRENGTH          │ ATTENDANCE TODAY  │ FEE COLLECTION (Sep)     │
│ 1,842 students    │ 91.4%             │ ₹38.2L / ₹46.0L  (83%)   │
│ +12 / −4 this mo. │ ▼ 2.1pt vs last wk│ ▲ 6pt vs Sep last year   │
├───────────────────┴───────────────────┴──────────────────────────┤
│ ADMISSION FUNNEL 2027-28                                         │
│ Enquiries 612 → Applications 341 → Tested 288 → Admitted 121     │
│ Seats: 140 · Filled 121 · Waitlist 34 · Conversion 19.8%         │
├──────────────────────────────────────────────────────────────────┤
│ TRENDS  [attendance ▾] [12 months ▾]        (updated 06:00)      │
│ ▁▂▃▅▆▇▇▆▅▄▃▂  with prior-year overlay                            │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 Other role landings (summary)

| Role | Lands on | Primary actions |
|---|---|---|
| Accountant | Collection counter + today's day book | Collect fee, print receipt, defaulters |
| Admission Officer | Pipeline queue by stage | Next action per application, today's interviews |
| Class Teacher | Own section: attendance not marked, absent today, upcoming exams | Mark attendance, view roster |
| HR Manager | Leave approvals, staff absent today, expiring documents | Approve leave, arrange substitution |
| Transport Manager | Routes running, compliance expiries, unassigned requests | Assign student, flag vehicle |
| Exam Controller | Marks entry progress by section/subject | Chase pending entries, lock, publish |
| Front Desk | Today's enquiries and visitor log, search | Log enquiry, look up a student |

### 9.4 What deliberately does not go on a dashboard

Anything requiring a heavy query per view, anything that cannot be drilled into, and vanity metrics with no decision attached. If nobody can name the action a tile triggers, it should not be a tile.

---

## 10. Role and permission model

### 10.1 Structure

```
User ──< user_roles >── Role ──< role_permissions >── Permission
         │                                              │
      scope_type + scope_id              module.resource.action
      (global | academic_year |          e.g. fees.invoice.void
       class_section | department |            students.profile.read
       self)                                   marks.entry.after_lock
```

### 10.2 Permission naming

`<module>.<resource>.<action>` — for example `admission.application.decide`, `fees.payment.collect`, `fees.payment.void`, `hr.payroll.approve`, `exam.marks.enter`, `exam.result.publish`, `admin.role.edit`. Actions include `read`, `list`, `create`, `update`, `delete`, `approve`, `publish`, `export`, `print`, `void`, `override`.

Note that `read` and `export` are **separate permissions**. Being allowed to see a student's record on screen is not the same as being allowed to download two thousand of them, and a school's most likely data breach is an authorised user exporting more than they need.

### 10.3 Indicative role matrix (abridged)

| Role | Admission | Students | Fees | Exams | HR | Transport | Comms | Admin |
|---|---|---|---|---|---|---|---|---|
| Super Admin | full | full | full | full | full | full | full | full |
| Principal | full | full | approve | publish | approve | read | full | settings |
| Vice Principal | read | full | read | full | read | read | send | – |
| Admission Officer | full | create | read | – | – | – | send | – |
| Admin Officer | setup | full | read | setup | read | read | send | settings |
| Accountant | fees | read | full | – | payroll | fee-read | fee-msgs | – |
| Fee Collector | – | read | collect only | – | – | – | – | – |
| Exam Controller | – | read | – | full | – | – | exam-msgs | – |
| HR Manager | assess | read | – | – | full | drivers | staff-msgs | – |
| Transport Manager | – | read | transport dues | – | read | full | route-msgs | – |
| Class Teacher | – | own section | – | own section marks | – | own students | own section | – |
| Subject Teacher | – | own sections read | – | own subject marks | – | – | – | – |
| Guardian | own application | own children | own children | own children | – | own children | receive | – |
| Student | – | self | self | self | – | self | receive | – |
| Auditor | read | read | read | read | read | read | read | audit log |

### 10.4 Enforcement rules

- **Permission at the route, scope in the service.** Keep `scoping.py` as the single place row-level access is decided; change its inputs from `user.role` to the resolved permission-and-scope set. This preserves v0's best decision while removing its rigidity.
- **Deny by default.** A permission not granted is denied; there are no deny rules to reason about.
- **Scope narrows, never widens.** Two grants for the same permission produce the union of their scopes, but a scoped grant can never reach outside its scope.
- **UI hiding is convenience, not security.** Every hidden control must also be refused by the API.
- **Permission changes take effect at the next token refresh**, and a revocation that must be immediate uses a session-invalidation list. (This is also the fix for v0's known "no token revocation" gap.)
- **Self-escalation is impossible** — see §5.11.

---

## 11. Technical architecture

### 11.1 API architecture

Keep FastAPI, SQLAlchemy 2, Pydantic 2 and the three-layer split. The changes are structural, not technological.

**Restructure routes by module and resource, not by role.** The current `api/admin/…`, `api/teacher/…`, `api/student/…` split duplicates the same resource across role folders and hardcodes the four-role assumption into the URL space. With modelled permissions, one resource has one route, and the caller's permissions decide what they get back.

```
/api/v1/admissions/enquiries          /api/v1/students
/api/v1/admissions/applications       /api/v1/students/{id}/guardians
/api/v1/admissions/applications/{id}/documents
/api/v1/fees/invoices                 /api/v1/attendance
/api/v1/fees/payments                 /api/v1/exams/{id}/marks
/api/v1/hr/employees                  /api/v1/transport/routes
```

Conventions to fix now rather than later:
- **Versioned prefix** (`/api/v1`) from the start — the mobile app will lag the web app, and that is exactly what versioning is for.
- **Uniform list contract** on every collection: `page`, `page_size`, `sort`, `q`, plus module filters, returning `{items, total, page, page_size}`. The current inconsistency (only students paginate) must not be carried forward.
- **`academic_year_id` is an explicit optional parameter** on year-scoped endpoints, defaulting to current at the boundary.
- **Errors are structured** (`code`, `message`, `field_errors`) so both clients can render them without string matching.
- **Idempotency keys** accepted on all money-moving and bulk endpoints.
- **Async jobs return a job id**, not a blocked request; clients poll or receive a notification.
- **The generated OpenAPI types must actually be imported by the clients.** BLUEPRINT §19 #20 records that `packages/api-types/schema.d.ts` is generated but unused, so a backend rename breaks clients silently at runtime. At ERP surface area this stops being a nice-to-have.

### 11.2 Database architecture

- **PostgreSQL, single instance.** No sharding, no microservice-per-module databases. The workload (§3.14) does not justify distribution and would multiply operational cost.
- **Constraints in the database.** Continue v0's practice: unique constraints as business rules, foreign keys everywhere, check constraints for ranges, partial unique indexes for "exactly one current" rules.
- **Indexing rules:** every foreign key indexed; composite indexes on the actual access paths (`(academic_year_id, class_section_id)`, `(enrolment_id, date)`, `(status, due_date)`); partial indexes for hot filtered queries (unpaid invoices).
- **Money is `Numeric(12,2)`** — widen from v0's `Numeric(10,2)`, which caps at ~₹99.99L and is uncomfortably close for an annual payroll or a consolidated fee total.
- **Timestamps are `timestamptz`,** and the application has one timezone (Asia/Kolkata) configured centrally. v0 uses `Date.today()` server-side, which is a latent bug the moment the server is not in IST — and it is not, on Vercel.
- **JSONB only for genuinely variable data** (audit before/after, structured interview scores, report definitions). Never for data that will be queried or joined as a first-class attribute.
- **Migration discipline:** one baseline exists today; from here every change is a reviewed migration, expand-then-contract for anything destructive, and rehearsed against a production-shaped copy before it runs on real school data.
- **Archival:** closed years stay in the same tables (the volumes are small); partitioning is a later option for `attendance` alone if it ever justifies itself.

### 11.3 Management web application architecture

Keep React + Vite + TypeScript. The changes are about structure and scale.

- **Feature-folder structure** (`features/admissions/…`, `features/fees/…`) rather than a flat `pages/` directory. Ten pages is a directory; eighty is an architecture.
- **A server-state library** (TanStack Query or equivalent) for caching, invalidation and background refresh. Hand-rolled fetching across eighty screens is where consistency bugs live.
- **A shared component contract** — `DataTable` (with its `loading` prop rule), form controls, filter bar, status chip, drill-through link, confirm-with-reason dialog. Reason-capture appears in dozens of places (§3.6) and must be one component, not thirty.
- **Permission-aware rendering** driven by the permission set from `/me`, with the API as the real enforcement point.
- **Route-based code splitting per module,** so an Accountant does not download the HR bundle.
- **A global academic-year context** in the header, held in one place and passed to every query key so that switching years invalidates cleanly.
- **Frontend tests are no longer optional.** v0 has zero (an honestly recorded gap); an ERP with money and permissions needs at least: permission-gated rendering, the fee collection flow, marks entry, and admission conversion.
- **Print and export are first-class**, not an afterthought — receipts, report cards, registers, hall tickets and TCs all have expected paper formats.

---

## 12. Implementation plan — four parts

Delivery is split into **four parts, each ending at a checkpoint** where work stops
until the product owner gives the green light. This exists because session time is the
scarcest resource on this project, not because the work naturally divides in four.

**An honest caveat: four checkpoints is not four sessions.** Parts 3 and 4 will each
span several working sessions. The checkpoints are safe places to stop and review, not
a cost estimate. Every completed unit inside a part is committed, so an exhausted
session never loses work.

### Part 1 — Foundation

Everything the other three parts stand on. Nothing here is user-visible, which is
exactly why it must not be skipped.

- Multi-tenancy: `school_id` throughout, tenant filter in the service layer, `login_id`
  unique per school
- `academic_years` with a single-current constraint and an explicit close process
- `enrolments` replacing `students.class_section_id` and `roll_no`
- `employees` replacing `teachers`; `guardians` replacing `parents` with structured relations
- Modelled roles and permissions, with `scoping.py` rewired from `user.role` to
  resolved permission-and-scope sets
- Append-only `audit_log`, plus `created_by` / `updated_by`
- `documents` + MinIO object storage with signed, expiring URLs
- `number_sequences` — admission number `YYYY` + 6-digit sequence, receipt and invoice numbers
- Status lifecycles replacing `is_active`; the shared roster helper that closes the
  known soft-delete defect
- Settings, custom fields, feature flags (§3.15 levels 1–3) and the plugin **seams**
- Uniform pagination, sorting and search conventions across every endpoint
- Homework removed from the web admin dashboard, retained in the mobile app (§0.17)
- Infrastructure: Oracle Cloud instance running Docker (API + worker + PostgreSQL +
  MinIO), scheduler, CI running the test suite before deploy, backup with a **tested** restore
- Demo data expanded to one school, 10 classes × 10 students

**Checkpoint 1 passes when:** the year-end rollover of §7.4 runs end to end on demo
data; a Class Teacher's section scope is refused by the API, not just hidden in the UI;
a scheduled job runs without a request triggering it; and a restore from backup has
actually been performed.

### Part 2 — Admission

The full pipeline of §5.1, including the public online portal.

- Admission cycles, seat configuration, document checklists
- Enquiry register with follow-up
- Public online application portal with spam protection; staff-entered applications too
- Document upload and verification workflow
- Assessment scheduling and marks; interview scheduling and structured feedback
- Merit/selection view against seats, batch decisions with mandatory reasons
- Offers with expiry, automatic waitlist promotion on lapse
- Application and admission fee collection (offline recording — no gateway, §0.10)
- **Atomic conversion** to student + enrolment + guardians + fee plan + portal login,
  with automatic section allocation and a preview

**Checkpoint 2 passes when:** a parent completes an application on the public portal
and, after staff action, exists as an enrolled student with a fee account, a login and
migrated documents — with no manual database work at any point.

### Part 3 — Fees and daily operations

- Fee heads, plans, per-student assignment, 10% sibling concession
- Invoices with lines; **allocation-based payments** supporting part payment
- Late fee rule: ₹300 at day 5, +₹100/day, capped at 50% of invoice
- Collection counter, receipts from a gapless sequence, day book, defaulters
- Void/reverse instead of edit/delete; period close
- Attendance (daily), corrections with reason, absentee list, leave requests
- Timetable made editable with live conflict detection, plus substitutions

**Checkpoint 3 passes when:** a month is billed, partially paid, late-feed, chased,
fully collected and closed — and the closed period refuses further writes. A week of
attendance is marked and corrected with an audit trail.

### Part 4 — Academics and back office

- Examinations: assessment schemes, datesheet, marks entry with lock, moderation
- CBSE report cards, template-configurable, **frozen at publication** (§0.8)
- Result withholding for unpaid dues; TC withheld until dues cleared (§0.6b)
- HR: employees, departments, leave, staff attendance, recruitment
- Payroll as configurable components (§3.16)
- Transport: vehicles, routes, stops, assignments, compliance expiry, transport fee head
- Communication: outbox, email through a pluggable provider, templates, delivery receipts
- Reports: summary tables, report library, scheduling, audited exports
- **`CONFIGURATION-GUIDE.md`** and **`EXTENSION-GUIDE.md`**

**Checkpoint 4 passes when:** a CBSE report card publishes and stays frozen; a payroll
run completes for the demo school; and a non-technical reader can change a fee rule
using only the configuration guide.

### Explicitly not in any part

Mobile app changes beyond keeping it working · payment gateway (V2) · SMS and WhatsApp
(wired but disabled) · Library, Hostel, Inventory, Health Room · multi-branch ·
plugin runtime · Excel/SQL import from a real school's existing system (built when a
school is signed) · localisation.

---

## 13. Risks and architectural decisions

### 13.1 Decisions this document proposes (and what it would take to reverse them)

| # | Decision | Reversal cost |
|---|---|---|
| D1 | Enrolment-per-year replaces `students.class_section_id` | Very high once data exists — this is why it is Phase 0 |
| D2 | `academic_years` as a first-class entity, explicit not implicit | Very high |
| D3 | Allocation-based fee ledger replacing the one-payment-per-invoice model | Very high after real payments exist |
| D4 | Modelled roles and permissions replacing four hardcoded roles | Medium |
| D5 | `employees` replaces `teachers` | Medium if done early, high after HR is built on it |
| D6 | Guardians with structured relations replacing free-text `parents` | Medium |
| D7 | Append-only audit log with reason capture on sensitive actions | Low to add, high to backfill |
| D8 | Documents as a polymorphic table plus object storage | Low |
| D9 | Routes restructured by module rather than by role | Medium (both clients change) |
| D10 | Single PostgreSQL, no distribution | Low — deliberately reversible if volumes ever justify it |
| D11 | Compute analytics into summary tables rather than on read | Low |
| D12 | Keep service-layer scoping (v0's best decision) | n/a — retained |

### 13.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Scope explosion** — 11 modules is a multi-year build for a small team | High | High | Phase gates; each phase independently useful; resist starting modules before Phase 0 lands |
| **Fee migration corrupts financial history** | Medium | Severe | Migrate to the new model with a reconciliation report proving old and new totals agree per student, exactly as the N+1 fix was verified before shipping |
| **Serverless constraint forces bad workarounds** (cron-by-request, sync SMS) | High if unaddressed | High | Make the hosting decision in Phase 1, before modules depend on it |
| **Permission model becomes unmaintainable** | Medium | High | Additive-only, no deny rules, a visible permission matrix screen, and the Auditor role as a standing test case |
| **The system is built for a school we have not talked to** | High | Severe | Every "Open Decision" in §16 is a question for a real school, not for us. This is the biggest risk in the document. |
| **Report card correctness regressions** | Medium | Severe (parent-facing) | Snapshot grades at publication; verify a full cohort old-vs-new before any grading change ships |
| **Personal data exposure via exports or public demo** | Medium | Severe | Separate `export` permission, export auditing, and the writable public demo (a known current defect) fixed before real data exists |
| **Single developer, no CI, one migration baseline** | High | High | CI in Phase 1; migration review discipline; a tested restore before any school data is loaded |
| **Over-engineering in anticipation of scale that never arrives** | Medium | Medium | Explicit non-goals: no microservices, no sharding, no event-sourcing, no multi-tenancy until answered |

### 13.3 Weak assumptions in this document that should be challenged

Stated plainly, because a design document that presents itself as certain is less useful than one that marks its own soft ground:

1. **That the school wants all 11 modules.** Most schools would rather have four that work. This document specifies the full scope because it was asked for, but the phasing exists precisely so that scope can be cut.
2. **That period-wise attendance is needed.** Assumed optional here. It roughly multiplies attendance data volume and marking effort, and many schools never use it.
3. **That the assessment scheme should be configurable.** Configurable schemes are significantly harder than a fixed CBSE-style one. If the school follows one board and one pattern, a fixed scheme with a migration path is the lazier and probably better answer.
4. **That admission runs online.** The design assumes staff-entered applications with optional online submission. A fully public online portal is a different security and scale problem.
5. **That payroll belongs in this system at all.** Many schools already run payroll in Tally or an accountant's package. Building it may be duplicated effort; an export may be the right answer.
6. **That we should build a report builder.** Saved reports and scheduling are proposed; a general-purpose query builder is a product in itself and is probably out of scope.
7. **That transport GPS tracking is wanted.** Deliberately excluded — it is a hardware and vendor integration problem, not an ERP one.

---

## 14. Future mobile implications

The mobile app is not designed here. These are the decisions that must not be made in a way that blocks it.

| Decision made now | Why the mobile app depends on it |
|---|---|
| **One versioned API serving both clients** (`/api/v1`) | Web and mobile will ship on different cycles; the API must tolerate an older client. No web-only endpoints, no HTML-shaped responses. |
| **Permissions returned from `/me`** | Mobile renders its tab set from permissions rather than hardcoding role tabs, so a new role does not require an app release. |
| **Idempotent writes everywhere** | Phones lose connectivity mid-request. Attendance marking and fee payment must be safe to retry — this is why §5.8 requires idempotent roster submission. |
| **Structured error codes** | Mobile cannot match on error strings across versions. |
| **Server-driven configuration** (fee heads, document types, statuses as data) | Avoids an app release every time the school changes a list. |
| **Signed, expiring document URLs** | Mobile downloads documents through the same mechanism the web uses; no separate auth path. Note the existing SDK 54 constraint recorded in BLUEPRINT §19 #15 — headers are supported only via `expo-file-system/legacy`. |
| **Push token registry** (`device_tokens`) built with Communication | Retrofitting push into a finished communication module is expensive. |
| **Pagination on every list** | A phone cannot render 2,000 rows; the web app can get away with it for longer, which is exactly why the discipline must be set by the API. |
| **Token refresh with revocation** | Long-lived mobile sessions make v0's missing revocation a real security gap rather than a theoretical one. |
| **No server-side session state** | Keeps the door open for offline-first behaviour later. |

Explicitly deferred: offline data sync, biometric login, in-app payments, and live location. Each is a design exercise of its own.

---

## 15. Security and privacy

This system holds children's names, photographs, addresses, medical conditions, family income and financial records. That raises the bar above ordinary business software.

**Authentication and access**
- Forced password change on first login, and an end to shared default passwords (`Student@123` today, with no forced change — a recorded v0 gap).
- Rate limiting on login (absent today), account lockout with a reset path, and login-attempt logging.
- Token revocation on logout, role change and deactivation (absent today — logout is client-side only).
- MFA for Super Admin, Principal and Accountant. These accounts can move money and change permissions.
- Session timeout appropriate to a shared office machine.

**Data protection**
- HTTPS everywhere (already true in production), and TLS to the database.
- Sensitive fields encrypted at rest: bank details, medical notes, and Aadhaar if it is stored at all.
- **Aadhaar: only the last 4 digits and a `verified` flag are stored (§0.12).** The full 12-digit number is never written to the database. This satisfies document matching and student identification while making an Aadhaar leak impossible.
- Medical and financial data permission-gated separately from the general profile.
- Documents served only via short-lived signed URLs after a permission check.
- Database backups encrypted, with a **tested** restore — an untested backup is not a backup.

**Operational**
- The public demo is currently writable by anyone with the URL (a recorded defect). It must be made read-only, re-seeded on a schedule, or taken down before any real data exists anywhere near this system.
- Production database credentials held only in the platform's secret store, never in the repo. The Neon credential pasted into a chat transcript on 3 September should be rotated regardless.
- Separate environments, with production data never copied to development un-anonymised.
- Exports audited and rate-limited; bulk export permission granted narrowly.
- **Retention (§0.14): academic and financial records are kept indefinitely.** A school must be able to issue a duplicate mark sheet or TC years after a student leaves. What expires is *portal access* — a departed student and their guardians lose their login 3 months after leaving. No scheduled job deletes records.
- An incident response path: who is called, what is logged, how parents are informed.

---

## 16. Open items

The twenty-one open decisions this document originally posed were answered on
6 September 2026 and are recorded in **§0 — Decision register**, which is authoritative.

Four items remain, none of them blocking Part 1:

| # | Question | Needed by |
|---|---|---|
| A | A real Lucknow school's payroll structure, to validate the component model against. The defaults in §3.16 are researched, not confirmed against a live payslip. | Part 4 |
| B | Confirmation that Uttar Pradesh levies no professional tax. Assumed in §3.16 and shipped disabled; to be verified before payroll is written rather than trusted. | Part 4 |
| C | Whether the late-fee clock stops when the next month's invoice is generated, or keeps accruing on the old invoice until paid. Changes the fine calculation. | Part 3 |
| D | The exact CBSE report card layout the target school expects. The template is configurable, but the shipped default should match something real. | Part 4 |

Anything else that surfaces during implementation is raised at the nearest checkpoint
rather than decided unilaterally.

---

## Closing note

The existing Sunrise system is a sound foundation in the ways that are hardest to get right — layered architecture, service-layer access control, constraints as business rules, honest empty states, and a documented decision history. It should not be thrown away.

But it was built to demonstrate a school management system, and an ERP is asked to *be* one. The difference shows up in three places: a student that has no history, an academic year that is a string, and a fee model that cannot represent a partial payment. Those three are worth fixing before anything is added on top, because every module in §5 either depends on them or would have to work around them.

Those three are fixed first, in Part 1, before anything is built on top of them.

The twenty-one product questions this document opened were answered on 6 September 2026 and are locked in §0. Four minor items remain, listed in §16. The design is ready to build against.
