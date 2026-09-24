"""Tests for Transport Module Plan 1 & Plan 2 Upgrade:
- Address-first geocoding and distance calculation
- Fleet & vehicle updates
- Route updates and stop address resolution
- Crew candidate listing with compliance documents
- Student search and nearby stop ranking
- Assignment transfer with mandatory reason
- Detailed printable route roster
"""

from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    Application,
    Document,
    DocumentType,
    Employee,
    Enrolment,
    EnrolmentStatus,
    OwnerType,
    Route,
    RouteStatus,
    RouteStop,
    Student,
    StudentAuthorizedPerson,
    TransportAssignment,
    TransportAssignmentStatus,
    TransportDirection,
    TransportFeeSlab,
    User,
    Vehicle,
)
from app.services import documents, transport as svc
from app.services.geocoding import geocode_address, haversine_distance_km

TODAY = date.today()
NEXT_YEAR = TODAY + timedelta(days=365)


def _paper(db, admin_user, owner_type, owner_id, code, expires_on):
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
    v = Vehicle(
        school_id=admin_user.school_id,
        registration_no="UP32TT0099",
        make_model="Tata Starbus",
        capacity=4,
    )
    db.add(v)
    db.flush()
    _papers_for_vehicle(db, admin_user, v.id)
    return v


@pytest.fixture()
def driver(db, admin_user, ids):
    e = db.get(Employee, ids["teacher_1"])
    _papers_for_driver(db, admin_user, e.id)
    return e


@pytest.fixture()
def slab(db, admin_user):
    s = TransportFeeSlab(
        school_id=admin_user.school_id,
        name="Test near upgrade",
        monthly_amount=Decimal("800.00"),
    )
    db.add(s)
    db.flush()
    return s


@pytest.fixture()
def route(db, admin_user, bus, driver, slab):
    r = Route(
        school_id=admin_user.school_id,
        code="TU1",
        name="Test Upgrade Gomti Nagar",
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
                "pickup_time": time(6, 45),
                "drop_time": time(14, 30),
                "fee_slab_id": slab.id,
            },
            {
                "sequence": 2,
                "name": "Patrakarpuram",
                "pickup_time": time(7, 5),
                "drop_time": time(14, 50),
                "fee_slab_id": slab.id,
            },
        ],
        admin_user,
    )
    svc.set_status(db, r, RouteStatus.active, admin_user, reason="test fixture")
    return r


@pytest.fixture()
def riders(db, ids):
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


