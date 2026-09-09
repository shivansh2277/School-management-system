"""Conversion: applicant to student, in one transaction (§5.1.9(15)-(19)).

The last test in this file is Checkpoint 2 itself — a parent completes an
application on the public portal and, after staff action, exists as an enrolled
student with a fee account, a login and migrated documents, with no manual
database work at any point.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import (
    AdmissionCycle,
    Application,
    ApplicationPayment,
    Document,
    Enrolment,
    FeeInvoice,
    Guardian,
    OwnerType,
    Student,
    StudentGuardian,
    User,
)
from app.services import storage

PDF = b"%PDF-1.4\n%certificate\n"
PORTAL = "/public/SPS/admission"


@pytest.fixture(autouse=True)
def local_storage(tmp_path, monkeypatch):
    backend = storage.LocalStorage(tmp_path / "docs")
    monkeypatch.setattr(storage, "_backend", backend)
    yield backend
    storage.reset_storage()


@pytest.fixture()
def cycle_id(db):
    return db.scalar(select(AdmissionCycle)).id


def _apply_on_portal(client, **over):
    body = {
        "first_name": "Vihaan",
        "last_name": "Srivastava",
        "date_of_birth": "2019-03-05",
        "gender": "male",
        "class_applying_for": "1",
        "address": {
            "line1": "18 Gomti Nagar",
            "city": "Lucknow",
            "state": "Uttar Pradesh",
            "pincode": "226010",
        },
        "guardians": [
            {
                "relation": "father",
                "full_name": "Alok Srivastava",
                "mobile": "9844400001",
                "email": "alok@example.com",
                "is_primary": True,
            }
        ],
        "information_accuracy": True,
        "school_rules_accepted": True,
        "data_processing_consent": True,
    }
    body.update(over)
    r = client.post(f"{PORTAL}/apply", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _application_id(db, application_no):
    return db.scalar(
        select(Application.id).where(Application.application_no == application_no)
    )


def _clear_documents(client, admin, application_id):
    for code in ("birth_certificate", "photo", "address_proof"):
        doc_id = client.post(
            f"/admin/admission/applications/{application_id}/documents",
            data={"code": code},
            files={"file": (f"{code}.pdf", PDF + code.encode(), "application/pdf")},
            headers=admin,
        ).json()["document_id"]
        client.post(
            f"/admin/admission/documents/{doc_id}/verify",
            json={"approved": True, "original_seen": True},
            headers=admin,
        )


def _admit_and_offer(client, admin, application_id):
    client.post(
        f"/admin/admission/applications/{application_id}/status",
        json={"status": "decision_pending"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/decision",
        json={"decision": "admitted", "reason": "Ranked within the seats available"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/offer",
        json={"expires_on": str(date.today() + timedelta(days=10)), "offer_amount": "25000"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/offer/response",
        json={"accepted": True},
        headers=admin,
    )


def test_a_receipt_is_issued_and_two_clicks_are_one_payment(client, admin, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])

    first = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500",
            "method": "cash",
            "idempotency_key": "counter-1",
        },
        headers=admin,
    )
    assert first.status_code == 201, first.text
    assert first.json()["receipt_no"].startswith("AR")

    again = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500",
            "method": "cash",
            "idempotency_key": "counter-1",
        },
        headers=admin,
    )
    assert again.json()["receipt_no"] == first.json()["receipt_no"]
    assert len(client.get(f"/admin/admission/applications/{app_id}/payments", headers=admin).json()) == 1


def test_a_payment_is_voided_not_deleted(client, admin, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])
    payment = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "amount": "500"},
        headers=admin,
    ).json()

    r = client.delete(
        f"/admin/admission/payments/{payment['id']}?reason=Cheque+bounced", headers=admin
    )
    assert r.status_code == 200
    assert r.json()["status"] == "voided"
    # The receipt number stays used: that is what makes the sequence auditable.
    still_there = client.get(
        f"/admin/admission/applications/{app_id}/payments", headers=admin
    ).json()
    assert [p["receipt_no"] for p in still_there] == [payment["receipt_no"]]


def test_the_preview_writes_nothing_and_names_its_blockers(client, admin, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])

    plan = client.get(
        f"/admin/admission/applications/{app_id}/conversion-preview", headers=admin
    ).json()
    assert plan["ready"] is False
    assert any("submitted" in b for b in plan["blockers"])
    # Nothing was created while looking.
    assert db.scalar(select(Application.student_id).where(Application.id == app_id)) is None

    _clear_documents(client, admin, app_id)
    _admit_and_offer(client, admin, app_id)

    plan = client.get(
        f"/admin/admission/applications/{app_id}/conversion-preview", headers=admin
    ).json()
    assert plan["ready"] is True
    assert plan["class_label"].startswith("1-")
    assert "fewest students" in plan["section_rationale"]
    assert plan["documents_to_migrate"] == 3


def test_an_application_cannot_be_converted_twice(client, admin, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admin, app_id)
    _admit_and_offer(client, admin, app_id)

    assert client.post(
        f"/admin/admission/applications/{app_id}/convert", headers=admin
    ).status_code == 200
    second = client.post(
        f"/admin/admission/applications/{app_id}/convert", headers=admin
    )
    assert second.status_code == 409


def test_a_second_child_reuses_the_family_login(client, admin, db):
    """Otherwise the parent ends up with two portals and sees one child in
    each."""
    first = _apply_on_portal(client)
    first_id = _application_id(db, first["application_no"])
    _clear_documents(client, admin, first_id)
    _admit_and_offer(client, admin, first_id)
    client.post(f"/admin/admission/applications/{first_id}/convert", headers=admin)

    second = _apply_on_portal(
        client,
        first_name="Kiara",
        date_of_birth="2018-01-09",
        gender="female",
        guardians=[
            {
                "relation": "father",
                "full_name": "Alok Srivastava",
                "mobile": "9844400001",  # the same father
                "is_primary": True,
            }
        ],
    )
    second_id = _application_id(db, second["application_no"])
    _clear_documents(client, admin, second_id)
    _admit_and_offer(client, admin, second_id)
    client.post(f"/admin/admission/applications/{second_id}/convert", headers=admin)

    logins = db.scalars(
        select(User).where(User.login_id == "9844400001")
    ).all()
    assert len(logins) == 1
    guardian = db.scalar(select(Guardian).where(Guardian.user_id == logins[0].id))
    children = db.scalars(
        select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)
    ).all()
    assert len(children) == 2


def test_checkpoint_2_portal_to_enrolled_student(client, admin, db):
    """A parent applies online; staff verify, admit, offer and collect; the
    child ends up a student with a login, a class, a guardian and their
    documents — and no manual database work anywhere in between."""
    created = _apply_on_portal(client, first_name="Aarav", last_name="Bhandari",
                               guardians=[{
                                   "relation": "mother",
                                   "full_name": "Ritu Bhandari",
                                   "mobile": "9844400009",
                                   "is_primary": True,
                               }])
    app_id = _application_id(db, created["application_no"])

    # The office works the pipeline.
    _clear_documents(client, admin, app_id)
    _admit_and_offer(client, admin, app_id)
    client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "admission_fee", "amount": "25000", "method": "upi",
              "reference": "UPI-88213"},
        headers=admin,
    )

    result = client.post(
        f"/admin/admission/applications/{app_id}/convert", headers=admin
    )
    assert result.status_code == 200, result.text
    body = result.json()

    # A student, with the admission number allocated here and not before.
    student = db.get(Student, body["student_id"])
    assert student.admission_no == body["admission_no"]
    assert len(student.admission_no) == 10 and student.admission_no.isdigit()

    # A login that actually works.
    login = client.post(
        "/auth/login",
        json={
            "role": "student",
            "login_id": body["admission_no"],
            "password": body["student_login"]["password"],
        },
    )
    assert login.status_code == 200, login.text

    # An enrolment in a real section, and the guardian linked to the child.
    enrolment = db.scalar(
        select(Enrolment).where(Enrolment.student_id == student.id)
    )
    assert enrolment is not None and enrolment.class_section.label == body["class_label"]
    link = db.scalar(
        select(StudentGuardian).where(StudentGuardian.student_id == student.id)
    )
    assert link is not None and link.is_primary is True

    # The documents moved with the child rather than staying on a closed form.
    assert body["documents_migrated"] == 3
    assert (
        db.scalars(
            select(Document).where(
                Document.owner_type == OwnerType.student,
                Document.owner_id == student.id,
            )
        ).all()
        != []
    )

    # A fee account: the next billing run invoices them like anybody else.
    from app.services import fees

    # One reading, so a month boundary between the two cannot bill the wrong
    # period.
    billing = date.today()
    fees.generate(db, month=billing.month, year=billing.year, school_id=student.school_id)
    db.commit()
    invoice = db.scalar(
        select(FeeInvoice)
        .join(Enrolment, Enrolment.id == FeeInvoice.enrolment_id)
        .where(Enrolment.student_id == student.id)
    )
    assert invoice is not None

    # And the trail back: the application points at the student, and the
    # receipt is still attached to the application it was taken against.
    app = db.get(Application, app_id)
    assert app.student_id == student.id
    assert app.status.value == "enrolled"
    assert db.scalar(
        select(ApplicationPayment).where(ApplicationPayment.application_id == app_id)
    ) is not None
