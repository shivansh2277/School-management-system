# Sunrise School ERP — Single Source of Truth

**Date:** 29 September 2026  
**Status:** Authoritative — Session 22 Verified: Central Academy Reference Website Study & Comprehensive Institutional Public Website Upgrade. Upgraded public navigation to 11 institutional menu items (Home, About, Academics, Admissions, Campus & Facilities, School Life, Events, Gallery, Public Disclosure, Resources, Contact) plus prominent "Admission Enquiry / Apply Now" CTA button. Desktop top utility micro-strip permanently removed (main nav is the topmost element). Zero public ERP login links anywhere on public views (no Sign In, Student/Parent/Teacher portals, or Branches). Mandatory Public Disclosure portal (`/public-disclosure`) with 6 CBSE Appendix-IX tabs (General, Documents, Results, Staff, Infrastructure, Grievance) with demo disclaimers and zero invented affiliation numbers. Resources & Downloads Hub (`/resources`) with approved 1-page A4 PDFs (strictly excludes Parent Info PDF). End-to-end Announcements & Circulars system with backend migration `d5e6f7a8b9c0` adding public fields to `notices`, public endpoint `/public/{school_code}/announcements`, ERP publishing controls with public checkboxes and pin badges, live ticker, listing (`/announcements`), and detail view (`/announcements/:id`). All 10 demo single-page A4 PDFs generated and verified. Full test suite: 776 backend tests passed (1 skipped), 125 web unit tests passed (2 skipped across 21 files), 0 TypeScript errors on web and mobile, and clean Vite production build.  
**Canonical Branch:** `slice/office-feedback` (synced with `origin/main` and `origin/slice/office-feedback`).  
**Live Cloud Deployment:**
- **Web Frontend (Vercel):** `https://school-management-system-blush-iota.vercel.app`
- **Backend API (Render):** `https://school-management-system-12ks.onrender.com`
- **Database (Neon Tech):** Serverless PostgreSQL (`postgresql+psycopg://`)
**Primary PDF Deliverables:**
- [`docs/Sunrise-ERP-Admission-Demo-Guide.pdf`](docs/Sunrise-ERP-Admission-Demo-Guide.pdf) — Complete Digital Admission Dossier & Interactive Testing Guide for Application 360° with Aarav Sharma & Ananya Verma walkthroughs.
- [`docs/Sunrise-ERP-Operational-Data-Flows.pdf`](docs/Sunrise-ERP-Operational-Data-Flows.pdf) — Simple Database Data-Flow Guide showing TABLE → TABLE → TABLE flows, PK/FK connections, Student ID vs Enrollment ID rules, and the final student data journey.
- [`docs/Sunrise-ERP-Database-Tables-and-Features.pdf`](docs/Sunrise-ERP-Database-Tables-and-Features.pdf) — Complete 93-table database & feature mapping reference (all 68 live tables + 25 unused tables mapped to web routes, UI components, and workflows).
- [`docs/Sunrise-ERP-Database-Viva-100.pdf`](docs/Sunrise-ERP-Database-Viva-100.pdf) — 100 Project-Specific Database & Backend Viva Questions and Answers with Top 20 Focus.
- [`docs/Sunrise-ERP-Features-Operational-and-Planned.pdf`](docs/Sunrise-ERP-Features-Operational-and-Planned.pdf) — Comprehensive operational (31 live screens, 18 staff) & planned feature specification.
- [`docs/Sunrise-ERP-Database-Essentials-Explained.pdf`](docs/Sunrise-ERP-Database-Essentials-Explained.pdf) — Step-by-step plain-English process explanation guide for the 68 essential database tables across 16 end-to-end workflows.
- [`docs/Sunrise-ERP-Database-Essentials.pdf`](docs/Sunrise-ERP-Database-Essentials.pdf) — 68 live data tables with entity relationship diagrams.
- [`docs/Sunrise-ERP-Database.pdf`](docs/Sunrise-ERP-Database.pdf) — Complete 93-table database schema with all 1,097 columns and 250 foreign keys.

---

## 1. Project Directives & Strategic Decisions

1. **Multi-Tenant Architecture**: Built as an ERP sold to **separate, independent schools** (each school is an isolated tenant with its own `school_id`, branding, and configuration), not branches of one school.
2. **Platform Focus (Owner Directive)**:
   - **The Admin Web ERP is the primary focus.**
   - **Public Website Modernization & Institutional Upgrade Complete (Session 21 & Session 22)**: 12 distinct public views, polished PublicNavbar (11 items, no top utility micro-strip, prominent CTA) & PublicFooter, seamless /apply routing to live admission engine, Public Disclosure portal, Resources & Downloads Hub, and end-to-end Announcements system.
   - **Mobile app operational depth complete**: Teacher Attendance Roll-Call, Homework Management, Marks Keypad, Parent Fee Ledger & Receipt, Parent CBSE Report Card & Dues Gate, Student Timetable & Digital Turn-in, and Important Alerts Engine.
   - Counter fee collection forms remain off the web for now (the web keeps the complete financial ledger, student accounts, and payment reversal contra-entries).
3. **Unified Leadership Authentication (Owner Directive)**:
   - **Principal, Vice Principal, Administration, Owner/Management, and Coordinator** can all use the **same unified login** and **same password** for the admin website:
     - **Shared Login ID:** `admin@sunrisepublic.edu`
     - **Password:** `Admin@123`
   - Individual title-based logins also exist with the exact same password and full administrative permissions:
     - Principal: `principal@sunrisepublic.edu`
     - Vice Principal: `viceprincipal@sunrisepublic.edu`
     - Owner / Management: `owner@sunrisepublic.edu`
     - Academic Coordinator: `coordinator@sunrisepublic.edu`
     - Fee counter clerk: `counter@sunrisepublic.edu` (`Admin@123`) — segregated duties (can read ledger, view defaulters, but cannot void payments or approve concessions).
     - Admission officer: `admission@sunrisepublic.edu` (`Admin@123`) — owns the complete admission pipeline (enquiries, applications, merit ranking, waitlist, reports, and atomic fee collection). Navigation strictly hardened: `Students`, `Classes`, and `Notices` removed; direct URLs `#/students`, `#/classes`, `#/notices` protected with in-page refusal and backend HTTP 403 Forbidden.
     - Front desk receptionist: `receptionist@sunrisepublic.edu` (`Admin@123`) — dedicated front desk operational suite. Owns Enquiries, Notices, and all Front Desk modules: Found & Lost, Student Gate Passes, Visitor Meeting Slips (Principal only), Important Directory, and Reception Fee Counter. Navigation strictly hardened: `Applications`, `Merit & selection`, `Waitlist`, `Admission reports`, and all admin fee management screens (`Fees`, `Defaulters`, `Fee setup`, `Period close`, `Student fees`) are completely removed; direct URLs protected with in-page refusal and backend HTTP 403 Forbidden.
     - Transport In-Charge: `transport@sunrisepublic.edu` (`Admin@123`) — dedicated transport management role. Strictly hardened: People and Academics modules completely removed; sees only Transport & Logistics (`/transport`) and Notices (`/notices`); direct URLs protected with in-page refusal and backend HTTP 403 Forbidden (`students.profile.read` and `academics.class.read` removed). Upgraded with Plan 1 (Fleet & Route Setup Desk), Plan 2 (Student Transport Allocation Desk), and Address-First geocoding location system.
     - Accounts Officer: `accounts@sunrisepublic.edu` (`Admin@123`) — dedicated accounts department role. Owns financial operations (Fees overview, student ledger, defaulters, fee structure setup, periods close), payroll management, and Fee Reports. Strictly isolated via RBAC: zero access to Admin settings, Admissions, Transport, or Academic grading.
4. **Git Protocol (Owner Directive)**:
   - Remote repository origin configured at `https://github.com/shivansh2277/School-management-system.git`.
   - Branch `slice/office-feedback` pushed to origin and synced to `main` for Vercel/Render automatic deployments.
   - Always display the exact file list and commit history before any hard-to-undo operation.

---

## 2. Verified Technical State (Measured 29 Sep 2026 — Session 22 Verified)

| Layer | Metric | Verification Command | Result |
|---|---|---|:---:|
| **Backend Suite** | 777 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest -q` | **776 passed, 1 skipped, 0 failed** (100% green, 0 regressions) |
| **Public Announcements API** | 5 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_public_announcements.py -q` | **5 passed, 0 failed** (100% green) |
| **Public Admission Workflow** | 5 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_public_admission_workflow.py -q` | **5 passed, 0 failed** (100% green) |
| **Backend Alerts Engine** | 10 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_alerts.py -q` | **10 passed, 0 failed** (100% green) |
| **Backend RBAC** | 13 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_rbac.py -q` | **13 passed, 0 failed** (100% green) |
| **Backend Auth** | 8 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_auth.py -q` | **8 passed, 0 failed** (100% green) |
| **Admin User Access** | 6 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_admin_user_access.py -q` | **6 passed, 0 failed** (100% green) |
| **Teacher Leave & Substitutions** | 6 tests | `cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_teacher_leave_ranked_substitutions.py -q` | **6 passed, 0 failed** (100% green) |
| **Active Migration Head** | Revision `d5e6f7a8b9c0` | `alembic current` | **`d5e6f7a8b9c0 (head)` clean bidirectional** |
| **Web Typecheck** | TypeScript 5.5 | `cd web && npx tsc --noEmit` | **0 errors** |
| **Web Unit Tests** | Vitest 2.1 | `cd web && npm test` | **125 passed, 2 skipped across 21 test files** (100% green) |
| **Mobile Typecheck** | React Native 0.86 / TS | `cd mobile && npx tsc --noEmit` | **0 errors (clean compilation, Expo SDK 57)** |
| **Production Build** | Vite 5.4 | `cd web && npm run build` | **Clean build (14.60s)** |
| **Public Pages Live** | 12 Views + /apply | `/`, `/about`, `/academics`, `/admissions`, `/facilities`, `/school-life`, `/events`, `/gallery`, `/public-disclosure`, `/resources`, `/announcements`, `/announcements/:id`, `/apply` | **13/13 functional, responsive & integrated** |
| **Declared Web Screens** | 32 Screens | Registered in `web/src/screens.ts` | **32/32 functional & gated** |
| **Visual Verification Suite** | 17 Screenshots | Puppeteer automated verification | **17/17 passed in `docs/screenshots/session21/`** |

### Stack Configuration
- **FastAPI Backend API**: `http://127.0.0.1:8000` (LAN binding: `http://0.0.0.0:8000` / `http://10.109.197.170:8000`)
- **Render Cloud Backend**: `https://school-management-system-12ks.onrender.com` (`/healthz` 200 OK)
- **Vercel Web Dashboard**: `https://school-management-system-blush-iota.vercel.app`
- **Expo Mobile Server**: `exp://10.109.197.170:8081` (Metro on `http://localhost:8081`)
- **Database**: Native PostgreSQL on `localhost:5432` (`sunrise_test`) + Neon Tech Serverless PostgreSQL in cloud
- **Python Runtime**: 3.13.7 in `.venv/` at workspace root
- **Node Runtime**: v24.19.0

---

## 3. The Three Binding Contracts

### Contract 1 — Screen Registry is Canonical (`web/src/screens.ts`)
- Every screen in the ERP is declared once in `SCREENS`.
- Navigation sidebar, client-side routing, permission gating, and module hiding all derive strictly from this list.
- A screen declares only the permissions needed for its initial read path. Secondary widgets gate themselves with `<Can>` inside the screen component.
- Modules are feature flags (`core/modules.py`). When a module is disabled, its screens cleanly vanish.

### Contract 2 — Verify Before Claiming
- Every claim must be backed by real execution output pasted in full.
- "It type-checks" is not "it works". Real browser verification against a running backend is mandatory.
- If a feature or edge case is unverified, state it plainly.

### Contract 3 — Writes are Gated, Confirmed, and Audited
- Controls that perform writes are gated with `<ActionButton>` and disabled with a tooltip explaining missing permissions.
- Destructive operations (void, reverse, delete, status change, deactivate) **must** collect a user-typed reason via `<ConfirmDialog>` and commit it to `audit_log`.
- **Financial Immutability**: Money is never edited. Invoices are voided and reissued; payments are reversed via contra entries.

---

## 4. Design & Ergonomic Standards (Lucknow School Office Context)

1. **Clean Page Headings (Owner Directive, 12 Sep 2026)**:
   - **No descriptive subtitle/purpose lines** directly under page/view headings.
   - Headers are clean and concise (e.g., `Enquiry Register`, `Waitlist Queue`, `Reports Library`, `Stock & Inventory`, `Merit Ranking & Selection`, `Application Register`, `Admission Analytics & Reports`).
   - Maximizes vertical reading space for dense operational tables, filters, and primary action controls.
2. **Resilient Badge & Header Layouts**:
   - Long identifier codes use `min-w-0 truncate` with native browser tooltip (`title={...}`).
   - Right-side status/scope badge clusters strictly apply `shrink-0` to eliminate layout wrapping or badge clipping on varying viewports.
   - Sidebar header branding padding matches all item containers (`px-3 py-3 mb-2`).
3. **Primary Action Above the Fold**: Clear visual hierarchy (e.g., Student screen searches a child; Fees ledger looks up an account).
4. **Real-world Search**: Search by student name, admission number, or guardian phone.
5. **Keyboard-First Data Entry**: Form workflows must support Tab and Enter navigation without mandatory mouse interaction.
6. **Actionable Empty States**: Empty states must explain the next step rather than stating a generic "No data".
7. **No Fabricated Data**: An honest empty state beats an invented number or placeholder.
8. **Indian Formatting**:
   - Currency: `money()` helper for Indian comma format (e.g., `₹1,20,000.00`).
   - Dates: `dd/mm/yyyy` on screen (`en-GB`), ISO on the wire.

---

## 5. Screen Registry Inventory (31 Screens Live)

