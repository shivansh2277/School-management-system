from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import hash_password
from app.models import (
    AuditAction,
    AuditLog,
    Employee,
    Enrolment,
    EnrolmentStatus,
    Guardian,
    Role,
    ScopeType,
    Student,
    StudentGuardian,
    User,
    UserRole,
    UserRoleAssignment,
)
from app.schemas.user_access import (
    AdminUserAccessItem,
    AssignUserRoleRequest,
    BlockUserRequest,
    ResetPasswordRequest,
    UserAccessActionResponse,
)
from app.services import rbac
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin/users", tags=["admin-user-access"])

manager_permission = require_permission("admin.user_access.manage", school_wide=True)


@router.get("", response_model=list[AdminUserAccessItem])
def list_users_access(
    role: UserRole | None = Query(None, description="Filter by user role"),
    search: str | None = Query(None, description="Search by name, login ID, or phone"),
    blocked: bool | None = Query(None, description="Filter by blocked status"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: User = Depends(manager_permission),
    db: Session = Depends(get_db),
) -> list[AdminUserAccessItem]:
    # Tenant-scoped
    q = select(User).where(User.school_id == user.school_id)
    if role:
        q = q.where(User.role == role)
    if blocked is not None:
        q = q.where(User.app_access_blocked == blocked)
    if search:
        s = f"%{search.strip()}%"
        q = q.where(
            or_(
                User.full_name.ilike(s),
                User.login_id.ilike(s),
                User.phone.ilike(s),
                User.email.ilike(s),
            )
        )

    q = q.order_by(User.id.desc()).offset(offset).limit(limit)
    users = list(db.scalars(q))
    if not users:
        return []

    user_ids = [u.id for u in users]

    # Preload student info
    students_by_user = {
        s.user_id: s
        for s in db.scalars(select(Student).where(Student.user_id.in_(user_ids)))
    }
    student_ids = [s.id for s in students_by_user.values()]

    # Student active enrolments for class label
    enrolment_labels: dict[int, str] = {}
    if student_ids:
        enrolments = db.scalars(
            select(Enrolment).where(
                Enrolment.student_id.in_(student_ids),
                Enrolment.status == EnrolmentStatus.active,
            )
        )
        for e in enrolments:
            if e.class_section:
                cls_name = e.class_section.class_.name if getattr(e.class_section, "class_", None) else ""
                enrolment_labels[e.student_id] = f"{cls_name} - {e.class_section.section}".strip(" -")

    # Preload employee info
    employees_by_user = {
        e.user_id: e
        for e in db.scalars(select(Employee).where(Employee.user_id.in_(user_ids)))
    }

    # Preload guardian info
    guardians_by_user = {
        g.user_id: g
        for g in db.scalars(select(Guardian).where(Guardian.user_id.in_(user_ids)))
    }
    guardian_ids = [g.id for g in guardians_by_user.values()]
    children_by_guardian: dict[int, list[str]] = {}
    if guardian_ids:
        sg_rows = db.execute(
            select(StudentGuardian.guardian_id, User.full_name)
            .join(Student, Student.id == StudentGuardian.student_id)
            .join(User, User.id == Student.user_id)
            .where(StudentGuardian.guardian_id.in_(guardian_ids))
        ).all()
        for gid, name in sg_rows:
            children_by_guardian.setdefault(gid, []).append(name)

    # Preload assigned RBAC roles
    roles_by_user: dict[int, list[str]] = {}
    if user_ids:
        role_rows = db.execute(
            select(UserRoleAssignment.user_id, Role.code)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserRoleAssignment.school_id == user.school_id,
                UserRoleAssignment.user_id.in_(user_ids),
            )
        ).all()
        for uid, code in role_rows:
            roles_by_user.setdefault(uid, []).append(code)

    items: list[AdminUserAccessItem] = []
    for u in users:
        identifier = None
        subtext = None

        if u.role == UserRole.student and u.id in students_by_user:
            stu = students_by_user[u.id]
            identifier = stu.admission_no
            subtext = enrolment_labels.get(stu.id, "Enrolled Student")
        elif u.role == UserRole.teacher and u.id in employees_by_user:
            emp = employees_by_user[u.id]
            identifier = emp.employee_code
            subtext = emp.department.name if emp.department else emp.designation or "Faculty"
        elif u.role == UserRole.parent and u.id in guardians_by_user:
            g = guardians_by_user[u.id]
            kids = children_by_guardian.get(g.id, [])
            identifier = "Parent / Guardian"
            subtext = f"Ward(s): {', '.join(kids)}" if kids else "No registered wards"
        else:
            identifier = u.role.value.capitalize()
            subtext = u.email or u.login_id

        user_assigned_roles = sorted(roles_by_user.get(u.id, []))
        if not user_assigned_roles and u.role == UserRole.admin:
            user_assigned_roles = ["super_admin"]

        items.append(
            AdminUserAccessItem(
                id=u.id,
                login_id=u.login_id,
                role=u.role,
                full_name=u.full_name,
                phone=u.phone,
                email=u.email,
                is_active=u.is_active,
                app_access_blocked=getattr(u, "app_access_blocked", False),
                token_version=getattr(u, "token_version", 1),
                created_at=u.created_at,
                identifier=identifier,
                subtext=subtext,
                roles=user_assigned_roles,
            )
        )

    return items


