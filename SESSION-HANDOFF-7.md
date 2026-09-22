# SESSION-HANDOFF-7: Complete Admission Workflow & Immediate Student Enrollment Specification

> **Target Implementation Session:** Session 7  
> **Status:** READY FOR EXECUTION  
> **Branch:** `slice/office-feedback` (strictly local development; do NOT push to remote)  
> **Test Baseline:** 708 passed, 1 skipped, 0 failed (100% green with `school-management-system/.venv/Scripts/python.exe -m pytest -q`)  
> **Alembic Revision Head:** `b2c3d4e5f6a7` (`enrolment_id_refactor.py`)  
> **Corpus / Repository Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 0. AUTHORITATIVE PRODUCT OVERRIDES & LOCKED DECISIONS

The following 10 product decisions override any conflicting statements in earlier blueprints, handoffs, or discussions:

1. **Receptionist Persona Boundary:** Receptionist is responsible **ONLY** for the Enquiry workflow (logging walk-in/phone enquiries, saving enquiry details, printing official enquiry slips, and logging follow-up interactions). **Do NOT give Receptionist application-processing or application-fee permissions if they are not present already.**
2. **Admission Cell / Officer Workflow Ownership:** The Admission Cell / Admission Officer owns the complete Application workflow:
   - Open / convert enquiry to application (as permitted)
   - Complete and edit application dossiers
   - Submit applications (validating mandatory fields)
   - Verify required applicant information and uploaded documents
   - Collect application fee
   - Print and view official application fee receipts and A4 dossiers
3. **NO SEPARATE "CONVERT TO STUDENT" ACTION:** There is **NO** separate "Convert to Student" button or manual conversion step anywhere in the UI or operational flow.
4. **Payment as the Sole Enrollment Trigger:** Successful application-fee payment is the **single, automatic trigger** for student enrollment.
5. **Atomic Enrollment Payload:** The single successful payment operation must **atomically create/update**:
   - `application_payments` record (with sequential receipt number)
   - `students` record (permanent institutional identity with admission number)
   - `enrolments` record (annual class/section membership for target academic year)
   - `applications.student_id` linkage
   - `applications.status = ApplicationStatus.enrolled`
6. **Strict All-or-Nothing Rollback:** If any database operation inside this transaction fails (e.g., section capacity full, missing guardian, sequence failure), **all database changes from that entire operation must roll back completely**. No payment is recorded and no orphan student is created.
7. **Idempotency Protection:** Payment collection must strictly honor `idempotency_key` so that network retries or double-clicks return the existing receipt and student without duplicate charges or enrollments.
8. **Configured Application Fee (NO Hardcoding):** The application fee **MUST come from the configured admission cycle** (`AdmissionCycle.application_fee`). Never hardcode ₹500 or any other amount in backend calculations or frontend components.
9. **Maximum Logic Reuse:** Reuse existing verified logic wherever possible: student creation, enrolment, section balancing, receipt sequencing, RBAC, audit logging, and authentication. Do not reinvent what is already tested and green.
10. **Canonical Master Acceptance Test:**
    $$\text{Enquiry} \longrightarrow \text{Application} \longrightarrow \text{Complete} \longrightarrow \text{Submit} \longrightarrow \text{Pay Fee} \longrightarrow \text{Student Created} \longrightarrow \text{Enrolment Created} \longrightarrow \text{Visible in School Roster}$$

---

## 1. CURRENT PROJECT STATE

### 1.1 Git Branch & Environment
- **Branch:** `slice/office-feedback`
- **Python Runtime:** Python 3.13 (`.venv/Scripts/python.exe`)
- **PostgreSQL Database:** `postgresql://postgres:postgres@localhost:5432/sunrise_test`
- **Frontend Stack:** React 18, Vite 5 (`web/`), TailwindCSS, React Query v5, Lucide React
- **Mobile Stack:** React Native 0.76.7, Expo 52 (`mobile/`)
- **Active Servers:**
  - Backend API: `http://localhost:8078`
  - Web Frontend: `http://localhost:5173`

### 1.2 Baseline Verification Metrics
- **Pytest Suite:** 708 passed, 1 skipped, 0 failed across 25 test suites in ~153 seconds.
- **Database Schema Documentation:** 17/17 checks passed with 0 drift (`python scripts/verify_db_docs.py`). Total 93 tables, 68 live populated tables.
- **TypeScript Health:** 0 compiler errors in `web/` (`npx tsc --noEmit`) and `mobile/`.
- **Expo Doctor:** 21/21 checks passed.

### 1.3 Relevant Existing Admission Modules
- **Database Models (`backend/app/models/`):**
  - `admission.py`: `AdmissionCycle`, `CycleClassConfig`, `Enquiry`, `EnquiryInteraction`
  - `application.py`: `Application`, `ApplicationGuardian`, `ApplicationSibling`, `ApplicationMedical`
  - `application_payment.py`: `ApplicationPayment`
  - `user.py`: `User`, `Student`, `Guardian`, `StudentGuardian`
  - `academic.py`: `AcademicYear`, `ClassSection`, `Enrolment`
  - `document.py`: `Document`
- **Backend API Routes (`backend/app/api/admin/`):**
  - `admission.py`: Cycle setup, seat quotas, enquiries register (`/admin/admission/enquiries`), timeline interactions.
  - `applications.py`: Draft creation, multi-tab updates, guardian CRUD, document attachments, status moves (`/admin/admission/applications`).
  - `conversion.py`: Payment recording (`/payments`), voiding (`/payments/{id}`), preview (`/conversion-preview`), conversion (`/convert`).
  - `admission_documents.py`, `admission_assessment.py`, `selection.py`, `admission_reports.py`.
