from pathlib import Path

p = Path("backend/app/api/admin/timetable.py")
content = p.read_text(encoding="utf-8")

# 1. Update import
old_import = "from sqlalchemy import select"
new_import = "from sqlalchemy import func, select"
if old_import in content:
    content = content.replace(old_import, new_import, 1)

# 2. Add PeriodUpdateIn
old_schema = """class PeriodIn(BaseModel):
    model_config = {"extra": "forbid"}

    period_no: int
    start_time: Time
    end_time: Time
    name: str | None = None
    is_break: bool = False"""

new_schema = """class PeriodIn(BaseModel):
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
    is_break: bool | None = None"""

if old_schema in content:
    content = content.replace(old_schema, new_schema, 1)

# 3. Add PUT and DELETE endpoints right after add_period
old_add_period = """    db.commit()
    return {"id": row.id, "period_no": row.period_no}"""

new_endpoints = """    db.commit()
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
    db.commit()"""

if old_add_period in content:
    content = content.replace(old_add_period, new_endpoints, 1)

p.write_text(content, encoding="utf-8")
print("Updated timetable.py with period update and delete endpoints.")
