import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.db import SessionLocal, engine
from sqlalchemy import select, delete, text
from app.services import rbac
from app.models import School, User, Role, UserRoleAssignment, ScopeType

db = SessionLocal()
try:
    rbac.sync_catalogue(db)
    schools = db.scalars(select(School)).all()
    for s in schools:
        installed = rbac.install_system_roles(db, s.id)
        print(f"Installed roles for school {s.id}: count={len(installed)}")
        assert "academic_coordinator" in installed, "academic_coordinator role missing in installed"

    coordinators = db.scalars(
        select(User).where(User.login_id.in_(["coordinator@sunrisepublic.edu", "coordinator"]))
    ).all()
    for c in coordinators:
        role = db.scalar(
            select(Role).where(Role.school_id == c.school_id, Role.code == "academic_coordinator")
        )
        assert role is not None, "academic_coordinator role must exist"
        db.execute(delete(UserRoleAssignment).where(UserRoleAssignment.user_id == c.id))
        db.flush()
        rbac.assign(db, c, role, scope_type=ScopeType.school)
        print(f"Assigned academic_coordinator role to user {c.login_id} (ID: {c.id})")

    db.commit()
    with engine.connect() as conn:
        conn.execute(text("UPDATE alembic_version SET version_num = 'b3c4d5e6f7a8'"))
        conn.commit()
        print("Updated alembic_version to b3c4d5e6f7a8")
finally:
    db.close()
