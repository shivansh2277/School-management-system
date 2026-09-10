"""The bus service, and the two rules it must never bend.

ERP_BLUEPRINT §5.6.9 has a dozen validations. Two of them are different in kind
from the rest, and most of this file is about them:

* a route may not carry more children than the vehicle has seats;
* a bus without valid papers, or crewed by somebody without a current licence
  and a police verification, may not run.

The timetable has a comparable ceiling on a teacher's weekly load, and that one
*is* overridable — `timetable.slot.override` exists and a principal may use it.
These two are not, and several tests below exist specifically to prove there is
no door: not a permission, not a reason string, not a second endpoint.
"""

from datetime import date as Date, time as Time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import (
    ConcessionStatus,
    ConcessionType,
    Document,
    DocumentType,
    Employee,
    Enrolment,
    EnrolmentStatus,
    FeeConcession,
    FeeFrequency,
    FeeHead,
    FeeHeadType,
    FeeInvoice,
    FeeInvoiceLine,
    FeePlan,
    FeePlanItem,
    OwnerType,
    Route,
    RouteStatus,
    TransportAssignment,
    TransportAssignmentStatus,
    TransportDirection,
    TransportFeeSlab,
    User,
    Vehicle,
    VehicleStatus,
)
from app.services import documents, fees, transport as svc

TODAY = Date.today()
NEXT_YEAR = TODAY + timedelta(days=365)
LAST_MONTH = TODAY - timedelta(days=30)


# --- fixtures ---------------------------------------------------------------


def _paper(db, admin_user, owner_type, owner_id, code, expires_on):
    """Put one compliance document on file, with an expiry."""
    dt = db.scalar(
        select(DocumentType).where(
            DocumentType.school_id == admin_user.school_id, DocumentType.code == code
        )
    )
    assert dt is not None, f"seed has no {code} document type"
    return documents.upload(
        db,
        actor=admin_user,
        owner_type=owner_type,
        owner_id=owner_id,
        filename=f"{code}-{owner_type.value}-{owner_id}.pdf",
        mime_type="application/pdf",
        # The bytes are irrelevant to every rule under test; what matters is
        # that a row exists with an expiry the compliance check can read.
        data=f"{code}:{owner_id}:{expires_on}".encode(),
        document_type_id=dt.id,
        expires_on=expires_on,
    )


def _papers_for_vehicle(db, admin_user, vehicle_id, expires_on=NEXT_YEAR):
    for code in svc.VEHICLE_PAPERS:
        _paper(db, admin_user, OwnerType.vehicle, vehicle_id, code, expires_on)


def _papers_for_driver(db, admin_user, employee_id, expires_on=NEXT_YEAR):
    for code in svc.DRIVER_PAPERS:
        _paper(db, admin_user, OwnerType.employee, employee_id, code, expires_on)


@pytest.fixture()
def bus(db, admin_user):
    """A four-seat bus with every paper valid for a year."""
    v = Vehicle(
        school_id=admin_user.school_id,
        registration_no="UP32TT0001",
        make_model="Tata Starbus",
        capacity=4,
    )
    db.add(v)
    db.flush()
    _papers_for_vehicle(db, admin_user, v.id)
    return v


@pytest.fixture()
def driver(db, admin_user, ids):
    """An employee with a current licence and police verification.

    Reusing a seeded teacher on purpose: §5.6.6 says a driver *is* an employee,
    and a test that had to invent a `drivers` row would be testing a design
    this module deliberately does not have.
    """
    e = db.get(Employee, ids["teacher_1"])
    _papers_for_driver(db, admin_user, e.id)
    return e


@pytest.fixture()
def slab(db, admin_user):
    s = TransportFeeSlab(
        school_id=admin_user.school_id,
        name="Test near",
        monthly_amount=Decimal("800.00"),
    )
    db.add(s)
    db.flush()
    return s


@pytest.fixture()
def route(db, admin_user, bus, driver, slab):
    """An active route with two stops, ready to carry children."""
    r = Route(
        school_id=admin_user.school_id,
        code="T1",
        name="Test Gomti Nagar",
        vehicle_id=bus.id,
        driver_id=driver.id,
    )
    db.add(r)
    db.flush()
    svc.set_stops(
        db,
        r,
        [
            {
                "sequence": 1,
                "name": "Vibhuti Khand",
                "pickup_time": Time(6, 45),
                "drop_time": Time(14, 30),
                "fee_slab_id": slab.id,
            },
            {
                "sequence": 2,
                "name": "Patrakarpuram",
                "pickup_time": Time(7, 5),
                "drop_time": Time(14, 50),
                "fee_slab_id": slab.id,
            },
        ],
        admin_user,
    )
    svc.set_status(db, r, RouteStatus.active, admin_user, reason="test fixture")
    return r


@pytest.fixture()
def riders(db, ids):
    """Six active enrolments the seed has *not* already put on a bus.

    The demo school runs two real routes with thirty children on them, and a
    child who already holds a live assignment is refused a second one — which
    is itself a rule tested below. Picking blindly off the roster would make
    half this file fail for the right reason at the wrong moment.
    """
    taken = select(TransportAssignment.enrolment_id).where(
        TransportAssignment.status.in_(svc.LIVE)
    )
    rows = list(
        db.scalars(
            select(Enrolment)
            .where(
                Enrolment.school_id == ids["school"],
                Enrolment.status == EnrolmentStatus.active,
                Enrolment.id.not_in(taken),
            )
            .order_by(Enrolment.id)
            .limit(6)
        )
    )
    assert len(rows) == 6
    return rows


