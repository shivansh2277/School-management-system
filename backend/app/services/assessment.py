"""Marks: entering them, closing them, and changing one after it is closed.

Three rules here are the module's integrity, and each is cheap to state and
expensive to omit.

**Absent, exempted and zero are three different states** (§5.4.9). A zero is a
mark. An absence is not, and neither is an exemption — a child excused from a
paper must not be averaged against it.

**A paper is locked, not a mark.** §5.4.7 closes marks entry per subject, so
the lock lives on the paper and a paper cannot be half shut.

**Every post-lock change is audited, without exception.** It needs the override
permission and a reason, and it lands in the audit log with the old and new
mark side by side. That log is where a re-evaluation dispute is settled.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    Exam,
    ExamSchedule,
    Mark,
    Student,
    User,
)
from app.schemas.common import (
    ExamScheduleOut,
    MarksRequest,
    MarksRosterRow,
    ReportCard,
    ReportCardRow,
)
from app.services import audit, rbac, scoping
from app.services.common import (
    grade_for,
    require_current_enrolment,
    roster,
    section_labels,
    subject_names,
)


def schedule_out(db: Session, rows: list[ExamSchedule]) -> list[ExamScheduleOut]:
    if not rows:
        return []
    school_id = rows[0].school_id
    labels = section_labels(db, school_id)
    subjects = subject_names(db, school_id)
    exams = {
        e.id: e.name
        for e in db.scalars(select(Exam).where(Exam.school_id == school_id))
    }
    with_marks = set(
        db.scalars(
            select(Mark.exam_schedule_id).where(
                Mark.exam_schedule_id.in_([r.id for r in rows] or [0])
            )
        )
    )
    return [
        ExamScheduleOut(
            id=r.id,
            exam_id=r.exam_id,
            exam_name=exams.get(r.exam_id, ""),
            class_section_id=r.class_section_id,
            class_label=labels.get(r.class_section_id, ""),
            subject_id=r.subject_id,
            subject=subjects.get(r.subject_id, ""),
            exam_date=r.exam_date,
            start_time=r.start_time,
            max_marks=r.max_marks,
            marks_entered=r.id in with_marks,
            marks_locked=r.is_locked,
        )
        for r in rows
    ]


def _owned_schedule(
    db: Session, user: User, exam_schedule_id: int, *, school_wide: bool = False
) -> ExamSchedule:
    """The paper, if this user may touch it.

    A subject teacher reaches only the papers they teach (§5.4.8). An exam
    controller reaches every paper in their school and no other — which is why
    `school_wide` still checks the tenant key rather than skipping the check.
    """
    sched = db.get(ExamSchedule, exam_schedule_id)
    if sched is None or sched.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam paper not found")
    if not school_wide:
        scoping.assert_teaches_subject_in_section(
            db, user, sched.class_section_id, sched.subject_id
        )
    return sched


def marks_roster(
    db: Session, user: User, exam_schedule_id: int, *, school_wide: bool = False
) -> list[MarksRosterRow]:
    sched = _owned_schedule(db, user, exam_schedule_id, school_wide=school_wide)
    existing = {
        m.student_id: m
        for m in db.scalars(select(Mark).where(Mark.exam_schedule_id == sched.id))
    }
    rows = []
    for e in roster(db, sched.class_section_id):
        m = existing.get(e.student_id)
        rows.append(
            MarksRosterRow(
                student_id=e.student_id,
                full_name=e.student.user.full_name,
                roll_no=e.roll_no,
                marks_obtained=m.marks_obtained if m else None,
                is_absent=bool(m and m.is_absent),
                is_exempted=bool(m and m.is_exempted),
                remarks=m.remarks if m else None,
            )
        )
    return rows


def _state(entry) -> tuple[Decimal | None, bool, bool]:
    """Resolve one entry into the (score, absent, exempted) triple, refusing
    the combinations the database constraints would reject anyway."""
    if entry.is_absent and entry.is_exempted:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A child is absent or exempted, not both",
        )
    if (entry.is_absent or entry.is_exempted) and entry.marks_obtained is not None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A child marked absent or exempted cannot also carry a score",
        )
    return entry.marks_obtained, entry.is_absent, entry.is_exempted


def enter_marks(
    db: Session, user: User, body: MarksRequest, *, school_wide: bool = False
) -> list[MarksRosterRow]:
    sched = _owned_schedule(db, user, body.exam_schedule_id, school_wide=school_wide)
    students = {e.student_id: e.student for e in roster(db, sched.class_section_id)}
    existing = {
        m.student_id: m
        for m in db.scalars(select(Mark).where(Mark.exam_schedule_id == sched.id))
    }

    # The lock is checked once for the paper, before anything is written: a
    # half-applied batch is worse than a refused one.
    if sched.is_locked:
        if not rbac.authz_for(db, user).can("exam.marks.override"):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Marks for this paper are locked. Changing one now needs an "
                "exam controller's override and a reason.",
            )
        if not (body.reason and body.reason.strip()):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "A reason is required to change a mark after the paper is locked",
            )

    for entry in body.entries:
        student = students.get(entry.student_id)
        if student is None:
            raise scoping.forbidden("Student is not in this class section")
        score, absent, exempted = _state(entry)
        if score is not None and (score < 0 or score > sched.max_marks):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"{student.user.full_name}: marks must be between 0 and {sched.max_marks}",
            )
        if score is None and not (absent or exempted):
            # Nothing said about this child. Leaving the row alone is the point:
            # writing a null would erase a mark somebody already entered.
            continue

        row = existing.get(entry.student_id)
        if row is None:
            db.add(
                Mark(
                    school_id=sched.school_id,
                    exam_schedule_id=sched.id,
                    student_id=entry.student_id,
                    marks_obtained=score,
                    is_absent=absent,
                    is_exempted=exempted,
                    remarks=entry.remarks,
                    entered_by=user.id,
                )
            )
            continue

        before = audit.snapshot(row, ["marks_obtained", "is_absent", "is_exempted"])
        row.marks_obtained = score
        row.is_absent = absent
        row.is_exempted = exempted
        if entry.remarks is not None:
            row.remarks = entry.remarks
        row.entered_by = user.id
        if sched.is_locked:
            # Without exception (§5.4.9): the old and new mark side by side,
            # with who changed it and why. This log is where a re-evaluation
            # dispute is settled.
            audit.record(
                db,
                actor=user,
                school_id=sched.school_id,
                entity_type="mark",
                entity_id=row.id,
                action=AuditAction.status_change,
                before=before,
                after=audit.snapshot(
                    row, ["marks_obtained", "is_absent", "is_exempted"]
                ),
                reason=body.reason,
            )
    db.commit()
    return marks_roster(db, user, sched.id, school_wide=school_wide)


def lock_marks(db: Session, user: User, exam_schedule_id: int) -> ExamSchedule:
    """Close entry on a paper. Idempotent: locking a locked paper is a no-op,
    not an error, because two clerks clicking it is not a fault."""
    sched = db.get(ExamSchedule, exam_schedule_id)
    if sched is None or sched.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam paper not found")
    if sched.is_locked:
        return sched
    entered = db.scalar(
        select(Mark.id).where(Mark.exam_schedule_id == sched.id).limit(1)
    )
    if entered is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Nothing has been entered for this paper yet, so there is nothing "
            "to lock",
        )
    sched.marks_locked_at = datetime.now(UTC)
    sched.marks_locked_by = user.id
    audit.record(
        db,
        actor=user,
        school_id=sched.school_id,
        entity_type="exam_schedule",
        entity_id=sched.id,
        action=AuditAction.publish,
        after={"marks_locked_at": str(sched.marks_locked_at)},
    )
    db.commit()
    return sched


def unlock_marks(db: Session, user: User, exam_schedule_id: int, reason: str) -> ExamSchedule:
    """Reopen a paper. Needs a reason, and is audited like any other reversal."""
    sched = db.get(ExamSchedule, exam_schedule_id)
    if sched is None or sched.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam paper not found")
    if not sched.is_locked:
        return sched
    audit.record(
        db,
        actor=user,
        school_id=sched.school_id,
        entity_type="exam_schedule",
        entity_id=sched.id,
        action=AuditAction.status_change,
        before={"marks_locked_at": str(sched.marks_locked_at)},
        after={"marks_locked_at": None},
        reason=reason,
    )
    sched.marks_locked_at = None
    sched.marks_locked_by = None
    db.commit()
    return sched


def report_card(db: Session, student_id: int, exam_id: int) -> ReportCard:
    student = db.get(Student, student_id)
    exam = db.get(Exam, exam_id)
    if student is None or exam is None or exam.school_id != student.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam or student not found")
    enrolment = require_current_enrolment(db, student.id)
    schedules = list(
        db.scalars(
            select(ExamSchedule).where(
                ExamSchedule.exam_id == exam_id,
                ExamSchedule.class_section_id == enrolment.class_section_id,
            )
        )
    )
    marks = {
        m.exam_schedule_id: m
        for m in db.scalars(
            select(Mark).where(
                Mark.student_id == student_id,
                Mark.exam_schedule_id.in_([s.id for s in schedules] or [0]),
            )
        )
    }
    subjects = subject_names(db, student.school_id)
    rows, total_obtained, total_max = [], Decimal(0), Decimal(0)
    for sched in sorted(schedules, key=lambda s: s.exam_date):
        mark = marks.get(sched.id)
        obtained = mark.marks_obtained if mark else None
        percent = None
        if obtained is not None:
            # A subject with no mark is excluded from the totals rather than
            # counted as zero (BLUEPRINT §8, kept from v0). Absent and exempted
            # are both "no mark" for this purpose and are labelled separately
            # on the row, so the card can print AB rather than a blank.
            total_obtained += obtained
            total_max += sched.max_marks
            percent = round(float(obtained) / float(sched.max_marks) * 100, 1)
        rows.append(
            ReportCardRow(
                subject=subjects.get(sched.subject_id, ""),
                marks_obtained=obtained,
                max_marks=sched.max_marks,
                percent=percent,
                grade=grade_for(db, student.school_id, percent),
                is_absent=bool(mark and mark.is_absent),
                is_exempted=bool(mark and mark.is_exempted),
            )
        )
    overall = round(float(total_obtained) / float(total_max) * 100, 1) if total_max else None
    return ReportCard(
        exam_id=exam.id,
        exam_name=exam.name,
        student_id=student.id,
        student_name=student.user.full_name,
        class_label=enrolment.class_section.label,
        rows=rows,
        total_obtained=total_obtained,
        total_max=total_max,
        overall_percent=overall,
        overall_grade=grade_for(db, student.school_id, overall),
    )


def latest_exam_with_marks(
    db: Session, school_id: int, class_section_id: int | None = None
) -> Exam | None:
    q = (
        select(Exam)
        .join(ExamSchedule, ExamSchedule.exam_id == Exam.id)
        .join(Mark, Mark.exam_schedule_id == ExamSchedule.id)
        .where(Exam.school_id == school_id)
    )
    if class_section_id is not None:
        q = q.where(ExamSchedule.class_section_id == class_section_id)
    return db.scalars(q.order_by(Exam.end_date.desc()).limit(1)).first()


def student_average_percent(db: Session, student_id: int, exam_id: int) -> float | None:
    return report_card(db, student_id, exam_id).overall_percent
