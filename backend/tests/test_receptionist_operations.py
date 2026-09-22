"""Tests for Receptionist Operational Responsibilities:
1. Found & Lost (Found items, broadcast alerts, claim & handover).
2. Student Gate Pass (One-time pass, departure update, decoupling from permanent authorized roster).
3. Principal Meeting Slips (Slip generation, Principal response decision).
4. Teacher Meeting Slips (Slip generation, Teacher response decision).
5. Important Directory (Admin CRUD, Receptionist read-only enforcement).
6. Fee Collection Counter (Student fee status lookup, complete-month FIFO calculation, receipt slip generation).
"""
from datetime import date
from fastapi import status
from sqlalchemy import select

from app.models import Student, User, Enrolment, EnrolmentStatus


def test_found_items_workflow(client, receptionist, student):
    # 1. Receptionist creates a found item
    payload = {
        "item_name": "Titan Blue Water Bottle",
        "category": "bottles",
        "found_location": "Junior Football Ground Pavilion",
        "found_date": str(date.today()),
        "found_time": "11:30 AM",
        "photo_url": "https://storage.sunrisepublic.edu/found/titan-bottle.jpg",
        "description": "Stainless steel 750ml blue bottle with sticker of Spider-Man on base",
    }
    res = client.post("/admin/reception/found-items", json=payload, headers=receptionist)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    item = res.json()
    item_id = item["id"]
    assert item["item_name"] == payload["item_name"]
    assert item["status"] == "reported"

    # 2. Receptionist lists found items
    res = client.get("/admin/reception/found-items", headers=receptionist)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert any(i["id"] == item_id for i in items)

    # 3. Receptionist broadcasts notification to students
    res = client.post(f"/admin/reception/found-items/{item_id}/broadcast", headers=receptionist)
    assert res.status_code == status.HTTP_200_OK, res.text
    broadcasted = res.json()
    assert broadcasted["broadcasted_at"] is not None

    # 4. Student comes to claim item; receptionist records verification & handover
    claim_payload = {
        "claimed_by_student_name": "Aarav Sharma",
        "claimed_by_admission_no": "2024000001",
        "claimed_by_class_name": "Class 10-A",
        "handover_photo_url": "https://storage.sunrisepublic.edu/handover/claim_001.jpg",
        "handover_notes": "Student verified against School ID card and identified sticker on bottle base",
    }
    res = client.post(f"/admin/reception/found-items/{item_id}/collect", json=claim_payload, headers=receptionist)
    assert res.status_code == status.HTTP_200_OK, res.text
    collected = res.json()
    assert collected["status"] == "collected"
    assert collected["claimed_by_student_name"] == claim_payload["claimed_by_student_name"]
    assert collected["collected_at"] is not None

    # 5. Unauthorized role (student) cannot create or collect found items
    res = client.post("/admin/reception/found-items", json=payload, headers=student)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_student_pass_and_permanent_roster_decoupling(client, receptionist, admin, db):
    # Retrieve a seeded student
    student_record = db.scalars(select(Student)).first()
    assert student_record is not None
    student_id = student_record.id

    # 1. Fetch authorized persons roster
    res = client.get(f"/admin/reception/students/{student_id}/authorized-persons", headers=receptionist)
    assert res.status_code == status.HTTP_200_OK
    initial_roster = res.json()
    initial_roster_count = len(initial_roster)

    # 2. Add an authorized person to permanent roster
    auth_person_payload = {
        "name": "Ramesh Kumar",
        "relationship": "Maternal Uncle",
        "phone": "+91 9876543210",
        "id_proof_type": "Aadhaar Card",
        "id_proof_number": "XXXX-XXXX-4321",
        "is_active": True,
        "notes": "Authorized for afternoon pickup with photo verification",
    }
    res = client.post(
        f"/admin/reception/students/{student_id}/authorized-persons",
        json=auth_person_payload,
        headers=receptionist,
    )
    assert res.status_code == status.HTTP_201_CREATED, res.text
    person = res.json()
    assert person["name"] == "Ramesh Kumar"

    # Verify roster increased by 1
    res = client.get(f"/admin/reception/students/{student_id}/authorized-persons", headers=receptionist)
    assert len(res.json()) == initial_roster_count + 1

    # 3. Create a one-time Student Gate Pass on behalf of a parent
    pass_payload = {
        "student_id": student_id,
        "reason": "Urgent dental consultation at City Hospital",
        "pickup_person_name": "Dr. Sunil Gupta",
        "pickup_person_relation": "Family Physician / Friend",
        "pickup_person_phone": "+91 9988776655",
        "pickup_person_id_proof": "Driver License DL-8899",
        "pass_date": str(date.today()),
        "pass_time": "01:30 PM",
        "remarks": "Parent phoned and authorized pickup by Dr. Gupta",
    }
    res = client.post("/admin/reception/passes", json=pass_payload, headers=receptionist)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    gate_pass = res.json()
    pass_id = gate_pass["id"]
    assert gate_pass["pass_code"].startswith("SP/")
    assert gate_pass["status"] == "issued"
    assert gate_pass["pickup_person_name"] == pass_payload["pickup_person_name"]

    # Invariant Check: The permanent roster must NOT have been modified by creating the pass!
    res = client.get(f"/admin/reception/students/{student_id}/authorized-persons", headers=receptionist)
    current_roster = res.json()
    assert len(current_roster) == initial_roster_count + 1
    assert not any(p["name"] == "Dr. Sunil Gupta" for p in current_roster)

    # 4. Mark pass departed
    status_payload = {
        "status": "departed",
        "remarks": "Escort and student passed Main Gate security checkpoint",
    }
    res = client.patch(f"/admin/reception/passes/{pass_id}/status", json=status_payload, headers=receptionist)
    assert res.status_code == status.HTTP_200_OK, res.text
    departed_pass = res.json()
    assert departed_pass["status"] == "departed"


