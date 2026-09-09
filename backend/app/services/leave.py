"""Student leave requests (§5.8.5).

Approving a request writes the attendance rows for the range. Without that,
"approved leave" lives in one table and the register says `absent` in another,
and the two are only reconciled by whoever remembers — which is how a child
with approved leave ends up on a defaulter-style absence report.
"""

from datetime import UTC, date as Date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Attendance,
    Employee,
    AttendanceStatus,
    AuditAction,
    Enrolment,
    LeaveStatus,
    StudentLeaveRequest,
    User,
)
from app.services import attendance as att
from app.services import audit, scoping

MAX_DAYS = 60


def to_out(db: Session, row: StudentLeaveRequest) -> dict:
    enrolment = db.get(Enrolment, row.enrolment_id)
    student = enrolment.student
    return {
        "id": row.id,
        "student_id": student.id,
        "student_name": student.user.full_name,
        "class_label": enrolment.class_section.label,
        "from_date": row.from_date,
        "to_date": row.to_date,
        "type": row.type,
        "reason": row.reason,
        "status": row.status,
        "decided_at": row.decided_at,
        "decision_note": row.decision_note,
    }


def apply_for(
    db: Session,
    user: User,
    student_id: int,
    from_date: Date,
    to_date: Date,
    type_,
    reason: str,
) -> StudentLeaveRequest:
    scoping.assert_can_read_student(db, user, student_id)
    if to_date < from_date:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "The end date is before the start date"
        )
    if (to_date - from_date).days + 1 > MAX_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Leave longer than {MAX_DAYS} days is a withdrawal, not a leave request",
        )
    enrolment = att.enrolment_of(db, student_id)
    if enrolment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active enrolment")

    overlapping = db.scalar(
        select(StudentLeaveRequest).where(
            StudentLeaveRequest.enrolment_id == enrolment.id,
            StudentLeaveRequest.status.in_((LeaveStatus.applied, LeaveStatus.approved)),
            StudentLeaveRequest.from_date <= to_date,
            StudentLeaveRequest.to_date >= from_date,
        )
    )
    if overlapping is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A request already covers part of those dates",
        )

    row = StudentLeaveRequest(
        school_id=enrolment.school_id,
        enrolment_id=enrolment.id,
        from_date=from_date,
        to_date=to_date,
        type=type_,
        reason=reason,
        status=LeaveStatus.applied,
        requested_by=user.id,
    )
    db.add(row)
    db.commit()
    return row


def decide(
    db: Session, row: StudentLeaveRequest, actor: User, approve: bool, note: str | None
) -> StudentLeaveRequest:
    if row.status is not LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"This request is already {row.status.value}"
        )
    row.status = LeaveStatus.approved if approve else LeaveStatus.rejected
    row.decided_by = actor.id
    row.decided_at = datetime.now(UTC)
    row.decision_note = note

    written = 0
    if approve:
        written = _write_leave_days(db, row, actor)
    audit.record(
        db,
        actor=actor,
        school_id=row.school_id,
        entity_type="student_leave_request",
        entity_id=row.id,
        action=AuditAction.status_change,
        after={"status": row.status.value, "days_marked": written},
        reason=note or row.reason,
    )
    db.commit()
    return row


def _write_leave_days(db: Session, row: StudentLeaveRequest, actor: User) -> int:
    """Mark the working days in the range as leave.

    Days already marked are left alone rather than overwritten: if the teacher
    recorded the child as present on Tuesday, the child was there, and an
    approval granted afterwards must not erase that.
    """
    # The approver is usually the office, not a teacher, so there may be no
    # employee row to attribute the mark to. The audit log records who
    # approved; the register records that leave, not a person, wrote it.
    teacher = db.scalar(select(Employee).where(Employee.user_id == actor.id))
    holidays = att.holidays_between(db, row.school_id, row.from_date, row.to_date)
    existing = {
        a.date
        for a in db.scalars(
            select(Attendance).where(
                Attendance.enrolment_id == row.enrolment_id,
                Attendance.date >= row.from_date,
                Attendance.date <= row.to_date,
            )
        )
    }
    written = 0
    for n in range((row.to_date - row.from_date).days + 1):
        day = row.from_date + timedelta(days=n)
        if not att.is_working_day(day, holidays) or day in existing:
            continue
        db.add(
            Attendance(
                school_id=row.school_id,
                enrolment_id=row.enrolment_id,
                date=day,
                status=AttendanceStatus.leave,
                marked_by=teacher.id if teacher else None,
                remarks=f"Approved leave ({row.type.value})",
            )
        )
        written += 1
    db.flush()
    return written
