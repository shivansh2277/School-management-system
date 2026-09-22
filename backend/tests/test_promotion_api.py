from datetime import date

import pytest
from sqlalchemy import select

from app.models import (
    AcademicYear,
    AcademicYearStatus,
    AuditLog,
    ClassSection,
)
from app.services.common import roster


@pytest.fixture()
def next_year(db):
    year = AcademicYear(
        school_id=1,
        code="2026-27",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.planning,
    )
    db.add(year)
    db.flush()
    return year


def make_section(db, year, class_name, section="A"):
    cs = ClassSection(
        school_id=1, academic_year_id=year.id, class_name=class_name, section=section
    )
    db.add(cs)
    db.flush()
    return cs


def test_promotion_years_and_sections_api(client, admin, ids, next_year):
    r = client.get("/admin/promotion/years", headers=admin)
    assert r.status_code == 200
    years = r.json()
    assert any(y["code"] == "2026-27" for y in years)

    r_sec = client.get("/admin/promotion/sections", headers=admin)
    assert r_sec.status_code == 200
    sections = r_sec.json()
    assert any(s["id"] == ids["section_10a"] for s in sections)


def test_promotion_preview_api(client, admin, ids, next_year, db):
    make_section(db, next_year, "11")
    r = client.post(
        "/admin/promotion/preview",
        headers=admin,
        json={"class_section_id": ids["section_10a"], "to_year_id": next_year.id},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["can_commit"] is True
    assert data["from_section"] == "10-A"
    assert data["to_section"] == "11-A"
    assert len(data["lines"]) > 0
    assert data["blockers"] == []


def test_promotion_preview_blocker_api(client, admin, ids, next_year):
    # Target section "11-A" does not exist in next_year
    r = client.post(
        "/admin/promotion/preview",
        headers=admin,
        json={"class_section_id": ids["section_10a"], "to_year_id": next_year.id},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["can_commit"] is False
    assert len(data["blockers"]) > 0


def test_promotion_commit_and_audit_api(client, admin, ids, next_year, db):
    make_section(db, next_year, "11")
    before_count = len(roster(db, ids["section_10a"]))

    r = client.post(
        "/admin/promotion/commit",
        headers=admin,
        json={
            "class_section_id": ids["section_10a"],
            "to_year_id": next_year.id,
            "reason": "Annual session rollover test",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["can_commit"] is True
    assert len(data["lines"]) == before_count

    # Verify audit log
    audit_entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "enrolment",
            AuditLog.entity_id == ids["section_10a"],
        )
    )
    assert audit_entry is not None
    assert "Annual session rollover" in (audit_entry.reason or "")


def test_promotion_with_outcomes_override_api(client, admin, ids, next_year, db):
    make_section(db, next_year, "11")
    make_section(db, next_year, "10")
    students = roster(db, ids["section_10a"])
    detained_sid = students[0].student_id

    r = client.post(
        "/admin/promotion/commit",
        headers=admin,
        json={
            "class_section_id": ids["section_10a"],
            "to_year_id": next_year.id,
            "outcomes": {str(detained_sid): "detain"},
        },
    )
    assert r.status_code == 200
    detained_line = next(row for row in r.json()["lines"] if row["student_id"] == detained_sid)
    assert detained_line["outcome"] == "detain"


def test_promotion_permissions(client, teacher, ids, next_year):
    # Teacher does not have academics.class.read or students.enrolment.promote
    r1 = client.get("/admin/promotion/years", headers=teacher)
    assert r1.status_code == 403

    r2 = client.post(
        "/admin/promotion/commit",
        headers=teacher,
        json={"class_section_id": ids["section_10a"], "to_year_id": next_year.id},
    )
    assert r2.status_code == 403