- **Frontend Pages & Components (`web/src/pages/admission/`):**
  - `Enquiries.tsx`: Enquiry list, filters by cycle/status/search, quick enquiry modal, timeline viewer.
  - `Applications.tsx`: 7-tab application management console (Overview, Guardians, Documents, Evaluation, Decision, Fees & Conversion, Medical).
  - `PrintableApplicationForm.tsx` (`web/src/components/recruitment/`): Reference printable template using Tailwind `@media print`.

### 1.4 Unfinished Admission Work (Target for Session 7)
1. **Persona Separation in UI:** Receptionist currently sees elements beyond enquiry intake; Receptionist must be focused strictly on Enquiries, while Admission Officer owns Application intake and processing.
2. **Missing Printable Slips:** No "Print Enquiry Slip" in `Enquiries.tsx`, no "Print Application Dossier" (CBSE A4) or "Print Fee Receipt" voucher in `Applications.tsx`.
3. **Manual Conversion Disconnect:** Tab 6 of `Applications.tsx` currently has a separate "Convert to Enrolled Student" button. This must be eliminated.
4. **Automated Conversion on Payment:** Fee collection must invoke conversion logic automatically and atomically, returning the receipt and student info in one response.
5. **Configured Application Fee Sourcing:** Payment modal and backend must pull fee from `cycle.application_fee`, never a hardcoded constant.

---

## 2. CANONICAL ARCHITECTURE RULES

All implementation in Session 7 must strictly follow these core project rules:

1. **Multi-Tenant Architecture & `school_id` Scoping:**
   - Every table in the admission workflow inherits from `TenantBase` (`school_id`).
   - Every database query in services and endpoints must be scoped by `school_id`. No cross-tenant reads or writes are permitted.
2. **Permanent Identity vs Academic Membership (`enrolment_id` invariant):**
   - `students.id`: Permanent lifetime student identity in the institution. Never tied to an academic year.
   - `enrolments.id`: Specific class and academic year membership (`student_id`, `academic_year_id`, `class_section_id`, `roll_no`).
   - All academic facts (attendance, exam marks, fees, report cards) scope strictly to `enrolment_id`.
   - Conversions MUST create BOTH a `Student` row AND an initial `Enrolment` row.
3. **Applicant Lifecycle Isolation:**
   - An applicant in `applications` is NOT a user and NOT a student while in the funnel.
   - Login accounts (`User`) for student and parent are created ONLY upon payment/conversion.
4. **Financial Ledger Immutability:**
   - `application_payments` records are financial source-of-truth documents.
   - Payments are **NEVER deleted or updated in place**. Voiding an invalid receipt is achieved strictly by setting `status = PaymentStatus.voided` and recording `void_reason`.
   - Sequential receipt numbers (`audit.next_number(...)`) must never have gaps re-used.
   - Idempotency key (`idempotency_key`) must be enforced: two clicks on "Collect" must return the existing receipt, never creating a duplicate charge.
5. **Service & Route Transaction Boundaries:**
   - **Service Layer (`app/services/`):** Must invoke `db.flush()` to allocate IDs and validate constraints without committing. Never call `db.commit()` inside reusable service helper methods.
   - **Route Layer (`app/api/`):** Boundary where `db.commit()` is invoked after all operations succeed.
6. **Frontend Design System:**
   - Styling: Strict Tailwind CSS with semantic tokens (`bg-surface`, `bg-ground`, `text-ink`, `text-ink-soft`, `text-ink-faint`, `border-rule`, `border-primary`).
   - Icons: `lucide-react`.
   - Modals: Reusable `Modal` component with clean exit and escape handling.
   - Printing: Pure browser printing using `@media print` CSS utility classes and `window.print()`.

---

## 3. ADMISSION WORKFLOW — FINAL SPECIFICATION

