# MEMORY.md — Sunrise School ERP

**Date:** 21 September 2026  
**Canonical State Document:** [`SINGLE_SOURCE_OF_TRUTH.md`](SINGLE_SOURCE_OF_TRUTH.md)  
**Completed Milestone:** Session 9 Completed: Mobile Navigation Redesign (Acharya Prashant 4 Bottom Tabs + Drawer), Admin Dashboard Fee Graph Removal, Teacher Recruitment Decommissioning, and Global Red-X Controls.  
**Active Session Specification:** [`SESSION-HANDOFF-9.md`](SESSION-HANDOFF-9.md)  
**Active Branch:** `slice/office-feedback` (strictly local-only per owner directive)  
**Alembic Migration Head:** `c3d4e5f6a7b8` (`c3d4e5f6a7b8_drop_recruitment_tables.py`)  

---

## 1. Executive Summary & Current Status

Sunrise School ERP is a multi-tenant school management system built for independent private schools.
- **Backend Test Suite**: **729 passed, 1 skipped, 0 failed** in 229s (100% green across all 730 tests).
- **26 Live Screens** registered in `web/src/screens.ts` (all functional and permission-gated; recruitment purged).
- **18 Active Staff** in employee directory (`employees`).
- **Database**: PostgreSQL tables in `sunrise_test`. Alembic head `c3d4e5f6a7b8` drops `candidates` and `candidate_offers`.
- **TypeScript**: 0 errors across backend, web (`npx tsc --noEmit`), and mobile (`npx tsc --noEmit`).
- **Web Unit Tests**: Vitest 2.1 — **82 passed, 2 skipped across 18 test files** (100% green).
- **Mobile Stack**: Expo SDK 57, React Native `0.86.3`. Navigation redesigned with 4 bottom tabs per role, top-left hamburger opening smooth drawer (`NavDrawer.tsx`), multi-child switcher, and zero lost features via `options={{ href: null }}`. Red X dismiss buttons.
- **Primary Canonical PDFs in `docs/`**:
  1. `Sunrise-ERP-Admission-Demo-Guide.pdf` (265 KB, Complete Digital Admission Dossier & Interactive Testing Guide)
  2. `Sunrise-ERP-Operational-Data-Flows.pdf` (1.31 MB, Simple Table-to-Table Data-Flow Guide)
  3. `Sunrise-ERP-Database-Tables-and-Features.pdf` (7.76 MB, All-tables feature mapping)
  4. `Sunrise-ERP-Database-Viva-100.pdf` (2.20 MB, 100 Viva questions & architectural answers)
  5. `Sunrise-ERP-Features-Operational-and-Planned.pdf` (723 KB, 27 screens inventory)
  6. `Sunrise-ERP-Database-Essentials-Explained.pdf` (1.78 MB, 16 business process workflows)
  7. `Sunrise-ERP-Database-Essentials.pdf` (1.21 MB, 68 live tables & ERDs)
  8. `Sunrise-ERP-Database.pdf` (1.92 MB, 93 tables full schema reference)

---

## 2. Completed Features & Verified Milestones

### A. Database Schema Refactoring (`enrolment_id` Migration) — Session 6 Complete
- **Physical Column Elimination**: Removed `student_id` from `marks` and `homework_submissions`; made `enrolment_id` (`BIGINT NOT NULL REFERENCES enrolments(id)`) mandatory. Compound unique constraints ensure an enrolment holds at most one mark per exam schedule and one submission per homework.
- **Grievances Scoping**: Added `enrolment_id` (`BIGINT NULL REFERENCES enrolments(id) ON DELETE SET NULL`) to anchor parent/student grievances to the relevant academic year.
- **Alembic Migration**: Revision `b2c3d4e5f6a7_enrolment_id_refactor.py` (down revision `a1b2c3d4e5f6`). 100% of existing rows backfilled cleanly from active enrolments. Bidirectional upgrade/downgrade verified clean.
- **Backward Compatibility Scrutiny & Invariant Enforcement**:
  - `Mark.student_id` is a `@hybrid_property` with **strictly no setter** (`AttributeError: can't set attribute` on any mutation or instantiation).
  - `HomeworkSubmission` and `Attendance` have no `student_id` column or attribute on write.
  - Ingestion translation resolves inputs strictly against `roster(db, sched.class_section_id)`; cross-section or past-year IDs are refused with HTTP 403 / 422.
  - Enforced by 7 automated tests in [`backend/tests/test_enrolment_id_invariant_enforcement.py`](backend/tests/test_enrolment_id_invariant_enforcement.py).

