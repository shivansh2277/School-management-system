"""Departments, the staff profile, and the exit that refuses.

Two rules carry the weight. §5.3.9 refuses an exit while the employee still
holds an active timetable allocation — otherwise a class keeps a teacher who no
longer works here and nobody finds out until Monday. And §5.3.9 gates salary
information apart from the rest of the profile, which is only true if no
profile shape carries the fields at all.
"""

import pytest
from sqlalchemy import select

from app.models import (
    AuditAction,
    AuditLog,
    ClassSection,
    ClassSubjectTeacher,
    Department,
    Employee,
    EmployeeStatus,
    TimetableSlot,
    User,
)
from app.services import hr


@pytest.fixture()
def teacher_1(db, ids):
    return db.get(Employee, ids["teacher_1"])


@pytest.fixture()
def spare(db, ids):
    """A teacher with no timetable, no subjects and no section — somebody the
    exit rule should let through."""
    user = User(
        school_id=ids["school"],
        role="teacher",
        login_id="TCH900",
        password_hash="x",
        full_name="Spare Teacher",
    )
    db.add(user)
    db.flush()
    row = Employee(
        school_id=ids["school"], user_id=user.id, employee_code="TCH900"
    )
    db.add(row)
    db.flush()
    return row


# --- departments -----------------------------------------------------------


def test_the_demo_school_has_departments_with_heads_and_headcounts(client, admin):
    rows = client.get("/admin/departments", headers=admin).json()
    by_code = {d["code"]: d for d in rows}
    assert {"SCI", "LANG", "HUM", "PRI", "ADM"} <= set(by_code)
    assert by_code["SCI"]["head"] is not None
    assert by_code["SCI"]["headcount"] == 5
    assert by_code["ADM"]["headcount"] == 0, "a department may be empty"


def test_a_department_code_is_unique_per_school(client, admin):
    first = client.post(
        "/admin/departments", headers=admin, json={"code": "MUS", "name": "Music"}
    )
    assert first.status_code == 201, first.text
    with pytest.raises(Exception):
        client.post(
            "/admin/departments", headers=admin, json={"code": "MUS", "name": "Music 2"}
        )


def test_a_departed_employee_cannot_head_a_department(db, admin_user, spare, ids):
    dept = hr.create_department(db, ids["school"], code="TMP", name="Temp")
    hr.exit_employee(db, admin_user, spare, on="2026-09-01", reason="Resigned")
    with pytest.raises(Exception) as e:
        hr.set_head(db, dept, spare)
    assert "cannot head a department" in str(e.value.detail)


# --- the profile, and what it must not contain -----------------------------


def test_the_profile_carries_the_department_and_designation(client, admin, ids):
    row = client.get(f"/admin/employees/{ids['teacher_1']}", headers=admin).json()
    assert row["employee_code"] == "TCH001"
    assert row["department"] == "Science and Mathematics"
    assert row["designation"] == "PGT"
    assert row["status"] == "active"


def test_no_profile_shape_carries_bank_or_pan(client, admin, ids):
    """The gate of §5.3.9 is only real if the fields are absent, not merely
    unpopulated — one careless serializer would otherwise undo it."""
    banned = {"pan", "uan", "esi_number", "bank_account_no", "bank_ifsc", "bank_name"}
    one = client.get(f"/admin/employees/{ids['teacher_1']}", headers=admin).json()
    assert banned & set(one) == set()
    listed = client.get("/admin/employees", headers=admin).json()
    assert banned & set(listed[0]) == set()


def test_statutory_details_are_served_only_behind_their_own_permission(
    client, admin, teacher, ids
):
    r = client.get(f"/admin/employees/{ids['teacher_1']}/statutory", headers=admin)
    assert r.status_code == 200, r.text
    assert "bank_account_no" in r.json()

    # A teacher can read a staff record and must not read a colleague's bank.
    assert client.get(
        f"/admin/employees/{ids['teacher_1']}", headers=teacher
    ).status_code in (200, 403)
    assert client.get(
        f"/admin/employees/{ids['teacher_1']}/statutory", headers=teacher
    ).status_code == 403


def test_reading_everything_does_not_include_reading_salary():
    """The trap in the READ_ONLY helper: naming a permission `.read` would have
    handed a records clerk every colleague's bank account."""
    from app.core.permissions import READ_ONLY, SYSTEM_ROLES

    assert "hr.salary.read" not in READ_ONLY
    holders = {code for code, _, perms in SYSTEM_ROLES if "hr.salary.read" in perms}
    assert holders == {"super_admin", "principal", "auditor"}
    assert "admin_officer" not in holders


