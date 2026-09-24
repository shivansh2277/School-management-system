# SESSION-HANDOFF-12: Transport In-Charge Login, Authorized Pickup Persons with Photos & Separate Accounts Department

> **Session Completed:** Session 12  
> **Status:** ALL SESSION 12 DELIVERABLES COMPLETED & VERIFIED  
> **Branch:** `slice/office-feedback` (strictly local development; NEVER push to remote)  
> **Backend Test Baseline:** 741 passed, 1 skipped, 0 failed (`school-management-system/.venv/Scripts/python.exe -m pytest -q`)  
> **Web Test Baseline:** 91 passed, 2 skipped across 19 test files (`npm test` in `web/`)  
> **Web Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `web/`)  
> **Mobile Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `mobile/`)  
> **Migration Head:** `e5f6a7b8c9d0` (`backend/alembic/versions/e5f6a7b8c9d0_application_authorized_pickup_persons.py`)  
> **Visual Verification Suite:** 18/18 passed (`node verify_session12_visual.mjs` in `web/`)  
> **Corpus Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 1. COMPLETED DELIVERABLES IN SESSION 12

### 1. Transport In-Charge Dedicated Role & Isolated RBAC
- **Dedicated Role & Login:**
  - Login credentials: `transport@sunrisepublic.edu` / `Admin@123`.
  - Registered role `transport_incharge` in `backend/app/core/permissions.py` and `backend/seed.py`.
  - Permissions held:
    - `students.profile.read` (View student names and class rosters for route assignment)
    - `academics.class.read` (View section details for stop allocations)
    - `transport.setup.read` & `transport.setup.write` (Routes, stops, vehicles, paper expiry tracking)
    - `transport.assignment.read` & `transport.assignment.manage` (Student bus stop assignments)
    - `comms.notice.read` & `comms.message.send` (Transport broadcast alerts)
- **Strict RBAC Boundary Enforcement:**
  - Zero access to Admin settings (`/admin/settings`, `/admin/configuration` -> 403 Forbidden).
  - Zero access to Fees and Accounting (`/admin/fees/invoices`, `/admin/fees/defaulters` -> 403 Forbidden).
  - Zero access to Admissions processing (`/admin/admission/cycles`, `/admin/admission/applications` -> 403 Forbidden).
  - Zero access to HR/Payroll (`/admin/payroll/runs` -> 403 Forbidden).
  - Zero access to Academic grading (`/admin/grading-scales` -> 403 Forbidden).
  - Verified by `backend/tests/test_transport_incharge_rbac.py` and live visual verification.

### 2. Authorized Student Pickup Persons with Photos
- **Database Schema & Alembic Migration:**
  - Added `photo_url` (`String(500)`) to `ApplicationGuardian` model in `backend/app/models/application.py`.
  - Created `ApplicationAuthorizedPerson` model in `backend/app/models/application.py` and mapped table `application_authorized_persons` with columns: `id`, `school_id`, `application_id`, `name`, `relationship`, `phone`, `id_proof_type`, `id_proof_number`, `photo_url`, `notes`, `created_at`.
  - Created and applied Alembic migration `e5f6a7b8c9d0_application_authorized_pickup_persons.py`.
- **Public & Admin APIs:**
  - Added `POST /public/{school_code}/admission/upload` in `backend/app/api/public/admission.py` handling `.jpg`, `.jpeg`, `.png`, `.webp` $\le$ 5MB stored under `var/documents/{school_id}/admission/{uuid}.{ext}`.
  - Extended public admission application schema (`PublicApplication`) to accept `authorized_pickup_persons` array with photo URLs.
  - Extended `_detail()` in `backend/app/api/admin/applications.py` to return `authorized_pickup_persons`.
  - Added `PUT /admin/admission/applications/{id}/authorized-pickup-persons` to edit pickup persons during application review.
- **Conversion Carry-Forward:**
  - In `backend/app/services/conversion.py` (`_do_conversion`), all `ApplicationAuthorizedPerson` records and pickup-authorized guardians are automatically carried forward into permanent student records (`StudentAuthorizedPerson`) with their uploaded photos and ID proofs.
