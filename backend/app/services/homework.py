from datetime import UTC, date as Date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ClassSection,
    Enrolment,
    Homework,
    HomeworkSubmission,
    Subject,
    Employee,
    User,
)
from app.schemas.common import (
    HomeworkCreate,
    HomeworkOut,
    HomeworkUpdate,
    StudentHomeworkOut,
    SubmissionRow,
)
from app.services import scoping
from app.services.common import require_current_enrolment, roster


def _counts(db: Session, homework_ids: list[int]) -> dict[int, int]:
    if not homework_ids:
        return {}
    rows = db.execute(
        select(HomeworkSubmission.homework_id, func.count())
        .where(HomeworkSubmission.homework_id.in_(homework_ids))
        .group_by(HomeworkSubmission.homework_id)
    ).all()
    return dict(rows)


def _roster_sizes(db: Session) -> dict[int, int]:
    return dict(
        db.execute(
            select(Enrolment.class_section_id, func.count()).group_by(
                Enrolment.class_section_id
            )
        ).all()
    )


def to_out(db: Session, items: list[Homework]) -> list[HomeworkOut]:
    subs = _counts(db, [h.id for h in items])
    sizes = _roster_sizes(db)
    labels = {c.id: c.label for c in db.scalars(select(ClassSection))}
    subjects = {s.id: s.name for s in db.scalars(select(Subject))}
    teachers = {t.id: t.user.full_name for t in db.scalars(select(Employee))}
    return [
        HomeworkOut(
            id=h.id,
            class_section_id=h.class_section_id,
            class_label=labels.get(h.class_section_id, ""),
            subject_id=h.subject_id,
            subject=subjects.get(h.subject_id, ""),
            teacher_id=h.teacher_id,
            teacher=teachers.get(h.teacher_id, ""),
            title=h.title,
            description=h.description,
            assigned_date=h.assigned_date,
            due_date=h.due_date,
            # pending = roster - submissions; there is no status column (§7.4)
            submitted_count=subs.get(h.id, 0),
            total_students=sizes.get(h.class_section_id, 0),
            attachment_url=h.attachment_url,
        )
        for h in items
    ]


def create(db: Session, user: User, body: HomeworkCreate) -> HomeworkOut:
    scoping.assert_teaches_subject_in_section(db, user, body.class_section_id, body.subject_id)
    assigned = Date.today()
    if body.due_date < assigned:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "due_date must not precede assigned_date")
    hw = Homework(
        class_section_id=body.class_section_id,
        school_id=user.school_id,
        subject_id=body.subject_id,
        teacher_id=scoping.employee_for(db, user).id,
        title=body.title,
        description=body.description,
        assigned_date=assigned,
        due_date=body.due_date,
        attachment_url=body.attachment_url,
    )
    db.add(hw)
    db.commit()
    return to_out(db, [hw])[0]


def _owned(db: Session, user: User, homework_id: int) -> Homework:
    hw = db.get(Homework, homework_id)
    if hw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Homework not found")
    scoping.assert_teaches_subject_in_section(db, user, hw.class_section_id, hw.subject_id)
    return hw


def update(db: Session, user: User, homework_id: int, body: HomeworkUpdate) -> HomeworkOut:
    hw = _owned(db, user, homework_id)
    if body.title is not None:
        hw.title = body.title
    if body.description is not None:
        hw.description = body.description
    if body.due_date is not None:
        if body.due_date < hw.assigned_date:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "due_date must not precede assigned_date"
            )
        hw.due_date = body.due_date
    if body.attachment_url is not None:
        hw.attachment_url = body.attachment_url
    db.commit()
    return to_out(db, [hw])[0]


def delete(db: Session, user: User, homework_id: int) -> None:
    hw = _owned(db, user, homework_id)
    db.query(HomeworkSubmission).filter(HomeworkSubmission.homework_id == hw.id).delete()
    db.delete(hw)
    db.commit()


def submissions(db: Session, user: User, homework_id: int) -> list[SubmissionRow]:
    hw = _owned(db, user, homework_id)
    rows = {
        s.enrolment_id: s
        for s in db.scalars(
            select(HomeworkSubmission).where(HomeworkSubmission.homework_id == hw.id)
        )
    }
    out = []
    for e in roster(db, hw.class_section_id):
        sub = rows.get(e.id)
        out.append(
            SubmissionRow(
                id=sub.id if sub else None,
                submission_id=sub.id if sub else None,
                student_id=e.student_id,
                enrolment_id=e.id,
                full_name=e.student.user.full_name,
                roll_no=e.roll_no,
                submitted=sub is not None,
                submitted_at=sub.submitted_at if sub else None,
                late=bool(sub and sub.submitted_at.date() > hw.due_date),
                answer_text=sub.answer_text if sub else None,
                marks=sub.marks if sub else None,
                remarks=sub.remarks if sub else None,
                graded_at=sub.graded_at if sub else None,
                attachment_url=sub.attachment_url if sub else None,
            )
        )
    return out


