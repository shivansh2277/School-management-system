"""Hostel and Mess management business logic.

Adheres strictly to ERP architecture rules:
- Services flush(), Endpoints commit()
- Scope enforced via UserRoleAssignment in services/hostel_scoping.py
- Class 9+ eligibility and gender invariants enforced server-side
- Bed capacity and single-occupant invariants enforced
- Chief Provost exclusive exit workflow
- Dynamic fee lookup from fee_plans without hardcoded amounts or fractional proration
- 8:00 PM evening attendance with auto-leave resolution
"""

from datetime import UTC, date, datetime, time
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    FeeHead,
    FeePlan,
    FeePlanItem,
    Gender,
    Guardian,
    Student,
    StudentFeePlan,
    StudentGuardian,
    User,
    UserRole,
    Hostel,
    HostelFloor,
    HostelRoom,
    HostelBed,
    HostelAdmission,
    BedAllocation,
    HostelAttendance,
    HostelLeaveRequest,
    HostelMessMenu,
    HostelComplaint,
    HostelIncident,
    HostelNotice,
    Application,
    ApplicationStatus,
)
from app.services.hostel_scoping import (
    assert_can_manage_hostel,
    get_warden_assigned_hostel_id,
    is_chief_provost_or_admin,
    readable_hostel_ids_for,
)

ELIGIBLE_CLASSES = {"9", "10", "11", "12"}


def bad_request(msg: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)


def conflict(msg: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, msg)


def not_found(msg: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, msg)


def forbidden(msg: str) -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, msg)


# --- Eligibility & Invariants ------------------------------------------------


def get_student_current_enrolment(db: Session, student_id: int) -> Enrolment | None:
    """Finds the active enrolment for a student in an active academic year."""
    return db.scalar(
        select(Enrolment)
        .join(AcademicYear, AcademicYear.id == Enrolment.academic_year_id)
        .where(
            Enrolment.student_id == student_id,
            Enrolment.status == EnrolmentStatus.active,
        )
        .order_by(Enrolment.id.desc())
    )


def assert_student_eligibility(db: Session, student: Student, hostel: Hostel) -> None:
    """Enforces Class 9+ and gender integrity. Server rejects Class <= 8 with HTTP 422."""
    enrolment = get_student_current_enrolment(db, student.id)
    if enrolment is None:
        raise bad_request("Student has no active academic enrolment")

    section = db.get(ClassSection, enrolment.class_section_id)
    if not section or section.class_name not in ELIGIBLE_CLASSES:
        current_cls = section.class_name if section else "Unknown"
        raise bad_request(
            f"Hostel accommodation is available strictly to Class 9 and above. Student is in Class {current_cls}."
        )

    # Gender match
    if hostel.gender == Gender.male and student.gender != Gender.male:
        raise bad_request("Male students can only be admitted to Boys Hostel")
    if hostel.gender == Gender.female and student.gender != Gender.female:
        raise bad_request("Female students can only be admitted to Girls Hostel")

    # Check active stay
    active_stay = db.scalar(
        select(HostelAdmission.id).where(
            HostelAdmission.student_id == student.id,
            HostelAdmission.status == "active",
        )
    )
    if active_stay:
        raise conflict("Student already has an active hostel admission")


# --- Overview & Structure -----------------------------------------------------


