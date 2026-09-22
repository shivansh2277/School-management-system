# Session Handoff 5 — All-Tables Database & Feature Mapping Reference PDF

**Date:** 16 September 2026  
**Canonical Reference:** [`SINGLE_SOURCE_OF_TRUTH.md`](SINGLE_SOURCE_OF_TRUTH.md)  
**Branch:** `slice/office-feedback` (strictly local per owner directive)  
**Status:** Complete handoff for execution in the next session

---

## 1. Verified Technical State (Session 4 Baseline)

All features, RBAC controls, and framework upgrades are 100% green and verified:

| Component | Status | Metrics / Evidence |
|---|---|---|
| **Backend API (FastAPI)** | 100% Green | 649 passed, 1 skipped (`pytest -q`) on `http://127.0.0.1:8078` |
| **Frontend Web ERP (Vite / React)** | 100% Green | 23 screens declared in `screens.ts`, TypeScript 0 errors, 68 Vitest passed |
| **Mobile App (Expo SDK 57)** | 100% Green | Upgraded to Expo SDK 57 (`~57.0.22`), React Native `0.86.3`, React `19.2.3`, `npx expo-doctor` 21/21 passed, `tsc --noEmit` 0 errors |
| **Database (PostgreSQL)** | 100% Green | 89 tables total, 61 live populated tables, 28 unpopulated tables in `sunrise_test` |
| **Live Browser Verification** | 100% Green | Full visual proofs captured in `docs/screenshots/` (Admin Dashboard, Receptionist Isolation, Attendance Overview) |
| **Existing PDF Documentation** | Up to Date | 5 canonical PDFs in `docs/`: <br>1. `Sunrise-ERP-Features-Operational-and-Planned.pdf`<br>2. `Sunrise-ERP-Database-Essentials-Explained.pdf`<br>3. `Sunrise-ERP-Database-Viva-100.pdf`<br>4. `Sunrise-ERP-Database-Essentials.pdf`<br>5. `Sunrise-ERP-Database.pdf` |

### Recent Deliverables Completed in Session 4:
1. **Main Dashboard Attendance Overview**:
   - Replaced the old 4 summary cards (`Total Students`, `Total Teachers`, `Total Classes`, `Fees Collected`) with a modern **Attendance Overview** card.
   - Live metrics: Total Students (`100`), Present Today (`90`), Absent Today (`10` with `5 absent · 5 on leave` breakdown), Attendance Percentage (`90%`).
   - Dynamic dual-tone progress distribution bar matching the theme.
   - Dynamic SQL calculation in `app/services/stats.py` (`today_attendance`) with auto-fallback to the most recent marked school day when morning roll is pending.
2. **Dedicated Receptionist Role & Admission RBAC**:
   - Receptionist account: `receptionist@sunrisepublic.edu` / `Admin@123`.
   - Strict RBAC isolation: Receptionist has exclusive access to the 5 operational admission queues (`/admission/enquiries`, `/admission/applications`, `/admission/merit`, `/admission/waitlist`, `/admission/reports`), landing directly on `/admission/enquiries`. All non-admission routes are hidden and URL-blocked.
   - Admin (`admin@sunrisepublic.edu`) retains executive **Admission Dashboard** (`/admission`) with cycle metrics, funnel conversion, and seat capacities; operational queues are segregated from Admin's sidebar.
3. **Mobile App Upgraded to Expo SDK 57**:
   - Migrated from Expo SDK 54 (`~54.0.0`) to Expo SDK 57 (`~57.0.22`).
   - React upgraded to `19.2.3`, React Native to `0.86.3`, TypeScript to `~6.0.3`.
   - `npx expo-doctor` reports 21/21 checks passed.

---

## 2. Objective for the Next Session

### The Task: Complete Database Tables & Feature Mapping PDF
Create a dedicated, comprehensive **Database Tables PDF** (`docs/Sunrise-ERP-Database-Tables-and-Features.pdf`) that documents **all 89 tables in the schema (not just the 61 essential ones)**, detailing the exact role of each table and its direct correspondence to operational and planned features on the Sunrise School ERP website.