```
  ========================================================================================
                           RECEPTIONIST ROLE (FRONT DESK ENQUIRIES ONLY)
  ========================================================================================
   [ Walk-in / Phone Parent ]
              │
              ▼
   [ 1. Log Enquiry ] ─────────► [ Save to Database ]
              │                              │
              └──────────────────────────────┴──────────────► [ Print Enquiry Slip (A5) ]
                                                             (Parent copy with checklist)

  ========================================================================================
                    ADMISSION CELL / ADMISSION OFFICER ROLE (APPLICATION WORKFLOW)
  ========================================================================================
   [ 2. Open / Convert Enquiry to Application ]
   (Permitted staff converts Enquiry ──► creates Application Draft with contact prefill)
              │
              ▼
   [ 3. Complete / Edit Application Dossier ]
   (Applicant profile, academic history, parent records, medical, address, documents upload)
              │
              ▼
   [ 4. Verify Documents & Submit Application ]
   (Marksheet, Birth Certificate, Aadhaar verified; mandatory dossier fields locked)
              │
              ▼
   [ 5. Collect Application Fee ] ◄── (Fee amount dynamically loaded from cycle.application_fee)
              │
              ▼
  ╔══════════════════════════════════════════════════════════════════════════════════════╗
  ║                 CRITICAL AUTOMATION: ATOMIC CONVERSION ON PAYMENT                    ║
  ╠══════════════════════════════════════════════════════════════════════════════════════╣
  ║  Inside a SINGLE DATABASE TRANSACTION:                                              ║
  ║  1. Validate application status, documents, and cycle configuration                 ║
  ║  2. Read fee amount from cycle.application_fee                                      ║
  ║  3. Create ApplicationPayment record (Receipt No: AR-YYYY-XXXXX)                     ║
  ║  4. Allocate Class Section (balanced headcount / preferred section)                  ║
  ║  5. Allocate next Roll Number in section                                             ║
  ║  6. Generate Permanent Admission Number (ADM-YYYY-XXXXX)                             ║
  ║  7. Create Student User login (Login: Admission No, Pass: Student@123)               ║
  ║  8. Create Student record (students table) linked to User                            ║
  ║  9. Create Enrolment record (enrolments table) for current/next Academic Year        ║
  ║ 10. Create/Reuse Guardian User & Guardian record (deduplicated by mobile)            ║
  ║ 11. Create StudentGuardian linkage (is_primary = true)                               ║
  ║ 12. Migrate uploaded Documents (owner_type: application ──► student)                 ║
  ║ 13. Update Application: application.student_id = student.id, status = ENROLLED       ║
  ║ 14. Record comprehensive Audit Log entries                                           ║
  ╚══════════════════════════════════════════════════════════════════════════════════════╝
              │
              ▼
   [ 6. Immediate Output & Verification Screen ]
   - Success banner with Student Name, Admission Number, Class & Section
   - Action Buttons:
     * [ Print Application Fee Receipt ]
     * [ Print Full Application Dossier (A4) ]
     * [ View in Students Roster ]
```

---

## 4. TRANSACTION & ATOMICITY SPECIFICATION

```
             ┌────────────────────────────────────────────────────────┐
             │       HTTP POST /admin/admission/applications/         │
             │                   {id}/payments                        │
             └──────────────────────────┬─────────────────────────────┘
                                        │
                                  BEGIN TX (db)
                                        │
             ┌──────────────────────────┴─────────────────────────────┐
             │ 1. Validate application status & eligibility           │
             │    - Not already enrolled                              │
             │    - Target cycle & academic year active               │
             │    - Fee matches cycle.application_fee                 │
             └──────────────────────────┬─────────────────────────────┘
                                        │
             ┌──────────────────────────┴─────────────────────────────┐
             │ 2. Check Idempotency Key                               │
             │    - If key exists: return existing payment & student  │
             └──────────────────────────┬─────────────────────────────┘
                                        │
             ┌──────────────────────────┴─────────────────────────────┐
             │ 3. Allocate Class Section & Roll Number                │
             │    - Find sections for class & academic year           │
             │    - Check capacity limits                             │
             │    - Balance headcount; assign roll number             │
             └──────────────────────────┬─────────────────────────────┘
                                        │
             ┌──────────────────────────┴─────────────────────────────┐
             │ 4. Generate Numbers & Identifiers                      │
             │    - Next Receipt Number: AR-YYYY-XXXXX                │
             │    - Next Admission Number: ADM-YYYY-XXXXX             │
             └──────────────────────────┬─────────────────────────────┘
                                        │
             ┌──────────────────────────┴─────────────────────────────┐
             │ 5. Create Database Entities (using flush())            │
             │    - Insert ApplicationPayment (status: paid)          │
             │    - Insert User (role: student)                       │
             │    - Insert Student (status: active)                   │
             │    - Insert Enrolment (status: active)                 │
             │    - Insert/Reuse Guardian & StudentGuardian           │
             │    - Migrate Documents (owner_type -> student)         │
             │    - Update Application (status: enrolled, student_id) │
             └──────────────────────────┬─────────────────────────────┘
                                        │
                         Any Exception or Constraint Failure?
                              /          \
                           YES            NO
                           /                \
             ┌────────────┴────────┐   ┌─────┴────────────────────────┐
             │     ROLLBACK TX     │   │          COMMIT TX           │
             │  - No payment saved │   │  - Payment committed         │
             │  - No student made  │   │  - Student live in roster    │
             │  - Return 4xx / 5xx │   │  - Return payment + student  │
             └─────────────────────┘   └──────────────────────────────┘
```

---

## 5. ENQUIRY TO APPLICATION DATA FLOW

### 5.1 Exact Field Mapping Table

| Source Field (`enquiries`) | Target Field (`applications` / `application_guardians`) | Transformation / Business Logic |
| :--- | :--- | :--- |
| `school_id` | `applications.school_id` | Direct copy (strictly tenant scoped) |
| `cycle_id` | `applications.cycle_id` | Direct copy; fallback to open cycle if null |
| `child_name` | `applications.first_name`, `applications.middle_name`, `applications.last_name` | Split: 1 word $\rightarrow$ `first_name`; 2 words $\rightarrow$ `first_name`, `last_name`; 3+ words $\rightarrow$ `first_name`, `middle_name`, `last_name` |
| `child_dob` | `applications.date_of_birth` | Direct copy (`date`) |
| `class_of_interest` | `applications.class_applying_for` | Direct copy (e.g., "Class 1", "Nursery", "9") |
| `source` | `applications.source` | Enum copy (`EnquirySource` $\rightarrow$ `EnquirySource`) |
| `enquirer_name` | `application_guardians.full_name` | Populates primary guardian full name |
| `mobile` | `application_guardians.mobile` | Populates primary guardian mobile (family portal identifier) |
| `email` | `application_guardians.email` | Populates primary guardian email |
| *(Default)* | `application_guardians.relation` | Defaults to `"parent"` or `"father"` |
| *(Default)* | `application_guardians.is_primary` | Set to `True` |
| *(Default)* | `applications.status` | Set to `ApplicationStatus.draft` |
| `id` | `enquiries.converted_application_id` | Foreign key backlink to the created application |
| *(State)* | `enquiries.status` | Updates from current status to `EnquiryStatus.converted` |
| *(State)* | `enquiries.next_follow_up_on` | Cleared to `None` |

