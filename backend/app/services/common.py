"""Small shared lookups used by more than one service."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ClassSection, GradeBand, Student, Subject


def section_labels(db: Session) -> dict[int, str]:
    return {s.id: s.label for s in db.scalars(select(ClassSection))}


def subject_names(db: Session) -> dict[int, str]:
    return {s.id: s.name for s in db.scalars(select(Subject))}


def roster(db: Session, class_section_id: int) -> list[Student]:
    """Active students of a section, in roll order."""
    return list(
        db.scalars(
            select(Student)
            .where(Student.class_section_id == class_section_id)
            .order_by(Student.roll_no)
        )
    )


def grade_for(db: Session, percent: float | Decimal | None) -> str | None:
    """Computed at read time from grade_bands; never stored (BLUEPRINT §7.5)."""
    if percent is None:
        return None
    bands = db.scalars(select(GradeBand).order_by(GradeBand.min_percent.desc())).all()
    for band in bands:
        if Decimal(str(percent)) >= band.min_percent:
            return band.grade
    return None
