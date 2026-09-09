"""Resolving what a user may do, and where.

Permission answers "may you do this at all" and is checked at the route.
Scope answers "over which rows" and stays in `services/scoping.py`, which is
where v0 already put it — the placement was right, only the inputs change.
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.permissions import PERMISSIONS, SYSTEM_ROLES
from app.models import (
    Permission,
    Role,
    RolePermission,
    ScopeType,
    User,
    UserRoleAssignment,
)


@dataclass(frozen=True)
class Grant:
    """One permission, and how far it reaches."""

    code: str
    scope_type: ScopeType
    scope_id: int | None


class Authz:
    """A user's resolved authority, built once per request."""

    def __init__(self, user: User, grants: list[Grant]):
        self.user = user
        self.grants = grants
        self._codes = {g.code for g in grants}

    def can(self, code: str) -> bool:
        return code in self._codes

    def require(self, code: str) -> None:
        if not self.can(code):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"This role does not have permission: {code}",
            )

    def scope_ids(self, code: str, scope_type: ScopeType) -> list[int] | None:
        """Ids this permission is limited to, or None for unrestricted.

        None means school-wide — not "nothing". A caller that treats an empty
        list and None the same would silently widen a scoped grant.
        """
        relevant = [g for g in self.grants if g.code == code]
        if not relevant:
            return []
        if any(g.scope_type is ScopeType.school for g in relevant):
            return None
        return [
            g.scope_id
            for g in relevant
            if g.scope_type is scope_type and g.scope_id is not None
        ]

    def is_school_wide(self, code: str) -> bool:
        """True when this permission is held without a scope restriction."""
        return any(
            g.code == code and g.scope_type is ScopeType.school for g in self.grants
        )

    @property
    def codes(self) -> list[str]:
        return sorted(self._codes)


def grants_for(db: Session, user: User) -> list[Grant]:
    rows = db.execute(
        select(
            Permission.code,
            UserRoleAssignment.scope_type,
            UserRoleAssignment.scope_id,
        )
        .join(Role, Role.id == UserRoleAssignment.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.school_id == user.school_id,
        )
    ).all()
    return [Grant(code=c, scope_type=st, scope_id=sid) for c, st, sid in rows]


def authz_for(db: Session, user: User) -> Authz:
    return Authz(user, grants_for(db, user))


def get_authz(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Authz:
    return authz_for(db, user)


def require_permission(*codes: str, school_wide: bool = False):
    """Route dependency. Holding any one of `codes` is enough.

    `school_wide=True` additionally demands the grant be unscoped. A guardian
    and an office clerk both hold `students.profile.read`, but the guardian
    holds it only over their own children; without this, the guardian's grant
    would open the admin roster of every student in the school.

    Returns the User so existing handlers that take `user: User = Depends(...)`
    keep working unchanged.
    """

    def _dep(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        authz = authz_for(db, user)
        ok = any(
            authz.can(c) and (not school_wide or authz.is_school_wide(c)) for c in codes
        )
        if not ok:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"This role does not have permission: {' or '.join(codes)}",
            )
        return user

    return _dep


def sync_catalogue(db: Session) -> None:
    """Insert any permission defined in code but missing from the database.

    Additive only: a permission that disappears from the catalogue keeps its
    row and its grants, so a rename cannot silently strip a school's roles.
    """
    existing = set(db.scalars(select(Permission.code)))
    for code, description in PERMISSIONS:
        if code in existing:
            continue
        module, _, action = code.partition(".")
        db.add(
            Permission(
                code=code,
                module=module,
                action=code.rsplit(".", 1)[1],
                description=description,
            )
        )
    db.flush()


def install_system_roles(db: Session, school_id: int) -> dict[str, Role]:
    """Create this school's copy of the roles that ship with the product."""
    sync_catalogue(db)
    perms = {p.code: p for p in db.scalars(select(Permission))}
    out: dict[str, Role] = {}

    for code, name, granted in SYSTEM_ROLES:
        role = db.scalar(
            select(Role).where(Role.school_id == school_id, Role.code == code)
        )
        if role is None:
            role = Role(school_id=school_id, code=code, name=name, is_system=True)
            db.add(role)
            db.flush()
        held = set(
            db.scalars(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == role.id)
            )
        )
        # dict.fromkeys de-duplicates while keeping order: a code can appear
        # both in READ_ONLY and in a role's explicit list.
        for pcode in dict.fromkeys(granted):
            if pcode in held:
                continue
            db.add(
                RolePermission(
                    school_id=school_id,
                    role_id=role.id,
                    permission_id=perms[pcode].id,
                )
            )
        out[code] = role
    db.flush()
    return out


def assign(
    db: Session,
    user: User,
    role: Role,
    scope_type: ScopeType = ScopeType.school,
    scope_id: int | None = None,
) -> UserRoleAssignment:
    existing = db.scalar(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role_id == role.id,
            UserRoleAssignment.scope_type == scope_type,
            UserRoleAssignment.scope_id == scope_id,
        )
    )
    if existing is not None:
        return existing
    row = UserRoleAssignment(
        school_id=user.school_id,
        user_id=user.id,
        role_id=role.id,
        scope_type=scope_type,
        scope_id=scope_id,
    )
    db.add(row)
    db.flush()
    return row
