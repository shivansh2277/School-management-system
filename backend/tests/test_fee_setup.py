"""The fee catalogue: heads, plans, assignment and concessions.

The money rules that Part 3's invoice generator will depend on. Every test here
either proves a §0.6 locked decision or an approval gate from §5.5.9.
"""

from decimal import Decimal

from sqlalchemy import select

from app.models import (
    ConcessionStatus,
    ConcessionType,
    Enrolment,
    FeeConcession,
    FeePlan,
    Student,
    StudentGuardian,
)
from app.services import fee_setup


def _head(client, admin, code="LAB"):
    return client.post(
        "/admin/fees/heads",
        json={"name": f"{code} Fee", "code": code, "type": "recurring"},
        headers=admin,
    ).json()


def test_a_fee_head_code_is_unique_within_a_school(client, admin):
    first = client.post(
        "/admin/fees/heads",
        json={"name": "Lab Fee", "code": "LAB1", "type": "recurring"},
        headers=admin,
    )
    assert first.status_code == 201
    again = client.post(
        "/admin/fees/heads",
        json={"name": "Laboratory", "code": "LAB1", "type": "optional"},
        headers=admin,
    )
    assert again.status_code == 409


def test_a_plan_cannot_carry_a_head_from_another_school(client, admin, db):
    year = db.scalar(select(FeePlan)).academic_year_id
    r = client.post(
        "/admin/fees/plans",
        json={
            "academic_year_id": year,
            "name": "Bogus plan",
            "items": [{"fee_head_id": 999999, "amount": "100.00"}],
        },
        headers=admin,
    )
    assert r.status_code == 404


def test_the_seeded_plan_totals_the_class_fee(client, admin, db):
    """Two lines, and they add back up to the flat amount they replaced."""
    plans = client.get("/admin/fees/plans", headers=admin).json()
    ten = next(p for p in plans if p["class_name"] == "10")
    assert len(ten["items"]) == 2
    assert Decimal(ten["monthly_total"]) == Decimal("2800.00")


def test_an_individual_assignment_overrides_the_class_plan(client, admin, db, ids):
    enrolment = db.scalar(
        select(Enrolment).where(Enrolment.student_id == ids["student_1"])
    )
    class_plan = fee_setup.plan_for(db, enrolment)
    assert class_plan.class_name == "10"

    other = db.scalar(select(FeePlan).where(FeePlan.class_name == "8"))
    r = client.post(
        "/admin/fees/assignments",
        json={"enrolment_id": enrolment.id, "fee_plan_id": other.id},
        headers=admin,
    )
    assert r.status_code == 201
    db.expire_all()
    assert fee_setup.plan_for(db, enrolment).id == other.id


def test_a_concession_needs_either_a_percent_or_an_amount(client, admin, db, ids):
    enrolment = db.scalar(
        select(Enrolment).where(Enrolment.student_id == ids["student_1"])
    )
    both = client.post(
        "/admin/fees/concessions",
        json={
            "enrolment_id": enrolment.id,
            "type": "scholarship",
            "reason": "Merit",
            "percent": "10",
            "amount": "100",
        },
        headers=admin,
    )
    assert both.status_code == 422


def test_a_requested_concession_does_not_reduce_anything_until_approved(
    client, admin, db, ids
):
    from datetime import date

    enrolment = db.scalar(
        select(Enrolment).where(Enrolment.student_id == ids["student_1"])
    )
    created = client.post(
        "/admin/fees/concessions",
        json={
            "enrolment_id": enrolment.id,
            "type": "scholarship",
            "reason": "District topper",
            "percent": "25",
        },
        headers=admin,
    ).json()
    assert created["status"] == "requested"
    live = fee_setup.concessions_for(db, [enrolment.id], date.today()).get(enrolment.id, [])
    assert all(c.type is not ConcessionType.scholarship for c in live)

    decided = client.post(
        f"/admin/fees/concessions/{created['id']}/decide",
        json={"approve": True, "reason": "Approved by the principal"},
        headers=admin,
    ).json()
    assert decided["status"] == "approved"
    db.expire_all()
    live = fee_setup.concessions_for(db, [enrolment.id], date.today())[enrolment.id]
    assert any(c.type is ConcessionType.scholarship for c in live)


