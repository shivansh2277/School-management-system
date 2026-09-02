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
    Parent,
    ParentStudent,
    Student,
    Teacher,
    User,
    UserRole,
)


def forbidden(msg: str = "Out of scope") -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, msg)


def teacher_for(db: Session, user: User) -> Teacher:
    t = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    if t is None:
        raise forbidden("Not a teacher")
    return t


def parent_for(db: Session, user: User) -> Parent:
    p = db.scalar(select(Parent).where(Parent.user_id == user.id))
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
    parent = parent_for(db, user)
    return list(
        db.scalars(select(ParentStudent.student_id).where(ParentStudent.parent_id == parent.id))
    )


def class_section_ids_for(db: Session, user: User) -> list[int]:
    """Sections a teacher class-teaches OR teaches a subject in."""
    teacher = teacher_for(db, user)
    own = select(ClassSection.id).where(ClassSection.class_teacher_id == teacher.id)
    taught = select(ClassSubjectTeacher.class_section_id).where(
        ClassSubjectTeacher.teacher_id == teacher.id
    )
    return sorted({*db.scalars(own), *db.scalars(taught)})


def assert_teaches_section(db: Session, user: User, class_section_id: int) -> None:
    if class_section_id not in class_section_ids_for(db, user):
        raise forbidden("You do not teach this class section")


def assert_teaches_subject_in_section(
    db: Session, user: User, class_section_id: int, subject_id: int
) -> None:
    teacher = teacher_for(db, user)
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
    if student is None:
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
        if student.class_section_id not in class_section_ids_for(db, user):
            raise forbidden("Student is outside your sections")
        return student
    raise forbidden()
