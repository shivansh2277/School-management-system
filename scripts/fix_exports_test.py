from pathlib import Path

test_path = Path("backend/tests/test_exports.py")
code = test_path.read_text(encoding="utf-8")

old_func = '''def test_the_roster_exports_as_csv(client, admin):
    r = client.get("/admin/students/export", headers=admin)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = _rows(r.text)
    assert len(rows) == 100  # the demo school's roll
    assert rows[0]["admission_no"] and rows[0]["full_name"]'''

new_func = '''def test_the_roster_exports_as_csv(client, admin, db, ids):
    r = client.get("/admin/students/export", headers=admin)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = _rows(r.text)
    from app.models import Student
    assert len(rows) == db.query(Student).filter_by(school_id=ids["school"]).count()
    assert rows[0]["admission_no"] and rows[0]["full_name"]'''

assert old_func in code, "old_func not found"
code = code.replace(old_func, new_func, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_exports.py successfully")