### Binding User Instructions:
1. **Include ALL 89 tables**, organized logically by functional domain.
2. **In front of every non-essential table (the 28 currently unpopulated in seed data), prominently write: `"UNUSED FOR NOW"`.**
3. **Map each table to its corresponding website feature**:
   - Exact web screen route (e.g., `/dashboard`, `/admission/enquiries`, `/fees/ledger`, `/inventory`, `/attendance`, `/exams`, etc.).
   - UI components, modals, and actions that interact with the table.
   - Explicit distinction between **Live Operational Features** vs **Planned Features** (as analyzed from `docs/Sunrise-ERP-Features-Operational-and-Planned.pdf`).
4. **Deep Analysis of Existing Project Documentation**:
   - Cross-reference with:
     - `docs/Sunrise-ERP-Features-Operational-and-Planned.pdf` (Operational vs Planned feature matrix).
     - `docs/Sunrise-ERP-Database.pdf` (Full 89-table schema and column specifications).
     - `docs/Sunrise-ERP-Database-Essentials.pdf` (61 live table subset with ER relationships).
     - `docs/Sunrise-ERP-Database-Essentials-Explained.pdf` (Plain-English business workflows).
     - `docs/Sunrise-ERP-Database-Viva-100.pdf` (Architectural rationale and database invariants).
5. **Production Quality Deliverables**:
   - A standalone Python generation script (`scripts/gen_db_tables_feature_mapping_pdf.py`).
   - Generated print-optimized HTML (`docs/database-tables-and-features-print.html`).
   - Final compiled PDF rendered via Headless Google Chrome (`docs/Sunrise-ERP-Database-Tables-and-Features.pdf`).

---

## 3. Comprehensive Schema Breakdown: All 89 Tables by Domain

The PostgreSQL database `sunrise_test` holds **89 tables**:
- **61 Live / Essential Tables** (holding active rows in the seeded school).
- **28 Non-Essential Tables** (empty in seed data; each belongs to an operational API or planned feature) -> **Must be stamped with `"UNUSED FOR NOW"`**.

### Domain 1: Tenancy, Identity & Access (11 Tables)
*Controls multi-tenant isolation, user authentication, RBAC permissions, and global school settings.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `schools` | **LIVE (1 row)** | **Tenant Anchor**: Multi-tenant isolation anchor for Sunrise Public School (`school_id = 2`). Defines school code, CBSE board affiliation, branding colors, and contact information. |
| `academic_years` | **LIVE (1 row)** | **Configuration & Header (`/configuration`, `/settings`)**: Controls the active academic session (`2025-26`). Displayed in top navbar header. Delineates enrolments, class rosters, fee structures, and attendance terms. |
| `users` | **LIVE (235 rows)** | **Authentication (`/login`, `/auth/*`)**: Core credentials table storing `login_id`, Argon2 `password_hash`, full name, and active status for Admin, Receptionist, Teachers, Parents, and Students. |
| `roles` | **LIVE (10 rows)** | **RBAC Engine**: Defines system roles (`super_admin`, `receptionist`, `principal`, `teacher`, `student`, `parent`, `fee_clerk`). Used by backend `require_permission()` gates. |
| `permissions` | **LIVE (70 rows)** | **RBAC Granular Scopes**: Fine-grained capability codes (`admission.enquiry.read`, `fees.invoice.write`, `attendance.record.correct`, `inventory.item.read`). |
| `role_permissions` | **LIVE (216 rows)** | **Permission Mapping**: Many-to-many bridge linking roles to permissions. Defines exact privileges for `receptionist` (exclusive admission) and `admin` (school leadership). |
| `user_roles` | **LIVE (235 rows)** | **User Role Assignment**: Assigns roles to users with scope boundaries (`school`, `class_section`, `department`). |
| `settings` | **LIVE (17 rows)** | **School Settings (`/settings`, `/configuration`)**: Key-value registry for tenant configurations (fee due dates, attendance thresholds, module feature switches). |
| `custom_fields` | **LIVE (2 rows)** | **Custom Field Builder (`/configuration`)**: Stores school-defined custom attributes (e.g. `father_occupation`, `house`) rendered dynamically on student profiles. |
| `number_sequences` | **LIVE (6 rows)** | **Sequential Identifier Engine**: Atomic counters guaranteeing gapless numbering for admission numbers (`SPS/2026/0001`), fee receipt vouchers (`REC-...`), and enquiry numbers. |
| `alembic_version` | **LIVE (1 row)** | **Database Migrations (Internal Engine)**: Tracks Alembic schema migration head (`f4d82b1c99e1`). Not exposed directly in the UI. |

