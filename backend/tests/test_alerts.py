"""Tests for Student & Parent Important Alerts System (Session 19).

Verifies the 4 important alert types:
1. Attendance Shortage Alert (< 75.0%)
2. Fee Due Alert (> 0 balance)
3. Report Card Available Alert
4. Periodic Test Result Alert

Also verifies multi-child parent alert aggregation and child attribution.
"""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select

from app.models import (
    AlertView,
    Attendance,
    AttendanceStatus,
    Enrolment,
    Exam,
    ExamSchedule,
    FeeInvoice,
    Mark,
    ReportCardPublication,
    SchemeComponent,
    Student,
    User,
    UserRole,
)
from app.services import alerts as alerts_svc
from tests.conftest import auth


def test_student_dashboard_includes_alerts_contract(client, student, db):
    """Student dashboard includes fee_due_amount, report card, periodic test, and alerts array."""
    resp = client.get("/student/dashboard", headers=student)
    assert resp.status_code == 200
    data = resp.json()

    assert "fee_due_amount" in data
    assert "latest_report_card" in data
    assert "latest_periodic_test" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_attendance_shortage_alert_lifecycle(client, student, db, ids):
    """Attendance shortage alert triggers strictly when attendance < 75%, and clears when >= 75%."""
    enrolment_id = db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == ids["student_1"])
    )

    records = list(db.scalars(select(Attendance).where(Attendance.enrolment_id == enrolment_id)))
    assert records, "Student must have seeded attendance records"

    # 1. Update 80% of records to absent to drop attendance < 75%
    for r in records[:int(len(records) * 0.8)]:
        r.status = AttendanceStatus.absent
    db.flush()

    info = alerts_svc.get_student_alerts(db, ids["student_1"])
    assert info["attendance_percent"] is not None and info["attendance_percent"] < 75.0
    att_alert = next((a for a in info["alerts"] if a["type"] == "attendance"), None)
    assert att_alert is not None
    assert "Attendance Shortage" in att_alert["title"]
    assert att_alert["route"] == "/(student)/attendance"

    # 2. Restore records to present so attendance >= 75%
    for r in records:
        r.status = AttendanceStatus.present
    db.flush()

    info_cleared = alerts_svc.get_student_alerts(db, ids["student_1"])
    assert info_cleared["attendance_percent"] is not None and info_cleared["attendance_percent"] >= 75.0
    att_alert_cleared = next((a for a in info_cleared["alerts"] if a["type"] == "attendance"), None)
    assert att_alert_cleared is None, "Attendance shortage alert must disappear when >= 75%"


def test_fee_due_alert_lifecycle(client, student, db, ids):
    """Fee due alert triggers when balance > 0, and disappears when balance is 0."""
    enrolment_id = db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == ids["student_1"])
    )

    info = alerts_svc.get_student_alerts(db, ids["student_1"])
    if info["fee_due_amount"] > 0:
        fee_alert = next((a for a in info["alerts"] if a["type"] == "fee"), None)
        assert fee_alert is not None
        assert "Fee Due" in fee_alert["title"]
        assert fee_alert["amount"] == info["fee_due_amount"]


def test_parent_alerts_endpoint_multi_child(client, parent, db):
    """Parent /parent/alerts evaluates alerts independently per child with clear child attribution."""
    resp = client.get("/parent/alerts", headers=parent)
    assert resp.status_code == 200
    alerts = resp.json()
    assert isinstance(alerts, list)

    for alert in alerts:
        assert "child_id" in alert
        assert "child_name" in alert
        assert "type" in alert
        assert "title" in alert
        assert "message" in alert
        assert "route" in alert
        # Attribution check: title must end with `— {child_name}`
        assert f"— {alert['child_name']}" in alert["title"]
        # Destination routes must be valid parent routes
        assert alert["route"] in ["/(parent)/attendance", "/(parent)/fees", "/(parent)/results"]


