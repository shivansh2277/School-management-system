# MEMORY.md — Sunrise School ERP

**Date:** 12 November 2026  
**Canonical State Document:** [`SINGLE_SOURCE_OF_TRUTH.md`](SINGLE_SOURCE_OF_TRUTH.md)  
**Completed Milestone:** QA Audit Critical Defect Remediation Completed & Verified: **All 8 Issues Resolved** ([`remediation_plan.md`](remediation_plan.md)).
**Active Branch:** `slice/office-feedback` (synced with `origin/main` and `origin/slice/office-feedback`)  

---

## 1. Executive Summary & Current Status

Sunrise School ERP is a multi-tenant school management system built for independent private schools.
- **QA Audit Defect Remediation Suite**: **9/9 passed, 0 failed** (`tests/test_audit_defect_remediations.py`).
- **Migration & Empty DB Compatibility Suite**: **3/3 passed, 0 failed** (`tests/test_migrations.py`).
- **Active Migration Head**: `a2b3c4d5e6f0` (`a2b3c4d5e6f0_audit_defect_remediations.py`).
- **Public Announcements API**: 5/5 unit tests passed (`tests/test_public_announcements.py`).
- **Librarian RBAC**: 3/3 unit tests passed (`tests/test_librarian_rbac.py`).
- **Admission Document Overrides**: 4/4 unit tests passed (`tests/test_admission_documents_override.py`).
- **Public Enquiry**: 4/4 unit tests passed (`tests/test_public_enquiry.py`).
- **10/10 Alert Unit Tests passed** (`tests/test_alerts.py`).
- **32 Live Web Screens** registered in `web/src/screens.ts` (all functional and permission-gated).
- **13 Public Website Views**: `/`, `/about`, `/academics`, `/admissions`, `/facilities`, `/school-life`, `/events`, `/gallery`, `/public-disclosure`, `/resources`, `/announcements`, `/announcements/:id`, and `/apply`.
- **24 Active Teachers / Staff** in employee directory (`employees`), covering Pre-primary, Secondary, and Senior Secondary streams.
- **19 Academic Groups / Sections**: Nursery-A, LKG-A, UKG-A, 1-A to 10-A, 11-Sci, 11-Com, 11-Hum, 12-Sci, 12-Com, 12-Hum (190 students enrolled).
- **Database**: PostgreSQL on `localhost:5432` (`sunrise_test` live, `sunrise` dedicated test runner DB) — **105 tables total** (72 live with rows, 33 reserved).
- **TypeScript**: 0 errors across backend, web (`npx tsc -b`), and mobile (`npx tsc --noEmit`).
- **Web Unit Tests**: Vitest 2.1 — **149 passed, 2 skipped across 28 test files** (100% green).
- **Production Build**: Clean Vite production build (`npm run build` in 8.75s).
- **Dev Automation**: 1-click Windows batch scripts `start_dev.bat` and `show_qr.bat` with auto-IP detection and QR code generation.
- **Mobile Stack**: Expo SDK 57, React Native `0.86.3`. Navigation with 4 bottom tabs per role, top-left hamburger opening smooth drawer (`NavDrawer.tsx`), multi-child switcher, and tap-to-fill demo credentials.
- **Live Cloud Deployment**:
  - Web: `https://school-management-system-blush-iota.vercel.app`
  - Backend: `https://school-management-system-12ks.onrender.com`
  - Database: Neon Tech PostgreSQL
- **Primary Canonical PDFs in `docs/`**:
  1. `Sunrise-ERP-Features-Operational-and-Planned.pdf` (778 KB, 28 operational feature cards)
  2. `Sunrise-ERP-Operational-Data-Flows.pdf` (3.66 MB, Comprehensive operational workflows, highways, and ERDs)
  3. `Sunrise-ERP-Database.pdf` (2.20 MB, 105 tables full schema reference)
  4. `Sunrise-ERP-Database-Essentials.pdf` (1.32 MB, 72 live tables & Mermaid ERDs)

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

