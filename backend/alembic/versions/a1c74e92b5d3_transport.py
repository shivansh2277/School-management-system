"""transport: vehicles, routes, stops, fee slabs and assignments

Five tables where ERP_BLUEPRINT §5.6.5 lists eleven. The six that are not here
are deliberate:

* `drivers` — a driver is an `employee` (§5.6.6). A second staff register would
  know nothing of departments, the exit rule or payroll.
* `vehicle_documents` — a vehicle's papers are `documents`. `OwnerType.vehicle`
  has been in the enum since Part 1 for exactly this, and that table already
  carries `expires_on`, verification and soft deletion.
* `trip_logs`, `maintenance_records`, `fuel_logs`, `incidents` — none is needed
  to run a bus service safely, and each would be a table nothing reads yet.

The one index worth reading twice is `uq_transport_assignment_live`. It is
partial on the three statuses that are not `ended`, so a child has at most one
live assignment and the month's transport charge is one slab rather than a sum
of two that something would have to arbitrate between.

Revision ID: a1c74e92b5d3
Revises: f8b05d37a1ec
Create Date: 2026-09-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c74e92b5d3"
down_revision: str | None = "f8b05d37a1ec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VEHICLE = sa.Enum(
    "active", "under_maintenance", "grounded", "retired",
    name="vehiclestatus", native_enum=False,
)
_OWNERSHIP = sa.Enum("owned", "hired", name="vehicleownership", native_enum=False)
_ROUTE = sa.Enum(
    "planned", "active", "suspended", "closed", name="routestatus", native_enum=False,
)
_DIRECTION = sa.Enum(
    "pickup", "drop", "both", name="transportdirection", native_enum=False,
)
_ASSIGNMENT = sa.Enum(
    "requested", "active", "suspended", "ended",
    name="transportassignmentstatus", native_enum=False,
)

_LIVE = "status IN ('requested', 'active', 'suspended')"


def _pk() -> sa.Column:
    return sa.Column(
        "id",
        sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
        autoincrement=True,
        primary_key=True,
    )


def _stamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
    ]


def _tenant() -> sa.Column:
    return sa.Column(
        "school_id", sa.BigInteger(), sa.ForeignKey("schools.id"),
        nullable=False, index=True,
    )


def upgrade() -> None:
    op.create_table(
        "vehicles",
        _pk(), _tenant(),
        sa.Column("registration_no", sa.String(20), nullable=False),
        sa.Column("make_model", sa.String(60)),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "ownership", _OWNERSHIP, nullable=False, server_default="owned"
        ),
        sa.Column("status", _VEHICLE, nullable=False, server_default="active"),
        sa.Column("gps_device_id", sa.String(40)),
        *_stamps(),
        sa.UniqueConstraint(
            "school_id", "registration_no", name="uq_vehicle_registration"
        ),
        sa.CheckConstraint("capacity > 0", name="ck_vehicle_capacity"),
    )

    op.create_table(
        "transport_fee_slabs",
        _pk(), _tenant(),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_stamps(),
        sa.UniqueConstraint("school_id", "name", name="uq_transport_slab_name"),
        sa.CheckConstraint("monthly_amount >= 0", name="ck_transport_slab_amount"),
    )

    op.create_table(
        "routes",
        _pk(), _tenant(),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        # Nullable: a route is designed before it is crewed. They become
        # required the moment it goes active, which the service enforces.
        sa.Column(
            "vehicle_id", sa.BigInteger(), sa.ForeignKey("vehicles.id"), index=True
        ),
        sa.Column("driver_id", sa.BigInteger(), sa.ForeignKey("employees.id")),
        sa.Column("attendant_id", sa.BigInteger(), sa.ForeignKey("employees.id")),
        sa.Column("distance_km", sa.Numeric(6, 2)),
        sa.Column("status", _ROUTE, nullable=False, server_default="planned"),
        *_stamps(),
        sa.UniqueConstraint("school_id", "code", name="uq_route_code"),
    )

    op.create_table(
        "route_stops",
        _pk(), _tenant(),
        sa.Column(
            "route_id", sa.BigInteger(), sa.ForeignKey("routes.id"),
            nullable=False, index=True,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("landmark", sa.String(120)),
        sa.Column("pickup_time", sa.Time(), nullable=False),
        sa.Column("drop_time", sa.Time()),
        sa.Column(
            "fee_slab_id", sa.BigInteger(), sa.ForeignKey("transport_fee_slabs.id")
        ),
        *_stamps(),
        sa.UniqueConstraint("route_id", "sequence", name="uq_route_stop_sequence"),
        sa.CheckConstraint("sequence > 0", name="ck_route_stop_sequence"),
    )

    op.create_table(
        "transport_assignments",
        _pk(), _tenant(),
        sa.Column(
            "enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"),
            nullable=False, index=True,
        ),
        sa.Column(
            "route_stop_id", sa.BigInteger(), sa.ForeignKey("route_stops.id"),
            nullable=False,
        ),
        sa.Column("direction", _DIRECTION, nullable=False, server_default="both"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date()),
        sa.Column("status", _ASSIGNMENT, nullable=False, server_default="requested"),
        sa.Column("end_reason", sa.Text()),
        *_stamps(),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="ck_transport_range"
        ),
    )
    op.create_index(
        "uq_transport_assignment_live",
        "transport_assignments",
        ["enrolment_id"],
        unique=True,
        postgresql_where=sa.text(_LIVE),
        sqlite_where=sa.text(_LIVE),
    )
    op.create_index(
        "ix_transport_assignment_stop",
        "transport_assignments",
        ["route_stop_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_transport_assignment_stop", table_name="transport_assignments")
    op.drop_index("uq_transport_assignment_live", table_name="transport_assignments")
    op.drop_table("transport_assignments")
    op.drop_table("route_stops")
    op.drop_table("routes")
    op.drop_table("transport_fee_slabs")
    op.drop_table("vehicles")
