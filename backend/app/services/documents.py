"""Uploading, verifying and serving documents."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    Document,
    DocumentStatus,
    DocumentType,
    OwnerType,
    User,
)
from app.services import audit, storage


def upload(
    db: Session,
    *,
    actor: User,
    owner_type: OwnerType,
    owner_id: int,
    filename: str,
    mime_type: str,
    data: bytes,
    document_type_id: int | None = None,
    expires_on=None,
) -> Document:
    try:
        storage.validate_upload(filename, mime_type, data)
    except storage.StorageError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e

    digest = storage.checksum(data)
    # The same file uploaded twice against the same owner is the same document,
    # not two. Parents re-submit constantly.
    existing = db.scalar(
        select(Document).where(
            Document.school_id == actor.school_id,
            Document.owner_type == owner_type,
            Document.owner_id == owner_id,
            Document.checksum == digest,
            Document.deleted_at.is_(None),
        )
    )
    if existing is not None:
        return existing

    doc_type = (
        db.get(DocumentType, document_type_id) if document_type_id is not None else None
    )
    if document_type_id is not None and (
        doc_type is None or doc_type.school_id != actor.school_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document type not found")

    key = storage.build_key(actor.school_id, owner_type.value, owner_id, filename)
    storage.get_storage().put(key, data, mime_type)

    doc = Document(
        school_id=actor.school_id,
        owner_type=owner_type,
        owner_id=owner_id,
        document_type_id=document_type_id,
        file_key=key,
        file_name=filename[:255],
        mime_type=mime_type,
        size_bytes=len(data),
        checksum=digest,
        uploaded_by=actor.id,
        uploaded_at=datetime.now(UTC),
        status=DocumentStatus.submitted,
        expires_on=expires_on,
        is_confidential=bool(doc_type and doc_type.is_confidential),
    )
    db.add(doc)
    db.flush()

    audit.record(
        db,
        actor=actor,
        school_id=actor.school_id,
        entity_type="document",
        entity_id=doc.id,
        action=AuditAction.create,
        after={"file_name": doc.file_name, "owner": f"{owner_type.value}:{owner_id}"},
    )
    return doc


def for_owner(
    db: Session, school_id: int, owner_type: OwnerType, owner_id: int
) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(
                Document.school_id == school_id,
                Document.owner_type == owner_type,
                Document.owner_id == owner_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.uploaded_at.desc())
        )
    )


def download_url(db: Session, doc: Document, expires_seconds: int = 300) -> str:
    """A short-lived link, minted per request.

    Never a permanent URL: one that leaks would expose a child's birth
    certificate for as long as the object exists (ERP_BLUEPRINT §3.8).
    """
    return storage.get_storage().presigned_url(doc.file_key, expires_seconds)


def verify(
    db: Session,
    *,
    actor: User,
    doc: Document,
    approved: bool,
    reason: str | None = None,
    original_seen: bool = False,
) -> Document:
    if not approved and not (reason and reason.strip()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A reason is required when rejecting a document",
        )

    before = {"status": doc.status.value}
    doc.status = DocumentStatus.verified if approved else DocumentStatus.rejected
    doc.verified_by = actor.id
    doc.verified_at = datetime.now(UTC)
    doc.rejection_reason = None if approved else reason
    doc.original_seen = original_seen or doc.original_seen

    audit.record(
        db,
        actor=actor,
        school_id=actor.school_id,
        entity_type="document",
        entity_id=doc.id,
        action=AuditAction.status_change,
        before=before,
        after={"status": doc.status.value},
        reason=reason or "Verified against the original",
    )
    db.flush()
    return doc


def soft_delete(db: Session, *, actor: User, doc: Document, reason: str) -> None:
    """Marks the row deleted and leaves the object in storage.

    A retention job removes the bytes later. Deleting them inside the request
    would make the audit entry point at something that no longer exists.
    """
    doc.deleted_at = datetime.now(UTC)
    doc.deleted_by = actor.id
    doc.delete_reason = reason
    audit.record(
        db,
        actor=actor,
        school_id=actor.school_id,
        entity_type="document",
        entity_id=doc.id,
        action=AuditAction.delete,
        reason=reason,
    )
    db.flush()


def missing_mandatory(
    db: Session, school_id: int, owner_type: OwnerType, owner_id: int, category: str | None = None
) -> list[DocumentType]:
    """Which required documents are still not verified.

    Category-conditional types only count when the category is claimed: an
    income certificate is mandatory for EWS and irrelevant for everyone else.
    """
    types = db.scalars(
        select(DocumentType).where(
            DocumentType.school_id == school_id,
            DocumentType.applies_to == owner_type,
            DocumentType.is_mandatory.is_(True),
        )
    ).all()
    verified = {
        d.document_type_id
        for d in for_owner(db, school_id, owner_type, owner_id)
        if d.status is DocumentStatus.verified
    }
    return [
        t
        for t in types
        if t.id not in verified
        and (t.required_if_category is None or t.required_if_category == category)
    ]
