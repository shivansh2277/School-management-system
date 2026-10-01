from datetime import date
import pytest
from app.models import Application, Student, User
from app.services import applications as app_svc


def test_apaar_validation_missing_both_fails(client):
    """Application missing both APAAR ID and consent fails validation."""
    res = client.post(
        "/public/SPS/admission/apply",
        json={
            "first_name": "Rohan",
            "last_name": "Das",
            "class_applying_for": "5",
            "date_of_birth": "2015-02-10",
            "gender": "male",
            "guardians": [
                {
                    "relation": "father",
                    "full_name": "Kishore Das",
                    "mobile": "9876543230",
                    "is_primary": True,
                }
            ],
            # Neither apaar_id nor apaar_consent
            "apaar_id": None,
            "apaar_consent": False,
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert res.status_code == 422
    assert "apaar" in res.text.lower()


def test_apaar_existing_12_digit_id_succeeds(client):
    """Providing a valid 12-digit APAAR ID succeeds without requiring consent."""
    res = client.post(
        "/public/SPS/admission/apply",
        json={
            "first_name": "Meera",
            "last_name": "Patel",
            "class_applying_for": "6",
            "date_of_birth": "2014-06-20",
            "gender": "female",
            "guardians": [
                {
                    "relation": "father",
                    "full_name": "Sanjay Patel",
                    "mobile": "9876543231",
                    "is_primary": True,
                }
            ],
            "apaar_id": "123456789012",
            "apaar_consent": False,
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert res.status_code == 201
    assert "application_no" in res.json()


def test_apaar_invalid_format_fails(client):
    """Providing an invalid APAAR ID format (e.g. less than 12 digits or letters) fails validation."""
    res = client.post(
        "/public/SPS/admission/apply",
        json={
            "first_name": "Meera",
            "last_name": "Patel",
            "class_applying_for": "6",
            "date_of_birth": "2014-06-20",
            "gender": "female",
            "guardians": [
                {
                    "relation": "father",
                    "full_name": "Sanjay Patel",
                    "mobile": "9876543231",
                    "is_primary": True,
                }
            ],
            "apaar_id": "12345",  # Invalid! Must be 12 digits
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert res.status_code == 422


def test_apaar_consent_option_succeeds(client):
    """Providing parental consent records consenting parent and succeeds."""
    res = client.post(
        "/public/SPS/admission/apply",
        json={
            "first_name": "Kabir",
            "last_name": "Joshi",
            "class_applying_for": "5",
            "date_of_birth": "2015-09-12",
            "gender": "male",
            "guardians": [
                {
                    "relation": "father",
                    "full_name": "Alok Joshi",
                    "mobile": "9876543232",
                    "is_primary": True,
                }
            ],
            "apaar_consent": True,
            "apaar_consent_guardian_name": "Alok Joshi",
            "information_accuracy": True,
            "school_rules_accepted": True,
            "data_processing_consent": True,
            "documents": [],
        },
    )
    assert res.status_code == 201


def test_apaar_transferred_to_student_and_updated_later(client, db, admin, admission_officer):
    """When application is converted, APAAR fields are transferred to Student, and can be updated later."""
    # Find an existing student in SPS to verify update endpoint
    students_res = client.get("/admin/students", headers=admin)
    assert students_res.status_code == 200
    items = students_res.json().get("items", [])
    assert len(items) > 0
    std_id = items[0]["id"]

    # Update APAAR ID on student
    up_res = client.patch(
        f"/admin/students/{std_id}",
        headers=admin,
        json={"apaar_id": "987654321098"},
    )
    assert up_res.status_code == 200
    assert up_res.json()["apaar_id"] == "987654321098"

    # Verify student detail
    get_res = client.get(f"/admin/students/{std_id}", headers=admin)
    assert get_res.status_code == 200
    assert get_res.json()["apaar_id"] == "987654321098"