def get_overview(db: Session, school_id: int, user: User) -> dict:
    """Calculates dashboard summary metrics scoped to the caller's authority."""
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(Hostel).where(Hostel.school_id == school_id)
    if allowed_ids is not None:
        q = q.where(Hostel.id.in_(allowed_ids))
    hostels = list(db.scalars(q))

    h_ids = [h.id for h in hostels]
    if not h_ids:
        return {
            "total_hostels": 0,
            "total_rooms": 0,
            "total_beds": 0,
            "occupied_beds": 0,
            "vacant_beds": 0,
            "occupancy_rate": 0.0,
            "today_attendance": {"present": 0, "absent": 0, "on_leave": 0, "on_outing": 0},
            "pending_leaves": 0,
            "open_complaints": 0,
            "hostels": [],
        }

    total_rooms = db.scalar(
        select(func.count(HostelRoom.id)).where(HostelRoom.hostel_id.in_(h_ids))
    ) or 0

    total_beds = db.scalar(
        select(func.count(HostelBed.id))
        .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
        .where(HostelRoom.hostel_id.in_(h_ids))
    ) or 0

    occupied_beds = db.scalar(
        select(func.count(BedAllocation.id))
        .join(HostelBed, HostelBed.id == BedAllocation.bed_id)
        .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
        .where(HostelRoom.hostel_id.in_(h_ids), BedAllocation.is_active == True)
    ) or 0

    vacant_beds = max(0, total_beds - occupied_beds)
    rate = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    today = date.today()
    att_rows = db.execute(
        select(HostelAttendance.status, func.count(HostelAttendance.id))
        .where(HostelAttendance.hostel_id.in_(h_ids), HostelAttendance.attendance_date == today)
        .group_by(HostelAttendance.status)
    ).all()
    att_map = dict(att_rows)

    pending_leaves = db.scalar(
        select(func.count(HostelLeaveRequest.id)).where(
            HostelLeaveRequest.hostel_id.in_(h_ids),
            HostelLeaveRequest.status == "pending",
        )
    ) or 0

    open_complaints = db.scalar(
        select(func.count(HostelComplaint.id)).where(
            HostelComplaint.hostel_id.in_(h_ids),
            HostelComplaint.status.in_(("pending", "in_progress")),
        )
    ) or 0

    hostels_summary = []
    for h in hostels:
        h_beds = db.scalar(
            select(func.count(HostelBed.id))
            .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
            .where(HostelRoom.hostel_id == h.id)
        ) or 0
        h_occ = db.scalar(
            select(func.count(BedAllocation.id))
            .join(HostelBed, HostelBed.id == BedAllocation.bed_id)
            .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
            .where(HostelRoom.hostel_id == h.id, BedAllocation.is_active == True)
        ) or 0
        hostels_summary.append({
            "id": h.id,
            "name": h.name,
            "code": h.code,
            "gender": h.gender.value,
            "status": h.status,
            "total_beds": h_beds,
            "occupied_beds": h_occ,
            "vacant_beds": max(0, h_beds - h_occ),
            "occupancy_rate": round(h_occ / h_beds * 100, 1) if h_beds > 0 else 0.0,
        })

    return {
        "total_hostels": len(hostels),
        "total_rooms": total_rooms,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "vacant_beds": vacant_beds,
        "occupancy_rate": rate,
        "today_attendance": {
            "present": att_map.get("present", 0),
            "absent": att_map.get("absent", 0),
            "on_leave": att_map.get("on_leave", 0),
            "on_outing": att_map.get("on_outing", 0),
        },
        "pending_leaves": pending_leaves,
        "open_complaints": open_complaints,
        "hostels": hostels_summary,
    }


def get_structure(db: Session, school_id: int, user: User, hostel_id: int | None = None) -> list[dict]:
    """Retrieves full nested hierarchy: Hostel -> Floor -> Room -> Bed -> Student."""
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(Hostel).where(Hostel.school_id == school_id)
    if allowed_ids is not None:
        q = q.where(Hostel.id.in_(allowed_ids))
    if hostel_id is not None:
        assert_can_manage_hostel(db, user, hostel_id)
        q = q.where(Hostel.id == hostel_id)

    hostels = list(db.scalars(q.order_by(Hostel.name)))
    out = []

    for h in hostels:
        floors_out = []
        for f in h.floors:
            rooms_out = []
            for r in f.rooms:
                beds_out = []
                for b in r.beds:
                    active_alloc = db.scalar(
                        select(BedAllocation).where(
                            BedAllocation.bed_id == b.id,
                            BedAllocation.is_active == True,
                        )
                    )
                    resident_info = None
                    if active_alloc and active_alloc.admission:
                        adm = active_alloc.admission
                        stu = adm.student
                        enrol = get_student_current_enrolment(db, stu.id)
                        sec = db.get(ClassSection, enrol.class_section_id) if enrol else None
                        resident_info = {
                            "admission_id": adm.id,
                            "student_id": stu.id,
                            "admission_no": stu.admission_no,
                            "full_name": stu.user.full_name,
                            "class_label": f"{sec.class_name}-{sec.section}" if sec else "N/A",
                            "gender": stu.gender.value if stu.gender else "N/A",
                            "admission_date": adm.admission_date.isoformat(),
                            "allocated_at": active_alloc.allocated_at.isoformat(),
                        }
                    beds_out.append({
                        "id": b.id,
                        "bed_number": b.bed_number,
                        "status": b.status,
                        "is_occupied": active_alloc is not None,
                        "resident": resident_info,
                    })
                rooms_out.append({
                    "id": r.id,
                    "room_number": r.room_number,
                    "capacity": r.capacity,
                    "room_type": r.room_type,
                    "status": r.status,
                    "occupied_count": sum(1 for b in beds_out if b["is_occupied"]),
                    "beds": beds_out,
                })
            floors_out.append({
                "id": f.id,
                "floor_number": f.floor_number,
                "floor_name": f.floor_name,
                "status": f.status,
                "rooms": rooms_out,
            })
        out.append({
            "id": h.id,
            "name": h.name,
            "code": h.code,
            "gender": h.gender.value,
            "status": h.status,
            "description": h.description,
            "floors": floors_out,
        })

    return out