### 5.2 Navigation & Initiation
- Initiated by Admission Officer or authorized clerk.
- Calls `POST /admin/admission/applications` passing `{ enquiry_id: enquiry.id, ... }`.
- Automatically transitions enquiry to `converted`, sets `converted_application_id`, and routes to `Applications.tsx?selectedAppId=<new_id>` in edit mode.

---

## 6. STUDENT + ENROLMENT CREATION ON PAYMENT

### 6.1 Entity Field Populators

#### 1. User (`users` table) — Student Login
- `school_id`: `app.school_id`
- `role`: `UserRole.student`
- `login_id`: `admission_no` (e.g., `"20260001"`)
- `password_hash`: `hash_password("Student@123")`
- `full_name`: `f"{app.first_name} {app.last_name}"`
- `status`: `"active"`

#### 2. Student (`students` table) — Permanent Institutional Record
- `school_id`: `app.school_id`
- `user_id`: `student_user.id`
- `admission_no`: Generated sequential number (`audit.admission_number(db, school_id, year)`)
- `status`: `StudentStatus.active`
- `dob`: `app.date_of_birth`
- `gender`: `app.gender`
- `address`: Formatted address string from `app.address` JSON
- `admission_date`: `date.today()`

#### 3. Enrolment (`enrolments` table) — Annual Membership
- `school_id`: `app.school_id`
- `student_id`: `student.id`
- `academic_year_id`: `section.academic_year_id`
- `class_section_id`: `section.id`
- `roll_no`: `(max(roll_no in section) or 0) + 1`
- `joined_on`: `date.today()`
- `status`: `EnrolmentStatus.active`

#### 4. Guardian Deduplication & Login (`guardians` & `users` tables)
- Lookup existing `User` where `school_id == app.school_id`, `role == UserRole.parent`, and `login_id == g.mobile`.
- If found: reuse existing `Guardian`.
- If not found:
  - Create `User` (`role=UserRole.parent`, `login_id=g.mobile`, `full_name=g.full_name`, `phone=g.mobile`, `email=g.email`, `password_hash=hash_password("Parent@123")`).
  - Create `Guardian` (`user_id=user.id`, `occupation=g.occupation`, `employee_id=g.employee_id`).
- Create `StudentGuardian` (`student_id=student.id`, `guardian_id=guardian.id`, `relation=g.relation`, `is_primary=g.is_primary`).

#### 5. Document Transfer
- Migrate all documents with `owner_type == OwnerType.application` and `owner_id == app.id` to `owner_type = OwnerType.student` and `owner_id = student.id`.

#### 6. Application Closure
- `app.student_id = student.id`
- `app.status = ApplicationStatus.enrolled`

### 6.2 Section Allocation & Capacity Balancing Algorithm
1. Query active `ClassSection` records matching `school_id`, `academic_year_id = cycle.academic_year_id`, and `class_name = app.class_applying_for`.
2. If none exist: raise `HTTP 409 Conflict` ("No section exists for class {X} in academic year {Y}. Create class sections first.").
3. For each section, compute active count: `count(Enrolment) where class_section_id == section.id and status == active`.
4. Filter sections where `section.capacity is None or count < section.capacity`.
5. If all sections at capacity: raise `HTTP 409 Conflict` ("Every section of class {X} is at maximum capacity.").
6. If `app.preferred_section` specified and section has room without causing severe imbalance (`count <= min_count + 2`): allocate preferred section.
7. Otherwise: allocate section with the lowest current headcount.

---

## 7. RBAC & PERMISSION MATRIX

| Role | Enquiries (Log/Edit/Print) | Convert Enquiry -> Application | Application (Draft/Edit) | Verify Documents | Collect Application Fee & Auto-Enroll | Void Payments | Configure Cycles / Seats |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Receptionist** | ✅ Full | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No |
| **Admission Officer** | 👁️ Read | ✅ Yes | ✅ Full | ✅ Yes | ✅ Yes | ❌ No | 👁️ Read |
| **Fee Collector / Cashier** | ❌ No | ❌ No | 👁️ Read | ❌ No | ✅ Yes | ❌ No | ❌ No |
| **Admin / Principal** | ✅ Full | ✅ Yes | ✅ Full | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Full |
| **Super Admin** | 👁️ Dashboard | ❌ Operational | 👁️ Dashboard | ❌ Operational | ❌ Operational | ❌ Operational | ✅ Full |

### Permission Strings in Backend Code (`app/core/permissions.py`)
- `admission.enquiry.read`: View enquiries and search register.
- `admission.enquiry.write`: Create, edit, log interaction, and mark enquiry invalid.
- `admission.application.read`: View application listing and dossier details.
- `admission.application.write`: Open draft, edit details, submit dossier.
- `admission.document.verify`: Verify identity proofs, marksheet, birth certificates.
- `fees.payment.collect`: Collect offline payment and issue sequential receipt.
- `admission.application.convert`: Authorization to convert applicant to enrolled student.
- `fees.payment.void`: Void a printed receipt with mandatory recorded reason.

