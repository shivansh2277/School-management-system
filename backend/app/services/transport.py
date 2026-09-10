"""Running the bus service, and refusing to run it unsafely.

Two of the rules in ERP_BLUEPRINT §5.6.9 are not validations in the ordinary
sense, and this module treats them differently from everything else it does:

* **A route may not carry more children than the vehicle has seats.**
* **A vehicle without valid insurance, fitness, permit and PUC may not run an
  active route, and nobody without a current licence and a police verification
  may crew one.**

Neither is expressible as an override with a reason. The timetable's workload
ceiling is — `timetable.slot.override` exists and a principal may schedule a
teacher past it, because the cost of being wrong is a tired teacher. The cost
of being wrong here is a child on an uninsured bus driven by someone nobody
checked, so there is no permission that lets it through and no `reason=`
parameter to pass. Keeping that distinction visible is the point; if a future
caller wants a way past these, that is a conversation, not a keyword argument.

Compliance is read from `documents`, not from columns on the vehicle. A paper
that expires is a document with an `expires_on`, and the module that already
models expiry, verification and confidentiality models these too.
"""

import calendar
from datetime import date as Date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Application,
    AuditAction,
    Document,
    DocumentStatus,
    DocumentType,
    Employee,
    Enrolment,
    EnrolmentStatus,
    OwnerType,
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
    VehicleStatus,
)
from app.services import audit
from app.services.fee_setup import money

# The papers a bus must hold. §5.6.9 names all four, and each is a document
# type the school already has from `core/document_types.py`.
VEHICLE_PAPERS = ("vehicle_insurance", "vehicle_fitness", "vehicle_permit", "vehicle_puc")
# A driver drives and is checked; an attendant only rides, so no licence.
DRIVER_PAPERS = ("driving_licence", "police_verification")
ATTENDANT_PAPERS = ("police_verification",)

LIVE = (
    TransportAssignmentStatus.requested,
    TransportAssignmentStatus.active,
    TransportAssignmentStatus.suspended,
)


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def _refuse(message: str) -> HTTPException:
    """A child-safety refusal. 409 rather than 422 because the request is
    well-formed — the world is simply not in a state where it may be granted."""
    return HTTPException(status.HTTP_409_CONFLICT, message)


# --- compliance -------------------------------------------------------------


def paper_gaps(
    db: Session,
    school_id: int,
    owner_type: OwnerType,
    owner_id: int,
    required_codes: tuple[str, ...],
    on: Date | None = None,
) -> list[str]:
    """Which of the required papers are missing, expired, or unusable.

    Three things count as a gap, and the third is the one worth stating:

    * no document of that type at all;
    * one whose `expires_on` has passed;
    * one with **no expiry recorded** for a type that has one. A certificate
      whose validity nobody entered is not evidence that it is valid, and
      treating a blank as "fine forever" is how an expired paper survives an
      audit.

    A rejected document does not count as held — the office looked at it and
    said no.
    """
    on = on or Date.today()
    rows = db.execute(
        select(DocumentType.code, Document.expires_on, Document.status)
        .join(Document, Document.document_type_id == DocumentType.id)
        .where(
            Document.school_id == school_id,
            Document.owner_type == owner_type,
            Document.owner_id == owner_id,
            Document.deleted_at.is_(None),
            DocumentType.code.in_(required_codes),
        )
    ).all()

    best: dict[str, list] = {}
    for code, expires_on, doc_status in rows:
        if doc_status is DocumentStatus.rejected:
            continue
        best.setdefault(code, []).append(expires_on)

    names = dict(
        db.execute(
            select(DocumentType.code, DocumentType.name).where(
                DocumentType.school_id == school_id,
                DocumentType.code.in_(required_codes),
            )
        ).all()
    )

    gaps: list[str] = []
    for code in required_codes:
        label = names.get(code, code)
        held = best.get(code)
        if not held:
            gaps.append(f"no {label} on file")
            continue
        # Several copies may exist — a renewal beside last year's. The latest
        # expiry is the one that decides, and a blank one proves nothing.
        dated = [d for d in held if d is not None]
        if not dated:
            gaps.append(f"{label} has no expiry date recorded")
        elif max(dated) < on:
            gaps.append(f"{label} expired on {max(dated)}")
    return gaps