def get_available_beds(db: Session, school_id: int, hostel_id: int) -> list[dict]:
    """Retrieves all currently available beds in a hostel."""
    occupied_bed_ids = select(BedAllocation.bed_id).where(BedAllocation.is_active == True)
    rows = db.execute(
        select(HostelBed, HostelRoom, HostelFloor)
        .join(HostelRoom, HostelRoom.id == HostelBed.room_id)
        .join(HostelFloor, HostelFloor.id == HostelRoom.floor_id)
        .where(
            HostelFloor.hostel_id == hostel_id,
            HostelBed.status == "available",
            HostelBed.id.not_in(occupied_bed_ids),
        )
        .order_by(HostelFloor.floor_number, HostelRoom.room_number, HostelBed.bed_number)
    ).all()
    return [
        {
            "id": b.id,
            "bed_id": b.id,
            "bed_number": b.bed_number,
            "room_number": r.room_number,
            "floor_number": f.floor_number,
        }
        for b, r, f in rows
    ]


# --- Resident Management & Admissions -----------------------------------------


def get_residents(
    db: Session,
    school_id: int,
    user: User,
    hostel_id: int | None = None,
    status_filter: str = "active",
) -> list[dict]:
    """Lists hostel residents with their current allocation details."""
    allowed_ids = readable_hostel_ids_for(db, user)
    q = (
        select(HostelAdmission)
        .join(Hostel, Hostel.id == HostelAdmission.hostel_id)
        .where(HostelAdmission.school_id == school_id)
    )
    if allowed_ids is not None:
        q = q.where(HostelAdmission.hostel_id.in_(allowed_ids))
    if hostel_id is not None:
        assert_can_manage_hostel(db, user, hostel_id)
        q = q.where(HostelAdmission.hostel_id == hostel_id)
    if status_filter:
        q = q.where(HostelAdmission.status == status_filter)

    admissions = list(db.scalars(q.order_by(HostelAdmission.admission_date.desc())))
    out = []

    for adm in admissions:
        stu = adm.student
        enrol = get_student_current_enrolment(db, stu.id)
        sec = db.get(ClassSection, enrol.class_section_id) if enrol else None
        active_alloc = db.scalar(
            select(BedAllocation).where(
                BedAllocation.admission_id == adm.id,
                BedAllocation.is_active == True,
            )
        )
        bed_str = "None"
        room_str = "None"
        bed_id = None
        floor_num = None
        if active_alloc and active_alloc.bed:
            bed = active_alloc.bed
            bed_str = bed.bed_number
            bed_id = bed.id
            if bed.room:
                room_str = bed.room.room_number
                if bed.room.floor:
                    floor_num = bed.room.floor.floor_number

        out.append({
            "id": adm.id,
            "admission_id": adm.id,
            "student_id": stu.id,
            "admission_no": stu.admission_no,
            "full_name": stu.user.full_name,
            "student_name": stu.user.full_name,
            "gender": stu.gender.value if stu.gender else "N/A",
            "class_label": f"{sec.class_name}-{sec.section}" if sec else "N/A",
            "hostel_id": adm.hostel_id,
            "hostel_name": adm.hostel.name,
            "floor_number": floor_num,
            "room_number": room_str,
            "bed_number": bed_str,
            "bed_id": bed_id,
            "admission_date": adm.admission_date.isoformat(),
            "status": adm.status,
            "exit_date": adm.exit_date.isoformat() if adm.exit_date else None,
            "exit_reason": adm.exit_reason,
            "remarks": adm.remarks,
        })
    return out


