from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models import (
    AuditAction,
    AuditLog,
    Enrolment,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    FeePaymentStatus,
    GeneralLedger,
    InvoiceStatus,
)
from app.services import fees as svc

NEXT_MONTH = {"month": 12, "year": 2026}


def enrolment_id(db, student_id: int) -> int:
    return db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == student_id)
    )


def test_cheque_payment_dishonour_flow(client, admin, db, ids):
    # 1. Generate invoices
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    initial_outstanding = svc.ledger(db, eid)["outstanding"]
    assert initial_outstanding > Decimal("0.00")

    # 2. Collect fee payment via cheque
    pay_res = client.post(
        "/admin/fees/payments",
        json={
            "enrolment_id": eid,
            "amount": "1500.00",
            "method": "cheque",
            "instrument_ref": "CHQ-889900",
            "idempotency_key": "test-cheque-pay-01",
        },
        headers=admin,
    )
    assert pay_res.status_code == 201
    payment_data = pay_res.json()
    payment_id = payment_data["id"]

    db.expire_all()
    ledger_after_pay = svc.ledger(db, eid)
    assert ledger_after_pay["outstanding"] == initial_outstanding - Decimal("1500.00")

    # 3. Dishonour the cheque payment
    dishonour_res = client.post(
        f"/admin/fees/payments/{payment_id}/dishonour",
        json={
            "reason": "Insufficient funds in drawer account",
            "bank_charge": "500.00",
        },
        headers=admin,
    )
    assert dishonour_res.status_code == 200
    res_body = dishonour_res.json()
    assert res_body["status"] == "dishonoured"
    assert res_body["bank_charge"] == 500.0

    # 4. Assert original payment is marked dishonoured
    db.expire_all()
    payment = db.get(FeePayment, payment_id)
    assert payment.status == FeePaymentStatus.dishonoured

    # 5. Assert contra payment exists
    contra = db.scalar(
        select(FeePayment).where(FeePayment.reverses_payment_id == payment_id)
    )
    assert contra is not None
    assert contra.amount == Decimal("-1500.00")
    assert contra.status == FeePaymentStatus.dishonoured

    # 6. Assert invoice balance is restored and penalty line added
    ledger_after_dishonour = svc.ledger(db, eid)
    # Outstanding should be initial_outstanding + 500.00 penalty
    assert ledger_after_dishonour["outstanding"] == initial_outstanding + Decimal("500.00")

    # 7. Assert GeneralLedger entries exist and balance
    gl_entries = db.scalars(
        select(GeneralLedger).where(GeneralLedger.reference_id == payment_id)
    ).all()
    assert len(gl_entries) == 4

    # Reversal entries (1500 AR debit, 1500 BANK credit)
    reversal_ar = next(e for e in gl_entries if e.account_code == "AR" and e.reference_type == "fee_payment_dishonour")
    assert reversal_ar.debit == Decimal("1500.00")
    assert reversal_ar.credit == Decimal("0.00")

    reversal_bank = next(e for e in gl_entries if e.account_code == "BANK" and e.reference_type == "fee_payment_dishonour")
    assert reversal_bank.debit == Decimal("0.00")
    assert reversal_bank.credit == Decimal("1500.00")

    # Penalty entries (500 AR debit, 500 PENALTY_INCOME credit)
    penalty_ar = next(e for e in gl_entries if e.account_code == "AR" and e.reference_type == "fee_payment_dishonour_penalty")
    assert penalty_ar.debit == Decimal("500.00")
    assert penalty_ar.credit == Decimal("0.00")

    penalty_income = next(e for e in gl_entries if e.account_code == "PENALTY_INCOME" and e.reference_type == "fee_payment_dishonour_penalty")
    assert penalty_income.debit == Decimal("0.00")
    assert penalty_income.credit == Decimal("500.00")

    # Assert total debit == total credit across GL entries
    total_debits = sum(e.debit for e in gl_entries)
    total_credits = sum(e.credit for e in gl_entries)
    assert total_debits == total_credits == Decimal("2000.00")

    # 8. Assert audit log was recorded
    audit_log = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "fee_payment",
            AuditLog.entity_id == payment_id,
            AuditLog.action == AuditAction.void,
        )
    ).first()
    assert audit_log is not None
    assert "Insufficient funds" in audit_log.reason


def test_cannot_dishonour_twice_or_negative_payment(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])

    pay_res = client.post(
        "/admin/fees/payments",
        json={
            "enrolment_id": eid,
            "amount": "1000.00",
            "method": "cheque",
            "instrument_ref": "CHQ-777",
            "idempotency_key": "test-cheque-pay-02",
        },
        headers=admin,
    )
    payment_id = pay_res.json()["id"]

    # First dishonour succeeds
    d1 = client.post(
        f"/admin/fees/payments/{payment_id}/dishonour",
        json={"reason": "Signature mismatch"},
        headers=admin,
    )
    assert d1.status_code == 200

    # Second dishonour fails with 409
    d2 = client.post(
        f"/admin/fees/payments/{payment_id}/dishonour",
        json={"reason": "Try again"},
        headers=admin,
    )
    assert d2.status_code == 409


def test_dishonour_requires_permission(client, teacher, db, ids):
    eid = enrolment_id(db, ids["student_1"])
    # Teacher does not have fees.payment.void permission
    res = client.post(
        "/admin/fees/payments/1/dishonour",
        json={"reason": "Unauthorized attempt"},
        headers=teacher,
    )
    assert res.status_code in (401, 403)
