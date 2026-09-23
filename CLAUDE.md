# CLAUDE.md — Sunrise School ERP

## Read these first, in this order

0. **`SINGLE_SOURCE_OF_TRUTH.md`**, **`SESSION-HANDOFF-9.md`**, & **`SESSION-HANDOFF-10.md`** — **start here.**
   The canonical single source of truth and session handoffs for the ERP.
   Details current git status (`slice/office-feedback`), verified 31 live web screens,
   18 active staff, database tables (reception tables added),
   Alembic migration head `d4e5f6a7b8c9` (`receptionist_operations.py`), leadership credentials (`admin@sunrisepublic.edu` / `Admin@123`),
   Session 10 completed & verified (735 passed backend tests, 1 skipped, 0 failed, 100% green; 84 passed web unit tests across 18 files; 0 TypeScript errors on web and mobile; clean Vite production build; 5 new Front Desk operational modules live: Found & Lost, Student Gate Passes, Meeting Slips, Important Directory, Reception Fee Counter; complete-month fee collection invariant; Admission Dossier print enhancement; Front-desk sidebar navigation leak cleanly resolved with 12/12 automated checks passing).
   Supersedes all previous session handoffs.
1. **`FRONTEND-HANDOFF.md`** — the brief for **Parts Two to Six**: the
   three contracts, what "clean and easy for a school office" means, the
   remaining packets, the report format every packet owes, and the traps list.
2. **`HANDOFF.md`** (this directory) — current state, the commits and why each
   exists, and what is explicitly *not* verified.
3. **`docs/ERP_BLUEPRINT.md` §0** — the 21 locked product decisions. **§0 wins
   over anything else in that document**; the rest was written before those
   answers and is corrected only where it would mislead.
4. **`docs/ERP_BLUEPRINT.md` §12** — the four-part delivery plan.

`docs/BLUEPRINT.md` is the original v0 build contract. Still useful for the
reasoning behind the original design, but superseded wherever the ERP blueprint
disagrees.

## What this is

A multi-tenant school ERP being sold to **separate, independent schools** — not
branches of one school. A tenant is a customer.

**`main` IS the ERP** as of 10 September 2026: PR #1 merged the
`part-1-foundation` branch (126 commits) with a merge commit, and **CI is green
on both jobs** — backend lint, 615 tests, migrations from an empty schema, seed
and worker; web typecheck, schema drift, 31 tests and build. CI runs on every
push to `main` or `part-*`.

Those two figures are `main`'s. On `slice/office-feedback` they are **735 passed
backend (1 skipped, 736 total, 0 failed)** and **84 passed web unit tests (2 skipped in 18 files)**;
CI has never run on that branch because it has never been pushed.

**Nothing is deployed**, and one thing blocks that regardless of frontend work:
every account the ERP creates gets a fixed default password with no forced
change on first login (`students.py`, `teachers.py`, `services/conversion.py`;
recorded as a gap in `ERP_BLUEPRINT` §§5 and 11). That is a product decision
about how accounts are issued and has deliberately not been made.

## Commands

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q          # 615 on main, 735 on slice/office-feedback
../.venv/Scripts/python.exe -m pytest tests/test_rbac.py -q       # one file
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe seed.py               # idempotent
../.venv/Scripts/python.exe worker.py --once      # drain the job queue
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cd web && npx tsc --noEmit && npm run dev

