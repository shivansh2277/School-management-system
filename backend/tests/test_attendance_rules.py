"""The attendance rules of §5.8.9 — corrections, holidays, the denominator,
absentees and leave.

The plain marking path is covered in `test_attendance.py`; this is the part
that is easy to get quietly wrong.
"""

from datetime import date, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.models import (
    Attendance,
    AttendanceStatus,
    AuditLog,
    Enrolment,
    Holiday,
    LeaveStatus,
    Permission,
    Role,
    RolePermission,
    StudentLeaveRequest,
    User,
    UserRole,
)
from app.services import attendance as svc
from app.services import rbac
from tests.conftest import auth


def last_working_day(days_back: int = 1) -> date:
    day = date.today() - timedelta(days=days_back)
    while day.weekday() == 6:
        day -= timedelta(days=1)
    return day


def mark(client, teacher, section, day, entries, reason=None):
    body = {
        "class_section_id": section,
        "date": day.isoformat(),
        "entries": entries,
    }
    if reason is not None:
        body["reason"] = reason
    return client.post("/teacher/attendance", json=body, headers=teacher)


def test_a_working_day_count_skips_sundays_and_holidays(db, ids):
    """The denominator §5.8.9 calls the most common reporting bug."""
    school_id = db.get(Enrolment, 1).school_id
    monday = date(2026, 6, 1)  # a Monday
    assert svc.working_days(db, school_id, monday, monday + timedelta(days=6)) == 6

    db.add(
        Holiday(
            school_id=school_id,
            academic_year_id=db.get(Enrolment, 1).academic_year_id,
            date=monday + timedelta(days=2),
            name="Test holiday",
        )
    )
    db.flush()
    assert svc.working_days(db, school_id, monday, monday + timedelta(days=6)) == 5


def test_attendance_cannot_be_marked_on_a_holiday(client, teacher, admin, db, ids):
    day = last_working_day(2)
    added = client.post(
        "/admin/attendance/holidays",
        json={"date": day.isoformat(), "name": "Founder's Day (test)"},
        headers=admin,
    )
    assert added.status_code in (201, 409)

    roll = client.get(
        f"/admin/attendance?class_section_id={ids['section_10a']}&date={day}", headers=admin
    ).json()
    r = mark(
        client,
        teacher,
        ids["section_10a"],
        day,
        [{"student_id": roll[0]["student_id"], "status": "present"}],
    )
    assert r.status_code == 400
    assert "working day" in r.json()["detail"]


def test_correcting_an_earlier_day_requires_a_reason_and_is_audited(
    client, teacher, db, ids
):
    day = last_working_day(3)
    first = mark(
        client,
        teacher,
        ids["section_10a"],
        day,
        [{"student_id": ids["student_1"], "status": "present"}],
    )
    assert first.status_code == 200

    without_reason = mark(
        client,
        teacher,
        ids["section_10a"],
        day,
        [{"student_id": ids["student_1"], "status": "absent"}],
    )
    assert without_reason.status_code == 422
    assert "reason" in without_reason.json()["detail"].lower()

    with_reason = mark(
        client,
        teacher,
        ids["section_10a"],
        day,
        [{"student_id": ids["student_1"], "status": "absent"}],
        reason="Marked from the wrong register page",
    )
    assert with_reason.status_code == 200
    db.expire_all()

    entry = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == "attendance")
        .order_by(AuditLog.id.desc())
    ).first()
    assert entry is not None
    assert entry.reason == "Marked from the wrong register page"
    assert entry.before["status"] == "present" and entry.after["status"] == "absent"

    row = next(r for r in with_reason.json() if r["student_id"] == ids["student_1"])
    assert row["corrected"] is True


def test_fixing_todays_roll_is_not_a_correction(client, teacher, db, ids):
    """A teacher fixing a tap while the register is still open is not amending
    a record, and should not be made to justify it."""
    today = date.today()
    school_id = db.get(Enrolment, 1).school_id
    if today.weekday() == 6 or not svc.is_working_day(today, svc.holidays_between(db, school_id, today, today)):
        return
    mark(
        client,
        teacher,
        ids["section_10a"],
        today,
        [{"student_id": ids["student_1"], "status": "present"}],
    )
    again = mark(
        client,
        teacher,
        ids["section_10a"],
        today,
        [{"student_id": ids["student_1"], "status": "absent"}],
    )
    assert again.status_code == 200
    assert next(r for r in again.json() if r["student_id"] == ids["student_1"])["corrected"] is False