def admit_student(
    db: Session,
    school_id: int,
    user: User,
    student_id: int,
    hostel_id: int,
    bed_id: int,
    admission_date: date,
    remarks: str | None = None,
) -> HostelAdmission:
    """Admits an eligible Class 9+ student and allocates a specific bed."""
    if get_warden_assigned_hostel_id(db, user) is not None:
        raise forbidden("Wardens cannot manage hostel admissions")
    assert_can_manage_hostel(db, user, hostel_id)
    hostel = db.get(Hostel, hostel_id)
    if not hostel or hostel.school_id != school_id:
        raise not_found("Hostel not found")

    student = db.get(Student, student_id)
    if not student or student.school_id != school_id:
        raise not_found("Student not found")

    assert_student_eligibility(db, student, hostel)

    bed = db.get(HostelBed, bed_id)
    if not bed or bed.school_id != school_id:
        raise not_found("Bed not found")

    room = db.get(HostelRoom, bed.room_id)
    if not room or room.hostel_id != hostel_id:
        raise bad_request("Bed does not belong to the selected hostel")

    if bed.status != "available":
        raise conflict(f"Bed {bed.bed_number} is already occupied or under maintenance")

    # Double booking invariant
    existing_active = db.scalar(
        select(BedAllocation.id).where(BedAllocation.bed_id == bed_id, BedAllocation.is_active == True)
    )
    if existing_active:
        raise conflict(f"Bed {bed.bed_number} already has an active occupant")

    # Room capacity invariant
    active_in_room = db.scalar(
        select(func.count(BedAllocation.id))
        .join(HostelBed, HostelBed.id == BedAllocation.bed_id)
        .where(HostelBed.room_id == room.id, BedAllocation.is_active == True)
    ) or 0
    if active_in_room >= room.capacity:
        raise bad_request(f"Room {room.room_number} is already at full capacity ({room.capacity})")

    admission = HostelAdmission(
        school_id=school_id,
        student_id=student.id,
        hostel_id=hostel.id,
        admission_date=admission_date,
        status="active",
        remarks=remarks,
        admitted_by_id=user.id,
    )
    db.add(admission)
    db.flush()

    allocation = BedAllocation(
        school_id=school_id,
        admission_id=admission.id,
        bed_id=bed.id,
        allocated_at=datetime.now(UTC),
        is_active=True,
        allocated_by_id=user.id,
    )
    db.add(allocation)

    bed.status = "occupied"
    if active_in_room + 1 >= room.capacity:
        room.status = "full"

    db.flush()
    return admission


def transfer_bed(
    db: Session,
    school_id: int,
    user: User,
    admission_id: int,
    new_bed_id: int,
    reason: str,
) -> BedAllocation:
    """Transfers a resident to another bed, closing the previous allocation and maintaining history."""
    admission = db.get(HostelAdmission, admission_id)
    if not admission or admission.school_id != school_id:
        raise not_found("Hostel admission record not found")
    if admission.status != "active":
        raise bad_request("Cannot transfer a student who is not currently an active resident")

    assert_can_manage_hostel(db, user, admission.hostel_id)

    new_bed = db.get(HostelBed, new_bed_id)
    if not new_bed or new_bed.school_id != school_id:
        raise not_found("Target bed not found")

    new_room = db.get(HostelRoom, new_bed.room_id)
    if not new_room:
        raise not_found("Target room not found")

    # Scope check for target hostel
    assert_can_manage_hostel(db, user, new_room.hostel_id)

    if new_bed.status != "available":
        raise conflict(f"Bed {new_bed.bed_number} is already occupied or unavailable")

    # Close prior allocation
    old_alloc = db.scalar(
        select(BedAllocation).where(
            BedAllocation.admission_id == admission.id,
            BedAllocation.is_active == True,
        )
    )
    if old_alloc:
        old_alloc.vacated_at = datetime.now(UTC)
        old_alloc.is_active = False
        old_bed = db.get(HostelBed, old_alloc.bed_id)
        if old_bed:
            old_bed.status = "available"
            if old_bed.room:
                old_bed.room.status = "available"

    # Create new allocation
    new_alloc = BedAllocation(
        school_id=school_id,
        admission_id=admission.id,
        bed_id=new_bed.id,
        allocated_at=datetime.now(UTC),
        is_active=True,
        allocated_by_id=user.id,
        remarks=reason,
    )
    db.add(new_alloc)
    new_bed.status = "occupied"

    # Re-evaluate new room capacity
    active_in_new_room = db.scalar(
        select(func.count(BedAllocation.id))
        .join(HostelBed, HostelBed.id == BedAllocation.bed_id)
        .where(HostelBed.room_id == new_room.id, BedAllocation.is_active == True)
    ) or 0
    if active_in_new_room + 1 >= new_room.capacity:
        new_room.status = "full"

    db.flush()
    return new_alloc


def exit_student(
    db: Session,
    school_id: int,
    user: User,
    admission_id: int,
    exit_date: date,
    exit_reason: str,
) -> HostelAdmission:
    """Permanently exits a student from the hostel. Exclusively permitted to Chief Provost."""
    if not is_chief_provost_or_admin(db, user):
        raise forbidden("Only the Chief Provost has authority to permanently exit a student from the hostel")

    if not exit_reason or not exit_reason.strip():
        raise bad_request("An exit reason is mandatory when removing a student from hostel")

    admission = db.get(HostelAdmission, admission_id)
    if not admission or admission.school_id != school_id:
        raise not_found("Hostel admission record not found")
    if admission.status != "active":
        raise bad_request("Student is already exited or vacated from hostel")

    admission.status = "vacated"
    admission.exit_date = exit_date
    admission.exit_reason = exit_reason
    admission.exited_by_id = user.id

    # Close active allocation
    active_alloc = db.scalar(
        select(BedAllocation).where(
            BedAllocation.admission_id == admission.id,
            BedAllocation.is_active == True,
        )
    )
    if active_alloc:
        active_alloc.vacated_at = datetime.now(UTC)
        active_alloc.is_active = False
        bed = db.get(HostelBed, active_alloc.bed_id)
        if bed:
            bed.status = "available"
            if bed.room:
                bed.room.status = "available"

    db.flush()
    return admission


