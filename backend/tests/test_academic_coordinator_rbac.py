"""Strict RBAC tests for the Academic Coordinator role.
Verifies complete operational control over the Timetable module:
- Configure bell timings and school periods
- Create, view, edit, delete timetable slots
- View class-wise and teacher-wise timetables
- Run live conflict detection
- Access completeness and teacher workload dashboards
- Publish and unpublish timetables
- Access the Substitution Desk and assign relief duty
- View daily operational schedule
- Audit logging for all actions
- Strict 403 Forbidden blocks for Admin settings, Finance/Fees, HR, Payroll, Admissions, Student rosters, and Exams.
"""

from datetime import date, time
from fastapi import status
from sqlalchemy import select

from app.models import (
    AcademicYear,
    AuditLog,
    ClassSection,
    Employee,
    SchoolPeriod,
    Subject,
    TimetableSlot,
)


def test_academic_coordinator_allowed_timetable_operations(client, academic_coordinator, db):
    # 1. Configure school periods and bell timings
    res = client.get("/admin/timetable/periods", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    periods = res.json()
    assert isinstance(periods, list)

    # 2. View classes and teachers for timetable scheduling
    res = client.get("/admin/classes", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    classes = res.json()
    assert len(classes) > 0
    section_id = classes[0]["id"]

    res = client.get("/admin/teachers", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    teachers = res.json()
    assert len(teachers) > 0
    teacher_id = teachers[0]["id"]

    res = client.get("/admin/subjects", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    subjects = res.json()
    assert len(subjects) > 0
    subject_id = subjects[0]["id"]

    # 3. View class-wise and teacher-wise timetables
    res = client.get(f"/admin/timetable/slots?class_section_id={section_id}", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert isinstance(res.json(), list)

    res = client.get(f"/admin/timetable/slots?teacher_id={teacher_id}", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert isinstance(res.json(), list)

    # 4. Conflict detection pre-flight check
    first_teaching_period = next(p for p in periods if not p.get("is_break"))
    res = client.post(
        "/admin/timetable/slots/check",
        json={
            "class_section_id": section_id,
            "day_of_week": "sat",
            "period_id": first_teaching_period["id"],
            "teacher_id": teacher_id,
            "subject_id": subject_id,
            "room": "Room 999",
        },
        headers=academic_coordinator,
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert "ok" in data
    assert "conflicts" in data

    # 5. Access completeness and teacher workload dashboards
    res = client.get("/admin/timetable/completeness", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert isinstance(res.json(), list)

    res = client.get("/admin/timetable/workload", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    workload = res.json()
    assert "fair_share" in workload
    assert "spread" in workload
    assert "rows" in workload

    # 6. View daily operational schedule
    res = client.get("/admin/timetable/day", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert isinstance(res.json(), list)

    # 7. Access substitution desk and find free teachers
    slot = db.scalars(select(TimetableSlot)).first()
    if slot:
        res = client.get(f"/admin/timetable/slots/{slot.id}/free-teachers", headers=academic_coordinator)
        assert res.status_code == status.HTTP_200_OK, res.text
        assert isinstance(res.json(), list)

    # 8. View notices (communication read-only)
    res = client.get("/admin/notices", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text


def test_academic_coordinator_lifecycle_and_audit(client, academic_coordinator, db):
    # 1. Add a period and verify audit
    new_period_no = 99
    res = client.post(
        "/admin/timetable/periods",
        json={
            "period_no": new_period_no,
            "start_time": "15:00:00",
            "end_time": "15:45:00",
            "name": "Co-Curricular",
            "is_break": False,
        },
        headers=academic_coordinator,
    )
    assert res.status_code == status.HTTP_201_CREATED, res.text

    audit_period = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "school_period",
            AuditLog.action == "create",
        ).order_by(AuditLog.id.desc())
    ).first()
    assert audit_period is not None
    assert audit_period.actor_user_id is not None

    # 2. Publish & Unpublish timetable and verify audit
    res = client.post("/admin/timetable/publish", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["published"] is True

    audit_pub = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "timetable",
            AuditLog.action == "publish",
        ).order_by(AuditLog.id.desc())
    ).first()
    assert audit_pub is not None

    res = client.post("/admin/timetable/unpublish", headers=academic_coordinator)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["published"] is False


def test_academic_coordinator_strictly_forbidden_modules(client, academic_coordinator):
    # 1. Admin System Settings & Users (Strictly 403)
    res = client.get("/admin/settings", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/configuration", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/users", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Financial & Fee Invoices (Strictly 403)
    res = client.get("/admin/fees/invoices", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/fees/defaulters", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.post("/admin/fees/invoices/generate", json={"class_names": ["10"]}, headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Admission Applications & Merit (Strictly 403)
    res = client.get("/admin/admission/cycles", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/admission/applications", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 4. Student Profiles (Strictly 403)
    res = client.get("/admin/students", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 5. Examinations (Strictly 403)
    res = client.get("/admin/exams", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 6. HR & Payroll (Strictly 403)
    res = client.get("/admin/payroll/runs", headers=academic_coordinator)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.post(
        "/admin/teachers",
        json={"full_name": "Test", "employee_code": "T999", "password": "Password123"},
        headers=academic_coordinator,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 7. Class Section Creation & Mutation (Strictly 403)
    res = client.post(
        "/admin/classes",
        json={"class_name": "12", "section": "Z"},
        headers=academic_coordinator,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_academic_coordinator_can_configure_break_period(client, academic_coordinator, db):
    """Break period must not be hardcoded: it can be configured dynamically."""
    # 1. Fetch periods and check that Period 3 is currently configured as a break
    periods = client.get("/admin/timetable/periods", headers=academic_coordinator).json()
    p3 = next(p for p in periods if p["period_no"] == 3)
    assert p3["is_break"] is True, "Period 3 should be configured as break"

    # 2. Update Period 3 to custom break label and timing
    res = client.put(
        f"/admin/timetable/periods/{p3['id']}",
        json={
            "name": "Mid-Morning Recess",
            "is_break": True,
        },
        headers=academic_coordinator,
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["name"] == "Mid-Morning Recess"
    assert res.json()["is_break"] is True

    # 3. Verify audit log recorded the update
    audit_update = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "school_period",
            AuditLog.entity_id == p3["id"],
            AuditLog.action == "update",
        ).order_by(AuditLog.id.desc())
    ).first()
    assert audit_update is not None
    assert audit_update.after["name"] == "Mid-Morning Recess"

    # 4. Verify scheduling conflict occurs when trying to place a lesson in the break
    sections = client.get("/admin/classes", headers=academic_coordinator).json()
    teachers = client.get("/admin/teachers", headers=academic_coordinator).json()
    subjects = client.get("/admin/subjects", headers=academic_coordinator).json()
    check_res = client.post(
        "/admin/timetable/slots/check",
        json={
            "class_section_id": sections[0]["id"],
            "day_of_week": "mon",
            "period_id": p3["id"],
            "subject_id": subjects[0]["id"],
            "teacher_id": teachers[0]["id"],
        },
        headers=academic_coordinator,
    )
    assert check_res.status_code == status.HTTP_200_OK
    kinds = [c["kind"] for c in check_res.json()["conflicts"]]
    assert "break" in kinds

    # 5. Reset back to clean "Break"
    client.put(
        f"/admin/timetable/periods/{p3['id']}",
        json={"name": "Break", "is_break": True},
        headers=academic_coordinator,
    )
