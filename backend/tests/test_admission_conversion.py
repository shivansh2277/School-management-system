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
    ApplicationStatus,
    Document,
    Enrolment,
    EnrolmentStatus,
    Enquiry,
    EnquiryStatus,
    FeeInvoice,
    Guardian,
    OwnerType,
    Student,
    StudentGuardian,
    StudentStatus,
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


def _clear_documents(client, receptionist, application_id):
    for code in ("birth_certificate", "photo", "address_proof"):
        doc_id = client.post(
            f"/admin/admission/applications/{application_id}/documents",
            data={"code": code},
            files={"file": (f"{code}.pdf", PDF + code.encode(), "application/pdf")},
            headers=receptionist,
        ).json()["document_id"]
        client.post(
            f"/admin/admission/documents/{doc_id}/verify",
            json={"approved": True, "original_seen": True},
            headers=receptionist,
        )


def _admit_and_offer(client, receptionist, application_id):
    client.post(
        f"/admin/admission/applications/{application_id}/status",
        json={"status": "decision_pending"},
        headers=receptionist,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/decision",
        json={"decision": "admitted", "reason": "Ranked within the seats available"},
        headers=receptionist,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/offer",
        json={"expires_on": str(date.today() + timedelta(days=10)), "offer_amount": "25000"},
        headers=receptionist,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/offer/response",
        json={"accepted": True},
        headers=receptionist,
    )


def test_a_receipt_is_issued_and_two_clicks_are_one_payment(client, admission_officer, db):
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
        headers=admission_officer,
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
        headers=admission_officer,
    )
    assert again.json()["receipt_no"] == first.json()["receipt_no"]
    assert len(client.get(f"/admin/admission/applications/{app_id}/payments", headers=admission_officer).json()) == 1


def test_a_payment_is_voided_not_deleted(client, admission_officer, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])
    payment = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "amount": "500"},
        headers=admission_officer,
    ).json()

    r = client.delete(
        f"/admin/admission/payments/{payment['id']}?reason=Cheque+bounced", headers=admission_officer
    )
    assert r.status_code == 200
    assert r.json()["status"] == "voided"
    # The receipt number stays used: that is what makes the sequence auditable.
    still_there = client.get(
        f"/admin/admission/applications/{app_id}/payments", headers=admission_officer
    ).json()
    assert [p["receipt_no"] for p in still_there] == [payment["receipt_no"]]


def test_the_preview_writes_nothing_and_names_its_blockers(client, admission_officer, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])

    plan = client.get(
        f"/admin/admission/applications/{app_id}/conversion-preview", headers=admission_officer
    ).json()
    assert plan["ready"] is False
    assert any("submitted" in b for b in plan["blockers"])
    # Nothing was created while looking.
    assert db.scalar(select(Application.student_id).where(Application.id == app_id)) is None

    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    plan = client.get(
        f"/admin/admission/applications/{app_id}/conversion-preview", headers=admission_officer
    ).json()
    assert plan["ready"] is True
    assert plan["class_label"].startswith("1-")
    assert "fewest students" in plan["section_rationale"]
    assert plan["documents_to_migrate"] == 3


def test_an_application_cannot_be_converted_twice(client, admission_officer, db):
    created = _apply_on_portal(client)
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    assert client.post(
        f"/admin/admission/applications/{app_id}/convert", headers=admission_officer
    ).status_code == 200
    second = client.post(
        f"/admin/admission/applications/{app_id}/convert", headers=admission_officer
    )
    assert second.status_code == 409


def test_a_second_child_reuses_the_family_login(client, admission_officer, db):
    """Otherwise the parent ends up with two portals and sees one child in
    each."""
    first = _apply_on_portal(client)
    first_id = _application_id(db, first["application_no"])
    _clear_documents(client, admission_officer, first_id)
    _admit_and_offer(client, admission_officer, first_id)
    client.post(f"/admin/admission/applications/{first_id}/convert", headers=admission_officer)

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
    _clear_documents(client, admission_officer, second_id)
    _admit_and_offer(client, admission_officer, second_id)
    client.post(f"/admin/admission/applications/{second_id}/convert", headers=admission_officer)

    logins = db.scalars(
        select(User).where(User.login_id == "9844400001")
    ).all()
    assert len(logins) == 1
    guardian = db.scalar(select(Guardian).where(Guardian.user_id == logins[0].id))
    children = db.scalars(
        select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)
    ).all()
    assert len(children) == 2


