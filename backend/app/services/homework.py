from datetime import UTC, date as Date, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ClassSection,
    Enrolment,
    Homework,
    HomeworkSubmission,
    Student,
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
        s.student_id: s
        for s in db.scalars(
            select(HomeworkSubmission).where(HomeworkSubmission.homework_id == hw.id)
        )
    }
    out = []
    for e in roster(db, hw.class_section_id):
        sub = rows.get(e.student_id)
        out.append(
            SubmissionRow(
                student_id=e.student_id,
                full_name=e.student.user.full_name,
                roll_no=e.roll_no,
                submitted=sub is not None,
                submitted_at=sub.submitted_at if sub else None,
                late=bool(sub and sub.submitted_at.date() > hw.due_date),
                answer_text=sub.answer_text if sub else None,
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
            select(HomeworkSubmission).where(HomeworkSubmission.student_id == student_id)
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
            )
        )
    return out


def submit(db: Session, user: User, homework_id: int, answer_text: str) -> StudentHomeworkOut:
    student = scoping.student_for(db, user)
    hw = db.get(Homework, homework_id)
    if hw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Homework not found")
    if hw.class_section_id != require_current_enrolment(db, student.id).class_section_id:
        raise scoping.forbidden("This homework is not assigned to your class")
    answer = answer_text.strip()
    if not answer:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Answer must not be empty")

    existing = db.scalar(
        select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == hw.id,
            HomeworkSubmission.student_id == student.id,
        )
    )
    now = datetime.now(UTC)
    if existing is None:
        db.add(
            HomeworkSubmission(
                school_id=student.school_id,
                homework_id=hw.id,
                student_id=student.id,
                answer_text=answer,
                submitted_at=now,
            )
        )
    else:  # resubmission updates in place and refreshes the timestamp (§8)
        existing.answer_text = answer
        existing.submitted_at = now
    db.commit()
    return next(h for h in for_student(db, student.id) if h.id == hw.id)


def pending_count(db: Session, student_id: int) -> int:
    return len(for_student(db, student_id, "pending"))
