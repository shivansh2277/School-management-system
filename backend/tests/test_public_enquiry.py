"""Tests for public admission enquiry endpoint (§5.1.3).
Verifies that public web enquiries are saved directly into the ERP Enquiry register,
support duplicate resolution, and record interaction logs.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Enquiry, EnquiryInteraction, EnquirySource, EnquiryStatus


def test_submit_public_enquiry_success(client: TestClient, db: Session):
    """Submitting a valid public enquiry records a new Enquiry in the ERP DB."""
    payload = {
        "enquirer_name": "Vikramaditya Verma",
        "mobile": "+91 98765 43210",
        "email": "vikram.verma@example.com",
        "child_name": "Aarav Verma",
        "child_dob": "2019-05-15",
        "class_of_interest": "Class 1",
        "notes": "Looking for bus transport from Gomti Nagar Extension and robotics club.",
    }

    res = client.post("/public/SPS/admission/enquiry", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert "enquiry_id" in data
    assert data["enquiry_no"].startswith("ENQ-")

    # Verify DB persistence
    enquiry = db.get(Enquiry, data["enquiry_id"])
    assert enquiry is not None
    assert enquiry.enquirer_name == "Vikramaditya Verma"
    assert enquiry.mobile == "+91 98765 43210"
    assert enquiry.email == "vikram.verma@example.com"
    assert enquiry.child_name == "Aarav Verma"
    assert enquiry.class_of_interest == "Class 1"
    assert enquiry.source == EnquirySource.website
    assert enquiry.status == EnquiryStatus.new

    # Verify initial interaction note was saved
    interaction = db.query(EnquiryInteraction).filter_by(enquiry_id=enquiry.id).first()
    assert interaction is not None
    assert "robotics club" in interaction.notes


def test_submit_public_enquiry_duplicate_mobile_handling(client: TestClient, db: Session):
    """Submitting a second enquiry with the same mobile number appends an interaction note instead of creating a duplicate row."""
    payload1 = {
        "enquirer_name": "Sunita Sharma",
        "mobile": "+91 91234 56789",
        "class_of_interest": "Class 2",
        "notes": "First enquiry about admissions.",
    }

    res1 = client.post("/public/SPS/admission/enquiry", json=payload1)
    assert res1.status_code == 200
    id1 = res1.json()["enquiry_id"]

    # Submit second enquiry with same mobile number
    payload2 = {
        "enquirer_name": "Sunita Sharma",
        "mobile": "+91 91234 56789",
        "class_of_interest": "Class 2",
        "notes": "Follow-up question regarding fee structure.",
    }

    res2 = client.post("/public/SPS/admission/enquiry", json=payload2)
    assert res2.status_code == 200
    id2 = res2.json()["enquiry_id"]

    assert id1 == id2  # Reused existing enquiry ID!

    # Check interactions count
    interactions = db.query(EnquiryInteraction).filter_by(enquiry_id=id1).all()
    assert len(interactions) == 2
    assert "fee structure" in interactions[1].notes
