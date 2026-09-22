"""Receptionist operational services: Found & Lost, Passes, Meetings, Directory, and Fee Counter."""
from datetime import UTC, date as Date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    DirectoryContact,
    Employee,
    Enrolment,
    EnrolmentStatus,
    FeeInvoice,
    FeePayment,
    FoundItem,
    InAppNotification,
    PrincipalMeetingRequest,
    Student,
    StudentAuthorizedPerson,
    StudentPass,
    TeacherMeetingRequest,
    User,
    UserRoleAssignment,
    Role,
)
from app.services import audit, fees
from app.services.fee_setup import money
from app.services.notifications import notify_user

ZERO = Decimal("0.00")


# --- Found & Lost -----------------------------------------------------------


def list_found_items(
    db: Session,
    school_id: int,
    status_filter: str | None = None,
    category_filter: str | None = None,
    search: str | None = None,
) -> list[FoundItem]:
    q = select(FoundItem).where(FoundItem.school_id == school_id)
    if status_filter:
        q = q.where(FoundItem.status == status_filter)
    if category_filter:
        q = q.where(FoundItem.category == category_filter)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(
            or_(
                FoundItem.item_name.ilike(pattern),
                FoundItem.description.ilike(pattern),
                FoundItem.found_location.ilike(pattern),
                FoundItem.claimed_by_student_name.ilike(pattern),
                FoundItem.claimed_by_admission_no.ilike(pattern),
            )
        )
    q = q.order_by(FoundItem.found_date.desc(), FoundItem.id.desc())
    return list(db.scalars(q))


def get_found_item(db: Session, school_id: int, item_id: int) -> FoundItem:
    item = db.scalar(
        select(FoundItem).where(FoundItem.school_id == school_id, FoundItem.id == item_id)
    )
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Found item not found")
    return item


