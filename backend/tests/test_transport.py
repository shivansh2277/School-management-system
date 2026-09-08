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
from sqlalchemy import select

from app.models import (
    Document,
    DocumentType,
    Employee,
    Enrolment,
    EnrolmentStatus,
    OwnerType,
    Route,
    RouteStatus,
    Student,
    TransportAssignment,
    TransportAssignmentStatus,
    TransportDirection,
    TransportFeeSlab,
    User,
    Vehicle,
    VehicleStatus,
)
from app.services import documents, school_settings, transport as svc

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
        registration_no="UP32AB1234",
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
        school_id=admin_user.school_id, name="0-5 km", monthly_amount=Decimal("800.00")
    )
    db.add(s)
    db.flush()
    return s


@pytest.fixture()
def route(db, admin_user, bus, driver, slab):
    """An active route with two stops, ready to carry children."""
    r = Route(
        school_id=admin_user.school_id,
        code="R1",
        name="Gomti Nagar",
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
    svc.set_status(db, r, RouteStatus.active, admin_user)
    return r


@pytest.fixture()
def riders(db, ids):
    """Six active enrolments — more than the four-seat bus holds."""
    rows = list(
        db.scalars(
            select(Enrolment)
            .where(
                Enrolment.school_id == ids["school"],
                Enrolment.status == EnrolmentStatus.active,
            )
            .order_by(Enrolment.id)
            .limit(6)
        )
    )
    assert len(rows) == 6
    return rows


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
    svc.set_status(db, route, RouteStatus.planned, admin_user)
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
        school_id=admin_user.school_id, registration_no="UP32XY0001", capacity=2
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
        code="R9",
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
        svc.set_status(db, r, RouteStatus.active, admin_user)
    assert e.value.status_code == 409
    assert "Insurance expired" in e.value.detail


def test_a_paper_nobody_uploaded_is_a_refusal_not_a_pass(db, admin_user, driver):
    """Missing is at least as bad as expired.

    A bus with no insurance certificate on file is not safer than one whose
    certificate lapsed last week, and defaulting an absent paper to "fine" is
    how a compliance check quietly stops checking anything.
    """
    bare = Vehicle(
        school_id=admin_user.school_id, registration_no="UP32ZZ9999", capacity=10
    )
    db.add(bare)
    db.flush()
    r = Route(
        school_id=admin_user.school_id,
        code="R8",
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
        svc.set_status(db, r, RouteStatus.active, admin_user)
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
        code="R7",
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
        svc.set_status(db, r, RouteStatus.active, admin_user)
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
        school_id=admin_user.school_id, code="R2", name="Backwards", vehicle_id=bus.id,
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
        school_id=admin_user.school_id, code="R3", name="Overlap", vehicle_id=bus.id,
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
    assert "is on route R1" in e.value.detail


def test_a_second_trip_after_the_first_is_fine(db, admin_user, route, bus, driver):
    second = Route(
        school_id=admin_user.school_id, code="R4", name="Second trip",
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
        svc.set_status(db, route, RouteStatus.closed, admin_user)
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
    assert len(charges) == 2
    assert set(charges) == {e.id for e in riders[:2]}
    assert all(v == Decimal("800.00") for v in charges.values())


def test_a_requested_seat_is_not_a_billed_one(db, admin_user, route, riders):
    """A seat that has been asked for is not a service delivered."""
    _assign(db, admin_user, route, riders[0], start=Date(2026, 4, 1))
    assert svc.charges_for_month(db, admin_user.school_id, 2026, 5) == {}


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
    assert june == {}
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
    assert svc.charges_for_month(db, admin_user.school_id, 2026, 4) == {}


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
    assert puc[0]["owner"] == "UP32AB1234"


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
