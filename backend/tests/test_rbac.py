"""Roles, permissions and scopes.

The Auditor is the standing test case for whether the permission model is real:
a role that can read everything and write nothing has to be expressible without
touching code (ERP_BLUEPRINT §3.5).
"""

from sqlalchemy import select

from app.core.permissions import SYSTEM_ROLES
from app.core.security import hash_password
from app.models import Role, ScopeType, User, UserRole, UserRoleAssignment
from app.services import rbac
from tests.conftest import auth


def make_user(db, login_id, role=UserRole.admin, name="Test User"):
    u = User(
        school_id=1,
        role=role,
        login_id=login_id,
        password_hash=hash_password("Test@123"),
        full_name=name,
    )
    db.add(u)
    db.flush()
    return u


def role_by_code(db, code):
    return db.scalar(select(Role).where(Role.school_id == 1, Role.code == code))


def token_for(client, login_id, role="admin"):
    r = client.post(
        "/auth/login",
        json={"role": role, "login_id": login_id, "password": "Test@123"},
    )
    assert r.status_code == 200, r.text
    return auth(r.json()["access_token"])


def test_every_system_role_is_installed(db):
    codes = set(db.scalars(select(Role.code).where(Role.school_id == 1)))
    assert codes == {code for code, _, _ in SYSTEM_ROLES}


def test_an_auditor_can_read_but_cannot_write(client, db):
    """If this passes, the permission model is doing real work. Under v0 it was
    not expressible at all: there were four roles and admin could do everything."""
    user = make_user(db, "auditor@sunrisepublic.edu", name="Auditor")
    rbac.assign(db, user, role_by_code(db, "auditor"))
    db.flush()
    headers = token_for(client, "auditor@sunrisepublic.edu")

    assert client.get("/admin/students", headers=headers).status_code == 200
    assert client.get("/admin/classes", headers=headers).status_code == 200

    denied = client.post(
        "/admin/classes",
        json={"class_name": "7", "section": "A"},
        headers=headers,
    )
    assert denied.status_code == 403
    assert "academics.class.write" in denied.json()["detail"]


def test_a_fee_collector_cannot_void_what_they_collect(client, db):
    """Segregation of duties: whoever takes the money must not be able to
    cancel the record of it."""
    authz = rbac.authz_for(
        db, make_user(db, "cashier@sunrisepublic.edu", name="Cashier")
    )
    assert authz.codes == []

    user = db.scalar(select(User).where(User.login_id == "cashier@sunrisepublic.edu"))
    rbac.assign(db, user, role_by_code(db, "fee_collector"))
    db.flush()
    authz = rbac.authz_for(db, user)

    assert authz.can("fees.payment.collect")
    assert not authz.can("fees.payment.void")
    assert not authz.can("fees.concession.approve")


def test_a_user_with_no_role_can_do_nothing(client, db):
    make_user(db, "nobody@sunrisepublic.edu", name="No Role")
    db.flush()
    headers = token_for(client, "nobody@sunrisepublic.edu")
    assert client.get("/admin/students", headers=headers).status_code == 403


def test_a_guardian_cannot_read_the_admin_roster(client, parent):
    """A guardian and an office clerk both hold students.profile.read. The
    guardian holds it over their own children only, so the school-wide roster
    stays closed to them."""
    assert client.get("/admin/students", headers=parent).status_code == 403
    # ...while their own children remain readable.
    assert client.get("/parent/children", headers=parent).status_code == 200


def test_class_teacher_is_a_scoped_grant_not_a_role(db, ids):
    """"Class Employee" is the teacher role plus authority over one section."""
    teacher_user = db.scalar(select(User).where(User.login_id == "TCH001"))
    grants = db.scalars(
        select(UserRoleAssignment).where(UserRoleAssignment.user_id == teacher_user.id)
    ).all()

    scoped = [g for g in grants if g.scope_type is ScopeType.class_section]
    assert scoped, "TCH001 class-teaches 10-A and should hold a section-scoped grant"
    assert scoped[0].scope_id == ids["section_10a"]

    authz = rbac.authz_for(db, teacher_user)
    # The school-wide teacher grant means the permission is not restricted...
    assert authz.can("attendance.record.mark")
    # ...and the section grant is what a scope-aware caller would narrow by.
    assert ids["section_10a"] in (
        authz.scope_ids("attendance.record.mark", ScopeType.class_section) or []
    ) or authz.is_school_wide("attendance.record.mark")


def test_scope_ids_distinguishes_unrestricted_from_none(db):
    """None means school-wide; [] means the permission is not held at all.
    Treating them the same would silently widen a scoped grant."""
    user = make_user(db, "scoped@sunrisepublic.edu", name="Scoped")
    rbac.assign(
        db,
        user,
        role_by_code(db, "teacher"),
        scope_type=ScopeType.class_section,
        scope_id=42,
    )
    db.flush()
    authz = rbac.authz_for(db, user)

    assert authz.scope_ids("attendance.record.mark", ScopeType.class_section) == [42]
    assert not authz.is_school_wide("attendance.record.mark")
    assert authz.scope_ids("fees.payment.void", ScopeType.class_section) == []


def test_me_reports_permissions_for_the_client_to_render_from(client, admin):
    body = client.get("/auth/me", headers=admin).json()
    assert "students.profile.read" in body["permissions"]
    assert "super_admin" in body["roles"]
    assert body["school_code"] == "SPS"
    assert body["academic_year"] == "2025-26"


def test_installing_system_roles_twice_is_idempotent(db):
    before = db.scalar(
        select(Role).where(Role.school_id == 1, Role.code == "auditor")
    ).id
    rbac.install_system_roles(db, 1)
    after = db.scalars(select(Role).where(Role.school_id == 1, Role.code == "auditor")).all()
    assert len(after) == 1 and after[0].id == before


def test_permission_catalogue_is_shared_but_roles_are_per_school(db):
    """The vocabulary belongs to the software; the grants belong to a school."""
    from app.models import Permission, School, SchoolStatus

    other = School(code="OTH2", name="Another School", status=SchoolStatus.active)
    db.add(other)
    db.flush()
    permissions_before = db.scalars(select(Permission.code)).all()

    rbac.install_system_roles(db, other.id)

    assert db.scalars(select(Permission.code)).all() == permissions_before
    assert db.scalar(
        select(Role).where(Role.school_id == other.id, Role.code == "auditor")
    ) is not None


def test_scheduling_an_exam_paper_needs_the_write_permission(client, teacher, ids):
    """A write must not be gated on a read.

    `POST /admin/exams/{id}/schedule` declared no permission of its own and so
    inherited the router's `admin_only`, which is `exam.definition.read`.
    Anyone who could look at the exam calendar could add papers to it: a
    teacher holding read and not write got 403 from `POST /admin/exams` and
    201 from this route, which is the whole bug in two status codes.

    Pinned here rather than in test_assessment.py because the defect is about
    the permission model, not about exams - the same omission on any router
    with a read-scoped `admin_only` would be the same class of hole.
    """
    exam = client.get("/admin/exams", headers=teacher)
    assert exam.status_code == 200, exam.text
    exam_id = exam.json()[0]["id"]

    r = client.post(
        f"/admin/exams/{exam_id}/schedule",
        headers=teacher,
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "exam_date": "2026-11-02",
            "max_marks": "100",
        },
    )
    assert r.status_code == 403, (
        f"a teacher without exam.definition.write scheduled a paper: {r.status_code} {r.text}"
    )
