"""Vehicles, routes, stops, fee slabs and who rides which bus (§5.6).

Thin, like every other router here: the two refusals that matter — seating
capacity and expired compliance papers — live in `services/transport.py`, so a
future mobile or public caller inherits them rather than reimplementing them.

Behind `module_enabled("transport")` as well as its permissions. §0.2c makes
transport a module a school buys, and a switch the UI honours while the API
does not is not a switch.
"""

from datetime import date as Date, time as Time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    AuditAction,
    Enrolment,
    EnrolmentStatus,
    Route,
    RouteStatus,
    RouteStop,
    Student,
    TransportAssignment,
    TransportAssignmentStatus,
    TransportDirection,
    TransportFeeSlab,
    User,
    Vehicle,
    VehicleOwnership,
    VehicleStatus,
)
from app.services import audit, transport as svc
from app.services.common import section_labels
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/transport",
    tags=["admin"],
    dependencies=[Depends(module_enabled("transport"))],
)
reader = require_permission("transport.setup.read", school_wide=True)
setup = require_permission("transport.setup.write", school_wide=True)
desk_reader = require_permission("transport.assignment.read", school_wide=True)
desk = require_permission("transport.assignment.manage", school_wide=True)


class VehicleIn(BaseModel):
    registration_no: str = Field(min_length=4, max_length=20)
    make_model: str | None = Field(default=None, max_length=60)
    capacity: int = Field(gt=0, le=100)
    ownership: VehicleOwnership = VehicleOwnership.owned
    gps_device_id: str | None = Field(default=None, max_length=40)


class VehicleStatusIn(BaseModel):
    status: VehicleStatus
    reason: str = Field(min_length=3, max_length=500)


class SlabIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    monthly_amount: Decimal = Field(ge=0)
    is_active: bool = True


class RouteIn(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=80)
    distance_km: Decimal | None = Field(default=None, ge=0)


class CrewIn(BaseModel):
    """Every field optional and three-valued: absent means "leave it alone",
    null means "take it off". A PATCH that cannot say "remove the attendant"
    would need a second endpoint to do it."""

    vehicle_id: int | None = None
    driver_id: int | None = None
    attendant_id: int | None = None
    clear: list[str] = Field(default_factory=list)


class RouteStatusIn(BaseModel):
    status: RouteStatus


class StopIn(BaseModel):
    sequence: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=80)
    landmark: str | None = Field(default=None, max_length=120)
    pickup_time: Time
    drop_time: Time | None = None
    fee_slab_id: int | None = None


class AssignmentIn(BaseModel):
    student_id: int
    route_stop_id: int
    direction: TransportDirection = TransportDirection.both
    start_date: Date


class AssignmentStatusIn(BaseModel):
    status: TransportAssignmentStatus
    end_date: Date | None = None
    reason: str | None = Field(default=None, max_length=500)


