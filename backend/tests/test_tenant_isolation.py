"""A second school must be invisible to the first.

Every table carries `school_id` (CLAUDE.md), but carrying the column is not the
same as filtering on it. These tests plant a rival school's rows and assert the
demo school's admin cannot see them — the check that turns the tenant key from
a convention into a boundary.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    AcademicYear,
    AcademicYearStatus,
    Exam,
    School,
    Subject,
)
from app.services import grading
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
