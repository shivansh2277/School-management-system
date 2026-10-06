# SESSION-HANDOFF-29.md — Sunrise School ERP

**Date:** 06 October 2026  
**Status:** Session 29 Completed & Verified (Public Admission Enquiry Fix, View Admission Steps Scroll, Dedicated Librarian Role & Admission Document Overrides Queue).  
**Canonical Branch:** `slice/office-feedback`  

---

## 1. Summary of Completed Objectives

In this session, four core areas of Sunrise School ERP were upgraded and verified:

1. **Public Website — Admission Enquiry Form Fix:**
   - **Root Cause:** When submitting admission enquiries from the public landing pages or modal, the backend endpoint `/public/{school_code}/admission/enquiry` checked `School.code == school_code`. When called with tenant aliases (such as `sunrise` or `sunrisepublic` used in client bundles and links), the query returned `None`, triggering `404 Not Found: "No such school"`. Additionally, the frontend modal was attempting to post to an unhandled fallback or misaligned endpoint without clear submission feedback.
   - **Fix:** 
     - Updated `backend/app/api/public/admission.py` and `backend/app/api/public/announcements.py` with alias mapping (`sunrise`, `sunrisepublic`, `sunrise-public` -> canonical `SPS` tenant).
     - Standardized `AdmissionEnquiryModal.tsx` to submit to `/public/SPS/admission/enquiry` using `api.rawPost`.
     - Integrated a prominent green success confirmation state displaying reference guidance after enquiry submission.
     - Preserved multi-tenant isolation and verified enquiries persist directly into the ERP database (`enquiries` table) and appear in the Admission & Reception Enquiry workflows (`/admin/enquiries` and `/admin/reception/enquiries`).

2. **Public Website — "View Admission Steps" Routing:**
   - **Root Cause:** On `AdmissionsPage.tsx`, the "View Admission Steps" CTA was rendered as an anchor link `<a href="#process">`. Under React Router's `<HashRouter>`, browser navigation to `#process` modified the hash fragment, clobbering the router path and triggering the default fallback route to `/login`.
   - **Fix:** 
     - Replaced the anchor navigation with a smooth scrolling DOM button handler:
       ```tsx
       onClick={() => document.getElementById("process")?.scrollIntoView({ behavior: "smooth" })}
       ```
     - Visitors remain on the public Admissions page and smoothly glide to the 4-step admission guide (`#process`) without URL mutation or redirection to `/login`.

3. **Librarian RBAC & Library Module:**
   - **Role Definition:** Added a dedicated `librarian` role to `SYSTEM_ROLES` in `backend/app/core/permissions.py`:
     - Allowed permissions: `library.read`, `library.manage`, `comms.notice.read`.
     - Strictly excluded from: `admissions.*`, `fees.*`, `recruitment.*`, `transport.*`, `staff.*`, `attendance.*`, `finance.*`, `settings.*`, `academics.*`, `students.profile.read`.
   - **User Management Integration (`/user-access`):**
     - Enhanced `backend/app/api/admin/users.py` with `POST /admin/users/{user_id}/roles` and `DELETE /admin/users/{user_id}/roles/{role_code}` supporting multi-tenant role assignments, token version invalidation, and audit logging.
     - Updated `web/src/pages/UserAccessPage.tsx` with a dynamic "RBAC Roles" column and a "Manage Roles" dialog enabling admins to assign or revoke the Librarian role for any staff member.
     - Added quick demo credentials for Librarian on `web/src/auth/LoginPage.tsx` (`librarian@sunrisepublic.edu` / `Admin@123`).
     - Added backend authentication alias support in `backend/app/api/auth.py` so both `librarian@sunrisepublic.edu` and legacy `library@sunrisepublic.edu` authenticate seamlessly into the School Librarian account with identical tokens and permissions.

