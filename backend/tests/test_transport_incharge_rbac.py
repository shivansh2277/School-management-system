"""Strict RBAC tests for the Transport In-Charge role.
Verifies operational access to transport routes, vehicles, expiring papers,
and strict 403 Forbidden blocks for admin settings, accounts/fees, admissions, payroll, and grading.
"""
from fastapi import status


def test_transport_incharge_allowed_operations(client, transport_incharge):
    # Can view transport routes
    res = client.get("/admin/transport/routes", headers=transport_incharge)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert isinstance(res.json(), list)

    # Can view transport vehicles
    res = client.get("/admin/transport/vehicles", headers=transport_incharge)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert isinstance(res.json(), list)

    # Can view expiring compliance papers
    res = client.get("/admin/transport/expiring", headers=transport_incharge)
    assert res.status_code == status.HTTP_200_OK, res.text

    # Can view fee slabs
    res = client.get("/admin/transport/slabs", headers=transport_incharge)
    assert res.status_code == status.HTTP_200_OK, res.text

    # Can read notices
    res = client.get("/admin/notices", headers=transport_incharge)
    assert res.status_code == status.HTTP_200_OK, res.text


def test_transport_incharge_strictly_forbidden_departments(client, transport_incharge, hr_enabled):
    # 1. Admin System Settings & Configuration (Strictly 403)
    res = client.get("/admin/settings", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/configuration", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Financial & Fee Invoices (Strictly 403)
    res = client.get("/admin/fees/invoices", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.post("/admin/fees/invoices/generate", json={"class_names": ["10"]}, headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/fees/defaulters", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Admission Applications & Cycles (Strictly 403)
    res = client.get("/admin/admission/cycles", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/admission/applications", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 4. HR Payroll (Strictly 403)
    res = client.get("/admin/payroll/runs", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 5. Academic Grading & Schemes (Strictly 403)
    res = client.get("/admin/grading-scales", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 6. People & Students (Strictly 403)
    res = client.get("/admin/students", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 7. Academics & Classes (Strictly 403)
    res = client.get("/admin/classes", headers=transport_incharge)
    assert res.status_code == status.HTTP_403_FORBIDDEN