def get_allocation_history(db: Session, school_id: int, admission_id: int) -> list[dict]:
    """Returns chronological allocation and transfer records for an admission."""
    admission = db.get(HostelAdmission, admission_id)
    if not admission or admission.school_id != school_id:
        raise not_found("Admission not found")

    allocs = list(
        db.scalars(
            select(BedAllocation)
            .where(BedAllocation.admission_id == admission_id)
            .order_by(BedAllocation.allocated_at.desc())
        )
    )
    out = []
    for a in allocs:
        bed = a.bed
        room = bed.room if bed else None
        hostel = room.hostel if room else None
        out.append({
            "id": a.id,
            "bed_number": bed.bed_number if bed else "N/A",
            "room_number": room.room_number if room else "N/A",
            "hostel_name": hostel.name if hostel else "N/A",
            "allocated_at": a.allocated_at.isoformat(),
            "vacated_at": a.vacated_at.isoformat() if a.vacated_at else None,
            "is_active": a.is_active,
            "remarks": a.remarks,
        })
    return out


# --- Application Intake & Day Scholar Admission Queues -----------------------


def get_pending_applications(db: Session, school_id: int, user: User) -> list[dict]:
    """Enrolled students who requested hostel accommodation during admission intake."""
    if get_warden_assigned_hostel_id(db, user) is not None:
        raise forbidden("Wardens cannot access hostel admissions")
    q = (
        select(Application)
        .where(
            Application.school_id == school_id,
            Application.hostel_required == True,
            Application.status == ApplicationStatus.enrolled,
            Application.student_id.isnot(None),
        )
        .order_by(Application.submitted_at.desc())
    )
    apps = list(db.scalars(q))
    out = []

    for app in apps:
        student_id = app.student_id
        # Check if already admitted to hostel
        active_adm = db.scalar(
            select(HostelAdmission).where(
                HostelAdmission.student_id == student_id,
                HostelAdmission.status == "active",
            )
        )
        if active_adm:
            derived_status = "Allocated"
        else:
            derived_status = "Pending Allocation"

        out.append({
            "application_id": app.id,
            "application_no": app.application_no,
            "student_id": student_id,
            "full_name": app.full_name,
            "class_name": app.class_applying_for,
            "gender": app.gender,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "hostel_request_status": derived_status,
            "is_allocated": active_adm is not None,
            "allocated_hostel_name": active_adm.hostel.name if active_adm else None,
        })
    return out


def get_eligible_day_scholars(db: Session, school_id: int, user: User) -> list[dict]:
    """Class 9+ enrolled day scholars available for independent hostel admission."""
    if get_warden_assigned_hostel_id(db, user) is not None:
        raise forbidden("Wardens cannot access hostel admissions")
    # Active hosteller student IDs
    active_hosteller_ids = select(HostelAdmission.student_id).where(
        HostelAdmission.school_id == school_id,
        HostelAdmission.status == "active",
    )

    q = (
        select(Student, ClassSection.class_name, ClassSection.section)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .join(ClassSection, ClassSection.id == Enrolment.class_section_id)
        .where(
            Student.school_id == school_id,
            ClassSection.class_name.in_(ELIGIBLE_CLASSES),
            Enrolment.status == EnrolmentStatus.active,
            Student.id.not_in(active_hosteller_ids),
        )
        .order_by(ClassSection.class_name, Student.admission_no)
    )

    rows = db.execute(q).all()
    out = []
    for s, c_name, sec_name in rows:
        out.append({
            "student_id": s.id,
            "admission_no": s.admission_no,
            "full_name": s.user.full_name,
            "gender": s.gender.value if s.gender else "N/A",
            "class_label": f"{c_name}-{sec_name}",
        })
    return out


# --- Evening Attendance (8:00 PM) ---------------------------------------------


