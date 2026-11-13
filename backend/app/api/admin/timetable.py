"""The timetable builder, workload view and substitution desk (§5.7.3)."""

from datetime import date as Date, time as Time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AcademicYear,
    DayOfWeek,
    Employee,
    SchoolPeriod,
    Substitution,
    TimetableSlot,
    User,
    AuditAction,
)
from app.services import audit, timetable as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/timetable",
    tags=["timetable"],
    dependencies=[Depends(module_enabled("timetable"))],
)

reader = require_permission("timetable.slot.read", school_wide=True)
writer = Depends(require_permission("timetable.slot.write"))
cover = require_permission("timetable.substitution.manage", school_wide=True)


class PeriodIn(BaseModel):
    model_config = {"extra": "forbid"}

    period_no: int
    start_time: Time
    end_time: Time
    name: str | None = None
    is_break: bool = False


class PeriodUpdateIn(BaseModel):
    model_config = {"extra": "forbid"}

    period_no: int | None = None
    start_time: Time | None = None
    end_time: Time | None = None
    name: str | None = None
    is_break: bool | None = None


class SlotIn(BaseModel):
    model_config = {"extra": "forbid"}

    class_section_id: int
    day_of_week: DayOfWeek
    period_id: int
    subject_id: int
    teacher_id: int
    room: str | None = None
    override_reason: str | None = None


class SubstitutionIn(BaseModel):
    model_config = {"extra": "forbid"}

    slot_id: int
    date: Date
    substitute_teacher_id: int | None = None
    reason: str = Field(min_length=3, max_length=200)


@router.get("/periods")
def periods(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": p.id,
            "period_no": p.period_no,
            "start_time": p.start_time,
            "end_time": p.end_time,
            "name": p.name,
            "is_break": p.is_break,
        }
        for p in db.scalars(
            select(SchoolPeriod)
            .where(SchoolPeriod.school_id == user.school_id)
            .order_by(SchoolPeriod.period_no)
        )
    ]


@router.post("/periods", status_code=201, dependencies=[writer])
def add_period(
    body: PeriodIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    if body.end_time <= body.start_time:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A period must end after it starts"
        )
    if db.scalar(
        select(SchoolPeriod).where(
            SchoolPeriod.school_id == user.school_id,
            SchoolPeriod.period_no == body.period_no,
        )
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "That period number already exists")
    row = SchoolPeriod(school_id=user.school_id, **body.model_dump())
    db.add(row)
    db.commit()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="school_period",
        entity_id=row.id,
        action=AuditAction.create,
        after={
            "period_no": row.period_no,
            "start_time": str(row.start_time),
            "end_time": str(row.end_time),
            "name": row.name,
            "is_break": row.is_break,
        },
    )
    db.commit()
    return {"id": row.id, "period_no": row.period_no}


@router.put("/periods/{period_id}", dependencies=[writer])
def update_period(
    period_id: int,
    body: PeriodUpdateIn,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    period = db.get(SchoolPeriod, period_id)
    if period is None or period.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School period not found")

    start = body.start_time if body.start_time is not None else period.start_time
    end = body.end_time if body.end_time is not None else period.end_time
    if end <= start:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A period must end after it starts"
        )

    if body.period_no is not None and body.period_no != period.period_no:
        existing = db.scalar(
            select(SchoolPeriod).where(
                SchoolPeriod.school_id == user.school_id,
                SchoolPeriod.period_no == body.period_no,
                SchoolPeriod.id != period_id,
            )
        )
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "That period number already exists")
        period.period_no = body.period_no

    before_data = {
        "period_no": period.period_no,
        "start_time": str(period.start_time),
        "end_time": str(period.end_time),
        "name": period.name,
        "is_break": period.is_break,
    }

    if body.start_time is not None:
        period.start_time = body.start_time
    if body.end_time is not None:
        period.end_time = body.end_time
    if body.name is not None:
        period.name = body.name.strip() if body.name.strip() else None
    if body.is_break is not None:
        period.is_break = body.is_break

    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="school_period",
        entity_id=period.id,
        action=AuditAction.update,
        before=before_data,
        after={
            "period_no": period.period_no,
            "start_time": str(period.start_time),
            "end_time": str(period.end_time),
            "name": period.name,
            "is_break": period.is_break,
        },
    )
    db.commit()
    return {
        "id": period.id,
        "period_no": period.period_no,
        "start_time": period.start_time,
        "end_time": period.end_time,
        "name": period.name,
        "is_break": period.is_break,
    }


@router.delete("/periods/{period_id}", status_code=204, dependencies=[writer])
def delete_period(
    period_id: int,
    reason: str | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> None:
    period = db.get(SchoolPeriod, period_id)
    if period is None or period.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "School period not found")
    slots_count = db.scalar(
        select(func.count())
        .select_from(TimetableSlot)
        .where(TimetableSlot.period_id == period_id)
    ) or 0
    if slots_count > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot delete period with {slots_count} assigned timetable slots. Remove or reassign them first.",
        )
    before_data = {
        "period_no": period.period_no,
        "start_time": str(period.start_time),
        "end_time": str(period.end_time),
        "name": period.name,
        "is_break": period.is_break,
    }
    db.delete(period)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="school_period",
        entity_id=period_id,
        action=AuditAction.delete,
        before=before_data,
        reason=reason or "School period removed",
    )
    db.commit()


