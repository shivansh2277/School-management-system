# SESSION-HANDOFF-30.md — Sunrise School ERP

**Date:** 08 October 2026  
**Status:** Session 29 Fully Completed & Verified; Canonical Hand-off for Session 30: **Hostel + Mess Management Module**.  
**Canonical Branch:** `slice/office-feedback` (synced with `origin/main` and `origin/slice/office-feedback`)  

---

## 1. Executive Summary & Verified Baseline

The Sunrise School ERP codebase is fully verified, operational, and in a clean state:
- **Database Schema**: 105 tables total (72 active holding rows, 33 reserved), 852 total active columns (571 non-boilerplate columns displayed; 281 `id`/`school_id`/`created_at`/`updated_at` boilerplate collapsed), 114 real relational foreign keys.
- **Rosters & Academics**: 19 class sections (Nursery through 12-Hum), 190 active students (10 per section), 24 active teaching faculty (28 employees total).
- **Backend Quality Gate**: `pytest -q` in `backend` passes **808 tests passed, 1 skipped, 0 failed** (100% green).
- **Web Frontend Quality Gate**: `npm test` in `web` passes **140 unit/integration tests across 26 test files, 2 skipped, 0 failed** (100% green).
- **TypeScript Checks**: Clean exit code 0 on Web (`npx tsc -b`) and Mobile (`npx tsc --noEmit`).
- **Schema Documentation Verification**: `python scripts/verify_db_docs.py` passes **17/17 checks**.
- **Canonical PDF Deliverables Recompiled & Synced**:
  1. `docs/Sunrise-ERP-Features-Operational-and-Planned.pdf` (778,358 bytes)
  2. `docs/Sunrise-ERP-Operational-Data-Flows.pdf` (3,667,978 bytes)
  3. `docs/Sunrise-ERP-Database.pdf` (2,205,459 bytes)
  4. `docs/Sunrise-ERP-Database-Essentials.pdf` (1,324,866 bytes)

---

## 2. Upstream Completed in Session 29

1. **Public Website Admission Enquiry Fix**: Resolved tenant alias resolution (`sunrise`/`sunrisepublic` -> canonical `SPS`), wired `AdmissionEnquiryModal.tsx` to `/public/SPS/admission/enquiry` with green confirmation feedback, verified multi-tenant persistence into `enquiries` table.
2. **"View Admission Steps" Routing Fix**: Replaced hash anchor navigation with smooth DOM scroll to `#process`, preventing collision with React Router's `<HashRouter>`.
3. **Dedicated Librarian RBAC Role & User Management**: Added `librarian` role strictly scoped to `library.read`, `library.manage`, `comms.notice.read`, isolated from admissions, fees, HR, and settings. Added `/admin/users/{user_id}/roles` endpoints, token version invalidation (`token_version`), and `/user-access` UI with quick login.
4. **Admission Document Overrides Pending Queue**: Transformed `/admin/admission-exceptions` from manual lookup into an automatic pending exceptions queue with student details, document type, reason, timestamp, and 1-click Approve/Reject actions, enforcing that only approved overrides satisfy application checklists.

---

## 3. Session 30 Target: Complete Hostel + Mess Management Module

### Mandatory Architecture Principles
- **Do NOT create duplicate systems**: Reuse existing students (`students`), enrollments (`enrolments`), users (`users`), fee structures/invoices (`fee_plans`, `fee_invoices`), in-app notifications (`in_app_notifications`), audit logging (`audit_log`), and UI design patterns.
- **Tenant Isolation**: Every hostel-related table must derive from `TenantBase` with a non-nullable `school_id` foreign key.

---

### Detailed Specification for Session 30

#### 1. Core Business Model
* **Optional residential facility**: Day scholars operate completely unaffected.
* **Class 9+ Eligibility**: Hostel is available strictly to students enrolled in **Class 9 and above**. Enforced at UI, API, database, and admission validation levels.
* **Multi-Hostel Structure**: Hierarchical structure:
  $$\text{School/Tenant} \longrightarrow \text{Hostel} \longrightarrow \text{Floor} \longrightarrow \text{Room} \longrightarrow \text{Bed} \longrightarrow \text{Student}$$