### K. Session 10 — Receptionist Operational Responsibilities & Sidebar Cleanup (23 Sep 2026)
- **Found & Lost Register (`/reception/found-items`)**: Multi-step found item intake, broadcast alerts, student verification search, and claim/handover tracking with photo recording (`found_items` table).
- **Student Gate Pass & Authorized Roster (`/reception/passes`)**: One-time early departure gate passes (`student_passes`), permanent pre-approved pickup roster (`student_authorized_persons`), and official printable A5 gate pass slip (`PrintableStudentPass.tsx`).
- **Visitor Meeting Slips (`/reception/meetings`)**: Dual-tab visitor workflow for Principal executive appointments and Teacher academic parent interactions with Accept/Wait/Decline response states and printable slips.
- **Important Emergency Directory (`/reception/directory`)**: 7 seeded verified civic, police, and medical contacts; read-only for receptionist, full CRUD for admin.
- **Front Desk Fee Counter (`/reception/fee-counter`)**: Student lookup, FIFO invoice settlement, complete-month-only collection invariant, and printable receipt voucher (`PrintableFeeReceiptSlip.tsx`).
- **Admission Dossier Print Enhancement**: Upgraded `PrintableAdmissionDossier.tsx` with all mandatory audit fields.
- **Sidebar Navigation Leak Fix**: Removed `fees.invoice.read` from receptionist to cleanly eliminate admin fee screens (`Fees`, `Defaulters`, `Fee setup`, `Period close`) from front desk sidebar navigation. Verified with 12/12 automated browser checks.

### L. QA Audit Critical Defect Remediation (8 Issues Resolved) — 29 Oct 2026
Following an extensive QA audit across Admission, Timetable, Examination, and Cross-Tenant security workflows, 8 critical defects were resolved and verified:
1. **Student Data Loss Fix**: Preserved 17 demographic, medical, emergency contact, and previous-school dossier fields in `Student` record (`a2b3c4d5e6f0_audit_defect_remediations.py`), updating permanent profile view and edit endpoints.
2. **Admission Fee Trigger Decoupled**: Paying application fee advances status to `submitted` without enrolling; paying admission fee on accepted offer triggers atomic enrollment into `Student` and `Enrolment`; duplicate 409 prevention; void payment rollback.
3. **Interactive Web Timetable Builder**: Full slot builder in `Classes.tsx` (Add/Edit/Delete slots, `SlotModal`, live conflict checking via `/admin/timetable/slots/check`, draft/published badges).
4. **Teacher & Room Double-Booking Concurrency**: Composite unique constraint `uq_timetable_teacher_slot` and partial unique index `uq_timetable_room_slot` on `(school_id, UPPER(TRIM(room)), day_of_week, period_id)` with room normalization.
5. **Timetable Draft vs Published Lifecycle**: Default draft (`is_published=false`), admin publish/unpublish actions, published-only filtering for student, parent, and teacher APIs.
6. **Absent-Student Score Inflation Fix**: Absent papers contribute scheduled `max_marks` to denominator (`total_max`) with 0 marks obtained. Only explicitly exempted papers are omitted from both numerator and denominator.
7. **Genuine CBSE Pass/Fail Evaluation**: Standard 33% subject and aggregate thresholds with compartment evaluation in `evaluate_academic_result()`; no hardcoded PASS; fee dues withholding cleanly separated into `is_withheld`.
8. **Cross-Tenant Exam Security**: `tenancy.get_owned()` on Exam, ClassSection, and Subject; exam paper date bounded by exam start/end dates.

---

## 3. Active Status: QA Audit Remediation Complete & Verified

