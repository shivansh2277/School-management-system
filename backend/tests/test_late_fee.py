"""The late-fee rule of §0.6, and the §8 item C decision.

Locked on 7 September 2026: **the clock runs until the invoice is paid.**
Generating next month's invoice does not stop it. These tests exist so that
answer cannot be silently reversed by a later change.

Rule: nothing for 5 days, then ₹300, then +₹100 per further day, never more
than 50% of the invoice.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models import Enrolment, FeeInvoice, InvoiceStatus, Job
import app.jobs  # noqa: F401 - importing registers the handlers
from app.services import fees as svc
from app.services import jobs

RULES = {"grace_days": 5, "initial": 300, "per_day": 100, "cap_percent": 50}
DUE = date(2026, 6, 10)
NEXT_MONTH = {"month": 12, "year": 2026}


def a_clean_invoice(client, admin, db, student_id: int, overdue_days: int) -> FeeInvoice:
    """One invoice for one student and nothing else outstanding.

    The seed's own collection run assesses fines, so an arbitrary seeded
    invoice may already carry one. Clearing the ledger first is what makes the
    arithmetic below about this rule rather than about seed history.
    """
    eid = db.scalar(select(Enrolment.id).where(Enrolment.student_id == student_id))
    owed = svc.ledger(db, eid)["outstanding"]
    if owed > 0:
        client.post(
            "/admin/fees/payments",
            json={
                "enrolment_id": eid,
                "amount": str(owed),
                "idempotency_key": f"clear-{student_id}-{overdue_days}",
            },
            headers=admin,
        )
    client.post("/admin/fees/invoices/generate", json=NEXT_MONTH, headers=admin)
    db.expire_all()

    outstanding = svc.outstanding_invoices(db, eid)
    assert len(outstanding) == 1, "the ledger should hold exactly the new month"
    invoice = outstanding[0]
    invoice.due_date = date.today() - timedelta(days=overdue_days)
    invoice.status = InvoiceStatus.overdue
    db.flush()
    return invoice


def test_the_rule_day_by_day():
    """The arithmetic, in one place, against a fee big enough not to cap."""
    payable = Decimal("10000.00")
    fee = lambda days: svc.late_fee_due(payable, DUE, DUE + timedelta(days=days), RULES)  # noqa: E731

    assert fee(0) == Decimal("0.00"), "nothing on the due date"
    assert fee(4) == Decimal("0.00"), "still inside the grace period"
    assert fee(5) == Decimal("300.00"), "the flat charge lands on day 5"
    assert fee(6) == Decimal("400.00"), "then 100 per further day"
    assert fee(10) == Decimal("800.00")


def test_the_fee_is_capped_at_half_the_invoice():
    """Uncapped, 100/day passes a monthly fee inside two months."""
    payable = Decimal("2800.00")
    assert svc.late_fee_due(payable, DUE, DUE + timedelta(days=365), RULES) == payable / 2
    assert svc.late_fee_due(payable, DUE, DUE + timedelta(days=16), RULES) <= payable / 2


def test_a_payment_before_the_grace_period_ends_costs_nothing():
    assert svc.late_fee_due(Decimal("2800"), DUE, DUE + timedelta(days=3), RULES) == 0


def test_the_fine_is_a_line_on_the_invoice(client, admin, db, ids):
    """An ordinary line against an ordinary head, so it is paid, receipted and
    reported like any other charge rather than through a parallel mechanism."""
    invoice = a_clean_invoice(client, admin, db, ids["student_1"], overdue_days=8)
    before = svc.totals(db, invoice)["balance"]

    charged = svc.assess_late_fee(db, invoice, date.today())
    assert charged == Decimal("600.00"), "300 at day 5, plus three further days"

    db.refresh(invoice)
    late = [line for line in invoice.lines if line.description.startswith("Late fee")]
    assert len(late) == 1
    assert svc.totals(db, invoice)["balance"] == before + Decimal("600.00")


def test_reassessing_the_same_day_does_not_stack(client, admin, db, ids):
    invoice = a_clean_invoice(client, admin, db, ids["student_1"], overdue_days=8)
    for _ in range(3):
        svc.assess_late_fee(db, invoice, date.today())
    db.refresh(invoice)
    late = [line for line in invoice.lines if line.description.startswith("Late fee")]
    assert len(late) == 1 and late[0].amount == Decimal("600.00")


def test_the_clock_keeps_running_after_the_next_invoice_is_generated(
    client, admin, db, ids
):
    """§8 item C, the locked answer. If generating a newer invoice stopped the
    clock, the fine below would stay at its day-8 value."""
    invoice = a_clean_invoice(client, admin, db, ids["student_1"], overdue_days=8)
    assert svc.assess_late_fee(db, invoice, date.today()) == Decimal("600.00")
    db.commit()

    client.post(
        "/admin/fees/invoices/generate", json={"month": 1, "year": 2027}, headers=admin
    )
    db.expire_all()

    invoice = db.get(FeeInvoice, invoice.id)
    later = svc.assess_late_fee(db, invoice, date.today() + timedelta(days=4))
    assert later == Decimal("1000.00"), "a newer invoice must not freeze the old fine"


def test_paying_stops_the_clock(client, admin, db, ids):
    invoice = a_clean_invoice(client, admin, db, ids["student_17"], overdue_days=8)
    eid = invoice.enrolment_id
    db.commit()

    # collect() assesses first, so ask the ledger what is owed *after* that
    svc.assess_late_fee(db, invoice, date.today())
    db.commit()
    owed = svc.totals(db, invoice)["balance"]
    client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": str(owed), "idempotency_key": "settle-the-fine"},
        headers=admin,
    )
    db.expire_all()

    invoice = db.get(FeeInvoice, invoice.id)
    assert invoice.settled_on is not None
    frozen = svc.late_fee_charged(db, invoice)
    assert frozen == Decimal("600.00")
    # a month later the fine on a paid invoice has not moved
    assert svc.assess_late_fee(db, invoice, date.today() + timedelta(days=30)) == frozen
    db.refresh(invoice)
    assert svc.late_fee_charged(db, invoice) == frozen


def test_the_counter_charges_the_fine_owed_today_not_at_the_last_sweep(
    client, admin, db, ids
):
    """A parent paying on a day the sweep has not run must still be asked for
    the current fine."""
    invoice = a_clean_invoice(client, admin, db, ids["student_17"], overdue_days=9)
    eid = invoice.enrolment_id
    db.commit()
    assert svc.late_fee_charged(db, invoice) == 0, "no sweep has run"

    client.post(
        "/admin/fees/payments",
        json={"enrolment_id": eid, "amount": "1.00", "idempotency_key": "counter-assess"},
        headers=admin,
    )
    db.expire_all()
    invoice = db.get(FeeInvoice, invoice.id)
    assert svc.late_fee_charged(db, invoice) == Decimal("700.00")  # 300 + four days


def test_the_fee_rule_is_configuration_not_code(client, admin, db, ids):
    """§3.15: a school changes the rule without a deployment."""
    r = client.put(
        "/admin/configuration",
        json={"values": {"fees.late_fee.initial": 500, "fees.late_fee.per_day": 50}},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    invoice = a_clean_invoice(client, admin, db, ids["student_1"], overdue_days=7)
    assert svc.assess_late_fee(db, invoice, date.today()) == Decimal("600.00")  # 500 + 2×50


def test_lowering_the_rule_does_not_refund_a_fine_already_charged(client, admin, db, ids):
    invoice = a_clean_invoice(client, admin, db, ids["student_1"], overdue_days=8)
    charged = svc.assess_late_fee(db, invoice, date.today())
    db.commit()

    client.put(
        "/admin/configuration",
        json={"values": {"fees.late_fee.initial": 0, "fees.late_fee.per_day": 0}},
        headers=admin,
    )
    db.expire_all()
    invoice = db.get(FeeInvoice, invoice.id)
    svc.assess_late_fee(db, invoice, date.today())
    db.refresh(invoice)
    # Waiving a fine is a concession and needs approval; it is not a side
    # effect of editing a setting.
    assert svc.late_fee_charged(db, invoice) == charged


def test_the_sweep_charges_and_reports(client, admin, db, ids):
    invoice = a_clean_invoice(client, admin, db, ids["student_1"], overdue_days=20)
    school_id = invoice.school_id
    db.commit()

    jobs.enqueue(db, "fees.overdue_sweep", school_id=school_id)
    db.commit()
    jobs.drain(db)

    done = db.scalars(
        select(Job).where(Job.kind == "fees.overdue_sweep").order_by(Job.id.desc())
    ).first()
    assert done.result["late_fees_charged"] >= 1
    assert done.result["total"] > 0
    db.expire_all()
    assert svc.late_fee_charged(db, db.get(FeeInvoice, invoice.id)) > 0
