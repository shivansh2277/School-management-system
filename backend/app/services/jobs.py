"""Enqueueing, claiming and running background jobs."""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobStatus, ScheduledJob, School, SchoolStatus

log = logging.getLogger("jobs")


def _utc(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes even for timestamptz columns, and
    comparing one against an aware `now` raises. Normalise on the way in."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

# kind -> handler(db, job) -> dict | None
HANDLERS: dict[str, Callable[[Session, Job], dict | None]] = {}


def handler(kind: str):
    """Register a job handler.

    A job whose kind has no handler is failed loudly rather than left pending
    forever, which is the quiet failure mode of most home-made queues.
    """

    def _wrap(fn):
        HANDLERS[kind] = fn
        return fn

    return _wrap


def enqueue(
    db: Session,
    kind: str,
    *,
    school_id: int,
    payload: dict | None = None,
    run_after: datetime | None = None,
    idempotency_key: str | None = None,
    max_attempts: int = 3,
    requested_by: int | None = None,
) -> Job | None:
    """Queue a job. Returns None when the idempotency key is already queued.

    Enqueue in the same transaction as the work that caused it: a job for a
    payment that then rolls back must not survive.
    """
    if idempotency_key is not None:
        existing = db.scalar(
            select(Job).where(Job.idempotency_key == idempotency_key)
        )
        if existing is not None:
            return None

    job = Job(
        school_id=school_id,
        kind=kind,
        payload=payload,
        status=JobStatus.pending,
        run_after=run_after or datetime.now(UTC),
        max_attempts=max_attempts,
        idempotency_key=idempotency_key,
        requested_by=requested_by,
    )
    db.add(job)
    db.flush()
    return job


def claim(db: Session) -> Job | None:
    """Take the oldest due job, locking it against other workers.

    SKIP LOCKED is what makes several workers safe: each takes a different row
    instead of queueing behind the same one. SQLite has neither, but it
    serialises writes anyway and only ever runs one worker in development.
    """
    q = (
        select(Job)
        .where(Job.status == JobStatus.pending, Job.run_after <= datetime.now(UTC))
        .order_by(Job.run_after, Job.id)
        .limit(1)
    )
    if db.bind is not None and db.bind.dialect.name != "sqlite":
        q = q.with_for_update(skip_locked=True)

    job = db.scalar(q)
    if job is None:
        return None

    job.status = JobStatus.running
    job.started_at = datetime.now(UTC)
    job.attempts += 1
    db.commit()
    return job


def run_one(db: Session, job: Job) -> None:
    """Execute a claimed job, recording success or failure either way."""
    fn = HANDLERS.get(job.kind)
    if fn is None:
        job.status = JobStatus.failed
        job.last_error = f"No handler registered for job kind {job.kind!r}"
        job.finished_at = datetime.now(UTC)
        db.commit()
        log.error("job %s: %s", job.id, job.last_error)
        return

    try:
        result = fn(db, job)
        job.result = result if isinstance(result, dict) else None
        job.status = JobStatus.done
        job.finished_at = datetime.now(UTC)
        db.commit()
        log.info("job %s (%s) done", job.id, job.kind)
    except Exception:  # noqa: BLE001 - a failing job must not stop the worker
        db.rollback()
        job = db.get(Job, job.id)
        job.last_error = traceback.format_exc(limit=8)
        if job.attempts >= job.max_attempts:
            job.status = JobStatus.failed
            job.finished_at = datetime.now(UTC)
            log.error("job %s (%s) failed permanently", job.id, job.kind)
        else:
            # Back off so a transient failure is retried later rather than
            # spinning: 1 minute, then 4, then 9.
            job.status = JobStatus.pending
            job.run_after = datetime.now(UTC) + timedelta(minutes=job.attempts**2)
            log.warning("job %s (%s) failed, retry %s", job.id, job.kind, job.attempts)
        db.commit()


def drain(db: Session, limit: int = 100) -> int:
    """Run every due job. Used by the worker loop and by the tests."""
    done = 0
    while done < limit:
        job = claim(db)
        if job is None:
            break
        run_one(db, job)
        done += 1
    return done


# (kind, every_minutes, at_hour). The migration inserts these too; keeping the
# list here as well is what lets a database built by `create_all` — every test
# database — have a schedule at all.
#
# **`at_hour` is compared against the UTC hour**, not the school's. The office
# these are timed for is UTC+5:30, so `2` fires at 07:30 in Lucknow and `6` at
# 11:30 — which is not what the comments below them used to claim, and is how
# `test_the_scheduler_queues_a_due_job_once_per_slot` came to fail for one hour
# a day. The hours are left as they are rather than quietly shifted: changing
# when a school's nightly sweep runs is the owner's call, and it is raised as
# HANDOFF §8 item R.
DEFAULT_SCHEDULES: list[tuple[str, int, int | None]] = [
    ("fees.overdue_sweep", 1440, 2),
    ("admission.offer_sweep", 1440, 6),
    # 01:00 UTC, 06:30 in the office: the compliance list is on the Transport
    # Manager's desk before the first bus leaves rather than after it.
    ("transport.document_expiry", 1440, 1),
    ("system.heartbeat", 60, None),
]


def install_schedules(db: Session) -> None:
    """Idempotent: adds any default schedule the database is missing, and
    leaves the timings of one already there alone — they are a school's to
    change."""
    have = set(db.scalars(select(ScheduledJob.kind)))
    for kind, every, hour in DEFAULT_SCHEDULES:
        if kind not in have:
            db.add(
                ScheduledJob(kind=kind, every_minutes=every, at_hour=hour, enabled=True)
            )
    db.flush()


def tick_schedules(db: Session, now: datetime | None = None) -> list[Job]:
    """Enqueue any recurring job that has come due.

    Idempotent by construction: the key includes the slot the job is due for, so
    a scheduler that runs twice in a minute still queues one job.
    """
    now = now or datetime.now(UTC)
    queued: list[Job] = []

    for sched in db.scalars(select(ScheduledJob).where(ScheduledJob.enabled)):
        next_run = _utc(sched.next_run_at)
        if next_run is not None and next_run > now:
            continue
        if sched.at_hour is not None and now.hour != sched.at_hour:
            # A daily job only becomes due in its hour.
            if sched.next_run_at is None:
                sched.next_run_at = now.replace(
                    hour=sched.at_hour, minute=0, second=0, microsecond=0
                )
                if sched.next_run_at <= now:
                    sched.next_run_at += timedelta(days=1)
            continue

        slot = now.strftime("%Y%m%d%H%M")
        # One job per school, not one job for school 1. The schedule is global
        # — "sweep overdue invoices nightly" — but the work is a tenant's, and
        # a hardcoded id both skipped every other customer and crashed outright
        # once school 1 no longer existed.
        for school_id in db.scalars(
            select(School.id).where(School.status == SchoolStatus.active)
        ):
            job = enqueue(
                db,
                sched.kind,
                school_id=school_id,
                payload=sched.payload,
                idempotency_key=f"sched:{sched.kind}:{school_id}:{slot}",
            )
            if job is not None:
                queued.append(job)
        sched.last_run_at = now
        sched.next_run_at = now + timedelta(minutes=sched.every_minutes)

    db.commit()
    return queued