The QA Audit Critical Defect Remediation milestone has been fully delivered and verified on branch `slice/office-feedback`:
- **Audit Defect Remediation Suite**: 9 passed, 0 failed (`tests/test_audit_defect_remediations.py`).
- **Migration & Empty DB Compatibility Suite**: 3 passed, 0 failed (`tests/test_migrations.py`).
- **Web unit tests**: 149 passed, 2 skipped across 28 test files (100% green).
- **Web typecheck**: 0 errors (`npx tsc -b`).
- **Mobile typecheck**: 0 errors (`npx tsc --noEmit`).
- **Web build**: Clean Vite production build (`npm run build` in 8.75s).
- **Active Migration head**: `a2b3c4d5e6f0 (head)` (`a2b3c4d5e6f0_audit_defect_remediations.py`).
- **32 live web screens** all functional and permission-gated.

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
15. **Reception Fee Counter vs Admin Fee Screens Gate Segregation**:
    - The front desk fee counter endpoint `/admin/reception/fees/*` is gated strictly on `fees.payment.collect`. Granting `fees.invoice.read` to the receptionist causes admin-only billing screens (`/fees`, `/fees/defaulters`, `/fees/setup`, `/fees/periods`) to inadvertently appear in the receptionist's navigation sidebar. Omitting `fees.invoice.read` from the receptionist role and declaring only `fees.payment.collect` on `/reception/fee-counter` guarantees complete front-desk navigation hygiene while preserving counter fee collection capabilities.
16. **Decoupled Authorized Pickup Roster from Single-Use Gate Passes**:
    - Emergency or early student gate passes require recording the specific authorized person collecting the student. Coupling gate pass records directly to permanent authorized pickup lists creates friction when a pre-approved relative collects a child. Maintain a permanent roster table (`student_authorized_persons`) for authorized guardians/drivers alongside one-time transactional passes (`student_passes`), allowing the receptionist to either select from the roster or enter a verified single-use collector with relationship.
17. **Complete-Month Fee Collection Invariant**:
    - Receptionists at the front desk are prohibited from taking arbitrary partial fee amounts (e.g. ₹500 against a ₹5,400 bill). Fee collection logic at the reception counter enforces strict chronological FIFO settlement of complete billing periods (1 month, 2 months, ..., N months) to eliminate reconciliation discrepancies and prevent ledger tampering.
18. **React Native Fetch Infinite Loading Trap**:
    - React Native's native `fetch()` does not have a default timeout. When a mobile app attempts to connect to an unreachable backend (wrong IP, firewall, server down), the promise hangs indefinitely, leaving UI buttons stuck in "Signing in...". Always wrap mobile `fetch()` calls with an `AbortController` timeout (15s) and catch `AbortError` to provide clear, actionable feedback.
19. **Expo Mobile Network IP Stale Trap**:
    - Hardcoding a local IP in `.env` (`EXPO_PUBLIC_API_URL=http://192.168.x.x:8000`) breaks whenever the Wi-Fi network or location changes. Use `Constants.expoConfig?.hostUri` to dynamically discover the packager host IP in development (since the device is already connected to it to load the bundle), and use a cloud backend URL as a resilient production fallback.
20. **RBAC Auto-Heal Scoping Invariant**:
    - When adding automatic role recovery for database desyncs on cloud, strictly scope the check to primary admin credentials (`user.login_id == "admin@sunrisepublic.edu"` or `admin@...`), never to generic `user.role == UserRole.admin`. Broad matching unintentionally grants `super_admin` permissions to unassigned test accounts, violating segregation of duties and breaking unit tests.
21. **Public Website Scope & Isolation**:
    - The public website (`/`, `/about`, `/academics`, `/admissions`, `/facilities`, `/school-life`, `/events`, `/gallery`, `/contact`) uses `PublicLayout.tsx` and must never mutate or break the internal ERP shell (`Shell.tsx`) or role-gated screens (`screens.ts`). All admissions CTAs ("Apply Online") must link directly to the existing, live application flow at `/apply` (`PublicApplyPage.tsx`).
22. **Public Admission Enquiry Model Unity**:
    - Never create a separate public enquiry model or table; public enquiries write directly to the existing ERP `enquiries` table (`source=EnquirySource.website`, `status=EnquiryStatus.new`). Duplicate phone submissions within the active cycle append an `EnquiryInteraction` with `occurred_at=datetime.now(UTC)` rather than creating orphan duplicate rows.
23. **Global Announcement Strip Exclusions**:
    - The global dark-blue announcement ticker renders across all standard public pages, but is strictly excluded from `/apply` (`PublicApplyPage.tsx`) to keep the multi-step admission application workflow focused and distraction-free.
