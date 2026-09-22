# Sunrise School ERP — Comprehensive Academic & Operational Dataset

## Overview
This dataset contains real-world structured relational data from the **Sunrise School ERP** system (CBSE Affiliated K-12 School Management System).
It encompasses student lifecycle records, academic grades, examination scores, daily attendance logs, fee billing and transactions, timetable scheduling, staff payroll, recruitment, and inventory catalog.

- **Total Tables**: 72 relational tables
- **Total Records**: 12,584 rows
- **Format**: Standard CSV (UTF-8) with headers

## Key Relational Domains & Tables
1. **Students & Demographics**:
   - `students.csv` — Permanent student identity, registration, DOB, blood group, admission numbers.
   - `enrolments.csv` — Academic session enrollments, class & section memberships, promotion status.
   - `guardians.csv` & `student_guardian.csv` — Parents, emergency contacts, occupations.
2. **Academics & Examinations**:
   - `marks.csv` — 2,400 exam score records with subject breakdown and grade scales.
   - `attendance.csv` — 5,800 daily period attendance entries with Present/Absent/Late status.
   - `homework.csv` & `homework_submissions.csv` — Homework assignments, digital turn-in status, marks.
   - `timetable_slots.csv` — Weekly period schedule across classes, teachers, and subjects.
3. **Finance & Fee Management**:
   - `fee_invoices.csv` & `fee_invoice_lines.csv` — Term tuition, transport, admission fee breakdown.
   - `fee_payments.csv` & `payment_allocations.csv` — Cash, bank, and online receipt allocations.
4. **Staff, HR & Payroll**:
   - `employees.csv` — Teacher and staff master directory, departments, qualification.
   - `salary_structures.csv` & `salary_components.csv` — CTC, EPF, ESI, and tax structures.
5. **School Operations**:
   - `stock_items.csv` & `stock_requests.csv` — School inventory, consumption, minimum threshold levels.
   - `grievances.csv` & `grievance_replies.csv` — Parent/Teacher support ticketing and audit logs.
   - `routes.csv` & `route_stops.csv` — Bus fleet transit stops and passenger assignments.

## Primary Invariants & Primary/Foreign Keys
- `students.id` is the permanent student record across all years.
- `enrolments.id` is the session-scoped record (`marks`, `attendance`, and `homework_submissions` link strictly to `enrolment_id`).
- All tables maintain multi-tenant isolation via `school_id`.
