# Sunrise School ERP — Session 27 Handoff Report

**Date:** 05 October 2026  
**Session Goal:** Implement ERP, Database, Mobile App Improvements and Comprehensive Admission/Transport Documentation.  
**Status:** 100% Completed & Verified across all 5 Phases.

---

## 1. Summary of Deliverables & Achievements

### Phase 1 — ERP Website Improvements
1. **Independent Scrolling and Navigation Reset (`web/src/layout/Shell.tsx`):**
   - Refactored Shell layout so that the navigation sidebar (`aside`) and the main content area (`<main>`) scroll completely independently.
   - Fixed header bar with continuous visual hierarchy.
   - Added automatic scroll-to-top on route changes (`pathname` dependency) and explicit navigation clicks using safe JSDOM-compatible `scrollTo` / `scrollTop = 0` checks.
   - Verified across desktop, tablet, and mobile breakpoints without nested-scroll usability issues.
2. **Dynamic Dashboard Attendance (`backend/app/services/stats.py` & `web/src/pages/Dashboard.tsx`):**
   - Removed all hardcoded fallbacks and old Friday metrics on Sundays/holidays.
   - Proper evaluation of `is_sunday` (`today.weekday() == 6`) and declared calendar holidays via `is_holiday_for()`.
   - On non-school days, returns strictly `{present: 0, absent: 0, leave: 0, percent: None, is_school_day: False, non_school_reason: "Sunday" | "Holiday: ..."}`.
   - On instructional days, calculates live figures from database records; if roll call is pending, explicitly displays "Attendance not marked today".
   - Zero fabricated metrics; completely preserves tenant isolation and calendar configuration.
3. **Sign-in Page UI Redesign (`web/src/auth/LoginPage.tsx`):**
   - Modernized school-administration aesthetic with deep navy banner (`#042954`), gold sunburst logo, and warm cream/sandstone card surfaces.
   - Clean input groups with icons for email and password.
   - Accessible password-visibility toggle button (`showPassword`).
   - Quick demo credentials selector for 1-click testing (Admin, Accounts, Admission, Receptionist, Transport).
   - Preserved all authentication logic, session handling, error banners, online admission link (`/apply`), and return-to-website link.

### Phase 2 — Database and Seed Data Expansion
4. **Academic Classes Expansion (19 Groups):**
   - Expanded class groups from 10 to 19:
     - **Pre-primary:** Nursery-A, LKG-A, UKG-A.
     - **Primary & Middle:** Classes 1 through 10.
     - **Senior Secondary (CBSE Streams):**
       - Class 11: 11-Sci (Science), 11-Com (Commerce), 11-Hum (Humanities).
       - Class 12: 12-Sci (Science), 12-Com (Commerce), 12-Hum (Humanities).
   - Updated `class_sort_key` in `backend/app/services/common.py` to rank Nursery &rarr; LKG &rarr; UKG &rarr; 1..12.
   - Enhanced `_target_section` in `backend/app/services/promotion.py` to smoothly promote students through Pre-primary, Class 10 &rarr; 11 streams, and 11 &rarr; 12.
5. **Idempotent Seed Expansion Script (`scripts/expand_classes_and_seed.py`):**
   - Added 12 new qualified teachers (`TCH013` to `TCH024`) with statutory payroll structures and leave allocations.
   - Seeded 9 new subjects: Physics, Chemistry, Biology, Accountancy, Business Studies, Economics, History, Political Science, Geography.
   - Populated 90 new demo students and enrolments (10 students per section) with complete guardian accounts.
   - Created 270 conflict-free timetable slots balancing teacher workloads (10–30 periods/week per teacher).
   - Created standard fee plans for Nursery, LKG, UKG, 11, and 12 (Tuition 80%, Development 20%, Transport optional).
   - Script is 100% idempotent: running repeatedly leaves the database clean without duplicate records or primary key conflicts.
6. **Attendance Records Clean-up:**
   - Deleted all 5,800 historical student attendance records dated prior to 1 October 2026.
   - Preserved all records from 1 October 2026 onward.
   - Seeded 570 demo attendance records across all 190 active students for Thursday Oct 1, Friday Oct 2, and Saturday Oct 3, 2026.
   - Sunday Oct 4, 2026 left strictly unmarked/closed (0 present/absent).
   - Zero cascading deletions or foreign key anomalies.

