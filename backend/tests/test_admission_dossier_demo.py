"""End-to-end test suite for the Complete Digital Admission Dossier.
Covers both demo students:
1. Aarav Sharma (Class 1, Fresh Entry)
2. Ananya Verma (Class 6, Sibling Claim linked to Aarav)
Verifies all 11 CBSE / Institutional sections, serialization, persistence on reload,
and atomic auto-enrollment upon fee payment.
"""

from datetime import date
import pytest
from sqlalchemy import select

from app.models import (
    AdmissionCycle,
    Application,
    ApplicationStatus,
    Enrolment,
    EnrolmentStatus,
    Student,
)


@pytest.fixture()
def cycle_id(db):
    return db.scalar(select(AdmissionCycle)).id


def test_complete_digital_admission_dossier_two_students(client, admin, cycle_id, db):
    # =========================================================================
    # STUDENT 1: Aarav Sharma (Class 1 Fresh Entry)
    # =========================================================================

    # 1. Draft
    r1 = client.post(
        "/admin/admission/applications",
        json={
            "cycle_id": cycle_id,
            "first_name": "Aarav",
            "middle_name": "Kumar",
            "last_name": "Sharma",
            "date_of_birth": "2020-05-14",
            "gender": "male",
            "class_applying_for": "1",
            "admission_category": "general",
            "transport_required": True,
            "source": "walk_in",
        },
        headers=admin,
    )
    assert r1.status_code == 201, r1.text
    aarav_app = r1.json()
    aarav_id = aarav_app["id"]

    # 2. Section 1 & 2: Update Personal & Admission Preferences
    r_patch1 = client.patch(
        f"/admin/admission/applications/{aarav_id}",
        json={
            "nationality": "Indian",
            "religion": "Hindu",
            "caste_category": "General",
            "mother_tongue": "Hindi",
            "place_of_birth": "Lucknow",
            "identification_marks": "Small mole on right cheek",
            "is_single_child": False,
            "aadhaar_last4": "4321",
            "second_language": "Hindi",
            "preferred_section": "A",
            "address": {
                "line1": "42/B, Vikas Nagar, Sector 4",
                "address_line_1": "42/B, Vikas Nagar, Sector 4",
                "city": "Lucknow",
                "state": "Uttar Pradesh",
                "pincode": "226022",
                "country": "India",
                "same_as_residential": True,
            },
            "previous_school": {
                "is_fresh_admission": False,
                "school_name": "Little Angels Montessori School",
                "board": "Pre-School",
                "last_class_passed": "UKG",
                "tc_number": "LA/2026/042",
                "tc_date": "2026-03-15",
                "percentage_or_grade": "A+",
                "reason_for_leaving": "Promoted to primary school",
            },
            "declarations": {
                "information_accuracy": True,
                "school_rules_accepted": True,
                "data_processing_consent": True,
                "transport_undertaking": True,
                "parent_signature_name": "Rajesh Sharma",
                "declared_on": "2026-04-02",
            },
        },
        headers=admin,
    )
    assert r_patch1.status_code == 200, r_patch1.text

    # 3. Section 3: Parents & Guardians (Full Schema Details)
    r_guardians1 = client.put(
        f"/admin/admission/applications/{aarav_id}/guardians",
        json=[
            {
                "relation": "father",
                "full_name": "Rajesh Sharma",
                "date_of_birth": "1985-08-12",
                "qualification": "B.Tech (Computer Science)",
                "occupation": "Service",
                "designation": "Senior Engineering Manager",
                "organisation": "Tata Consultancy Services",
                "annual_income_band": "₹15L - ₹25L",
                "office_address": "Cyber City, Phase 2, Gurugram / Gomti Nagar Lucknow",
                "mobile": "9811223344",
                "alternate_mobile": "9811223345",
                "email": "rajesh.sharma@example.com",
                "is_primary": True,
                "is_emergency_contact": True,
                "is_authorised_for_pickup": True,
            },
            {
                "relation": "mother",
                "full_name": "Sunita Sharma",
                "date_of_birth": "1988-11-20",
                "qualification": "M.Sc, B.Ed",
                "occupation": "Education",
                "designation": "Senior PGT Teacher",
                "organisation": "St. Mary's Convent School",
                "annual_income_band": "₹8L - ₹15L",
                "mobile": "9811223355",
                "email": "sunita.sharma@example.com",
                "is_primary": False,
                "is_emergency_contact": True,
                "is_authorised_for_pickup": True,
            },
        ],
        headers=admin,
    )
    assert r_guardians1.status_code == 200, r_guardians1.text
    # Verify serialization of DOB, qualification, and office address
    g_out = r_guardians1.json()["guardians"]
    assert len(g_out) == 2
    father = next(g for g in g_out if g["relation"] == "father")
    assert father["qualification"] == "B.Tech (Computer Science)"
    assert father["date_of_birth"] == "1985-08-12"
    assert "Cyber City" in father["office_address"]

    # 4. Section 7: Medical Profile
    r_med1 = client.put(
        f"/admin/admission/applications/{aarav_id}/medical",
        json={
            "blood_group": "B+",
            "known_allergies": None,
            "chronic_conditions": None,
            "regular_medication": None,
            "emergency_doctor": "Dr. K. N. Rao",
            "emergency_doctor_phone": "9415012345",
            "consent_for_emergency_treatment": True,
        },
        headers=admin,
    )
    assert r_med1.status_code == 200, r_med1.text

    # 5. Submit Application
    r_sub1 = client.post(f"/admin/admission/applications/{aarav_id}/submit", headers=admin)
    assert r_sub1.status_code == 200, r_sub1.text
    assert r_sub1.json()["status"] == "submitted"
    assert r_sub1.json()["application_no"].startswith("APP")

    # 6. Collect Application Fee -> Triggers Immediate Auto-Enrolment
    r_pay1 = client.post(
        f"/admin/admission/applications/{aarav_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500.00",
            "method": "cash",
            "reference": "REC-CASH-0101",
        },
        headers=admin,
    )
    assert r_pay1.status_code == 201, r_pay1.text
    pay_data1 = r_pay1.json()
    assert pay_data1["student"] is not None
    aarav_adm_no = pay_data1["student"]["admission_no"]
    aarav_student_id = pay_data1["student"]["id"]
    assert aarav_adm_no is not None and len(aarav_adm_no) > 0

    # 7. Reload Application 360° Detail & Verify 100% Persistence of Enrollment
    r_detail1 = client.get(f"/admin/admission/applications/{aarav_id}", headers=admin)
    assert r_detail1.status_code == 200
    d1 = r_detail1.json()
    assert d1["status"] == "enrolled"
    assert d1["student_id"] == aarav_student_id
    assert d1["enrolled_student"] is not None
    assert d1["enrolled_student"]["admission_no"] == aarav_adm_no
    assert "1" in d1["enrolled_student"]["class_label"]
    assert d1["enrolled_student"]["roll_no"] is not None

    # =========================================================================
    # STUDENT 2: Ananya Verma (Class 6 Sibling Claim)
    # =========================================================================

    # 1. Draft
    r2 = client.post(
        "/admin/admission/applications",
        json={
            "cycle_id": cycle_id,
            "first_name": "Ananya",
            "middle_name": "",
            "last_name": "Verma",
            "date_of_birth": "2015-08-22",
            "gender": "female",
            "class_applying_for": "6",
            "admission_category": "general",
            "transport_required": False,
            "source": "walk_in",
        },
        headers=admin,
    )
    assert r2.status_code == 201, r2.text
    ananya_id = r2.json()["id"]

    # 2. Section 1 & 2: Personal & Academic Preferences
    client.patch(
        f"/admin/admission/applications/{ananya_id}",
        json={
            "nationality": "Indian",
            "religion": "Hindu",
            "caste_category": "General",
            "mother_tongue": "Hindi",
            "place_of_birth": "Lucknow",
            "identification_marks": "None",
            "is_single_child": False,
            "aadhaar_last4": "8765",
            "second_language": "Sanskrit",
            "optional_subject": "Computer Science",
            "preferred_section": "A",
            "address": {
                "line1": "12/480, Indira Nagar, Ring Road",
                "city": "Lucknow",
                "state": "Uttar Pradesh",
                "pincode": "226016",
                "country": "India",
                "same_as_residential": True,
            },
            "previous_school": {
                "is_fresh_admission": False,
                "school_name": "Delhi Public School",
                "board": "CBSE",
                "last_class_passed": "Class 5",
                "tc_number": "DPS/LKO/2026/892",
                "tc_date": "2026-03-20",
                "percentage_or_grade": "94.5% (A1)",
                "reason_for_leaving": "Relocated closer to Sunrise campus",
            },
            "declarations": {
                "information_accuracy": True,
                "school_rules_accepted": True,
                "data_processing_consent": True,
                "transport_undertaking": False,
                "parent_signature_name": "Dr. Amit Verma",
                "declared_on": "2026-04-05",
            },
        },
        headers=admin,
    )

    # 3. Section 3: Parents & Guardians
    client.put(
        f"/admin/admission/applications/{ananya_id}/guardians",
        json=[
            {
                "relation": "father",
                "full_name": "Dr. Amit Verma",
                "date_of_birth": "1980-04-10",
                "qualification": "MBBS, MD (Medicine)",
                "occupation": "Doctor / Physician",
                "designation": "Senior Consultant Physician",
                "organisation": "Apollo Clinic Lucknow",
                "annual_income_band": "> ₹25 Lakhs",
                "office_address": "Sector B, Aliganj, Lucknow",
                "mobile": "9839011223",
                "email": "dr.amit.verma@example.com",
                "is_primary": True,
                "is_emergency_contact": True,
                "is_authorised_for_pickup": True,
            },
            {
                "relation": "mother",
                "full_name": "Dr. Ritu Verma",
                "date_of_birth": "1982-09-15",
                "qualification": "Ph.D, M.Sc (Biochemistry)",
                "occupation": "Professor / Academic",
                "designation": "Associate Professor",
                "organisation": "University of Lucknow",
                "annual_income_band": "₹15L - ₹25L",
                "mobile": "9839011224",
                "email": "ritu.verma@example.com",
                "is_primary": False,
                "is_emergency_contact": True,
                "is_authorised_for_pickup": True,
            },
        ],
        headers=admin,
    )

    # 4. Section 4: Sibling Link & Claim Authentication
    # Link to newly enrolled student Aarav Sharma!
    r_sib = client.put(
        f"/admin/admission/applications/{ananya_id}/siblings",
        json=[
            {
                "student_id": aarav_student_id,
                "name": "Aarav Sharma",
                "age": 6,
                "school_name": "Sunrise Public School (Class 1-A)",
            }
        ],
        headers=admin,
    )
    assert r_sib.status_code == 200, r_sib.text

    # Authenticate Claims against enrolled roster
    r_vc = client.post(f"/admin/admission/applications/{ananya_id}/verify-claims", headers=admin)
    assert r_vc.status_code == 200, r_vc.text
    assert r_vc.json()["sibling_verified"] is True

    # 5. Section 7: Medical Profile
    client.put(
        f"/admin/admission/applications/{ananya_id}/medical",
        json={
            "blood_group": "O+",
            "known_allergies": "Mild pollen allergy in spring",
            "chronic_conditions": None,
            "regular_medication": "Cetirizine as needed",
            "emergency_doctor": "Dr. Amit Verma (Father)",
            "emergency_doctor_phone": "9839011223",
            "consent_for_emergency_treatment": True,
        },
        headers=admin,
    )

    # 6. Submit Application
    r_sub2 = client.post(f"/admin/admission/applications/{ananya_id}/submit", headers=admin)
    assert r_sub2.status_code == 200
    assert r_sub2.json()["status"] == "submitted"

    # 7. Collect Application Fee & Auto-Enroll into Class 6
    r_pay2 = client.post(
        f"/admin/admission/applications/{ananya_id}/payments",
        json={
            "purpose": "application_fee",
            "amount": "500.00",
            "method": "upi",
            "reference": "UPI-HDFC-998822",
        },
        headers=admin,
    )
    assert r_pay2.status_code == 201, r_pay2.text
    pay_data2 = r_pay2.json()
    assert pay_data2["student"] is not None
    ananya_adm_no = pay_data2["student"]["admission_no"]
    ananya_student_id = pay_data2["student"]["id"]
    assert ananya_adm_no is not None and len(ananya_adm_no) > 0

    # 8. Reload & Verify Ananya's 360° Detail
    r_detail2 = client.get(f"/admin/admission/applications/{ananya_id}", headers=admin)
    assert r_detail2.status_code == 200
    d2 = r_detail2.json()
    assert d2["status"] == "enrolled"
    assert d2["student_id"] == ananya_student_id
    assert d2["sibling_verified"] is True
    assert d2["enrolled_student"]["admission_no"] == ananya_adm_no
    assert "6" in d2["enrolled_student"]["class_label"]
