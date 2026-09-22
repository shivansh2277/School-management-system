# Session Handoff 6 — Schema Refactoring (enrolment_id) & Mobile Operational Depth

**Date:** 18 September 2026  
**Canonical Reference:** [`SINGLE_SOURCE_OF_TRUTH.md`](SINGLE_SOURCE_OF_TRUTH.md)  
**Branch:** `slice/office-feedback` (strictly local development)  
**Database:** PostgreSQL `sunrise_test` on `localhost:5432` (93 Tables, 68 Live Populated Tables, 25 Scaffolded Tables)  
**Active Alembic Migration Head:** `a1b2c3d4e5f6` (`teacher_leave_and_recruitment.py`)  
**Status:** Ready for execution in Session 6  

---

## 1. Verified Technical Baseline (Session 5 Wrap-Up)

All existing features, web screens, documentation PDFs, and test suites are 100% green:

| Component | Status | Verified Metrics & Technical Evidence |
|---|:---:|---|
| **Backend API (FastAPI)** | **100% Green** | Port 8000 active, all routers loaded, `/docs` responding with 200 OK. |
| **Frontend Web Console (React/Vite)** | **100% Green** | 27 live operational screens on `http://localhost:5173`, RBAC permission gates active. |
| **Mobile App (Expo SDK 57)** | **100% Green** | React 19.2.3, React Native 0.86.3, Expo SDK 57, TypeScript 0 errors, doctor 21/21 passed. |
| **Database (PostgreSQL)** | **100% Green** | 93 tables, 68 populated tables, 25 reserved scaffolded tables, 1,097 columns, 250 foreign keys. |
| **Documentation PDFs** | **Up to Date** | All 6 canonical PDFs in `docs/` synchronized against live database schema (`verify_db_docs.py` 17/17 passed):<br>1. `Sunrise-ERP-Operational-Data-Flows.pdf` (1.31 MB, Table-to-Table Guide)<br>2. `Sunrise-ERP-Database.pdf` (1.92 MB, 93-table introspected schema)<br>3. `Sunrise-ERP-Database-Tables-and-Features.pdf` (7.76 MB, Feature mapping)<br>4. `Sunrise-ERP-Database-Essentials.pdf` (1.21 MB, 68 live tables & ERDs)<br>5. `Sunrise-ERP-Database-Essentials-Explained.pdf` (1.78 MB, 16 business processes)<br>6. `Sunrise-ERP-Features-Operational-and-Planned.pdf` (723 KB, 27 screens inventory) |

---

## 2. Session 6 Objective & Master Scope

Session 6 executes two major engineering milestones:
1. **Schema Refactoring**: Transition `marks`, `homework_submissions`, and `grievances` from lifetime `student_id` to annual `enrolment_id` to uphold Sunrise ERP's fundamental invariant: *"Year-scoped facts hang off `enrolment_id`; lifetime facts hang off `student_id`"*.
2. **Mobile App Operational Depth**: Build out the end-to-end operational workflows for the **Teacher**, **Parent**, and **Student** mobile apps.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SESSION 6 ROADMAP                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Phase 1: Database Migration & Model Refactor                             │
│    Migrate marks, homework_submissions, and grievances to enrolment_id     │
│                                                                             │
│ 2. Phase 2: Teacher Mobile App Depth (mobile/app/(teacher))                 │
│    • Mobile Classroom Roll Marking (attendance.tsx)                         │
│    • Homework Manager & Submissions Review (homework.tsx)                   │
│    • Mobile Test Marks Entry Keypad (results.tsx / marks.tsx)               │
│                                                                             │
│ 3. Phase 3: Parent Mobile App Depth (mobile/app/(parent))                   │
│    • Monthly Attendance Calendar & Medical Leave (attendance.tsx)           │
│    • Fee Receipts & Online Ledger (fees.tsx)                                │
│    • Official CBSE Report Card Download (results.tsx)                       │
│    • School Broadcast Push Alerts (notices.tsx)                             │
│                                                                             │
│ 4. Phase 4: Student Mobile App Depth (mobile/app/(student))                 │
│    • Timetable & Homework Digital Turn-in (timetable.tsx, homework.tsx)     │
│    • Academic Marks & Performance Viewer (results.tsx)                      │
│                                                                             │
│ 5. Phase 5: Verification, Testing & Documentation Refresh                   │
│    Run pytest, verify mobile screens, capture visual proofs, update docs.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase 1: Schema Refactoring — `enrolment_id` Migration

