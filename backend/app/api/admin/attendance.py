"""Absentee list, shortage view, holidays and leave approval (§5.8.3).

The roll sheet itself stays where teachers reach it; these are the office's
screens — who is missing today, who is heading for a shortage, and which leave
requests are waiting.
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AcademicYear,
    AuditAction,
    ClassSection,
    Holiday,
    HolidayClassSection,
    LeaveStatus,
    StudentLeaveRequest,
    User,
)
from app.schemas.common import AttendanceSummary, RollRow
from app.services import attendance as svc
from app.services import audit
from app.services import leave as leave_svc
from app.services import scoping
from app.services import tenancy
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/attendance",
    tags=["attendance"],
    dependencies=[Depends(module_enabled("attendance"))],
)

reader = require_permission("attendance.record.read", school_wide=True)
corrector = require_permission("attendance.record.correct", school_wide=True)
holiday_manager = require_permission("attendance.holiday.manage", school_wide=True)


@router.get("", response_model=list[RollRow])
def attendance_roll(
    class_section_id: int,
    date: Date,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[RollRow]:
    """Read-only: admins do not mark attendance (BLUEPRINT §9 matrix).

    Moved here from `api/admin/exams.py`, where it was declared on the exams
    router and so gated on `exam.definition.read` instead of
    `attendance.record.read`. That let the Exam Controller (who holds the exam
    permission but not the attendance one) read the roll while the `/attendance`
    web screen — gated on `attendance.record.read` per `web/src/screens.ts` —
    stayed hidden from them, and let anyone holding `attendance.record.read`
    alone open that screen and get a 403 from both of its fetches. The route
    now lives on the router whose permission it actually needs.
    """
    # `roll_sheet()` takes a bare section id, so the section is proved to be
    # this school's first — otherwise any section number read back a roll.
    section = tenancy.get_owned(
        db, ClassSection, class_section_id, user, what="Class section"
    )
    return svc.roll_sheet(db, section.id, date)


@router.get("/summary", response_model=AttendanceSummary)
def attendance_summary(
    date_from: Date | None = Query(None, alias="from"),
    date_to: Date | None = Query(None, alias="to"),
    class_section_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> AttendanceSummary:
    """See `attendance_roll` above for why this moved out of `exams.py`."""
    return svc.section_summary(db, user.school_id, class_section_id, date_from, date_to)


class HolidayIn(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1, max_length=120)
    start_date: Date | None = None
    end_date: Date | None = None
    date: Date | None = None
    description: str | None = None
    is_school_wide: bool = True
    class_section_ids: list[int] = []
    academic_year_id: int | None = None


class HolidayCancelInput(BaseModel):
    model_config = {"extra": "forbid"}

    reason: str = Field(min_length=3, max_length=255)


class LeaveDecision(BaseModel):
    model_config = {"extra": "forbid"}

    approve: bool
    note: str | None = Field(default=None, max_length=400)


@router.get("/absentees")
def absentees(
    date: Date | None = None,
    class_section_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    # A class teacher gets their own section, not the school. This route was
    # gated on `attendance.record.read` school-wide and nothing else, and a
    # teacher holds that - so it answered TCH001 with all 100 children, names,
    # admission numbers and all. Same helper the report gate uses.
    class_section_id = scoping.narrow_to_own_sections(
        db, user, class_section_id, "The absentee list"
    )
    return svc.absentees(db, user.school_id, date or Date.today(), class_section_id)


@router.get("/shortage")
def shortage(
    threshold: float | None = None,
    class_section_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Children below the attendance threshold.

    `threshold` now defaults to the school's setting rather than to 75.0 in the
    signature. What counts as short attendance is a policy - CBSE's 75% is the
    common answer and not the only one - and every other policy number here
    lives in `core/settings_registry.py` (CLAUDE.md: money rules are settings,
    not constants).
    """
    class_section_id = scoping.narrow_to_own_sections(
        db, user, class_section_id, "The shortage list"
    )
    return svc.shortage(db, user.school_id, threshold, class_section_id)


