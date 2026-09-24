"""API endpoints for Receptionist Operations: Found & Lost, Passes, Meetings, Directory, and Fees."""
import os
import uuid
from datetime import date as Date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models import Employee, EmployeeStatus, Enrolment, EnrolmentStatus, Student, User
from app.schemas.reception import (
    DirectoryContactIn,
    DirectoryContactOut,
    FoundItemCollect,
    FoundItemCreate,
    FoundItemOut,
    PrincipalMeetingCreate,
    PrincipalMeetingOut,
    PrincipalMeetingRespond,
    ReceptionFeeCollectIn,
    StudentAuthorizedPersonIn,
    StudentAuthorizedPersonOut,
    StudentPassCreate,
    StudentPassOut,
    StudentPassStatusUpdate,
    TeacherMeetingCreate,
    TeacherMeetingOut,
    TeacherMeetingRespond,
)
from app.services import rbac, scoping
from app.services import reception as svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin/reception", tags=["admin-reception"])

# Permissions dependencies
can_read_found = require_permission("reception.found_items.read", school_wide=True)
can_write_found = require_permission("reception.found_items.write", school_wide=True)
can_collect_found = require_permission("reception.found_items.collect", school_wide=True)
can_upload_found = require_permission("reception.found_items.write", "reception.found_items.collect")

can_read_passes = require_permission("reception.passes.read", school_wide=True)
can_write_passes = require_permission("reception.passes.write", school_wide=True)
can_manage_roster = require_permission("reception.authorized_persons.manage", school_wide=True)

can_read_meetings = require_permission("reception.meetings.read", school_wide=True)
can_write_meetings = require_permission("reception.meetings.write", school_wide=True)
can_respond_principal = require_permission("reception.meetings.respond_principal", school_wide=True)
can_respond_teacher = require_permission("reception.meetings.respond_teacher")
can_read_teacher_meetings = require_permission("reception.meetings.read", "reception.meetings.respond_teacher")

can_read_directory = require_permission("reception.directory.read", school_wide=True)
can_write_directory = require_permission("reception.directory.write", school_wide=True)

can_collect_fees = require_permission("fees.payment.collect", school_wide=True)


# --- Helper Endpoints: Student Search & Teacher List -------------------------


