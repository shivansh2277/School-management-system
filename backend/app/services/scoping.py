"""Access scoping. Every service function touching student-owned data goes through here.

BLUEPRINT D12: enforced in the service layer, not only at the routes, so a new
endpoint cannot accidentally skip it.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ClassSection,
    ClassSubjectTeacher,
    Guardian,
    StudentGuardian,
    Student,
    Employee,
    User,
    UserRole,
)
from app.services.common import current_enrolment


def forbidden(msg: str = "Out of scope") -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, msg)


def employee_for(db: Session, user: User) -> Employee:
    t = db.scalar(select(Employee).where(Employee.user_id == user.id))
    if t is None:
        raise forbidden("Not a teacher")
    return t


def guardian_for(db: Session, user: User) -> Guardian:
    p = db.scalar(select(Guardian).where(Guardian.user_id == user.id))
    if p is None:
        raise forbidden("Not a parent")
    return p


def student_for(db: Session, user: User) -> Student:
    s = db.scalar(select(Student).where(Student.user_id == user.id))
    if s is None:
        raise forbidden("Not a student")
    return s


def student_id_for(db: Session, user: User) -> int:
    return student_for(db, user).id


def child_ids_for(db: Session, user: User) -> list[int]:
    parent = guardian_for(db, user)
    return list(
        db.scalars(select(StudentGuardian.student_id).where(StudentGuardian.guardian_id == parent.id))
    )


def class_section_ids_for(db: Session, user: User) -> list[int]:
    """Sections a teacher class-teaches OR teaches a subject in."""
    teacher = employee_for(db, user)
    own = select(ClassSection.id).where(ClassSection.class_teacher_id == teacher.id)
    taught = select(ClassSubjectTeacher.class_section_id).where(
        ClassSubjectTeacher.teacher_id == teacher.id
    )
    return sorted({*db.scalars(own), *db.scalars(taught)})


def assert_teaches_section(db: Session, user: User, class_section_id: int) -> None:
    if class_section_id not in class_section_ids_for(db, user):
        raise forbidden("You do not teach this class section")


def narrow_to_own_sections(
    db: Session, user: User, class_section_id: int | None, what: str = "This list"
) -> int | None:
    """Hold a whole-school read down to one section the caller actually teaches.

    The single definition of ERP_BLUEPRINT section 5.10.8's "Class Teacher (own
    section)", used by the admin attendance screens and by the report gate, so
    a report and the screen beside it cannot answer the same question
    differently.

    It exists because the permission layer cannot do this job. A teacher holds
    `attendance.record.read` school-wide - their permissions are unscoped by
    design and the restriction has always lived here (HANDOFF section 4) - so
    `require_permission(..., school_wide=True)` passes for them. It stops a
    guardian, whose grant is scoped to their own children, and nobody else.

    Omitting the section is refused rather than quietly widened. Returning
    every section a teacher teaches would be defensible, but "no filter" is
    exactly how this leaked in the first place: a missing parameter must not
    mean the whole school.

    Anyone who is not a teacher is unchanged: an office clerk, a principal and
    an auditor read the school, which is what their roles are for.
    """
    if user.role is not UserRole.teacher:
        return class_section_id
    if class_section_id is None:
        raise forbidden(f"{what} must name one of your class sections")
    assert_teaches_section(db, user, class_section_id)
    return class_section_id


def assert_teaches_subject_in_section(
    db: Session, user: User, class_section_id: int, subject_id: int
) -> None:
    teacher = employee_for(db, user)
    owned = db.scalar(
        select(ClassSubjectTeacher.id).where(
            ClassSubjectTeacher.class_section_id == class_section_id,
            ClassSubjectTeacher.subject_id == subject_id,
            ClassSubjectTeacher.teacher_id == teacher.id,
        )
    )
    if owned is None:
        raise forbidden("You do not teach this subject in this class section")


def assert_can_read_student(db: Session, user: User, student_id: int) -> Student:
    student = db.get(Student, student_id)
    # The tenant boundary comes before every role rule, and answers 404 rather
    # than 403: whether another customer has a student with this id is itself
    # not this school's business. The role branches below happen to bind a
    # teacher, guardian and student to their own school through the sections
    # and links they check; the admin branch checked nothing at all, which left
    # this chokepoint's thirteen callers cross-tenant readable.
    if student is None or student.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    if user.role == UserRole.admin:
        return student
    if user.role == UserRole.student:
        if student.user_id != user.id:
            raise forbidden("You may only read your own record")
        return student
    if user.role == UserRole.parent:
        if student_id not in child_ids_for(db, user):
            raise forbidden("Not your child")
        return student
    if user.role == UserRole.teacher:
        enrolment = current_enrolment(db, student.id)
        if (
            enrolment is None
            or enrolment.class_section_id not in class_section_ids_for(db, user)
        ):
            raise forbidden("Student is outside your sections")
        return student
    raise forbidden()
