"""Tests for the full lifecycle of Authorized Student Pickup Persons with Photos:
1. Public Photo Upload endpoint (/public/{school_code}/admission/upload).
2. Admission Application with multiple authorized pickup persons and guardian photos.
3. Admin detail retrieval and editing of authorized pickup persons.
4. Conversion / Enrollment carry-forward into permanent StudentAuthorizedPerson records.
5. Strict decoupling: Issuing a one-time gate pass for a different person does NOT alter the permanent authorized roster.
"""
from datetime import date, timedelta
from fastapi import status
from sqlalchemy import select

from app.models import (
    Application,
    ApplicationAuthorizedPerson,
    Enrolment,
    Student,
    StudentAuthorizedPerson,
    StudentPass,
)


def _upload_photo(client, school_code: str = "SPS", filename: str = "escort.jpg", content_type: str = "image/jpeg") -> str:
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200
    res = client.post(
        f"/public/{school_code}/admission/upload",
        files={"file": (filename, fake_image_bytes, content_type)},
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert "url" in data
    assert data["url"].startswith(f"/documents/")
    assert data["url"].endswith(".jpg") or data["url"].endswith(".png")
    return data["url"]


def test_public_upload_and_application_with_authorized_persons(client, admission_officer, db):
    # 1. Upload photos for guardians and authorized pickup persons
    father_photo = _upload_photo(client, "SPS", "father.jpg")
    mother_photo = _upload_photo(client, "SPS", "mother.png", "image/png")
    grandfather_photo = _upload_photo(client, "SPS", "grandfather.jpg")
    driver_photo = _upload_photo(client, "SPS", "driver.jpg")

    # 2. Submit application with 2 guardians and 2 additional authorized pickup persons
    app_payload = {
        "first_name": "Arjun",
        "last_name": "Verma",
        "date_of_birth": "2019-06-15",
        "gender": "male",
        "class_applying_for": "1",
        "address": {
            "line1": "Flat 402, Royal Palms",
            "city": "Lucknow",
            "state": "Uttar Pradesh",
            "pincode": "226016",
        },
        "guardians": [
            {
                "relation": "father",
                "full_name": "Suresh Verma",
                "mobile": "9811100001",
                "email": "suresh@example.com",
                "is_primary": True,
                "photo_url": father_photo,
                "is_authorised_for_pickup": True,
            },
            {
                "relation": "mother",
                "full_name": "Sunita Verma",
                "mobile": "9811100002",
                "email": "sunita@example.com",
                "is_primary": False,
                "photo_url": mother_photo,
                "is_authorised_for_pickup": True,
            },
        ],
        "authorized_pickup_persons": [
            {
                "name": "Devendra Verma",
                "relationship": "Grandfather",
                "phone": "9811100003",
                "id_proof_type": "Aadhaar Card",
                "id_proof_number": "1234 5678 9012",
                "photo_url": grandfather_photo,
                "notes": "Authorized for afternoon pickup",
            },
            {
                "name": "Ramesh Singh",
                "relationship": "Family Chauffeur",
                "phone": "9811100004",
                "id_proof_type": "Driving License",
                "id_proof_number": "DL-042011009988",
                "photo_url": driver_photo,
                "notes": "School van/driver",
            },
        ],
        "information_accuracy": True,
        "school_rules_accepted": True,
        "data_processing_consent": True,
    }

    res = client.post("/public/SPS/admission/apply", json=app_payload)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    app_no = res.json()["application_no"]

    app = db.scalar(select(Application).where(Application.application_no == app_no))
    assert app is not None
    app_id = app.id

    # 3. Verify in Admin detail API
    detail_res = client.get(f"/admin/admission/applications/{app_id}", headers=admission_officer)
    assert detail_res.status_code == status.HTTP_200_OK, detail_res.text
    detail = detail_res.json()

    # Verify guardians hold photos
    assert len(detail["guardians"]) == 2
    father = next(g for g in detail["guardians"] if g["is_primary"])
    assert father["photo_url"] == father_photo
    assert father["is_authorised_for_pickup"] is True

    # Verify authorized pickup persons stored and returned
    assert len(detail["authorized_pickup_persons"]) == 2
    persons = {p["name"]: p for p in detail["authorized_pickup_persons"]}
    assert "Devendra Verma" in persons
    assert persons["Devendra Verma"]["relationship"] == "Grandfather"
    assert persons["Devendra Verma"]["photo_url"] == grandfather_photo
    assert "Ramesh Singh" in persons
    assert persons["Ramesh Singh"]["relationship"] == "Family Chauffeur"
    assert persons["Ramesh Singh"]["photo_url"] == driver_photo

    # 4. Admin edits authorized pickup persons
    update_persons_payload = [
        {
            "name": "Devendra Verma",
            "relationship": "Grandfather",
            "phone": "9811100003",
            "id_proof_type": "Aadhaar Card",
            "id_proof_number": "1234 5678 9012",
            "photo_url": grandfather_photo,
            "notes": "Verified grandfather",
        },
        {
            "name": "Mohan Lal",
            "relationship": "Maternal Uncle",
            "phone": "9811100005",
            "id_proof_type": "Voter ID",
            "id_proof_number": "VTR-998877",
            "photo_url": driver_photo,
            "notes": "Weekend and emergency pickup",
        },
    ]
    edit_res = client.put(
        f"/admin/admission/applications/{app_id}/authorized-pickup-persons",
        json=update_persons_payload,
        headers=admission_officer,
    )
    assert edit_res.status_code == status.HTTP_200_OK
    updated_persons = edit_res.json()["authorized_pickup_persons"]
    assert len(updated_persons) == 2
    assert any(p["name"] == "Mohan Lal" and p["relationship"] == "Maternal Uncle" for p in updated_persons)


def test_conversion_carries_forward_authorized_persons_and_decoupling(client, admission_officer, receptionist, db):
    """Verifies that conversion carries forward both declared authorized persons
    and pickup-authorized guardians, and issuing a one-time gate pass does NOT alter
    the permanent authorized roster.
    """
    # 1. Upload photo and create application
    photo_url = _upload_photo(client, "SPS", "escort_test.jpg")
    app_payload = {
        "first_name": "Meera",
        "last_name": "Nambiar",
        "date_of_birth": "2019-02-10",
        "gender": "female",
        "class_applying_for": "1",
        "address": {
            "line1": "Flat 101, Palm Meadows",
            "city": "Lucknow",
            "state": "Uttar Pradesh",
            "pincode": "226010",
        },
        "guardians": [
            {
                "relation": "father",
                "full_name": "Rohan Nambiar",
                "mobile": "9822200001",
                "email": "rohan@example.com",
                "is_primary": True,
                "photo_url": photo_url,
                "is_authorised_for_pickup": True,
            }
        ],
        "authorized_pickup_persons": [
            {
                "name": "Kamala Nambiar",
                "relationship": "Grandmother",
                "phone": "9822200002",
                "id_proof_type": "Aadhaar Card",
                "id_proof_number": "5555 4444 3333",
                "photo_url": photo_url,
                "notes": "Authorized daily escort",
            }
        ],
        "information_accuracy": True,
        "school_rules_accepted": True,
        "data_processing_consent": True,
    }
    res = client.post("/public/SPS/admission/apply", json=app_payload)
    assert res.status_code == status.HTTP_201_CREATED
    app_no = res.json()["application_no"]

    app = db.scalar(select(Application).where(Application.application_no == app_no))
    app_id = app.id

    # 2. Upload mandatory documents and approve them
    for code in ("birth_certificate", "photo", "address_proof"):
        doc_res = client.post(
            f"/admin/admission/applications/{app_id}/documents",
            data={"code": code},
            files={"file": (f"{code}.pdf", b"%PDF-1.4 mock " + code.encode(), "application/pdf")},
            headers=admission_officer,
        )
        assert doc_res.status_code == status.HTTP_201_CREATED, doc_res.text
        doc_id = doc_res.json()["document_id"]
        client.post(
            f"/admin/admission/documents/{doc_id}/verify",
            json={"approved": True, "original_seen": True},
            headers=admission_officer,
        )

    # 3. Admit and offer
    client.post(
        f"/admin/admission/applications/{app_id}/status",
        json={"status": "decision_pending"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{app_id}/decision",
        json={"decision": "admitted", "reason": "Seat confirmed"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{app_id}/offer",
        json={"expires_on": str(date.today() + timedelta(days=10)), "offer_amount": "25000"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{app_id}/offer/response",
        json={"accepted": True},
        headers=admission_officer,
    )

    # 4. Convert application to student
    convert_res = client.post(
        f"/admin/admission/applications/{app_id}/convert",
        headers=admission_officer,
    )
    assert convert_res.status_code == status.HTTP_200_OK, convert_res.text
    student_id = convert_res.json()["student_id"]
    admission_no = convert_res.json()["admission_no"]

    # 5. Verify permanent StudentAuthorizedPerson records were created
    permanent_persons = list(
        db.scalars(
            select(StudentAuthorizedPerson)
            .where(StudentAuthorizedPerson.student_id == student_id)
            .order_by(StudentAuthorizedPerson.name)
        )
    )
    assert len(permanent_persons) >= 2
    names = {p.name: p for p in permanent_persons}

    # Grandmother from application_authorized_persons
    assert "Kamala Nambiar" in names
    kamala = names["Kamala Nambiar"]
    assert kamala.relationship == "Grandmother"
    assert kamala.phone == "9822200002"
    assert kamala.photo_url == photo_url
    assert kamala.is_active is True

    # Father from application_guardians
    assert "Rohan Nambiar" in names
    rohan = names["Rohan Nambiar"]
    assert rohan.phone == "9822200001"
    assert rohan.photo_url == photo_url
    assert rohan.is_active is True

    # 6. Receptionist checks permanent roster via reception API
    roster_res = client.get(
        f"/admin/reception/students/{student_id}/authorized-persons",
        headers=receptionist,
    )
    assert roster_res.status_code == status.HTTP_200_OK
    roster = roster_res.json()
    assert len(roster) >= 2
    roster_names = [p["name"] for p in roster]
    assert "Kamala Nambiar" in roster_names
    assert "Rohan Nambiar" in roster_names

    # 7. Receptionist edits permanent roster: add Uncle
    new_uncle = {
        "name": "Vijay Nambiar",
        "relationship": "Uncle",
        "phone": "9822200099",
        "id_proof_type": "PAN Card",
        "id_proof_number": "ABCDE1234F",
        "photo_url": photo_url,
        "notes": "Added per mother request",
    }
    add_roster_res = client.post(
        f"/admin/reception/students/{student_id}/authorized-persons",
        json=new_uncle,
        headers=receptionist,
    )
    assert add_roster_res.status_code == status.HTTP_201_CREATED
    assert add_roster_res.json()["name"] == "Vijay Nambiar"

    # Permanent list now contains Kamala, Rohan, and Vijay
    current_permanent = db.scalars(
        select(StudentAuthorizedPerson.name).where(
            StudentAuthorizedPerson.student_id == student_id,
            StudentAuthorizedPerson.is_active.is_(True),
        )
    ).all()
    assert set(current_permanent) == {"Kamala Nambiar", "Rohan Nambiar", "Vijay Nambiar"}

    # 8. Receptionist issues ONE-TIME gate pass for a DIFFERENT person (e.g. Neighbor Anita)
    pass_payload = {
        "student_id": student_id,
        "reason": "Doctor appointment",
        "pickup_person_name": "Anita Neighbor",
        "pickup_person_relation": "Family Friend / Neighbor",
        "pickup_person_phone": "9899911122",
        "pickup_person_id_proof": "Aadhaar: 9999 8888 7777",
        "pass_date": str(date.today()),
        "pass_time": "01:30 PM",
        "remarks": "One-time emergency pickup authorized over phone by mother",
    }
    pass_res = client.post("/admin/reception/passes", json=pass_payload, headers=receptionist)
    assert pass_res.status_code == status.HTTP_201_CREATED, pass_res.text
    issued_pass = pass_res.json()
    assert issued_pass["pickup_person_name"] == "Anita Neighbor"

    # 9. CRITICAL VERIFICATION:
    # Ensure permanent authorized-relative list remains completely unchanged!
    # "Anita Neighbor" MUST NOT appear in StudentAuthorizedPerson table.
    permanent_after_pass = db.scalars(
        select(StudentAuthorizedPerson.name).where(
            StudentAuthorizedPerson.student_id == student_id,
            StudentAuthorizedPerson.is_active.is_(True),
        )
    ).all()
    assert set(permanent_after_pass) == {"Kamala Nambiar", "Rohan Nambiar", "Vijay Nambiar"}
    assert "Anita Neighbor" not in permanent_after_pass
