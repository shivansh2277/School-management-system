# SESSION 30 HANDOFF PROMPT — Sunrise School ERP

> **Instructions for User:** Copy and paste the prompt below into the chat when starting the next session.

---

```markdown
# MANDATORY WORKFLOW RULE — READ THIS FIRST BEFORE ANYTHING ELSE

IMPORTANT:
First generate a comprehensive, detailed implementation plan and present it to me.
When I review it and give approval, then only proceed with making changes or modifying code.
Do NOT start writing code, creating migrations, or modifying files until I have explicitly approved your implementation plan.

---

# Sunrise School ERP — Session 30: Complete Hostel + Mess Management Module

Read SINGLE_SOURCE_OF_TRUTH.md, CLAUDE.md, and SESSION-HANDOFF-30.md.
Work on the existing **Sunrise School ERP**. First inspect the current codebase, SSOT, existing RBAC implementation, student/admission/application workflow, fee module, parent/teacher/student mobile workflows, notification system, and existing UI patterns. Reuse existing entities, components, services, APIs, validation utilities, and design patterns wherever appropriate.

Do not create duplicate student, fee, notification, or authentication systems.

Implement the complete **Hostel + Mess Management module** according to the following specifications:

## 1. CORE BUSINESS MODEL
Hostel is an optional residential facility.
- Day scholars continue to work exactly as before.
- Hostel is available only to students in Class 9 and above.
- There will be multiple hostels under one school/tenant.
- For demo/seed data, create exactly:
  - Boys Hostel: 2 floors, 5 rooms total, 2 beds/students per room, 10 beds total, 10 demo residents
  - Girls Hostel: 2 floors, 5 rooms total, 2 beds/students per room, 10 beds total, 10 demo residents
- Room capacity must be configurable even though demo rooms have capacity 2.
- Beds must be explicit database entities, not just a room capacity number.
- UI must display both the room and individual beds with their assigned students (Hostel → Floor → Room → Bed → Student).
- Do not hard-code the demo structure into application logic.

## 2. RBAC
Add exactly two new hostel-related RBAC roles:
1. **Chief Provost**: School-wide hostel authority across all hostels in the tenant.
   - Permissions: Manage/view all hostels, floors, rooms, beds, residents; admit students, allocate/change/transfer rooms & beds, view allocation history, manage hostel exits; view attendance, leave/outing records, incidents, complaints, notices, mess menu, reports, wardens; configure hostel fee applicability according to existing Fee architecture.
2. **Warden**: Assigned to exactly one hostel.
   - Permissions restricted strictly to assigned hostel: view residents, rooms/beds; admit eligible students to assigned hostel, allocate/change room and bed within assigned hostel, view allocation history; mark hostel attendance; approve/reject leave/outing requests, record student return; manage complaints, incidents, notices; view menu and reports.
   - CRITICAL: Warden scope must be enforced at backend/database/API authorization level. A Warden assigned to Boys Hostel must never access Girls Hostel data.
   - Chief Provost has cross-hostel access. Do not create additional Hostel/Mess RBAC roles.

## 3. HOSTEL STRUCTURE & CONSTRAINTS
- School/Tenant → Hostels → Floors → Rooms → Beds.
- Beds must have identifier, room link, status, and current allocation.
- Prevent more active allocations than room capacity.
- Prevent two students occupying the same bed simultaneously.

## 4. STUDENT ELIGIBILITY & GENDER ENFORCEMENT
- Only students in Class 9 and above are eligible. Enforce in UI, backend/API validation, hostel admission workflow, and application integration. Server-side rejection for ineligible students.
- Hostel gender enforced: Male → Boys Hostel, Female → Girls Hostel.

## 5. APPLICATION FORM INTEGRATION
- Add hostel requirement/request section during admission application (`hostel_required = True`).
- Important: Admission Cell does NOT allocate room or bed.
- Workflow: Application (Hostel Required = Yes) → Regular Student Admission/Enrollment → Hostel Administration processes admission and allocates hostel, room, and bed.

## 6. INDEPENDENT HOSTEL ADMISSION
- Provide separate workflow for already-enrolled day scholars (Class 9+) to be admitted into hostel independently.

## 7. HOSTEL ADMISSION & ALLOCATION HISTORY RECORD
- Student hostel stays modeled with history: `hostel_admissions` and `bed_allocations`.
- Preserve historical allocations upon transfers. Active admission/allocation clearly identifiable.

## 8. ROOM/BED ALLOCATION & TRANSFERS
- Warden allocates within assigned hostel; Chief Provost allocates across all hostels.
- Transfers close previous allocation, open new allocation, preserve history, prevent overlapping active allocations.

## 9. HOSTEL EXIT
- Only Chief Provost can permanently remove/exit a student from hostel.
- Requires exit date and exit reason. Closes active admission/allocation; hostel fee stops according to configured rules.

## 10. HOSTEL ATTENDANCE
- Marked by Warden for assigned hostel at 8:00 PM every evening (Present, Absent, On Leave, On Outing).
- Approved leave/outing reflected automatically. Timestamped audit of actual recording time.
- Chief Provost views all hostels; Warden views only assigned hostel. No mess attendance.

## 11. LEAVE / OUTING WORKFLOW
- Parents submit leave/outing requests from Parent App. Students CANNOT submit outing requests.
- Warden approves/rejects with remarks and timestamp.
- After student returns, Warden explicitly records "Student Returned".
- Surface overdue indicator if expected return time passes without recorded return.

## 12. PARENT APP & STUDENT APP
- Parent App: View child's hostel, room, bed, status, notices, attendance, leave/outing requests & return status, mess menu, integrated hostel fee status.
- Student App: Read-only view of hostel, room, bed, notices, mess menu, attendance, leave/outing status. Outing requests blocked for students.

## 13. MESS MANAGEMENT
- Mess is part of Hostel. NO separate mess fee, NO mess attendance, NO cost-per-meal calculation, NO Mess Manager role.
- Chief Provost creates/edits/publishes weekly menu (Breakfast, Lunch, Snacks, Dinner). Wardens, parents, and students view published menu.

## 14. HOSTEL FEES
- Single fee covering accommodation and mess. Integrated into existing Fee module (`fee_plans`, `fee_invoices`).
- Automated applicability upon admission; stops upon exit. Standard payment and FIFO allocation logic applies.

## 15. DASHBOARDS & UI
- Chief Provost Dashboard (cross-hostel stats, room/bed occupancy, attendance, requests, complaints).
- Warden Dashboard (assigned hostel metrics only).
- Structured screens following Sunrise ERP UI patterns.

## 16. DEMO SEED DATA
- 2 hostels: Boys Hostel (10 beds, 10 residents, 1 Warden) and Girls Hostel (10 beds, 10 residents, 1 Warden).
- 1 Chief Provost (`provost@sunrisepublic.edu` / `Admin@123`).
- 1 Boys Hostel Warden (`warden.boys@sunrisepublic.edu` / `Admin@123`).
- 1 Girls Hostel Warden (`warden.girls@sunrisepublic.edu` / `Admin@123`).
- 20 existing Class 9+ student records assigned as residents (10 male, 10 female).

## 17. VERIFICATION & QUALITY GATES
- Full authorization & RBAC tests (Chief Provost cross-hostel, Warden isolated, gender and class 9+ enforcement, capacity limits).
- End-to-end tests for Workflows A through G.
- Visual browser verification of Chief Provost, Warden, Parent, and Student screens.
- Run complete test regression: `pytest -q`, `npm test`, `npx tsc -b`, `npx tsc --noEmit`.
```
