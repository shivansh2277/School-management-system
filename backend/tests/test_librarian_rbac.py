"""Strict RBAC tests for the dedicated Librarian role.
Verifies library operations (catalog, borrower lookup, loans, notices)
and strict 403 Forbidden boundaries for admissions, fees, transport, staff,
attendance, payroll, and administrative settings.
Also tests user role assignment via the Admin User Access API.
"""
from fastapi import status
from sqlalchemy import select

from app.models import Role, User, UserRoleAssignment


def test_librarian_allowed_library_operations(client, librarian):
    # 1. Library catalog books
    res = client.get("/admin/library/books", headers=librarian)
    assert res.status_code == status.HTTP_200_OK, res.text

    # 2. Borrower lookup
    res = client.get("/admin/library/borrowers/lookup?q=Rahul", headers=librarian)
    assert res.status_code == status.HTTP_200_OK, res.text

    # 3. Loans list
    res = client.get("/admin/library/loans", headers=librarian)
    assert res.status_code == status.HTTP_200_OK, res.text

    # 4. Notices / announcements reading
    res = client.get("/admin/notices", headers=librarian)
    assert res.status_code == status.HTTP_200_OK, res.text


def test_librarian_strictly_forbidden_unrelated_modules(client, librarian, hr_enabled):
    # 1. Admissions
    res = client.get("/admin/admission/enquiries", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/admission/applications", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Fees
    res = client.get("/admin/fees/invoices", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Transport
    res = client.get("/admin/transport/routes", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 4. HR & Staff
    res = client.get("/admin/departments", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 5. Attendance administration
    res = client.get("/admin/attendance/summary", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 6. Payroll
    res = client.get("/admin/payroll/runs", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 7. Students profile directory
    res = client.get("/admin/students", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 8. User access security
    res = client.get("/admin/users", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 9. Settings
    res = client.get("/admin/settings", headers=librarian)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_assign_and_remove_librarian_role(client, admin, db):
    # Find a user to assign role to (e.g. receptionist or another user)
    target = db.scalar(select(User).where(User.login_id == "receptionist@sunrisepublic.edu"))
    assert target is not None

    # 1. Assign librarian role
    res = client.post(
        f"/admin/users/{target.id}/roles",
        json={"role_code": "librarian"},
        headers=admin,
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert data["success"] is True
    assert "librarian" in data["roles"]

    # 2. Verify in User Access list
    res_list = client.get(f"/admin/users?search=receptionist", headers=admin)
    assert res_list.status_code == status.HTTP_200_OK
    user_item = next((u for u in res_list.json() if u["id"] == target.id), None)
    assert user_item is not None
    assert "librarian" in user_item["roles"]

    # 3. Remove librarian role
    res_del = client.delete(
        f"/admin/users/{target.id}/roles/librarian",
        headers=admin,
    )
    assert res_del.status_code == status.HTTP_200_OK
    del_data = res_del.json()
    assert del_data["success"] is True
    assert "librarian" not in del_data["roles"]


def test_librarian_login_both_emails(client):
    # Both librarian@sunrisepublic.edu and library@sunrisepublic.edu authenticate cleanly
    for email in ("librarian@sunrisepublic.edu", "library@sunrisepublic.edu"):
        res = client.post(
            "/auth/login",
            json={"role": "admin", "login_id": email, "password": "Admin@123"},
        )
        assert res.status_code == status.HTTP_200_OK, f"Failed for {email}: {res.text}"
        token = res.json()["access_token"]
        assert token

        # Verify /auth/me returns librarian role
        me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == status.HTTP_200_OK
        data = me_res.json()
        assert "librarian" in data["roles"]
        assert "library.read" in data["permissions"]
        assert "library.manage" in data["permissions"]