cd mobile && npx tsc --noEmit && npx expo start --go --lan --port 8081
```

## Key Logins & Role Isolation (RBAC)

- **Leadership / Admin**: `admin@sunrisepublic.edu` (`Admin@123`) — Full school-wide administrative access across all modules. Retains the executive **Admission Dashboard** (`/admission`) with cycle overview, conversion funnels, and class intake capacities. To keep the sidebar uncluttered, the 5 operational queues are segregated from the Admin sidebar.
- **Dedicated Receptionist**: `receptionist@sunrisepublic.edu` (`Admin@123`) — Dedicated front desk operational staff. Lands directly on `#/admission/enquiries`. Owns Enquiries, Notices, and all 5 Front Desk operational modules: Found & Lost (`/reception/found-items`), Student Gate Passes (`/reception/passes`), Meeting Slips (`/reception/meetings`), Important Directory (`/reception/directory`), and Reception Fee Counter (`/reception/fee-counter`). Navigation strictly hardened: `Applications`, `Merit & selection`, `Waitlist`, `Admission reports`, and all admin fee management screens (`Fees`, `Defaulters`, `Fee setup`, `Period close`, `Student fees`) are completely removed; direct URLs are protected with in-page refusal and backend HTTP 403 Forbidden.
- **Admission Officer**: `admission@sunrisepublic.edu` (`Admin@123`) — Owns the complete admission pipeline: Enquiries, Applications, Merit Ranking, Waitlist, Admission Reports, and atomic fee payment enrollment. Navigation strictly hardened: `Students`, `Classes`, and `Notices` are completely removed from the sidebar; direct URLs `#/students`, `#/classes`, and `#/notices` are protected with in-page refusal and backend HTTP 403 Forbidden.
- **Fee Counter Clerk**: `counter@sunrisepublic.edu` (`Admin@123`) — Read ledger, view defaulters; cannot void payments or alter concessions.

## Recent Features Built & Verified (14–23 Sep 2026)

1. **Main Dashboard Upgrade (Attendance Overview)**:
   - Replaced the top 4 summary cards (`Total Students`, `Total Teachers`, `Total Classes`, `Fees Collected`) with a dedicated live **Attendance Overview** section (100 students, 90 present, 10 absent, 90% rate).
2. **Receptionist Role & Admission Queue Isolation**:
   - Seeded `receptionist@sunrisepublic.edu` (`Admin@123`) front desk login with exclusive access to the 5 operational admission queues.
3. **Staff Payroll Batches & Disbursal (`/payroll`)**:
   - Monthly salary batch calculation across all 18 staff with statutory EPF/ESI/TDS registers, printable CBSE payslips, and bank CSV export.
4. **Session Rollover & Promotion Wizard (`/admin/session-rollover`)**:
   - 4-step progression wizard from 2025-26 to 2026-27 with dynamic roll numbers, class overrides, and typed PROMOTE audit gate.
5. **Teacher Leave Management & 100% Substitution Coverage Gate (`/staff-leave`)**:
   - Mobile teacher leave queue with timetable conflict checking and locked approval gate requiring 100% substitution coverage before approval.
6. **Teacher Recruitment Decommissioned (Session 9)**:
   - Recruitment decommissioned and purged across backend, database, seed data, and web UI per owner directive.
7. **Simple Database Data-Flow Guide**:
   - Publication of `docs/Sunrise-ERP-Operational-Data-Flows.pdf` detailing `TABLE → TABLE → TABLE` flows, PK/FK connections, and Student ID vs Enrollment ID rules.
8. **Session 6 — Database Schema Refactoring (`enrolment_id` Migration)**:
   - Migrated `marks` and `homework_submissions` to require `enrolment_id` (`BigInteger, NOT NULL, FK -> enrolments.id`), removing legacy `student_id` columns from both tables. Compound unique constraints ensure an enrolment holds at most one mark per exam schedule and one submission per homework.
   - Migrated `grievances` to carry `enrolment_id` (`BigInteger, NULLABLE, FK -> enrolments.id`) for year-scoped parent grievance context.
   - Upholds foundational ERP invariant: *"Year-scoped facts hang off `enrolment_id`; lifetime facts hang off `student_id`"*.
   - Proven read/input translation only: `Mark.student_id` is a `@hybrid_property` with no setter (`AttributeError` on write); legacy `student_id` inputs are strictly resolved against section roster or rejected with HTTP 403 / 422. Enforced by 7 automated invariant tests.
