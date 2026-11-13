from datetime import date, time
from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models import (
    AcademicYear,
    AcademicYearStatus,
    ClassSection,
    ConcessionStatus,
    ConcessionType,
    Enrolment,
    EnrolmentStatus,
    FeeConcession,
    FeeHead,
    FeePlan,
    Route,
    RouteStop,
    RouteStatus,
    StudentFeePlan,
    TransportAssignment,
    TransportAssignmentStatus,
    TransportDirection,
    Vehicle,
)
from app.services import promotion
from app.services.common import roster
from tests.test_promotion import make_section


@pytest.fixture()
def next_year(db, ids):
    year = AcademicYear(
        school_id=ids["school"],
        code="2026-27",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.planning,
    )
    db.add(year)
    db.flush()
    return year


def test_session_rollover_integrity(db, ids, next_year):
    school_id = ids["school"]
    target_section = make_section(db, next_year, "11")

    # 1. Setup target year FeePlan for class 11
    fee_plan_11 = FeePlan(
        school_id=school_id,
        academic_year_id=next_year.id,
        name="Class 11 Standard Plan",
        class_name="11",
        is_active=True,
    )
    db.add(fee_plan_11)

    # 2. Setup a FeeConcession for student 1 in Section 10-A
    section_10a_enrolments = roster(db, ids["section_10a"])
    student_1_enr = section_10a_enrolments[0]

    # Create fee head
    fee_head = db.scalar(select(FeeHead).where(FeeHead.school_id == school_id))
    if not fee_head:
        fee_head = FeeHead(
            school_id=school_id,
            name="Tuition",
            code="TUIT",
            is_active=True,
        )
        db.add(fee_head)
        db.flush()

    concession = FeeConcession(
        school_id=school_id,
        enrolment_id=student_1_enr.id,
        type=ConcessionType.scholarship,
        fee_head_id=fee_head.id,
        percent=Decimal("25.00"),
        amount=None,
        reason="Academic Excellence",
        status=ConcessionStatus.approved,
        valid_from=date(2025, 4, 1),
        valid_to=date(2027, 3, 31),
    )
    db.add(concession)

    # 3. Setup or retrieve TransportAssignment for student 1
    existing_ta = db.scalar(
        select(TransportAssignment).where(
            TransportAssignment.enrolment_id == student_1_enr.id,
            TransportAssignment.status.in_([
                TransportAssignmentStatus.active,
                TransportAssignmentStatus.requested,
                TransportAssignmentStatus.suspended,
            ]),
        )
    )
    if existing_ta:
        transport_assignment = existing_ta
        expected_stop_id = existing_ta.route_stop_id
    else:
        vehicle = Vehicle(
            school_id=school_id,
            registration_no="DL-01-AB-1234",
            capacity=40,
        )
        db.add(vehicle)
        db.flush()

        route = Route(
            school_id=school_id,
            name="Route 1 Morning",
            code="R1-M",
            vehicle_id=vehicle.id,
            status=RouteStatus.active,
        )
        db.add(route)
        db.flush()

        stop = RouteStop(
            school_id=school_id,
            route_id=route.id,
            sequence=1,
            name="Main Gate",
            pickup_time=time(7, 30),
        )
        db.add(stop)
        db.flush()

        transport_assignment = TransportAssignment(
            school_id=school_id,
            enrolment_id=student_1_enr.id,
            route_stop_id=stop.id,
            direction=TransportDirection.both,
            start_date=date(2025, 4, 1),
            status=TransportAssignmentStatus.active,
        )
        db.add(transport_assignment)
        db.flush()
        expected_stop_id = stop.id

    # Execute promotion commit
    plan = promotion.commit(db, ids["section_10a"], next_year.id)
    assert plan.can_commit

    # Fetch new enrolments in target year
    new_enrolments = db.scalars(
        select(Enrolment).where(Enrolment.academic_year_id == next_year.id)
    ).all()
    assert len(new_enrolments) > 0

    # 4. Assert all promoted students have active StudentFeePlan
    for new_enr in new_enrolments:
        sfp = db.scalar(
            select(StudentFeePlan).where(StudentFeePlan.enrolment_id == new_enr.id)
        )
        assert sfp is not None, f"Enrolment {new_enr.id} missing StudentFeePlan"
        assert sfp.fee_plan_id == fee_plan_11.id

    # 5. Assert student 1 has carried-forward FeeConcession
    new_student_1_enr = db.scalar(
        select(Enrolment).where(
            Enrolment.academic_year_id == next_year.id,
            Enrolment.student_id == student_1_enr.student_id,
        )
    )
    assert new_student_1_enr is not None

    new_concession = db.scalar(
        select(FeeConcession).where(
            FeeConcession.enrolment_id == new_student_1_enr.id,
            FeeConcession.status == ConcessionStatus.approved,
        )
    )
    assert new_concession is not None
    assert new_concession.percent == Decimal("25.00")
    assert new_concession.fee_head_id == fee_head.id
    assert new_concession.valid_from >= next_year.start_date

    # 6. Assert student 1 has carried-forward TransportAssignment
    new_transport = db.scalar(
        select(TransportAssignment).where(
            TransportAssignment.enrolment_id == new_student_1_enr.id,
            TransportAssignment.status == TransportAssignmentStatus.active,
        )
    )
    assert new_transport is not None
    assert new_transport.route_stop_id == expected_stop_id
    assert new_transport.start_date == next_year.start_date

    # 7. Assert old TransportAssignment was marked ended
    db.refresh(transport_assignment)
    assert transport_assignment.status == TransportAssignmentStatus.ended
    assert transport_assignment.end_date == next_year.start_date
    assert f"Promoted to {next_year.code}" in transport_assignment.end_reason


def test_session_rollover_detained_student(db, ids, next_year):
    school_id = ids["school"]
    target_11 = make_section(db, next_year, "11")
    repeat_10 = make_section(db, next_year, "10", section="A")

    # Fee plan for Class 10 in next year
    fee_plan_10 = FeePlan(
        school_id=school_id,
        academic_year_id=next_year.id,
        name="Class 10 Standard Plan",
        class_name="10",
        is_active=True,
    )
    db.add(fee_plan_10)

    # Detain second student
    enrolments = roster(db, ids["section_10a"])
    student_detained = enrolments[1]

    outcomes = {student_detained.student_id: "detain"}
    plan = promotion.commit(db, ids["section_10a"], next_year.id, outcomes=outcomes)
    assert plan.can_commit

    detained_enr = db.scalar(
        select(Enrolment).where(
            Enrolment.academic_year_id == next_year.id,
            Enrolment.student_id == student_detained.student_id,
        )
    )
    assert detained_enr is not None
    assert detained_enr.class_section_id == repeat_10.id

    # Detained student gets class 10 fee plan
    sfp = db.scalar(
        select(StudentFeePlan).where(StudentFeePlan.enrolment_id == detained_enr.id)
    )
    assert sfp is not None
    assert sfp.fee_plan_id == fee_plan_10.id