### Architectural Rationale
In Sunrise ERP:
- `students` represents the person for life (`admission_no`, birth date, legal name).
- `enrolments` represents the student's membership in a specific class and section for one academic year (`class_section_id`, `roll_no`, `academic_year_id`).
- When a student completes homework in Class 5, that homework belongs to Class 5.
- When a student takes an exam in Class 5, those marks belong to Class 5.
- When a parent files a grievance regarding a classroom or teacher issue, it relates to the student's active enrollment in that class.

Currently, `marks`, `homework_submissions`, and `grievances` reference `student_id`. This phase refactors them to point to `enrolment_id` (with foreign key constraint to `enrolments.id`).

### Detailed Migration Plan

#### 1. Alembic Migration Script
Create Alembic revision `b2c3d4e5f6a7_enrolment_id_refactor.py` (down-revision `a1b2c3d4e5f6`):
1. **Table `marks`**:
   - Add column `enrolment_id` (BigInteger, nullable initially).
   - Data migration backfill query:
     ```sql
     UPDATE marks m
     SET enrolment_id = e.id
     FROM enrolments e
     JOIN exams ex ON ex.id = m.exam_id
     WHERE e.student_id = m.student_id
       AND e.academic_year_id = ex.academic_year_id;
     ```
   - Alter `enrolment_id` to `nullable=False`.
   - Add foreign key: `FOREIGN KEY (enrolment_id) REFERENCES enrolments(id) ON DELETE RESTRICT`.
   - Update unique constraint from `(exam_id, subject_id, student_id)` to `(exam_id, subject_id, enrolment_id)`.
   - Drop old `student_id` column (or keep as nullable legacy mirror if backward compatibility is required; preferred: clean removal).

2. **Table `homework_submissions`**:
   - Add column `enrolment_id` (BigInteger, nullable initially).
   - Data migration backfill query:
     ```sql
     UPDATE homework_submissions hs
     SET enrolment_id = e.id
     FROM enrolments e
     JOIN homework h ON h.id = hs.homework_id
     WHERE e.student_id = hs.student_id
       AND e.class_section_id = h.class_section_id;
     ```
   - Alter `enrolment_id` to `nullable=False`.
   - Add foreign key: `FOREIGN KEY (enrolment_id) REFERENCES enrolments(id) ON DELETE CASCADE`.
   - Update unique constraint to `(homework_id, enrolment_id)`.
   - Drop old `student_id` column.

3. **Table `grievances`**:
   - Add column `enrolment_id` (BigInteger, nullable=True since grievances can be general/staff without a student).
   - Data migration backfill query:
     ```sql
     UPDATE grievances g
     SET enrolment_id = e.id
     FROM enrolments e
     WHERE e.student_id = g.student_id
       AND e.status = 'active';
     ```
   - Add foreign key: `FOREIGN KEY (enrolment_id) REFERENCES enrolments(id) ON DELETE SET NULL`.
   - Retain or deprecate `student_id` column.

#### 2. Model Updates in Backend
1. `backend/app/models/assessment.py`:
   - Update `Mark` model:
     ```python
     enrolment_id: Mapped[int] = mapped_column(
         BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
     )
     enrolment = relationship("Enrolment", lazy="joined")
     ```
2. `backend/app/models/ops.py`:
   - Update `HomeworkSubmission` model:
     ```python
     enrolment_id: Mapped[int] = mapped_column(
         BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
     )
     enrolment = relationship("Enrolment", lazy="joined")
     ```
3. `backend/app/models/grievance.py`:
   - Update `Grievance` model:
     ```python
     enrolment_id: Mapped[int | None] = mapped_column(
         BigInteger, ForeignKey("enrolments.id"), nullable=True, index=True
     )
     enrolment = relationship("Enrolment", lazy="joined")
     ```

#### 3. API Handlers & Schemas to Update
- `backend/app/api/admin/exams.py`: Marks batch entry endpoints (`/admin/exams/{id}/marks`).
- `backend/app/api/teacher/marks.py`: Teacher marks submission route.
- `backend/app/api/teacher/homework.py`: Teacher homework creation and submissions evaluation.
- `backend/app/api/student/academics.py` & `dashboard.py`: Student homework and report card view.
- `backend/app/api/admin/grievances.py` & `parent/grievances.py`.
- `backend/seed.py`: Update mark and homework submission seeding to bind to `enrolments.id`.

---

## 4. Phase 2: Teacher Mobile App Operational Depth

Target Directory: `mobile/app/(teacher)/`