### B. Mobile App Operational Depth — Session 6 Complete
- **Teacher Mobile App (`mobile/app/(teacher)`)**:
  - In-classroom morning roll marking with fast status toggles (`attendance.tsx`).
  - Homework assignment composer and student turn-in grading drawer (`homework.tsx`).
  - Compact mobile test marks entry keypad with real-time validation and CBSE scale resolution (`results.tsx`).
- **Parent Mobile App (`mobile/app/(parent)`)**:
  - Monthly color-coded attendance calendar & medical leave application (`attendance.tsx`).
  - Real-time fee ledger and 1-click official 2-copy PDF receipt download (`fees.tsx`).
  - Official CBSE term report card PDF download with outstanding fee dues withholding gate (`results.tsx`).
  - School broadcast push notices listener (`notices.tsx`).
- **Student Mobile App (`mobile/app/(student)`)**:
  - Weekly 6-period timetable viewer & digital homework turn-in upload (`timetable.tsx`, `homework.tsx`).
  - Personal exam marks scorecard and grade bands viewer (`results.tsx`).
- **Visual Verification Proofs**: All 8 mobile screenshot proofs captured and documented in `docs/screenshots/`.

### C. Teacher Leave Management & 100% Substitution Coverage Gate (`/staff-leave`)
- Teachers apply for leave via mobile app (`mobile/app/(teacher)/leave.tsx`).
- Admin reviews leave queue on `/staff-leave` with timetable conflict detection.
- **100% Coverage Gate**: The "Approve Leave" button is strictly locked until 100% of vacant periods have substitute teachers assigned via the free-teacher selector.
- Upon approval, relief duties activate in `substitutions` and in-app alerts dispatch via `in_app_notifications`. Rejection purges draft substitutions.

### D. Teacher Recruitment Decommissioned (Session 9)
- Decommissioned and purged across backend (models, services, APIs, permissions, modules, seeds), database tables (`candidates`, `candidate_offers` dropped in migration `c3d4e5f6a7b8`), and web UI (`/recruitment` page and components deleted). Operational depth focuses on core school administration.

### E. Monthly Staff Payroll Batches & Disbursal (`/payroll`)
- Compensation structures and allowances.
- Monthly payroll batch calculation across all 18 staff with statutory EPF (12%), ESI (0.75%), and TDS.
- Printable CBSE payslips and bank disbursal CSV export.

### F. Academic Session Rollover & Promotion Wizard (`/admin/session-rollover`)
- 4-step progression wizard advancing students from 2025-26 to 2026-27.
- Cohort roster review, promote/detain overrides, dynamic roll numbers.
- Preserves historical records: prior `enrolments` marked `promoted`; new `enrolments` inserted as `active`; permanent `students` record untouched.

### G. Complete Admission Pipeline & Immediate Student Enrollment — Session 7 Complete
- **Fee Payment as Sole Enrollment Trigger**:
  - Eliminated manual "Convert to Student" button.
  - Dynamically configured application fee (`cycle.application_fee`) payment atomically creates:
    - `application_payments` record (sequential receipt number)
    - Permanent `students` record (`SCH-YYYY-NNNN`)
    - Annual `enrolments` record with balanced section allocation
    - Student user credentials (`username: admission_no`, `password: Student@123`)
    - Linked `student_guardians` and migrated application documents
    - Complete transactional rollback on any exception.