def _mine(charges: dict, riders: list) -> dict:
    """The charges belonging to this test's own riders.

    The seed runs two real routes with thirty children on them and they are
    correctly billed, so a bare `== {}` would be asserting that the demo data
    does not exist rather than that the opt-in works.
    """
    return {e.id: charges[e.id] for e in riders if e.id in charges}


def _assign(db, admin_user, route, enrolment, start=None, seq=1):
    stop = next(s for s in route.stops if s.sequence == seq)
    return svc.assign(
        db,
        actor=admin_user,
        enrolment=enrolment,
        stop=stop,
        direction=TransportDirection.both,
        start_date=start or Date(2026, 4, 1),
    )


# --- the capacity block -----------------------------------------------------


def test_a_route_cannot_be_filled_past_the_vehicles_seats(
    db, admin_user, route, bus, riders
):
    """The first hard block of §5.6.9, and the reason it is a refusal.

    Four seats take four children. The fifth is turned away, and the message
    names the vehicle and the number so the office can act on it rather than
    retrying.
    """
    for enrolment in riders[:4]:
        _assign(db, admin_user, route, enrolment)
    assert svc.seats(db, route)["free"] == 0

    with pytest.raises(Exception) as e:
        _assign(db, admin_user, route, riders[4])
    assert e.value.status_code == 409
    assert "seats 4" in e.value.detail
    assert svc.seats(db, route)["taken"] == 4


def test_the_capacity_block_has_no_override(db, admin_user, route, riders):
    """There is no way past it, which is the whole point.

    The timetable's workload ceiling takes a reason and a permission; this one
    takes neither, and `assign` has no parameter that would accept one. If a
    `reason` or `force` argument ever appears here, this test fails and the
    conversation happens before the code ships.
    """
    import inspect

    params = set(inspect.signature(svc.assign).parameters)
    assert not params & {"reason", "force", "override", "allow_over_capacity"}


def test_a_seat_somebody_is_coming_back_to_is_still_taken(
    db, admin_user, route, riders
):
    """Suspending a child does not free their seat.

    Counting only `active` assignments would let the bus be filled twice over
    on paper and then turn children away at the door in the morning.
    """
    rows = [_assign(db, admin_user, route, e) for e in riders[:4]]
    svc.set_assignment_status(
        db,
        actor=admin_user,
        row=rows[0],
        new_status=TransportAssignmentStatus.suspended,
    )
    assert svc.seats(db, route)["taken"] == 4
    with pytest.raises(Exception) as e:
        _assign(db, admin_user, route, riders[4])
    assert e.value.status_code == 409


def test_ending_an_assignment_frees_the_seat(db, admin_user, route, riders):
    rows = [_assign(db, admin_user, route, e) for e in riders[:4]]
    svc.set_assignment_status(
        db,
        actor=admin_user,
        row=rows[0],
        new_status=TransportAssignmentStatus.ended,
        end_date=Date(2026, 6, 30),
        reason="family moved",
    )
    assert svc.seats(db, route)["free"] == 1
    _assign(db, admin_user, route, riders[4])
    assert svc.seats(db, route)["free"] == 0


def test_a_route_with_no_vehicle_refuses_rather_than_waving_children_through(
    db, admin_user, route, riders
):
    """A capacity check that cannot run must refuse.

    Removing the bus from a route leaves no seating figure to count against,
    and treating "unknown" as "unlimited" is how the block would be bypassed
    without anybody deciding to bypass it.
    """
    svc.set_status(db, route, RouteStatus.planned, admin_user, reason="test fixture")
    svc.set_crew(db, route, admin_user, vehicle_id=None)
    with pytest.raises(Exception) as e:
        _assign(db, admin_user, route, riders[0])
    assert e.value.status_code == 409
    assert "no vehicle" in e.value.detail


def test_a_smaller_bus_cannot_be_swapped_under_the_children_already_on_board(
    db, admin_user, route, riders
):
    """The capacity rule guards the other direction too.

    Four children on a four-seat bus, then somebody puts a two-seater on the
    route. Guarding only `assign` would leave two children standing.
    """
    for enrolment in riders[:4]:
        _assign(db, admin_user, route, enrolment)
    small = Vehicle(
        school_id=admin_user.school_id, registration_no="UP32TT0002", capacity=2
    )
    db.add(small)
    db.flush()
    with pytest.raises(Exception) as e:
        svc.set_crew(db, route, admin_user, vehicle_id=small.id)
    assert e.value.status_code == 409
    assert "seats 2" in e.value.detail


# --- the compliance block ---------------------------------------------------


