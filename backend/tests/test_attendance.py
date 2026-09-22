from datetime import date, timedelta
import pytest

from app.services.attendance import summarise


@pytest.fixture(autouse=True)
def allow_marking_today(monkeypatch):
    import app.services.attendance
    monkeypatch.setattr(app.services.attendance, "is_working_day", lambda day, holidays: True)


def roster_ids(db, class_section_id):
    from app.models import Enrolment, Student

    return [
        s.id
        for s in db.query(Student)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .filter(Enrolment.class_section_id == class_section_id)
        .order_by(Enrolment.roll_no)
    ]


def test_percentage_counts_leave_against_presence():
    from app.models import AttendanceStatus as S

    s = summarise({S.present: 90, S.absent: 5, S.leave: 5})
    assert s.percent == 90.0
    assert summarise({}).percent is None  # nothing marked -> no fabricated figure


def test_marking_twice_upserts_rather_than_duplicating(client, teacher, db, ids):
    students = roster_ids(db, ids["section_10a"])
    day = date.today().isoformat()

    def post(status):
        return client.post(
            "/teacher/attendance",
            json={
                "class_section_id": ids["section_10a"],
                "date": day,
                "entries": [{"student_id": sid, "status": status} for sid in students],
            },
            headers=teacher,
        )

    assert post("present").status_code == 200
    second = post("absent")
    assert second.status_code == 200
    assert all(row["status"] == "absent" for row in second.json())

    from app.models import Attendance, Enrolment

    rows = (
        db.query(Attendance)
        .join(Enrolment, Enrolment.id == Attendance.enrolment_id)
        # `day`, not a second `date.today()`: the rows were written for the
        # date posted above, and a run crossing midnight between the two counts
        # zero of them.
        .filter(Enrolment.student_id.in_(students), Attendance.date == date.fromisoformat(day))
        .count()
    )
    assert rows == len(students)  # one row per student per day, not two


def test_future_date_is_rejected(client, teacher, db, ids):
    students = roster_ids(db, ids["section_10a"])
    r = client.post(
        "/teacher/attendance",
        json={
            "class_section_id": ids["section_10a"],
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "entries": [{"student_id": students[0], "status": "present"}],
        },
        headers=teacher,
    )
    assert r.status_code == 400


def test_a_teacher_cannot_mark_a_student_from_another_section(client, teacher, db, ids):
    outsider = roster_ids(db, ids["section_8a"])[0]
    r = client.post(
        "/teacher/attendance",
        json={
            "class_section_id": ids["section_10a"],
            "date": date.today().isoformat(),
            "entries": [{"student_id": outsider, "status": "absent"}],
        },
        headers=teacher,
    )
    assert r.status_code == 403


def test_roll_sheet_is_prefilled_after_marking(client, teacher, db, ids):
    students = roster_ids(db, ids["section_10a"])
    day = date.today().isoformat()
    client.post(
        "/teacher/attendance",
        json={
            "class_section_id": ids["section_10a"],
            "date": day,
            "entries": [{"student_id": sid, "status": "leave"} for sid in students],
        },
        headers=teacher,
    )
    rows = client.get(
        f"/teacher/attendance?class_section_id={ids['section_10a']}&date={day}", headers=teacher
    ).json()
    assert rows and all(r["status"] == "leave" for r in rows)


def test_student_month_view_matches_its_own_summary(client, student):
    body = client.get("/student/attendance", headers=student).json()
    counted = {"present": 0, "absent": 0, "leave": 0}
    for d in body["days"]:
        counted[d["status"]] += 1
    assert counted["present"] == body["summary"]["present"]
    assert counted["absent"] == body["summary"]["absent"]
    assert counted["leave"] == body["summary"]["leave"]
