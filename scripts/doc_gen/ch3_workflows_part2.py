"""Chapter 4 & 5: Operational Workflows Part 2
Covers:
6. Fee Setup, Billing, Collection, Contra, Defaulters & Period Close (6.1 - 6.7)
7. Examinations, Marks Grid, Paper Lock & CBSE Report Cards (7.1 - 7.3)
8. Academic Session Rollover & Cohort Promotion (8.1 - 8.2)
"""

from .ch3_workflows_part1 import render_workflow

def render_ch3_part2() -> str:
    content = """
<div class="section-banner">
  <h2>5. Detailed Operational Workflows: Fees, Examinations & Session Rollover</h2>
  <p class="desc">Deep architectural data flows for financial immutability, grading engines, and multi-year progression.</p>
</div>
"""

    # --- 6.3 Fee Invoicing ---
    content += render_workflow(
        wf_id="6.3",
        title="Monthly Fee Invoicing & Line Item Generation Engine",
        overview={
            "real_life": "At the beginning of each billing month (e.g. April 2026), the school accountant generates monthly invoices for all enrolled students.",
            "actor": "School Accountant or Bursar.",
            "trigger": "Accountant clicks 'Generate Monthly Invoices' at <code>/fees</code>.",
            "problem": "Translating complex class fee structures, monthly fee heads, and individualized student concessions into clean billing records.",
            "outcome": "One <code>fee_invoices</code> header per active student enrollment, with discrete <code>fee_invoice_lines</code> per fee head."
        },
        steps=[
            "<strong>User Action:</strong> Accountant selects Academic Year 2026-27, billing month 'April', and clicks 'Generate Invoices'.",
            "<strong>Frontend Processing:</strong> <code>FeesOverview.tsx</code> submits <code>POST /api/v1/fees/invoices/generate</code> with month and due date parameters.",
            "<strong>Active Period Verification:</strong> Backend verifies the financial period in <code>fee_periods</code> is in <code>open</code> status.",
            "<strong>Roster & Plan Query:</strong> Fetches all active <code>enrolments</code> and resolves their applicable <code>fee_plans</code> and <code>fee_plan_items</code>.",
            "<strong>Concession Application:</strong> Queries <code>fee_concessions</code> to identify approved sibling or merit discounts active for each child.",
            "<strong>Invoice Creation:</strong> Inserts parent row into <code>fee_invoices</code> with total billing amount and status <code>unpaid</code>.",
            "<strong>Invoice Line Breakdown:</strong> Inserts individual child lines into <code>fee_invoice_lines</code> (Tuition, Computer Lab, Annual Sports).",
            "<strong>Final Output:</strong> Invoices generated for 100 students; totals reflected in collection dashboards and parent ledgers."
        ],
        diagram="""[Accountant Billing Action]
       │
       ▼ (POST /fees/invoices/generate)
[Fee Billing Service (app/services/fees.py)]
       │
       ├─► [READ] fee_periods ─────────► Ensure April 2026 is 'open' (not closed)
       ├─► [READ] enrolments ──────────► Fetch active student enrollments
       ├─► [READ] fee_plan_items ──────► Resolve tuition, exam, and activity heads
       ├─► [READ] fee_concessions ─────► Apply approved discounts
       │
       ├─► [INSERT] fee_invoices ──────► Create invoice header (INV-2026-0042)
       │         │
       │         ▼ (fee_invoices.id)
       └─► [INSERT] fee_invoice_lines ─► Insert discrete items (Tuition: ₹3,500, Lab: ₹500)
       │
       ▼
[Student Accounts Billed & Due For Payment]""",
        transfers=[
            ("1", "Frontend Screen", "Fee Invoicing Service", "academic_year_id, month, due_date", "INSERT", "Initiate bulk billing run"),
            ("2", "Billing Service", "enrolments & fee_plans", "enrolment_id, plan_items", "READ", "Determine fee obligations per student"),
            ("3", "Billing Service", "fee_invoices table", "enrolment_id, invoice_no, total_amount", "INSERT", "Create formal student invoice voucher"),
            ("4", "Billing Service", "fee_invoice_lines table", "invoice_id, fee_head_id, amount", "INSERT", "Create auditable line-item breakdown")
        ],
        tables=[
            ("fee_invoices", "Student fee invoice header", "id (BigInt)", "invoice_no, enrolment_id, period_id, total_amount, status", "enrolment_id -> enrolments.id", "Invoices issued to students (300+ rows)", "Represents the student's monthly bill"),
            ("fee_invoice_lines", "Invoice line item details", "id (BigInt)", "invoice_id, fee_head_id, amount, description", "invoice_id -> fee_invoices.id, fee_head_id -> fee_heads.id", "Discrete fee component amounts (900+ rows)", "Granular bill lines allocated during payment"),
            ("fee_heads", "Fee category definitions", "id (BigInt)", "name, code, is_refundable, priority", "school_id -> schools.id", "Catalog of charges (Tuition, Library, etc.)", "Labels charge and defines allocation priority")
        ],
        lifecycle="<strong>Year-Scoped Fact:</strong> <code>fee_invoices.enrolment_id</code> attaches strictly to the student's annual enrollment. If an invoice is generated erroneously, the accounting rule dictates that it must be voided and re-issued rather than deleted, keeping the invoice sequence gapless.",
        example="Student Aarav Sharma (enrolment_id 101) is billed for April 2026. System generates invoice <code>INV-2026-0101</code> for ₹4,000 comprising two lines: Tuition Fee (₹3,500) and Computer Fee (₹500). Status is set to <code>unpaid</code>."
    )

    # --- 6.4 Fee Counter Collection & FIFO Allocation ---
    content += render_workflow(
        wf_id="6.4",
        title="Counter Fee Collection, Oldest-First FIFO Line Allocation & Receipt Generation",
        overview={
            "real_life": "A parent visits the school fee counter to pay school fees in cash, card, UPI, or cheque.",
            "actor": "Fee Collector / Cashier / Accountant.",
            "trigger": "Parent presents payment at the counter; cashier searches student on <code>/fees/ledger</code>.",
            "problem": "Accurately applying lump-sum payments to multiple overdue invoice lines, generating official receipts, and tracking partial payments.",
            "outcome": "New <code>fee_payments</code> row created; funds allocated oldest-first via <code>payment_allocations</code>; printable PDF receipt issued."
        },
        steps=[
            "<strong>User Action:</strong> Cashier inputs student admission number, payment amount (e.g. ₹5,000), payment mode ('UPI'), and reference number.",
            "<strong>Frontend Processing:</strong> <code>FeeCollectModal.tsx</code> submits <code>POST /api/v1/fees/payments</code>.",
            "<strong>Backend Validation:</strong> <code>app/services/fees.py</code> validates amount &gt; 0, confirms period is open, and checks payment mode.",
            "<strong>Payment Record Insertion:</strong> Inserts parent row into <code>fee_payments</code> with unique voucher number (e.g. <code>RCT-2026-0089</code>).",
            "<strong>FIFO Line Allocation Algorithm:</strong> Queries all unpaid or partially paid <code>fee_invoice_lines</code> for this enrollment, ordered by invoice date ASC and line priority ASC.",
            "<strong>Payment Allocation Insertions:</strong> Iteratively allocates payment amount across lines, inserting rows into <code>payment_allocations</code> until funds are exhausted.",
            "<strong>Invoice Status Update:</strong> Checks remaining unpaid balance across all lines of each invoice. Marks invoice <code>paid</code> if fully settled, or <code>partial</code>.",
            "<strong>Receipt PDF Generation:</strong> <code>app/pdf/receipt.py</code> compiles an A4 two-copy official receipt (School Copy + Parent Copy) with unique verification code.",
            "<strong>Final Output:</strong> Instant PDF receipt delivered to screen and thermal printer; student ledger balance reduced immediately."
        ],
        diagram="""[Fee Cashier Counter Screen]
       │
       ▼ (POST /api/v1/fees/payments)
[Fee Payment & Allocation Engine (app/services/fees.py)]
       │
       ├─► [INSERT] fee_payments ────────────► Create receipt voucher (RCT-2026-0089, ₹5,000)
       │         │
       │         ▼ (payment.id)
       ├─► [READ] fee_invoice_lines ─────────► Query unpaid lines ordered by due date (FIFO)
       │         │
       │         ▼
       ├─► [INSERT] payment_allocations ─────► Allocate ₹3,500 to April Tuition, ₹1,500 to May Tuition
       │         │
       │         ▼
       ├─► [UPDATE] fee_invoices ────────────► Update status: April='paid', May='partial'
       │
       └─► [EXECUTE] app/pdf/receipt.py ─────► Stream official two-copy signed receipt PDF
       │
       ▼
[Parent Handed Receipt; Outstanding Balance Updated]""",
        transfers=[
            ("1", "Cashier Form", "Fee API", "enrolment_id, amount=5000, mode='UPI'", "INSERT", "Submit collected fee amount"),
            ("2", "Payment Service", "fee_payments table", "enrolment_id, payment_no, amount, mode", "INSERT", "Create permanent financial receipt voucher"),
            ("3", "FIFO Allocator", "payment_allocations table", "payment_id, invoice_line_id, amount", "ALLOCATE", "Link payment dollars to specific charge lines"),
            ("4", "FIFO Allocator", "fee_invoices table", "status='paid' | 'partial'", "UPDATE", "Reflect updated settlement status")
        ],
        tables=[
            ("fee_payments", "Fee collection voucher", "id (BigInt)", "payment_no, enrolment_id, amount, payment_mode, transaction_ref", "enrolment_id -> enrolments.id", "Counter payment vouchers (170+ rows)", "Primary immutable financial receipt"),
            ("payment_allocations", "Payment-to-line allocation", "id (BigInt)", "payment_id, invoice_line_id, amount", "payment_id -> fee_payments.id, invoice_line_id -> fee_invoice_lines.id", "M:N payment allocations (450+ rows)", "The ledger binding payments to charges"),
            ("fee_invoice_lines", "Invoiced fee components", "id (BigInt)", "invoice_id, amount, fee_head_id", "invoice_id -> fee_invoices.id", "Line-item charges", "Target entity satisfied by allocations")
        ],
        lifecycle="<strong>Financial Invariant: A Balance is Always a SUM.</strong> Sunrise ERP never stores an <code>outstanding_balance</code> column on the student! Outstanding balance is calculated dynamically on demand: <code>SUM(invoice_lines.amount) - SUM(payment_allocations.amount)</code>. This guarantees mathematical precision and prevents balance drift.",
        example="Parent pays ₹5,000 for Aarav Sharma. April invoice had ₹4,000 due; May invoice had ₹4,000 due. System allocates ₹4,000 to April lines (marking April 'paid') and ₹1,000 to May Tuition (marking May 'partial' with ₹3,000 remaining)."
    )

    # --- 6.5 Contra Payment Reversals ---
    content += render_workflow(
        wf_id="6.5",
        title="Audited Contra Payment Reversals & Anti-Fraud Ledger Rollback",
        overview={
            "real_life": "A cheque bounces, a bank card payment fails settlement, or a cashier made an erroneous duplicate entry.",
            "actor": "Senior Bursar / Head of Accounts with <code>fees.payment.reverse</code> permission.",
            "trigger": "Accountant clicks 'Reverse Payment' on a voucher in <code>/fees/ledger</code>.",
            "problem": "Reversing an erroneous payment without deleting records or breaking financial audit trails.",
            "outcome": "A contra payment record is created with negative amount; allocations are reversed; original invoice lines become overdue again; audited with mandatory reason."
        },
        steps=[
            "<strong>User Action:</strong> Accountant inputs mandatory cancellation reason (e.g. 'Cheque #40291 bounced due to insufficient funds').",
            "<strong>Frontend Processing:</strong> <code>StudentLedger.tsx</code> calls <code>POST /api/v1/fees/payments/{id}/reverse</code>.",
            "<strong>Backend Validation:</strong> Verifies user has reversal authority; ensures original payment was not already reversed.",
            "<strong>Contra Payment Insertion:</strong> Inserts a new row in <code>fee_payments</code> with <code>amount = -original.amount</code> and <code>reverses_payment_id = original.id</code>.",
            "<strong>Allocation Rollback:</strong> Inserts corresponding negative rows into <code>payment_allocations</code>, freeing up the invoice lines.",
            "<strong>Invoice Status Reset:</strong> Re-evaluates invoice lines; restores affected invoices from <code>paid</code> back to <code>unpaid</code> or <code>overdue</code>.",
            "<strong>Audit Log Commitment:</strong> Inserts mandatory record into <code>audit_log</code> capturing user, timestamp, and typed reason.",
            "<strong>Final Output:</strong> Ledger balance restored to debit; bounced payment indelibly recorded in bank reconciliation history."
        ],
        diagram="""[Senior Accountant / Bursar]
       │
       ▼ (POST /fees/payments/{id}/reverse with typed reason)
[Contra Reversal Service (app/services/fees.py)]
       │
       ├─► [READ] fee_payments ────────────► Validate original voucher (RCT-2026-0089)
       │
       ├─► [INSERT] fee_payments ──────────► Insert Contra voucher (amount = -5000, reverses_id=89)
       │         │
       │         ▼
       ├─► [INSERT] payment_allocations ───► Insert negative allocations (-3500, -1500)
       │         │
       │         ▼
       ├─► [UPDATE] fee_invoices ──────────► Reopen invoices: status reset to 'unpaid' / 'overdue'
       │
       └─► [INSERT] audit_log ─────────────► Commit immutable audit entry with typed explanation
       │
       ▼
[Financial History Preserved Intact; Defaulter Alarm Reactivated]""",
        transfers=[
            ("1", "Accountant Modal", "Reversal API", "payment_id, reversal_reason", "INSERT", "Request authorized payment reversal"),
            ("2", "Reversal Service", "fee_payments table", "reverses_payment_id, negative amount", "INSERT", "Create immutable contra accounting entry"),
            ("3", "Reversal Service", "payment_allocations", "negative allocation amounts", "ALLOCATE", "Roll back line item settlement"),
            ("4", "Reversal Service", "fee_invoices table", "status='unpaid'", "UPDATE", "Re-open unpaid invoice balances"),
            ("5", "Reversal Service", "audit_log table", "user_id, action='REVERSE', reason", "INSERT", "Log permanent audit trail record")
        ],
        tables=[
            ("fee_payments", "Fee vouchers", "id (BigInt)", "amount, reverses_payment_id, receipt_no", "reverses_payment_id -> fee_payments.id", "Payment and contra records", "Stores both original payment and contra reversal row"),
            ("payment_allocations", "Line allocations", "id (BigInt)", "payment_id, invoice_line_id, amount", "payment_id -> fee_payments.id", "Allocation links", "Negates prior allocations via negative offsets"),
            ("audit_log", "System audit trail", "id (BigInt)", "user_id, action, table_name, record_id, reason", "user_id -> users.id", "Audit log records (288+ rows)", "Stores who reversed the payment and why")
        ],
        lifecycle="<strong>Immutability Rule: Money is NEVER Deleted.</strong> The original payment row is untouched. The reverse row explicitly points to it. This design withstands statutory audits and criminal investigations.",
        example="Voucher <code>RCT-2026-0089</code> for ₹5,000 is reversed due to cheque dishonor. System creates <code>RCT-2026-0095</code> with amount -₹5,000 pointing to <code>RCT-2026-0089</code>. April and May invoices revert to unpaid status; ₹5,000 shows as overdue."
    )

    # --- 7.2 Marks Entry Grid & Audited Paper Locking ---
    content += render_workflow(
        wf_id="7.2",
        title="Examination Marks Entry Grid, CBSE Grading & Audited Paper Locking",
        overview={
            "real_life": "Subject teachers enter examination marks for their class papers, verify totals, and lock the paper against further tampering.",
            "actor": "Subject Teacher (entry) and Examination Controller (locking/unlocking).",
            "trigger": "Exam evaluation completion on <code>/exams</code> Marks Entry Grid.",
            "problem": "Preventing unauthorized grade modifications after submission while providing an auditable mechanism for administrative corrections.",
            "outcome": "Individual student marks inserted/updated; letter grades auto-computed; paper locked with audit reason required to reopen."
        },
        steps=[
            "<strong>User Action:</strong> Teacher enters scores out of 100 for each student in Class 10-A Mathematics; clicks 'Save Marks'.",
            "<strong>Frontend Processing:</strong> <code>MarksEntryGrid.tsx</code> validates scores &lt;= max_marks; dispatches <code>POST /api/v1/exams/marks/batch</code>.",
            "<strong>Backend Paper Lock Check:</strong> Service checks <code>exam_schedule.is_locked</code>. If locked, rejects write with HTTP 403 unless caller is Exam Controller.",
            "<strong>Marks Insertion & Upsert:</strong> Upserts records into <code>marks</code> table on composite key <code>(exam_id, subject_id, student_id)</code>.",
            "<strong>CBSE Grading Scale Resolution:</strong> Evaluates marks against <code>grade_bands</code> table to compute CBSE letter grade (A1, A2, B1, etc.) and grade point.",
            "<strong>Paper Locking Action:</strong> Exam Controller clicks 'Lock Paper'; backend sets <code>exam_schedule.is_locked = True</code> and commits timestamp.",
            "<strong>Audited Unlock Workflow:</strong> If a mark must be corrected post-lock, Controller must enter a mandatory audit explanation which commits to <code>audit_log</code>.",
            "<strong>Final Output:</strong> Verified marks committed; tamper-proof grades locked for report card generation."
        ],
        diagram="""[Subject Teacher Screen]
       │
       ▼ (POST /exams/marks/batch)
[Marks Evaluation Engine (api/admin/exams.py)]
       │
       ├─► [READ] exam_schedule ───────► Check is_locked flag (Must be False)
       │
       ├─► [INSERT / UPDATE] marks ────► Upsert marks awarded (e.g. 88/100)
       │         │
       │         ▼
       ├─► [READ] grade_bands ─────────► Resolve CBSE 8-Point Scale: 88% -> 'A2' (Point: 9.0)
       │
       ▼ (Exam Controller Lock Action)
[Lock Paper Service]
       │
       ├─► [UPDATE] exam_schedule ─────► Set is_locked = True, locked_at = NOW()
       │
       └─► [INSERT] audit_log ─────────► Log lock event (or audited unlock reason)
       │
       ▼
[Marks Secured Against Alteration]""",
        transfers=[
            ("1", "Teacher Grid Form", "Exams API", "exam_id, subject_id, list of (student_id, marks_obtained)", "INSERT", "Submit evaluated paper marks"),
            ("2", "Marks Service", "marks table", "exam_id, subject_id, student_id, marks_obtained, grade", "INSERT", "Commit scores to official grade register"),
            ("3", "Grading Engine", "grade_bands table", "percentage score", "READ", "Translate raw marks into CBSE letter grades"),
            ("4", "Lock Service", "exam_schedule table", "is_locked=True, locked_at", "UPDATE", "Impose cryptographic write freeze on paper")
        ],
        tables=[
            ("marks", "Student exam marks register", "id (BigInt)", "exam_id, subject_id, student_id, marks_obtained, grade_point", "exam_id -> exams.id, student_id -> students.id", "Official student exam scores (2,400+ rows)", "Stores the raw score and computed grade"),
            ("exam_schedule", "Class paper timetable & lock", "id (BigInt)", "exam_id, class_section_id, subject_id, max_marks, is_locked", "exam_id -> exams.id, subject_id -> subjects.id", "Datesheet and lock state (240 rows)", "Governs whether paper is open for editing"),
            ("grade_bands", "Grading scale brackets", "id (BigInt)", "grading_scale_id, min_percentage, max_percentage, grade, grade_point", "grading_scale_id -> grading_scales.id", "CBSE grade definition (A1: 91-100, etc.)", "Supplies letter grade and grade points")
        ],
        lifecycle="<strong>Foreign Key Nuance:</strong> Notice that <code>marks.student_id</code> references <code>students.id</code> directly, while the exam itself references <code>academic_year_id</code>. Once locked, <code>exam_schedule.is_locked</code> cannot be set back to <code>False</code> without an auditable reason recorded in <code>audit_log</code>.",
        example="Teacher enters 92/100 in Class 10 Mathematics for Aarav Sharma. System maps 92% to grade 'A1' (grade point 10.0) via <code>grade_bands</code>. Exam Controller locks the paper; subsequent write attempts are blocked with 403 Forbidden."
    )

    # --- 8.2 Academic Session Rollover Execution ---
    content += render_workflow(
        wf_id="8.2",
        title="Academic Session Rollover & Annual Class Progression Execution",
        overview={
            "real_life": "At the conclusion of the academic year in March, the school transitions all eligible students into the next grade for the new academic year.",
            "actor": "School Principal / Registrar with <code>students.enrolment.promote</code> permission.",
            "trigger": "Execution of the 4-step wizard at <code>/admin/session-rollover</code> with typed audit confirmation 'PROMOTE'.",
            "problem": "Promoting hundreds of students to the next class without overwriting historical academic, fee, and attendance records.",
            "outcome": "New <code>enrolments</code> rows created for the upcoming year; old <code>enrolments</code> marked <code>promoted</code>; permanent <code>students</code> records unchanged."
        },
        steps=[
            "<strong>User Action:</strong> Principal selects Source Year (2025-26) and Target Year (2026-27), reviews student roster, adjusts detained students, types 'PROMOTE', and clicks 'Execute Rollover'.",
            "<strong>Frontend Processing:</strong> <code>SessionRollover.tsx</code> validates typed confirmation string and dispatches <code>POST /api/v1/admin/promotion/execute</code>.",
            "<strong>Backend Transaction Initiation:</strong> <code>services/promotion.py</code> begins a single isolated database transaction.",
            "<strong>Target Year Verification:</strong> Confirms target academic year exists and is marked <code>active</code> in <code>academic_years</code>.",
            "<strong>Historical Enrolment Transition:</strong> Queries current active <code>enrolments</code> for the source year; updates their status to <code>promoted</code> (or <code>detained</code>).",
            "<strong>New Enrolment Creation:</strong> For each promoted student, determines next class section (e.g. 5-A -> 6-A); generates dynamic roll number; inserts new row into <code>enrolments</code> for the target year with status <code>active</code>.",
            "<strong>Graduating Cohort Handling:</strong> Students completing final grade (Class 12) have old enrollment marked <code>graduated</code> and student status updated to <code>alumni</code> without creating a new enrollment.",
            "<strong>Fee Structure Attachment:</strong> Optionally links new enrolments to the target year's class fee plans in <code>student_fee_plans</code>.",
            "<strong>Audit Commitment:</strong> Records execution metrics (promoted count, detained count) and user signature in <code>audit_log</code>.",
            "<strong>Final Output:</strong> Complete school population successfully advanced; past year remains 100% auditable."
        ],
        diagram="""[Principal Rollover Wizard (/admin/session-rollover)]
       │
       ▼ (POST /admin/promotion/execute - Typed 'PROMOTE')
[Promotion Engine (app/services/promotion.py)]
       │
       ├─► [READ] academic_years ──────► Verify target year 2026-27 is active
       │
       ├─► [UPDATE] enrolments (Old) ──► Set status = 'promoted' (Preserves 2025-26 history)
       │         │
       │         ▼
       ├─► [INSERT] enrolments (New) ──► Insert 2026-27 row (New class_section_id, roll_no, status='active')
       │         │
       │         ▼ (enrolments.id)
       ├─► [INSERT] student_fee_plans ─► Attach 2026-27 class fee plan
       │
       └─► [INSERT] audit_log ─────────► Log rollover execution timestamp and operator
       │
       ▼
[School Successfully Transitioned to New Academic Session]""",
        transfers=[
            ("1", "Rollover Wizard", "Promotion API", "source_year_id, target_year_id, student_overrides, confirmation='PROMOTE'", "INSERT", "Initiate school-wide cohort progression"),
            ("2", "Promotion Service", "enrolments table (Old)", "status='promoted', left_on=date", "UPDATE", "Close prior year academic membership"),
            ("3", "Promotion Service", "enrolments table (New)", "student_id, target_year_id, next_section_id, roll_no, status='active'", "INSERT", "Establish upcoming year academic membership"),
            ("4", "Promotion Service", "audit_log table", "action='SESSION_ROLLOVER', count, reason", "INSERT", "Audit major institutional transition")
        ],
        tables=[
            ("enrolments", "Class enrollment membership", "id (BigInt)", "student_id, academic_year_id, class_section_id, roll_no, status", "student_id -> students.id, year_id -> academic_years.id", "Year-by-year pupil enrollment (100 rows)", "Old row set to 'promoted'; new row inserted as 'active'"),
            ("students", "Lifetime student master", "id (BigInt)", "admission_no, user_id, status", "user_id -> users.id", "Permanent student identities", "Remains COMPLETELY UNTOUCHED during promotion"),
            ("academic_years", "School academic sessions", "id (BigInt)", "name, start_date, end_date, is_current", "school_id -> schools.id", "Year master records", "Identifies source and destination year contexts")
        ],
        lifecycle="<strong>The Fundamental Splitting Invariant:</strong> Why does Sunrise ERP split <code>students</code> and <code>enrolments</code>? In legacy ERPs, class was stored on <code>students</code>; promoting a student overwrote their class, causing old attendance, marks, and invoices to silently re-parent to the new class! In Sunrise ERP, promotion *creates* new rows in <code>enrolments</code> and marks the old ones <code>promoted</code>. History is never destroyed.",
        example="Student Aarav Sharma was in Class 5-A (<code>enrolments.id = 42</code>) in 2025-26. During rollover, <code>enrolments.id = 42</code> status is updated to <code>promoted</code>. A new row <code>enrolments.id = 142</code> is inserted for Class 6-A in 2026-27 with roll number 14. Aarav's <code>students.id = 12</code> and <code>admission_no = 'ADM-2024-001'</code> remain identical."
    )

    return content