def _crew_gaps(db: Session, employee: Employee, papers: tuple[str, ...], on: Date) -> list[str]:
    who = employee.user.full_name
    if not employee.in_service:
        return [f"{who} is no longer in service"]
    return [f"{who}: {g}" for g in paper_gaps(
        db, employee.school_id, OwnerType.employee, employee.id, papers, on
    )]


def roadworthiness(db: Session, route: Route, on: Date | None = None) -> list[str]:
    """Every reason this route may not carry children today.

    Reported as a list rather than raised, so a setup screen can show the
    Transport Manager all four expired papers at once instead of one per save.
    `assert_roadworthy` is the same check at the point it must refuse.
    """
    on = on or Date.today()
    gaps: list[str] = []

    if route.vehicle_id is None:
        gaps.append("no vehicle assigned")
    else:
        vehicle = db.get(Vehicle, route.vehicle_id)
        if vehicle.status is not VehicleStatus.active:
            gaps.append(
                f"{vehicle.registration_no} is {vehicle.status.value.replace('_', ' ')}"
            )
        gaps += [
            f"{vehicle.registration_no}: {g}"
            for g in paper_gaps(
                db, route.school_id, OwnerType.vehicle, vehicle.id, VEHICLE_PAPERS, on
            )
        ]

    if route.driver_id is None:
        gaps.append("no driver assigned")
    else:
        gaps += _crew_gaps(db, db.get(Employee, route.driver_id), DRIVER_PAPERS, on)

    # An attendant is optional — many routes run without one — but if there is
    # one, they are alone with children and the verification is not optional.
    if route.attendant_id is not None:
        gaps += _crew_gaps(
            db, db.get(Employee, route.attendant_id), ATTENDANT_PAPERS, on
        )
    return gaps


def assert_roadworthy(db: Session, route: Route, on: Date | None = None) -> None:
    """The hard block. No override, no reason, no permission that skips it."""
    gaps = roadworthiness(db, route, on)
    if gaps:
        raise _refuse(
            f"Route {route.code} cannot run: " + "; ".join(gaps)
        )


# --- routes and stops -------------------------------------------------------


def _route(db: Session, school_id: int, route_id: int) -> Route:
    row = db.get(Route, route_id)
    if row is None or row.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Route not found")
    return row


def _windows(route: Route) -> list[tuple[str, object, object]]:
    """When this route's vehicle is out, as (leg, earliest, latest)."""
    out = []
    pickups = [s.pickup_time for s in route.stops if s.pickup_time is not None]
    drops = [s.drop_time for s in route.stops if s.drop_time is not None]
    if pickups:
        out.append(("pickup", min(pickups), max(pickups)))
    if drops:
        out.append(("drop", min(drops), max(drops)))
    return out


def vehicle_clashes(db: Session, route: Route) -> list[str]:
    """Other live routes whose vehicle is this one at an overlapping time.

    §5.6.9 rejects them, and the shape is `timetable.conflicts()`: the same bus
    cannot be in two places at once any more than the same teacher can. A
    route's window is its first stop to its last, per leg — a bus doing a 6:30
    to 7:30 pickup is free for a 7:45 one.
    """
    if route.vehicle_id is None:
        return []
    others = db.scalars(
        select(Route).where(
            Route.school_id == route.school_id,
            Route.vehicle_id == route.vehicle_id,
            Route.id != route.id,
            Route.status.in_((RouteStatus.planned, RouteStatus.active)),
        )
    ).all()

    mine = _windows(route)
    found = []
    for other in others:
        for leg, start, end in mine:
            for other_leg, o_start, o_end in _windows(other):
                if leg == other_leg and start <= o_end and o_start <= end:
                    found.append(
                        f"{route.vehicle.registration_no} is on route {other.code} "
                        f"for the {other_leg} between {o_start:%H:%M} and {o_end:%H:%M}"
                    )
    return found


