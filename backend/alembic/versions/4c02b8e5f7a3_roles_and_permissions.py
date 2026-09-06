"""roles and permissions

Replaces four hardcoded roles with a modelled permission system
(ERP_BLUEPRINT §3.5). Existing accounts are backfilled onto the system role
matching their `users.role`, so nobody loses access when this runs.

`users.role` is deliberately kept: it drives the login tab and the role profile
tables. What changes is that it no longer decides what a user may *do*.

Revision ID: 4c02b8e5f7a3
Revises: 3a91c6d40e12
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.permissions import LEGACY_ROLE_MAP, PERMISSIONS, SYSTEM_ROLES

revision: str = "4c02b8e5f7a3"
down_revision: str | None = "3a91c6d40e12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCOPE = sa.Enum(
    "school",
    "academic_year",
    "class_section",
    "department",
    "self",
    name="scopetype",
    native_enum=False,
)


def _ts():
    return [
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "permissions",
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("module", sa.String(40), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("description", sa.Text()),
        *_ts(),
    )
    op.create_table(
        "roles",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_ts(),
        sa.UniqueConstraint("school_id", "code", name="uq_role_code"),
    )
    op.create_index("ix_roles_school_id", "roles", ["school_id"])
    op.create_table(
        "role_permissions",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("role_id", sa.BigInteger(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column(
            "permission_id", sa.BigInteger(), sa.ForeignKey("permissions.id"), nullable=False
        ),
        *_ts(),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_school_id", "role_permissions", ["school_id"])
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index(
        "ix_role_permissions_permission_id", "role_permissions", ["permission_id"]
    )
    op.create_table(
        "user_roles",
        sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role_id", sa.BigInteger(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("scope_type", _SCOPE, nullable=False, server_default="school"),
        sa.Column("scope_id", sa.BigInteger()),
        *_ts(),
        sa.UniqueConstraint(
            "user_id", "role_id", "scope_type", "scope_id", name="uq_user_role_scope"
        ),
    )
    op.create_index("ix_user_roles_school_id", "user_roles", ["school_id"])
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    # ------------------------------------------------------------- catalogue
    ins = sa.text(
        "INSERT INTO permissions (code, module, action, description, created_at,"
        " updated_at) VALUES (:code, :module, :action, :description,"
        " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )
    for code, description in PERMISSIONS:
        bind.execute(
            ins,
            {
                "code": code,
                "module": code.partition(".")[0],
                "action": code.rsplit(".", 1)[1],
                "description": description,
            },
        )
    perm_ids = dict(bind.execute(sa.text("SELECT code, id FROM permissions")).all())

    # ------------------------------------- a copy of the system roles per school
    for school_id in [
        r[0] for r in bind.execute(sa.text("SELECT id FROM schools")).all()
    ]:
        role_ids = {}
        for code, name, granted in SYSTEM_ROLES:
            bind.execute(
                sa.text(
                    "INSERT INTO roles (school_id, code, name, is_system, created_at,"
                    " updated_at) VALUES (:sid, :code, :name, 1, CURRENT_TIMESTAMP,"
                    " CURRENT_TIMESTAMP)"
                ),
                {"sid": school_id, "code": code, "name": name},
            )
            role_id = bind.execute(
                sa.text(
                    "SELECT id FROM roles WHERE school_id = :sid AND code = :code"
                ),
                {"sid": school_id, "code": code},
            ).scalar_one()
            role_ids[code] = role_id
            # dict.fromkeys: a code may appear in both READ_ONLY and a role's
            # explicit list.
            for pcode in dict.fromkeys(granted):
                bind.execute(
                    sa.text(
                        "INSERT INTO role_permissions (school_id, role_id,"
                        " permission_id, created_at, updated_at) VALUES (:sid, :rid,"
                        " :pid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    ),
                    {"sid": school_id, "rid": role_id, "pid": perm_ids[pcode]},
                )

        # ------------------------------------------------ backfill existing users
        users = bind.execute(
            sa.text("SELECT id, role FROM users WHERE school_id = :sid"),
            {"sid": school_id},
        ).all()
        for user_id, legacy in users:
            code = LEGACY_ROLE_MAP.get(legacy)
            if code is None:
                continue
            # Students and guardians hold their permissions over their own
            # records only; school-wide would open the admin roster to a parent.
            scope = "self" if code in ("student", "guardian") else "school"
            bind.execute(
                sa.text(
                    "INSERT INTO user_roles (school_id, user_id, role_id, scope_type,"
                    " created_at, updated_at) VALUES (:sid, :uid, :rid, :scope,"
                    " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {
                    "sid": school_id,
                    "uid": user_id,
                    "rid": role_ids[code],
                    "scope": scope,
                },
            )

        # Class teachers get the section-scoped grant that "Class Teacher"
        # actually means.
        for section_id, teacher_user_id in bind.execute(
            sa.text(
                "SELECT cs.id, t.user_id FROM class_sections cs"
                " JOIN teachers t ON t.id = cs.class_teacher_id"
                " WHERE cs.school_id = :sid"
            ),
            {"sid": school_id},
        ).all():
            bind.execute(
                sa.text(
                    "INSERT INTO user_roles (school_id, user_id, role_id, scope_type,"
                    " scope_id, created_at, updated_at) VALUES (:sid, :uid, :rid,"
                    " 'class_section', :scope_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {
                    "sid": school_id,
                    "uid": teacher_user_id,
                    "rid": role_ids["teacher"],
                    "scope_id": section_id,
                },
            )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