def test_a_bus_with_expired_insurance_cannot_be_put_on_the_road(
    db, admin_user, bus, driver, slab
):
    """The second hard block, and the one that is also a legal requirement."""
    doc = db.scalar(
        select(Document)
        .join(DocumentType, DocumentType.id == Document.document_type_id)
        .where(
            Document.owner_type == OwnerType.vehicle,
            Document.owner_id == bus.id,
            DocumentType.code == "vehicle_insurance",
        )
    )
    doc.expires_on = LAST_MONTH
    db.flush()

    r = Route(
        school_id=admin_user.school_id,
        code="T9",
        name="Expired",
        vehicle_id=bus.id,
        driver_id=driver.id,
    )
    db.add(r)
    db.flush()
    svc.set_stops(
        db, r, [{"sequence": 1, "name": "A", "pickup_time": Time(7, 0)}], admin_user
    )
    with pytest.raises(Exception) as e:
        svc.set_status(db, r, RouteStatus.active, admin_user, reason="test fixture")
    assert e.value.status_code == 409
    assert "Insurance expired" in e.value.detail


def test_a_paper_nobody_uploaded_is_a_refusal_not_a_pass(db, admin_user, driver):
    """Missing is at least as bad as expired.

    A bus with no insurance certificate on file is not safer than one whose
    certificate lapsed last week, and defaulting an absent paper to "fine" is
    how a compliance check quietly stops checking anything.
    """
    bare = Vehicle(
        school_id=admin_user.school_id, registration_no="UP32TT0003", capacity=10
    )
    db.add(bare)
    db.flush()
    r = Route(
        school_id=admin_user.school_id,
        code="T8",
        name="Bare",
        vehicle_id=bare.id,
        driver_id=driver.id,
    )
    db.add(r)
    db.flush()
    svc.set_stops(
        db, r, [{"sequence": 1, "name": "A", "pickup_time": Time(7, 0)}], admin_user
    )
    with pytest.raises(Exception) as e:
        svc.set_status(db, r, RouteStatus.active, admin_user, reason="test fixture")
    gaps = svc.roadworthiness(db, r)
    assert len(gaps) == 4
    assert all("no " in g for g in gaps)
    assert e.value.status_code == 409


def test_a_paper_with_no_expiry_recorded_proves_nothing(db, admin_user, bus):
    """A blank expiry is not "valid forever".

    This is the quiet one: somebody uploads the insurance certificate and
    leaves the date field empty, and a check that only compares dates would
    treat that as compliant for the rest of the vehicle's life.
    """
    doc = db.scalar(
        select(Document)
        .join(DocumentType, DocumentType.id == Document.document_type_id)
        .where(
            Document.owner_type == OwnerType.vehicle,
            Document.owner_id == bus.id,
            DocumentType.code == "vehicle_permit",
        )
    )
    doc.expires_on = None
    db.flush()
    gaps = svc.paper_gaps(
        db, admin_user.school_id, OwnerType.vehicle, bus.id, svc.VEHICLE_PAPERS
    )
    assert gaps == ["Permit has no expiry date recorded"]


def test_a_driver_without_a_police_verification_cannot_crew_a_route(
    db, admin_user, bus, ids
):
    """§5.6.9, and a legal requirement for school transport in India."""
    unchecked = db.scalar(
        select(Employee).join(User).where(User.login_id == "TCH004")
    )
    _paper(db, admin_user, OwnerType.employee, unchecked.id, "driving_licence", NEXT_YEAR)

    r = Route(
        school_id=admin_user.school_id,
        code="T7",
        name="Unchecked",
        vehicle_id=bus.id,
        driver_id=unchecked.id,
    )
    db.add(r)
    db.flush()
    svc.set_stops(
        db, r, [{"sequence": 1, "name": "A", "pickup_time": Time(7, 0)}], admin_user
    )
    with pytest.raises(Exception) as e:
        svc.set_status(db, r, RouteStatus.active, admin_user, reason="test fixture")
    assert "no Police Verification on file" in e.value.detail


def test_an_expired_licence_stops_a_driver_who_was_already_crewing(
    db, admin_user, route, driver
):
    """The refusal is on the write path, not only on activation.

    Swapping a compliant driver for a lapsed one on a route that is already
    active is exactly as unsafe as activating with them, so `set_crew` runs the
    same check rather than trusting that activation caught it.
    """
    lapsed = db.scalar(select(Employee).join(User).where(User.login_id == "TCH005"))
    _paper(db, admin_user, OwnerType.employee, lapsed.id, "driving_licence", LAST_MONTH)
    _paper(
        db, admin_user, OwnerType.employee, lapsed.id, "police_verification", NEXT_YEAR
    )
    with pytest.raises(Exception) as e:
        svc.set_crew(db, route, admin_user, driver_id=lapsed.id)
    assert e.value.status_code == 409
    assert "Driving Licence expired" in e.value.detail


def test_a_grounded_bus_cannot_run_an_active_route(
    db, admin_user, route, bus, riders
):
    """`under_maintenance`, `grounded` and `retired` are all "not on the road".

    The assignment is made first, while the bus is fine, so that what fails is
    specifically activating a child onto a grounded vehicle rather than the
    assignment itself — otherwise this would pass without ever reaching
    `set_assignment_status`.
    """
    row = _assign(db, admin_user, route, riders[0])
    bus.status = VehicleStatus.grounded
    db.flush()

    assert any("grounded" in g for g in svc.roadworthiness(db, route))
    with pytest.raises(Exception) as e:
        svc.set_assignment_status(
            db,
            actor=admin_user,
            row=row,
            new_status=TransportAssignmentStatus.active,
        )
    assert e.value.status_code == 409
    assert "grounded" in e.value.detail


