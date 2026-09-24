"""The school bus service.

Three things this file deliberately does *not* have a table for, because
Part 3 and Part 4 already built them (HANDOFF §9.4):

* **Drivers and attendants are `employees`.** A `drivers` table holding a name
  and a phone number would be a second staff register that HR, payroll and the
  exit rule know nothing about.
* **Vehicle papers are `documents`.** `OwnerType.vehicle` has been in the enum
  since Part 1 waiting for exactly this, and `documents` already carries
  `expires_on`, verification and soft deletion.
* **A driver's licence and police verification are also `documents`**, against
  the employee. Both have an expiry the compliance check reads.

What is left is the service itself: what the school owns, where it goes, who
rides it, and what that costs.
"""

from datetime import date, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    RouteStatus,
    TransportAssignmentStatus,
    TransportDirection,
    VehicleOwnership,
    VehicleStatus,
)


class Vehicle(TenantBase):
    """A bus. `capacity` is the seating figure on the registration papers, and
    it is the number the hard block in §5.6.9 counts against — not a soft
    target the office can talk its way past."""

    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("school_id", "registration_no", name="uq_vehicle_registration"),
        CheckConstraint("capacity > 0", name="ck_vehicle_capacity"),
    )

    registration_no: Mapped[str] = mapped_column(String(20), nullable=False)
    make_model: Mapped[str | None] = mapped_column(String(60))
    capacity: Mapped[int] = mapped_column(nullable=False)
    ownership: Mapped[VehicleOwnership] = enum_col(
        VehicleOwnership, nullable=False, default=VehicleOwnership.owned
    )
    status: Mapped[VehicleStatus] = enum_col(
        VehicleStatus, nullable=False, default=VehicleStatus.active
    )
    # Recorded because §5.6.4 asks for it and a school that later buys tracking
    # has somewhere to put the id. Nothing reads it: GPS is out of scope.
    gps_device_id: Mapped[str | None] = mapped_column(String(40))


class TransportFeeSlab(TenantBase):
    """A distance band and its monthly price.

    Its own table rather than an amount on each stop: a school runs three or
    four slabs across a dozen stops, and re-pricing "5-10 km" should be one
    edit rather than four that can disagree.
    """

    __tablename__ = "transport_fee_slabs"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_transport_slab_name"),
        CheckConstraint("monthly_amount >= 0", name="ck_transport_slab_amount"),
    )

    name: Mapped[str] = mapped_column(String(40), nullable=False)
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Route(TenantBase):
    """One bus doing one circuit.

    The vehicle, driver and attendant are nullable because a route is designed
    before it is crewed — `planned` is a real state. They stop being optional
    the moment the route goes `active`, which is where the compliance refusals
    in `services/transport.py` bite.

    There is no `direction` column although §5.6.4 lists one: a stop carries
    both a pickup and a drop time, so one route row covers the morning and the
    afternoon and a school does not maintain two mirror-image routes.
    """

    __tablename__ = "routes"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_route_code"),)

    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    vehicle_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vehicles.id"), index=True
    )
    driver_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))
    attendant_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    status: Mapped[RouteStatus] = enum_col(
        RouteStatus, nullable=False, default=RouteStatus.planned
    )

    vehicle = relationship("Vehicle", lazy="joined")
    stops = relationship(
        "RouteStop",
        lazy="selectin",
        cascade="all, delete-orphan",
        back_populates="route",
        order_by="RouteStop.sequence",
    )


class RouteStop(TenantBase):
    """A halt on a route, with the times the bus is actually there.

    `sequence` is what "monotonically increasing" in §5.6.9 is measured along:
    stop 3 may not be picked up before stop 2. That rule lives in the service
    because it is a statement about the whole route, not about one row.
    """

    __tablename__ = "route_stops"
    __table_args__ = (
        UniqueConstraint("route_id", "sequence", name="uq_route_stop_sequence"),
        CheckConstraint("sequence > 0", name="ck_route_stop_sequence"),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_route_stop_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_route_stop_longitude",
        ),
    )

    route_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("routes.id"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    landmark: Mapped[str | None] = mapped_column(String(120))
    pickup_time: Mapped[time] = mapped_column(Time, nullable=False)
    drop_time: Mapped[time | None] = mapped_column(Time)
    fee_slab_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("transport_fee_slabs.id")
    )
    # Where the halt actually is, for the route map. Nullable because every
    # stop that already exists was entered without one and a school is not
    # blocked from running buses until someone has pinned all of them; the map
    # says which stops are still unplaced rather than guessing at them.
    #
    # Float rather than Numeric: this is a measurement, not money, and it
    # crosses the wire as a JSON number the map can use directly. The ranges
    # are CheckConstraints because "latitude 200" is wrong everywhere, not just
    # in the one service that happens to validate it.
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    route = relationship("Route", back_populates="stops")
    fee_slab = relationship("TransportFeeSlab", lazy="joined")


class TransportAssignment(TenantBase):
    """A child on a bus, from a date until a date.

    Keyed to the **enrolment**, not the student: riding the bus is a fact about
    a year (CLAUDE.md), and keying it to the student would silently carry last
    year's route into the new class.

    The partial unique index is the billing guarantee. At most one live
    assignment per enrolment means the month's transport charge is one slab and
    never a sum of two, so nothing has to decide which of a child's two buses
    to bill for. That is stricter than §5.6.9, which allows a separate pickup
    and drop route — see HANDOFF §8 item P.
    """

    __tablename__ = "transport_assignments"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="ck_transport_range"
        ),
        Index(
            "uq_transport_assignment_live",
            "enrolment_id",
            unique=True,
            postgresql_where=text("status IN ('requested', 'active', 'suspended')"),
            sqlite_where=text("status IN ('requested', 'active', 'suspended')"),
        ),
        Index("ix_transport_assignment_stop", "route_stop_id", "status"),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
    )
    route_stop_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("route_stops.id"), nullable=False
    )
    direction: Mapped[TransportDirection] = enum_col(
        TransportDirection, nullable=False, default=TransportDirection.both
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Set when the assignment ends. Billing reads it rather than the status, so
    # a child who left the service on the 10th is charged ten days, not a month.
    end_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[TransportAssignmentStatus] = enum_col(
        TransportAssignmentStatus,
        nullable=False,
        default=TransportAssignmentStatus.requested,
    )
    end_reason: Mapped[str | None] = mapped_column(Text)

    route_stop = relationship("RouteStop", lazy="joined")
