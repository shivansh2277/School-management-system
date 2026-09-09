"""Multi-tenancy and academic-year invariants.

These are the checks that would have caught the v0 assumptions this commit
removes: that a login is globally unique, that a school has exactly one
implicit session, and that a dashboard count means "everyone in the database".
"""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models import (
    AcademicYear,
    AcademicYearStatus,
    ClassSection,
    Enrolment,
    School,
    SchoolStatus,
    Student,
    User,
    UserRole,
)


def make_school(db, code="OTHER", name="Other Public School"):
    school = School(code=code, name=name, status=SchoolStatus.active, city="Lucknow")
    db.add(school)
    db.flush()
    year = AcademicYear(
        school_id=school.id,
        code="2025-26",
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        status=AcademicYearStatus.active,
        is_current=True,
    )
    db.add(year)
    db.flush()
    return school, year


def test_two_schools_may_reuse_the_same_login_id(db):
    """The v0 schema made `login_id` globally unique, so the second school to
    create an "admin" would collide with the first."""
    school, _ = make_school(db)
    existing = db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))
    assert existing is not None

    db.add(
        User(
            school_id=school.id,
            role=UserRole.admin,
            login_id="admin@sunrisepublic.edu",
            password_hash=hash_password("Admin@123"),
            full_name="Other Office",
        )
    )
    db.flush()  # no IntegrityError: uniqueness is (school_id, login_id)


def test_two_schools_may_issue_the_same_admission_number(db):
    school, year = make_school(db)
    section = ClassSection(
        school_id=school.id, academic_year_id=year.id, class_name="10", section="A"
    )
    db.add(section)
    db.flush()
    user = User(
        school_id=school.id,
        role=UserRole.student,
        login_id="SPS2024001",
        password_hash=hash_password("x"),
        full_name="Someone Else",
    )
    db.add(user)
    db.flush()
    student = Student(
        school_id=school.id,
        user_id=user.id,
        admission_no="SPS2024001",  # already used by the seeded school
    )
    db.add(student)
    db.flush()
    db.add(
        Enrolment(
            school_id=school.id,
            student_id=student.id,
            academic_year_id=year.id,
            class_section_id=section.id,
            roll_no=1,
        )
    )
    db.flush()


def test_a_school_cannot_have_two_current_years(db):
    """Enforced by a partial unique index, not by application code that a new
    code path could forget."""
    school, _ = make_school(db)
    db.add(
        AcademicYear(
            school_id=school.id,
            code="2026-27",
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            status=AcademicYearStatus.planning,
            is_current=True,  # a second current year for the same school
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_a_second_school_may_have_its_own_current_year(db):
    """The constraint is per school, not global — several schools are each in
    their own current session at the same time."""
    school, _ = make_school(db)
    current = db.scalars(
        select(AcademicYear).where(AcademicYear.is_current.is_(True))
    ).all()
    assert {y.school_id for y in current} == {1, school.id}


def test_dashboard_totals_ignore_another_schools_students(client, admin, db):
    """The count must mean "this school", not "every row in the table"."""
    before = client.get("/admin/dashboard/stats", headers=admin).json()["totals"]

    school, year = make_school(db)
    section = ClassSection(
        school_id=school.id, academic_year_id=year.id, class_name="10", section="A"
    )
    db.add(section)
    db.flush()
    for i in range(3):
        u = User(
            school_id=school.id,
            role=UserRole.student,
            login_id=f"OTHER{i}",
            password_hash=hash_password("x"),
            full_name=f"Other Student {i}",
        )
        db.add(u)
        db.flush()
        st = Student(
            school_id=school.id, user_id=u.id, admission_no=f"OTHER{i}"
        )
        db.add(st)
        db.flush()
        db.add(
            Enrolment(
                school_id=school.id,
                student_id=st.id,
                academic_year_id=year.id,
                class_section_id=section.id,
                roll_no=i + 1,
            )
        )
    db.flush()

    after = client.get("/admin/dashboard/stats", headers=admin).json()["totals"]
    assert after["students"] == before["students"]
    assert after["classes"] == before["classes"]


def test_login_refuses_to_guess_between_schools(client, db):
    """Two schools share a login id, so the request is ambiguous without a
    school_code. Guessing one would be an authentication bug."""
    school, _ = make_school(db)
    db.add(
        User(
            school_id=school.id,
            role=UserRole.admin,
            login_id="admin@sunrisepublic.edu",
            password_hash=hash_password("Admin@123"),
            full_name="Other Office",
        )
    )
    db.flush()

    r = client.post(
        "/auth/login",
        json={
            "role": "admin",
            "login_id": "admin@sunrisepublic.edu",
            "password": "Admin@123",
        },
    )
    assert r.status_code == 409

    r = client.post(
        "/auth/login",
        json={
            "role": "admin",
            "login_id": "admin@sunrisepublic.edu",
            "password": "Admin@123",
            "school_code": "OTHER",
        },
    )
    assert r.status_code == 200


def test_a_suspended_school_cannot_log_in(client, db):
    school, _ = make_school(db, code="SUSP", name="Suspended School")
    school.status = SchoolStatus.suspended
    db.add(
        User(
            school_id=school.id,
            role=UserRole.admin,
            login_id="head@suspended.edu",
            password_hash=hash_password("Admin@123"),
            full_name="Head",
        )
    )
    db.flush()

    r = client.post(
        "/auth/login",
        json={
            "role": "admin",
            "login_id": "head@suspended.edu",
            "password": "Admin@123",
            "school_code": "SUSP",
        },
    )
    assert r.status_code == 403