def test_the_compliance_block_has_no_override_either(db):
    import inspect

    params = set(inspect.signature(svc.assert_roadworthy).parameters)
    assert not params & {"reason", "force", "override"}
    assert not params & {"actor", "user"}, (
        "taking an actor would invite a permission check, and there is no "
        "permission that may skip this"
    )


# --- route design -----------------------------------------------------------


def test_stop_timings_must_increase_along_the_route(db, admin_user, bus, driver):
    r = Route(
        school_id=admin_user.school_id, code="T2", name="Backwards", vehicle_id=bus.id,
        driver_id=driver.id,
    )
    db.add(r)
    db.flush()
    with pytest.raises(Exception) as e:
        svc.set_stops(
            db,
            r,
            [
                {"sequence": 1, "name": "First", "pickup_time": Time(7, 30)},
                {"sequence": 2, "name": "Second", "pickup_time": Time(7, 0)},
            ],
            admin_user,
        )
    assert e.value.status_code == 422
    assert "not after stop 1" in e.value.detail


def test_one_bus_cannot_be_on_two_routes_at_the_same_time(
    db, admin_user, route, bus, driver
):
    """The same shape as `timetable.conflicts()`: a bus, like a teacher, is in
    one place at a time. A 6:45-7:05 pickup leaves it free at 7:45."""
    second = Route(
        school_id=admin_user.school_id, code="T3", name="Overlap", vehicle_id=bus.id,
        driver_id=driver.id,
    )
    db.add(second)
    db.flush()
    with pytest.raises(Exception) as e:
        svc.set_stops(
            db,
            second,
            [{"sequence": 1, "name": "Clash", "pickup_time": Time(6, 50)}],
            admin_user,
        )
    assert e.value.status_code == 409
    assert "is on route T1" in e.value.detail


def test_a_second_trip_after_the_first_is_fine(db, admin_user, route, bus, driver):
    second = Route(
        school_id=admin_user.school_id, code="T4", name="Second trip",
        vehicle_id=bus.id, driver_id=driver.id,
    )
    db.add(second)
    db.flush()
    svc.set_stops(
        db,
        second,
        [
            {"sequence": 1, "name": "Later", "pickup_time": Time(7, 45),
             "drop_time": Time(15, 30)},
        ],
        admin_user,
    )
    assert svc.vehicle_clashes(db, second) == []


def test_a_stop_children_are_standing_at_cannot_be_deleted(
    db, admin_user, route, riders, slab
):
    _assign(db, admin_user, route, riders[0], seq=2)
    with pytest.raises(Exception) as e:
        svc.set_stops(
            db,
            route,
            [
                {
                    "id": route.stops[0].id,
                    "sequence": 1,
                    "name": "Vibhuti Khand",
                    "pickup_time": Time(6, 45),
                    "fee_slab_id": slab.id,
                }
            ],
            admin_user,
        )
    assert e.value.status_code == 409


def test_a_route_with_children_on_it_cannot_be_closed(db, admin_user, route, riders):
    _assign(db, admin_user, route, riders[0])
    with pytest.raises(Exception) as e:
        svc.set_status(db, route, RouteStatus.closed, admin_user, reason="test fixture")
    assert "still has children assigned" in e.value.detail


def test_a_child_cannot_be_on_two_buses(db, admin_user, route, riders, bus, driver):
    _assign(db, admin_user, route, riders[0])
    with pytest.raises(Exception) as e:
        _assign(db, admin_user, route, riders[0], seq=2)
    assert e.value.status_code == 409


# --- what it costs ----------------------------------------------------------


def test_only_children_on_the_bus_are_charged_for_it(db, admin_user, route, riders):
    """The opt-in, stated as a number.

    Six active children, two on the bus. `charges_for_month` returns two rows —
    the protection that makes `FeeHeadType.optional` mean something rather than
    being a label nothing reads.
    """
    for enrolment in riders[:2]:
        row = _assign(db, admin_user, route, enrolment, start=Date(2026, 4, 1))
        svc.set_assignment_status(
            db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
        )
    charges = svc.charges_for_month(db, admin_user.school_id, 2026, 5)
    mine = _mine(charges, riders)
    assert set(mine) == {e.id for e in riders[:2]}
    assert all(v == Decimal("800.00") for v in mine.values())
    # The four who were not put on a bus are absent, not zero.
    assert all(e.id not in charges for e in riders[2:])


def test_a_requested_seat_is_not_a_billed_one(db, admin_user, route, riders):
    """A seat that has been asked for is not a service delivered."""
    _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1))
    assert riders[0].id not in svc.charges_for_month(db, admin_user.school_id, 2026, 5)


def test_a_mid_month_start_is_prorated_by_the_days_actually_ridden(
    db, admin_user, route, riders
):
    """§5.6.9. Starting on the 16th of a 30-day month is half a month's bus."""
    row = _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 16))
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )
    charges = svc.charges_for_month(db, admin_user.school_id, 2026, 4)
    # 16 April to 30 April inclusive is 15 of 30 days.
    assert charges[riders[0].id] == Decimal("400.00")