- **Front-Desk Reception Gate Pass Integration:**
  - Quick-select buttons in `StudentPassPage.tsx` display permanent escort photo thumbnails.
  - Form Section 3 displays "Verified Escort Photo Attached" thumbnail.
  - Printable slip (`PrintableStudentPass.tsx`) renders the escort's photo directly in Section 2 beside escort particulars.
- **Permanent Roster Invariant Decoupling:**
  - Issuing a one-time gate pass (`POST /admin/reception/passes`) with ad-hoc escort details writes to `student_passes` but NEVER alters `student_authorized_persons`. Verified in backend test suite.

### 3. Separate Accounts Department Dedicated Role & Financial Operations
- **Dedicated Role & Login:**
  - Login credentials: `accounts@sunrisepublic.edu` / `Admin@123`.
  - Registered role `accounts` in `backend/app/core/permissions.py` and `backend/seed.py`.
  - Permissions held:
    - `fees.setup.manage`, `fees.invoice.read`, `fees.invoice.generate`, `fees.payment.collect`, `fees.payment.void`, `fees.concession.approve`
    - `payroll.run.read`, `payroll.setup.manage`, `payroll.run.manage`, `hr.employee.read`, `hr.salary.read`
    - `reports.read` (Access to reports library and fee reports)
    - `students.profile.read`, `academics.class.read`, `comms.notice.read`, `comms.message.send`
- **Frontend & Navigation:**
  - Shell sidebar derives financial sections: "Financial / Money" (`/fees`, `/fees/ledger`, `/fees/defaulters`, `/fees/setup`, `/fees/periods`), "HR & Payroll" (`/payroll`), and "Analytics" (`/reports`).
  - Strict RBAC isolation from Admin settings, Admissions, Transport, and Grading.
  - Enabled `feature.hr=True` in `backend/seed.py` so payroll is active for the school by default.
  - Verified by `backend/tests/test_accounts_role_rbac.py` and live visual verification.

---

## 2. FILES, COMPONENTS & ROUTES MODIFIED IN SESSION 12

### Backend Files:
1. `backend/app/models/application.py`: Added `photo_url` to `ApplicationGuardian`, created `ApplicationAuthorizedPerson`.
2. `backend/app/models/__init__.py`: Exported `ApplicationAuthorizedPerson`.
3. `backend/alembic/versions/e5f6a7b8c9d0_application_authorized_pickup_persons.py`: Created and applied migration.
4. `backend/app/core/permissions.py`: Registered `"reports.read"`, added `transport_incharge` and `accounts` system roles.
5. `backend/app/api/public/admission.py`: Added multipart upload endpoint `POST /public/{school_code}/admission/upload`, added `PublicAuthorizedPickupPerson` and updated `PublicApplication`.
6. `backend/app/api/admin/applications.py`: Added `photo_url` to `GuardianInput`, added `PUT /applications/{id}/authorized-pickup-persons`, included pickup persons in `_detail()`.
7. `backend/app/services/conversion.py`: Carried forward `ApplicationAuthorizedPerson` rows to `StudentAuthorizedPerson` on conversion.
8. `backend/seed.py`: Added `transport@sunrisepublic.edu` and `accounts@sunrisepublic.edu`, enabled `feature.hr=True`.
9. `backend/tests/conftest.py`: Added `transport_incharge` and `accounts_user` fixtures.
10. `backend/tests/test_transport_incharge_rbac.py`: Unit test suite verifying allowed transport operations and 403 boundaries.
11. `backend/tests/test_accounts_role_rbac.py`: Unit test suite verifying financial operations and 403 boundaries.
12. `backend/tests/test_authorized_pickup_persons_lifecycle.py`: Unit test suite for upload, application, conversion, and gate pass decoupling.
13. `backend/tests/test_hr.py`: Updated `hr.salary.read` holders assertion to include `accounts`.

### Frontend Files:
1. `web/src/screens.ts`: Updated reports screen required permission to `reports.read`.
2. `web/src/pages/public/PublicApplyPage.tsx`: Added `PhotoUploadField`, dynamic "Authorized Student Pickup Persons" section with real file uploads, live previews, and API payload mapping.
3. `web/src/pages/reception/StudentPassPage.tsx`: Added `pickup_person_photo_url` to `passForm`, rendered escort photo in quick-select buttons, master roster modal, Section 3 preview, and print slip trigger.
4. `web/src/components/reception/PrintableStudentPass.tsx`: Rendered escort photo thumbnail directly in Section 2 beside escort particulars.
5. `web/verify_session12_visual.mjs`: Automated Puppeteer verification capturing live screenshot proofs.

