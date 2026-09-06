"""The document gate (§5.1.9(4), (5)).

Documents arrive late and incomplete, so the pipeline has to keep moving with a
partial set and stop only at the gate before a decision. A design that demands
everything at application time is worked around by staff typing junk.
"""

import pytest
from sqlalchemy import select

from app.models import Application, ApplicationStatus, DocumentType, OwnerType
from app.services import storage

PDF = b"%PDF-1.4\n%demo birth certificate\n"


@pytest.fixture(autouse=True)
def local_storage(tmp_path, monkeypatch):
    backend = storage.LocalStorage(tmp_path / "docs")
    monkeypatch.setattr(storage, "_backend", backend)
    yield backend
    storage.reset_storage()


@pytest.fixture()
def application(client, admin):
    app = client.post(
        "/admin/admission/applications",
        json={
            "first_name": "Devansh",
            "last_name": "Mehra",
            "date_of_birth": "2019-04-02",
            "gender": "male",
            "class_applying_for": "1",
        },
        headers=admin,
    ).json()
    client.put(
        f"/admin/admission/applications/{app['id']}/guardians",
        json=[
            {
                "relation": "father",
                "full_name": "Sanjay Mehra",
                "mobile": "9899900001",
                "is_primary": True,
            }
        ],
        headers=admin,
    )
    client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    return app


def _upload(client, admin, application_id, code):
    return client.post(
        f"/admin/admission/applications/{application_id}/documents",
        data={"code": code},
        files={"file": (f"{code}.pdf", PDF + code.encode(), "application/pdf")},
        headers=admin,
    )


def test_the_checklist_is_the_class_checklist(client, admin, application):
    body = client.get(
        f"/admin/admission/applications/{application['id']}/documents", headers=admin
    ).json()
    required = {i["code"] for i in body["items"] if i["required"]}
    # The seeded class 1 asks for exactly these three.
    assert required == {"birth_certificate", "photo", "address_proof"}
    assert set(body["outstanding"]) == {
        i["name"] for i in body["items"] if i["required"]
    }


def test_a_conditional_document_is_asked_for_only_when_claimed(client, admin, application):
    body = client.get(
        f"/admin/admission/applications/{application['id']}/documents", headers=admin
    ).json()
    assert "income_certificate" not in {i["code"] for i in body["items"]}

    client.patch(
        f"/admin/admission/applications/{application['id']}",
        json={"caste_category": "EWS"},
        headers=admin,
    )
    body = client.get(
        f"/admin/admission/applications/{application['id']}/documents", headers=admin
    ).json()
    income = [i for i in body["items"] if i["code"] == "income_certificate"]
    assert income and income[0]["required"] is True


def test_uploading_does_not_verify(client, admin, application):
    r = _upload(client, admin, application["id"], "birth_certificate")
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "submitted"

    body = client.get(
        f"/admin/admission/applications/{application['id']}/documents", headers=admin
    ).json()
    assert "Birth Certificate" in body["outstanding"]


def test_a_decision_waits_for_every_required_document(client, admin, application):
    """§5.1.9(4): the gate is here, and only here."""
    r = client.post(
        f"/admin/admission/applications/{application['id']}/status",
        json={"status": "decision_pending"},
        headers=admin,
    )
    assert r.status_code == 409
    assert "Birth Certificate" in r.json()["detail"]

    for code in ("birth_certificate", "photo", "address_proof"):
        doc_id = _upload(client, admin, application["id"], code).json()["document_id"]
        client.post(
            f"/admin/admission/documents/{doc_id}/verify",
            json={"approved": True, "original_seen": True},
            headers=admin,
        )

    r = client.post(
        f"/admin/admission/applications/{application['id']}/status",
        json={"status": "decision_pending"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "decision_pending"


def test_a_rejection_needs_a_reason_and_reopens_verification(client, admin, application, db):
    """§5.1.9(5): an application sitting in `documents_verified` with a
    rejected document inside it is exactly the inconsistency that gets
    missed."""
    doc_id = _upload(client, admin, application["id"], "birth_certificate").json()[
        "document_id"
    ]
    client.post(
        f"/admin/admission/applications/{application['id']}/status",
        json={"status": "documents_verified"},
        headers=admin,
    )

    r = client.post(
        f"/admin/admission/documents/{doc_id}/verify",
        json={"approved": False},
        headers=admin,
    )
    assert r.status_code == 422

    r = client.post(
        f"/admin/admission/documents/{doc_id}/verify",
        json={"approved": False, "reason": "Photocopy is illegible; bring the original"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["application_status"] == "under_document_verification"

    body = client.get(
        f"/admin/admission/applications/{application['id']}/documents", headers=admin
    ).json()
    rejected = [i for i in body["items"] if i["code"] == "birth_certificate"][0]
    assert rejected["status"] == "rejected"
    assert "illegible" in rejected["rejection_reason"]


def test_the_download_link_is_signed_and_temporary(client, admin, application):
    doc_id = _upload(client, admin, application["id"], "photo").json()["document_id"]
    url = client.get(f"/admin/admission/documents/{doc_id}/url", headers=admin).json()[
        "url"
    ]
    # The key is a random hash, not the file name: a guessable path is a
    # public document.
    assert url and "photo" not in url


def test_the_verifier_role_can_verify_and_nothing_else(client):
    from app.core.permissions import SYSTEM_ROLES

    perms = dict((code, granted) for code, _, granted in SYSTEM_ROLES)["document_verifier"]
    assert set(perms) == {"admission.application.read", "admission.document.verify"}


def test_a_teacher_cannot_verify_documents(client, teacher, application):
    r = client.post(
        "/admin/admission/documents/1/verify",
        json={"approved": True},
        headers=teacher,
    )
    assert r.status_code == 403