> [!IMPORTANT]
> **Role Alignment in `app/core/permissions.py`:**
> 1. `receptionist`: Holds `admission.enquiry.read` and `admission.enquiry.write`. Do **NOT** grant application-processing or fee collection permissions to receptionist.
> 2. `admission_officer`: Holds `admission.application.read`, `admission.application.write`, `admission.document.verify`, `admission.application.convert`, AND `fees.payment.collect`.
> 3. Route `POST /admin/admission/applications/{id}/payments`: Uses `dependencies=[collector]` where `collector = Depends(require_permission("fees.payment.collect", "admission.application.write"))`. Both Admission Officer and Admin satisfy this.

---

## 8. APPLICATION FORM & DYNAMIC FEE CONFIGURATION

### 8.1 Comprehensive Dossier Fields
1. **Applicant Personal Details:** Full name (first, middle, last), DOB, gender, blood group, nationality, religion, caste category, mother tongue, place of birth, identification marks, single child status, Aadhaar last 4.
2. **Academic & Class Applied:** Class applied for, stream (Class 11-12), second language, optional subject, preferred section, admission category, transport required.
3. **Previous School History (JSON):** School name, board, last class passed, percentage/grade, TC number, TC date, TC submitted flag.
4. **Parents & Guardians (`application_guardians`):** Father and Mother details (full name, mobile, email, qualification, occupation, designation, organisation, annual income band, alumnus/staff flags). Min 1 primary guardian required.
5. **Address Details (JSON):** Line 1, Line 2, city, state, pincode.
6. **Health & Medical (`application_medicals`):** Blood group, allergies, chronic conditions, regular medications, emergency doctor and phone.

### 8.2 Dynamic Application Fee Sourcing (NO Hardcoding)
- In `backend/app/models/admission.py`, `AdmissionCycle` defines:
  ```python
  application_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
  ```
- **Backend Rule:** In `collect(...)` in `app/services/conversion.py`, the payment amount must default to `app.cycle.application_fee`. If a specific amount is passed from the client, validate that it matches `app.cycle.application_fee` (unless explicit fee concession/override is recorded). Never hardcode ₹500.
- **Frontend Rule:** In `Applications.tsx`, the "Collect Application Fee & Enroll" modal fetches `cycle.application_fee` for the active cycle and pre-fills the payment amount field dynamically.

---

## 9. ENQUIRY FORM & PRINTABLE ENQUIRY SLIP

### 9.1 Enquiry Form Fields
- `enquirer_name` (string, required)
- `mobile` (10-digit string, required)
- `email` (string, optional)
- `child_name` (string, optional)
- `child_dob` (date, optional)
- `class_of_interest` (dropdown: Nursery, LKG, UKG, Class 1 to 12)
- `source` (walk_in, phone, website, referral, hoarding, digital_ad, other)
- `next_follow_up_on` (date, optional)

### 9.2 Printable Enquiry Slip Specifications
- **Format:** A5 Portrait or half-A4 slip using `@media print`.
- **Header:** School crest, "Sunrise Public School", Affiliation No. & Address, Contact phone & email.
- **Enquiry Reference:** `ENQ-YYYY-XXXXX`, Date & Time logged, Logged by staff name.
- **Candidate & Parent Details:** Child Name, DOB, Age as on date, Class Applied, Enquirer Name, Mobile, Email, Source.
- **Parent Instructions Checklist:**
  - 1. Original Birth Certificate + 2 Photocopies
  - 2. Aadhaar Card copy of Student and Parents
  - 3. 4 Passport-size photographs of Student, 2 of each Parent
  - 4. Previous School Marksheet and Transfer Certificate (Class 1 upwards)
  - 5. Residence Proof (Electricity bill / Passport / Rent agreement)
- **Footer:** Tear-off office acknowledgment slip with parent signature line and reception counter stamp box.

---

## 10. PRINTABLE APPLICATION DOSSIER & FEE RECEIPT

### 10.1 Printable Application Form (Full A4 Dossier)
- **Layout:** Standard CBSE 2-page A4 Portrait using Tailwind `@media print`.
- **Components:**
  1. School header with affiliation details and form title ("STUDENT ADMISSION DOSSIER — ACADEMIC YEAR 2026-27").
  2. Photo box (3.5cm x 4.5cm) with cross-signature instruction.
  3. Student personal details table (Name, DOB, Gender, Category, Aadhaar last 4).
  4. Academic enrollment table (Class, Stream, Transport).
  5. Parent & guardian grid (Father and Mother details side by side).
  6. Address block with pincode.
  7. Academic history and TC record.
  8. Parent declaration undertaking and signature blocks.
  9. Official use box: verification checklist, allocated admission number, assigned section, signature of Principal.

### 10.2 Printable Application Fee Receipt
- **Layout:** 1/3 A4 landscape voucher.
- **Content:**
  - School header with "APPLICATION & REGISTRATION FEE RECEIPT".
  - Receipt Number: `payment.receipt_no` (e.g. `AR-2026-00042`).
  - Receipt Date: `payment.paid_at`.
  - Application No: `app.application_no`.
  - Student / Applicant Name: `app.full_name`.
  - Permanent Admission No: `student.admission_no` *(Generated automatically upon payment!)*.
  - Class & Section Enrolled: `section.label` *(Allocated automatically upon payment!)*.
  - Fee Head: "Application Processing & Registration Fee".
  - Amount Paid: Dynamically sourced from `payment.amount` (e.g. formatted in INR and words).
  - Payment Mode & Reference: `Cash / UPI / Cheque` and transaction reference.
  - Cashier / Officer signature block & system watermark.

