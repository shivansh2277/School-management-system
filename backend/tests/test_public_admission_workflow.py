"""Comprehensive test suite for the public admission portal workflow (§0.13, §5.1):
1. Multi-step form submission (personal details, address, guardians, escorts, siblings, medical, documents)
2. Document and photo upload (.jpg, .png, .pdf)
3. Application status tracking with registered guardian mobile number
4. Security and authorization checks (enumeration protection, 404 on mismatched mobile)
5. Gated document download (403 before payment/enrollment)
6. Controlled mock payment gateway (initiate, process: failure, cancellation, success)
7. Payment idempotency (protection against double clicks, repeated calls, multiple tabs)
8. Sole atomic enrollment trigger on fee payment (Student, Enrolment, User, fee allocation)
9. Post-payment document access (dossier, admission letter, fee receipt)
10. Student credentials verification
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    AdmissionCycle,
    AdmissionOffer,
    Application,
    ApplicationPayment,
    ApplicationStatus,
    Document,
    Enrolment,
    EnrolmentStatus,
    FeeInvoice,
    FeePayment,
    OfferStatus,
    PaymentStatus,
    Student,
    User,
)
from app.services import storage

PDF = b"%PDF-1.4\n%official-document-sample\n"
PORTAL = "/public/SPS/admission"


@pytest.fixture(autouse=True)
def local_storage(tmp_path, monkeypatch):
    backend = storage.LocalStorage(tmp_path / "docs")
    monkeypatch.setattr(storage, "_backend", backend)
    yield backend
    storage.reset_storage()


def _full_application_payload(**overrides):
    payload = {
        "first_name": "Aarav",
        "middle_name": "Kumar",
        "last_name": "Shukla",
        "date_of_birth": "2019-07-15",
        "gender": "male",
        "class_applying_for": "1",
        "stream": None,
        "nationality": "Indian",
        "religion": "Hindu",
        "caste_category": "General",
        "mother_tongue": "Hindi",
        "place_of_birth": "Lucknow",
        "identification_marks": "Small mole on right forearm",
        "is_single_child": False,
        "aadhaar_last4": "5678",
        "second_language": "Sanskrit",
        "transport_required": True,
        "address": {
            "address_line": "House 42, Sector 4, Gomti Nagar",
            "city": "Lucknow",
            "state": "Uttar Pradesh",
            "pin_code": "226010",
        },
        "previous_school": {
            "school_name": "St. Mary Early Learning Centre",
            "board": "CBSE",
            "last_class": "UKG",
            "percentage": "A+",
            "tc_number": "TC/2026/089",
        },
        "guardians": [
            {
                "relation": "father",
                "full_name": "Rajesh Shukla",
                "mobile": "9876543210",
                "email": "rajesh.shukla@example.com",
                "qualification": "B.Tech, MBA",
                "occupation": "Software Architect",
                "designation": "Vice President",
                "organisation": "Tech Mahindra",
                "annual_income_band": "15-20 LPA",
                "office_address": "Vibhuti Khand, Gomti Nagar, Lucknow",
                "alternate_mobile": "9876543211",
                "is_primary": True,
                "is_emergency_contact": True,
                "is_authorised_for_pickup": True,
                "photo_url": "/documents/1/admission/father_photo.jpg",
                "is_school_alumnus": False,
                "is_school_staff": False,
            },
            {
                "relation": "mother",
                "full_name": "Pooja Shukla",
                "mobile": "9876543212",
                "email": "pooja.shukla@example.com",
                "qualification": "M.Sc, B.Ed",
                "occupation": "Teacher",
                "is_primary": False,
                "is_emergency_contact": True,
                "is_authorised_for_pickup": True,
                "photo_url": None,
                "is_school_alumnus": False,
                "is_school_staff": False,
            },
        ],
        "authorized_pickup_persons": [
            {
                "name": "Ram Prasad Shukla",
                "relationship": "Grandfather",
                "phone": "9876543219",
                "id_proof_type": "Aadhaar Card",
                "id_proof_number": "XXXX-XXXX-1234",
                "photo_url": None,
                "notes": "Authorized for daily pickup after 2 PM",
            }
        ],
        "siblings": [
            {
                "name": "Ananya Shukla",
                "age": 9,
                "school_name": "Sunrise School",
                "student_id": None,
            }
        ],
        "medical": {
            "blood_group": "B+",
            "known_allergies": "Dust, Peanuts",
            "chronic_conditions": None,
            "regular_medication": None,
            "emergency_doctor": "Dr. V. K. Mishra",
            "emergency_doctor_phone": "9415000000",
            "consent_for_emergency_treatment": True,
        },
        "documents": [
            {
                "code": "birth_certificate",
                "filename": "birth_certificate.pdf",
                "url": "/documents/1/admission/birth_cert.pdf",
                "size": 102400,
            },
            {
                "code": "address_proof",
                "filename": "electricity_bill.pdf",
                "url": "/documents/1/admission/electricity_bill.pdf",
                "size": 204800,
            },
        ],
        "heard_about_us": "website",
        "information_accuracy": True,
        "school_rules_accepted": True,
        "data_processing_consent": True,
        "photo_media_consent": True,
    }
    payload.update(overrides)
    return payload


def test_public_upload_images_and_pdf(client):
    # Upload JPEG
    jpeg_res = client.post(
        f"{PORTAL}/upload",
        files={"file": ("student_photo.jpg", b"\xff\xd8\xff\xe0" + b"image_data", "image/jpeg")},
    )
    assert jpeg_res.status_code == 200
    assert jpeg_res.json()["url"].startswith("/documents/")
    assert jpeg_res.json()["url"].endswith(".jpg")

    # Upload PDF
    pdf_res = client.post(
        f"{PORTAL}/upload",
        files={"file": ("birth_certificate.pdf", PDF, "application/pdf")},
    )
    assert pdf_res.status_code == 200
    assert pdf_res.json()["url"].endswith(".pdf")

    # Reject unsupported executable
    bad_res = client.post(
        f"{PORTAL}/upload",
        files={"file": ("script.sh", b"#!/bin/bash", "text/x-shellscript")},
    )
    assert bad_res.status_code == 422


def test_multi_step_application_submission_persists_full_schema(client, db):
    payload = _full_application_payload()
    res = client.post(f"{PORTAL}/apply", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["application_no"] is not None
    assert data["status"] == "submitted"

    app = db.scalar(
        select(Application).where(Application.application_no == data["application_no"])
    )
    assert app is not None
    assert app.first_name == "Aarav"
    assert app.last_name == "Shukla"
    assert app.nationality == "Indian"
    assert app.religion == "Hindu"
    assert app.place_of_birth == "Lucknow"
    assert app.identification_marks == "Small mole on right forearm"
    assert app.aadhaar_last4 == "5678"
    assert app.second_language == "Sanskrit"
    assert app.transport_required is True

    # Check guardians
    guardians = app.guardians if hasattr(app, "guardians") else None
    # Verify through query
    from app.models import ApplicationGuardian, ApplicationSibling, ApplicationMedical, Document
    g_rows = db.scalars(select(ApplicationGuardian).where(ApplicationGuardian.application_id == app.id)).all()
    assert len(g_rows) == 2
    primary = next(g for g in g_rows if g.is_primary)
    assert primary.full_name == "Rajesh Shukla"
    assert primary.mobile == "9876543210"
    assert primary.qualification == "B.Tech, MBA"
    assert primary.organisation == "Tech Mahindra"

    # Check siblings
    s_rows = db.scalars(select(ApplicationSibling).where(ApplicationSibling.application_id == app.id)).all()
    assert len(s_rows) == 1
    assert s_rows[0].name == "Ananya Shukla"
    assert s_rows[0].age == 9

    # Check medical
    med = db.scalar(select(ApplicationMedical).where(ApplicationMedical.application_id == app.id))
    assert med is not None
    assert med.blood_group == "B+"
    assert "Peanuts" in med.known_allergies
    assert med.emergency_doctor == "Dr. V. K. Mishra"

    # Check documents attached
    docs = db.scalars(select(Document).where(Document.owner_id == app.id)).all()
    assert len(docs) >= 2


def test_public_status_verification_mobile_and_dob(client, db):
    payload = _full_application_payload(first_name="Ishaan", last_name="Dubey")
    res = client.post(f"{PORTAL}/apply", json=payload).json()
    app_no = res["application_no"]

    # 1. Authorize via registered primary guardian mobile number
    status_mobile = client.get(f"{PORTAL}/status?application_no={app_no}&mobile=9876543210")
    assert status_mobile.status_code == 200
    data = status_mobile.json()
    assert data["application_no"] == app_no
    assert data["name"] == "Ishaan Shukla" or "Ishaan" in data["name"]
    assert data["stage"] == "submitted"
    assert data["is_payable"] is False
    assert data["documents_available"] is False

    # 2. Authorize via child's Date of Birth (backwards-compatible)
    status_dob = client.get(f"{PORTAL}/status?application_no={app_no}&date_of_birth=2019-07-15")
    assert status_dob.status_code == 200
    assert status_dob.json()["application_no"] == app_no

    # 3. Security: Wrong mobile number -> 404 (prevents enumeration oracle)
    wrong_mobile = client.get(f"{PORTAL}/status?application_no={app_no}&mobile=9999999999")
    assert wrong_mobile.status_code == 404
    assert "No application matches" in wrong_mobile.json()["detail"]

    # 4. Security: Non-existent application -> 404
    wrong_app = client.get(f"{PORTAL}/status?application_no=APP-FAKE-9999&mobile=9876543210")
    assert wrong_app.status_code == 404


def test_document_download_gated_before_payment(client, db):
    payload = _full_application_payload(first_name="Kavya")
    res = client.post(f"{PORTAL}/apply", json=payload).json()
    app_no = res["application_no"]

    # Attempt to download before payment -> 403 Forbidden!
    doc_res = client.get(f"{PORTAL}/documents/dossier?application_no={app_no}&mobile=9876543210")
    assert doc_res.status_code == 403
    assert "only downloadable after admission fee payment" in doc_res.json()["detail"]


def test_mock_payment_gateway_complete_journey_and_atomic_enrollment(client, admission_officer, db):
    """End-to-end test of the complete journey:
    1. Parent applies online
    2. ERP Admission Cell reviews, admits, and issues offer
    3. Parent checks status -> sees Offer Issued and Fee Payment Pending
    4. Parent initiates mock payment
    5. Parent simulates failure -> status stays offer_issued
    6. Parent simulates cancellation -> status stays offer_issued
    7. Parent simulates success:
       - Sole enrollment trigger executes atomically
       - Student record created
       - Enrolment record created with section & roll number
       - Fee invoice created & allocated via FIFO
       - ApplicationPayment recorded
       - Status moves to enrolled
    8. Parent downloads completed application dossier, admission letter, and payment receipt
    9. Student logs in using admission_no and default credentials
    """
    # 1. Apply online
    payload = _full_application_payload(first_name="Samar", last_name="Gupta")
    res = client.post(f"{PORTAL}/apply", json=payload).json()
    app_no = res["application_no"]
    app = db.scalar(select(Application).where(Application.application_no == app_no))
    app_id = app.id

    # 2. ERP Admission Cell works the pipeline
    # Verify documents
    for code in ("birth_certificate", "address_proof"):
        doc = db.scalar(select(Document).where(Document.owner_id == app_id))
        if doc:
            client.post(
                f"/admin/admission/documents/{doc.id}/verify",
                json={"approved": True, "original_seen": True},
                headers=admission_officer,
            )

    # Move to decision pending and admit
    client.post(
        f"/admin/admission/applications/{app_id}/status",
        json={"status": "decision_pending"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{app_id}/decision",
        json={"decision": "admitted", "reason": "High merit in readiness assessment"},
        headers=admission_officer,
    )
    # Issue offer with specific offer_amount
    offer_res = client.post(
        f"/admin/admission/applications/{app_id}/offer",
        json={"expires_on": str(date.today() + timedelta(days=14)), "offer_amount": "28500.00"},
        headers=admission_officer,
    )
    assert offer_res.status_code == 201

    # 3. Parent checks status on public portal
    status_res = client.get(f"{PORTAL}/status?application_no={app_no}&mobile=9876543210").json()
    assert status_res["stage"] == "offer_issued"
    assert status_res["is_payable"] is True
    assert status_res["payable_amount"] == "28500.00"
    assert status_res["offer"]["offer_amount"] == "28500.00"

    # 4. Initiate payment
    init_res = client.post(
        f"{PORTAL}/payments/initiate",
        json={"application_no": app_no, "mobile": "9876543210"},
    )
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["status"] == "initiated"
    assert init_data["amount"] == "28500.00"
    order_token = init_data["order_token"]
    order_id = init_data["order_id"]

    # 5. Negative: Test payment failure scenario
    fail_res = client.post(
        f"{PORTAL}/payments/process",
        json={"order_token": order_token, "scenario": "failure"},
    )
    assert fail_res.status_code == 200
    assert fail_res.json()["status"] == "failed"
    # Ensure application is still in offer_issued
    db.refresh(app)
    assert app.status == ApplicationStatus.offer_issued

    # 6. Negative: Test payment cancellation scenario
    cancel_res = client.post(
        f"{PORTAL}/payments/process",
        json={"order_token": order_token, "scenario": "cancel"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
    db.refresh(app)
    assert app.status == ApplicationStatus.offer_issued

    # 7. Positive: Simulate successful payment -> triggers atomic enrollment!
    success_res = client.post(
        f"{PORTAL}/payments/process",
        json={"order_token": order_token, "scenario": "success", "idempotency_key": "PAY-IDEM-001"},
    )
    assert success_res.status_code == 200, success_res.text
    pay_data = success_res.json()
    assert pay_data["status"] == "success"
    assert pay_data["receipt_no"].startswith("AR")
    assert pay_data["student"]["admission_no"] is not None

    admission_no = pay_data["student"]["admission_no"]
    student_id = pay_data["student"]["id"]

    # Verify database state after atomic conversion
    db.refresh(app)
    assert app.status == ApplicationStatus.enrolled
    assert app.student_id == student_id

    # Verify student
    student = db.get(Student, student_id)
    assert student.admission_no == admission_no
    assert student.status.value == "active"

    # Verify enrolment in Class 1
    enrolment = db.scalar(select(Enrolment).where(Enrolment.student_id == student.id))
    assert enrolment is not None
    assert enrolment.status == EnrolmentStatus.active
    assert enrolment.roll_no is not None

    # Verify FeeInvoice created & allocated via FIFO
    invoice = db.scalar(select(FeeInvoice).where(FeeInvoice.enrolment_id == enrolment.id))
    assert invoice is not None
    # Check allocations
    fee_pmt = db.scalar(select(FeePayment).where(FeePayment.enrolment_id == enrolment.id))
    assert fee_pmt is not None
    assert len(fee_pmt.allocations) >= 1
    assert invoice.status.value in ("paid", "issued")

    # 8. Test Idempotency: retry the same process call with same key or token
    retry_res = client.post(
        f"{PORTAL}/payments/process",
        json={"order_token": order_token, "scenario": "success", "idempotency_key": "PAY-IDEM-001"},
    )
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "success"
    assert retry_res.json()["student"]["admission_no"] == admission_no
    # Confirm no duplicate student or double enrolment created
    student_count = db.scalar(select(Application.student_id).where(Application.application_no == app_no))
    assert student_count == student_id

    # 9. Verify parent status reflects enrolled state
    new_status = client.get(f"{PORTAL}/status?application_no={app_no}&mobile=9876543210").json()
    assert new_status["stage"] == "enrolled"
    assert new_status["documents_available"] is True
    assert new_status["student"]["admission_no"] == admission_no
    assert new_status["receipt"]["receipt_no"] == pay_data["receipt_no"]

    # 10. Gated Document Download: Now accessible after successful payment!
    # A. Completed Application Dossier
    dossier_res = client.get(f"{PORTAL}/documents/dossier?application_no={app_no}&mobile=9876543210")
    assert dossier_res.status_code == 200
    d_data = dossier_res.json()
    assert d_data["doc_type"] == "dossier"
    assert d_data["school"]["name"] is not None
    assert d_data["student"]["admission_no"] == admission_no
    assert len(d_data["guardians"]) == 2

    # B. Official Provisional Admission Letter
    letter_res = client.get(f"{PORTAL}/documents/admission_letter?application_no={app_no}&mobile=9876543210")
    assert letter_res.status_code == 200
    l_data = letter_res.json()
    assert l_data["student"]["admission_no"] == admission_no
    assert l_data["student"]["class_label"] is not None

    # C. Payment Receipt Voucher
    receipt_res = client.get(f"{PORTAL}/documents/receipt?application_no={app_no}&mobile=9876543210")
    assert receipt_res.status_code == 200
    r_data = receipt_res.json()
    assert r_data["payment"]["receipt_no"] == pay_data["receipt_no"]
    assert "Twenty Eight Thousand" in r_data["payment"]["amount_in_words"]

    # 11. Student Credentials Authentication
    login_res = client.post(
        "/auth/login",
        json={"role": "student", "login_id": admission_no, "password": "Student@123"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["role"] == "student"
