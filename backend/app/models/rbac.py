"""Roles, permissions and scopes.

v0 had four hardcoded roles and `require_role(UserRole.admin)`. A real school
needs ten to twenty: a Principal who sees everything but changes little, an
Accountant confined to Fees, an Auditor who can read everything and write
nothing, a Class Teacher who is a Subject Teacher plus extra rights over one
section (ERP_BLUEPRINT §3.5).

Three layers, kept deliberately distinct:

  authentication  who are you                 core/deps.py
  permission      may you do this at all      require_permission(), at the route
  scope           over which rows             services/scoping.py, in the service

`users.role` is retained as the *primary* role — it drives the login tab and the
role profile tables — while these tables decide what that user may actually do.
"""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantBase, TimestampedBase, enum_col
from app.models.enums import ScopeType


class Permission(TimestampedBase):
    """A thing that can be done, named `module.resource.action`.

    Global rather than per-tenant: the vocabulary is defined by the software,
    not by a school. Which school grants what is `role_permissions`.
    """

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    module: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Permission {self.code}>"


class Role(TenantBase):
    """A named set of permissions. System roles ship with the product and cannot
    be deleted; a school may copy one and adjust it."""

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_role_code"),)

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Role {self.code}>"


class RolePermission(TenantBase):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.id"), nullable=False, index=True
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("permissions.id"), nullable=False, index=True
    )


class UserRoleAssignment(TenantBase):
    """A user holds a role, optionally narrowed to part of the school.

    A Class Teacher is not a separate role: it is the teacher role plus a
    `class_section`-scoped grant. Grants are additive and there are no deny
    rules — deny-overrides is where permission bugs hide, and no school
    requirement needs it.
    """

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", "scope_type", "scope_id", name="uq_user_role_scope"
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.id"), nullable=False, index=True
    )
    scope_type: Mapped[ScopeType] = enum_col(
        ScopeType, nullable=False, default=ScopeType.school
    )
    # Null for school-wide grants; otherwise the id of the section, department
    # or academic year the grant is limited to.
    scope_id: Mapped[int | None] = mapped_column(BigInteger)