def test_deciding_the_same_concession_twice_is_a_conflict(client, admin, db, ids):
    enrolment = db.scalar(
        select(Enrolment).where(Enrolment.student_id == ids["student_17"])
    )
    created = client.post(
        "/admin/fees/concessions",
        json={
            "enrolment_id": enrolment.id,
            "type": "management",
            "reason": "Trustee nomination",
            "amount": "500",
        },
        headers=admin,
    ).json()
    url = f"/admin/fees/concessions/{created['id']}/decide"
    assert client.post(url, json={"approve": True, "reason": "ok"}, headers=admin).status_code == 200
    assert client.post(url, json={"approve": False, "reason": "no"}, headers=admin).status_code == 409


def test_the_sibling_concession_is_ten_percent_and_skips_the_eldest(db):
    """§0.6. Siblings share a primary guardian; the eldest by admission number
    pays in full."""
    granted = db.scalars(
        select(FeeConcession).where(FeeConcession.type == ConcessionType.sibling)
    ).all()
    assert granted, "the seed should have granted at least one sibling concession"
    assert {c.percent for c in granted} == {Decimal("10.00")}
    assert {c.status for c in granted} == {ConcessionStatus.approved}

    for concession in granted:
        enrolment = db.get(Enrolment, concession.enrolment_id)
        guardian = db.scalar(
            select(StudentGuardian).where(
                StudentGuardian.student_id == enrolment.student_id,
                StudentGuardian.is_primary.is_(True),
            )
        )
        family = db.scalars(
            select(Student.admission_no)
            .join(StudentGuardian, StudentGuardian.student_id == Student.id)
            .where(
                StudentGuardian.guardian_id == guardian.guardian_id,
                StudentGuardian.is_primary.is_(True),
            )
        ).all()
        mine = db.get(Student, enrolment.student_id).admission_no
        assert mine != min(family), "the eldest child must not be discounted"


def test_the_sibling_sweep_is_idempotent(client, admin, db):
    before = db.scalar(
        select(FeeConcession.id).where(FeeConcession.type == ConcessionType.sibling).limit(1)
    )
    count = lambda: len(  # noqa: E731
        db.scalars(
            select(FeeConcession).where(FeeConcession.type == ConcessionType.sibling)
        ).all()
    )
    started_with = count()
    again = client.post("/admin/fees/concessions/sibling-sweep", headers=admin).json()
    db.expire_all()
    assert again["granted"] == 0
    assert count() == started_with
    assert before is not None


def test_a_percentage_discount_never_exceeds_the_line(db):
    """A 10% concession and a ₹5,000 one on a ₹2,000 line take the line to
    zero, not below it — a concession is a discount, not a credit note."""
    percent = FeeConcession(enrolment_id=1, type=ConcessionType.sibling, percent=Decimal("10"), reason="x")
    flat = FeeConcession(enrolment_id=1, type=ConcessionType.other, amount=Decimal("5000"), reason="x")
    line = Decimal("2000.00")
    assert fee_setup.discount_on(line, 1, [percent]) == Decimal("200.00")
    assert fee_setup.discount_on(line, 1, [percent, flat]) == line


def test_a_head_scoped_concession_leaves_other_heads_alone(db):
    transport_only = FeeConcession(
        enrolment_id=1, type=ConcessionType.other, fee_head_id=7, percent=Decimal("50"), reason="x"
    )
    assert fee_setup.discount_on(Decimal("1000.00"), 7, [transport_only]) == Decimal("500.00")
    assert fee_setup.discount_on(Decimal("1000.00"), 8, [transport_only]) == Decimal("0")
