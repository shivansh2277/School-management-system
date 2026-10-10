"""Admin and Warden Hostel & Mess management APIs.

Strictly enforces authorization:
- Route dependencies: require_permission
- Service-level scoping: assert_can_manage_hostel via UserRoleAssignment
- Warden access is strictly isolated to their assigned hostel.
- Chief Provost possesses cross-hostel school-wide access.
"""

from datetime import UTC, date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import (
    Gender,
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
    User,
    UserRole,
)
from app.services import hostel as svc
from app.services.hostel_scoping import (
    assert_can_manage_hostel,
    get_warden_assigned_hostel_id,
    is_chief_provost,
    readable_hostel_ids_for,
)
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin/hostel", tags=["admin-hostel"])

structure_reader = require_permission("hostel.structure.read")
structure_manager = require_permission("hostel.structure.manage")
resident_reader = require_permission("hostel.resident.read")
resident_transfer = require_permission("hostel.resident.allocate")
admission_manager = require_permission("hostel.resident.admit")
attendance_reader = require_permission("hostel.attendance.read")
attendance_marker = require_permission("hostel.attendance.mark")
leave_reader = require_permission("hostel.leave.read")
leave_adjudicator = require_permission("hostel.leave.approve")
mess_reader = require_permission("hostel.mess.read")
mess_manager = require_permission("hostel.mess.manage")
incident_reader = require_permission("hostel.incident.read")
incident_manager = require_permission("hostel.incident.manage")
notice_reader = require_permission("hostel.notice.read")
notice_manager = require_permission("hostel.notice.manage")
provost_only = require_permission("hostel.resident.exit", "hostel.structure.manage")


def assert_not_warden(db: Session, user: User) -> None:
    """Explicitly denies wardens from admission endpoints."""
    if get_warden_assigned_hostel_id(db, user) is not None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Wardens cannot access or manage hostel admissions",
        )


# --- Schemas ---


class HostelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)
    gender: Gender
    description: str | None = None


class FloorCreate(BaseModel):
    floor_number: int
    floor_name: str = Field(min_length=1, max_length=60)


class RoomCreate(BaseModel):
    floor_id: int
    room_number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(default=2, ge=1)
    room_type: str = "standard"


class BedCreate(BaseModel):
    bed_number: str = Field(min_length=1, max_length=20)


class AdmissionInput(BaseModel):
    student_id: int
    hostel_id: int
    bed_id: int
    admission_date: date
    remarks: str | None = None


class DirectAdmissionInput(BaseModel):
    student_id: int
    bed_id: int
    admission_date: date
    remarks: str | None = None


class TransferInput(BaseModel):
    new_bed_id: int
    reason: str = Field(min_length=1)


class ExitInput(BaseModel):
    exit_date: date
    exit_reason: str = Field(min_length=1)


class AttendanceEntry(BaseModel):
    student_id: int
    status: str  # present, absent, on_leave, on_outing
    remarks: str | None = None


class AttendanceBatchSubmit(BaseModel):
    attendance_date: date
    entries: list[AttendanceEntry]


class LeaveAdjudicateInput(BaseModel):
    action: str  # approve, reject
    remarks: str | None = None
    rejection_reason: str | None = None


class MessDayInput(BaseModel):
    day_of_week: str
    breakfast: str
    lunch: str
    snacks: str
    dinner: str
    is_published: bool = True


class MessMenuUpdate(BaseModel):
    menu: list[MessDayInput]


class ComplaintCreate(BaseModel):
    hostel_id: int
    student_id: int | None = None
    room_id: int | None = None
    category: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class ComplaintResolve(BaseModel):
    status: str = "resolved"
    resolution_remarks: str = Field(min_length=1)


class IncidentCreate(BaseModel):
    hostel_id: int
    student_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    severity: str = "medium"
    incident_date: date
    action_taken: str | None = None


class NoticeCreate(BaseModel):
    hostel_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    priority: str = "normal"


# --- Endpoints ---


