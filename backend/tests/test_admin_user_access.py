from fastapi import status
from sqlalchemy import select

from app.models import User, UserRole


def test_admin_list_users_access(client, admin):
    res = client.get("/admin/users", headers=admin)
    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Every item has access control fields
    item = data[0]
    assert "id" in item
    assert "login_id" in item
    assert "role" in item
    assert "app_access_blocked" in item
    assert "token_version" in item


def test_admin_filter_users_by_role_and_search(client, admin):
    # Filter teachers
    res = client.get("/admin/users?role=teacher", headers=admin)
    assert res.status_code == status.HTTP_200_OK
    teachers = res.json()
    assert len(teachers) > 0
    assert all(t["role"] == "teacher" for t in teachers)

    # Filter students
    res = client.get("/admin/users?role=student", headers=admin)
    assert res.status_code == status.HTTP_200_OK
    students = res.json()
    assert len(students) > 0
    assert all(s["role"] == "student" for s in students)


def test_block_and_unblock_user_workflow(client, admin, db):
    # Find a teacher user
    target = db.scalar(select(User).where(User.role == UserRole.teacher))
    assert target is not None

    # Step 1: Login as teacher initially succeeds
    login_res = client.post(
        "/auth/login",
        json={"role": "teacher", "login_id": target.login_id, "password": "Teacher@123"},
    )
    assert login_res.status_code == status.HTTP_200_OK, login_res.text
    teacher_token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    # Teacher token can query /auth/me
    headers = {"Authorization": f"Bearer {teacher_token}"}
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == status.HTTP_200_OK

    # Step 2: Admin blocks user
    block_res = client.post(
        f"/admin/users/{target.id}/block",
        json={"reason": "Suspended pending investigation"},
        headers=admin,
    )
    assert block_res.status_code == status.HTTP_200_OK, block_res.text
    assert block_res.json()["app_access_blocked"] is True

    # Step 3: Existing active session is immediately rejected (HTTP 403)
    me_after_block = client.get("/auth/me", headers=headers)
    assert me_after_block.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Step 4: Blocked user cannot log in
    new_login = client.post(
        "/auth/login",
        json={"role": "teacher", "login_id": target.login_id, "password": "Teacher@123"},
    )
    assert new_login.status_code == status.HTTP_403_FORBIDDEN

    # Step 5: Blocked user cannot refresh token
    refresh_res = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Step 6: Admin unblocks user
    unblock_res = client.post(
        f"/admin/users/{target.id}/unblock",
        headers=admin,
    )
    assert unblock_res.status_code == status.HTTP_200_OK
    assert unblock_res.json()["app_access_blocked"] is False

    # Step 7: Teacher can now log in again
    post_unblock_login = client.post(
        "/auth/login",
        json={"role": "teacher", "login_id": target.login_id, "password": "Teacher@123"},
    )
    assert post_unblock_login.status_code == status.HTTP_200_OK


def test_admin_reset_password_invalidates_tokens(client, admin, db):
    # Find a student user
    target = db.scalar(select(User).where(User.role == UserRole.student))
    assert target is not None

    # Step 1: Student logs in
    login_res = client.post(
        "/auth/login",
        json={"role": "student", "login_id": target.login_id, "password": "Student@123"},
    )
    assert login_res.status_code == status.HTTP_200_OK
    old_token = login_res.json()["access_token"]

    # Student can call /auth/me with current token
    headers = {"Authorization": f"Bearer {old_token}"}
    assert client.get("/auth/me", headers=headers).status_code == status.HTTP_200_OK

    # Step 2: Admin resets student's password
    new_pass = "NewStudentPass#2026"
    reset_res = client.post(
        f"/admin/users/{target.id}/reset-password",
        json={"new_password": new_pass},
        headers=admin,
    )
    assert reset_res.status_code == status.HTTP_200_OK

    # Step 3: Old token is now invalid because token_version incremented (HTTP 401)
    me_after_reset = client.get("/auth/me", headers=headers)
    assert me_after_reset.status_code == status.HTTP_401_UNAUTHORIZED

    # Step 4: Old password no longer works
    bad_login = client.post(
        "/auth/login",
        json={"role": "student", "login_id": target.login_id, "password": "Student@123"},
    )
    assert bad_login.status_code == status.HTTP_401_UNAUTHORIZED

    # Step 5: New password succeeds
    good_login = client.post(
        "/auth/login",
        json={"role": "student", "login_id": target.login_id, "password": new_pass},
    )
    assert good_login.status_code == status.HTTP_200_OK


def test_non_admin_cannot_manage_user_access(client, teacher, student, parent):
    # Teachers cannot list or block users
    assert client.get("/admin/users", headers=teacher).status_code == status.HTTP_403_FORBIDDEN
    assert client.post("/admin/users/1/block", json={}, headers=teacher).status_code == status.HTTP_403_FORBIDDEN

    # Students cannot list or reset password
    assert client.get("/admin/users", headers=student).status_code == status.HTTP_403_FORBIDDEN
    assert client.post("/admin/users/1/reset-password", json={"new_password": "abc"}, headers=student).status_code == status.HTTP_403_FORBIDDEN

    # Parents cannot list users
    assert client.get("/admin/users", headers=parent).status_code == status.HTTP_403_FORBIDDEN


def test_admin_cannot_block_self(client, admin, db):
    admin_user = db.scalar(select(User).where(User.login_id.startswith("admin@")))
    assert admin_user is not None
    res = client.post(f"/admin/users/{admin_user.id}/block", json={}, headers=admin)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
