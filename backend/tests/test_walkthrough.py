"""The BLUEPRINT section 13 cross-role walkthrough, executed end to end.

Each numbered step below is the same step a reviewer is walked through live.
If this test passes, the demo works; if any link were mocked, it would fail.
"""

from datetime import date, timedelta


def test_cross_role_walkthrough(client, admin, teacher, student, parent, db, ids):
    from app.models import Enrolment, Student

    section = ids["section_10a"]
    today = date.today().isoformat()
    roster = (
        db.query(Student)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .filter(Enrolment.class_section_id == section)
        .order_by(Enrolment.roll_no)
        .all()
    )
    absent_two = {roster[0].id, roster[1].id}

    # 1. Employee marks two students absent for 10-A today.
    entries = [
        {"student_id": s.id, "status": "absent" if s.id in absent_two else "present"}
        for s in roster
    ]
    r = client.post(
        "/teacher/attendance",
        json={"class_section_id": section, "date": today, "entries": entries},
        headers=teacher,
    )
    assert r.status_code == 200

    # 2. Admin dashboard reflects those absences (same database row).
    roll = client.get(
        f"/admin/attendance?class_section_id={section}&date={today}", headers=admin
    ).json()
    assert sum(1 for row in roll if row["status"] == "absent") == 2

    # 3. The absent student sees Absent for today.
    mine = client.get("/student/attendance", headers=student).json()
    assert {"date": today, "status": "absent"} in mine["days"]

    # 4. Their parent sees the same absence.
    theirs = client.get(
        f"/parent/children/{ids['student_1']}/attendance", headers=parent
    ).json()
    assert {"date": today, "status": "absent"} in theirs["days"]

    # 5. Employee creates homework for 10-A / Mathematics, due tomorrow.
    hw = client.post(
        "/teacher/homework",
        json={
            "class_section_id": section,
            "subject_id": ids["maths"],
            "title": "Walkthrough assignment",
            "description": "Solve the exercise.",
            "due_date": (date.today() + timedelta(days=1)).isoformat(),
        },
        headers=teacher,
    )
    assert hw.status_code == 201
    hw_id = hw.json()["id"]

    # 6. Student sees it pending, then submits an answer.
    pending = client.get("/student/homework?status=pending", headers=student).json()
    assert hw_id in {h["id"] for h in pending}
    submitted = client.post(
        f"/student/homework/{hw_id}/submit",
        json={"answer_text": "Here is my answer."},
        headers=student,
    )
    assert submitted.status_code == 200 and submitted.json()["submitted"] is True

    # 7. Employee's submission list shows that student as Submitted.
    rows = client.get(f"/teacher/homework/{hw_id}/submissions", headers=teacher).json()
    theirs_row = next(r for r in rows if r["student_id"] == ids["student_1"])
    assert theirs_row["submitted"] is True and theirs_row["late"] is False

    # 8. Guardian's submitted count includes it.
    child_hw = client.get(
        f"/parent/children/{ids['student_1']}/homework", headers=parent
    ).json()
    assert next(h for h in child_hw if h["id"] == hw_id)["submitted"] is True

    # 9. Admin creates an exam and adds a Mathematics paper for 10-A.
    exam = client.post(
        "/admin/exams",
        json={
            "name": "Term 1 - Unit Test 2",
            "term": "Term 1",
            "start_date": today,
            "end_date": today,
        },
        headers=admin,
    ).json()
    paper = client.post(
        f"/admin/exams/{exam['id']}/schedule",
        json={
            "class_section_id": section,
            "subject_id": ids["maths"],
            "exam_date": today,
            "max_marks": "50.00",
        },
        headers=admin,
    )
    assert paper.status_code == 201
    paper_id = paper.json()["id"]

    # 10. Employee enters marks; above max is rejected.
    too_high = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": paper_id,
            "entries": [{"student_id": ids["student_1"], "marks_obtained": "51"}],
        },
        headers=teacher,
    )
    assert too_high.status_code == 422
    ok = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": paper_id,
            "entries": [{"student_id": s.id, "marks_obtained": "44"} for s in roster],
        },
        headers=teacher,
    )
    assert ok.status_code == 200

    # 11. Student's report card shows the subject, percentage and grade.
    card = client.get(f"/student/results/{exam['id']}", headers=student).json()
    row = next(r for r in card["rows"] if r["subject"] == "Mathematics")
    assert float(row["marks_obtained"]) == 44.0
    assert row["percent"] == 88.0 and row["grade"] == "A2"

    # 12. Guardian sees the same report card.
    assert (
        client.get(
            f"/parent/children/{ids['student_1']}/results/{exam['id']}", headers=parent
        ).json()
        == card
    )

    # 13. Admin generates invoices for a fresh month.
    generated = client.post(
        "/admin/fees/invoices/generate", json={"month": 12, "year": 2026}, headers=admin
    ).json()
    assert generated["created"] == db.query(Student).count()

    # 14. Guardian pays one and downloads the PDF receipt.
    before = client.get("/admin/fees/collection?year=2026", headers=admin).json()
    invoice = next(
        i
        for i in client.get("/parent/fees", headers=parent).json()
        if i["status"] != "paid" and i["year"] == 2026 and i["month"] == 12
    )
    payment = client.post(f"/parent/fees/{invoice['id']}/pay", headers=parent)
    assert payment.status_code == 200
    assert (
        next(
            i for i in client.get("/parent/fees", headers=parent).json() if i["id"] == invoice["id"]
        )["status"]
        == "paid"
    )
    pdf = client.get(f"/parent/fees/{invoice['id']}/receipt.pdf", headers=parent)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    # 15. The admin collection total rose by exactly that amount.
    after = client.get("/admin/fees/collection?year=2026", headers=admin).json()
    assert float(after["collected"]) - float(before["collected"]) == float(invoice["amount"])

    # 16. An admin notice to "parents" reaches the parent and not the student.
    notice = client.post(
        "/admin/notices",
        json={"title": "PTM reminder", "body": "Saturday 10 AM.", "audience": "parents"},
        headers=admin,
    ).json()
    assert notice["id"] in {n["id"] for n in client.get("/parent/notices", headers=parent).json()}
    assert notice["id"] not in {
        n["id"] for n in client.get("/student/notices", headers=student).json()
    }
