"""Admission cycle setup and the enquiry register (screens 2-4 and 17 of
ERP_BLUEPRINT §5.1.3)."""

from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AcademicYear,
    AdmissionCycle,
    AdmissionCycleStatus,
    CycleClassConfig,
    Enquiry,
    EnquiryChannel,
    EnquiryInteraction,
    EnquirySource,
    EnquiryStatus,
    User,
)
from app.services import admission as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

cycle_reader = require_permission("admission.cycle.read", school_wide=True)
enquiry_reader = require_permission("admission.enquiry.read", school_wide=True)
cycle_writer = Depends(require_permission("admission.cycle.write"))
enquiry_writer = Depends(require_permission("admission.enquiry.write"))


class CycleCreate(BaseModel):
    model_config = {"extra": "forbid"}

    academic_year_id: int
    name: str
    starts_on: Date | None = None
    ends_on: Date | None = None
    application_fee: Decimal = Decimal("0")
    late_fee: Decimal = Decimal("0")
    allow_online_applications: bool = True
    admission_fee_refund_policy: str | None = None


class CycleUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    status: AdmissionCycleStatus | None = None
    starts_on: Date | None = None
    ends_on: Date | None = None
    application_fee: Decimal | None = None
    late_fee: Decimal | None = None
    allow_online_applications: bool | None = None
    admission_fee_refund_policy: str | None = None


class ClassConfigInput(BaseModel):
    model_config = {"extra": "forbid"}

    class_name: str
    stream: str | None = None
    total_seats: int = Field(ge=0)
    reserved_seats: dict[str, int] | None = None
    age_on: Date | None = None
    min_age_years: Decimal | None = None
    max_age_years: Decimal | None = None
    requires_test: bool = False
    requires_interview: bool = False
    required_document_codes: list[str] | None = None


class EnquiryCreate(BaseModel):
    """Deliberately small. Screen 3 is a receptionist on the phone with sixty
    seconds; everything but a name and a number can arrive later."""

    model_config = {"extra": "forbid"}

    enquirer_name: str
    mobile: str
    cycle_id: int | None = None
    email: str | None = None
    child_name: str | None = None
    child_dob: Date | None = None
    class_of_interest: str | None = None
    source: EnquirySource = EnquirySource.walk_in
    assigned_to: int | None = None
    next_follow_up_on: Date | None = None


class InteractionCreate(BaseModel):
    model_config = {"extra": "forbid"}

    channel: EnquiryChannel
    notes: str | None = None
    outcome: EnquiryStatus | None = None
    next_follow_up_on: Date | None = None


def _cycle_out(c: AdmissionCycle) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "academic_year_id": c.academic_year_id,
        "academic_year": c.academic_year.code,
        "status": c.status,
        "starts_on": c.starts_on,
        "ends_on": c.ends_on,
        "application_fee": c.application_fee,
        "late_fee": c.late_fee,
        "allow_online_applications": c.allow_online_applications,
        "admission_fee_refund_policy": c.admission_fee_refund_policy,
    }


def _config_out(c: CycleClassConfig) -> dict:
    return {
        "id": c.id,
        "class_name": c.class_name,
        "stream": c.stream,
        "total_seats": c.total_seats,
        "reserved_seats": c.reserved_seats or {},
        "age_on": c.age_on,
        "min_age_years": c.min_age_years,
        "max_age_years": c.max_age_years,
        "requires_test": c.requires_test,
        "requires_interview": c.requires_interview,
        "required_document_codes": c.required_document_codes or [],
    }


def _enquiry_out(e: Enquiry) -> dict:
    return {
        "id": e.id,
        "cycle_id": e.cycle_id,
        "enquirer_name": e.enquirer_name,
        "mobile": e.mobile,
        "email": e.email,
        "child_name": e.child_name,
        "child_dob": e.child_dob,
        "class_of_interest": e.class_of_interest,
        "source": e.source,
        "status": e.status,
        "assigned_to": e.assigned_to,
        "next_follow_up_on": e.next_follow_up_on,
        "converted_application_id": e.converted_application_id,
    }


# --------------------------------------------------------------------- cycles


@router.get("/cycles")
def list_cycles(
    user: User = Depends(cycle_reader), db: Session = Depends(get_db)
) -> list[dict]:
    return [
        _cycle_out(c)
        for c in db.scalars(
            select(AdmissionCycle)
            .where(AdmissionCycle.school_id == user.school_id)
            .order_by(AdmissionCycle.id.desc())
        )
    ]


@router.post("/cycles", status_code=status.HTTP_201_CREATED, dependencies=[cycle_writer])
def create_cycle(
    body: CycleCreate, user: User = Depends(cycle_reader), db: Session = Depends(get_db)
) -> dict:
    year = db.get(AcademicYear, body.academic_year_id)
    if year is None or year.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    cycle = AdmissionCycle(school_id=user.school_id, **body.model_dump())
    db.add(cycle)
    db.commit()
    return _cycle_out(cycle)


@router.patch("/cycles/{cycle_id}", dependencies=[cycle_writer])
def update_cycle(
    cycle_id: int,
    body: CycleUpdate,
    user: User = Depends(cycle_reader),
    db: Session = Depends(get_db),
) -> dict:
    cycle = svc.cycle_for(db, user.school_id, cycle_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cycle, field, value)
    db.commit()
    return _cycle_out(cycle)