@router.get("/slots")
def slots(
    class_section_id: int | None = None,
    teacher_id: int | None = None,
    day_of_week: DayOfWeek | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.grid(db, user.school_id, class_section_id, teacher_id, day_of_week)


@router.post("/slots/check")
def check(body: SlotIn, user: User = Depends(reader), db: Session = Depends(get_db)) -> dict:
    """What would go wrong if this lesson were placed here.

    A separate read so a builder can colour a cell while the coordinator drags
    it, without writing anything (§5.7.9 wants live validation, not a
    validate-at-the-end button).
    """
    found = svc.conflicts(
        db,
        user.school_id,
        class_section_id=body.class_section_id,
        day_of_week=body.day_of_week,
        period_id=body.period_id,
        teacher_id=body.teacher_id,
        room=body.room,
    )
    return {"ok": not found, "conflicts": found}


@router.post("/slots", status_code=201, dependencies=[writer])
def create_slot(
    body: SlotIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    try:
        slot = svc.save_slot(db, user, **body.model_dump())
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Teacher or room is already booked for this time period",
        )
    return svc.slot_out(db, slot)


@router.put("/slots/{slot_id}", dependencies=[writer])
def update_slot(
    slot_id: int, body: SlotIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    # Ownership is proved inside save_slot(), which is where the write is.
    try:
        slot = svc.save_slot(db, user, slot_id=slot_id, **body.model_dump())
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Teacher or room is already booked for this time period",
        )
    return svc.slot_out(db, slot)


@router.post("/publish", dependencies=[writer])
def publish_timetable(
    class_section_id: int | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.publish_timetable(db, user.school_id, class_section_id)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="timetable",
        action=AuditAction.publish,
        after={"published": True, "count": count, "class_section_id": class_section_id},
    )
    db.commit()
    return {"published": True, "count": count}


@router.post("/unpublish", dependencies=[writer])
def unpublish_timetable(
    class_section_id: int | None = Query(None),
    reason: str | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.unpublish_timetable(db, user.school_id, class_section_id)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="timetable",
        action=AuditAction.status_change,
        after={"published": False, "count": count, "class_section_id": class_section_id},
        reason=reason or "Timetable reverted to draft",
    )
    db.commit()
    return {"published": False, "count": count}


@router.delete("/slots/{slot_id}", status_code=204, dependencies=[writer])
def delete_slot(
    slot_id: int,
    reason: str | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> None:
    slot = db.get(TimetableSlot, slot_id)
    if slot is None or slot.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    before_data = {
        "class_section_id": slot.class_section_id,
        "day_of_week": slot.day_of_week.value if hasattr(slot.day_of_week, "value") else str(slot.day_of_week),
        "period_id": slot.period_id,
        "subject_id": slot.subject_id,
        "teacher_id": slot.teacher_id,
        "room": slot.room,
    }
    db.delete(slot)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="timetable_slot",
        entity_id=slot_id,
        action=AuditAction.delete,
        before=before_data,
        reason=reason or "Timetable slot removed",
    )
    db.commit()


@router.get("/workload")
def workload(user: User = Depends(reader), db: Session = Depends(get_db)) -> dict:
    return svc.workload(db, user.school_id)


@router.get("/completeness")
def completeness(
    academic_year_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    year_id = academic_year_id
    if year_id is None:
        current = db.scalar(
            select(AcademicYear).where(
                AcademicYear.school_id == user.school_id, AcademicYear.is_current.is_(True)
            )
        )
        if current is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "No current academic year")
        year_id = current.id
    return svc.completeness(db, user.school_id, year_id)


@router.get("/day")
def day_plan(
    date: Date | None = None, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    """The day as it will actually run, substitutions applied."""
    return svc.day_plan(db, user.school_id, date or Date.today())


@router.get("/slots/{slot_id}/free-teachers")
def free_teachers(
    slot_id: int,
    date: Date | None = None,
    user: User = Depends(cover),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.free_teachers(db, user.school_id, slot_id, date or Date.today())


@router.post("/substitutions", status_code=201)
def arrange(
    body: SubstitutionIn, user: User = Depends(cover), db: Session = Depends(get_db)
) -> dict:
    row = svc.arrange(
        db,
        user,
        slot_id=body.slot_id,
        on=body.date,
        substitute_teacher_id=body.substitute_teacher_id,
        reason=body.reason,
    )
    return _sub_out(db, row)


@router.get("/substitutions")
def substitutions(
    date: Date | None = None, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    q = select(Substitution).where(Substitution.school_id == user.school_id)
    if date is not None:
        q = q.where(Substitution.date == date)
    return [_sub_out(db, s) for s in db.scalars(q.order_by(Substitution.date.desc()))]


def _sub_out(db: Session, row: Substitution) -> dict:
    slot = row.slot
    return {
        "id": row.id,
        "date": row.date,
        "slot_id": row.timetable_slot_id,
        "class_label": slot.class_section.label,
        "period": slot.period.period_no,
        "absent_teacher": db.get(Employee, row.absent_teacher_id).user.full_name,
        "substitute_teacher": (
            db.get(Employee, row.substitute_teacher_id).user.full_name
            if row.substitute_teacher_id
            else None
        ),
        "status": row.status,
        "reason": row.reason,
    }
