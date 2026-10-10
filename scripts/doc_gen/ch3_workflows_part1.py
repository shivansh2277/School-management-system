"""Chapter 4 & 5: Operational Workflows Part 1
Covers:
1. System, Auth, Tenancy & RBAC (1.1 - 1.5)
2. Student & Guardian Master Identity (2.1 - 2.3)
3. Admissions & Student Intake Pipeline (3.1 - 3.8)
4. Academics, Classes & Timetabling (4.1 - 4.2)
5. Daily Student Attendance (5.1 - 5.2)
"""

def render_workflow(wf_id: str, title: str, overview: dict, steps: list, diagram: str, transfers: list, tables: list, lifecycle: str, example: str) -> str:
    transfer_rows = "".join(f"""
      <tr>
        <td style="font-weight:600; text-align:center;">{t[0]}</td>
        <td><code>{t[1]}</code></td>
        <td><code>{t[2]}</code></td>
        <td>{t[3]}</td>
        <td><span class="diagram-op-{t[4].lower()}">{t[4]}</span></td>
        <td>{t[5]}</td>
      </tr>""" for t in transfers)

    table_rows = "".join(f"""
      <tr>
        <td><strong><code>{tbl[0]}</code></strong></td>
        <td>{tbl[1]}</td>
        <td><code>{tbl[2]}</code></td>
        <td><code>{tbl[3]}</code></td>
        <td><code>{tbl[4]}</code></td>
        <td>{tbl[5]}</td>
        <td>{tbl[6]}</td>
      </tr>""" for tbl in tables)

    step_items = "".join(f"<li>{s}</li>" for s in steps)

    return f"""
<div class="workflow-box no-break">
  <div class="workflow-title">
    <span>Workflow {wf_id}: {title}</span>
    <span class="badge">Operational Flow</span>
  </div>

  <!-- A. OVERVIEW -->
  <div class="sub-heading">A. Workflow Overview</div>
  <div class="overview-grid">
    <div class="overview-item"><strong>Real-Life Context:</strong> {overview['real_life']}</div>
    <div class="overview-item"><strong>Primary Actor:</strong> {overview['actor']}</div>
    <div class="overview-item"><strong>Triggering Event:</strong> {overview['trigger']}</div>
    <div class="overview-item"><strong>Business Problem:</strong> {overview['problem']}</div>
    <div class="overview-item" style="grid-column: span 2;"><strong>Expected Outcome:</strong> {overview['outcome']}</div>
  </div>

  <!-- B. STEP-BY-STEP -->
  <div class="sub-heading">B. Step-by-Step Processing Pipeline</div>
  <ol class="step-list">
    {step_items}
  </ol>

  <!-- C. DIAGRAM -->
  <div class="sub-heading">C. Data-Flow Architecture Diagram</div>
  <div class="diagram-card">
{diagram}
  </div>

  <!-- D. DATA TRANSFER TABLE -->
  <div class="sub-heading">D. Data Transfer Table</div>
  <table class="doc-table">
    <thead>
      <tr>
        <th style="width:5%;">Step</th>
        <th style="width:16%;">Source</th>
        <th style="width:16%;">Destination</th>
        <th style="width:25%;">Data Transferred</th>
        <th style="width:10%;">Operation</th>
        <th style="width:28%;">Operational Purpose</th>
      </tr>
    </thead>
    <tbody>
      {transfer_rows}
    </tbody>
  </table>

  <!-- E. TABLE-BY-TABLE EXPLANATION -->
  <div class="sub-heading">E. Table-by-Table Technical Specifications</div>
  <table class="doc-table">
    <thead>
      <tr>
        <th style="width:14%;">Table</th>
        <th style="width:15%;">Purpose</th>
        <th style="width:8%;">Primary Key</th>
        <th style="width:18%;">Important Fields</th>
        <th style="width:15%;">Foreign Keys</th>
        <th style="width:15%;">Data Stored</th>
        <th style="width:15%;">Role in Workflow</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>

  <!-- F. RELATIONSHIPS AND LIFECYCLE -->
  <div class="sub-heading">F. Entity Relationships and Data Lifecycle</div>
  <div style="font-size:7.9pt; color:#334155; margin-bottom:8px; line-height:1.4;">
    {lifecycle}
  </div>

  <!-- G. REAL-LIFE EXAMPLE -->
  <div class="sub-heading">G. Real-Life Execution Scenario</div>
  <div class="scenario-box">
    <strong>Execution Walkthrough:</strong> {example}
  </div>
</div>
"""

