"""Chapter 4 & 5: Operational Workflows Part 4
Covers:
14. Notices & Targeted Broadcasts (14.1 - 14.2)
15. Transport Routes & Bus Manifests (15.1 - 15.2)
16. Stock Inventory & Low-Stock Alerts (16.1 - 16.3)
17. Grievance Redressal & Helpdesk (17.1 - 17.2)
18. School Analytics & Reports Center (18.1)
"""

from .ch3_workflows_part1 import render_workflow

def render_ch3_part4() -> str:
    content = """
<div class="section-banner">
  <h2>7. Detailed Operational Workflows: Operations, Communications & Analytics</h2>
  <p class="desc">Logistics data flows for fleet transport, consumables catalog, multi-tier grievances, and dynamic reporting.</p>
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

    return content