def test_editing_statutory_details_is_audited(db, admin_user, teacher_1):
    hr.set_statutory(db, admin_user, teacher_1, {"pan": "ABCDE1234F"})
    entry = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "employee_statutory",
            AuditLog.entity_id == teacher_1.id,
        )
        .order_by(AuditLog.occurred_at.desc())
    )
    assert entry is not None
    assert entry.after["pan"] == "ABCDE1234F"


def test_an_unknown_statutory_field_is_refused_not_ignored(db, admin_user, teacher_1):
    with pytest.raises(Exception) as e:
        hr.set_statutory(db, admin_user, teacher_1, {"salary": "100000"})
    assert "not a statutory field" in str(e.value.detail)


# --- assignment ------------------------------------------------------------


def test_somebody_cannot_report_to_themselves(db, admin_user, teacher_1):
    with pytest.raises(Exception) as e:
        hr.assign(db, admin_user, teacher_1, reporting_to_id=teacher_1.id)
    assert "report to themselves" in str(e.value.detail)


def test_a_department_of_another_school_is_not_found(db, admin_user, teacher_1, ids):
    from app.models import School

    rival = School(code="RIVAL5", name="Rival Five")
    db.add(rival)
    db.flush()
    theirs = hr.create_department(db, rival.id, code="X", name="Theirs")
    with pytest.raises(Exception) as e:
        hr.assign(db, admin_user, teacher_1, department_id=theirs.id)
    assert e.value.status_code == 404


# --- leaving, which is the rule with teeth ---------------------------------


def test_a_teacher_still_holding_periods_cannot_be_exited(db, admin_user, teacher_1):
    """§5.3.9. Exiting them does not free the periods — it leaves classes with
    a teacher who no longer works here."""
    held = hr.active_allocations(db, teacher_1)
    assert held["timetable_periods"] > 0, "TCH001 teaches 10-A Mathematics"

    with pytest.raises(Exception) as e:
        hr.exit_employee(db, admin_user, teacher_1, on="2026-09-01", reason="Resigned")
    assert e.value.status_code == 409
    assert "Reassign these" in str(e.value.detail)
    assert teacher_1.status is EmployeeStatus.active, "nothing changed"


def test_the_allocations_route_lists_what_to_reassign_first(client, admin, ids):
    r = client.get(f"/admin/employees/{ids['teacher_1']}/allocations", headers=admin)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["timetable_periods"] > 0
    assert "10-A" in body["class_teacher_of"]
    assert "Science and Mathematics" in body["heads_departments"]


def test_someone_holding_nothing_can_be_exited(db, admin_user, spare):
    row = hr.exit_employee(
        db, admin_user, spare, on="2026-09-01", reason="Contract ended"
    )
    assert row.status is EmployeeStatus.exited
    assert str(row.exited_on) == "2026-09-01"


def test_an_exit_is_audited_with_its_reason(db, admin_user, spare):
    hr.exit_employee(db, admin_user, spare, on="2026-09-01", reason="Contract ended")
    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "employee", AuditLog.entity_id == spare.id
        )
    )
    assert entry.action is AuditAction.status_change
    assert entry.reason == "Contract ended"


def test_an_exit_takes_the_login_with_it(db, admin_user, spare):
    """Retaining the record is not retaining access (§14)."""
    hr.exit_employee(db, admin_user, spare, on="2026-09-01", reason="Contract ended")
    assert spare.user.is_active is False


def test_the_employee_row_and_its_code_survive_the_exit(db, admin_user, spare):
    """§5.3.9: never reused, even after exit — which is what keeps an old
    payslip or an old mark resolvable."""
    code = spare.employee_code
    hr.exit_employee(db, admin_user, spare, on="2026-09-01", reason="Contract ended")
    still = db.scalar(select(Employee).where(Employee.employee_code == code))
    assert still is not None and still.id == spare.id


def test_exiting_twice_is_a_no_op(db, admin_user, spare):
    hr.exit_employee(db, admin_user, spare, on="2026-09-01", reason="Contract ended")
    again = hr.exit_employee(
        db, admin_user, spare, on="2026-10-01", reason="Contract ended"
    )
    assert str(again.exited_on) == "2026-09-01", "the first date stands"


def test_past_staff_are_kept_but_are_not_the_default_answer(
    client, admin, db, admin_user, spare
):
    hr.exit_employee(db, admin_user, spare, on="2026-09-01", reason="Contract ended")
    db.flush()
    current = client.get("/admin/employees", headers=admin).json()
    assert spare.employee_code not in [e["employee_code"] for e in current]

    everyone = client.get(
        "/admin/employees", headers=admin, params={"include_exited": True}
    ).json()
    assert spare.employee_code in [e["employee_code"] for e in everyone]