def get_evening_attendance_roster(
    db: Session, school_id: int, user: User, hostel_id: int, on_date: date
) -> list[dict]:
    """Prepares 8:00 PM evening attendance roster, pre-populating approved leaves/outings."""
    assert_can_manage_hostel(db, user, hostel_id)

    # Get active admissions for this hostel
    admissions = list(
        db.scalars(
            select(HostelAdmission)
            .where(
                HostelAdmission.school_id == school_id,
                HostelAdmission.hostel_id == hostel_id,
                HostelAdmission.status == "active",
            )
        )
    )

    # Existing attendance records for on_date
    att_records = {
        a.student_id: a
        for a in db.scalars(
            select(HostelAttendance).where(
                HostelAttendance.hostel_id == hostel_id,
                HostelAttendance.attendance_date == on_date,
            )
        )
    }

    # Approved leave or outing requests for this date at 20:00:00
    target_dt = datetime.combine(on_date, time(20, 0, 0), tzinfo=UTC)
    active_leaves = list(
        db.scalars(
            select(HostelLeaveRequest).where(
                HostelLeaveRequest.hostel_id == hostel_id,
                HostelLeaveRequest.status.in_(("approved", "departed")),
                HostelLeaveRequest.start_date <= on_date,
                HostelLeaveRequest.end_date >= on_date,
            )
        )
    )
    leave_map = {l.student_id: l for l in active_leaves}

    out = []
    for adm in admissions:
        stu = adm.student
        existing = att_records.get(stu.id)
        leave_req = leave_map.get(stu.id)

        if existing:
            current_status = existing.status
        elif leave_req:
            current_status = "on_leave" if leave_req.request_type == "leave" else "on_outing"
        else:
            current_status = "present"

        alloc = db.scalar(
            select(BedAllocation).where(
                BedAllocation.admission_id == adm.id,
                BedAllocation.is_active == True,
            )
        )
        bed_number = alloc.bed.bed_number if alloc and alloc.bed else "N/A"
        room_number = alloc.bed.room.room_number if alloc and alloc.bed and alloc.bed.room else "N/A"

        out.append({
            "admission_id": adm.id,
            "student_id": stu.id,
            "admission_no": stu.admission_no,
            "full_name": stu.user.full_name,
            "room_number": room_number,
            "bed_number": bed_number,
            "status": current_status,
            "is_on_approved_leave": leave_req is not None,
            "leave_purpose": leave_req.purpose if leave_req else None,
            "recorded_at": existing.recorded_at.isoformat() if existing else None,
        })
    return out


def mark_evening_attendance(
    db: Session,
    school_id: int,
    user: User,
    hostel_id: int,
    on_date: date,
    entries: list[dict],
) -> int:
    """Submits 8:00 PM evening attendance with audit accountability."""
    assert_can_manage_hostel(db, user, hostel_id)

    recorded_count = 0
    now = datetime.now(UTC)

    for item in entries:
        student_id = item["student_id"]
        status_val = item["status"]  # present, absent, on_leave, on_outing
        remarks = item.get("remarks")

        admission = db.scalar(
            select(HostelAdmission).where(
                HostelAdmission.student_id == student_id,
                HostelAdmission.hostel_id == hostel_id,
                HostelAdmission.status == "active",
            )
        )
        if not admission:
            continue

        existing = db.scalar(
            select(HostelAttendance).where(
                HostelAttendance.hostel_id == hostel_id,
                HostelAttendance.student_id == student_id,
                HostelAttendance.attendance_date == on_date,
            )
        )

        if existing:
            existing.status = status_val
            existing.recorded_at = now
            existing.recorded_by_id = user.id
            existing.remarks = remarks
        else:
            att = HostelAttendance(
                school_id=school_id,
                hostel_id=hostel_id,
                student_id=student_id,
                admission_id=admission.id,
                attendance_date=on_date,
                status=status_val,
                scheduled_time=time(20, 0, 0),
                recorded_at=now,
                recorded_by_id=user.id,
                remarks=remarks,
            )
            db.add(att)
        recorded_count += 1

    db.flush()
    return recorded_count


# --- Leave & Outing Workflow --------------------------------------------------


def submit_leave_or_outing(
    db: Session,
    school_id: int,
    user: User,
    student_id: int,
    request_type: str,
    start_date: date,
    end_date: date,
    expected_return_time: datetime,
    purpose: str,
    out_time: time | None = None,
) -> HostelLeaveRequest:
    """Parent initiates leave or outing request. Students are strictly forbidden."""
    if user.role == UserRole.student:
        raise forbidden("Students cannot submit leave or outing requests. Requests must be submitted by parents.")

    guardian = db.scalar(select(Guardian).where(Guardian.user_id == user.id))
    if not guardian:
        raise forbidden("Only a registered parent/guardian can submit hostel leave requests")

    # Verify link
    link = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.guardian_id == guardian.id,
            StudentGuardian.student_id == student_id,
        )
    )
    if not link:
        raise forbidden("Student is not linked to your parent account")

    active_adm = db.scalar(
        select(HostelAdmission).where(
            HostelAdmission.student_id == student_id,
            HostelAdmission.status == "active",
        )
    )
    if not active_adm:
        raise bad_request("Student is not currently an active hostel resident")

    req = HostelLeaveRequest(
        school_id=school_id,
        student_id=student_id,
        admission_id=active_adm.id,
        hostel_id=active_adm.hostel_id,
        request_type=request_type,
        start_date=start_date,
        end_date=end_date,
        out_time=out_time,
        expected_return_time=expected_return_time,
        purpose=purpose,
        parent_guardian_id=guardian.id,
        status="pending",
    )
    db.add(req)
    db.flush()
    return req