def test_ending_an_assignment_stops_the_next_invoice_and_keeps_the_history(
    db, admin_user, route, riders
):
    """§5.6.9 with §0.6: the next month stops, the months already ridden stand,
    and nothing already paid comes back."""
    row = _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1))
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )
    svc.set_assignment_status(
        db,
        actor=admin_user,
        row=row,
        new_status=TransportAssignmentStatus.ended,
        end_date=Date(2026, 5, 10),
        reason="moved house",
    )
    may = svc.charges_for_month(db, admin_user.school_id, 2026, 5)
    june = svc.charges_for_month(db, admin_user.school_id, 2026, 6)
    # 1-10 May is 10 of 31 days: 800 * 10 / 31 = 258.06 (half up).
    assert may[riders[0].id] == Decimal("258.06")
    assert riders[0].id not in june
    # The row survives, which is what "preserves history" means.
    assert db.get(TransportAssignment, row.id).end_reason == "moved house"


def test_ending_an_assignment_needs_a_reason(db, admin_user, route, riders):
    row = _assign(db, admin_user, route, riders[0])
    with pytest.raises(Exception) as e:
        svc.set_assignment_status(
            db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.ended
        )
    assert e.value.status_code == 422


def test_a_stop_with_no_slab_bills_nothing_rather_than_guessing(
    db, admin_user, route, riders
):
    """A stop nobody priced is a setup error, and the safe reading of it is
    zero. Inventing a figure would put a number on a parent's invoice that no
    fee card anywhere justifies."""
    route.stops[0].fee_slab_id = None
    db.flush()
    row = _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1))
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )
    assert riders[0].id not in svc.charges_for_month(db, admin_user.school_id, 2026, 4)


# --- expiry alerts ----------------------------------------------------------


def test_the_expiry_sweep_reports_lapsed_papers_as_well_as_lapsing_ones(
    db, admin_user, bus, driver
):
    """A permit that expired last week is more urgent than one expiring next
    month, so dropping it off the list the day it lapses is backwards."""
    doc = db.scalar(
        select(Document)
        .join(DocumentType, DocumentType.id == Document.document_type_id)
        .where(
            Document.owner_type == OwnerType.vehicle,
            Document.owner_id == bus.id,
            DocumentType.code == "vehicle_puc",
        )
    )
    doc.expires_on = LAST_MONTH
    db.flush()
    found = svc.expiring_papers(db, admin_user.school_id)
    puc = [f for f in found if f["code"] == "vehicle_puc" and f["owner_id"] == bus.id]
    assert len(puc) == 1
    assert puc[0]["days_left"] < 0
    assert puc[0]["owner"] == "UP32TT0001"


# --- the module switch and the permission gate ------------------------------


def test_the_transport_module_can_be_switched_off_at_the_api(client, db, admin, ids):
    assert client.get("/admin/transport/vehicles", headers=admin).status_code == 200
    db.execute(
        __import__("sqlalchemy").text(
            "UPDATE settings SET value = :v WHERE school_id = :s AND key = 'feature.transport'"
        ),
        {"v": "false", "s": ids["school"]},
    )
    db.flush()
    assert client.get("/admin/transport/vehicles", headers=admin).status_code == 404


def test_a_parent_sees_their_own_childs_bus_and_not_another_familys(
    client, db, admin_user, route, parent, other_parent
):
    """§5.6.8 gives a guardian their own child's route, stop and timing.

    The child is resolved from the API rather than picked out of the roster, so
    the positive half genuinely asserts something: a hard-coded enrolment that
    turned out not to be this parent's would make the test pass by returning
    nothing at all.
    """
    mine = client.get("/parent/children", headers=parent).json()
    assert mine, "the parent fixture has no children"
    student_id = mine[0]["id"]
    enrolment = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == student_id,
            Enrolment.status == EnrolmentStatus.active,
        )
    )
    # This child may already be one of the seed's thirty riders, and a child
    # may hold only one live assignment — which is the rule tested above.
    existing = db.scalar(
        select(TransportAssignment).where(
            TransportAssignment.enrolment_id == enrolment.id,
            TransportAssignment.status.in_(svc.LIVE),
        )
    )
    if existing is not None:
        svc.set_assignment_status(
            db,
            actor=admin_user,
            row=existing,
            new_status=TransportAssignmentStatus.ended,
            reason="moved to the test route",
        )
    row = _assign(db, admin_user, route, enrolment)
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )

    seen = client.get(f"/parent/children/{student_id}/transport", headers=parent)
    assert seen.status_code == 200
    assert seen.json()["stop"] == "Vibhuti Khand"
    assert seen.json()["pickup_time"].startswith("06:45")
    # And no family's stop appears in another family's answer.
    theirs = client.get(
        f"/parent/children/{student_id}/transport", headers=other_parent
    )
    assert theirs.status_code == 403


def test_a_teacher_cannot_run_the_transport_desk(client, teacher):
    r = client.post(
        "/admin/transport/vehicles",
        headers=teacher,
        json={"registration_no": "UP32QQ0000", "capacity": 30},
    )
    assert r.status_code == 403


