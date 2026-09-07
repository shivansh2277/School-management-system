"""Staff records: departments, the employee profile, and leaving.

The rule that shapes this module is §5.3.9's: **an employee cannot be exited
with an active timetable allocation.** Exiting a teacher who still holds six
periods a week does not free those periods — it leaves a class with a teacher
who no longer works here, and nobody finds out until Monday. So the exit refuses
and names what has to be reassigned first.

Salary information is deliberately absent from every profile shape here.
§5.3.9 gates it separately, so `statutory()` is its own call behind its own
permission rather than a field the profile happens to include.
"""

from datetime import date as Date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    ClassSection,
    ClassSubjectTeacher,
    Department,
    Employee,
    EmployeeStatus,
    TimetableSlot,
    User,
)
from app.services import audit

# The columns §5.3.9 keeps behind its own permission.
STATUTORY_FIELDS = (
    "pan",
    "uan",
    "esi_number",
    "bank_account_no",
    "bank_ifsc",
    "bank_name",
)


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def owned(db: Session, user: User, employee_id: int) -> Employee:
    row = db.get(Employee, employee_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    return row


def owned_department(db: Session, user: User, department_id: int) -> Department:
    row = db.get(Department, department_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")
    return row


# --- departments -----------------------------------------------------------


def create_department(
    db: Session, school_id: int, *, code: str, name: str
) -> Department:
    row = Department(school_id=school_id, code=code.strip().upper(), name=name.strip())
    db.add(row)
    db.flush()
    return row


def set_head(db: Session, department: Department, employee: Employee | None) -> Department:
    if employee is not None:
        if employee.school_id != department.school_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
        if not employee.in_service:
            raise _bad(
                f"{employee.user.full_name} has left, and cannot head a department"
            )
    department.head_employee_id = employee.id if employee else None
    db.flush()
    return department


def department_out(db: Session, row: Department) -> dict:
    head = db.get(Employee, row.head_employee_id) if row.head_employee_id else None
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "head_employee_id": row.head_employee_id,
        "head": head.user.full_name if head else None,
        "headcount": db.scalar(
            select(func.count(Employee.id)).where(
                Employee.department_id == row.id,
                Employee.status != EmployeeStatus.exited,
            )
        ),
    }


# --- the profile -----------------------------------------------------------


def profile(db: Session, employee: Employee) -> dict:
    """Everything about a member of staff except what they are paid."""
    reports_to = (
        db.get(Employee, employee.reporting_to_id)
        if employee.reporting_to_id
        else None
    )
    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "full_name": employee.user.full_name,
        "email": employee.user.email,
        "phone": employee.user.phone,
        "employee_type": employee.employee_type,
        "status": employee.status,
        "qualification": employee.qualification,
        "designation": employee.designation,
        "department_id": employee.department_id,
        "department": employee.department.name if employee.department else None,
        "reporting_to_id": employee.reporting_to_id,
        "reporting_to": reports_to.user.full_name if reports_to else None,
        "joining_date": employee.joining_date,
        "exited_on": employee.exited_on,
        "emergency_contact_name": employee.emergency_contact_name,
        "emergency_contact_phone": employee.emergency_contact_phone,
    }


def statutory(db: Session, employee: Employee) -> dict:
    """PAN, PF, ESI and bank. Served only behind `hr.salary.read` (§5.3.9)."""
    return {"id": employee.id, **{f: getattr(employee, f) for f in STATUTORY_FIELDS}}


def set_statutory(
    db: Session, user: User, employee: Employee, values: dict
) -> Employee:
    before = audit.snapshot(employee, list(STATUTORY_FIELDS))
    for field, value in values.items():
        if field not in STATUTORY_FIELDS:
            raise _bad(f"{field} is not a statutory field")
        setattr(employee, field, value)
    audit.record(
        db,
        actor=user,
        school_id=employee.school_id,
        entity_type="employee_statutory",
        entity_id=employee.id,
        action=AuditAction.update,
        before=before,
        after=audit.snapshot(employee, list(STATUTORY_FIELDS)),
    )
    db.flush()
    return employee


def assign(
    db: Session,
    user: User,
    employee: Employee,
    *,
    department_id: int | None = None,
    designation: str | None = None,
    reporting_to_id: int | None = None,
) -> Employee:
    if department_id is not None:
        owned_department(db, user, department_id)
        employee.department_id = department_id
    if designation is not None:
        employee.designation = designation
    if reporting_to_id is not None:
        if reporting_to_id == employee.id:
            raise _bad("Somebody cannot report to themselves")
        manager = owned(db, user, reporting_to_id)
        if not manager.in_service:
            raise _bad(f"{manager.user.full_name} has left")
        employee.reporting_to_id = manager.id
    db.flush()
    return employee


# --- leaving ---------------------------------------------------------------


def active_allocations(db: Session, employee: Employee) -> dict:
    """What would be left unattended if this person walked out today."""
    return {
        "timetable_periods": db.scalar(
            select(func.count(TimetableSlot.id)).where(
                TimetableSlot.teacher_id == employee.id
            )
        ),
        "subjects": db.scalar(
            select(func.count(ClassSubjectTeacher.id)).where(
                ClassSubjectTeacher.teacher_id == employee.id
            )
        ),
        "class_teacher_of": [
            c.label
            for c in db.scalars(
                select(ClassSection).where(
                    ClassSection.class_teacher_id == employee.id
                )
            )
        ],
        "heads_departments": [
            d.name
            for d in db.scalars(
                select(Department).where(Department.head_employee_id == employee.id)
            )
        ],
    }


def exit_employee(
    db: Session, user: User, employee: Employee, *, on: Date, reason: str
) -> Employee:
    """Mark someone as having left.

    §5.3.9 refuses this while they still hold an active timetable allocation.
    Exiting a teacher who holds six periods a week does not free those periods:
    it leaves classes with a teacher who no longer works here, and nobody finds
    out until Monday. The refusal names what has to be reassigned first.

    The employee row and its `employee_code` stay forever — the code is never
    reused, which is what makes an old payslip or an old mark still resolvable.
    """
    if employee.status is EmployeeStatus.exited:
        return employee
    held = active_allocations(db, employee)
    blocking = {k: v for k, v in held.items() if v}
    if blocking:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This employee still holds "
            + ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in blocking.items())
            + ". Reassign these before recording the exit.",
        )
    audit.record(
        db,
        actor=user,
        school_id=employee.school_id,
        entity_type="employee",
        entity_id=employee.id,
        action=AuditAction.status_change,
        before={"status": employee.status.value},
        after={"status": EmployeeStatus.exited.value, "exited_on": str(on)},
        reason=reason,
    )
    employee.status = EmployeeStatus.exited
    employee.exited_on = on
    # The login goes with the post. Retaining the record is not retaining
    # access (§14).
    employee.user.is_active = False
    db.flush()
    return employee