def set_stops(db: Session, route: Route, stops: list[dict], actor: User) -> Route:
    """Replace a route's stops, in one call, because the rules are about the
    whole sequence rather than any one halt.

    §5.6.9: timings increase along the route. Stop 3 cannot be picked up before
    stop 2 — a sequence that goes backwards is a route somebody has typed
    wrongly, and the printed timing sheet a parent stands at the gate holding
    would be wrong.
    """
    if not stops:
        raise _bad("A route needs at least one stop")

    ordered = sorted(stops, key=lambda s: s["sequence"])
    if len({s["sequence"] for s in ordered}) != len(ordered):
        raise _bad("Two stops cannot share a sequence number")

    for earlier, later in zip(ordered, ordered[1:], strict=False):
        if later["pickup_time"] <= earlier["pickup_time"]:
            raise _bad(
                f"Stop {later['sequence']} ({later['name']}) is picked up at "
                f"{later['pickup_time']:%H:%M}, which is not after stop "
                f"{earlier['sequence']} at {earlier['pickup_time']:%H:%M}"
            )
        a, b = earlier.get("drop_time"), later.get("drop_time")
        if a is not None and b is not None and b <= a:
            raise _bad(
                f"Stop {later['sequence']} ({later['name']}) is dropped at "
                f"{b:%H:%M}, which is not after stop {earlier['sequence']} at {a:%H:%M}"
            )

    # A stop that children are already assigned to cannot be deleted out from
    # under them: their assignment would point at nothing.
    keeping = {s.get("id") for s in ordered if s.get("id") is not None}
    for stop in route.stops:
        if stop.id not in keeping and _live_on_stops(db, [stop.id]):
            raise _refuse(
                f"Children are assigned to {stop.name}; move or end their "
                "assignments before removing the stop"
            )

    slabs = {
        s.id
        for s in db.scalars(
            select(TransportFeeSlab).where(TransportFeeSlab.school_id == route.school_id)
        )
    }
    for spec in ordered:
        if spec.get("fee_slab_id") is not None and spec["fee_slab_id"] not in slabs:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fee slab not found")

    route.stops = [
        RouteStop(
            school_id=route.school_id,
            sequence=spec["sequence"],
            name=spec["name"],
            landmark=spec.get("landmark"),
            pickup_time=spec["pickup_time"],
            drop_time=spec.get("drop_time"),
            fee_slab_id=spec.get("fee_slab_id"),
            latitude=spec.get("latitude"),
            longitude=spec.get("longitude"),
        )
        for spec in ordered
    ]
    db.flush()

    clashes = vehicle_clashes(db, route)
    if clashes:
        raise _refuse("; ".join(clashes))

    audit.record(
        db,
        actor=actor,
        school_id=route.school_id,
        entity_type="route",
        entity_id=route.id,
        action=AuditAction.update,
        after={"stops": len(route.stops)},
    )
    db.flush()
    return route


def set_status(
    db: Session, route: Route, new_status: RouteStatus, actor: User, *, reason: str
) -> Route:
    """Move a route between planned, active, suspended and closed.

    Going `active` is where the compliance refusal bites, because that is the
    moment the route means "children ride this".

    `reason` is required and keyword-only. It used to be a string this function
    made up - `f"route set to {new_status.value}"` - which is not a reason, it
    is a restatement of `after`. Suspending a route stops children getting to
    school, and the audit log is the only record of why anyone did it; filling
    it in from the code turns the trail into the software's opinion rather than
    a person's. Keyword-only and unconditional so that a caller who has no
    reason to give has to notice, rather than inheriting a plausible one.
    """
    before = route.status.value
    if new_status is RouteStatus.active:
        if not route.stops:
            raise _bad("A route with no stops cannot be made active")
        assert_roadworthy(db, route)
        clashes = vehicle_clashes(db, route)
        if clashes:
            raise _refuse("; ".join(clashes))
    if new_status is RouteStatus.closed and _live_on_route(db, route):
        raise _refuse(
            f"Route {route.code} still has children assigned; end their "
            "assignments first"
        )

    route.status = new_status
    audit.record(
        db,
        actor=actor,
        school_id=route.school_id,
        entity_type="route",
        entity_id=route.id,
        action=AuditAction.status_change,
        before={"status": before},
        after={"status": new_status.value},
        reason=reason,
    )
    db.flush()
    return route


