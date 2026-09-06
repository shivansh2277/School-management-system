"""Background jobs.

The ERP needs work that cannot happen inside a request: nightly invoice runs,
overdue sweeps, bulk import, report-card PDFs for a thousand students, email
dispatch. v0 ran on Vercel functions, which have no scheduler and no worker, and
the workaround was `refresh_overdue()` writing and committing inside a GET
(ERP_BLUEPRINT §2.5(7)).

The queue lives in Postgres rather than in Redis with Celery. For one school on
one box, `SELECT … FOR UPDATE SKIP LOCKED` is the standard pattern, needs no
extra service to run or monitor, and gives transactional enqueue for free — a
job queued in the same transaction as the work that caused it cannot be
orphaned by a rollback.

ponytail: single-process polling worker, ~1s latency. Move to Redis/Celery only
if throughput or fan-out actually demands it, not before.
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, TimestampedBase, enum_col
from app.models.enums import JobStatus


class Job(TenantBase):
    __tablename__ = "jobs"
    __table_args__ = (
        # The claim query's access path: due, pending, oldest first.
        Index("ix_jobs_claim", "status", "run_after"),
        Index("ix_jobs_school_kind", "school_id", "kind"),
    )

    kind: Mapped[str] = mapped_column(String(48), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[JobStatus] = enum_col(
        JobStatus, nullable=False, default=JobStatus.pending
    )

    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(nullable=False, default=3)
    last_error: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSON)

    # Set by the caller to make enqueueing idempotent: re-running a scheduler
    # tick must not queue the same nightly job twice.
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True)

    requested_by: Mapped[int | None] = mapped_column(BigInteger)


class ScheduledJob(TimestampedBase):
    """A recurring job. Deliberately not cron syntax — a school needs "every day
    at 02:00", not "*/7 3-5 * * 2", and an interval plus an hour is far easier
    for a non-technical administrator to read in a settings screen.
    """

    __tablename__ = "scheduled_jobs"

    kind: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    payload: Mapped[dict | None] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Run once per this many minutes; `at_hour` pins a daily job to a local hour.
    every_minutes: Mapped[int] = mapped_column(nullable=False, default=1440)
    at_hour: Mapped[int | None] = mapped_column()

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