@router.post("/{user_id}/block", response_model=UserAccessActionResponse)
def block_user_access(
    user_id: int,
    body: BlockUserRequest,
    user: User = Depends(manager_permission),
    db: Session = Depends(get_db),
) -> UserAccessActionResponse:
    target = db.get(User, user_id)
    if not target or target.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target.id == user.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Administrators cannot block their own account"
        )

    target.app_access_blocked = True
    target.token_version = (target.token_version or 1) + 1

    audit_entry = AuditLog(
        school_id=user.school_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=user.id,
        actor_label=f"{user.full_name} ({user.login_id})",
        entity_type="user",
        entity_id=target.id,
        action=AuditAction.status_change,
        reason=body.reason or "Admin blocked mobile app access",
        before={"app_access_blocked": False},
        after={"app_access_blocked": True, "token_version": target.token_version},
    )
    db.add(audit_entry)
    db.commit()

    return UserAccessActionResponse(
        success=True,
        message=f"Mobile app access for {target.full_name} ({target.login_id}) has been blocked.",
        user_id=target.id,
        app_access_blocked=True,
        token_version=target.token_version,
    )


@router.post("/{user_id}/unblock", response_model=UserAccessActionResponse)
def unblock_user_access(
    user_id: int,
    user: User = Depends(manager_permission),
    db: Session = Depends(get_db),
) -> UserAccessActionResponse:
    target = db.get(User, user_id)
    if not target or target.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    target.app_access_blocked = False

    audit_entry = AuditLog(
        school_id=user.school_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=user.id,
        actor_label=f"{user.full_name} ({user.login_id})",
        entity_type="user",
        entity_id=target.id,
        action=AuditAction.status_change,
        reason="Admin unblocked mobile app access",
        before={"app_access_blocked": True},
        after={"app_access_blocked": False},
    )
    db.add(audit_entry)
    db.commit()

    return UserAccessActionResponse(
        success=True,
        message=f"Mobile app access for {target.full_name} ({target.login_id}) has been restored.",
        user_id=target.id,
        app_access_blocked=False,
        token_version=target.token_version,
    )


@router.post("/{user_id}/reset-password", response_model=UserAccessActionResponse)
def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    user: User = Depends(manager_permission),
    db: Session = Depends(get_db),
) -> UserAccessActionResponse:
    target = db.get(User, user_id)
    if not target or target.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    target.password_hash = hash_password(body.new_password)
    target.token_version = (target.token_version or 1) + 1

    audit_entry = AuditLog(
        school_id=user.school_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=user.id,
        actor_label=f"{user.full_name} ({user.login_id})",
        entity_type="user",
        entity_id=target.id,
        action=AuditAction.update,
        reason="Admin reset user password (invalidated existing sessions)",
        before={"password_reset": False},
        after={"password_reset": True, "token_version": target.token_version},
    )
    db.add(audit_entry)
    db.commit()

    return UserAccessActionResponse(
        success=True,
        message=f"Password for {target.full_name} ({target.login_id}) was reset. All active sessions have been invalidated.",
        user_id=target.id,
        app_access_blocked=target.app_access_blocked,
        token_version=target.token_version,
    )