def for_student(db: Session, student_id: int, only: str = "all") -> list[StudentHomeworkOut]:
    enrolment = require_current_enrolment(db, student_id)
    items = list(
        db.scalars(
            select(Homework)
            .where(Homework.class_section_id == enrolment.class_section_id)
            .order_by(Homework.due_date.desc())
        )
    )
    subs = {
        s.homework_id: s
        for s in db.scalars(
            select(HomeworkSubmission).where(HomeworkSubmission.enrolment_id == enrolment.id)
        )
    }
    out = []
    for base, hw in zip(to_out(db, items), items, strict=True):
        sub = subs.get(hw.id)
        if only == "pending" and sub is not None:
            continue
        if only == "submitted" and sub is None:
            continue
        out.append(
            StudentHomeworkOut(
                **base.model_dump(),
                submitted=sub is not None,
                submitted_at=sub.submitted_at if sub else None,
                late=bool(sub and sub.submitted_at.date() > hw.due_date),
                answer_text=sub.answer_text if sub else None,
                marks=sub.marks if sub else None,
                remarks=sub.remarks if sub else None,
                graded_at=sub.graded_at if sub else None,
            )
        )
    return out


def submit(
    db: Session,
    user: User,
    homework_id: int,
    answer_text: str,
    attachment_url: str | None = None,
    enrolment_id: int | None = None,
) -> StudentHomeworkOut:
    student = scoping.student_for(db, user)
    hw = db.get(Homework, homework_id)
    if hw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Homework not found")
    current_enr = require_current_enrolment(db, student.id)
    if enrolment_id is not None:
        enr = db.get(Enrolment, enrolment_id)
        if enr is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")
        if enr.school_id != user.school_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cross-tenant access forbidden")
        if enr.student_id != student.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot submit for another student")
        if enr.class_section_id != hw.class_section_id:
            raise scoping.forbidden("This homework is not assigned to your class")
        target_enrolment = enr
    else:
        if hw.class_section_id != current_enr.class_section_id:
            raise scoping.forbidden("This homework is not assigned to your class")
        target_enrolment = current_enr

    answer = answer_text.strip() if answer_text else ""
    if not answer and not attachment_url:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Answer must not be empty")

    existing = db.scalar(
        select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == hw.id,
            HomeworkSubmission.enrolment_id == target_enrolment.id,
        )
    )
    now = datetime.now(UTC)
    if existing is None:
        db.add(
            HomeworkSubmission(
                school_id=student.school_id,
                homework_id=hw.id,
                enrolment_id=target_enrolment.id,
                answer_text=answer,
                attachment_url=attachment_url,
                submitted_at=now,
            )
        )
    else:  # resubmission updates in place and refreshes the timestamp (§8)
        existing.answer_text = answer
        if attachment_url is not None:
            existing.attachment_url = attachment_url
        existing.submitted_at = now
    db.commit()
    return next(h for h in for_student(db, student.id) if h.id == hw.id)


def grade_submission(
    db: Session,
    user: User,
    submission_id: int,
    marks: Decimal | float | None = None,
    remarks: str | None = None,
) -> SubmissionRow:
    sub = db.get(HomeworkSubmission, submission_id)
    if sub is None:
        sub = db.scalar(select(HomeworkSubmission).where(HomeworkSubmission.enrolment_id == submission_id))
    if sub is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    hw = db.get(Homework, sub.homework_id)
    scoping.assert_teaches_subject_in_section(db, user, hw.class_section_id, hw.subject_id)
    sub.marks = Decimal(str(marks)) if marks is not None else None
    sub.remarks = remarks
    sub.graded_at = datetime.now(UTC)
    db.commit()
    db.refresh(sub)
    enrolment = db.get(Enrolment, sub.enrolment_id)
    return SubmissionRow(
        id=sub.id,
        student_id=enrolment.student_id,
        enrolment_id=enrolment.id,
        full_name=enrolment.student.user.full_name,
        roll_no=enrolment.roll_no,
        submitted=True,
        submitted_at=sub.submitted_at,
        late=bool(sub.submitted_at.date() > hw.due_date),
        answer_text=sub.answer_text,
        marks=sub.marks,
        remarks=sub.remarks,
        graded_at=sub.graded_at,
        attachment_url=sub.attachment_url,
    )


def pending_count(db: Session, student_id: int) -> int:
    return len(for_student(db, student_id, "pending"))
