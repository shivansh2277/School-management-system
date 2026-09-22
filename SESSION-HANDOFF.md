# Session Handoff — Active Brief for Session 6

> **ACTIVE BRIEF — 18 September 2026.**  
> See the complete, detailed engineering specification in **[`SESSION-HANDOFF-6.md`](SESSION-HANDOFF-6.md)**.

---

## Master Scope for Session 6

1. **Schema Refactoring (`enrolment_id` Migration)**:
   - Refactor `marks`, `homework_submissions`, and `grievances` to use `enrolment_id` instead of `student_id`.
   - Enforce the foundational invariant: *"Year-scoped facts hang off `enrolment_id`; lifetime facts hang off `student_id`"*.
   - Create Alembic migration `b2c3d4e5f6a7_enrolment_id_refactor.py` with data backfill and foreign key constraints to `enrolments.id`.
   - Update SQLAlchemy models, Pydantic schemas, and API routes in `backend/app/`.

2. **Teacher Mobile App (`mobile/app/(teacher)`)**:
   - **Classroom Roll Marking (`attendance.tsx`)**: Class/Section picker, pupil list with status toggles (P/A/L/M), mark all present quick button, and batch submit.
   - **Homework Manager (`homework.tsx`)**: Daily homework composer with due dates and attachments; student turn-in viewer and grading/evaluation drawer.
   - **Mobile Test Marks Entry Keypad (`results.tsx` / `marks.tsx`)**: Compact keypad for teachers to rapidly enter exam scores with max_marks validation and auto CBSE grade band chips.

3. **Parent Mobile App (`mobile/app/(parent)`)**:
   - **Monthly Attendance Calendar & Leave (`attendance.tsx`)**: Color-coded attendance calendar, shortage alerts (&lt;75%), and medical leave request modal submitting to `student_leave_requests`.
   - **Fee Receipts & Online Ledger (`fees.tsx`)**: Outstanding dues card, invoice breakdown, and 1-click download/view of official two-copy PDF fee receipts (`/api/v1/fees/receipt/{id}`).
   - **CBSE Report Card Download (`results.tsx`)**: Term scorecards with GPA and 1-click official A4 report card PDF download (with zero-dues withholding gate).
   - **School Broadcast Push Alerts (`notices.tsx`)**: Official circulars, holiday announcements, and urgent emergency alerts.

4. **Student Mobile App (`mobile/app/(student)`)**:
   - **Timetable & Homework Turn-in (`timetable.tsx` & `homework.tsx`)**: Daily 6-period timetable schedule with room and teacher names; homework viewer with photo/PDF digital turn-in upload.
   - **Academic Marks Viewer (`results.tsx`)**: Subject-wise term exam scores, CBSE letter grades, and teacher remarks.

5. **Deep Automated Testing Mandate & Multi-Tier Verification**:
   - **Schema Migration Tests**: Foreign keys, NOT NULL, cascade rules, backfill accuracy, cross-year mark rejection, cross-section homework rejection.
   - **Direct Database Mutation Assertions**: Assert directly on database rows (`db.scalars(...)`), not just HTTP 200.
   - **Full Role & Workflow Coverage**: Dedicated automated tests for Teacher attendance/homework/marks, Parent child isolation/ledger/report-card gate, Student timetable/turn-in, and strict Multi-Tenant isolation.
   - **Zero Regression Policy**: Baseline test pass + intentional update tracking for any `student_id` test references.
   - **Acceptance Gates (9/9)**: Alembic migration, 100% green pytest, schema assertions, multi-tenant isolation, web & mobile linting, web & mobile TypeScript, Expo doctor (21/21), `verify_db_docs.py` (17/17), and visual screenshot proofs.

---

*For exact SQL queries, model definitions, UI components, and complete testing specifications, refer to [`SESSION-HANDOFF-6.md`](SESSION-HANDOFF-6.md).*