---

## 11. DATABASE FLOW & STATE MACHINES

```
[ENQUIRY STATE MACHINE - RECEPTIONIST WORKFLOW]
  ┌─────────┐      Phone / Walk-in       ┌───────────┐
  │   NEW   │ ─────────────────────────► │ CONTACTED │
  └────┬────┘                            └─────┬─────┘
       │                                       │
       │ Parent Visits Campus                  │
       ├───────────────────────────────────────┤
       ▼                                       ▼
  ┌──────────────┐   Handed to Admission ┌───────────┐
  │  INTERESTED  │ ────────────────────► │ CONVERTED │ ──► (Generates Application Draft)
  └──────────────┘                       └───────────┘
       │                                       │
       │ Parent Declines                       │ Invalid Number / Spam
       ▼                                       ▼
  ┌──────────────┐                       ┌───────────┐
  │NOT_INTERESTED│                       │  INVALID  │
  └──────────────┘                       └───────────┘

[APPLICATION STATE MACHINE - ADMISSION CELL WORKFLOW]
  ┌─────────┐      Dossier Completed     ┌───────────┐
  │  DRAFT  │ ─────────────────────────► │ SUBMITTED │
  └─────────┘                            └─────┬─────┘
                                               │
                                               │ Document Verification
                                               ▼
                                         ┌───────────────────────────┐
                                         │UNDER_DOCUMENT_VERIFICATION│
                                         └─────────────┬─────────────┘
                                                       │
                                  ┌────────────────────┴───────────────────┐
                                  ▼                                        ▼
                        ┌───────────────────┐                    ┌───────────────────┐
                        │DOCUMENTS_VERIFIED │                    │DOCUMENTS_REJECTED │
                        └─────────┬─────────┘                    └───────────────────┘
                                  │
                                  │ Evaluation / Shortlist (Optional per class)
                                  ▼
                        ┌───────────────────┐
                        │     ADMITTED      │
                        └─────────┬─────────┘
                                  │
                                  │ Collect Application Fee (Single Action)
                                  ▼
                        ╔═══════════════════╗
                        ║     ENROLLED      ║ ◄── (ATOMIC TRIGGER: Student & Enrolment Created)
                        ╚═══════════════════╝
```

---

## 12. EXISTING CODE TO REUSE & EXTEND

| File Path | Function / Component | Action for Session 7 |
| :--- | :--- | :--- |
| `backend/app/services/conversion.py` | `collect(...)` | **Extend:** In `collect()`, when `purpose == ApplicationFeePurpose.application_fee`, retrieve fee from `app.cycle.application_fee`, create payment, and immediately execute `_do_conversion(db, app, actor)` in the same transaction. |
| `backend/app/services/conversion.py` | `convert(...)` | **Refactor:** Extract internal helper `_do_conversion(db, app, actor)` using `db.flush()`. Keep `convert(...)` as an internal/admin utility if needed, but primary path is through `collect()`. |
| `backend/app/services/conversion.py` | `allocate_section(...)` | **Reuse as-is:** Perfectly balances section headcounts and honors preferred section when available. |
| `backend/app/services/conversion.py` | `_guardian_for(...)` | **Reuse as-is:** Reuses existing parent login when mobile matches across siblings. |
| `backend/app/api/admin/conversion.py` | `collect_payment(...)` | **Update:** Return `{ ...payment_data, student: { id, admission_no, class_label } }` in response. |
| `backend/app/api/admin/applications.py` | `create_application(...)` | **Reuse:** Already supports `enquiry_id` and marks enquiry as `converted`. |
| `web/src/pages/admission/Enquiries.tsx` | `Enquiries()` | **Extend:** Add "Print Slip" modal trigger. Allow authorized Admission Cell to convert enquiry to application. Keep Receptionist focused on Enquiries. |
| `web/src/pages/admission/Applications.tsx` | `Applications()` | **Refactor:** Eliminate separate "Convert to Student" button. Tab 6 (Fees) has single "Collect Fee & Enroll" action defaulting to `cycle.application_fee`. On success, show student info with print receipt & dossier buttons. |
| `web/src/components/recruitment/PrintableApplicationForm.tsx` | Print Layout | **Reference:** Replicate print CSS styling for `PrintableEnquirySlip.tsx` and `PrintableAdmissionDossier.tsx`. |

---

## 13. TESTING PLAN FOR SESSION 7

Session 7 must implement and verify the following automated test cases in `backend/tests/test_admission_conversion.py` and `backend/tests/test_admission_applications.py`:

1. **Master Acceptance Test (Rule 10):**  
   `test_complete_admission_pipeline_enquiry_to_roster`:  
   Execute full pipeline: Create Enquiry $\rightarrow$ Convert to Application $\rightarrow$ Fill complete dossier $\rightarrow$ Submit $\rightarrow$ Collect Application Fee $\rightarrow$ Assert `ApplicationPayment` created $\rightarrow$ Assert `Student` created with valid admission number $\rightarrow$ Assert `Enrolment` created in target class/section $\rightarrow$ Assert student is visible in school roster query (`select(Student).join(Enrolment)...`).
