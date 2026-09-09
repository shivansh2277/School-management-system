"""Job handlers.

Importing this module registers every handler, so both the worker and the tests
need only `import app.jobs`.
"""

import logging
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

log = logging.getLogger("jobs.handlers")


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

    # And chase them. The sweep already knows exactly who is behind, so the
    # defaulter list is a query it has effectively just run — and
    # `comms.notify` addresses it through `fees.defaulters()`, the same
    # function the office's screen uses, so the families dunned are the
    # families listed (§5.10.9).
    #
    # `notify` returns None when the school has not written its own wording,
    # rather than failing the sweep. A school losing its overdue *marking*
    # because it never edited a template would be the tail wagging the dog.
    from app.services import comms

    # Caught deliberately. `jobs.run_one` rolls the transaction back when a
    # handler raises, so an exception from the chase would undo the overdue
    # marking and the late fees this sweep just computed — a communication
    # problem silently reversing the money work is precisely the coupling
    # §5.9.9 exists to prevent, one layer further in than the gateway timeout
    # it names. The failure is reported in the job result rather than dropped.
    chased, chase_error = 0, None
    try:
        chase = comms.notify(
            db,
            job.school_id,
            template_code="fees.overdue",
            audience={"kind": "defaulters"},
        )
        chased = len(chase.recipients) if chase else 0
    except Exception as exc:  # noqa: BLE001 - the money work must stand
        chase_error = f"{type(exc).__name__}: {exc}"[:300]
        log.warning("fee chase failed for school %s: %s", job.school_id, exc)

    return {
        "marked_overdue": len(stale),
        "late_fees_charged": fined,
        "total": charged,
        "chased": chased,
        "chase_error": chase_error,
    }


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


@handler("comms.dispatch")
def comms_dispatch(db: Session, job: Job) -> dict:
    """Send a message's queued recipients.

    This handler existing is the whole point of §5.9.9's first rule: a gateway
    timeout must never fail the action that triggered the message. Nothing in a
    route opens a socket to a mail server, so a parent's fee payment cannot
    fail because Brevo was slow.

    A message that has vanished is not an error worth failing the job over — it
    was cancelled, or the transaction that created it rolled back after the
    enqueue. Say so and move on.
    """
    from app.models import Message
    from app.services import comms

    message = db.get(Message, int((job.payload or {})["message_id"]))
    if message is None or message.school_id != job.school_id:
        return {"skipped": "message no longer exists"}
    return comms.dispatch(db, message)


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

    from app.services import comms

    found = transport.expiring_papers(db, job.school_id)
    expired = sum(1 for f in found if f["days_left"] < 0)

    # §5.6.9 wants the alert to reach the Transport Manager, and until
    # Communication landed this handler produced a payload with nowhere to send
    # it. Addressed by *permission* rather than by role name, so a school that
    # renames the role or splits it in two still reaches whoever actually holds
    # the job.
    # Same reason as the fee sweep: a handler that raises rolls its
    # transaction back, and the compliance list is worth having even on a day
    # the mail server is down.
    sent, notify_error = None, None
    try:
        sent = comms.notify(
            db,
            job.school_id,
            template_code="transport.compliance_alert",
            audience={"kind": "staff", "permission": "transport.setup.write"},
            extra={
                "expiring": str(len(found)),
                "already_expired": str(expired),
                "expiry_list": "\n".join(
                    f"- {f['owner']}: {f['document']} expires {f['expires_on']}"
                    f" ({f['days_left']} days)"
                    for f in found
                ),
            },
        ) if found else None
    except Exception as exc:  # noqa: BLE001 - the report must stand
        notify_error = f"{type(exc).__name__}: {exc}"[:300]
        log.warning("expiry alert failed for school %s: %s", job.school_id, exc)

    return {
        "checked_on": str(Date.today()),
        "expiring": len(found),
        "already_expired": expired,
        "notified": len(sent.recipients) if sent else 0,
        "notify_error": notify_error,
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
