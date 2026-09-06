from datetime import date as Date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import (
    Exam,
    ExamSchedule,
    FeeInvoice,
    InvoiceStatus,
    Mark,
    Parent,
    ParentStudent,
    Student,
    Teacher,
    User,
    UserRole,
)
from app.schemas.common import AttendanceMonth, ReportCard, StudentHomeworkOut
from app.services import assessment, attendance, fees, homework, notices, scoping

router = APIRouter(prefix="/parent", tags=["parent"])
parent_only = require_role(UserRole.parent)


@router.get("/children")
def children(user: User = Depends(parent_only), db: Session = Depends(get_db)) -> list[dict]:
    ids = scoping.child_ids_for(db, user)
    return [
        {
            "id": s.id,
            "name": s.user.full_name,
            "class_label": s.class_section.label,
            "admission_no": s.admission_no,
            "roll_no": s.roll_no,
        }
        for s in db.scalars(select(Student).where(Student.id.in_(ids)))
    ]


@router.get("/children/{student_id}/summary")
def summary(
    student_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> dict:
    s = scoping.assert_can_read_student(db, user, student_id)
    exam = assessment.latest_exam_with_marks(db, s.school_id, s.class_section_id)
    hw = homework.for_student(db, s.id)
    invoices = list(db.scalars(select(FeeInvoice).where(FeeInvoice.student_id == s.id)))
    fees.refresh_overdue(db, invoices)
    return {
        "student_id": s.id,
        "name": s.user.full_name,
        "class_label": s.class_section.label,
        "attendance_percent": attendance.student_percent(db, s.id),
        "homework_submitted": sum(1 for h in hw if h.submitted),
        "homework_pending": sum(1 for h in hw if not h.submitted),
        "latest_result_percent": (
            assessment.student_average_percent(db, s.id, exam.id) if exam else None
        ),
        "fee_dues": sum(1 for i in invoices if i.status != InvoiceStatus.paid),
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
    teacher = db.get(Teacher, s.class_section.class_teacher_id) if s.class_section.class_teacher_id else None
    return {
        "id": s.id,
        "full_name": s.user.full_name,
        "admission_no": s.admission_no,
        "class_label": s.class_section.label,
        "roll_no": s.roll_no,
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
    p = db.scalar(select(Parent).where(Parent.user_id == user.id))
    links = db.scalars(select(ParentStudent).where(ParentStudent.parent_id == p.id)).all()
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
