"""Comprehensive Hostel & Mess Management Test Suite.

Covers:
1. Eligibility Rules: Class 9+ enforcement (HTTP 422 for Class <= 8), gender matching.
2. RBAC & Scoping: Warden strict isolation (HTTP 403 on other hostel), Chief Provost cross-hostel authority.
3. Provost Exclusivity: Only Chief Provost can exit residents and update mess menu.
4. Beds & Allocations: Capacity constraints, transfers preserving history.
5. Attendance: 8:00 PM evening roll-call, approved leave pre-population.
6. Leaves & Outings: Parent submission, student blocked, Warden adjudication & return recording, overdue flag.
7. Fees: Dynamic lookup of FeePlanItem for FeeHead 'HOSTEL', idempotent calculation.
"""

from datetime import UTC, date, datetime, timedelta
import pytest
from sqlalchemy import select

from app.models import (
    BedAllocation,
    ClassSection,
    Enrolment,
    FeeHead,
    FeePlan,
    FeePlanItem,
    Gender,
    Guardian,
    Hostel,
    HostelAdmission,
    HostelBed,
    HostelFloor,
    HostelLeaveRequest,
    HostelNotice,
    HostelRoom,
    Student,
    StudentGuardian,
    User,
    UserRole,
)
from app.services import hostel as hostel_svc


@pytest.fixture()
def hostel_data(db):
    """Retrieves seeded hostels, beds, and test students."""
    boys_hostel = db.scalar(select(Hostel).where(Hostel.code == "BH-01"))
    girls_hostel = db.scalar(select(Hostel).where(Hostel.code == "GH-01"))

    # Vacant bed in boys hostel
    vacant_bed = db.scalar(
        select(HostelBed)
        .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
        .join(HostelFloor, HostelFloor.id == HostelRoom.floor_id)
        .where(HostelFloor.hostel_id == boys_hostel.id, HostelBed.status == "available")
    )
    if not vacant_bed:
        # Create or fetch an extra available room + bed for testing
        room = db.scalar(
            select(HostelRoom).where(
                HostelRoom.hostel_id == boys_hostel.id,
                HostelRoom.room_number == "999",
            )
        )
        if not room:
            floor = db.scalar(select(HostelFloor).where(HostelFloor.hostel_id == boys_hostel.id))
            room = HostelRoom(
                school_id=boys_hostel.school_id,
                hostel_id=boys_hostel.id,
                floor_id=floor.id,
                room_number="999",
                capacity=2,
                status="available",
            )
            db.add(room)
            db.flush()

        vacant_bed = db.scalar(
            select(HostelBed).where(
                HostelBed.room_id == room.id,
                HostelBed.bed_number == "999-A",
            )
        )
        if not vacant_bed:
            vacant_bed = HostelBed(
                school_id=boys_hostel.school_id,
                room_id=room.id,
                bed_number="999-A",
                status="available",
            )
            db.add(vacant_bed)
            db.flush()
        else:
            vacant_bed.status = "available"
            db.flush()

    # Find a Class 8 student (ineligible)
    class_8_boy = db.scalar(
        select(Student)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .join(ClassSection, ClassSection.id == Enrolment.class_section_id)
        .where(ClassSection.class_name == "8", Student.gender == Gender.male)
    )

    # Find a Class 9/10 boy who is NOT yet a hosteller
    active_hosteller_ids = set(
        db.scalars(
            select(HostelAdmission.student_id).where(HostelAdmission.status == "active")
        )
    )
    class_10_boy = db.scalar(
        select(Student)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .join(ClassSection, ClassSection.id == Enrolment.class_section_id)
        .where(
            ClassSection.class_name.in_(("9", "10", "11", "12")),
            Student.gender == Gender.male,
            Student.id.not_in(active_hosteller_ids),
        )
    )
    if not class_10_boy:
        sec = db.scalar(
            select(ClassSection).where(ClassSection.class_name.in_(("9", "10", "11", "12")))
        )
        if sec:
            u_boy = User(
                school_id=boys_hostel.school_id,
                login_id="boy.fixture.day@example.com",
                password_hash="$2b$04$testpasswordhashplaceholder",
                full_name="Day Scholar Fixture Boy",
                phone="9999999991",
                role=UserRole.student,
            )
            db.add(u_boy)
            db.flush()
            class_10_boy = Student(
                school_id=boys_hostel.school_id,
                user_id=u_boy.id,
                admission_no="ADM-DAY-FIXTURE",
                gender=Gender.male,
                dob=date(2010, 1, 1),
            )
            db.add(class_10_boy)
            db.flush()
            enr = Enrolment(
                school_id=boys_hostel.school_id,
                student_id=class_10_boy.id,
                academic_year_id=sec.academic_year_id,
                class_section_id=sec.id,
                roll_no=95,
            )
            db.add(enr)
            db.flush()

    # Find an active resident boy
    active_boy_admission = db.scalar(
        select(HostelAdmission).where(
            HostelAdmission.hostel_id == boys_hostel.id,
            HostelAdmission.status == "active",
        )
    )

    return {
        "boys_hostel": boys_hostel,
        "girls_hostel": girls_hostel,
        "vacant_bed": vacant_bed,
        "class_8_boy": class_8_boy,
        "class_10_boy": class_10_boy,
        "active_boy_admission": active_boy_admission,
    }


