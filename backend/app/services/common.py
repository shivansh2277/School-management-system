"""Small shared lookups used by more than one service."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    Student,
    Subject,
    User,
)


def section_labels(db: Session, school_id: int) -> dict[int, str]:
    return {
        s.id: s.label
        for s in db.scalars(select(ClassSection).where(ClassSection.school_id == school_id))
    }


def subject_names(db: Session, school_id: int) -> dict[int, str]:
    return {
        s.id: s.name
        for s in db.scalars(select(Subject).where(Subject.school_id == school_id))
    }


def roster(db: Session, class_section_id: int) -> list[Enrolment]:
    """Active enrolments of a section, in roll order.

    Returns enrolments rather than students because a roster is a fact about a
    year: `e.roll_no` and `e.class_section_id` belong to the enrolment, and
    `e.student` is eager-loaded so a caller iterating the list does not issue a
    query per row.

    The `is_active` filter is applied HERE, once, rather than left as a
    convention each caller must remember. v0's docstring promised "Active
    students" while the query had no such filter, so a deactivated student
    still appeared on attendance sheets and marks rosters; a shared, tested
    code path is what stops that recurring (ERP_BLUEPRINT §3.7).
    """
    return list(
        db.scalars(
            select(Enrolment)
            .join(Student, Student.id == Enrolment.student_id)
            .join(User, User.id == Student.user_id)
            .where(
                Enrolment.class_section_id == class_section_id,
                Enrolment.status == EnrolmentStatus.active,
                User.is_active,
            )
            .order_by(Enrolment.roll_no)
        )
    )


def roster_student_ids(db: Session, class_section_id: int) -> list[int]:
    """Just the student ids of a section's active roster."""
    return [e.student_id for e in roster(db, class_section_id)]


def current_enrolment(db: Session, student_id: int) -> Enrolment | None:
    """The student's enrolment in their school's current academic year."""
    return db.scalar(
        select(Enrolment)
        .join(AcademicYear, AcademicYear.id == Enrolment.academic_year_id)
        .where(
            Enrolment.student_id == student_id,
            AcademicYear.is_current.is_(True),
        )
    )


def require_current_enrolment(db: Session, student_id: int) -> Enrolment:
    from fastapi import HTTPException, status

    e = current_enrolment(db, student_id)
    if e is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This student has no enrolment in the current academic year",
        )
    return e


def enrolment_map(db: Session, student_ids: list[int]) -> dict[int, "Enrolment"]:
    """student_id -> current Enrolment, in one query.

    Used wherever a list of students needs its class label: doing it per row is
    how the 8.5s dashboard N+1 happened.
    """
    if not student_ids:
        return {}
    rows = db.scalars(
        select(Enrolment)
        .join(AcademicYear, AcademicYear.id == Enrolment.academic_year_id)
        .where(
            Enrolment.student_id.in_(student_ids),
            AcademicYear.is_current.is_(True),
        )
    )
    return {e.student_id: e for e in rows}


def class_label_map(db: Session, student_ids: list[int]) -> dict[int, str]:
    """student_id -> "10-A" for the current year, or "" if not enrolled."""
    return {
        sid: e.class_section.label for sid, e in enrolment_map(db, student_ids).items()
    }


def enrolment_sections(db: Session, student_ids: list[int]) -> dict[int, int]:
    """student_id -> current class_section_id, in one query rather than one per
    student."""
    if not student_ids:
        return {}
    rows = db.execute(
        select(Enrolment.student_id, Enrolment.class_section_id)
        .join(AcademicYear, AcademicYear.id == Enrolment.academic_year_id)
        .where(
            Enrolment.student_id.in_(student_ids),
            AcademicYear.is_current.is_(True),
        )
    ).all()
    return {sid: csid for sid, csid in rows}


def grade_for(db: Session, school_id: int, percent: float | Decimal | None) -> str | None:
    """The grade a percentage earns on the school's scale *currently in force*.

    Computed at read time, never stored (BLUEPRINT §7.5) — but only for live
    screens. A published report card cites its scale version and is read back
    through `grading.grade_in()`, so editing a band never rewrites a document
    the school has already issued (§0.8).
    """
    from app.services import grading

    scale = grading.active_scale(db, school_id)
    if scale is None:
        return None
    return grading.grade_in(db, scale.id, percent)


def class_sort_key(class_name: str | None) -> tuple[int, int, str]:
    """Order class names the way a school does: 1, 2, ... 9, 10, 11, 12.

    `class_name` is a String column everywhere it appears - on ClassSection, on
    FeePlan, on CycleClassConfig - so ordering by the column is lexicographic
    and puts class 10 immediately after class 1. Five listings had that bug
    independently, which is why the key lives here rather than in whichever one
    was noticed first.

    Sorted in Python because it has to hold on both engines: the test suite
    runs on SQLite, where a Postgres `::int` cast does not exist.

    Pre-primary names sort ahead of the numbered classes, alphabetically among
    themselves.
    # ponytail: alphabetical is wrong for Nursery -> LKG -> UKG, which is the
    # real progression. No seeded school has them, so this stays a note rather
    # than a hardcoded ladder; give the row an explicit ordinal column if a
    # school ever needs it.
    """
    name = (class_name or "").strip()
    if name.isdigit():
        return (1, int(name), "")
    return (0, 0, name.lower())