- **Printable CBSE School Assets**:
  - Multi-page A4 Dossier with clean sections (biodata, guardians, medical, documents, signatures, seal).
  - Printable A5 Enquiry Slip with parent checklist and tear-off counterfoil.
  - Printable 1/3 A4 landscape Application Fee Receipt Voucher with dual authorization stamps.
- **RBAC Navigation & Direct URL Hardening**:
  - Admission Officer (`admission@sunrisepublic.edu`): `Students`, `Classes`, and `Notices` completely removed from sidebar; direct URLs `#/students`, `#/classes`, `#/notices` blocked with in-page refusal and HTTP 403. Retains full admission pipeline ownership.
  - Receptionist (`receptionist@sunrisepublic.edu`): `Applications`, `Merit & selection`, `Waitlist`, and `Admission reports` completely removed; direct URL `#/admission/applications` blocked with in-page refusal and HTTP 403. Focuses strictly on Enquiries and candidate intake.
  - Super Admin (`admin@sunrisepublic.edu`) and Principal (`principal@sunrisepublic.edu`) navigation and access across all 22 modules remain 100% intact.

### H. Mobile API Connectivity & Password Visibility Toggle — Session 7 Complete
- **Root Cause & Fix for Physical Android Device Connection Failure**:
  - Root cause: In React Native / Hermes, `typeof window !== "undefined"` evaluates to `true` (`window === globalThis`), causing `mobile/src/api/client.ts` to hardcode `http://127.0.0.1:8000`. On a physical phone, `127.0.0.1` resolved to the phone itself, producing `ConnectException: Failed to connect to /127.0.0.1:8000`.
  - Resolution: Dynamically resolves developer host IP via `Constants.expoConfig?.hostUri` / `Constants.manifest2?.extra?.expoGo?.debuggerHost` (e.g. `192.168.29.227:8081`). Respects `process.env.EXPO_PUBLIC_API_URL` when non-loopback; falls back to `10.0.2.2` on Android emulator and `127.0.0.1` on web/iOS simulator.
  - Backend Uvicorn binding: Started with `--host 0.0.0.0 --port 8000`, enabling LAN devices on `192.168.29.xxx` to communicate directly with the API.
- **Password Visibility Eye Toggle**:
  - Interactive toggle inside password input right edge on `mobile/app/index.tsx`.
  - Uses `@expo/vector-icons/Ionicons` (`eye-outline` vs `eye-off-outline`).
  - Default hidden (`secureTextEntry={!showPassword}`); tapping toggles plain text without clearing or modifying entered password.
   - Shared across Student, Parent, and Teacher roles; automatically resets to hidden on role tab switch.

