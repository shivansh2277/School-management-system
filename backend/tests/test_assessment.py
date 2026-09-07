import pytest

from app.services.common import grade_for


@pytest.mark.parametrize(
    ("percent", "grade"),
    [
        (100, "A1"), (91, "A1"), (90.9, "A2"), (81, "A2"), (80.9, "B1"),
        (71, "B1"), (61, "B2"), (51, "C1"), (41, "C2"), (33, "D"), (32.9, "E"), (0, "E"),
    ],
)
def test_grade_band_boundaries(db, ids, percent, grade):
    assert grade_for(db, ids["school"], percent) == grade


def paper(db, ids, subject="maths"):
    from app.models import ExamSchedule

    return (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == ids["section_10a"],
            ExamSchedule.subject_id == ids[subject],
        )
        .first()
    )


def test_marks_above_max_are_rejected_and_name_the_student(client, teacher, db, ids):
    p = paper(db, ids)
    r = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": p.id,
            "entries": [{"student_id": ids["student_1"], "marks_obtained": "150"}],
        },
        headers=teacher,
    )
    assert r.status_code == 422
    assert "Aarav" in r.json()["detail"]


def test_marks_entry_is_an_upsert(client, teacher, db, ids):
    p = paper(db, ids)
    for value in ("55", "66"):
        r = client.post(
            "/teacher/marks",
            json={
                "exam_schedule_id": p.id,
                "entries": [{"student_id": ids["student_1"], "marks_obtained": value}],
            },
            headers=teacher,
        )
        assert r.status_code == 200
    row = next(x for x in r.json() if x["student_id"] == ids["student_1"])
    assert float(row["marks_obtained"]) == 66.0

    from app.models import Mark

    assert (
        db.query(Mark)
        .filter(Mark.exam_schedule_id == p.id, Mark.student_id == ids["student_1"])
        .count()
        == 1
    )


def test_report_card_excludes_an_absent_subject_from_the_totals(client, student, db, ids):
    from app.models import Mark

    p = paper(db, ids)
    db.query(Mark).filter(
        Mark.exam_schedule_id == p.id, Mark.student_id == ids["student_1"]
    ).delete()
    db.flush()

    exams = client.get("/student/results", headers=student).json()
    card = client.get(f"/student/results/{p.exam_id}", headers=student).json()
    absent = [r for r in card["rows"] if r["marks_obtained"] is None]
    assert len(absent) == 1 and absent[0]["subject"] == "Mathematics"
    # five subjects remain, so the denominator is 500 not 600
    assert float(card["total_max"]) == 500.0
    assert exams  # the exam still appears in the list


def test_report_card_totals_and_grade_are_consistent(client, student):
    exams = client.get("/student/results", headers=student).json()
    card = client.get(f"/student/results/{exams[0]['exam_id']}", headers=student).json()
    scored = [r for r in card["rows"] if r["marks_obtained"] is not None]
    assert float(card["total_obtained"]) == sum(float(r["marks_obtained"]) for r in scored)
    assert card["overall_percent"] == round(
        float(card["total_obtained"]) / float(card["total_max"]) * 100, 1
    )
    assert card["overall_grade"] is not None


def test_parent_sees_the_same_report_card(client, student, parent, ids):
    exams = client.get("/student/results", headers=student).json()
    mine = client.get(f"/student/results/{exams[0]['exam_id']}", headers=student).json()
    theirs = client.get(
        f"/parent/children/{ids['student_1']}/results/{exams[0]['exam_id']}", headers=parent
    ).json()
    assert mine == theirs
