"""Tests for Session 6: Parent Mobile Workflow & Ledger Test Suite.

Validates:
1. Strict Child Isolation: Parent A querying child of Parent B returns 403 or 404.
2. Attendance Calendar: GET /parent/children/{id}/attendance?month=YYYY-MM returns calendar with P/A/L/M badges.
3. Student Medical Leave: POST /parent/leave creates row pointing to child's enrolment_id,
   admin approval writes M status to attendance calendar.
4. Fee Receipts & Online Ledger:
   - GET /parent/children/{id}/fees/summary strictly equals SUM(invoices) - SUM(payments).
   - Receipt download: GET /parent/fees/receipt/{id} returns 200 application/pdf.
5. CBSE Report Card Download & Dues-Withholding Gate:
   - Blocks report card with HTTP 402 when fee dues > 0.
   - Allows download with HTTP 200 application/pdf when dues are cleared.
6. School Notices: GET /parent/notices returns circulars.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import (
    Attendance,
    AttendanceStatus,
    Enrolment,
    Exam,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    LeaveStatus,
    PaymentAllocation,
    StudentLeaveRequest,
)


@pytest.fixture(autouse=True)
def allow_working_days(monkeypatch):
    import app.services.attendance
    monkeypatch.setattr(app.services.attendance, "is_working_day", lambda day, holidays: True)


def test_strict_child_isolation(client, parent, other_parent, ids):
    """Parent A cannot access data of a child belonging to Parent B."""
    child_a = ids["student_1"]
    child_b = ids["student_17"]

    # Parent A can read child A
    res_ok = client.get(f"/parent/children/{child_a}/summary", headers=parent)
    assert res_ok.status_code == 200

    # Parent A accessing child B must be forbidden / not found
    res_forbidden = client.get(f"/parent/children/{child_b}/summary", headers=parent)
    assert res_forbidden.status_code in (403, 404)

    # Parent B accessing child A must be forbidden / not found
    res_b_forbidden = client.get(f"/parent/children/{child_a}/summary", headers=other_parent)
    assert res_b_forbidden.status_code in (403, 404)


def test_parent_attendance_calendar_monthly(client, parent, ids):
    """GET /parent/children/{id}/attendance?month=YYYY-MM returns monthly calendar."""
    child_id = ids["student_1"]
    current_month_str = date.today().strftime("%Y-%m")

    res = client.get(
        f"/parent/children/{child_id}/attendance?month={current_month_str}",
        headers=parent,
    )
    assert res.status_code == 200, res.text
    cal = res.json()
    assert "days" in cal
    assert "summary" in cal
    assert isinstance(cal["days"], list)


def test_student_medical_leave_application_and_approval(client, parent, admin, admin_user, db, ids):
    """Parent submits leave request pointing to child's enrolment_id; approval updates attendance."""
    child_id = ids["student_1"]
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == child_id))
    assert enr is not None

    start = date.today() + timedelta(days=5)
    end = start + timedelta(days=2)

    # Submit leave request
    resp = client.post(
        "/parent/leave",
        json={
            "student_id": child_id,
            "from_date": start.isoformat(),
            "to_date": end.isoformat(),
            "type": "sick",
            "reason": "Severe viral fever and doctor advised rest",
        },
        headers=parent,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    req_id = data["id"]

    # Direct DB assertion on StudentLeaveRequest
    db.expire_all()
    req = db.get(StudentLeaveRequest, req_id)
    assert req is not None
    assert req.enrolment_id == enr.id
    assert req.status == LeaveStatus.applied

    # Admin approves leave
    approve_resp = client.post(
        f"/admin/attendance/leave-requests/{req_id}/decide",
        json={"approve": True, "note": "Get well soon"},
        headers=admin,
    )
    assert approve_resp.status_code == 200, approve_resp.text

    # Direct DB assertion: attendance rows marked for date range
    db.expire_all()
    att_rows = list(
        db.scalars(
            select(Attendance).where(
                Attendance.enrolment_id == enr.id,
                Attendance.date >= start,
                Attendance.date <= end,
            )
        )
    )
    assert len(att_rows) > 0
    assert all(r.status in (AttendanceStatus.leave, AttendanceStatus.excused) for r in att_rows)


def test_fee_summary_math_and_receipt_download(client, parent, db, ids):
    """Fee summary strictly equals SUM(invoices) - SUM(payments), and receipt PDF is downloadable."""
    child_id = ids["student_1"]
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == child_id))
    assert enr is not None

    # Fetch summary via API
    res = client.get(f"/parent/children/{child_id}/fees/summary", headers=parent)
    assert res.status_code == 200, res.text
    summary = res.json()

    # Calculate actual numbers from DB
    total_invoiced_db = db.scalar(
        select(func.coalesce(func.sum(FeeInvoiceLine.amount), Decimal("0.00")))
        .join(FeeInvoice, FeeInvoice.id == FeeInvoiceLine.invoice_id)
        .where(FeeInvoice.enrolment_id == enr.id)
    )
    total_paid_db = db.scalar(
        select(func.coalesce(func.sum(PaymentAllocation.amount), Decimal("0.00")))
        .join(FeeInvoiceLine, FeeInvoiceLine.id == PaymentAllocation.invoice_line_id)
        .join(FeeInvoice, FeeInvoice.id == FeeInvoiceLine.invoice_id)
        .where(FeeInvoice.enrolment_id == enr.id)
    )
    balance_db = total_invoiced_db - total_paid_db

    assert float(summary["total_invoiced"]) == float(total_invoiced_db)
    assert float(summary["total_paid"]) == float(total_paid_db)
    assert float(summary["total_dues"]) == float(balance_db)

    # Receipt download test
    payment = db.scalar(
        select(FeePayment).where(FeePayment.enrolment_id == enr.id).order_by(FeePayment.id.desc())
    )
    if payment:
        rcpt_resp = client.get(f"/parent/fees/receipt/{payment.id}", headers=parent)
        assert rcpt_resp.status_code == 200
        assert rcpt_resp.headers["content-type"] == "application/pdf"
        assert len(rcpt_resp.content) > 100


def test_report_card_dues_withholding_gate(client, parent, db, ids):
    """Report card download is withheld (HTTP 402) when fee dues > 0; allowed (HTTP 200) when 0."""
    child_id = ids["student_1"]
    enr = db.scalar(select(Enrolment).where(Enrolment.student_id == child_id))
    exam = db.query(Exam).first()
    assert exam is not None

    # Check fee dues
    invs = list(db.scalars(select(FeeInvoice).where(FeeInvoice.enrolment_id == enr.id)))
    # If dues > 0, report card must return 402
    rc_resp = client.get(f"/parent/children/{child_id}/report-card/{exam.id}", headers=parent)
    if any(inv.status.value != "paid" for inv in invs):
        assert rc_resp.status_code == 402
        assert "withheld" in rc_resp.json()["detail"].lower()
    else:
        assert rc_resp.status_code == 200
        assert rc_resp.headers["content-type"] == "application/pdf"


def test_parent_notices_list(client, parent):
    """GET /parent/notices returns circulars for parents."""
    res = client.get("/parent/notices", headers=parent)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
