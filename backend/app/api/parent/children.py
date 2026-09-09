from datetime import date as Date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import (
    Exam,
    ExamSchedule,
    FeeInvoice,
    LeaveType,
    Mark,
    StudentLeaveRequest,
    Route,
    StudentGuardian,
    Student,
    TransportAssignment,
    TransportAssignmentStatus,
    Employee,
    User,
)
from app.schemas.common import AttendanceMonth, ReportCard, StudentHomeworkOut
from app.services import assessment, attendance, fees, homework, leave, notices, scoping
from app.services.common import current_enrolment, enrolment_map

router = APIRouter(prefix="/parent", tags=["parent"])
parent_only = require_permission("students.profile.read")


@router.get("/children")
def children(user: User = Depends(parent_only), db: Session = Depends(get_db)) -> list[dict]:
    ids = scoping.child_ids_for(db, user)
    enrolments = enrolment_map(db, ids)
    return [
        {
            "id": s.id,
            "name": s.user.full_name,
            "class_label": (
                enrolments[s.id].class_section.label if s.id in enrolments else ""
            ),
            "admission_no": s.admission_no,
            "roll_no": enrolments[s.id].roll_no if s.id in enrolments else None,
        }
        for s in db.scalars(select(Student).where(Student.id.in_(ids)))
    ]


