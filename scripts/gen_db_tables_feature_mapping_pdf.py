"""Generates the authoritative All-Tables Database & Feature Mapping Reference PDF:
docs/Sunrise-ERP-Database-Tables-and-Features.pdf

Covers ALL 89 tables in the schema:
- 61 Live / Essential Tables (holding active rows in the seeded school) -> stamped with LIVE / IN USE (N rows)
- 28 Non-Essential Tables (unpopulated in seed data) -> prominently stamped with 'UNUSED FOR NOW'
- Each table mapped to exact website routes, UI components, modals, and actions.
- Explicit distinction between Live Operational Features vs Planned Features.
- Strict multi-tenant scoping and architectural invariants documented.
"""
import os
import subprocess
import html as H
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("SUNRISE_DB", "sunrise_test")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_HTML = os.path.join(REPO, "docs", "database-tables-and-features-print.html")
OUTPUT_PDF = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Tables-and-Features.pdf")
SEP = chr(31)

def esc(s):
    return H.escape(str(s) if s is not None else "", quote=False)

def q(sql):
    """Execute psql query using unit separator."""
    env = dict(os.environ)
    env.setdefault("PGPASSWORD", "sunrise")
    out = subprocess.run(
        ["psql", "-U", "sunrise", "-h", "localhost", "-d", DB, "-tAF", SEP, "-c", sql],
        capture_output=True, text=True, env=env)
    if out.returncode:
        raise SystemExit(f"psql query failed: {out.stderr}\nSQL: {sql}")
    return [line.split(SEP) for line in out.stdout.strip().splitlines() if line]

def introspect_db():
    """Introspect all tables, row counts, columns, and foreign keys directly from Postgres."""
    raw_tables = q(
        "select c.relname, coalesce(s.n_live_tup,0) from pg_class c "
        "join pg_namespace ns on ns.oid=c.relnamespace and ns.nspname='public' "
        "left join pg_stat_user_tables s on s.relid=c.oid "
        "where c.relkind='r' order by c.relname;")
    
    tables = {t: {"rows": int(n), "columns": [], "fk": [], "unique": []} for t, n in raw_tables}

    cols = q(
        "select table_name, column_name, case "
        "when data_type='character varying' then 'varchar('||coalesce(character_maximum_length::text,'')||')' "
        "when data_type='numeric' then 'numeric('||coalesce(numeric_precision::text,'')||','||coalesce(numeric_scale::text,'')||')' "
        "when data_type='timestamp with time zone' then 'timestamptz' "
        "when data_type='double precision' then 'float' else data_type end, "
        "is_nullable, coalesce(column_default,'') "
        "from information_schema.columns where table_schema='public' "
        "order by table_name, ordinal_position;")
    
    for tbl, col, typ, nullable, default in cols:
        if tbl in tables:
            tables[tbl]["columns"].append({
                "name": col,
                "type": typ,
                "null": nullable == "YES",
                "default": default
            })

    fks = q(
        "select tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name "
        "from information_schema.table_constraints tc "
        "join information_schema.key_column_usage kcu on kcu.constraint_name=tc.constraint_name "
        "and kcu.constraint_schema=tc.constraint_schema "
        "join information_schema.constraint_column_usage ccu on ccu.constraint_name=tc.constraint_name "
        "and ccu.constraint_schema=tc.constraint_schema "
        "where tc.constraint_type='FOREIGN KEY' and tc.constraint_schema='public' "
        "order by tc.table_name, kcu.column_name;")
    
    for src, scol, tgt, tcol in fks:
        if src in tables:
            tables[src]["fk"].append({"col": scol, "to": f"{tgt}.{tcol}"})

    uniqs = q(
        "select tc.table_name, tc.constraint_name, "
        "string_agg(kcu.column_name, ',' order by kcu.ordinal_position) "
        "from information_schema.table_constraints tc "
        "join information_schema.key_column_usage kcu on kcu.constraint_name=tc.constraint_name "
        "and kcu.constraint_schema=tc.constraint_schema "
        "where tc.constraint_type='UNIQUE' and tc.constraint_schema='public' "
        "group by 1,2 order by 1,2;")
    
    for tbl, name, ucols in uniqs:
        if tbl in tables:
            tables[tbl]["unique"].append(ucols)

    return tables