@router.get("/holidays")
def holidays(
    year: int | None = None,
    status_filter: str | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(Holiday).where(Holiday.school_id == user.school_id)
    if year is not None:
        q = q.where(Holiday.academic_year_id == year)
    if status_filter:
        q = q.where(Holiday.status == status_filter)
    rows = list(db.scalars(q.order_by(Holiday.start_date.desc(), Holiday.id.desc())).all())
    return [
        {
            "id": h.id,
            "name": h.name,
            "description": h.description,
            "date": h.date,
            "start_date": h.start_date,
            "end_date": h.end_date,
            "is_school_wide": h.is_school_wide,
            "status": h.status,
            "cancellation_reason": h.cancellation_reason,
            "academic_year_id": h.academic_year_id,
            "class_sections": [
                {"id": cs.id, "label": cs.label} for cs in h.class_sections
            ],
        }
        for h in rows
    ]


@router.post("/holidays", status_code=201, dependencies=[Depends(holiday_manager)])
def add_holiday(
    body: HolidayIn, user: User = Depends(holiday_manager), db: Session = Depends(get_db)
) -> dict:
    start_date = body.start_date or body.date
    if not start_date:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "start_date or date is required")
    end_date = body.end_date or start_date
    if end_date < start_date:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "end_date cannot be earlier than start_date"
        )

    year_id = body.academic_year_id
    if year_id is None:
        current = db.scalar(
            select(AcademicYear).where(
                AcademicYear.school_id == user.school_id, AcademicYear.is_current.is_(True)
            )
        )
        if current is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "No current academic year")
        year_id = current.id

    row = Holiday(
        school_id=user.school_id,
        academic_year_id=year_id,
        date=start_date,
        start_date=start_date,
        end_date=end_date,
        name=body.name,
        description=body.description,
        is_school_wide=body.is_school_wide,
        status="active",
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()

    if not body.is_school_wide and body.class_section_ids:
        for cs_id in body.class_section_ids:
            cs = db.get(ClassSection, cs_id)
            if cs and cs.school_id == user.school_id:
                db.add(
                    HolidayClassSection(
                        school_id=user.school_id,
                        holiday_id=row.id,
                        class_section_id=cs.id,
                    )
                )

    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="holiday",
        entity_id=row.id,
        action=AuditAction.create,
        after={
            "name": row.name,
            "start_date": str(row.start_date),
            "end_date": str(row.end_date),
            "is_school_wide": row.is_school_wide,
        },
        reason="Holiday declared",
    )
    db.commit()
    return {
        "id": row.id,
        "name": row.name,
        "date": row.date,
        "start_date": row.start_date,
        "end_date": row.end_date,
        "is_school_wide": row.is_school_wide,
        "class_section_ids": [cs.id for cs in row.class_sections] if not row.is_school_wide else [],
        "status": row.status,
    }


@router.put("/holidays/{holiday_id}", dependencies=[Depends(holiday_manager)])
def update_holiday(
    holiday_id: int,
    body: HolidayIn,
    user: User = Depends(holiday_manager),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Holiday, holiday_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Holiday not found")

    start_date = body.start_date or body.date or row.start_date
    end_date = body.end_date or start_date
    if end_date < start_date:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "end_date cannot be earlier than start_date"
        )

    row.name = body.name
    row.start_date = start_date
    row.end_date = end_date
    row.date = start_date
    row.description = body.description
    row.is_school_wide = body.is_school_wide

    if not body.is_school_wide and body.class_section_ids is not None:
        db.query(HolidayClassSection).filter(HolidayClassSection.holiday_id == row.id).delete()
        for cs_id in body.class_section_ids:
            cs = db.get(ClassSection, cs_id)
            if cs and cs.school_id == user.school_id:
                db.add(
                    HolidayClassSection(
                        school_id=user.school_id,
                        holiday_id=row.id,
                        class_section_id=cs.id,
                    )
                )

    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="holiday",
        entity_id=row.id,
        action=AuditAction.update,
        after={
            "name": row.name,
            "start_date": str(row.start_date),
            "end_date": str(row.end_date),
            "is_school_wide": row.is_school_wide,
        },
        reason="Holiday updated",
    )
    db.commit()
    return {"id": row.id, "name": row.name, "status": row.status}


@router.post("/holidays/{holiday_id}/cancel", dependencies=[Depends(holiday_manager)])
def cancel_holiday(
    holiday_id: int,
    body: HolidayCancelInput,
    user: User = Depends(holiday_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel a holiday with mandatory reason. Retains historical attendance."""
    row = db.get(Holiday, holiday_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Holiday not found")
    if row.status == "cancelled":
        raise HTTPException(status.HTTP_409_CONFLICT, "Holiday is already cancelled")

    row.status = "cancelled"
    row.cancelled_by_id = user.id
    row.cancellation_reason = body.reason

    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="holiday",
        entity_id=row.id,
        action=AuditAction.status_change,
        after={"status": "cancelled", "cancellation_reason": body.reason},
        reason=f"Holiday cancelled: {body.reason}",
    )
    db.commit()
    return {"id": row.id, "status": row.status, "cancellation_reason": row.cancellation_reason}


@router.delete("/holidays/{holiday_id}", dependencies=[Depends(holiday_manager)])
def delete_holiday(
    holiday_id: int,
    reason: str = Query(..., min_length=1),
    user: User = Depends(holiday_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel a holiday via DELETE with query param reason."""
    return cancel_holiday(holiday_id, HolidayCancelInput(reason=reason), user, db)


@router.get("/leave-requests")
def leave_requests(
    status_: LeaveStatus | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(StudentLeaveRequest).where(StudentLeaveRequest.school_id == user.school_id)
    if status_ is not None:
        q = q.where(StudentLeaveRequest.status == status_)
    return [
        leave_svc.to_out(db, r)
        for r in db.scalars(q.order_by(StudentLeaveRequest.from_date.desc()))
    ]


@router.post("/leave-requests/{request_id}/decide", dependencies=[Depends(corrector)])
def decide(
    request_id: int,
    body: LeaveDecision,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(StudentLeaveRequest, request_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave request not found")
    return leave_svc.to_out(db, leave_svc.decide(db, row, user, body.approve, body.note))
