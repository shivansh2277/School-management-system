"""Chapter 8: Consolidated Database Table Reference & Table Classifications."""

def render_ch6() -> str:
    return """
<div class="page-break"></div>

<div class="section-banner">
  <h2>8. Consolidated Database Table Reference</h2>
  <p class="desc">Complete technical classification of active database tables supporting operational workflows.</p>
</div>

<p>
  The Sunrise ERP schema organizes relational data across six distinct architectural classifications. Understanding these categories is essential for database administrators, query optimization, and transaction design.
</p>

<!-- TABLE CLASSIFICATION DEFINITIONS -->
<div class="sub-heading">8.1 Architectural Table Classifications</div>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 20%;">Category</th>
      <th style="width: 40%;">Architectural Responsibility</th>
      <th style="width: 40%;">Operational Invariants & Examples</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Core / Master Tables</strong></td>
      <td>Stores foundational business entities that exist independently of specific transactions (e.g. users, students, employees, classes, subjects).</td>
      <td>Rarely deleted; uses soft-deactivation flags (<code>is_active</code>); primary keys widely referenced as foreign keys across the schema.</td>
    </tr>
    <tr>
      <td><strong>Transaction Tables</strong></td>
      <td>Records operational events that occur at specific points in time (e.g. fee payments, attendance marks, exam scores, stock requisitions).</td>
      <td>High write volume; strictly immutable financial records; financial rows use contra reversals rather than in-place updates.</td>
    </tr>
    <tr>
      <td><strong>Linking / Junction Tables</strong></td>
      <td>Resolves Many-to-Many (M:N) relationships between master or transactional entities (e.g. <code>student_guardian</code>, <code>class_subject_teacher</code>, <code>payment_allocations</code>).</td>
      <td>Carries composite foreign keys; frequently maintains unique constraints to prevent duplicate associations.</td>
    </tr>
    <tr>
      <td><strong>Audit & History Tables</strong></td>
      <td>Preserves immutable chronological logs of sensitive actions, destructive state changes, and session rollover progression (e.g. <code>audit_log</code>).</td>
      <td>Append-only; requires mandatory human-typed explanation reasons; never updated or purged.</td>
    </tr>
    <tr>
      <td><strong>Configuration Tables</strong></td>
      <td>Governs school-wide operational rules, feature toggles, grading boundaries, and fee schedules (e.g. <code>settings</code>, <code>grade_bands</code>, <code>fee_plans</code>).</td>
      <td>Low row counts; modified primarily by administrators during school setup or annual review.</td>
    </tr>
    <tr>
      <td><strong>Tenant-Scoped Tables</strong></td>
      <td>Every table deriving from <code>TenantBase</code> carrying a non-nullable <code>school_id</code> foreign key pointing to <code>schools.id</code>.</td>
      <td>90 of 93 tables in Sunrise ERP; guarantees complete multi-tenant database isolation.</td>
    </tr>
  </tbody>
</table>

<!-- CONSOLIDATED TABLE DIRECTORY -->
<div class="sub-heading">8.2 Complete Reference of Operational Tables</div>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 15%;">Table</th>
      <th style="width: 12%;">Classification</th>
      <th style="width: 15%;">Primary Module(s)</th>
      <th style="width: 28%;">Main Responsibility & Stored Records</th>
      <th style="width: 30%;">Important Foreign Keys</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>schools</code></td>
      <td>Core Master</td>
      <td>System / Tenancy</td>
      <td>Customer school tenant identity, domain slug, and status.</td>
      <td>None (Root Master Entity)</td>
    </tr>
    <tr>
      <td><code>users</code></td>
      <td>Core Master</td>
      <td>System / Auth</td>
      <td>Authentication logins, Bcrypt password hashes, active status.</td>
      <td><code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>students</code></td>
      <td>Core Master</td>
      <td>Students</td>
      <td>Permanent student identity, unique admission number, DOB, gender.</td>
      <td><code>user_id -> users.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>guardians</code></td>
      <td>Core Master</td>
      <td>Students</td>
      <td>Parent/guardian identity, contact details, occupation, income.</td>
      <td><code>user_id -> users.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>student_guardian</code></td>
      <td>Junction Table</td>
      <td>Students</td>
      <td>M:N linkage binding students to parent/guardian records.</td>
      <td><code>student_id -> students.id</code>, <code>guardian_id -> guardians.id</code></td>
    </tr>
    <tr>
      <td><code>academic_years</code></td>
      <td>Configuration</td>
      <td>Academics</td>
      <td>Academic session calendars (e.g. 2025-26, 2026-27), start/end dates.</td>
      <td><code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>class_sections</code></td>
      <td>Core Master</td>
      <td>Academics</td>
      <td>Classroom cohorts (e.g. 10-A), class teacher assignments.</td>
      <td><code>class_teacher_id -> employees.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>enrolments</code></td>
      <td>Core / Transaction</td>
      <td>Academics / All</td>
      <td>Annual class membership, roll numbers, progression status.</td>
      <td><code>student_id -> students.id</code>, <code>academic_year_id -> academic_years.id</code>, <code>class_section_id -> class_sections.id</code></td>
    </tr>
    <tr>
      <td><code>attendance</code></td>
      <td>Transaction</td>
      <td>Attendance</td>
      <td>Daily morning student roll-call presence/absence records.</td>
      <td><code>enrolment_id -> enrolments.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>fee_heads</code></td>
      <td>Configuration</td>
      <td>Fees</td>
      <td>Catalog of fee charge heads (Tuition, Lab, Transport).</td>
      <td><code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>fee_plans</code></td>
      <td>Configuration</td>
      <td>Fees</td>
      <td>Standard class fee structures per academic year.</td>
      <td><code>academic_year_id -> academic_years.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>fee_invoices</code></td>
      <td>Transaction</td>
      <td>Fees</td>
      <td>Student billing invoice vouchers and total settlement status.</td>
      <td><code>enrolment_id -> enrolments.id</code>, <code>period_id -> fee_periods.id</code></td>
    </tr>
    <tr>
      <td><code>fee_invoice_lines</code></td>
      <td>Transaction</td>
      <td>Fees</td>
      <td>Line-item breakdown of invoiced fee heads.</td>
      <td><code>invoice_id -> fee_invoices.id</code>, <code>fee_head_id -> fee_heads.id</code></td>
    </tr>
    <tr>
      <td><code>fee_payments</code></td>
      <td>Transaction</td>
      <td>Fees</td>
      <td>Cashier receipt vouchers and contra reversal entries.</td>
      <td><code>enrolment_id -> enrolments.id</code>, <code>reverses_payment_id -> fee_payments.id</code></td>
    </tr>
    <tr>
      <td><code>payment_allocations</code></td>
      <td>Junction Table</td>
      <td>Fees</td>
      <td>FIFO binding between collected payments and invoice lines.</td>
      <td><code>payment_id -> fee_payments.id</code>, <code>invoice_line_id -> fee_invoice_lines.id</code></td>
    </tr>
    <tr>
      <td><code>fee_periods</code></td>
      <td>Configuration</td>
      <td>Fees</td>
      <td>Monthly financial accounting close periods.</td>
      <td><code>academic_year_id -> academic_years.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>exams</code></td>
      <td>Configuration</td>
      <td>Examinations</td>
      <td>Major examination definitions (Term 1, Final Board Prep).</td>
      <td><code>academic_year_id -> academic_years.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>marks</code></td>
      <td>Transaction</td>
      <td>Examinations</td>
      <td>Subject marks awarded to students and calculated grade points.</td>
      <td><code>exam_id -> exams.id</code>, <code>subject_id -> subjects.id</code>, <code>student_id -> students.id</code></td>
    </tr>
    <tr>
      <td><code>grade_bands</code></td>
      <td>Configuration</td>
      <td>Examinations</td>
      <td>CBSE 8-Point scale percentage brackets (A1, A2, B1, etc.).</td>
      <td><code>grading_scale_id -> grading_scales.id</code></td>
    </tr>
    <tr>
      <td><code>employees</code></td>
      <td>Core Master</td>
      <td>HR / Staff</td>
      <td>Staff master catalog, unique employee codes, departments.</td>
      <td><code>user_id -> users.id</code>, <code>department_id -> departments.id</code></td>
    </tr>
    <tr>
      <td><code>staff_leave_requests</code></td>
      <td>Transaction</td>
      <td>HR / Leave</td>
      <td>Teacher mobile leave applications and approval state.</td>
      <td><code>employee_id -> employees.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>substitutions</code></td>
      <td>Transaction</td>
      <td>HR / Academics</td>
      <td>Temporary faculty relief assignments to timetable slots.</td>
      <td><code>leave_request_id -> staff_leave_requests.id</code>, <code>substitute_teacher_id -> employees.id</code></td>
    </tr>
    <tr>
      <td><code>candidates</code></td>
      <td>Transaction</td>
      <td>Recruitment</td>
      <td>Teacher applicant pipeline stages (Applied, Shortlisted, Hired).</td>
      <td><code>employee_id -> employees.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>stock_items</code></td>
      <td>Core Master</td>
      <td>Inventory</td>
      <td>Consumable and equipment catalog, live balances, thresholds.</td>
      <td><code>category_id -> stock_categories.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
    <tr>
      <td><code>grievances</code></td>
      <td>Transaction</td>
      <td>Helpdesk</td>
      <td>Parent/staff complaint tickets, assigned departments, status.</td>
      <td><code>assigned_to_id -> employees.id</code>, <code>student_id -> students.id</code></td>
    </tr>
    <tr>
      <td><code>audit_log</code></td>
      <td>Audit & History</td>
      <td>System</td>
      <td>Immutable audit trail with operator IDs, actions, and typed reasons.</td>
      <td><code>user_id -> users.id</code>, <code>school_id -> schools.id</code></td>
    </tr>
  </tbody>
</table>
"""
