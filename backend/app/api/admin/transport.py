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
    # Same floor as VehicleStatusIn's. Grounding a bus already demanded a
    # reason; suspending the route those children ride did not.
    reason: str = Field(min_length=3, max_length=500)


class StopIn(BaseModel):
    sequence: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=120)
    pickup_time: Time
    drop_time: Time | None = None
    fee_slab_id: int | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class AssignmentIn(BaseModel):
    student_id: int
    route_stop_id: int
    direction: TransportDirection = TransportDirection.both
    start_date: Date


class AssignmentStatusIn(BaseModel):
    status: TransportAssignmentStatus
    end_date: Date | None = None
    reason: str | None = Field(default=None, max_length=500)


class VehicleUpdateIn(BaseModel):
    make_model: str | None = Field(default=None, max_length=60)
    capacity: int = Field(gt=0, le=100)
    ownership: VehicleOwnership = VehicleOwnership.owned
    gps_device_id: str | None = Field(default=None, max_length=40)


class RouteUpdateIn(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=80)
    distance_km: Decimal | None = Field(default=None, ge=0)


class SlabUpdateIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    monthly_amount: Decimal = Field(ge=0)
    is_active: bool = True


class TransferIn(BaseModel):
    new_route_stop_id: int
    reason: str = Field(min_length=3, max_length=500)
    start_date: Date = Field(default_factory=Date.today)
    direction: TransportDirection = TransportDirection.both


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
                "address": s.address,
                "landmark": s.landmark,
                "pickup_time": s.pickup_time,
                "drop_time": s.drop_time,
                "fee_slab_id": s.fee_slab_id,
                "monthly_amount": s.fee_slab.monthly_amount if s.fee_slab else None,
                "latitude": s.latitude,
                "longitude": s.longitude,
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