def _vehicle(db: Session, user: User, vehicle_id: int) -> Vehicle:
    row = db.get(Vehicle, vehicle_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    return row


def _route(db: Session, user: User, route_id: int) -> Route:
    row = db.get(Route, route_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Route not found")
    return row


def _vehicle_out(v: Vehicle) -> dict:
    return {
        "id": v.id,
        "registration_no": v.registration_no,
        "make_model": v.make_model,
        "capacity": v.capacity,
        "ownership": v.ownership.value,
        "status": v.status.value,
        "gps_device_id": v.gps_device_id,
    }


def _route_out(db: Session, r: Route) -> dict:
    return {
        "id": r.id,
        "code": r.code,
        "name": r.name,
        "status": r.status.value,
        "distance_km": r.distance_km,
        "vehicle_id": r.vehicle_id,
        "driver_id": r.driver_id,
        "attendant_id": r.attendant_id,
        "stops": [
            {
                "id": s.id,
                "sequence": s.sequence,
                "name": s.name,
                "landmark": s.landmark,
                "pickup_time": s.pickup_time,
                "drop_time": s.drop_time,
                "fee_slab_id": s.fee_slab_id,
                "monthly_amount": s.fee_slab.monthly_amount if s.fee_slab else None,
            }
            for s in r.stops
        ],
        **svc.seats(db, r),
    }


# --- vehicles ---------------------------------------------------------------


@router.get("/vehicles")
def vehicles(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(Vehicle)
        .where(Vehicle.school_id == user.school_id)
        .order_by(Vehicle.registration_no)
    )
    return [_vehicle_out(v) for v in rows]


@router.post("/vehicles", status_code=status.HTTP_201_CREATED)
def add_vehicle(
    body: VehicleIn, user: User = Depends(setup), db: Session = Depends(get_db)
) -> dict:
    row = Vehicle(school_id=user.school_id, **body.model_dump())
    db.add(row)
    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="vehicle",
        entity_id=row.id,
        action=AuditAction.create,
        after=audit.snapshot(row, ["registration_no", "capacity", "ownership"]),
    )
    db.commit()
    return _vehicle_out(row)


@router.get("/vehicles/{vehicle_id}/compliance")
def vehicle_compliance(
    vehicle_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """What is missing before this bus may run. Empty `gaps` is roadworthy."""
    v = _vehicle(db, user, vehicle_id)
    from app.models import OwnerType

    return {
        "vehicle": _vehicle_out(v),
        "gaps": svc.paper_gaps(
            db, user.school_id, OwnerType.vehicle, v.id, svc.VEHICLE_PAPERS
        ),
    }


@router.patch("/vehicles/{vehicle_id}/status")
def vehicle_status(
    vehicle_id: int,
    body: VehicleStatusIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    """Ground a bus, send it for service, or retire it.

    Audited with a reason like any other status change. It does not cascade:
    the routes it is on stay as they are and simply stop being roadworthy,
    which is what makes the refusal visible rather than silently rewriting a
    school's timetable at 6am.
    """
    v = _vehicle(db, user, vehicle_id)
    before = v.status.value
    v.status = body.status
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="vehicle",
        entity_id=v.id,
        action=AuditAction.status_change,
        before={"status": before},
        after={"status": v.status.value},
        reason=body.reason,
    )
    db.commit()
    return _vehicle_out(v)


# --- fee slabs --------------------------------------------------------------


@router.get("/slabs")
def slabs(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(TransportFeeSlab)
        .where(TransportFeeSlab.school_id == user.school_id)
        .order_by(TransportFeeSlab.monthly_amount)
    )
    return [
        {
            "id": s.id,
            "name": s.name,
            "monthly_amount": s.monthly_amount,
            "is_active": s.is_active,
        }
        for s in rows
    ]


@router.post("/slabs", status_code=status.HTTP_201_CREATED)
def add_slab(
    body: SlabIn, user: User = Depends(setup), db: Session = Depends(get_db)
) -> dict:
    row = TransportFeeSlab(school_id=user.school_id, **body.model_dump())
    db.add(row)
    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="transport_fee_slab",
        entity_id=row.id,
        action=AuditAction.create,
        after=audit.snapshot(row, ["name", "monthly_amount"]),
    )
    db.commit()
    return {"id": row.id, "name": row.name, "monthly_amount": row.monthly_amount}


# --- routes -----------------------------------------------------------------


@router.get("/routes")
def routes(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(Route).where(Route.school_id == user.school_id).order_by(Route.code)
    )
    return [_route_out(db, r) for r in rows]


@router.post("/routes", status_code=status.HTTP_201_CREATED)
def add_route(
    body: RouteIn, user: User = Depends(setup), db: Session = Depends(get_db)
) -> dict:
    row = Route(school_id=user.school_id, **body.model_dump())
    db.add(row)
    db.flush()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="route",
        entity_id=row.id,
        action=AuditAction.create,
        after=audit.snapshot(row, ["code", "name"]),
    )
    db.commit()
    return _route_out(db, row)