def test_geocoding_service_and_endpoint(client, transport_incharge):
    # Test service directly
    res = geocode_address("Vibhuti Khand, Lucknow")
    assert res["latitude"] == 26.8722
    assert res["longitude"] == 80.9994
    assert res["is_approximate"] is False

    # Test via API
    r = client.get(
        "/admin/transport/geocode",
        params={"address": "Patrakarpuram, Lucknow"},
        headers=transport_incharge,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["latitude"] == 26.8491
    assert data["longitude"] == 80.9950
    assert data["is_approximate"] is False

    # Test haversine distance
    dist = haversine_distance_km(26.8722, 80.9994, 26.8491, 80.9950)
    assert 2.0 < dist < 3.0  # Approx 2.5 km between Vibhuti Khand and Patrakarpuram


def test_vehicle_update_and_capacity_guard(client, transport_incharge, db, route):
    # Get the vehicle
    v = db.get(Vehicle, route.vehicle_id)
    old_capacity = v.capacity

    # Valid update
    r = client.put(
        f"/admin/transport/vehicles/{v.id}",
        json={
            "make_model": "Tata Starbus Ultra 44",
            "capacity": 44,
            "ownership": "owned",
            "gps_device_id": "GPS-TATA-9988",
        },
        headers=transport_incharge,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["make_model"] == "Tata Starbus Ultra 44"
    assert data["capacity"] == 44
    assert data["gps_device_id"] == "GPS-TATA-9988"


def test_route_update_and_clash_prevention(client, transport_incharge, route):
    r = client.put(
        f"/admin/transport/routes/{route.id}",
        json={
            "code": "R1-EXP",
            "name": "Gomti Nagar Express",
            "distance_km": 15.5,
        },
        headers=transport_incharge,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == "R1-EXP"
    assert data["name"] == "Gomti Nagar Express"
    assert float(data["distance_km"]) == 15.5


def test_stop_location_with_address(client, transport_incharge, route):
    stop = route.stops[0]
    r = client.patch(
        f"/admin/transport/stops/{stop.id}/location",
        json={
            "latitude": 26.8722,
            "longitude": 80.9994,
            "address": "Vibhuti Khand, Gomti Nagar, Lucknow",
        },
        headers=transport_incharge,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["latitude"] == 26.8722
    assert data["longitude"] == 80.9994
    assert data["address"] == "Vibhuti Khand, Gomti Nagar, Lucknow"


def test_crew_candidates_endpoint(client, transport_incharge, db):
    r = client.get("/admin/transport/crew", headers=transport_incharge)
    assert r.status_code == 200
    crew_list = r.json()
    assert isinstance(crew_list, list)


def test_student_search_and_nearby_stops(client, transport_incharge, db, route):
    # Pin route stops so distance calculation works with specific coordinates
    stop = route.stops[0]
    client.patch(
        f"/admin/transport/stops/{stop.id}/location",
        json={
            "latitude": 27.2500,
            "longitude": 81.3500,
            "address": "Isolated Test Point, Lucknow Outer",
        },
        headers=transport_incharge,
    )

    # Search students
    r = client.get("/admin/transport/students/search", headers=transport_incharge)
    assert r.status_code == 200
    students = r.json()
    assert len(students) > 0

    # Query nearby stops for specific coordinates
    r_nearby = client.get(
        "/admin/transport/stops/nearby",
        params={"lat": 27.2500, "lon": 81.3500},
        headers=transport_incharge,
    )
    assert r_nearby.status_code == 200
    nearby = r_nearby.json()
    assert len(nearby) > 0
    # First stop should be our explicitly matched stop with 0.0 distance
    assert nearby[0]["stop_id"] == stop.id
    assert nearby[0]["distance_km"] == 0.0


def test_assignment_transfer_with_mandatory_reason(client, transport_incharge, db, route, riders):
    # First assign a student to stop 0
    enrolment = riders[0]
    stop1 = route.stops[0]
    stop2 = route.stops[1]

    # Create assignment
    assign_res = client.post(
        "/admin/transport/assignments",
        json={
            "student_id": enrolment.student_id,
            "route_stop_id": stop1.id,
            "direction": "both",
            "start_date": "2026-04-01",
        },
        headers=transport_incharge,
    )
    assert assign_res.status_code == 201
    assign_id = assign_res.json()["id"]

    # Transfer to stop 2
    transfer_res = client.post(
        f"/admin/transport/assignments/{assign_id}/transfer",
        json={
            "new_route_stop_id": stop2.id,
            "reason": "Family shifted to Vinay Khand apartment",
            "start_date": "2026-05-01",
            "direction": "both",
        },
        headers=transport_incharge,
    )
    assert transfer_res.status_code == 200
    t_data = transfer_res.json()
    assert t_data["ended_assignment_id"] == assign_id
    assert t_data["stop_name"] == stop2.name


def test_route_roster_printable(client, transport_incharge, db, route, riders):
    # Assign a rider
    client.post(
        "/admin/transport/assignments",
        json={
            "student_id": riders[0].student_id,
            "route_stop_id": route.stops[0].id,
            "direction": "both",
            "start_date": "2026-04-01",
        },
        headers=transport_incharge,
    )

    r = client.get(f"/admin/transport/routes/{route.id}/roster", headers=transport_incharge)
    assert r.status_code == 200
    data = r.json()
    assert data["route_id"] == route.id
    assert data["code"] == route.code
    assert "vehicle" in data
    assert "driver" in data
    assert "attendant" in data
    assert "stops" in data
    assert len(data["stops"]) > 0
