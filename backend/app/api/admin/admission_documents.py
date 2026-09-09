"""Document upload and verification for applicants (screen 8 of §5.1.3).

No new storage machinery: `documents` is already polymorphic, already signs its
URLs, and already knows which types are mandatory and which are conditional on
a claimed category. This is the admission-shaped view of it.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Document, DocumentType, OwnerType, User
from app.services import applications as svc
from app.services import documents
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/admission",
    tags=["admission"],
    dependencies=[Depends(module_enabled("admission"))],
)

reader = require_permission("admission.application.read", school_wide=True)
uploader = Depends(
    require_permission("admission.application.write", "admission.document.verify")
)
verifier = Depends(require_permission("admission.document.verify"))


class Verdict(BaseModel):
    model_config = {"extra": "forbid"}

    approved: bool
    reason: str | None = None
    original_seen: bool = False


@router.get("/applications/{application_id}/documents")
def checklist(
    application_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    items = svc.checklist(db, app)
    return {
        "items": items,
        "outstanding": svc.outstanding_documents(db, app),
    }


@router.post(
    "/applications/{application_id}/documents",
    status_code=status.HTTP_201_CREATED,
    dependencies=[uploader],
)
def upload_document(
    application_id: int,
    code: str = Form(..., description="Document type code, e.g. birth_certificate"),
    file: UploadFile = File(...),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    app = svc.get(db, user.school_id, application_id)
    doc_type = db.scalar(
        select(DocumentType).where(
            DocumentType.school_id == user.school_id,
            DocumentType.code == code,
            DocumentType.applies_to == OwnerType.application,
        )
    )
    if doc_type is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No document type {code}")

    doc = documents.upload(
        db,
        actor=user,
        owner_type=OwnerType.application,
        owner_id=app.id,
        filename=file.filename or code,
        mime_type=file.content_type or "application/octet-stream",
        data=file.file.read(),
        document_type_id=doc_type.id,
    )
    db.commit()
    return {"document_id": doc.id, "status": doc.status, "code": code}


@router.get("/documents/{document_id}/url")
def download_url(
    document_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """A link that expires in five minutes, minted per request. A permanent one
    that leaked would expose a child's birth certificate indefinitely."""
    doc = db.get(Document, document_id)
    if doc is None or doc.school_id != user.school_id or doc.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return {"url": documents.download_url(db, doc)}


@router.post("/documents/{document_id}/verify", dependencies=[verifier])
def verify_document(
    document_id: int,
    body: Verdict,
    user: User = Depends(require_permission("admission.document.verify", school_wide=True)),
    db: Session = Depends(get_db),
) -> dict:
    doc = db.get(Document, document_id)
    if (
        doc is None
        or doc.school_id != user.school_id
        or doc.owner_type is not OwnerType.application
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    documents.verify(
        db,
        actor=user,
        doc=doc,
        approved=body.approved,
        reason=body.reason,
        original_seen=body.original_seen,
    )
    app = svc.get(db, user.school_id, doc.owner_id)
    if not body.approved:
        svc.on_document_rejected(db, app, actor=user)
    db.commit()
    return {
        "document_id": doc.id,
        "status": doc.status,
        "application_status": app.status,
        "outstanding": svc.outstanding_documents(db, app),
    }