def adjudicate_leave_request(
    db: Session,
    school_id: int,
    user: User,
    request_id: int,
    action: str,  # "approve" or "reject"
    remarks: str | None = None,
    rejection_reason: str | None = None,
) -> HostelLeaveRequest:
    """Warden or Chief Provost approves/rejects leave request."""
    req = db.get(HostelLeaveRequest, request_id)
    if not req or req.school_id != school_id:
        raise not_found("Leave request not found")

    assert_can_manage_hostel(db, user, req.hostel_id)

    if req.status != "pending":
        raise bad_request(f"Cannot adjudicate request already in status '{req.status}'")

    if action == "approve":
        req.status = "approved"
        req.approved_by_id = user.id
        req.approved_at = datetime.now(UTC)
        req.remarks = remarks
    elif action == "reject":
        req.status = "rejected"
        req.approved_by_id = user.id
        req.approved_at = datetime.now(UTC)
        req.rejection_reason = rejection_reason or remarks
    else:
        raise bad_request(f"Invalid adjudication action '{action}'")

    db.flush()
    return req


def record_student_return(
    db: Session,
    school_id: int,
    user: User,
    request_id: int,
) -> HostelLeaveRequest:
    """Warden explicitly records that the student has returned to hostel."""
    req = db.get(HostelLeaveRequest, request_id)
    if not req or req.school_id != school_id:
        raise not_found("Leave request not found")

    assert_can_manage_hostel(db, user, req.hostel_id)

    if req.status not in ("approved", "departed"):
        raise bad_request(f"Cannot record return for request in status '{req.status}'")

    req.status = "returned"
    req.actual_return_time = datetime.now(UTC)
    req.returned_recorded_by_id = user.id

    db.flush()
    return req


def get_leave_requests(
    db: Session,
    school_id: int,
    user: User,
    hostel_id: int | None = None,
    status_filter: str | None = None,
) -> list[dict]:
    """Retrieves leave and outing requests with visual overdue flag calculation."""
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(HostelLeaveRequest).where(HostelLeaveRequest.school_id == school_id)
    if allowed_ids is not None:
        q = q.where(HostelLeaveRequest.hostel_id.in_(allowed_ids))
    if hostel_id is not None:
        assert_can_manage_hostel(db, user, hostel_id)
        q = q.where(HostelLeaveRequest.hostel_id == hostel_id)
    if status_filter:
        q = q.where(HostelLeaveRequest.status == status_filter)

    rows = list(db.scalars(q.order_by(HostelLeaveRequest.created_at.desc())))
    now = datetime.now(UTC)
    out = []

    for r in rows:
        stu = r.student
        is_overdue = (
            r.status in ("approved", "departed")
            and r.expected_return_time < now
            and r.actual_return_time is None
        )
        out.append({
            "id": r.id,
            "student_id": stu.id,
            "admission_no": stu.admission_no,
            "full_name": stu.user.full_name,
            "hostel_id": r.hostel_id,
            "request_type": r.request_type,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "expected_return_time": r.expected_return_time.isoformat(),
            "actual_return_time": r.actual_return_time.isoformat() if r.actual_return_time else None,
            "purpose": r.purpose,
            "status": r.status,
            "is_overdue": is_overdue,
            "parent_name": r.guardian.user.full_name if r.guardian and r.guardian.user else "Parent",
            "remarks": r.remarks,
            "rejection_reason": r.rejection_reason,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
        })
    return out


# --- Mess Menu (School-wide) --------------------------------------------------


def get_mess_menu(db: Session, school_id: int) -> list[dict]:
    """Retrieves the published weekly mess menu across all 7 days."""
    rows = list(
        db.scalars(
            select(HostelMessMenu)
            .where(HostelMessMenu.school_id == school_id)
            .order_by(HostelMessMenu.id)
        )
    )
    return [
        {
            "id": m.id,
            "day_of_week": m.day_of_week.value,
            "breakfast": m.breakfast,
            "lunch": m.lunch,
            "snacks": m.snacks,
            "dinner": m.dinner,
            "is_published": m.is_published,
        }
        for m in rows
    ]