2. `test_payment_atomically_creates_student_and_enrolment`: Verify single call to `POST /admin/admission/applications/{id}/payments` creates payment, student, enrolment, and sets `app.status = ApplicationStatus.enrolled`.
3. `test_payment_amount_derived_from_cycle_application_fee`: Verify payment uses `cycle.application_fee` and rejects mismatch if not overridden.
4. `test_payment_failure_rolls_back_entire_transaction`: If section allocation fails (e.g. all sections full), ensure payment is rolled back and no student or payment record remains.
5. `test_payment_idempotency_prevents_duplicate_charge_and_enrolment`: Two calls with same `idempotency_key` return existing receipt and enrolled student without creating second student or payment.
6. `test_enquiry_to_application_conversion_field_mapping`: Verify name, DOB, mobile, class, and source correctly map from enquiry to application and primary guardian.
7. `test_enquiry_status_transitions_to_converted`: Confirm `enquiry.status == "converted"` and `enquiry.converted_application_id == app.id`.
8. `test_receptionist_cannot_collect_application_fee`: Verify 403 Forbidden when user with only `receptionist` permissions attempts to collect application fee.
9. `test_admission_officer_can_collect_and_auto_enroll`: Verify 201 Created and successful enrollment for user with `admission_officer` role.
10. `test_section_allocation_headcount_balancing`: Converted students distribute evenly across available sections.
11. `test_section_allocation_honors_preferred_section`: Preferred section assigned when room is available and balance is maintained.
12. `test_student_user_login_creation`: Converted student can authenticate via `/auth/login` using `admission_no` and default password.
13. `test_parent_user_login_deduplication`: Sibling admission reuses existing parent login matched by mobile number.
14. `test_document_migration_ownership`: Application documents transition from `OwnerType.application` to `OwnerType.student`.
15. `test_void_payment_leaves_audit_record`: Voided payment sets status to `voided`, records reason, and preserves receipt number sequence.
16. `test_draft_application_allows_minimal_fields`: Draft opens with only basic student name, DOB, gender, and class.
17. `test_submitted_application_enforces_mandatory_fields`: Cannot pay fee or submit if primary guardian or address is missing.
18. `test_no_separate_conversion_step_required`: Verify application reaches `enrolled` status immediately upon fee collection without calling any secondary convert endpoint.

---

## 14. CURRENT IMPLEMENTATION GAPS

```
┌───────────────────────────────┬───────────────────────────┬────────────────────────────────────────┐
│ Area                          │ Current Codebase Status   │ Required Action in Session 7           │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Persona Separation            │ Receptionist sees excess  │ Bound Receptionist to Enquiries;       │
│                               │ queues in some contexts   │ Admission Officer owns Applications.   │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Enquiry Conversion Action     │ Backend supports it; UI   │ Add "Convert to Application" in        │
│                               │ missing in Enquiries.tsx  │ Enquiries (Admission Cell action).     │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Enquiry Printable Slip        │ Missing                   │ Create PrintableEnquirySlip (A5) with  │
│                               │                           │ school header and parent checklist.    │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Automatic Enrollment          │ Disconnected (Two manual  │ Unify collect() + convert() in backend │
│ on Payment                    │ steps: Pay then Convert)  │ so fee payment triggers enrollment.    │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Configured Fee Sourcing       │ Partially manual amount   │ Sourced dynamically from               │
│                               │                           │ cycle.application_fee (no hardcoding). │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Printable Application Dossier │ Missing                   │ Create PrintableAdmissionDossier A4    │
│                               │                           │ component with photo box & signatures. │
├───────────────────────────────┼───────────────────────────┼────────────────────────────────────────┤
│ Printable Fee Receipt         │ Missing in frontend UI    │ Create PrintableFeeReceipt voucher     │
│                               │                           │ modal launched after payment.          │
└───────────────────────────────┴───────────────────────────┴────────────────────────────────────────┘
```

---

## 15. NEXT SESSION STEP-BY-STEP EXECUTION PLAN

```
  PHASE 1: RBAC & PERMISSION BOUNDARIES
  ├── Ensure receptionist holds ONLY Enquiry permissions (no fees.payment.collect)
  ├── Ensure admission_officer holds admission.application.* AND fees.payment.collect
  └── Verify collector dependency in app/api/admin/conversion.py accepts admission_officer

  PHASE 2: BACKEND ATOMIC ENROLLMENT ON FEE PAYMENT
  ├── Refactor app/services/conversion.py:
  │   ├── Create internal helper _execute_enrollment(db, app, actor) using db.flush()
  │   └── Update collect(): source fee from cycle.application_fee; after creating payment,
  │       call _execute_enrollment() in the same transaction
  ├── Update POST /admin/admission/applications/{id}/payments response to return student info
  └── Ensure complete rollback if any step in _execute_enrollment fails

  PHASE 3: ENQUIRY TO APPLICATION BACKEND VERIFICATION
  ├── Verify POST /admin/admission/applications with enquiry_id maps all fields
  └── Add test in test_admission_enquiries.py verifying link and status transition

  PHASE 4: BACKEND TEST SUITE RUN & MASTER ACCEPTANCE TEST
  ├── Implement all 18 automated tests in test_admission_conversion.py
  └── Verify test_complete_admission_pipeline_enquiry_to_roster passes 100% green

  PHASE 5: FRONTEND ENQUIRY ENHANCEMENTS (Enquiries.tsx)
  ├── Receptionist UX: Log enquiry, save, follow-ups
  ├── Add PrintableEnquirySlip.tsx component (A5) with parent document checklist
  └── Add "Convert to Application" action (for Admission Cell / Officer)

  PHASE 6: FRONTEND APPLICATION DOSSIER & AUTOMATED ENROLLMENT (Applications.tsx)
  ├── Remove separate "Convert to Student" button from Tab 6
  ├── Update Tab 6 "Collect Application Fee & Enroll" modal:
  │   ├── Pre-fill fee dynamically from active cycle.application_fee
  │   └── On submit: calls payments API -> receives payment + enrolled student details
  └── Display Success State with Admission Number, Section, and Roll Number

  PHASE 7: PRINTABLE ASSETS IMPLEMENTATION
  ├── Create PrintableFeeReceipt.tsx (Voucher with receipt no, admission no, amount)
  ├── Create PrintableAdmissionDossier.tsx (CBSE Standard 2-page A4 dossier)
  └── Wire print buttons into Applications detail screen

  PHASE 8: FULL SYSTEM VERIFICATION
  ├── Run full backend pytest suite (all 708 baseline + new tests green)
  ├── Run verify_db_docs.py (ensure 0 schema drift)
  └── Run web and mobile TypeScript compilation (0 errors)
```