### A. Mobile Classroom Roll Marking (`attendance.tsx`)
- **Real-Life Action:** Class teacher marks morning attendance inside the classroom on their smartphone.
- **Components & Interactions**:
  1. Class & Date selector (fetches teacher's class sections via `GET /teacher/classes`).
  2. Attendance roster view (pulls active students for that section with roll numbers).
  3. Interactive status toggles per student: **P** (Present, green), **A** (Absent, red), **L** (Late, amber), **M** (Medical Leave, blue).
  4. One-tap **"Mark All Present"** button for fast morning completion.
  5. Live counter header showing: *Total: 40 | Present: 36 | Absent: 4*.
  6. **"Submit Register"** button invoking `POST /teacher/attendance` with batch payload.
  7. Success toast notification and read-only lock once submitted.

### B. Homework Manager (`homework.tsx`)
- **Real-Life Action:** Teacher assigns daily homework with attachments and grades submitted pupil assignments.
- **Components & Interactions**:
  1. **Active Assignments Tab**:
     - List of homework assigned by the teacher, showing Subject, Title, Class/Section, Due Date, and submission counter (e.g. *28 / 40 Submitted*).
  2. **"Create Homework" Modal / Tab**:
     - Form: Class Section picker, Subject picker, Title, Description / Instructions, Due Date picker.
     - Attachment picker (select camera photo or PDF).
     - Submits to `POST /teacher/homework`.
  3. **Submissions Evaluation Drawer / Modal**:
     - Tap any homework card to view student submission list.
     - Each student card displays: Student Name, Roll No, Status (*Submitted*, *Missing*, *Evaluated*), Submission Timestamp, Download Attachment button.
     - Teacher grading input: Marks awarded (out of max marks), Evaluation Remarks, and "Save Grade" button (submits to `PATCH /teacher/homework/submissions/{id}`).

### C. Mobile Test Marks Entry Keypad (`results.tsx` / `marks.tsx`)
- **Real-Life Action:** Subject teacher enters scores for unit tests or class papers from their mobile device.
- **Components & Interactions**:
  1. Paper & Section selector: Select Exam (e.g. Unit Test 1), Class (10-A), and Subject (Mathematics).
  2. Maximum marks indicator (e.g. `/ 50`).
  3. List of enrolled students in roll order.
  4. Quick numerical entry keypad: Fast tap-to-enter score per child.
  5. Real-time validation: Prevents score &gt; max_marks.
  6. Live CBSE Grade Band chip (e.g. 45/50 = 90% -> A1).
  7. Batch "Save Marks" action calling `POST /teacher/marks`.

---

## 5. Phase 3: Parent Mobile App Operational Depth

Target Directory: `mobile/app/(parent)/`

### A. Monthly Attendance Calendar & Medical Leave (`attendance.tsx`)
- **Real-Life Action:** Parent tracks child's daily presence and requests medical leave.
- **Components & Interactions**:
  1. Child selector (for parents with multiple children in school).
  2. Monthly grid calendar with color-coded daily badges:
     - Green dot: Present
     - Red dot: Absent
     - Amber dot: Late
     - Blue dot: Approved Leave
     - Gray: Holiday / Weekend
  3. Monthly Attendance Percentage Gauge: Displays overall rate (e.g. 92%); highlights in amber/red if below 75% CBSE requirement.
  4. **"Apply for Leave" Button & Modal**:
     - Date Range picker (Start Date to End Date).
     - Reason text box (e.g. "Viral fever and doctor prescribed bed rest").
     - Medical certificate attachment upload.
     - Submits to `POST /parent/leave` (`student_leave_requests` table with `enrolment_id`).
     - Status tracker: Pending, Approved, Rejected with admin reason.

### B. Fee Receipts & Online Ledger (`fees.tsx`)
- **Real-Life Action:** Parent reviews billed invoices, views payment ledger, and downloads tax-deductible receipts.
- **Components & Interactions**:
  1. Financial summary card: Total Billed, Total Paid, Net Outstanding Balance.
  2. Unpaid / Overdue Invoices breakdown: Monthly invoice cards showing fee heads (Tuition, Computer Lab) and Due Date.
  3. **Payment Receipts History Tab**:
     - List of collected payments with receipt voucher numbers, payment dates, and payment modes (Cash, UPI, Card).
     - **"Download Receipt PDF"** button calling backend PDF generator (`/api/v1/fees/receipt/{id}`), enabling parent to save or print official two-copy receipts directly from phone.

### C. CBSE Report Card Download (`results.tsx`)
- **Real-Life Action:** Parent inspects term exam performance and downloads official report card.
- **Components & Interactions**:
  1. Exam Selector: Term 1 Exam, Midterm Exam, Final Board Prep.
  2. Academic Performance Card: Total Marks, Percentage, Overall Letter Grade (A1, A2, B1), and GPA.
  3. Subject-wise score table: Theory score, Practical score, Total, and Grade Point.
  4. **"Download Official Report Card" Button**:
     - Validates zero fee dues (enforces ERP dues-withholding rule).
     - Streams official school-crested A4 PDF report card to device.

### D. School Broadcast Push Alerts (`notices.tsx`)
- **Real-Life Action:** Parent receives instant official notices from school management.
- **Components & Interactions**:
  1. In-app notification feed with category tabs: All, Academic, Holidays, Emergencies.
  2. High-priority alert banner for urgent closures or bus delays.
  3. Full notice detail view with attachment downloads and publication date.

---

## 6. Phase 4: Student Mobile App Operational Depth

Target Directory: `mobile/app/(student)/`

### A. Timetable & Homework Digital Turn-in (`timetable.tsx` & `homework.tsx`)
- **Real-Life Action:** Student checks their daily classroom timetable and submits homework online.
- **Components & Interactions**:
  1. **Weekly Timetable Grid (`timetable.tsx`)**:
     - Day tabs: Mon, Tue, Wed, Thu, Fri, Sat.
     - Period cards showing Period Number, Timing (e.g. 08:30 - 09:15), Subject Name, Classroom Room Number, and Teacher Name.
     - Dynamic relief teacher indicator if a substitute has been assigned for that period.
  2. **Homework Turn-In Dashboard (`homework.tsx`)**:
     - Filter by Pending vs Completed assignments.
     - Homework card showing subject, title, instructions, and due date countdown.
     - **"Submit Homework" Modal**:
       - Text submission area.
       - Photo/PDF document upload (homework photo).
       - Submits to `POST /student/homework/{id}/submit` (`homework_submissions` table linked to `enrolment_id`).
       - Displays status: *Turned In*, *Graded*, with teacher remarks.

### B. Academic Marks Viewer (`results.tsx`)
- **Real-Life Action:** Student reviews their academic progress and examination grades.
- **Components & Interactions**:
  1. Exam scorecard selector.
  2. Marks breakdown per subject with visual progress bars.
  3. Teacher comments and subject grade points.

---

## 7. Deep Automated Testing Strategy & Verification Plan (Mandatory Engineering Standard)

To guarantee rock-solid database integrity and zero regressions during Session 6, testing must not merely rely on existing tests or HTTP 200 responses. **Every new and refactored workflow must be verified through automated tests that assert directly against database row mutations, foreign key constraints, relational bounds, and strict RBAC isolation.**

---

### 7.1 Schema Migration & Database Constraint Test Suite (`backend/tests/test_enrolment_id_migration.py`)

A dedicated migration test file verifying schema evolution, foreign key constraints, cascade rules, and backfill accuracy:

1. **Foreign Key & Column Nullability Assertions**:
   - `marks.enrolment_id` exists, is `NOT NULL`, and has an active foreign key `FK -> enrolments.id` with `ON DELETE RESTRICT`.
   - `homework_submissions.enrolment_id` exists, is `NOT NULL`, and has an active foreign key `FK -> enrolments.id` with `ON DELETE CASCADE`.
   - `grievances.enrolment_id` exists, is nullable (`nullable=True`), and has an active foreign key `FK -> enrolments.id` with `ON DELETE SET NULL`.
   - Direct introspection via `sqlalchemy.inspect` or `information_schema` asserting column types (`BigInteger`), nullability flags, and foreign key definitions.

2. **Data Migration Backfill Accuracy**:
   - Verify pre-existing records in `marks` are correctly mapped to `enrolments.id` where `enrolments.student_id = marks.student_id` AND `enrolments.academic_year_id = exams.academic_year_id`.
   - Verify pre-existing records in `homework_submissions` are correctly mapped to `enrolments.id` where `enrolments.student_id = homework_submissions.student_id` AND `enrolments.class_section_id = homework.class_section_id`.
   - Verify pre-existing student grievances map to the student's active enrollment.

3. **Relational Boundary Enforcement (Cross-Contamination Rejection)**:
   - **Cross-Academic-Year Mark Rejection**: Attempting to insert a `Mark` for an `enrolment_id` belonging to 2025-26 on an `Exam` scheduled for 2026-27 must be strictly rejected at the service/database layer with an integrity error or `422 Unprocessable Entity`.
   - **Cross-Section Homework Rejection**: Attempting to insert a `HomeworkSubmission` for an `enrolment_id` belonging to Class 10-B on a `Homework` assigned to Class 10-A must fail validation and raise an error.

4. **Updated Unique Constraint Verification**:
   - Assert `UniqueConstraint('exam_id', 'subject_id', 'enrolment_id')` on `marks`. Attempting to insert two marks for the same exam, subject, and enrollment must trigger a database `IntegrityError` or API `409 Conflict`.
   - Assert `UniqueConstraint('homework_id', 'enrolment_id')` on `homework_submissions`. Attempting to insert duplicate submissions without explicit revision flow must trigger an `IntegrityError`.

5. **ON DELETE Integrity Verification**:
   - **Marks**: Deleting an `enrolment` that has linked marks must be prevented by the database (`ON DELETE RESTRICT`) to preserve official academic transcripts.
   - **Homework Submissions**: Deleting an `enrolment` must cascade-delete student homework submissions (`ON DELETE CASCADE`).
   - **Grievances**: Deleting an `enrolment` must retain the grievance record while setting `grievances.enrolment_id = NULL` (`ON DELETE SET NULL`).

---

### 7.2 Backend API & Database Mutation Test Suite (`backend/tests/test_enrolment_id_api.py`)

Every new or modified endpoint must have tests asserting both the HTTP response and the resulting database state:

1. **Direct Database Assertion Rule**:
   - **Do NOT merely assert `response.status_code == 200`.**
   - After invoking any mutating endpoint (`POST`, `PUT`, `PATCH`, `DELETE`), query the database directly using `db.scalars(select(...))` or `db.get(...)`.
   - Assert that the exact database row exists, that `enrolment_id` matches the expected ID, that foreign keys are valid, and that timestamp/status columns were accurately updated.

2. **Negative & Edge-Case Test Scenarios**:
   - **Invalid / Non-Existent `enrolment_id`**: Submitting an arbitrary or non-existent `enrolment_id` (e.g. `999999`) must return `404 Not Found` or `422 Unprocessable Entity`.
   - **Cross-Tenant Access Attempt**: A request authenticated under Tenant A attempting to create or access data using a Tenant B `enrolment_id` must return `403 Forbidden` or `404 Not Found`, guaranteeing zero cross-tenant data leakage.
   - **Cross-Academic-Year Access Attempt**: Submitting marks, attendance, or homework for an enrollment in a previous academic session must be rejected with `400/422`.
   - **Unauthorized Roles**: Verifying role boundaries (e.g., student calling teacher marks entry endpoint, parent calling homework grading endpoint) strictly returns `403 Forbidden`.
   - **Missing Required Fields**: Payloads omitting required fields (`enrolment_id`, `marks_obtained`, `status`) must return `422 Validation Error`.
   - **Duplicate Submissions**: Submitting duplicate marks or duplicate homework submissions without a revision flag returns `409 Conflict` or a clear validation error.
   - **Validation Boundaries**:
     - Marks > `max_marks` (e.g. 55/50) or negative marks (-5) must be rejected with `422`.
     - Future dates for daily attendance roll-calls must be rejected.
     - Invalid status transitions (e.g. directly jumping from 'draft' to 'completed' without review) must be rejected.

---

### 7.3 Teacher Mobile Workflow Test Suite (`backend/tests/test_mobile_teacher_workflows.py`)

Validates the teacher mobile operational workflows end-to-end:

1. **Classroom Roll Marking (`attendance.tsx`)**:
   - **Fetch Section Roster**: `GET /api/v1/teacher/classes/{section_id}/students` returns students enrolled in that class section with their active `enrolment_id` and roll numbers.
   - **Submit Batch Attendance**: `POST /api/v1/teacher/attendance` accepts a batch roster payload with a realistic mix of `P` (Present), `A` (Absent), `L` (Late), and `M` (Medical Leave).
   - **"Mark All Present" Shortcut**: Payload generated by the one-tap action correctly marks all active enrollments as `P`.
   - **Counter Verification**: Headers and payload summaries correctly compute Total, Present, Absent, and Leave counts.
   - **Database Row Verification**: Direct DB query on `attendance` table verifies that rows exist for that `date`, that each row references `enrolment_id`, and that the `status` enum matches.
   - **Submitted State & Lock**: Once submitted, verify the endpoint reports the attendance register as submitted (read-only or requiring supervisor override).

2. **Homework Management (`homework.tsx`)**:
   - **Create Homework**: `POST /api/v1/teacher/homework` creates a new assignment with due date, title, instructions, and attachment JSON. Assert DB row has correct `academic_year_id`, `class_section_id`, and `created_by_teacher_id`.
   - **List Submissions**: `GET /api/v1/teacher/homework/{id}/submissions` returns all submissions filtered strictly to this homework's class section.
   - **Grade Submission**: `PATCH /api/v1/teacher/homework/submissions/{id}` updates marks, letter grade, and teacher remarks. Assert DB row in `homework_submissions` reflects `marks`, `remarks`, and a non-null `graded_at` timestamp.
   - **Teacher Section Isolation**: Verify Teacher X cannot grade or edit homework assigned to Teacher Y's section (returns `403 Forbidden` unless Admin).

3. **Mobile Test Marks Entry (`results.tsx` / `marks.tsx`)**:
   - **Fetch Examination Roster**: `GET /api/v1/teacher/exams/{exam_id}/classes/{class_section_id}/subjects/{subject_id}/roster` returns enrolled students for that specific exam and subject.
   - **Enter Marks with Numerical Validation**: `POST /api/v1/teacher/marks` accepts numerical scores. Asserts scores > `max_marks` or < 0 are rejected with `422`.
   - **Database Insertion Assertion**: Assert rows in `marks` table are saved against `enrolment_id` with computed CBSE grade bands.
   - **Upsert / Conflict Handling**: Verifies that updating an existing student mark correctly executes an in-place update or audited mark revision.

---

### 7.4 Parent Mobile Workflow & Ledger Test Suite (`backend/tests/test_mobile_parent_workflows.py`)

Validates parent portal data access, isolation, fee ledgers, and report cards:

1. **Strict Child Isolation**:
   - Parent accounts are linked to specific students via `student_guardians`.
   - Assert Parent A can ONLY query endpoints for their own linked children.
   - Assert Parent A querying child data of Parent B returns `403 Forbidden` or `404 Not Found`.

2. **Attendance Calendar**:
   - `GET /api/v1/parent/children/{child_id}/attendance?month=YYYY-MM`: Returns month attendance mapping keyed by day with status badges (`P`, `A`, `L`, `M`).
   - Asserts that days with approved medical leave display `M` status.

3. **Student Medical Leave Application**:
   - `POST /api/v1/parent/leave`: Submits leave request with date range, reason, and optional medical certificate document URL.
   - Assert DB row in `student_leave_requests` is created with `status='pending'` and points to the child's `enrolment_id`.
   - Simulate Admin approval and verify that the child's attendance calendar for that date range reflects `M`.

4. **Fee Receipts & Online Ledger**:
   - `GET /api/v1/parent/children/{child_id}/fees/summary`: Returns Total Billed, Total Paid, and Balance Dues.
   - Direct assertion: Verify the returned figures strictly equal `SUM(invoice_lines.amount) - SUM(payment_allocations.amount)` from the live database.
   - **Receipt Download**: `GET /api/v1/fees/receipt/{id}` returns HTTP 200 with `Content-Type: application/pdf` and non-empty binary content.

5. **CBSE Report Card Download & Dues Withholding Gate**:
   - `GET /api/v1/parent/children/{child_id}/report-card/{exam_id}`: Returns official school-crested A4 PDF report card.
   - **Fee-Dues Withholding Rule**: If the student's active enrollment has unpaid fee dues exceeding the allowed threshold, report card download must be blocked with `402 Payment Required` or `403 Forbidden` and an explicit message ("Fee dues outstanding. Please clear balance to download report card.").

6. **School Notices & Circulars**:
   - `GET /api/v1/parent/notices`: Returns school circulars filtered by tenant and child's class. Asserts attachment download URLs are valid and accessible.

---

### 7.5 Student Mobile Workflow Test Suite (`backend/tests/test_mobile_student_workflows.py`)

Validates the student portal workflows:

1. **Class Timetable Resolution**:
   - `GET /api/v1/student/timetable`: Fetches timetable for the logged-in student.
   - Asserts that returned periods belong strictly to the student's current active class section and academic year.

2. **Digital Homework Turn-In**:
   - `GET /api/v1/student/homework`: Returns active homework assigned to the student's class section.
   - `POST /api/v1/student/homework/{id}/submit`: Submits homework response with text and attachment document.
   - Assert DB row created in `homework_submissions` linked to the student's `enrolment_id`.
   - **Cross-Class Restriction**: Verify student in Class 10-A cannot submit homework assigned to Class 10-B (rejected with `403/422`).
   - **Duplicate Turn-In**: Submitting a duplicate response without explicit resubmission flag returns `409 Conflict`.
   - **Status Reflection**: Once submitted, verify the endpoint reflects "Turned In" status; once graded by teacher, reflects "Graded" status with marks and teacher remarks.

3. **Academic Marks & Term Results**:
   - `GET /api/v1/student/results`: Returns exam results and subject scorecards.
   - Assert that only marks corresponding to the student's active enrollment are returned.

---

### 7.6 Critical Multi-Tenant & RBAC Isolation Test Suite (`backend/tests/test_session6_tenant_isolation.py`)

Enforces the project's zero-leakage multi-tenant architectural foundation:

1. **Multi-Tenant Isolation**:
   - Fixtures seed Tenant 1 (`school_id=1`, Sunrise Public School) and Tenant 2 (`school_id=2`, Green Valley Academy).
   - Assert at both the database query level and API level that a user from Tenant 1 cannot access, read, or mutate Tenant 2 records across:
     - `students` and `enrolments`
     - `attendance`
     - `homework` and `homework_submissions`
     - `marks` and `exams`
     - `fee_invoices`, `fee_payments`, and `fee_receipts`
     - `grievances`
   - Any query attempting cross-tenant access must return `403 Forbidden` or `404 Not Found` with zero data exposure.

2. **Role-Based Access Control (RBAC) Boundaries**:
   - Dedicated `receptionist` role: Strictly restricted to admission queues and walk-in candidate intake (`/recruitment`); blocked from `/staff-leave`, `/payroll`, `/exams/marks`, and `/fees/receipts`.
   - `student` role: Strictly blocked from teacher roll marking, homework creation, and marks entry.
   - `teacher` role: Restricted to assigned classes; blocked from modifying school fee plans or student admission status.

---

### 7.7 Regression Testing Protocol & Baseline Tracking

1. **Pre-Session Baseline**:
   - Run `pytest -q` before writing any Session 6 code to establish the exact passing baseline (e.g. 657 passed, 1 skipped).
2. **Zero Regressions Standard**:
   - All pre-existing test suites across exams, homework, grievances, admissions, attendance, and fees must continue to pass 100% green.
3. **Intentional Test Updates for `enrolment_id`**:
   - If an existing test fails because it passed `student_id` into a `Mark` or `HomeworkSubmission` factory or assertion, update that test to pass `enrolment_id`.
   - **Strict Rule:** Document every single updated test (filename, test function name, line number, and why it changed) in the final session report. **Never delete, skip, or weaken an existing test.**

---

### 7.8 Test Quality & Realistic Fixture Data Architecture (`backend/tests/conftest_session6.py`)

Tests must avoid synthetic shortcuts and reflect real-world school operations:
1. **Full Pipeline Verification**:
   - Every test must execute the full cycle: `API Request Payload` → `JWT Auth & Tenant Scoping` → `Business Rule Validation` → `Database Mutation` → `Relational Integrity Check` → `Response Body Validation`.
2. **Realistic Multi-Tenant & Multi-Year Fixtures**:
   - **Two Tenants**: Minimum 2 independent schools (`school_id=1`, `school_id=2`).
   - **Two Academic Years**: Minimum 2 consecutive academic years (e.g. `2025-26` and `2026-27`) to test year isolation and promotion rollover.
   - **Multi-Year Enrolments**: Seed students who have an enrollment in 2025-26 (`Class 9-A`, `status='promoted'`) and a new active enrollment in 2026-27 (`Class 10-A`, `status='active'`). Prove marks and homework attach to the correct annual enrollment.
   - **Multiple Class Sections**: Class 10-A and 10-B with assigned class teachers.
   - **Multi-Child Guardians**: Parent fixtures linked to multiple children in different classes.

---

### 7.9 Final Acceptance Gate & Verification Checklist

Before Session 6 can be declared complete, ALL 9 acceptance gates must pass:

- [ ] **Gate 1 (Alembic Migration)**: `alembic upgrade head` succeeds cleanly from `a1b2c3d4e5f6` to `b2c3d4e5f6a7_enrolment_id_refactor`.
- [ ] **Gate 2 (Full Test Suite Pass)**: `pytest -q` passes 100% green with 0 failures (baseline tests + all new Session 6 tests).
- [ ] **Gate 3 (Schema & Backfill Integrity)**: All migration tests pass verifying `marks.enrolment_id`, `homework_submissions.enrolment_id`, `grievances.enrolment_id`, foreign keys, cascade rules, and backfilled rows.
- [ ] **Gate 4 (Multi-Tenant & RBAC Isolation)**: All isolation tests pass proving zero cross-tenant and cross-role leakage.
- [ ] **Gate 5 (Linter Compliance)**: `npm run lint` passes with 0 errors in both `web/` and `mobile/`.
- [ ] **Gate 6 (TypeScript Typecheck)**: `npx tsc --noEmit` passes with 0 errors in both `web/` and `mobile/`.
- [ ] **Gate 7 (Mobile Ecosystem Health)**: `npx expo-doctor` passes all 21/21 health checks in `mobile/`.
- [ ] **Gate 8 (Documentation Sync)**: `python scripts/verify_db_docs.py` passes with 0 schema drift (17/17 checks passed).
- [ ] **Gate 9 (Visual Verification Proofs)**: Screenshot proofs captured and saved in `docs/screenshots/` for:
  1. Teacher classroom roll-call marking screen (`attendance.tsx`).
  2. Teacher homework manager and submission grading drawer (`homework.tsx`).
  3. Teacher mobile marks entry keypad (`results.tsx` / `marks.tsx`).
  4. Parent attendance calendar and medical leave modal (`attendance.tsx`).
  5. Parent fee ledger and 2-copy PDF receipt view (`fees.tsx`).
  6. Parent CBSE report card download and dues-withholding gate (`results.tsx`).
  7. Student weekly timetable grid and homework turn-in drawer (`timetable.tsx`, `homework.tsx`).

---

### 7.10 Standard Final Report Format Mandate

Upon completion of Session 6, provide the final report in this exact structure:

```markdown
# Session 6 Completion Report

## 1. Executive Summary
[Brief overview of Session 6 achievements: enrolment_id refactor, mobile features, test results]

## 2. Schema Changes Verified
- Tables modified: marks, homework_submissions, grievances
- Columns added / migrated: enrolment_id (BigInteger, FK -> enrolments.id)
- Constraints updated: UniqueConstraint(exam_id, subject_id, enrolment_id), UniqueConstraint(homework_id, enrolment_id)
- Migration revision: b2c3d4e5f6a7_enrolment_id_refactor (down: a1b2c3d4e5f6)
- Backfill verification summary: [X marks, Y submissions backfilled cleanly]

## 3. Test Execution Results
- Total tests executed: [Count]
- Existing baseline tests: [Count passed]
- New tests implemented in Session 6: [Count passed]
  - Schema migration & constraints: [Count]
  - Backend API & DB mutations: [Count]
  - Teacher mobile workflows: [Count]
  - Parent mobile workflows & ledger: [Count]
  - Student mobile workflows: [Count]
  - Multi-tenant & RBAC isolation: [Count]
- Test failures / errors: 0 (100% green)

## 4. Key Workflow Verification Highlights
- Classroom Attendance: [Roll call marking, P/A/L/M status, Mark All Present, DB verified]
- Homework Management: [Creation with attachments, student turn-in, teacher grading drawer, section isolation]
- Mobile Marks Keypad: [Score entry <= max_marks, CBSE grade bands, DB verified against enrolment_id]
- Parent Fee Receipts & Ledger: [Real-time ledger math, 2-copy PDF receipt download verified]
- Parent CBSE Report Card: [A4 PDF generation, fee-dues withholding gate verified]
- Student Timetable & Turn-in: [Class timetable resolution, digital homework submission]

## 5. Regression Confirmation
- Zero regressions confirmed across all existing test suites.
- List of existing tests updated due to student_id -> enrolment_id migration:
  - [File, test name, rationale for update]

## 6. Acceptance Gate Status
- [x] Gate 1: Alembic upgrade head clean
- [x] Gate 2: Full pytest suite 100% green
- [x] Gate 3: Schema migration & backfill assertions pass
- [x] Gate 4: Multi-tenant & RBAC assertions pass
- [x] Gate 5: npm run lint clean (web + mobile)
- [x] Gate 6: TypeScript clean (web + mobile)
- [x] Gate 7: Expo doctor 21/21 passed
- [x] Gate 8: verify_db_docs.py 17/17 passed (0 drift)
- [x] Gate 9: Visual proofs captured
```

---

## 8. Hard-Won Rules & Invariants to Uphold

1. **The Enrolment vs Student Invariant**:
   - `students.id` is permanent identity for life.
   - `enrolments.id` is the annual class session membership.
   - Daily attendance, homework submissions, marks, fee invoices, fee payments, and report cards must strictly hang off `enrolment_id`.
2. **Financial Immutability**:
   - Fee payments are never edited in place; contra reversals remain mandatory.
   - Outstanding balance is always calculated as `SUM(invoice_lines) - SUM(payment_allocations)`.
3. **Audit Trails for Destructive Actions**:
   - Deleting homework, overriding marks, or rejecting leave requires a typed reason saved to `audit_log`.
4. **Mobile Native Design**:
   - Use existing UI primitives from `mobile/src/components/ui.tsx` (`Card`, `Button`, `Screen`, `s`).
   - Maintain clean typography, responsive touch targets (minimum 44px), and native status bar styling.
