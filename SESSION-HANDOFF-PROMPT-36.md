# SESSION 36 HANDOFF PROMPT — Sunrise School ERP

> **Instructions for User:** Copy and paste the prompt block below into the chat when starting the next session.

---

```markdown
# MANDATORY WORKFLOW RULE — READ THIS FIRST BEFORE ANYTHING ELSE

IMPORTANT:
First generate a comprehensive, detailed implementation plan and present it to me.
When I review it and give approval, then only proceed with making changes or modifying code.
Do NOT start writing code, creating migrations, or modifying files until I have explicitly approved your implementation plan.

---

# Sunrise School ERP — Critical Production Remediation & Operational Survivability (Phase 1 & Phase 2)

Act as a Senior Principal Full-Stack Engineer and School ERP Systems Architect.

Your task is to implement the Phase 1 and Phase 2 critical remediations identified in the Independent Second-Stage QA Audit (`report.pdf` / `SESSION-HANDOFF-35.md`) to resolve calculation divergences, financial leakage, test suite fragility, academic year rollover gaps, cheque dishonour handling, and mobile offline resilience.

## Workspace & Context
- Repository: `C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`
- Database: PostgreSQL on `localhost:5432/sunrise_test` (105 relational tables)
- Read these first before planning:
  1. `SESSION-HANDOFF-35.md` — Authoritative audit findings, verified remediations, and failure root causes.
  2. `SINGLE_SOURCE_OF_TRUTH.md` — Core domain architecture, schemas, and locked decisions.
  3. `CLAUDE.md` and `MEMORY.md` — Invariant rules (e.g. `enrolment_id` foreign keys, multi-tenant scoping, test database handling).

---

## 1. Fix BUG-EXAM-01: Examination Analytics & Report Card Score Divergence
- **Defect:** In `app/services/stats.py`, `exam_percentages()` filters `MarksEntry.is_absent == False`, excluding absent subjects from the maximum marks denominator and yielding 37.2% overall performance. Conversely, `app/services/report_cards.py` includes scheduled absent papers with 0 obtained marks in `total_max`, yielding 31.0%. The executive dashboard directly contradicts printed CBSE report cards.
- **Requirement:**
  - Align `stats.py` with `report_cards.py` so that scheduled papers where a child is marked absent contribute to the total scheduled maximum marks denominator with 0 marks obtained.
  - Ensure `test_the_dashboard_and_the_report_card_agree_about_an_absent_child` in `backend/tests/test_marks_lock.py` passes cleanly.

## 2. Fix BUG-CERT-01: Mandatory Fee Dues Clearance Gate for Transfer Certificates (TC)
- **Defect:** In `app/api/admin/certificates.py`, `issue_certificate()` generates official CBSE Transfer Certificates without verifying outstanding invoice balances. Students with unpaid fees can be issued TCs, forfeiting legal recovery leverage.
- **Requirement:**
  - Before issuing or printing a Transfer Certificate, calculate total outstanding dues (`sum(invoice.balance)` across active invoices for the student).
  - If outstanding balance > 0, refuse TC generation with HTTP 400/422 ("Outstanding fee dues pending: Rs. X. TC cannot be issued without full dues clearance or authorized Admin override").
  - Provide an authorized Admin override parameter (`dues_override_reason`) requiring Super Admin role and logging the exception in `audit_logs`.
  - Add comprehensive unit tests in `backend/tests/test_certificates.py` verifying both blocked generation with dues and authorized override paths.

## 3. Fix BUG-SEED-01 & Headcount Drift: Restore 100% Green CI/CD (845 Tests)
- **Defect:** 8 test suites failed due to test fixture/seed headcount drift (2 day scholars added to Section 10-A expanded headcount from 10 to 12 and school roll from 100 to 102), and 1 test assumed an outdated auto-enrollment payment behavior.
- **Requirement:**
  - `backend/tests/test_admission_dossier_demo.py`: Update test fixture to execute the full workflow and pay `admission_fee` (not just `application_fee`) to verify conversion.
  - `backend/tests/test_admission_reports.py`: Adjust funnel clean-slate assertion or seed scoping.
  - `backend/tests/test_app_endpoints.py`, `backend/tests/test_attendance_scope.py`, `backend/tests/test_exports.py`, `backend/tests/test_management_kpis.py`, and `backend/tests/test_stats.py`: Replace hardcoded literals (`assert 10`, `assert 100`, `assert 30.0`) with dynamic database count queries (e.g. `db.query(Enrolment).filter_by(class_section_id=...).count()`).
  - Run the complete backend test suite and verify **all 845 tests pass (0 failures, 100% green)**.

## 4. Academic Year Rollover & Promotion Data Integrity (`promotion.py`)
- **Defect:** `POST /admin/promotion/commit` promotes enrolments to the target academic year, but fails to create `StudentFeePlan` records, drops approved `FeeConcession` entries, and leaves `TransportAssignment` rows tied to old enrolment IDs. Promoted students cannot be billed on April 1st.
- **Requirement:**
  - In `app/services/promotion.py:commit()`, atomically:
    1. Identify active fee structure for the promoted class section in the target academic year.
    2. Automatically instantiate active `StudentFeePlan` records for all promoted students in the target year.
    3. Carry forward valid ongoing `FeeConcession` records to the new session.
    4. Re-link active `TransportAssignment` records to the promoted student's new `enrolment_id`.
  - Write dedicated unit tests in `backend/tests/test_session_rollover_integrity.py` asserting that promoted students have active fee plans, valid concessions, and transport assignments in the new academic year.

## 5. Cheque Bounce / Dishonour Reversal Workflow
- **Defect:** The Fees module lacks an operational action to reverse payment allocations and levy bank charges when a fee cheque is dishonoured.
- **Requirement:**
  - Implement endpoint `POST /admin/fees/payments/{payment_id}/dishonour`.
  - Atomically:
    1. Mark `Payment.status = "dishonoured"`.
    2. Reverse all `payment_allocations` against invoice lines, reopening the invoices and restoring `invoice.balance`.
    3. Generate a new invoice line or debit note for "Cheque Bounce Penalty Fee" (configurable bank charge, e.g. Rs. 500).
    4. Record the reversal and cheque bounce reason in `audit_logs`.
    5. Post appropriate reversing journal entries in `general_ledger` (Debit Accounts Receivable, Credit Bank; Debit Accounts Receivable, Credit Penalty Income).
  - Add unit test coverage in `backend/tests/test_fees_dishonour.py`.

## 6. Mobile App: Offline Roll-Call Queue with Auto-Sync on Reconnect
- **Defect:** Teachers marking attendance in basement classrooms or sports fields experience network timeouts and lost data on Wi-Fi drops.
- **Requirement:**
  - In `mobile/app/(teacher)/attendance.tsx`, implement a resilient offline queue using `AsyncStorage`.
  - When network is unreachable (or HTTP request times out), serialize the attendance payload into an offline mutation queue (`@offline_attendance_queue`) and show an optimistic status pill: "Saved Locally (Offline - Will Sync When Connected)".
  - Add a network status listener / reconnect trigger (`NetInfo` or ping check) that automatically drains the queue to `POST /teacher/classes/{id}/attendance` with idempotency key once connectivity is restored.
  - Verify that offline roll-call does not crash the app and syncs accurately upon reconnect.

---

## Verification & Execution Instructions
1. Run backend pytest suite: `..\.venv\Scripts\python.exe -m pytest -v` (expect all 845 tests passing).
2. Run defect verification suite: `..\.venv\Scripts\python.exe -m pytest tests/test_audit_defect_remediations.py`.
3. Run frontend TypeScript checks: `web: npx tsc -b`, `mobile: npx tsc --noEmit`.
4. Run web test suite: `web: npm run test:run`.
5. Ensure no existing RBAC permissions, multi-tenant boundaries, or working modules are broken.
```
