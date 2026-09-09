"""Every endpoint that takes an id must refuse another school's id.

`test_tenant_isolation.py` proves the *reads* that were fixed once already.
This file is the systematic version, and it exists because seven live
cross-tenant defects survived a 610-test suite: a rival school's staff list and
notice board were readable, and its employees, class sections, timetable slots
and notices were writable or deletable, by anyone who guessed a sequential
integer.

The rule being pinned, from CLAUDE.md: *"Every table carries `school_id`. A
missing tenant key is a data leak between customers, not a style problem."*
Carrying the column is not filtering on it, and `db.get(Model, id)` answers
"does this row exist anywhere in the product" rather than "may this customer
touch it".

Four properties, for every resource that matters:

  1. School A cannot READ School B's row by id.
  2. School A cannot MODIFY School B's row by id.
  3. School A cannot DELETE or disable School B's row by id.
  4. A list endpoint never returns School B's rows.

A refusal is 404 rather than 403 throughout, deliberately: which ids another
customer owns is not something to confirm. Tests therefore assert `!= 200`
where a route may legitimately 404, 405 or 409, and assert 404 exactly where
the route is reachable and the row exists.
"""

from datetime import date, time, timedelta

import pytest
from sqlalchemy import select

from app.models import (
    AcademicYear,
    ClassSection,
    DayOfWeek,
    Employee,
    Enrolment,
    Exam,
    ExamSchedule,
    Notice,
    SchoolPeriod,
    Student,
    Subject,
    TimetableSlot,
    User,
    UserRole,
)
from app.services import school_settings
from tests.test_tenant_isolation import rival  # noqa: F401


@pytest.fixture()
def modules_on(db, admin_user):
    """HR and transport default to off; these tests are about the tenant
    boundary, not about the module gate, and a 404 from the gate would look
    exactly like a 404 from the boundary and prove nothing."""
    school_settings.set_many(db, admin_user, {"feature.hr": True, "feature.transport": True})
    return True


@pytest.fixture()
def estate(db, rival):  # noqa: F811  (pytest fixture: imported, then named as a parameter)
    """A populated rival school: everything an admin of *our* school might
    reach by guessing an id. Returned as a dict of ids."""
    year = db.scalar(select(AcademicYear).where(AcademicYear.school_id == rival.id))

    section = ClassSection(
        school_id=rival.id, academic_year_id=year.id, class_name="12", section="Z"
    )
    db.add(section)
    db.flush()

    child_user = User(
        school_id=rival.id,
        role=UserRole.student,
        login_id="RIVALKID1",
        password_hash="x",
        full_name="Rival Child One",
    )
    db.add(child_user)
    db.flush()
    child = Student(school_id=rival.id, user_id=child_user.id, admission_no="9999000101")
    db.add(child)
    db.flush()
    enrolment = Enrolment(
        school_id=rival.id,
        student_id=child.id,
        class_section_id=section.id,
        academic_year_id=year.id,
        roll_no=1,
    )
    db.add(enrolment)

    staff_user = User(
        school_id=rival.id,
        role=UserRole.teacher,
        login_id="RIVALSTAFF1",
        password_hash="x",
        full_name="Rival Staff One",
        is_active=True,
    )
    db.add(staff_user)
    db.flush()
    employee = Employee(school_id=rival.id, user_id=staff_user.id, employee_code="RIVEMP01")
    db.add(employee)

    admin_user_row = User(
        school_id=rival.id,
        role=UserRole.admin,
        login_id="RIVALADMIN1",
        password_hash="x",
        full_name="Rival Admin One",
    )
    db.add(admin_user_row)
    db.flush()
    notice = Notice(
        school_id=rival.id,
        title="Rival confidential notice",
        body="Internal to the rival school only.",
        audience="all",
        published_by=admin_user_row.id,
        published_at=date.today(),
    )
    db.add(notice)

    exam = db.scalar(select(Exam).where(Exam.school_id == rival.id))
    subject = db.scalar(select(Subject).where(Subject.school_id == rival.id))
    period = SchoolPeriod(
        school_id=rival.id, period_no=1, start_time=time(8, 0), end_time=time(9, 0)
    )
    db.add(period)
    db.flush()

    schedule = ExamSchedule(
        school_id=rival.id,
        exam_id=exam.id,
        class_section_id=section.id,
        subject_id=subject.id,
        exam_date=date.today() + timedelta(days=7),
        max_marks=100,
    )
    db.add(schedule)

    slot = TimetableSlot(
        school_id=rival.id,
        class_section_id=section.id,
        day_of_week=DayOfWeek.mon,
        period_id=period.id,
        subject_id=subject.id,
        teacher_id=employee.id,
    )
    db.add(slot)
    db.flush()

    return {
        "school": rival.id,
        "section": section.id,
        "student": child.id,
        "enrolment": enrolment.id,
        "employee": employee.id,
        "staff_user": staff_user.id,
        "notice": notice.id,
        "exam": exam.id,
        "schedule": schedule.id,
        "slot": slot.id,
        "subject": subject.id,
        "period": period.id,
    }


# --- 1. reads by id ---------------------------------------------------------


