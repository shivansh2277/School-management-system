"""Enqueueing, claiming and running background jobs."""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobStatus, ScheduledJob

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
        job = enqueue(
            db,
            sched.kind,
            school_id=(sched.payload or {}).get("school_id", 1),
            payload=sched.payload,
            idempotency_key=f"sched:{sched.kind}:{slot}",
        )
        sched.last_run_at = now
        sched.next_run_at = now + timedelta(minutes=sched.every_minutes)
        if job is not None:
            queued.append(job)

    db.commit()
    return queued