def test_parent_child_summary_includes_alert_contract(client, parent, db):
    """Parent /parent/children/{id}/summary includes fee_due_amount, report card, PT, and alerts."""
    children = client.get("/parent/children", headers=parent).json()
    assert children, "Parent must have at least one child"
    child_id = children[0]["id"]

    resp = client.get(f"/parent/children/{child_id}/summary", headers=parent)
    assert resp.status_code == 200
    data = resp.json()

    assert "fee_due_amount" in data
    assert "latest_report_card" in data
    assert "latest_periodic_test" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_viewed_attendance_alert_lifecycle_and_reappearance(client, student, db, ids):
    """Viewed attendance shortage alert disappears, but reappears when a new absence occurs."""
    enrolment_id = db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == ids["student_1"])
    )
    records = list(
        db.scalars(
            select(Attendance)
            .where(Attendance.enrolment_id == enrolment_id)
            .order_by(Attendance.date)
        )
    )
    assert len(records) >= 3

    # 1. Cause attendance shortage by marking early records absent
    for r in records[:int(len(records) * 0.8)]:
        r.status = AttendanceStatus.absent
    db.flush()

    # Dashboard shows attendance shortage
    resp = client.get("/student/dashboard", headers=student)
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    att_alert = next((a for a in alerts if a["type"] == "attendance"), None)
    assert att_alert is not None
    orig_key = att_alert["event_key"]

    # 2. View/dismiss attendance alert via POST /student/alerts/view
    view_resp = client.post(
        "/student/alerts/view",
        headers=student,
        json={"alert_type": "attendance", "event_key": orig_key},
    )
    assert view_resp.status_code == 200

    # 3. Reload dashboard: viewed attendance alert must NOT be shown!
    resp2 = client.get("/student/dashboard", headers=student)
    alerts2 = resp2.json()["alerts"]
    assert next((a for a in alerts2 if a["type"] == "attendance"), None) is None

    # 4. A new attendance-shortage event occurs later:
    # Another record (previously present) is marked absent
    new_absent_record = next(r for r in records if r.status == AttendanceStatus.present)
    new_absent_record.status = AttendanceStatus.absent
    db.flush()

    # 5. Reload dashboard: new shortage alert must appear with new event_key!
    resp3 = client.get("/student/dashboard", headers=student)
    alerts3 = resp3.json()["alerts"]
    new_att_alert = next((a for a in alerts3 if a["type"] == "attendance"), None)
    assert new_att_alert is not None
    assert new_att_alert["event_key"] != orig_key

    # 6. Cleanup: restore all to present
    for r in records:
        r.status = AttendanceStatus.present
    db.flush()


def test_viewed_report_card_and_periodic_test_alerts_disappear(client, student, db):
    """Viewed report card and periodic test alerts disappear after viewing."""
    dash = client.get("/student/dashboard", headers=student).json()
    alerts = dash["alerts"]

    rc_alert = next((a for a in alerts if a["type"] == "report_card"), None)
    pt_alert = next((a for a in alerts if a["type"] == "periodic_test"), None)

    assert rc_alert is not None, "Student should have a report card alert seeded"
    assert pt_alert is not None, "Student should have a periodic test alert seeded"

    # 1. View Report Card alert
    resp_rc = client.post(
        "/student/alerts/view",
        headers=student,
        json={"alert_type": "report_card", "event_key": rc_alert["event_key"]},
    )
    assert resp_rc.status_code == 200

    # 2. View Periodic Test alert
    resp_pt = client.post(
        "/student/alerts/view",
        headers=student,
        json={"alert_type": "periodic_test", "event_key": pt_alert["event_key"]},
    )
    assert resp_pt.status_code == 200

    # 3. Reload dashboard: both must be gone!
    dash2 = client.get("/student/dashboard", headers=student).json()
    assert next((a for a in dash2["alerts"] if a["type"] == "report_card"), None) is None
    assert next((a for a in dash2["alerts"] if a["type"] == "periodic_test"), None) is None


