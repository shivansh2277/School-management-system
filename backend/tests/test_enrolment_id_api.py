"""Tests for Session 6: Backend API & Database Mutation Test Suite.

Validates:
1. Direct database assertions: verifying enrolment_id matches in the database after API calls.
2. Edge cases & boundaries: invalid enrolment_id (999999), cross-section homework rejection,
   cross-class marks entry, marks exceeding max_marks, negative marks.
3. Role boundaries: student/parent calling teacher marks or grading endpoints strictly 403.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models import (
    Enrolment,
    ExamSchedule,
    HomeworkSubmission,
    Mark,
)


def _get_10a_paper(db, ids):
    return (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == ids["section_10a"],
            ExamSchedule.subject_id == ids["maths"],
        )
        .order_by(ExamSchedule.max_marks.desc())
        .first()
    )


def test_marks_entry_populates_enrolment_id_in_db(client, teacher, db, ids):
    """Teacher marks entry using enrolment_id directly mutates the database row with that enrolment_id."""
    p = _get_10a_paper(db, ids)
    enr = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == ids["student_1"],
            Enrolment.class_section_id == ids["section_10a"],
        )
    )
    assert enr is not None

    # Post using enrolment_id
    score = Decimal(str(p.max_marks - 5))
    resp = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": p.id,
            "entries": [{"enrolment_id": enr.id, "marks_obtained": str(score)}],
        },
        headers=teacher,
    )
    assert resp.status_code == 200, resp.text

    # Direct DB assertion
    db.expire_all()
    mark = db.scalar(
        select(Mark).where(Mark.exam_schedule_id == p.id, Mark.enrolment_id == enr.id)
    )
    assert mark is not None, "Mark row must exist in database"
    assert mark.enrolment_id == enr.id
    assert mark.marks_obtained == score
    assert mark.is_absent is False
    assert mark.is_exempted is False


def test_marks_entry_rejects_nonexistent_enrolment(client, teacher, db, ids):
    """Submitting an arbitrary non-existent enrolment_id must return 404 or 422."""
    p = _get_10a_paper(db, ids)
    resp = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": p.id,
            "entries": [{"enrolment_id": 999999, "marks_obtained": "50"}],
        },
        headers=teacher,
    )
    assert resp.status_code in (404, 422), resp.text


def test_marks_entry_rejects_cross_section_enrolment(client, teacher, db, ids):
    """Entering mark for a student enrolled in 8-A on a 10-A exam paper must be rejected."""
    p = _get_10a_paper(db, ids)
    # Student 17 is enrolled in Class 8-A
    enr_8a = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == ids["student_17"],
            Enrolment.class_section_id == ids["section_8a"],
        )
    )
    assert enr_8a is not None

    resp = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": p.id,
            "entries": [{"enrolment_id": enr_8a.id, "marks_obtained": "50"}],
        },
        headers=teacher,
    )
    assert resp.status_code in (400, 403, 404, 422), resp.text


def test_marks_validation_boundaries(client, teacher, db, ids):
    """Marks exceeding max_marks or negative marks are strictly rejected with 422."""
    p = _get_10a_paper(db, ids)
    enr = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == ids["student_1"],
            Enrolment.class_section_id == ids["section_10a"],
        )
    )

    # Above max_marks
    resp_above = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": p.id,
            "entries": [{"enrolment_id": enr.id, "marks_obtained": str(p.max_marks + 1)}],
        },
        headers=teacher,
    )
    assert resp_above.status_code == 422

    # Negative marks
    resp_neg = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": p.id,
            "entries": [{"enrolment_id": enr.id, "marks_obtained": "-5"}],
        },
        headers=teacher,
    )
    assert resp_neg.status_code == 422


def test_student_homework_submission_populates_enrolment_id(client, teacher, student, db, ids):
    """Student submitting homework creates a DB row with their active enrolment_id."""
    # Teacher creates homework
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Algebra Practice Chapter 4",
            "description": "Complete problems 1 through 10",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
            "attachment_url": "https://storage.sunrisepublic.edu/hw/ch4.pdf",
        },
        headers=teacher,
    )
    assert hw_resp.status_code == 201
    hw_id = hw_resp.json()["id"]

    # Student submits homework
    sub_resp = client.post(
        f"/student/homework/{hw_id}/submit",
        json={
            "answer_text": "Completed all 10 problems on notebook pages 45-48",
            "attachment_url": "https://storage.sunrisepublic.edu/sub/student1_ch4.pdf",
        },
        headers=student,
    )
    assert sub_resp.status_code == 200, sub_resp.text

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
    assert sub_db is not None, "Submission row must exist in database"
    assert sub_db.enrolment_id == enr.id
    assert sub_db.student_id == ids["student_1"]
    assert sub_db.attachment_url == "https://storage.sunrisepublic.edu/sub/student1_ch4.pdf"


def test_cross_section_homework_submission_rejected(client, teacher, other_student, ids):
    """Student in 8-A cannot submit homework assigned to 10-A."""
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Geometry Theorem 5",
            "description": "Prove theorem 5.1",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
        },
        headers=teacher,
    )
    assert hw_resp.status_code == 201
    hw_id = hw_resp.json()["id"]

    # other_student is in 8-A
    sub_resp = client.post(
        f"/student/homework/{hw_id}/submit",
        json={"answer_text": "Trying to submit from wrong class"},
        headers=other_student,
    )
    assert sub_resp.status_code in (403, 404, 422), sub_resp.text


def test_teacher_grades_homework_submission_db_assertion(client, teacher, student, db, ids):
    """Grading homework updates marks, remarks, and graded_at in the database."""
    hw_resp = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["maths"],
            "title": "Calculus Foundations",
            "description": "Limits and continuity",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
        },
        headers=teacher,
    )
    hw_id = hw_resp.json()["id"]

    client.post(
        f"/student/homework/{hw_id}/submit",
        json={"answer_text": "Here are the solutions."},
        headers=student,
    )

    # List submissions to get submission ID
    subs = client.get(f"/teacher/homework/{hw_id}/submissions", headers=teacher).json()
    my_sub = next(s for s in subs if s["student_id"] == ids["student_1"])
    sub_id = my_sub["submission_id"]

    # Teacher grades via PATCH
    grade_resp = client.patch(
        f"/teacher/homework/submissions/{sub_id}",
        json={"marks": "18.5", "remarks": "Very well reasoned solutions!"},
        headers=teacher,
    )
    assert grade_resp.status_code == 200, grade_resp.text

    # Direct DB assertion
    db.expire_all()
    sub_row = db.get(HomeworkSubmission, sub_id)
    assert sub_row is not None
    assert sub_row.marks == Decimal("18.5")
    assert sub_row.remarks == "Very well reasoned solutions!"
    assert sub_row.graded_at is not None


def test_unauthorized_roles_blocked_from_mutating_marks_and_grading(client, student, parent, ids):
    """Students and parents are strictly blocked from teacher marks entry and homework grading."""
    # Student attempting to enter marks
    m_resp = client.post(
        "/teacher/marks",
        json={"exam_schedule_id": 1, "entries": [{"enrolment_id": 1, "marks_obtained": "100"}]},
        headers=student,
    )
    assert m_resp.status_code == 403

    # Parent attempting to enter marks
    p_resp = client.post(
        "/teacher/marks",
        json={"exam_schedule_id": 1, "entries": [{"enrolment_id": 1, "marks_obtained": "100"}]},
        headers=parent,
    )
    assert p_resp.status_code == 403

    # Student attempting to grade homework
    g_resp = client.patch(
        "/teacher/homework/submissions/1",
        json={"marks": "20.0", "remarks": "Self graded"},
        headers=student,
    )
    assert g_resp.status_code == 403