# --- the fee opt-in ---------------------------------------------------------
#
# The one piece of new money-path code transport needed. `fees.generate()`
# billed every monthly item on a plan with no regard to the head's type, so
# putting the transport head on a plan charged every child in the school for
# the bus. `FeeHeadType.optional` existed and nothing read it.


@pytest.fixture()
def transport_on_the_plan(db, admin_user, slab):
    """Put the transport head on every class plan, as a school actually would.

    This is the arrangement that used to be a trap. Before the opt-in existed,
    these two lines were enough to bill a hundred families for a bus service
    two of them use.
    """
    head = db.scalar(
        select(FeeHead).where(
            FeeHead.school_id == admin_user.school_id, FeeHead.code == "TRANSPORT"
        )
    )
    assert head is not None and head.type is FeeHeadType.optional
    items = list(
        db.scalars(
            select(FeePlanItem).where(
                FeePlanItem.school_id == admin_user.school_id,
                FeePlanItem.fee_head_id == head.id,
            )
        )
    )
    assert items, "the seed puts the transport head on every class plan"
    for item in items:
        # A deliberately wrong, eye-catching number. Nothing should ever bill
        # it: the price comes from the slab on the stop the child boards at.
        item.amount = Decimal("9999.00")
        item.frequency = FeeFrequency.monthly
    db.flush()
    return head


def _future_month():
    """A month the seed has not already billed, so `generate` is not a no-op."""
    anchor = Date.today() + timedelta(days=200)
    return anchor.year, anchor.month


def _transport_lines(db, head_id, year, month):
    return dict(
        db.execute(
            select(FeeInvoice.enrolment_id, FeeInvoiceLine.amount)
            .join(FeeInvoiceLine, FeeInvoiceLine.invoice_id == FeeInvoice.id)
            .where(
                FeeInvoice.period_year == year,
                FeeInvoice.period_month == month,
                FeeInvoiceLine.fee_head_id == head_id,
            )
        ).all()
    )


def test_putting_transport_on_a_plan_does_not_charge_the_whole_school(
    db, admin_user, route, riders, transport_on_the_plan
):
    """The defect this opt-in exists to prevent, stated as a number.

    Two children ride the bus; the rest of the school does not. Before the
    change every active enrolment would have carried a Rs 9,999 transport line.
    """
    for enrolment in riders[:2]:
        row = _assign(db, admin_user, route, enrolment, start=Date(2026, 4, 1))
        svc.set_assignment_status(
            db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
        )
    year, month = _future_month()
    fees.generate(db, month, year, admin_user.school_id)

    charged = _transport_lines(db, transport_on_the_plan.id, year, month)
    # Exactly the children with a live assignment, and no others. Stated as
    # the invariant rather than as a count, because the demo school already
    # runs two routes with thirty children on them.
    riding = set(
        db.scalars(
            select(TransportAssignment.enrolment_id).where(
                TransportAssignment.school_id == admin_user.school_id,
                TransportAssignment.status == TransportAssignmentStatus.active,
            )
        )
    )
    assert set(charged) == riding
    assert {e.id for e in riders[:2]} <= set(charged)

    invoiced = db.scalar(
        select(func.count(FeeInvoice.id)).where(
            FeeInvoice.school_id == admin_user.school_id,
            FeeInvoice.period_year == year,
            FeeInvoice.period_month == month,
        )
    )
    # The point of the whole change: far more children were invoiced than were
    # charged for a bus. Before it, these two numbers were equal.
    assert invoiced > 50
    assert len(charged) < invoiced


def test_the_bus_is_priced_from_the_stop_not_from_the_plan(
    db, admin_user, route, riders, transport_on_the_plan
):
    """A twenty-kilometre ride is not the same money as a two-kilometre one.

    The plan item carries Rs 9,999 and nothing bills it: the amount comes from
    the slab on the stop the child actually boards at, which is what lets one
    transport head serve a dozen stops without a plan per stop.
    """
    far = TransportFeeSlab(
        school_id=admin_user.school_id,
        name="Test far",
        monthly_amount=Decimal("1500.00"),
    )
    db.add(far)
    db.flush()
    route.stops[1].fee_slab_id = far.id
    db.flush()

    near = _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1), seq=1)
    distant = _assign(db, admin_user, route, riders[1], start=Date(2026, 4, 1), seq=2)
    for row in (near, distant):
        svc.set_assignment_status(
            db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
        )

    year, month = _future_month()
    fees.generate(db, month, year, admin_user.school_id)
    charged = _transport_lines(db, transport_on_the_plan.id, year, month)
    assert charged[riders[0].id] == Decimal("800.00")
    assert charged[riders[1].id] == Decimal("1500.00")


