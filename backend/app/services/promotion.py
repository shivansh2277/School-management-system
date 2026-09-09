"""Year-end rollover: promote, detain, or pass out a section.

This is the workflow ERP_BLUEPRINT §7.4 calls the proof of the architecture.
Under v0 it was impossible without destroying data, because a student's class
was a mutable column. Here it only ever *creates* enrolments and closes the old
ones, so a promotion can be reviewed before it commits and last year stays
exactly as it was afterwards.
"""

from dataclasses import dataclass, field
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    Student,
    StudentStatus,
)
from app.services.common import roster
from app.services.tenancy import assert_writable


class Outcome:
    """What happens to one student at the end of a year."""

    promote = "promote"
    detain = "detain"
    pass_out = "pass_out"
    transfer_out = "transfer_out"


@dataclass
class PromotionLine:
    student_id: int
    student_name: str
    admission_no: str
    from_roll_no: int
    outcome: str
    to_class_label: str | None = None
    to_roll_no: int | None = None
    note: str | None = None


@dataclass
class PromotionPreview:
    """Always produced before anything is written. A promotion that cannot be
    inspected first is one nobody will trust."""

    from_year: str
    to_year: str
    from_section: str
    to_section: str | None
    lines: list[PromotionLine] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    @property
    def can_commit(self) -> bool:
        return not self.blockers


def _target_section(
    db: Session, section: ClassSection, to_year: AcademicYear
) -> ClassSection | None:
    """The same section letter, one class up, in the target year."""
    try:
        next_class = str(int(section.class_name) + 1)
    except ValueError:
        return None
    return db.scalar(
        select(ClassSection).where(
            ClassSection.academic_year_id == to_year.id,
            ClassSection.class_name == next_class,
            ClassSection.section == section.section,
        )
    )


def preview(
    db: Session,
    class_section_id: int,
    to_year_id: int,
    outcomes: dict[int, str] | None = None,
    final_class: str = "12",
) -> PromotionPreview:
    """Work out what a promotion would do, without doing it.

    `outcomes` overrides the default (promote) for named students, so a detained
    or leaving child is decided explicitly rather than by omission.
    """
    outcomes = outcomes or {}
    section = db.get(ClassSection, class_section_id)
    to_year = db.get(AcademicYear, to_year_id)
    if section is None or to_year is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Section or year not found")
    if section.school_id != to_year.school_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Section and year differ in school")

    from_year = db.get(AcademicYear, section.academic_year_id)
    if from_year.id == to_year.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Cannot promote a section into its own year"
        )

    target = _target_section(db, section, to_year)
    out = PromotionPreview(
        from_year=from_year.code,
        to_year=to_year.code,
        from_section=section.label,
        to_section=target.label if target else None,
    )

    current = roster(db, class_section_id)

    # Look at every enrolment of this section, not just the active ones: after
    # a run they are all `promoted`, and reporting "no active students" would
    # describe the symptom rather than the cause.
    section_student_ids = [
        e.student_id
        for e in db.scalars(
            select(Enrolment).where(Enrolment.class_section_id == class_section_id)
        )
    ]
    already = db.scalar(
        select(Enrolment).where(
            Enrolment.academic_year_id == to_year.id,
            Enrolment.student_id.in_(section_student_ids or [0]),
        )
    )
    if already is not None:
        out.blockers.append(
            f"At least one student from {section.label} already has an enrolment in "
            f"{to_year.code}; this promotion has already been run"
        )
    elif not current:
        out.blockers.append("This section has no active students to promote")

    # Roll numbers already used in the target section, so a partial re-run does
    # not collide with what an earlier run created.
    taken = set()
    if target is not None:
        taken = {
            e.roll_no
            for e in db.scalars(
                select(Enrolment).where(Enrolment.class_section_id == target.id)
            )
        }

    next_roll = 1
    for e in current:
        outcome = outcomes.get(e.student_id, Outcome.promote)
        line = PromotionLine(
            student_id=e.student_id,
            student_name=e.student.user.full_name,
            admission_no=e.student.admission_no,
            from_roll_no=e.roll_no,
            outcome=outcome,
        )

        if outcome == Outcome.promote:
            if section.class_name == final_class:
                line.outcome = Outcome.pass_out
                line.note = f"Class {final_class} is the final class"
            elif target is None:
                line.note = "No matching section exists in the target year"
                out.blockers.append(
                    f"Create the next class section in {to_year.code} before promoting "
                    f"{section.label}"
                )
            else:
                while next_roll in taken:
                    next_roll += 1
                taken.add(next_roll)
                line.to_class_label = target.label
                line.to_roll_no = next_roll
                next_roll += 1
        elif outcome == Outcome.detain:
            line.note = f"Repeats {section.class_name}"

        out.lines.append(line)

    return out


def commit(
    db: Session,
    class_section_id: int,
    to_year_id: int,
    outcomes: dict[int, str] | None = None,
    final_class: str = "12",
) -> PromotionPreview:
    """Apply a previewed promotion, all of it or none of it."""
    plan = preview(db, class_section_id, to_year_id, outcomes, final_class)
    if not plan.can_commit:
        raise HTTPException(status.HTTP_409_CONFLICT, "; ".join(plan.blockers))

    to_year = db.get(AcademicYear, to_year_id)
    assert_writable(to_year)
    section = db.get(ClassSection, class_section_id)
    target = _target_section(db, section, to_year)
    today = date.today()

    by_student = {e.student_id: e for e in roster(db, class_section_id)}
    for line in plan.lines:
        old = by_student[line.student_id]
        student = db.get(Student, line.student_id)

        if line.outcome == Outcome.promote:
            old.status = EnrolmentStatus.promoted
            db.add(
                Enrolment(
                    school_id=section.school_id,
                    student_id=line.student_id,
                    academic_year_id=to_year.id,
                    class_section_id=target.id,
                    roll_no=line.to_roll_no,
                    joined_on=to_year.start_date,
                    house=old.house,
                )
            )
        elif line.outcome == Outcome.detain:
            old.status = EnrolmentStatus.detained
            # Repeats the same class, so the target section is the same class
            # name in the new year.
            repeat = db.scalar(
                select(ClassSection).where(
                    ClassSection.academic_year_id == to_year.id,
                    ClassSection.class_name == section.class_name,
                    ClassSection.section == section.section,
                )
            )
            if repeat is None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Cannot detain into {to_year.code}: {section.label} does not exist there",
                )
            db.add(
                Enrolment(
                    school_id=section.school_id,
                    student_id=line.student_id,
                    academic_year_id=to_year.id,
                    class_section_id=repeat.id,
                    roll_no=line.to_roll_no or old.roll_no,
                    joined_on=to_year.start_date,
                )
            )
        elif line.outcome == Outcome.pass_out:
            old.status = EnrolmentStatus.passed_out
            old.left_on = today
            student.status = StudentStatus.passed_out
        elif line.outcome == Outcome.transfer_out:
            old.status = EnrolmentStatus.transferred_out
            old.left_on = today
            student.status = StudentStatus.transferred_out

    db.commit()
    return plan
