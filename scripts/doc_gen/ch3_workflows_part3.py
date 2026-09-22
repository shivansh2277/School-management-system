"""Chapter 4 & 5: Operational Workflows Part 3
Covers:
9. Staff Directory & HR (9.1)
10. Staff Attendance & Biometrics (10.1)
11. Staff Payroll, Statutory Deductions & Disbursal (11.1 - 11.3)
12. Teacher Leave & 100% Substitution Coverage Gate (12.1 - 12.3)
13. Teacher Recruitment & Automated Onboarding (13.1 - 13.3)
"""

from .ch3_workflows_part1 import render_workflow

def render_ch3_part3() -> str:
    content = """
<div class="section-banner">
  <h2>6. Detailed Operational Workflows: HR, Payroll, Leave & Recruitment</h2>
  <p class="desc">Faculty workforce lifecycle, biometric attendance, automated payroll registers, substitution locks, and hiring pipelines.</p>
</div>
"""

    # --- 11.2 Monthly Payroll Batch Processing ---
    content += render_workflow(
        wf_id="11.2",
        title="Monthly Staff Payroll Batch Processing, Statutory EPF/ESI/TDS Registers & Payslip Generation",
        overview={
            "real_life": "At month-end, the school accounts office computes monthly salaries for all 18 employees based on active salary structures, unpaid leaves, and statutory deductions.",
            "actor": "Payroll Officer / Head Bursar.",
            "trigger": "Accountant initiates payroll calculation for the month at <code>/payroll</code>.",
            "problem": "Manual salary calculation produces errors in statutory EPF, ESI, professional tax, and income tax (TDS) calculations.",
            "outcome": "Single batch calculates gross pay, statutory items, net pay, and generates individual printable CBSE payslips."
        },
        steps=[
            "<strong>User Action:</strong> Accountant selects Month (e.g. 'August 2026') and Year (2026) and clicks 'Calculate Payroll'.",
            "<strong>Frontend Processing:</strong> <code>Payroll.tsx</code> submits <code>POST /api/v1/admin/payroll/calculate</code>.",
            "<strong>Batch Header Insertion:</strong> Inserts parent row into <code>payroll_batches</code> with status <code>calculated</code>.",
            "<strong>Active Staff Iteration:</strong> Queries all active <code>employees</code> and their attached <code>salary_structures</code>.",
            "<strong>Salary Component Resolution:</strong> For each employee, calculates Base Pay, Dearness Allowance (DA), House Rent Allowance (HRA), EPF (12% of basic), ESI (0.75%), and TDS.",
            "<strong>Payslip Record Creation:</strong> Inserts row into <code>payslips</code> holding gross earnings, total deductions, and net payable salary.",
            "<strong>Payslip Line Item Breakdown:</strong> Inserts detailed rows into <code>payslip_items</code> itemizing each statutory and earning component.",
            "<strong>Final Output:</strong> Payroll register displayed with summary cards; printable payslips ready for staff; pending final disbursal approval."
        ],
        diagram="""[Payroll Accountant Screen (/payroll)]
       │
       ▼ (POST /admin/payroll/calculate)
[Payroll Calculation Engine (api/admin/payroll.py)]
       │
       ├─► [INSERT] payroll_batches ────────► Create monthly run header (AUG-2026, status='calculated')
       │         │
       │         ▼ (batch_id)
       ├─► [READ] employees & salary_struct ─► Fetch compensation packages for 18 staff
       │         │
       │         ▼
       ├─► [INSERT] payslips ───────────────► Insert individual slip per employee (Gross, Deductions, Net)
       │         │
       │         ▼ (payslip.id)
       └─► [INSERT] payslip_items ──────────► Itemize Basic (₹30,000), HRA (₹12,000), EPF (-₹3,600)
       │
       ▼
[Payroll Batch Calculated; Awaiting Disbursal Approval]""",
        transfers=[
            ("1", "Payroll UI", "Payroll API", "month=8, year=2026", "INSERT", "Initiate monthly salary calculation run"),
            ("2", "Payroll Engine", "payroll_batches", "month, year, status='calculated', total_net_amount", "INSERT", "Create monthly batch tracking record"),
            ("3", "Payroll Engine", "payslips table", "batch_id, employee_id, gross, deductions, net", "INSERT", "Generate official individual employee payslip"),
            ("4", "Payroll Engine", "payslip_items table", "payslip_id, component_id, amount, is_deduction", "INSERT", "Store granular earning/deduction line breakdown")
        ],
        tables=[
            ("payroll_batches", "Monthly payroll run header", "id (BigInt)", "month, year, status, total_gross, total_net", "school_id -> schools.id", "Monthly payroll runs", "Header entity tracking state from calculated to disbursed"),
            ("payslips", "Employee monthly payslip", "id (BigInt)", "batch_id, employee_id, gross_amount, net_amount", "batch_id -> payroll_batches.id, employee_id -> employees.id", "Individual salary slips", "Stores net payable salary and disbursal status"),
            ("payslip_items", "Payslip line breakdown", "id (BigInt)", "payslip_id, component_name, amount, type", "payslip_id -> payslips.id", "Component breakdown (EPF, HRA, etc.)", "Itemizes every statutory deduction and earning")
        ],
        lifecycle="<strong>State Machine:</strong> Batch starts in <code>calculated</code> status. The Bursar can review numbers or recalculate. Once verified, clicking 'Disburse' transitions batch status to <code>disbursed</code>, locks all payslips from editing, stamps <code>disbursed_at = NOW()</code>, and generates the bank disbursement CSV file.",
        example="Payroll for August 2026 is run for 18 staff. Total gross ₹720,000; total deductions ₹86,400 (EPF, ESI, TDS); total net payable ₹633,600. Teacher Vikram Singh receives payslip #14 with Basic ₹32,000, DA ₹8,000, HRA ₹10,000, EPF ₹3,840, Net ₹46,160."
    )

    # --- 12.2 Teacher Leave & 100% Substitution Coverage Gate ---
    content += render_workflow(
        wf_id="12.2",
        title="Teacher Leave Review, Free Teacher Selector & 100% Substitution Coverage Gate",
        overview={
            "real_life": "A teacher applies for leave via their mobile app. The Vice Principal reviews the leave queue on the web console and must ensure all classroom periods are covered before approving.",
            "actor": "Vice Principal / Timetable In-Charge.",
            "trigger": "Opening <code>/staff-leave</code> to process a pending teacher leave request.",
            "problem": "Leaving classrooms unattended during teacher absences and preventing faculty double-booking.",
            "outcome": "Admin selects free teachers for all conflicting periods. The system strictly forbids approval until 100% of periods are substituted. Upon approval, temporary substitutions activate and notifications dispatch."
        },
        steps=[
            "<strong>Leave Application:</strong> Teacher applies for leave from Mobile App (<code>/teacher/leave</code>). Request created in <code>staff_leave_requests</code> with status <code>pending</code>.",
            "<strong>Admin Queue Triage:</strong> Admin visits <code>/staff-leave</code>. Backend identifies 2 conflicting classroom periods on the requested leave date from <code>timetable_slots</code>.",
            "<strong>Substitution Locked Gate:</strong> Frontend renders 'Approve Leave' button in a strictly <strong>LOCKED (disabled)</strong> state with indicator: <em>'Coverage: 0% — All periods must be assigned before approval'</em>.",
            "<strong>Free Teacher Discovery:</strong> Admin clicks 'Assign Substitute' for Period 2 (Class 10-A Maths). Backend calculates which teachers have NO timetable assignment during that specific period on that day.",
            "<strong>Substitution Assignment:</strong> Admin selects free teacher (e.g. TCH004 Sunita Rao). System writes temporary row into <code>substitutions</code> table with status <code>draft</code>.",
            "<strong>100% Gate Unlocking:</strong> Once Period 2 and Period 5 are both covered (100% coverage achieved), the 'Approve Leave' button turns green and unlocks.",
            "<strong>Approval Commitment:</strong> Admin clicks 'Approve Leave'. System sets <code>staff_leave_requests.status = 'approved'</code>, promotes substitutions to <code>active</code>, and dispatches in-app notifications to both teachers via <code>in_app_notifications</code>.",
            "<strong>Rejection Purge Branch:</strong> If Admin clicks 'Reject Leave', system prompts for a mandatory rejection reason, sets status to <code>rejected</code>, and immediately hard-deletes all draft substitutions.",
            "<strong>Final Output:</strong> Zero unattended classrooms; timetable queries on that date transparently route to the substitute teacher."
        ],
        diagram="""[Teacher Mobile App] ──► [POST /api/v1/teacher/leave/apply] ──► [INSERT] staff_leave_requests (pending)
                                                                             │
                                                                             ▼
[Admin Console: /staff-leave] ◄──────────────────────────────────────────────┘
       │
       ├─► [READ] timetable_slots ───────────► Detect 2 conflicting periods for applicant
       │
       ├─► [GATE CHECK] ─────────────────────► 0% Coverage -> APPROVE BUTTON LOCKED
       │
       ├─► [READ] free_teachers API ─────────► Filter teachers with no timetable entry in Period 2
       │
       ├─► [INSERT] substitutions ───────────► Assign TCH004 for Period 2; TCH005 for Period 5
       │
       ├─► [GATE CHECK] ─────────────────────► 100% Coverage Reached -> APPROVE BUTTON UNLOCKED!
       │
       ▼ (Admin Clicks 'Approve Leave')
[Leave Approval Service]
       │
       ├─► [UPDATE] staff_leave_requests ────► Set status = 'approved', approved_by = user.id
       ├─► [UPDATE] substitutions ───────────► Set status = 'active'
       └─► [INSERT] in_app_notifications ────► Send duty alerts to TCH004 and TCH005
       │
       ▼
[Classrooms 100% Covered; Substitutes Notified on Mobile]""",
        transfers=[
            ("1", "Mobile Faculty App", "Leave API", "start_date, end_date, reason", "INSERT", "Teacher submits personal leave request"),
            ("2", "Timetable Service", "timetable_slots", "employee_id, day_of_week", "READ", "Identify which classroom periods will be vacant"),
            ("3", "Admin Console", "substitutions table", "leave_request_id, slot_id, substitute_id", "INSERT", "Assign temporary relief faculty to timetable slots"),
            ("4", "Admin Console", "staff_leave_requests", "status='approved', approved_at", "UPDATE", "Formally grant teacher leave"),
            ("5", "Notification Service", "in_app_notifications", "user_id, title, message, link", "INSERT", "Alert substitute teachers of assigned relief periods")
        ],
        tables=[
            ("staff_leave_requests", "Teacher leave applications", "id (BigInt)", "employee_id, start_date, end_date, status, reason", "employee_id -> employees.id", "Faculty leave records", "Tracks leave application state (pending, approved, rejected)"),
            ("substitutions", "Temporary relief assignments", "id (BigInt)", "leave_request_id, timetable_slot_id, substitute_teacher_id, date", "leave_request_id -> staff_leave_requests.id, sub_id -> employees.id", "Substitution duties", "Links vacant timetable slot to relief faculty"),
            ("in_app_notifications", "System alerts vault", "id (BigInt)", "user_id, title, message, is_read, notification_type", "user_id -> users.id", "In-app mobile/web notifications", "Delivers substitution duty alerts to relief teachers")
        ],
        lifecycle="<strong>Automatic Substitution Scope & Expiry:</strong> <code>substitutions</code> records have an explicit date scope (<code>date</code>). The master <code>timetable_slots</code> table is NEVER modified! Daily timetable views join <code>substitutions</code> for the specific query date. When the leave ends, the original teacher is automatically restored without any cleanup script.",
        example="Teacher Vikram Singh (TCH003) applies for leave on 18 Sep 2026. He has Period 2 (10-A Maths) and Period 5 (9-B Maths). Vice Principal assigns TCH004 Sunita Rao to Period 2 and TCH005 Amit Patel to Period 5. Coverage hits 100%; leave is approved; Sunita and Amit receive instant push notifications with their relief duties."
    )

    # --- 13.3 Teacher Recruitment & 1-Click Onboarding ---
    content += render_workflow(
        wf_id="13.3",
        title="Teacher Recruitment Pipeline, Offer Management & 1-Click Faculty Onboarding",
        overview={
            "real_life": "The Principal manages faculty hiring from job application, shortlisting, and formal offer letters through to officially onboarding the candidate as a recognized school teacher.",
            "actor": "Principal / HR Manager at <code>/recruitment</code>.",
            "trigger": "Clicking 'Onboard Candidate' on an applicant who has accepted their formal job offer.",
            "problem": "Manual data entry to create user logins, staff numbers, and department profiles for newly hired teachers causes credential errors and delays.",
            "outcome": "Candidate record updated to <code>hired</code>; new <code>users</code> account created; new <code>employees</code> record generated with automatic sequential staff code (e.g. <code>TCH014</code>)."
        },
        steps=[
            "<strong>Candidate Intake:</strong> Candidate profile created in <code>candidates</code> table via intake form or online portal (status <code>applied</code>).",
            "<strong>Review & Shortlisting:</strong> Admin reviews resume, schedules interview, and advances candidate to <code>shortlisted</code>.",
            "<strong>Job Offer Issuance:</strong> Admin clicks 'Issue Offer'; specifies designation ('Senior TGT Science'), department ('Science'), joining date, and offered salary. System writes to <code>candidate_offers</code> table and updates candidate status to <code>offered</code>.",
            "<strong>Candidate Acceptance:</strong> Candidate signs offer; status advances to <code>accepted</code>.",
            "<strong>1-Click Onboarding Trigger:</strong> Admin clicks 'Onboard as Staff' on <code>/recruitment</code>.",
            "<strong>Atomic Onboarding Transaction:</strong> Backend opens database transaction in <code>services/recruitment.py</code>.",
            "<strong>User Account Provisioning:</strong> Inserts parent row in <code>users</code> table with candidate's email, full name, and temporary password hash.",
            "<strong>Staff Code Generation:</strong> Generates next unique staff code (e.g. <code>TCH014</code>) via <code>number_sequences</code> or table max query.",
            "<strong>Employee Master Insertion:</strong> Inserts row into <code>employees</code> referencing <code>users.id</code>, with designation, joining date, and department.",
            "<strong>RBAC Role Assignment:</strong> Links user to 'Teacher' role in <code>user_roles</code>.",
            "<strong>Candidate State Closure:</strong> Updates <code>candidates.status = 'hired'</code> and records created <code>employee_id</code>.",
            "<strong>Final Output:</strong> New teacher appears immediately in <code>/teachers</code> directory and becomes available for timetable and class assignment."
        ],
        diagram="""[Principal Recruitment Screen (/recruitment)]
       │
       ▼ (POST /admin/recruitment/candidates/{id}/onboard)
[Recruitment Onboarding Service (app/services/recruitment.py)]
       │
       ├─► [READ] candidates & candidate_offers ──► Verify candidate accepted offer
       │
       ├─► [INSERT] users ────────────────────────► Create user account (email, name, hashed_password)
       │         │
       │         ▼ (user.id)
       ├─► [GENERATE] employee_code ──────────────► Generate unique staff number (TCH014)
       │         │
       │         ▼
       ├─► [INSERT] employees ────────────────────► Create employee record (TCH014, Science Dept)
       │         │
       │         ▼
       ├─► [INSERT] user_roles ───────────────────► Assign 'Teacher' RBAC role
       │         │
       │         ▼
       └─► [UPDATE] candidates ───────────────────► Set status = 'hired', employee_id = employees.id
       │
       ▼
[Faculty Fully Provisioned in Staff Roster & Systems]""",
        transfers=[
            ("1", "Recruitment UI", "Recruitment API", "candidate_id, department_id, joining_date", "INSERT", "Trigger atomic faculty onboarding"),
            ("2", "Onboarding Service", "users table", "email, full_name, default_password_hash", "INSERT", "Create system user principal"),
            ("3", "Onboarding Service", "employees table", "user_id, employee_code, designation, department_id", "INSERT", "Create official employee employment record"),
            ("4", "Onboarding Service", "user_roles table", "user_id, role_id='teacher'", "LINK", "Grant teacher application access rights"),
            ("5", "Onboarding Service", "candidates table", "status='hired', employee_id", "UPDATE", "Complete hiring lifecycle")
        ],
        tables=[
            ("candidates", "Job applicant pipeline", "id (BigInt)", "first_name, email, status, position_applied, employee_id", "school_id -> schools.id, employee_id -> employees.id", "Job applicant records (2 rows)", "Tracks applicant from application to hiring"),
            ("candidate_offers", "Formal job offers", "id (BigInt)", "candidate_id, designation, offered_salary, status", "candidate_id -> candidates.id", "Job offer parameters (2 rows)", "Stores contractual terms of offer"),
            ("employees", "Staff master catalog", "id (BigInt)", "user_id, employee_code, designation, department_id, status", "user_id -> users.id, department_id -> departments.id", "Official staff records (18 rows)", "Primary HR entity representing active faculty")
        ],
        lifecycle="<strong>Unique Employee Code Invariant:</strong> <code>employees.employee_code</code> (e.g. <code>TCH014</code>) has a unique constraint per school (<code>uq_employee_code</code>). It is never reassigned or deleted, even if the faculty member resigns, ensuring historical integrity in past attendance and exam registers.",
        example="Candidate 'Meenakshi Sundaram' applies for PGT Chemistry. Principal issues offer for ₹45,000/mo. Candidate accepts. Principal clicks 'Onboard'. System generates staff code <code>TCH014</code>, creates user login, inserts <code>employees</code> record, assigns Teacher role, and updates candidate status to <code>hired</code>."
    )

    return content