def set_crew(
    db: Session,
    route: Route,
    actor: User,
    *,
    vehicle_id: int | None = ...,
    driver_id: int | None = ...,
    attendant_id: int | None = ...,
) -> Route:
    """Change the bus or the people on it.

    The same refusal as activation, applied here too: an active route that has
    its compliant vehicle swapped for a grounded one is exactly as unsafe as
    one that was made active with it, and guarding only the activation path
    would leave the back door open.
    """
    before = audit.snapshot(route, ["vehicle_id", "driver_id", "attendant_id"])
    if vehicle_id is not ...:
        if vehicle_id is not None:
            v = db.get(Vehicle, vehicle_id)
            if v is None or v.school_id != route.school_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
            seated = _live_on_route(db, route)
            if seated > v.capacity:
                raise _refuse(
                    f"{v.registration_no} seats {v.capacity} and {seated} children "
                    f"are assigned to route {route.code}"
                )
        route.vehicle_id = vehicle_id
    for field, value in (("driver_id", driver_id), ("attendant_id", attendant_id)):
        if value is ...:
            continue
        if value is not None:
            e = db.get(Employee, value)
            if e is None or e.school_id != route.school_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
        setattr(route, field, value)

    db.flush()
    if route.status is RouteStatus.active:
        assert_roadworthy(db, route)
        clashes = vehicle_clashes(db, route)
        if clashes:
            raise _refuse("; ".join(clashes))

    audit.record(
        db,
        actor=actor,
        school_id=route.school_id,
        entity_type="route",
        entity_id=route.id,
        action=AuditAction.update,
        before=before,
        after=audit.snapshot(route, ["vehicle_id", "driver_id", "attendant_id"]),
    )
    db.flush()
    return route


# --- who is on the bus ------------------------------------------------------


def _live_on_stops(db: Session, stop_ids: list[int]) -> int:
    if not stop_ids:
        return 0
    return db.scalar(
        select(func.count(TransportAssignment.id)).where(
            TransportAssignment.route_stop_id.in_(stop_ids),
            TransportAssignment.status.in_(LIVE),
        )
    )


def _live_on_route(db: Session, route: Route) -> int:
    return _live_on_stops(db, [s.id for s in route.stops])


def seats(db: Session, route: Route) -> dict:
    """Capacity, taken and free — the number the assignment desk needs and the
    number the utilisation report in §5.6.10 is."""
    vehicle = db.get(Vehicle, route.vehicle_id) if route.vehicle_id else None
    taken = _live_on_route(db, route)
    capacity = vehicle.capacity if vehicle else None
    return {
        "route_id": route.id,
        "code": route.code,
        "vehicle": vehicle.registration_no if vehicle else None,
        "capacity": capacity,
        "taken": taken,
        "free": None if capacity is None else capacity - taken,
    }