### I. Complete Digital Admission Dossier — Application 360° Major Overhaul (21 Sep 2026)
- **Authoritative Invariant Satisfied**: *"APPLICATION 360° = COMPLETE DIGITAL ADMISSION DOSSIER. It must contain and allow the Admission Cell to COMPLETE and EDIT the complete information required for admission of a student."*
- **10 Modular Dossier Tabs (`web/src/pages/admission/Applications.tsx`)**:
  - `Student Details` (`DossierStudentDetails.tsx`): First name, middle name, last name, DOB, gender, blood group, nationality, religion, category, mother tongue, Aadhaar number. Full edit and patch support.
  - `Admission Details` (`DossierAdmissionDetails.tsx`): Target class (`class_id`), stream (`stream`: Science, Commerce, Humanities), second language, third language, admission type, day scholar vs hosteler (`residential_status`), school transport opted (`opt_transport`), pickup/drop bus stops.
  - `Guardians` (`DossierGuardians.tsx`): Father, Mother, Local Guardian editable profiles: full name, relation, mobile, email, occupation, employer, annual income, educational qualification, office address, residential address, primary and emergency contact toggles.
  - `Siblings` (`DossierSiblings.tsx`): Real school sibling linking: Sibling Name, Class/Section, Admission Number, dynamic student record lookup & verification link.
  - `Address` (`DossierAddress.tsx`): Present and Permanent postal addresses with 1-click "Same as Present Address" copy checkbox.
  - `Previous School` (`DossierPreviousSchool.tsx`): School name, board (CBSE, ICSE, State), last class passed, passing year, marks % / CGPA, TC number, TC issue date, reason for leaving.
  - `Medical` (`DossierMedical.tsx`): Blood group, height (cm), weight (kg), existing medical conditions, allergies, regular medications, emergency doctor/hospital contact name & phone, special care instructions.
  - `Documents` (`DossierDocuments`): CBSE compliance checklist & viewer for 7 required certificates with verification status badges.
  - `Declarations` (`DossierDeclarations.tsx`): Parent/guardian declaration, student rules acceptance, transport guidelines pledge, anti-ragging undertaking, date of declaration, signatory name.
  - `Selection & Enrollment` (`DossierEnrollmentResult.tsx`): Entrance test score, interview notes, reviewer recommendation, status change actions, atomic fee collection trigger with class & section allocation, and permanent enrollment result banner (Admission No, Academic Year, Class & Section, Roll No, login credentials).
- **Backend Schema & Serializer Alignment**:
  - Serialized `date_of_birth`, `qualification`, `office_address` on `ApplicationGuardian` (`_guardian_out` in `backend/app/api/admin/applications.py`).
  - Dynamic resolution of `enrolled_student` in `_detail()` querying `Student`, `Enrolment`, and `AcademicYear` safely without invalid ORM attributes.
  - Extended `ActionButton` to support `type="submit"` and optional `onClick`; enhanced `useWrite` with `runAsync`.
- **Two Seeded & Verified Demo Students**:
  - **Aarav Sharma** (`APP-2026-0091`, Grade 1): Submitted status, complete bio, parents (HCL Tech VP father, DPS Headmistress mother), elder sibling (Ananya Sharma in Class 4-A), medical & address data.
  - **Ananya Verma** (`APP-2026-0092`, Grade 11 Science): Enrolled status, admission fee paid (`REC-2026-0092`), permanent Student ID `SCH-2026-0092`, allocated to Class 11-A (Science PCM + CS), parents (CMO father, High Court Advocate mother), sibling (Kabir Verma in Class 8-B).
  - Verified by dedicated automated test suite `backend/tests/test_admission_dossier_demo.py` (2/2 passed, full backend suite 731 passed, 1 skipped).
- **Publication Guide Deliverable**:
  - `docs/Sunrise-ERP-Admission-Demo-Guide.pdf` (265 KB) with full visual walkthrough, screenshots, role permissions, and testing credentials.

### J. Session 9 — Mobile Navigation Redesign, Fee Graph Removal, Recruitment Decommissioning & Red-X Controls
- **Mobile Navigation Redesign (Acharya Prashant Concept)**:
  - 4 bottom tabs per role (Parent: Home, Child, Fees, Profile; Teacher: Home, Classes, Attendance, Profile; Student: Home, Timetable, Homework, Profile).
  - Reusable `mobile/src/components/NavDrawer.tsx` modal drawer triggered by top-left hamburger button in custom headers.
  - Profile header with initials, role badge, subtitle; multi-child switcher for parents; categorized menu sections (`ACADEMICS`, `OPERATIONS`, `COMMUNICATION`, `OTHER`); confirmation-guarded Logout.
  - Hidden tabs preserved via `options={{ href: null }}` on `<Tabs.Screen>` allowing direct navigation with zero lost functionality.
- **Admin Dashboard Fee Graph Removal**:
  - Removed `<Card title="Fee Collection">` Recharts chart from `web/src/pages/Dashboard.tsx`.
  - Balanced 2-column dashboard grid without empty containers or unused Recharts imports.