| Screen | Route | Group | Primary Permissions | Module Gate | What It Does |
|---|---|---|---|---|---|
| **Dashboard** | `/dashboard` | *(Top)* | `admin.settings.read` | — | School KPI stats, Attendance Overview top card (Total Students, Present Today, Absent Today, Attendance Percentage with distribution progress bar replacing old 4 summary cards), upgraded Fees Overview (clickable fees remaining with 10-column defaulters modal & CSV export), Grievances & Feedback real-time feed with staff assignment & reply threads |
| **Admission dashboard** | `/admission` | Admission | `admin.settings.read`, `admission.cycle.read` | `admission` | Active admission cycle, conversion funnel metrics, class seat capacity table, intake config modal |
| **Enquiries** | `/admission/enquiries` | Admission | `admission.enquiry.read` | `admission` | Walk-in/call inquiry log, follow-up interaction timeline, convert to draft app, mark invalid |
| **Applications** | `/admission/applications` | Admission | `admission.application.read` | `admission` | Complete Digital Admission Dossier (10 tabs: Student Details, Admission Details, Guardians, Siblings, Address, Previous School, Medical, Documents, Declarations, Selection & Enrollment) |
| **Merit & selection** | `/admission/merit` | Admission | `admission.application.read` | `admission` | Ranked merit list per class, test/interview scores, batch decision workflow with shared audit reason |
| **Waitlist** | `/admission/waitlist` | Admission | `admission.application.read` | `admission` | Ordered waiting list by rank, capacity gauges, promote next candidate when seats release |
| **Admission reports** | `/admission/reports` | Admission | `admission.application.read` | `admission` | Funnel drop-offs, lead source yield %, class seat utilization, demographics, cycle times |
| **Students** | `/students` | People | `students.profile.read` | `students` | 100 students roster, fees status, class filter, student profile drill-down |
| **Staff** | `/teachers` | People | `hr.employee.read` | `hr` | Directory of all 18 staff (teachers, admin, bus drivers, attendant), department & contact details |
| **Staff leave** | `/staff-leave` | People | `hr.employee.read` | `hr` | Teacher leave queue, review & substitution matrix, 100% coverage locked approval gate, free teacher selector, rejection purge |
| **Classes** | `/classes` | Academics | `academics.class.read` | — | Class 1-A to 10-A sections, class teacher assignments, subject teacher allocations, timetable grid |
| **Attendance** | `/attendance` | Academics | `attendance.record.read`, `academics.class.read` | `attendance` | Daily roll marking register, status summary, shortage indicators |
| **Exams** | `/exams` | Academics | `exam.definition.read`, `academics.class.read` | `examinations` | 3-tab deep suite: 1) Exams & Datesheets with Marks Entry Grid, paper lock & audited overrides; 2) CBSE Schemes & 8-Point Grading Scales; 3) Report Cards & Publications with dues withholdings (§0.6b, §5.4.9) |
| **Session rollover** | `/admin/session-rollover` | Academics | `students.enrolment.promote`, `academics.class.read` | `students` | 4-step wizard to transition from 2025-26 to 2026-27: cohort roster review, promote/detain overrides, dynamic roll numbers, typed PROMOTE audit gate |
| **Fees** | `/fees` | Money | `fees.invoice.read` | `fees` | Overall billing vs collection totals, monthly invoice generation with form error feedback |
| **Student fees** | `/fees/ledger` | Money | `fees.invoice.read`, `students.profile.read` | `fees` | Student ledger lookup, invoice lines, payment history, audited contra payment reversals |
| **Defaulters** | `/fees/defaulters` | Money | `fees.invoice.read` | `fees` | Overdue fee chase list, threshold filter (`min_amount`), guardian phone contact numbers |
| **Fee setup** | `/fees/setup` | Money | `fees.invoice.read` | `fees` | 10 class fee plans, fee heads, monthly fee items, student concessions approval workflow |
| **Period close** | `/fees/periods` | Money | `fees.invoice.read` | `fees` | 12 monthly periods, closed/open status audit log, audited close/reopen actions |
| **Payroll** | `/payroll` | Money | `hr.employee.read` | `hr` | Monthly salary batches, compensation structures, statutory EPF/ESI/TDS registers, printable CBSE payslips, bank disbursal CSV export |
| **Notices** | `/notices` | Communication | `comms.notice.read` | `communication` | School notice board, composer with audience targeting, audited delete action with reason |
| **Transport** | `/transport` | Operations | `transport.setup.read` | `transport` | Routes running, seat capacities, riders drill-down, expiring vehicle papers, Leaflet route map |
| **Stock** | `/inventory` | Operations | `inventory.item.read` | `inventory` | Consumable and equipment catalog, low-stock threshold alerts, purchase/issue approval modal, teacher depletion flagging |
| **Found & Lost** | `/reception/found-items` | Front Desk | `reception.found_items.read` | — | Found items register, record found item modal with photo URL, broadcast notifications, student claim & photo handover modal |
| **Student Passes** | `/reception/passes` | Front Desk | `reception.passes.read` | — | One-time student gate passes, parent/guardian authorization, independent permanent authorized roster management, printable gate pass slip |
| **Meeting Slips** | `/reception/meetings` | Front Desk | `reception.meetings.read` | — | Executive visitor appointments for Principal and academic parent-teacher meetings, accept/wait/decline response, printable meeting slips |
| **Important Directory** | `/reception/directory` | Front Desk | `reception.directory.read` | — | Essential school, medical, civic, police, and emergency services directory (read-only for receptionist, full CRUD with Add/Edit/Delete for admin) |
| **Fee Counter** | `/reception/fee-counter` | Front Desk | `fees.payment.collect` | `fees` | Front desk counter fee collection: student lookup, chronological FIFO invoice loading, complete-month-only collection invariant, printable fee receipt slip |
| **Configuration** | `/configuration` | Administration | `admin.settings.read` | — | 11 module feature switches with live refresh, setting registry groups, custom field editor |
| **Settings** | `/settings` | Administration | `admin.settings.read` | — | School profile, address, academic year, grading scale editor, fee structure editor |
| **Reports library** | `/reports` | Analytics | `admin.settings.read` | `reports` | Full reporting centre for the 21 registered backend reports across 9 categories, dynamic runner modal, formatted tables/stat cards, authenticated CSV export |

---

## 6. Packet Status & Complete Feature Specification

### 6.1 Completed Packets & Features (Operational)
- **Packet 0 — Write Layer**: Complete (`reports/packet-0-write-layer.md`).
- **Packet 2 — Fees at the Counter**: Complete (`reports/packet-2-fees.md`).
- **Packet 1 — Admission**: Complete (`reports/packet-1-admission.md`). All 6 admission screens live, verified in Chrome CDP with 17 proofs.
- **Academics & Examination Depth**: Complete (`reports/packet-3-academics-reports.md`).
  - Marks Entry Grid, Audited Paper Lock/Unlock, CBSE Assessment Schemes & 8-Point Grading Scales, and Report Card publication with dues withholding.
- **Reports Library**: Complete (`reports/packet-3-academics-reports.md`). 21 reports across 9 categories with dynamic runners and CSV exports.
- **Packet 5 — Inventory & Stock Management (Completed 13 Sep 2026)**:
  - Multi-tenant catalog (`stock_items`, `stock_requests`), minimum quantity threshold alerts, purchase/issue request approval modal, live reactive quantities.
  - Mobile Teacher Stock-Flagging (`mobile/app/(teacher)/stock.tsx`) connected to `/teacher/stock/flag`.
- **Packet 6 — Dashboard Upgrade & Grievance System (Completed 13 Sep 2026)**:
  - Upgraded **Fees Overview Card**: Clickable Fees Remaining trigger opening Defaulters Modal with all 10 requested columns (Student Name, Admission ID, Class/Sec, Class Teacher, Academic Year, Fee Type, Due Date, Payment Status, Pending Amount, and Total Pending Amount footer) plus CSV export.
  - Upgraded **Grievances Card**: Real-time KPI chips, feed of recent complaints, detail modal with full conversational thread, admin reply box, ticket status actions, and staff assignment via `/admin/grievances/staff`.
  - Mobile Grievance Screens: Teacher (`mobile/app/(teacher)/grievances.tsx`) and Parent Helpdesk (`mobile/app/(parent)/grievances.tsx`).
- **Main Dashboard Upgrade — Attendance Overview Card (Completed 14 Sep 2026)**:
  - Replaced the top 4 summary cards (`Total Students`, `Total Teachers`, `Total Classes`, `Fees Collected`) with a dedicated **Attendance Overview** card.
  - Displays 4 live database metrics: Total Students (`100`), Present Today (`90`), Absent Today (`10` with `5 absent · 5 on leave`), and Attendance Percentage (`90%`).
  - Real-time dual-tone attendance distribution progress bar.
  - Backend API `svc.today_attendance(db, school_id)` in `app/services/stats.py` provides dynamic SQL metrics with automatic fallback to latest marked date when morning roll is pending.
- **Receptionist Role & Admission RBAC Isolation (Completed 14 Sep 2026)**:
  - Dedicated front desk receptionist role (`receptionist@sunrisepublic.edu` / `Admin@123`).
  - Strict isolation: Receptionist has exclusive access to the 5 operational admission queues (`/admission/enquiries`, `/admission/applications`, `/admission/merit`, `/admission/waitlist`, `/admission/reports`) and candidate walk-in intake (`/recruitment`).
- **Database Documentation Sync**:
  - `docs/Sunrise-ERP-Database-Essentials.pdf` (68 live tables), `docs/Sunrise-ERP-Database-Essentials-Explained.pdf`, and `docs/Sunrise-ERP-Database.pdf` (all 93 tables) regenerated. All 17 verification checks pass.

---

### 6.2 Recently Completed Features (Session 5 & 6)

#### 1. Payroll & Salary Disbursal (`/payroll`) — 100% Complete & Operational
- **Dedicated Web Screen:** Monthly salary calculation, multi-tab layout (`Runs`, `Salary Structures`, `Components Registry`), summary stat cards.
- **CBSE Printable Payslip Modal:** Lucknow school header, earnings/deductions breakdown, in-words currency conversion (`₹`), official school stamps and signature blocks with native `window.print()`.
- **Bank Disbursal CSV:** `GET /admin/payroll/runs/{id}/bank-disbursal?format=csv` export for electronic bank transfers (NEFT/RTGS format).
- **Statutory Registers:** EPF (12%), ESI (0.75%), TDS, and department cost allocations.

#### 2. Session Rollover & Promotion Wizard (`/admin/session-rollover`) — 100% Complete & Operational
- **4-Step Wizard Workflow:**
  1. *Select Session & Section:* Source year (`2025-26`), target planning year (`2026-27`), class card selector.
  2. *Roster Review & Overrides:* Interactive table with individual outcome decisions (`Promote`, `Detain`, `Pass Out`, `Transfer Out`), live dynamic roll number reallocation, and blocker alerts.
  3. *Safety Gate Verification:* Mandatory typed `PROMOTE` confirmation with audit reason recorded to `audit_logs`.
  4. *Rollover Summary:* Completion metrics with links to classes and reports.
- **Backend Promotion API:** `GET /admin/promotion/years`, `GET /admin/promotion/sections`, `POST /admin/promotion/preview`, `POST /admin/promotion/commit`. Gated on `students.enrolment.promote`.

#### 3. Teacher Leave Management & Timetable Substitution Gate (`/staff-leave` & mobile `/leave`) — 100% Complete & Operational
- **Mobile Self-Service Leave Application:** Teachers apply for full-day or consecutive multi-day leave with reason. Applications display an explicit policy notice that leaves cannot be withdrawn or cancelled once submitted. Strict teacher-to-teacher data isolation enforced.
- **Dynamic Substitution Matrix:** When admin reviews leave on `/staff-leave`, the backend inspects scheduled periods on `timetable_slots` and computes free, non-conflicting faculty members for each period.
- **Strict 100% Safety Gate:** The "Approve Leave" button remains completely locked at 0% or partial coverage. Only when 100% of affected periods have assigned substitutes does the button turn green and unlock.
- **Automatic Rejection Purge:** If admin rejects the leave with an audited reason, all provisional substitutions are immediately purged from the database, leaving master timetable slots 100% untouched.
- **Substitute Teacher Mobile Duty Reflection:** Assigned substitute teachers automatically see their date-scoped substitution duty on their mobile device under the "Duties" tab.

#### 4. Teacher Recruitment, Intake & Staff Onboarding (`/recruitment`) — 100% Complete & Operational
- **Front-Desk Candidate Intake:** Receptionist registers walk-in teacher applicants and prints official CBSE A4 formatted application dossiers with photograph box and qualifications table.
- **Strict RBAC Separation:** Receptionist is prohibited from seeing or performing pipeline transitions (shortlist, offer, hire).
- **Offer Generation & Onboarding:** Admin reviews candidate, sets designation and monthly salary (₹), and confirms joining. Upon confirmation, the system automatically provisions an active employee record and teacher user account (`TCH0xx` / `Teacher@123`).

#### 5. Master Browser E2E Test Suite & Visual Proofs (23 Screenshots)
- Complete master Puppeteer execution (`scratch/e2e_full_master.mjs`) verified in headless Chrome with exit code 0.
- Exactly 23 distinct visual proof screenshots captured and saved to `docs/screenshots/` and documented in `walkthrough.md`.

#### 6. Database Schema Refactoring (`enrolment_id` Migration) — 100% Complete & Operational (Session 6)
- **Tables Refactored**: `marks`, `homework_submissions`, and `grievances`.
- **Physical Column Elimination**: `student_id` eliminated from `marks` and `homework_submissions`; `enrolment_id` (`BIGINT NOT NULL REFERENCES enrolments(id)`) made mandatory. Compound unique constraints ensure an enrolment holds at most one mark per exam schedule and one submission per homework.
- **Migration & Backfill**: Revision `b2c3d4e5f6a7_enrolment_id_refactor.py` (down revision `a1b2c3d4e5f6`). 100% of existing rows backfilled cleanly from active enrolments. Bidirectional downgrade/upgrade verified clean.
- **Backward Compatibility Scrutiny**:
  - `Mark.student_id` is a `@hybrid_property` with **strictly no setter** (`AttributeError: can't set attribute` on any mutation or instantiation).
  - `HomeworkSubmission` and `Attendance` have no `student_id` column or attribute on write.
  - Ingestion translation resolves inputs strictly against `roster(db, sched.class_section_id)`; cross-section or past-year IDs are refused with HTTP 403 / 422.
  - Enforced by 7 automated tests in `test_enrolment_id_invariant_enforcement.py`.

#### 7. Mobile App Operational Depth — 100% Complete & Operational (Session 6)
- **Teacher Mobile App (`mobile/app/(teacher)`)**:
  - In-classroom morning roll marking with one-tap status toggles (`attendance.tsx`).
  - Homework assignment composer and student turn-in grading drawer (`homework.tsx`).
  - Compact mobile test marks entry keypad with real-time validation (`results.tsx` / `marks.tsx`).
- **Parent Mobile App (`mobile/app/(parent)`)**:
  - Monthly color-coded attendance calendar & medical leave application (`attendance.tsx`).
  - Real-time fee ledger and 1-click official PDF receipt download (`fees.tsx`).
  - Official CBSE term report card PDF download with fee dues withholding gate (`results.tsx`).
  - School broadcast push notices listener (`notices.tsx`).
- **Student Mobile App (`mobile/app/(student)`)**:
  - Weekly 6-period timetable viewer & digital homework turn-in upload (`timetable.tsx`, `homework.tsx`).
  - Personal exam marks scorecard and grade bands viewer (`results.tsx`).
- **Visual Verification Proofs**: All 8 mobile screenshot proofs captured and documented in `docs/screenshots/`.

---

### 6.3 Planned Features & Development Roadmap (Session 7 Handoff)

Canonical specification for Session 7 is defined in [`SESSION-HANDOFF-7.md`](SESSION-HANDOFF-7.md) (and roadmap in [`docs/Sunrise-ERP-Features-Operational-and-Planned.pdf`](docs/Sunrise-ERP-Features-Operational-and-Planned.pdf)):

