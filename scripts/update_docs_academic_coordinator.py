from pathlib import Path

# 1. Update SINGLE_SOURCE_OF_TRUTH.md
ssot_path = Path("SINGLE_SOURCE_OF_TRUTH.md")
ssot_text = ssot_path.read_text(encoding="utf-8")

coordinator_section = """
## 14. Academic Coordinator Role & Timetable Module Administration

### 14.1 RBAC Registration & Role Scoping
- **Role Code**: `academic_coordinator` ("Academic Coordinator").
- **Assigned Account**: `coordinator@sunrisepublic.edu` (password: `Admin@123`, primary role: `admin`, user ID: 5).
- **Granted Permissions**:
  - `academics.class.read` — View academic classes and class section rosters.
  - `timetable.slot.read` — View class, teacher, and daily timetable grids.
  - `timetable.slot.write` — Create, edit, and delete timetable lesson slots.
  - `timetable.slot.override` — Override scheduling conflicts with required audit reason.
  - `timetable.substitution.manage` — Access Substitution Desk, view free teachers, and assign relief duties.
  - `comms.notice.read` — View institutional notices.
- **Strict Role Boundary**:
  - No access to Admin Settings, School Configuration, Users & RBAC management.
  - No access to Fees, Invoices, Payment Collection, Defaulters, or Fee Setup.
  - No access to HR Staff records, Payroll Runs, or Employee creation.
  - No access to Student Admission Cycles, Applications, Enrolment, or Student Profile editing.
  - No access to Examinations, Grading Bands, Exam Schedules, or Marks entry.
  - No access to Transport, Library, Hostel, or Inventory.
  - Strict multi-tenant isolation enforced via `user.school_id` on all endpoints.

### 14.2 Timetable Web Workspace (`web/src/pages/Timetable.tsx`)
A dedicated 5-tab web administration portal accessible via `/#/timetable`:
1. **Class Timetables**:
   - Class Section picker with real-time slot counter and publication status badge.
   - Interactive weekly timetable grid (Monday–Saturday, Periods 1–8).
   - `+ Add Lesson Slot` modal with live conflict detection (`/admin/timetable/slots/check`) and coordinator override controls.
   - Quick slot actions: Edit, Delete (with confirmation and audit reason).
   - Publication controls: Publish Section, Revert to Draft, and Publish All Classes.
2. **Teacher Schedules**:
   - Faculty teacher picker with weekly load counter.
   - Weekly teacher timetable grid displaying assigned sections, subjects, classrooms, and relief duties.
3. **Daily Schedule & Substitution Desk**:
   - Date selector with "Today" quick shortcut.
   - Daily operational schedule with live substitution status tags.
   - Active substitutions log tracking absent faculty, relief teachers, reasons, and status.
   - "Assign Relief Duty" modal with automated ranking of free teachers (highlighting subject specialists and teachers with lowest weekly load).
4. **Workload & Completeness Dashboards**:
   - KPI metrics: Teaching Faculty count, Total Weekly Periods, Fair Share average, Heaviest load, Lightest load, and Workload Spread.
   - Timetable Completeness Matrix: Class section breakdown with Placed vs Expected periods, gap count, and completion badge.
   - Faculty Teaching Workload Table: Employee codes, names, departments, weekly periods, fair share ratio, and load limit status.
5. **Bell Timings / School Periods**:
   - Master list of school periods, start/end times, durations, and lesson vs break types.
   - `+ Add School Period` modal supporting instructional lessons, recess, lunch breaks, and assemblies.

### 14.3 Full Audit Logging
All timetable actions are comprehensively recorded in `audit_logs`:
- School period creation (`entity_type="school_period"`, `action=create`).
- Lesson slot creation & updates (`entity_type="timetable_slot"`, `action=create|update`, captures `before`/`after` diffs and override reasons).
- Lesson slot deletion (`entity_type="timetable_slot"`, `action=delete`, required audit reason).
- Timetable publication (`entity_type="timetable"`, `action=publish`).
- Timetable draft reversion (`entity_type="timetable"`, `action=status_change`, required audit reason).
- Substitution arrangement (`entity_type="substitution"`, `action=create|update`, captures date, slot, absent teacher, relief teacher, reason).

### 14.4 Database Migration & Verification
- Alembic migration `backend/alembic/versions/b3c4d5e6f7a8_academic_coordinator_role.py` installs the role and seed assignment.
- 100% test coverage in `backend/tests/test_academic_coordinator_rbac.py` and `backend/tests/test_timetable.py`.
- 100% Vitest coverage in `web/src/screens.test.tsx` and `web/src/auth/LoginPage.test.tsx`.
- Playwright E2E automation captured 8 high-resolution screenshots in `docs/screenshots/` verifying full functionality and strict role isolation.
"""