@router.put("/routes/{route_id}/stops")
def put_stops(
    route_id: int,
    body: list[StopIn],
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    r = _route(db, user, route_id)
    svc.set_stops(db, r, [s.model_dump() for s in body], user)
    db.commit()
    return _route_out(db, r)


@router.patch("/routes/{route_id}/crew")
def crew(
    route_id: int,
    body: CrewIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    r = _route(db, user, route_id)
    fields: dict = {}
    for name in ("vehicle_id", "driver_id", "attendant_id"):
        if name in body.clear:
            fields[name] = None
        elif getattr(body, name) is not None:
            fields[name] = getattr(body, name)
    svc.set_crew(db, r, user, **fields)
    db.commit()
    return _route_out(db, r)


@router.patch("/routes/{route_id}/status")
def route_status(
    route_id: int,
    body: RouteStatusIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    r = _route(db, user, route_id)
    svc.set_status(db, r, body.status, user)
    db.commit()
    return _route_out(db, r)


@router.get("/routes/{route_id}/roadworthiness")
def roadworthiness(
    route_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """Every reason this route may not carry children, in one call.

    A read, so it reports rather than refuses — the setup screen shows all four
    expired papers at once instead of surfacing them one failed save at a time.
    """
    r = _route(db, user, route_id)
    gaps = svc.roadworthiness(db, r)
    return {"route_id": r.id, "code": r.code, "roadworthy": not gaps, "gaps": gaps}


@router.get("/routes/{route_id}/students")
def route_students(
    route_id: int, user: User = Depends(desk_reader), db: Session = Depends(get_db)
) -> list[dict]:
    """The list a driver actually needs (§5.6.10): who is at which stop, in the
    order the bus reaches them."""
    r = _route(db, user, route_id)
    rows = db.execute(
        select(TransportAssignment, RouteStop, Student, Enrolment)
        .join(RouteStop, RouteStop.id == TransportAssignment.route_stop_id)
        .join(Enrolment, Enrolment.id == TransportAssignment.enrolment_id)
        .join(Student, Student.id == Enrolment.student_id)
        .where(
            RouteStop.route_id == r.id,
            TransportAssignment.status.in_(svc.LIVE),
        )
        .order_by(RouteStop.sequence, Student.id)
    ).all()
    labels = section_labels(db, user.school_id)
    return [
        {
            "assignment_id": a.id,
            "student_id": s.id,
            "name": s.user.full_name,
            "admission_no": s.admission_no,
            "class_label": labels.get(e.class_section_id, ""),
            "stop": stop.name,
            "sequence": stop.sequence,
            "pickup_time": stop.pickup_time,
            "drop_time": stop.drop_time,
            "direction": a.direction.value,
            "status": a.status.value,
        }
        for a, stop, s, e in rows
    ]


# --- assignments ------------------------------------------------------------


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def assign(
    body: AssignmentIn, user: User = Depends(desk), db: Session = Depends(get_db)
) -> dict:
    enrolment = db.scalar(
        select(Enrolment).where(
            Enrolment.school_id == user.school_id,
            Enrolment.student_id == body.student_id,
            Enrolment.status == EnrolmentStatus.active,
        )
    )
    if enrolment is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "That student has no active enrolment"
        )
    stop = db.get(RouteStop, body.route_stop_id)
    if stop is None or stop.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stop not found")

    row = svc.assign(
        db,
        actor=user,
        enrolment=enrolment,
        stop=stop,
        direction=body.direction,
        start_date=body.start_date,
    )
    db.commit()
    return {
        "id": row.id,
        "student_id": body.student_id,
        "route_stop_id": row.route_stop_id,
        "direction": row.direction.value,
        "start_date": row.start_date,
        "status": row.status.value,
    }


@router.patch("/assignments/{assignment_id}")
def assignment_status(
    assignment_id: int,
    body: AssignmentStatusIn,
    user: User = Depends(desk),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(TransportAssignment, assignment_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    svc.set_assignment_status(
        db,
        actor=user,
        row=row,
        new_status=body.status,
        end_date=body.end_date,
        reason=body.reason,
    )
    db.commit()
    return {
        "id": row.id,
        "status": row.status.value,
        "start_date": row.start_date,
        "end_date": row.end_date,
    }


# --- money and compliance reporting -----------------------------------------


@router.get("/charges")
def charges(
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
    user: User = Depends(desk_reader),
    db: Session = Depends(get_db),
) -> dict:
    """What the bus will add to next month's invoices, before it is billed.

    The same function the fee run calls, not a second one that computes it
    differently — reconciliation is the rule §5.10.9 is most insistent about.
    """
    found = svc.charges_for_month(db, user.school_id, year, month)
    return {
        "year": year,
        "month": month,
        "students": len(found),
        "total": sum(found.values(), Decimal(0)),
    }


@router.get("/expiring")
def expiring(
    within_days: int = Query(default=svc.EXPIRY_HORIZON_DAYS, ge=1, le=365),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """The compliance dashboard of §5.6.10, already-lapsed papers included: a
    permit that expired last week is more urgent than one expiring next month,
    not less."""
    return svc.expiring_papers(db, user.school_id, within_days)
