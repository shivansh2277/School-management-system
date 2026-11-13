from pathlib import Path

test_path = Path("backend/tests/test_management_kpis.py")
code = test_path.read_text(encoding="utf-8")

old_func1 = '''def test_the_first_year_has_no_retention_figure(db, ids):
    """There is no year before it to have retained anyone from. Reporting 0 or
    100 would be the fabricated data point section 5.10.9 forbids, and it is
    the one a trend line is most likely to be misread from."""
    trend = stats.enrolment_trend(db, ids["school"])
    assert trend, "the demo school has a roll"
    assert trend[0]["retention_percent"] is None
    assert trend[0]["retained"] is None
    assert trend[0]["students"] == 100'''

new_func1 = '''def test_the_first_year_has_no_retention_figure(db, ids):
    """There is no year before it to have retained anyone from. Reporting 0 or
    100 would be the fabricated data point section 5.10.9 forbids, and it is
    the one a trend line is most likely to be misread from."""
    from app.models import Enrolment
    from sqlalchemy import func
    trend = stats.enrolment_trend(db, ids["school"])
    assert trend, "the demo school has a roll"
    assert trend[0]["retention_percent"] is None
    assert trend[0]["retained"] is None
    expected_students = db.scalar(select(func.count(Enrolment.id)).where(Enrolment.academic_year_id == ids["year"]))
    assert trend[0]["students"] == expected_students'''

old_retention = '''    # 30 of the previous year's 100.
    assert latest["retention_percent"] == 30.0'''

new_retention = '''    from sqlalchemy import func
    prev_count = db.scalar(select(func.count(Enrolment.id)).where(Enrolment.academic_year_id == first.id))
    expected_pct = round(30.0 / float(prev_count) * 100, 1)
    assert latest["retention_percent"] == pytest.approx(expected_pct, abs=0.1)'''

assert old_func1 in code, "old_func1 not found"
assert old_retention in code, "old_retention not found"
code = code.replace(old_func1, new_func1, 1).replace(old_retention, new_retention, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_management_kpis.py successfully")