@router.get("/children/{student_id}/summary")
def summary(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> dict:
    s = scoping.assert_can_read_student(db, user, student_id)
    enrolment = current_enrolment(db, s.id)
    exam = assessment.latest_exam_with_marks(
        db, s.school_id, enrolment.class_section_id if enrolment else None
    )
    hw = homework.for_student(db, s.id)
    return {
        "student_id": s.id,
        "name": s.user.full_name,
        "class_label": (e.class_section.label if (e := current_enrolment(db, s.id)) else ""),
        "attendance_percent": attendance.student_percent(db, s.id),
        "homework_submitted": sum(1 for h in hw if h.submitted),
        "homework_pending": sum(1 for h in hw if not h.submitted),
        "latest_result_percent": (
            assessment.student_average_percent(db, s.id, exam.id) if exam else None
        ),
        # Unsettled invoices, from the ledger rather than from a status
        # column, so a part payment does not read as a cleared due.
        "fee_dues": sum(
            1
            for i in fees.list_invoices(
                db,
                list(
                    db.scalars(
                        select(FeeInvoice).where(
                            FeeInvoice.enrolment_id == (enrolment.id if enrolment else 0)
                        )
                    )
                ),
            )
            if i["balance"] > 0
        ),
        "recent_notices": notices.visible_to(db, user)[:5],
    }


@router.get("/children/{student_id}/attendance", response_model=AttendanceMonth)
def child_attendance(
    student_id: int,
    month: int | None = None,
    year: int | None = None,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> AttendanceMonth:
    scoping.assert_can_read_student(db, user, student_id)
    today = Date.today()
    return attendance.student_month(db, student_id, month or today.month, year or today.year)


@router.get("/children/{student_id}/homework", response_model=list[StudentHomeworkOut])
def child_homework(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> list[StudentHomeworkOut]:
    scoping.assert_can_read_student(db, user, student_id)
    return homework.for_student(db, student_id)


@router.get("/children/{student_id}/results")
def child_results(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> list[dict]:
    scoping.assert_can_read_student(db, user, student_id)
    exams = db.scalars(
        select(Exam)
        .join(ExamSchedule, ExamSchedule.exam_id == Exam.id)
        .join(Mark, Mark.exam_schedule_id == ExamSchedule.id)
        .where(Mark.student_id == student_id)
        .distinct()
        .order_by(Exam.end_date.desc())
    ).all()
    return [
        {
            "exam_id": e.id,
            "name": e.name,
            "term": e.term,
            "overall_percent": assessment.report_card(db, student_id, e.id).overall_percent,
        }
        for e in exams
    ]


@router.get("/children/{student_id}/results/{exam_id}", response_model=ReportCard)
def child_report_card(
    student_id: int,
    exam_id: int,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> ReportCard:
    scoping.assert_can_read_student(db, user, student_id)
    return assessment.report_card(db, student_id, exam_id)


@router.get("/children/{student_id}/profile")
def child_profile(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> dict:
    s = scoping.assert_can_read_student(db, user, student_id)
    enrolment = current_enrolment(db, s.id)
    section = enrolment.class_section if enrolment else None
    teacher = (
        db.get(Employee, section.class_teacher_id)
        if section and section.class_teacher_id
        else None
    )
    return {
        "id": s.id,
        "full_name": s.user.full_name,
        "admission_no": s.admission_no,
        "class_label": section.label if section else "",
        "roll_no": enrolment.roll_no if enrolment else None,
        "dob": s.dob,
        "gender": s.gender,
        "address": s.address,
        "admission_date": s.admission_date,
        "class_teacher": (
            {"full_name": teacher.user.full_name, "phone": teacher.user.phone}
            if teacher
            else None
        ),
    }


@router.get("/profile")
def my_profile(user: User = Depends(parent_only), db: Session = Depends(get_db)) -> dict:
    # `parent_only` is `students.profile.read`, which an office clerk and a
    # teacher also hold, so non-guardians reach this route. The bare query
    # returned None for them and the next line raised - a 500 where the answer
    # is "you are not a parent". `guardian_for` is the shared gate that says so.
    p = scoping.guardian_for(db, user)
    links = db.scalars(select(StudentGuardian).where(StudentGuardian.guardian_id == p.id)).all()
    return {
        "id": p.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "occupation": p.occupation,
        "children_names": ", ".join(
            db.get(Student, link.student_id).user.full_name for link in links
        ),
        "children": [
            {
                "id": link.student_id,
                "relation": link.relation,
                "name": db.get(Student, link.student_id).user.full_name,
            }
            for link in links
        ],
    }


@router.get("/notices")
def my_notices(user: User = Depends(parent_only), db: Session = Depends(get_db)) -> list:
    return notices.visible_to(db, user)


class LeaveIn(BaseModel):
    model_config = {"extra": "forbid"}

    student_id: int
    from_date: Date
    to_date: Date
    type: LeaveType = LeaveType.sick
    reason: str = Field(min_length=3, max_length=400)


@router.post("/leave-requests", status_code=201)
def apply_for_leave(
    body: LeaveIn, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> dict:
    """A guardian asking for their own child to be away (§5.8.5).

    Only a request: it changes the register when someone approves it.
    """
    row = leave.apply_for(
        db, user, body.student_id, body.from_date, body.to_date, body.type, body.reason
    )
    return leave.to_out(db, row)


@router.get("/leave-requests")
def my_leave_requests(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> list[dict]:
    scoping.assert_can_read_student(db, user, student_id)
    enrolment = attendance.enrolment_of(db, student_id)
    if enrolment is None:
        return []
    return [
        leave.to_out(db, r)
        for r in db.scalars(
            select(StudentLeaveRequest)
            .where(StudentLeaveRequest.enrolment_id == enrolment.id)
            .order_by(StudentLeaveRequest.from_date.desc())
        )
    ]


@router.get("/children/{student_id}/transport")
def child_transport(
    student_id: int,
    user: User = Depends(require_permission("transport.assignment.read")),
    db: Session = Depends(get_db),
) -> dict | None:
    """Which bus this child is on, where it stops and when (§5.6.8).

    Scoped through `assert_can_read_student`, the same gate as everything else
    here — a guardian sees their own child's stop and nobody else's, and the
    driver's name and phone number are deliberately not in the payload.
    """
    scoping.assert_can_read_student(db, user, student_id)
    enrolment = current_enrolment(db, student_id)
    if enrolment is None:
        return None
    row = db.scalar(
        select(TransportAssignment).where(
            TransportAssignment.enrolment_id == enrolment.id,
            TransportAssignment.status.in_(
                (TransportAssignmentStatus.active, TransportAssignmentStatus.suspended)
            ),
        )
    )
    if row is None:
        return None
    stop = row.route_stop
    route = db.get(Route, stop.route_id)
    return {
        "route": route.name,
        "route_code": route.code,
        "stop": stop.name,
        "landmark": stop.landmark,
        "pickup_time": stop.pickup_time,
        "drop_time": stop.drop_time,
        "direction": row.direction.value,
        "status": row.status.value,
        "since": row.start_date,
    }
