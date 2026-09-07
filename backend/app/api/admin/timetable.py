"""The timetable builder, workload view and substitution desk (§5.7.3)."""

from datetime import date as Date, time as Time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
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
)
from app.services import timetable as svc
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
    return {"id": row.id, "period_no": row.period_no}


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
    slot = svc.save_slot(db, user, **body.model_dump())
    return svc.slot_out(db, slot)


@router.put("/slots/{slot_id}", dependencies=[writer])
def update_slot(
    slot_id: int, body: SlotIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    if db.get(TimetableSlot, slot_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    slot = svc.save_slot(db, user, slot_id=slot_id, **body.model_dump())
    return svc.slot_out(db, slot)


@router.delete("/slots/{slot_id}", status_code=204, dependencies=[writer])
def delete_slot(
    slot_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> None:
    slot = db.get(TimetableSlot, slot_id)
    if slot is None or slot.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    db.delete(slot)
    db.commit()


@router.get("/workload")
def workload(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
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