def test_no_read_reaches_another_schools_row(client, admin, estate, modules_on):
    """Each of these returned another school's data before the fix.

    The four marked (fixed) were confirmed by execution against a planted
    rival school; the rest are the same shape and are pinned so the class
    cannot come back somewhere new.
    """
    reads = {
        "class roster": f"/admin/classes/{estate['section']}/students",  # fixed
        "attendance roll": (
            f"/admin/attendance?class_section_id={estate['section']}&date={date.today()}"
        ),  # fixed
        "timetable grid": f"/admin/timetable?class_section_id={estate['section']}",  # fixed
        "exam schedule": f"/admin/exams/{estate['exam']}/schedule",  # fixed
        "student profile": f"/admin/students/{estate['student']}",
        "employee profile": f"/admin/employees/{estate['employee']}",
    }
    for what, url in reads.items():
        r = client.get(url, headers=admin)
        assert r.status_code != 200, f"{what}: {url} returned another school's data"


# --- 2. writes by id --------------------------------------------------------


def test_no_write_reaches_another_schools_row(client, admin, estate, modules_on, db):
    """A write that lands on another customer's row corrupts their data, which
    is worse than reading it."""
    before_name = db.get(User, estate["staff_user"]).full_name

    cases = [
        (
            "employee",
            "patch",
            f"/admin/teachers/{estate['employee']}",
            {"full_name": "TAKEN OVER", "phone": "0000000000"},
        ),
        (
            "class section",
            "patch",
            f"/admin/classes/{estate['section']}",
            {"class_teacher_id": None},
        ),
        (
            "timetable slot",
            "put",
            f"/admin/timetable/slots/{estate['slot']}",
            {
                "class_section_id": estate["section"],
                "day_of_week": "mon",
                "period_id": estate["period"],
                "subject_id": estate["subject"],
                "teacher_id": estate["employee"],
            },
        ),
    ]
    for what, verb, url, payload in cases:
        r = getattr(client, verb)(url, json=payload, headers=admin)
        assert r.status_code != 200, f"{what}: {verb.upper()} {url} modified another school"

    db.expire_all()
    assert db.get(User, estate["staff_user"]).full_name == before_name, (
        "the rival employee's name was rewritten by another school"
    )


# --- 3. deletes and disables ------------------------------------------------


def test_no_delete_or_disable_reaches_another_schools_row(client, admin, estate, modules_on, db):
    """Deactivating another customer's staff is a cross-tenant denial of
    service: their people simply stop being able to log in."""
    deletes = [
        ("employee (deactivate)", f"/admin/teachers/{estate['employee']}"),
        ("notice", f"/admin/notices/{estate['notice']}"),
    ]
    for what, url in deletes:
        r = client.delete(url, headers=admin)
        assert r.status_code not in (200, 204), f"{what}: DELETE {url} succeeded"

    db.expire_all()
    assert db.get(User, estate["staff_user"]).is_active is True, (
        "the rival school's employee was disabled by another school"
    )
    assert db.get(Notice, estate["notice"]) is not None, (
        "the rival school's notice was deleted by another school"
    )


# --- 4. list endpoints ------------------------------------------------------


def test_no_list_endpoint_returns_another_schools_rows(client, admin, estate, modules_on):
    """The leak that needs no guessing at all: just open the screen."""
    checks = [
        ("/admin/teachers", "Rival Staff One", "full_name"),  # fixed
        ("/admin/employees", "Rival Staff One", "full_name"),
        ("/admin/notices", "Rival confidential notice", "title"),  # fixed
        ("/admin/students", "Rival Child One", "full_name"),
        ("/admin/classes", "12-Z", "label"),
        ("/admin/exams", "Rival Half Yearly", "name"),
        ("/admin/subjects", "Rival Sanskrit", "name"),
    ]
    for url, needle, field in checks:
        r = client.get(url, headers=admin)
        assert r.status_code == 200, f"{url} -> {r.status_code}"
        body = r.json()
        rows = body.get("items", body) if isinstance(body, dict) else body
        values = [str(row.get(field, "")) for row in rows if isinstance(row, dict)]
        assert needle not in values, f"{url} leaked the rival school's {field}: {needle}"


# --- the helper itself ------------------------------------------------------


def test_get_owned_refuses_a_row_from_another_school(db, admin_user, estate):
    """The boundary helper, tested directly rather than only through routes."""
    from fastapi import HTTPException

    from app.services import tenancy

    ours = tenancy.get_owned(
        db,
        ClassSection,
        db.scalar(
            select(ClassSection.id).where(ClassSection.school_id == admin_user.school_id)
        ),
        admin_user,
    )
    assert ours.school_id == admin_user.school_id

    with pytest.raises(HTTPException) as refused:
        tenancy.get_owned(db, ClassSection, estate["section"], admin_user)
    assert refused.value.status_code == 404

    # A missing row and someone else's row are the same answer on purpose.
    with pytest.raises(HTTPException) as missing:
        tenancy.get_owned(db, ClassSection, 10**9, admin_user)
    assert missing.value.status_code == 404
    assert missing.value.detail == refused.value.detail
