import csv
import io
from datetime import UTC, date as Date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled
from app.core.security import hash_password
from app.models import (
    AuditAction,
    ClassSection,
    Enrolment,
    Gender,
    Guardian,
    StudentGuardian,
    GuardianRelation,
    OwnerType,
    Student,
    User,
    UserRole,
)
from app.schemas.common import Page
from app.services import assessment, attendance, audit, homework, tenancy
from app.services import custom_fields as cf
from app.services import scoping
from app.services.common import current_enrolment

router = APIRouter(
    prefix="/admin", tags=["admin"],
    dependencies=[Depends(module_enabled("students"))],
)
admin_only = require_permission("students.profile.read", school_wide=True)


class GuardianInput(BaseModel):
    full_name: str
    phone: str
    relation: GuardianRelation = GuardianRelation.father
    occupation: str | None = None
    password: str = "Parent@123"


class StudentCreate(BaseModel):
    # extra="forbid" because the guardian key was renamed under these tests
    # and they kept passing: a body with a key nobody reads looked identical
    # to a body that worked.
    model_config = {"extra": "forbid"}

    full_name: str
    # Omit it and the school's gapless sequence allocates one (§0.21).
    admission_no: str | None = None
    class_section_id: int
    roll_no: int
    dob: Date | None = None
    gender: Gender | None = None
    address: str | None = None
    admission_date: Date | None = None
    phone: str | None = None
    email: str | None = None
    password: str = "Student@123"
    guardian: GuardianInput | None = None
    guardian_id: int | None = None
    # School-defined attributes (§3.15 level 2), keyed by custom field key.
    custom: dict | None = None


class StudentUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    full_name: str | None = None
    class_section_id: int | None = None
    roll_no: int | None = None
    dob: Date | None = None
    gender: Gender | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    custom: dict | None = None


def _owned(db: Session, user: User, student_id: int) -> Student:
    """This school's student, or 404.

    `db.get()` is not tenant-aware, and three handlers here used it bare, so a
    guessed id read - and in one case edited - another customer's child.

    Writes only. Reading a child goes through
    `scoping.assert_can_read_student`, which applies the role scope on top of
    the tenant one; the write handlers here are gated on
    `students.profile.write`, which no teacher holds, so the roles that reach
    them read the whole school anyway.
    """
    s = db.get(Student, student_id)
    if s is None or s.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return s


def _row(db: Session, s: Student) -> dict:
    enrolment = current_enrolment(db, s.id)
    guardians = db.scalars(
        select(Guardian)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(StudentGuardian.student_id == s.id)
    ).all()
    return {
        "id": s.id,
        "full_name": s.user.full_name,
        "admission_no": s.admission_no,
        # The current year's enrolment id, which nothing else exposed.
        # Every money route is keyed on the enrolment rather than the student -
        # a fee belongs to a child's year in a class, not to the child - so
        # without this the client could only reach it by finding a row that
        # already carried money (an invoice, a defaulter, a ledger line). A
        # student with no invoices was therefore unpayable-for, and assigning a
        # fee plan or requesting a concession could not be built at all.
        # `current_enrolment` was already being called here for the class and
        # roll number; only the id was being dropped.
        "enrolment_id": enrolment.id if enrolment else None,
        "class_section_id": enrolment.class_section_id if enrolment else None,
        "class_label": enrolment.class_section.label if enrolment else "",
        "roll_no": enrolment.roll_no if enrolment else None,
        "photo_url": s.user.photo_url,
        "is_active": s.user.is_active,
        "guardian_name": guardians[0].user.full_name if guardians else None,
        "guardian_phone": guardians[0].user.phone if guardians else None,
        "custom": s.custom or {},
    }


def _roster(db: Session, user: User, class_section_id: int | None, q: str | None):
    """The roster query, shared by the screen and the export.

    One query, not two, on purpose: section 5.10.9 calls a report that shows
    rows the screen would not the most common data-leak path in an ERP, and the
    realistic way that happens is a download handler written to be quick rather
    than written to match. Sharing the statement means it cannot drift.
    """
    # Carrying `school_id` is not filtering on it (CLAUDE.md, HANDOFF section
    # 4). This is the roster of every child in the school, so the omission here
    # was the widest of that family.
    stmt = (
        select(Student)
        .join(User, User.id == Student.user_id)
        .where(Student.school_id == user.school_id)
    )
    if class_section_id is not None:
        stmt = stmt.where(
            Student.id.in_(
                select(Enrolment.student_id).where(
                    Enrolment.class_section_id == class_section_id
                )
            )
        )
    # And a teacher sees the children they teach, not the school. This roster
    # carries date of birth, address and a guardian's phone number through to
    # the detail screen and the export, and it was answering any of the twelve
    # teachers for all hundred children. Same rule as the attendance screens
    # and the report library, from the same helper.
    allowed = scoping.readable_section_ids(db, user)
    if allowed is not None:
        stmt = stmt.where(
            Student.id.in_(
                select(Enrolment.student_id).where(
                    Enrolment.class_section_id.in_(allowed)
                )
            )
        )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(User.full_name.ilike(like), Student.admission_no.ilike(like))
        )
    return stmt.order_by(Student.admission_no)


