"""The application itself, and the repeatable blocks around it (§5.1.4-5).

Kept apart from `admission.py` — cycles and enquiries — because this is the
half that grows: assessments, interviews, offers and decisions all hang off an
application.
"""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase, enum_col
from app.models.enums import (
    AdmissionCategory,
    ApplicationStatus,
    EnquirySource,
    GuardianRelation,
)


class Application(TenantBase):
    """One child's candidacy in one cycle.

    Columns are for what the office filters, ranks and decides on. The three
    descriptive blocks a form step writes and reads whole — address, previous
    school, declarations — are JSON, because a column each would be forty more
    columns and three more tables for data nothing ever queries. Medical is the
    exception and has its own table: §15 requires it to be permission-gated
    separately from the rest of the application.

    Aadhaar follows §0.12 — last four digits and a verified flag, never the
    full twelve.
    """

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("school_id", "application_no", name="uq_application_no"),
        Index("ix_application_cycle_status", "cycle_id", "status"),
        Index("ix_application_class", "cycle_id", "class_applying_for"),
        # Duplicate detection reads this on every submission (§5.1.9(2)).
        Index("ix_application_child", "school_id", "last_name", "date_of_birth"),
    )

    cycle_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("admission_cycles.id"), nullable=False
    )
    # Allocated at submission, not at draft: an abandoned draft must not burn a
    # number. The *admission* number comes later still, at conversion (§5.1.9(17)).
    application_no: Mapped[str | None] = mapped_column(String(24))

    first_name: Mapped[str] = mapped_column(String(60), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(12), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(40))
    religion: Mapped[str | None] = mapped_column(String(40))
    caste_category: Mapped[str | None] = mapped_column(String(12))
    mother_tongue: Mapped[str | None] = mapped_column(String(40))
    place_of_birth: Mapped[str | None] = mapped_column(String(80))
    identification_marks: Mapped[str | None] = mapped_column(Text)
    is_single_child: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aadhaar_last4: Mapped[str | None] = mapped_column(String(4))
    aadhaar_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    class_applying_for: Mapped[str] = mapped_column(String(8), nullable=False)
    stream: Mapped[str | None] = mapped_column(String(20))
    second_language: Mapped[str | None] = mapped_column(String(40))
    optional_subject: Mapped[str | None] = mapped_column(String(40))
    # A request, never a guarantee (§5.1.4 step 2).
    preferred_section: Mapped[str | None] = mapped_column(String(4))
    admission_category: Mapped[AdmissionCategory] = enum_col(
        AdmissionCategory, nullable=False, default=AdmissionCategory.general
    )
    transport_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    status: Mapped[ApplicationStatus] = enum_col(
        ApplicationStatus, nullable=False, default=ApplicationStatus.draft
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[EnquirySource] = enum_col(
        EnquirySource, nullable=False, default=EnquirySource.walk_in
    )
    # Null for one a parent filled in on the public portal: there is no staff
    # user behind it (§5.1.2(2)).
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    address: Mapped[dict | None] = mapped_column(JSON)
    previous_school: Mapped[dict | None] = mapped_column(JSON)
    declarations: Mapped[dict | None] = mapped_column(JSON)

    # Claims become priorities only once checked against the real records
    # (§5.1.9(6)).
    sibling_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    staff_ward_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # An age outside the class's range is admissible, but only deliberately.
    age_override_reason: Mapped[str | None] = mapped_column(Text)
    # A rejected applicant may reapply; the history is linked, not hidden
    # (§5.1.9(3)).
    previous_application_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("applications.id")
    )
    # Set at conversion and never cleared: the student's immutable pointer back
    # to where they came from (§5.1.9(19)).
    student_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("students.id"))

    cycle = relationship("AdmissionCycle", lazy="joined")

    @property
    def full_name(self) -> str:
        return " ".join(
            p for p in (self.first_name, self.middle_name, self.last_name) if p
        )


class ApplicationGuardian(TenantBase):
    """Repeatable: father, mother, guardian (§5.1.4 step 3).

    Exactly one primary contact, under a partial unique index, for the same
    reason `student_guardian` has one.
    """

    __tablename__ = "application_guardians"
    __table_args__ = (
        Index(
            "uq_application_primary_guardian",
            "application_id",
            unique=True,
            sqlite_where=text("is_primary"),
            postgresql_where=text("is_primary"),
        ),
        # Duplicate detection matches on a guardian's mobile (§5.1.9(2)).
        Index("ix_application_guardian_mobile", "school_id", "mobile"),
    )

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False, index=True
    )
    relation: Mapped[GuardianRelation] = enum_col(GuardianRelation, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    qualification: Mapped[str | None] = mapped_column(String(120))
    occupation: Mapped[str | None] = mapped_column(String(80))
    designation: Mapped[str | None] = mapped_column(String(80))
    organisation: Mapped[str | None] = mapped_column(String(120))
    annual_income_band: Mapped[str | None] = mapped_column(String(40))
    office_address: Mapped[str | None] = mapped_column(Text)
    mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    alternate_mobile: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(160))

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_emergency_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_authorised_for_pickup: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_school_alumnus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # A claim, until verified against `employees`.
    is_school_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))


class ApplicationSibling(TenantBase):
    """Step 4. A sibling already in the school is a link to a real student,
    never free text, because it drives a fee concession."""

    __tablename__ = "application_siblings"

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False, index=True
    )
    student_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("students.id"))
    name: Mapped[str | None] = mapped_column(String(120))
    age: Mapped[int | None] = mapped_column()
    school_name: Mapped[str | None] = mapped_column(String(160))


class ApplicationMedical(TenantBase):
    """Step 7, in its own table because §15 requires it to be permission-gated
    separately from everything else on the application."""

    __tablename__ = "application_medical"
    __table_args__ = (UniqueConstraint("application_id", name="uq_application_medical"),)

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id"), nullable=False
    )
    blood_group: Mapped[str | None] = mapped_column(String(8))
    known_allergies: Mapped[str | None] = mapped_column(Text)
    chronic_conditions: Mapped[str | None] = mapped_column(Text)
    regular_medication: Mapped[str | None] = mapped_column(Text)
    physical_disability: Mapped[str | None] = mapped_column(Text)
    learning_needs: Mapped[str | None] = mapped_column(Text)
    vision_hearing_notes: Mapped[str | None] = mapped_column(Text)
    emergency_doctor: Mapped[str | None] = mapped_column(String(160))
    emergency_doctor_phone: Mapped[str | None] = mapped_column(String(20))
    consent_for_emergency_treatment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )


class ApplicationAuthorizedPerson(TenantBase):
    """Repeatable: authorized pickup persons permitted to collect the student (§5.1.4 step 3).
    Supports multiple people (parents, grandparents, drivers, relatives) with genuine photos.
    """

    __tablename__ = "application_authorized_persons"
    __table_args__ = (
        Index("ix_app_auth_persons_app", "school_id", "application_id"),
    )

    application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship: Mapped[str] = mapped_column(String(60), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    id_proof_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    id_proof_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

