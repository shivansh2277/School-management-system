"""Job handlers.

Importing this module registers every handler, so both the worker and the tests
need only `import app.jobs`.
"""

from datetime import date as Date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    FeeInvoice,
    InvoiceStatus,
    Job,
    School,
    SchoolStatus,
)
from app.services import audit, fees
from app.services.jobs import handler


@handler("fees.overdue_sweep")
def overdue_sweep(db: Session, job: Job) -> dict:
    """Move pending invoices past their due date to overdue.

    v0 did this inside `to_out()`, which meant a GET wrote and committed — a
    side effect on a read, and the pattern that breaks first under concurrency
    (ERP_BLUEPRINT §2.5(7)). It belongs on a schedule.
    """
    today = Date.today()
    stale = list(
        db.scalars(
            select(FeeInvoice).where(
                FeeInvoice.school_id == job.school_id,
                FeeInvoice.status.in_(
                    (InvoiceStatus.issued, InvoiceStatus.partially_paid)
                ),
                FeeInvoice.due_date < today,
            )
        )
    )
    for invoice in stale:
        invoice.status = InvoiceStatus.overdue
    db.flush()

    # And charge the day's fine. §0.6, with §8 item C answered on
    # 7 September 2026: the clock keeps running until the invoice is paid, so
    # every unsettled invoice is reassessed, not only the ones billed this
    # month. The amount is a pure function of the dates, so a missed run
    # catches up rather than losing a day's accrual.
    unsettled = db.scalars(
        select(FeeInvoice).where(
            FeeInvoice.school_id == job.school_id,
            FeeInvoice.status.not_in(fees.DEAD),
            FeeInvoice.settled_on.is_(None),
            FeeInvoice.due_date < today,
        )
    ).all()
    fined = charged = 0
    for invoice in unsettled:
        amount = fees.assess_late_fee(db, invoice, today)
        if amount > 0:
            fined += 1
            charged += int(amount)
    db.flush()
    return {"marked_overdue": len(stale), "late_fees_charged": fined, "total": charged}


@handler("fees.generate_invoices")
def generate_invoices(db: Session, job: Job) -> dict:
    """Bill a period for a whole school.

    At 100 students this would fit in a request; at 2,000 with PDF receipts it
    would not, and the caller should not be waiting on it either way.
    """
    payload = job.payload or {}
    month = int(payload["month"])
    year = int(payload["year"])
    result = fees.generate(db, month, year, job.school_id)
    audit.record(
        db,
        actor=None,
        school_id=job.school_id,
        entity_type="fee_invoice_run",
        action=AuditAction.create,
        after={"month": month, "year": year, "created": result["created"]},
    )
    return result


@handler("admission.offer_sweep")
def offer_sweep(db: Session, job: Job) -> dict:
    """Expire lapsed offers and move the waitlist behind them.

    ERP_BLUEPRINT §5.1.2(6) calls this a large part of the module's value, and
    it is: without it a seat sits behind a family who stopped answering the
    phone in March, and everyone below them waits for nothing.
    """
    from app.services import selection

    return selection.expire_offers(db, job.school_id)


@handler("transport.document_expiry")
def transport_document_expiry(db: Session, job: Job) -> dict:
    """The nightly vehicle and crew compliance pass (§5.6.9).

    It reports rather than acts, and that is deliberate. Grounding a bus at
    03:00 because a certificate lapsed overnight would strand a hundred
    children at their stops with no warning to anybody. The hard refusal
    already sits on every path that *assigns* a vehicle or a driver; what was
    missing is the office finding out in time to renew.

    §5.6.9 asks for warnings at 60, 30 and 7 days. One pass reports everything
    inside the widest window and says how many days are left, rather than three
    schedules that each have to be kept in step with the other two. Papers that
    have already lapsed are included with a negative `days_left`: an expired
    permit is more urgent than one expiring next month, not less.
    """
    from app.services import transport

    found = transport.expiring_papers(db, job.school_id)
    return {
        "checked_on": str(Date.today()),
        "expiring": len(found),
        "already_expired": sum(1 for f in found if f["days_left"] < 0),
        "items": found,
    }


@handler("system.heartbeat")
def heartbeat(db: Session, job: Job) -> dict:
    """Proves the scheduler and worker are actually alive.

    Checkpoint 1 requires showing a job that runs without a request triggering
    it; this is the thing that demonstrates it, and it is cheap enough to leave
    running in production as a liveness signal.
    """
    active = db.scalar(
        select(School).where(School.status == SchoolStatus.active).limit(1)
    )
    return {"ok": True, "school": active.code if active else None}