#### A. Admission Workflow & Immediate Student Enrollment (Active Scope: Session 7)
- **Authoritative Engineering Specification:** [`SESSION-HANDOFF-7.md`](SESSION-HANDOFF-7.md)
- **Persona Workflows (Strict Separation):**
  - *Receptionist:* Responsible ONLY for the Enquiry workflow (Log Enquiry -> Save -> Print Enquiry Slip [A5] -> Log Interactions / Follow-ups). Does NOT process applications or collect fees.
  - *Admission Cell / Officer:* Owns the Application workflow (Open/Convert Enquiry -> Complete Dossier -> Validate / Submit -> Collect Application Fee -> Immediate Atomic Enrollment -> Print Receipt & Dossier).
- **Critical Automation Invariant:** Fee payment (amount dynamically sourced from `cycle.application_fee`, no hardcoding) is the single trigger that atomically creates `ApplicationPayment`, permanent `Student`, `Enrolment` in target class/section, login accounts, and document migration in a single transaction with all-or-nothing rollback. No separate conversion button.
- **Master Acceptance Pipeline:**
  $$\text{Enquiry} \longrightarrow \text{Application} \longrightarrow \text{Complete} \longrightarrow \text{Submit} \longrightarrow \text{Pay Fee} \longrightarrow \text{Student Created} \longrightarrow \text{Enrolment Created} \longrightarrow \text{Visible in School Roster}$$
- **Printable Assets:** Printable Enquiry Slip (A5), Fee Receipt Voucher, and CBSE-standard Application Dossier (2-page A4).

#### B. Admin Web ERP (Upcoming Scope)
1. **Public Online Admission Portal UI (`/apply`)**:
   - Parent-facing unauthenticated landing page and registration form with CAPTCHA/bot protection connecting to existing `/public/admission/*` endpoints.
2. **Packet 4 — Contract 3 System-Wide Audit Reason Sweep**:
   - System-wide enforcement pass ensuring 100% of destructive operations (employee exits, status changes, mark overrides, invoice cancellations) prompt a mandatory user-typed reason modal recorded in `audit_log`.
3. **Academic Year Manager UI (`/configuration`)**:
   - Front-end wizard for clerks to activate/deactivate terms and academic years without developer API calls.

#### C. Third-Party Integrations (V2 Scope)
1. **Online Payment Gateway**: Direct parent fee checkout via Razorpay/Easebuzz/PayU with automated webhook ledger reconciliation.
2. **SMS & WhatsApp Alerts**: Automated absence notifications and overdue reminders via TRAI DLT commercial accounts and WhatsApp Business API.
3. **Bulk Legacy Excel Data Importer**: Self-service onboarding tool for schools to import historical rosters and balances from Excel sheets.
4. **Live GPS Bus Tracking**: Real-time vehicle telematics via AIS-140 GPS tracking on the Transport map.

---

### 6.4 Session 6 Verification Gate Results (All 9 Passed)

All 9 acceptance gates specified in `SESSION-HANDOFF-6.md` have been satisfied 100% green:
1. **Gate 1 (Alembic Head)**: Stamped at `b2c3d4e5f6a7 (head)`, clean bidirectional downgrade/upgrade.
2. **Gate 2 (Full Test Suite)**: **708 passed, 1 skipped, 0 failed** in 153.08s (0 regressions).
3. **Gate 3 (Schema Migration & Backfill Assertions)**: 8/8 tests passed in `test_enrolment_id_migration.py`.
4. **Gate 4 (Multi-Tenant & RBAC Isolation)**: 6/6 tests passed in `test_session6_tenant_isolation.py`.
5. **Gate 5 (Linter Compliance)**: `ruff check .` -> All checks passed! Web & Mobile lint clean.
6. **Gate 6 (TypeScript Compilation)**: Web `npx tsc --noEmit` (0 errors), Mobile `npx tsc --noEmit` (0 errors).
7. **Gate 7 (Mobile Ecosystem Health)**: `npx expo-doctor` passed 21/21 checks.
8. **Gate 8 (Database Documentation Sync)**: `verify_db_docs.py` passed 17/17 checks (93 tables, 68 live, 0 drift).
9. **Gate 9 (Visual Proofs Captured)**: 8 mobile proofs captured in `docs/screenshots/`.

---

### 6.5 Session 7 Admission Pipeline & RBAC Hardening (Fully Verified)

Delivered and verified strictly on `slice/office-feedback` with **722 backend tests (100% green)** and **85 web tests**:
1. **Fee Payment as Sole Enrollment Trigger**:
   - Eliminated the manual "Convert to Student" button.
   - Collecting the dynamically configured application fee (`cycle.application_fee`) atomically creates:
     - `application_payments` record (with sequential receipt number)
     - `students` permanent record (`SCH-YYYY-NNNN`)
     - `enrolments` annual record with balanced section allocation
     - Student user login credentials (`username: admission_no`, `password: Student@123`)
     - Linked `student_guardians` and migrated application documents
     - Audit trail with atomic rollback on any failure.
2. **Professional School Admission Dossier & Vouchers**:
   - Multi-page A4 Dossier with clean sections (biodata, guardians, medical, documents, signatures, and seal blocks).
   - Printable A5 Enquiry Slip with parent checklist and tear-off counterfoil.
   - Printable 1/3 A4 Landscape Application Fee Receipt Voucher with dual authorization stamps.
3. **Admission Officer RBAC Navigation & Route Hardening**:
   - Removed `Students`, `Classes`, and `Notices` from sidebar navigation.
   - Direct URLs `#/students`, `#/classes`, and `#/notices` protected with in-page permission refusal and HTTP 403 Forbidden on backend routes.
   - Retains full ownership of admission pipeline: Enquiries, Applications, Merit Ranking, Waitlist, and Admission Reports.
4. **Front Desk Receptionist RBAC Navigation & Route Hardening**:
   - Removed `Applications` and application-processing links (`Merit & selection`, `Waitlist`, `Admission reports`) from sidebar navigation.
   - Direct URL `#/admission/applications` protected with in-page permission refusal and HTTP 403 Forbidden.
   - Strictly focused on `Enquiries` (and `Notices`).
5. **Preserved Executive Integrity**:
   - Super Admin (`admin@sunrisepublic.edu`) and Principal (`principal@sunrisepublic.edu`) navigation and access across all 22 modules remain 100% intact.

---

### 6.6 Mobile API Connectivity & Password Visibility Toggle (Fully Verified)

1. **Root Cause & Fix for Physical Android Device Connection Failure**:
   - Root cause: In React Native / Hermes, `window = globalThis` is defined, causing `typeof window !== "undefined"` in `mobile/src/api/client.ts` to evaluate to `true` and hardcode `http://127.0.0.1:8000`. On a physical phone, `127.0.0.1` resolved to the phone itself, producing `ConnectException: Failed to connect to /127.0.0.1:8000`.
   - Resolution: Dynamically resolves host IP via `Constants.expoConfig?.hostUri` / `Constants.manifest2?.extra?.expoGo?.debuggerHost` (e.g. `192.168.29.227:8081`) from Expo CLI. Respects `process.env.EXPO_PUBLIC_API_URL` when non-loopback; falls back to `10.0.2.2` on Android emulator and `127.0.0.1` on web/iOS simulator.
   - Backend Uvicorn binding: Bound to `--host 0.0.0.0 --port 8000`, enabling LAN devices on `192.168.29.xxx` to communicate directly with the API.
2. **Password Visibility Eye Toggle**:
   - Added interactive toggle inside password input right edge on `mobile/app/index.tsx`.
   - Uses `@expo/vector-icons/Ionicons` (`eye-outline` vs `eye-off-outline`).
   - Default hidden (`secureTextEntry={!showPassword}`); tapping toggles plain text without clearing or modifying entered password.
   - Shared across Student, Parent, and Teacher roles; automatically resets to hidden on role tab switch.

---

### 6.7 Active Hand-Off for Session 8 (`SESSION-HANDOFF-8.md`)

Authoritative specification written in [`SESSION-HANDOFF-8.md`](SESSION-HANDOFF-8.md) covering 6 mobile ERP refinements:
1. **Student Home Isolation**: Remove `Today's Schedule` (Timetable) and `Latest Notices` cards from the Student Home dashboard (`mobile/app/(student)/dashboard.tsx`) while preserving dedicated tab routes.
2. **Parent Fees Accurate Invoicing**: Fix `₹0.00` display by resolving `invoice.payable` from `/parent/fees` backend response (`invTotal = invoice.payable ?? invoice.total ?? invoice.amount ?? 0`).
3. **Teacher Supplies Real Stock Consumption**: Add `"Use / Consume Stock"` workflow in `mobile/app/(teacher)/stock.tsx` and backend service `consume_stock`, updating `current_quantity`, logging audit trails, preventing over-consumption (`HTTP 400`), and automatically flagging `is_low_stock` when `<= min_quantity`.
4. **Universal Standardized Date Display**: Standardize all user-facing dates to `DD-MM-YYYY` using shared `formatDate(d)` helper across Student, Parent, and Teacher screens.
5. **Class Teacher Only Attendance Authorization**: Enforce `ClassSection.class_teacher_id == teacher.id` at the backend API level (`HTTP 403 Forbidden` for subject teachers) and filter mobile UI section dropdown.
6. **Student Homework Submitted Tab Fix**: Correct boolean filter bug in `mobile/app/(student)/homework.tsx` (`item.marks === null && item.marks === undefined` -> `item.submitted && (item.marks === null || item.marks === undefined)`).

---

### 6.8 Complete Digital Admission Dossier — Application 360° Major Overhaul (Delivered & Verified 21 Sep 2026)

Delivered in direct response to the authoritative requirement: **"APPLICATION 360° = COMPLETE DIGITAL ADMISSION DOSSIER. It must contain and allow the Admission Cell to COMPLETE and EDIT the complete information required for admission of a student."**

1. **10 Modular Dossier Tabs (`web/src/pages/admission/Applications.tsx`)**:
   - **Tab 1: Student Details (`DossierStudentDetails.tsx`)**: First name, middle name, last name, DOB, gender, blood group, nationality, religion, category, mother tongue, Aadhaar number. Full edit & patch support.
   - **Tab 2: Admission Details (`DossierAdmissionDetails.tsx`)**: Target class (`class_id`), stream (`stream`: Science, Commerce, Humanities), second language, third language, admission type, day scholar vs hosteler (`residential_status`), school transport opted (`opt_transport`), pickup/drop bus stops.
   - **Tab 3: Guardians (`DossierGuardians.tsx`)**: Father, Mother, Local Guardian editable profiles: full name, relation, mobile, email, occupation, employer, annual income, educational qualification, office address, residential address, primary and emergency contact toggles.
   - **Tab 4: Siblings (`DossierSiblings.tsx`)**: Real school sibling linking: Sibling Name, Class/Section, Admission Number, dynamic student record lookup & verification link.
   - **Tab 5: Address (`DossierAddress.tsx`)**: Present and Permanent postal addresses with 1-click "Same as Present Address" copy checkbox.
   - **Tab 6: Previous School (`DossierPreviousSchool.tsx`)**: School name, board (CBSE, ICSE, State), last class passed, passing year, marks % / CGPA, TC number, TC issue date, reason for leaving.
   - **Tab 7: Medical (`DossierMedical.tsx`)**: Blood group, height (cm), weight (kg), existing medical conditions, allergies, regular medications, emergency doctor/hospital contact name & phone, special care instructions.
   - **Tab 8: Documents (`DossierDocuments`)**: CBSE compliance checklist & viewer for 7 required certificates (Birth Certificate, TC, Previous Marksheet, Aadhaar Card, Guardian ID Proof, Caste Certificate, Medical Certificate) with verification status badges.
   - **Tab 9: Declarations (`DossierDeclarations.tsx`)**: Parent/guardian declaration, student rules acceptance, transport guidelines pledge, anti-ragging undertaking, date of declaration, signatory name.
   - **Tab 10: Selection & Enrollment (`DossierEnrollmentResult.tsx`)**: Entrance test score, interview notes, reviewer recommendation, status change actions, atomic fee collection trigger with class & section allocation, and permanent enrollment result banner (Admission No, Academic Year, Class & Section, Roll No, login credentials).
2. **CBSE Multi-Page Printable Admission Dossier Enhancement**:
   - `PrintableAdmissionDossier.tsx` upgraded with all 11 CBSE official sections, complete guardian breakdown (qualifications, office address), sibling records, detailed medical metrics, allocated class section, permanent admission number, and official school seals & authorization stamps.
   - Headless Chrome publication-quality PDF guide: `docs/Sunrise-ERP-Admission-Demo-Guide.pdf` (265,107 bytes) generated via `scripts/gen_admission_demo_pdf.py`.
   - In-browser HTML preview at `docs/admission-demo-guide-print.html`.
3. **Backend Schema & Serializer Alignment**:
   - Serialized `date_of_birth`, `qualification`, `office_address` on `ApplicationGuardian` (`_guardian_out`).
   - Dynamic resolution of `enrolled_student` in `_detail()` querying `Student`, `Enrolment`, and `AcademicYear` safely without relationship attribute errors.
   - Extended `ActionButton` to support `type="submit"` and optional `onClick`; enhanced `useWrite` with `runAsync`.
4. **Two Seeded & Verified Demo Students**:
   - **Aarav Sharma** (`APP-2026-0091`, Grade 1): Submitted status, complete bio, parents (HCL Tech VP father, DPS Headmistress mother), elder sibling (Ananya Sharma in Class 4-A), medical & address data.
   - **Ananya Verma** (`APP-2026-0092`, Grade 11 Science): Enrolled status, admission fee paid (`REC-2026-0092`), permanent Student ID `SCH-2026-0092`, allocated to Class 11-A (Science PCM + CS), parents (CMO father, High Court Advocate mother), sibling (Kabir Verma in Class 8-B).
355:    - Verified by dedicated automated test suite `backend/tests/test_admission_dossier_demo.py` (2/2 passed, full backend suite 731 passed, 1 skipped).
356: 
357: ---
358: 
359: ### 6.9 Session 9 Verification Gate Results (All 5 Scope Items Complete & Verified)
360: 
361: Delivered and verified strictly on local branch `slice/office-feedback` with **729 backend tests (100% green)**, **82 web tests (100% green)**, 0 type errors on web and mobile, and a clean Vite production build:
362: 1. **Mobile Navigation Redesign (Acharya Prashant Interaction Concept)**:
363:    - **4 Visible Bottom Tabs Per Role**:
364:      - Parent: `Home`, `Child`, `Fees`, `Profile`
365:      - Teacher: `Home`, `Classes`, `Attendance`, `Profile`
366:      - Student: `Home`, `Timetable`, `Homework`, `Profile`
367:    - **Top-Left Hamburger Header & Smooth Drawer (`mobile/src/components/NavDrawer.tsx`)**:
368:      - User profile header with circular avatar, initials, role pill, and school/class subtitle.
   - Verified by dedicated automated test suite `backend/tests/test_admission_dossier_demo.py` (2/2 passed, full backend suite 731 passed, 1 skipped).