@router.put("/vehicles/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    body: VehicleUpdateIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    """Update vehicle specifications: make/model, capacity, ownership, and GPS tracker ID."""
    v = _vehicle(db, user, vehicle_id)
    # Check if capacity reduction clashes with existing assignments on active routes
    for r in db.scalars(select(Route).where(Route.vehicle_id == v.id, Route.school_id == user.school_id)):
        taken = svc.seats(db, r)["taken"]
        if taken > body.capacity:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Cannot reduce capacity to {body.capacity}: Route {r.code} already has {taken} riders assigned",
            )
    v.make_model = body.make_model
    v.capacity = body.capacity
    v.ownership = body.ownership
    v.gps_device_id = body.gps_device_id
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


@router.patch("/slabs/{slab_id}")
def update_slab(
    slab_id: int,
    body: SlabUpdateIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    slab = db.get(TransportFeeSlab, slab_id)
    if slab is None or slab.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fee slab not found")
    slab.name = body.name
    slab.monthly_amount = body.monthly_amount
    slab.is_active = body.is_active
    db.commit()
    return {
        "id": slab.id,
        "name": slab.name,
        "monthly_amount": slab.monthly_amount,
        "is_active": slab.is_active,
    }


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


@router.put("/routes/{route_id}")
def update_route(
    route_id: int,
    body: RouteUpdateIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    """Update route code, name, or total distance."""
    r = _route(db, user, route_id)
    if body.code != r.code:
        clash = db.scalar(
            select(Route).where(
                Route.school_id == user.school_id,
                Route.code == body.code,
                Route.id != r.id,
            )
        )
        if clash is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Route code {body.code} is already in use"
            )
    r.code = body.code
    r.name = body.name
    r.distance_km = body.distance_km
    db.commit()
    return _route_out(db, r)


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


class StopLocationIn(BaseModel):
    model_config = {"extra": "forbid"}

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str | None = Field(default=None, max_length=255)


@router.patch("/stops/{stop_id}/location")
def stop_location(
    stop_id: int,
    body: StopLocationIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    """Pin one stop, in place.

    Deliberately not folded into `PUT /routes/{id}/stops`. That route replaces
    the whole list and `set_stops` rebuilds every RouteStop as a new row, so it
    cannot preserve a stop id - and because `StopIn` carries no `id`, its
    "children are assigned here" guard sees an empty keep-set and refuses
    outright on any route with riders. Pinning a stop on a running route is the
    ordinary case, so it gets a route that updates one row and leaves the
    assignments pointing where they already point.
    """
    stop = db.get(RouteStop, stop_id)
    if stop is None or stop.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stop not found")
    stop.latitude = body.latitude
    stop.longitude = body.longitude
    if body.address is not None:
        stop.address = body.address
    db.commit()
    return {
        "id": stop.id,
        "name": stop.name,
        "sequence": stop.sequence,
        "address": stop.address,
        "latitude": stop.latitude,
        "longitude": stop.longitude,
    }


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
    svc.set_status(db, r, body.status, user, reason=body.reason)
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


@router.get("/requests")
def requests(
    user: User = Depends(desk_reader), db: Session = Depends(get_db)
) -> list[dict]:
    """Families who asked for the bus on their admission form and have no seat.

    `transport_required` has been on every application since Part 2 and read by
    nothing. It seeds this queue rather than an assignment: the form says a
    family wants transport, never which stop, and choosing one for them off a
    postal address would be a guess about a child's walk to the bus.
    """
    return svc.awaiting_assignment(db, user.school_id)


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


# --- Plan 1 & 2 Upgrades: Geocoding, Fleet Crew, Allocation & Rosters -------


@router.get("/geocode")
def geocode(
    address: str = Query(min_length=1),
    user: User = Depends(reader),
) -> dict:
    """Address-first geocoder resolving addresses to internal coordinates."""
    from app.services.geocoding import geocode_address

    return geocode_address(address)


@router.get("/crew")
def transport_crew(
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Staff available to crew a bus (drivers and attendants) with document compliance status."""
    from datetime import date
    from app.models import Document, DocumentType, Employee, OwnerType

    stmt = (
        select(Employee)
        .join(User, User.id == Employee.user_id)
        .where(Employee.school_id == user.school_id)
        .order_by(Employee.employee_code)
    )
    all_emps = db.scalars(stmt).all()

    today = date.today()
    out = []
    for emp in all_emps:
        desig = (emp.designation or "").lower()
        dept_code = emp.department.code if emp.department else ""
        if (
            "driver" in desig
            or "attendant" in desig
            or "transport" in desig
            or dept_code == "TRA"
        ):
            docs = db.execute(
                select(Document, DocumentType)
                .join(DocumentType, DocumentType.id == Document.document_type_id)
                .where(
                    Document.school_id == user.school_id,
                    Document.owner_type == OwnerType.employee,
                    Document.owner_id == emp.id,
                    Document.deleted_at.is_(None),
                )
            ).all()
            papers_info = []
            has_license = False
            has_pv = False
            for d, dt in docs:
                code = dt.code if dt else ""
                days_left = (d.expires_on - today).days if d.expires_on else None
                if code == "driving_licence":
                    has_license = True
                elif code == "police_verification":
                    has_pv = True
                papers_info.append(
                    {
                        "code": code,
                        "name": dt.name if dt else code,
                        "expires_on": str(d.expires_on) if d.expires_on else None,
                        "days_left": days_left,
                        "is_expired": days_left is not None and days_left < 0,
                    }
                )
            out.append(
                {
                    "id": emp.id,
                    "employee_code": emp.employee_code,
                    "name": emp.user.full_name,
                    "phone": emp.user.phone,
                    "designation": emp.designation,
                    "department": dept_code,
                    "has_driving_licence": has_license,
                    "has_police_verification": has_pv,
                    "papers": papers_info,
                }
            )
    return out


@router.get("/students/search")
def search_students(
    q: str = Query(default="", min_length=0),
    user: User = Depends(desk_reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Search enrolled students for transport allocation without exposing People module."""
    from app.services.geocoding import geocode_address

    labels = section_labels(db, user.school_id)
    query = (
        select(Student, Enrolment)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .join(User, User.id == Student.user_id)
        .where(
            Student.school_id == user.school_id,
            Enrolment.status == EnrolmentStatus.active,
        )
    )
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            (User.full_name.ilike(term)) | (Student.admission_no.ilike(term))
        )
    query = query.order_by(Student.admission_no).limit(50)

    results = db.execute(query).all()
    out = []
    for s, e in results:
        curr = db.scalar(
            select(TransportAssignment).where(
                TransportAssignment.enrolment_id == e.id,
                TransportAssignment.status.in_(svc.LIVE),
            )
        )
        curr_info = None
        if curr:
            curr_info = {
                "assignment_id": curr.id,
                "route_id": curr.route_stop.route_id,
                "route_code": curr.route_stop.route.code,
                "route_name": curr.route_stop.route.name,
                "stop_id": curr.route_stop_id,
                "stop_name": curr.route_stop.name,
                "direction": curr.direction.value,
                "status": curr.status.value,
                "start_date": str(curr.start_date),
            }

        addr = s.address or s.user.address or ""
        geo = geocode_address(addr) if addr else None

        out.append(
            {
                "student_id": s.id,
                "enrolment_id": e.id,
                "name": s.user.full_name,
                "admission_no": s.admission_no,
                "class_label": labels.get(e.class_section_id, ""),
                "address": addr,
                "phone": s.user.phone,
                "latitude": geo["latitude"] if geo else None,
                "longitude": geo["longitude"] if geo else None,
                "is_approximate": geo["is_approximate"] if geo else True,
                "current_assignment": curr_info,
            }
        )
    return out


@router.get("/stops/nearby")
def nearby_stops(
    address: str | None = Query(default=None),
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    user: User = Depends(desk_reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Find and rank all active route stops by approximate distance from a student's address or coordinates."""
    from app.services.geocoding import geocode_address, haversine_distance_km

    target_lat = lat
    target_lon = lon
    resolved_address = address or ""

    if (target_lat is None or target_lon is None) and address:
        geo = geocode_address(address)
        target_lat = geo["latitude"]
        target_lon = geo["longitude"]
        resolved_address = geo["address"]

    routes = db.scalars(
        select(Route).where(
            Route.school_id == user.school_id, Route.status == RouteStatus.active
        )
    ).all()

    all_stops = []
    for r in routes:
        vehicle = db.get(Vehicle, r.vehicle_id) if r.vehicle_id else None
        capacity = vehicle.capacity if vehicle else 0
        seats = svc.seats(db, r)

        for stop in r.stops:
            dist = None
            if (
                target_lat is not None
                and target_lon is not None
                and stop.latitude is not None
                and stop.longitude is not None
            ):
                dist = haversine_distance_km(
                    target_lat, target_lon, stop.latitude, stop.longitude
                )

            all_stops.append(
                {
                    "stop_id": stop.id,
                    "stop_name": stop.name,
                    "stop_address": stop.address or stop.landmark or "",
                    "landmark": stop.landmark,
                    "sequence": stop.sequence,
                    "pickup_time": str(stop.pickup_time)[:5] if stop.pickup_time else "",
                    "drop_time": str(stop.drop_time)[:5] if stop.drop_time else "",
                    "route_id": r.id,
                    "route_code": r.code,
                    "route_name": r.name,
                    "vehicle_registration": vehicle.registration_no if vehicle else None,
                    "vehicle_capacity": capacity,
                    "seats_taken": seats["taken"],
                    "seats_free": seats["free"],
                    "has_capacity": (seats["free"] or 0) > 0,
                    "fee_slab_name": stop.fee_slab.name if stop.fee_slab else None,
                    "monthly_amount": stop.fee_slab.monthly_amount if stop.fee_slab else None,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "distance_km": dist,
                }
            )

    all_stops.sort(
        key=lambda x: (
            x["distance_km"] if x["distance_km"] is not None else 9999.0,
            x["sequence"],
        )
    )
    return all_stops


@router.post("/assignments/{assignment_id}/transfer")
def transfer_assignment(
    assignment_id: int,
    body: TransferIn,
    user: User = Depends(desk),
    db: Session = Depends(get_db),
) -> dict:
    """Transfer an existing transport assignment to a new stop/route with mandatory reason."""
    curr = db.get(TransportAssignment, assignment_id)
    if curr is None or curr.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    if curr.status is TransportAssignmentStatus.ended:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Cannot transfer an already ended assignment"
        )

    new_stop = db.get(RouteStop, body.new_route_stop_id)
    if new_stop is None or new_stop.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target stop not found")

    enrolment = db.get(Enrolment, curr.enrolment_id)
    if enrolment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")

    # 1. End current assignment with transfer reason
    end_reason = f"Transferred to {new_stop.name}: {body.reason}"
    svc.set_assignment_status(
        db,
        actor=user,
        row=curr,
        new_status=TransportAssignmentStatus.ended,
        end_date=body.start_date,
        reason=end_reason,
    )

    # 2. Create new assignment on the new stop
    new_row = svc.assign(
        db,
        actor=user,
        enrolment=enrolment,
        stop=new_stop,
        direction=body.direction,
        start_date=body.start_date,
    )
    try:
        svc.set_assignment_status(
            db,
            actor=user,
            row=new_row,
            new_status=TransportAssignmentStatus.active,
        )
    except Exception:
        pass  # If route is planned/suspended, stays in requested status

    db.commit()
    return {
        "ended_assignment_id": curr.id,
        "new_assignment_id": new_row.id,
        "stop_name": new_stop.name,
        "start_date": str(new_row.start_date),
        "status": new_row.status.value,
    }


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    reason: str = Query(min_length=3, max_length=500),
    user: User = Depends(desk),
    db: Session = Depends(get_db),
) -> dict:
    """End a transport assignment with a mandatory reason."""
    row = db.get(TransportAssignment, assignment_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    svc.set_assignment_status(
        db,
        actor=user,
        row=row,
        new_status=TransportAssignmentStatus.ended,
        reason=reason,
    )
    db.commit()
    return {"id": row.id, "status": row.status.value, "end_reason": row.end_reason}


@router.get("/routes/{route_id}/roster")
def route_roster(
    route_id: int,
    user: User = Depends(desk_reader),
    db: Session = Depends(get_db),
) -> dict:
    """Detailed A4 printable roster with stops, students, parent emergency contacts, and authorized pickup escorts."""
    from app.models import (
        Employee,
        Guardian,
        StudentAuthorizedPerson,
        StudentGuardian,
    )

    r = _route(db, user, route_id)
    vehicle = db.get(Vehicle, r.vehicle_id) if r.vehicle_id else None
    driver = db.get(Employee, r.driver_id) if r.driver_id else None
    attendant = db.get(Employee, r.attendant_id) if r.attendant_id else None

    labels = section_labels(db, user.school_id)

    rows = db.execute(
        select(TransportAssignment, RouteStop, Student, Enrolment)
        .join(RouteStop, RouteStop.id == TransportAssignment.route_stop_id)
        .join(Enrolment, Enrolment.id == TransportAssignment.enrolment_id)
        .join(Student, Student.id == Enrolment.student_id)
        .where(
            RouteStop.route_id == r.id,
            TransportAssignment.status.in_(svc.LIVE),
        )
        .order_by(RouteStop.sequence, Student.admission_no)
    ).all()

    stop_map: dict[int, dict] = {}
    for stop in r.stops:
        stop_map[stop.id] = {
            "id": stop.id,
            "sequence": stop.sequence,
            "name": stop.name,
            "address": stop.address or stop.landmark or "",
            "landmark": stop.landmark,
            "pickup_time": str(stop.pickup_time)[:5] if stop.pickup_time else "",
            "drop_time": str(stop.drop_time)[:5] if stop.drop_time else "",
            "riders": [],
        }

    for a, stop, s, e in rows:
        guardian_row = db.execute(
            select(Guardian, User)
            .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
            .join(User, User.id == Guardian.user_id)
            .where(StudentGuardian.student_id == s.id)
        ).first()

        parent_name = guardian_row[1].full_name if guardian_row else "Parent / Guardian"
        parent_phone = guardian_row[1].phone if guardian_row else s.user.phone

        auth_persons = db.scalars(
            select(StudentAuthorizedPerson).where(
                StudentAuthorizedPerson.student_id == s.id,
                StudentAuthorizedPerson.school_id == user.school_id,
            )
        ).all()
        escorts = [
            {
                "name": p.name,
                "relationship": p.relationship,
                "phone": p.phone,
                "photo_url": p.photo_url,
            }
            for p in auth_persons
        ]

        if stop.id in stop_map:
            stop_map[stop.id]["riders"].append(
                {
                    "assignment_id": a.id,
                    "student_id": s.id,
                    "name": s.user.full_name,
                    "admission_no": s.admission_no,
                    "class_label": labels.get(e.class_section_id, ""),
                    "direction": a.direction.value,
                    "parent_name": parent_name,
                    "parent_phone": parent_phone,
                    "escorts": escorts,
                }
            )

    ordered_stops = [
        stop_map[s.id]
        for s in sorted(r.stops, key=lambda x: x.sequence)
        if s.id in stop_map
    ]
    total_riders = sum(len(s["riders"]) for s in ordered_stops)

    return {
        "route_id": r.id,
        "code": r.code,
        "name": r.name,
        "status": r.status.value,
        "distance_km": float(r.distance_km) if r.distance_km is not None else None,
        "vehicle": {
            "registration_no": vehicle.registration_no if vehicle else "Unassigned",
            "make_model": vehicle.make_model if vehicle else "",
            "capacity": vehicle.capacity if vehicle else 0,
        },
        "driver": {
            "name": driver.user.full_name if driver else "Unassigned",
            "phone": driver.user.phone if driver else "",
            "code": driver.employee_code if driver else "",
        },
        "attendant": {
            "name": attendant.user.full_name if attendant else "Unassigned",
            "phone": attendant.user.phone if attendant else "",
            "code": attendant.employee_code if attendant else "",
        },
        "total_riders": total_riders,
        "stops": ordered_stops,
    }