---

## 16. ACCEPTANCE CRITERIA

Session 7 is complete when all of the following criteria are satisfied:
1. **Receptionist Persona Scoping:** Receptionist operates strictly on Enquiries. Receptionist cannot collect application fees or process applications.
2. **Admission Cell Workflow:** Admission Officer converts enquiries, completes and submits application dossiers, and collects fees.
3. **Dynamic Fee Sourcing:** Application fee is read dynamically from `AdmissionCycle.application_fee`. No hardcoded ₹500.
4. **Zero Manual Conversion Step:** No separate "Convert to Enrolled Student" button exists. Fee payment is the sole trigger that enrolls the student.
5. **Atomic Enrollment:** Upon successful payment of the application fee:
   - An `ApplicationPayment` row is created with an `AR-` receipt number.
   - A `Student` row is created with a permanent admission number.
   - An `Enrolment` row is created with an allocated section and sequenced roll number.
   - Student and Parent portal accounts are provisioned.
   - Documents are migrated to `student` ownership.
   - The application status becomes `enrolled`.
6. **All-or-Nothing Rollback:** Any failure during payment or enrollment rolls back the entire transaction.
7. **Printable Assets:** Official Printable Enquiry Slip (A5), Application Fee Receipt Voucher, and CBSE 2-page A4 Application Dossier render cleanly and print via `window.print()`.
8. **Master Acceptance Test Passes:** `Enquiry → Application → Complete → Submit → Pay Fee → Student created → Enrolment created → Student visible in school database/roster` passes 100% green.
9. **Green Test Suite & Zero Drift:** All backend tests pass and `verify_db_docs.py` reports 17/17 passed with 0 drift.

---

## 17. FILE / ROUTE / MODEL INVENTORY

### Backend Files
- `backend/app/models/admission.py`: `Enquiry`, `AdmissionCycle`, `CycleClassConfig`
- `backend/app/models/application.py`: `Application`, `ApplicationGuardian`, `ApplicationMedical`
- `backend/app/models/application_payment.py`: `ApplicationPayment`
- `backend/app/models/user.py`: `User`, `Student`, `Guardian`, `StudentGuardian`
- `backend/app/models/academic.py`: `ClassSection`, `Enrolment`
- `backend/app/services/conversion.py`: Payment collection and atomic student enrollment logic
- `backend/app/services/applications.py`: Application dossier operations and validations
- `backend/app/api/admin/admission.py`: Enquiry endpoints (`/admin/admission/enquiries`)
- `backend/app/api/admin/applications.py`: Application endpoints (`/admin/admission/applications`)
- `backend/app/api/admin/conversion.py`: Payment collection endpoints (`/admin/admission/applications/{id}/payments`)
- `backend/app/core/permissions.py`: Role definitions and permission matrices

### Frontend Files
- `web/src/pages/admission/Enquiries.tsx`: Enquiry register, timeline, quick log modal
- `web/src/pages/admission/Applications.tsx`: 7-tab application dossier management console
- `web/src/pages/admission/types.ts`: TypeScript interfaces for cycles, enquiries, applications, payments
- `web/src/components/admission/PrintableEnquirySlip.tsx` *(To be created)*: A5 printable slip
- `web/src/components/admission/PrintableFeeReceipt.tsx` *(To be created)*: Official fee receipt voucher
- `web/src/components/admission/PrintableAdmissionDossier.tsx` *(To be created)*: CBSE-standard A4 dossier

---

## 18. PRE-SESSION VERIFICATION COMMANDS

Before commencing Session 7, run these commands to verify that the workspace is in a healthy, green baseline state:

```bash
# 1. Verify Git status and branch
git status
# Expected: On branch slice/office-feedback

# 2. Run the complete pytest backend test suite
school-management-system/.venv/Scripts/python.exe -m pytest -q
# Expected: 708 passed, 1 skipped, 0 failed

# 3. Verify database documentation sync
school-management-system/.venv/Scripts/python.exe scripts/verify_db_docs.py
# Expected: 17 passed, 0 failed, 0 drift

# 4. Verify web frontend TypeScript compilation
cd web && npx tsc --noEmit
# Expected: 0 errors

# 5. Verify mobile TypeScript compilation
cd mobile && npx tsc --noEmit
# Expected: 0 errors
```
