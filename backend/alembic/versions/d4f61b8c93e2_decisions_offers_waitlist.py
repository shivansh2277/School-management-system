"""admission decisions, offers and the waitlist

ERP_BLUEPRINT §5.1.5. `admission_decisions.reason` is NOT NULL on purpose:
§5.1.9(13) requires a reason for every decision including the admits, and
`admission_offers.expires_on` is NOT NULL for the same kind of reason — an
offer without one holds a seat forever and the waitlist behind it never moves.

Revision ID: d4f61b8c93e2
Revises: c3e58f24d1a7
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4f61b8c93e2"
down_revision: str | None = "c3e58f24d1a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OUTCOME = sa.Enum(
    "admitted", "waitlisted", "rejected", name="decisionoutcome", native_enum=False
)
_OFFER = sa.Enum(
    "issued", "accepted", "declined", "expired", "withdrawn",
    name="offerstatus", native_enum=False,
)
_WAITLIST = sa.Enum(
    "waiting", "offered", "converted", "lapsed", "withdrawn",
    name="waitliststatus", native_enum=False,
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
        "admission_decisions",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("decision", _OUTCOME, nullable=False),
        sa.Column("decided_by", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("seat_category", sa.String(20)),
        sa.Column("conditions", sa.Text()),
        sa.Column(
            "over_allocation_approved", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        *_ts(),
    )
    op.create_index(
        "ix_admission_decisions_school_id", "admission_decisions", ["school_id"]
    )
    op.create_index(
        "ix_decision_application", "admission_decisions", ["application_id", "decided_at"]
    )

    op.create_table(
        "admission_offers",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("offered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("offer_amount", sa.Numeric(10, 2)),
        sa.Column("status", _OFFER, nullable=False, server_default="issued"),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        *_ts(),
    )
    op.create_index("ix_admission_offers_school_id", "admission_offers", ["school_id"])
    op.create_index(
        "ix_admission_offers_application_id", "admission_offers", ["application_id"]
    )
    op.create_index(
        "ix_offer_expiry", "admission_offers", ["school_id", "status", "expires_on"]
    )

    op.create_table(
        "waitlist_entries",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "cycle_id", sa.BigInteger(), sa.ForeignKey("admission_cycles.id"), nullable=False
        ),
        sa.Column("class_name", sa.String(8), nullable=False),
        sa.Column(
            "application_id", sa.BigInteger(), sa.ForeignKey("applications.id"), nullable=False
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("status", _WAITLIST, nullable=False, server_default="waiting"),
        *_ts(),
        sa.UniqueConstraint("cycle_id", "class_name", "rank", name="uq_waitlist_rank"),
        sa.UniqueConstraint("application_id", name="uq_waitlist_application"),
    )
    op.create_index("ix_waitlist_entries_school_id", "waitlist_entries", ["school_id"])
    op.create_index(
        "ix_waitlist_queue",
        "waitlist_entries",
        ["cycle_id", "class_name", "status", "rank"],
    )

    # 06:00, so a seat released overnight is offered on before the office opens.
    op.execute(
        sa.text(
            "INSERT INTO scheduled_jobs (kind, enabled, every_minutes, at_hour,"
            " created_at, updated_at) VALUES ('admission.offer_sweep', true, 1440, 6,"
            " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM scheduled_jobs WHERE kind = 'admission.offer_sweep'"))
    op.drop_table("waitlist_entries")
    op.drop_table("admission_offers")
    op.drop_table("admission_decisions")