- **Teacher Recruitment Decommissioning**:
  - Dropped `candidates` and `candidate_offers` tables via migration `c3d4e5f6a7b8`.
  - Deleted models, services, APIs, permissions, modules, seed rows, and web frontend pages.
  - Regenerated API schema types (`web/src/api/schema.d.ts`).
- **Global Red-X Close Controls**:
  - Replaced textual "Close" buttons on modals/drawers across web and mobile with standardized Red X icon buttons (`#ef4444` / `text-red-500` / `theme.danger`).

---

## 3. Active Status: Session 9 Complete

Session 9 has been fully delivered and verified on local branch `slice/office-feedback` (strictly local-only):
- Backend tests: 729 passed, 1 skipped, 0 failed (100% green).
- Web unit tests: 82 passed, 2 skipped across 18 test files (100% green).
- Web typecheck: 0 errors (`npx tsc --noEmit`).
- Mobile typecheck: 0 errors (`npx tsc --noEmit`).
- Web build: clean Vite build (`npm run build`).
- Alembic migration head: `c3d4e5f6a7b8 (head)`.
- 26 live web screens.

1. **Student Home Isolation**: Remove `Today's Schedule` (Timetable) and `Latest Notices` cards from the Student Home dashboard (`mobile/app/(student)/dashboard.tsx`) while preserving dedicated tab routes.
2. **Parent Fees Accurate Invoicing**: Fix `₹0.00` display by resolving `invoice.payable` from `/parent/fees` backend response (`invTotal = invoice.payable ?? invoice.total ?? invoice.amount ?? 0`).
3. **Teacher Supplies Real Stock Consumption**: Add `"Use / Consume Stock"` workflow in `mobile/app/(teacher)/stock.tsx` and backend service `consume_stock`, updating `current_quantity`, logging audit trails, preventing over-consumption (`HTTP 400`), and automatically flagging `is_low_stock` when `<= min_quantity`.
4. **Universal Standardized Date Display**: Standardize all user-facing dates to `DD-MM-YYYY` using shared `formatDate(d)` helper across Student, Parent, and Teacher screens.
5. **Class Teacher Only Attendance Authorization**: Enforce `ClassSection.class_teacher_id == teacher.id` at the backend API level (`HTTP 403 Forbidden` for subject teachers) and filter mobile UI section dropdown.
6. **Student Homework Submitted Tab Fix**: Correct boolean filter bug in `mobile/app/(student)/homework.tsx` (`item.marks === null && item.marks === undefined` -> `item.submitted && (item.marks === null || item.marks === undefined)`).

### Upcoming Web Scope:
1. **Public Online Admission Portal UI (`/apply`)**:
   - Parent-facing unauthenticated landing page and registration form with CAPTCHA/bot protection connecting to existing `/public/admission/*` endpoints.
2. **Packet 4 — Contract 3 System-Wide Audit Reason Sweep**:
   - System-wide enforcement pass ensuring 100% of destructive operations (employee exits, status changes, mark overrides, invoice cancellations) prompt a mandatory user-typed reason modal recorded in `audit_log`.
3. **Academic Year Manager UI (`/configuration`)**:
   - Front-end wizard for clerks to activate/deactivate terms and academic years without developer API calls.
4. **Third-Party Integrations (V2 Scope)**:
   - Razorpay/Easebuzz fee gateway, TRAI DLT SMS & WhatsApp alerts, bulk Excel roster importer, AIS-140 GPS bus tracking.

---

## 4. Key Architectural Contracts & Invariants

1. **The Enrolment vs Student Invariant**:
   - `students.id` is permanent identity for life.
   - `enrolments.id` is the annual class session membership.
   - Year-scoped operational facts (attendance, marks, homework, fees, transport, report cards) must strictly hang off `enrolment_id`.
   - `Mark.student_id` is a read-only `@hybrid_property` with no setter — never write or instantiate with `student_id`.