---

### Domain 2: People — Students & Guardians (4 Tables)
*Manages student identities, demographics, parental relationships, and annual academic enrolments.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `students` | **LIVE (100 rows)** | **Students Screen (`/students`)**: Student biographical record, admission number, date of birth, gender, blood group, caste category, and linked user identity. |
| `guardians` | **LIVE (92 rows)** | **Parent Profiles & Contact Chase (`/fees/defaulters`, `/students`)**: Father, mother, and local guardian records with primary phone numbers used for fee collection calls. |
| `student_guardian` | **LIVE (100 rows)** | **Family Relationship Linkage**: Many-to-many bridge associating students with guardians (`relation = father/mother/guardian`, `is_emergency_contact`). |
| `enrolments` | **LIVE (100 rows)** | **Class Rosters & Academics (`/classes`, `/students`)**: Critical invariant: connects a student to exactly one `class_section` per `academic_year` with their assigned class `roll_no`. |

---

### Domain 3: People — Staff & Departments (2 Tables)
*Manages employee records, teaching designations, and departmental structures.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `departments` | **LIVE (5 rows)** | **Staff Directory (`/teachers`)**: School academic departments (Science, Languages, Humanities, Primary) with assigned Department Heads. |
| `employees` | **LIVE (16 rows)** | **Staff Management (`/teachers`)**: Employee master directory holding employee codes, designations (PGT, TGT, PRT, Admin), joining dates, qualifications, and department associations. |

---