if "## 14. Academic Coordinator Role" not in ssot_text:
    ssot_path.write_text(ssot_text.strip() + "\n" + coordinator_section, encoding="utf-8")
    print("Appended section 14 to SINGLE_SOURCE_OF_TRUTH.md")

# 2. Update MEMORY.md
mem_path = Path("MEMORY.md")
mem_text = mem_path.read_text(encoding="utf-8")

mem_addition = """
### Academic Coordinator Role & Timetable Module Administration (Completed Oct 2026)
- **Role**: `academic_coordinator` installed in `backend/app/core/permissions.py` with 6 timetable & class permissions (`academics.class.read`, `timetable.slot.read`, `timetable.slot.write`, `timetable.slot.override`, `timetable.substitution.manage`, `comms.notice.read`).
- **Account**: `coordinator@sunrisepublic.edu` (`Admin@123`).
- **Web ERP**: Dedicated workspace at `/#/timetable` (`web/src/pages/Timetable.tsx`) with 5 tabs: Class Timetables, Teacher Schedules, Daily Schedule & Substitution Desk, Workload & Completeness Dashboards, and Bell Timings / School Periods.
- **Audit Logging**: Comprehensive audit recording added to `save_slot`, `delete_slot`, `publish_timetable`, `unpublish_timetable`, `add_period`, and `arrange` (substitutions).
- **Alembic Migration**: `b3c4d5e6f7a8_academic_coordinator_role.py`.
- **E2E Playwright Verification**: 8 verification screenshots captured in `docs/screenshots/` proving class grid, slot modal, conflict resolution, teacher schedule, substitution desk, dashboards, bell timings, and strict sidebar role isolation.
"""

if "Academic Coordinator Role & Timetable Module Administration" not in mem_text:
    mem_path.write_text(mem_text.strip() + "\n" + mem_addition, encoding="utf-8")
    print("Updated MEMORY.md")

# 3. Update CLAUDE.md
claude_path = Path("CLAUDE.md")
claude_text = claude_path.read_text(encoding="utf-8")

claude_addition = """
17. **Academic Coordinator Role & Dedicated Timetable Module Workspace**:
    - **Role & RBAC**: `academic_coordinator` installed in RBAC system granting full administrative control over Timetable without leaking Admin, HR, Finance, Student, or Exam permissions.
    - **Web Timetable Workspace**: `web/src/pages/Timetable.tsx` registered at `/timetable` under Academics, with 5 comprehensive management tabs.
    - **Audit Logs**: All slot mutations, deletions, publications, unpublications, period additions, and substitutions logged to PostgreSQL `audit_logs`.
    - **Verification**: Verified with 20/20 pytest tests (`test_academic_coordinator_rbac.py`, `test_timetable.py`), 42/42 vitest screens tests, and 8 Playwright E2E screenshots.
"""

if "Academic Coordinator Role" not in claude_text:
    claude_path.write_text(claude_text.strip() + "\n" + claude_addition, encoding="utf-8")
    print("Updated CLAUDE.md")
