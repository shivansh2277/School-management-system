from pathlib import Path

test_path = Path("backend/tests/test_stats.py")
code = test_path.read_text(encoding="utf-8")

old_func = '''def test_performance_buckets_cover_every_scored_student(client, admin, db):
    from app.models import Student

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    buckets = stats["performance"]
    assert sum(buckets.values()) == db.query(Student).count()
    assert all(v > 0 for v in buckets.values()), buckets  # seed must populate all four'''

new_func = '''def test_performance_buckets_cover_every_scored_student(client, admin, db):
    from app.services import assessment, stats as stats_svc

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    buckets = stats["performance"]
    exam = assessment.latest_exam_with_marks(db, 1)
    expected_scored = len(stats_svc.exam_percentages(db, exam.id)) if exam else 0
    assert sum(buckets.values()) == expected_scored
    assert all(v > 0 for v in buckets.values()), buckets  # seed must populate all four'''

assert old_func in code, "old_func not found"
code = code.replace(old_func, new_func, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_stats.py successfully")
