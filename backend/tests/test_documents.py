"""Documents and object storage.

Admission is blocked on this, and it holds the most sensitive data in the
system — a child's birth certificate and medical notes.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import Document, DocumentStatus, DocumentType, OwnerType, User
from app.services import documents, storage

PDF = b"%PDF-1.4 pretend certificate"


@pytest.fixture(autouse=True)
def local_storage(tmp_path, monkeypatch):
    """A fresh directory per test, so nothing leaks between them and no bucket
    needs to be running."""
    backend = storage.LocalStorage(tmp_path / "docs")
    monkeypatch.setattr(storage, "_backend", backend)
    yield backend
    storage.reset_storage()


@pytest.fixture()
def admin_user(db):
    return db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))


@pytest.fixture()
def doc_type(db):
    return db.scalar(
        select(DocumentType).where(DocumentType.code == "birth_certificate")
    )


def test_uploading_stores_the_bytes_and_records_the_row(db, admin_user, doc_type, local_storage):
    doc = documents.upload(
        db,
        actor=admin_user,
        owner_type=OwnerType.student,
        owner_id=1,
        filename="birth.pdf",
        mime_type="application/pdf",
        data=PDF,
        document_type_id=doc_type.id,
    )
    db.flush()

    assert doc.size_bytes == len(PDF)
    assert doc.status is DocumentStatus.submitted
    assert local_storage.get(doc.file_key) == PDF


def test_the_key_is_unguessable(db, admin_user, local_storage):
    """A predictable key plus a misconfigured bucket is a directory of
    children's documents."""
    doc = documents.upload(
        db,
        actor=admin_user,
        owner_type=OwnerType.student,
        owner_id=1,
        filename="birth_certificate.pdf",
        mime_type="application/pdf",
        data=PDF,
    )
    assert "birth_certificate" not in doc.file_key
    assert doc.file_key.endswith(".pdf")
    assert doc.file_key.startswith(f"{admin_user.school_id}/student/1/")


def test_an_executable_is_refused(db, admin_user):
    """The MIME allow-list is a security control, not a convenience."""
    for mime in ("application/x-msdownload", "text/html", "application/javascript"):
        with pytest.raises(HTTPException) as e:
            documents.upload(
                db,
                actor=admin_user,
                owner_type=OwnerType.student,
                owner_id=1,
                filename="payload.exe",
                mime_type=mime,
                data=b"MZ",
            )
        assert e.value.status_code == 422


def test_an_oversized_file_is_refused(db, admin_user):
    with pytest.raises(HTTPException) as e:
        documents.upload(
            db,
            actor=admin_user,
            owner_type=OwnerType.student,
            owner_id=1,
            filename="huge.pdf",
            mime_type="application/pdf",
            data=b"x" * (storage.MAX_BYTES + 1),
        )
    assert "limit" in e.value.detail


def test_the_same_file_twice_is_one_document(db, admin_user):
    """Parents re-submit constantly; two rows for one file is a verification
    queue with duplicates in it."""
    first = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.student, owner_id=1,
        filename="birth.pdf", mime_type="application/pdf", data=PDF,
    )
    second = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.student, owner_id=1,
        filename="birth-again.pdf", mime_type="application/pdf", data=PDF,
    )
    assert first.id == second.id


def test_rejecting_a_document_requires_a_reason(db, admin_user):
    doc = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.student, owner_id=1,
        filename="birth.pdf", mime_type="application/pdf", data=PDF,
    )
    with pytest.raises(HTTPException) as e:
        documents.verify(db, actor=admin_user, doc=doc, approved=False)
    assert e.value.status_code == 422

    documents.verify(
        db, actor=admin_user, doc=doc, approved=False, reason="Illegible scan"
    )
    assert doc.status is DocumentStatus.rejected
    assert doc.rejection_reason == "Illegible scan"


def test_a_download_url_expires(db, admin_user, local_storage):
    """Never a permanent URL — a leaked one would expose the document for as
    long as it exists."""
    doc = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.student, owner_id=1,
        filename="birth.pdf", mime_type="application/pdf", data=PDF,
    )
    url = documents.download_url(db, doc, expires_seconds=60)
    assert doc.file_key in url


def test_deleting_keeps_the_row_and_the_bytes(db, admin_user, local_storage):
    """Soft delete with a reason; a retention job removes the object later."""
    doc = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.student, owner_id=1,
        filename="birth.pdf", mime_type="application/pdf", data=PDF,
    )
    key = doc.file_key
    documents.soft_delete(db, actor=admin_user, doc=doc, reason="Uploaded to the wrong student")

    assert doc.deleted_at is not None
    assert local_storage.exists(key)
    assert doc.id not in [
        d.id for d in documents.for_owner(db, admin_user.school_id, OwnerType.student, 1)
    ]


def test_mandatory_documents_are_reported_until_verified(db, admin_user, doc_type):
    missing = documents.missing_mandatory(
        db, admin_user.school_id, OwnerType.application, 99
    )
    codes = {t.code for t in missing}
    assert "birth_certificate" in codes
    # Category-conditional types stay out until the category is claimed.
    assert "income_certificate" not in codes

    ews = documents.missing_mandatory(
        db, admin_user.school_id, OwnerType.application, 99, category="EWS"
    )
    assert "income_certificate" in {t.code for t in ews}


def test_a_verified_document_clears_the_requirement(db, admin_user):
    app_type = db.scalar(
        select(DocumentType).where(
            DocumentType.code == "birth_certificate",
            DocumentType.applies_to == OwnerType.application,
        )
    )
    doc = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.application, owner_id=99,
        filename="birth.pdf", mime_type="application/pdf", data=PDF,
        document_type_id=app_type.id,
    )
    documents.verify(db, actor=admin_user, doc=doc, approved=True, original_seen=True)

    missing = documents.missing_mandatory(
        db, admin_user.school_id, OwnerType.application, 99
    )
    assert "birth_certificate" not in {t.code for t in missing}


def test_storage_refuses_a_key_that_escapes_its_root(local_storage):
    with pytest.raises(storage.StorageError):
        local_storage.get("../../../etc/passwd")


def test_confidential_types_mark_their_documents(db, admin_user):
    medical = db.scalar(
        select(DocumentType).where(DocumentType.code == "medical_certificate")
    )
    doc = documents.upload(
        db, actor=admin_user, owner_type=OwnerType.application, owner_id=99,
        filename="medical.pdf", mime_type="application/pdf", data=PDF,
        document_type_id=medical.id,
    )
    assert doc.is_confidential is True