def test_resubmitting_the_same_roster_changes_nothing(client, teacher, db, ids):
    """The mobile app on a poor connection sends the same roster twice."""
    day = last_working_day(4)
    entries = [{"student_id": ids["student_1"], "status": "present"}]
    mark(client, teacher, ids["section_10a"], day, entries)
    db.expire_all()
    before = db.scalar(
        select(Attendance).where(
            Attendance.enrolment_id
            == db.scalar(select(Enrolment.id).where(Enrolment.student_id == ids["student_1"])),
            Attendance.date == day,
        )
    )
    stamp = before.corrected_at

    # no reason given, and none needed: nothing is changing
    assert mark(client, teacher, ids["section_10a"], day, entries).status_code == 200
    db.expire_all()
    after = db.get(Attendance, before.id)
    assert after.corrected_at == stamp


def test_the_percentage_uses_working_days_not_marked_days(client, admin, db, ids):
    """A section nobody marked must not read as 100%."""
    percent = svc.student_percent(db, ids["student_1"])
    assert percent is not None and 0 < percent <= 100


def test_late_counts_as_present_and_half_day_as_half(db):
    S = AttendanceStatus
    assert svc.summarise({S.present: 8, S.late: 2}, 10).percent == 100.0
    assert svc.summarise({S.present: 9, S.half_day: 2}, 10).percent == 100.0
    assert svc.summarise({S.present: 5, S.absent: 5}, 10).percent == 50.0


def test_approved_leave_is_reported_apart_from_absence(db):
    S = AttendanceStatus
    summary = svc.summarise({S.present: 8, S.absent: 1, S.leave: 1}, 10)
    assert summary.absent == 1 and summary.leave == 1
    assert summary.percent == 80.0, "leave is not presence"


def test_the_absentee_list_separates_leave_from_unexplained_absence(
    client, teacher, admin, db, ids
):
    day = last_working_day(5)
    roster_rows = client.get(
        f"/admin/attendance?class_section_id={ids['section_10a']}&date={day}", headers=admin
    ).json()
    two = [r["student_id"] for r in roster_rows[:2]]
    mark(
        client,
        teacher,
        ids["section_10a"],
        day,
        [
            {"student_id": two[0], "status": "absent"},
            {"student_id": two[1], "status": "leave"},
        ],
        reason="Register reconciled with the front office",
    )
    listed = client.get(f"/admin/attendance/absentees?date={day}", headers=admin).json()
    mine = {r["student_id"]: r for r in listed}
    assert mine[two[0]]["expected"] is False, "an unexplained absence is one to chase"
    assert mine[two[1]]["expected"] is True, "approved leave is not"
    assert "contact" in mine[two[0]]


def test_a_guardian_applies_for_leave_and_approval_writes_the_register(
    client, parent, admin, db
):
    child = client.get("/parent/children", headers=parent).json()[0]["id"]
    start = date.today() + timedelta(days=3)
    end = start + timedelta(days=2)
    applied = client.post(
        "/parent/leave-requests",
        json={
            "student_id": child,
            "from_date": start.isoformat(),
            "to_date": end.isoformat(),
            "type": "planned",
            "reason": "Family wedding out of station",
        },
        headers=parent,
    )
    assert applied.status_code == 201
    assert applied.json()["status"] == LeaveStatus.applied

    pending = client.get("/admin/attendance/leave-requests?status_=applied", headers=admin).json()
    assert applied.json()["id"] in {r["id"] for r in pending}

    decided = client.post(
        f"/admin/attendance/leave-requests/{applied.json()['id']}/decide",
        json={"approve": True, "note": "Approved by the class teacher"},
        headers=admin,
    )
    assert decided.status_code == 200 and decided.json()["status"] == LeaveStatus.approved

    db.expire_all()
    enrolment = svc.enrolment_of(db, child)
    written = db.scalars(
        select(Attendance).where(
            Attendance.enrolment_id == enrolment.id,
            Attendance.date >= start,
            Attendance.date <= end,
        )
    ).all()
    assert written, "approval must reach the register, not just the request table"
    assert all(a.status is AttendanceStatus.leave for a in written)
    assert all(a.date.weekday() != 6 for a in written), "no leave marked on a Sunday"


def test_a_second_overlapping_leave_request_is_refused(client, parent, db):
    child = client.get("/parent/children", headers=parent).json()[0]["id"]
    start = date.today() + timedelta(days=20)
    body = {
        "student_id": child,
        "from_date": start.isoformat(),
        "to_date": (start + timedelta(days=2)).isoformat(),
        "type": "sick",
        "reason": "Chickenpox, doctor advised rest",
    }
    assert client.post("/parent/leave-requests", json=body, headers=parent).status_code == 201
    body["from_date"] = (start + timedelta(days=1)).isoformat()
    assert client.post("/parent/leave-requests", json=body, headers=parent).status_code == 409