### Phase 3 — Mobile App Improvements
7. **Same-Day Attendance Deadline & Automated Admin Alert:**
   - Enforced same-day deadline of 11:59 PM in school timezone in `backend/app/services/attendance.py`.
   - Implemented `check_unmarked_attendance_and_notify_admin()`: automatically creates an admin ERP `Notice` and `InAppNotification` identifying the class section, assigned teacher, date, and missing status when unmarked on instructional days.
   - Excludes Sundays and declared holidays; strictly idempotent against duplicate alerts.
   - Added late submission audit trail (`attendance_late_marking`) in `mark()`.
   - Exposed endpoint `POST /admin/attendance/deadline-sweep` and registered recurring scheduler job handler `@handler("attendance.unmarked_deadline_sweep")` in `backend/app/jobs.py` and `backend/app/services/jobs.py`.
8. **Teacher Mobile Homework Date Picker (`mobile/app/(teacher)/homework.tsx`):**
   - Integrated interactive calendar date picker modal triggered by an accessible calendar icon button next to the due date input.
   - Month-by-month calendar navigation with `<` and `>` controls and day selection grid.
   - Quick-select interval chips for "Today", "Tomorrow", "In 3 Days", and "In 1 Week".
   - Timezone-safe local date formatting (`YYYY-MM-DD`).
   - Retained manual text input option.
   - Validates that new homework assignments cannot have a due date set in the past, while allowing past dates when reviewing or editing existing assignments.

### Phase 4 — Documentation PDF
9. **Publication-Quality Documentation Manual (`docs/Sunrise-ERP-Admission-and-Transport-Documentation.pdf`):**
   - Generated 8-page publication-grade PDF via Headless Chrome printing (`scripts/gen_admission_transport_doc_pdf.py`).
   - **Chapter A:** End-to-end admission lifecycle, walk-in inquiries, 10-tab digital dossier, reference profiles (Aarav Sharma & Ananya Verma), APAAR ID consent tracking, PEN (UDISE+), medical/allergy profiles, sibling concession engine, document verification audit overrides, age eligibility cutoffs matrix, and atomic fee-to-enrollment trigger.
   - **Chapter B:** Transport operations lifecycle, Transport In-charge role, fleet health & 30-day statutory expiry warnings, address-first stop allocation, GPS & CCTV safety protocols, distance-based fee slabs (Slabs A–D), passenger manifests, and bus pass issuance.
   - **Chapter C:** Granular RBAC Role and Permission Matrix, ASCII/relational Entity Relationship Diagrams (ERDs), diagnostic troubleshooting guide for common operational scenarios, and automated verification appendix.

### Phase 5 — Full Test Suite Verification
- **Backend Tests:** 800 passed, 1 skipped, 0 failed in `backend/` pytest.
- **Web Tests:** 135 passed, 2 skipped across 25 test files in `web/` vitest.
- **Web Typecheck:** 0 errors (`npx tsc -b`).
- **Mobile Typecheck:** 0 errors (`npx tsc --noEmit`).

---

## 2. Key File Modifications

| File Path | Description of Changes |
|---|---|
| `web/src/layout/Shell.tsx` | Independent scrolling for sidebar & main content with scroll-to-top on navigation |
| `web/src/auth/LoginPage.tsx` | Modern school-administration login UI with password visibility toggle & demo credentials |
| `backend/app/services/stats.py` | Dynamic dashboard attendance calculations; 0 on Sundays/holidays; optional `on_date` |
| `backend/app/services/common.py` | Updated `class_sort_key` to rank Nursery &rarr; LKG &rarr; UKG &rarr; 1..12 |
| `backend/app/services/promotion.py` | Updated `_target_section` to support Pre-primary and Senior Secondary streams |
| `backend/app/services/attendance.py` | Added same-day 11:59 PM deadline sweep, admin notices/notifications, and late marking audit trail |
| `backend/app/api/admin/attendance.py` | Exposed `POST /admin/attendance/deadline-sweep` |
| `backend/app/jobs.py` & `jobs.py` | Registered `attendance.unmarked_deadline_sweep` scheduler handler |
| `backend/tests/test_attendance.py` | Added automated tests for deadline sweep, Sunday exclusion, and idempotency |
| `backend/tests/test_class_listing.py` | Added assertions for Nursery, LKG, UKG class ordering |
| `mobile/app/(teacher)/homework.tsx` | Added interactive calendar date picker modal, quick chips, and past-date validation |
| `scripts/expand_classes_and_seed.py` | Standalone idempotent seed expansion script for 19 classes, 90 students, 12 teachers, 270 slots, fees, and attendance cleanup |
| `scripts/gen_admission_transport_doc_pdf.py` | PDF generator for comprehensive 8-page Admission & Transport documentation |
| `docs/Sunrise-ERP-Admission-and-Transport-Documentation.pdf` | Generated 8-page publication-quality documentation PDF |
| `SINGLE_SOURCE_OF_TRUTH.md` & `MEMORY.md` | Updated with Session 27 deliverables and certified technical status |
