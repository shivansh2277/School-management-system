"""Student API endpoints for Hostel and Mess management (Strictly Read-Only)."""

from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    BedAllocation,
    HostelAdmission,
    HostelAttendance,
    HostelBed,
    HostelLeaveRequest,
    Student,
    User,
)
from app.services import hostel as hostel_svc, scoping
from app.services.rbac import require_permission

router = APIRouter(prefix="/student", tags=["student-hostel"])
student_read = require_permission("hostel.structure.read")


@router.get("/hostel")
def get_my_hostel_details(
    user: User = Depends(student_read),
    db: Session = Depends(get_db),
) -> dict:
    """Read-only details of the student's assigned hostel, room, bed, and roommates."""
    student = scoping.student_for(db, user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    admission = db.scalar(
        select(HostelAdmission).where(
            HostelAdmission.student_id == student.id,
            HostelAdmission.status == "active",
        )
    )

    if not admission:
        return {
            "is_hosteller": False,
            "student_name": user.full_name,
            "admission": None,
        }

    hostel = admission.hostel
    alloc = db.scalar(
        select(BedAllocation).where(
            BedAllocation.admission_id == admission.id,
            BedAllocation.is_active == True,
        )
    )

    bed = alloc.bed if alloc else None
    room = bed.room if bed else None
    floor = room.floor if room else None

    # Roommates in the same room
    roommates = []
    if room:
        room_allocs = list(
            db.scalars(
                select(BedAllocation)
                .join(HostelBed, HostelBed.id == BedAllocation.bed_id)
                .where(
                    HostelBed.room_id == room.id,
                    BedAllocation.is_active == True,
                    BedAllocation.id != (alloc.id if alloc else -1),
                )
            )
        )
        for ra in room_allocs:
            if ra.admission and ra.admission.student:
                roommates.append({
                    "student_name": ra.admission.student.user.full_name,
                    "bed_number": ra.bed.bed_number if ra.bed else "N/A",
                })

    # Recent evening attendance records (last 15)
    att_records = list(
        db.scalars(
            select(HostelAttendance)
            .where(
                HostelAttendance.student_id == student.id,
                HostelAttendance.hostel_id == hostel.id,
            )
            .order_by(HostelAttendance.attendance_date.desc())
            .limit(15)
        )
    )

    # Published mess menu
    menu_rows = hostel_svc.get_mess_menu(db, user.school_id)

    # Active notices for this hostel or school-wide
    notices = hostel_svc.get_notices(db, user.school_id, user, hostel_id=hostel.id)

    return {
        "is_hosteller": True,
        "student_name": user.full_name,
        "admission_id": admission.id,
        "admission_date": admission.admission_date.isoformat(),
        "hostel": {
            "id": hostel.id,
            "name": hostel.name,
            "code": hostel.code,
            "gender": hostel.gender.value,
            "category": hostel.gender.value,
        },
        "room": {
            "id": room.id if room else None,
            "room_number": room.room_number if room else "N/A",
            "capacity": room.capacity if room else 0,
            "floor_number": floor.floor_number if floor else 0,
        },
        "bed": {
            "id": bed.id if bed else None,
            "bed_number": bed.bed_number if bed else "N/A",
        },
        "roommates": roommates,
        "recent_attendance": [
            {
                "id": a.id,
                "date": a.attendance_date.isoformat(),
                "status": a.status,
                "recorded_at": a.recorded_at.isoformat(),
                "remarks": a.remarks,
            }
            for a in att_records
        ],
        "mess_menu": menu_rows,
        "notices": notices[:5],
    }


@router.get("/hostel/leaves")
def get_my_leave_history(
    user: User = Depends(student_read),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Read-only view of leave and outing requests submitted by parents."""
    student = scoping.student_for(db, user)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    reqs = list(
        db.scalars(
            select(HostelLeaveRequest)
            .where(HostelLeaveRequest.student_id == student.id)
            .order_by(HostelLeaveRequest.created_at.desc())
        )
    )
    now = datetime.now(UTC)
    out = []
    for r in reqs:
        is_overdue = (
            r.status in ("approved", "departed")
            and r.expected_return_time < now
            and r.actual_return_time is None
        )
        out.append({
            "id": r.id,
            "request_type": r.request_type,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "expected_return_time": r.expected_return_time.isoformat(),
            "actual_return_time": r.actual_return_time.isoformat() if r.actual_return_time else None,
            "purpose": r.purpose,
            "status": r.status,
            "is_overdue": is_overdue,
            "remarks": r.remarks,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return out


@router.get("/hostel/mess-menu")
def get_student_mess_menu(
    user: User = Depends(student_read),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Returns the published weekly mess menu."""
    return hostel_svc.get_mess_menu(db, user.school_id)
