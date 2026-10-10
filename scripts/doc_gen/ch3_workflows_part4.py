"""Chapter 4 & 5: Operational Workflows Part 4
Covers:
14. Notices & Targeted Broadcasts (14.1 - 14.2)
15. Transport Routes & Bus Manifests (15.1 - 15.2)
16. Stock Inventory & Low-Stock Alerts (16.1 - 16.3)
17. Grievance Redressal & Helpdesk (17.1 - 17.2)
18. School Analytics & Reports Center (18.1)
19. Library Circulation Desk & Lending (19.1)
20. Student Certificate Generation & Official Issuance (20.1)
21. Academic Calendar & Multi-Section Holidays (21.1)
22. Front Desk Reception Suite: Gate Passes, Principal Meetings & Found Property (22.1)
"""

from .ch3_workflows_part1 import render_workflow

def render_ch3_part4() -> str:
    content = """
<div class="section-banner">
  <h2>7. Detailed Operational Workflows: Logistics, Library, Student Services & Front Desk</h2>
  <p class="desc">Operational data flows for consumable inventory, helpdesk grievances, analytics, library circulation desk, certificates, holidays, and front desk reception.</p>
</div>
"""

    # --- 16.2 Requisition & Low Stock Alerts ---
    content += render_workflow(
        wf_id="16.2",
        title="Inventory Requisition Workflow, Reactive Stock Levels & Low-Stock Threshold Alerts",
        overview={
            "real_life": "The school stores lab consumables, stationery, and sports equipment. Staff submit requisitions for supplies, and the system alerts the storekeeper when quantities fall below safe minimum thresholds.",
            "actor": "Staff Member (requisition), Storekeeper / Admin (approval & issue).",
            "trigger": "Stock request submission on <code>/inventory</code> or mobile stock tab.",
            "problem": "Running out of critical teaching supplies (chalk, printer paper, test tubes) and unmonitored stock shrinkage.",
            "outcome": "Stock request approved; inventory quantity decremented; low-stock alarm triggered if balance &lt; minimum threshold."
        },
        steps=[
            "<strong>User Action:</strong> Chemistry teacher submits a request for 10 units of 'Laboratory Glass Flasks'.",
            "<strong>Frontend Processing:</strong> <code>Inventory.tsx</code> submits <code>POST /api/v1/admin/inventory/requests</code>.",
            "<strong>Request Header Insertion:</strong> Inserts parent row in <code>stock_requests</code> with status <code>pending</code>.",
            "<strong>Admin Review & Approval:</strong> Storekeeper opens request approval modal, inspects available shelf stock, and clicks 'Approve & Issue'.",
            "<strong>Inventory Quantity Decrement:</strong> Backend updates <code>stock_items.quantity = quantity - requested_quantity</code>.",
            "<strong>Threshold Evaluation:</strong> Checks if <code>stock_items.quantity &lt;= stock_items.min_quantity</code>.",
            "<strong>Alarm Activation:</strong> If below threshold, flags <code>stock_items.is_low_stock = True</code>; triggers visual amber badge on admin dashboard.",
            "<strong>Final Output:</strong> Teacher receives supplies; stock catalog reflects real-time quantity; purchase order alert posted."
        ],
        diagram="""[Staff Member Screen]
       │
       ▼ (POST /admin/inventory/requests)
[Inventory Service (app/services/inventory.py)]
       │
       ├─► [INSERT] stock_requests ──────► Create request (item_id=5, qty=10, status='pending')
       │
       ▼ (Admin Clicks 'Approve & Issue')
[Stock Issue & Decrement Engine]
       │
       ├─► [UPDATE] stock_requests ──────► Set status = 'approved', approved_at = NOW()
       │
       ├─► [UPDATE] stock_items ─────────► Decrement quantity (e.g. 15 - 10 = 5)
       │         │
       │         ▼
       ├─► [CHECK] min_quantity ─────────► 5 <= 8 (min_quantity) -> TRIGGER ALARM
       │         │
       │         ▼
       └─► [UPDATE] stock_items ─────────► Set is_low_stock = True
       │
       ▼
[Stock Issued; Low Stock Re-order Alert Displayed]""",
        transfers=[
            ("1", "Staff Requisition", "Inventory API", "item_id, quantity, purpose", "INSERT", "Submit consumable supply request"),
            ("2", "Inventory Service", "stock_requests table", "item_id, requested_by, quantity, status", "INSERT", "Record pending stock requisition"),
            ("3", "Issue Service", "stock_items table", "quantity = quantity - requested_quantity", "UPDATE", "Deduct issued items from physical stock"),
            ("4", "Issue Service", "stock_requests table", "status='approved', approved_by", "UPDATE", "Complete requisition lifecycle")
        ],
        tables=[
            ("stock_items", "Consumable catalog", "id (BigInt)", "name, category_id, quantity, min_quantity, unit", "category_id -> stock_categories.id", "Stock catalog items (31 rows)", "Maintains current inventory balance and threshold"),
            ("stock_requests", "Supply requisitions", "id (BigInt)", "item_id, employee_id, quantity, status", "item_id -> stock_items.id, employee_id -> employees.id", "Stock requisitions (9 rows)", "Tracks requisition from request to fulfillment")
        ],
        lifecycle="<strong>Reactive Quantity Auditing:</strong> Inventory items are never deleted once issued. Discontinued items are flagged with <code>is_active = False</code> to preserve historical departmental expenditure records.",
        example="Physics Department requests 10 bundles of A4 Paper (Item #12). Current stock is 15; minimum threshold is 8. Storekeeper approves request. Stock decrements to 5. Since 5 &lt;= 8, the system flags the item as 'Low Stock' on the dashboard."
    )

    # --- 17.2 Grievance Redressal ---
    content += render_workflow(
        wf_id="17.2",
        title="Grievance Redressal, Staff Assignment & Threaded Resolution",
        overview={
            "real_life": "A parent lodges a complaint via the mobile app regarding bus delay. The front office assigns the ticket to the Transport Manager, communicates via real-time threaded chat, and resolves the issue.",
            "actor": "Parent / Teacher (lodging), Admin / Front Office (triage), Assigned Staff (resolution).",
            "trigger": "New ticket appears on Dashboard Grievance feed or <code>/grievances</code>.",
            "problem": "Unorganized parent complaints, lost feedback, lack of accountability, and missing resolution history.",
            "outcome": "Ticket categorized, assigned to staff member, threaded responses exchanged, and status closed with resolution notes."
        },
        steps=[
            "<strong>Ticket Submission:</strong> Parent submits grievance from mobile app. System inserts row into <code>grievances</code> with status <code>open</code>.",
            "<strong>Dashboard Triage:</strong> Admin sees ticket in Dashboard feed; clicks 'View Thread' to open detail modal.",
            "<strong>Staff Assignment:</strong> Admin selects Transport Manager (TCH008) from <code>/admin/grievances/staff</code> selector; updates <code>grievances.assigned_to_id</code>.",
            "<strong>Threaded Chat:</strong> Transport Manager posts a response: <em>'Route 2 bus encountered flat tire; replacement dispatched.'</em>",
            "<strong>Reply Insertion:</strong> Backend inserts row into <code>grievance_replies</code> referencing <code>grievance_id</code>.",
            "<strong>Parent Notification:</strong> Push notification sent to parent mobile app.",
            "<strong>Ticket Closure:</strong> Admin clicks 'Resolve'; sets <code>grievances.status = 'resolved'</code> and records resolution timestamp.",
            "<strong>Final Output:</strong> Complaint formally resolved; full conversation transcript preserved for administrative review."
        ],
        diagram="""[Parent Mobile App] ──► [POST /api/v1/parent/grievances] ──► [INSERT] grievances (status='open')
                                                                         │
                                                                         ▼
[Admin Dashboard Feed] ◄─────────────────────────────────────────────────┘
       │
       ├─► [UPDATE] grievances ──────────────► Assign to Transport Manager (assigned_to_id=8)
       │
       ├─► [INSERT] grievance_replies ───────► Staff posts explanation in thread
       │         │
       │         ▼
       ├─► [PUSH ALERT] ─────────────────────► Parent notified of reply on mobile
       │
       ▼ (Admin Clicks 'Resolve Ticket')
[Grievance Resolution Service]
       │
       └─► [UPDATE] grievances ──────────────► Set status = 'resolved', resolved_at = NOW()
       │
       ▼
[Ticket Closed; Complete Conversation Auditable]""",
        transfers=[
            ("1", "Parent Mobile App", "Grievance API", "title, description, category, student_id", "INSERT", "Lodge formal parental grievance"),
            ("2", "Grievance Service", "grievances table", "ticket_no, created_by, status='open'", "INSERT", "Create grievance tracking header"),
            ("3", "Admin Action", "grievances table", "assigned_to_id = employee.id", "UPDATE", "Delegate ticket to responsible department"),
            ("4", "Staff / Parent Chat", "grievance_replies table", "grievance_id, user_id, message", "INSERT", "Add immutable conversational reply to thread"),
            ("5", "Admin Action", "grievances table", "status='resolved', resolution_notes", "UPDATE", "Close ticket with formal administrative outcome")
        ],
        tables=[
            ("grievances", "Grievance ticket header", "id (BigInt)", "ticket_no, title, category, status, assigned_to_id, student_id", "assigned_to_id -> employees.id, student_id -> students.id", "Grievance tickets (5 rows)", "Primary entity governing complaint lifecycle"),
            ("grievance_replies", "Threaded chat replies", "id (BigInt)", "grievance_id, user_id, message, created_at", "grievance_id -> grievances.id, user_id -> users.id", "Conversation transcripts (4 rows)", "Stores chronologically ordered thread messages")
        ],
        lifecycle="<strong>Tenant Scoping & Child Privacy:</strong> <code>grievances.student_id</code> is optional; when present, it links the complaint to a specific child master record. Parents can only view grievances created by their own user account.",
        example="Father of Aarav Sharma files ticket <code>GRV-2026-004</code> regarding bus arrival delay. Admin assigns ticket to Transport Head. Transport Head replies explaining construction detour. Parent acknowledges. Admin marks ticket 'resolved'."
    )

    # --- 18.1 Reports Library ---
    content += render_workflow(
        wf_id="18.1",
        title="School Analytics & Reports Center: Parameterized Query Execution & CSV Export",
        overview={
            "real_life": "School Principal, CBSE Inspector, or Auditor requests a statistical breakdown (e.g. Fee Defaulters List, Class Attendance Summary, Staff Salary Register).",
            "actor": "Principal / Auditor / Registrar at <code>/reports</code>.",
            "trigger": "User selects report card from 21 registered reports and clicks 'Run Report'.",
            "problem": "Extracting aggregated cross-module metrics quickly without executing dangerous ad-hoc SQL queries on the live database.",
            "outcome": "Backend executes parameterized SQL aggregator; streams formatted data table, summary stat cards, and authenticated CSV download."
        },
        steps=[
            "<strong>User Action:</strong> User navigates to <code>/reports</code>, picks category 'Fees & Financials', and clicks 'Fee Defaulters Aging Report'.",
            "<strong>Frontend Processing:</strong> <code>Reports.tsx</code> renders dynamic filter parameters modal (Academic Year, Class, Minimum Overdue Amount).",
            "<strong>Backend Registry Lookup:</strong> <code>app/core/report_registry.py</code> resolves registered report metadata and verifies caller permissions.",
            "<strong>Optimized Query Execution:</strong> Backend runs parameterized SQL analytical query across <code>fee_invoices</code>, <code>payment_allocations</code>, and <code>enrolments</code>.",
            "<strong>Aggregation & Formatting:</strong> Calculates summary metrics (Total Defaulters, Total Outstanding Amount, 30/60/90 Day Aging Brackets).",
            "<strong>CSV Stream Generation:</strong> If user clicks 'Export CSV', streaming response formats data with RFC 4180 compliance and UTF-8 BOM encoding.",
            "<strong>Final Output:</strong> Instant on-screen analytical visualizer and downloadable audit spreadsheet."
        ],
        diagram="""[Administrator / Auditor Screen (/reports)]
       │
       ▼ (GET /api/v1/reports/{code}/run?params)
[Report Engine (app/core/report_registry.py)]
       │
       ├─► [READ] report_registry ────────► Verify user has required permissions
       │
       ├─► [EXECUTE SQL] Target Tables ───► Run optimized analytical JOIN query
       │         │                          (e.g. fee_invoices JOIN payment_allocations)
       │         ▼
       ├─► [COMPUTE] Metric Aggregates ───► Total Outstanding, Aging Distribution
       │
       └─► [STREAM] CSV / JSON Data ──────► Return structured payload to client
       │
       ▼
[Interactive Grid Rendered; Audit CSV Downloaded]""",
        transfers=[
            ("1", "Reports UI", "Report Runner API", "report_code, filter_params", "READ", "Request parameterized report execution"),
            ("2", "Report Engine", "Database Engine", "Analytical SQL Query with parameters", "READ", "Extract aggregated cross-table metrics"),
            ("3", "Report Engine", "Client Browser", "Summary Cards, Data Grid, CSV Stream", "READ", "Deliver audit-ready analytical report")
        ],
        tables=[
            ("report_registry (Code)", "Report definition catalog", "In-Memory / Core", "code, title, category, required_permissions, sql_query", "None", "21 registered operational reports", "Governs schema and parameter requirements of reports"),
            ("fee_invoices / marks / attendance", "Operational source tables", "BigInt", "Various analytical columns", "Various FKs", "Live operational records", "Source data scanned by reporting queries")
        ],
        lifecycle="<strong>Read-Only Safety:</strong> Report execution is strictly read-only. Database connection operates with read locks or standard MVCC non-blocking snapshots, ensuring that large analytical queries never impede counter fee collections or morning attendance taking.",
        example="Principal runs 'Student Fee Defaulters Aging Report' for Class 10 with minimum amount ₹5,000. System queries live invoice lines and payment allocations, returning 8 students owing a combined ₹62,000. Principal exports the list to CSV for immediate parent follow-up."
    )

    # --- 19.1 Library Circulation Desk ---
    content += render_workflow(
        wf_id="19.1",
        title="Library Circulation Desk, Physical Barcode Inventory & Lending Lifecycle",
        overview={
            "real_life": "The School Librarian catalogs accessioned books, registers barcode-tagged physical copies, issues books to enrolled students and faculty, and processes loan returns with automated overdue tracking.",
            "actor": "Librarian (dedicated RBAC role) or School Administrator.",
            "trigger": "Librarian registers books, scans barcode at Circulation Desk (<code>/library/issue</code>), or logs returns at <code>/library/loans</code>.",
            "problem": "Manual paper book ledgers lead to untracked asset loss, missed return dates, uncollected fines, and inventory discrepancies.",
            "outcome": "Books accessioned in <code>books</code>, copies tracked in <code>book_copies</code>, active loans committed to <code>library_loans</code>, and borrower limits enforced."
        },
        steps=[
            "<strong>User Action:</strong> Librarian registers title, ISBN, author, and copies in the catalog modal on <code>/library/catalog</code>.",
            "<strong>Accession Ingestion:</strong> Backend inserts book header into <code>books</code> and generates individual physical barcode entries in <code>book_copies</code> with <code>status='available'</code>.",
            "<strong>Circulation Checkout:</strong> At the Circulation Desk (<code>/library/issue</code>), the Librarian enters copy barcode and selects borrower (student enrollment or staff member).",
            "<strong>Borrower Rule Validation:</strong> System checks borrower active loan count against loan policy limits and verifies the copy status is <code>available</code>.",
            "<strong>Loan Creation:</strong> Dispatches <code>POST /api/v1/library/loans</code>; creates loan record in <code>library_loans</code> with due date (default +14 days) and updates <code>book_copies.status = 'issued'</code>.",
            "<strong>Return Check-in:</strong> When borrower returns the item, Librarian scans barcode; dispatches <code>PUT /api/v1/library/loans/{id}/return</code>.",
            "<strong>Inventory Reset:</strong> Sets <code>library_loans.returned_on = CURRENT_DATE</code>, calculates fine if overdue, and resets <code>book_copies.status = 'available'</code>."
        ],
        diagram="""[Librarian Screen: /library]
       │
       ├─► [POST /api/v1/library/books] ──────► [INSERT] books & book_copies (Accession & Barcodes)
       │
       ▼ (Circulation Issue: POST /library/loans)
[Circulation Desk Validation]
       │
       ├─► [READ] book_copies ────────────────► Check status == 'available'
       ├─► [READ] library_loans ──────────────► Verify borrower active loans < max_allowed
       ├─► [INSERT] library_loans ────────────► Record loan (book_copy_id, enrolment_id, due_date)
       └─► [UPDATE] book_copies ──────────────► Set status = 'issued'
       │
       ▼ (Check-in / Return: PUT /library/loans/{id}/return)
[Return Desk & Fine Assessment]
       │
       ├─► [UPDATE] library_loans ────────────► Set returned_on = TODAY, fine_amount
       └─► [UPDATE] book_copies ──────────────► Reset status = 'available'""",
        transfers=[
            ("1", "Catalog Form", "Library API", "isbn, title, author, copies", "INSERT", "Register new book title and physical accession count"),
            ("2", "Circulation Screen", "Library API", "barcode, enrolment_id, due_date", "INSERT", "Issue book copy to active borrower"),
            ("3", "Library Service", "book_copies table", "copy_id, status='issued'", "UPDATE", "Lock physical copy against duplicate lending"),
            ("4", "Library Service", "library_loans table", "loan record, issued_by_id", "INSERT", "Record formal lending transaction"),
            ("5", "Return Desk", "book_copies & library_loans", "returned_on, status='available'", "UPDATE", "Complete loan cycle and restore copy to shelf")
        ],
        tables=[
            ("books", "Library book catalog", "id (BigInt)", "isbn, title, author, total_copies, available_copies", "school_id -> schools.id", "Title master catalog", "Tracks title metadata and stock aggregates"),
            ("book_copies", "Physical barcode copies", "id (BigInt)", "book_id, accession_no, barcode, status", "book_id -> books.id, school_id -> schools.id", "Individual book items on shelves", "Tracks circulation state ('available' vs 'issued')"),
            ("library_loans", "Circulation loan register", "id (BigInt)", "book_copy_id, enrolment_id, employee_id, due_date, returned_on, fine_amount", "book_copy_id -> book_copies.id, enrolment_id -> enrolments.id", "Active and historical loans", "Enforces borrowing rules and overdue penalties"),
            ("enrolments", "Class enrollment roster", "id (BigInt)", "student_id, class_section_id, roll_no", "student_id -> students.id", "Enrolled student records", "Identifies pupil borrowers by academic section")
        ],
        lifecycle="<strong>Circulation State Machine:</strong> Physical copy states follow <code>available -> issued -> available</code> (or <code>lost / damaged</code>). Loans transition from active (<code>returned_on IS NULL</code>) to returned. Granular RBAC ensures users holding only the <code>LIBRARIAN</code> role can execute loans without accessing financial ledgers or student grading.",
        example="Librarian Priya issues copy 'BC-MATH-10-04' of 'NCERT Mathematics Class 10' to student Rahul Sharma (Enrolment 101). The system verifies Rahul currently holds only 1 other active loan (below the limit of 3), creates <code>library_loans</code> record due in 14 days, and flips the copy status to 'issued'. Upon return, the book is checked in and instantly available for other students."
    )

    # --- 20.1 Student Certificate Issuance ---
    content += render_workflow(
        wf_id="20.1",
        title="Student Certificate Generation, Templated Layout & Official Document Issuance",
        overview={
            "real_life": "School administrative staff generates Transfer Certificates (TC), Bonafide Certificates, Study Certificates, or Character Certificates for enrolled students.",
            "actor": "School Registrar / Academic Administrative Officer / Principal.",
            "trigger": "Staff member selects student at <code>/certificates</code>, selects certificate template, and initiates issuance.",
            "problem": "Manual word-processor drafting produces non-standard formatting, duplicate certificate serial numbers, and lacks audit trails.",
            "outcome": "Certificate generated from <code>certificate_templates</code>, recorded in <code>student_certificates</code> with unique number and snapshot data, ready for PDF printing."
        },
        steps=[
            "<strong>User Action:</strong> Officer selects student and certificate type (e.g. 'Bonafide') on <code>/certificates</code>.",
            "<strong>Template Resolution:</strong> Backend queries <code>certificate_templates</code> matching school ID and certificate type.",
            "<strong>Data Snapshot Compilation:</strong> Merges live student identity, section roll, father's name, admission date, and attendance percentage into template placeholders.",
            "<strong>Unique Number Generation:</strong> Allocates next sequential certificate number (e.g. <code>CERT-2026-0042</code>) unique per school tenant.",
            "<strong>Record Commitment:</strong> Dispatches <code>POST /api/v1/certificates/issue</code>; inserts row into <code>student_certificates</code> storing serialized snapshot and issue timestamp.",
            "<strong>Print Render:</strong> Returns formatted HTML/PDF preview complete with official school header, digital signature block, and CBSE school seal."
        ],
        diagram="""[Administrative Staff: /certificates]
       │
       ▼ (POST /api/v1/certificates/issue)
[Certificate Issuance Engine (api/admin/certificates.py)]
       │
       ├─► [READ] certificate_templates ────► Resolve template layout & header/body texts
       ├─► [READ] students & enrolments ────► Extract student biodata, admission date, section
       ├─► [GENERATE] Unique Serial No ─────► Generate CERT-2026-0042
       ├─► [INSERT] student_certificates ───► Store issued certificate with data snapshot
       └─► [INSERT] audit_log ──────────────► Record administrative issuance event
       │
       ▼
[Official Certificate Rendered & PDF Generated for Printing]""",
        transfers=[
            ("1", "Certificates UI", "Certificates API", "student_id, certificate_type", "INSERT", "Initiate certificate generation request"),
            ("2", "Certificates Service", "certificate_templates", "certificate_type filter", "READ", "Fetch approved institutional template text"),
            ("3", "Certificates Service", "students & enrolments", "student_id, enrolment_id", "READ", "Extract verified student biodata and enrolment facts"),
            ("4", "Certificates Service", "student_certificates", "certificate_no, snapshot, status", "INSERT", "Commit immutable issued certificate voucher"),
            ("5", "Certificates Service", "Client Browser", "Printable Certificate PDF", "READ", "Deliver formatted official institutional document")
        ],
        tables=[
            ("certificate_templates", "Institutional templates", "id (BigInt)", "certificate_type, title, header_text, body_template, show_seal", "school_id -> schools.id", "Approved certificate formats", "Provides layout structure and legal boilerplate"),
            ("student_certificates", "Issued certificate register", "id (BigInt)", "certificate_no, student_id, enrolment_id, issue_date, data_snapshot, status", "student_id -> students.id, enrolment_id -> enrolments.id", "Official issuance records", "Guarantees document uniqueness and preserves frozen snapshot"),
            ("students", "Student master identity", "id (BigInt)", "admission_no, dob, gender, user_id", "user_id -> users.id", "Lifetime student master", "Supplies permanent student identification details"),
            ("enrolments", "Class enrollment roster", "id (BigInt)", "class_section_id, roll_no, academic_year_id", "section_id -> class_sections.id", "Academic year facts", "Supplies current class, section, and roll number")
        ],
        lifecycle="<strong>Frozen Snapshot Invariant:</strong> Issued certificates store a complete JSON <code>data_snapshot</code> at moment of generation. Even if student information or class names change later, the historic issued certificate preserves exact state as certified.",
        example="Registrar issues a 'Bonafide Certificate' for student Aarav Sharma (Class 7-A). System pulls template, generates serial <code>CERT-2026-0012</code>, saves full snapshot in <code>student_certificates</code>, and prints the stamped document for parent passport application."
    )

    # --- 21.1 Multi-Section Academic Holidays ---
    content += render_workflow(
        wf_id="21.1",
        title="Multi-Section Academic Calendar & Holiday Overrides",
        overview={
            "real_life": "School leadership configures school-wide holidays as well as class-specific breaks (such as Nursery-only monsoon holidays or Class 10/12 board study preparatory leaves).",
            "actor": "Academic Coordinator / School Principal.",
            "trigger": "Coordinator schedules a holiday at <code>/holidays</code> and specifies applicable class sections.",
            "problem": "Uniform school-wide holiday declarations fail to capture section-specific breaks, incorrectly marking absent students during authorized class breaks.",
            "outcome": "Holiday created in <code>holidays</code> and selectively linked to cohorts in <code>holiday_class_sections</code>, suppressing false attendance alarms."
        },
        steps=[
            "<strong>User Action:</strong> Coordinator fills holiday name, date range, and selects target classes (or 'All School') at <code>/holidays</code>.",
            "<strong>Frontend Processing:</strong> <code>Holidays.tsx</code> submits <code>POST /api/v1/holidays</code> with date bounds and optional array of <code>class_section_ids</code>.",
            "<strong>Master Holiday Insertion:</strong> Backend inserts header record into <code>holidays</code> with name, date range, and school ID.",
            "<strong>Section Scoping Junction:</strong> If specific sections are chosen, inserts rows into <code>holiday_class_sections</code> mapping holiday ID to each section.",
            "<strong>Attendance Gate Integration:</strong> Daily attendance roll-call API checks whether today's date matches a general or section-scoped holiday.",
            "<strong>UI & Calendar Sync:</strong> Holiday appears highlighted on academic calendars and class teacher attendance registers."
        ],
        diagram="""[Academic Coordinator: /holidays]
       │
       ▼ (POST /api/v1/holidays)
[Calendar Service (api/admin/holidays.py)]
       │
       ├─► [INSERT] holidays ────────────────► Create holiday header (name, start_date, end_date)
       │         │
       │         ▼ (holiday.id)
       └─► [INSERT] holiday_class_sections ──► Map specific section IDs (e.g. Nursery-A, Nursery-B)
       │
       ▼ (Daily Attendance Check: POST /attendance/mark)
[Attendance Engine Gate]
       │
       └─► [READ] holiday_class_sections ────► Suppresses morning roll-call for targeted sections""",
        transfers=[
            ("1", "Holiday Form", "Calendar API", "name, start_date, end_date, section_ids", "INSERT", "Create academic holiday with optional section filters"),
            ("2", "Calendar API", "holidays table", "name, start_date, end_date, school_id", "INSERT", "Store master institutional holiday definition"),
            ("3", "Calendar API", "holiday_class_sections", "holiday_id, class_section_id", "INSERT", "Bind holiday to specific classroom cohorts"),
            ("4", "Attendance Service", "holiday_class_sections", "date, class_section_id", "READ", "Verify section is exempt from roll-call on specified date")
        ],
        tables=[
            ("holidays", "School holiday calendar", "id (BigInt)", "name, start_date, end_date, is_academic, description", "school_id -> schools.id", "Calendar holiday events", "Defines the holiday time window and description"),
            ("holiday_class_sections", "Section-holiday junction", "id (BigInt)", "holiday_id, class_section_id, school_id", "holiday_id -> holidays.id, class_section_id -> class_sections.id", "Section-specific holiday mappings", "Restricts holiday applicability to designated grades"),
            ("class_sections", "Classroom sections", "id (BigInt)", "class_name, section_name", "school_id -> schools.id", "Class cohorts", "Supplies class section target identifiers")
        ],
        lifecycle="<strong>Calendar Filtering:</strong> When <code>holiday_class_sections</code> has no entries for a holiday, the holiday applies school-wide. When entries exist, only the mapped sections observe the holiday, preserving regular registers for other grades.",
        example="Principal declares a 2-day 'Monsoon Rain Break' for Nursery and LKG only. System creates <code>holidays</code> row and inserts 2 rows into <code>holiday_class_sections</code>. Class 1 through 12 teachers mark normal attendance, while Nursery roll-calls are automatically disabled."
    )

    # --- 22.1 Front Desk Reception Suite ---
    content += render_workflow(
        wf_id="22.1",
        title="Front Desk Reception Suite: Student Passes, Principal Meetings & Found Property",
        overview={
            "real_life": "Campus security and front desk staff log early departure gate passes, coordinate parent appointment requests with the Principal, and catalog lost personal property.",
            "actor": "Front Desk Receptionist, Campus Security Officer, or Administrative Assistant.",
            "trigger": "Visitor arrives at gate, parent requests student early checkout, or staff deposits lost property at <code>/reception</code>.",
            "problem": "Uncontrolled campus entry, unauthorized child pickups, unmanaged administrative queues, and lost student belongings.",
            "outcome": "Student gate pass generated in <code>student_passes</code>, appointment logged in <code>principal_meeting_requests</code>, and property tracked in <code>found_items</code>."
        },
        steps=[
            "<strong>Gate Pass Generation:</strong> Parent arrives to pick up student early. Receptionist verifies identity against authorized guardians on <code>/reception/student-passes</code>.",
            "<strong>Pass Creation:</strong> Submits <code>POST /api/v1/reception/passes</code>. System creates <code>student_passes</code> with student ID, pickup person name, relation, phone, ID proof, and unique <code>pass_code</code>.",
            "<strong>Gate Clearance:</strong> Security guard verifies <code>pass_code</code> at gate and records exit timestamp.",
            "<strong>Principal Meeting Request:</strong> Visitor requests meeting. Receptionist logs visitor name, phone, purpose, and student reference into <code>principal_meeting_requests</code> with status <code>pending</code>.",
            "<strong>Lost Property Tracking:</strong> Unclaimed item found on campus. Receptionist registers item name, location, and description into <code>found_items</code> with status <code>found</code>.",
            "<strong>Claim & Handover:</strong> When student claims item, receptionist records claiming student ID, handover notes, and marks status <code>claimed</code>."
        ],
        diagram="""[Receptionist / Security Screen: /reception]
       │
       ├─► [POST /api/v1/reception/passes] ──► [INSERT] student_passes (pass_code, pickup_person, relation)
       │
       ├─► [POST /api/v1/reception/meetings] ► [INSERT] principal_meeting_requests (slip_code, visitor, purpose)
       │
       └─► [POST /api/v1/reception/found] ───► [INSERT] found_items (item_name, location, status='found')
                 │
                 ▼ (Claim Verification & Handover)
           [UPDATE] found_items (status='claimed', claimed_by_student_id, collected_at)""",
        transfers=[
            ("1", "Passes UI", "Reception API", "student_id, pickup_person, relation", "INSERT", "Create authorized student gate exit pass"),
            ("2", "Reception API", "student_passes table", "pass_code, student_id, phone", "INSERT", "Store security pass voucher with unique code"),
            ("3", "Meetings UI", "Reception API", "visitor_name, purpose, student_id", "INSERT", "Log executive meeting appointment request"),
            ("4", "Found Items UI", "Reception API", "item_name, category, location", "INSERT", "Catalog unclaimed personal property"),
            ("5", "Reception API", "found_items table", "claimed_by, collected_at, status", "UPDATE", "Complete property handover audit")
        ],
        tables=[
            ("student_passes", "Gate departure passes", "id (BigInt)", "pass_code, student_id, pickup_person_name, relation, pass_date, status", "student_id -> students.id, school_id -> schools.id", "Authorized student exit passes", "Prevents unauthorized pupil pickup from campus"),
            ("principal_meeting_requests", "Executive visitor slips", "id (BigInt)", "slip_code, visitor_name, visitor_phone, reason, meeting_date, status", "school_id -> schools.id", "Appointments with school leadership", "Manages visitor queues and leadership availability"),
            ("found_items", "Lost and found catalog", "id (BigInt)", "item_name, category, description, found_location, status, claimed_by_student_id", "claimed_by_student_id -> students.id, school_id -> schools.id", "Property registry and handovers", "Provides transparent lost property custody tracking")
        ],
        lifecycle="<strong>Campus Security Lifecycle:</strong> Passes are issued for single-day validity and close upon exit. Meeting slips progress from <code>pending -> approved / completed / rejected</code>. Found items progress from <code>found -> claimed</code> with verified recipient identity.",
        example="Mother of student Ananya Verma arrives at 1:30 PM for doctor appointment pickup. Receptionist enters parent name and phone, verifies relation, and issues gate pass <code>GP-2026-0038</code>. Security confirms pass code at gate, logging clean departure."
    )

    return content

