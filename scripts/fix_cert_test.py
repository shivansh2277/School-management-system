from pathlib import Path

test_path = Path("backend/tests/test_certificates.py")
code = test_path.read_text(encoding="utf-8")

old_clerk_block = '''    # Create a non-super-admin user who has certificates.issue permission
    from app.models import User
    from app.models.enums import UserRole
    issuer_user = User(
        school_id=1,
        login_id="tc_clerk@sunrisepublic.edu",
        role=UserRole.teacher,
        full_name="TC Issuing Clerk",
        is_active=True,
    )
    issuer_user.set_password("Clerk@123")
    db.add(issuer_user)
    db.flush()

    # Grant certificates.issue to this user
    issue_perm = db.scalar(select(Permission).where(Permission.code == "certificates.issue"))
    role = Role(school_id=1, code="tc_clerk_role", name="TC Clerk Role", is_system=False)
    db.add(role)
    db.flush()
    from app.models.rbac import RolePermission
    db.add(RolePermission(school_id=1, role_id=role.id, permission_id=issue_perm.id))
    db.add(UserRoleAssignment(school_id=1, user_id=issuer_user.id, role_id=role.id, scope_type=ScopeType.school))
    db.flush()

    # Login as tc_clerk
    login_res = client.post("/auth/login", json={"login_id": "tc_clerk@sunrisepublic.edu", "password": "Clerk@123"})
    assert login_res.status_code == 200, login_res.text
    clerk_headers = {"Authorization": f"Bearer {login_res.json()['token']}"}

    # Attempt to issue with dues_override_reason -> must fail with HTTP 403 Forbidden
    res = client.post(
        "/admin/certificates/issue",
        headers=clerk_headers,'''

new_clerk_block = '''    # Grant certificates.issue to a non-admin teacher user
    from app.models import User
    from app.models.enums import UserRole
    from app.models.rbac import RolePermission
    tch = db.scalar(select(User).where(User.role == UserRole.teacher, User.school_id == 1))
    issue_perm = db.scalar(select(Permission).where(Permission.code == "certificates.issue"))
    role = Role(school_id=1, code="tc_teacher_role", name="TC Teacher Role", is_system=False)
    db.add(role)
    db.flush()
    db.add(RolePermission(school_id=1, role_id=role.id, permission_id=issue_perm.id))
    db.add(UserRoleAssignment(school_id=1, user_id=tch.id, role_id=role.id, scope_type=ScopeType.school))
    db.flush()

    # Attempt to issue with dues_override_reason using teacher headers -> must fail with HTTP 403 Forbidden
    res = client.post(
        "/admin/certificates/issue",
        headers=teacher,'''

assert old_clerk_block in code, "old_clerk_block not found"
code = code.replace(old_clerk_block, new_clerk_block, 1)
test_path.write_text(code, encoding="utf-8")
print("Cleanly updated teacher test in test_certificates.py")
