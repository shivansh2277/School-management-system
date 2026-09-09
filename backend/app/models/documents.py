"""Documents.

Nothing in v0 modelled an uploaded file at all — `photo_url` and `logo_url` were
bare Text (ERP_BLUEPRINT §2.5(8)). Admission cannot function without documents:
birth certificate, transfer certificate, Aadhaar, photographs, caste and income
certificates.

Two rules the design turns on:

* Files live in object storage; the row holds the key. Never the bytes.
* The browser never gets a permanent URL. Access is a short-lived signed URL
  issued after a permission check, so a leaked link does not expose a child's
  birth certificate indefinitely.
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, enum_col
from app.models.enums import DocumentStatus, OwnerType


class DocumentType(TenantBase):
    """Configurable, not an enum: required-document lists change by class, by
    category and by state regulation, and a school must be able to edit them
    without a deploy (§3.8)."""

    __tablename__ = "document_types"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_document_type"),)

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    applies_to: Mapped[OwnerType] = enum_col(OwnerType, nullable=False)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Only required when the applicant claims the thing it proves — an income
    # certificate matters for EWS and for nobody else.
    required_if_category: Mapped[str | None] = mapped_column(String(40))
    # Licences, insurance and medical certificates lapse, and a lapsed one is
    # an operational alert rather than a filing detail.
    has_expiry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=100)


class Document(TenantBase):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_document_owner", "owner_type", "owner_id"),
        Index("ix_document_status", "school_id", "status"),
    )

    owner_type: Mapped[OwnerType] = enum_col(OwnerType, nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_type_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("document_types.id")
    )

    file_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Lets a re-upload of the identical file be recognised rather than stored twice.
    checksum: Mapped[str | None] = mapped_column(String(64))

    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    status: Mapped[DocumentStatus] = enum_col(
        DocumentStatus, nullable=False, default=DocumentStatus.pending
    )
    original_seen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    expires_on: Mapped[date | None] = mapped_column(Date)
    is_confidential: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Soft delete with a reason. The storage object is removed later by a
    # retention job, never by the request that "deleted" it.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[int | None] = mapped_column(BigInteger)
    delete_reason: Mapped[str | None] = mapped_column(Text)

    @property
    def is_expired(self) -> bool:
        return self.expires_on is not None and self.expires_on < date.today()