def test_checkpoint_2_portal_to_enrolled_student(client, admission_officer, db):
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
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)
    pay_res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "admission_fee", "amount": "25000", "method": "upi",
              "reference": "UPI-88213"},
        headers=admission_officer,
    )
    assert pay_res.status_code == 201

    result = client.post(
        f"/admin/admission/applications/{app_id}/convert", headers=admission_officer
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


def test_admin_can_convert(client, admin, receptionist, admission_officer):
    # Receptionist does not have application conversion permissions
    assert client.post("/admin/admission/applications/99999/convert", headers=receptionist).status_code == 403
    # Authorized roles (admin, admission_officer) pass RBAC (returns 404 for nonexistent app)
    assert client.post("/admin/admission/applications/99999/convert", headers=admin).status_code == 404
    assert client.post("/admin/admission/applications/99999/convert", headers=admission_officer).status_code == 404


def test_complete_admission_pipeline_enquiry_to_roster(client, receptionist, admission_officer, db):
    """Canonical Master Acceptance Test:
    Enquiry -> Application -> Complete -> Submit -> Pay Fee -> Student Created -> Enrolment Created -> Visible in Roster
    """
    # 1. Receptionist logs enquiry
    enq_res = client.post(
        "/admin/admission/enquiries",
        json={
            "enquirer_name": "Ramesh Sharma",
            "mobile": "9811122233",
            "child_name": "Kavya Sharma",
            "child_dob": "2019-05-10",
            "class_of_interest": "1",
            "source": "walk_in",
        },
        headers=receptionist,
    )
    assert enq_res.status_code == 201, enq_res.text
    enquiry = enq_res.json()

    # 2. Admission Officer converts enquiry to application draft
    app_res = client.post(
        "/admin/admission/applications",
        json={
            "enquiry_id": enquiry["id"],
            "first_name": "Kavya",
            "last_name": "Sharma",
            "date_of_birth": "2019-05-10",
            "gender": "female",
            "class_applying_for": "1",
        },
        headers=admission_officer,
    )
    assert app_res.status_code == 201, app_res.text
    app_data = app_res.json()
    app_id = app_data["id"]

    # Verify Enquiry transitioned to converted
    enq_updated = db.get(Enquiry, enquiry["id"])
    assert enq_updated.status == EnquiryStatus.converted
    assert enq_updated.converted_application_id == app_id
    assert enq_updated.next_follow_up_on is None

    # Verify Guardian was auto-populated from enquiry
    assert len(app_data["guardians"]) >= 1
    primary_g = next(g for g in app_data["guardians"] if g["is_primary"])
    assert primary_g["full_name"] == "Ramesh Sharma"
    assert primary_g["mobile"] == "9811122233"

    # 3. Complete application dossier & documents
    client.patch(
        f"/admin/admission/applications/{app_id}",
        json={
            "address": {
                "line1": "42 Civil Lines",
                "city": "Lucknow",
                "state": "Uttar Pradesh",
                "pincode": "226001",
            },
            "declarations": {
                "information_accuracy": True,
                "school_rules_accepted": True,
                "data_processing_consent": True,
            },
        },
        headers=admission_officer,
    )
    _clear_documents(client, admission_officer, app_id)

    # 4. Status moves through decision to admitted
    _admit_and_offer(client, admission_officer, app_id)

    # 5. Admission Officer collects Application Fee -> ATOMIC AUTO-ENROLLMENT TRIGGER
    pay_res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={
            "purpose": "application_fee",
            "method": "cash",
            "reference": "COUNTER-CASH-001",
        },
        headers=admission_officer,
    )
    assert pay_res.status_code == 201, pay_res.text
    pay_data = pay_res.json()

    # Verify payment response has student data
    assert "student" in pay_data
    student_info = pay_data["student"]
    assert student_info["admission_no"] is not None
    assert student_info["class_label"].startswith("1-")

    # 6. Verify Database State
    student = db.get(Student, student_info["id"])
    assert student is not None
    assert student.status == StudentStatus.active
    assert student.admission_no == student_info["admission_no"]

    # Enrolment in Class 1
    enrolment = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == student.id,
            Enrolment.status == EnrolmentStatus.active,
        )
    )
    assert enrolment is not None
    assert enrolment.class_section.label == student_info["class_label"]

    # Student User login
    student_user = db.scalar(select(User).where(User.login_id == student.admission_no))
    assert student_user is not None
    assert student_user.role.value == "student"

    # Parent User login deduplicated/created
    parent_user = db.scalar(select(User).where(User.login_id == "9811122233"))
    assert parent_user is not None
    assert parent_user.role.value == "parent"

    # Application is marked enrolled
    app_final = db.get(Application, app_id)
    assert app_final.status.value == "enrolled"
    assert app_final.student_id == student.id

    # Migrated documents to student
    migrated_docs = db.scalars(
        select(Document).where(
            Document.owner_type == OwnerType.student,
            Document.owner_id == student.id,
        )
    ).all()
    assert len(migrated_docs) == 3


