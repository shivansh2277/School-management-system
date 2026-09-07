"""Departments, the staff profile, and recording an exit (§5.3.3).

The statutory route is separate on purpose. §5.3.9 gates salary information
apart from the rest of the profile, and the way to make that true rather than
intended is for no profile shape to carry the fields at all.
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Department, Employee, EmployeeStatus, User
from app.services import hr as svc
from app.services.rbac import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])
reader = require_permission("hr.employee.read", school_wide=True)
writer = require_permission("hr.employee.write", school_wide=True)
dept_writer = require_permission("hr.department.write", school_wide=True)
salary_reader = require_permission("hr.salary.read", school_wide=True)
salary_writer = require_permission("hr.salary.write", school_wide=True)
exiter = require_permission("hr.employee.exit", school_wide=True)


class DepartmentIn(BaseModel):
    code: str = Field(min_length=1, max_length=12)
    name: str = Field(min_length=1, max_length=80)


class HeadIn(BaseModel):
    head_employee_id: int | None = None


class AssignmentIn(BaseModel):
    department_id: int | None = None
    designation: str | None = Field(default=None, max_length=60)
    reporting_to_id: int | None = None


class StatutoryIn(BaseModel):
    pan: str | None = Field(default=None, max_length=10)
    uan: str | None = Field(default=None, max_length=12)
    esi_number: str | None = Field(default=None, max_length=20)
    bank_account_no: str | None = Field(default=None, max_length=20)
    bank_ifsc: str | None = Field(default=None, max_length=11)
    bank_name: str | None = Field(default=None, max_length=80)


class ExitIn(BaseModel):
    exited_on: Date
    reason: str = Field(min_length=3, max_length=500)


# --- departments -----------------------------------------------------------


@router.get("/departments")
def list_departments(
    user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.scalars(
        select(Department)
        .where(Department.school_id == user.school_id)
        .order_by(Department.name)
    )
    return [svc.department_out(db, d) for d in rows]


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def create_department(
    body: DepartmentIn, user: User = Depends(dept_writer), db: Session = Depends(get_db)
) -> dict:
    row = svc.create_department(db, user.school_id, code=body.code, name=body.name)
    db.commit()
    return svc.department_out(db, row)


@router.put("/departments/{department_id}/head")
def set_head(
    department_id: int,
    body: HeadIn,
    user: User = Depends(dept_writer),
    db: Session = Depends(get_db),
) -> dict:
    department = svc.owned_department(db, user, department_id)
    head = (
        svc.owned(db, user, body.head_employee_id) if body.head_employee_id else None
    )
    svc.set_head(db, department, head)
    db.commit()
    return svc.department_out(db, department)


# --- staff -----------------------------------------------------------------


@router.get("/employees")
def list_employees(
    department_id: int | None = None,
    include_exited: bool = Query(
        False,
        description="Past staff are kept forever; they are simply not the "
        "default answer to 'who works here'.",
    ),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(Employee).where(Employee.school_id == user.school_id)
    if department_id is not None:
        q = q.where(Employee.department_id == department_id)
    if not include_exited:
        q = q.where(Employee.status != EmployeeStatus.exited)
    return [
        svc.profile(db, e) for e in db.scalars(q.order_by(Employee.employee_code))
    ]


@router.get("/employees/{employee_id}")
def employee(
    employee_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    return svc.profile(db, svc.owned(db, user, employee_id))


@router.put("/employees/{employee_id}/assignment")
def assign(
    employee_id: int,
    body: AssignmentIn,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.assign(
        db,
        user,
        svc.owned(db, user, employee_id),
        department_id=body.department_id,
        designation=body.designation,
        reporting_to_id=body.reporting_to_id,
    )
    db.commit()
    return svc.profile(db, row)


@router.get("/employees/{employee_id}/statutory")
def statutory(
    employee_id: int,
    user: User = Depends(salary_reader),
    db: Session = Depends(get_db),
) -> dict:
    """PAN, PF, ESI and bank. Its own permission, held by the principal and the
    auditor and nobody else who can merely read a staff record."""
    return svc.statutory(db, svc.owned(db, user, employee_id))


@router.put("/employees/{employee_id}/statutory")
def set_statutory(
    employee_id: int,
    body: StatutoryIn,
    user: User = Depends(salary_writer),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.set_statutory(
        db, user, svc.owned(db, user, employee_id), body.model_dump(exclude_unset=True)
    )
    db.commit()
    return svc.statutory(db, row)


@router.get("/employees/{employee_id}/allocations")
def allocations(
    employee_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """What would be left unattended if this person walked out today.

    Answered before an exit is attempted rather than as a 409 afterwards: the
    office wants the list of what to reassign, not a refusal.
    """
    return svc.active_allocations(db, svc.owned(db, user, employee_id))


@router.post("/employees/{employee_id}/exit")
def record_exit(
    employee_id: int,
    body: ExitIn,
    user: User = Depends(exiter),
    db: Session = Depends(get_db),
) -> dict:
    row = svc.exit_employee(
        db, user, svc.owned(db, user, employee_id), on=body.exited_on, reason=body.reason
    )
    db.commit()
    return svc.profile(db, row)
