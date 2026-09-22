from datetime import date
import pytest
from sqlalchemy import select

from app.models import AuditAction, AuditLog, ClassSection, ClassSubjectTeacher, Employee, School, StockItem, User


@pytest.fixture(autouse=True)
def allow_marking_today(monkeypatch):
    import app.services.attendance
    monkeypatch.setattr(app.services.attendance, "is_working_day", lambda day, holidays: True)


def test_teacher_consume_stock_success(client, teacher, db):
    """Teachers can consume stock items for classroom/lab use, updating quantity and audit log."""
    item = db.scalar(select(StockItem).where(StockItem.current_quantity > 5))
    assert item is not None
    initial_qty = item.current_quantity

    res = client.post(
        f"/teacher/stock/{item.id}/consume",
        headers=teacher,
        json={"quantity": 3, "reason": "Class 10-A chemistry lab experiment"},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["current_quantity"] == initial_qty - 3

    # Verify audit log entry
    db.expire_all()
    audit_entry = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "stock_item",
            AuditLog.entity_id == item.id,
            AuditLog.action == AuditAction.update,
        )
        .order_by(AuditLog.occurred_at.desc())
    )
    assert audit_entry is not None
    assert audit_entry.after["consumed"] == 3
    assert audit_entry.after["current_quantity"] == initial_qty - 3
    assert "Class 10-A chemistry lab" in audit_entry.reason


def test_teacher_consume_stock_validation_errors(client, teacher, db):
    """Consuming 0 or more than available quantity yields HTTP 400 Bad Request."""
    item = db.scalar(select(StockItem).where(StockItem.current_quantity > 0))
    assert item is not None

    # Test 0 quantity
    res_zero = client.post(
        f"/teacher/stock/{item.id}/consume",
        headers=teacher,
        json={"quantity": 0, "reason": "Invalid zero test"},
    )
    assert res_zero.status_code == 422  # Pydantic gt=0 triggers 422 or 400

    # Test over-consumption
    excessive_qty = item.current_quantity + 50
    res_excess = client.post(
        f"/teacher/stock/{item.id}/consume",
        headers=teacher,
        json={"quantity": excessive_qty, "reason": "Over consumption attempt"},
    )
    assert res_excess.status_code == 400
    assert "Cannot consume" in res_excess.json()["detail"]


def test_teacher_consume_stock_triggers_low_stock_status(client, teacher, db):
    """Consuming stock until current_quantity <= min_quantity triggers is_low_stock flag."""
    item = db.scalar(select(StockItem).where(StockItem.current_quantity > StockItem.min_quantity))
    assert item is not None

    consume_amount = item.current_quantity - item.min_quantity + 1
    assert consume_amount > 0

    res = client.post(
        f"/teacher/stock/{item.id}/consume",
        headers=teacher,
        json={"quantity": consume_amount, "reason": "Depleting stock to low threshold"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_low_stock"] is True
    assert data["current_quantity"] <= data["min_quantity"]


def test_teacher_stock_consume_cross_tenant_rejected(client, teacher, db):
    """Teacher cannot consume stock belonging to a different school tenant."""
    other_school = School(name="Cross Tenant Academy", code="CTA")
    db.add(other_school)
    db.flush()

    other_item = StockItem(
        school_id=other_school.id,
        name="Foreign School Beaker",
        category="Science Lab",
        location="Lab Z",
        unit="pieces",
        current_quantity=10,
        min_quantity=2,
    )
    db.add(other_item)
    db.commit()

    res = client.post(
        f"/teacher/stock/{other_item.id}/consume",
        headers=teacher,
        json={"quantity": 1, "reason": "Cross-tenant intrusion attempt"},
    )
    assert res.status_code == 404


def test_class_teacher_attendance_authorization(client, teacher, other_teacher, ids, db):
    """Only the designated Class Teacher may view roll sheet and mark attendance.
    Subject teachers who merely teach a subject are rejected with HTTP 403 Forbidden.
    """
    section_id = ids["section_10a"]
    today_str = date.today().isoformat()

    # 1. Designated class teacher (TCH001) successfully views roll sheet
    res_roll = client.get(
        f"/teacher/attendance?class_section_id={section_id}&date={today_str}",
        headers=teacher,
    )
    assert res_roll.status_code == 200
    roster = res_roll.json()
    assert len(roster) > 0

    # 2. Non-class teacher (other_teacher: TCH004) is rejected with 403 Forbidden on GET
    res_roll_forbidden = client.get(
        f"/teacher/attendance?class_section_id={section_id}&date={today_str}",
        headers=other_teacher,
    )
    assert res_roll_forbidden.status_code == 403
    assert "designated class teacher" in res_roll_forbidden.json()["detail"].lower()

    # 3. Test subject teacher scenario:
    # TCH001 teaches Mathematics in 9-A, but is NOT the class teacher of 9-A (TCH002 is).
    # When TCH001 attempts to view roll sheet or mark attendance for 9-A, verify 403 Forbidden.
    section_9a_id = ids["section_9a"]
    res_sub_get = client.get(
        f"/teacher/attendance?class_section_id={section_9a_id}&date={today_str}",
        headers=teacher,
    )
    assert res_sub_get.status_code == 403
    assert "designated class teacher" in res_sub_get.json()["detail"].lower()

    mark_body_9a = {
        "class_section_id": section_9a_id,
        "date": today_str,
        "entries": [],
    }
    res_sub_post = client.post(
        "/teacher/attendance",
        headers=teacher,
        json=mark_body_9a,
    )
    assert res_sub_post.status_code == 403
    assert "designated class teacher" in res_sub_post.json()["detail"].lower()

    # 4. Class teacher (TCH001) successfully marks attendance for their own section (10-A)
    mark_body_10a = {
        "class_section_id": section_id,
        "date": today_str,
        "entries": [{"student_id": r["student_id"], "status": "present"} for r in roster],
    }
    res_mark_ok = client.post(
        "/teacher/attendance",
        headers=teacher,
        json=mark_body_10a,
    )
    assert res_mark_ok.status_code == 200


def test_teacher_class_teacher_sections_endpoint(client, teacher, db):
    """GET /teacher/classes/class-teacher-sections filters exclusively to assigned class sections."""
    res = client.get("/teacher/classes/class-teacher-sections", headers=teacher)
    assert res.status_code == 200
    sections = res.json()
    assert len(sections) >= 1
    for s in sections:
        assert s["is_class_teacher"] is True


def test_student_homework_retrieval_and_submission(client, student, ids, db):
    """Student can list homework with status=all and submit assignments."""
    # List all homework
    res_all = client.get("/student/homework?status=all", headers=student)
    assert res_all.status_code == 200
    all_hw = res_all.json()
    assert len(all_hw) > 0

    hw_item = all_hw[0]
    # Submit homework
    res_submit = client.post(
        f"/student/homework/{hw_item['id']}/submit",
        headers=student,
        json={"answer_text": "Completed homework problems 1-10 with detailed derivations."},
    )
    assert res_submit.status_code == 200
    assert res_submit.json()["submitted"] is True

    # Check submitted list
    res_sub = client.get("/student/homework?status=submitted", headers=student)
    assert res_sub.status_code == 200
    submitted_ids = [h["id"] for h in res_sub.json()]
    assert hw_item["id"] in submitted_ids