def test_principal_meeting_slip_lifecycle(client, receptionist, admin, teacher):
    # 1. Receptionist creates a Principal Meeting Slip
    meeting_payload = {
        "visitor_name": "Suresh Oberoi",
        "visitor_phone": "+91 9820011223",
        "visitor_organization": "District Collectorate Education Cell",
        "student_name": None,
        "student_admission_no": None,
        "reason": "Review of upcoming Inter-School Athletics Championship",
        "meeting_date": str(date.today()),
        "meeting_time": "11:00 AM",
    }
    res = client.post("/admin/reception/meetings/principal", json=meeting_payload, headers=receptionist)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    slip = res.json()
    meeting_id = slip["id"]
    assert slip["slip_code"].startswith("PR/")
    assert slip["status"] == "pending"

    # 2. Receptionist cannot respond to Principal meeting (lacks reception.meetings.respond_principal)
    respond_payload = {
        "status": "waiting",
        "wait_duration_minutes": 15,
        "response_notes": "Principal is in an emergency board meeting; please have visitor wait 15 mins",
    }
    res = client.post(
        f"/admin/reception/meetings/principal/{meeting_id}/respond",
        json=respond_payload,
        headers=receptionist,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Principal / Admin responds to the meeting slip
    res = client.post(
        f"/admin/reception/meetings/principal/{meeting_id}/respond",
        json=respond_payload,
        headers=admin,
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    responded = res.json()
    assert responded["status"] == "waiting"
    assert responded["wait_duration_minutes"] == 15
    assert responded["response_notes"] == respond_payload["response_notes"]
    assert responded["responded_at"] is not None


def test_teacher_meeting_slip_lifecycle(client, receptionist, teacher, admin):
    # Fetch teachers list
    res = client.get("/admin/reception/teachers", headers=receptionist)
    assert res.status_code == status.HTTP_200_OK
    teachers = res.json()
    assert len(teachers) > 0
    target_teacher = teachers[0]
    teacher_id = target_teacher["id"]

    # 1. Receptionist creates a Teacher Meeting Slip
    meeting_payload = {
        "teacher_id": teacher_id,
        "visitor_name": "Meena Agarwal",
        "visitor_phone": "+91 9811223344",
        "visitor_relation": "Mother",
        "student_name": "Karan Agarwal",
        "student_admission_no": "2024000045",
        "reason": "Quarterly progress review in Science and project submission",
        "meeting_date": str(date.today()),
        "meeting_time": "02:30 PM",
    }
    res = client.post("/admin/reception/meetings/teacher", json=meeting_payload, headers=receptionist)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    slip = res.json()
    meeting_id = slip["id"]
    assert slip["slip_code"].startswith("TR/")
    assert slip["status"] == "pending"

    # 2. Teacher responds to meeting slip
    respond_payload = {
        "status": "accepted",
        "response_notes": "Accepted. Please send parent to Room 104 during the free period.",
    }
    res = client.post(
        f"/admin/reception/meetings/teacher/{meeting_id}/respond",
        json=respond_payload,
        headers=teacher,
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    responded = res.json()
    assert responded["status"] == "accepted"
    assert responded["response_notes"] == respond_payload["response_notes"]


def test_important_directory_role_enforcement(client, receptionist, admin):
    contact_payload = {
        "category": "Medical",
        "name": "Metro Heart Hospital",
        "designation_or_department": "Casualty & Emergency Ambulance",
        "phone_primary": "+91 11 2345 6789",
        "phone_secondary": "+91 98765 00000",
        "email": "emergency@metroheart.org",
        "address": "Ring Road Sector 4",
        "operating_hours": "24x7",
        "is_emergency": True,
        "display_order": 1,
        "notes": "Direct ambulance hotline; contract hospital for school",
    }

    # 1. Receptionist CANNOT WRITE directory (strictly Read-Only)
    res = client.post("/admin/reception/directory", json=contact_payload, headers=receptionist)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Admin CAN create directory contact
    res = client.post("/admin/reception/directory", json=contact_payload, headers=admin)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    created = res.json()
    contact_id = created["id"]
    assert created["name"] == contact_payload["name"]

    # 3. Receptionist can READ directory and sees the contact
    res = client.get("/admin/reception/directory", headers=receptionist)
    assert res.status_code == status.HTTP_200_OK
    contacts = res.json()
    assert isinstance(contacts, list)
    assert any(c["id"] == contact_id for c in contacts)

    # 4. Admin CAN update contact
    update_payload = {**contact_payload, "name": "Metro Heart Institute & Hospital"}
    res = client.put(f"/admin/reception/directory/{contact_id}", json=update_payload, headers=admin)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["name"] == "Metro Heart Institute & Hospital"

    # 5. Admin CAN delete contact
    res = client.delete(f"/admin/reception/directory/{contact_id}", headers=admin)
    assert res.status_code == status.HTTP_200_OK


def test_receptionist_fee_collection_counter(client, receptionist, db):
    # Locate a student with active enrolment
    enrolment = (
        db.scalars(
            select(Enrolment)
            .where(Enrolment.status == EnrolmentStatus.active)
        )
        .first()
    )
    assert enrolment is not None
    student = enrolment.student
    search_q = student.admission_no

    # 1. Receptionist checks fee status
    res = client.get(f"/admin/reception/fees/status?q={search_q}", headers=receptionist)
    assert res.status_code == status.HTTP_200_OK, res.text
    status_data = res.json()
    assert "student" in status_data
    assert "outstanding_invoices" in status_data
    assert "available_month_options" in status_data

    options = status_data["available_month_options"]
    if len(options) > 0:
        # 2. Receptionist collects 1 complete month
        collect_payload = {
            "enrolment_id": enrolment.id,
            "num_months": 1,
            "payment_method": "cash",
            "notes": "Counter cash fee collection - 1 month",
        }
        res = client.post("/admin/reception/fees/collect", json=collect_payload, headers=receptionist)
        assert res.status_code == status.HTTP_200_OK, res.text
        receipt = res.json()
        assert "receipt_no" in receipt
        assert receipt["student_name"] == status_data["student"]["name"]
        assert receipt["total_paid"] == options[0]["total_amount"]
        assert len(receipt["invoices_covered"]) >= 1

        # 3. Verify validation error if arbitrary/invalid months requested
        invalid_payload = {
            "enrolment_id": enrolment.id,
            "num_months": 999,  # exceeds outstanding months
            "payment_method": "cash",
        }
        res = client.post("/admin/reception/fees/collect", json=invalid_payload, headers=receptionist)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