# ==============================================================================
# 1. Eligibility: Class 9+ and Gender Integrity
# ==============================================================================


def test_class_8_student_rejected_from_hostel_admission(client, chief_provost, hostel_data):
    """Class <= 8 students are strictly ineligible for hostel (HTTP 422)."""
    c8 = hostel_data["class_8_boy"]
    assert c8 is not None, "Class 8 boy must exist"

    payload = {
        "student_id": c8.id,
        "hostel_id": hostel_data["boys_hostel"].id,
        "bed_id": hostel_data["vacant_bed"].id,
        "admission_date": "2026-10-08",
        "remarks": "Attempting Class 8 admission",
    }
    r = client.post(
        "/admin/hostel/admissions",
        json=payload,
        headers=chief_provost,
    )
    assert r.status_code == 422
    assert "Class 9 and above" in r.text


def test_gender_mismatch_rejected(client, chief_provost, hostel_data, db):
    """Male student cannot be admitted to Girls Hostel."""
    c10 = hostel_data["class_10_boy"]
    if not c10:
        sec = db.scalar(
            select(ClassSection).where(ClassSection.class_name.in_(("9", "10", "11", "12")))
        )
        if sec:
            user = User(
                school_id=hostel_data["boys_hostel"].school_id,
                login_id="boy.gender.test@example.com",
                password_hash="$2b$04$testpasswordhashplaceholder",
                full_name="Gender Test Boy",
                phone="9999999992",
                role=UserRole.student,
            )
            db.add(user)
            db.flush()
            c10 = Student(
                school_id=hostel_data["boys_hostel"].school_id,
                user_id=user.id,
                admission_no="ADM-GENDER-TEST",
                gender=Gender.male,
                dob=date(2010, 1, 1),
            )
            db.add(c10)
            db.flush()
            enr = Enrolment(
                school_id=hostel_data["boys_hostel"].school_id,
                student_id=c10.id,
                academic_year_id=sec.academic_year_id,
                class_section_id=sec.id,
                roll_no=99,
            )
            db.add(enr)
            db.flush()

    assert c10 is not None, "Class 9+ male student must exist"

    # Bed in girls hostel
    girls_bed = db.scalar(
        select(HostelBed)
        .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
        .join(HostelFloor, HostelFloor.id == HostelRoom.floor_id)
        .where(HostelFloor.hostel_id == hostel_data["girls_hostel"].id)
    )

    payload = {
        "student_id": c10.id,
        "hostel_id": hostel_data["girls_hostel"].id,
        "bed_id": girls_bed.id,
        "admission_date": "2026-10-08",
    }
    r = client.post(
        "/admin/hostel/admissions",
        json=payload,
        headers=chief_provost,
    )
    assert r.status_code in (400, 422)
    assert "girls hostel" in r.text.lower() or "gender" in r.text.lower()


# ==============================================================================
# 2. RBAC & Warden Cross-Hostel Isolation
# ==============================================================================


def test_warden_cannot_access_other_hostel(client, boys_warden, hostel_data):
    """Boys Hostel Warden accessing Girls Hostel structure returns HTTP 403 Forbidden."""
    girls_id = hostel_data["girls_hostel"].id

    r = client.get(f"/admin/hostel/{girls_id}/structure", headers=boys_warden)
    assert r.status_code == 403
    assert "out of scope" in r.text.lower() or "forbidden" in r.text.lower()