* **Configurable capacity**: Room capacity is configurable; beds are explicit database records (`beds`), not just an integer count.
* **UI Representation**: Displays hostel hierarchy, room layouts, individual beds, and assigned resident students with vacancy status.
* **Demo Seed Target**:
  * **Boys Hostel**: 2 floors, 5 rooms total, 2 beds/students per room, 10 beds total, 10 demo residents (Class 9+ male students).
  * **Girls Hostel**: 2 floors, 5 rooms total, 2 beds/students per room, 10 beds total, 10 demo residents (Class 9+ female students).
* **Constraints**: No room occupancy can exceed configured room capacity; no two active students can occupy the same bed simultaneously.

#### 2. RBAC & Roles
Exactly two new hostel RBAC roles:
* **Chief Provost**: School-wide hostel authority across all hostels in the tenant.
  * Permissions: View all hostels, manage hostels/floors/rooms/beds, view all residents, admit students, allocate/change room and bed, transfer students between rooms/hostels, view allocation history, manage hostel exits, view hostel attendance, view leave/outing records, view incidents/complaints, manage hostel notices, manage mess menu, view reports, manage wardens, configure hostel fee structures.
* **Warden**: Assigned to **exactly one hostel**.
  * Permissions: Limited strictly to their assigned hostel (`assigned_hostel_id`). View residents, view rooms/beds, admit eligible students to assigned hostel, allocate/change room and bed within assigned hostel, view allocation history, mark evening attendance, approve/reject leave/outing requests, record student return, view/manage hostel complaints/incidents, manage notices, view menu, view reports.
  * **CRITICAL Authorization Enforcement**: Warden hostel scope must be validated at the backend service/API authorization layer, rejecting any manipulated request or cross-hostel URL parameter with HTTP 403 Forbidden.

#### 3. Student Eligibility & Gender Invariants
* Only students in Class 9, 10, 11, or 12 can be admitted. Any request attempting to admit a Class $\le 8$ student must be rejected server-side (HTTP 422).
* Student gender matching: Male students can only be admitted to Boys Hostel; female students can only be admitted to Girls Hostel. Server-side validation must enforce gender integrity.

#### 4. Admission Integration vs. Independent Hostel Admission
* **Application Form Integration**: In the existing admission/application workflow, parents/applicants can indicate that hostel accommodation is required (`hostel_required = True`).
  * **Important**: Admission Cell does NOT allocate rooms or beds.
  * Workflow: Application submitted with hostel request $\to$ Student admitted/enrolled through regular admission pipeline $\to$ Hostel administration processes hostel admission and allocates hostel, room, and bed.
* **Independent Hostel Admission**: Enrolled day scholars (Class 9+) can apply/be admitted to hostel independently during the academic session.

#### 5. Hostel Admission & Allocation History Model
* A student may have multiple hostel stays during schooling.
* Historical allocations must be preserved in history; active admission/allocation must be clearly identified.
* Schema: `hostel_admissions` (student, hostel, admission_date, status, exit_date, exit_reason) and `bed_allocations` (admission_id, bed_id, allocated_at, vacated_at, is_active).

#### 6. Room / Bed Allocation & Transfers
* Warden allocates within their assigned hostel; Chief Provost allocates across all hostels.
* When transferring: End previous bed allocation (`vacated_at = NOW()`, `is_active = False`), create new bed allocation, preserve historical records, prevent overlapping active allocations.

#### 7. Hostel Exit Workflow
* **Chief Provost Exclusive**: Only Chief Provost can permanently exit a student from the hostel.
* Requires mandatory exit date and typed exit reason.
* Closes active hostel admission and bed allocation; student reverts to day scholar.
* Hostel fee applicability stops according to configured fee rules.

#### 8. Hostel Attendance (Residential Safety)
* Marked by the Warden for their assigned hostel at **8:00 PM every evening**.
* Statuses: `Present`, `Absent`, `On Leave`, `On Outing`.
* Approved leave/outing automatically pre-populates/reflects so wardens do not incorrectly mark them absent.
* Stores scheduled time (8:00 PM) and actual recording timestamp for audit accountability.
* Chief Provost can view attendance across all hostels; Warden only views their own hostel.

#### 9. Leave & Outing Workflow
* **Parent-Only Initiation**: Parents submit leave/outing requests via Parent App. Students **cannot** submit outing requests.
* **Warden Adjudication**: Warden reviews and approves or rejects the request with remarks and timestamp.
* **Explicit Student Return**: After student returns, Warden must explicitly record "Student Returned".
* **Overdue Indicator**: If expected return time has passed and student is not marked returned, surface a visual overdue indicator to Warden and Chief Provost.

