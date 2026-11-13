"""academic coordinator role registration and assignment

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f0
Create Date: 2026-10-31 01:15:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.services import rbac
from app.models import School, User, Role, UserRoleAssignment, ScopeType

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a2b3c4d5e6f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)

    # 1. Sync permissions catalogue and install system roles across all schools
    rbac.sync_catalogue(session)
    schools = session.scalars(sa.select(School)).all()
    for school in schools:
        rbac.install_system_roles(session, school.id)

    # 2. Assign academic_coordinator role to coordinator@sunrisepublic.edu if present
    coordinators = session.scalars(
        sa.select(User).where(User.login_id.in_(["coordinator@sunrisepublic.edu", "coordinator"]))
    ).all()
    for coord in coordinators:
        role = session.scalar(
            sa.select(Role).where(Role.school_id == coord.school_id, Role.code == "academic_coordinator")
        )
        if role:
            # Clear old role assignments (such as super_admin)
            session.execute(
                sa.delete(UserRoleAssignment).where(UserRoleAssignment.user_id == coord.id)
            )
            session.flush()
            rbac.assign(session, coord, role, scope_type=ScopeType.school)

    session.commit()


def downgrade() -> None:
    pass