24. **School Life & Photo Gallery Merge**:
    - The photographic gallery is permanently consolidated at the bottom of School Life (`/school-life#gallery`) with category filter tabs and lightbox. Do not re-add a separate `/gallery` item to the primary navigation bar.
25. **Hostel Class 9+ Eligibility Invariant**:
    - Hostel accommodation is available strictly to students in **Class 9 and above**. Server-side validation, admission endpoints, and UI must block students in Class <= 8 with HTTP 422 Unprocessable Content.
26. **Hostel Gender Scoping Invariant**:
    - Male students can only be admitted to Boys Hostel; female students can only be admitted to Girls Hostel. Gender compatibility must be validated server-side.
27. **Warden Tenant & Single-Hostel Scope Invariant**:
    - A Warden is assigned to exactly one hostel. Backend/database authorization must reject any query, mutation, or URL manipulation by a Warden targeting other hostels or tenants with HTTP 403 Forbidden. Chief Provost has cross-hostel scope.
28. **Hostel Fee Unity Invariant (No Separate Mess Fee)**:
    - Accommodation and mess are billed under a single, unified hostel fee head integrated into `fee_plans` and `fee_invoices`. There is strictly NO separate mess fee, NO mess attendance, and NO cost-per-meal calculation.
29. **Parent-Only Outing Request Invariant**:
    - Only parents can submit leave and outing requests via the Parent App. Students cannot submit outing requests. Warden approves/rejects and must explicitly record student return.
30. **Chief Provost Exclusive Exit Invariant**:
    - Only the Chief Provost role can permanently exit a student from the hostel with an exit date and typed reason, closing active bed allocations and stopping hostel fee applicability.
31. **Admission Fee Trigger Invariant**:
    - Application fee (`cycle.application_fee`) payment merely marks an application `submitted`. Only the payment of an `admission_fee` against an accepted offer triggers atomic enrollment into permanent `students` and annual `enrolments`. Duplicate conversions return HTTP 409 Conflict; payment voids rollback to `offer_accepted`.
32. **Timetable Draft vs Published Lifecycle Invariant**:
    - Timetable slots default to `is_published=false` (draft mode). Administrators see draft slots for configuration; public, student, parent, and teacher interfaces are strictly filtered with `published_only=True` until an administrator publishes the schedule.
33. **Timetable Room Uppercase Trim Normalization Invariant**:
    - All room identifiers are normalized via `UPPER(TRIM(room))` before persistence. A PostgreSQL partial unique index `uq_timetable_room_slot` enforces that no room is double-booked for the same day and period within a school tenant.
34. **Absent Exam Paper Denominator Invariant**:
    - Scheduled exam papers where a student was marked absent (`is_absent=True`) contribute their full `max_marks` to the denominator (`total_max`) with 0 marks obtained, eliminating score inflation. Only explicitly exempted papers (`is_exempt=True`) are excluded from both numerator and denominator.
35. **Dynamic CBSE Academic Evaluation Invariant**:
    - Term report card academic status (`card.result`) is evaluated strictly against CBSE criteria (>= 33% subject threshold, >= 33% aggregate threshold, 1 failure = COMPARTMENT, >= 2 failures or aggregate < 33% = FAIL). PASS is never hardcoded. Fee dues withholding is maintained orthogonally via `card.is_withheld` and never alters academic performance metrics.
36. **Configurable School Period Break Invariant**:
    - School breaks (recess/lunch) must never be hardcoded to a fixed period index in services, calculations, or frontend grids. `SchoolPeriod.is_break` dynamically determines whether a period is instructional or non-instructional. Period 3 defaults to Break/Recess (10:00 - 10:20), with full API (`PUT /admin/timetable/periods/{id}`) and Web UI support for Academic Coordinators and Admins to reconfigure period labels, times, and break statuses at any time.

37. **Parent Dashboard Fee Balance Calculation Invariant**:
    - `/parent/children/{id}/summary` returns `fee_dues` as an integer representing the count of unpaid/overdue invoices, NOT a rupee balance. Mobile and web dashboards must never format `summary.fee_dues` as currency. The authoritative rupee balance must be resolved from `/parent/children/{id}/fees/summary` (`balance` or `total_dues`).