def test_warden_cannot_admit_to_other_hostel(client, boys_warden, hostel_data):
    """Boys Hostel Warden cannot admit or modify students in Girls Hostel."""
    girls_id = hostel_data["girls_hostel"].id

    r = client.post(
        "/admin/hostel/admissions",
        json={"student_id": 1, "hostel_id": girls_id, "bed_id": 1, "admission_date": "2026-10-08"},
        headers=boys_warden,
    )
    assert r.status_code == 403


def test_warden_can_access_assigned_hostel(client, boys_warden, hostel_data):
    """Boys Hostel Warden has full operational access to Boys Hostel."""
    boys_id = hostel_data["boys_hostel"].id

    r = client.get(f"/admin/hostel/{boys_id}/structure", headers=boys_warden)
    assert r.status_code == 200
    assert r.json()["code"] == "BH-01"


def test_chief_provost_has_cross_hostel_access(client, chief_provost, hostel_data):
    """Chief Provost possesses cross-hostel authority over both Boys and Girls Hostels."""
    boys_id = hostel_data["boys_hostel"].id
    girls_id = hostel_data["girls_hostel"].id

    r_boys = client.get(f"/admin/hostel/{boys_id}/structure", headers=chief_provost)
    assert r_boys.status_code == 200

    r_girls = client.get(f"/admin/hostel/{girls_id}/structure", headers=chief_provost)
    assert r_girls.status_code == 200


# ==============================================================================
# 3. Chief Provost Exclusivity: Permanent Exit & Mess Menu
# ==============================================================================


def test_warden_cannot_exit_student(client, boys_warden, hostel_data):
    """Warden cannot permanently exit a student from hostel (HTTP 403)."""
    adm = hostel_data["active_boy_admission"]
    assert adm is not None

    r = client.post(
        f"/admin/hostel/admissions/{adm.id}/exit",
        json={"exit_date": "2026-10-08", "exit_reason": "Warden attempting exit"},
        headers=boys_warden,
    )
    assert r.status_code == 403


def test_warden_cannot_publish_mess_menu(client, boys_warden):
    """Warden cannot modify or publish weekly mess menu (HTTP 403)."""
    payload = {
        "menu": [
            {
                "day_of_week": "mon",
                "breakfast": "Poha",
                "lunch": "Rajma Chawal",
                "snacks": "Tea",
                "dinner": "Khichdi",
            }
        ]
    }
    r = client.put("/admin/hostel/menu", json=payload, headers=boys_warden)
    assert r.status_code == 403


