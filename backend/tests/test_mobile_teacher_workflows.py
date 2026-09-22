"""Tests for Session 6: Teacher Mobile Workflow Test Suite.

Validates the teacher mobile operational workflows end-to-end:
1. Classroom Roll Marking (attendance.tsx):
   - Roster fetching: GET /teacher/classes/{section_id}/students returns enrolment_id
   - Batch attendance: POST /teacher/attendance with P, A, L, M
   - "Mark All Present" shortcut verification
   - Future date rejection (400)
   - Direct database assertion on attendance table
2. Homework Management (homework.tsx):
   - POST /teacher/homework with attachment_url
   - GET /teacher/homework/{id}/submissions
   - PATCH /teacher/homework/submissions/{id} grading
   - Teacher section isolation: other_teacher blocked with 403
3. Mobile Test Marks Entry (results.tsx / marks.tsx):
   - Roster by paper: GET /teacher/exams/{exam_id}/classes/{section_id}/subjects/{subject_id}/roster
   - Score entry <= max_marks with enrolment_id
   - Score > max_marks rejected with 422
   - In-place upsert verification in DB
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    Attendance,
    AttendanceStatus,
    ExamSchedule,
    HomeworkSubmission,
    Mark,
)


@pytest.fixture(autouse=True)
def allow_marking_today(monkeypatch):
    import app.services.attendance
    monkeypatch.setattr(app.services.attendance, "is_working_day", lambda day, holidays: True)


def test_classroom_roll_marking_workflow(client, teacher, db, ids):
    """Teacher fetches class roster with enrolment_id, marks batch attendance with P/A/L/M, and DB rows are verified."""
    # 1. Fetch section roster
    roster_resp = client.get(f"/teacher/classes/{ids['section_10a']}/students", headers=teacher)
    assert roster_resp.status_code == 200, roster_resp.text
    students = roster_resp.json()
    assert len(students) > 0
    assert all("enrolment_id" in s for s in students)
    assert all("student_id" in s for s in students)

    # 2. Prepare batch payload with realistic mix: P, A, L, M
    # (Mapping: P=present, A=absent, L=late, M=excused/leave)
    statuses = [
        AttendanceStatus.present,
        AttendanceStatus.absent,
        AttendanceStatus.late,
        AttendanceStatus.leave,
    ]
    today_str = date.today().isoformat()
    entries = []
    for idx, s in enumerate(students):
        status_chosen = statuses[idx % len(statuses)]
        entries.append(
            {
                "enrolment_id": s["enrolment_id"],
                "student_id": s["student_id"],
                "status": status_chosen.value,
                "remarks": f"Batch mark {status_chosen.value}",
            }
        )

    # 3. Submit batch attendance
    mark_resp = client.post(
        "/teacher/attendance",
        json={
            "class_section_id": ids["section_10a"],
            "date": today_str,
            "entries": entries,
        },
        headers=teacher,
    )
    assert mark_resp.status_code == 200, mark_resp.text
    roll_rows = mark_resp.json()
    assert len(roll_rows) == len(students)

    # 4. Direct DB assertion
    db.expire_all()
    enrolment_ids = [s["enrolment_id"] for s in students]
    db_rows = list(
        db.scalars(
            select(Attendance).where(
                Attendance.enrolment_id.in_(enrolment_ids),
                Attendance.date == date.today(),
            )
        )
    )
    assert len(db_rows) == len(students)
    db_map = {r.enrolment_id: r for r in db_rows}
    for e in entries:
        row = db_map[e["enrolment_id"]]
        assert row.status.value == e["status"]
        assert row.remarks == e["remarks"]


def test_mark_all_present_shortcut(client, teacher, db, ids):
    """Mark all present shortcut correctly updates all enrolled students to 'present' in DB."""
    roster_resp = client.get(f"/teacher/classes/{ids['section_10a']}/students", headers=teacher)
    students = roster_resp.json()
    today_str = date.today().isoformat()

    all_present_entries = [
        {"enrolment_id": s["enrolment_id"], "status": "present"}
        for s in students
    ]
    resp = client.post(
        "/teacher/attendance",
        json={
            "class_section_id": ids["section_10a"],
            "date": today_str,
            "entries": all_present_entries,
        },
        headers=teacher,
    )
    assert resp.status_code == 200
    db.expire_all()

    enrolment_ids = [s["enrolment_id"] for s in students]
    db_rows = list(
        db.scalars(
            select(Attendance).where(
                Attendance.enrolment_id.in_(enrolment_ids),
                Attendance.date == date.today(),
            )
        )
    )
    assert all(r.status == AttendanceStatus.present for r in db_rows)


def test_attendance_future_date_rejected(client, teacher, ids):
    """Submitting attendance for a future date must be rejected with 400."""
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/teacher/attendance",
        json={
            "class_section_id": ids["section_10a"],
            "date": tomorrow_str,
            "entries": [{"student_id": ids["student_1"], "status": "present"}],
        },
        headers=teacher,
    )
    assert resp.status_code == 400
    assert "future date" in resp.json()["detail"].lower()


def test_teacher_homework_lifecycle_and_grading(client, teacher, student, other_teacher, db, ids):
    """Teacher creates homework with attachment URL, student submits, teacher grades via drawer, and other teacher is blocked."""
    # 1. Teacher creates assignment with attachment URL
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Quadratic Equations Set B",
            "description": "Solve problems 1 to 5 from chapter 4",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
            "attachment_url": "https://cdn.sunrisepublic.edu/assignments/quadratics.pdf",
        },
        headers=teacher,
    )
    assert hw_resp.status_code == 201
    hw_data = hw_resp.json()
    hw_id = hw_data["id"]
    assert hw_data["attachment_url"] == "https://cdn.sunrisepublic.edu/assignments/quadratics.pdf"

    # 2. Student submits homework
    client.post(
        f"/student/homework/{hw_id}/submit",
        json={
            "answer_text": "Completed roots x = 2 and x = -3",
            "attachment_url": "https://cdn.sunrisepublic.edu/submissions/ans_set_b.pdf",
        },
        headers=student,
    )

    # 3. List submissions
    subs_resp = client.get(f"/teacher/homework/{hw_id}/submissions", headers=teacher)
    assert subs_resp.status_code == 200
    subs = subs_resp.json()
    sub_row = next(s for s in subs if s["student_id"] == ids["student_1"])
    assert sub_row["submitted"] is True
    assert sub_row["answer_text"] == "Completed roots x = 2 and x = -3"
    sub_id = sub_row["id"]

    # 4. Teacher grades submission via PATCH
    grade_resp = client.patch(
        f"/teacher/homework/submissions/{sub_id}",
        json={"marks": "24.5", "remarks": "Excellent derivation"},
        headers=teacher,
    )
    assert grade_resp.status_code == 200
    graded_data = grade_resp.json()
    assert graded_data["marks"] == "24.50" or float(graded_data["marks"]) == 24.5
    assert graded_data["remarks"] == "Excellent derivation"
    assert graded_data["graded_at"] is not None

    # Direct DB assertion
    db.expire_all()
    sub_db = db.get(HomeworkSubmission, sub_id)
    assert sub_db.marks == Decimal("24.50")
    assert sub_db.remarks == "Excellent derivation"
    assert sub_db.graded_at is not None

    # 5. Teacher section isolation: other_teacher cannot grade or view submissions
    unauth_resp = client.patch(
        f"/teacher/homework/submissions/{sub_id}",
        json={"marks": "10.0", "remarks": "Tampered"},
        headers=other_teacher,
    )
    assert unauth_resp.status_code in (403, 404)


def test_mobile_marks_entry_by_paper_roster(client, teacher, db, ids):
    """Teacher resolves paper roster, inputs marks against enrolment_id, validates <= max_marks, and upserts."""
    paper = (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == ids["section_10a"],
            ExamSchedule.subject_id == ids["maths"],
        )
        .order_by(ExamSchedule.max_marks.desc())
        .first()
    )
    assert paper is not None

    # 1. Fetch roster by exam, class, and subject path
    roster_url = (
        f"/teacher/exams/{paper.exam_id}"
        f"/classes/{ids['section_10a']}"
        f"/subjects/{ids['maths']}/roster"
    )
    r = client.get(roster_url, headers=teacher)
    assert r.status_code == 200, r.text
    roster_rows = r.json()
    assert len(roster_rows) > 0
    assert all("enrolment_id" in row for row in roster_rows)

    target_student = roster_rows[0]
    enrolment_id = target_student["enrolment_id"]
    max_m = float(paper.max_marks)

    # 2. Scores exceeding max_marks must be rejected with 422
    invalid_resp = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": paper.id,
            "entries": [{"enrolment_id": enrolment_id, "marks_obtained": str(max_m + 5.0)}],
        },
        headers=teacher,
    )
    assert invalid_resp.status_code == 422

    # 3. Valid score entered
    score1 = Decimal(str(round(max_m * 0.85, 2)))
    save_resp1 = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": paper.id,
            "entries": [{"enrolment_id": enrolment_id, "marks_obtained": str(score1)}],
        },
        headers=teacher,
    )
    assert save_resp1.status_code == 200

    # DB assertion
    db.expire_all()
    m1 = db.scalar(
        select(Mark).where(Mark.exam_schedule_id == paper.id, Mark.enrolment_id == enrolment_id)
    )
    assert m1 is not None
    assert m1.marks_obtained == score1

    # 4. In-place upsert: update score to 95%
    score2 = Decimal(str(round(max_m * 0.95, 2)))
    save_resp2 = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": paper.id,
            "entries": [{"enrolment_id": enrolment_id, "marks_obtained": str(score2)}],
        },
        headers=teacher,
    )
    assert save_resp2.status_code == 200

    db.expire_all()
    m2 = db.scalar(
        select(Mark).where(Mark.exam_schedule_id == paper.id, Mark.enrolment_id == enrolment_id)
    )
    assert m2 is not None
    assert m2.marks_obtained == score2