def test_an_optional_head_with_no_opt_in_source_bills_nobody(
    db, admin_user, riders, transport_on_the_plan
):
    """The safe default for a head nobody wired up.

    A school that adds a `MEALS` head and forgets to connect it under-bills and
    finds out at the counter. The other direction charges four hundred families
    for a lunch nobody ordered, and they find out too, differently.
    """
    head = FeeHead(
        school_id=admin_user.school_id,
        name="Meals",
        code="MEALS",
        type=FeeHeadType.optional,
    )
    db.add(head)
    db.flush()
    for plan in db.scalars(
        select(FeePlan).where(FeePlan.school_id == admin_user.school_id)
    ):
        db.add(
            FeePlanItem(
                school_id=admin_user.school_id,
                fee_plan_id=plan.id,
                fee_head_id=head.id,
                amount=Decimal("1200.00"),
                frequency=FeeFrequency.monthly,
            )
        )
    db.flush()

    year, month = _future_month()
    fees.generate(db, month, year, admin_user.school_id)
    assert _transport_lines(db, head.id, year, month) == {}


def test_a_child_who_leaves_the_service_stops_being_billed_for_it(
    db, admin_user, route, riders, transport_on_the_plan
):
    """§5.6.9 with §0.6, through the real biller rather than through
    `charges_for_month` alone."""
    row = _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1))
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )
    year, month = _future_month()
    svc.set_assignment_status(
        db,
        actor=admin_user,
        row=row,
        new_status=TransportAssignmentStatus.ended,
        end_date=Date(year, month, 1) - timedelta(days=1),
        reason="left the school",
    )
    fees.generate(db, month, year, admin_user.school_id)
    assert riders[0].id not in _transport_lines(
        db, transport_on_the_plan.id, year, month
    )


def test_a_sibling_concession_comes_off_the_bus_fare_too(
    db, admin_user, route, transport_on_the_plan
):
    """Pinning a consequence rather than asserting a decision.

    §0.6's sibling concession is stored with a null `fee_head_id`, which means
    "every head". Transport is the first optional head that anything bills, so
    this is the first time that rule reaches a bus fare: 10% off Rs 800 is
    Rs 80. Defensible, but it fell out of an existing rule meeting a new line
    rather than anybody choosing it, so HANDOFF §8 item Q asks the owner. A
    school wanting the other answer can already scope a concession to a head.
    """
    younger = db.scalar(
        select(Enrolment)
        .join(FeeConcession, FeeConcession.enrolment_id == Enrolment.id)
        .where(
            FeeConcession.school_id == admin_user.school_id,
            FeeConcession.type == ConcessionType.sibling,
            FeeConcession.status == ConcessionStatus.approved,
            FeeConcession.fee_head_id.is_(None),
            Enrolment.status == EnrolmentStatus.active,
        )
    )
    assert younger is not None, "the seed grants at least one sibling concession"

    existing = db.scalar(
        select(TransportAssignment).where(
            TransportAssignment.enrolment_id == younger.id,
            TransportAssignment.status.in_(svc.LIVE),
        )
    )
    if existing is not None:
        svc.set_assignment_status(
            db,
            actor=admin_user,
            row=existing,
            new_status=TransportAssignmentStatus.ended,
            reason="moved to the test route",
        )
    row = _assign(db, admin_user, route, younger, start=Date(2026, 4, 1))
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )
    year, month = _future_month()
    fees.generate(db, month, year, admin_user.school_id)
    line = db.scalar(
        select(FeeInvoiceLine)
        .join(FeeInvoice, FeeInvoice.id == FeeInvoiceLine.invoice_id)
        .where(
            FeeInvoice.enrolment_id == younger.id,
            FeeInvoice.period_year == year,
            FeeInvoice.period_month == month,
            FeeInvoiceLine.fee_head_id == transport_on_the_plan.id,
        )
    )
    assert line.amount == Decimal("800.00")
    assert line.discount == Decimal("80.00")


def test_billing_the_bus_twice_still_bills_it_once(
    db, admin_user, route, riders, transport_on_the_plan
):
    """The idempotency the whole generator rests on is untouched by the opt-in:
    a retried batch job creates nothing the second time."""
    row = _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1))
    svc.set_assignment_status(
        db, actor=admin_user, row=row, new_status=TransportAssignmentStatus.active
    )
    year, month = _future_month()
    first = fees.generate(db, month, year, admin_user.school_id)
    second = fees.generate(db, month, year, admin_user.school_id)
    assert first["created"] > 0
    assert second["created"] == 0


# --- the admission form's transport tick box --------------------------------


def test_a_family_who_asked_for_the_bus_at_admission_reaches_a_queue(
    db, admin_user, route, riders
):
    """`applications.transport_required` finally goes somewhere.

    It has been captured on every application since Part 2 and read by nothing:
    a box a parent ticked that reached no screen and no list, so the office
    asked them again from scratch. It seeds a work queue rather than an
    assignment, because the form records *that* a family wants transport and
    never which stop — choosing one off a postal address would be a guess about
    a seven-year-old's walk to the bus.
    """
    from app.models import AdmissionCycle, Application, Gender

    cycle = db.scalar(
        select(AdmissionCycle).where(AdmissionCycle.school_id == admin_user.school_id)
    )
    assert cycle is not None, "the seed opens an admission cycle"
    student_id = db.get(Enrolment, riders[0].id).student_id
    db.add(
        Application(
            school_id=admin_user.school_id,
            cycle_id=cycle.id,
            first_name="Asked",
            last_name="For Transport",
            date_of_birth=Date(2016, 5, 4),
            gender=Gender.female,
            class_applying_for="1",
            transport_required=True,
            student_id=student_id,
        )
    )
    db.flush()

    waiting = svc.awaiting_assignment(db, admin_user.school_id)
    assert riders[0].id in {w["enrolment_id"] for w in waiting}

    # Once they are on a bus they leave the queue, which is what makes it a
    # queue rather than a list of everyone who ever asked.
    _assign(db, admin_user, route, riders[0])
    after = svc.awaiting_assignment(db, admin_user.school_id)
    assert riders[0].id not in {w["enrolment_id"] for w in after}