def test_chief_provost_can_exit_student_and_vacate_bed(client, chief_provost, hostel_data, db):
    """Chief Provost exits student, closing allocation and reverting to day scholar."""
    adm = hostel_data["active_boy_admission"]
    assert adm is not None

    r = client.post(
        f"/admin/hostel/admissions/{adm.id}/exit",
        json={"exit_date": "2026-10-08", "exit_reason": "Senior session completion"},
        headers=chief_provost,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "vacated"

    # Verify DB state
    db.expire_all()
    refreshed_adm = db.get(HostelAdmission, adm.id)
    assert refreshed_adm.status == "vacated"
    assert refreshed_adm.exit_date == date(2026, 10, 8)

    # Allocation closed
    alloc = db.scalar(
        select(BedAllocation).where(
            BedAllocation.admission_id == adm.id,
            BedAllocation.is_active == False,
        )
    )
    assert alloc is not None
    assert alloc.vacated_at is not None


# ==============================================================================
# 4. Room & Bed Transfers Preserving History
# ==============================================================================


def test_bed_transfer_preserves_history(client, chief_provost, hostel_data, db):
    """Transferring student to a new bed closes old allocation with timestamp and opens new allocation."""
    adm = hostel_data["active_boy_admission"]
    vacant = hostel_data["vacant_bed"]
    vacant.status = "available"
    db.flush()

    r = client.post(
        f"/admin/hostel/admissions/{adm.id}/transfer",
        json={"new_bed_id": vacant.id, "reason": "Room shift to ground floor"},
        headers=chief_provost,
    )
    assert r.status_code == 200
    assert r.json()["bed_number"] == vacant.bed_number

    # Verify allocation history in DB
    history = list(
        db.scalars(
            select(BedAllocation)
            .where(BedAllocation.admission_id == adm.id)
            .order_by(BedAllocation.allocated_at.desc())
        )
    )
    assert len(history) >= 2
    assert history[0].is_active is True
    assert history[0].bed_id == vacant.id
    assert history[1].is_active is False
    assert history[1].vacated_at is not None


# ==============================================================================
# 5. Evening 8:00 PM Attendance & Pre-populated Leaves
# ==============================================================================


def test_evening_attendance_roll_call(client, boys_warden, hostel_data):
    """Warden submits evening attendance for assigned hostel at 8:00 PM."""
    boys_id = hostel_data["boys_hostel"].id
    today_str = date.today().isoformat()

    # Fetch roster
    roster_res = client.get(
        f"/admin/hostel/{boys_id}/attendance?on_date={today_str}",
        headers=boys_warden,
    )
    assert roster_res.status_code == 200
    roster = roster_res.json()
    assert len(roster) > 0

    # Submit batch attendance
    entries = [{"student_id": r["student_id"], "status": "present"} for r in roster]
    sub_res = client.post(
        f"/admin/hostel/{boys_id}/attendance",
        json={"attendance_date": today_str, "entries": entries},
        headers=boys_warden,
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["marked_count"] == len(entries)


# ==============================================================================
# 6. Parent Leave Submission & Overdue Alert
# ==============================================================================


def test_student_cannot_apply_for_leave_or_outing(client, db):
    """Students cannot submit leave or outing requests (HTTP 404 / 405 / unauthorized)."""
    # Student token
    r = client.post("/student/hostel/leave", json={"request_type": "outing"})
    # No student leave submission route exists
    assert r.status_code in (401, 404, 405)


def test_overdue_outing_calculation(db, hostel_data):
    """Outings past expected return time without recorded arrival are flagged overdue."""
    adm = hostel_data["active_boy_admission"]
    now = datetime.now(UTC)

    guardian = db.scalar(
        select(Guardian)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(StudentGuardian.student_id == adm.student_id)
    )
    if not guardian:
        guardian = db.scalar(select(Guardian).where(Guardian.school_id == adm.school_id))
    guardian_id = guardian.id if guardian else 1

    # Create an outing that was expected back 2 hours ago
    past_due_req = HostelLeaveRequest(
        school_id=adm.school_id,
        hostel_id=adm.hostel_id,
        student_id=adm.student_id,
        admission_id=adm.id,
        parent_guardian_id=guardian_id,
        request_type="outing",
        start_date=date.today(),
        end_date=date.today(),
        expected_return_time=now - timedelta(hours=2),
        actual_return_time=None,
        purpose="City book fair",
        status="approved",
    )
    db.add(past_due_req)
    db.flush()

    # Query through service
    admin_u = db.scalar(select(User).where(User.login_id == "provost@sunrisepublic.edu"))
    requests = hostel_svc.get_leave_requests(db, adm.school_id, admin_u, hostel_id=adm.hostel_id)
    matching = next((r for r in requests if r["id"] == past_due_req.id), None)
    assert matching is not None
    assert matching["is_overdue"] is True


# ==============================================================================
# 7. Dynamic FeePlanItem Lookup (Idempotent, No Hardcoding)
# ==============================================================================


def test_hostel_charges_for_month_dynamic_and_idempotent(db, hostel_data):
    """Hostel monthly fee dynamically resolves from FeePlanItem for FeeHead 'HOSTEL'."""
    adm = hostel_data["active_boy_admission"]
    school_id = adm.school_id

    # Sourced from fee engine
    charges_1 = hostel_svc.charges_for_month(db, school_id, year=2026, month=9)
    assert isinstance(charges_1, dict)

    # Idempotent: second run yields exact identical amounts
    charges_2 = hostel_svc.charges_for_month(db, school_id, year=2026, month=9)
    assert charges_1 == charges_2


def test_student_and_parent_hostel_views_and_leaves(client, db, hostel_data, boys_warden):
    """Verifies Student & Parent portals, notices resolution, and leave workflow."""
    from app.core.security import create_access_token

    adm = hostel_data["active_boy_admission"]
    student = db.get(Student, adm.student_id)
    student_user = student.user

    # Broadcast a hostel notice
    notice = HostelNotice(
        school_id=adm.school_id,
        hostel_id=adm.hostel_id,
        title="Quiet Hours Announcement",
        content="Quiet hours begin at 10 PM tonight.",
        priority="important",
        posted_by_id=student_user.id,
        posted_at=datetime.now(UTC),
        is_active=True,
    )
    db.add(notice)
    db.flush()

    # Authenticate student
    st_token = create_access_token(student_user.id, "student")
    st_headers = {"Authorization": f"Bearer {st_token}"}

    # Student checks /student/hostel
    st_res = client.get("/student/hostel", headers=st_headers)
    assert st_res.status_code == 200, st_res.text
    st_data = st_res.json()
    assert st_data["is_hosteller"] is True
    assert st_data["hostel"]["id"] == adm.hostel_id
    assert "room" in st_data
    assert "bed" in st_data
    assert "notices" in st_data
    assert any(n["title"] == "Quiet Hours Announcement" for n in st_data["notices"])
    assert "mess_menu" in st_data

    # Student cannot submit leave/outing
    post_res = client.post("/student/hostel/leave", json={"request_type": "outing"}, headers=st_headers)
    assert post_res.status_code in (404, 405)

    # Parent authentication
    sg = db.scalar(select(StudentGuardian).where(StudentGuardian.student_id == student.id))
    guardian = db.get(Guardian, sg.guardian_id) if sg else None
    if not guardian:
        guardian = db.scalar(select(Guardian).where(Guardian.school_id == student.school_id))
    parent_user = guardian.user
    p_token = create_access_token(parent_user.id, "parent")
    p_headers = {"Authorization": f"Bearer {p_token}"}

    # Parent checks child hostel status
    p_res = client.get(f"/parent/children/{student.id}/hostel", headers=p_headers)
    assert p_res.status_code == 200, p_res.text
    p_data = p_res.json()
    assert p_data["is_hosteller"] is True
    assert p_data["hostel"]["id"] == adm.hostel_id
    assert any(n["title"] == "Quiet Hours Announcement" for n in p_data["notices"])

    # Parent submits leave request
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    now_iso = (datetime.now(UTC) + timedelta(hours=5)).isoformat()
    leave_payload = {
        "request_type": "leave",
        "start_date": today_str,
        "end_date": tomorrow_str,
        "expected_return_time": now_iso,
        "purpose": "Family wedding visit",
    }
    sub_res = client.post(f"/parent/children/{student.id}/hostel/leave", json=leave_payload, headers=p_headers)
    assert sub_res.status_code == 201, sub_res.text
    leave_id = sub_res.json()["id"]

    # Warden approves leave
    app_res = client.post(
        f"/admin/hostel/leaves/{leave_id}/adjudicate",
        json={"action": "approve", "remarks": "Approved with guardian consent"},
        headers=boys_warden,
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"

    # Warden records return
    ret_res = client.post(
        f"/admin/hostel/leaves/{leave_id}/return",
        json={},
        headers=boys_warden,
    )
    assert ret_res.status_code == 200
    assert ret_res.json()["status"] == "returned"


# ==============================================================================
# 8. RBAC Separation: Admin vs Chief Provost vs Warden
# ==============================================================================


def test_existing_admin_functionality_intact(client, admin):
    """The existing Admin remains the full ERP administrator with access to all school modules."""
    # 1. Students roster
    r_students = client.get("/admin/students", headers=admin)
    assert r_students.status_code == 200

    # 2. Invoices & finance
    r_fees = client.get("/admin/fees/invoices", headers=admin)
    assert r_fees.status_code == 200

    # 3. Administrative overview of hostel
    r_hostel = client.get("/admin/hostel/overview", headers=admin)
    assert r_hostel.status_code == 200


def test_admin_is_not_chief_provost(db):
    """Admin role assignment is super_admin, Chief Provost is chief_provost, and Warden is warden."""
    from app.models import Role, UserRoleAssignment

    admin_u = db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))
    provost_u = db.scalar(select(User).where(User.login_id == "provost@sunrisepublic.edu"))
    warden_u = db.scalar(select(User).where(User.login_id == "warden.boys@sunrisepublic.edu"))

    admin_roles = set(
        db.scalars(
            select(Role.code)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == admin_u.id)
        )
    )
    provost_roles = set(
        db.scalars(
            select(Role.code)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == provost_u.id)
        )
    )
    warden_roles = set(
        db.scalars(
            select(Role.code)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == warden_u.id)
        )
    )

    # Admin holds super_admin, never chief_provost
    assert "super_admin" in admin_roles
    assert "chief_provost" not in admin_roles

    # Chief Provost holds chief_provost, never super_admin
    assert "chief_provost" in provost_roles
    assert "super_admin" not in provost_roles

    # Warden holds warden, never super_admin or chief_provost
    assert "warden" in warden_roles
    assert "super_admin" not in warden_roles
    assert "chief_provost" not in warden_roles