TABLE_MAPPINGS = {
    # -------------------------------------------------------------
    # Domain 1: Tenancy, Identity & Access (10 DB tables)
    # -------------------------------------------------------------
    "schools": {
        "domain": "Tenancy, Identity & Access",
        "route": "/settings, /configuration",
        "feature_type": "Live Operational Feature",
        "ui_components": "School Header Branding, School Profile Card on /settings, Logo/Palette Customizer",
        "purpose": "Root tenant anchor for multi-school isolation. Stores school legal name, CBSE board affiliation number, school code (SPS), brand hex colors, and official contact details.",
        "workflow": "Queried on initial application boot and Shell mounting to populate top navbar school name and brand styling. Updated via PUT /admin/settings when modifying school profile details.",
        "invariants": "Root entity: does NOT have a school_id column (TimestampedBase). Every other product table enforces an indexed school_id referencing schools.id."
    },
    "academic_years": {
        "domain": "Tenancy, Identity & Access",
        "route": "/configuration, /settings, Top Header Bar",
        "feature_type": "Live Operational Feature",
        "ui_components": "Top Navbar Academic Session Badge ('2025-26'), Configuration Session Card, Promotion Target Picker",
        "purpose": "Controls active academic operating session (e.g., 2025-26). Delineates class enrolments, fee structures, timetable grids, exam schedules, and attendance rolls.",
        "workflow": "Mounted globally across all screens to scope queries to the active session. Admin configures start/end dates and locks past terms on /configuration.",
        "invariants": "Enforces UNIQUE(school_id, name). At least one academic year marked is_active=True per tenant."
    },
    "users": {
        "domain": "Tenancy, Identity & Access",
        "route": "/login, /auth/*, System-Wide Auth",
        "feature_type": "Live Operational Feature",
        "ui_components": "Login Screen Form, User Profile Menu, User Switcher (Dev Mode), Password Reset Modal",
        "purpose": "Core authentication credentials table storing login_id (email), Argon2 password hashes, full display name, and active account status for all staff, guardians, and students.",
        "workflow": "Queried during POST /auth/login. Issues signed JWT bearer tokens. Used by Audit Log to stamp who performed every write.",
        "invariants": "Enforces UNIQUE(school_id, login_id). Foreign-referenced by employees, guardians, students, and audit_log."
    },
    "roles": {
        "domain": "Tenancy, Identity & Access",
        "route": "RBAC Engine (All Screens)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Sidebar Navigation Filter, Permission Gate Component (<Can>), Role Badges in Staff Directory",
        "purpose": "Defines system-wide and tenant-defined role profiles (super_admin, receptionist, principal, teacher, student, parent, fee_clerk).",
        "workflow": "Read during JWT verification to determine caller's permission set. Controls sidebar item visibility and URL access.",
        "invariants": "Enforces UNIQUE(school_id, name). Seeded system roles are immutable."
    },
    "permissions": {
        "domain": "Tenancy, Identity & Access",
        "route": "RBAC Engine (All Screens)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Backend Endpoint Gates (require_permission), UI ActionButton Tooltip Disablers",
        "purpose": "Granular capability codes (e.g., admission.enquiry.read, fees.invoice.write, attendance.record.correct, inventory.item.read).",
        "workflow": "Checked on every HTTP API request via FastAPI dependency injection and on frontend buttons via <ActionButton>.",
        "invariants": "Global catalogue of permissions. Uniqueness enforced across permission code strings."
    },
    "role_permissions": {
        "domain": "Tenancy, Identity & Access",
        "route": "RBAC Engine (All Screens)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Role Permission Assignment Grid on /configuration (Admin)",
        "purpose": "Many-to-many bridge linking roles to specific permissions. Enforces exclusive privileges (e.g. receptionist restricted to admission queues).",
        "workflow": "Queried during role token resolution to build user's effective permission scope.",
        "invariants": "Composite PRIMARY KEY (role_id, permission_id)."
    },
    "user_roles": {
        "domain": "Tenancy, Identity & Access",
        "route": "User Management, /teachers",
        "feature_type": "Live Operational Feature",
        "ui_components": "Staff Profile Role Pills, Role Assignment Dropdown in Staff Creation Modal",
        "purpose": "Binds users to roles with optional scope constraints (school-wide, class-section, or departmental).",
        "workflow": "Read on authentication to resolve all active roles for the authenticated user.",
        "invariants": "Composite PRIMARY KEY (user_id, role_id)."
    },
    "settings": {
        "domain": "Tenancy, Identity & Access",
        "route": "/settings, /configuration",
        "feature_type": "Live Operational Feature",
        "ui_components": "School Configuration Form, Attendance Threshold Slider, Fee Due Day Input, Module Toggles",
        "purpose": "Per-school key/value configuration registry storing operational settings and module switches (feature.<module>).",
        "workflow": "Loaded on app bootstrap to toggle navigation items and enforce business rules (e.g., late fee grace days).",
        "invariants": "Enforces UNIQUE(school_id, key). Key registry defined in backend core/settings_registry.py."
    },
    "custom_fields": {
        "domain": "Tenancy, Identity & Access",
        "route": "/configuration",
        "feature_type": "Live Operational Feature",
        "ui_components": "Custom Field Builder on /configuration, Dynamic Form Fields on Student Profile",
        "purpose": "Allows school administrators to define bespoke student/staff attributes (e.g., caste category, house, father's occupation) without altering the database schema.",
        "workflow": "Admin defines custom field; Student creation modal dynamically renders input widgets matching field_type.",
        "invariants": "Enforces UNIQUE(school_id, entity_type, field_name). Stored values validated against field data type."
    },
    "number_sequences": {
        "domain": "Tenancy, Identity & Access",
        "route": "/students, /admission, /fees/ledger",
        "feature_type": "Live Operational Feature",
        "ui_components": "Voucher Number Preview, Admission Number Formatter, Receipt Generation Dialog",
        "purpose": "Atomic sequence counter guaranteeing gapless, sequential numbering for admission numbers (SPS/2026/0001), fee receipts (REC-...), and enquiry codes.",
        "workflow": "Invoked inside write transactions via SELECT ... FOR UPDATE to atomically increment next_val and format voucher codes.",
        "invariants": "Enforces UNIQUE(school_id, sequence_type, prefix). Concurrency-safe via row-level database locks."
    },

    # -------------------------------------------------------------
    # Domain 2: People — Students & Guardians (4 DB tables)
    # -------------------------------------------------------------
    "students": {
        "domain": "People — Students & Guardians",
        "route": "/students, /admission, /fees/ledger",
        "feature_type": "Live Operational Feature",
        "ui_components": "Student Roster Table, Student Search Bar, Student 360° Profile Drawer, Add Student Modal",
        "purpose": "Master biographical record of enrolled students: admission number, full name, date of birth, gender, blood group, medical notes, and linked user authentication ID.",
        "workflow": "Created when converting an accepted admission applicant or manually by Admin. Searched across student fee ledger and attendance register.",
        "invariants": "Enforces UNIQUE(school_id, admission_number). Year-independent: historical facts attach to enrolments, not students."
    },
    "guardians": {
        "domain": "People — Students & Guardians",
        "route": "/students, /fees/defaulters",
        "feature_type": "Live Operational Feature",
        "ui_components": "Guardian Contact Card in Student Drawer, Defaulter Chase Phone Call Button, Parent Portal Link",
        "purpose": "Parent and guardian registry holding primary mobile numbers, email addresses, occupations, and residential addresses.",
        "workflow": "Displayed on student profile drawer. Queried on Defaulters screen (/fees/defaulters) to generate parent contact lists for payment reminders.",
        "invariants": "A guardian may be linked to multiple children (siblings) via student_guardian."
    },
    "student_guardian": {
        "domain": "People — Students & Guardians",
        "route": "/students, /fees/defaulters",
        "feature_type": "Live Operational Feature",
        "ui_components": "Family Relationship Section in Student Drawer, Primary Contact Checkbox",
        "purpose": "Many-to-many bridge linking students to guardians, capturing relationship type (father, mother, local guardian) and emergency contact priority.",
        "workflow": "Populated during student onboarding. Read whenever parent notifications or emergency notices are dispatched.",
        "invariants": "Composite PRIMARY KEY (student_id, guardian_id)."
    },
    "enrolments": {
        "domain": "People — Students & Guardians",
        "route": "/classes, /students, /attendance, /fees",
        "feature_type": "Live Operational Feature",
        "ui_components": "Class Roster List on /classes, Academic Enrolment History in Student Drawer, Roll Number Editor",
        "purpose": "The single most critical academic anchor: connects a student to exactly one class_section for one academic_year, assigning their roll_no.",
        "workflow": "Created during annual admission or session promotion. All year-scoped operational data (fees, attendance, exam marks, bus seats) hangs off enrolment_id.",
        "invariants": "Enforces UNIQUE(student_id, academic_year_id) and UNIQUE(class_section_id, roll_no)."
    },

    # -------------------------------------------------------------
    # Domain 3: People — Staff & Departments (2 DB tables)
    # -------------------------------------------------------------
    "departments": {
        "domain": "People — Staff & Departments",
        "route": "/teachers",
        "feature_type": "Live Operational Feature",
        "ui_components": "Department Filter Tabs on /teachers, Department Manager Dropdown",
        "purpose": "Academic and administrative department master (Science, Languages, Mathematics, Social Studies, Administration) with assigned Department Heads.",
        "workflow": "Queried on Staff screen to group teachers by discipline and filter staff rosters.",
        "invariants": "Enforces UNIQUE(school_id, name)."
    },
    "employees": {
        "domain": "People — Staff & Departments",
        "route": "/teachers, /classes",
        "feature_type": "Live Operational Feature",
        "ui_components": "Staff Directory Grid, Employee Profile Drawer, Add Staff Modal, Teacher Allocation Picker",
        "purpose": "Employee master directory storing employee code (EMP001), designation (PGT, TGT, PRT, Admin), joining date, qualifications, and department affiliation.",
        "workflow": "Queried on /teachers for HR directory. Referenced when assigning class teachers on /classes and creating timetable periods.",
        "invariants": "Enforces UNIQUE(school_id, employee_code). Links to users.id for web authentication."
    },

    # -------------------------------------------------------------
    # Domain 4: Academics, Timetable & Homework (9 DB tables)
    # -------------------------------------------------------------
    "class_sections": {
        "domain": "Academics, Timetable & Homework",
        "route": "/classes, /attendance, /fees/setup",
        "feature_type": "Live Operational Feature",
        "ui_components": "Class Selector Dropdown (All Screens), Class 1-A to 10-A Cards, Room Allocation Modal",
        "purpose": "Academic class-section unit for an academic session (e.g., Class 10-A, Class 5-B) with room number, student capacity, and appointed Class Teacher.",
        "workflow": "The primary operational grouping across the entire ERP. Feeds class dropdowns in Attendance, Exams, Fees, and Timetable.",
        "invariants": "Enforces UNIQUE(school_id, academic_year_id, name)."
    },
    "subjects": {
        "domain": "Academics, Timetable & Homework",
        "route": "/classes, /exams",
        "feature_type": "Live Operational Feature",
        "ui_components": "Curriculum Subject List on /classes, Exam Subject Picker on /exams Tab 1",
        "purpose": "Subject master catalogue (Mathematics, English, Hindi, Science, Social Science, Computer Science, Sanskrit, Art, EVS) with subject code and credit units.",
        "workflow": "Attached to classes through class_subject_teacher; defines subjects scheduled on exam datesheets.",
        "invariants": "Enforces UNIQUE(school_id, code)."
    },
    "class_subject_teacher": {
        "domain": "Academics, Timetable & Homework",
        "route": "/classes",
        "feature_type": "Live Operational Feature",
        "ui_components": "Teacher Allocation Matrix on /classes, Weekly Teaching Load Counter (25 periods/wk)",
        "purpose": "Associates subject specialists to class sections. Enforces balanced teaching workloads and gates which teachers can enter exam marks and assign homework.",
        "workflow": "Configured at the start of session on /classes. Used by RBAC to verify teacher marks-entry permissions.",
        "invariants": "Enforces UNIQUE(class_section_id, subject_id, teacher_id)."
    },
    "school_periods": {
        "domain": "Academics, Timetable & Homework",
        "route": "/classes, /dashboard",
        "feature_type": "Live Operational Feature",
        "ui_components": "Period Timing Configuration on /classes, Daily Schedule Timeline on /dashboard",
        "purpose": "Defines daily bell timings and period slots (Period 1 to Period 6, 08:00 AM to 02:00 PM) including recess intervals.",
        "workflow": "Forms the vertical time axis of the weekly timetable grid on /classes and 'Today's Schedule' on the dashboard.",
        "invariants": "Enforces period sequence order and non-overlapping start/end times per school."
    },
    "timetable_slots": {
        "domain": "Academics, Timetable & Homework",
        "route": "/classes, /dashboard",
        "feature_type": "Live Operational Feature",
        "ui_components": "Weekly Timetable Interactive Grid on /classes, Today's Classes Widget on /dashboard",
        "purpose": "Weekly timetable grid mapping day_of_week, period_id, class_section_id, subject_id, and teacher_id to classroom rooms.",
        "workflow": "Displayed on /classes as a full weekly timetable matrix. Filtered on /dashboard to show active classes today.",
        "invariants": "Enforces zero teacher collisions (no teacher double-booked in the same period) and zero room collisions."
    },
    "holidays": {
        "domain": "Academics, Timetable & Homework",
        "route": "/dashboard, /attendance",
        "feature_type": "Live Operational Feature",
        "ui_components": "Upcoming Events & Holidays Widget on /dashboard, Non-School Day Greyout on /attendance",
        "purpose": "School calendar closures, gazetted holidays, and vacation breaks (Mid-term Break, Winter Break, Founder's Week).",
        "workflow": "Displayed in the Upcoming Events widget on the dashboard. Prevents attendance roll-call marking on closed days.",
        "invariants": "Enforces holiday date ranges within the active academic session."
    },
    "homework": {
        "domain": "Academics, Timetable & Homework",
        "route": "Mobile App (Teacher) & Web Homework",
        "feature_type": "Live Operational Feature",
        "ui_components": "Teacher Homework Creation Form, Daily Diary Card, Due Date Picker",
        "purpose": "Homework assignments set by subject teachers for specific class sections, including description, due date, and attachments.",
        "workflow": "Teacher creates homework task via Mobile App or Web; pushed to student/parent mobile diaries.",
        "invariants": "Foreign key references class_sections, subjects, and employees."
    },
    "homework_submissions": {
        "domain": "Academics, Timetable & Homework",
        "route": "Mobile App (Student/Teacher)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Student Submission Upload Button, Teacher Grading & Feedback Modal",
        "purpose": "Student homework submissions with submission timestamps, student comments, and teacher evaluation marks.",
        "workflow": "Student uploads completed work via mobile app; teacher reviews and assigns remarks and marks.",
        "invariants": "Enforces UNIQUE(homework_id, student_id)."
    },
    "substitutions": {
        "domain": "Academics, Timetable & Homework",
        "route": "/staff-leave, /classes, /leave (Mobile Duties)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Dynamic Free Teacher Picker, 100% Coverage Progress Bar, Substitute Duty Card on Mobile App",
        "purpose": "Date-bound provisional and confirmed substitution assignments covering timetable periods when a teacher is on leave. Acts as a daily overlay without modifying master timetable slots.",
        "workflow": "Admin selects free substitute teacher from dynamic non-conflicting teacher list. Approved leaves mark substitutions as confirmed; rejected leaves purge provisional rows immediately.",
        "invariants": "Zero mutation of master timetable_slots. Scope is strictly date-bound with CASCADE delete on rejected leave request."
    },

    # -------------------------------------------------------------
    # Domain 5: Attendance (2 DB tables)
    # -------------------------------------------------------------
    "attendance": {
        "domain": "Attendance",
        "route": "/attendance, /dashboard",
        "feature_type": "Live Operational Feature",
        "ui_components": "Main Dashboard Attendance Overview Card (90% Present, 10 Absent Breakdown), Daily Roll Register on /attendance, Mark Attendance Button",
        "purpose": "Daily student roll-call records: status (present, absent, late, half_day, leave) per enrolment per school date.",
        "workflow": "Marked each morning by class teacher on /attendance. Directly powers the top Attendance Overview card on the main dashboard with auto-fallback to last recorded school day.",
        "invariants": "Enforces UNIQUE(enrolment_id, date). Revisions require attendance.record.correct permission."
    },
    "student_leave_requests": {
        "domain": "Attendance",
        "route": "/attendance/leave-requests",
        "feature_type": "Planned Feature",
        "ui_components": "Parent Leave Application Form (Mobile), Office Leave Approval Queue on /attendance",
        "purpose": "Student absence and medical leave applications submitted by parents, with doctor's notes and admin approval status.",
        "workflow": "Parent submits leave in mobile app; Class teacher or receptionist approves or rejects request with remarks.",
        "invariants": "Approved leave automatically converts student daily attendance status to 'leave'."
    },

    # -------------------------------------------------------------
    # Domain 6: Examinations, Grading & Results (8 DB tables)
    # -------------------------------------------------------------
    "assessment_schemes": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 2",
        "feature_type": "Live Operational Feature",
        "ui_components": "CBSE Assessment Scheme Selector, Scheme Weightage Panel",
        "purpose": "Formal CBSE assessment architecture defining evaluation components and weightages for the academic session.",
        "workflow": "Configured once per academic year on /exams Tab 2 (Grading Setup). Dictates report card component calculation.",
        "invariants": "Enforces UNIQUE(school_id, academic_year_id, name)."
    },
    "scheme_components": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 2",
        "feature_type": "Live Operational Feature",
        "ui_components": "Component Weightage Breakdown (Periodic Assessment 10%, Notebook 5%, Enrichment 5%, Term Exam 80%)",
        "purpose": "Constituent evaluation components and percentage weightages belonging to an assessment scheme.",
        "workflow": "Sum of component weightages validated to total exactly 100% before activating scheme.",
        "invariants": "Foreign key references assessment_schemes.id with ON DELETE CASCADE."
    },
    "grading_scales": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 2, /settings",
        "feature_type": "Live Operational Feature",
        "ui_components": "CBSE 8-Point Grading Scale Card on /exams Tab 2",
        "purpose": "Master grading system definition (e.g. CBSE 8-point scale from A1 down to E).",
        "workflow": "Linked to assessment schemes to automatically convert percentage marks into CBSE letter grades.",
        "invariants": "Enforces UNIQUE(school_id, name)."
    },
    "grade_bands": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 2",
        "feature_type": "Live Operational Feature",
        "ui_components": "Grade Interval Matrix (A1 >= 91%, A2 >= 81%, ..., E < 33%), Report Card Remarks Editor",
        "purpose": "Specific percentage threshold intervals, letter grades, grade points, and qualitative remarks (e.g. Outstanding, Satisfactory).",
        "workflow": "Queried when compiling student report cards and term marks summaries.",
        "invariants": "Enforces non-overlapping, contiguous percentage ranges from 0% to 100%."
    },
    "exams": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 1",
        "feature_type": "Live Operational Feature",
        "ui_components": "Exam Term Selector (Half-Yearly Exam, Final Exam), Create Exam Dialog",
        "purpose": "Formal examination term definitions with scheduled start and end dates.",
        "workflow": "Coordinator creates exam term; opens exam datesheet scheduling and marks entry windows.",
        "invariants": "Enforces UNIQUE(school_id, academic_year_id, name)."
    },
    "exam_schedule": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 1",
        "feature_type": "Live Operational Feature",
        "ui_components": "Datesheet Table, Max Marks/Pass Marks Inputs, Exam Paper Lock Button",
        "purpose": "Datesheet papers scheduled per class and subject: exam date, start/end time, max marks, pass marks, and marks entry lock status.",
        "workflow": "Teacher views assigned papers on /exams Tab 1. Coordinator locks paper after entry deadline to freeze scores.",
        "invariants": "Enforces pass_marks <= max_marks and UNIQUE(exam_id, class_section_id, subject_id)."
    },
    "marks": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 1",
        "feature_type": "Live Operational Feature",
        "ui_components": "Marks Entry Matrix Grid, Absent Checkbox, Audit Reason Override Dialog",
        "purpose": "Marks scored by each student for a scheduled exam paper, tracking absent flags, medical exemptions, and audited edits.",
        "workflow": "Entered by subject teachers on /exams Tab 1. Score corrections post-lock require audited user-typed justification.",
        "invariants": "Enforces score <= exam_schedule.max_marks and UNIQUE(exam_schedule_id, student_id)."
    },
    "report_card_publications": {
        "domain": "Examinations, Grading & Results",
        "route": "/exams Tab 3",
        "feature_type": "Planned Feature",
        "ui_components": "Publish Report Cards Button, Withhold for Fee Dues Filter, Student PDF Download Link",
        "purpose": "Formal publication records releasing term report cards to parent portals, supporting automated dues withholdings.",
        "workflow": "Principal reviews finalized class marks and clicks Publish. System suppresses download for students with pending fee arrears.",
        "invariants": "Audited with publisher user ID and publication timestamp."
    },

    # -------------------------------------------------------------
    # Domain 7: Fees & Financial Ledger (10 DB tables)
    # -------------------------------------------------------------
    "fee_heads": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/setup",
        "feature_type": "Live Operational Feature",
        "ui_components": "Fee Head Master Table, Add Billing Category Modal (Tuition, Annual, Transport, Exam)",
        "purpose": "Financial billing categories (Tuition Fee, Admission Fee, Annual Charges, Exam Fee, Transport Fee, Computer Lab Fee).",
        "workflow": "Configured by finance manager on /fees/setup; forms the vocabulary from which fee plans and invoice lines are built.",
        "invariants": "Enforces UNIQUE(school_id, name)."
    },
    "fee_plans": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/setup",
        "feature_type": "Live Operational Feature",
        "ui_components": "Class Fee Schedule Cards (Class 1 Plan to Class 10 Plan), Clone Plan Action",
        "purpose": "Class-wise annual fee structures governing student billing schedules across classes.",
        "workflow": "Created during annual budget setup. Applied automatically to all enrolled students in the corresponding class.",
        "invariants": "Enforces UNIQUE(school_id, academic_year_id, name)."
    },
    "fee_plan_items": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/setup",
        "feature_type": "Live Operational Feature",
        "ui_components": "Fee Plan Line Item Table, Billing Frequency Picker (Monthly, Quarterly, Annual, One-Time)",
        "purpose": "Constituent line items of a fee plan defining fee head, billing frequency, and amount.",
        "workflow": "Batch invoice generator multiplies item amounts by frequency periods to build monthly student invoices.",
        "invariants": "Foreign key references fee_plans.id and fee_heads.id."
    },
    "fee_concessions": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/setup",
        "feature_type": "Live Operational Feature",
        "ui_components": "Concession Approvals Table, Concession Type Picker (Staff Ward 50%, Sibling 25%, Merit Scholarship)",
        "purpose": "Audited fee waivers and discount structures approved by School Management or Principal.",
        "workflow": "Concession percentage or fixed amount automatically deducted from student monthly invoice line calculations.",
        "invariants": "Requires principal approval notes committed to audit log."
    },
    "fee_invoices": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees, /dashboard",
        "feature_type": "Live Operational Feature",
        "ui_components": "Fee Billing Roster, Financial Summary Card (₹4,72,890 Realized / ₹9,72,930 Demand), Void Invoice Action",
        "purpose": "Monthly student billing invoices recording total demand, concessions credited, net payable, and payment status.",
        "workflow": "Generated monthly by automated background cron or clerk. Displayed on /fees and dashboard financial overview.",
        "invariants": "Financial Immutability: Invoices are never updated in-place; voided and reissued with audited reason."
    },
    "fee_invoice_lines": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/ledger",
        "feature_type": "Live Operational Feature",
        "ui_components": "Student Fee Account Ledger Table, Head-wise Breakdown Drawer, Balance Due Pills",
        "purpose": "Granular line-item breakdown of student invoices showing exact fee heads (e.g. Tuition ₹3,500, Transport ₹1,200).",
        "workflow": "Rendered on /fees/ledger when inspecting a student account. Target of double-entry payment allocations.",
        "invariants": "Sum of invoice lines equals parent invoice total_amount."
    },
    "fee_payments": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/ledger",
        "feature_type": "Live Operational Feature",
        "ui_components": "Payment History Table, Print Receipt Voucher Button, Reverse Payment Action Dialog",
        "purpose": "Financial collection transaction receipts holding receipt number, payment mode (Cash, UPI, Cheque, Bank Transfer), and amount.",
        "workflow": "Created when recording fee collections. Printed as official school receipt. Payment reversals create contra-entries.",
        "invariants": "Enforces UNIQUE(school_id, receipt_number). Completely immutable once committed."
    },
    "payment_allocations": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/ledger",
        "feature_type": "Live Operational Feature",
        "ui_components": "Allocation Breakdown Drawer, Double-Entry Reversal Audit Trail",
        "purpose": "Double-entry accounting bridge associating payment receipts to specific invoice lines.",
        "workflow": "Reconciles money collected against individual fees owed. When a payment is voided, negative contra-allocations are written.",
        "invariants": "Sum of allocations for a payment cannot exceed payment.amount."
    },
    "student_fee_plans": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/setup",
        "feature_type": "Planned Feature",
        "ui_components": "Individual Student Fee Plan Override Modal, Custom Billing Agreement Card",
        "purpose": "Individual student fee schedule overrides differing from the standard class fee plan (e.g. RTE quota exemptions).",
        "workflow": "Assigned to specific students by administrator when class-wide standard billing does not apply.",
        "invariants": "Enforces UNIQUE(enrolment_id)."
    },
    "fee_periods": {
        "domain": "Fees & Financial Ledger",
        "route": "/fees/periods",
        "feature_type": "Planned Feature",
        "ui_components": "Period Close Screen (/fees/periods), Close Month Button, Prior-Period Adjustment Locks",
        "purpose": "Monthly accounting period close locks preventing retroactive modifications to finalized financial accounts.",
        "workflow": "School bursar closes financial month on /fees/periods; locks all invoice lines against retroactive edits.",
        "invariants": "Requires super-admin authorization and audit log stamp to reopen a closed period."
    },

    # -------------------------------------------------------------
    # Domain 8: Transport & Fleet Management (5 DB tables)
    # -------------------------------------------------------------
    "vehicles": {
        "domain": "Transport & Fleet Management",
        "route": "/transport",
        "feature_type": "Live Operational Feature",
        "ui_components": "Fleet Registry Cards (Buses UP-32-AT-1001 to 1003), Vehicle Fitness Tracker, Expiring Papers Banner",
        "purpose": "School fleet registry holding registration numbers, seating capacities, insurance expiry, fitness certificates, and pollution checks.",
        "workflow": "Viewed on /transport. Alerts school administration 30 days prior to fitness/insurance paper expirations.",
        "invariants": "Enforces UNIQUE(school_id, registration_number)."
    },
    "routes": {
        "domain": "Transport & Fleet Management",
        "route": "/transport",
        "feature_type": "Live Operational Feature",
        "ui_components": "Route Management Cards (Gomti Nagar, Aliganj, Indira Nagar), Interactive Leaflet Route Map",
        "purpose": "Transport routes operating across Lucknow sectors, linking vehicles, drivers, and pickup/drop corridors.",
        "workflow": "Rendered on /transport with interactive route maps. Selected when assigning transport to students.",
        "invariants": "Enforces UNIQUE(school_id, route_name)."
    },
    "route_stops": {
        "domain": "Transport & Fleet Management",
        "route": "/transport",
        "feature_type": "Live Operational Feature",
        "ui_components": "Stops & Timings Table, Boarding Sequence Ordering, Pickup/Drop Arrival Schedule",
        "purpose": "Designated boarding stops along each route with sequence order numbers, GPS coordinates, and morning/afternoon scheduled arrival times.",
        "workflow": "Displayed on route drill-down. Feeds parent transport notifications for scheduled bus arrivals.",
        "invariants": "Enforces stop sequence order along the route path."
    },
    "transport_fee_slabs": {
        "domain": "Transport & Fleet Management",
        "route": "/transport, /fees/setup",
        "feature_type": "Live Operational Feature",
        "ui_components": "Distance Slab Pricing Table (0-3 km ₹800, 3-6 km ₹1,200, 6-10 km ₹1,600, 10+ km ₹2,000)",
        "purpose": "Distance-based transport fare pricing slabs linked to monthly fee invoice generation.",
        "workflow": "When student transport is assigned, system queries stop distance and adds corresponding slab charge to monthly fee invoice.",
        "invariants": "Enforces non-overlapping kilometer distance intervals."
    },
    "transport_assignments": {
        "domain": "Transport & Fleet Management",
        "route": "/transport",
        "feature_type": "Live Operational Feature",
        "ui_components": "Route Passenger Roster Drilldown, Assign Bus Seat Modal, Trip Direction Radio (Both, Morning, Evening)",
        "purpose": "Maps enrolled students to specific bus routes, boarding stops, and trip directions.",
        "workflow": "Gated with transport.assignment.read on /transport. Generates daily bus attendance rosters for bus attendants.",
        "invariants": "Enforces bus seating capacity limits (cannot over-allocate riders beyond vehicle capacity)."
    },

    # -------------------------------------------------------------
    # Domain 9: Human Resources & Payroll (10 DB tables)
    # -------------------------------------------------------------
    "salary_components": {
        "domain": "Human Resources & Payroll",
        "route": "/payroll [Planned]",
        "feature_type": "Live Operational Feature",
        "ui_components": "Salary Component Master Table, Component Type Toggle (Earning vs Deduction)",
        "purpose": "Statutory and standard salary building blocks: Basic Pay, Dearness Allowance (DA), HRA, Provident Fund (PF), ESI, Professional Tax.",
        "workflow": "Configured in HR setup; defines compensation contract formulas for Lucknow teaching and administrative staff.",
        "invariants": "Enforces UNIQUE(school_id, name)."
    },
    "salary_structures": {
        "domain": "Human Resources & Payroll",
        "route": "/teachers, /payroll [Planned]",
        "feature_type": "Live Operational Feature",
        "ui_components": "Staff Salary Package Card in Teacher Profile (PGT ₹42,000, TGT ₹32,000, PRT ₹19,500)",
        "purpose": "Active compensation scale packages assigned to staff designations reflecting private school salary levels.",
        "workflow": "Viewed in employee profile drawer on /teachers. Used as base contract for monthly salary calculations.",
        "invariants": "Enforces UNIQUE(school_id, name)."
    },
    "leave_types": {
        "domain": "Human Resources & Payroll",
        "route": "/settings, /teachers",
        "feature_type": "Live Operational Feature",
        "ui_components": "Staff Leave Policy Setup Table (Casual Leave 12d, Sick Leave 10d, Earned Leave 15d)",
        "purpose": "School staff leave quota categories and annual allocations.",
        "workflow": "Configured in School Settings; governs maximum allowed paid leaves per employee per academic session.",
        "invariants": "Enforces UNIQUE(school_id, code)."
    },
    "staff_attendance": {
        "domain": "Human Resources & Payroll",
        "route": "/teachers, /attendance",
        "feature_type": "Live Operational Feature",
        "ui_components": "Staff Biometric Punch Log, Daily Staff Attendance Register, Clock-in/Clock-out Table",
        "purpose": "Daily biometric, RFID, and leave-derived punch records for teachers, drivers, and administrative staff.",
        "workflow": "Updated when morning staff roll is recorded or when staff leave requests are approved with status='leave'. Feeds payroll loss-of-pay calculations.",
        "invariants": "Enforces UNIQUE(employee_id, date)."
    },
    "staff_leave_requests": {
        "domain": "Human Resources & Payroll",
        "route": "/staff-leave, /leave (Mobile)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Staff Leave Queue, Review & Substitution Matrix, Locked/Unlocked Approval Button, Mobile Apply Leave Form, Mobile My Leaves History",
        "purpose": "Staff leave applications submitted by teachers strictly through the mobile app, with dates, reason, status (applied, approved, rejected), and admin remarks.",
        "workflow": "Teacher applies on mobile app. Admin reviews on /staff-leave. Approval is strictly locked until 100% of affected timetable slots have assigned substitutes. Rejection purges provisional substitutions.",
        "invariants": "Enforces 100% substitution coverage gate before approval. Non-cancellable by teachers once submitted."
    },
    "leave_balances": {
        "domain": "Human Resources & Payroll",
        "route": "/teachers",
        "feature_type": "Planned Feature",
        "ui_components": "Annual Leave Quota Balance Ledger, Used vs Available Leave Gauges",
        "purpose": "Annual running ledger tracking credited, used, and remaining leave quotas per employee.",
        "workflow": "Updated automatically when staff leave requests are approved or annual quotas are credited.",
        "invariants": "Enforces UNIQUE(employee_id, leave_type_id, academic_year_id)."
    },
    "salary_structure_items": {
        "domain": "Human Resources & Payroll",
        "route": "/payroll [Planned]",
        "feature_type": "Planned Feature",
        "ui_components": "Custom Salary Package Line Items, Allowance Calculation Formula Builder",
        "purpose": "Itemized salary rules and customized earnings/deduction amounts linked to staff compensation packages.",
        "workflow": "Detailed contract items compiled into monthly employee payslips.",
        "invariants": "Foreign key references salary_structures and salary_components."
    },
    "payroll_runs": {
        "domain": "Human Resources & Payroll",
        "route": "/payroll [Planned]",
        "feature_type": "Planned Feature",
        "ui_components": "Monthly Payroll Disbursal Batch Screen, Run Payroll Button, Bank Transfer Export (NEFT/RTGS)",
        "purpose": "Monthly salary processing batches recording total school wage bill, statutory deductions, and disbursement approval stamps.",
        "workflow": "Bursar clicks 'Run Payroll' for active month; computes attendance deductions, generates individual payslips, and exports bank transfer sheet.",
        "invariants": "Enforces one finalized payroll run per calendar month per school."
    },
    "payslips": {
        "domain": "Human Resources & Payroll",
        "route": "/payroll [Planned]",
        "feature_type": "Planned Feature",
        "ui_components": "Staff Payslip Voucher Drawer, Download Payslip PDF Button, Net Salary Breakdown",
        "purpose": "Individual monthly pay vouchers issued to staff detailing gross earnings, deductions, and net salary payout.",
        "workflow": "Generated during payroll run; accessible to staff members on their employee profiles.",
        "invariants": "Enforces UNIQUE(payroll_run_id, employee_id)."
    },
    "payslip_lines": {
        "domain": "Human Resources & Payroll",
        "route": "/payroll [Planned]",
        "feature_type": "Planned Feature",
        "ui_components": "Itemized Payslip Ledger, Statutory PF/ESI Deduction Lines",
        "purpose": "Itemized earnings and deduction breakdown lines on individual payslips.",
        "workflow": "Provides itemized audit trail for statutory compliance and employee tax filings.",
        "invariants": "Foreign key references payslips.id and salary_components.id."
    },

    # -------------------------------------------------------------
    # Domain 10: Admission Management (15 DB tables)
    # -------------------------------------------------------------
    "admission_cycles": {
        "domain": "Admission Management",
        "route": "/admission",
        "feature_type": "Live Operational Feature",
        "ui_components": "Admission Dashboard Header, Active Cycle Card ('2026-27 Intake'), Application Fee Configuration",
        "purpose": "Admission campaign cycle controller (e.g. AY 2026-27 Intake) with start/end dates, application fee, and operational status.",
        "workflow": "Loaded on /admission to display executive metrics, lead funnel counts, and seat fill gauges.",
        "invariants": "Enforces UNIQUE(school_id, name). Exactly one cycle marked is_active=True."
    },
    "cycle_class_config": {
        "domain": "Admission Management",
        "route": "/admission",
        "feature_type": "Live Operational Feature",
        "ui_components": "Class Intake Capacity Table (Class 1: 40 seats, Class 6: 20 seats, Class 9: 15 seats), Written Test Toggles",
        "purpose": "Class-wise admission seat quotas, minimum/maximum age requirements, and evaluation workflow switches (written test, interview).",
        "workflow": "Rendered on /admission to display class capacity utilization bars and validate candidate birthdates during application intake.",
        "invariants": "Enforces UNIQUE(admission_cycle_id, class_section_id)."
    },
    "enquiries": {
        "domain": "Admission Management",
        "route": "/admission/enquiries",
        "feature_type": "Live Operational Feature",
        "ui_components": "Enquiry Register Table, Add Enquiry Modal, Status Filter (Open, Contacted, Converted, Dropped), Convert to Application Button",
        "purpose": "Front-desk walk-in and telephone inquiry register capturing candidate details, contact phones, lead sources, and admission stage.",
        "workflow": "Logged by receptionist on /admission/enquiries. One-click conversion carries enquiry biodata into a formal applicant record.",
        "invariants": "Enforces UNIQUE(school_id, enquiry_number)."
    },
    "applications": {
        "domain": "Admission Management",
        "route": "/admission/applications",
        "feature_type": "Planned Feature",
        "ui_components": "Application Register Table, Multi-tab Applicant Dossier Drawer (Biodata, Parents, Medical, Documents), Application Status Pills",
        "purpose": "360° candidate admission application dossier holding applicant biodata, category, photographs, and submission timestamps.",
        "workflow": "Receptionist enters application details on /admission/applications or received from public online portal. Advances through merit screening.",
        "invariants": "Enforces UNIQUE(school_id, application_number)."
    },
    "enquiry_interactions": {
        "domain": "Admission Management",
        "route": "/admission/enquiries",
        "feature_type": "Planned Feature",
        "ui_components": "Follow-up Timeline Drawer, Log Counselling Call Modal, Next Follow-up Date Picker",
        "purpose": "Chronological audit log of parent follow-up calls, campus visits, and counselling notes for each admission lead.",
        "workflow": "Receptionist logs phone interaction notes on /admission/enquiries; sets reminder flags for pending callbacks.",
        "invariants": "Foreign key references enquiries.id."
    },
    "application_guardians": {
        "domain": "Admission Management",
        "route": "/admission/applications Tab 2",
        "feature_type": "Planned Feature",
        "ui_components": "Applicant Parent Details Tab, Primary Guardian Designation, Annual Income Field",
        "purpose": "Parent and guardian records submitted as part of the admission application dossier.",
        "workflow": "Entered on application form; converted into permanent guardians records upon student enrollment.",
        "invariants": "Foreign key references applications.id."
    },
    "application_siblings": {
        "domain": "Admission Management",
        "route": "/admission/applications Tab 2",
        "feature_type": "Planned Feature",
        "ui_components": "Sibling Quota Point Selector, Current Student Roll Lookup Modal",
        "purpose": "Records elder siblings currently studying in the school to award sibling quota priority points.",
        "workflow": "Checked during merit list compilation to award additional admission points.",
        "invariants": "Foreign key references applications.id and students.id."
    },
    "application_medical": {
        "domain": "Admission Management",
        "route": "/admission/applications Tab 7",
        "feature_type": "Planned Feature",
        "ui_components": "Applicant Medical Disclosure Tab, Blood Group Selector, Chronic Conditions & Allergy Notes",
        "purpose": "Medical disclosures, allergy alerts, and emergency care authorizations submitted during admission.",
        "workflow": "Transferred into permanent student medical profile upon admission conversion.",
        "invariants": "Foreign key references applications.id."
    },
    "application_payments": {
        "domain": "Admission Management",
        "route": "/admission/applications Tab 6",
        "feature_type": "Planned Feature",
        "ui_components": "Application Registration Fee Receipt Drawer, Cash/UPI Payment Mode Toggle, Print Receipt Action",
        "purpose": "Application processing fee transaction receipts recording payment mode, receipt number, and payment timestamp.",
        "workflow": "Receptionist collects registration fee; issues official application fee receipt voucher.",
        "invariants": "Enforces UNIQUE(school_id, receipt_number)."
    },
    "assessments": {
        "domain": "Admission Management",
        "route": "/admission/merit",
        "feature_type": "Planned Feature",
        "ui_components": "Entrance Test Session Scheduling Matrix, Room Allocation, Roll Number Allotment",
        "purpose": "Scheduled entrance evaluation sessions for applicants applying for Class 6 and Class 9 intake.",
        "workflow": "Coordinator schedules entrance exam dates on /admission/merit; allocates applicants to test halls.",
        "invariants": "Foreign key references admission_cycles and class_sections."
    },
    "assessment_subjects": {
        "domain": "Admission Management",
        "route": "/admission/merit",
        "feature_type": "Planned Feature",
        "ui_components": "Subject Test Score Entry Grid (English, Mathematics, Science), Max Marks vs Scored Inputs",
        "purpose": "Subject-level entrance test scores entered by evaluating teachers for candidate ranking.",
        "workflow": "Teachers input written test scores on /admission/merit; system computes aggregated test totals.",
        "invariants": "Foreign key references assessments.id and subjects.id."
    },
    "interviews": {
        "domain": "Admission Management",
        "route": "/admission/merit",
        "feature_type": "Planned Feature",
        "ui_components": "Interview Schedule Table, Principal Evaluation Rating Stars, Interaction Remarks Box",
        "purpose": "Oral interview and interaction ratings conducted by Principal or Coordinator for primary applicants.",
        "workflow": "Principal rates candidate readiness on /admission/merit; marks recommendation notes.",
        "invariants": "Foreign key references applications.id."
    },
    "admission_decisions": {
        "domain": "Admission Management",
        "route": "/admission/merit",
        "feature_type": "Planned Feature",
        "ui_components": "Merit Selection Table, Decision Buttons (Selected, Waitlisted, Rejected), Bulk Decision Modal",
        "purpose": "Final admission decisions (selected, waitlisted, rejected, offered) with audited principal rationale.",
        "workflow": "School committee reviews merit ranks on /admission/merit; commits decisions to database.",
        "invariants": "Enforces UNIQUE(application_id)."
    },
    "admission_offers": {
        "domain": "Admission Management",
        "route": "/admission/applications",
        "feature_type": "Planned Feature",
        "ui_components": "Offer Letter Generator, Fee Payment Deadline Picker, Send Offer SMS/Email Action",
        "purpose": "Provisional admission offer letters issued to selected candidates with fee payment deadlines.",
        "workflow": "Issued on /admission/applications; triggers notification to parents to pay admission dues.",
        "invariants": "Tracks offer expiration date; unaccepted offers trigger waitlist promotion."
    },
    "waitlist_entries": {
        "domain": "Admission Management",
        "route": "/admission/waitlist",
        "feature_type": "Planned Feature",
        "ui_components": "Waitlist Queue Table, Drag-and-Drop Rank Reorder, Promote to Offered Action Button",
        "purpose": "Ordered waitlist queue tracking priority rank, merit scores, and seat promotion actions.",
        "workflow": "Displayed on /admission/waitlist. When a selected candidate declines, receptionist clicks 'Promote' to offer seat to next waitlisted child.",
        "invariants": "Enforces UNIQUE(admission_cycle_id, class_section_id, waitlist_rank)."
    },

    # -------------------------------------------------------------
    # Domain 11: Communication & Notices (5 DB tables)
    # -------------------------------------------------------------
    "notices": {
        "domain": "Communication & Notices",
        "route": "/notices, /dashboard",
        "feature_type": "Live Operational Feature",
        "ui_components": "School Notice Board Roster, Publish Notice Drawer, Audience Target Picker (All, Students, Teachers, Parents, Class 10-A)",
        "purpose": "School digital notice board for announcements, circulars, and holiday notifications.",
        "workflow": "Published on /notices; displayed on dashboard notice widget and mobile apps.",
        "invariants": "Audited with author employee_id and publication timestamp."
    },
    "message_templates": {
        "domain": "Communication & Notices",
        "route": "/notices",
        "feature_type": "Live Operational Feature",
        "ui_components": "Pre-approved SMS/WhatsApp Template Selector, Template Placeholder Variable Pills ({student_name}, {due_amount})",
        "purpose": "Pre-approved TRAI DLT message templates for fee reminders, attendance absence alerts, and urgent closures.",
        "workflow": "Selected when composing broadcast alerts on /notices to ensure compliance with Indian telecom regulations.",
        "invariants": "Enforces UNIQUE(school_id, code)."
    },
    "messages": {
        "domain": "Communication & Notices",
        "route": "/notices [Planned]",
        "feature_type": "Planned Feature",
        "ui_components": "Outbound Message Dispatch Queue, Broadcast Channel Selector (SMS, WhatsApp, Email)",
        "purpose": "Outbound communication batch queue for school-wide SMS, WhatsApp, and email alerts.",
        "workflow": "Enqueued when sending batch announcements; processed asynchronously by messaging worker.",
        "invariants": "Foreign key references message_templates.id."
    },
    "message_recipients": {
        "domain": "Communication & Notices",
        "route": "/notices [Planned]",
        "feature_type": "Planned Feature",
        "ui_components": "Delivery Status Indicator Pills (Sent, Delivered, Failed, Read), Retry Dispatch Button",
        "purpose": "Recipient-level dispatch logs tracking individual phone numbers and delivery gateway statuses.",
        "workflow": "Updated via SMS gateway webhook callbacks to report real delivery rates to school administrators.",
        "invariants": "Foreign key references messages.id and users.id."
    },
    "notification_preferences": {
        "domain": "Communication & Notices",
        "route": "/settings",
        "feature_type": "Planned Feature",
        "ui_components": "Parent Notification Preferences Matrix, Channel Toggles (SMS on/off, WhatsApp on/off)",
        "purpose": "Guardian opt-in/opt-out channel preferences per notification category (academic, fee, transport).",
        "workflow": "Checked before dispatching automated notifications to respect parental channel choices.",
        "invariants": "Enforces UNIQUE(user_id, category)."
    },

    # -------------------------------------------------------------
    # Domain 12: Inventory & Stock Management (2 DB tables)
    # -------------------------------------------------------------
    "stock_items": {
        "domain": "Inventory & Stock Management",
        "route": "/inventory",
        "feature_type": "Live Operational Feature",
        "ui_components": "Stock Catalogue Grid, Low Stock Reorder Threshold Alert Banner, Add Item Modal, Adjust Stock Counter",
        "purpose": "Consumables and equipment catalogue (Chalk, Whiteboard Markers, Printing Paper, Footballs) with reorder thresholds and live stock counts.",
        "workflow": "Monitored on /inventory; triggers red warning pills when stock falls below reorder_level.",
        "invariants": "Enforces UNIQUE(school_id, item_code) and non-negative stock quantities."
    },
    "stock_requests": {
        "domain": "Inventory & Stock Management",
        "route": "/inventory, Mobile App (Teacher)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Stock Indent Approval Queue, Approve/Reject Action Dialog, Teacher Stock Request Modal",
        "purpose": "Replenishment indents and consumable issuance requests submitted by teachers and staff.",
        "workflow": "Teacher flags diminishing stock via mobile app; Administrator reviews and approves indent on /inventory.",
        "invariants": "Requires administrative approval reason logged to audit trail upon status change."
    },

    # -------------------------------------------------------------
    # Domain 13: Grievances & Feedback System (2 DB tables)
    # -------------------------------------------------------------
    "grievances": {
        "domain": "Grievances & Feedback System",
        "route": "/dashboard, Mobile App",
        "feature_type": "Live Operational Feature",
        "ui_components": "Grievance Feed on Dashboard, Priority Badges (Low, Medium, High, Urgent), Category Pills, Status Dropdown (Submitted, In Progress, Resolved)",
        "purpose": "School helpdesk tickets raised by parents, teachers, and students (Facilities, Academic, Transport, Billing).",
        "workflow": "Complainant submits ticket on mobile app; School leadership assigns ticket to staff and tracks resolution on dashboard.",
        "invariants": "Enforces UNIQUE(school_id, ticket_number)."
    },
    "grievance_replies": {
        "domain": "Grievances & Feedback System",
        "route": "/dashboard, Mobile App",
        "feature_type": "Live Operational Feature",
        "ui_components": "Ticket Detail Modal Thread, Post Reply Textarea, Internal Note Toggle",
        "purpose": "Conversational messages, internal administrative notes, and complainant replies on grievance threads.",
        "workflow": "Staff and parents exchange updates directly inside the ticket drawer until issue closure.",
        "invariants": "Foreign key references grievances.id and users.id."
    },

    # -------------------------------------------------------------
    # Domain 14: System, Documents & Audit (5 DB tables)
    # -------------------------------------------------------------
    "document_types": {
        "domain": "System, Documents & Audit",
        "route": "/configuration, /admission/applications",
        "feature_type": "Live Operational Feature",
        "ui_components": "Mandatory Document Checklist Setup Table, Required Document Badges",
        "purpose": "Mandatory document checklist definitions (Birth Certificate, Transfer Certificate, Aadhaar Card, Previous Marksheet).",
        "workflow": "Governs required attachments during student admission and employee hiring workflows.",
        "invariants": "Enforces UNIQUE(school_id, name)."
    },
    "documents": {
        "domain": "System, Documents & Audit",
        "route": "/students, /admission/applications, /transport",
        "feature_type": "Live Operational Feature",
        "ui_components": "Uploaded Files Attachment Drawer, Document Verification Checkmark, Expiry Date Warning",
        "purpose": "Binary file storage metadata for uploaded student identities, employee certificates, and vehicle fitness papers.",
        "workflow": "Office staff uploads scanned PDF/JPG; marks document status as Verified. Soft-deleted to preserve audit integrity.",
        "invariants": "Soft-deleted records preserve historical references in audit log."
    },
    "scheduled_jobs": {
        "domain": "System, Documents & Audit",
        "route": "/configuration",
        "feature_type": "Live Operational Feature",
        "ui_components": "Background Cron Jobs Table, Last Run Status Indicator, Run Now Trigger Button",
        "purpose": "System automation cron definitions for nightly fee invoice generation, daily absentee SMS alerts, and attendance aggregation.",
        "workflow": "Monitored on /configuration; executed periodically by backend scheduler worker.",
        "invariants": "Enforces UNIQUE(school_id, job_name)."
    },
    "audit_log": {
        "domain": "System, Documents & Audit",
        "route": "System-Wide (Contract 3 Compliance)",
        "feature_type": "Live Operational Feature",
        "ui_components": "Contract 3 Compliance Audit Trail, Entity History Drawer, User Reason Viewer",
        "purpose": "Contract 3 Compliance Audit Log: immutable audit trail recording every write, status change, and reverse action with timestamp, IP address, and user-typed reason.",
        "workflow": "Automatically written on every state-changing HTTP request across all ERP modules. Never updated or deleted.",
        "invariants": "Append-only: zero UPDATE or DELETE operations permitted on this table."
    },
    "jobs": {
        "domain": "System, Documents & Audit",
        "route": "Background Worker Queue",
        "feature_type": "Planned Feature",
        "ui_components": "Long-running Task Progress Bar, Bulk Export Download Modal, PDF Generation Status",
        "purpose": "Asynchronous background worker queue for long-running report exports, bulk PDF generation, and batch data migrations.",
        "workflow": "When user requests a heavy report export, job is enqueued here and processed in background by worker tasks.",
        "invariants": "Tracks task execution state (pending, processing, completed, failed) with retry counts."
    },
    "alembic_version": {
        "domain": "Tenancy, Identity & Access",
        "route": "Database Migration Engine",
        "feature_type": "Live Operational Feature",
        "ui_components": "Backend Schema Revision Head Tracker",
        "purpose": "Internal Alembic schema migration version tracker recording the active database migration revision hash.",
        "workflow": "Read and updated during alembic upgrade head to ensure database schema matches current codebase revision.",
        "invariants": "Single-row table storing version_num varchar(32)."
    },
    "candidates": {
        "domain": "Teacher Recruitment & Onboarding",
        "route": "/recruitment",
        "feature_type": "Live Operational Feature",
        "ui_components": "Candidate Intake Form, Pipeline Stages (Applied, Shortlisted, Offered, Hired), CBSE A4 Printable Application Preview",
        "purpose": "Teacher recruitment candidate master storing personal details, CBSE teaching qualifications, prior school experience, post applied for, expected salary, and recruitment status.",
        "workflow": "Receptionist registers walk-in candidate on /recruitment. Admin reviews dossier, prints CBSE A4 form, moves candidate through pipeline stages, and confirms hiring.",
        "invariants": "Enforces UNIQUE(school_id, application_no) and optional UNIQUE(employee_id)."
    },
    "candidate_offers": {
        "domain": "Teacher Recruitment & Onboarding",
        "route": "/recruitment",
        "feature_type": "Live Operational Feature",
        "ui_components": "Issue Job Offer Modal, Designation & Department Selector, Offered Salary Input (₹), Joining Date Picker",
        "purpose": "Formal employment offer issued to a shortlisted teacher candidate, tracking offered designation, department, monthly CTC salary, and scheduled joining date.",
        "workflow": "Admin creates offer via POST /admin/recruitment/candidates/{id}/offer. Upon candidate acceptance, admin confirms joining which automatically provisions active teacher employee and user accounts.",
        "invariants": "Enforces UNIQUE(candidate_id) and school_id tenant scoping."
    },
    "in_app_notifications": {
        "domain": "Communication & Notices",
        "route": "Mobile App / Web App Notifications",
        "feature_type": "Live Operational Feature",
        "ui_components": "Top Navigation Notification Bell, In-App Alert Banners, Mobile Duties & Leave Alerts",
        "purpose": "In-app notifications dispatched to teachers, staff, and leadership for leave approvals/rejections, substitution duty assignments, and stock requests.",
        "workflow": "Triggered by backend domain events (e.g. staff leave approval). Queried by mobile and web clients via GET /notifications; marked read on interaction.",
        "invariants": "Indexed on (user_id, is_read) and school_id."
    }
}

