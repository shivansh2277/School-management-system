"""Year-end rollover — ERP_BLUEPRINT §7.4.

"If this workflow is easy, the architecture is right." These tests are what
that claim has to survive.
"""

from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import (
    AcademicYear,
    AcademicYearStatus,
    Attendance,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    StudentStatus,
)
from app.services import promotion
from app.services.common import roster


@pytest.fixture()
def next_year(db):
    year = AcademicYear(
        school_id=1,
        code="2026-27",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.planning,
    )
    db.add(year)
    db.flush()
    return year


def make_section(db, year, class_name, section="A"):
    cs = ClassSection(
        school_id=1, academic_year_id=year.id, class_name=class_name, section=section
    )
    db.add(cs)
    db.flush()
    return cs


def test_preview_changes_nothing(db, ids, next_year):
    make_section(db, next_year, "11")
    before = [(e.student_id, e.class_section_id, e.status) for e in roster(db, ids["section_10a"])]

    plan = promotion.preview(db, ids["section_10a"], next_year.id)

    assert plan.can_commit
    assert plan.from_section == "10-A" and plan.to_section == "11-A"
    assert [(e.student_id, e.class_section_id, e.status) for e in roster(db, ids["section_10a"])] == before
    assert db.scalar(
        select(Enrolment).where(Enrolment.academic_year_id == next_year.id)
    ) is None


def test_promotion_blocks_when_the_target_section_does_not_exist(db, ids, next_year):
    """Better to refuse than to invent a class or silently drop students."""
    plan = promotion.preview(db, ids["section_10a"], next_year.id)
    assert not plan.can_commit
    with pytest.raises(HTTPException) as e:
        promotion.commit(db, ids["section_10a"], next_year.id)
    assert e.value.status_code == 409


def test_commit_moves_everyone_and_keeps_last_year_intact(db, ids, next_year):
    make_section(db, next_year, "11")
    before = {(e.student_id, e.roll_no) for e in roster(db, ids["section_10a"])}

    plan = promotion.commit(db, ids["section_10a"], next_year.id)

    old = db.scalars(
        select(Enrolment).where(Enrolment.class_section_id == ids["section_10a"])
    ).all()
    assert {(e.student_id, e.roll_no) for e in old} == before
    assert all(e.status is EnrolmentStatus.promoted for e in old)

    new = db.scalars(
        select(Enrolment).where(Enrolment.academic_year_id == next_year.id)
    ).all()
    assert {e.student_id for e in new} == {sid for sid, _ in before}
    assert sorted(e.roll_no for e in new) == list(range(1, len(before) + 1))
    assert len(plan.lines) == len(before)


def test_promotion_does_not_touch_historical_attendance(db, ids, next_year):
    """The failure v0 made structurally possible: last year's rows following the
    student into the new class."""
    make_section(db, next_year, "11")
    student_id = roster(db, ids["section_10a"])[0].student_id
    before = db.scalars(
        select(Attendance).where(Attendance.student_id == student_id)
    ).all()
    assert before, "seed should have attendance"
    snapshot = {(a.id, a.date, a.status) for a in before}

    promotion.commit(db, ids["section_10a"], next_year.id)

    after = db.scalars(
        select(Attendance).where(Attendance.student_id == student_id)
    ).all()
    assert {(a.id, a.date, a.status) for a in after} == snapshot


def test_a_detained_student_repeats_the_same_class(db, ids, next_year):
    make_section(db, next_year, "11")
    make_section(db, next_year, "10")
    current = roster(db, ids["section_10a"])
    detained = current[0].student_id

    promotion.commit(
        db, ids["section_10a"], next_year.id, outcomes={detained: promotion.Outcome.detain}
    )

    new = {
        e.student_id: e
        for e in db.scalars(
            select(Enrolment).where(Enrolment.academic_year_id == next_year.id)
        )
    }
    assert new[detained].class_section.class_name == "10"
    assert new[current[1].student_id].class_section.class_name == "11"

    old = {e.student_id: e for e in db.scalars(
        select(Enrolment).where(Enrolment.class_section_id == ids["section_10a"])
    )}
    assert old[detained].status is EnrolmentStatus.detained


def test_the_final_class_passes_out_rather_than_promoting(db, ids, next_year):
    """Class 12 has nowhere to go, so promotion means leaving."""
    plan = promotion.commit(db, ids["section_10a"], next_year.id, final_class="10")

    assert {line.outcome for line in plan.lines} == {promotion.Outcome.pass_out}
    old = db.scalars(
        select(Enrolment).where(Enrolment.class_section_id == ids["section_10a"])
    ).all()
    assert all(e.status is EnrolmentStatus.passed_out for e in old)
    assert all(e.left_on is not None for e in old)
    assert all(e.student.status is StudentStatus.passed_out for e in old)
    # Nothing was created in the target year.
    assert db.scalar(
        select(Enrolment).where(Enrolment.academic_year_id == next_year.id)
    ) is None


def test_running_a_promotion_twice_is_refused(db, ids, next_year):
    """Not idempotent-by-silence: the second run says so rather than creating a
    duplicate set of enrolments."""
    make_section(db, next_year, "11")
    promotion.commit(db, ids["section_10a"], next_year.id)

    plan = promotion.preview(db, ids["section_10a"], next_year.id)
    assert not plan.can_commit
    assert any("already been run" in b for b in plan.blockers)


def test_promotion_into_a_closed_year_is_refused(db, ids, next_year):
    make_section(db, next_year, "11")
    next_year.status = AcademicYearStatus.closed
    db.flush()
    with pytest.raises(HTTPException) as e:
        promotion.commit(db, ids["section_10a"], next_year.id)
    assert e.value.status_code == 409