def test_payment_atomically_creates_student_and_enrolment(client, admission_officer, db):
    """Payment collection atomically creates payment, student, and active enrolment."""
    created = _apply_on_portal(client, first_name="Dev", last_name="Pandey")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    r = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "method": "upi", "reference": "UPI-111"},
        headers=admission_officer,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["receipt_no"].startswith("AR")
    assert data["student"]["admission_no"] is not None

    student = db.get(Student, data["student"]["id"])
    assert student is not None
    enrolment = db.scalar(select(Enrolment).where(Enrolment.student_id == student.id))
    assert enrolment is not None


def test_payment_amount_derived_from_cycle_application_fee(client, admission_officer, db):
    """Payment amount is derived from cycle.application_fee, rejecting mismatched amounts."""
    cycle = db.scalar(select(AdmissionCycle))
    expected_fee = cycle.application_fee

    created = _apply_on_portal(client, first_name="Rohan", last_name="Verma")
    app_id = _application_id(db, created["application_no"])

    # Wrong amount sent -> 422 rejected
    bad_res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "amount": "999.00", "method": "cash"},
        headers=admission_officer,
    )
    assert bad_res.status_code == 422
    assert "does not match cycle application fee" in bad_res.json()["detail"]

    # None amount sent -> automatically picks cycle.application_fee
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)
    good_res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "method": "cash"},
        headers=admission_officer,
    )
    assert good_res.status_code == 201
    assert str(good_res.json()["amount"]).startswith(str(int(expected_fee)))


def test_payment_failure_rolls_back_entire_transaction(client, admission_officer, monkeypatch, db):
    """If downstream conversion fails, payment and student creation are rolled back completely."""
    created = _apply_on_portal(client, first_name="Ananya", last_name="Gupta")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    # Monkeypatch allocate_section to raise a 409
    from app.services import conversion as conv_svc
    def _fail_allocate(*args, **kwargs):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Every section of class 1 is at maximum capacity.")

    monkeypatch.setattr(conv_svc, "allocate_section", _fail_allocate)

    r = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "method": "cash"},
        headers=admission_officer,
    )
    assert r.status_code == 409
    assert "maximum capacity" in r.text

    # Verify no payment was persisted
    payments = client.get(f"/admin/admission/applications/{app_id}/payments", headers=admission_officer).json()
    assert len(payments) == 0

    # Verify no student was linked
    app = db.get(Application, app_id)
    assert app.student_id is None
    assert app.status != ApplicationStatus.enrolled