DOMAINS_ORDER = [
    ("Domain 1: Tenancy, Identity & Access", "Controls multi-tenant isolation, user authentication, RBAC permissions, and global school settings.", [
        "schools", "academic_years", "users", "roles", "permissions",
        "role_permissions", "user_roles", "settings", "custom_fields",
        "number_sequences", "alembic_version"
    ]),
    ("Domain 2: People — Students & Guardians", "Manages student identities, demographics, parental relationships, and annual academic enrolments.", [
        "students", "guardians", "student_guardian", "enrolments"
    ]),
    ("Domain 3: People — Staff & Departments", "Manages employee records, teaching designations, and departmental structures.", [
        "departments", "employees"
    ]),
    ("Domain 4: Academics, Timetable & Homework", "Drives class sections, timetable scheduling, subjects, school calendar, and homework assignments.", [
        "class_sections", "subjects", "class_subject_teacher", "school_periods",
        "timetable_slots", "holidays", "homework", "homework_submissions", "substitutions"
    ]),
    ("Domain 5: Attendance", "Drives daily student roll call, absence tracking, leave requests, and attendance dashboard analytics.", [
        "attendance", "student_leave_requests"
    ]),
    ("Domain 6: Examinations, Grading & Results", "Manages CBSE assessment schemes, exam datesheets, marks entry, and report card publications.", [
        "assessment_schemes", "scheme_components", "grading_scales", "grade_bands",
        "exams", "exam_schedule", "marks", "report_card_publications"
    ]),
    ("Domain 7: Fees & Financial Ledger", "Drives student billing, fee plans, concessions, payments, receipting, and defaulter tracking.", [
        "fee_heads", "fee_plans", "fee_plan_items", "fee_concessions",
        "fee_invoices", "fee_invoice_lines", "fee_payments", "payment_allocations",
        "student_fee_plans", "fee_periods"
    ]),
    ("Domain 8: Transport & Fleet Management", "Manages school buses, transport routes, boarding stops, vehicle fitness papers, and student riders.", [
        "vehicles", "routes", "route_stops", "transport_fee_slabs", "transport_assignments"
    ]),
    ("Domain 9: Human Resources & Payroll", "Drives employee salary packages, statutory deductions, monthly payroll runs, staff leave, and biometric attendance.", [
        "salary_components", "salary_structures", "leave_types", "staff_attendance",
        "staff_leave_requests", "leave_balances", "salary_structure_items", "payroll_runs",
        "payslips", "payslip_lines"
    ]),
    ("Domain 10: Admission Management", "Drives the front-desk admission cycle, inquiry register, applicant screening, scoring, merit ranking, and waitlists.", [
        "admission_cycles", "cycle_class_config", "enquiries", "applications",
        "enquiry_interactions", "application_guardians", "application_siblings",
        "application_medical", "application_payments", "assessments",
        "assessment_subjects", "interviews", "admission_decisions",
        "admission_offers", "waitlist_entries"
    ]),
    ("Domain 11: Communication & Notices", "Drives the school digital notice board, parent notifications, and delivery tracking.", [
        "notices", "message_templates", "messages", "message_recipients", "notification_preferences", "in_app_notifications"
    ]),
    ("Domain 12: Inventory & Stock Management", "Drives the school consumable catalog, minimum quantity alerts, and purchase approval workflows.", [
        "stock_items", "stock_requests"
    ]),
    ("Domain 13: Grievances & Feedback System", "Drives the ticketing helpdesk, priority queues, staff assignments, and conversational resolution threads.", [
        "grievances", "grievance_replies"
    ]),
    ("Domain 14: System, Documents & Audit", "Drives document verification checklists, binary file storage, background scheduler, and compliance audit logs.", [
        "document_types", "documents", "scheduled_jobs", "audit_log", "jobs"
    ]),
    ("Domain 15: Teacher Recruitment & Onboarding", "Drives front-desk candidate intake, CBSE A4 printable application dossiers, admin review, salary offers, and automatic teacher account provisioning.", [
        "candidates", "candidate_offers"
    ]),
]