def update_mess_menu(
    db: Session, school_id: int, user: User, menu_data: list[dict]
) -> None:
    """Chief Provost updates and publishes the school-wide weekly mess menu."""
    if not is_chief_provost_or_admin(db, user):
        raise forbidden("Only Chief Provost can manage and publish the mess menu")

    for item in menu_data:
        day = item["day_of_week"]
        menu_row = db.scalar(
            select(HostelMessMenu).where(
                HostelMessMenu.school_id == school_id,
                HostelMessMenu.day_of_week == day,
            )
        )
        if menu_row:
            menu_row.breakfast = item["breakfast"]
            menu_row.lunch = item["lunch"]
            menu_row.snacks = item["snacks"]
            menu_row.dinner = item["dinner"]
            menu_row.is_published = item.get("is_published", True)
            menu_row.updated_by_id = user.id
        else:
            db.add(
                HostelMessMenu(
                    school_id=school_id,
                    day_of_week=day,
                    breakfast=item["breakfast"],
                    lunch=item["lunch"],
                    snacks=item["snacks"],
                    dinner=item["dinner"],
                    is_published=item.get("is_published", True),
                    updated_by_id=user.id,
                )
            )
    db.flush()


# --- Fee Engine Integration (Idempotent, Dynamic, No Proration) ----------------


def charges_for_month(
    db: Session, school_id: int, year: int, month: int
) -> dict[int, Decimal]:
    """Dynamically resolves {enrolment_id: amount} for hostel billing for the specified month.
    
    Integrated into `OPT_IN_SOURCES["HOSTEL"]`.
    - Dynamic amount sourced from FeePlanItem for FeeHead 'HOSTEL'.
    - Idempotent and clean.
    - Sourced per existing fee rules without fractional day proration.
    """
    first_of_month = date(year, month, 1)
    if month == 12:
        last_of_month = date(year, 12, 31)
    else:
        from calendar import monthrange
        last_of_month = date(year, month, monthrange(year, month)[1])

    # Find admissions active during this month
    admissions = list(
        db.scalars(
            select(HostelAdmission).where(
                HostelAdmission.school_id == school_id,
                HostelAdmission.admission_date <= last_of_month,
                or_(
                    HostelAdmission.exit_date.is_(None),
                    HostelAdmission.exit_date >= first_of_month,
                ),
                HostelAdmission.status.in_(("active", "vacated")),
            )
        )
    )

    if not admissions:
        return {}

    # Look up the HOSTEL fee head
    hostel_head = db.scalar(
        select(FeeHead).where(FeeHead.school_id == school_id, FeeHead.code == "HOSTEL")
    )
    if not hostel_head:
        return {}

    out: dict[int, Decimal] = {}
    for adm in admissions:
        enrolment = get_student_current_enrolment(db, adm.student_id)
        if not enrolment:
            continue

        # Look up configured fee amount from student's plan or class plan
        student_plan_id = db.scalar(
            select(StudentFeePlan.fee_plan_id).where(StudentFeePlan.enrolment_id == enrolment.id)
        )
        if student_plan_id:
            plan = db.get(FeePlan, student_plan_id)
        else:
            sec = db.get(ClassSection, enrolment.class_section_id)
            cls_name = sec.class_name if sec else None
            plan = db.scalar(
                select(FeePlan).where(
                    FeePlan.school_id == school_id,
                    FeePlan.academic_year_id == enrolment.academic_year_id,
                    FeePlan.class_name == cls_name,
                )
            )

        amount = Decimal("0.00")
        if plan:
            item = db.scalar(
                select(FeePlanItem).where(
                    FeePlanItem.fee_plan_id == plan.id,
                    FeePlanItem.fee_head_id == hostel_head.id,
                )
            )
            if item:
                amount = item.amount

        # If amount configured is > 0, attach charge for this enrolment
        if amount > Decimal("0.00"):
            out[enrolment.id] = amount

    return out


def get_notices(
    db: Session, school_id: int, user: User, hostel_id: int | None = None
) -> list[dict]:
    """Retrieves active notices for a given hostel or school-wide."""
    q = select(HostelNotice).where(
        HostelNotice.school_id == school_id,
        HostelNotice.is_active == True,
    )
    if hostel_id is not None:
        q = q.where(or_(HostelNotice.hostel_id.is_(None), HostelNotice.hostel_id == hostel_id))
    rows = list(db.scalars(q.order_by(HostelNotice.posted_at.desc())))
    return [
        {
            "id": n.id,
            "hostel_id": n.hostel_id,
            "hostel_name": n.hostel.name if n.hostel else "All Hostels",
            "title": n.title,
            "content": n.content,
            "priority": n.priority,
            "posted_at": n.posted_at.isoformat(),
            "posted_by": n.posted_by.full_name if n.posted_by else "Hostel Office",
            "posted_by_name": n.posted_by.full_name if n.posted_by else "Hostel Office",
        }
        for n in rows
    ]