---

## 3. TEST SUITES & VERIFICATION RESULTS

### Automated Test Runs
```bash
# Backend test suite (741 passed, 1 skipped)
cd backend && ../.venv/Scripts/python.exe -m pytest -q

# Web unit tests (91 passed across 19 files, 2 skipped)
cd web && npm test

# Web TypeScript compilation (0 errors)
cd web && npx tsc --noEmit

# Mobile TypeScript compilation (0 errors)
cd mobile && npx tsc --noEmit

# End-to-end visual verification (18/18 passed)
cd web && node verify_session12_visual.mjs
```

### Visual Verification Artifacts
- `proof_transport_incharge_portal.png`: Transport In-Charge logged-in view with isolated Transport & Logistics sidebar.
- `proof_accounts_role_portal.png`: Accounts Officer logged-in view showing Fees overview, financial sidebar, and payroll access.
- `proof_online_admission_pickup_persons.png`: Public admission portal (`/#/apply`) showing multiple authorized pickup persons with relationship badges, ID proofs, and verified photo uploads.
- `proof_student_pass_with_escort_photo.png`: Official Student Gate Pass A5 printable slip showing verified escort photo thumbnail beside escort particulars.

---

## 4. UPCOMING SCOPE & FOLLOW-UP WORK FOR SESSION 13: ROLE-SPECIFIC SIDEBAR & RBAC CHANGES

The following requirements have been defined for **Session 13**:

### 1. Admin Role Sidebar & Route Gating
* **Admission Module:**
  - Show **only** `Admission Dashboard` (`/admission`).
  - Hide and restrict:
    - Enquiries (`/admission/enquiries`)
    - Applications (`/admission/applications`)
    - Merit & Selection (`/admission/selection`)
    - Waitlist (`/admission/waitlist`)
    - Admission Reports (`/admission/reports`)
* **Money Module:**
  - Remove **Student Fees** (`/fees/ledger`) and **Defaulters** (`/fees/defaulters`) from Admin view.
  - Admin retains Fees Overview/Dashboard (`/fees`), Fee Setup (`/fees/setup`), and Period Close (`/fees/periods`).
* **Front Desk Module:**
  - Remove **Found & Lost** (`/reception/found-lost`), **Student Passes** (`/reception/passes`), and **Fee Counter** (`/reception/fee-counter`) from Admin view.
  - Admin retains Meeting Slips (`/reception/meetings`) and Important Directory (`/reception/directory`).
* **Enforcement Invariant:**
  - Changes apply to the **Admin role only**.
  - Direct URL access to hidden screens should be refused for Admin (via route protection / permission gating).
  - Do NOT delete the underlying features/routes/database functionality; other roles (Admission Officer, Receptionist, Accounts, Fee Counter) must continue using them.

### 2. Transport In-Charge Role Sidebar & Route Gating
* **Remove People Module:**
  - Completely remove the **People** module (`/students`, `/teachers`, `/staff`) from the Transport In-Charge sidebar.
* **Remove Academics Module:**
  - Completely remove the **Academics** module (`/classes`, `/subjects`, `/timetable`, etc.) from the Transport In-Charge sidebar.
* **Access Scope:**
  - The Transport In-Charge should have access **only** to modules/features relevant to transport responsibilities: Transport & Logistics (`/transport`) and Communication/Notices (`/notices`).
  - Underlying data needed for bus stop assignments (such as student names and class sections) should be accessed directly by transport components through service APIs without exposing standalone student management or academic class management screens.
* **Enforcement Invariant:**
  - Enforce through RBAC and route protection (`Can` / `ProtectedRoute` / backend permissions), not merely by hiding sidebar items.
  - Do not delete underlying People or Academics functionality for Admin, Teachers, or other roles.

---

## 5. REPOSITORY STATE
- **Branch:** `slice/office-feedback` (strictly local development; zero remote push)
- **Git Status:** All Session 12 changes cleanly verified.