def test_payment_idempotency_prevents_duplicate_charge_and_enrolment(client, admission_officer, db):
    """Repeated calls with the same idempotency_key return the existing payment and student."""
    created = _apply_on_portal(client, first_name="Ishan", last_name="Mishra")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    first = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "method": "cash", "idempotency_key": "uniq-idem-999"},
        headers=admission_officer,
    )
    assert first.status_code == 201
    f_data = first.json()

    second = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "method": "cash", "idempotency_key": "uniq-idem-999"},
        headers=admission_officer,
    )
    assert second.status_code == 201
    s_data = second.json()

    assert f_data["id"] == s_data["id"]
    assert f_data["receipt_no"] == s_data["receipt_no"]
    assert f_data["student"]["admission_no"] == s_data["student"]["admission_no"]


def test_enquiry_to_application_conversion_field_mapping(client, receptionist, admission_officer, db):
    """Enquiry conversion correctly maps names and parent contact."""
    enq_res = client.post(
        "/admin/admission/enquiries",
        json={
            "enquirer_name": "Suresh Kumar",
            "mobile": "9812345678",
            "email": "suresh@example.com",
            "child_name": "Aditya Raj Singh",
            "child_dob": "2019-06-15",
            "class_of_interest": "1",
        },
        headers=receptionist,
    )
    enq = enq_res.json()

    app_res = client.post(
        "/admin/admission/applications",
        json={
            "enquiry_id": enq["id"],
            "first_name": "Aditya",
            "middle_name": "Raj",
            "last_name": "Singh",
            "date_of_birth": "2019-06-15",
            "gender": "male",
            "class_applying_for": "1",
        },
        headers=admission_officer,
    )
    assert app_res.status_code == 201
    app = app_res.json()
    assert app["first_name"] == "Aditya"
    assert app["middle_name"] == "Raj"
    assert app["last_name"] == "Singh"
    g = app["guardians"][0]
    assert g["full_name"] == "Suresh Kumar"
    assert g["mobile"] == "9812345678"
    assert g["email"] == "suresh@example.com"
    assert g["is_primary"] is True


def test_enquiry_status_transitions_to_converted(client, receptionist, admission_officer, db):
    """Enquiry status updates to converted and follow-up is cleared upon conversion."""
    follow_up = str(date.today() + timedelta(days=2))
    enq = client.post(
        "/admin/admission/enquiries",
        json={
            "enquirer_name": "Pooja Mehta",
            "mobile": "9899988877",
            "next_follow_up_on": follow_up,
        },
        headers=receptionist,
    ).json()

    client.post(
        "/admin/admission/applications",
        json={
            "enquiry_id": enq["id"],
            "first_name": "Aryan",
            "last_name": "Mehta",
            "date_of_birth": "2019-07-20",
            "gender": "male",
            "class_applying_for": "1",
        },
        headers=admission_officer,
    )

    enquiry = db.get(Enquiry, enq["id"])
    assert enquiry.status == EnquiryStatus.converted
    assert enquiry.next_follow_up_on is None
    assert enquiry.converted_application_id is not None


def test_receptionist_cannot_collect_application_fee(client, receptionist, db):
    """Receptionist lacks fees.payment.collect and is forbidden from collecting application fees."""
    created = _apply_on_portal(client, first_name="Sara", last_name="Ali")
    app_id = _application_id(db, created["application_no"])

    res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "amount": "500", "method": "cash"},
        headers=receptionist,
    )
    assert res.status_code == 403


def test_admission_officer_can_collect_and_auto_enroll(client, admission_officer, db):
    """Admission Officer holds required permissions to collect fee and trigger enrollment."""
    created = _apply_on_portal(client, first_name="Tanya", last_name="Bose")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee", "amount": "500", "method": "cash"},
        headers=admission_officer,
    )
    assert res.status_code == 201
    assert res.json()["student"]["admission_no"] is not None