9. **Session 6 — Mobile App Operational Depth (`mobile/app`)**:
   - **Teacher**: Morning roll-call marking with status toggles (`attendance.tsx`), Homework Manager with grading drawer (`homework.tsx`), Test Marks Entry Keypad with CBSE scale resolution (`results.tsx`).
   - **Parent**: Monthly attendance calendar with sick leave request (`attendance.tsx`), Real-time fee ledger & official 2-copy downloadable PDF receipt (`fees.tsx`), CBSE report card viewer with outstanding dues withholding gate (`results.tsx`), School broadcast alerts (`notices.tsx`).
   - **Student**: Section weekly timetable schedule (`timetable.tsx`), Digital homework turn-in modal (`homework.tsx`), Term exam results scorecard (`results.tsx`).
   - Verified across 8 visual proofs in `docs/screenshots/` and 21/21 Expo doctor checks.
10. **Session 7 — Complete Admission Pipeline & Atomic Student Enrollment on Fee Payment**:
    - Fee payment dynamically sourced from `cycle.application_fee` serves as the sole atomic enrollment trigger, eliminating manual conversion and creating `application_payments`, permanent `students` (`SCH-YYYY-NNNN`), `enrolments`, student credentials (`admission_no` / `Student@123`), guardian links, and document migration with transactional rollback.
    - Printable CBSE multi-page A4 Application Dossier, A5 Enquiry Slip with parent checklist and tear-off counterfoil, and 1/3 A4 landscape Fee Receipt Voucher with dual authorization stamps.
    - Strict RBAC Navigation & Route Hardening: Admission Officer (removed Students, Classes, Notices; 403 on direct URLs), Receptionist (removed Applications, Merit, Waitlist, Reports; 403 on direct URLs). Super Admin/Principal navigation 100% intact.
11. **Session 7 — Mobile API Dynamic Connectivity & Password Visibility Eye Toggle**:
    - Dynamic host IP resolution via `Constants.expoConfig?.hostUri` / `Constants.manifest2?.extra?.expoGo?.debuggerHost` eliminating physical Android `127.0.0.1:8000` ConnectException. Uvicorn `--host 0.0.0.0 --port 8000` LAN binding.
    - Interactive password visibility eye toggle inside password input (`eye-outline` vs `eye-off-outline`), default hidden, resetting on role tab switch.