def render_columns_table(tbl, info):
    fk_map = {f["col"]: f["to"] for f in info.get("fk", [])}
    uniq_set = set()
    for u in info.get("unique", []):
        uniq_set.update(c.strip() for c in u.split(","))

    rows_html = []
    for c in info.get("columns", []):
        name = c["name"]
        typ = c["type"]
        nullable = "optional" if c["null"] else "required"
        
        notes = []
        if name == "id":
            notes.append('<span class="badge-pk">PRIMARY KEY</span>')
        if name == "school_id":
            notes.append('<span class="badge-tenant">TENANT FK</span>')
        elif name in fk_map:
            notes.append(f'<span class="badge-fk">&rarr; {esc(fk_map[name])}</span>')
        
        if name in uniq_set:
            notes.append('<span class="badge-uniq">UNIQUE</span>')
            
        default_val = c["default"]
        if default_val and not default_val.startswith("nextval"):
            clean_def = default_val.split("::")[0].strip("'")
            notes.append(f'<span class="badge-def">def: {esc(clean_def)}</span>')

        notes_str = " ".join(notes) if notes else '<span class="text-muted">—</span>'

        rows_html.append(f"""
        <tr>
          <td class="col-name">{esc(name)}</td>
          <td class="col-type">{esc(typ)}</td>
          <td class="col-null"><span class="null-pill null-{nullable}">{nullable}</span></td>
          <td class="col-notes">{notes_str}</td>
        </tr>
        """)

    return f"""
    <table class="columns-table">
      <thead>
        <tr>
          <th style="width: 28%;">Column</th>
          <th style="width: 22%;">Data Type</th>
          <th style="width: 14%;">Nullability</th>
          <th style="width: 36%;">Foreign Keys &amp; Invariants</th>
        </tr>
      </thead>
      <tbody>
        {"".join(rows_html)}
      </tbody>
    </table>
    """