@router.post("/{user_id}/roles", response_model=UserAccessActionResponse)
def assign_user_role(
    user_id: int,
    body: AssignUserRoleRequest,
    user: User = Depends(manager_permission),
    db: Session = Depends(get_db),
) -> UserAccessActionResponse:
    target = db.get(User, user_id)
    if not target or target.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    role_code = body.role_code.strip().lower()
    role = db.scalar(
        select(Role).where(
            Role.school_id == user.school_id,
            Role.code == role_code,
        )
    )
    if not role:
        rbac.install_system_roles(db, user.school_id)
        role = db.scalar(
            select(Role).where(
                Role.school_id == user.school_id,
                Role.code == role_code,
            )
        )
    if not role:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Role '{body.role_code}' not found"
        )

    rbac.assign(db, target, role, scope_type=ScopeType.school)
    target.token_version = (target.token_version or 1) + 1

    audit_entry = AuditLog(
        school_id=user.school_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=user.id,
        actor_label=f"{user.full_name} ({user.login_id})",
        entity_type="user_role",
        entity_id=target.id,
        action=AuditAction.create,
        reason=f"Assigned RBAC role '{role.name or role.code}'",
        before={},
        after={"role": role.code, "token_version": target.token_version},
    )
    db.add(audit_entry)
    db.commit()

    assigned_roles = list(
        db.scalars(
            select(Role.code)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(
                UserRoleAssignment.school_id == user.school_id,
                UserRoleAssignment.user_id == target.id,
            )
        ).all()
    )

    return UserAccessActionResponse(
        success=True,
        message=f"Role '{role.name or role.code}' assigned to {target.full_name}.",
        user_id=target.id,
        app_access_blocked=target.app_access_blocked,
        token_version=target.token_version,
        roles=assigned_roles,
    )


@router.delete("/{user_id}/roles/{role_code}", response_model=UserAccessActionResponse)
def remove_user_role(
    user_id: int,
    role_code: str,
    user: User = Depends(manager_permission),
    db: Session = Depends(get_db),
) -> UserAccessActionResponse:
    target = db.get(User, user_id)
    if not target or target.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    clean_code = role_code.strip().lower()
    role = db.scalar(
        select(Role).where(
            Role.school_id == user.school_id,
            Role.code == clean_code,
        )
    )
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Role '{role_code}' not found")

    assignments = db.scalars(
        select(UserRoleAssignment).where(
            UserRoleAssignment.school_id == user.school_id,
            UserRoleAssignment.user_id == target.id,
            UserRoleAssignment.role_id == role.id,
        )
    ).all()
    for a in assignments:
        db.delete(a)

    target.token_version = (target.token_version or 1) + 1
    audit_entry = AuditLog(
        school_id=user.school_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=user.id,
        actor_label=f"{user.full_name} ({user.login_id})",
        entity_type="user_role",
        entity_id=target.id,
        action=AuditAction.delete,
        reason=f"Removed RBAC role '{role.name or role.code}'",
        before={"role": role.code},
        after={"token_version": target.token_version},
    )
    db.add(audit_entry)
    db.commit()

    assigned_roles = list(
        db.scalars(
            select(Role.code)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(
                UserRoleAssignment.school_id == user.school_id,
                UserRoleAssignment.user_id == target.id,
            )
        ).all()
    )

    return UserAccessActionResponse(
        success=True,
        message=f"Role '{role.name or role.code}' removed from {target.full_name}.",
        user_id=target.id,
        app_access_blocked=target.app_access_blocked,
        token_version=target.token_version,
        roles=assigned_roles,
    )

