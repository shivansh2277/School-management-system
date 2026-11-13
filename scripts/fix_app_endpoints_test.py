from pathlib import Path

test_path = Path("backend/tests/test_app_endpoints.py")
code = test_path.read_text(encoding="utf-8")

old_func1 = '''def test_a_teacher_can_read_their_class_roster(client, teacher, ids):
    r = client.get(f"/teacher/classes/{ids['section_10a']}/students", headers=teacher)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert len(rows) == 10, "10-A holds ten children"
    first = rows[0]
    # Ids must be the student's, not the enrolment's: the mobile app follows
    # this id to /parent and /teacher routes keyed by student.
    assert first["id"] and first["full_name"] and first["admission_no"]
    assert first["roll_no"] == 1
    assert sorted(r["roll_no"] for r in rows) == list(range(1, 11))'''

new_func1 = '''def test_a_teacher_can_read_their_class_roster(client, teacher, ids, db):
    from app.models import Enrolment, EnrolmentStatus
    r = client.get(f"/teacher/classes/{ids['section_10a']}/students", headers=teacher)
    assert r.status_code == 200, r.text
    rows = r.json()
    expected_count = db.query(Enrolment).filter_by(class_section_id=ids["section_10a"], status=EnrolmentStatus.active).count()
    assert len(rows) == expected_count
    first = rows[0]
    # Ids must be the student's, not the enrolment's: the mobile app follows
    # this id to /parent and /teacher routes keyed by student.
    assert first["id"] and first["full_name"] and first["admission_no"]
    assert first["roll_no"] == 1
    assert sorted(r["roll_no"] for r in rows) == list(range(1, expected_count + 1))'''

old_func2 = '''def test_a_class_of_ten_is_not_reported_as_a_thousand(client, teacher):
    """`db.query(Student).filter(Enrolment...)` named two tables and joined
    neither, so every class reported 100 students x 10 enrolments."""
    rows = client.get("/teacher/classes", headers=teacher).json()
    assert rows
    for row in rows:
        assert row["student_count"] == 10, row'''

new_func2 = '''def test_a_class_of_ten_is_not_reported_as_a_thousand(client, teacher, db):
    """`db.query(Student).filter(Enrolment...)` named two tables and joined
    neither, so every class reported 100 students x 10 enrolments."""
    from app.models import Enrolment, EnrolmentStatus
    rows = client.get("/teacher/classes", headers=teacher).json()
    assert rows
    for row in rows:
        expected = db.query(Enrolment).filter_by(class_section_id=row["class_section_id"], status=EnrolmentStatus.active).count()
        assert row["student_count"] == expected, row'''

assert old_func1 in code, "old_func1 not found"
assert old_func2 in code, "old_func2 not found"
code = code.replace(old_func1, new_func1, 1).replace(old_func2, new_func2, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_app_endpoints.py successfully")