@router.get("/students", response_model=Page)
def list_students(
    class_section_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> Page:
    stmt = _roster(db, user, class_section_id, q)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return Page(items=[_row(db, s) for s in rows], total=total, page=page, page_size=page_size)


# The columns a bulk export carries. Deliberately the roster's own fields plus
# the contact details an office actually needs, and deliberately not the whole
# record: date of birth, address and the school's custom fields stay behind the
# per-student screen. An export is where over-collection becomes permanent.
EXPORT_COLUMNS = [
    "admission_no",
    "full_name",
    "class_label",
    "roll_no",
    "guardian_name",
    "guardian_phone",
    "is_active",
]


@router.get("/students/export")
def export_students(
    class_section_id: int | None = None,
    q: str | None = None,
    user: User = Depends(require_permission("students.profile.export", school_wide=True)),
    db: Session = Depends(get_db),
) -> Response:
    """Download the roster as CSV.

    This route exists to make two controls real that until now gated nothing.

    `students.profile.export` was granted to the Admin Officer and required by
    no route in `app/api/`, so the separation section 10.2 is proud of - being
    allowed to see a child on screen is not being allowed to download two
    thousand of them - was decorative. It is now the only way to get the file,
    and it is demanded school-wide so a guardian's own-children grant cannot
    reach it.

    `AuditAction.export` had been in the enum since Part 1 and had never once
    been written. Every download is now a row in `audit_log` naming the actor,
    the filters and the count (section 5.10.9).

    The rows come from `_roster()`, the same statement the screen uses, so this
    cannot become a way to see what the screen would not.

    This is a GET that commits, which CLAUDE.md otherwise forbids. The rule
    exists to stop incidental writes on a read - v0's `refresh_overdue()`
    moving invoice statuses from inside a dashboard query. Here the write *is*
    the point: section 5.10.9 requires the download to be audited, and an audit
    row written only on some other request would not record the download. The
    exception is this route and the ones like it, not a licence generally.
    """
    year = tenancy.current_year(db, user.school_id)
    rows = db.scalars(_roster(db, user, class_section_id, q)).all()
    items = [_row(db, s) for s in rows]

    buf = io.StringIO(newline="")
    # Section 5.10.9: an export states its year, its filters and when it was
    # made. A printed report with no context is one that gets misquoted, and a
    # CSV on somebody's desktop six months from now is exactly that case.
    filters = {"class_section_id": class_section_id, "q": q}
    stated = ", ".join(f"{k}={v}" for k, v in filters.items() if v is not None) or "none"
    print(
        f"# Sunrise ERP student roster | academic year {year.code}"
        f" | filters: {stated}"
        f" | generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC"
        f" by {user.full_name}",
        file=buf,
    )
    writer = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)

    audit.record_export(
        db,
        actor=user,
        school_id=user.school_id,
        what="student",
        rows=len(items),
        filters={k: v for k, v in filters.items() if v is not None},
        academic_year_id=year.id,
    )
    db.commit()

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="students-{year.code}-'
                f'{datetime.now(UTC):%Y%m%d}.csv"'
            )
        },
    )