def create_found_item(
    db: Session, school_id: int, user: User, data: dict
) -> FoundItem:
    item = FoundItem(
        school_id=school_id,
        item_name=data["item_name"].strip(),
        category=data.get("category", "other"),
        description=data.get("description", "").strip() or None,
        found_location=data["found_location"].strip(),
        found_date=data["found_date"] if isinstance(data["found_date"], Date) else Date.fromisoformat(str(data["found_date"])),
        found_time=data.get("found_time", "").strip() or None,
        recorded_by_id=user.id,
        recorded_by_name=user.full_name,
        photo_url=data.get("photo_url"),
        status="reported",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def broadcast_found_item(
    db: Session, school_id: int, user: User, item_id: int
) -> FoundItem:
    item = get_found_item(db, school_id, item_id)
    if item.status == "collected":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot broadcast an already collected item")

    item.status = "broadcasted"
    item.broadcasted_at = datetime.now(UTC)
    db.flush()

    # Broadcast notification to all active students in the school
    student_users = db.scalars(
        select(User)
        .join(Student, Student.user_id == User.id)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .where(
            User.school_id == school_id,
            User.is_active.is_(True),
            Enrolment.status == EnrolmentStatus.active,
        )
        .distinct()
    ).all()

    for su in student_users:
        notify_user(
            db=db,
            school_id=school_id,
            user_id=su.id,
            title=f"Found Item: {item.item_name}",
            message=f"An item '{item.item_name}' was found at {item.found_location} on {item.found_date}. Please contact the Reception desk if it is yours.",
            category="found_item",
        )

    db.commit()
    db.refresh(item)
    return item


def collect_found_item(
    db: Session, school_id: int, user: User, item_id: int, data: dict
) -> FoundItem:
    item = get_found_item(db, school_id, item_id)
    if item.status == "collected":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Item is already marked as collected")

    item.status = "collected"
    item.collected_at = datetime.now(UTC)
    item.collected_by_staff_id = user.id
    item.collected_by_staff_name = user.full_name
    item.claimed_by_student_id = data.get("claimed_by_student_id")
    item.claimed_by_student_name = (data.get("claimed_by_student_name") or "").strip() or None
    item.claimed_by_admission_no = (data.get("claimed_by_admission_no") or "").strip() or None
    item.claimed_by_class_name = (data.get("claimed_by_class_name") or "").strip() or None
    item.handover_photo_url = data.get("handover_photo_url")
    item.handover_notes = (data.get("handover_notes") or "").strip() or None

    db.commit()
    db.refresh(item)
    return item


# --- Student Authorized Persons Roster ---------------------------------------


def list_authorized_persons(
    db: Session, school_id: int, student_id: int
) -> list[StudentAuthorizedPerson]:
    return list(
        db.scalars(
            select(StudentAuthorizedPerson)
            .where(
                StudentAuthorizedPerson.school_id == school_id,
                StudentAuthorizedPerson.student_id == student_id,
                StudentAuthorizedPerson.is_active.is_(True),
            )
            .order_by(StudentAuthorizedPerson.name)
        )
    )


def add_authorized_person(
    db: Session, school_id: int, student_id: int, data: dict
) -> StudentAuthorizedPerson:
    student = db.scalar(
        select(Student).where(Student.school_id == school_id, Student.id == student_id)
    )
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    person = StudentAuthorizedPerson(
        school_id=school_id,
        student_id=student_id,
        name=data["name"].strip(),
        relationship=data["relationship"].strip(),
        phone=data["phone"].strip(),
        id_proof_type=(data.get("id_proof_type") or "").strip() or None,
        id_proof_number=(data.get("id_proof_number") or "").strip() or None,
        photo_url=data.get("photo_url"),
        notes=(data.get("notes") or "").strip() or None,
        is_active=True,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def update_authorized_person(
    db: Session, school_id: int, person_id: int, data: dict
) -> StudentAuthorizedPerson:
    person = db.scalar(
        select(StudentAuthorizedPerson).where(
            StudentAuthorizedPerson.school_id == school_id,
            StudentAuthorizedPerson.id == person_id,
        )
    )
    if not person:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Authorized person record not found")

    for field in ("name", "relationship", "phone", "id_proof_type", "id_proof_number", "photo_url", "notes"):
        if field in data:
            val = data[field]
            setattr(person, field, val.strip() if isinstance(val, str) else val)
    if "is_active" in data:
        person.is_active = bool(data["is_active"])

    db.commit()
    db.refresh(person)
    return person


def delete_authorized_person(db: Session, school_id: int, person_id: int) -> dict:
    person = db.scalar(
        select(StudentAuthorizedPerson).where(
            StudentAuthorizedPerson.school_id == school_id,
            StudentAuthorizedPerson.id == person_id,
        )
    )
    if not person:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Authorized person record not found")
    person.is_active = False
    db.commit()
    return {"deleted": True, "id": person_id}


# --- Student Passes ----------------------------------------------------------


def list_student_passes(
    db: Session,
    school_id: int,
    pass_date: Date | None = None,
    student_id: int | None = None,
    search: str | None = None,
) -> list[StudentPass]:
    q = select(StudentPass).where(StudentPass.school_id == school_id)
    if pass_date:
        q = q.where(StudentPass.pass_date == pass_date)
    if student_id:
        q = q.where(StudentPass.student_id == student_id)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(
            or_(
                StudentPass.pass_code.ilike(pattern),
                StudentPass.student_name.ilike(pattern),
                StudentPass.admission_no.ilike(pattern),
                StudentPass.pickup_person_name.ilike(pattern),
            )
        )
    q = q.order_by(StudentPass.pass_date.desc(), StudentPass.id.desc())
    return list(db.scalars(q))


def get_student_pass(db: Session, school_id: int, pass_id: int) -> StudentPass:
    p = db.scalar(
        select(StudentPass).where(StudentPass.school_id == school_id, StudentPass.id == pass_id)
    )
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student pass not found")
    return p


def create_student_pass(
    db: Session, school_id: int, user: User, data: dict
) -> StudentPass:
    student = db.scalar(
        select(Student).where(Student.school_id == school_id, Student.id == data["student_id"])
    )
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")

    now = datetime.now(UTC)
    pass_date = (
        data["pass_date"]
        if isinstance(data["pass_date"], Date)
        else Date.fromisoformat(str(data["pass_date"]))
    )
    pass_time = str(data.get("pass_time", now.strftime("%I:%M %p")))

    # Generate sequential pass code
    pass_code = audit.next_number(
        db, school_id, kind="student_pass", year=pass_date.year, prefix=f"SP/{pass_date.year}/", width=5
    )

    # Class section name
    class_label = None
    enrolment = fees.enrolment_for_student(db, student.id)
    if enrolment and enrolment.class_section:
        class_label = enrolment.class_section.label

    # INVARIANT: Creating a pass with ad-hoc or permanent pickup details NEVER mutates
    # the permanent StudentAuthorizedPerson roster table.
    pass_obj = StudentPass(
        school_id=school_id,
        pass_code=pass_code,
        student_id=student.id,
        student_name=student.user.full_name,
        admission_no=student.admission_no,
        class_name=class_label,
        reason=data["reason"].strip(),
        pickup_person_name=data["pickup_person_name"].strip(),
        pickup_person_relation=data["pickup_person_relation"].strip(),
        pickup_person_phone=data["pickup_person_phone"].strip(),
        pickup_person_id_proof=(data.get("pickup_person_id_proof") or "").strip() or None,
        pass_date=pass_date,
        pass_time=pass_time,
        issued_by_id=user.id,
        issued_by_name=user.full_name,
        status="issued",
        remarks=(data.get("remarks") or "").strip() or None,
    )
    db.add(pass_obj)
    db.commit()
    db.refresh(pass_obj)
    return pass_obj


def update_student_pass_status(
    db: Session, school_id: int, pass_id: int, new_status: str, remarks: str | None = None
) -> StudentPass:
    pass_obj = get_student_pass(db, school_id, pass_id)
    pass_obj.status = new_status
    if remarks:
        pass_obj.remarks = remarks.strip()
    db.commit()
    db.refresh(pass_obj)
    return pass_obj


# --- Principal Meeting Slips -------------------------------------------------


def list_principal_meetings(
    db: Session,
    school_id: int,
    meeting_date: Date | None = None,
    status_filter: str | None = None,
    search: str | None = None,
) -> list[PrincipalMeetingRequest]:
    q = select(PrincipalMeetingRequest).where(PrincipalMeetingRequest.school_id == school_id)
    if meeting_date:
        q = q.where(PrincipalMeetingRequest.meeting_date == meeting_date)
    if status_filter:
        q = q.where(PrincipalMeetingRequest.status == status_filter)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(
            or_(
                PrincipalMeetingRequest.slip_code.ilike(pattern),
                PrincipalMeetingRequest.visitor_name.ilike(pattern),
                PrincipalMeetingRequest.visitor_phone.ilike(pattern),
                PrincipalMeetingRequest.student_name.ilike(pattern),
            )
        )
    q = q.order_by(PrincipalMeetingRequest.meeting_date.desc(), PrincipalMeetingRequest.id.desc())
    return list(db.scalars(q))


def get_principal_meeting(
    db: Session, school_id: int, meeting_id: int
) -> PrincipalMeetingRequest:
    m = db.scalar(
        select(PrincipalMeetingRequest).where(
            PrincipalMeetingRequest.school_id == school_id,
            PrincipalMeetingRequest.id == meeting_id,
        )
    )
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Principal meeting slip not found")
    return m


def create_principal_meeting(
    db: Session, school_id: int, user: User, data: dict
) -> PrincipalMeetingRequest:
    now = datetime.now(UTC)
    meeting_date = (
        data["meeting_date"]
        if isinstance(data["meeting_date"], Date)
        else Date.fromisoformat(str(data["meeting_date"]))
    )
    meeting_time = str(data.get("meeting_time", now.strftime("%I:%M %p")))

    slip_code = audit.next_number(
        db, school_id, kind="principal_meeting", year=meeting_date.year, prefix=f"PR/{meeting_date.year}/", width=5
    )

    req = PrincipalMeetingRequest(
        school_id=school_id,
        slip_code=slip_code,
        visitor_name=data["visitor_name"].strip(),
        visitor_phone=data["visitor_phone"].strip(),
        visitor_organization=(data.get("visitor_organization") or "").strip() or None,
        student_name=(data.get("student_name") or "").strip() or None,
        student_admission_no=(data.get("student_admission_no") or "").strip() or None,
        reason=data["reason"].strip(),
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        status="pending",
        created_by_id=user.id,
        created_by_name=user.full_name,
    )
    db.add(req)
    db.flush()

    # Find principal user(s) in this school to send notification
    principal_users = db.scalars(
        select(User)
        .join(UserRoleAssignment, UserRoleAssignment.user_id == User.id)
        .join(Role, Role.id == UserRoleAssignment.role_id)
        .where(
            User.school_id == school_id,
            User.is_active.is_(True),
            Role.code == "principal",
        )
    ).all()

    for pu in principal_users:
        notify_user(
            db=db,
            school_id=school_id,
            user_id=pu.id,
            title="Principal Meeting Request",
            message=f"Visitor {req.visitor_name} ({req.visitor_phone}) requests a meeting. Reason: {req.reason}",
            category="principal_meeting",
        )

    db.commit()
    db.refresh(req)
    return req


def respond_principal_meeting(
    db: Session, school_id: int, user: User, meeting_id: int, data: dict
) -> PrincipalMeetingRequest:
    req = get_principal_meeting(db, school_id, meeting_id)
    status_val = data["status"].strip().lower()  # accepted, declined, waiting, completed, cancelled
    req.status = status_val
    if status_val == "waiting":
        req.wait_duration_minutes = int(data.get("wait_duration_minutes", 15))
    else:
        req.wait_duration_minutes = None

    req.response_notes = data.get("response_notes", "").strip() or None
    req.responded_at = datetime.now(UTC)

    # Notify front desk receptionist who created it
    notify_user(
        db=db,
        school_id=school_id,
        user_id=req.created_by_id,
        title=f"Principal Response: {req.slip_code}",
        message=f"Principal marked meeting as '{req.status}'"
        + (f" (Wait: {req.wait_duration_minutes} mins)" if req.wait_duration_minutes else "")
        + (f". Notes: {req.response_notes}" if req.response_notes else ""),
        category="principal_meeting",
    )

    db.commit()
    db.refresh(req)
    return req


# --- Teacher Meeting Slips ---------------------------------------------------


def list_teacher_meetings(
    db: Session,
    school_id: int,
    teacher_id: int | None = None,
    meeting_date: Date | None = None,
    status_filter: str | None = None,
    search: str | None = None,
) -> list[TeacherMeetingRequest]:
    q = select(TeacherMeetingRequest).where(TeacherMeetingRequest.school_id == school_id)
    if teacher_id:
        q = q.where(TeacherMeetingRequest.teacher_id == teacher_id)
    if meeting_date:
        q = q.where(TeacherMeetingRequest.meeting_date == meeting_date)
    if status_filter:
        q = q.where(TeacherMeetingRequest.status == status_filter)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(
            or_(
                TeacherMeetingRequest.slip_code.ilike(pattern),
                TeacherMeetingRequest.teacher_name.ilike(pattern),
                TeacherMeetingRequest.visitor_name.ilike(pattern),
                TeacherMeetingRequest.visitor_phone.ilike(pattern),
                TeacherMeetingRequest.student_name.ilike(pattern),
            )
        )
    q = q.order_by(TeacherMeetingRequest.meeting_date.desc(), TeacherMeetingRequest.id.desc())
    return list(db.scalars(q))


def get_teacher_meeting(
    db: Session, school_id: int, meeting_id: int
) -> TeacherMeetingRequest:
    m = db.scalar(
        select(TeacherMeetingRequest).where(
            TeacherMeetingRequest.school_id == school_id,
            TeacherMeetingRequest.id == meeting_id,
        )
    )
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher meeting slip not found")
    return m


def create_teacher_meeting(
    db: Session, school_id: int, user: User, data: dict
) -> TeacherMeetingRequest:
    teacher = db.scalar(
        select(Employee).where(Employee.school_id == school_id, Employee.id == data["teacher_id"])
    )
    if not teacher:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher employee not found")

    now = datetime.now(UTC)
    meeting_date = (
        data["meeting_date"]
        if isinstance(data["meeting_date"], Date)
        else Date.fromisoformat(str(data["meeting_date"]))
    )
    meeting_time = str(data.get("meeting_time", now.strftime("%I:%M %p")))

    slip_code = audit.next_number(
        db, school_id, kind="teacher_meeting", year=meeting_date.year, prefix=f"TR/{meeting_date.year}/", width=5
    )

    req = TeacherMeetingRequest(
        school_id=school_id,
        slip_code=slip_code,
        teacher_id=teacher.id,
        teacher_name=teacher.user.full_name if teacher.user else "Teacher",
        visitor_name=data["visitor_name"].strip(),
        visitor_phone=data["visitor_phone"].strip(),
        visitor_relation=(data.get("visitor_relation") or "").strip() or None,
        student_name=(data.get("student_name") or "").strip() or None,
        student_admission_no=(data.get("student_admission_no") or "").strip() or None,
        reason=data["reason"].strip(),
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        status="pending",
        created_by_id=user.id,
        created_by_name=user.full_name,
    )
    db.add(req)
    db.flush()

    # Notify teacher user
    if teacher.user_id:
        notify_user(
            db=db,
            school_id=school_id,
            user_id=teacher.user_id,
            title="Teacher Meeting Request",
            message=f"Visitor {req.visitor_name} ({req.visitor_phone}) requests a meeting. Reason: {req.reason}",
            category="teacher_meeting",
        )

    db.commit()
    db.refresh(req)
    return req


def respond_teacher_meeting(
    db: Session, school_id: int, user: User, meeting_id: int, data: dict
) -> TeacherMeetingRequest:
    req = get_teacher_meeting(db, school_id, meeting_id)
    status_val = data["status"].strip().lower()  # accepted, declined, completed, cancelled
    req.status = status_val
    req.response_notes = data.get("response_notes", "").strip() or None
    req.responded_at = datetime.now(UTC)

    # Notify front desk receptionist who created it
    notify_user(
        db=db,
        school_id=school_id,
        user_id=req.created_by_id,
        title=f"Teacher Response: {req.slip_code}",
        message=f"{req.teacher_name} marked meeting as '{req.status}'. Notes: {req.response_notes or 'None'}",
        category="teacher_meeting",
    )

    db.commit()
    db.refresh(req)
    return req


# --- Important Directory -----------------------------------------------------


def list_directory_contacts(
    db: Session, school_id: int, category: str | None = None, search: str | None = None
) -> list[DirectoryContact]:
    q = select(DirectoryContact).where(DirectoryContact.school_id == school_id)
    if category:
        q = q.where(DirectoryContact.category == category)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where(
            or_(
                DirectoryContact.name.ilike(pattern),
                DirectoryContact.designation_or_department.ilike(pattern),
                DirectoryContact.phone_primary.ilike(pattern),
                DirectoryContact.address.ilike(pattern),
            )
        )
    q = q.order_by(
        DirectoryContact.is_emergency.desc(),
        DirectoryContact.display_order,
        DirectoryContact.name,
    )
    return list(db.scalars(q))


def create_directory_contact(
    db: Session, school_id: int, data: dict
) -> DirectoryContact:
    contact = DirectoryContact(
        school_id=school_id,
        category=data.get("category", "Emergency").strip(),
        name=data["name"].strip(),
        designation_or_department=data.get("designation_or_department", "").strip() or None,
        phone_primary=data["phone_primary"].strip(),
        phone_secondary=data.get("phone_secondary", "").strip() or None,
        email=data.get("email", "").strip() or None,
        address=data.get("address", "").strip() or None,
        operating_hours=data.get("operating_hours", "").strip() or None,
        is_emergency=bool(data.get("is_emergency", False)),
        display_order=int(data.get("display_order", 0)),
        notes=data.get("notes", "").strip() or None,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_directory_contact(
    db: Session, school_id: int, contact_id: int, data: dict
) -> DirectoryContact:
    contact = db.scalar(
        select(DirectoryContact).where(
            DirectoryContact.school_id == school_id, DirectoryContact.id == contact_id
        )
    )
    if not contact:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory contact not found")

    for field in (
        "category",
        "name",
        "designation_or_department",
        "phone_primary",
        "phone_secondary",
        "email",
        "address",
        "operating_hours",
        "notes",
    ):
        if field in data:
            val = data[field]
            setattr(contact, field, val.strip() if isinstance(val, str) else val)
    if "is_emergency" in data:
        contact.is_emergency = bool(data["is_emergency"])
    if "display_order" in data:
        contact.display_order = int(data["display_order"])

    db.commit()
    db.refresh(contact)
    return contact


def delete_directory_contact(db: Session, school_id: int, contact_id: int) -> dict:
    contact = db.scalar(
        select(DirectoryContact).where(
            DirectoryContact.school_id == school_id, DirectoryContact.id == contact_id
        )
    )
    if not contact:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Directory contact not found")
    db.delete(contact)
    db.commit()
    return {"deleted": True, "id": contact_id}


# --- Receptionist Complete-Month Fee Collection ------------------------------


def get_student_fee_counter_status(
    db: Session, school_id: int, query: str
) -> dict:
    """Search for a student and return their outstanding chronological invoices

    and the pre-computed exact sums for complete month selections (1..N).
    Strictly forbids partial month or arbitrary payment amounts.
    """
    clean_q = query.strip()
    student = db.scalar(
        select(Student)
        .join(User, User.id == Student.user_id)
        .where(
            Student.school_id == school_id,
            or_(
                Student.admission_no == clean_q,
                User.full_name.ilike(f"%{clean_q}%"),
            ),
        )
    )
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Student '{query}' not found")

    enrolment = fees.enrolment_for_student(db, student.id)
    if not enrolment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No active enrolment for student {student.admission_no}")

    # Outstanding invoices in strict chronological order (oldest first)
    invoices = fees.outstanding_invoices(db, enrolment.id)
    # Bring any late fees up to date for presentation
    today = Date.today()
    for inv in invoices:
        fees.assess_late_fee(db, inv, today)

    invoice_summaries = []
    for inv in invoices:
        t = fees.totals(db, inv)
        invoice_summaries.append({
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "month": inv.period_month,
            "year": inv.period_year,
            "due_date": inv.due_date.isoformat(),
            "amount": str(t["charged"]),
            "discount": str(t["discount"]),
            "payable": str(t["payable"]),
            "paid": str(t["paid"]),
            "balance": str(t["balance"]),
            "lines": [
                {
                    "description": line.description,
                    "amount": str(line.amount),
                    "discount": str(line.discount),
                    "net": str(line.net),
                }
                for line in inv.lines
            ],
        })

    # Build options for selecting complete months 1..N
    # Option k corresponds to paying exactly the sum of the balances of the first k invoices
    month_options = []
    cumulative_total = ZERO
    for idx, inv_sum in enumerate(invoice_summaries):
        balance = Decimal(inv_sum["balance"])
        cumulative_total += balance
        month_options.append({
            "months_count": idx + 1,
            "label": f"{idx + 1} Month{'s' if idx > 0 else ''} (Through {inv_sum['month']:02d}/{inv_sum['year']})",
            "total_amount": str(money(cumulative_total)),
            "invoices_covered": [inv["invoice_no"] for inv in invoice_summaries[: idx + 1]],
        })

    return {
        "student": {
            "id": student.id,
            "enrolment_id": enrolment.id,
            "admission_no": student.admission_no,
            "name": student.user.full_name,
            "phone": student.user.phone,
            "email": student.user.email,
            "class_label": enrolment.class_section.label if enrolment.class_section else "—",
            "roll_number": enrolment.roll_no,
        },
        "outstanding_invoices": invoice_summaries,
        "available_month_options": month_options,
        "total_outstanding": str(money(cumulative_total)),
    }


def collect_reception_fees(
    db: Session,
    school_id: int,
    user: User,
    enrolment_id: int,
    num_months: int,
    payment_method: str = "cash",
    notes: str | None = None,
) -> dict:
    """Collect fee for exactly num_months complete outstanding invoices.

    Strictly no partial amount or arbitrary entry.
    """
    enrolment = db.scalar(
        select(Enrolment).where(Enrolment.school_id == school_id, Enrolment.id == enrolment_id)
    )
    if not enrolment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")

    invoices = fees.outstanding_invoices(db, enrolment.id)
    if not invoices:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Student has no outstanding fee invoices")

    if num_months < 1 or num_months > len(invoices):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid month selection. Must select between 1 and {len(invoices)} complete months.",
        )

    # Bring late fees up to date
    today = Date.today()
    for inv in invoices:
        fees.assess_late_fee(db, inv, today)

    # Strictly calculate exact total of the first num_months invoices
    target_invoices = invoices[:num_months]
    exact_total = ZERO
    for inv in target_invoices:
        t = fees.totals(db, inv)
        exact_total += t["balance"]

    exact_total = money(exact_total)
    if exact_total <= ZERO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Selected invoices have zero remaining balance")

    # Generate counter idempotency key
    idempotency_key = f"RECEP-{enrolment.id}-{int(datetime.now(UTC).timestamp())}-{num_months}"

    # Collect via the existing authoritative FIFO collection engine
    payment = fees.collect(
        db=db,
        enrolment_id=enrolment.id,
        amount=exact_total,
        idempotency_key=idempotency_key,
        method=payment_method,
        instrument_ref=(notes or f"Counter-{user.full_name}")[:40],
        actor=user,
    )

    return {
        "success": True,
        "payment_id": payment.id,
        "receipt_no": payment.receipt_no,
        "amount": str(payment.amount),
        "total_paid": str(payment.amount),
        "method": payment.method,
        "received_at": payment.received_at.isoformat(),
        "months_paid": num_months,
        "student_name": enrolment.student.user.full_name,
        "admission_no": enrolment.student.admission_no,
        "class_label": enrolment.class_section.label if enrolment.class_section else "—",
        "invoices_cleared": [inv.invoice_no for inv in target_invoices],
        "invoices_covered": [inv.invoice_no for inv in target_invoices],
    }