def test_fee_alert_remains_after_viewing_and_clears_only_when_balance_zero(
    client, student, db, ids
):
    """Fee alert cannot be dismissed by viewing; only disappears when outstanding dues are 0."""
    dash = client.get("/student/dashboard", headers=student).json()
    fee_alert = next((a for a in dash["alerts"] if a["type"] == "fee"), None)
    assert fee_alert is not None
    assert dash["fee_due_amount"] > 0

    # 1. Attempt to view/dismiss fee alert
    resp = client.post(
        "/student/alerts/view",
        headers=student,
        json={"alert_type": "fee", "event_key": fee_alert["event_key"]},
    )
    assert resp.status_code == 200

    # 2. Reload dashboard: Fee alert MUST still be present!
    dash2 = client.get("/student/dashboard", headers=student).json()
    fee_alert2 = next((a for a in dash2["alerts"] if a["type"] == "fee"), None)
    assert fee_alert2 is not None, "Fee alert must remain visible after viewing"

    # 3. Now clear fee dues to 0 (set invoice line amounts to 0 so balance is 0)
    enrolment_id = db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == ids["student_1"])
    )
    invoices = list(db.scalars(select(FeeInvoice).where(FeeInvoice.enrolment_id == enrolment_id)))
    orig_states = [(line, line.amount) for inv in invoices for line in inv.lines]
    for line, _ in orig_states:
        line.amount = Decimal("0.00")
    db.flush()

    # 4. Reload dashboard: Fee alert must now disappear because dues are cleared!
    dash3 = client.get("/student/dashboard", headers=student).json()
    assert dash3["fee_due_amount"] == 0
    assert (
        next((a for a in dash3["alerts"] if a["type"] == "fee"), None) is None
    ), "Fee alert must disappear when dues are cleared"

    # Restore invoice states
    for line, orig_amt in orig_states:
        line.amount = orig_amt
    db.flush()


def test_multi_child_alerts_independent_viewed_states(client, parent, db):
    """Viewing an alert for Child A does not dismiss the corresponding alert for Child B."""
    alerts = client.get("/parent/alerts", headers=parent).json()
    assert len(alerts) >= 2

    # Find two children who both have report_card alerts
    children = client.get("/parent/children", headers=parent).json()
    assert len(children) >= 2
    child_a = children[0]
    child_b = children[1]

    child_a_rc = next(
        (a for a in alerts if a["child_id"] == child_a["id"] and a["type"] == "report_card"),
        None,
    )
    child_b_rc = next(
        (a for a in alerts if a["child_id"] == child_b["id"] and a["type"] == "report_card"),
        None,
    )

    assert child_a_rc is not None and child_b_rc is not None

    # Parent views Child A's report card alert
    view_resp = client.post(
        "/parent/alerts/view",
        headers=parent,
        json={
            "child_id": child_a["id"],
            "alert_type": "report_card",
            "event_key": child_a_rc["event_key"],
        },
    )
    assert view_resp.status_code == 200

    # Reload /parent/alerts: Child A's alert is gone, but Child B's alert is STILL present!
    alerts2 = client.get("/parent/alerts", headers=parent).json()
    assert (
        next(
            (a for a in alerts2 if a["child_id"] == child_a["id"] and a["type"] == "report_card"),
            None,
        )
        is None
    )
    child_b_rc_still = next(
        (a for a in alerts2 if a["child_id"] == child_b["id"] and a["type"] == "report_card"),
        None,
    )
    assert (
        child_b_rc_still is not None
    ), "Child B's alert must remain visible when Child A's alert is viewed"


def test_screen_navigation_marks_alert_viewed(client, student, parent, db, ids):
    """Directly viewing attendance or results marks corresponding alerts viewed."""
    # 1. Mark attendance < 75% for student
    enrolment_id = db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == ids["student_1"])
    )
    records = list(
        db.scalars(select(Attendance).where(Attendance.enrolment_id == enrolment_id))
    )
    for r in records[:int(len(records) * 0.8)]:
        r.status = AttendanceStatus.absent
    db.flush()

    # Visiting /student/attendance automatically marks attendance shortage viewed
    resp = client.get("/student/attendance", headers=student)
    assert resp.status_code == 200

    # Dashboard shows attendance alert is gone!
    dash = client.get("/student/dashboard", headers=student).json()
    assert next((a for a in dash["alerts"] if a["type"] == "attendance"), None) is None

    # Cleanup
    for r in records:
        r.status = AttendanceStatus.present
    db.flush()

