"""Strict RBAC tests for the dedicated Accounts department role.
Verifies full financial operations (invoices, defaulters, plans, periods, payroll, fee reports)
and strict 403 Forbidden boundaries for admin configuration, admissions, transport setup, and academic grading.
"""
from fastapi import status


def test_accounts_role_allowed_financial_operations(client, accounts_user, hr_enabled):
    # 1. Fees management
    res = client.get("/admin/fees/invoices", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text

    res = client.get("/admin/fees/defaulters", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text

    res = client.get("/admin/fees/plans", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text

    res = client.get("/admin/fees/periods", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text

    # 2. Payroll operations
    res = client.get("/admin/payroll/runs", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text

    res = client.get("/admin/payroll/components", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text

    # 3. Reports library and fee collection report
    res = client.get("/admin/reports", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text
    reports_data = res.json()
    available_codes = [r["code"] for r in reports_data.get("reports", [])]
    assert "fees.collection" in available_codes or "fees.defaulters" in available_codes

    res = client.get("/admin/reports/fees.collection?year=2026", headers=accounts_user)
    assert res.status_code == status.HTTP_200_OK, res.text


def test_accounts_role_strictly_forbidden_departments(client, accounts_user):
    # 1. Admin System Settings & Configuration (Strictly 403)
    res = client.get("/admin/settings", headers=accounts_user)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/admin/configuration", headers=accounts_user)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.put("/admin/configuration", json={"module": "transport", "enabled": False}, headers=accounts_user)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Admission Processing (Strictly 403)
    res = client.post(
        "/admin/admission/cycles",
        json={"academic_year_id": 1, "name": "Hack Cycle", "starts_on": "2026-04-01", "ends_on": "2026-05-01"},
        headers=accounts_user,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Transport Setup (Strictly 403)
    res = client.post(
        "/admin/transport/routes",
        json={"code": "R-NEW", "name": "Illegal Route", "distance_km": 10},
        headers=accounts_user,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 4. Academic Grading (Strictly 403)
    res = client.get("/admin/grading-scales", headers=accounts_user)
    assert res.status_code == status.HTTP_403_FORBIDDEN