---

### 6.9 Session 9 Verification Gate Results (All 5 Scope Items Complete & Verified)

Delivered and verified strictly on local branch `slice/office-feedback` with **729 backend tests (100% green)**, **82 web tests (100% green)**, 0 type errors on web and mobile, and a clean Vite production build:
1. **Mobile Navigation Redesign (Acharya Prashant Interaction Concept)**:
   - **4 Visible Bottom Tabs Per Role**:
     - Parent: `Home`, `Child`, `Fees`, `Profile`
     - Teacher: `Home`, `Classes`, `Attendance`, `Profile`
     - Student: `Home`, `Timetable`, `Homework`, `Profile`
   - **Top-Left Hamburger Header & Smooth Drawer (`mobile/src/components/NavDrawer.tsx`)**:
     - User profile header with circular avatar, initials, role pill, and school/class subtitle.
     - Quick multi-child switcher for parents with active child highlight and instant context update.
     - Categorized menu sections (`ACADEMICS`, `OPERATIONS`, `COMMUNICATION`, `OTHER`) with distinct icons.
     - Hidden tab routes preserved via `options={{ href: null }}` on `<Tabs.Screen>` allowing full deep-linking and zero feature loss.
     - Role-isolated menus and confirmation-guarded Logout action.
2. **Admin Dashboard Fee Collection Graph Removal**:
   - Completely removed `<Card title="Fee Collection">` and all Recharts components/imports in `web/src/pages/Dashboard.tsx`.
   - Layout preserved with 2-column balanced grid without blank container artifacts; test suite passes cleanly.
3. **Teacher Recruitment Decommissioning & Purge**:
   - Pre-drop safety audit confirmed `candidates` and `candidate_offers` tables were 100% recruitment-exclusive with 0 incoming foreign keys from any other school table.
   - Alembic migration `c3d4e5f6a7b8_drop_recruitment_tables.py` applied, dropping `candidate_offers` and `candidates` tables.
   - Permanently removed backend models (`Candidate`, `CandidateOffer`, `CandidateStatus`), schemas, services (`app/services/recruitment.py`), and routes (`app/api/admin/recruitment.py`).
   - Removed `recruitment.candidate.*` permissions from `app/core/permissions.py` and `"recruitment"` module from `app/core/modules.py`.
   - Removed seed data from `backend/seed.py` and updated operational seed idempotency check to `StaffLeaveRequest`.
   - Cleaned up web client: removed `/recruitment` route, `RecruitmentPage.tsx`, `RecruitmentPage.test.tsx`, and `components/recruitment/`.
   - Regenerated TypeScript API types (`web/src/api/schema.d.ts`).
4. **Global Red-X Close Controls**:
   - Replaced all textual "Close" buttons on modals, dialogs, and slide-overs across web and mobile with standardized Red X icon buttons (`#ef4444` / `text-red-500` / `theme.danger`).
   - Web: Standard `Modal` in `web/src/components/ui.tsx` and printable dialogs (`PrintableFeeReceipt.tsx`, `PrintableEnquirySlip.tsx`, `PrintableAdmissionDossier.tsx`).
   - Mobile: `NavDrawer.tsx`, `mobile/app/(teacher)/grievances.tsx`, `mobile/app/(parent)/grievances.tsx`, `mobile/app/(teacher)/stock.tsx`.
   - Kept business action buttons ("Close Grievance", "Period Close") strictly untouched.

---

### 6.10 Session 10 — Receptionist Operational Responsibilities & Sidebar Cleanup (Delivered & Verified 23 Sep 2026)

Delivered in direct response to the authoritative specification for Receptionist Operational Responsibilities and strict front-desk navigation hardening:

1. **Found & Lost — Found Item Workflow (`web/src/pages/reception/FoundItemsPage.tsx`)**:
   - Backend table `found_items` (`id`, `school_id`, `item_name`, `category`, `description`, `found_location`, `found_date`, `status`, `photo_url`, `receiving_student_id`, `handover_photo_url`, `collected_at`, `notes`, `created_at`).
   - Workflow:
     1. Receptionist records found object (name, category, description, location, date/time, photo URL).
     2. Broadcast alert to all students (sets status to `BROADCASTED`).
     3. Student identification and verification search via `/admin/reception/students/search?q=...`.
     4. Claim & Handover modal with claimant verification, handover photo URL, receiving student name/roll/admission number, and timestamp.
     5. Preserves complete historical audit trail of found objects and collection outcomes.

2. **Student Gate Pass & Authorized Collector Roster (`web/src/pages/reception/StudentPassPage.tsx`)**:
   - Backend tables `student_passes` (single-use transactional gate passes) and `student_authorized_persons` (permanent pre-approved collector roster).
   - Strict decoupling: One-time gate passes can be issued either to a person on the permanent roster or to a one-time emergency collector with verified relationship, reason, date, and departure time.
   - Authorized Persons Roster modal allows managing permanent approved pickup persons (name, relationship, phone, photo URL, ID proof, active status).
   - Official CBSE A5 format printable gate pass slip (`PrintableStudentPass.tsx`) with student details, collector authorization, gate security checkpoint tear-off, and school seal block.

3. **Visitor Meeting Slips — Principal & Teacher (`web/src/pages/reception/MeetingsPage.tsx`)**:
   - Backend tables `principal_meeting_requests` and `teacher_meeting_requests`.
   - Dual-tab interface:
     - **Principal Tab:** Receptionist logs visitor meeting request (visitor name, mobile, affiliation/type, purpose, student reference if applicable). Executive response workflow allows Principal/Admin to review pending requests and mark `ACCEPTED`, `WAITING`, or `DECLINED` with executive notes. Printable Principal Meeting Slip (`PrintablePrincipalMeetingSlip.tsx`).
     - **Teacher Tab:** Receptionist creates meeting slip targeting any school teacher (`teacher_id`). Teacher or coordinator can accept or decline with schedule notes. Printable Teacher Meeting Slip (`PrintableTeacherMeetingSlip.tsx`).

4. **Important Emergency & School Directory (`web/src/pages/reception/DirectoryPage.tsx`)**:
   - Backend table `directory_contacts` (`name`, `category`, `department`, `phone_primary`, `phone_secondary`, `email`, `address`, `operating_hours`, `is_emergency`, `notes`).
   - Seeded with 7 verified Lucknow school community contacts (City General Hospital & Trauma Centre, Sector 12 Police Station, School Pediatric Clinic & Ambulance, District Fire & Rescue Services, District Education Officer, School Bus Fleet Contractor, Child Helpline).
   - Strict Role Separation:
     - Receptionist: Clean **Read-Only** view with quick 1-click phone number copy buttons and emergency badges. Add/Edit/Delete action buttons are strictly suppressed via `<Can permission="reception.directory.write">`.
     - Administrator: Full CRUD management (Add Contact modal, inline Edit, and Delete).

