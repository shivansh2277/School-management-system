"""Tests for bank disbursal export endpoint in payroll API."""

import pytest
from app.services import payroll

YEAR = 2026
MONTH = 4


@pytest.fixture()
def approved_run(db, admin_user):
    run = payroll.open_run(db, admin_user, year=YEAR, month=MONTH)
    payroll.calculate(db, admin_user, run)
    payroll.approve(db, admin_user, run)
    return run


def test_bank_disbursal_json(client, admin, hr_enabled, approved_run):
    r = client.get(
        f"/admin/payroll/runs/{approved_run.id}/bank-disbursal",
        headers=admin,
    )
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) > 0
    first = rows[0]
    assert "employee_code" in first
    assert "beneficiary_name" in first
    assert "bank_name" in first
    assert "bank_account_no" in first
    assert "bank_ifsc" in first
    assert "net_amount" in first
    assert "narration" in first
    assert float(first["net_amount"]) > 0


def test_bank_disbursal_csv(client, admin, hr_enabled, approved_run):
    r = client.get(
        f"/admin/payroll/runs/{approved_run.id}/bank-disbursal?format=csv",
        headers=admin,
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in r.headers["content-disposition"]
    text = r.text
    assert "Employee Code,Beneficiary Name,Bank Name,Account Number,IFSC Code,Net Amount (INR),Narration" in text
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    assert len(lines) > 1  # Header + at least one staff row
