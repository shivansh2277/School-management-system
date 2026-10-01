from datetime import date, timedelta
import pytest
from app.models import ClassSection, Holiday, HolidayClassSection, Student, User
from sqlalchemy import select


def test_holiday_management_crud_and_scoping(client, admin, db):
    """Admin can create single/multi-day, school-wide or section-scoped holidays and cancel with reason."""
    sec = db.scalar(select(ClassSection).where(ClassSection.school_id == 1))
    assert sec is not None

    # 1. Create section-scoped 2-day holiday
    h_start = date(2026, 10, 15)
    h_end = date(2026, 10, 16)
    create_res = client.post(
        "/admin/attendance/holidays",
        headers=admin,
        json={
            "name": "Class Sports Meet",
            "start_date": str(h_start),
            "end_date": str(h_end),
            "is_school_wide": False,
            "description": "Annual sports meet for primary",
            "class_section_ids": [sec.id],
        },
    )
    assert create_res.status_code == 201
    h_data = create_res.json()
    h_id = h_data["id"]
    assert h_data["is_school_wide"] is False
    assert sec.id in h_data["class_section_ids"]

    # 2. List holidays includes new holiday
    list_res = client.get("/admin/attendance/holidays", headers=admin)
    assert list_res.status_code == 200
    holidays = list_res.json()
    assert any(h["id"] == h_id for h in holidays)

    # 3. Cancel holiday requires reason
    fail_cancel = client.delete(f"/admin/attendance/holidays/{h_id}", headers=admin)
    assert fail_cancel.status_code == 422  # query param reason required

    cancel_res = client.delete(
        f"/admin/attendance/holidays/{h_id}?reason=Sports+meet+postponed+due+to+rain",
        headers=admin,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"


def test_attendance_marking_blocked_on_holiday_unless_override(client, admin, teacher, db):
    """Attendance marking on holiday is blocked by default; requires attendance.holiday.override + reason."""
    from datetime import date
    from app.models import ClassSection, Employee, Role, RolePermission, User
    t_user = db.scalar(select(User).where(User.login_id == "TCH001"))
    t_emp = db.scalar(select(Employee).where(Employee.user_id == t_user.id))
    sec = db.scalar(select(ClassSection).where(ClassSection.class_teacher_id == t_emp.id))
    assert sec is not None

    # Use today's date for attendance marking test
    h_date = date.today()
    h_res = client.post(
        "/admin/attendance/holidays",
        headers=admin,
        json={
            "name": "State Formation Day",
            "start_date": str(h_date),
            "end_date": str(h_date),
            "is_school_wide": True,
            "description": "Gazetted holiday",
        },
    )
    assert h_res.status_code == 201

    # Fetch students in section
    roster_res = client.get(f"/teacher/attendance?class_section_id={sec.id}&date={h_date}", headers=teacher)
    assert roster_res.status_code == 200
    roster_data = roster_res.json()
    assert len(roster_data) > 0
    entries = [{"student_id": r["student_id"], "status": "present"} for r in roster_data]

    # Attempt 1: Teacher tries to mark attendance on holiday -> 400 Bad Request
    mark_fail = client.post(
        "/teacher/attendance",
        headers=teacher,
        json={
            "class_section_id": sec.id,
            "date": str(h_date),
            "entries": entries,
        },
    )
    assert mark_fail.status_code == 400
    assert "holiday" in mark_fail.text.lower()

    # Attempt 2: Teacher tries to mark with override reason, but lacks permission -> 400 Bad Request
    mark_no_perm = client.post(
        "/teacher/attendance",
        headers=teacher,
        json={
            "class_section_id": sec.id,
            "date": str(h_date),
            "entries": entries,
            "holiday_override_reason": "Special rehearsal without authorization",
        },
    )
    assert mark_no_perm.status_code == 400

    # Attempt 3: Grant attendance.holiday.override to teacher's role and provide reason -> succeeds!
    from app.models import Permission
    perm = db.scalar(select(Permission).where(Permission.code == "attendance.holiday.override"))
    teacher_role = db.scalar(select(Role).where(Role.school_id == 1, Role.code == "teacher"))
    if teacher_role and perm:
        db.add(RolePermission(school_id=1, role_id=teacher_role.id, permission_id=perm.id))
        db.commit()

    override_res = client.post(
        "/teacher/attendance",
        headers=teacher,
        json={
            "class_section_id": sec.id,
            "date": str(h_date),
            "entries": entries,
            "holiday_override_reason": "Special rehearsal session approved by Principal",
        },
    )
    assert override_res.status_code == 200
    assert len(override_res.json()) == len(entries)