def assign(
    db: Session,
    *,
    actor: User,
    enrolment: Enrolment,
    stop: RouteStop,
    direction: TransportDirection,
    start_date: Date,
) -> TransportAssignment:
    """Put a child on a stop.

    The capacity check here is the hard block of §5.6.9. It counts every live
    assignment — requested and suspended as well as active — because a seat
    somebody is coming back to is a seat that is taken, and counting only the
    active ones would let a bus be filled twice over on paper and then refuse
    the children at the door.
    """
    route = db.get(Route, stop.route_id)
    if route.status in (RouteStatus.suspended, RouteStatus.closed):
        raise _bad(f"Route {route.code} is {route.status.value}")

    vehicle = db.get(Vehicle, route.vehicle_id) if route.vehicle_id else None
    if vehicle is None:
        # Without a vehicle there is no capacity, and a capacity check that
        # cannot run must refuse rather than wave the child through.
        raise _refuse(
            f"Route {route.code} has no vehicle, so there is no seating "
            "capacity to check against"
        )
    taken = _live_on_route(db, route)
    if taken >= vehicle.capacity:
        raise _refuse(
            f"Route {route.code} is full: {vehicle.registration_no} seats "
            f"{vehicle.capacity} and {taken} children are already assigned"
        )
    if route.status is RouteStatus.active:
        assert_roadworthy(db, route)

    existing = db.scalar(
        select(TransportAssignment).where(
            TransportAssignment.enrolment_id == enrolment.id,
            TransportAssignment.status.in_(LIVE),
        )
    )
    if existing is not None:
        raise _refuse(
            "This child already has a transport assignment; end it before "
            "starting another"
        )

    row = TransportAssignment(
        school_id=enrolment.school_id,
        enrolment_id=enrolment.id,
        route_stop_id=stop.id,
        direction=direction,
        start_date=start_date,
        status=TransportAssignmentStatus.requested,
    )
    db.add(row)
    db.flush()
    audit.record(
        db,
        actor=actor,
        school_id=enrolment.school_id,
        entity_type="transport_assignment",
        entity_id=row.id,
        action=AuditAction.create,
        after=audit.snapshot(row, ["enrolment_id", "route_stop_id", "direction", "start_date"]),
    )
    db.flush()
    return row


def set_assignment_status(
    db: Session,
    *,
    actor: User,
    row: TransportAssignment,
    new_status: TransportAssignmentStatus,
    end_date: Date | None = None,
    reason: str | None = None,
) -> TransportAssignment:
    """Activate, suspend or end a child's place on the bus.

    Ending sets an `end_date` rather than deleting the row (§5.6.9): billing
    reads the dates, so the next invoice stops while the history of who rode
    which bus survives. It refunds nothing already paid, which is §0.6.
    """
    if row.status is TransportAssignmentStatus.ended:
        raise _bad("This assignment has already ended")

    if new_status is TransportAssignmentStatus.active:
        route = db.get(Route, row.route_stop.route_id)
        if route.status is not RouteStatus.active:
            raise _bad(f"Route {route.code} is not active")
        assert_roadworthy(db, route)

    before = row.status.value
    if new_status is TransportAssignmentStatus.ended:
        if not reason:
            raise _bad("Ending a transport assignment needs a reason")
        row.end_date = end_date or Date.today()
        if row.end_date < row.start_date:
            raise _bad("An assignment cannot end before it started")
        row.end_reason = reason
    row.status = new_status

    audit.record(
        db,
        actor=actor,
        school_id=row.school_id,
        entity_type="transport_assignment",
        entity_id=row.id,
        action=AuditAction.status_change,
        before={"status": before},
        after={"status": new_status.value, "end_date": str(row.end_date or "")},
        reason=reason or f"assignment set to {new_status.value}",
    )
    db.flush()
    return row


def awaiting_assignment(db: Session, school_id: int) -> list[dict]:
    """Children who asked for the bus at admission and are not on one yet.

    `applications.transport_required` has been captured on every application
    since Part 2 and read by nothing — a tick box a parent filled in that
    reached no queue and no screen. This is where it goes.

    It is a work list, not an automatic assignment. The form records *that* a
    family wants transport, never which stop, and picking one for them from a
    postal address would be a guess made about a seven-year-old's walk to the
    bus. So the office gets the name, the class and the address on file, and
    chooses.
    """
    rows = db.execute(
        select(Application, Student, Enrolment)
        .join(Student, Student.id == Application.student_id)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .where(
            Application.school_id == school_id,
            Application.transport_required.is_(True),
            Application.student_id.is_not(None),
            Enrolment.status == EnrolmentStatus.active,
            Enrolment.id.not_in(
                select(TransportAssignment.enrolment_id).where(
                    TransportAssignment.status.in_(LIVE)
                )
            ),
        )
        .order_by(Application.id)
    ).all()
    return [
        {
            "enrolment_id": enrolment.id,
            "student_id": student.id,
            "name": student.user.full_name,
            "admission_no": student.admission_no,
            "application_no": application.application_no,
            # The only thing the system knows that helps choose a stop.
            "address": student.address,
        }
        for application, student, enrolment in rows
    ]


