"""Period close, the day book, and the Checkpoint 3 money cycle.

§12: "a month is billed, partially paid, late-feed, chased, fully collected and
closed — and the closed period refuses further writes."
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

import app.jobs  # noqa: F401 - importing registers the handlers
from app.models import Enrolment, FeeInvoice, FeePeriodStatus, InvoiceStatus
from app.services import fees as svc
from app.services import jobs

MONTH = {"month": 12, "year": 2026}


def test_a_closed_month_refuses_to_be_billed_again(client, admin, db):
    client.post("/admin/fees/invoices/generate", json=MONTH, headers=admin)
    closed = client.post(
        "/admin/fees/periods/2026/12/close",
        json={"reason": "December books signed off"},
        headers=admin,
    )
    assert closed.status_code == 200 and closed.json()["status"] == FeePeriodStatus.closed

    again = client.post("/admin/fees/invoices/generate", json=MONTH, headers=admin)
    assert again.status_code == 409


def test_a_closed_month_refuses_money_dated_inside_it(client, admin, db, ids):
    """A receipt belongs to the day it was issued, so this is about the date of
    the payment, not about which invoice it settles."""
    eid = db.scalar(select(Enrolment.id).where(Enrolment.student_id == ids["student_1"]))
    today = date.today()
    client.post(
        f"/admin/fees/periods/{today.year}/{today.month}/close",
        json={"reason": "Month closed early for the audit"},
        headers=admin,
    )
    r = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "100.00", "idempotency_key": "closed-period"},
        headers=admin,
    )
    assert r.status_code == 409


def test_a_closed_month_refuses_a_void(client, admin, db, ids):
    client.post("/admin/fees/invoices/generate", json=MONTH, headers=admin)
    eid = db.scalar(select(Enrolment.id).where(Enrolment.student_id == ids["student_17"]))
    invoice = db.scalar(
        select(FeeInvoice).where(
            FeeInvoice.enrolment_id == eid, FeeInvoice.period_month == 12
        )
    )
    client.post(
        "/admin/fees/periods/2026/12/close",
        json={"reason": "December books signed off"},
        headers=admin,
    )
    r = client.post(
        f"/admin/fees/invoices/{invoice.id}/void",
        json={"reason": "Wrong plan"},
        headers=admin,
    )
    assert r.status_code == 409


def test_collecting_an_old_due_today_still_works(client, admin, db, ids):
    """§5.5.9's "late entries go into the current open period". Closing June
    must not make a June defaulter uncollectable in September."""
    eid = db.scalar(select(Enrolment.id).where(Enrolment.student_id == ids["student_1"]))
    oldest = svc.outstanding_invoices(db, eid)[0]
    client.post(
        f"/admin/fees/periods/{oldest.period_year}/{oldest.period_month}/close",
        json={"reason": "Books closed for that month"},
        headers=admin,
    )
    r = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "500.00", "idempotency_key": "old-due-today"},
        headers=admin,
    )
    assert r.status_code == 201, r.text


def test_reopening_is_allowed_and_audited(client, admin, db):
    from app.models import AuditLog

    client.post(
        "/admin/fees/periods/2026/12/close", json={"reason": "Signed off"}, headers=admin
    )
    r = client.post(
        "/admin/fees/periods/2026/12/reopen",
        json={"reason": "A cheque from November surfaced"},
        headers=admin,
    )
    assert r.status_code == 200 and r.json()["status"] == FeePeriodStatus.open
    entry = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == "fee_period")
        .order_by(AuditLog.id.desc())
    ).first()
    assert entry.reason == "A cheque from November surfaced"


def test_closing_without_a_reason_is_refused(client, admin):
    assert (
        client.post(
            "/admin/fees/periods/2026/12/close", json={"reason": ""}, headers=admin
        ).status_code
        == 422
    )


def test_the_daybook_adds_up_by_mode_and_by_cashier(client, admin, cashier, db, ids):
    eid = db.scalar(select(Enrolment.id).where(Enrolment.student_id == ids["student_1"]))
    client.post(
        "/admin/fees/payments",
        json={
            "enrolment_id": eid,
            "amount": "300.00",
            "method": "cash",
            "idempotency_key": "daybook-cash",
        },
        headers=cashier,
    )
    client.post(
        "/admin/fees/payments",
        json={
            "enrolment_id": eid,
            "amount": "200.00",
            "method": "upi",
            "idempotency_key": "daybook-upi",
        },
        headers=admin,
    )
    book = client.get("/admin/fees/daybook", headers=admin).json()
    assert Decimal(book["by_mode"]["cash"]) >= Decimal("300.00")
    assert Decimal(book["by_mode"]["upi"]) >= Decimal("200.00")
    assert Decimal(book["total"]) == sum(
        Decimal(v) for v in book["by_mode"].values()
    ), "the modes must add to the day's total"
    assert Decimal(book["total"]) == sum(Decimal(v) for v in book["by_cashier"].values())
    assert "Fee Counter Clerk" in book["by_cashier"]


def test_the_defaulter_list_is_worst_first_and_has_a_phone_number(client, admin):
    rows = client.get("/admin/fees/defaulters", headers=admin).json()
    assert rows, "the seed leaves some families unpaid on purpose"
    amounts = [Decimal(r["outstanding"]) for r in rows]
    assert amounts == sorted(amounts, reverse=True)
    assert all(r["months_due"] >= 1 for r in rows)
    with_contact = [r for r in rows if r["contact"] and r["contact"]["phone"]]
    assert with_contact, "a defaulter list without a contact is a report, not a chase"


def test_checkpoint_3_bill_part_pay_fine_chase_collect_close(
    client, admin, cashier, db, ids
):
    """§12 Checkpoint 3, end to end, with no manual database work.

    Bill a month, part-pay it, let the fine accrue, find the family on the
    defaulter list, collect the rest, close the month, and prove the closed
    month refuses the next write.
    """
    eid = db.scalar(select(Enrolment.id).where(Enrolment.student_id == ids["student_1"]))

    # clear the seeded history so the month under test stands alone
    owed = svc.ledger(db, eid)["outstanding"]
    if owed > 0:
        client.post(
            "/admin/fees/payments",
            json={"enrolment_id": eid, "amount": str(owed), "idempotency_key": "cp3-clear"},
            headers=cashier,
        )

    # 1. Bill.
    billed = client.post(
        "/admin/fees/invoices/generate", json={"month": 1, "year": 2027}, headers=admin
    ).json()
    assert billed["created"] >= 1
    db.expire_all()
    invoice = svc.outstanding_invoices(db, eid)[0]
    payable = svc.totals(db, invoice)["payable"]

    # 2. Part payment.
    part = client.post(
        "/admin/fees/payments",
        json={
            "enrolment_id": eid,
            "amount": "1000.00",
            "idempotency_key": "cp3-part-payment",
        },
        headers=cashier,
    )
    assert part.status_code == 201
    db.expire_all()
    assert svc.totals(db, db.get(FeeInvoice, invoice.id))["balance"] == payable - Decimal(
        "1000.00"
    )

    # 3. It falls overdue, and the sweep charges the fine.
    invoice = db.get(FeeInvoice, invoice.id)
    invoice.due_date = date.today() - timedelta(days=12)
    db.commit()
    jobs.enqueue(db, "fees.overdue_sweep", school_id=invoice.school_id)
    db.commit()
    jobs.drain(db)
    db.expire_all()

    invoice = db.get(FeeInvoice, invoice.id)
    fine = svc.late_fee_charged(db, invoice)
    assert fine == Decimal("1000.00"), "300 at day 5 plus seven further days"
    assert svc.invoice_out(db, invoice)["status"] == InvoiceStatus.overdue

    # 4. Chase: the family is on the defaulter list with the fine included.
    listed = client.get("/admin/fees/defaulters", headers=admin).json()
    row = next(r for r in listed if r["enrolment_id"] == eid)
    assert Decimal(row["late_fee"]) == fine
    assert row["days_overdue"] >= 12

    # 5. Collect the rest, fine and all.
    rest = svc.totals(db, invoice)["balance"]
    paid = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": str(rest), "idempotency_key": "cp3-final-pay"},
        headers=cashier,
    )
    assert paid.status_code == 201
    db.expire_all()
    invoice = db.get(FeeInvoice, invoice.id)
    assert svc.totals(db, invoice)["balance"] == 0
    assert invoice.status is InvoiceStatus.paid and invoice.settled_on is not None

    # the day's register shows both collections
    book = client.get("/admin/fees/daybook", headers=admin).json()
    assert Decimal(book["total"]) >= Decimal("1000.00") + rest

    # 6. Close the month the money landed in, and prove it refuses more.
    today = date.today()
    closed = client.post(
        f"/admin/fees/periods/{today.year}/{today.month}/close",
        json={"reason": "Checkpoint 3 close"},
        headers=admin,
    )
    assert closed.status_code == 200
    refused = client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "50.00", "idempotency_key": "cp3-after-close"},
        headers=cashier,
    )
    assert refused.status_code == 409, "a closed period must refuse further writes"