38. **Android 11+ Package Visibility & NPCI Direct UPI Intent Invariant**:
    - Modern Android (API 30+) requires `<queries>` declarations in `AndroidManifest.xml` for `upi://` and target packages (GPay, PhonePe, Paytm, BHIM, CRED) via Expo Config Plugin `mobile/plugins/withAndroidQueries.js`. Without this, `Linking.canOpenURL()` returns false. Specific app targeting requires standard intent format `intent://pay?<params>#Intent;scheme=upi;package=<pkg>;end`. The school's verified NPCI merchant VPA is `8004400433@pthdfc`.

### Standalone Production Android APK (v1.0.1, Build 2) & Direct UPI Payment System (Completed Nov 2026 - Session 36)
- **Status**: Standalone Release APK Generated & Verified on Physical Device (`edu.sunrisepublic.app`).
- **EAS Cloud Build**: Build ID `2d756308-e13e-4bde-8efb-d621d5e1cbea`, version `1.0.1`, build `2`, profile `preview` (APK).
- **Direct Download Artifact**: `https://expo.dev/artifacts/eas/WpvEepEkhGN4NRYntwo_YxI_pPdrP4U8T40UQtSDPmM.apk`
- **Local Binary**: `school-management-system/sunrise-school.apk` (88.15 MB, 92,435,901 bytes).
- **Scannable QR Code**: `apk_download_qr.png` for instant WhatsApp sharing and one-click camera scanning.
- **Physical Device Verified**: Streamed and installed via ADB to Xiaomi/Redmi 13C (`2310FPCA4I`). Verified running live with pre-compiled Hermes bytecode and offline assets, connected to live Render cloud backend (`https://school-management-system-12ks.onrender.com`).
- **Remediated Defects**:
  1. *UPI Intent Launching*: Fixed Android 11+ package visibility restrictions using custom config plugin; added dual-mode launcher targeting apps with universal chooser fallback; added client-side NPCI URL generation fallback with merchant VPA `8004400433@pthdfc`; integrated `expo-clipboard` for 1-tap VPA and amount copying.
  2. *Parent Dashboard Balance Anomaly*: Fixed `dashboard.tsx` where invoice count (`2`) was formatted as ₹2 instead of the actual ledger balance of ₹7,200.

### Academic Coordinator Role & Timetable Module Administration (Completed Oct 2026)
- **Role**: `academic_coordinator` installed in `backend/app/core/permissions.py` with 6 timetable & class permissions (`academics.class.read`, `timetable.slot.read`, `timetable.slot.write`, `timetable.slot.override`, `timetable.substitution.manage`, `comms.notice.read`).
- **Account**: `coordinator@sunrisepublic.edu` (`Admin@123`).
- **Web ERP**: Dedicated workspace at `/#/timetable` (`web/src/pages/Timetable.tsx`) with 5 tabs: Class Timetables, Teacher Schedules, Daily Schedule & Substitution Desk, Workload & Completeness Dashboards, and Bell Timings / School Periods.
- **Audit Logging**: Comprehensive audit recording added to `save_slot`, `delete_slot`, `publish_timetable`, `unpublish_timetable`, `add_period`, and `arrange` (substitutions).
- **Alembic Migration**: `b3c4d5e6f7a8_academic_coordinator_role.py`.
- **E2E Playwright Verification**: 8 verification screenshots captured in `docs/screenshots/` proving class grid, slot modal, conflict resolution, teacher schedule, substitution desk, dashboards, bell timings, and strict sidebar role isolation.


### Independent Second-Stage QA Audit & Readiness Verdict (Completed Nov 2026 - Session 35)
- **Status**: Audit Completed; Score Revised to 68.5% (Production Clearance Denied; Lab Sandbox Pilot Only).
- **Master PDF**: `school-management-system/docs/reporterp.pdf` (8-page master PDF synchronized to `report.pdf`, `reporterp.pdf`).
- **10 Pytest Failures Resolved to Technical Root Causes**:
  1. `BUG-EXAM-01`: Genuine calculation defect where `stats.py` omits absent papers (37.2%) while `report_cards.py` includes them (31.0%).
  2. `BUG-SEED-01`: 8 tests failed due to hardcoded literal assertions when 2 day scholars were added to Section 10-A, expanding headcount from 10 to 12 and roll from 100 to 102.
  3. Outdated test fixture in `test_admission_dossier_demo.py` requiring `admission_fee` payment.
