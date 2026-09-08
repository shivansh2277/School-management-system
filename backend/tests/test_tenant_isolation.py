"""A second school must be invisible to the first.

Every table carries `school_id` (CLAUDE.md), but carrying the column is not the
same as filtering on it. These tests plant a rival school's rows and assert the
demo school's admin cannot see them — the check that turns the tenant key from
a convention into a boundary.
"""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import (
    AcademicYear,
    AcademicYearStatus,
    Exam,
    School,
    Student,
    Subject,
    User,
    UserRole,
)
from app.services import grading, scoping
from app.services.common import grade_for


@pytest.fixture()
def rival(db):
    """A second, entirely separate customer with its own year and rows."""
    school = School(code="RIVAL", name="Rival Academy", board="CBSE")
    db.add(school)
    db.flush()
    year = AcademicYear(
        school_id=school.id,
        code="2026-27",
        start_date="2026-04-01",
        end_date="2027-03-31",
        status=AcademicYearStatus.active,
        is_current=True,
    )
    db.add(year)
    db.flush()
    db.add_all(
        [
            Subject(school_id=school.id, name="Rival Sanskrit", code="RSAN"),
            Exam(
                school_id=school.id,
                name="Rival Half Yearly",
                term="Term 1",
                start_date="2026-09-01",
                end_date="2026-09-10",
            ),
        ]
    )
    # A scale so lax that 1% is an A1 — if it leaks, the demo school's grades
    # change.
    grading.create(
        db,
        school.id,
        name="Lax",
        bands=[(Decimal("1"), "A1", None), (Decimal(0), "E", None)],
        activate=True,
    )
    db.flush()
    return school


def test_the_exam_list_shows_only_this_schools_exams(client, admin, rival, db):
    names = [e["name"] for e in client.get("/admin/exams", headers=admin).json()]
    assert "Rival Half Yearly" not in names


def test_the_subject_list_shows_only_this_schools_subjects(client, admin, rival):
    r = client.get("/admin/subjects", headers=admin)
    assert r.status_code == 200, r.text
    assert "Rival Sanskrit" not in [s["name"] for s in r.json()]


def test_a_grade_is_computed_from_this_schools_scale_only(db, rival, ids):
    """35% is a D on the demo school's scale. It must not become an A1 because
    another customer defined a band at 1%."""
    assert grade_for(db, ids["school"], 35) == "D"


@pytest.fixture()
def rival_student(db, rival):
    """One child on the rival school's roll, with nothing linking them here."""
    u = User(
        school_id=rival.id,
        role=UserRole.student,
        login_id="RIVAL0001",
        password_hash="x",
        full_name="Rival Child",
    )
    db.add(u)
    db.flush()
    s = Student(school_id=rival.id, user_id=u.id, admission_no="9999000001")
    db.add(s)
    db.flush()
    return s


def test_the_student_roster_shows_only_this_schools_children(
    client, admin, rival_student
):
    """The roster query carried `school_id` on the table and never filtered on
    it - the section 4 defect, on the largest table of personal data here."""
    r = client.get("/admin/students", headers=admin, params={"page_size": 200})
    assert r.status_code == 200, r.text
    assert "Rival Child" not in [i["full_name"] for i in r.json()["items"]]


def test_another_schools_student_cannot_be_opened_by_id(client, admin, rival_student):
    r = client.get(f"/admin/students/{rival_student.id}", headers=admin)
    assert r.status_code == 404, r.text


def test_another_schools_student_cannot_be_edited(client, admin, rival_student):
    """The worse half: the roster leaked reads, this one accepted writes."""
    r = client.patch(
        f"/admin/students/{rival_student.id}",
        headers=admin,
        json={"full_name": "Renamed By A Stranger"},
    )
    assert r.status_code == 404, r.text


def test_the_scoping_gate_refuses_another_schools_student(
    db, admin_user, rival_student
):
    """`assert_can_read_student` is the chokepoint thirteen routes call, and
    its admin branch returned the row without ever looking at the tenant."""
    with pytest.raises(HTTPException) as excinfo:
        scoping.assert_can_read_student(db, admin_user, rival_student.id)
    assert excinfo.value.status_code == 404