@router.get("/cycles/{cycle_id}/classes")
def list_class_config(
    cycle_id: int, user: User = Depends(cycle_reader), db: Session = Depends(get_db)
) -> list[dict]:
    svc.cycle_for(db, user.school_id, cycle_id)
    return [
        _config_out(c)
        for c in db.scalars(
            select(CycleClassConfig)
            .where(CycleClassConfig.cycle_id == cycle_id)
            .order_by(CycleClassConfig.class_name, CycleClassConfig.stream)
        )
    ]


@router.put("/cycles/{cycle_id}/classes", dependencies=[cycle_writer])
def set_class_config(
    cycle_id: int,
    body: ClassConfigInput,
    user: User = Depends(cycle_reader),
    db: Session = Depends(get_db),
) -> dict:
    """Upsert: seat counts get revised repeatedly during a cycle, and a school
    should not have to know whether this class was configured already."""
    svc.cycle_for(db, user.school_id, cycle_id)
    reserved = body.reserved_seats or {}
    if sum(reserved.values()) > body.total_seats:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Reserved seats exceed the total for this class",
        )
    config = svc.class_config(db, cycle_id, body.class_name, body.stream)
    if config is None:
        config = CycleClassConfig(
            school_id=user.school_id, cycle_id=cycle_id, **body.model_dump()
        )
        db.add(config)
    else:
        for field, value in body.model_dump().items():
            setattr(config, field, value)
    db.commit()
    return _config_out(config)


# ------------------------------------------------------------------ enquiries


@router.get("/enquiries")
def list_enquiries(
    cycle_id: int | None = None,
    status_filter: EnquiryStatus | None = Query(None, alias="status"),
    due_by: Date | None = Query(
        None, description="Only enquiries whose follow-up is due on or before this date"
    ),
    q: str | None = None,
    user: User = Depends(enquiry_reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(Enquiry).where(Enquiry.school_id == user.school_id)
    if cycle_id is not None:
        stmt = stmt.where(Enquiry.cycle_id == cycle_id)
    if status_filter is not None:
        stmt = stmt.where(Enquiry.status == status_filter)
    if due_by is not None:
        stmt = stmt.where(
            Enquiry.next_follow_up_on.is_not(None), Enquiry.next_follow_up_on <= due_by
        )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Enquiry.enquirer_name.ilike(like)
            | Enquiry.mobile.ilike(like)
            | Enquiry.child_name.ilike(like)
        )
    return [_enquiry_out(e) for e in db.scalars(stmt.order_by(Enquiry.id.desc()))]


@router.post("/enquiries", status_code=status.HTTP_201_CREATED, dependencies=[enquiry_writer])
def create_enquiry(
    body: EnquiryCreate,
    user: User = Depends(enquiry_reader),
    db: Session = Depends(get_db),
) -> dict:
    cycle = (
        svc.cycle_for(db, user.school_id, body.cycle_id)
        if body.cycle_id is not None
        else svc.open_cycle(db, user.school_id)
    )
    enquiry = Enquiry(
        school_id=user.school_id,
        **{**body.model_dump(exclude={"cycle_id"}), "cycle_id": cycle.id},
    )
    db.add(enquiry)
    db.commit()
    return _enquiry_out(enquiry)


@router.get("/enquiries/{enquiry_id}")
def enquiry_detail(
    enquiry_id: int, user: User = Depends(enquiry_reader), db: Session = Depends(get_db)
) -> dict:
    enquiry = db.get(Enquiry, enquiry_id)
    if enquiry is None or enquiry.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enquiry not found")
    log = db.scalars(
        select(EnquiryInteraction)
        .where(EnquiryInteraction.enquiry_id == enquiry_id)
        .order_by(EnquiryInteraction.occurred_at.desc())
    )
    return {
        **_enquiry_out(enquiry),
        "interactions": [
            {
                "id": i.id,
                "occurred_at": i.occurred_at,
                "channel": i.channel,
                "notes": i.notes,
                "outcome": i.outcome,
                "by_user_id": i.by_user_id,
            }
            for i in log
        ],
    }


@router.post(
    "/enquiries/{enquiry_id}/interactions",
    status_code=status.HTTP_201_CREATED,
    dependencies=[enquiry_writer],
)
def log_interaction(
    enquiry_id: int,
    body: InteractionCreate,
    user: User = Depends(enquiry_reader),
    db: Session = Depends(get_db),
) -> dict:
    enquiry = db.get(Enquiry, enquiry_id)
    if enquiry is None or enquiry.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enquiry not found")
    svc.log_interaction(
        db,
        enquiry,
        actor=user,
        channel=body.channel,
        notes=body.notes,
        outcome=body.outcome,
        next_follow_up_on=body.next_follow_up_on,
    )
    return enquiry_detail(enquiry_id, user, db)


@router.get("/cycles/{cycle_id}/funnel")
def funnel(
    cycle_id: int, user: User = Depends(enquiry_reader), db: Session = Depends(get_db)
) -> dict:
    svc.cycle_for(db, user.school_id, cycle_id)
    return {"enquiries": svc.funnel(db, user.school_id, cycle_id)}


@router.delete(
    "/enquiries/{enquiry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[enquiry_writer],
)
def mark_invalid(
    enquiry_id: int,
    reason: str = Query(..., min_length=3),
    user: User = Depends(enquiry_reader),
    db: Session = Depends(get_db),
) -> Response:
    """Enquiries are closed as invalid, never deleted: a wrong number is still
    a data point about where the enquiries are coming from."""
    enquiry = db.get(Enquiry, enquiry_id)
    if enquiry is None or enquiry.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enquiry not found")
    svc.log_interaction(
        db,
        enquiry,
        actor=user,
        channel=EnquiryChannel.phone,
        notes=reason,
        outcome=EnquiryStatus.invalid,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
