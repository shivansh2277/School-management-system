from datetime import date, timedelta
import pytest
from app.models import Application, ApplicationStatus, School, User
from app.services import applications as app_svc


def test_birth_certificate_mandatory_rules(db):
    """Birth certificate is mandatory if class is in junior section through UKG,
    OR student is younger than 5 on cutoff date."""
    # Pre-primary classes: mandatory regardless of age
    assert app_svc.is_birth_certificate_mandatory(db, 1, "Nursery", date(2018, 1, 1)) is True
    assert app_svc.is_birth_certificate_mandatory(db, 1, "LKG", date(2018, 1, 1)) is True
    assert app_svc.is_birth_certificate_mandatory(db, 1, "UKG", date(2018, 1, 1)) is True

    # Class 1, student younger than 5 years on cutoff date (e.g., born 2022-05-01 -> age ~4.4 on 2026-10-01)
    assert app_svc.is_birth_certificate_mandatory(db, 1, "1", date(2022, 5, 1)) is True

    # Class 1, student older than 5 years on cutoff date (e.g., born 2018-01-01 -> age ~8.7)
    assert app_svc.is_birth_certificate_mandatory(db, 1, "1", date(2018, 1, 1)) is False

    # Class 6, older student: optional
    assert app_svc.is_birth_certificate_mandatory(db, 1, "6", date(2014, 5, 1)) is False


def test_public_draft_and_conditional_birth_certificate_validation(client):
    """Public apply blocks missing birth certificate if mandatory, but allows when optional."""
    # Case 1: UKG applicant with no birth certificate -> fails validation
    res = client.post(
        "/public/SPS/admission/apply",
        json={
            "first_name": "Junior",
            "last_name": "Kid",
            "class_applying_for": "UKG",
            "date_of_birth": "2021-08-15",
            "gender": "male",
            "guardians": [
                {
                    "relation": "father",
                    "full_name": "Rakesh Sharma",
                    "mobile": "9876543210",
                    "is_primary": True,
                }
            ],
            "apaar_consent": True,
            "apaar_consent_guardian_name": "Rakesh Sharma",
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert res.status_code == 422
    assert "birth certificate" in res.text.lower()

    # Case 2: Class 5 applicant (age >= 5) with no birth certificate -> succeeds
    res_ok = client.post(
        "/public/SPS/admission/apply",
        json={
            "first_name": "Senior",
            "last_name": "Kid",
            "class_applying_for": "5",
            "date_of_birth": "2015-05-10",
            "gender": "female",
            "guardians": [
                {
                    "relation": "mother",
                    "full_name": "Sunita Verma",
                    "mobile": "9876543211",
                    "is_primary": True,
                }
            ],
            "apaar_consent": True,
            "apaar_consent_guardian_name": "Sunita Verma",
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert res_ok.status_code == 201
    assert "application_no" in res_ok.json()


def test_public_draft_and_admin_document_override(client, admin, admission_officer, teacher):
    """Admin can authorize document exception for a draft; non-admin cannot; submission succeeds."""
    # 1. Create a draft application via public draft endpoint
    draft_res = client.post(
        "/public/SPS/admission/draft",
        json={
            "first_name": "Ananya",
            "last_name": "Sharma",
            "class_applying_for": "LKG",
            "date_of_birth": "2022-01-15",
            "gender": "female",
            "apaar_consent": True,
            "apaar_consent_guardian_name": "Ravi Sharma",
            "documents": [],
        },
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    draft_id = draft_data["draft_id"]
    draft_ref = draft_data["reference_code"]
    assert draft_ref.startswith("DFT-")

    # 2. Teacher or unauthenticated user tries to override -> 403/401
    unauth_res = client.post(
        f"/admin/admission/applications/{draft_id}/document-overrides",
        headers=teacher,
        json={"document_code": "birth_certificate", "reason": "Parent promised to submit next week"},
    )
    assert unauth_res.status_code == 403

    # 3. Admin authorizes the exception
    override_res = client.post(
        f"/admin/admission/applications/{draft_id}/document-overrides",
        headers=admin,
        json={"document_code": "birth_certificate", "reason": "Verified municipal receipt #4928"},
    )
    assert override_res.status_code == 200
    assert override_res.json()["document_code"] == "birth_certificate"

    # 4. Check overrides list
    list_res = client.get(f"/admin/admission/applications/{draft_id}/document-overrides", headers=admin)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert list_res.json()[0]["document_code"] == "birth_certificate"

    # 5. Now submit public application referencing draft_id -> succeeds without birth certificate!
    submit_res = client.post(
        "/public/SPS/admission/apply",
        json={
            "draft_id": draft_id,
            "first_name": "Ananya",
            "last_name": "Sharma",
            "class_applying_for": "LKG",
            "date_of_birth": "2022-01-15",
            "gender": "female",
            "guardians": [
                {
                    "relation": "father",
                    "full_name": "Ravi Sharma",
                    "mobile": "9876543222",
                    "is_primary": True,
                }
            ],
            "apaar_consent": True,
            "apaar_consent_guardian_name": "Ravi Sharma",
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert submit_res.status_code == 201
    app_data = submit_res.json()
    assert "application_no" in app_data
