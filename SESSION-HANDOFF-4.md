# Session Handoff 4 — Dedicated Receptionist Role & Admission Module Isolation

**Date:** 14 September 2026  
**Canonical Reference:** [`SINGLE_SOURCE_OF_TRUTH.md`](SINGLE_SOURCE_OF_TRUTH.md)  
**Branch:** `slice/office-feedback` (strictly local per owner directive)  
**Status:** Ready for execution in the next session

---

## 1. Current Verified System State (Session 3 Baseline)

All work from the previous session has been built, tested, verified, and documented:

| Component | Status | Metrics / Evidence |
|---|---|---|
| **Backend API** | 100% Green | 641 passed, 2 skipped (`pytest -q`) on `http://127.0.0.1:8078` |
| **Frontend Web ERP** | 100% Green | 23 screens declared in `screens.ts`, TypeScript 0 errors, 66 Vitest passed |
| **Mobile App (Expo)** | 100% Green | React Native TypeScript 0 errors, Teacher Stock & Grievances live |
| **Database (PostgreSQL)** | 100% Green | 89 tables total, 61 active populated tables in `sunrise_test` |
| **Live Browser Verification**| 100% Green | All 22 operational feature workflows verified via headless Chrome CDP |
| **Documentation Deliverables**| Up to Date | All 5 executive PDFs compiled and verified in `docs/`: |
| | | 1. `docs/Sunrise-ERP-Database-Essentials-Explained.pdf` (1.28 MB) |
| | | 2. `docs/Sunrise-ERP-Database-Viva-100.pdf` (2.19 MB) |
| | | 3. `docs/Sunrise-ERP-Features-Operational-and-Planned.pdf` (674 KB) |
| | | 4. `docs/Sunrise-ERP-Database-Essentials.pdf` (1.08 MB) |
| | | 5. `docs/Sunrise-ERP-Database.pdf` (1.85 MB) |

---

## 2. Objective for the Next Session

### The Feature Request: Dedicated Receptionist Role & Admission Isolation
The school owner wants to introduce a dedicated **Receptionist login and role** in Sunrise ERP:

1. **Receptionist Access**:
   - The Receptionist must **only** have access to the **Admission Management** module, specifically these 5 sections:
     1. **Enquiries** (`/admission/enquiries`)
     2. **Applications** (`/admission/applications`)
     3. **Merit & Selection** (`/admission/merit`)
     4. **Waitlist** (`/admission/waitlist`)
     5. **Admission Reports** (`/admission/reports`)
   - The receptionist should be able to view and use these sections according to the existing functionality of the website.

2. **Sidebar Visibility for Receptionist**:
   - The sidebar must show **ONLY** the 5 admission sections listed above.
   - **All other modules and sections must be completely hidden** (Dashboard, Students, Staff, Classes, Attendance, Fees, Transport, Stock, Configuration, Settings, Reports Library, etc.).

3. **Other Logins (Admin, Principal, Coordinator, Owner, Accountant, etc.)**:
   - **Remove the five admission sections completely from their sidebar.** These sections become exclusive to the Receptionist role.
   - The existing functionality of all other roles must remain unchanged.
   - Do not remove or break admission data, backend APIs, database tables, or existing functionality.

4. **Binding Implementation Requirements**:
   - Implement this as **proper Role-Based Access Control (RBAC)**, not just CSS/menu hiding.
   - Ensure a receptionist cannot access restricted modules by manually typing URLs (enforced by `RequirePermission` and backend route gates).
   - Ensure Admin/Principal cannot access admission endpoints if restricted.
   - Ensure existing users and logins continue working.
   - Reuse existing admission pages and backend functionality (zero code duplication).
   - Follow current website design and sidebar styling.
   - Verify that the correct sections appear for each role after implementation.

---

## 3. Architectural Inspection & Impact Analysis

### 3.1 Backend Role & Permission Architecture
Located in `backend/app/core/permissions.py`:
- `PERMISSIONS`: Defines the granular permission codes:
  - `admission.enquiry.read`, `admission.enquiry.write`
  - `admission.application.read`, `admission.application.write`
  - `admission.cycle.read`, `admission.cycle.write`
  - `admission.document.verify`, `admission.assessment.enter`, `admission.interview.enter`
  - `admission.decision.make`, `admission.decision.override`, `admission.application.convert`, `admission.medical.read`
- `READ_ONLY` list: Automatically builds a "can read everything" set by finding all permissions ending in `.read`.
  - Currently, `NOT_BLANKET_READ` excludes `hr.salary.read` and `payroll.run.read`.
  - **Key Decision:** Adding `admission.enquiry.read`, `admission.application.read`, and `admission.cycle.read` to `NOT_BLANKET_READ` prevents `READ_ONLY` from automatically leaking admission access to `principal`, `admin_officer`, and other staff roles!
- `SYSTEM_ROLES`:
  - A new system role `("receptionist", "Receptionist", [...])` will be defined containing all `admission.*` permissions, and **no other permissions** (no `students.profile.read`, no `fees.invoice.read`, no `admin.settings.read`).
  - Strip `admission.*` permissions from `principal`, `admin_officer`, and ensure `admin@sunrisepublic.edu` does not hold admission scopes.

### 3.2 Seeding & Authentication
Located in `backend/seed.py`:
- Seed a dedicated user account:
  - **Login ID / Email:** `receptionist@sunrisepublic.edu`
  - **Password:** `Admin@123` (matching the leadership demo password standard)
  - **Full Name:** "Front Desk Receptionist"
  - **Role:** `UserRole.admin` (Web ERP user) with system role `receptionist` assigned in `_assign_roles()`.
