"""Payroll setup, runs, payslips and the statutory registers (§5.3.3).

Everything here is behind `payroll.*` permissions rather than `hr.*`: §5.3.8
gives the Accountant payroll and nothing else of HR, and the HR Manager staff
records and not the money.
"""

import csv
from datetime import date as Date
from decimal import Decimal
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import PayrollRun, Payslip, SalaryComponent, User
from app.services import hr
from app.services import payroll as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/payroll", tags=["admin"],
    dependencies=[Depends(module_enabled("hr"))],
)
reader = require_permission("payroll.run.read", school_wide=True)
setup = require_permission("payroll.setup.manage", school_wide=True)
runner = require_permission("payroll.run.manage", school_wide=True)
approver = require_permission("payroll.run.approve", school_wide=True)


class ComponentIn(BaseModel):
    value: Decimal | None = Field(default=None, ge=0)
    active: bool | None = None
    sequence: int | None = None
    applies_below_gross: Decimal | None = None


class StructureIn(BaseModel):
    employee_id: int
    effective_from: Date
    monthly_gross: Decimal = Field(gt=0)
    # Per-employee overrides by component code, e.g. {"TDS": "2500"}.
    overrides: dict[str, Decimal] | None = None
    note: str | None = None


class RunIn(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    supplementary: bool = False


class NoteIn(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


def _run(db: Session, user: User, run_id: int) -> PayrollRun:
    row = db.get(PayrollRun, run_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payroll run not found")
    return row


# --- setup -----------------------------------------------------------------


@router.get("/components")
def components(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    """Every component, active or not — a school switching DA on needs to see
    the one that is off."""
    rows = db.scalars(
        select(SalaryComponent)
        .where(SalaryComponent.school_id == user.school_id)
        .order_by(SalaryComponent.sequence, SalaryComponent.code)
    )
    return [
        {
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "type": c.type,
            "calculation": c.calculation,
            "value": c.value,
            "applies_below_gross": c.applies_below_gross,
            "taxable": c.taxable,
            "statutory": c.statutory,
            "active": c.active,
            "sequence": c.sequence,
        }
        for c in rows
    ]


@router.put("/components/{component_id}")
def update_component(
    component_id: int,
    body: ComponentIn,
    user: User = Depends(setup),
    db: Session = Depends(get_db),
) -> dict:
    """Change a rate, or switch a component on or off.

    This is §3.16's whole point: a school that pays HRA at 30% edits a number
    here rather than asking for a code change.
    """
    row = db.get(SalaryComponent, component_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Component not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    return {"id": row.id, "code": row.code, "value": row.value, "active": row.active}


@router.get("/structures/{employee_id}")
def structure(
    employee_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict | None:
    employee = hr.owned(db, user, employee_id)
    row = svc.active_structure(db, employee.id)
    if row is None:
        return None
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "effective_from": row.effective_from,
        "monthly_gross": row.monthly_gross,
        "note": row.note,
    }


@router.post("/structures", status_code=status.HTTP_201_CREATED)
def set_structure(
    body: StructureIn, user: User = Depends(setup), db: Session = Depends(get_db)
) -> dict:
    """Put somebody on new terms. Supersedes rather than edits."""
    employee = hr.owned(db, user, body.employee_id)
    row = svc.set_structure(
        db,
        user,
        employee,
        effective_from=body.effective_from,
        monthly_gross=body.monthly_gross,
        overrides=body.overrides,
        note=body.note,
    )
    db.commit()
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "monthly_gross": row.monthly_gross,
        "effective_from": row.effective_from,
    }


@router.get("/preview/{employee_id}")
def preview(
    employee_id: int,
    year: int = Query(),
    month: int = Query(ge=1, le=12),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    """What this person's payslip would say, without running anything.

    Uses the same `compute()` the run does, so a preview and the real thing
    cannot drift.
    """
    from app.services import attendance as att
    from app.services import staff_attendance

    employee = hr.owned(db, user, employee_id)
    structure = svc.active_structure(db, employee.id)
    if structure is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{employee.user.full_name} has no salary structure",
        )
    start, end = svc.month_range(year, month)
    return svc.compute(
        db,
        structure,
        working_days=att.working_days(db, user.school_id, start, end),
        lop_days=staff_attendance.lop_days(db, employee, start, end),
    )


# --- runs ------------------------------------------------------------------


@router.get("/runs")
def list_runs(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(PayrollRun)
        .where(PayrollRun.school_id == user.school_id)
        .order_by(PayrollRun.year.desc(), PayrollRun.month.desc(), PayrollRun.run_no)
    )
    return [
        {
            "id": r.id,
            "month": f"{r.month:02d}/{r.year}",
            "run_no": r.run_no,
            "is_supplementary": r.is_supplementary,
            "status": r.status,
            "working_days": r.working_days,
            "approved_at": r.approved_at,
            "paid_at": r.paid_at,
            **svc.totals(db, r),
        }
        for r in rows
    ]


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def open_run(
    body: RunIn, user: User = Depends(runner), db: Session = Depends(get_db)
) -> dict:
    row = svc.open_run(
        db, user, year=body.year, month=body.month, supplementary=body.supplementary
    )
    db.commit()
    return {
        "id": row.id,
        "month": f"{row.month:02d}/{row.year}",
        "run_no": row.run_no,
        "status": row.status,
        "working_days": row.working_days,
    }


@router.post("/runs/{run_id}/calculate")
def calculate(
    run_id: int, user: User = Depends(runner), db: Session = Depends(get_db)
) -> dict:
    result = svc.calculate(db, user, _run(db, user, run_id))
    db.commit()
    run = result["run"]
    return {
        "id": run.id,
        "status": run.status,
        **svc.totals(db, run),
        # Named, not silently skipped: a missing structure is an oversight, and
        # a zero payslip would hide it.
        "without_structure": result["without_structure"],
    }


@router.post("/runs/{run_id}/approve")
def approve(
    run_id: int,
    body: NoteIn,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> dict:
    run = svc.approve(db, user, _run(db, user, run_id), note=body.note)
    db.commit()
    return {"id": run.id, "status": run.status, "approved_at": run.approved_at}


@router.post("/runs/{run_id}/paid")
def mark_paid(
    run_id: int, user: User = Depends(approver), db: Session = Depends(get_db)
) -> dict:
    run = svc.mark_paid(db, user, _run(db, user, run_id))
    db.commit()
    return {"id": run.id, "status": run.status, "paid_at": run.paid_at}


@router.post("/runs/{run_id}/discard")
def discard(
    run_id: int,
    body: ReasonIn,
    user: User = Depends(runner),
    db: Session = Depends(get_db),
) -> dict:
    svc.discard(db, user, _run(db, user, run_id), reason=body.reason)
    db.commit()
    return {"discarded": run_id}


# --- output ----------------------------------------------------------------


@router.get("/runs/{run_id}/payslips")
def payslips(
    run_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    run = _run(db, user, run_id)
    rows = db.scalars(select(Payslip).where(Payslip.run_id == run.id))
    return [svc.payslip_out(db, s) for s in rows]


@router.get("/payslips/{payslip_id}")
def payslip(
    payslip_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    row = db.get(Payslip, payslip_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payslip not found")
    return svc.payslip_out(db, row)


@router.get("/runs/{run_id}/register/{code}")
def register(
    run_id: int, code: str, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    """A statutory register — PF, ESI, TDS (§5.3.10)."""
    return svc.register(db, _run(db, user, run_id), code.upper())


@router.get("/runs/{run_id}/cost-by-department")
def cost_by_department(
    run_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    return svc.cost_by_department(db, _run(db, user, run_id))


@router.get("/runs/{run_id}/bank-disbursal")
def bank_disbursal(
    run_id: int,
    format: str | None = Query(default=None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
):
    """Bank disbursal file (NEFT transfer sheet) for salary credit."""
    run = _run(db, user, run_id)
    slips = db.scalars(
        select(Payslip)
        .where(Payslip.run_id == run.id)
        .order_by(Payslip.payslip_no)
    ).all()

    rows = []
    for slip in slips:
        emp = slip.employee
        narration = f"Salary {run.month:02d}/{run.year} {emp.employee_code}"
        rows.append({
            "employee_code": emp.employee_code,
            "beneficiary_name": emp.user.full_name,
            "bank_name": emp.bank_name or "N/A",
            "bank_account_no": emp.bank_account_no or "N/A",
            "bank_ifsc": emp.bank_ifsc or "N/A",
            "net_amount": slip.net_pay,
            "narration": narration,
        })

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Employee Code",
            "Beneficiary Name",
            "Bank Name",
            "Account Number",
            "IFSC Code",
            "Net Amount (INR)",
            "Narration",
        ])
        for r in rows:
            writer.writerow([
                r["employee_code"],
                r["beneficiary_name"],
                r["bank_name"],
                r["bank_account_no"],
                r["bank_ifsc"],
                f"{r['net_amount']:.2f}",
                r["narration"],
            ])
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="salary_disbursal_{run.month:02d}_{run.year}_run{run.run_no}.csv"'
                )
            },
        )

    return rows