4. **Admission Document Overrides — Automatic Pending Queue:**
   - **Workflow Enhancement:** Replaced the previous manual lookup requirement on `/admin/admission-exceptions` (`AdmissionExceptions.tsx`) with an automatic pending queue.
   - **Data Model & Migration:**
     - Extended `ApplicationDocumentOverride` in `backend/app/models/application.py` with `status` (`pending`, `approved`, `rejected`), `rejection_reason`, and nullable `authorized_by_id` & `authorized_at`.
     - Created Alembic migration `backend/alembic/versions/f7a8b9c0d1e2_document_override_status_and_librarian_role.py`.
   - **Public Portal Integration:**
     - Added exception submission schema and endpoint `POST /public/{school_code}/admission/exception-request` in `backend/app/api/public/admission.py`.
     - Exception requests submitted during online admission draft creation automatically persist into `application_document_overrides` with `status = "pending"`.
   - **Review & Approval Engine:**
     - Added `POST /admin/document-overrides/{override_id}/approve` and `POST /admin/document-overrides/{override_id}/reject` endpoints in `backend/app/api/admin/applications.py`.
     - Updated `backend/app/services/applications.py`: only overrides with `status == "approved"` fulfill mandatory document checklists.
     - Upgraded `AdmissionExceptions.tsx` UI:
       - Displays a top "Pending Document Exception Queue" card listing Student Name, Application ID, Requested Document, Reason, Requested Date, Status, and Review / Approve / Reject action buttons.
       - Full Audit Trail table below displaying processed (`approved` / `rejected`) records with reviewer identity and timestamps.
       - Preserved collapsible manual lookup and ad-hoc override tools.

---

## 2. Quality Gate Verification Results

| Quality Gate | Tool / Command | Result |
|---|---|:---:|
| **1. Backend Pytest Suite** | `pytest -q` in `backend` | **807 passed, 1 skipped** (100% green) |
| **2. Web Vitest Suite** | `npm test -- --run` in `web` | **140 passed, 2 skipped across 26 test files** (100% green) |
| **3. Web TypeScript Check** | `npx tsc -b` in `web` | **0 errors, clean exit code 0** |
| **4. Mobile TypeScript Check** | `npx tsc --noEmit` in `mobile` | **0 errors, clean exit code 0** |

---

## 3. Files Modified and Added

### Backend
- `backend/app/api/public/admission.py`: Tenant alias mapping, public exception request endpoint, draft exception persistence.
- `backend/app/api/public/announcements.py`: Tenant alias mapping and `func` case-insensitive query support.
- `backend/app/core/permissions.py`: Dedicated `librarian` role definition.
- `backend/app/models/application.py`: `ApplicationDocumentOverride` status and rejection attributes.
- `backend/app/services/applications.py`: Strict `status == "approved"` check for document checklist satisfaction.
- `backend/app/schemas/user_access.py`: User roles serialization schema.
- `backend/app/api/admin/users.py`: Role assignment and revocation endpoints with audit logging.
- `backend/app/api/admin/applications.py`: Override approval/rejection endpoints, pending queue listing.
- `backend/alembic/versions/f7a8b9c0d1e2_document_override_status_and_librarian_role.py`: Migration for status and librarian role seed.
- `backend/tests/test_public_enquiry.py`: Unit tests for enquiry alias lookup, validation, and storage.
- `backend/tests/test_librarian_rbac.py`: Unit tests for librarian access allowance and cross-module restriction.
- `backend/tests/test_admission_documents_override.py`: Unit tests for pending queue lifecycle (`pending` -> `approved` / `rejected`).

### Frontend (Web)
- `web/src/api/client.ts`: Added `rawDel` helper for DELETE requests.
- `web/src/auth/LoginPage.tsx`: Added Librarian quick-fill button.
- `web/src/components/public/AdmissionEnquiryModal.tsx`: Fixed submission endpoint and added success confirmation banner.
- `web/src/components/public/AdmissionEnquiryModal.test.tsx`: Vitest for enquiry submission and modal behavior.
- `web/src/pages/public/website/AdmissionsPage.tsx`: Fixed "View Admission Steps" smooth scroll handler.
- `web/src/pages/UserAccessPage.tsx`: Added Roles column and Manage Roles modal dialog.
- `web/src/pages/admission/AdmissionExceptions.tsx`: Automatic Pending Queue UI, review modal, reject dialog with reason, and audit trail table.
- `web/src/pages/admission/AdmissionExceptions.test.tsx`: Vitest tests for automatic queue rendering and approval actions.
- `web/src/screens.test.tsx`: Added Librarian screen access and restriction assertions.
