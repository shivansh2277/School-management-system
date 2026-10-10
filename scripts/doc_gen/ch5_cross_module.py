"""Chapter 7: Cross-Module Data Relationships and High-Level ERP Architecture."""

def render_ch5() -> str:
    return """
<div class="page-break"></div>

<div class="section-banner">
  <h2>7. Cross-Module Data Relationships & System Highways</h2>
  <p class="desc">How operational entities interface across functional domains through validated foreign key constraints.</p>
</div>

<p>
  In Sunrise School ERP, no module operates in a silo. A child's admission application becomes the student master record, which triggers annual enrollment, which subsequently feeds daily attendance, monthly fee invoicing, exam marksheets, bus routing, and report card publications. Similarly, teacher hiring directly feeds the employee directory, which drives timetable scheduling, mobile leave management, and monthly payroll batches.
</p>

<!-- HIGH-LEVEL ARCHITECTURE DIAGRAM -->
<div class="sub-heading">7.1 High-Level ERP Entity-Relationship Highway</div>

<div class="diagram-card">
   ========================================================================================
                               SUNRISE ERP DATA HIGHWAY
   ========================================================================================

   [ADMISSION PIPELINE]
   admission_cycles ──► applications ──► application_guardians / documents
                              │                 ▲
                              │                 │ (Document Exceptions Queue)
                              │        application_document_overrides
                              │
                              ▼ (1-Click Conversion: services/conversion.py)
   ========================================================================================
   [MASTER IDENTITY & RBAC CORE]
             ┌───────────────► users (Principals & token_version Invalidation)
             │                   │        ▲
             │                   │        └─► user_roles ◄── roles (Librarian, etc.)
             │                   ├─► employees ──────► departments
             │                   │        │
             │                   │        ├─► staff_leave_requests ──► substitutions
             │                   │        ├─► staff_attendance
             │                   │        ├─► payslips ──► payslip_items
             │                   │        └─► library_loans (Staff Borrowing)
             │                   │
             │                   └─► guardians ◄──┐
             │                                    │ (student_guardian junction)
             └───────────────► students ──────────┴───────────────────────────┐
                                 │                                            │
                                 ├─► student_passes / found_items (Reception) │
                                 ├─► student_certificates (Official TC/Study) │
                                 ▼ (student_id)                               │
   ========================================================================   │
   [SESSION-SCOPED ACADEMIC CORE]                                             │
   academic_years ──► class_sections ◄── class_subject_teacher                │
             │               │                                                │
             │               ├─► holiday_class_sections ◄── holidays          │
             │               │                                                │
             └───────────────┼─────────────────────────────────┐              │
                             ▼ (academic_year_id + section_id) │              │
                        enrolments ◄───────────────────────────┴──────────────┘
                             │
                             ├─► attendance (Daily Roll-Call Marks)
                             ├─► student_fee_plans ──► fee_plans ──► fee_plan_items
                             ├─► fee_invoices ──► fee_invoice_lines
                             │        ▲
                             │        └─► payment_allocations ◄── fee_payments
                             ├─► transport_assignments ──► routes ──► route_stops
                             ├─► student_leave_requests
                             ├─► library_loans ◄── book_copies ◄── books
                             └─► report_card_publications
                                      ▲
                                      │ (Gated on Zero Fee Dues)
   ========================================================================
   [EVALUATION & ASSESSMENT]
   exams ──► exam_schedule ──► marks ◄── students (student_id)
      │                          │
      └─► assessment_schemes     └─► grade_bands (CBSE 8-Point Scale)
   ========================================================================================
</div>

<!-- INTER-MODULE INPUT-OUTPUT CONTRACTS -->
<div class="sub-heading">7.2 Inter-Module Data Handoff Contracts</div>

<table class="doc-table">
  <thead>
    <tr>
      <th style="width: 20%;">Upstream Producing Module</th>
      <th style="width: 20%;">Downstream Consuming Module</th>
      <th style="width: 25%;">Shared Entities & Foreign Keys</th>
      <th style="width: 35%;">How Upstream Output Becomes Downstream Input</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Admission Pipeline</strong></td>
      <td><strong>Student Master & Academics</strong></td>
      <td><code>applications.student_id</code><br><code>students.id</code><br><code>enrolments.id</code></td>
      <td>Approved applications are converted into <code>students</code> and <code>enrolments</code> rows, populating class rosters and parent user logins.</td>
    </tr>
    <tr>
      <td><strong>Admission Document Overrides</strong></td>
      <td><strong>Application Checklist Gate</strong></td>
      <td><code>application_document_overrides.application_id</code><br><code>applications.id</code></td>
      <td>Document override requests queued with <code>status='pending'</code> are approved by Admin, clearing mandatory document prerequisites for admission scoring and conversion.</td>
    </tr>
    <tr>
      <td><strong>Class & Timetabling</strong></td>
      <td><strong>Student Attendance</strong></td>
      <td><code>class_sections.id</code><br><code>enrolments.id</code><br><code>class_sections.class_teacher_id</code></td>
      <td>Daily attendance forms pull the active student roster from <code>enrolments</code> and restrict morning roll marking to the designated <code>class_teacher_id</code>.</td>
    </tr>
    <tr>
      <td><strong>Class Fee Setup</strong></td>
      <td><strong>Fee Billing Engine</strong></td>
      <td><code>fee_plans.id</code><br><code>fee_plan_items.id</code><br><code>fee_concessions.enrolment_id</code></td>
      <td>The monthly invoicing engine queries class fee structures and approved student concessions to calculate invoice line totals.</td>
    </tr>
    <tr>
      <td><strong>Fee Collection</strong></td>
      <td><strong>Report Card Publication</strong></td>
      <td><code>fee_invoices.status</code><br><code>payment_allocations.amount</code><br><code>report_card_publications</code></td>
      <td>Before publishing exam report cards or hall tickets, the examination service verifies that the student has no outstanding invoice balance (<code>fees.defaulters</code> check).</td>
    </tr>
    <tr>
      <td><strong>Examinations & Marks</strong></td>
      <td><strong>Session Rollover</strong></td>
      <td><code>marks.grade_point</code><br><code>enrolments.status</code></td>
      <td>Session rollover wizard displays student term marks and GPA alongside promotion eligibility checkboxes to help coordinators identify detentions.</td>
    </tr>
    <tr>
      <td><strong>Teacher Recruitment</strong></td>
      <td><strong>Staff Directory & Timetable</strong></td>
      <td><code>candidates.employee_id</code><br><code>employees.id</code><br><code>timetable_slots</code></td>
      <td>Onboarding a hired teacher creates an <code>employees</code> record, making them immediately selectable as a class teacher or timetable subject instructor.</td>
    </tr>
    <tr>
      <td><strong>Teacher Leave Management</strong></td>
      <td><strong>Master Timetabling Grid</strong></td>
      <td><code>staff_leave_requests.id</code><br><code>substitutions.timetable_slot_id</code></td>
      <td>When teacher leave is approved, the system writes temporary rows to <code>substitutions</code>; daily timetable views automatically route duties to substitute teachers without altering master slots.</td>
    </tr>
    <tr>
      <td><strong>Consumable Inventory</strong></td>
      <td><strong>Departmental Expense Tracking</strong></td>
      <td><code>stock_requests.employee_id</code><br><code>stock_items.quantity</code></td>
      <td>Staff requisitions deduct from real-time stock balances and flag low-stock warnings when quantities drop below safe thresholds.</td>
    </tr>
    <tr>
      <td><strong>Library Circulation Desk</strong></td>
      <td><strong>Student & Staff Accounts</strong></td>
      <td><code>books.id</code><br><code>book_copies.id</code><br><code>library_loans.enrolment_id</code></td>
      <td>Physical barcode copies in <code>book_copies</code> are loaned to active student enrollments or employees; returns compute overdue fines and reset copy shelf availability.</td>
    </tr>
    <tr>
      <td><strong>Certificate Templating</strong></td>
      <td><strong>Official Student Records</strong></td>
      <td><code>certificate_templates.id</code><br><code>student_certificates.enrolment_id</code><br><code>students.id</code></td>
      <td>Templates format student identity and enrollment facts into standardized Transfer or Bonafide Certificates with frozen data snapshots and unique serial numbers.</td>
    </tr>
    <tr>
      <td><strong>Front Desk Reception</strong></td>
      <td><strong>Student Gate Security</strong></td>
      <td><code>student_passes.student_id</code><br><code>student_authorized_persons.student_id</code></td>
      <td>Reception verifies authorized pickup contacts before issuing student early departure gate passes, recording verified guardian details and gate codes.</td>
    </tr>
    <tr>
      <td><strong>User Access & RBAC</strong></td>
      <td><strong>Module Security & Authorization</strong></td>
      <td><code>user_roles.role_id</code><br><code>roles.code</code><br><code>users.token_version</code></td>
      <td>Admin assigns granular roles (e.g. Librarian) via <code>/user-access</code>; system increments <code>token_version</code> to enforce instant session claim refresh across web and mobile clients.</td>
    </tr>
  </tbody>
</table>
"""