- Record credentials in `PASSWORDS.md`.

### 3.3 Frontend Screen Registry & Routing
Located in `web/src/screens.ts`:
- Current admission screen entries:
  - `/admission/enquiries`: gated on `["admission.enquiry.read"]`
  - `/admission/applications`: gated on `["admission.application.read"]`
  - `/admission/merit`: gated on `["admission.application.read"]`
  - `/admission/waitlist`: gated on `["admission.application.read"]`
  - `/admission/reports`: gated on `["admission.application.read"]`
  - `/admission` (Overview): currently gated on `["admission.application.read", "admission.cycle.read"]`.
    - *Decision:* Gate `/admission` to `receptionist` or redirect `/admission` to `/admission/enquiries`.
- `visibleScreens(can, hasModule)`:
  - Automatically filters `SCREENS` based on `can(permission)`.
  - Since Receptionist holds *only* `admission.*` permissions, `visibleScreens` will return **only** the admission screens.
  - Since Admin/Principal will *lack* `admission.*` permissions, `visibleScreens` will omit all admission screens from their sidebar!
- `Home()` route (`web/src/App.tsx`):
  - When the Receptionist logs in, `Home()` calls `visibleScreens(can, hasModule)[0]`.
  - The first visible screen will be `/admission/enquiries`, so the Receptionist automatically lands directly on the Enquiries screen!
- `RequirePermission` (`web/src/auth/RequirePermission.tsx`):
  - If the Receptionist types `/#/students` or `/#/fees`, `RequirePermission` checks `can("students.profile.read")`, finds it false, and renders a clean "Permission denied" panel.

---

## 4. Step-by-Step Implementation Plan for Next Session

### Phase 1: Backend Role & Permission Segregation
1. **Modify `backend/app/core/permissions.py`**:
   - Add admission read permissions to `NOT_BLANKET_READ`:
     ```python
     NOT_BLANKET_READ = {
         "hr.salary.read",
         "payroll.run.read",
         "admission.enquiry.read",
         "admission.application.read",
         "admission.cycle.read",
     }
     ```
   - Define the `receptionist` role in `SYSTEM_ROLES`:
     ```python
     (
         "receptionist",
         "Receptionist",
         [
             "admission.cycle.read",
             "admission.cycle.write",
             "admission.enquiry.read",
             "admission.enquiry.write",
             "admission.application.read",
             "admission.application.write",
             "admission.document.verify",
             "admission.assessment.enter",
             "admission.interview.enter",
             "admission.decision.make",
             "admission.decision.override",
             "admission.application.convert",
             "admission.medical.read",
         ],
     )
     ```
   - Remove all `admission.*` permissions from `principal` and `admin_officer`.
   - Update `super_admin` or define an explicit role assignment in `seed.py` so `admin@sunrisepublic.edu` does not hold admission permissions.

2. **Update `backend/seed.py`**:
   - Create `receptionist = User(login_id="receptionist@sunrisepublic.edu", email="receptionist@sunrisepublic.edu", full_name="Front Desk Receptionist", ...)`
   - In `_assign_roles()`:
     Assign `roles["receptionist"]` to `receptionist@sunrisepublic.edu`.
   - Ensure other accounts do not receive the `receptionist` role.

3. **Update `PASSWORDS.md`**:
   - Add `receptionist@sunrisepublic.edu` (`Admin@123`) under Web dashboard logins.

### Phase 2: Frontend Screen & Navigation Validation
1. **Inspect `web/src/screens.ts`**:
   - Verify the 5 admission screens require `admission.enquiry.read` and `admission.application.read`.
   - Update `/admission` (Admission Overview) permissions or group label if needed to ensure the Receptionist sees exactly the 5 intended sections.
2. **Verify `web/src/layout/Shell.tsx`**:
   - Confirm that empty groups (e.g. `Admission` group when user has no admission permissions) automatically omit their section header.
3. **Run TypeScript Check & Unit Tests**:
   - `cd web && npx tsc --noEmit`
   - `cd web && npm test`
   - `cd backend && pytest`

### Phase 3: Automated Browser Verification
Create or run a headless Chrome test (`web/test_receptionist_role.mjs`) to verify:
1. **Receptionist Session (`receptionist@sunrisepublic.edu`)**:
   - Logs in successfully.
   - Lands on `/admission/enquiries`.
   - Sidebar contains **ONLY**: Enquiries, Applications, Merit & selection, Waitlist, Admission reports.
   - Sidebar contains **NO**: Dashboard, Students, Staff, Classes, Attendance, Fees, Transport, Stock, Configuration, Settings, Reports.
   - Navigates manually to `/#/students`, `/#/fees`, `/#/dashboard`: all render "Permission denied" or redirect.
   - Can interact with Enquiries and Applications successfully.
2. **Admin Session (`admin@sunrisepublic.edu`)**:
   - Logs in successfully.
   - Lands on `/dashboard`.
   - Sidebar contains: Dashboard, Students, Staff, Classes, Attendance, Exams, Fees, Transport, Stock, Configuration, Settings, Reports.
   - Sidebar contains **ZERO** admission links (Enquiries, Applications, Merit, Waitlist, Admission Reports are gone).
   - Navigates manually to `/#/admission/enquiries`: renders "Permission denied" or 403.

---

## 5. Quick Command Reference

```powershell
# 1. Start Backend API
cd C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8078

# 2. Start Frontend Web
cd C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\web
npm run dev -- --host 0.0.0.0 --port 5173

# 3. Run Backend Suite
cd C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\backend
..\.venv\Scripts\python.exe -m pytest -q

# 4. Run Web Verification
cd C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system\web
npx tsc --noEmit
npm test -- --run
```
