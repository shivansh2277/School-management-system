from pathlib import Path

p = Path("backend/tests/test_academic_coordinator_rbac.py")
content = p.read_text(encoding="utf-8")

test_code = """

def test_academic_coordinator_can_configure_break_period(client, academic_coordinator, db):
    \"\"\"Break period must not be hardcoded: it can be configured dynamically.\"\"\"
    # 1. Fetch periods and check that Period 3 is currently configured as a break
    periods = client.get("/admin/timetable/periods", headers=academic_coordinator).json()
    p3 = next(p for p in periods if p["period_no"] == 3)
    assert p3["is_break"] is True, "Period 3 should be configured as break"

    # 2. Update Period 3 to custom break label and timing
    res = client.put(
        f"/admin/timetable/periods/{p3['id']}",
        json={
            "name": "Mid-Morning Recess",
            "is_break": True,
        },
        headers=academic_coordinator,
    )
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["name"] == "Mid-Morning Recess"
    assert res.json()["is_break"] is True

    # 3. Verify audit log recorded the update
    audit_update = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "school_period",
            AuditLog.entity_id == p3["id"],
            AuditLog.action == "update",
        ).order_by(AuditLog.id.desc())
    ).first()
    assert audit_update is not None
    assert audit_update.after["name"] == "Mid-Morning Recess"
    assert audit_update.after["is_break"] is True

    # 4. Verify scheduling conflict occurs when trying to place a lesson in the break
    sections = client.get("/admin/classes", headers=academic_coordinator).json()
    teachers = client.get("/admin/teachers", headers=academic_coordinator).json()
    subjects = client.get("/admin/subjects", headers=academic_coordinator).json()
    check_res = client.post(
        "/admin/timetable/slots/check",
        json={
            "class_section_id": sections[0]["id"],
            "day_of_week": "mon",
            "period_id": p3["id"],
            "subject_id": subjects[0]["id"],
            "teacher_id": teachers[0]["id"],
        },
        headers=academic_coordinator,
    )
    assert check_res.status_code == status.HTTP_200_OK
    kinds = [c["kind"] for c in check_res.json()["conflicts"]]
    assert "break" in kinds

    # 5. Reset back to clean "Break"
    client.put(
        f"/admin/timetable/periods/{p3['id']}",
        json={"name": "Break", "is_break": True},
        headers=academic_coordinator,
    )
"""

if "test_academic_coordinator_can_configure_break_period" not in content:
    content += test_code
    p.write_text(content, encoding="utf-8")
    print("Added test_academic_coordinator_can_configure_break_period")