2. **Services `flush()`, Endpoints `commit()`**:
   - Service functions in `app/services/` must call `db.flush()`, NEVER `db.commit()`. Calling `db.commit()` inside service logic breaks per-test transaction savepoint isolation (`join_transaction_mode="create_savepoint"` in `conftest.py`), causing uncommitted data from one test to leak into subsequent tests or violate foreign key constraints. Commits belong exclusively in API route handlers (`app/api/`).
3. **Operational Seed Rows Must Avoid `teacher_1` and Slot 1**:
   - When adding sample data to `seed.py` for operational tables (such as leave requests or substitutions), never attach them to `teacher_1` (`TCH001`) or the first timetable slot (`id=1`). The test suite fixtures assume `teacher_1` opens with a clean zero-used balance, and slot 1 is used by timetable tests to verify deletion without FK violations. Target `teachers[-1]` instead.
4. **Financial Immutability**:
   - Money is never edited in place; contra reversals remain mandatory.
   - Outstanding balance is always calculated as `SUM(invoice_lines) - SUM(payment_allocations)`.
5. **Screen Registry is Canonical (`web/src/screens.ts`)**:
   - Navigation, routing, permissions, and module hiding all derive from `SCREENS`.
6. **Tenant Isolation**:
   - Every table inherits `school_id` from `TenantBase`; queries without `school_id` are blocked.
7. **React Native Hermes `window` Polyfill Trap**:
   - In React Native with Hermes, `typeof window !== "undefined"` evaluates to `true` (`window === globalThis`). Never rely on `typeof window` to branch between web and mobile environments; use `Platform.OS === 'web'` and query `Constants.expoConfig?.hostUri` to dynamically discover developer machine LAN IP.
8. **Uvicorn `0.0.0.0` Host Binding Trap for Physical Mobile Devices**:
   - When testing on physical mobile devices over Wi-Fi, Uvicorn MUST be started with `--host 0.0.0.0 --port 8000`. Omitting `--host` binds exclusively to `127.0.0.1`, which refuses connections from external LAN clients even if they are on the same Wi-Fi subnet.
9. **Fee Invoice Serialization Key**:
   - In `backend/app/services/fees.py`, the net invoice amount is keyed as `"payable"`, with `"balance"` for outstanding dues. Frontend clients looking for `invoice.total` or `invoice.amount` silently resolve to `undefined` or `0.00` if `payable` is omitted from property lookups.
10. **Boolean Strict Equality Traps in Filters**:
   - Never combine mutually exclusive equality checks with `&&` (e.g. `val === null && val === undefined` is mathematically impossible in JavaScript and always evaluates to `false`). Use loose equality `val == null` or logical OR `val === null || val === undefined`.
11. **Guardian Serialization Completeness**:
   - In `backend/app/api/admin/applications.py`, ensure all columns from `ApplicationGuardian` (`qualification`, `office_address`, `date_of_birth`, etc.) are explicitly serialized in `_guardian_out`. Missing keys silently drop edited fields on browser reload even though they exist in the database.
12. **Dynamic Enrollment Resolution on Application Detail**:
   - When an applicant is enrolled, `application.student_id` links to the lifetime `students` row, but class, section, and roll number exist on the annual `enrolments` row. Always resolve `enrolled_student` dynamically via `db.get(Student, app.student_id)` and the active enrolment record.
13. **`Enrolment` Academic Year Relationship Trap**:
   - The `Enrolment` model has `academic_year_id` (`BIGINT`), NOT an `academic_year` ORM relationship. Accessing `enrolment.academic_year.code` raises `AttributeError`. Safely resolve via `db.get(AcademicYear, enrolment.academic_year_id)` or fallback to `application.cycle.academic_year.code`.
14. **ActionButton Form Submission**:
   - Using `<ActionButton>` inside a `<form onSubmit={...}>` with an explicit `type="submit"` requires that `ActionButton` pass `type="submit"` through to the underlying `<button>` and allow `onClick` to be optional; otherwise, the browser does not fire the synthetic form submit event.

