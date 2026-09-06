"""Enrolment invariants — the point of splitting students from enrolments.

v0 stored `class_section_id` and `roll_no` on `students`, so promoting a class
overwrote them and last year became unanswerable. These tests fail against that
design and pass against this one.
"""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AcademicYear,
    AcademicYearStatus,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    Student,
    User,
)
from app.services.common import current_enrolment, roster


def next_year(db, school_id=1):
    year = AcademicYear(
        school_id=school_id,
        code="2026-27",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.planning,
        is_current=False,
    )
    db.add(year)
    db.flush()
    return year


def test_promotion_preserves_last_years_enrolment(db, ids):
    """The behaviour v0 could not express: after promotion, last year's roster
    is still exactly what it was."""
    old_section = ids["section_10a"]
    before = [(e.student_id, e.roll_no) for e in roster(db, old_section)]
    assert before, "fixture should have a populated section"

    year = next_year(db)
    new_section = ClassSection(
        school_id=1, academic_year_id=year.id, class_name="11", section="A"
    )
    db.add(new_section)
    db.flush()

    for e in roster(db, old_section):
        e.status = EnrolmentStatus.promoted
        db.add(
            Enrolment(
                school_id=1,
                student_id=e.student_id,
                academic_year_id=year.id,
                class_section_id=new_section.id,
                roll_no=e.roll_no,
            )
        )
    db.flush()

    # Last year's rows are untouched — same students, same roll numbers.
    historical = db.scalars(
        select(Enrolment)
        .where(Enrolment.class_section_id == old_section)
        .order_by(Enrolment.roll_no)
    ).all()
    assert [(e.student_id, e.roll_no) for e in historical] == before
    assert all(e.status is EnrolmentStatus.promoted for e in historical)

    # And this year's section holds the same children.
    assert {e.student_id for e in roster(db, new_section.id)} == {
        sid for sid, _ in before
    }


def test_a_student_cannot_be_enrolled_twice_in_one_year(db, ids):
    """The invariant that keeps "which class is this child in" answerable."""
    existing = roster(db, ids["section_10a"])[0]
    db.add(
        Enrolment(
            school_id=1,
            student_id=existing.student_id,
            academic_year_id=existing.academic_year_id,
            class_section_id=ids["section_9a"],
            roll_no=99,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_roll_numbers_are_unique_within_a_section(db, ids):
    taken = roster(db, ids["section_10a"])[0]
    student = db.scalars(select(Student)).all()[-1]
    db.add(
        Enrolment(
            school_id=1,
            student_id=student.id,
            academic_year_id=taken.academic_year_id,
            class_section_id=taken.class_section_id,
            roll_no=taken.roll_no,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_roster_excludes_a_deactivated_student(db, ids):
    """The recorded v0 defect: `roster()` promised "Active students" in its
    docstring while the query had no such filter, so a deactivated student kept
    appearing on attendance sheets and marks rosters."""
    before = roster(db, ids["section_10a"])
    victim = before[0]

    user = db.get(User, db.get(Student, victim.student_id).user_id)
    user.is_active = False
    db.flush()

    after = roster(db, ids["section_10a"])
    assert victim.student_id not in {e.student_id for e in after}
    assert len(after) == len(before) - 1


def test_roster_excludes_a_non_active_enrolment(db, ids):
    before = roster(db, ids["section_10a"])
    left = before[0]
    left.status = EnrolmentStatus.transferred_out
    left.left_on = date(2026, 8, 1)
    db.flush()

    after = roster(db, ids["section_10a"])
    assert left.student_id not in {e.student_id for e in after}


def test_current_enrolment_follows_the_current_year(db, ids):
    """A student with two enrolments resolves to the one in the current year,
    not to whichever row was written last."""
    e = roster(db, ids["section_10a"])[0]
    year = next_year(db)
    section = ClassSection(
        school_id=1, academic_year_id=year.id, class_name="11", section="A"
    )
    db.add(section)
    db.flush()
    db.add(
        Enrolment(
            school_id=1,
            student_id=e.student_id,
            academic_year_id=year.id,
            class_section_id=section.id,
            roll_no=1,
        )
    )
    db.flush()

    # 2026-27 exists but is not current, so the answer is still this year's.
    assert current_enrolment(db, e.student_id).class_section_id == ids["section_10a"]


def test_the_student_record_carries_no_class(db):
    """Guards the split itself: if these ever come back onto `students`, the
    history model is broken again."""
    assert not hasattr(Student, "class_section_id")
    assert not hasattr(Student, "roll_no")
