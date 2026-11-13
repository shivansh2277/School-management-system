from pathlib import Path

test_path = Path("backend/tests/test_attendance_scope.py")
code = test_path.read_text(encoding="utf-8")

old_func = '''def test_the_office_still_reads_every_child(client, admin):
    body = client.get("/admin/students", headers=admin, params={"page_size": 200}).json()
    assert body["total"] == 100'''

new_func = '''def test_the_office_still_reads_every_child(client, admin, db, ids):
    from app.models import Student
    body = client.get("/admin/students", headers=admin, params={"page_size": 200}).json()
    assert body["total"] == db.query(Student).filter_by(school_id=ids["school"]).count()'''

assert old_func in code, "old_func not found"
code = code.replace(old_func, new_func, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_attendance_scope.py successfully")
