"""Negative tests for every deny in the BLUEPRINT §9 RBAC matrix.

These are written first on purpose: they are the part that matters if a school
ever runs this.
"""

from datetime import date, timedelta


def test_no_token_is_401(client):
    assert client.get("/student/dashboard").status_code == 401


def test_correct_credentials_through_the_wrong_role_tab(client):
    r = client.post(
        "/auth/login",
        json={"role": "teacher", "login_id": "SPS2024001", "password": "Student@123"},
    )
    assert r.status_code == 401


def test_admin_cannot_log_in_through_a_mobile_role_tab(client):
    for role in ("teacher", "student", "parent"):
        r = client.post(
            "/auth/login",
            json={"role": role, "login_id": "admin@sunrisepublic.edu", "password": "Admin@123"},
        )
        assert r.status_code == 401


def test_student_cannot_log_in_through_the_web_admin_tab(client):
    r = client.post(
        "/auth/login",
        json={"role": "admin", "login_id": "SPS2024001", "password": "Student@123"},
    )
    assert r.status_code == 401


def test_student_cannot_read_another_students_results(client, student, ids):
    r = client.get(f"/parent/children/{ids['student_17']}/results", headers=student)
    assert r.status_code == 403


def test_student_only_sees_their_own_class_homework(client, student, other_student):
    mine = {h["id"] for h in client.get("/student/homework", headers=student).json()}
    theirs = {h["id"] for h in client.get("/student/homework", headers=other_student).json()}
    assert mine and theirs and not (mine & theirs)


def test_student_cannot_submit_homework_for_another_section(client, student, other_student):
    theirs = client.get("/student/homework", headers=other_student).json()
    r = client.post(
        f"/student/homework/{theirs[0]['id']}/submit",
        json={"answer_text": "not mine"},
        headers=student,
    )
    assert r.status_code == 403


def test_parent_cannot_read_a_child_that_is_not_theirs(client, other_parent, ids):
    r = client.get(f"/parent/children/{ids['student_1']}/attendance", headers=other_parent)
    assert r.status_code == 403


def test_parent_cannot_submit_homework(client, parent):
    r = client.post("/student/homework/1/submit", json={"answer_text": "x"}, headers=parent)
    assert r.status_code in (403, 405)


def test_teacher_cannot_mark_attendance_for_a_section_they_do_not_teach(
    client, other_teacher, ids, db
):
    from app.models import Student

    roster = db.query(Student).filter(Student.class_section_id == ids["section_10a"]).all()
    body = {
        "class_section_id": ids["section_10a"],
        "date": date.today().isoformat(),
        "entries": [{"student_id": s.id, "status": "present"} for s in roster],
    }
    r = client.post("/teacher/attendance", json=body, headers=other_teacher)
    assert r.status_code == 403


def test_teacher_cannot_enter_marks_for_a_paper_outside_their_subject(
    client, teacher, other_teacher, db, ids
):
    from app.models import ExamSchedule

    paper = (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == ids["section_10a"],
            ExamSchedule.subject_id == ids["maths"],
        )
        .first()
    )
    assert client.get(f"/teacher/marks?exam_schedule_id={paper.id}", headers=teacher).status_code == 200
    r = client.get(f"/teacher/marks?exam_schedule_id={paper.id}", headers=other_teacher)
    assert r.status_code == 403


def test_teacher_cannot_publish_to_a_section_they_do_not_teach(client, teacher, ids):
    r = client.post(
        "/teacher/announcements",
        json={"title": "x", "body": "y", "class_section_id": ids["section_9a"]},
        headers=teacher,
    )
    assert r.status_code == 403


def test_teacher_cannot_publish_a_school_wide_audience(client, teacher, ids):
    for audience in ("all", "students", "parents", "teachers"):
        r = client.post(
            "/teacher/announcements",
            json={
                "title": "x",
                "body": "y",
                "class_section_id": ids["section_10a"],
                "audience": audience,
            },
            headers=teacher,
        )
        assert r.status_code == 403, audience


def test_teacher_cannot_create_homework_for_a_subject_they_do_not_own(client, teacher, ids):
    r = client.post(
        "/teacher/homework",
        json={
            "class_section_id": ids["section_10a"],
            "subject_id": ids["hindi"],
            "title": "x",
            "due_date": (date.today() + timedelta(days=1)).isoformat(),
        },
        headers=teacher,
    )
    assert r.status_code == 403


def test_students_and_parents_cannot_reach_admin_routes(client, student, parent):
    for headers in (student, parent):
        assert client.get("/admin/dashboard/stats", headers=headers).status_code == 403
        assert client.get("/admin/students", headers=headers).status_code == 403


def test_teacher_cannot_reach_admin_routes(client, teacher):
    assert client.get("/admin/fees/invoices", headers=teacher).status_code == 403


def test_admin_cannot_mark_attendance(client, admin):
    # There is no admin write endpoint at all — read only (BLUEPRINT §9 matrix).
    assert client.post("/teacher/attendance", json={}, headers=admin).status_code == 403
