"""Small shared lookups used by more than one service."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    GradeBand,
    Student,
    Subject,
    User,
)


def section_labels(db: Session) -> dict[int, str]:
    return {s.id: s.label for s in db.scalars(select(ClassSection))}


def subject_names(db: Session) -> dict[int, str]:
    return {s.id: s.name for s in db.scalars(select(Subject))}


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


def grade_for(db: Session, percent: float | Decimal | None) -> str | None:
    """Computed at read time from grade_bands; never stored (BLUEPRINT §7.5)."""
    if percent is None:
        return None
    bands = db.scalars(select(GradeBand).order_by(GradeBand.min_percent.desc())).all()
    for band in bands:
        if Decimal(str(percent)) >= band.min_percent:
            return band.grade
    return None