@router.get("/overview", dependencies=[Depends(structure_reader)])
def get_hostel_overview(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    return svc.get_overview(db, user.school_id, user)


@router.get("/list", dependencies=[Depends(structure_reader)])
def list_hostels(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(Hostel).where(Hostel.school_id == user.school_id)
    if allowed_ids is not None:
        q = q.where(Hostel.id.in_(allowed_ids))
    hostels = list(db.scalars(q.order_by(Hostel.name)))
    assigned_hostel_id = get_warden_assigned_hostel_id(db, user)

    return [
        {
            "id": h.id,
            "name": h.name,
            "code": h.code,
            "gender": h.gender.value,
            "status": h.status,
            "description": h.description,
            "is_assigned_to_caller": (h.id == assigned_hostel_id) if assigned_hostel_id else True,
        }
        for h in hostels
    ]


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(structure_manager)])
def create_hostel(
    body: HostelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not is_chief_provost(db, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Chief Provost can create hostels")

    existing = db.scalar(
        select(Hostel).where(Hostel.school_id == user.school_id, Hostel.code == body.code)
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Hostel code '{body.code}' already exists")

    h = Hostel(
        school_id=user.school_id,
        name=body.name,
        code=body.code,
        gender=body.gender,
        description=body.description,
        status="active",
    )
    db.add(h)
    db.commit()
    return {"id": h.id, "name": h.name, "code": h.code, "gender": h.gender.value}


@router.get("/{hostel_id}/structure", dependencies=[Depends(structure_reader)])
def get_hostel_structure(
    hostel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assert_can_manage_hostel(db, user, hostel_id)
    res = svc.get_structure(db, user.school_id, user, hostel_id=hostel_id)
    if not res:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hostel not found")
    return res[0]


@router.get("/structure", dependencies=[Depends(structure_reader)])
def get_all_structures(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    return svc.get_structure(db, user.school_id, user)


@router.post("/{hostel_id}/floors", status_code=status.HTTP_201_CREATED, dependencies=[Depends(structure_manager)])
def create_floor(
    hostel_id: int,
    body: FloorCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assert_can_manage_hostel(db, user, hostel_id)
    f = HostelFloor(
        school_id=user.school_id,
        hostel_id=hostel_id,
        floor_number=body.floor_number,
        floor_name=body.floor_name,
        status="active",
    )
    db.add(f)
    db.commit()
    return {"id": f.id, "floor_number": f.floor_number, "floor_name": f.floor_name}


@router.post("/{hostel_id}/rooms", status_code=status.HTTP_201_CREATED, dependencies=[Depends(structure_manager)])
def create_room(
    hostel_id: int,
    body: RoomCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assert_can_manage_hostel(db, user, hostel_id)
    r = HostelRoom(
        school_id=user.school_id,
        hostel_id=hostel_id,
        floor_id=body.floor_id,
        room_number=body.room_number,
        capacity=body.capacity,
        room_type=body.room_type,
        status="available",
    )
    db.add(r)
    db.commit()
    return {"id": r.id, "room_number": r.room_number, "capacity": r.capacity}


@router.post("/rooms/{room_id}/beds", status_code=status.HTTP_201_CREATED, dependencies=[Depends(structure_manager)])
def create_bed(
    room_id: int,
    body: BedCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    room = db.get(HostelRoom, room_id)
    if not room or room.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    assert_can_manage_hostel(db, user, room.hostel_id)

    b = HostelBed(
        school_id=user.school_id,
        room_id=room.id,
        bed_number=body.bed_number,
        status="available",
    )
    db.add(b)
    db.commit()
    return {"id": b.id, "bed_number": b.bed_number, "status": b.status}


@router.get("/residents", dependencies=[Depends(resident_reader)])
def list_residents(
    hostel_id: int | None = None,
    status: str = "active",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.get_residents(db, user.school_id, user, hostel_id=hostel_id, status_filter=status)


@router.get("/admissions/pending-applications", dependencies=[Depends(admission_manager)])
@router.get("/pending-applications", dependencies=[Depends(admission_manager)])
def pending_applications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    assert_not_warden(db, user)
    return svc.get_pending_applications(db, user.school_id, user)


@router.get("/admissions/eligible-students", dependencies=[Depends(admission_manager)])
@router.get("/admissions/eligible-day-scholars", dependencies=[Depends(admission_manager)])
@router.get("/eligible-day-scholars", dependencies=[Depends(admission_manager)])
def eligible_day_scholars(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    assert_not_warden(db, user)
    return svc.get_eligible_day_scholars(db, user.school_id, user)


@router.post("/admissions", status_code=status.HTTP_201_CREATED, dependencies=[Depends(admission_manager)])
def admit_student_to_hostel(
    body: AdmissionInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assert_not_warden(db, user)
    adm = svc.admit_student(
        db,
        school_id=user.school_id,
        user=user,
        student_id=body.student_id,
        hostel_id=body.hostel_id,
        bed_id=body.bed_id,
        admission_date=body.admission_date,
        remarks=body.remarks,
    )
    db.commit()
    return {"id": adm.id, "status": adm.status, "admission_date": adm.admission_date.isoformat()}


@router.get("/{hostel_id}/available-beds", dependencies=[Depends(structure_reader)])
def list_available_beds(
    hostel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    assert_can_manage_hostel(db, user, hostel_id)
    return svc.get_available_beds(db, user.school_id, hostel_id)


@router.post("/{hostel_id}/admissions/direct", status_code=status.HTTP_201_CREATED, dependencies=[Depends(admission_manager)])
def admit_student_direct(
    hostel_id: int,
    body: DirectAdmissionInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assert_not_warden(db, user)
    adm = svc.admit_student(
        db,
        school_id=user.school_id,
        user=user,
        student_id=body.student_id,
        hostel_id=hostel_id,
        bed_id=body.bed_id,
        admission_date=body.admission_date,
        remarks=body.remarks,
    )
    db.commit()
    return {"id": adm.id, "status": adm.status, "admission_date": adm.admission_date.isoformat()}


@router.post("/admissions/{admission_id}/transfer", dependencies=[Depends(resident_transfer)])
def transfer_resident_bed(
    admission_id: int,
    body: TransferInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    alloc = svc.transfer_bed(
        db,
        school_id=user.school_id,
        user=user,
        admission_id=admission_id,
        new_bed_id=body.new_bed_id,
        reason=body.reason,
    )
    db.commit()
    return {
        "allocation_id": alloc.id,
        "bed_id": alloc.bed_id,
        "bed_number": alloc.bed.bed_number if alloc.bed else None,
        "is_active": alloc.is_active,
    }


@router.post("/admissions/{admission_id}/exit", dependencies=[Depends(provost_only)])
def exit_resident_from_hostel(
    admission_id: int,
    body: ExitInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    adm = svc.exit_student(
        db,
        school_id=user.school_id,
        user=user,
        admission_id=admission_id,
        exit_date=body.exit_date,
        exit_reason=body.exit_reason,
    )
    db.commit()
    return {"id": adm.id, "status": adm.status, "exit_date": adm.exit_date.isoformat()}


@router.get("/admissions/{admission_id}/history", dependencies=[Depends(resident_reader)])
def get_admission_history(
    admission_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.get_allocation_history(db, user.school_id, admission_id)


# --- Attendance ---


@router.get("/{hostel_id}/attendance", dependencies=[Depends(attendance_reader)])
def get_evening_attendance(
    hostel_id: int,
    on_date: date = Query(default_factory=date.today),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.get_evening_attendance_roster(db, user.school_id, user, hostel_id, on_date)


@router.post("/{hostel_id}/attendance", dependencies=[Depends(attendance_marker)])
def submit_evening_attendance(
    hostel_id: int,
    body: AttendanceBatchSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.mark_evening_attendance(
        db,
        school_id=user.school_id,
        user=user,
        hostel_id=hostel_id,
        on_date=body.attendance_date,
        entries=[e.model_dump() for e in body.entries],
    )
    db.commit()
    return {"marked_count": count, "attendance_date": body.attendance_date.isoformat()}


# --- Leaves & Outings ---


@router.get("/leaves", dependencies=[Depends(leave_reader)])
def list_leave_requests(
    hostel_id: int | None = None,
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.get_leave_requests(db, user.school_id, user, hostel_id=hostel_id, status_filter=status)


@router.post("/leaves/{request_id}/adjudicate", dependencies=[Depends(leave_adjudicator)])
def adjudicate_leave(
    request_id: int,
    body: LeaveAdjudicateInput,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    req = svc.adjudicate_leave_request(
        db,
        school_id=user.school_id,
        user=user,
        request_id=request_id,
        action=body.action,
        remarks=body.remarks,
        rejection_reason=body.rejection_reason,
    )
    db.commit()
    return {"id": req.id, "status": req.status}


@router.post("/leaves/{request_id}/return", dependencies=[Depends(leave_adjudicator)])
def record_return(
    request_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    req = svc.record_student_return(db, user.school_id, user, request_id)
    db.commit()
    return {"id": req.id, "status": req.status, "actual_return_time": req.actual_return_time.isoformat()}


# --- Mess Menu ---


@router.get("/menu", dependencies=[Depends(mess_reader)])
def get_mess_menu(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    return svc.get_mess_menu(db, user.school_id)


@router.put("/menu", dependencies=[Depends(mess_manager)])
def update_mess_menu(
    body: MessMenuUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    svc.update_mess_menu(
        db,
        school_id=user.school_id,
        user=user,
        menu_data=[m.model_dump() for m in body.menu],
    )
    db.commit()
    return {"status": "ok", "message": "Mess menu updated and published successfully"}


# --- Complaints & Incidents ---


@router.get("/complaints", dependencies=[Depends(incident_reader)])
def list_complaints(
    hostel_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(HostelComplaint).where(HostelComplaint.school_id == user.school_id)
    if allowed_ids is not None:
        q = q.where(HostelComplaint.hostel_id.in_(allowed_ids))
    if hostel_id is not None:
        assert_can_manage_hostel(db, user, hostel_id)
        q = q.where(HostelComplaint.hostel_id == hostel_id)

    rows = list(db.scalars(q.order_by(HostelComplaint.created_at.desc())))
    out = []
    for c in rows:
        out.append({
            "id": c.id,
            "hostel_id": c.hostel_id,
            "hostel_name": c.hostel.name if c.hostel else "N/A",
            "student_name": c.student.user.full_name if c.student and c.student.user else "N/A",
            "room_number": c.room.room_number if c.room else "N/A",
            "category": c.category,
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "resolution_remarks": c.resolution_remarks,
            "created_at": c.created_at.isoformat(),
        })
    return out


@router.post("/complaints", status_code=status.HTTP_201_CREATED, dependencies=[Depends(incident_reader)])
def file_complaint(
    body: ComplaintCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    c = HostelComplaint(
        school_id=user.school_id,
        hostel_id=body.hostel_id,
        student_id=body.student_id,
        room_id=body.room_id,
        category=body.category,
        title=body.title,
        description=body.description,
        status="pending",
    )
    db.add(c)
    db.commit()
    return {"id": c.id, "title": c.title, "status": c.status}


@router.patch("/complaints/{complaint_id}", dependencies=[Depends(incident_manager)])
def resolve_complaint(
    complaint_id: int,
    body: ComplaintResolve,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    c = db.get(HostelComplaint, complaint_id)
    if not c or c.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    assert_can_manage_hostel(db, user, c.hostel_id)

    c.status = body.status
    c.resolution_remarks = body.resolution_remarks
    c.resolved_by_id = user.id
    c.resolved_at = datetime.now(UTC)
    db.commit()
    return {"id": c.id, "status": c.status}


@router.get("/incidents", dependencies=[Depends(incident_reader)])
def list_incidents(
    hostel_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(HostelIncident).where(HostelIncident.school_id == user.school_id)
    if allowed_ids is not None:
        q = q.where(HostelIncident.hostel_id.in_(allowed_ids))
    if hostel_id is not None:
        assert_can_manage_hostel(db, user, hostel_id)
        q = q.where(HostelIncident.hostel_id == hostel_id)

    rows = list(db.scalars(q.order_by(HostelIncident.incident_date.desc())))
    return [
        {
            "id": i.id,
            "hostel_id": i.hostel_id,
            "hostel_name": i.hostel.name if i.hostel else "N/A",
            "student_name": i.student.user.full_name if i.student and i.student.user else "N/A",
            "title": i.title,
            "description": i.description,
            "severity": i.severity,
            "incident_date": i.incident_date.isoformat(),
            "action_taken": i.action_taken,
            "status": i.status,
        }
        for i in rows
    ]


@router.post("/incidents", status_code=status.HTTP_201_CREATED, dependencies=[Depends(incident_manager)])
def record_incident(
    body: IncidentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    assert_can_manage_hostel(db, user, body.hostel_id)
    inc = HostelIncident(
        school_id=user.school_id,
        hostel_id=body.hostel_id,
        student_id=body.student_id,
        title=body.title,
        description=body.description,
        severity=body.severity,
        incident_date=body.incident_date,
        action_taken=body.action_taken,
        reported_by_id=user.id,
        status="open",
    )
    db.add(inc)
    db.commit()
    return {"id": inc.id, "title": inc.title, "severity": inc.severity}


# --- Notices ---


@router.get("/notices", dependencies=[Depends(notice_reader)])
def list_notices(
    hostel_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    allowed_ids = readable_hostel_ids_for(db, user)
    q = select(HostelNotice).where(HostelNotice.school_id == user.school_id, HostelNotice.is_active == True)
    if allowed_ids is not None:
        q = q.where(or_(HostelNotice.hostel_id.is_(None), HostelNotice.hostel_id.in_(allowed_ids)))
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
            "posted_by_name": n.posted_by.full_name if n.posted_by else "Staff",
        }
        for n in rows
    ]


@router.post("/notices", status_code=status.HTTP_201_CREATED, dependencies=[Depends(notice_manager)])
def broadcast_notice(
    body: NoticeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if body.hostel_id is not None:
        assert_can_manage_hostel(db, user, body.hostel_id)
    elif not is_chief_provost(db, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Chief Provost can broadcast school-wide hostel notices")

    notice = HostelNotice(
        school_id=user.school_id,
        hostel_id=body.hostel_id,
        title=body.title,
        content=body.content,
        priority=body.priority,
        posted_by_id=user.id,
        posted_at=datetime.now(UTC),
        is_active=True,
    )
    db.add(notice)
    db.commit()
    return {"id": notice.id, "title": notice.title, "priority": notice.priority}