def test_section_allocation_headcount_balancing(client, admission_officer, db):
    """Auto-enrollment allocates section with fewest students to maintain balance."""
    from app.models import ClassSection
    sec_1a = db.scalar(select(ClassSection).where(ClassSection.class_name == "1", ClassSection.section == "A"))
    assert sec_1a is not None

    sec_1b = ClassSection(
        school_id=sec_1a.school_id,
        academic_year_id=sec_1a.academic_year_id,
        class_name="1",
        section="B",
        capacity=40,
    )
    db.add(sec_1b)
    db.flush()

    # Enroll child 1
    c1 = _apply_on_portal(client, first_name="Bal1", last_name="Test")
    id1 = _application_id(db, c1["application_no"])
    _clear_documents(client, admission_officer, id1)
    _admit_and_offer(client, admission_officer, id1)
    r1 = client.post(f"/admin/admission/applications/{id1}/payments", json={"purpose": "application_fee"}, headers=admission_officer).json()

    # Enroll child 2
    c2 = _apply_on_portal(client, first_name="Bal2", last_name="Test")
    id2 = _application_id(db, c2["application_no"])
    _clear_documents(client, admission_officer, id2)
    _admit_and_offer(client, admission_officer, id2)
    r2 = client.post(f"/admin/admission/applications/{id2}/payments", json={"purpose": "application_fee"}, headers=admission_officer).json()

    # The two children should be assigned to section B first (which had 0 students)
    assert r1["student"]["class_label"] == "1-B"
    assert r2["student"]["class_label"] == "1-B"


def test_section_allocation_honors_preferred_section(client, admission_officer, db):
    """Auto-enrollment honors preferred section when capacity and balance allow."""
    from app.models import ClassSection
    sec_1a = db.scalar(select(ClassSection).where(ClassSection.class_name == "1", ClassSection.section == "A"))
    sec_1b = ClassSection(
        school_id=sec_1a.school_id,
        academic_year_id=sec_1a.academic_year_id,
        class_name="1",
        section="B",
        capacity=40,
    )
    db.add(sec_1b)
    db.flush()

    app_res = client.post(
        "/admin/admission/applications",
        json={
            "first_name": "Pref",
            "last_name": "Child",
            "date_of_birth": "2019-01-01",
            "gender": "male",
            "class_applying_for": "1",
            "preferred_section": "B",
        },
        headers=admission_officer,
    )
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    client.put(
        f"/admin/admission/applications/{app_id}/guardians",
        json=[{
            "relation": "father",
            "full_name": "Papa Test",
            "mobile": "9819998888",
            "is_primary": True,
        }],
        headers=admission_officer,
    )
    client.patch(
        f"/admin/admission/applications/{app_id}",
        json={
            "address": {"line1": "10 Road", "city": "Lucknow", "state": "UP", "pincode": "226001"},
            "declarations": {"information_accuracy": True, "school_rules_accepted": True, "data_processing_consent": True},
        },
        headers=admission_officer,
    )
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee"},
        headers=admission_officer,
    )
    assert res.status_code == 201
    assert res.json()["student"]["class_label"] == "1-B"


def test_student_user_login_creation(client, admission_officer, db):
    """Enrolled student receives a working User account with default password."""
    created = _apply_on_portal(client, first_name="Logintest", last_name="Student")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee"},
        headers=admission_officer,
    ).json()

    adm_no = res["student"]["admission_no"]
    auth_res = client.post(
        "/auth/login",
        json={"role": "student", "login_id": adm_no, "password": "Student@123"},
    )
    assert auth_res.status_code == 200
    assert "access_token" in auth_res.json()