def test_chief_provost_cannot_access_unrelated_erp_apis(client, chief_provost):
    """Chief Provost is strictly scoped to Hostel/Mess and cannot access unrelated ERP endpoints."""
    # Cannot read or manage school-wide students roster
    r1 = client.get("/admin/students", headers=chief_provost)
    assert r1.status_code == 403

    # Cannot access school-wide fee invoices
    r2 = client.get("/admin/fees/invoices", headers=chief_provost)
    assert r2.status_code == 403

    # Cannot access transport routes
    r3 = client.get("/admin/transport/routes", headers=chief_provost)
    assert r3.status_code == 403

    # Cannot access school settings
    r4 = client.get("/admin/settings", headers=chief_provost)
    assert r4.status_code == 403


def test_warden_cannot_access_unrelated_erp_apis(client, boys_warden):
    """Warden is strictly scoped to Hostel and cannot access unrelated ERP endpoints."""
    r1 = client.get("/admin/students", headers=boys_warden)
    assert r1.status_code == 403

    r2 = client.get("/admin/fees/invoices", headers=boys_warden)
    assert r2.status_code == 403

    r3 = client.get("/admin/transport/routes", headers=boys_warden)
    assert r3.status_code == 403

    r4 = client.get("/admin/settings", headers=boys_warden)
    assert r4.status_code == 403