@router.get("/students/search")
def search_students(
    q: str = Query(..., min_length=1),
    user: User = Depends(can_read_passes),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    clean_q = q.strip()
    pattern = f"%{clean_q}%"
    students = (
        db.scalars(
            select(Student)
            .join(User, User.id == Student.user_id)
            .where(
                Student.school_id == user.school_id,
                or_(
                    Student.admission_no.ilike(pattern),
                    User.full_name.ilike(pattern),
                ),
            )
            .limit(20)
        )
        .all()
    )
    results = []
    for s in students:
        enrolment = (
            db.scalars(
                select(Enrolment)
                .where(Enrolment.student_id == s.id, Enrolment.status == EnrolmentStatus.active)
                .order_by(Enrolment.academic_year_id.desc())
            )
            .first()
        )
        class_label = enrolment.class_section.label if enrolment and enrolment.class_section else "—"
        results.append({
            "id": s.id,
            "admission_no": s.admission_no,
            "name": s.user.full_name if s.user else "—",
            "class_name": class_label,
            "phone": s.user.phone if s.user else None,
        })
    return results


@router.get("/teachers")
def list_teachers(
    user: User = Depends(can_read_meetings),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    teachers = (
        db.scalars(
            select(Employee)
            .where(
                Employee.school_id == user.school_id,
                Employee.status == EmployeeStatus.active,
            )
            .order_by(Employee.id)
        )
        .all()
    )
    return [
        {
            "id": t.id,
            "staff_id": t.employee_code,
            "name": t.user.full_name if t.user else "Teacher",
            "department": t.department.name if t.department else "Academic",
        }
        for t in teachers
    ]


# --- Found & Lost -----------------------------------------------------------


@router.get("/found-items", response_model=list[FoundItemOut])
def list_found_items(
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    user: User = Depends(can_read_found),
    db: Session = Depends(get_db),
) -> list[FoundItemOut]:
    return svc.list_found_items(
        db, user.school_id, status_filter=status, category_filter=category, search=search
    )


@router.get("/found-items/{item_id}", response_model=FoundItemOut)
def get_found_item(
    item_id: int,
    user: User = Depends(can_read_found),
    db: Session = Depends(get_db),
) -> FoundItemOut:
    return svc.get_found_item(db, user.school_id, item_id)


@router.post("/found-items", response_model=FoundItemOut, status_code=status.HTTP_201_CREATED)
def create_found_item(
    payload: FoundItemCreate,
    user: User = Depends(can_write_found),
    db: Session = Depends(get_db),
) -> FoundItemOut:
    return svc.create_found_item(db, user.school_id, user, payload.model_dump())


@router.post("/found-items/{item_id}/broadcast", response_model=FoundItemOut)
def broadcast_found_item(
    item_id: int,
    user: User = Depends(can_write_found),
    db: Session = Depends(get_db),
) -> FoundItemOut:
    return svc.broadcast_found_item(db, user.school_id, user, item_id)


@router.post("/found-items/{item_id}/collect", response_model=FoundItemOut)
def collect_found_item(
    item_id: int,
    payload: FoundItemCollect,
    user: User = Depends(can_collect_found),
    db: Session = Depends(get_db),
) -> FoundItemOut:
    return svc.collect_found_item(db, user.school_id, user, item_id, payload.model_dump())


ALLOWED_IMAGE_MIMES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


@router.post("/upload")
def upload_reception_image(
    file: UploadFile = File(...),
    user: User = Depends(can_upload_found),
) -> dict[str, Any]:
    content_type = (file.content_type or "").lower()
    ext = ALLOWED_IMAGE_MIMES.get(content_type)
    if not ext:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            ext = ".jpg"
        elif suffix == ".png":
            ext = ".png"
        elif suffix == ".webp":
            ext = ".webp"
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Only image files (.jpg, .jpeg, .png, .webp) are accepted",
            )

    data = file.file.read()
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Image file exceeds maximum allowed size of 5MB",
        )

    target_dir = Path(settings.STORAGE_LOCAL_PATH) / str(user.school_id) / "reception"
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = target_dir / filename
    file_path.write_bytes(data)

    rel_url = f"/documents/{user.school_id}/reception/{filename}"
    return {
        "url": rel_url,
        "filename": file.filename or filename,
        "size": len(data),
        "content_type": content_type or "image/jpeg",
    }


# --- Student Passes & Authorized Persons -------------------------------------


@router.get("/passes", response_model=list[StudentPassOut])
def list_student_passes(
    pass_date: Date | None = None,
    student_id: int | None = None,
    search: str | None = None,
    user: User = Depends(can_read_passes),
    db: Session = Depends(get_db),
) -> list[StudentPassOut]:
    return svc.list_student_passes(
        db, user.school_id, pass_date=pass_date, student_id=student_id, search=search
    )


@router.get("/passes/{pass_id}", response_model=StudentPassOut)
def get_student_pass(
    pass_id: int,
    user: User = Depends(can_read_passes),
    db: Session = Depends(get_db),
) -> StudentPassOut:
    return svc.get_student_pass(db, user.school_id, pass_id)


@router.post("/passes", response_model=StudentPassOut, status_code=status.HTTP_201_CREATED)
def create_student_pass(
    payload: StudentPassCreate,
    user: User = Depends(can_write_passes),
    db: Session = Depends(get_db),
) -> StudentPassOut:
    return svc.create_student_pass(db, user.school_id, user, payload.model_dump())


@router.patch("/passes/{pass_id}/status", response_model=StudentPassOut)
def update_student_pass_status(
    pass_id: int,
    payload: StudentPassStatusUpdate,
    user: User = Depends(can_write_passes),
    db: Session = Depends(get_db),
) -> StudentPassOut:
    return svc.update_student_pass_status(
        db, user.school_id, pass_id, payload.status, payload.remarks
    )


