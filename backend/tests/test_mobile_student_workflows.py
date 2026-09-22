"""Tests for Session 6: Student Mobile Workflow Test Suite.

Validates the student portal workflows:
1. Class Timetable Resolution:
   - GET /student/timetable returns slots for student's active class section and academic year.
2. Digital Homework Turn-In & Grading Reflection:
   - GET /student/homework?status=pending lists assigned homework.
   - POST /student/homework/{id}/submit submits text and attachment_url.
   - Direct DB assertion verifying HomeworkSubmission.enrolment_id.
   - Cross-class restriction: student from 8-A cannot submit 10-A homework.
   - Teacher grading reflects on student homework list with marks and remarks.
3. Academic Marks & Term Results:
   - GET /student/results and GET /student/results/{exam_id} return subject scorecards.
"""

from datetime import date, timedelta

from sqlalchemy import select

from app.models import Enrolment, HomeworkSubmission


def test_student_timetable_resolution(client, student, ids):
    """GET /student/timetable returns period slots matching the student's active class section."""
    resp = client.get("/student/timetable", headers=student)
    assert resp.status_code == 200, resp.text
    slots = resp.json()
    assert len(slots) > 0
    # Every slot must belong to 10-A
    assert all(s["class_section_id"] == ids["section_10a"] for s in slots)
    assert all("subject" in s and "day_of_week" in s for s in slots)


def test_student_homework_turn_in_and_db_assertion(client, student, teacher, db, ids):
    """Student views pending homework, turns in with attachment, and DB row is verified against enrolment_id."""
    # Teacher assigns homework
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Trigonometry Heights and Distances",
            "description": "Exercise 9.1 questions 1 to 8",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
            "attachment_url": "https://storage.sunrisepublic.edu/hw/trig_ex9.pdf",
        },
        headers=teacher,
    )
    assert hw_resp.status_code == 201
    hw_id = hw_resp.json()["id"]

    # Student checks pending list
    pending = client.get("/student/homework?status=pending", headers=student).json()
    assert any(h["id"] == hw_id for h in pending)

    # Student submits digital turn-in
    turn_in_resp = client.post(
        f"/student/homework/{hw_id}/submit",
        json={
            "answer_text": "Completed all 8 problems with angle diagrams attached.",
            "attachment_url": "https://storage.sunrisepublic.edu/submissions/trig_sol.pdf",
        },
        headers=student,
    )
    assert turn_in_resp.status_code == 200, turn_in_resp.text
    sub_out = turn_in_resp.json()
    assert sub_out["submitted"] is True
    assert sub_out["answer_text"] == "Completed all 8 problems with angle diagrams attached."

    # Verify student pending list no longer shows it, but submitted list does
    pending_after = client.get("/student/homework?status=pending", headers=student).json()
    assert not any(h["id"] == hw_id for h in pending_after)
    submitted_after = client.get("/student/homework?status=submitted", headers=student).json()
    assert any(h["id"] == hw_id for h in submitted_after)

    # Direct DB assertion
    enr = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == ids["student_1"],
            Enrolment.class_section_id == ids["section_10a"],
        )
    )
    db.expire_all()
    sub_db = db.scalar(
        select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == hw_id,
            HomeworkSubmission.enrolment_id == enr.id,
        )
    )
    assert sub_db is not None
    assert sub_db.enrolment_id == enr.id
    assert sub_db.attachment_url == "https://storage.sunrisepublic.edu/submissions/trig_sol.pdf"


def test_cross_class_homework_rejection(client, other_student, teacher, ids):
    """Student from 8-A cannot turn in homework assigned to 10-A."""
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Quadratic Equations Set C",
            "description": "Exclusive to 10-A",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
        },
        headers=teacher,
    )
    assert hw_resp.status_code == 201
    hw_id = hw_resp.json()["id"]

    # other_student is in 8-A
    sub_resp = client.post(
        f"/student/homework/{hw_id}/submit",
        json={"answer_text": "Trying to submit across class boundaries"},
        headers=other_student,
    )
    assert sub_resp.status_code in (403, 404, 422)


def test_homework_grading_reflection_on_student_portal(client, student, teacher, db, ids):
    """Teacher grades submission and student portal reflects marks, remarks, and graded status."""
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Coordinate Geometry Unit 7",
            "description": "Section formula problems",
            "due_date": (date.today() + timedelta(days=4)).isoformat(),
        },
        headers=teacher,
    )
    hw_id = hw_resp.json()["id"]

    client.post(
        f"/student/homework/{hw_id}/submit",
        json={"answer_text": "Solved all internal division problems."},
        headers=student,
    )

    # Teacher gets submission and grades it
    subs = client.get(f"/teacher/homework/{hw_id}/submissions", headers=teacher).json()
    sub_row = next(s for s in subs if s["student_id"] == ids["student_1"])
    sub_id = sub_row.get("submission_id") or sub_row.get("id")

    grade_resp = client.patch(
        f"/teacher/homework/submissions/{sub_id}",
        json={"marks": "23.0", "remarks": "Clear step-by-step working!"},
        headers=teacher,
    )
    assert grade_resp.status_code == 200

    # Student checks homework list
    my_hw = client.get("/student/homework?status=all", headers=student).json()
    matched = next(h for h in my_hw if h["id"] == hw_id)
    assert matched["submitted"] is True
    assert float(matched["marks"]) == 23.0
    assert matched["remarks"] == "Clear step-by-step working!"
    assert matched["graded_at"] is not None


def test_student_academic_marks_and_scorecard(client, student):
    """Student views overall exam results and detailed subject scorecard."""
    res = client.get("/student/results", headers=student)
    assert res.status_code == 200, res.text
    exams = res.json()
    assert len(exams) > 0

    first_exam = exams[0]
    assert "exam_id" in first_exam
    assert "overall_percent" in first_exam

    # Detailed report card
    card_resp = client.get(f"/student/results/{first_exam['exam_id']}", headers=student)
    assert card_resp.status_code == 200
    card = card_resp.json()
    assert "rows" in card
    assert "total_obtained" in card
    assert "total_max" in card
    assert len(card["rows"]) > 0
