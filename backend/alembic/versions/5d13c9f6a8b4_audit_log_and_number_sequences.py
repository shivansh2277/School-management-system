"""audit log and number sequences

Adds the append-only audit trail (ERP_BLUEPRINT §3.6) and gapless document
numbering (§3.9 rule 5). Seeds the receipt sequence from the highest number
already issued, so the first payment after this migration does not collide with
history.

Revision ID: 5d13c9f6a8b4
Revises: 4c02b8e5f7a3
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5d13c9f6a8b4"
down_revision: str | None = "4c02b8e5f7a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ACTION = sa.Enum(
    "create",
    "update",
    "delete",
    "status_change",
    "login",
    "login_failed",
    "export",
    "print",
    "void",
    "publish",
    name="auditaction",
    native_enum=False,
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
    bind = op.get_bind()

    op.create_table(
        "audit_log",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("actor_label", sa.String(120)),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.BigInteger()),
        sa.Column("action", _ACTION, nullable=False),
        sa.Column("before", sa.JSON()),
        sa.Column("after", sa.JSON()),
        sa.Column("reason", sa.Text()),
        sa.Column(
            "academic_year_id", sa.BigInteger(), sa.ForeignKey("academic_years.id")
        ),
        sa.Column("ip", sa.String(45)),
        *_ts(),
    )
    op.create_index("ix_audit_log_school_id", "audit_log", ["school_id"])
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_actor_time", "audit_log", ["actor_user_id", "occurred_at"])
    op.create_index("ix_audit_school_time", "audit_log", ["school_id", "occurred_at"])

    op.create_table(
        "number_sequences",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("prefix", sa.String(24)),
        sa.Column("width", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("next_value", sa.Integer(), nullable=False, server_default="1"),
        *_ts(),
        sa.UniqueConstraint("school_id", "kind", "year", name="uq_sequence_period"),
    )
    op.create_index("ix_number_sequences_school_id", "number_sequences", ["school_id"])

    # Continue receipt numbering from what has already been issued rather than
    # restarting at 1, which would collide with existing rows.
    rows = bind.execute(
        sa.text(
            "SELECT school_id, receipt_no FROM fee_payments WHERE receipt_no IS NOT NULL"
        )
    ).all()
    highest: dict[tuple[int, int], int] = {}
    for school_id, receipt in rows:
        # SPS/RCP/2026/000123
        parts = str(receipt).split("/")
        if len(parts) < 4:
            continue
        try:
            year, seq = int(parts[-2]), int(parts[-1])
        except ValueError:
            continue
        key = (school_id, year)
        highest[key] = max(highest.get(key, 0), seq)

    for (school_id, year), seq in highest.items():
        bind.execute(
            sa.text(
                "INSERT INTO number_sequences (school_id, kind, year, prefix, width,"
                " next_value, created_at, updated_at) VALUES (:sid, 'receipt', :year,"
                " :prefix, 6, :nxt, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {
                "sid": school_id,
                "year": year,
                "prefix": f"SPS/RCP/{year}/",
                "nxt": seq + 1,
            },
        )


def downgrade() -> None:
    op.drop_table("number_sequences")
    op.drop_table("audit_log")