- **Deep Operational Breaking Points**:
  - `promotion.py` fails to instantiate `StudentFeePlan`s for promoted students or migrate concessions/transport assignments.
  - `certificates.py` `issue_certificate()` generates official TCs without checking outstanding fee balances (`BUG-CERT-01`).
  - Fees module lacks 1-click Cheque Dishonour reversal workflow.
  - Mobile app lacks offline roll-call mutation queue.
- **Next Session Documents**: `SESSION-HANDOFF-35.md`, `SESSION-HANDOFF-PROMPT-36.md`, and `Sunrise-Part6-Prompt.md`.

---

## 5. Production Reliability, APK, iOS & Attendance Upgrade (Session 37 — 13 Nov 2026)

- **APK Untracked & Ignored**: `sunrise-school.apk` (88.15 MB, 92,435,901 bytes) removed from Git index (`git rm --cached`) while 100% preserved locally on disk. Updated `.gitignore` with `*.apk`, `*.aab`, `*.ipa`.
- **Mobile Login Root Cause & Permanent Fix**:
  - *Cold-Start Timeout*: Live Render backend container sleeps after 15m inactivity; measured cold start took 48.61s. Mobile app had hardcoded 15s timeout. Fixed by raising auth timeout to 60s and default request timeout to 30s.
  - *React Native Cancellation Mismatch*: In Hermes runtime, aborted fetches throw `TypeError: Fetch request has been canceled` where `err.name` is not `"AbortError"`. Fixed with multi-pattern cancellation detector (`isAborted`).
  - *Session Persistence Invalidation*: App startup cleared tokens on any network error. Fixed to only clear stored tokens on HTTP 401/403.
  - *Progressive UX*: Added 4s server warming banner informing user that the cloud backend is waking up.
  - *Live Multi-Role Verification*: Verified Student (`2024000001`), Parent (`9876500001`), Teacher (`TCH001`) logins and 6-user concurrent login test against live Render backend.
- **Complete iOS Compatibility (iPhone)**:
  - `app.json`: Added `bundleIdentifier: "edu.sunrisepublic.app"`, `buildNumber: "2"`, `ITSAppUsesNonExemptEncryption: false`, and `LSApplicationQueriesSchemes` (`upi`, `gpay`, `phonepe`, `paytmmp`, `bhim`, `cred`).
  - `eas.json`: Added iOS `preview` (simulator: true) and `production` (internal distribution) build profiles.
  - Safe Area Bottom Tabs: Fixed hardcoded `height: 60` in `_layout.tsx` across Parent, Student, and Teacher navigation to dynamically incorporate `insets.bottom` on modern iPhones with home indicators.
  - Build Export Verified: Clean iOS Hermes compilation (`npx expo export --platform ios`) with 0 errors in 8.4s. Android export also verified clean in 13.7s.
- **Attendance Database Optimization & Demo Generation**:
  - Full recoverable SQL (`1.78 MB`) and JSON (`1.93 MB`) backups created in `backend/var/backups/attendance_backup_pre_retention_20261113.*` and verified 100% recoverable (5,800 / 5,800 rows).
  - Calculated impact: 4,800 rows to prune (82.76% reduction, saving ~1.06 MB table & index storage).
  - Target 10 working days: 2026-08-21 through 2026-09-01 (Mon-Sat, excluding Sundays and holidays).
  - Created idempotent CLI script `backend/scripts/attendance_retention_and_demo_seed.py` with `--dry-run` and `--apply`.
  - Dry-run verified: Covers all 102 active students, expected 1,020 records, realistic distribution (93.3% Present, 4.5% Absent, 2.2% Leave), tagged `DEMO/SYNTHETIC`.
  - Deletion plan prepared and held for explicit user approval before execution.