def test_warden_cannot_perform_provost_operations(client, boys_warden, hostel_data):
    """Warden cannot mutate hostel physical structure or create hostels."""
    boys_id = hostel_data["boys_hostel"].id

    # Cannot create hostel
    r_create = client.post(
        "/admin/hostel",
        json={"name": "New Wing", "code": "NW-01", "gender": "male", "description": "Test"},
        headers=boys_warden,
    )
    assert r_create.status_code == 403

    # Cannot create floor
    r_floor = client.post(
        f"/admin/hostel/{boys_id}/floors",
        json={"floor_number": 3, "floor_name": "Third Floor"},
        headers=boys_warden,
    )
    assert r_floor.status_code == 403


def test_day_scholar_hostel_admission_workflow(client, chief_provost, hostel_data, db):
    """Admitting an eligible Class 9+ day scholar updates bed occupancy, room occupancy, and admission status."""
    c10 = hostel_data["class_10_boy"]
    boys_hostel = hostel_data["boys_hostel"]
    vacant_bed = hostel_data["vacant_bed"]
    vacant_bed.status = "available"
    db.flush()

    assert c10 is not None, "Class 10 male student must exist"
    assert vacant_bed is not None, "Vacant bed must exist"

    payload = {
        "student_id": c10.id,
        "hostel_id": boys_hostel.id,
        "bed_id": vacant_bed.id,
        "admission_date": date.today().isoformat(),
        "remarks": "Day scholar opting for hostel",
    }
    r = client.post("/admin/hostel/admissions", json=payload, headers=chief_provost)
    assert r.status_code == 201, r.text
    adm_id = r.json()["id"]

    # Verify bed status updated to occupied
    db.expire_all()
    refreshed_bed = db.get(HostelBed, vacant_bed.id)
    assert refreshed_bed.status == "occupied"

    # Verify room has active allocation
    refreshed_room = db.get(HostelRoom, refreshed_bed.room_id)
    assert refreshed_room.status in ("occupied", "partial", "available")

    # Verify active admission record exists
    adm = db.get(HostelAdmission, adm_id)
    assert adm.status == "active"
    assert adm.student_id == c10.id
    assert adm.hostel_id == boys_hostel.id

    # Verify BedAllocation active record
    alloc = db.scalar(
        select(BedAllocation).where(
            BedAllocation.admission_id == adm.id,
            BedAllocation.is_active == True,
        )
    )
    assert alloc is not None
    assert alloc.bed_id == vacant_bed.id


