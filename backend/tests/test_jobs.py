"""Background jobs — the capability v0's serverless deployment could not have."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

import app.jobs  # noqa: F401  - registers the handlers
from app.models import FeeInvoice, InvoiceStatus, Job, JobStatus, ScheduledJob
from app.services import jobs
from app.services.jobs import handler


def test_a_queued_job_runs_and_records_its_result(db):
    job = jobs.enqueue(db, "system.heartbeat", school_id=1)
    db.commit()

    assert jobs.drain(db) == 1
    done = db.get(Job, job.id)
    assert done.status is JobStatus.done
    assert done.result == {"ok": True, "school": "SPS"}
    assert done.finished_at is not None


def test_an_idempotency_key_stops_a_duplicate(db):
    first = jobs.enqueue(db, "system.heartbeat", school_id=1, idempotency_key="nightly:1")
    second = jobs.enqueue(db, "system.heartbeat", school_id=1, idempotency_key="nightly:1")
    db.commit()

    assert first is not None
    assert second is None
    assert db.scalar(
        select(Job).where(Job.idempotency_key == "nightly:1")
    ) is not None


def test_a_job_is_not_claimed_before_it_is_due(db):
    jobs.enqueue(
        db,
        "system.heartbeat",
        school_id=1,
        run_after=datetime.now(UTC) + timedelta(hours=1),
    )
    db.commit()
    assert jobs.claim(db) is None


def test_an_unknown_kind_fails_loudly(db):
    """The quiet failure mode of home-made queues is a job that stays pending
    forever because nobody registered a handler."""
    job = jobs.enqueue(db, "does.not.exist", school_id=1)
    db.commit()
    jobs.drain(db)

    failed = db.get(Job, job.id)
    assert failed.status is JobStatus.failed
    assert "No handler registered" in failed.last_error


def test_a_failing_job_is_retried_then_given_up_on(db):
    calls = []

    @handler("test.always_fails")
    def _boom(_db, _job):
        calls.append(1)
        raise RuntimeError("nope")

    job = jobs.enqueue(db, "test.always_fails", school_id=1, max_attempts=2)
    db.commit()

    jobs.drain(db)
    after_first = db.get(Job, job.id)
    assert after_first.status is JobStatus.pending  # backed off for a retry
    assert after_first.attempts == 1

    # Bring the retry forward rather than waiting a real minute.
    after_first.run_after = datetime.now(UTC)
    db.commit()
    jobs.drain(db)

    after_second = db.get(Job, job.id)
    assert after_second.status is JobStatus.failed
    assert after_second.attempts == 2
    assert "nope" in after_second.last_error
    assert len(calls) == 2

    jobs.HANDLERS.pop("test.always_fails", None)


def test_the_overdue_sweep_moves_stale_invoices(db):
    """This is the job that replaces v0 writing from inside a GET."""
    invoice = db.scalar(
        select(FeeInvoice).where(FeeInvoice.status == InvoiceStatus.issued)
    )
    if invoice is None:
        invoice = db.scalars(select(FeeInvoice)).first()
        invoice.status = InvoiceStatus.issued
    invoice.due_date = datetime.now(UTC).date() - timedelta(days=10)
    db.commit()

    jobs.enqueue(db, "fees.overdue_sweep", school_id=1)
    db.commit()
    jobs.drain(db)

    assert db.get(FeeInvoice, invoice.id).status is InvoiceStatus.overdue


def test_reading_invoices_does_not_write(client, parent, db):
    """v0's to_out() persisted pending -> overdue, so a GET committed. A read
    must not have side effects."""
    invoice = db.scalars(select(FeeInvoice)).first()
    invoice.status = InvoiceStatus.issued
    invoice.due_date = datetime.now(UTC).date() - timedelta(days=5)
    db.commit()

    body = client.get("/parent/fees", headers=parent).json()
    row = next((i for i in body if i["id"] == invoice.id), None)

    # It still *presents* as overdue...
    if row is not None:
        assert row["status"] == "overdue"
    # ...but nothing was written; only the sweep changes stored state.
    db.expire_all()
    assert db.get(FeeInvoice, invoice.id).status is InvoiceStatus.issued


def _heartbeat(db):
    """The schedule the seed installs, rather than a second one inserted here:
    `kind` is unique, and the row that ships is the row worth testing."""
    from sqlalchemy import select

    sched = db.scalar(select(ScheduledJob).where(ScheduledJob.kind == "system.heartbeat"))
    assert sched is not None, "seed should install the default schedules"
    return sched


def test_the_scheduler_queues_a_due_job_once_per_slot(db):
    """One due schedule queues one job, and queues it once.

    The other schedules are switched off first, and that is not tidiness. They
    are daily jobs with an `at_hour`, and `admission.offer_sweep` runs at 06:00
    **UTC** — which is 11:30 in the office this is built for. Leaving them
    enabled made this test pass for twenty-three hours a day and fail during
    the twenty-fourth, on a machine whose clock nobody would think to blame.
    CI has never run; it would have found this at some point and it would not
    have been obvious.
    """
    from sqlalchemy import select

    for other in db.scalars(select(ScheduledJob)):
        other.enabled = False
    sched = _heartbeat(db)
    sched.enabled = True
    sched.next_run_at = None
    db.commit()

    now = datetime.now(UTC)
    first = jobs.tick_schedules(db, now)
    second = jobs.tick_schedules(db, now)  # same minute, same slot

    assert len(first) == 1
    assert first[0].kind == "system.heartbeat"
    assert second == []


def test_a_disabled_schedule_queues_nothing(db):
    from sqlalchemy import select

    for sched in db.scalars(select(ScheduledJob)):
        sched.enabled = False
    db.commit()
    assert jobs.tick_schedules(db, datetime.now(UTC)) == []


def test_a_schedule_queues_one_job_per_school(db):
    """The schedule is global — "sweep overdue invoices nightly" — but the work
    belongs to a tenant. This used to enqueue a single job hardcoded to
    school_id 1, which skipped every other customer and failed outright once
    school 1 was not the demo school any more."""
    from sqlalchemy import select

    from app.models import Job, School, SchoolStatus
    from tests.test_tenancy import make_school

    other, _ = make_school(db, code="SECOND", name="Second Public School")
    suspended, _ = make_school(db, code="THIRD", name="Third Public School")
    suspended.status = SchoolStatus.suspended

    sched = _heartbeat(db)
    sched.enabled = True
    sched.next_run_at = None
    db.commit()

    queued = jobs.tick_schedules(db, datetime.now(UTC))
    active = set(db.scalars(select(School.id).where(School.status == SchoolStatus.active)))
    assert {j.school_id for j in queued} == active
    assert other.id in active and suspended.id not in active
    assert all(isinstance(j, Job) for j in queued)
