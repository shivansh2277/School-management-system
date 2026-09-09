"""Audit trail and gapless document numbering."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import AuditAction, AuditLog, FeePayment, NumberSequence
from app.services import audit


def test_deactivating_a_student_demands_a_reason(client, admin, db, ids):
    """The reason is the point of the entry, not the timestamp."""
    student_id = ids["student_1"]
    r = client.delete(f"/admin/students/{student_id}", headers=admin)
    assert r.status_code == 422  # reason is a required query parameter

    r = client.delete(
        f"/admin/students/{student_id}?reason=Left+the+city+mid-session",
        headers=admin,
    )
    assert r.status_code == 204

    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "student", AuditLog.entity_id == student_id
        )
    )
    assert entry is not None
    assert entry.action is AuditAction.status_change
    assert entry.reason == "Left the city mid-session"
    assert entry.actor_label == "Office Administrator"
    assert entry.before == {"is_active": True}
    assert entry.after == {"is_active": False}


def test_the_log_records_only_what_changed(db):
    before = {"name": "A", "city": "Lucknow", "phone": "1"}
    after = {"name": "B", "city": "Lucknow", "phone": "1"}
    row = audit.record(
        db,
        actor=None,
        school_id=1,
        entity_type="school",
        action=AuditAction.update,
        before=before,
        after=after,
    )
    assert row.before == {"name": "A"}
    assert row.after == {"name": "B"}


def test_a_reason_is_required_for_the_actions_that_need_one(db):
    for action in (AuditAction.void, AuditAction.status_change, AuditAction.delete):
        with pytest.raises(HTTPException) as e:
            audit.record(
                db,
                actor=None,
                school_id=1,
                entity_type="invoice",
                action=action,
            )
        assert e.value.status_code == 422

    # Ordinary changes do not need one — auditing everything with a mandatory
    # reason produces noise nobody reads.
    audit.record(
        db, actor=None, school_id=1, entity_type="invoice", action=AuditAction.update
    )


def test_paying_an_invoice_is_audited(client, parent, db):
    children = client.get("/parent/children", headers=parent).json()
    r = client.post(
        "/parent/fees/pay",
        json={
            "student_id": children[0]["id"],
            "amount": "100.00",
            "idempotency_key": "audit-payment",
        },
        headers=parent,
    )
    assert r.status_code == 201

    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "fee_payment",
            # the payment is the audited entity now, not the invoice: one
            # payment can settle several months
            AuditLog.entity_id == r.json()["id"],
        )
    )
    assert entry is not None
    assert entry.after["receipt_no"] == r.json()["receipt_no"]


def test_numbers_are_gapless_and_do_not_repeat(db):
    issued = [audit.next_number(db, 1, "test", 2026, prefix="T/", width=4) for _ in range(5)]
    assert issued == ["T/0001", "T/0002", "T/0003", "T/0004", "T/0005"]
    assert len(set(issued)) == 5


def test_sequences_are_separate_per_school_kind_and_year(db):
    a = audit.next_number(db, 1, "receipt", 2027, prefix="A/", width=3)
    b = audit.next_number(db, 1, "admission", 2027, prefix="B/", width=3)
    c = audit.next_number(db, 1, "receipt", 2028, prefix="C/", width=3)
    assert (a, b, c) == ("A/001", "B/001", "C/001")


def test_admission_numbers_are_ten_digits_encoding_the_joining_year(db):
    """YYYY + 6-digit sequence (ERP_BLUEPRINT §0.21). Ten digits, because
    office staff read this aloud and type it dozens of times a day."""
    first = audit.admission_number(db, 1, 2026)
    second = audit.admission_number(db, 1, 2026)

    assert first == "2026000001"
    assert second == "2026000002"
    assert len(first) == 10
    assert first.startswith("2026")

    # A new joining year restarts the sequence but stays unique overall.
    assert audit.admission_number(db, 1, 2027) == "2027000001"


def test_receipt_numbers_continue_from_the_seeded_history(client, parent, db):
    """The seed draws from the same counter, so the first payment afterwards
    does not collide with a receipt already issued."""
    existing = set(db.scalars(select(FeePayment.receipt_no)))
    children = client.get("/parent/children", headers=parent).json()

    receipt = client.post(
        "/parent/fees/pay",
        json={
            "student_id": children[0]["id"],
            "amount": "100.00",
            "idempotency_key": "receipt-continuity",
        },
        headers=parent,
    ).json()["receipt_no"]
    assert receipt not in existing

    seq = db.scalar(
        select(NumberSequence).where(
            NumberSequence.kind == "receipt", NumberSequence.school_id == 1
        )
    )
    assert seq is not None and seq.next_value > 1