def render_ch3_part1() -> str:
    content = """
<div class="section-banner">
  <h2>4. Detailed Operational Workflows: System, Master Data & Academics</h2>
  <p class="desc">Granular data flows for authentication, tenant scoping, student master, admissions, academics, and attendance.</p>
</div>
"""

    # --- 1.1 User Authentication ---
    content += render_workflow(
        wf_id="1.1",
        title="User Authentication, Credential Verification & JWT Issuance",
        overview={
            "real_life": "A school administrator, teacher, or receptionist logs in to access their operational workspace.",
            "actor": "Any valid system user (Admin, Principal, Teacher, Accountant, Receptionist, Parent).",
            "trigger": "User submits email/username and password at <code>/login</code> or the mobile login screen.",
            "problem": "Securely authenticating user identity without exposing plaintext passwords and generating time-bound access claims.",
            "outcome": "A cryptographically signed JWT bearer token containing user ID, school ID, active roles, and granular permissions."
        },
        steps=[
            "<strong>User Action:</strong> The user enters email and password into the login form and clicks 'Sign In'.",
            "<strong>Frontend Processing:</strong> <code>LoginPage.tsx</code> packages credentials into a JSON POST payload and dispatches to <code>POST /api/v1/auth/token</code>.",
            "<strong>Backend Validation:</strong> FastAPI receives request; validates fields against <code>LoginRequest</code> schema. Queries <code>users</code> table by email.",
            "<strong>Credential Verification:</strong> Passes entered password and <code>users.hashed_password</code> to Bcrypt/Passlib. Aborts with HTTP 401 if invalid.",
            "<strong>Role & Permission Resolution:</strong> Backend executes joined query across <code>user_roles</code>, <code>roles</code>, and <code>role_permissions</code> to collect all active permission strings.",
            "<strong>Token Generation:</strong> Encodes user claims (<code>sub=user.id</code>, <code>school_id</code>, <code>roles</code>, <code>permissions</code>, <code>exp</code>) into a signed JWT.",
            "<strong>Final Output:</strong> Token returned in HTTP response; stored in browser <code>localStorage</code> / SecureStore; user redirected to <code>/dashboard</code>."
        ],
        diagram="""[Frontend Login Screen]
       │
       ▼ (HTTP POST /auth/token)
[FastAPI Auth Route (api/auth.py)]
       │
       ├─► [READ] users ───────────────► Check email & Bcrypt hash match
       │
       ├─► [READ] user_roles ──────────► Fetch user's assigned role IDs
       │
       ├─► [READ] roles ───────────────► Resolve role definitions & school scope
       │
       └─► [READ] role_permissions ────► Aggregate permission codes (e.g. 'fees.invoice.read')
       │
       ▼
[Cryptographic JWT Minting] ──────────► Returns Bearer Access Token to Client""",
        transfers=[
            ("1", "Browser Login Form", "FastAPI /auth/token", "email, password", "READ", "Transmit login credentials securely"),
            ("2", "FastAPI Auth Service", "users table", "email filter", "READ", "Fetch user record, status, and hashed_password"),
            ("3", "FastAPI Auth Service", "user_roles table", "user_id filter", "READ", "Identify all roles assigned to this user"),
            ("4", "FastAPI Auth Service", "role_permissions table", "role_id filter", "READ", "Extract granular RBAC permission codes"),
            ("5", "FastAPI Auth Service", "Browser localStorage", "Bearer JWT Token", "LINK", "Authorize subsequent API requests via Authorization header")
        ],
        tables=[
            ("users", "User master credentials", "id (BigInt)", "email, hashed_password, is_active, school_id", "school_id -> schools.id", "User account identities across school", "Authenticates identity and checks active status"),
            ("user_roles", "User-to-role assignment", "id (BigInt)", "user_id, role_id, school_id", "user_id -> users.id, role_id -> roles.id", "Maps users to one or more system roles", "Determines the roles held by the authenticating user"),
            ("roles", "RBAC role definitions", "id (BigInt)", "name, code, is_system, school_id", "school_id -> schools.id", "Standard role catalogs (Admin, Teacher, etc.)", "Labels and groups user authority"),
            ("role_permissions", "Role permissions map", "id (BigInt)", "role_id, permission_id", "role_id -> roles.id, permission_id -> permissions.id", "Granular access rights per role", "Supplies permission strings embedded into the JWT")
        ],
        lifecycle="<strong>Creation & Immutability:</strong> <code>users</code> rows are created during initial school seeding or staff onboarding. Passwords are never stored in plaintext; only one-way Bcrypt hashes exist. <code>user_roles</code> links are tenant-scoped by <code>school_id</code>. Deleting a user soft-deactivates the account by setting <code>is_active = False</code>.",
        example="Principal Dr. Sunita Rao logs in with email <code>admin@sunrisepublic.edu</code>. Backend queries <code>users</code>, validates password hash, queries <code>user_roles</code> returning role 'ADMIN', queries <code>role_permissions</code> returning 91 permissions, and issues a JWT token valid for 24 hours."
    )

    # --- 1.2 Multi-Tenancy Scoping ---
    content += render_workflow(
        wf_id="1.2",
        title="Multi-Tenant School Isolation & Database Scoping",
        overview={
            "real_life": "Ensuring that data from Sunrise Public School is strictly inaccessible to any other school operating on the platform.",
            "actor": "Every authenticated user and automated background process.",
            "trigger": "Every incoming API request intercepted by dependency injection.",
            "problem": "Preventing accidental data leakage between independent schools sharing a single PostgreSQL database instance.",
            "outcome": "Every database query automatically appends <code>WHERE school_id = :school_id</code>."
        },
        steps=[
            "<strong>User Action:</strong> Client application sends an HTTP request with Bearer JWT token in Authorization header.",
            "<strong>Frontend Processing:</strong> <code>client.ts</code> automatically injects the active token into every outgoing Axios/fetch request.",
            "<strong>Backend Dependency Extraction:</strong> FastAPI executes <code>get_current_user</code> dependency, validating JWT signature and extracting <code>school_id</code> claim.",
            "<strong>Database Session Scoping:</strong> All repository queries inherit from <code>TenantBase</code>, which automatically injects <code>school_id</code> into SQLAlchemy queries.",
            "<strong>Query Execution:</strong> PostgreSQL executes the isolated SQL statement; records with different <code>school_id</code> are invisible at the database engine level.",
            "<strong>Final Output:</strong> Data returned strictly belongs to the caller's school."
        ],
        diagram="""[Client Request with JWT Token]
       │
       ▼
[FastAPI Dependency: get_current_user]
       │
       ▼ (Extracts validated school_id from token claims)
[SQLAlchemy Query Builder (TenantBase)]
       │
       ▼ [READ] / [INSERT] / [UPDATE]
[PostgreSQL Table: ANY TENANT TABLE] ──► Automatically filtered: WHERE school_id = :tenant_id
       │
       ▼
[Tenant-Isolated Result Set]""",
        transfers=[
            ("1", "HTTP Request Header", "FastAPI Middleware", "JWT Token", "READ", "Extract cryptographic tenant identity claims"),
            ("2", "Security Context", "SQLAlchemy Engine", "school_id integer", "LINK", "Inject tenant parameter into database query"),
            ("3", "PostgreSQL Engine", "Target Database Table", "WHERE school_id = :id", "READ", "Filter query execution plan strictly to tenant boundary")
        ],
        tables=[
            ("schools", "Tenant master record", "id (BigInt)", "name, code, slug, is_active", "None (Root master)", "Customer school identity and status", "Defines the tenant boundary"),
            ("TenantBase (Model)", "Declarative abstract base", "id (BigInt)", "school_id, created_at, updated_at", "school_id -> schools.id", "Shared columns for 102 of 105 tables", "Enforces foreign key constraint to schools on all tenant rows")
        ],
        lifecycle="<strong>Tenant Invariant:</strong> <code>school_id</code> is declared as a non-nullable foreign key on 102 tables. It cannot be altered once written. Only 3 system-level tables (<code>schools</code>, <code>permissions</code>, and <code>scheduled_jobs</code>) omit <code>school_id</code>.",
        example="A teacher at School ID 1 queries <code>/students</code>. The backend executes <code>SELECT * FROM students WHERE school_id = 1</code>. Even if School ID 2 has 500 students in the same table, 0 records from School ID 2 are returned."
    )

    # --- 1.5 User Access Role Assignment & Security Invalidation ---
    content += render_workflow(
        wf_id="1.5",
        title="User Access Role Assignment, Custom Roles & Token Invalidation",
        overview={
            "real_life": "School Administrator assigns or revokes operational roles (such as Librarian, Teacher, or Accountant) to staff accounts via the User Access console.",
            "actor": "System Administrator or School Principal.",
            "trigger": "Admin updates role assignments for a staff member at <code>/user-access</code> and clicks 'Save Roles'.",
            "problem": "Enforcing granular role-based access control (RBAC), preventing privilege escalation, and ensuring permission changes take immediate effect across sessions.",
            "outcome": "User-role bindings synchronized in <code>user_roles</code>; <code>users.token_version</code> incremented to invalidate stale JWTs; compliance logged in <code>audit_log</code>."
        },
        steps=[
            "<strong>User Action:</strong> Admin opens <code>/user-access</code>, selects a staff user (e.g. <code>librarian@sunrisepublic.edu</code>), toggles role assignments (e.g. checks 'Librarian'), and saves.",
            "<strong>Frontend Processing:</strong> <code>UserAccess.tsx</code> validates selections and dispatches <code>PUT /api/v1/auth/users/{user_id}/roles</code> with payload <code>{'role_names': ['Librarian']}</code>.",
            "<strong>Backend Authorization:</strong> FastAPI verifies caller holds <code>auth.user.manage</code> permission and both caller and target user share the same <code>school_id</code>.",
            "<strong>Role Resolution:</strong> Resolves role IDs from <code>roles</code> table matching school scope; validates role exists.",
            "<strong>Junction Sync:</strong> Executes atomic delete/insert on <code>user_roles</code> table binding the user to the updated role set.",
            "<strong>Security Invalidation:</strong> Increments <code>users.token_version</code> (+1) to force re-authentication or claim refresh on subsequent API calls.",
            "<strong>Audit Log:</strong> Writes compliance record to <code>audit_log</code> recording admin ID, target user ID, timestamp, and new role assignments."
        ],
        diagram="""[Admin Console: /user-access]
       │
       ▼ (PUT /api/v1/auth/users/{user_id}/roles)
[User Access & RBAC Service (api/auth.py)]
       │
       ├─► [READ] users ──────────────► Verify target user exists in school tenant
       ├─► [READ] roles ──────────────► Resolve role IDs for assigned role codes
       ├─► [SYNC] user_roles ─────────► Commit user_id to role_id associations
       ├─► [UPDATE] users ────────────► Increment token_version (+1) for immediate session invalidation
       └─► [INSERT] audit_log ────────► Record administrative compliance entry
       │
       ▼
[Updated RBAC Enforced Across All APIs & Sidebar Route Gates]""",
        transfers=[
            ("1", "User Access Screen", "Auth API", "user_id, role_names", "UPDATE", "Submit updated role assignments"),
            ("2", "Auth API", "roles table", "school_id, name filter", "READ", "Resolve role IDs from system & custom role catalog"),
            ("3", "Auth API", "user_roles table", "user_id, role_id, school_id", "SYNC", "Replace active user-role links"),
            ("4", "Auth API", "users table", "token_version = token_version + 1", "UPDATE", "Invalidate active JWT sessions"),
            ("5", "Auth API", "audit_log table", "user_id, action, details", "INSERT", "Preserve permanent security audit trail")
        ],
        tables=[
            ("users", "User credentials & auth version", "id (BigInt)", "email, token_version, is_active, school_id", "school_id -> schools.id", "User account identities", "Updates token version to invalidate prior tokens"),
            ("roles", "RBAC role catalog", "id (BigInt)", "name, code, is_system, school_id", "school_id -> schools.id", "Role definitions (Admin, Librarian, etc.)", "Supplies role definition and permission template"),
            ("user_roles", "User-role mapping", "id (BigInt)", "user_id, role_id, school_id", "user_id -> users.id, role_id -> roles.id", "Junction table binding users to roles", "Persists effective roles assigned to the user"),
            ("audit_log", "Security compliance trail", "id (BigInt)", "user_id, action, entity_type, details", "user_id -> users.id, school_id -> schools.id", "Immutable chronological audit events", "Records administrative role change event")
        ],
        lifecycle="<strong>Immediate Revocation & Invariant:</strong> Role updates take effect immediately because <code>token_version</code> is incremented on the <code>users</code> table, and incoming requests validate the token's embedded version against the database. Stale tokens are rejected with HTTP 401.",
        example="Admin assigns the dedicated <code>Librarian</code> role to staff user <code>librarian@sunrisepublic.edu</code>. The system maps the role in <code>user_roles</code>, increments <code>token_version</code>, and logs the change. When logging in, the user receives permissions restricted strictly to the Library circulation desk, cataloging, and returns—with no access to fees, payroll, or admissions."
    )

    # --- 2.1 Permanent Student Registration ---
    content += render_workflow(
        wf_id="2.1",
        title="Permanent Student Master Identity Creation & Admission Number Allocation",
        overview={
            "real_life": "A newly admitted student is officially enrolled into the school's permanent records registry.",
            "actor": "School Registrar or Admission Officer.",
            "trigger": "Admissions conversion execution or direct student registration.",
            "problem": "Establishing an unchangeable lifetime record for a student that persists across all future years and class promotions.",
            "outcome": "Permanent records created in <code>users</code> and <code>students</code> with a unique, unalterable <code>admission_no</code>."
        },
        steps=[
            "<strong>User Action:</strong> Officer inputs child's legal name, date of birth, gender, address, and admission number.",
            "<strong>Frontend Processing:</strong> <code>StudentForm.tsx</code> validates date formats and required fields; submits <code>POST /api/v1/students</code>.",
            "<strong>Backend Validation:</strong> <code>api/admin/students.py</code> checks that <code>admission_no</code> is unique for this <code>school_id</code>.",
            "<strong>User Record Creation:</strong> Inserts a parent row into <code>users</code> table with default student role credentials.",
            "<strong>Student Record Insertion:</strong> Inserts child row into <code>students</code> table referencing <code>users.id</code>.",
            "<strong>Family Relationship Linkage:</strong> Links the student to guardian records via <code>student_guardian</code> table.",
            "<strong>Final Output:</strong> Permanent student record established; returns student master ID and profile data."
        ],
        diagram="""[Admission Officer Form]
       │
       ▼ (POST /api/v1/students)
[Students API Service]
       │
       ├─► [INSERT] users ──────────────► Creates base user account (email, name)
       │         │
       │         ▼ (users.id)
       ├─► [INSERT] students ───────────► Creates lifetime student record (admission_no, dob, gender)
       │         │
       │         ▼ (students.id)
       └─► [INSERT] student_guardian ───► Links to existing or new guardians (guardians.id)
       │
       ▼
[Student Master Record Created]""",
        transfers=[
            ("1", "Frontend Form", "Backend API", "Name, DOB, Gender, Admission No", "INSERT", "Submit applicant biodata for registration"),
            ("2", "Backend Service", "users table", "email, full_name, role='student'", "INSERT", "Create authentication principal"),
            ("3", "Backend Service", "students table", "user_id, admission_no, dob, gender", "INSERT", "Store permanent student identity"),
            ("4", "Backend Service", "student_guardian table", "student_id, guardian_id, relation", "LINK", "Establish family legal guardianship")
        ],
        tables=[
            ("users", "Authentication identity", "id (BigInt)", "email, full_name, is_active", "school_id -> schools.id", "User credentials", "Stores login and name for student"),
            ("students", "Lifetime student master", "id (BigInt)", "admission_no, dob, gender, address, admission_date", "user_id -> users.id, school_id -> schools.id", "Permanent student records", "Primary entity representing the child for life"),
            ("guardians", "Parent/Guardian master", "id (BigInt)", "user_id, occupation, annual_income", "user_id -> users.id, school_id -> schools.id", "Parent profile data", "Stores family contact and demographic info"),
            ("student_guardian", "Student-Parent junction", "id (BigInt)", "student_id, guardian_id, relation, is_primary", "student_id -> students.id, guardian_id -> guardians.id", "M:N student-parent relationships", "Binds child to parents")
        ],
        lifecycle="<strong>Lifetime Persistence:</strong> <code>students.admission_no</code> is strictly unique per school (<code>uq_student_admission_no</code>). Once assigned, it is never changed or reassigned. When a student leaves or graduates, <code>students.status</code> is updated to <code>withdrawn</code> or <code>alumni</code>; the row is never physically deleted.",
        example="Student 'Aarav Sharma' is admitted. System creates <code>users.id = 101</code>, inserts <code>students.id = 55</code> with <code>admission_no = 'ADM-2024-001'</code>, and links to Father Rajesh Sharma via <code>student_guardian</code>."
    )

    # --- 3.3 Application Intake ---
    content += render_workflow(
        wf_id="3.3",
        title="Student Admission Application Intake & Multi-Tab Dossier Submission",
        overview={
            "real_life": "Parents submit an official admission application for their child, either online or through the school front office.",
            "actor": "Parent or Front-Desk Receptionist / Admission Officer.",
            "trigger": "Submission of the 7-tab admission dossier on <code>/admission/applications</code>.",
            "problem": "Capturing comprehensive child biodata, guardian contacts, previous school records, and uploaded documents before granting admission.",
            "outcome": "Application record created with status <code>submitted</code> and assigned application number (e.g. <code>APP-2026-001</code>)."
        },
        steps=[
            "<strong>User Action:</strong> Officer/Parent fills out 7 tabs: Biodata, Guardians, Documents, Academic History, Siblings, and Medical.",
            "<strong>Frontend Processing:</strong> <code>ApplicationForm.tsx</code> validates file uploads and required fields; submits <code>POST /api/v1/admission/applications</code>.",
            "<strong>Backend Validation:</strong> Checks that the target <code>admission_cycle_id</code> is in <code>active</code> status. Verifies seat availability config in <code>cycle_class_config</code>.",
            "<strong>Application Header Insertion:</strong> Inserts parent row into <code>applications</code> table with status <code>submitted</code>.",
            "<strong>Sub-Entity Insertions:</strong> Concurrently inserts linked rows into <code>application_guardians</code>, <code>application_academic_histories</code>, and <code>application_siblings</code>.",
            "<strong>Document Registration:</strong> Uploads certificates to storage (MinIO/S3) and logs records in <code>documents</code> table linked to the application.",
            "<strong>Final Output:</strong> Complete dossier available for academic review and assessment scoring."
        ],
        diagram="""[Parent / Receptionist Form]
       │
       ▼ (POST /api/v1/admission/applications)
[FastAPI Admission Service (api/admin/applications.py)]
       │
       ├─► [READ] admission_cycles ────────► Validate cycle is active
       │
       ├─► [INSERT] applications ──────────► Create application dossier (APP-2026-001)
       │         │
       │         ├─► [INSERT] application_guardians ──► Insert parent/guardian info
       │         ├─► [INSERT] application_academic ───► Insert previous school records
       │         ├─► [INSERT] application_siblings ───► Link existing sibling admission_no
       │         └─► [INSERT] documents ──────────────► Store birth cert & transfer cert
       │
       ▼
[Application Dossier Ready for Review]""",
        transfers=[
            ("1", "Frontend Dossier", "Backend API", "7-Tab Application JSON", "INSERT", "Submit applicant comprehensive dossier"),
            ("2", "Admission Service", "applications table", "cycle_id, student name, class_name", "INSERT", "Create core application tracking header"),
            ("3", "Admission Service", "application_guardians", "name, phone, relation, income", "INSERT", "Store applicant parent contact data"),
            ("4", "Admission Service", "documents table", "file_path, doc_type, application_id", "INSERT", "Store uploaded certificates")
        ],
        tables=[
            ("applications", "Admission application header", "id (BigInt)", "application_no, cycle_id, first_name, status", "cycle_id -> admission_cycles.id", "Applicant master application", "Primary tracking entity in admission pipeline"),
            ("application_guardians", "Applicant parent details", "id (BigInt)", "application_id, name, mobile, relation", "application_id -> applications.id", "Parent data for applicants", "Stores parent info prior to enrollment"),
            ("documents", "Document vault", "id (BigInt)", "document_type_id, file_path, owner_id", "owner_id -> applications.id", "Uploaded PDFs and certificates", "Holds birth certificate and transfer cert files")
        ],
        lifecycle="<strong>Pipeline Transition:</strong> Application begins in <code>draft</code> or <code>submitted</code> status. As it progresses through screening, status transitions through <code>under_review</code>, <code>shortlisted</code>, <code>approved</code>, or <code>rejected</code>.",
        example="Applicant 'Priya Verma' applies for Class 1. Application <code>APP-2026-001</code> is inserted into <code>applications</code> with 2 guardian rows in <code>application_guardians</code> and a birth certificate in <code>documents</code>."
    )

    # --- 3.7 1-Click Enrollment Conversion ---
    content += render_workflow(
        wf_id="3.7",
        title="1-Click Admission Conversion: Applicant to Active Student & Enrolment",
        overview={
            "real_life": "An approved applicant pays the admission fee and is formally converted into a full-fledged student of the school.",
            "actor": "Admission Officer / Principal.",
            "trigger": "Clicking 'Convert to Student' on an approved application in <code>/admission/applications</code>.",
            "problem": "Manually re-entering applicant data into student, user, guardian, and enrollment tables leads to human error and duplicate records.",
            "outcome": "Single atomic transaction creates <code>users</code>, <code>students</code>, <code>guardians</code>, <code>student_guardian</code>, <code>enrolments</code>, and <code>student_fee_plans</code>."
        },
        steps=[
            "<strong>User Action:</strong> Officer selects class section (e.g. '1-A') and clicks 'Confirm Conversion'.",
            "<strong>Frontend Processing:</strong> <code>ConversionModal.tsx</code> submits <code>POST /api/v1/admission/applications/{id}/convert</code> with section and fee plan selections.",
            "<strong>Backend Atomic Transaction:</strong> <code>services/conversion.py</code> initiates a database transaction block.",
            "<strong>User & Student Creation:</strong> Creates student <code>users</code> record, generates unique <code>admission_no</code>, and inserts <code>students</code> row.",
            "<strong>Guardian Provisioning:</strong> Converts <code>application_guardians</code> into permanent <code>guardians</code> and <code>student_guardian</code> records.",
            "<strong>Enrolment Allocation:</strong> Calculates next available roll number in target section; inserts active record into <code>enrolments</code>.",
            "<strong>Fee Plan Linking:</strong> Links the newly created enrollment to the selected class fee plan in <code>student_fee_plans</code>.",
            "<strong>Application Status Update:</strong> Updates <code>applications.status = 'enrolled'</code> and sets <code>applications.student_id = students.id</code>.",
            "<strong>Final Output:</strong> Student is now live on class nominal rolls, attendance registers, and fee billing schedules."
        ],
        diagram="""[Conversion Modal]
       │
       ▼ (POST /applications/{id}/convert)
[FastAPI Conversion Service (services/conversion.py)]
       │
       ├─► [INSERT] users (Student) ────────► Create student user login
       ├─► [INSERT] students ───────────────► Create lifetime student record (admission_no)
       ├─► [INSERT] users & guardians ──────► Create guardian user & profile records
       ├─► [INSERT] student_guardian ───────► Bind student to guardian
       ├─► [INSERT] enrolments ─────────────► Create year/section membership (roll_no)
       ├─► [INSERT] student_fee_plans ──────► Attach annual class fee schedule
       └─► [UPDATE] applications ───────────► Set status = 'enrolled', student_id = students.id
       │
       ▼
[Student Fully Active in Academic & Fee Engines]""",
        transfers=[
            ("1", "applications table", "students table", "first_name, dob, gender, address", "INSERT", "Promote applicant biodata to permanent student record"),
            ("2", "application_guardians", "guardians table", "name, phone, occupation", "INSERT", "Create permanent guardian profiles"),
            ("3", "Backend Allocator", "enrolments table", "student_id, academic_year_id, section_id, roll_no", "INSERT", "Enroll child into active class section"),
            ("4", "Backend Allocator", "student_fee_plans", "enrolment_id, fee_plan_id", "INSERT", "Assign billing plan to student enrollment"),
            ("5", "Backend Allocator", "applications table", "status='enrolled', student_id", "UPDATE", "Close admission lifecycle and preserve audit linkage")
        ],
        tables=[
            ("applications", "Applicant application", "id (BigInt)", "status, student_id", "cycle_id -> admission_cycles.id", "Originating application record", "Updated to 'enrolled' with FK to created student"),
            ("students", "Lifetime student master", "id (BigInt)", "admission_no, user_id, status", "user_id -> users.id", "Permanent student record", "Inserted as active student"),
            ("enrolments", "Class annual membership", "id (BigInt)", "student_id, class_section_id, roll_no", "student_id -> students.id, section_id -> class_sections.id", "Session class membership", "Created to place student in active classroom roster")
        ],
        lifecycle="<strong>Atomic Conversion:</strong> The entire process executes inside <code>db.transaction()</code>. If any step fails (e.g. duplicate admission number or roll number conflict), the entire transaction rolls back cleanly, leaving the application in its prior state.",
        example="Applicant 'Priya Verma' (APP-2026-001) is converted. System creates <code>students.id = 101</code> (admission_no 'ADM-2026-015'), assigns roll number 26 in Class 1-A (<code>enrolments.id = 101</code>), and updates application status to 'enrolled'."
    )

    # --- 3.8 Admission Document Overrides & Exceptions Queue ---
    content += render_workflow(
        wf_id="3.8",
        title="Admission Document Overrides & Exceptions Automatic Pending Queue",
        overview={
            "real_life": "A parent or applicant submits an admission application where a mandatory document (such as Transfer Certificate or Birth Certificate) is temporarily unavailable, generating a document exception request that automatically routes to the Admin review queue.",
            "actor": "Parent / Applicant (submission), Admission Officer / Principal (review & determination).",
            "trigger": "Parent requests document exception during application submission, or admission staff files an override for an applicant.",
            "problem": "Allowing applicants with pending paperwork to progress without getting stuck at mandatory document gates, while ensuring zero exceptions slip through without auditable administrative approval.",
            "outcome": "Override record queued in <code>application_document_overrides</code> with <code>status='pending'</code>; automatically presented on <code>/admissions/overrides-exceptions</code> without manual searching; reviewed with 1-click Approve or Reject."
        },
        steps=[
            "<strong>User / Intake Action:</strong> During application intake, an exception request is flagged for a missing mandatory document with a stated reason.",
            "<strong>Automatic Queue Ingestion:</strong> Backend inserts row into <code>application_document_overrides</code> with <code>status='pending'</code>, <code>application_id</code>, <code>document_type</code>, and <code>reason</code>.",
            "<strong>Staff Access:</strong> Admission officer navigates to <code>/admissions/overrides-exceptions</code>. The view automatically requests <code>GET /api/v1/admissions/overrides?status=pending</code>.",
            "<strong>Queue Presentation:</strong> Backend executes an outer join across <code>application_document_overrides</code> and <code>applications</code>, returning candidate name, application number, document name, submission timestamp, and reason directly in the list.",
            "<strong>Officer Adjudication:</strong> Officer reviews the case and clicks 'Approve' or 'Reject' with optional review notes.",
            "<strong>Status & Audit Update:</strong> Backend calls <code>PUT /api/v1/admissions/overrides/{id}/status</code>, setting <code>status='approved'</code> (or <code>'rejected'</code>), stamping <code>reviewed_by_id</code> and <code>reviewed_at</code>.",
            "<strong>Gate Clearance:</strong> Verification checklist detects approved override, clearing the document requirement for merit list generation and final enrollment."
        ],
        diagram="""[Parent / Applicant Intake (Public Web / Portal)]
       │
       ▼
[INSERT] application_document_overrides (status='pending', document_type, reason)
       │
       ▼ (Automatic Ingestion into Pending Queue)
[Admission Staff Screen: /admissions/overrides-exceptions]
       │
       ▼ (GET /admissions/overrides?status=pending — No Manual Search Required)
[Joined Query: application_document_overrides + applications]
       │
       ▼ (Officer Clicks 'Approve' or 'Reject')
[Admissions API: PUT /api/v1/admissions/overrides/{id}/status]
       │
       ├─► [UPDATE] application_document_overrides ──► Set status='approved'/'rejected', reviewed_by_id, reviewed_at
       ├─► [CHECK] Admission Verification Gate ──────► Approved exception satisfies mandatory document rule
       └─► [INSERT] audit_log ────────────────────────► Log compliance audit trail
       │
       ▼
[Applicant Cleared for Scoring, Merit List & 1-Click Conversion]""",
        transfers=[
            ("1", "Application Intake Form", "Admissions API", "application_id, document_type, reason", "INSERT", "Create document exception request in pending queue"),
            ("2", "Overrides Screen", "Admissions API", "status='pending' filter", "READ", "Fetch all pending document exceptions automatically"),
            ("3", "Overrides Screen", "Admissions API", "override_id, status, notes", "UPDATE", "Submit officer approval or rejection decision"),
            ("4", "Admissions API", "application_document_overrides", "status, reviewed_by_id, reviewed_at", "UPDATE", "Commit reviewer decision and timestamp"),
            ("5", "Admissions API", "audit_log table", "user_id, action='OVERRIDE_REVIEW', details", "INSERT", "Record compliance review trail")
        ],
        tables=[
            ("application_document_overrides", "Document exception requests", "id (BigInt)", "application_id, document_type, reason, status, reviewed_by_id, reviewed_at", "application_id -> applications.id, reviewed_by_id -> users.id", "Document override requests and decisions", "Maintains pending queue and approval audit state"),
            ("applications", "Applicant admission dossier", "id (BigInt)", "application_no, first_name, last_name, status", "cycle_id -> admission_cycles.id", "Core applicant dossier", "Provides student identity and links to checklist gates"),
            ("audit_log", "Security & compliance trail", "id (BigInt)", "user_id, action, entity_type, details", "user_id -> users.id, school_id -> schools.id", "Immutable audit trail", "Records reviewer decision and notes")
        ],
        lifecycle="<strong>Pending Queue Invariant:</strong> Exception requests start with <code>status = 'pending'</code>. Reviewing transitions the record to terminal state <code>approved</code> or <code>rejected</code> with an immutable reviewer ID and timestamp. Approved overrides satisfy mandatory document gates without modifying original file storage.",
        example="Applicant Rahul Sharma (APP-1024) requests an exception for 'Birth Certificate' because the official municipal copy is delayed. The request automatically surfaces in the Overrides Queue as Pending. Admission Officer Sunita reviews the justification and clicks 'Approve'. The checklist validation gate recognizes the approved override, clearing Rahul for final merit conversion."
    )

    # --- 4.1 Class & Section Mapping ---
    content += render_workflow(
        wf_id="4.1",
        title="Class, Section, Class Teacher & Subject Allocation",
        overview={
            "real_life": "Academic coordinators structure classes (e.g. Class 10-A), assign class teachers, and designate subject faculties.",
            "actor": "Academic Coordinator / Vice Principal.",
            "trigger": "Beginning of academic term or faculty reassignment at <code>/classes</code>.",
            "problem": "Maintaining clear pedagogical responsibility for student attendance, subject instruction, and marks entry.",
            "outcome": "Updated <code>class_sections</code> and <code>class_subject_teacher</code> records gating attendance and exam entry."
        },
        steps=[
            "<strong>User Action:</strong> Coordinator opens Class 10-A on <code>/classes</code>, assigns Class Teacher, and maps Mathematics to Teacher TCH003.",
            "<strong>Frontend Processing:</strong> <code>ClassDetail.tsx</code> submits updates via <code>PUT /api/v1/admin/classes/sections/{id}</code>.",
            "<strong>Backend Validation:</strong> Verifies employee exists and is active; checks for timetable clashes or double-booking.",
            "<strong>Class Section Update:</strong> Updates <code>class_sections.class_teacher_id = employee.id</code>.",
            "<strong>Subject Teacher Mapping:</strong> Upserts into <code>class_subject_teacher</code> table with <code>class_section_id</code>, <code>subject_id</code>, and <code>teacher_id</code>.",
            "<strong>Final Output:</strong> Teacher TCH003 now possesses permission to take attendance and enter marks for Class 10-A Mathematics."
        ],
        diagram="""[Academic Coordinator Screen]
       │
       ▼ (PUT /admin/classes/sections/{id})
[Classes API Service (api/admin/classes.py)]
       │
       ├─► [UPDATE] class_sections ────────► Set class_teacher_id = employee.id
       │
       └─► [INSERT / UPDATE] class_subject_teacher ──► Link section + subject + teacher
       │
       ▼
[Faculty Gated to Class Attendance & Exam Marks Entry]""",
        transfers=[
            ("1", "Frontend Form", "Classes API", "class_section_id, teacher_id, subject_id", "UPDATE", "Submit faculty teaching assignments"),
            ("2", "Classes API", "class_sections table", "class_teacher_id", "UPDATE", "Designate official class teacher for roll-call"),
            ("3", "Classes API", "class_subject_teacher", "class_section_id, subject_id, teacher_id", "INSERT", "Authorize subject teacher for grading")
        ],
        tables=[
            ("class_sections", "Classroom sections", "id (BigInt)", "class_name, section_name, class_teacher_id", "class_teacher_id -> employees.id", "Classroom divisions (e.g. 10-A)", "Stores class teacher responsible for morning roll"),
            ("class_subject_teacher", "Subject faculty mapping", "id (BigInt)", "class_section_id, subject_id, teacher_id", "subject_id -> subjects.id, teacher_id -> employees.id", "Subject-teacher allocations", "Controls which teacher grades which subject")
        ],
        lifecycle="<strong>Academic Scoping:</strong> <code>class_sections</code> belong to a specific <code>academic_year_id</code>. When a new school year begins, fresh sections are created or rolled over; faculty mappings are established per session.",
        example="Teacher Vikram Singh (TCH003) is assigned as Class Teacher of Class 10-A and Mathematics instructor. <code>class_sections.class_teacher_id</code> is updated to Vikram's employee ID, allowing him to mark morning roll-call."
    )

    # --- 5.1 Student Daily Attendance ---
    content += render_workflow(
        wf_id="5.1",
        title="Student Daily Attendance Roll-Call & Register Submission",
        overview={
            "real_life": "Every morning at 08:30 AM, class teachers take roll call, marking students present, absent, late, or on approved leave.",
            "actor": "Class Teacher via Web Console or Mobile Faculty App.",
            "trigger": "Teacher opens daily register on <code>/attendance</code> or mobile attendance tab.",
            "problem": "Accurately tracking daily pupil presence, detecting patterns of absenteeism, and triggering parent alerts.",
            "outcome": "Daily attendance records committed to <code>attendance</code> table for all students in the section."
        },
        steps=[
            "<strong>User Action:</strong> Teacher marks statuses (P, A, L, M) for all students in Class 10-A and clicks 'Submit Register'.",
            "<strong>Frontend Processing:</strong> <code>AttendanceRegister.tsx</code> packages roll records into payload and calls <code>POST /api/v1/attendance/mark</code>.",
            "<strong>Backend Validation:</strong> Validates caller is authorized class teacher or admin. Checks date is not a declared holiday in <code>holidays</code> table.",
            "<strong>Batch Attendance Upsert:</strong> Executes bulk SQL upsert into <code>attendance</code> table on composite key <code>(enrolment_id, date)</code>.",
            "<strong>Attendance Metrics Cache:</strong> Invalidates real-time stats cache; updates today's attendance summary on Dashboard.",
            "<strong>Final Output:</strong> Attendance register locked; absent students immediately flagged on the admin dashboard."
        ],
        diagram="""[Class Teacher Mobile / Web Screen]
       │
       ▼ (POST /api/v1/attendance/mark)
[Attendance API Service (api/admin/attendance.py)]
       │
       ├─► [READ] holidays ────────────► Check date is not a gazetted holiday
       │
       ├─► [READ] enrolments ──────────► Verify active roster for section
       │
       └─► [INSERT / UPDATE] attendance ──► Upsert (enrolment_id, date, status='present'|'absent')
       │
       ▼
[Attendance Overview Card & Shortage Alarms Updated]""",
        transfers=[
            ("1", "Teacher Screen", "Attendance API", "class_section_id, date, list of (enrolment_id, status)", "INSERT", "Transmit daily roll statuses"),
            ("2", "Attendance API", "attendance table", "enrolment_id, date, status, recorded_by", "INSERT", "Commit student daily presence records")
        ],
        tables=[
            ("attendance", "Student daily attendance", "id (BigInt)", "enrolment_id, date, status, remarks", "enrolment_id -> enrolments.id", "Daily pupil attendance log (5,800+ rows)", "Records actual presence/absence for each student day"),
            ("enrolments", "Class enrollment roster", "id (BigInt)", "student_id, class_section_id, roll_no", "section_id -> class_sections.id", "Active pupils in section", "Provides valid enrolment IDs for the roll-call")
        ],
        lifecycle="<strong>Year-Scoped Foreign Key:</strong> Notice that <code>attendance.enrolment_id</code> points at <code>enrolments.id</code>, NOT <code>students.id</code>! Attendance belongs strictly to the child's academic session in that specific class. Promoting the child next year preserves past attendance intact.",
        example="Teacher marks Class 10-A on 17 Sep 2026. 40 records are upserted into <code>attendance</code>: 36 marked <code>present</code>, 2 marked <code>absent</code>, and 2 marked <code>leave</code>. The dashboard immediately updates to show 90% attendance."
    )

    return content
