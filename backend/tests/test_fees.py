"""The fee ledger: billing, part payment, allocation, reversal.

These are the money paths, so each test states the rule it defends rather than
just exercising the endpoint.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.models import (
    Enrolment,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    FeePaymentStatus,
    InvoiceStatus,
    PaymentAllocation,
)
from app.pdf.receipt import amount_in_words
from app.services import fees as svc

NEXT_MONTH = {"month": 12, "year": 2026}


def enrolment_id(db, student_id: int) -> int:
    return db.scalar(
        select(Enrolment.id).where(Enrolment.student_id == student_id)
    )


def test_amount_in_words_indian_numbering():
    assert amount_in_words(Decimal("2800.00")) == "Rupees Two Thousand Eight Hundred Only"
    assert amount_in_words(Decimal("100000")) == "Rupees One Lakh Only"
    assert amount_in_words(Decimal("2500.50")) == (
        "Rupees Two Thousand Five Hundred and Fifty Paise Only"
    )


def test_invoice_generation_is_idempotent(client, admin, db):
    first = client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin).json()
    second = client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin).json()
    active = db.scalar(select(func.count()).select_from(Enrolment))
    assert first["created"] == active and first["skipped"] == 0
    assert second["created"] == 0 and second["skipped"] == active


def test_an_invoice_has_lines_that_sum_to_its_payable(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    rows = client.get("/admin/fees/invoices?month=12&year=2026", headers=admin).json()
    invoice = rows[0]
    assert len(invoice["lines"]) == 2  # tuition and development
    net = sum(Decimal(line["net"]) for line in invoice["lines"])
    assert Decimal(invoice["payable"]) == net
    assert Decimal(invoice["charged"]) - Decimal(invoice["discount"]) == net


def test_the_sibling_concession_reaches_the_invoice(client, admin, db):
    """§0.6, end to end: an approved 10% concession comes off the bill, not off
    a report."""
    from app.models import ConcessionType, FeeConcession

    concession = db.scalar(
        select(FeeConcession).where(FeeConcession.type == ConcessionType.sibling)
    )
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    invoice = db.scalar(
        select(FeeInvoice).where(
            FeeInvoice.enrolment_id == concession.enrolment_id,
            FeeInvoice.period_month == 12,
        )
    )
    out = svc.invoice_out(db, invoice)
    expected = (Decimal(out["charged"]) * Decimal("0.10")).quantize(Decimal("0.01"))
    # per-line rounding, so allow the sum of two rounded lines
    assert abs(Decimal(out["discount"]) - expected) <= Decimal("0.01")
    assert Decimal(out["payable"]) == Decimal(out["charged"]) - Decimal(out["discount"])


def test_a_part_payment_reduces_the_balance_it_does_not_clear_the_invoice(
    client, admin, db, ids
):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    before = svc.ledger(db, eid)["outstanding"]
    assert before > 0

    r = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "500.00", "idempotency_key": "counter-part-one"},
        headers=admin,
    )
    assert r.status_code == 201
    db.expire_all()
    after = svc.ledger(db, eid)
    assert after["outstanding"] == before - Decimal("500.00")
    assert all(i["status"] != InvoiceStatus.paid for i in after["invoices"] if i["balance"] > 0)


def test_a_part_paid_invoice_that_is_not_yet_due_reads_partially_paid(
    client, admin, db, ids
):
    """`overdue` deliberately outranks `partially_paid` when an invoice is both
    — the defaulter list is what the office acts on — so this checks the status
    on an invoice whose due date has not passed."""
    eid = enrolment_id(db, ids["student_1"])
    owed = svc.ledger(db, eid)["outstanding"]
    if owed > 0:  # clear the seeded history first
        client.post(
            "/admin/fees/payments",
            json={"enrolment_id": eid, "amount": str(owed), "idempotency_key": "clear-history"},
            headers=admin,
        )
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    db.expire_all()

    invoice = svc.outstanding_invoices(db, eid)[0]
    assert invoice.due_date > date.today(), "December 2026 is not yet due"
    client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "500.00", "idempotency_key": "future-part-pay"},
        headers=admin,
    )
    db.expire_all()
    out = svc.invoice_out(db, db.get(FeeInvoice, invoice.id))
    assert out["status"] == InvoiceStatus.partially_paid
    assert out["paid"] == Decimal("500.00")


def test_a_payment_spans_two_invoices(client, admin, db, ids):
    """The rule the v0 UNIQUE(invoice_id) made impossible."""
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    outstanding = svc.outstanding_invoices(db, eid)
    assert len(outstanding) >= 2

    first_balance = svc.totals(db, outstanding[0])["balance"]
    amount = first_balance + Decimal("100.00")
    r = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": str(amount), "idempotency_key": "spanning-pay"},
        headers=admin,
    )
    payment_id = r.json()["id"]
    db.expire_all()

    touched = db.scalars(
        select(FeeInvoice.id)
        .join(FeeInvoiceLine, FeeInvoiceLine.invoice_id == FeeInvoice.id)
        .join(PaymentAllocation, PaymentAllocation.invoice_line_id == FeeInvoiceLine.id)
        .where(PaymentAllocation.payment_id == payment_id)
        .distinct()
    ).all()
    assert len(touched) == 2
    assert svc.totals(db, db.get(FeeInvoice, outstanding[0].id))["balance"] == 0


def test_a_repeated_idempotency_key_returns_the_first_receipt(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    body = {"enrolment_id": eid, "amount": "300.00", "idempotency_key": "tap-twice-key"}
    first = client.post("/admin/fees/payments", json=body, headers=admin).json()
    second = client.post("/admin/fees/payments", json=body, headers=admin).json()
    assert first["id"] == second["id"]
    assert first["receipt_no"] == second["receipt_no"]

    db.expire_all()
    total = db.scalar(
        select(func.coalesce(func.sum(FeePayment.amount), 0)).where(
            FeePayment.enrolment_id == eid, FeePayment.idempotency_key == "tap-twice-key"
        )
    )
    assert Decimal(total) == Decimal("300.00"), "the money must not be taken twice"


def test_overpayment_becomes_a_credit_and_settles_the_next_month(client, admin, db, ids):
    """§5.5.9: parents round up. That is a credit, not an error."""
    eid = enrolment_id(db, ids["student_17"])
    owed = svc.ledger(db, eid)["outstanding"]
    client.post(
        "/admin/fees/payments",
        json={
            "enrolment_id": eid,
            "amount": str(owed + Decimal("2000.00")),
            "idempotency_key": "round-up-key",
        },
        headers=admin,
    )
    db.expire_all()
    assert svc.credit_balance(db, eid) == Decimal("2000.00")

    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    db.expire_all()
    # the advance was applied to the new month without anyone asking
    assert svc.credit_balance(db, eid) < Decimal("2000.00")


def test_receipt_numbers_are_gapless_and_unique(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    issued = [
        client.post(
            "/admin/fees/payments",
            json={"enrolment_id": eid, "amount": "100.00", "idempotency_key": f"sequence-{n}"},
            headers=admin,
        ).json()["receipt_no"]
        for n in range(3)
    ]
    assert len(set(issued)) == 3
    assert all(r.startswith("SPS/RCP/") for r in issued)
    tail = [int(r.rsplit("/", 1)[1]) for r in issued]
    assert tail == list(range(tail[0], tail[0] + 3)), "an auditor asks about gaps"


def test_a_reversal_is_a_contra_entry_not_a_deletion(client, admin, cashier, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    payment = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "1000.00", "idempotency_key": "to-be-reversed"},
        headers=cashier,
    ).json()
    db.expire_all()
    owed_after_payment = svc.ledger(db, eid)["outstanding"]

    r = client.post(
        f"/admin/fees/payments/{payment['id']}/reverse",
        json={"reason": "Cheque returned unpaid"},
        headers=admin,
    )
    assert r.status_code == 200
    db.expire_all()

    original = db.get(FeePayment, payment["id"])
    assert original is not None, "the original payment row must survive"
    assert original.status is FeePaymentStatus.reversed
    assert original.amount == Decimal("1000.00")
    contra = db.get(FeePayment, r.json()["id"])
    assert contra.amount == Decimal("-1000.00")
    assert svc.ledger(db, eid)["outstanding"] == owed_after_payment + Decimal("1000.00")


def test_a_reversal_needs_a_reason(client, admin, cashier, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    payment = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "100.00", "idempotency_key": "reason-check"},
        headers=cashier,
    ).json()
    r = client.post(
        f"/admin/fees/payments/{payment['id']}/reverse", json={"reason": ""}, headers=admin
    )
    assert r.status_code == 422


def test_a_cashier_may_collect_but_not_void(client, admin, cashier, db, ids):
    """§5.5.9: whoever takes the money must not be able to cancel the record of
    it. Enforced by the role, and again by the API for anyone who holds both."""
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    payment = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "100.00", "idempotency_key": "self-reversal"},
        headers=cashier,
    ).json()
    # the cashier's role does not carry fees.payment.void at all
    assert (
        client.post(
            f"/admin/fees/payments/{payment['id']}/reverse",
            json={"reason": "Mistake at the counter"},
            headers=cashier,
        ).status_code
        == 403
    )
    # and an admin who does hold it still cannot reverse their own collection
    own = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "100.00", "idempotency_key": "admin-own-key"},
        headers=admin,
    ).json()
    assert (
        client.post(
            f"/admin/fees/payments/{own['id']}/reverse",
            json={"reason": "Mistake at the counter"},
            headers=admin,
        ).status_code
        == 403
    )


def test_an_invoice_with_money_against_it_cannot_be_voided(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_1"])
    invoice = svc.outstanding_invoices(db, eid)[0]
    client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "100.00", "idempotency_key": "block-voiding"},
        headers=admin,
    )
    r = client.post(
        f"/admin/fees/invoices/{invoice.id}/void",
        json={"reason": "Raised against the wrong class"},
        headers=admin,
    )
    assert r.status_code == 409


def test_a_voided_month_can_be_reissued(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    eid = enrolment_id(db, ids["student_17"])
    invoice = db.scalar(
        select(FeeInvoice).where(
            FeeInvoice.enrolment_id == eid, FeeInvoice.period_month == 12
        )
    )
    assert (
        client.post(
            f"/admin/fees/invoices/{invoice.id}/void",
            json={"reason": "Wrong fee plan applied"},
            headers=admin,
        ).status_code
        == 200
    )
    db.expire_all()
    again = client.post(
        "/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin
    ).json()
    assert again["created"] >= 1, "voiding must leave the month billable again"


def test_a_read_never_moves_a_stored_status(client, admin, db):
    """The v0 defect: `to_out()` committed from inside a GET."""
    invoice = db.scalar(select(FeeInvoice).where(FeeInvoice.status == InvoiceStatus.issued))
    if invoice is None:
        invoice = db.scalars(select(FeeInvoice)).first()
        invoice.status = InvoiceStatus.issued
        invoice.due_date = invoice.due_date.replace(year=2020)
        db.flush()
    stored = invoice.status
    rows = client.get("/admin/fees/invoices", headers=admin).json()
    shown = next(r for r in rows if r["id"] == invoice.id)
    db.expire_all()
    assert db.get(FeeInvoice, invoice.id).status is stored
    if invoice.due_date.year == 2020:
        assert shown["status"] == InvoiceStatus.overdue


def test_collection_totals_equal_the_allocations(client, admin, db):
    year = db.scalar(select(FeeInvoice.period_year))
    body = client.get(f"/admin/fees/collection?year={year}", headers=admin).json()
    expected = db.scalar(
        select(func.coalesce(func.sum(PaymentAllocation.amount), 0))
        .join(FeeInvoiceLine, FeeInvoiceLine.id == PaymentAllocation.invoice_line_id)
        .join(FeeInvoice, FeeInvoice.id == FeeInvoiceLine.invoice_id)
        .where(FeeInvoice.period_year == year)
    )
    assert Decimal(body["collected"]) == Decimal(expected)
    assert Decimal(body["outstanding"]) == Decimal(body["billed"]) - Decimal(body["collected"])


def test_a_parent_pays_and_gets_a_receipt_pdf(client, parent, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    children = client.get("/parent/children", headers=parent).json()
    student_id = children[0]["id"]
    r = client.post(
        "/parent/fees/pay",
        json={"student_id": student_id, "amount": "250.00", "idempotency_key": "parent-pay-key"},
        headers=parent,
    )
    assert r.status_code == 201
    payment_id = r.json()["id"]
    pdf = client.get(f"/parent/fees/receipts/{payment_id}.pdf", headers=parent)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_a_parent_cannot_see_another_familys_receipt(client, parent, other_parent, admin, db):
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    mine = client.get("/parent/children", headers=parent).json()[0]["id"]
    payment = client.post(
        "/parent/fees/pay",
        json={"student_id": mine, "amount": "100.00", "idempotency_key": "scope-checking"},
        headers=parent,
    ).json()
    r = client.get(f"/parent/fees/receipts/{payment['id']}.pdf", headers=other_parent)
    assert r.status_code in (403, 404)