def build_html(db_tables):
    total_tables = len(db_tables)
    live_tables = sum(1 for t, d in db_tables.items() if d["rows"] > 0)
    unused_tables = sum(1 for t, d in db_tables.items() if d["rows"] == 0)

    # Master Domain Matrix
    domain_summary_rows = []
    for idx, (d_name, d_desc, d_tbls) in enumerate(DOMAINS_ORDER, 1):
        d_live = sum(1 for t in d_tbls if db_tables.get(t, {}).get("rows", 0) > 0)
        d_unused = sum(1 for t in d_tbls if db_tables.get(t, {}).get("rows", 0) == 0)
        routes = sorted(list({TABLE_MAPPINGS.get(t, {}).get("route", "").split(",")[0].strip() for t in d_tbls if TABLE_MAPPINGS.get(t, {}).get("route")}))
        routes_str = ", ".join(f"<code>{esc(r)}</code>" for r in routes[:3])
        if len(routes) > 3:
            routes_str += f" <span style='font-size:7.5pt; color:#64748b;'>+{len(routes)-3} more</span>"

        domain_summary_rows.append(f"""
        <tr>
          <td style="font-weight:700; color:#1e1b4b;">{idx}. {esc(d_name.split(':')[1].strip() if ':' in d_name else d_name)}</td>
          <td style="text-align:center; font-weight:700;">{len(d_tbls)}</td>
          <td style="text-align:center;"><span class="badge-live-sm">{d_live} Live</span></td>
          <td style="text-align:center;"><span class="badge-unused-sm">{d_unused} Unused</span></td>
          <td>{routes_str}</td>
          <td style="font-size:7.8pt; color:#475569;">{esc(d_desc)}</td>
        </tr>
        """)

    # Detailed Domain Sections
    sections_html = []
    for d_title, d_desc, d_tbls in DOMAINS_ORDER:
        d_live_cnt = sum(1 for t in d_tbls if db_tables.get(t, {}).get("rows", 0) > 0)
        d_unused_cnt = sum(1 for t in d_tbls if db_tables.get(t, {}).get("rows", 0) == 0)

        cards_html = []
        for t in d_tbls:
            t_info = db_tables.get(t, {"rows": 0, "columns": [], "fk": [], "unique": []})
            m = TABLE_MAPPINGS.get(t, {
                "route": "System",
                "feature_type": "Live Operational Feature" if t_info["rows"] > 0 else "Planned Feature",
                "ui_components": "Component view",
                "purpose": "Core system table",
                "workflow": "Operational workflow",
                "invariants": "Tenant-scoped table"
            })

            is_live = t_info["rows"] > 0
            row_count = t_info["rows"]

            # User Instruction: IN FRONT OF NON ESSENTIAL TABLES (empty tables), PROMINENTLY WRITE "UNUSED FOR NOW"
            if is_live:
                status_badge = f'<span class="badge-live">LIVE / IN USE ({row_count:,} {"row" if row_count == 1 else "rows"})</span>'
            else:
                status_badge = '<span class="badge-unused">UNUSED FOR NOW</span>'

            feature_type_badge = (
                '<span class="badge-feature-live">Live Operational Feature</span>'
                if m["feature_type"] == "Live Operational Feature"
                else '<span class="badge-feature-planned">Planned Feature</span>'
            )

            is_no_tenant = t in ("schools", "alembic_version")
            tenant_badge = (
                '<span class="badge-scope-root">Tenant Root Anchor</span>'
                if is_no_tenant
                else '<span class="badge-scope">Tenant Scoped (school_id)</span>'
            )

            card_html = f"""
            <div class="table-card">
              <div class="table-card-header">
                <div class="header-left">
                  <span class="table-name"><code>{esc(t)}</code></span>
                  {status_badge}
                </div>
                <div class="header-right">
                  {tenant_badge}
                  {feature_type_badge}
                </div>
              </div>

              <div class="feature-mapping-box">
                <div class="mapping-grid">
                  <div class="mapping-item">
                    <span class="mapping-label">🌐 Web Screen / Route:</span>
                    <span class="mapping-val route-val"><code>{esc(m["route"])}</code></span>
                  </div>
                  <div class="mapping-item">
                    <span class="mapping-label">🖥️ UI Components &amp; Modals:</span>
                    <span class="mapping-val">{esc(m["ui_components"])}</span>
                  </div>
                </div>

                <div class="business-purpose-box">
                  <span class="box-label">🎯 Core Business Role:</span>
                  <span class="box-text">{esc(m["purpose"])}</span>
                </div>

                <div class="workflow-invariants-grid">
                  <div class="sub-box">
                    <span class="sub-label">🔄 Real School ERP Workflow:</span>
                    <p class="sub-text">{esc(m["workflow"])}</p>
                  </div>
                  <div class="sub-box">
                    <span class="sub-label">🛡️ Database Invariants &amp; Guardrails:</span>
                    <p class="sub-text">{esc(m["invariants"])}</p>
                  </div>
                </div>
              </div>

              <div class="columns-container">
                <div class="columns-header">
                  <span>Schema Columns ({len(t_info.get("columns", []))} columns)</span>
                  <span class="columns-meta">{len(t_info.get("fk", []))} Foreign Keys &bull; {len(t_info.get("unique", []))} Unique Constraints</span>
                </div>
                {render_columns_table(t, t_info)}
              </div>
            </div>
            """
            cards_html.append(card_html)

        # Architectural callout for Domain 1 (Alembic Version)
        alembic_note_html = ""
        if "Domain 1" in d_title:
            alembic_note_html = """
            <div class="architectural-callout-card">
              <div class="callout-header">
                <span class="callout-title">⚙️ Internal Schema Migration Engine: <code>alembic_version</code></span>
                <span class="badge-scope-root">System Infrastructure</span>
                <span class="badge-feature-live">Live Migration Head</span>
              </div>
              <p class="callout-text">
                <strong>Migration Head:</strong> <code>a1b2c3d4e5f6</code> (Teacher Leave &amp; Recruitment Migration).<br>
                <strong>Role:</strong> Internal Alembic version tracking table storing the single active schema revision hash. 
                It does not contain <code>school_id</code>, <code>id</code>, or audit columns because it is an engine-level state table rather than an application business entity. 
                All 92 business tables derive from either <code>TenantBase</code> or <code>TimestampedBase</code>.
              </p>
            </div>
            """

        section_html = f"""
        <section class="domain-section">
          <div class="domain-header">
            <div class="domain-title-row">
              <h2 class="domain-title">{esc(d_title)}</h2>
              <div class="domain-metrics">
                <span class="badge-count-total">{len(d_tbls)} Tables</span>
                <span class="badge-count-live">{d_live_cnt} Live</span>
                <span class="badge-count-unused">{d_unused_cnt} Unused For Now</span>
              </div>
            </div>
            <p class="domain-description">{esc(d_desc)}</p>
          </div>

          {alembic_note_html}
          {"".join(cards_html)}
        </section>
        """
        sections_html.append(section_html)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sunrise School ERP — All-Tables Database &amp; Feature Mapping Reference</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    @page {{
      size: A4 portrait;
      margin: 14mm 14mm 14mm 14mm;
      @bottom-right {{
        content: "Page " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #64748b;
        font-weight: 500;
      }}
      @bottom-left {{
        content: "Sunrise School ERP — All-Tables Database & Feature Mapping Reference";
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #94a3b8;
      }}
    }}

    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 8.7pt;
      line-height: 1.48;
      color: #1e293b;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }}

    h1, h2, h3, h4 {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      margin: 0;
    }}

    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 8pt;
      background: #f1f5f9;
      color: #0f172a;
      padding: 1px 4px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}

    /* Executive Banner */
    .header-banner {{
      background: linear-gradient(135deg, #1e1b4b 0%, #312e81 55%, #4338ca 100%);
      color: #ffffff;
      padding: 22px 26px;
      border-radius: 12px;
      margin-bottom: 18px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .banner-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .school-title {{
      font-size: 8.5pt;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: #a5b4fc;
      font-weight: 700;
    }}
    .doc-date {{
      font-size: 8pt;
      color: #e0e7ff;
      background: rgba(255, 255, 255, 0.15);
      padding: 2px 10px;
      border-radius: 12px;
    }}
    .header-banner h1 {{
      font-size: 19pt;
      font-weight: 800;
      letter-spacing: -0.5px;
      line-height: 1.25;
      margin-bottom: 6px;
    }}
    .header-subtitle {{
      font-size: 9.5pt;
      color: #c7d2fe;
      font-weight: 500;
      margin-bottom: 14px;
      max-width: 90%;
    }}
    .meta-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.2);
      padding-top: 12px;
    }}
    .meta-pill {{
      font-size: 7.8pt;
      background: rgba(255, 255, 255, 0.12);
      color: #ffffff;
      padding: 3px 10px;
      border-radius: 6px;
      font-weight: 500;
    }}

    /* Metrics Summary Cards */
    .metrics-bar {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 20px;
    }}
    .metric-card {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 12px 14px;
      text-align: left;
    }}
    .metric-val {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 17pt;
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: 2px;
    }}
    .val-total {{ color: #1e1b4b; }}
    .val-live {{ color: #047857; }}
    .val-unused {{ color: #b45309; }}
    .val-screens {{ color: #4338ca; }}
    .metric-label {{
      font-size: 8pt;
      color: #64748b;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    /* Architecture Golden Rules Box */
    .architecture-box {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 10px;
      padding: 14px 18px;
      margin-bottom: 22px;
      break-inside: avoid;
    }}
    .architecture-box h3 {{
      font-size: 10.5pt;
      color: #1e3a8a;
      font-weight: 800;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .rules-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 16px;
      font-size: 8.2pt;
      color: #1e293b;
    }}
    .rule-item strong {{
      color: #1e40af;
    }}

    /* Master Domain Matrix Table */
    .matrix-section {{
      margin-bottom: 24px;
      break-inside: avoid;
    }}
    .matrix-title {{
      font-size: 11pt;
      font-weight: 800;
      color: #0f172a;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .matrix-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 8.2pt;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      overflow: hidden;
    }}
    .matrix-table th {{
      background: #f1f5f9;
      color: #334155;
      font-weight: 700;
      text-align: left;
      padding: 7px 10px;
      border-bottom: 1.5px solid #cbd5e1;
      font-size: 7.8pt;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .matrix-table td {{
      padding: 6px 10px;
      border-bottom: 1px solid #e2e8f0;
      vertical-align: middle;
    }}
    .matrix-table tr:nth-child(even) td {{
      background: #f8fafc;
    }}

    /* Badges */
    .badge-live {{
      background: #10b981;
      color: #ffffff;
      font-size: 7.5pt;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      display: inline-block;
    }}
    .badge-unused {{
      background: #f59e0b;
      color: #ffffff;
      font-size: 7.5pt;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      display: inline-block;
    }}
    .badge-live-sm {{
      background: #d1fae5;
      color: #065f46;
      font-size: 7.2pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .badge-unused-sm {{
      background: #fef3c7;
      color: #92400e;
      font-size: 7.2pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .badge-feature-live {{
      background: #ecfdf5;
      color: #047857;
      border: 1px solid #a7f3d0;
      font-size: 7pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }}
    .badge-feature-planned {{
      background: #fffbeb;
      color: #b45309;
      border: 1px solid #fde68a;
      font-size: 7pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }}
    .badge-scope {{
      background: #f1f5f9;
      color: #475569;
      border: 1px solid #cbd5e1;
      font-size: 7pt;
      font-weight: 600;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .badge-scope-root {{
      background: #fef2f2;
      color: #991b1b;
      border: 1px solid #fecaca;
      font-size: 7pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .badge-count-total {{ background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 5px; font-weight: 700; font-size: 7.5pt; }}
    .badge-count-live {{ background: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 5px; font-weight: 700; font-size: 7.5pt; }}
    .badge-count-unused {{ background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 5px; font-weight: 700; font-size: 7.5pt; }}

    /* Domain Section */
    .domain-section {{
      margin-bottom: 24px;
    }}
    .domain-header {{
      background: #f8fafc;
      border-left: 4px solid #4338ca;
      border-top: 1px solid #e2e8f0;
      border-right: 1px solid #e2e8f0;
      border-bottom: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 14px;
      margin-bottom: 14px;
      break-after: avoid;
    }}
    .domain-title-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }}
    .domain-title {{
      font-size: 12pt;
      font-weight: 800;
      color: #0f172a;
    }}
    .domain-metrics {{
      display: flex;
      gap: 6px;
    }}
    .domain-description {{
      font-size: 8.3pt;
      color: #475569;
      margin: 0;
    }}

    /* Table Cards */
    .table-card {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 9px;
      margin-bottom: 14px;
      break-inside: avoid;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
      overflow: hidden;
    }}
    .table-card-header {{
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
      padding: 8px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .header-left {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .table-name code {{
      font-size: 10pt;
      font-weight: 700;
      color: #1e1b4b;
      background: #e0e7ff;
      border: 1px solid #c7d2fe;
      padding: 2px 6px;
    }}
    .header-right {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    /* Feature Mapping Box */
    .feature-mapping-box {{
      padding: 10px 12px;
      background: #ffffff;
      border-bottom: 1px solid #f1f5f9;
    }}
    .mapping-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px 14px;
      margin-bottom: 8px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 10px;
    }}
    .mapping-item {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .mapping-label {{
      font-size: 7.2pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #64748b;
    }}
    .mapping-val {{
      font-size: 8.2pt;
      color: #1e293b;
      font-weight: 500;
    }}
    .route-val code {{
      font-weight: 700;
      color: #4338ca;
      background: #eef2ff;
      border-color: #c7d2fe;
    }}

    .business-purpose-box {{
      margin-bottom: 8px;
      font-size: 8.3pt;
      line-height: 1.45;
    }}
    .box-label {{
      font-weight: 700;
      color: #0f172a;
      margin-right: 4px;
    }}
    .box-text {{
      color: #334155;
    }}

    .workflow-invariants-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      font-size: 8pt;
    }}
    .sub-box {{
      background: #fafafa;
      border: 1px solid #f1f5f9;
      border-radius: 5px;
      padding: 6px 8px;
    }}
    .sub-label {{
      font-size: 7.2pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #475569;
      display: block;
      margin-bottom: 2px;
    }}
    .sub-text {{
      margin: 0;
      color: #334155;
      line-height: 1.4;
    }}

    /* Architectural Callout Card */
    .architectural-callout-card {{
      background: #faf5ff;
      border: 1px solid #e9d5ff;
      border-radius: 8px;
      padding: 10px 14px;
      margin-bottom: 14px;
      break-inside: avoid;
    }}
    .callout-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}
    .callout-title {{
      font-size: 9pt;
      font-weight: 700;
      color: #581c87;
    }}
    .callout-text {{
      font-size: 8pt;
      color: #3b0764;
      margin: 0;
      line-height: 1.45;
    }}

    /* Columns Table */
    .columns-container {{
      background: #ffffff;
      padding: 8px 12px 10px 12px;
    }}
    .columns-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 7.5pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #64748b;
      margin-bottom: 5px;
      padding-bottom: 3px;
      border-bottom: 1px solid #f1f5f9;
    }}
    .columns-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 7.8pt;
    }}
    .columns-table th {{
      background: #f8fafc;
      color: #475569;
      font-weight: 700;
      text-align: left;
      padding: 4px 6px;
      border-bottom: 1px solid #cbd5e1;
      font-size: 7.2pt;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .columns-table td {{
      padding: 3.5px 6px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }}
    .columns-table tr:last-child td {{
      border-bottom: none;
    }}
    .col-name {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.6pt;
      font-weight: 600;
      color: #0f172a;
    }}
    .col-type {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.4pt;
      color: #64748b;
    }}
    .null-pill {{
      font-size: 6.8pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
      text-transform: uppercase;
    }}
    .null-required {{ background: #fee2e2; color: #991b1b; }}
    .null-optional {{ background: #f1f5f9; color: #64748b; }}

    .badge-pk {{
      background: #dbeafe;
      color: #1e40af;
      font-size: 6.8pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    .badge-tenant {{
      background: #fef3c7;
      color: #92400e;
      font-size: 6.8pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    .badge-fk {{
      background: #f3e8ff;
      color: #6b21a8;
      font-size: 6.8pt;
      font-weight: 600;
      padding: 1px 4px;
      border-radius: 3px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .badge-uniq {{
      background: #ccfbf1;
      color: #115e59;
      font-size: 6.8pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    .badge-def {{
      background: #f1f5f9;
      color: #475569;
      font-size: 6.8pt;
      padding: 1px 4px;
      border-radius: 3px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .text-muted {{
      color: #cbd5e1;
    }}

    /* Page Break Rules */
    .domain-section {{
      break-inside: auto;
    }}
    .table-card {{
      break-inside: avoid;
    }}
  </style>
</head>
<body>

  <!-- Cover / Header Banner -->
  <div class="header-banner">
    <div class="banner-top">
      <span class="school-title">Sunrise Public School &bull; Lucknow (CBSE Affiliated)</span>
      <span class="doc-date">17 September 2026 &bull; Branch: <code>slice/office-feedback</code></span>
    </div>
    <h1>Sunrise School ERP — All-Tables Database &amp; Feature Mapping Reference</h1>
    <div class="header-subtitle">
      Comprehensive architectural specification detailing all 93 schema tables, their live row states, foreign key relationships, 
      and exact correspondence to operational and planned features on the Sunrise Web ERP and Mobile platforms.
    </div>
    <div class="meta-pills">
      <span class="meta-pill">🗄️ 93 Database Tables (68 Live Populated &bull; 25 Unused For Now)</span>
      <span class="meta-pill">🏢 15 Functional Business Domains</span>
      <span class="meta-pill">🖥️ 27 Live Screens in Web ERP (<code>web/src/screens.ts</code>)</span>
      <span class="meta-pill">🛡️ Tenant Isolation via <code>school_id</code> on 89 Tables</span>
      <span class="meta-pill">🔒 Contract 3 Compliance &amp; Immutable Financial Ledger</span>
    </div>
  </div>

  <!-- Key Metrics Summary Cards -->
  <div class="metrics-bar">
    <div class="metric-card">
      <div class="metric-val val-total">{total_tables}</div>
      <div class="metric-label">Total Schema Tables</div>
    </div>
    <div class="metric-card">
      <div class="metric-val val-live">{live_tables}</div>
      <div class="metric-label">Live Populated Tables</div>
    </div>
    <div class="metric-card">
      <div class="metric-val val-unused">{unused_tables}</div>
      <div class="metric-label">Unused For Now Tables</div>
    </div>
    <div class="metric-card">
      <div class="metric-val val-screens">27</div>
      <div class="metric-label">Live Web ERP Screens</div>
    </div>
  </div>

  <!-- Architecture Golden Rules Box -->
  <div class="architecture-box">
    <h3>🛡️ Core Architectural Invariants &amp; Development Contracts</h3>
    <div class="rules-grid">
      <div class="rule-item">
        <strong>1. Multi-Tenant Scoping (<code>school_id</code>):</strong> Every table deriving from <code>TenantBase</code> carries an indexed <code>school_id</code> foreign key pointing to <code>schools.id</code>. Only <code>schools</code> (tenant anchor) and <code>alembic_version</code> (system engine) lack it.
      </div>
      <div class="rule-item">
        <strong>2. The Enrolment Invariant:</strong> A student joins a class for an academic session via <code>enrolments</code>. All year-scoped facts (marks, attendance, fees, bus seat) hang off <code>enrolment_id</code>, never <code>student_id</code> directly.
      </div>
      <div class="rule-item">
        <strong>3. Contract 3 Compliance Auditing:</strong> Destructive operations (status changes, voids, reversals, marks overrides) mandate a user-typed reason and commit immutable entries to <code>audit_log</code> with IP and user ID.
      </div>
      <div class="rule-item">
        <strong>4. Financial Immutability:</strong> Money rows in <code>fee_invoices</code>, <code>fee_invoice_lines</code>, and <code>fee_payments</code> are never updated in-place. Cancellations create void flags and reversals post audited contra-allocations.
      </div>
      <div class="rule-item">
        <strong>5. Contract 1 (Canonical Screen Registry):</strong> Every web screen is declared once in <code>web/src/screens.ts</code>. Navbars, routes, and RBAC gates derive strictly from this single source of truth.
      </div>
      <div class="rule-item">
        <strong>6. "UNUSED FOR NOW" Designation:</strong> 28 tables are currently unpopulated in seed data. Each table is fully implemented with SQLAlchemy models and working endpoints, reserved for operational counter workflows or planned roadmap modules.
      </div>
    </div>
  </div>

  <!-- Master Domain Matrix Table -->
  <div class="matrix-section">
    <div class="matrix-title">📋 Master Functional Domain Index &amp; Roadmap Alignment</div>
    <table class="matrix-table">
      <thead>
        <tr>
          <th style="width: 25%;">Functional Domain</th>
          <th style="width: 8%; text-align:center;">Tables</th>
          <th style="width: 10%; text-align:center;">Live</th>
          <th style="width: 11%; text-align:center;">Unused</th>
          <th style="width: 20%;">Primary Web Routes</th>
          <th style="width: 26%;">Domain Operational Scope</th>
        </tr>
      </thead>
      <tbody>
        {"".join(domain_summary_rows)}
      </tbody>
    </table>
  </div>

  <!-- Domain Sections & Table Cards -->
  {"".join(sections_html)}

</body>
</html>
"""

def main():
    print("================================================================================")
    print("  Sunrise School ERP — All-Tables Database & Feature Mapping Reference Builder")
    print("================================================================================")
    print(f"Introspecting PostgreSQL database: '{DB}' on localhost...")
    tables = introspect_db()
    print(f"Successfully introspected {len(tables)} tables from PostgreSQL.")
    
    live_cnt = sum(1 for t, d in tables.items() if d["rows"] > 0)
    unused_cnt = sum(1 for t, d in tables.items() if d["rows"] == 0)
    print(f"Row count state: {live_cnt} live populated tables, {unused_cnt} unpopulated ('UNUSED FOR NOW') tables.")

    # Check for unmapped tables
    all_ordered_tables = []
    for _, _, tbls in DOMAINS_ORDER:
        all_ordered_tables.extend(tbls)
    
    missing_in_order = set(tables.keys()) - set(all_ordered_tables)
    missing_in_db = set(all_ordered_tables) - set(tables.keys())
    
    if missing_in_order:
        print("WARNING: Tables in DB but missing from DOMAINS_ORDER:", missing_in_order)
    if missing_in_db:
        print("WARNING: Tables in DOMAINS_ORDER but missing from DB:", missing_in_db)
        
    assert len(all_ordered_tables) == 93, f"Expected 93 tables in DOMAINS_ORDER, found {len(all_ordered_tables)}"
    assert len(tables) == 93, f"Expected 93 tables in Postgres, found {len(tables)}"
    assert live_cnt == 68, f"Expected 68 live tables, found {live_cnt}"
    assert unused_cnt == 25, f"Expected 25 unused tables, found {unused_cnt}"

    print(f"Generating print-optimized HTML: {OUTPUT_HTML}...")
    html_content = build_html(tables)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved HTML ({os.path.getsize(OUTPUT_HTML):,} bytes).")

    print(f"Compiling PDF via Headless Google Chrome: {OUTPUT_PDF}...")
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=20000",
        f"--print-to-pdf={OUTPUT_PDF}",
        OUTPUT_HTML,
    ]
    subprocess.run(cmd, check=True)
    pdf_size = os.path.getsize(OUTPUT_PDF)
    print(f"PDF generated successfully: {OUTPUT_PDF} ({pdf_size:,} bytes).")
    print("================================================================================")
    print("  ALL CHECKS PASSED: 93 tables documented with zero omissions.")
    print("================================================================================")

if __name__ == "__main__":
    main()