5. **Front Desk Fee Counter (`web/src/pages/reception/ReceptionFeeCounterPage.tsx`)**:
   - Purpose-built front desk fee counter endpoint `/admin/reception/fees/status` and `/admin/reception/fees/collect`.
   - Workflow & Invariants:
     - Instant student search by Admission Number (`2024000001`) or Student Name.
     - Displays active enrolment details (Class, Section, Roll No) and total outstanding balance.
     - Loads outstanding fee invoices in strict chronological FIFO priority order (#1 oldest unpaid, #2 next, etc.).
     - **Complete-Month Collection Invariant:** Receptionist is strictly prohibited from collecting arbitrary partial amounts. System generates discrete, one-click options for complete billing cycles only (e.g., "1 Month: ₹1,800.00", "2 Months: ₹7,200.00").
     - Records payment method (Cash, UPI, POS Card, Demand Draft), issues official receipt, and provides immediate printable receipt slip (`PrintableFeeReceiptSlip.tsx`).

6. **Admission Dossier Print Enhancement (`PrintableAdmissionDossier.tsx`)**:
   - Upgraded multi-page A4 dossier to display all mandatory fields: Place of Birth, Single Child status, Identification Marks, Optional Subject, Preferred Section, Admission Category, Transport Facility, Age Override Reason, and Health/Medical metrics with graceful fallback formatting.

7. **Front-Desk Sidebar Navigation Hygiene (Fix Applied & Verified)**:
   - Eliminated navigation leak where admin fee screens (`Fees`, `Defaulters`, `Fee setup`, `Period close`) appeared under "Money" for receptionist.
   - Root Cause: Receptionist had `fees.invoice.read` in `app/core/permissions.py`, which is what admin fee screens declare as their entry gate.
   - Fix: Removed `fees.invoice.read` from receptionist role; updated `/reception/fee-counter` in `screens.ts` to require only `fees.payment.collect`.
   - Verified clean navigation sidebar in Puppeteer: Receptionist sees only `Admission > Enquiries`, `Communication > Notices`, and `Front Desk > Found & Lost, Student Passes, Meeting Slips, Important Directory, Fee Counter`. All 6 forbidden admin fee screens confirmed 100% absent.

---

### 6.11 Session 11 — Modern Public-Facing Website & ERP Gateway Integration (Delivered & Verified 23 Sep 2026)

Delivered in direct response to the requirement for a modern, polished, lightweight public-facing website for "Sunrise School", completely decoupled from internal ERP operational workflows while providing a prominent entry point to the ERP portal.

1. **Architecture & Routing (`web/src/App.tsx`)**:
   - **Public Website Routes**: Registered inside `PublicLayout`:
     - `/` and `/home` → `HomePage.tsx`
     - `/about` → `AboutPage.tsx`
     - `/academics` → `AcademicsPage.tsx`
     - `/admissions` → `AdmissionsPage.tsx`
     - `/facilities` → `FacilitiesPage.tsx`
   - **Root Dispatch Contract Preservation**:
     - Maintained dual-dispatch behavior in `Home()`:
       - If unauthenticated visitor: renders `HomePage.tsx` within the public shell.
       - If authenticated staff member (`me` exists): immediately dispatches to the first authorized ERP screen (`visibleScreens(can, hasModule)[0].path`), preserving 100% compliance with `App.test.tsx` and internal staff deep-linking.
   - **HashRouter Compatibility**: Fully compatible with client-side hash routing (`http://localhost:5173/#/`, `#/about`, `#/academics`, `#/admissions`, `#/facilities`, `#/login`, `#/apply`).
   - **ERP Separation**: Public marketing and institutional information pages run completely without ERP authentication or API dependencies, remaining fast, lightweight, and resilient.

2. **Prominent ERP Gateway (`web/src/components/public/PublicNavbar.tsx`, `HomePage.tsx`, `LoginPage.tsx`)**:
   - High-visibility "Login to ERP" entry points:
     - Prominent primary action button in the public navigation header (`PublicNavbar.tsx`) with lock icon and gold accent border, linking to `#/login`.
     - Hero section dedicated "Staff & ERP Login" secondary action button on `HomePage.tsx`.
     - Quick "ERP Staff Portal" access links in `PublicFooter.tsx`.
   - ERP Return Link: Updated `web/src/auth/LoginPage.tsx` with a prominent return link (`← Back to Sunrise School Website` pointing to `#/`) so staff or visitors can smoothly transition back to the public site.

3. **Centerpiece Campus Hero Integration (`web/src/pages/public/website/HomePage.tsx`)**:
   - **Visual Centerpiece**: Utilizes the official Sunrise School campus visual asset (`web/src/assets/hero-campus.jpg` and `web/public/hero-campus.jpg`) featuring the modern multi-story academic complex, lush green grounds, and vibrant student community.
   - **Non-Redundant Design**: Respects the typography already rendered in the campus asset ("Sunrise School", "Nurturing Brighter Tomorrows", "LEARN | GROW | BELONG | SUCCEED") without duplicate HTML overlay text.
   - **Responsive Focal Alignment**: Uses `object-[32%_center] sm:object-center` with `object-cover` to keep the students and main entrance focal point perfectly framed across desktop, tablet, and mobile viewports.
   - **Key Metrics Section**: Prominently highlights school credibility:
     - 15+ Years of Academic Excellence (Est. 2011)
     - 1,200+ Active Learners across 10 Grades
     - 100% CBSE Board Examination Pass Rate
     - 1:20 Teacher-Student Mentorship Ratio
   - **Feature Previews & Leadership Welcome**:
     - 3-tier academic wings preview and core facilities cards.
     - Principal's Welcome message emphasizing holistic development, discipline, and modern innovation.

4. **Five Dedicated Public Pages (`web/src/pages/public/website/`)**:
   - **Home (`HomePage.tsx`)**: Hero banner centerpiece, school statistics grid, academic highlights, campus infrastructure preview, principal's vision message, and ERP access banner.
   - **About Us (`AboutPage.tsx`)**:
     - Founding narrative: Established in 2011 in Gomti Nagar, Lucknow, affiliated with CBSE (Affiliation No. 2130892).
     - School Vision and Mission statements.
     - *Panch Tattva* Core Values: *Satya* (Truth & Integrity), *Dharma* (Righteous Conduct), *Shanti* (Peace & Mindfulness), *Prema* (Compassion & Respect), and *Ahimsa* (Non-Violence & Ecological Harmony).
     - Leadership profiles: Founder & Managing Trustee (Dr. Vikramaditya Singhania) and Principal (Mrs. Sunita Mehrotra).
   - **Academics (`AcademicsPage.tsx`)**:
     - NEP 2020 5+3+3+4 Curriculum Alignment: Foundational & Preparatory Wing (Classes I–V), Middle School Wing (Classes VI–VIII), Secondary School Wing (Classes IX–X).
     - STEM & Innovation Focus: Coding, Robotics lab, AI workshops, experiential learning.
     - Assessment Framework: Continuous and Comprehensive Evaluation (CCE) following CBSE guidelines, periodic formative assessments, and board examination preparedness.
   - **Admissions (`AdmissionsPage.tsx`)**:
     - 5-Step Admission Journey: Enquiry & Registration, Campus Tour & Interaction, Application Form Submission, Document Verification & Assessment, Fee Payment & Formal Enrolment.
     - Age Eligibility Matrix: Standard age criteria from Nursery (3+ years) to Class X (15+ years) as of March 31st of the academic year.
     - Document Checklist: Birth certificate, transfer certificate (TC), previous report cards, Aadhaar card copies, passport photographs, and immunization records.
     - Direct CTA: Direct link to the existing online application portal (`#/apply`).
   - **Campus & Facilities (`FacilitiesPage.tsx`)**:
     - 9 Infrastructure Showcases: Smart Interactive Classrooms, Advanced Science Labs (Physics, Chemistry, Biology), High-Tech Computer & Robotics Lab, 15,000+ Volume Library, Multi-Sport Complex (cricket, basketball, badminton, athletics), GPS & CCTV-enabled Safe Transport Fleet, Hygienic Dining & RO Water, Full-Time Medical Infirmary, and 24x7 Security & CCTV Surveillance.

5. **Brand Identity & Reusable Public Components (`web/src/components/public/`)**:
   - `SchoolCrest.tsx`: Official scalable vector logo featuring radiating golden sun, open book, and royal navy shield representing illumination through education.
   - `PublicNavbar.tsx`: Sticky navigation bar with school crest, page links with active indicators, quick phone/email links, mobile hamburger drawer, and high-visibility "Login to ERP" button. Responsive breakpoint tuned to `lg:` (1024px) to guarantee zero layout wrapping on tablets.
   - `PublicFooter.tsx`: Rich institutional footer with CBSE affiliation data, complete address (Sector 12, Gomti Nagar, Lucknow, UP - 226010), emergency contact numbers, school working hours, quick links, and discrete ERP gateway.
   - `PublicLayout.tsx`: Common page wrapper managing sticky navbar, main viewport content, and footer layout.

6. **Verification & Quality Assurance**:
   - **Vitest Unit Test Suite**: Added `web/src/pages/public/website/Website.test.tsx` (7 tests covering navigation rendering, page routing, ERP login links, return-to-website button, and responsiveness).
   - **Test Results**: All **19 test files passed (91 tests passed, 2 skipped, 100% green)**.
   - **Production Build**: `npm run build` completed cleanly in 10.25s with all chunks and hero image asset (`dist/assets/hero-campus-*.jpg`) generated without warnings.
   - **Responsive Browser Visual Verification**: Puppeteer headless testing across 5 standard device viewports (1440px desktop, 1280px laptop, 768px tablet, 390px mobile, 360px small mobile):
     - Zero horizontal scrollbar/overflow across all resolutions.
     - Mobile navigation drawer opens and closes smoothly.
     - Hero campus image remains centered with students and main entrance in focus.
     - Zero regressions to ERP login, dashboard, or internal modules.

---

## 7. Operational Traps & Hard-Won Lessons

1. **Postgres vs SQLite**: SQLite returns naive datetimes and misses foreign key wipe order bugs. Always verify migrations and logic against native PostgreSQL.
2. **`alembic upgrade head` after Pytest**: Pytest runs `create_all` which drops/creates tables without writing Alembic version stamps. Drop the public schema before running Alembic migrations.
3. **Zombie Uvicorn Processes**: On Windows, always ensure port 8000/8078 has a single listener (`netstat -ano | findstr :8000`) before starting the server.
4. **HTML `<button>` Submit Default**: A `<button>` without an explicit `type="button"` inside a `<form>` submits the form. Use `ActionButton` which defaults to `type="button"`.
5. **React Controlled Input Automation**: Setting `input.value` in browser automation does not trigger React's synthetic `onChange`. Use `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set` before dispatching `input`.
6. **Query Cache Lifecycle**: Query cache must be cleared on logout (`qc.clear()`) so subsequent logins on shared office PCs cannot inspect cached data from other roles.
7. **LF Line Endings**: `web/src/api/schema.d.ts` is pinned to LF via `.gitattributes` to ensure schema drift checks pass across Windows and Linux.
8. **Badge Wrapping & Flex Constraints**: Always pair `truncate min-w-0` on flexible text containers with `shrink-0` on sibling badge clusters in card headers; otherwise, longer text pushes right-side badges beyond card borders.
9. **Visual Cleanliness in High-Volume School Offices**: Avoid explanatory paragraph subtitles beneath main headings; school administrators and counter clerks navigate repetitively and prefer immediate vertical access to filters, data tables, and primary actions.
10. **Headless Chrome PDF Rendering**: When generating PDFs via Chrome headless, avoid page breaks inside cards and tables using `break-inside: avoid` and `@page` layout margins to guarantee zero split headers or dangling footers.
11. **Year-scoped facts must never hold `student_id`**: Marks, homework submissions, and daily attendance records attach strictly to `enrolment_id`. `Mark.student_id` is a read-only `@hybrid_property` without a setter — never attempt to assign `mark.student_id = x` or instantiate `Mark(student_id=x)`.
12. **Services `flush()`, Endpoints `commit()`**: Service functions in `app/services/` must call `db.flush()`, NEVER `db.commit()`. Calling `db.commit()` inside service logic breaks per-test transaction savepoint isolation (`join_transaction_mode="create_savepoint"` in `conftest.py`), causing uncommitted data from one test to leak into subsequent tests or violate foreign key constraints. Commits belong exclusively in API route handlers (`app/api/`).
13. **Operational seed rows must avoid `teacher_1` and slot 1**: When adding sample data to `seed.py` for operational tables (such as leave requests or substitutions), never attach them to `teacher_1` (`TCH001`) or the first timetable slot (`id=1`). The test suite fixtures assume `teacher_1` opens with a clean zero-used balance, and slot 1 is used by timetable tests to verify deletion without FK violations. Target `teachers[-1]` instead.
14. **React Native Hermes `window` Polyfill Trap**: In React Native with Hermes, `typeof window !== "undefined"` is true (`window === globalThis`). Never rely on `typeof window` to branch between web and mobile environments; use `Platform.OS === 'web'` and query `Constants.expoConfig?.hostUri` to dynamically discover developer machine LAN IP.
15. **Uvicorn Host Binding for Physical Mobile Devices**: When testing on physical mobile devices over Wi-Fi, Uvicorn MUST be started with `--host 0.0.0.0 --port 8000`. Omitting `--host` binds exclusively to `127.0.0.1`, which refuses connections from external LAN clients even if they are on the same Wi-Fi subnet.
16. **Fee Invoice Serialization Key**: In `backend/app/services/fees.py`, the net invoice amount is keyed as `"payable"`, with `"balance"` for outstanding dues. Frontend clients looking for `invoice.total` or `invoice.amount` silently resolve to `undefined` or `0.00` if `payable` is omitted from property lookups.
17. **Boolean Strict Equality Traps in Filters**: Never combine mutually exclusive equality checks with `&&` (e.g. `val === null && val === undefined` is mathematically impossible in JavaScript and always evaluates to `false`). Use loose equality `val == null` or logical OR `val === null || val === undefined`.
18. **Guardian Serialization Completeness**: In `backend/app/api/admin/applications.py`, ensure all columns from `ApplicationGuardian` (`qualification`, `office_address`, `date_of_birth`, etc.) are explicitly serialized in `_guardian_out`. Missing keys silently drop edited fields on browser reload even though they exist in the database.
19. **Dynamic Enrollment Resolution on Application Detail**: When an applicant is enrolled, `application.student_id` links to the lifetime `students` row, but class, section, and roll number exist on the annual `enrolments` row. Always resolve `enrolled_student` dynamically via `db.get(Student, app.student_id)` and the active enrolment record.
20. **`Enrolment` Academic Year Relationship Trap**: The `Enrolment` model has `academic_year_id` (`BIGINT`), NOT an `academic_year` ORM relationship. Accessing `enrolment.academic_year.code` raises `AttributeError`. Safely resolve via `db.get(AcademicYear, enrolment.academic_year_id)` or fallback to `application.cycle.academic_year.code`.
21. **ActionButton Form Submission**: Using `<ActionButton>` inside a `<form onSubmit={...}>` with an explicit `type="submit"` requires that `ActionButton` pass `type="submit"` through to the underlying `<button>` and allow `onClick` to be optional; otherwise, the browser does not fire the synthetic form submit event.
22. **Seed Idempotency Table Coupling**: When decommissioning models, inspect seed idempotency gates. If `seed.py` uses a decommissioned model (e.g. `select(Candidate)`) to gate optional or operational seeding blocks, replace it with an enduring operational table (`StaffLeaveRequest`).
23. **Expo Router Hidden Screen Registration**: In Expo Router, setting `options={{ href: null }}` on `<Tabs.Screen>` cleanly hides the tab from the bottom bar while preserving the route definition. This enables full deep-linking (`router.push('/(role)/screen')`) without route unregistered warnings or missing component errors.
24. **React Native StyleSheet Absolute Fill**: In TypeScript React Native builds, use explicit `{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0 }` for modal backdrops to avoid typing discrepancies with `StyleSheet.absoluteFillObject` across different React Native bundler definitions.
25. **Reception Fee Counter vs Admin Fee Screens Gate Segregation**: The front desk fee counter endpoint `/admin/reception/fees/*` is gated strictly on `fees.payment.collect`. Granting `fees.invoice.read` to the receptionist causes admin-only billing screens (`/fees`, `/fees/defaulters`, `/fees/setup`, `/fees/periods`) to inadvertently appear in the receptionist's navigation sidebar. Omitting `fees.invoice.read` from the receptionist role and declaring only `fees.payment.collect` on `/reception/fee-counter` guarantees complete front-desk navigation hygiene while preserving counter fee collection capabilities.
26. **Decoupled Authorized Pickup Roster from Single-Use Gate Passes**: Emergency or early student gate passes require recording the specific authorized person collecting the student. Coupling gate pass records directly to permanent authorized pickup lists creates friction when a pre-approved relative collects a child. Maintain a permanent roster table (`student_authorized_persons`) for authorized guardians/drivers alongside one-time transactional passes (`student_passes`), allowing the receptionist to either select from the roster or enter a verified single-use collector with relationship.
27. **Complete-Month Fee Collection Invariant**: Receptionists at the front desk are prohibited from taking arbitrary partial fee amounts (e.g. ₹500 against a ₹5,400 bill). Fee collection logic at the reception counter enforces strict chronological FIFO settlement of complete billing periods (1 month, 2 months, ..., N months) to eliminate reconciliation discrepancies and prevent ledger tampering.
28. **Public Website & ERP Root Dual-Dispatch Contract**: In a unified single-page application hosting both public school marketing pages and an authenticated ERP system, routing at the root (`/` or `#/`) must safely distinguish between anonymous public visitors and authenticated staff. Unconditional redirection of `/` to an ERP screen forces prospective parents into an ERP login page; conversely, unconditionally rendering the public homepage breaks existing automated tests (e.g. `App.test.tsx`) that assert a logged-in user navigating to `/` dispatches to their first permitted operational screen. Inspecting authentication state (`me`) within the root dispatcher preserves both user journeys seamlessly.
29. **Responsive Hero Image Focal Offset on Aspect-Ratio Preserving Cards**: Fixed or banner-style hero containers using `object-cover` often default to center alignment (`object-center`), which clips subjects near the edges on tall vertical mobile viewports (e.g. 360px-390px). Applying responsive horizontal focal alignment (`object-[32%_center] sm:object-center`) ensures that critical compositional elements (e.g. student groups walking toward a campus entrance) stay framed across all phone, tablet, and widescreen display sizes.
30. **Employee Service Querying (`in_service` property trap)**: In SQLAlchemy ORM queries, never filter by `Employee.in_service == True` because `in_service` is an unmapped Python `@property` (`status == active and exited_on is None`), not a database column. Attempting to use it in a `where(...)` clause yields an invalid column error. Always filter explicitly with `Employee.status == EmployeeStatus.active, Employee.exited_on.is_(None)`.
31. **ClassSection Join Requirement for ClassSubjectTeacher**: In teacher assignment queries, `ClassSubjectTeacher` does not declare a relationship attribute back to `ClassSection`. When querying subjects or sections taught by a teacher, explicitly join `ClassSection` via `select(...).join(ClassSection, ClassSection.id == ClassSubjectTeacher.class_section_id)`.
32. **Immediate Token Invalidation via `token_version`**: Merely flagging an account as blocked in the database does not prevent continued access if client JWT tokens are cached and valid. Carrying a `token_version` integer in the user record and encoding it into JWT payloads allows both active sessions to be invalidated immediately upon block or password reset (by incrementing `token_version`), while returning HTTP 403 for blocked accounts and HTTP 401 for stale tokens.
33. **Multi-Day Leave Inspection and Clash Creation Ordering**: When applying for Casual Leave with affected periods and substitutions, period inspection and substitution validation must execute *before* the `StaffLeaveRequest` is flushed to the database. Flushing the leave application prematurely registers the teacher as on leave for those dates, causing self-clash detection issues during substitution eligibility evaluation.
34. **Parent-App-Only Multilingual Boundary**: To preserve developer ergonomics and administrative consistency, i18n support is restricted strictly to the Parent mobile app. Only static copy (labels, tab titles, headers, status strings, modal messages) is localized via translation dictionaries. Dynamic database entities (student names, descriptions, currency amounts, formatted dates) remain unadulterated to prevent translation corruption.
35. **Attendance Shortage Test Lifecycle via Record Mutation**: In unit tests verifying attendance shortage thresholds (< 75%), inserting duplicate `Attendance` rows for students who already have seed records will trigger `IntegrityError` on the `uq_attendance_enrolment_date` unique constraint. The reliable way to test shortage triggering and clearing is to query existing attendance records for the student's active enrollment, mutate a portion of them to `absent` to drive attendance strictly below 75%, assert the alert appears, and then restore them to `present` to assert the alert disappears.
36. **Multi-Child Alert Context Switch Invariant**: When parents tap an alert for Child B while Child A is currently selected, the app MUST invoke `selectChild(alert.child_id)` synchronously before executing `router.push(alert.route)`. Without this synchronous context switch, destination screens (such as Fees, Attendance, or Results) load the currently selected child's data rather than the child to whom the alert belongs.

---

## 8. Session 18 Features & Architectural Deliverables (26 Sep 2026)

### 1. Removal of Teacher Meeting Slip
- **Alembic Migration `a1b2c3d4e5f8`**: Dropped `teacher_meeting_requests` table.
- **Backend Purge**: Removed `TeacherMeetingRequest` model from `app/models/reception.py` and `app/models/__init__.py`. Deleted schemas (`TeacherMeetingSlipCreate`, `TeacherMeetingSlipOut`), permissions (`reception.meetings.teacher`), and API endpoint file `app/api/teacher/meetings.py`.
- **Frontend & Mobile Purge**: Removed `PrintableTeacherMeetingSlip.tsx` and simplified `web/src/pages/reception/MeetingsPage.tsx` to handle only Principal Meeting Slips. Deleted `mobile/app/(teacher)/meetings.tsx` and removed Teacher meetings tab from `mobile/app/(teacher)/_layout.tsx`.
- **Existing Workflows Intact**: Principal Meeting Slip workflow (`POST /admin/reception/meetings`, status tracking, and printable slips) verified with 100% test pass rate in `tests/test_receptionist_operations.py`.

### 2. Admin User Access Management
- **Database Schema**: Added `app_access_blocked` (boolean, default False) and `token_version` (integer, default 1) to `User` model (`app/models/user.py`).
- **Auth Enforcement Layer**:
  - `app/core/security.py`: JWT payload embeds `token_version`.
  - `app/core/deps.py`: `get_current_user` rejects blocked users with HTTP 403 Forbidden ("App access has been blocked by school administrator") and rejects tokens with stale `token_version` with HTTP 401 Unauthorized ("Token has been invalidated; please log in again").
  - `app/api/auth.py`: Login endpoint rejects blocked users with HTTP 403 Forbidden.
- **Admin Management API (`app/api/admin/users.py`)**:
  - `GET /admin/users`: Search, filter by role (teacher, parent, student) and blocked status, returns user list with app access flags.
  - `POST /admin/users/{user_id}/block`: Sets `app_access_blocked = True`, increments `token_version` (immediate session kill), logs audit trail.
  - `POST /admin/users/{user_id}/unblock`: Unblocks app access, logs audit trail.
  - `POST /admin/users/{user_id}/reset-password`: Resets password, increments `token_version` (revoking all active tokens), logs audit trail.
- **Web UI (`web/src/pages/UserAccessPage.tsx`)**:
  - Registered in `web/src/screens.ts` at `/admin/users` under Administration (`settings.general.read`).
  - Search by name/email/phone, filter by role chips (All, Teacher, Parent, Student), toggle block/unblock with confirmation dialogs, reset password with temporary password generation.

### 3. Timetable End-to-End & Menu Consistency
- **Active Relief Substitution State**:
  - Updated `SlotOut` schema with `id`, `is_relief`, and `relief_teacher`.
  - `app/services/timetable.py`: Dynamically checks active substitutions for class slots on the queried weekday. When a substitute is assigned, returns `is_relief = True` and the substitute's full name.
- **Parent Timetable Access**:
  - Added endpoint `GET /parent/children/{student_id}/timetable` verifying parent guardianship.
  - Added screen `mobile/app/(parent)/timetable.tsx` with weekly day switcher (Mon–Sat), period cards with start/end times, room numbers, teacher names, and dynamic "🔄 Relief Substitute Cover" badge with covered-by details.
- **Mobile Navigation Drawer Synchronization**:
  - `mobile/src/components/NavDrawer.tsx`: Synchronized all 4 bottom tabs under a dedicated `NAVIGATION` category for Teacher, Parent, and Student roles, ensuring complete parity between bottom tabs and the hamburger drawer menu.

### 4. Teacher Leave System & Ranked Substitutions
- **Configurable Leave Types**:
  - Leave types dynamically read from school leave configuration (not hardcoded to CL).
  - Helper `is_casual_leave(leave_type)` identifies casual leave for period inspection and substitution enforcement.
- **4-Tier Ranked Substitute Suggestions Algorithm**:
  - When inspecting affected slots for a casual leave application, candidates are ranked into 4 tiers:
    1. **Tier 1 (Priority 1)**: Teachers who teach the *same subject* to the *same grade/class*.
    2. **Tier 2 (Priority 2)**: Teachers who teach the *same subject* to other grades.
    3. **Tier 3 (Priority 3)**: Teachers who teach the *same grade* (any subject).
    4. **Tier 4 (Priority 4)**: Any other active teacher in service at the school.
  - **Availability Filtering**: Candidates are excluded if they have a scheduled teaching period at that time, already have an active substitution assignment, are on approved leave, or are not in active service.
- **Workflow & 100% Cover Gate**:
  - Multi-day range inspection (`POST /teacher/leave/inspect`): identifies all timetable clashes across the requested date span and returns ranked available candidates for each period.
  - Application with substitutions (`POST /teacher/leave/apply`): creates pending substitutions and sends in-app notifications to requested substitute colleagues.
  - Colleague response (`POST /teacher/substitutions/{id}/respond`): colleagues can accept or decline requests.
  - Reassignment (`POST /teacher/leave/applications/{id}/reassign`): if a colleague declines, the applicant teacher can select another available candidate.
  - Admin approval locked gate: `approve_teacher_leave_with_substitutions` enforces that for Casual Leave, 100% of affected periods must have assigned or accepted substitutions before admin approval is permitted. Non-casual leaves can be applied for and approved directly.
- **Mobile Teacher Leave UI (`mobile/app/(teacher)/leave.tsx`)**:
  - Interactive multi-tab layout ("Apply", "My Requests", "My Leaves").
  - Dynamically displays affected periods, ranked candidate pickers with priority tags, coverage summary, and status cards.

### 5. Parent App Multiple Languages (i18n)
- **Localization Infrastructure**:
  - `mobile/src/i18n/translations.ts`: Complete English and Hindi dictionaries covering all static labels, navigation titles, buttons, statuses, alerts, and placeholders.
  - `mobile/src/i18n/I18nContext.tsx`: `I18nProvider` context providing `locale`, `setLocale`, and `t(key)`.
  - Persistence: Automatically persists language preference to device storage via `@parent_language_pref` (`AsyncStorage`).
- **Complete Static Copy Coverage**:
  - Localized across all 10 Parent mobile screens and navigation:
    1. `mobile/app/(parent)/_layout.tsx`: Localized bottom tab bar labels.
    2. `mobile/src/components/NavDrawer.tsx`: Localized parent navigation items, logout, and added a quick `[ EN | हिन्दी ]` language switcher header toggle.
    3. `mobile/app/(parent)/profile.tsx`: Dedicated App Settings card with Language Preference picker (`English` vs `हिन्दी (Hindi)`).
    4. `mobile/app/(parent)/dashboard.tsx`: Localized greeting, quick navigation cards, summaries, and action links.
    5. `mobile/app/(parent)/child.tsx`: Localized student details labels (Class, Section, Roll No, Admission No, Blood Group, Emergency Contact).
    6. `mobile/app/(parent)/fees.tsx`: Localized outstanding balance, invoiced, paid, dues, invoice rows, receipt download, and payment confirmation dialogs.
    7. `mobile/app/(parent)/attendance.tsx`: Localized shortage alerts, monthly calendar navigation, legends, summaries, and leave application forms.
    8. `mobile/app/(parent)/homework.tsx`: Localized status counters, assignment list, and read-only student submission notes.
    9. `mobile/app/(parent)/results.tsx`: Localized exam list, fee withholding banner, scorecard details, marks table, and official PDF download trigger.
    10. `mobile/app/(parent)/grievances.tsx`: Localized helpdesk headers, status pills, category chips, priority chips, new grievance modal, message thread, and reply composer.
    11. `mobile/app/(parent)/notices.tsx`: Localized category filter chips (All, Urgent, Academic, Holiday, General), urgent alert banner, circular attachments, and audience tags.
    12. `mobile/app/(parent)/timetable.tsx`: Localized day switcher (सोम, मंगल, बुध, etc.), period indicators, teacher labels, and relief substitute badges.
- **Scope & Data Integrity**:
  - Translations restricted exclusively to the Parent app (Teacher and Student apps remain in standard English).
  - Dynamic database data (student names, descriptions, dates, amounts) remains untouched, guaranteeing zero translation corruption or financial display errors.

---

## 9. Session 19 Features & Architectural Deliverables (27 Sep 2026)

### 1. Website Sidebar Section Headings Redesign (`web/src/layout/Shell.tsx`)
- **Visual Hierarchy & Styling**:
  - Transformed faint grey text (`text-white/50`) into high-contrast, polished section headings (`text-[11px] font-bold text-white/90 uppercase tracking-wider`).
  - Added vertical branding accent pill (`w-1 h-3 rounded-full bg-blue-300/80 mr-2 shrink-0`) to visually anchor each section group.
  - Added hairline divider rule (`flex-1 h-px bg-white/10 ml-2`) providing subtle horizontal separation between logical ERP domains.
  - Adjusted spacing (`pt-5 pb-1 px-3`) for optimal vertical rhythm across all 32 declared ERP screens.
- **Structural Integrity**:
  - Retained strict non-clickable structural role (`role="presentation"`). Zero modifications to routing, permissions, or screen definitions in `web/src/screens.ts`.
  - Verified across multiple role sidebars (Office Administrator, Front Desk Receptionist) with zero visual regressions.

### 2. Mobile Future Feature Placeholders (`mobile/src/components/NavDrawer.tsx`)
- **Non-Interactive Roadmap Items with "Coming Soon" Badges**:
  - **Parent Role**:
    - `Call Class Teacher` (under `COMMUNICATION`)
    - `Message Class Teacher` (under `COMMUNICATION`)
  - **Teacher Role**:
    - `Today's Class` (under `ACADEMICS`)
    - `Parent Messages` (under `COMMUNICATION`)
  - **Student Role**:
    - `Today's Class` (under `ACADEMICS`)
    - Strictly preserves child safety policy: **Students never have direct teacher messaging**.
- **UX & Accessibility**:
  - Rendered with disabled visual cues (`opacity: 0.55`, grey text and icons).
  - Tapping disabled items has no effect (`disabled={true}`).
  - Equipped with rounded pill badge (`comingSoonBadge`: `bg-indigo-50`, `border-indigo-100`, text `Coming Soon` in `indigo-600`).
  - Multilingual support: fully translated for Parent app in `mobile/src/i18n/translations.ts` (`en: "Coming Soon"`, `hi: "जल्द आ रहा है"`).

### 3. Student & Parent Home Important Alerts System
### 3. Student & Parent Home Important Alerts System & Persistent Lifecycle
- **Alert Types & Thresholds**:
  1. **Attendance Shortage Alert**: Strict condition `attendance_pct < 75.0`. Severity `danger` (`#dc2626`), emoji `⚠️`. Tapping navigates to `/(role)/attendance`.
  2. **Fee Due Alert**: Condition `fee_due > 0.0`. Severity `warning` (`#d97706`), emoji `💰`. Formatted as `₹X,XXX.XX outstanding`. Tapping navigates to `/(role)/fees` (or modal on student).
  3. **Report Card Available Alert**: Condition `latest_report_card` published. Severity `info` (`#4f46e5`), emoji `📄`. Tapping navigates to `/(role)/results`.
  4. **Periodic Test Result Available Alert**: Condition `latest_periodic_test` published. Severity `info` (`#0284c7`), emoji `📊`. Tapping navigates to `/(role)/results`.
- **Persistent Alert Lifecycle Rules (`backend/app/models/notification.py`, `backend/app/services/alerts.py`)**:
  1. **Attendance Shortage**: Disappears after the student or parent views it. Stored in `alert_views` with dynamic event key `att-{absent_count}-{latest_absent_date}`. If a new absence occurs or absence count increments while still below 75%, the event key advances and a new alert reappears.
  2. **Report Card**: Disappears after viewing (via alert tap or direct navigation to results/report card screen). Does not show again for that exam.
  3. **Periodic Test Result**: Disappears after viewing (via alert tap or direct navigation to results screen). Does not show again for that exam.
  4. **Fee Alert — STRICT EXCEPTION**: Fee alerts **MUST remain visible until the outstanding fee is fully paid**. Simply viewing/tapping the alert does **NOT** dismiss it. Automatically clears once outstanding balance reaches zero.
  5. **Parent Multi-Child Independence**: Viewed state is tracked independently per user and per child (`user_id`, `student_id`). Viewing an alert for Child A never dismisses Child B's alert.
  6. **Persistence**: Backed by `alert_views` table with tenant isolation (`school_id`), persisting across devices, sessions, and page reloads.
- **Backend API Endpoints**:
  - `GET /student/dashboard`: Enriched with alerts array filtered against current user's viewed alerts.
  - `GET /parent/alerts`: Aggregates active unviewed alerts across all children in `me.children` for multi-child parents, with child attribution (`child_id`, `child_name`).
  - `POST /student/alerts/view`: Records viewed state for student (strictly refuses fee alert dismissal).
  - `POST /parent/alerts/view`: Records viewed state for parent with `child_id` (strictly refuses fee alert dismissal).
- **Mobile Component (`mobile/src/components/ImportantAlerts.tsx`)**:
  - Color-coded alert cards with left accent border (`borderLeftWidth: 4`), emoji icon, title, description, and chevron navigation indicator.
  - Header section with red accent bar and count badge.
  - **Zero Empty Container Invariant**: If 0 alerts apply, the container renders `null` with no empty cards or borders.
- **Parent Multi-Child Integration (`mobile/app/(parent)/dashboard.tsx`)**:
  - Queries `GET /parent/alerts` to aggregate alerts across all children.
  - Titles display clear child attribution (e.g. `Fee Due — Aarav Sharma`, `Report Card Available — Ishita Sharma`).
  - **Context Switch Invariant**: On tap, calls `selectChild(alert.child_id)` before calling `router.push(alert.route)` so the destination screen immediately displays the correct child's context.

### 4. Website — Redesigned Solid Dark-Blue Navigation Sidebar (Akkhor Theme Pattern)
- **Visual Design & Palette (`web/src/layout/Shell.tsx`, `web/src/layout/NavIcons.tsx`)**:
  - **Sidebar Panel**: Solid dark-blue vertical navigation panel (`#042954`), replacing previous purple `bg-primary`.
  - **Brand Header Bar**: Vibrant amber/orange banner (`bg-gradient-to-r from-[#ffa726] to-[#fb8c00]`, `h-14`) with a circular white crest badge (`w-8 h-8 rounded-full bg-white flex items-center justify-center`), bold white uppercase "SUNRISE" header, and "PUBLIC SCHOOL" subtitle. (The hamburger toggle button is located cleanly in the main top header bar across all roles, with the sidepanel header kept clean and dedicated solely to school branding on mobile, tablet, and desktop).
  - **Navigation Items**:
    - **Icons**: Custom golden-amber SVG icons (`text-[#ffa726]`, `18x18px`) for every screen route in [`NavIcons.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/web/src/layout/NavIcons.tsx).
    - **Labels**: High-contrast, clean typography (`text-[#c2d0e2]`, hovering to `text-white`).
    - **Right-Facing Chevrons `>`**: Displayed on items with expandable/sub-navigation or multi-view hubs (`screenHasChevron(path)`), matching the Akkhor template reference pattern.
    - **Item Separators**: Hairline horizontal dividers (`border-b border-white/[0.03]`) and section boundaries for a structured, professional vertical rhythm.
    - **Active / Highlighted State**: Active route highlighted with deep navy background (`bg-[#021b38]`), vibrant amber text (`text-[#ffa726] font-semibold`), amber chevron, and a solid left accent border (`border-l-4 border-l-[#ffa726] pl-[10px]`).
  - **Section Headings**: Visually distinct, non-clickable structural headers (`text-[10px] font-bold text-blue-200/50 uppercase tracking-widest`) with amber vertical pill accent (`w-1 h-2.5 rounded-full bg-[#ffa726]/80`) and hairline horizontal rule.
  - **Responsive Behavior**: Desktop collapsible rail/drawer (`w-60` vs `w-0 invisible`), mobile off-canvas drawer with dark backdrop overlay (`bg-black/60`), and synchronized toggles.
  - **Role & Route Integrity**: Zero changes to permissions, screens registry, or RBAC routing.

### 5. Automated Verification & Artifacts
- **Backend Test Suite**: 769 passed, 2 skipped (100% green).
- **Backend Alert Unit Tests (`backend/tests/test_alerts.py`)**: 10 passed in 21s (100% green).
- **Web Unit Tests (`npm test` in `web/`)**: 109 passed, 2 skipped in Vitest (100% green across 20 test files).
- **Typecheck**: 0 errors across web and mobile TypeScript suites.
- **Redesigned Sidebar Visual Verification Suite (`docs/screenshots/session20/` and persistent artifact directory)**:
  1. `session20_sidebar_admin_expanded.png` — Desktop Admin view showing solid dark-blue `#042954` sidebar, amber brand bar, white circular emblem, hamburger toggle, golden icons, chevrons, and active Dashboard state.
  2. `session20_sidebar_active_page.png` — Active page state on `/students` with amber text, active bed, and left border accent.
  3. `session20_sidebar_admin_collapsed.png` — Desktop collapsed state after clicking hamburger toggle.
  4. `session20_sidebar_admin_reopened.png` — Desktop reopened state after toggling again.
  5. `session20_sidebar_receptionist.png` — Role-specific Front Desk & Receptionist sidebar view.
  6. `session20_sidebar_mobile_drawer.png` — Mobile view showing responsive drawer with backdrop overlay.
- **Previous Session 19 Visual Verification Suite (`docs/screenshots/session19/`)**:
  1. `session19_web_admin_sidebar.png`
  2. `session19_web_receptionist_sidebar.png`
  3. `session19_mobile_student_dashboard.png`
  4. `session19_mobile_student_drawer.png`
  5. `session19_mobile_parent_dashboard.png`
  6. `session19_mobile_parent_drawer.png`
  7. `session19_mobile_teacher_drawer.png`

### 6. Network Auto-Detection & 1-Click Dev Server Automation
- **Root Cause Resolution**: Resolved dual-point failure mode where developer machine IP changes dynamically upon switching Wi-Fi networks (e.g. `10.109.197.170` to `192.168.29.227`) and agent sub-processes terminate upon system sleep or runner restarts.
- **Auto-Discovery Engine (`scripts/generate_qr.py`)**:
  - Dynamically probes default gateway routing socket to discover the active LAN IPv4 address.
  - Synchronously rewrites `mobile/.env` with `EXPO_PUBLIC_API_URL=http://<ACTIVE_IP>:8000`.
  - Generates Expo QR code image for `exp://<ACTIVE_IP>:8081` saved to `expo_qr_code.png` and `web/public/expo_qr_code.png`.
  - Windows cp1252 safe console reporting.
- **1-Click Launchers**:
  - `start_dev.bat`: Launches Backend (`uvicorn app.main:app --host 0.0.0.0 --port 8000`), Web ERP (`npm run dev -- --host`), and Expo Metro (`npx expo start --lan -c`) in three independent Windows command windows that persist across IDE reloads, and opens the QR code image for instant phone scanning.
  - `show_qr.bat`: Instant utility to re-detect IP, update `.env`, and display the latest QR code without restarting running servers.

### 7. Session 21 Directives — Public-Facing CBSE School Website Modernization
- **Institutional Identity**: Sunrise School, Gomti Nagar, Lucknow, CBSE Affiliated, Estd. 2011.
- **Core Architecture**: Upgraded the 9-page public website (`PublicLayout.tsx` in `web/src/pages/public/website/`) while preserving the internal ERP shell (`web/src/layout/Shell.tsx`) and mobile app completely untouched.
- **Navigation & Routing**:
  - `/` & `/home` — `HomePage.tsx`
  - `/about` — `AboutPage.tsx`
  - `/academics` — `AcademicsPage.tsx`
  - `/admissions` — `AdmissionsPage.tsx` (all "Apply Online" CTAs route to real `/apply`)
  - `/facilities` — `FacilitiesPage.tsx`
  - `/school-life` — `SchoolLifePage.tsx` (Clubs, sports, arts, houses)
  - `/events` — `EventsPage.tsx` (Calendar & highlights)
  - `/gallery` — `GalleryPage.tsx` (Categorized media showcase with high-res Lightbox)
  - `/contact` — `ContactPage.tsx` (Gomti Nagar campus, enquiries, visiting hours)

### 8. Session 21 Phase 2 — Visual Storytelling & Master Photography Integration
- **Photorealistic Coherent Photography Set**:
  - Generated and integrated a 13-image branded master photography set captured specifically for Sunrise School, Gomti Nagar, Lucknow.
  - Assets persisted in `web/public/images/school/` and `web/src/assets/school/`.
  - Typed metadata registry: `web/src/pages/public/website/schoolPhotos.ts`.
- **Strict Visual Identity Enforcement**:
  - *Architecture:* Warm red terracotta stone and buff sandstone institutional facade with louvers, Ashoka trees, and landscaped gardens.
  - *Uniform:* Crisp white collared shirts, navy blue ties with subtle diagonal gold stripes, navy trousers/skirts, embroidered crest.
  - *Signage:* Authentic campus branding reading *"SUNRISE SCHOOL, GOMTI NAGAR, LUCKNOW"*, *"ATAL TINKERING LAB"*, and *"SPORTS COMPLEX"*.
- **Page-by-Page Integration**:
  - `HomePage.tsx`: Exterior hero, academic stage wing photos, 4 facilities preview photos, campus life in motion row.
  - `AboutPage.tsx`: Entrance gate, reception lobby, and faculty mentorship spotlight.
  - `AcademicsPage.tsx`: Smart classroom, robotics lab, composite science lab, and computing lab photos.
  - `AdmissionsPage.tsx`: Reception welcome rotunda on the admissions portal card.
  - `FacilitiesPage.tsx`: Photo banners across all major facilities + Gate No. 1 security checkpoint.
  - `SchoolLifePage.tsx`: Sports complex showcase (outdoor turf & indoor arena) and co-curricular club photos.
  - `EventsPage.tsx`: Event banners for Science Expo, PTM, Tarang Sports Meet, and Udaan Cultural Fest.
  - `GalleryPage.tsx`: Complete real photography grid across 5 categories + interactive Lightbox with prev/next navigation.
  - `ContactPage.tsx`: Main entrance gate visual backdrop in the Gomti Nagar campus locator.
- **Verification Gates (100% Green)**:
  - Web unit tests: `114 passed, 2 skipped` (`Website.test.tsx` 12/12 passing).
  - Web TypeScript: `0 errors` (`npx tsc --noEmit`).
  - Mobile TypeScript: `0 errors` (`npm run typecheck`).
  - Backend tests: `770 passed, 1 skipped` (`pytest -q`).
  - Vite production build: Clean build in 7.03s (`npm run build`).
  - Visual verification: 17 screenshots captured in `docs/screenshots/session21/`.

### 9. Session 22 — Central Academy Reference Website Study & Institutional Public Website Upgrade
- **Reference Site Analysis**: Evaluated `https://inr.centralacademyschool.com/` (Central Academy, Indira Nagar, Lucknow) to understand authentic institutional CBSE structure, mandatory public disclosures, downloads architecture, and circular broadcasting.
- **Top Utility Micro-Strip Removal**:
  - Permanently eliminated desktop micro-bar (`Admissions Guide | Session 2026-27 | info@...`).
  - Main institutional navbar is now the topmost element on desktop and mobile.
- **Zero Public ERP Login Links**:
  - Strictly purged all login links ("Login to ERP", "Sign In", "Parent Portal", "Student Portal", "Teacher Portal", "Branches") from the public website header, mobile drawer, homepage callouts, and footer.
  - The public site serves prospective families, parents, and community members exclusively; internal staff and enrolled users access the ERP via direct `/login` or mobile apps.
- **11-Link Institutional Navigation (`web/src/components/public/PublicNavbar.tsx`)**:
  - Navigation links: `Home`, `About`, `Academics`, `Admissions`, `Campus & Facilities`, `School Life`, `Events`, `Gallery`, `Public Disclosure`, `Resources`, `Contact`.
  - Prominent CTA: `Admission Enquiry / Apply Now` routing directly to `/apply`.
  - Accessible mobile drawer with `tel:+915222990000` tap-to-dial link and quick application button.
- **Mandatory Public Disclosure Section (`/public-disclosure`)**:
  - Implements CBSE Appendix-IX disclosure mandate across 6 structured tabs:
    1. *A. General Information:* School name, Affiliation status, Principal details, School email & contact.
    2. *B. Documents & Information:* Download links for Society Registration, No Objection Certificate (NOC), Recognition Certificate, Building Safety, Fire Safety, Water/Sanitation, and Fee Structure (all 1-page A4 PDFs).
    3. *C. Results & Academics:* Annual academic calendar, fee schedule, and 3-year Class X & XII board examination results table (100% pass rate).
    4. *D. Staff & Faculty:* Principal profile, PGT/TGT/PRT faculty breakdown (52 total teachers, 1:18 teacher-student ratio), Special Educator, and Wellness Counselor.
    5. *E. Infrastructure:* 5-acre campus details, 42 smart classrooms, composite science labs, computer lab, library (12,000+ volumes), and fire safety compliance.
    6. *F. Student Support & Grievance:* POSH Committee, POCSO Committee, Anti-Bullying Cell, and Parent Grievance redressal officers.
  - Prominent yellow demo information notice: *"Demonstration Disclosure Notice: Sunrise School is a demonstration CBSE institution portal. Official certificates and affiliation records are sample representations."*
  - Zero invented credentials: Affiliation number and school code explicitly state `"To be configured (Demo information)"`.
- **Resources & Downloads Hub (`/resources`)**:
  - Card-based download center for official school documents.
  - Approved downloadable resources:
    1. School Prospectus 2026–27 (`/documents/school-prospectus.pdf`)
    2. Academic Calendar 2026–27 (`/documents/academic-calendar.pdf`)
    3. Admission Guidelines & Age Norms (`/documents/admission-guidelines.pdf`)
    4. Approved Annual Fee Structure (`/documents/fee-structure.pdf`)
    5. Curriculum & Syllabus Overview (`/documents/syllabus-overview.pdf`)
    6. Mandatory Public Disclosure Summary (`/documents/public-disclosure-summary.pdf`)
  - Prohibited document policy enforced: "Parent Information PDF" strictly excluded.
- **One-Page PDF Generation Engine (`scripts/generate_one_page_demo_pdfs.py`)**:
  - Python ReportLab generator with custom `NumberedCanvas` enforcing strict programmatic assertion: `assert canvas.page_count == 1`.
  - Produces clean single-page A4 documents with institutional headers, tables, demo disclaimers, and signature blocks in `web/public/documents/`.
- **Announcements & Circulars Architecture**:
  - *Database & Model:* Migration `d5e6f7a8b9c0_public_announcements_fields.py` added `category`, `is_public`, `is_pinned`, `summary`, `expiry_date`, and `attachment_url` to `notices` table.
  - *Backend API:* Public endpoints `GET /public/{school_code}/announcements` (filtered by `is_public=True`, active expiry, pinned first) and `GET /public/{school_code}/announcements/{id}` in `backend/app/api/public/announcements.py`.
  - *ERP Publishing:* Admin/Principal Notices screen (`web/src/pages/Notices.tsx`) updated with category dropdown, "Publish to Public School Website" checkbox, "Pin as Featured Announcement" checkbox, short summary field, and visibility pills.
  - *Public UI:*
    - Homepage marquee/ticker with live announcements count, pinned badges, and circular links.
    - Official Announcements catalog (`/announcements`) with category filtering, search input, and pinned cards.
    - Dedicated Announcement detail circular page (`/announcements/:id`) with back navigation and application CTA.
  - *Initial Live Seed:* 6 official announcements seeded via `scripts/seed_public_announcements.py` (Board results 100%, Admissions Open, STEM Expo, Career Counselling, Autumn Break, PTM).
- **Consolidated 4-Column Footer (`web/src/components/public/PublicFooter.tsx`)**:
  - Column 1: School Identity, Crest, Gomti Nagar story, CBSE affiliation text.
  - Column 2: Consolidated Explore links (all public pages including Public Disclosure, Resources, and Announcements).
  - Column 3: Academic Wings, NEP 2020 5+3+3+4 stages, and streams.
  - Column 4: Admissions & Hours, direct link to `/apply`, campus address, clickable phone helpline (`tel:+915222990000`).
  - Bottom bar: Copyright, demo disclaimer, and quick links to Mandatory Public Disclosures and Downloads.
- **Verification Gates (100% Green)**:
  - Backend pytest: `776 passed, 1 skipped, 0 failed` across entire suite (`pytest -q` in 337s).
  - Web unit tests: `125 passed, 2 skipped` across 21 test files (`npm test -- --run` in 28.9s).
  - TypeScript typecheck: `0 errors` on web (`npx tsc --noEmit`) and mobile (`npx tsc --noEmit`).
  - Vite production build: Clean build in 14.60s (`npm run build`).

### 10. Session 23 - Institutional Refinement Pass: Public Admission Enquiry Integration, Merged School Life & Gallery, Global Announcement Strip, Expanded About Story, and 4 Hero Photos
- **Primary Institutional Navigation & ERP Login CTA (`web/src/components/public/PublicNavbar.tsx`)**:
  - Refined to 9 primary links: `Home`, `About`, `Academics`, `Admissions`, `Campus & Facilities`, `School Life`, `Events`, `Public Disclosure`, `Resources`.
  - Header right action is **`ERP Login →`** (`/login`) using the existing Sunrise ERP login route (clean primary button on desktop and compact header/drawer button on mobile).
  - Purged `Contact` (contact details permanently anchored in the 4-column footer).
  - Purged `Gallery` from navbar (photographic gallery merged directly into `School Life` at `/school-life#gallery`).
  - Mobile drawer provides direct access to the 9 views, `ERP Login →`, and `Apply Online Portal`.
- **Persistent Admission Enquiry Side CTA (`web/src/components/public/AdmissionSideCTA.tsx`)**:
  - Persistent, non-intrusive Admission Enquiry block rendered via `PublicLayout.tsx` across all public informational pages.
  - *Desktop / Tablet:* Subtle, premium vertical tab flush against the right edge with dark slate container, amber gold accents, pen icon, vertical tracking, and `26–27` session badge.
  - *Mobile:* Compact, non-intrusive floating pill docked at `bottom-5 right-4` with amber gold gradient, icon, and pulsing live badge.
  - *Workflow Isolation:* Strictly excluded from the `/apply` admission application portal and `/login`.
  - *Unified Backend Flow:* Clicking opens the existing `AdmissionEnquiryModal`, submitting directly to `POST /public/{school_code}/admission/enquiry` and appearing in the front-desk ERP enquiry workflow without duplicate systems.
- **School Life & Photo Gallery Merged (`web/src/pages/public/website/SchoolLifePage.tsx`)**:
  - Integrated high-quality editorial gallery section at the bottom of School Life (`#gallery`).
  - 5 category filter tabs: `All`, `Campus`, `Classrooms & Labs`, `Sports & Athletics`, `Arts & Culture`.
  - Full-featured Lightbox overlay with smooth next/previous navigation, photo index, category tags, and captions.
- **Public Admission Enquiry Connected Directly to ERP Backend**:
  - Direct integration into ERP `enquiries` table (`backend/app/models/reception.py`) without duplicate models, tables, or workflows.
  - API endpoint: `POST /public/{school_code}/admission/enquiry` in `backend/app/api/public/admission.py`.
  - Schema (`PublicEnquiryCreate`): `parent_name`, `student_name`, `phone`, `email`, `target_class`, `notes`.
  - Invariants enforced:
    - Auto-resolves active cycle via `admission.open_cycle(db, school.id)`.
    - `source = EnquirySource.website`, `status = EnquiryStatus.new`.
    - Duplicate phone handling: If an enquiry with the same mobile exists in the active cycle, appends notes as a new `EnquiryInteraction` with `occurred_at=datetime.now(UTC)` and returns reference ID without duplicating records.
    - Reference code returned: `ENQ-{enquiry.id:04d}`.
  - Frontend modal (`web/src/components/public/AdmissionEnquiryModal.tsx`):
    - Clean modal dialog accessible from persistent side CTA, hero CTA, and floating triggers.
    - Fields: Guardian name, Student name, Mobile, Email, Grade Applying For, Inquiries/Questions.
    - Success state displays unique `ENQ-XXXX` reference number and admissions office contact details.
- **Global Announcement Strip (`web/src/components/public/GlobalAnnouncementStrip.tsx`)**:
  - Rendered globally directly beneath `PublicNavbar` across all public pages in `PublicLayout.tsx`.
  - Excluded strictly from the `/apply` admission application workflow to preserve an undistracted, focused application experience.
  - Deep blue institutional ticker with gold `ANNOUNCEMENT` badge, animated circular headline, and "View All" link routing to `/announcements`.
- **News & Announcements Fallback & Seeding**:
  - Comprehensive demo circulars covering all 7 categories: `Admission`, `Academic`, `Achievement`, `Event`, `Holiday`, `Notice`, `General`.
  - Client-side fallback (`DEFAULT_ANNOUNCEMENTS` in `AnnouncementsPage.tsx` and `AnnouncementDetailPage.tsx`) guaranteeing announcements and circular detail pages are never blank even in offline/empty states.
- **Expanded About Page Institutional Narrative (`web/src/pages/public/website/AboutPage.tsx`)**:
  - Comprehensive institutional history detailing Sunrise School's journey from 2011 to 2026.
  - Fictional Founder Section: Dr. Anand Mohan Shukla (Founding Trustee, Estd. 2011) with portrait (`/images/school/founder_portrait.jpg`), biography, and founding philosophy.
  - Founder's Quote Card: *"Education is not the filling of a vessel, but the kindling of a flame..."*
  - Institutional Milestones Timeline (2011 Foundation, 2014 Secondary Affiliation, 2017 Senior Secondary, 2020 STEM Labs, 2023 Sports Complex, 2026 Innovation Hub).
  - 7-C Educational Philosophy: Curiosity, Critical Thinking, Character, Creativity, Collaboration, Communication, and Confidence.
  - Core institutional values and campus visual showcase.
- **Homepage Photography & Principal Welcome Matching Reference**:
  - Hero and feature cards updated with 4 authentic Sunrise School photographs matching the visual reference: Modern Classroom, Composite Science Lab, Teacher Mentorship, and Athletics/Sports Field.
  - Principal welcome message from Dr. Meera Sharma with institutional quote card.
- **Verification Gates (100% Green)**:
  - Backend pytest: `778 passed, 1 skipped, 0 failed` across entire suite (`backend/tests/test_public_enquiry.py` 2/2 passed).
  - Web unit tests: `125 passed, 2 skipped` across 21 test files (`npm test -- --run` in 15.8s).
  - TypeScript typecheck: `0 errors` on web (`npx tsc --noEmit`).
  - Vite production build: Clean build in 10.21s (`npm run build`).
  - Visual verification: 15 screenshots captured across Desktop (1440x900), Tablet (768x1024), and Mobile (390x844) in `docs/screenshots/session23/`.

### 11. Session 24 - Comprehensive ERP Enhancements: Admission Conditional Birth Certificate & Admin Document Overrides, APAAR ID & Parental Consent, Student ID Cards, Unified Library Circulation, Admin-Managed Certificates Lifecycle & Templates, and Holiday Management & Attendance
- **1. Admission Form — Conditional Birth Certificate Requirement & Admin Document Overrides**:
  - *Dynamic Business Rule:* A birth certificate is mandatory if the applicant is applying for a class in the junior section through UKG, inclusive (`is_junior_section_through_ukg(class_name)`), OR is younger than 5 years old on the relevant admission cutoff date (`get_admission_cutoff_date(db, school_id, cycle_id, class_name)`). If neither condition is true, the birth certificate is optional.
  - *Server-Side & Public Portal Enforcement:* Validated independently on backend submission (`POST /public/{school_code}/admission/apply`). Missing mandatory birth certificate blocks final application submission by default (`422 Unprocessable Content`).
  - *Narrowly Scoped Admin Document Override:* Dedicated permission `admission.document.override` allows Admin to record an authorized document exception for a draft (`POST /admin/admission/applications/{draft_id}/document-overrides`), stored in `application_document_overrides` table with document code, student/draft reference, authorized user, timestamp, and mandatory reason. The audit log permanently records the override.
  - *RBAC Separation Invariant:* Admin override is a narrowly scoped exception authorization; Admin does not manage or process applications. The Admission Cell retains exclusive ownership of normal application workflows and document verification.
  - *Public Draft Reference:* Public draft endpoint (`POST /public/{school_code}/admission/draft`) persists draft applications, returning persistent reference code `DFT-{id}`. Applicants can obtain an administrative override for `DFT-{id}` and then submit successfully without the missing document.
- **2. APAAR ID and Parental Consent**:
  - *Required Admission Workflow Section:* Public admission portal and internal admission forms require selecting either:
    1. An existing 12-digit APAAR ID provided by the parent.
    2. Parental/guardian consent for new students whose APAAR ID is not yet available, authorizing the school to facilitate its creation.
    3. An authorized Admin exception recorded via `application_document_overrides`.
  - *Data Integrity & Audit Invariants:* Parental consent is strictly recorded with consenting parent/guardian name, relation, and UTC timestamp (`apaar_consent_at`). Consent is not treated as an existing APAAR ID or locally generated number.
  - *Student Conversion & Updates:* APAAR fields (`apaar_id`, `apaar_consent`, `apaar_consent_guardian_name`, `apaar_consent_at`) are transferred to `Student` upon conversion and can be updated later (`PATCH /admin/students/{id}`) without duplicate records.
- **3. Student ID Cards with Canonical Enrollment ID**:
  - *Canonical Identifier:* Consistently uses `ENR-{enrolments.id}` (not internal DB IDs or raw roll numbers) for human-readable ID card labels and QR payloads (`sunrise:enrolment:ENR-{enrolments.id}`).
  - *Privacy & Safety Invariant:* Strictly excludes admission number, blood group, emergency contact phone, and personal identifiable information from card front and QR payload.
  - *Active Enrolment Resolution:* Dynamically resolves active academic session enrolment for students with multiple historical enrolments, supporting optional explicit enrolment scoping.
  - *PDF Generators (`backend/app/pdf/id_card.py`)*:
    - Single CR80 standard card (85.6mm x 54mm, 242.6pt x 153.1pt) with header crest, photo box, name, Enrollment ID, class/section, roll number, session code, and QR code.
    - Bulk 8-up A4 printable sheet (2 columns x 4 rows) with cutting guides and margins.
- **4. Unified Library Circulation & Catalogue**:
  - *Enrollment ID Integration:* Circulation is directly linked to the enrolled student record via canonical `ENR-{enrolments.id}`. Zero separate library cards or duplicate student accounts.
  - *Catalogue & Copies:* Books table tracks titles, authors, categories, ISBNs, and copy counts. `book_copies` tracks physical copies with accession numbers (`ACC-{school}-{seq}`) and barcodes (`BC-ACC-XXXX`).
  - *Circulation Service (`backend/app/services/library.py`)*:
    - Borrower lookup by `ENR-{id}` with eligibility evaluation (active enrolment, max 3 active loans, no overdue items, unpaid fines <= ₹100).
    - Issue book copy to student, renew loan, return copy, and calculate overdue fines (₹5.00/day).
    - Fine settlement (collection / waiver) with reason and audit log.
  - *Endpoints & Module Gating (`backend/app/api/admin/library.py`)*: Routes guarded by `library.read` and `library.manage` permissions and `library` module toggle.
  - *Librarian System Role:* Registered `librarian` system role in `app/core/permissions.py` and seeded librarian user (`library@sunrisepublic.edu`) with administrative employee record (`LIB001`).
- **5. Admin-Managed Student Certificates (TC, Bonafide, Character)**:
  - *Configurable Templates (`certificate_templates` table)*: Configurable institutional details, title, header text, body template with variable placeholders (`{student_name}`, `{admission_no}`, `{class_name}`, `{session_code}`, etc.), signatory name, signatory title, and seal toggle.
  - *Certificate Lifecycle (`student_certificates` table)*: `requested` -> `approved` / `rejected` -> `issued` -> `reissued`.
  - *RBAC Restriction:* Certificate request permission `certificates.request` is restricted to Admin, Principal, and designated office staff; `teacher` role is strictly denied by default.
  - *Atomic TC Invariant:* Transfer Certificate request and approval do NOT alter student status; only final TC issuance atomically transitions student status to `transferred_out` and active enrolment to `transferred_out`, preserving all historical financial, academic, attendance, and library records.
  - *Numbering & Reissue:* Concurrency-safe sequence numbering (`audit.next_number`); reissuing increments `reissue_count`, logs reason, and generates PDF with a prominent "DUPLICATE" watermark.
- **6. Holiday Management & Attendance Invariants**:
  - *Database Schema & Migrations:* `holidays` table upgraded with `start_date`, `end_date`, `description`, `is_school_wide`, `status`, `created_by_id`, `cancelled_by_id`, `cancellation_reason`, and `holiday_class_sections` table for section scoping.
  - *Cancellation Invariant:* Holiday cancellation via DELETE/POST requires mandatory reason, updates status to `cancelled`, and retains all historical attendance and working day records.
  - *Holiday Attendance Override:* Dedicated permission `attendance.holiday.override`. Attendance marking on declared holidays is blocked by default (`400 Bad Request`); users with override permission may submit attendance only with a mandatory override reason, recorded in the audit log.
  - *Absence Denominator:* Working day and percentage calculations dynamically exclude declared holidays from the attendance denominator.
- **7. Frontend Implementation (`web/`)**:
  - *Public Admission Portal (`web/src/pages/public/PublicApplyPage.tsx`)*:
    - Dynamic conditional Birth Certificate requirement badge: displays "Mandatory" badge and validation if applicant is applying for Nursery through UKG or age < 5 on cutoff date; displays "Optional" badge otherwise.
    - APAAR ID Section: clear 3-way option (Existing 12-digit APAAR ID with digit formatting, Parental Facilitation Consent with consenting guardian name & relation, and Administrative Exception note).
    - Save Draft modal: saves draft and displays persistent `DFT-{id}` reference code with guidance for parents needing administrative document exceptions.
  - *Admin Admission Document Exceptions (`web/src/pages/admission/AdmissionExceptions.tsx`)*:
    - Dedicated screen at `/admin/admission-exceptions` strictly gated on `admission.document.override` under Admission module.
    - Draft lookup input (`DFT-...`), applicant summary card with missing mandatory documents checklist, reason selector (e.g. Affidavit submitted, Court order, Foreign national exemption), and authorized exception submission with full audit logging.
    - Preserves strict RBAC separation: Admin does not access Admission Cell application processing queues.
  - *Student ID Cards & Profile (`web/src/pages/Students.tsx`)*:
    - Single CR80 ID Card download button (`/admin/students/{id}/id-card`) in student profile drawer.
    - Bulk Print ID Cards modal (`/admin/students/id-cards/bulk?class_section_id=...`) for 8-up A4 printable card sheets.
    - Student profile drawer displays APAAR ID / Parental Consent status.
  - *Unified Library Module (`web/src/pages/Library.tsx`)*:
    - Registered at `/library` under Academics, gated on `library.read` and `library.manage` permissions.
    - Circulation Desk: Canonical Enrollment ID borrower lookup (`ENR-{id}`), active loans list with calculated fines, book issue form with barcode/accession number and loan duration, return book with fine settlement modal, and loan renewal.
    - Books Catalogue tab: Title/author/category search, copy status badges (available, issued, lost), and Add Book Title modal.
  - *Admin-Managed Certificates Module (`web/src/pages/Certificates.tsx`)*:
    - Registered at `/certificates` under Administration, gated on `certificates.read` (teacher role excluded).
    - Certificate requests and issued log with status filters (`requested`, `approved`, `issued`, `rejected`).
    - Request Certificate modal with Atomic TC exit warning (explaining student status transition to `transferred_out` upon issuance while preserving all history).
    - Certificate Templates tab: Configurable institutional details, headers, body templates with placeholders, signatories, and seal toggle for TC, Bonafide, and Character certificates.
  - *Holiday Management & Attendance (`web/src/pages/HolidayManagement.tsx` & `web/src/pages/Attendance.tsx`)*:
    - Registered at `/admin/holidays` under Academics, gated on `attendance.holiday.manage`.
    - Single and multi-day holiday declaration with school-wide or class-specific scoping.
    - Holiday cancellation with mandatory reason.
    - Attendance screen displays declared holiday banner for active section and date.
  - *Screen Registry (`web/src/screens.ts`)*: Added `library` and `certificates` module codes and registered `/admin/admission-exceptions`, `/library`, `/certificates`, `/admin/holidays`.

- **8. Verification Gates & Automated Test Coverage (100% Green)**:
  - *Backend Pytest*: **800 passed, 1 skipped, 0 failed** across all 801 backend tests (778 baseline + 22 new tests).
    - `backend/tests/test_admission_documents_override.py` (3 tests)
    - `backend/tests/test_apaar.py` (5 tests)
    - `backend/tests/test_id_cards.py` (3 tests)
    - `backend/tests/test_library.py` (4 tests)
    - `backend/tests/test_certificates.py` (5 tests)
    - `backend/tests/test_holidays_attendance.py` (2 tests)
    - Full regression across all historical domains (conversion, rbac, timetable, attendance, hr, payroll, fees).
  - *Web Unit Tests (`vitest`)*: **134 passed, 2 skipped, 0 failed** across 25 test files (`npm test -- --run` in 17.14s).
  - *TypeScript Typecheck*: **0 errors** on web (`npx tsc -b`).
  - *Vite Production Build*: **Clean production build in 6.76s** (`npm run build`).
  - *Visual Verification*: **14 screenshots captured** across Desktop (1440x900) in `docs/screenshots/session24/` and brain artifacts directory (`01_public_admission_step1_birth_cert_badge.png` through `14_attendance_declared_holiday_banner.png`).