@router.post("/students", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("students.profile.write"))])
def create_student(
    body: StudentCreate, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    section = db.get(ClassSection, body.class_section_id)
    if section is None or section.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class section not found")
    custom = cf.validate(db, user.school_id, OwnerType.student, body.custom)
    admission_no = body.admission_no or audit.admission_number(
        db, user.school_id, (body.admission_date or Date.today()).year
    )
    if db.scalar(select(User).where(User.login_id == admission_no)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Admission number already exists")
    # Student login + student row + (new or linked) guardian, in one transaction.
    su = User(
        school_id=user.school_id,
        role=UserRole.student,
        login_id=admission_no,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
    )
    db.add(su)
    db.flush()
    student = Student(
        school_id=user.school_id,
        user_id=su.id,
        admission_no=admission_no,
        dob=body.dob,
        gender=body.gender,
        address=body.address,
        admission_date=body.admission_date or Date.today(),
        custom=custom,
    )
    db.add(student)
    db.flush()
    # The class and roll number belong to a year, so creating a student also
    # creates their enrolment in the section's.
    db.add(
        Enrolment(
            school_id=user.school_id,
            student_id=student.id,
            academic_year_id=section.academic_year_id,
            class_section_id=section.id,
            roll_no=body.roll_no,
            joined_on=body.admission_date or Date.today(),
        )
    )
    db.flush()

    guardian_row = None
    if body.guardian_id is not None:
        guardian_row = db.get(Guardian, body.guardian_id)
        if guardian_row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardian not found")
        relation = GuardianRelation.legal_guardian
    elif body.guardian is not None:
        if db.scalar(select(User).where(User.login_id == body.guardian.phone)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Guardian mobile already registered")
        pu = User(
            school_id=user.school_id,
            role=UserRole.parent,
            login_id=body.guardian.phone,
            password_hash=hash_password(body.guardian.password),
            full_name=body.guardian.full_name,
            phone=body.guardian.phone,
        )
        db.add(pu)
        db.flush()
        guardian_row = Guardian(
            school_id=user.school_id,
            user_id=pu.id,
            occupation=body.guardian.occupation,
        )
        db.add(guardian_row)
        db.flush()
        relation = body.guardian.relation
    if guardian_row is not None:
        db.add(
            StudentGuardian(
                school_id=user.school_id,
                guardian_id=guardian_row.id,
                student_id=student.id,
                relation=relation,
                is_primary=not db.scalar(
                    select(StudentGuardian.id).where(
                        StudentGuardian.student_id == student.id,
                        StudentGuardian.is_primary.is_(True),
                    )
                ),
            )
        )
    db.commit()
    return _row(db, student)


@router.get("/students/{student_id}")
def student_detail(
    student_id: int, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    # The shared gate, not `_owned`: it applies the role scope as well as the
    # tenant one, so a teacher gets the children they teach and an office clerk
    # still gets the school. A teacher who knows an id must not be able to read
    # another section's child, and an id is guessable.
    s = scoping.assert_can_read_student(db, user, student_id)
    enrolment = current_enrolment(db, s.id)
    exam = assessment.latest_exam_with_marks(
        db, s.school_id, enrolment.class_section_id if enrolment else None
    )
    hw = homework.for_student(db, s.id)
    return {
        **_row(db, s),
        "dob": s.dob,
        "gender": s.gender,
        "address": s.address,
        "admission_date": s.admission_date,
        "attendance_percent": attendance.student_percent(db, s.id),
        "latest_result_percent": (
            assessment.student_average_percent(db, s.id, exam.id) if exam else None
        ),
        "homework_pending": sum(1 for h in hw if not h.submitted),
    }


@router.patch("/students/{student_id}", dependencies=[Depends(require_permission("students.profile.write"))])
def update_student(
    student_id: int,
    body: StudentUpdate,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    s = _owned(db, user, student_id)
    # class_section_id and roll_no live on the enrolment now. Setting them on
    # the Student silently did nothing: SQLAlchemy accepts the attribute, the
    # column is not there, and the move was lost.
    if body.class_section_id is not None or body.roll_no is not None:
        enrolment = current_enrolment(db, s.id)
        if enrolment is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This student has no enrolment in the current academic year",
            )
        if body.class_section_id is not None:
            section = db.get(ClassSection, body.class_section_id)
            if section is None or section.school_id != user.school_id:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Class section not found")
            enrolment.class_section_id = section.id
        if body.roll_no is not None:
            enrolment.roll_no = body.roll_no
    for field in ("dob", "gender", "address"):
        value = getattr(body, field)
        if value is not None:
            setattr(s, field, value)
    if body.custom is not None:
        s.custom = cf.validate(
            db, user.school_id, OwnerType.student, body.custom,
            existing=s.custom, partial=True,
        )
    for field in ("full_name", "phone", "email"):
        value = getattr(body, field)
        if value is not None:
            setattr(s.user, field, value)
    db.commit()
    return _row(db, s)


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("students.profile.write"))])
def deactivate_student(
    student_id: int,
    reason: str = Query(
        ...,
        min_length=3,
        description="Why this student is being deactivated. Recorded in the audit log.",
    ),
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> Response:
    s = _owned(db, user, student_id)
    before = audit.snapshot(s.user, ["is_active"])
    s.user.is_active = False  # portal access revoked; the record is retained
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="student",
        entity_id=s.id,
        action=AuditAction.status_change,
        before=before,
        after=audit.snapshot(s.user, ["is_active"]),
        reason=reason,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