def test_parent_user_login_deduplication(client, admission_officer, db):
    """Two children with the same primary guardian mobile share one User and Guardian row."""
    mobile = "9822233344"
    c1 = _apply_on_portal(
        client,
        first_name="Sibling1",
        guardians=[{"relation": "father", "full_name": "Papa Test", "mobile": mobile, "is_primary": True}],
    )
    id1 = _application_id(db, c1["application_no"])
    _clear_documents(client, admission_officer, id1)
    _admit_and_offer(client, admission_officer, id1)
    client.post(f"/admin/admission/applications/{id1}/payments", json={"purpose": "application_fee"}, headers=admission_officer)

    c2 = _apply_on_portal(
        client,
        first_name="Sibling2",
        guardians=[{"relation": "father", "full_name": "Papa Test", "mobile": mobile, "is_primary": True}],
    )
    id2 = _application_id(db, c2["application_no"])
    _clear_documents(client, admission_officer, id2)
    _admit_and_offer(client, admission_officer, id2)
    client.post(f"/admin/admission/applications/{id2}/payments", json={"purpose": "application_fee"}, headers=admission_officer)

    users = db.scalars(select(User).where(User.login_id == mobile)).all()
    assert len(users) == 1
    guardians = db.scalars(select(Guardian).where(Guardian.user_id == users[0].id)).all()
    assert len(guardians) == 1
    sg_links = db.scalars(select(StudentGuardian).where(StudentGuardian.guardian_id == guardians[0].id)).all()
    assert len(sg_links) == 2


def test_document_migration_ownership(client, admission_officer, db):
    """Documents uploaded during application are transferred to student ownership."""
    created = _apply_on_portal(client, first_name="Docmig", last_name="Student")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee"},
        headers=admission_officer,
    ).json()

    student_id = res["student"]["id"]
    student_docs = db.scalars(
        select(Document).where(
            Document.owner_type == OwnerType.student,
            Document.owner_id == student_id,
        )
    ).all()
    assert len(student_docs) == 3
    # None left pointing at application
    app_docs = db.scalars(
        select(Document).where(
            Document.owner_type == OwnerType.application,
            Document.owner_id == app_id,
        )
    ).all()
    assert len(app_docs) == 0


def test_void_payment_leaves_audit_record(client, admission_officer, db):
    """Voiding a payment retains receipt number and marks status voided."""
    created = _apply_on_portal(client, first_name="Voidtest", last_name="Student")
    app_id = _application_id(db, created["application_no"])
    pay = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "admission_fee", "amount": "25000", "method": "cash"},
        headers=admission_officer,
    ).json()

    void_res = client.delete(
        f"/admin/admission/payments/{pay['id']}?reason=Wrong+amount+entered",
        headers=admission_officer,
    )
    assert void_res.status_code == 200
    assert void_res.json()["status"] == "voided"
    assert void_res.json()["void_reason"] == "Wrong amount entered"


def test_draft_application_allows_minimal_fields(client, admission_officer):
    """Creating an application draft requires only minimal fields."""
    r = client.post(
        "/admin/admission/applications",
        json={
            "first_name": "Min",
            "last_name": "Fields",
            "date_of_birth": "2019-01-01",
            "gender": "female",
            "class_applying_for": "1",
        },
        headers=admission_officer,
    )
    assert r.status_code == 201
    assert r.json()["status"] == "draft"


def test_submitted_application_enforces_mandatory_fields(client, admission_officer):
    """Submitting an application requires mandatory fields (e.g. address)."""
    r = client.post(
        "/admin/admission/applications",
        json={
            "first_name": "Incomplete",
            "last_name": "Applicant",
            "date_of_birth": "2019-01-01",
            "gender": "male",
            "class_applying_for": "1",
        },
        headers=admission_officer,
    )
    app_id = r.json()["id"]

    sub_res = client.post(
        f"/admin/admission/applications/{app_id}/submit",
        headers=admission_officer,
    )
    assert sub_res.status_code == 422
    assert "Cannot submit without" in sub_res.json()["detail"]


def test_no_separate_conversion_step_required(client, admission_officer, db):
    """Directly after payment collection, applicant is enrolled without calling /convert."""
    created = _apply_on_portal(client, first_name="NoStep", last_name="Needed")
    app_id = _application_id(db, created["application_no"])
    _clear_documents(client, admission_officer, app_id)
    _admit_and_offer(client, admission_officer, app_id)

    res = client.post(
        f"/admin/admission/applications/{app_id}/payments",
        json={"purpose": "application_fee"},
        headers=admission_officer,
    )
    assert res.status_code == 201

    app = db.get(Application, app_id)
    assert app.status == ApplicationStatus.enrolled
    assert app.student_id is not None