### Domain 4: Academics, Timetable & Homework (9 Tables)
*Drives class sections, timetable scheduling, subjects, school calendar, and homework assignments.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `class_sections` | **LIVE (10 rows)** | **Classes Screen (`/classes`)**: Class 1-A through 10-A sections with assigned class teacher (`class_teacher_id`), room numbers, and student capacities. |
| `subjects` | **LIVE (9 rows)** | **Curriculum Setup (`/classes`)**: Subject master catalogue (Mathematics, English, Hindi, Science, Social Science, Sanskrit, Computer, EVS, Art). |
| `class_subject_teacher` | **LIVE (50 rows)** | **Teacher Allocations (`/classes`)**: Maps subject specialists to class sections. Enforces balanced 25-period teaching loads across staff. |
| `school_periods` | **LIVE (6 rows)** | **Bell Timings (`/classes`)**: Defines daily bell timings (Periods 1 to 6) from 08:00 AM to 02:00 PM. |
| `timetable_slots` | **LIVE (300 rows)** | **Timetable Grid (`/classes`, `/dashboard`)**: Weekly timetable schedule across all sections, rooms, and teachers; feeds "Today's Schedule" on the dashboard. |
| `holidays` | **LIVE (5 rows)** | **Calendar & Dashboard (`/dashboard`, `/attendance`)**: Declared school closures and vacations (Mid-term Break, Founder's Week, Winter Break) shown in Upcoming Events widget. |
| `homework` | **LIVE (10 rows)** | **Teacher Homework Screen (Mobile / Web)**: Daily homework assignments created by subject teachers with due dates and submission instructions. |
| `homework_submissions` | **LIVE (25 rows)** | **Student Submissions (Mobile / Web)**: Digital homework turn-in records with submission timestamps, student comments, and teacher evaluation marks. |
| `substitutions` | **UNUSED FOR NOW (0 rows)** | **Academics — Teacher Substitution Engine**: Planned feature allowing coordinators to assign proxy teachers to class periods when regular staff are absent. |

---

### Domain 5: Attendance (2 Tables)
*Drives the daily roll call, absence tracking, and student leave approvals.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `attendance` | **LIVE (5,800 rows)** | **Dashboard & Register (`/dashboard`, `/attendance`)**: Daily student roll marks (`present`, `absent`, `late`, `half_day`, `leave`). Feeds the top **Attendance Overview** card on the main dashboard (`90% Present, 10 Absent, 100 Total`). |
| `student_leave_requests` | **UNUSED FOR NOW (0 rows)** | **Attendance — Leave Approval Workflow (`/attendance/leave-requests`)**: Parent-submitted leave applications with doctor notes, awaiting office administrator approval. |

---

### Domain 6: Examinations, Grading & Report Cards (8 Tables)
*Manages CBSE assessment schemes, exam datesheets, marks entry, and report card publications.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `assessment_schemes` | **LIVE (1 row)** | **Exams & Grading (`/exams` Tab 2)**: Active CBSE assessment structure for the academic year defining evaluation components and weightages. |
| `scheme_components` | **LIVE (4 rows)** | **Scheme Weightage (`/exams` Tab 2)**: Component breakdown (Periodic Assessment 10%, Notebook 5%, Subject Enrichment 5%, Term Exam 80%). |
| `grading_scales` | **LIVE (1 row)** | **Grading Scales (`/exams` Tab 2, `/settings`)**: CBSE 8-point grading scale definition (`A1` down to `E`). |
| `grade_bands` | **LIVE (8 rows)** | **Grade Intervals (`/exams` Tab 2)**: Cut-off percentages (`A1` >= 91%, `A2` >= 81%, ..., `E` < 33%) with descriptive report card remarks. |
| `exams` | **LIVE (2 rows)** | **Exams & Datesheets (`/exams` Tab 1)**: Formal examination terms (Half-Yearly Exam, Final Exam) with scheduling ranges. |
| `exam_schedule` | **LIVE (16 rows)** | **Datesheet & Lock Workflow (`/exams` Tab 1)**: Subject exam papers per class, date/time, maximum marks, pass marks, and audited paper lock status. |
| `marks` | **LIVE (384 rows)** | **Marks Entry Grid (`/exams` Tab 1)**: Marks obtained by each student per subject paper, with support for absent flags, audited score edits, and exemptions. |
| `report_card_publications` | **UNUSED FOR NOW (0 rows)** | **Report Card Publishing (`/exams` Tab 3)**: Formal release records for term report cards, incorporating dues withholdings (§0.6b, §5.4.9). |

---

### Domain 7: Fees & Financial Ledger (10 Tables)
*Drives student billing, fee plans, concessions, payments, receipting, and defaulter tracking.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `fee_heads` | **LIVE (7 rows)** | **Fee Setup (`/fees/setup`)**: Financial billing categories (Tuition Fee, Admission Fee, Annual Charges, Exam Fee, Transport Fee, Computer Lab Fee). |
| `fee_plans` | **LIVE (10 rows)** | **Fee Setup (`/fees/setup`)**: Class-wise annual fee schedules (Class 1 Plan through Class 10 Plan). |
| `fee_plan_items` | **LIVE (40 rows)** | **Fee Setup (`/fees/setup`)**: Line-item heads and billing frequencies (Monthly, Quarterly, Annual, One-time) associated with each class fee plan. |
| `fee_concessions` | **LIVE (5 rows)** | **Fee Concessions (`/fees/setup`)**: Approved fee waivers (Staff Ward 50%, Sibling Concession 25%, Merit Scholarship), audited with principal approval notes. |
| `fee_invoices` | **LIVE (500 rows)** | **Billing & Overview (`/fees`, `/dashboard`)**: Monthly billing invoices generated per student; feeds realized collection vs pending demand (`₹4,72,890 / ₹9,72,930`). |
| `fee_invoice_lines` | **LIVE (1,500 rows)** | **Itemized Ledger (`/fees/ledger`)**: Line-item breakdown of every student invoice showing specific fee head amounts, concession credits, and net payable. |
| `fee_payments` | **LIVE (450 rows)** | **Counter Receipting (`/fees/ledger`)**: Realized transaction receipts holding receipt number, payment mode (Cash, UPI, Cheque), and payment timestamp. |
| `payment_allocations` | **LIVE (1,350 rows)** | **Double-Entry Reconciliation (`/fees/ledger`)**: Bridges payments to specific invoice lines. Adheres to financial immutability; reversals recorded via audited contra-entries. |
| `student_fee_plans` | **UNUSED FOR NOW (0 rows)** | **Fee Overrides — Custom Student Plans (`/fees/setup`)**: Individualized fee plan assignments overriding the standard class-level fee schedule. |
| `fee_periods` | **UNUSED FOR NOW (0 rows)** | **Period Close (`/fees/periods`)**: Monthly financial period accounting locks, recording open/closed status and administrator audit logs. |

---

### Domain 8: Transport & Fleet Management (5 Tables)
*Manages school buses, transport routes, boarding stops, vehicle fitness papers, and student transport allocations.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `vehicles` | **LIVE (3 rows)** | **Transport Screen (`/transport`)**: School fleet registry (Buses UP-32-AT-1001 to 1003), seating capacities, insurance expiry, fitness certificate validity, and pollution check dates. |
| `routes` | **LIVE (3 rows)** | **Route Management (`/transport`)**: Transport routes (Route 1 - Gomti Nagar, Route 2 - Aliganj, Route 3 - Indira Nagar) with interactive Leaflet map integration. |
| `route_stops` | **LIVE (15 rows)** | **Stops & Timings (`/transport`)**: Designated pickup/drop boarding points, sequence numbers, and morning/afternoon scheduled arrival times. |
| `transport_fee_slabs` | **LIVE (4 rows)** | **Transport Billing (`/transport`, `/fees/setup`)**: Distance-based fee slabs (0-3 km, 3-6 km, 6-10 km, 10+ km) linked to monthly fee calculations. |
| `transport_assignments` | **LIVE (35 rows)** | **Student Riders (`/transport`)**: Maps students to routes, boarding stops, and trip directions (Both, Morning Only, Drop Only). |

---

### Domain 9: Human Resources & Payroll (10 Tables)
*Drives employee salary packages, statutory deductions, monthly payroll runs, staff leave, and biometric attendance.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `salary_components` | **LIVE (6 rows)** | **Payroll Setup (`/payroll` Planned)**: Statutory and standard salary components (Basic Pay, Dearness Allowance, HRA, Provident Fund, ESI, Professional Tax). |
| `salary_structures` | **LIVE (12 rows)** | **Staff Salary Packages (`/teachers`)**: Active compensation structure per teacher based on Lucknow private school scales (PGT ₹42,000, TGT ₹32,000, PRT ₹19,500). |
| `leave_types` | **LIVE (4 rows)** | **Staff Leave Setup (`/settings`)**: School staff leave quotas (Casual Leave 12 days, Sick Leave 10 days, Earned Leave 15 days, Leave Without Pay). |
| `staff_attendance` | **UNUSED FOR NOW (0 rows)** | **HR — Staff Biometric Attendance (`/teachers`)**: Daily clock-in/clock-out punch records for teaching and administrative personnel. |
| `staff_leave_requests` | **UNUSED FOR NOW (0 rows)** | **HR — Staff Leave Workflow (`/teachers`)**: Staff leave applications, relief teacher arrangements, and principal approval status. |
| `leave_balances` | **UNUSED FOR NOW (0 rows)** | **HR — Staff Leave Ledger (`/teachers`)**: Annual running leave balance ledger tracking used and available quotas per employee. |
| `salary_structure_items`| **UNUSED FOR NOW (0 rows)** | **Payroll — Detailed Package Breakdown (`/payroll` Planned)**: Line-item earnings and deductions breakdown for customized staff compensation contracts. |
| `payroll_runs` | **UNUSED FOR NOW (0 rows)** | **Payroll Disbursal Screen (`/payroll` Planned)**: Monthly salary processing batches recording wage bills, bank export sheets, and final approval stamps. |
| `payslips` | **UNUSED FOR NOW (0 rows)** | **Employee Payslips (`/payroll` Planned)**: Individual monthly pay vouchers issued to staff with net salary and bank payout reference. |
| `payslip_lines` | **UNUSED FOR NOW (0 rows)** | **Itemized Payslip Ledger (`/payroll` Planned)**: Detailed itemized earnings and statutory PF/ESI deduction lines on employee payslips. |

---

### Domain 10: Admission Management (15 Tables)
*Drives the front-desk admission cycle, inquiry register, applicant screening, scoring, merit ranking, and waitlists.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `admission_cycles` | **LIVE (1 row)** | **Admission Dashboard (`/admission`)**: Active intake cycle (`Academic Year 2026-27 Intake`), start/end dates, application fee, and operational status. |
| `cycle_class_config` | **LIVE (3 rows)** | **Class Intake Capacity (`/admission`)**: Seat capacity and age limits per class (Class 1: 40 seats, Class 6: 20 seats, Class 9: 15 seats; interview & written test toggles). |
| `enquiries` | **LIVE (6 rows)** | **Enquiry Register (`/admission/enquiries`)**: Front desk walk-in and phone inquiry register with lead sources, candidate details, and conversion status. |
| `applications` | **UNUSED FOR NOW (0 rows)** | **Application Register (`/admission/applications`)**: 360° applicant dossiers holding applicant biodata, category, photo, and submission timestamp. |
| `enquiry_interactions` | **UNUSED FOR NOW (0 rows)** | **Enquiry Timeline (`/admission/enquiries`)**: Follow-up interaction log (phone calls, counselling notes, campus visits) per enquiry. |
| `application_guardians` | **UNUSED FOR NOW (0 rows)** | **Applicant Family Dossier (`/admission/applications` Tab 2)**: Secondary parent/guardian records submitted during admission registration. |
| `application_siblings` | **UNUSED FOR NOW (0 rows)** | **Applicant Siblings (`/admission/applications` Tab 2)**: Reference to elder siblings currently studying in the school for admission quota points. |
| `application_medical` | **UNUSED FOR NOW (0 rows)** | **Applicant Medical Tab (`/admission/applications` Tab 7)**: Chronic medical conditions, allergies, and emergency medical contacts for new applicants. |
| `application_payments` | **UNUSED FOR NOW (0 rows)** | **Application Fee Receipts (`/admission/applications` Tab 6)**: Application registration fee transaction receipts with payment mode and voucher number. |
| `assessments` | **UNUSED FOR NOW (0 rows)** | **Applicant Screening (`/admission/merit`)**: Scheduled entrance evaluation sessions for applicants applying for Class 6 and 9. |
| `assessment_subjects` | **UNUSED FOR NOW (0 rows)** | **Assessment Scoring (`/admission/merit`)**: Subject-level entrance test scores (English, Mathematics, Science) entered by evaluation teachers. |
| `interviews` | **UNUSED FOR NOW (0 rows)** | **Applicant Interviews (`/admission/merit`)**: Interaction ratings and principal interview remarks for primary school admissions. |
| `admission_decisions` | **UNUSED FOR NOW (0 rows)** | **Merit & Selection (`/admission/merit`)**: Final selection decisions (`selected`, `waitlisted`, `rejected`, `offered`) with audited principal reasons. |
| `admission_offers` | **UNUSED FOR NOW (0 rows)** | **Offer Letters & Conversion (`/admission/applications`)**: Formal provisional offer letters issued to selected students with fee payment deadlines. |
| `waitlist_entries` | **UNUSED FOR NOW (0 rows)** | **Waitlist Queue (`/admission/waitlist`)**: Ordered queue of waitlisted candidates with position ranks, capacity gauges, and seat promotion actions. |

---

### Domain 11: Communication & Notices (5 Tables)
*Drives the school digital notice board, parent notifications, and delivery tracking.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `notices` | **LIVE (6 rows)** | **Notices Screen (`/notices`, `/dashboard`)**: School notice board with audience targeting (`all`, `students`, `teachers`, `parents`, `class_10a`). |
| `message_templates` | **LIVE (6 rows)** | **Message Composer (`/notices`)**: Pre-approved TRAI DLT message templates for fee reminders, attendance absence alerts, and urgent closures. |
| `messages` | **UNUSED FOR NOW (0 rows)** | **Comms Outbox — Broadcast System (`/notices` Planned)**: Outbound communication batch queue for SMS, WhatsApp, and Email alerts. |
| `message_recipients` | **UNUSED FOR NOW (0 rows)** | **Delivery Tracking (`/notices` Planned)**: Recipient-level dispatch logs tracking delivery statuses (`sent`, `delivered`, `failed`). |
| `notification_preferences`| **UNUSED FOR NOW (0 rows)**| **Parent Notification Settings (`/settings`)**: Guardian opt-in/opt-out channel preferences per message category. |

---

### Domain 12: Inventory & Stock Management (2 Tables)
*Drives the school consumable catalog, minimum quantity alerts, and purchase approval workflows.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `stock_items` | **LIVE (8 rows)** | **Stock Screen (`/inventory`)**: Consumables and equipment catalogue (Chalk, Whiteboard Markers, Printing Paper, Footballs) with reorder thresholds and live stock counts. |
| `stock_requests` | **LIVE (5 rows)** | **Stock Indents & Approvals (`/inventory`, Mobile)**: Purchase and issuance requests submitted by teachers and staff, with administrator approval modal. |

---

### Domain 13: Grievances & Feedback System (2 Tables)
*Drives the ticketing helpdesk, priority queues, staff assignments, and conversational resolution threads.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `grievances` | **LIVE (5 rows)** | **Grievance Feed (`/dashboard`, Mobile Helpdesk)**: School helpdesk tickets raised by parents and teachers (categorized by Facilities, Academic, Transport, Billing) with priority and status tracking. |
| `grievance_replies` | **LIVE (4 rows)** | **Ticket Detail Modal (`/dashboard`, Mobile)**: Conversational messages, internal administrative notes, and parent/teacher replies on grievance threads. |

---

### Domain 14: System Documents & Audit (4 Tables)
*Drives document verification checklists, binary file storage, background scheduler, and compliance audit logs.*

| Table | Status | Website / ERP Feature & Usage |
|---|:---:|---|
| `document_types` | **LIVE (8 rows)** | **Document Setup (`/configuration`, `/admission/applications`)**: Mandatory document checklist definitions (Birth Certificate, Transfer Certificate, Aadhaar Card, Previous Marksheet). |
| `documents` | **LIVE (25 rows)** | **Dossier Attachments (`/students`, `/admission/applications`)**: Uploaded student and employee identity files, verification status, and MIME file metadata. |
| `scheduled_jobs` | **LIVE (4 rows)** | **Background Automation (`/configuration`)**: System cron definitions for automated nightly fee invoice generation, daily absentee alerts, and attendance aggregation. |
| `audit_log` | **LIVE (150 rows)** | **Contract 3 Compliance Audit Log (System-Wide)**: Immutable audit trail recording every write/status change/reverse action with timestamp, user identity, IP address, and user-typed reason. |
| `jobs` | **UNUSED FOR NOW (0 rows)** | **System — Asynchronous Worker Queue**: Planned background job runner table for long-running report exports and bulk PDF generation tasks. |

---

## 4. Synthesis of Reference Documents in `docs/`

To ensure the new PDF document aligns with the project's documentation standards:

1. **`docs/Sunrise-ERP-Features-Operational-and-Planned.pdf`**:
   - Outlines the 22 operational features live in the web ERP.
   - Highlights planned modules: `/payroll` (salary disbursal), session rollover & promotion engine, public admission portal (`/apply`), and bulk legacy Excel imports.
   - **Key takeaway for Session 5**: Clearly demarcate each of the 28 `UNUSED FOR NOW` tables as either belonging to an operational counter workflow or a planned roadmap module.
2. **`docs/Sunrise-ERP-Database.pdf`**:
   - The authoritative 89-table technical specification generated via `scripts/gen_db_pdf.py`.
   - Contains all column types, nullability, foreign keys, and defaults.
3. **`docs/Sunrise-ERP-Database-Essentials.pdf`**:
   - Explains the 61 populated tables that hold live demonstration rows.
   - Contains entity relationship diagrams for Core Tenancy, Academics, Fees, and Transport.
4. **`docs/Sunrise-ERP-Database-Essentials-Explained.pdf`**:
   - Step-by-step plain English business narrative explaining how data travels through the school office.
5. **`docs/Sunrise-ERP-Database-Viva-100.pdf`**:
   - 100 deep technical and architectural questions explaining why the database is modeled the way it is (financial immutability, scoping invariants, multi-tenancy).

---

## 5. Implementation Roadmap for Next Session

In Session 5, the agent should follow this exact sequence:

### Step 1: Create the Generator Script
- Write `scripts/gen_db_tables_feature_mapping_pdf.py`.
- Introspect the database via `psql` (querying `pg_class`, `information_schema.columns`, `information_schema.table_constraints`, and live row counts).
- Incorporate the comprehensive table-to-feature mapping derived in Section 3 of this handoff.
- Implement clear visual badge formatting:
  - Green badge: `<span class="badge-live">LIVE / IN USE (X rows)</span>` for the 61 populated tables.
  - Amber badge: `<span class="badge-unused">UNUSED FOR NOW</span>` for the 28 unpopulated tables.

### Step 2: Design Print-Optimized HTML
- Generate `docs/database-tables-and-features-print.html`.
- Incorporate Lucknow school context branding (Sunrise Public School, `#5B4BE0` primary palette).
- Ensure strict print styling:
  - `@page { size: A4; margin: 16mm 14mm 16mm 14mm; }`
  - `break-inside: avoid;` on all table cards to prevent awkward mid-table page splits.
  - Interactive Table of Contents with jump links and domain summaries.
  - Feature mapping box for every table highlighting the Web Screen, Component, and Workflow.

### Step 3: Headless Chrome PDF Compilation
- Compile the PDF deliverable using Headless Chrome:
  ```powershell
  & "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --no-pdf-header-footer --virtual-time-budget=20000 --print-to-pdf="docs\Sunrise-ERP-Database-Tables-and-Features.pdf" "file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/docs/database-tables-and-features-print.html"
  ```
- Verify the generated file size and page integrity.

### Step 4: Verification & Contract Checks
- Run `python scripts/verify_db_docs.py` to confirm that all 89 tables are accounted for with zero omissions.
- Inspect the PDF visually via Puppeteer or screenshot verification to confirm clean layout, typography, and badge alignment.
- Update `SINGLE_SOURCE_OF_TRUTH.md` with the new PDF deliverable.

---

## 6. Binding Operational Reminders for the Next Agent

- **Strictly Local Git**: Work on `slice/office-feedback`. Do not push to GitHub or create PRs.
- **Do Not Fabricate**: Every table column, foreign key, and row count must be live-introspected from `sunrise_test`.
- **Badge Exact Phrase**: The user specifically requested: **"IN FRONT OF NON ESSENTIAL TABLES WRITE 'UNUSED FOR NOW'"**. Do not use different phrasing.
- **Multi-Tenant Rule**: Remember that `school_id` multi-tenant scoping applies to all tables except the system tables (`schools`, `alembic_version`).