# --- what it costs ----------------------------------------------------------


def charges_for_month(db: Session, school_id: int, year: int, month: int) -> dict[int, Decimal]:
    """`{enrolment_id: amount}` for one month's transport, and nothing else.

    This is the opt-in that makes `FeeHeadType.optional` mean something. An
    enrolment with no row here is not billed for the bus, which is the whole
    protection: before this existed, putting the transport head on a plan
    charged every child in the school for it.

    Prorated by calendar day when the assignment starts or ends mid-month
    (§5.6.9). A whole month is the slab exactly, never the slab reconstructed
    from thirty daily divisions.

    `requested` and `suspended` do not bill. A seat that has been asked for is
    not a service delivered, and a suspended child is not riding.
    """
    days = calendar.monthrange(year, month)[1]
    first, last = Date(year, month, 1), Date(year, month, days)

    rows = db.execute(
        select(TransportAssignment, TransportFeeSlab.monthly_amount)
        .join(RouteStop, RouteStop.id == TransportAssignment.route_stop_id)
        .join(TransportFeeSlab, TransportFeeSlab.id == RouteStop.fee_slab_id)
        .where(
            TransportAssignment.school_id == school_id,
            TransportAssignment.status.in_(
                (TransportAssignmentStatus.active, TransportAssignmentStatus.ended)
            ),
            TransportAssignment.start_date <= last,
        )
    ).all()

    out: dict[int, Decimal] = {}
    for row, monthly in rows:
        if row.end_date is not None and row.end_date < first:
            continue
        covered = (min(row.end_date or last, last) - max(row.start_date, first)).days + 1
        if covered <= 0:
            continue
        out[row.enrolment_id] = (
            Decimal(monthly)
            if covered >= days
            else money(Decimal(monthly) * covered / days)
        )
    return out


# --- expiry alerts ----------------------------------------------------------

# §5.6.9 asks for 60/30/7-day warnings. One nightly pass reports everything
# inside the widest window and says how many days are left, rather than three
# schedules that each have to be kept in step with the others.
EXPIRY_HORIZON_DAYS = 60


def expiring_papers(db: Session, school_id: int, within_days: int = EXPIRY_HORIZON_DAYS) -> list[dict]:
    """Vehicle and crew papers that have lapsed or are about to.

    Already-expired papers are included with a negative `days_left`: a lapsed
    permit is more urgent than one lapsing next month, and dropping it off the
    list the day it expires is how it stops being anybody's problem.
    """
    today = Date.today()
    horizon = today + timedelta(days=within_days)
    rows = db.execute(
        select(Document, DocumentType.code, DocumentType.name)
        .join(DocumentType, DocumentType.id == Document.document_type_id)
        .where(
            Document.school_id == school_id,
            Document.deleted_at.is_(None),
            Document.status != DocumentStatus.rejected,
            Document.expires_on.is_not(None),
            Document.expires_on <= horizon,
            DocumentType.code.in_(VEHICLE_PAPERS + DRIVER_PAPERS),
        )
        .order_by(Document.expires_on)
    ).all()

    out = []
    for doc, code, name in rows:
        if doc.owner_type is OwnerType.vehicle:
            owner = db.get(Vehicle, doc.owner_id)
            label = owner.registration_no if owner else f"vehicle {doc.owner_id}"
        else:
            owner = db.get(Employee, doc.owner_id)
            label = owner.user.full_name if owner else f"employee {doc.owner_id}"
        out.append(
            {
                "owner_type": doc.owner_type.value,
                "owner_id": doc.owner_id,
                "owner": label,
                "document": name,
                "code": code,
                "expires_on": str(doc.expires_on),
                "days_left": (doc.expires_on - today).days,
            }
        )
    return out


# The nightly sweep that reads this lives in `app/jobs.py` with every other
# handler, because importing that one module is what registers them all — for
# the worker and for the tests. A handler defined here would exist only once
# something happened to import this service, which for a worker process is
# never, and the job would fail with "no handler registered" at 03:00.
