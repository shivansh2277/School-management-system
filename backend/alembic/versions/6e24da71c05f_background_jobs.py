"""background jobs

A Postgres-backed queue and a schedule table (ERP_BLUEPRINT §0.1). Seeds the
recurring jobs a school needs from day one: the nightly overdue sweep that
replaces v0's write-inside-a-GET, and a heartbeat that proves the worker is
alive.

Revision ID: 6e24da71c05f
Revises: 5d13c9f6a8b4
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6e24da71c05f"
down_revision: str | None = "5d13c9f6a8b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_STATUS = sa.Enum(
    "pending", "running", "done", "failed", "cancelled",
    name="jobstatus", native_enum=False,
)


def _ts():
    return [
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("kind", sa.String(48), nullable=False),
        sa.Column("payload", sa.JSON()),
        sa.Column("status", _STATUS, nullable=False, server_default="pending"),
        sa.Column("run_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_error", sa.Text()),
        sa.Column("result", sa.JSON()),
        sa.Column("idempotency_key", sa.String(120), unique=True),
        sa.Column("requested_by", sa.BigInteger()),
        *_ts(),
    )
    op.create_index("ix_jobs_school_id", "jobs", ["school_id"])
    op.create_index("ix_jobs_claim", "jobs", ["status", "run_after"])
    op.create_index("ix_jobs_school_kind", "jobs", ["school_id", "kind"])

    op.create_table(
        "scheduled_jobs",
        sa.Column("kind", sa.String(48), nullable=False, unique=True),
        sa.Column("payload", sa.JSON()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("every_minutes", sa.Integer(), nullable=False, server_default="1440"),
        sa.Column("at_hour", sa.Integer()),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        *_ts(),
    )

    bind = op.get_bind()
    ins = sa.text(
        "INSERT INTO scheduled_jobs (kind, enabled, every_minutes, at_hour,"
        " created_at, updated_at) VALUES (:kind, :enabled, :every, :hour,"
        " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )
    # 02:00 IST: after the day's collections are in, before the office opens.
    bind.execute(
        ins, {"kind": "fees.overdue_sweep", "enabled": True, "every": 1440, "hour": 2}
    )
    bind.execute(
        ins, {"kind": "system.heartbeat", "enabled": True, "every": 60, "hour": None}
    )


def downgrade() -> None:
    op.drop_table("scheduled_jobs")
    op.drop_table("jobs")