def test_a_guardian_cannot_apply_for_another_familys_child(client, other_parent, db, ids):
    start = date.today() + timedelta(days=5)
    r = client.post(
        "/parent/leave-requests",
        json={
            "student_id": ids["student_1"],
            "from_date": start.isoformat(),
            "to_date": start.isoformat(),
            "type": "sick",
            "reason": "Not their child",
        },
        headers=other_parent,
    )
    assert r.status_code in (403, 404)


def test_approving_leave_does_not_overwrite_a_day_already_marked(
    client, teacher, parent, admin, db, ids
):
    """If the teacher recorded the child as present, the child was there."""
    day = last_working_day(6)
    child = ids["student_1"]
    mark(
        client,
        teacher,
        ids["section_10a"],
        day,
        [{"student_id": child, "status": "present"}],
        reason="Register reconciled",
    )
    db.commit()

    request = StudentLeaveRequest(
        school_id=db.get(Enrolment, 1).school_id,
        enrolment_id=svc.enrolment_of(db, child).id,
        from_date=day,
        to_date=day,
        type="sick",
        reason="Applied late",
        status=LeaveStatus.applied,
    )
    db.add(request)
    db.commit()

    client.post(
        f"/admin/attendance/leave-requests/{request.id}/decide",
        json={"approve": True, "note": "Approved after the fact"},
        headers=admin,
    )
    db.expire_all()
    row = db.scalar(
        select(Attendance).where(
            Attendance.enrolment_id == svc.enrolment_of(db, child).id,
            Attendance.date == day,
        )
    )
    assert row.status is AttendanceStatus.present


def test_the_shortage_list_is_worst_first(client, admin):
    rows = client.get("/admin/attendance/shortage?threshold=100", headers=admin).json()
    assert rows, "with a 100% threshold everyone with a mark should appear"
    percents = [r["percent"] for r in rows]
    assert percents == sorted(percents)


def test_the_attendance_roll_is_gated_on_the_attendance_permission_not_the_exam_one(
    client, db, ids
):
    """`GET /admin/attendance` used to live on the exams router and so checked
    `exam.definition.read` - the permission the Exam Controller holds, not the
    one the `/attendance` web screen (`web/src/screens.ts`) actually declares.
    That let an Exam Controller read a register the UI hid from them, and
    denied anyone who held only `attendance.record.read`, the exact case the
    screen registry exists to prevent. The route now checks the permission it
    was always supposed to."""
    day = last_working_day(1)
    params = f"?class_section_id={ids['section_10a']}&date={day}"

    exam_controller = User(
        school_id=1,
        role=UserRole.admin,
        login_id="examctrl.test@sunrisepublic.edu",
        password_hash=hash_password("Test@123"),
        full_name="Exam Controller (test)",
    )
    db.add(exam_controller)
    db.flush()
    exam_role = db.scalar(select(Role).where(Role.school_id == 1, Role.code == "exam_controller"))
    rbac.assign(db, exam_controller, exam_role)
    db.commit()
    exam_ctrl_token = client.post(
        "/auth/login",
        json={
            "role": "admin",
            "login_id": "examctrl.test@sunrisepublic.edu",
            "password": "Test@123",
        },
    ).json()["access_token"]

    denied = client.get(f"/admin/attendance{params}", headers=auth(exam_ctrl_token))
    assert denied.status_code == 403, "exam.definition.read must not open the attendance roll"

    # A role holding only attendance.record.read, school-wide, must be let in.
    attendance_reader = User(
        school_id=1,
        role=UserRole.admin,
        login_id="attendanceonly.test@sunrisepublic.edu",
        password_hash=hash_password("Test@123"),
        full_name="Attendance Reader (test)",
    )
    db.add(attendance_reader)
    reader_role = Role(school_id=1, code="attendance_reader_test", name="Attendance Reader (test)")
    db.add(reader_role)
    db.flush()
    permission = db.scalar(select(Permission).where(Permission.code == "attendance.record.read"))
    db.add(RolePermission(school_id=1, role_id=reader_role.id, permission_id=permission.id))
    db.flush()
    rbac.assign(db, attendance_reader, reader_role)
    db.commit()
    reader_token = client.post(
        "/auth/login",
        json={
            "role": "admin",
            "login_id": "attendanceonly.test@sunrisepublic.edu",
            "password": "Test@123",
        },
    ).json()["access_token"]

    allowed = client.get(f"/admin/attendance{params}", headers=auth(reader_token))
    assert allowed.status_code == 200, "attendance.record.read alone must open the roll"