@router.get("/students/{student_id}/authorized-persons", response_model=list[StudentAuthorizedPersonOut])
def list_student_authorized_persons(
    student_id: int,
    user: User = Depends(can_read_passes),
    db: Session = Depends(get_db),
) -> list[StudentAuthorizedPersonOut]:
    return svc.list_authorized_persons(db, user.school_id, student_id)


@router.post(
    "/students/{student_id}/authorized-persons",
    response_model=StudentAuthorizedPersonOut,
    status_code=status.HTTP_201_CREATED,
)
def add_authorized_person(
    student_id: int,
    payload: StudentAuthorizedPersonIn,
    user: User = Depends(can_manage_roster),
    db: Session = Depends(get_db),
) -> StudentAuthorizedPersonOut:
    return svc.add_authorized_person(db, user.school_id, student_id, payload.model_dump())


@router.put("/authorized-persons/{person_id}", response_model=StudentAuthorizedPersonOut)
def update_authorized_person(
    person_id: int,
    payload: StudentAuthorizedPersonIn,
    user: User = Depends(can_manage_roster),
    db: Session = Depends(get_db),
) -> StudentAuthorizedPersonOut:
    return svc.update_authorized_person(db, user.school_id, person_id, payload.model_dump())


@router.delete("/authorized-persons/{person_id}")
def delete_authorized_person(
    person_id: int,
    user: User = Depends(can_manage_roster),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return svc.delete_authorized_person(db, user.school_id, person_id)


# --- Principal Meetings ------------------------------------------------------


@router.get("/meetings/principal", response_model=list[PrincipalMeetingOut])
def list_principal_meetings(
    meeting_date: Date | None = None,
    status: str | None = None,
    search: str | None = None,
    user: User = Depends(can_read_meetings),
    db: Session = Depends(get_db),
) -> list[PrincipalMeetingOut]:
    return svc.list_principal_meetings(
        db, user.school_id, meeting_date=meeting_date, status_filter=status, search=search
    )


@router.get("/meetings/principal/{meeting_id}", response_model=PrincipalMeetingOut)
def get_principal_meeting(
    meeting_id: int,
    user: User = Depends(can_read_meetings),
    db: Session = Depends(get_db),
) -> PrincipalMeetingOut:
    return svc.get_principal_meeting(db, user.school_id, meeting_id)


@router.post("/meetings/principal", response_model=PrincipalMeetingOut, status_code=status.HTTP_201_CREATED)
def create_principal_meeting(
    payload: PrincipalMeetingCreate,
    user: User = Depends(can_write_meetings),
    db: Session = Depends(get_db),
) -> PrincipalMeetingOut:
    return svc.create_principal_meeting(db, user.school_id, user, payload.model_dump())


@router.post("/meetings/principal/{meeting_id}/respond", response_model=PrincipalMeetingOut)
def respond_principal_meeting(
    meeting_id: int,
    payload: PrincipalMeetingRespond,
    user: User = Depends(can_respond_principal),
    db: Session = Depends(get_db),
) -> PrincipalMeetingOut:
    return svc.respond_principal_meeting(db, user.school_id, user, meeting_id, payload.model_dump())


# --- Teacher Meetings --------------------------------------------------------


@router.get("/meetings/teacher", response_model=list[TeacherMeetingOut])
def list_teacher_meetings(
    teacher_id: int | None = None,
    meeting_date: Date | None = None,
    status: str | None = None,
    search: str | None = None,
    user: User = Depends(can_read_teacher_meetings),
    db: Session = Depends(get_db),
) -> list[TeacherMeetingOut]:
    effective_teacher_id = teacher_id
    authz = rbac.authz_for(db, user)
    if not authz.can("admin.settings.read") and not authz.is_school_wide("reception.meetings.read"):
        emp = scoping.employee_for(db, user)
        effective_teacher_id = emp.id

    return svc.list_teacher_meetings(
        db,
        user.school_id,
        teacher_id=effective_teacher_id,
        meeting_date=meeting_date,
        status_filter=status,
        search=search,
    )


@router.get("/meetings/teacher/{meeting_id}", response_model=TeacherMeetingOut)
def get_teacher_meeting(
    meeting_id: int,
    user: User = Depends(can_read_teacher_meetings),
    db: Session = Depends(get_db),
) -> TeacherMeetingOut:
    meeting = svc.get_teacher_meeting(db, user.school_id, meeting_id)
    authz = rbac.authz_for(db, user)
    if not authz.can("admin.settings.read") and not authz.is_school_wide("reception.meetings.read"):
        emp = scoping.employee_for(db, user)
        if meeting.teacher_id != emp.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot access meeting slips for other teachers")
    return meeting


@router.post("/meetings/teacher", response_model=TeacherMeetingOut, status_code=status.HTTP_201_CREATED)
def create_teacher_meeting(
    payload: TeacherMeetingCreate,
    user: User = Depends(can_write_meetings),
    db: Session = Depends(get_db),
) -> TeacherMeetingOut:
    return svc.create_teacher_meeting(db, user.school_id, user, payload.model_dump())


@router.post("/meetings/teacher/{meeting_id}/respond", response_model=TeacherMeetingOut)
def respond_teacher_meeting(
    meeting_id: int,
    payload: TeacherMeetingRespond,
    user: User = Depends(can_respond_teacher),
    db: Session = Depends(get_db),
) -> TeacherMeetingOut:
    authz = rbac.authz_for(db, user)
    if not authz.can("admin.settings.read") and not authz.is_school_wide("reception.meetings.read"):
        emp = scoping.employee_for(db, user)
        meeting = svc.get_teacher_meeting(db, user.school_id, meeting_id)
        if meeting.teacher_id != emp.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot respond to meeting slips for other teachers")
    return svc.respond_teacher_meeting(db, user.school_id, user, meeting_id, payload.model_dump())


# --- Important Directory -----------------------------------------------------


@router.get("/directory", response_model=list[DirectoryContactOut])
def list_directory_contacts(
    category: str | None = None,
    search: str | None = None,
    user: User = Depends(can_read_directory),
    db: Session = Depends(get_db),
) -> list[DirectoryContactOut]:
    return svc.list_directory_contacts(db, user.school_id, category=category, search=search)


@router.post("/directory", response_model=DirectoryContactOut, status_code=status.HTTP_201_CREATED)
def create_directory_contact(
    payload: DirectoryContactIn,
    user: User = Depends(can_write_directory),
    db: Session = Depends(get_db),
) -> DirectoryContactOut:
    return svc.create_directory_contact(db, user.school_id, payload.model_dump())


@router.put("/directory/{contact_id}", response_model=DirectoryContactOut)
def update_directory_contact(
    contact_id: int,
    payload: DirectoryContactIn,
    user: User = Depends(can_write_directory),
    db: Session = Depends(get_db),
) -> DirectoryContactOut:
    return svc.update_directory_contact(db, user.school_id, contact_id, payload.model_dump())


@router.delete("/directory/{contact_id}")
def delete_directory_contact(
    contact_id: int,
    user: User = Depends(can_write_directory),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return svc.delete_directory_contact(db, user.school_id, contact_id)


# --- Receptionist Complete-Month Fee Collection ------------------------------


@router.get("/fees/status")
def get_fee_status(
    q: str = Query(..., min_length=1),
    user: User = Depends(can_collect_fees),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return svc.get_student_fee_counter_status(db, user.school_id, q)


@router.post("/fees/collect")
def collect_fees(
    payload: ReceptionFeeCollectIn,
    user: User = Depends(can_collect_fees),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return svc.collect_reception_fees(
        db=db,
        school_id=user.school_id,
        user=user,
        enrolment_id=payload.enrolment_id,
        num_months=payload.num_months,
        payment_method=payload.payment_method,
        notes=payload.notes,
    )
