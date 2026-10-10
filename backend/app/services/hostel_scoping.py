"""Hostel authorization scoping.

Enforces that Wardens can only access and manipulate data within their assigned hostel,
while Chief Provost and Super Admin possess school-wide multi-hostel authority.
Authoritative source of Warden scope is strictly `UserRoleAssignment` (zero competing sources).
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Guardian,
    Role,
    ScopeType,
    Student,
    StudentGuardian,
    User,
    UserRole,
    UserRoleAssignment,
    HostelAdmission,
)


def forbidden(msg: str = "Out of scope") -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, msg)


def get_warden_assigned_hostel_id(db: Session, user: User) -> int | None:
    """Authoritatively queries the assigned hostel id for a warden from UserRoleAssignment."""
    stmt = (
        select(UserRoleAssignment.scope_id)
        .join(Role, Role.id == UserRoleAssignment.role_id)
        .where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.school_id == user.school_id,
            Role.code == "warden",
            UserRoleAssignment.scope_type == ScopeType.hostel,
        )
    )
    return db.scalar(stmt)


def is_chief_provost(db: Session, user: User) -> bool:
    """True when caller holds the dedicated Chief Provost role (hostel-domain authority)."""
    stmt = (
        select(UserRoleAssignment.id)
        .join(Role, Role.id == UserRoleAssignment.role_id)
        .where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.school_id == user.school_id,
            Role.code == "chief_provost",
            UserRoleAssignment.scope_type == ScopeType.school,
        )
    )
    return db.scalar(stmt) is not None


def is_erp_admin(db: Session, user: User) -> bool:
    """True when caller is an existing full ERP Administrator (super_admin)."""
    if user.role == UserRole.admin and (user.login_id.startswith("admin@") or user.login_id == "admin"):
        return True
    stmt = (
        select(UserRoleAssignment.id)
        .join(Role, Role.id == UserRoleAssignment.role_id)
        .where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.school_id == user.school_id,
            Role.code.in_(("super_admin", "principal")),
            UserRoleAssignment.scope_type == ScopeType.school,
        )
    )
    return db.scalar(stmt) is not None


def can_manage_all_hostels(db: Session, user: User) -> bool:
    """True when caller has cross-hostel scope (Chief Provost within Hostel domain, or Super Admin)."""
    return is_chief_provost(db, user) or is_erp_admin(db, user)


is_chief_provost_or_admin = can_manage_all_hostels


def assert_can_manage_hostel(db: Session, user: User, hostel_id: int) -> None:
    """Enforces that caller has authority to manage the specified hostel.
    
    Chief Provost / Admin: allowed across all hostels.
    Warden: allowed strictly for their assigned hostel_id from UserRoleAssignment.
    Any attempt by a Warden to access another hostel raises HTTP 403 Forbidden.
    """
    if is_chief_provost_or_admin(db, user):
        return

    assigned_id = get_warden_assigned_hostel_id(db, user)
    if assigned_id is not None and assigned_id == hostel_id:
        return

    raise forbidden("Out of scope: Access to this hostel is forbidden for this warden")


def readable_hostel_ids_for(db: Session, user: User) -> list[int] | None:
    """Returns list of hostel IDs caller may read, or None for school-wide unrestricted."""
    if is_chief_provost_or_admin(db, user):
        return None  # Unrestricted school-wide

    assigned_id = get_warden_assigned_hostel_id(db, user)
    if assigned_id is not None:
        return [assigned_id]

    if user.role == UserRole.student:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student:
            return list(
                db.scalars(
                    select(HostelAdmission.hostel_id).where(
                        HostelAdmission.student_id == student.id,
                        HostelAdmission.status == "active",
                    )
                )
            )

    if user.role == UserRole.parent:
        guardian = db.scalar(select(Guardian).where(Guardian.user_id == user.id))
        if guardian:
            child_ids = select(StudentGuardian.student_id).where(
                StudentGuardian.guardian_id == guardian.id
            )
            return list(
                db.scalars(
                    select(HostelAdmission.hostel_id).where(
                        HostelAdmission.student_id.in_(child_ids),
                        HostelAdmission.status == "active",
                    )
                )
            )

    return []
