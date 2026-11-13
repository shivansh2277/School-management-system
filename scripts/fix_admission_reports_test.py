from pathlib import Path

test_path = Path("backend/tests/test_admission_reports.py")
code = test_path.read_text(encoding="utf-8")

old_func = '''def test_the_funnel_starts_at_enquiries_and_narrows(client, admin, cycle_id):
    """Most enquiries never become anything, and that ratio is the number the
    module exists to improve (§5.1.2(1))."""
    _applicant(client, admin, "FunnelOne", "9833300001")
    body = client.get(
        f"/admin/admission/cycles/{cycle_id}/reports", headers=admin
    ).json()["funnel"]

    stages = {s["stage"]: s["count"] for s in body["stages"]}
    assert stages["enquiries"] >= 6  # the seeded register
    assert stages["applied"] >= 1
    assert stages["enrolled"] == 0
    # Each stage reports what fraction of the one before it survived.
    assert body["stages"][1]["of_previous"] is not None
    assert body["overall_conversion_pct"] == 0.0'''

new_func = '''def test_the_funnel_starts_at_enquiries_and_narrows(client, admin, cycle_id, db):
    """Most enquiries never become anything, and that ratio is the number the
    module exists to improve (§5.1.2(1))."""
    from sqlalchemy import func
    from app.models import Application, ApplicationStatus

    _applicant(client, admin, "FunnelOne", "9833300001")
    body = client.get(
        f"/admin/admission/cycles/{cycle_id}/reports", headers=admin
    ).json()["funnel"]

    expected_enrolled = db.scalar(
        select(func.count(Application.id)).where(
            Application.cycle_id == cycle_id,
            Application.status == ApplicationStatus.enrolled,
        )
    )
    stages = {s["stage"]: s["count"] for s in body["stages"]}
    assert stages["enquiries"] >= 6  # the seeded register
    assert stages["applied"] >= 1
    assert stages["enrolled"] == expected_enrolled
    # Each stage reports what fraction of the one before it survived.
    assert body["stages"][1]["of_previous"] is not None
    expected_pct = round(float(expected_enrolled) / float(stages["enquiries"]) * 100, 1)
    assert body["overall_conversion_pct"] == pytest.approx(expected_pct, abs=0.1)'''

assert old_func in code, "old_func not found"
code = code.replace(old_func, new_func, 1)
test_path.write_text(code, encoding="utf-8")
print("Updated test_admission_reports.py successfully")