12. **Complete Digital Admission Dossier (Application 360° Major Overhaul — 21 Sep 2026)**:
    - Re-architected Application 360° into a complete, fully editable Digital Admission Dossier with 10 modular tabs (`web/src/components/admission/dossier/`), supporting complete CBSE data capture across 11 official sections. Seeded and verified demo profiles: **Aarav Sharma** (#91) and **Ananya Verma** (#92). Publication guide generated at `docs/Sunrise-ERP-Admission-Demo-Guide.pdf` (265 KB).
13. **Session 9 — Mobile Navigation Redesign, Fee Graph Removal, Recruitment Purge & Red-X Controls**:
    - **Mobile Navigation Redesign**: 4 bottom tabs per role (Parent: Home, Child, Fees, Profile; Teacher: Home, Classes, Attendance, Profile; Student: Home, Timetable, Homework, Profile); top-left hamburger opening reusable `NavDrawer.tsx` with user profile header, multi-child switcher, categorized menu sections (`ACADEMICS`, `OPERATIONS`, `COMMUNICATION`, `OTHER`), and confirmation-guarded Logout; hidden tabs preserved via `options={{ href: null }}` with zero feature loss.
    - **Admin Dashboard Fee Collection Graph Removal**: Cleanly removed `<Card title="Fee Collection">` Recharts chart from `web/src/pages/Dashboard.tsx` with balanced grid layout.
    - **Teacher Recruitment Decommissioning**: Purged all backend models, services, APIs, permissions, module flags, and seed rows; dropped tables `candidates` and `candidate_offers` via migration `c3d4e5f6a7b8`; deleted web `/recruitment` route, page, and components; regenerated API types.
    - **Global Red-X Close Controls**: Standardized modal/dialog dismiss controls to Red X icon buttons across web and mobile.
14. **Session 10 — Receptionist Operational Responsibilities & Sidebar Cleanup (23 Sep 2026)**:
    - **Found & Lost Register (`/reception/found-items`)**: Multi-step found item intake, broadcast alerts, student verification search, and claim/handover tracking with photo recording (`found_items` table).
    - **Student Gate Pass & Authorized Roster (`/reception/passes`)**: One-time early departure gate passes (`student_passes`), permanent pre-approved pickup roster (`student_authorized_persons`), and official printable A5 gate pass slip (`PrintableStudentPass.tsx`).
    - **Visitor Meeting Slips (`/reception/meetings`)**: Dual-tab visitor workflow for Principal executive appointments and Teacher academic parent interactions with Accept/Wait/Decline response states and printable slips.
    - **Important Emergency Directory (`/reception/directory`)**: 7 seeded verified civic, police, and medical contacts; read-only for receptionist, full CRUD for admin.
    - **Front Desk Fee Counter (`/reception/fee-counter`)**: Student lookup, FIFO invoice settlement, complete-month-only collection invariant, and printable receipt voucher (`PrintableFeeReceiptSlip.tsx`).
    - **Admission Dossier Print Enhancement**: Upgraded `PrintableAdmissionDossier.tsx` with all mandatory audit fields.
    - **Sidebar Navigation Leak Fix**: Removed `fees.invoice.read` from receptionist to cleanly eliminate admin fee screens (`Fees`, `Defaulters`, `Fee setup`, `Period close`) from front desk sidebar navigation. Verified with 12/12 automated browser checks.

## Active Status (Session 10 Complete, Session 11 Handoff)

Canonical specification for Session 11 is defined in **`SESSION-HANDOFF-10.md`**:
1. **Teacher Meeting Slip Response Interface**: Wire teacher view on web/mobile (`mobile/app/(teacher)/meetings.tsx`) to inspect incoming visitor slips and respond (`ACCEPTED` / `DECLINED`).
2. **Real Image / Photo Upload Pipeline for Front Desk**: Multipart upload endpoint `POST /admin/reception/upload` for found items and handover photos, replacing plain text URLs with file pickers / camera capture.
3. **End-to-End Visual Verification for Live Printable Slips**: Automated Puppeteer runner creating live transactions and capturing proof screenshots of all 4 printable slips (`PrintableStudentPass`, `PrintablePrincipalMeetingSlip`, `PrintableTeacherMeetingSlip`, `PrintableFeeReceiptSlip`).
4. **Public Online Admission Portal UI (`/apply`)**: Unauthenticated parent application portal.
5. **System-Wide Audit Reason Sweep (Packet 4 Contract 3)**: Ensuring 100% of destructive operations prompt mandatory user-typed reasons.

Upcoming Web Roadmap:
1. **Public Online Admission Portal UI (`/apply`)**: Parent-facing unauthenticated landing page and registration form with CAPTCHA/bot protection connecting to existing `/public/admission/*` endpoints.
2. **Packet 4 — Contract 3 System-Wide Audit Reason Sweep**: System-wide enforcement pass ensuring 100% of destructive operations prompt a mandatory user-typed reason modal recorded in `audit_log`.
3. **Academic Year Manager UI (`/configuration`)**: Front-end wizard for clerks to activate/deactivate terms and academic years without developer API calls.
4. **Third-Party Integrations (V2 Scope)**: Razorpay/Easebuzz fee gateway, TRAI DLT SMS & WhatsApp alerts, bulk Excel roster importer, AIS-140 GPS bus tracking.

Postgres runs natively on this machine, not in Docker. `make testdb` uses
`docker compose exec` and fails here — create `sunrise_test` by hand.

## Architecture rules that matter

- **Three layers.** `api/` is thin, `services/` holds the rules, `models/` holds
  the schema. Business logic does not live in a route.
- **Permission at the route, scope in the service.** `require_permission()`
  decides *may you at all*; `services/scoping.py` decides *over which rows*.
  Keep them separate.
- **Every table carries `school_id`.** It is declared on `TenantBase` so a new
  table cannot quietly be created without one. A missing tenant key is a data
  leak between customers, not a style problem.
- **Year-scoped facts join through `enrolment_id`; lifetime facts through
  `student_id`.** Getting this backwards reintroduces the bug the enrolment
  split exists to fix.
- **Reads never write.** Nothing in a GET may commit.
- **Business rules belong in database constraints** where they can be — unique
  constraints, partial indexes, foreign keys — not only in Python.
- **Staff are `employees`, not `teachers`; `guardians`, not `parents`.** The
  columns that name a teaching role in context — `class_teacher_id`,
  `class_subject_teacher.teacher_id` — keep their names on purpose, as do the
  `/teacher` and `/parent` URL prefixes the mobile app calls.
- **An applicant is not a user.** Nothing in Admission may require a
  `students` or `users` row: most applicants never get one. The links that do
  exist — a sibling, a staff parent — are claims until verified, and an
  unverified claim must never influence a decision.
- **Per-school configuration goes through the registries**, not through new
  columns: `core/settings_registry.py` for settings and feature flags,
  `custom_fields` for school-invented attributes. A feature flag is a boolean
  setting named `feature.<module>`, and it is enforced at the route.
- **Money is `Numeric`, never float. Timestamps are `timestamptz`.** Round with
  `services/fee_setup.py::money()` — half-up, the way a counter clerk rounds;
  Python's default is banker's rounding and puts a 10% concession a paisa away
  from the printed fee card.
- **Payments allocate to invoice lines, never to invoices.** A balance is a SUM
  over `payment_allocations`, never a stored column. Nothing financial is
  edited: an invoice is voided and reissued, a payment reversed by a contra
  entry.
- **Destructive actions are audited with a reason.** See `services/audit.py`;
  `void`, `status_change` and `delete` refuse to commit without one.

## Traps that have already cost time

- **The test suite builds its schema from the models (`create_all`), not from
  the migrations.** A dropped `server_default` once slipped through this gap.
  `tests/test_migrations.py` covers it — do not delete that test to speed the
  suite up.
- **`BCRYPT_ROUNDS` is 4 in tests, 12 everywhere else.** Never lower it outside
  tests.
- **SQLite returns naive datetimes** even for `timestamptz`; comparing against
  an aware `now` raises.
- **Demo logins changed.** Admission numbers are `2024000001`, not `SPS2024001`.
- **`/admin/settings` is the school's profile and branding.** The setting store
  and module switches are `/admin/configuration`.
- **The Postgres test database is dropped by schema, not by `drop_all`** — a
  leftover v0 table once made the whole suite unable to start.
- **`/public/{school_code}/...` is unauthenticated.** Its 404s are deliberately
  identical across unknown school, suspended school, module off, wrong
  application number and wrong date of birth. Do not make any of them more
  helpful.
- **Local date against UTC midnight is a bug**, and it has already bitten once:
  the office is five and a half hours ahead of the column.
- **`seed.py` runs the real fee and timetable services**, so a defect in either
  breaks seeding rather than only a test. That is on purpose: a seed that
  fabricates rows cannot catch a bug in the code that will produce them.
- **Seeded invoices already carry late fees**, because collection assesses the
  fine before allocating. Do not assume a seeded invoice has a round amount.
- **A whole-school read must narrow a teacher, and the permission layer will
  not do it.** A teacher holds most `.read` permissions school-wide, with the
  restriction in the service, so `school_wide=True` stops a guardian and nobody
  else. Any route or report answering across sections calls
  `scoping.narrow_to_own_sections()`. Two attendance screens skipped it and
  handed a class teacher all 100 children.
- **A report is gated twice, not once.** `require_permission(school_wide=True)`
  stops a guardian; it does not stop a teacher, who holds most `.read`
  permissions school-wide with the restriction in the service. Reports go
  through `services/reports.py::_authorise()`, which does both. Add a report by
  adding a registry entry and a runner — never by writing a query.
- **Money rules are settings, not constants.** The late fee, the sibling
  concession, the due day and the teacher load ceiling all live in
  `core/settings_registry.py`; changing behaviour by editing a number in code
  is the wrong place.
- **Receptionist vs Admin sidebar isolation**: Do not add operational admission queues back to the Admin sidebar; Admin retains only `/admission` (executive cycle overview & intake capacities), while Receptionist exclusively sees the 5 operational queues and is blocked from `/dashboard` and all other screens.
- **Year-scoped facts must never hold `student_id`**: Marks, homework submissions, and daily attendance records attach strictly to `enrolment_id`. `Mark.student_id` is a read-only `@hybrid_property` without a setter — never attempt to assign `mark.student_id = x` or instantiate `Mark(student_id=x)`.
- **Services `flush()`, Endpoints `commit()`**: Service functions in `app/services/` must call `db.flush()`, NEVER `db.commit()`. Calling `db.commit()` inside service logic breaks per-test transaction savepoint isolation (`join_transaction_mode="create_savepoint"` in `conftest.py`), causing uncommitted data from one test to leak into subsequent tests or violate foreign key constraints. Commits belong exclusively in API route handlers (`app/api/`).
- **Operational seed rows must avoid `teacher_1` and slot 1**: When adding sample data to `seed.py` for operational tables (such as leave requests or substitutions), never attach them to `teacher_1` (`TCH001`) or the first timetable slot (`id=1`). The test suite fixtures assume `teacher_1` opens with a clean zero-used balance, and slot 1 is used by timetable tests to verify deletion without FK violations. Target `teachers[-1]` instead.
- **React Native Hermes `window` polyfill trap**: In React Native with Hermes, `typeof window !== "undefined"` evaluates to `true` (`window === globalThis`). Never rely on `typeof window` to branch between web and mobile environments; use `Platform.OS === 'web'` and query `Constants.expoConfig?.hostUri` to dynamically discover developer machine LAN IP.
- **Uvicorn `0.0.0.0` host binding trap for physical mobile devices**: When testing on physical mobile devices over Wi-Fi, Uvicorn MUST be started with `--host 0.0.0.0 --port 8000`. Omitting `--host` binds exclusively to `127.0.0.1`, which refuses connections from external LAN clients even if they are on the same Wi-Fi subnet.
- **Fee invoice serialization key**: In `backend/app/services/fees.py`, the net invoice amount is keyed as `"payable"`, with `"balance"` for outstanding dues. Frontend clients looking for `invoice.total` or `invoice.amount` silently resolve to `undefined` or `0.00` if `payable` is omitted from property lookups.
- **Boolean strict equality traps in filters**: Never combine mutually exclusive equality checks with `&&` (e.g. `val === null && val === undefined` is mathematically impossible in JavaScript and always evaluates to `false`). Use loose equality `val == null` or logical OR `val === null || val === undefined`.
- **Guardian serialization completeness**: In `backend/app/api/admin/applications.py`, ensure all columns from `ApplicationGuardian` (`qualification`, `office_address`, `date_of_birth`, etc.) are explicitly serialized in `_guardian_out`. Missing keys silently drop edited fields on browser reload even though they exist in the database.
- **Dynamic enrollment resolution on application detail**: When an applicant is enrolled, `application.student_id` links to the lifetime `students` row, but class, section, and roll number exist on the annual `enrolments` row. Always resolve `enrolled_student` dynamically via `db.get(Student, app.student_id)` and the active enrolment record.
- **`Enrolment` academic year relationship trap**: The `Enrolment` model has `academic_year_id` (`BIGINT`), NOT an `academic_year` ORM relationship. Accessing `enrolment.academic_year.code` raises `AttributeError`. Safely resolve via `db.get(AcademicYear, enrolment.academic_year_id)` or fallback to `application.cycle.academic_year.code`.
- **ActionButton form submission**: Using `<ActionButton>` inside a `<form onSubmit={...}>` with an explicit `type="submit"` requires that `ActionButton` pass `type="submit"` through to the underlying `<button>` and allow `onClick` to be optional; otherwise, the browser does not fire the synthetic form submit event.

## Working style for this project

- Verify before claiming. Run the thing; do not report from reading the code.
- Commit messages carry the reasoning — why, not just what.
- Show the exact file list before any push.
- Ask before adding a dependency over 100 MB.
