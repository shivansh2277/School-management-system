from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class CertificateTemplate(TenantBase):
    """Configurable certificate template for a school.
    Allows institutional details, signatory titles, and wording to be configured
    rather than hardcoded.
    """

    __tablename__ = "certificate_templates"
    __table_args__ = (
        UniqueConstraint("school_id", "certificate_type", name="uq_school_cert_template"),
    )

    certificate_type: Mapped[str] = mapped_column(String(30), nullable=False)  # "transfer_certificate", "character_certificate", "bonafide_certificate"
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    header_text: Mapped[str | None] = mapped_column(Text)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    signatory_name: Mapped[str | None] = mapped_column(String(120))
    signatory_title: Mapped[str | None] = mapped_column(String(80), default="Principal")
    show_seal: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class StudentCertificate(TenantBase):
    """An official certificate issued to or requested for a student.
    Maintains an immutable issuance history, request/approval status, and
    audit records.
    """

    __tablename__ = "student_certificates"
    __table_args__ = (
        UniqueConstraint("school_id", "certificate_no", name="uq_school_certificate_no"),
        Index("ix_cert_student", "school_id", "student_id"),
        Index("ix_cert_type", "school_id", "certificate_type"),
    )

    certificate_type: Mapped[str] = mapped_column(String(30), nullable=False)  # "transfer_certificate", "character_certificate", "bonafide_certificate"
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    enrolment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("enrolments.id"), nullable=False)
    certificate_no: Mapped[str | None] = mapped_column(String(40))
    issue_date: Mapped[date | None] = mapped_column(Date)
    issued_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested")  # "requested", "approved", "rejected", "issued", "cancelled"
    requested_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    data_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_reissue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    reissue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    reissue_reason: Mapped[str | None] = mapped_column(Text)
    original_certificate_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("student_certificates.id"))

    student = relationship("Student", lazy="joined")
    enrolment = relationship("Enrolment", lazy="joined")
    issued_by = relationship("User", foreign_keys=[issued_by_id], lazy="joined")
    requested_by = relationship("User", foreign_keys=[requested_by_id], lazy="joined")
    approved_by = relationship("User", foreign_keys=[approved_by_id], lazy="joined")