def test_a_family_who_did_not_ask_is_not_in_the_queue(db, admin_user, riders):
    waiting = svc.awaiting_assignment(db, admin_user.school_id)
    assert {w["enrolment_id"] for w in waiting} & {e.id for e in riders} == set()


def test_suspending_a_route_records_the_reason_a_person_gave(client, admin, db):
    """The audit trail must be the person's words, not the code's.

    `set_status` used to pass `f"route set to {new_status.value}"` as the
    reason, which restates `after` and answers nothing. Suspending a route
    stops children getting to school and the log is the only record of why.
    """
    from app.models import AuditAction, AuditLog, Route

    route = db.scalars(select(Route)).first()
    assert route is not None

    refused = client.patch(
        f"/admin/transport/routes/{route.id}/status",
        headers=admin,
        json={"status": "suspended"},
    )
    assert refused.status_code == 422, refused.text

    ok = client.patch(
        f"/admin/transport/routes/{route.id}/status",
        headers=admin,
        json={"status": "suspended", "reason": "Driver off sick, no cover"},
    )
    assert ok.status_code == 200, ok.text

    entry = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "route",
            AuditLog.entity_id == route.id,
            AuditLog.action == AuditAction.status_change,
        )
        .order_by(AuditLog.id.desc())
    ).first()
    assert entry is not None
    assert entry.reason == "Driver off sick, no cover", (
        f"the log recorded the code's words, not the clerk's: {entry.reason!r}"
    )


def test_pinning_a_stop_keeps_the_children_who_ride_from_it(client, admin, db):
    """Coordinates go on one row, not through the whole-list stop replace.

    `PUT /routes/{id}/stops` rebuilds every RouteStop as a new row, and its
    "children are assigned here" guard reads `id` off the incoming spec - which
    `StopIn` does not carry, so the keep-set is always empty and the route
    refuses outright once anyone rides it. Pinning a stop on a running route is
    the ordinary case, so it has its own route that updates in place.
    """
    from app.models import Route, RouteStop, TransportAssignment

    route = db.scalars(select(Route)).first()
    stop = sorted(route.stops, key=lambda s: s.sequence)[0]
    stop_id, before = stop.id, _live_on_stops_count(db, stop.id)

    r = client.patch(
        f"/admin/transport/stops/{stop_id}/location",
        headers=admin,
        json={"latitude": 26.8467, "longitude": 80.9462},
    )
    assert r.status_code == 200, r.text
    assert r.json()["latitude"] == 26.8467

    db.expire_all()
    again = db.get(RouteStop, stop_id)
    assert again is not None, "the stop was replaced rather than updated"
    assert again.latitude == 26.8467 and again.longitude == 80.9462
    assert _live_on_stops_count(db, stop_id) == before, (
        "riders lost their stop when it was pinned"
    )

    # And the coordinates reach the screen that draws the map.
    listed = client.get("/admin/transport/routes", headers=admin)
    assert listed.status_code == 200
    row = next(x for x in listed.json() if x["id"] == route.id)
    pinned = next(s for s in row["stops"] if s["id"] == stop_id)
    assert pinned["latitude"] == 26.8467


def _live_on_stops_count(db, stop_id: int) -> int:
    from app.models import TransportAssignment

    return len(
        list(db.scalars(select(TransportAssignment).where(
            TransportAssignment.route_stop_id == stop_id
        )))
    )


def test_a_stop_cannot_be_pinned_off_the_planet(client, admin, db):
    """The range lives in a CheckConstraint as well, because a latitude of 200
    is wrong for every caller and not only this route."""
    from app.models import Route

    route = db.scalars(select(Route)).first()
    stop = route.stops[0]

    for bad in ({"latitude": 200, "longitude": 80.9}, {"latitude": 26.8, "longitude": -900}):
        r = client.patch(
            f"/admin/transport/stops/{stop.id}/location", headers=admin, json=bad
        )
        assert r.status_code == 422, f"{bad} was accepted: {r.status_code}"


def test_one_school_cannot_pin_another_schools_stop(client, admin, db):
    """`db.get` by a bare id is the cross-tenant hole this project keeps
    finding; the route filters on the actor's school."""
    from app.models import RouteStop

    other = db.scalars(
        select(RouteStop).where(RouteStop.school_id != 1)
    ).first()
    if other is None:
        pytest.skip("no second school's stop in this fixture")

    r = client.patch(
        f"/admin/transport/stops/{other.id}/location",
        headers=admin,
        json={"latitude": 26.8, "longitude": 80.9},
    )
    assert r.status_code == 404, r.text