#### 10. Parent App & Student App Integration
* **Parent App**: View child's hostel name, room, bed, admission status, notices, attendance records, leave/outing requests & statuses, return status, mess menu, and integrated hostel fee status.
* **Student App**: Read-only view of hostel name, room, bed, notices, mess menu, attendance records, and leave/outing status. Outing creation is hidden and blocked for students.

#### 11. Mess Management (Part of Hostel)
* **Single Fee**: Accommodation and mess are covered under one single hostel fee. There is **NO separate mess fee**, **NO mess attendance**, **NO cost-per-meal calculation**, and **NO separate Mess Manager role**.
* **Weekly Menu**: Chief Provost creates, edits, and publishes the weekly menu across Breakfast, Lunch, Snacks, and Dinner.
* Wardens, parents, and students can view the published menu.

#### 12. Hostel Fees & Billing Integration
* Single hostel fee encompassing accommodation and mess.
* Configured using existing fee architecture (`fee_heads`, `fee_plans`, `fee_plan_items`).
* When student is admitted to hostel, hostel fee schedule becomes applicable automatically.
* Existing fee invoicing engine bills the student; existing counter/online payment engine applies FIFO allocations.
* When hostel admission ends, fee applicability stops based on effective exit date.

#### 13. UI & Screens
* **Chief Provost**: Dashboard (total hostels, rooms, beds, occupancy, present/absent/leave counts, pending requests), Hostels list & detail, Floors, Rooms & Beds, Residents, Hostel Admissions, Allocation/Transfers, Attendance, Leave & Outing, Incidents, Complaints, Mess Menu, Notices, Reports, Wardens.
* **Warden**: My Hostel Dashboard (assigned hostel only), Residents, Rooms & Beds, Admissions, Allocation, Evening Attendance, Leave & Outing, Incidents, Complaints, Mess Menu, Notices, Reports.

#### 14. Demo Seed Data
* Exactly 2 demo hostels: Boys Hostel (10 beds, 10 residents, 1 Warden) and Girls Hostel (10 beds, 10 residents, 1 Warden).
* 1 Chief Provost user (`provost@sunrisepublic.edu` / `Admin@123`).
* 1 Boys Hostel Warden (`warden.boys@sunrisepublic.edu` / `Admin@123`).
* 1 Girls Hostel Warden (`warden.girls@sunrisepublic.edu` / `Admin@123`).
* 20 existing Class 9+ student records assigned as residents (10 male, 10 female).

#### 15. Testing & Verification Gates
* Multi-tenant isolation and Warden scoping tests (Warden cannot access another hostel or tenant).
* Class 9+ eligibility and gender matching validation tests.
* Bed capacity and double-booking constraint tests.
* Parent-only outing submission and Warden approval tests.
* Hostel fee integration and exit tests.
* E2E testing of Workflows A through G.
* Visual verification of all Chief Provost, Warden, Parent, and Student screens.
* Full test regression: `pytest -q`, `npm test`, `npx tsc -b`, `npx tsc --noEmit`.

---

## 4. Next Session Instructions for Successor Agent

1. **Mandatory Workflow Rule**: Present a comprehensive implementation plan to the user first. Obtain explicit approval before modifying code, adding migrations, or writing files.
2. **Review Ground-Truth First**: Read `SINGLE_SOURCE_OF_TRUTH.md`, `CLAUDE.md`, and `SESSION-HANDOFF-30.md`.
3. **Execution Sequence**:
   - Database models & Alembic migration for hostel entities.
   - RBAC permissions & role seeds for Chief Provost and Warden.
   - Services & FastAPI endpoints with strict hostel scoping and Class 9+ validation.
   - Fee module integration for automated hostel fee plan attachment.
   - Web UI screens for Chief Provost and Warden in `web/src/pages/hostel/`.
   - Mobile Parent App & Student App screens in `mobile/app/`.
   - Seed data creation (20 Class 9+ residents, 2 hostels, 3 staff accounts).
   - Automated tests (backend pytest, frontend vitest, TypeScript checks).
   - Visual verification using browser/CDP.