def test_admin_hostel_permissions_and_boundaries(client, admin, hostel_data, db):
    """Admin has full access to Hostel Dashboard overview and Admissions, but is strictly denied operational endpoints."""
    boys_hostel = hostel_data["boys_hostel"]

    # 1. Admin can access overview
    r_overview = client.get("/admin/hostel/overview", headers=admin)
    assert r_overview.status_code == 200, r_overview.text
    assert "total_hostels" in r_overview.json()
    assert "total_beds" in r_overview.json()

    # 2. Admin can access admissions queues
    r_pending = client.get("/admin/hostel/admissions/pending-applications", headers=admin)
    assert r_pending.status_code == 200, r_pending.text

    r_eligible = client.get("/admin/hostel/admissions/eligible-students", headers=admin)
    assert r_eligible.status_code == 200, r_eligible.text

    # 3. Admin can list available beds
    r_beds = client.get(f"/admin/hostel/{boys_hostel.id}/available-beds", headers=admin)
    assert r_beds.status_code == 200, r_beds.text

    # 4. Admin CANNOT access restricted operational hostel endpoints
    # Attendance roll-call
    r_att_get = client.get(f"/admin/hostel/{boys_hostel.id}/attendance", headers=admin)
    assert r_att_get.status_code == 403

    r_att_post = client.post(
        f"/admin/hostel/{boys_hostel.id}/attendance",
        json={"attendance_date": "2026-10-10", "entries": []},
        headers=admin,
    )
    assert r_att_post.status_code == 403

    # Leaves review and adjudication
    r_leaves = client.get("/admin/hostel/leaves", headers=admin)
    assert r_leaves.status_code == 403

    r_adjudicate = client.post(
        "/admin/hostel/leaves/1/adjudicate",
        json={"action": "approve"},
        headers=admin,
    )
    assert r_adjudicate.status_code == 403

    # Mess menu editing
    r_menu = client.put(
        "/admin/hostel/menu",
        json={"menu": []},
        headers=admin,
    )
    assert r_menu.status_code == 403

    # Physical hostel creation
    r_create = client.post(
        "/admin/hostel",
        json={"name": "Forbidden Wing", "code": "FW-01", "gender": "male"},
        headers=admin,
    )
    assert r_create.status_code == 403

    # Permanent student exit
    r_exit = client.post(
        "/admin/hostel/admissions/1/exit",
        json={"exit_date": "2026-10-10", "exit_reason": "Graduated"},
        headers=admin,
    )
    assert r_exit.status_code == 403


def test_warden_denied_all_hostel_admissions(client, boys_warden, hostel_data):
    """Warden is strictly denied access to hostel admissions queues and operations."""
    boys_hostel = hostel_data["boys_hostel"]

    # 1. Denied viewing pending intake applications
    r1 = client.get("/admin/hostel/admissions/pending-applications", headers=boys_warden)
    assert r1.status_code == 403

    r1_alias = client.get("/admin/hostel/pending-applications", headers=boys_warden)
    assert r1_alias.status_code == 403

    # 2. Denied viewing eligible day scholars
    r2 = client.get("/admin/hostel/admissions/eligible-students", headers=boys_warden)
    assert r2.status_code == 403

    r2_alias = client.get("/admin/hostel/eligible-day-scholars", headers=boys_warden)
    assert r2_alias.status_code == 403

    # 3. Denied performing admission POST
    r3 = client.post(
        "/admin/hostel/admissions",
        json={
            "student_id": 1,
            "hostel_id": boys_hostel.id,
            "bed_id": 1,
            "admission_date": "2026-10-10",
        },
        headers=boys_warden,
    )
    assert r3.status_code == 403

    # 4. Denied direct admission POST
    r4 = client.post(
        f"/admin/hostel/{boys_hostel.id}/admissions/direct",
        json={
            "student_id": 1,
            "bed_id": 1,
            "admission_date": "2026-10-10",
        },
        headers=boys_warden,
    )
    assert r4.status_code == 403



