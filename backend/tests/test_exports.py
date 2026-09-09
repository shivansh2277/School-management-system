"""Bulk export: the permission that gated nothing, and the audit nobody wrote.

Two controls existed in the vocabulary and were enforced nowhere before this
module. `students.profile.export` was granted to the Admin Officer and required
by no route, so ERP_BLUEPRINT section 10.2's separation between "may see this
on screen" and "may download two thousand of them" was decorative.
`AuditAction.export` had been in the enum since Part 1 with zero callers, so
section 5.10.9's requirement that exports of personal data be audited was
unmet.

These tests are what make both real. Deleting either route dependency, or the
`record_export` call, fails something here.
"""

import csv
import io

from sqlalchemy import select

from app.models import AuditAction, AuditLog

# The rival school and one child on its roll, so an export can be checked
# against the tenant boundary the roster tests already plant.
from tests.test_tenant_isolation import rival, rival_student  # noqa: F401


def _rows(body: str) -> list[dict]:
    """CSV rows, skipping the section 5.10.9 context line."""
    lines = body.splitlines()
    assert lines[0].startswith("#")
    return list(csv.DictReader(io.StringIO("\n".join(lines[1:]))))


def test_the_roster_exports_as_csv(client, admin):
    r = client.get("/admin/students/export", headers=admin)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = _rows(r.text)
    assert len(rows) == 100  # the demo school's roll
    assert rows[0]["admission_no"] and rows[0]["full_name"]


def test_the_export_states_its_year_filters_and_timestamp(client, admin, ids):
    """Section 5.10.9: a report with no context is one that gets misquoted."""
    line = client.get("/admin/students/export", headers=admin).text.splitlines()[0]
    assert "academic year" in line
    assert "filters: none" in line
    assert "generated" in line


def test_a_filtered_export_names_the_filter_it_used(client, admin, ids):
    section = ids["section_10a"]
    r = client.get("/admin/students/export", headers=admin, params={"class_section_id": section})
    assert f"class_section_id={section}" in r.text.splitlines()[0]


def test_the_export_carries_the_same_rows_as_the_screen(client, admin, ids):
    """One query, not two. A download that can show what the screen cannot is
    the leak section 5.10.9 names as the most common one in an ERP."""
    section = ids["section_10a"]
    params = {"class_section_id": section}
    exported = {r["admission_no"] for r in _rows(
        client.get("/admin/students/export", headers=admin, params=params).text
    )}
    on_screen = {
        i["admission_no"]
        for i in client.get(
            "/admin/students", headers=admin, params={**params, "page_size": 200}
        ).json()["items"]
    }
    assert exported == on_screen
    assert exported


def test_the_export_does_not_carry_the_fields_the_screen_keeps_back(client, admin):
    """An export is where over-collection becomes permanent, so date of birth,
    address and the school's custom fields stay behind the per-student screen."""
    body = client.get("/admin/students/export", headers=admin).text
    names = csv.DictReader(io.StringIO("\n".join(body.splitlines()[1:]))).fieldnames
    assert "dob" not in names
    assert "address" not in names
    assert "custom" not in names


def test_a_download_is_written_to_the_audit_log(client, admin, db, ids):
    """`AuditAction.export` had never been written by anything."""
    before = db.scalar(
        select(AuditLog.id).where(AuditLog.action == AuditAction.export).limit(1)
    )
    assert before is None

    client.get("/admin/students/export", headers=admin, params={"q": "Sharma"})

    row = db.scalars(
        select(AuditLog)
        .where(AuditLog.action == AuditAction.export)
        .order_by(AuditLog.id.desc())
    ).first()
    assert row is not None, "an export left no trace"
    assert row.school_id == ids["school"]
    assert row.entity_type == "student"
    assert row.actor_user_id is not None
    # Who and how many, and against what filters - "downloaded 40 rows" and
    # "downloaded 40 rows of the Sharmas" are different events.
    assert row.after["rows"] > 0
    assert row.after["filters"] == {"q": "Sharma"}


def test_the_export_permission_is_required_and_not_the_read_one(client, teacher, parent):
    """A teacher holds `students.profile.read` school-wide and must still not be
    able to download the roll. A guardian holds it at `self` scope."""
    assert client.get("/admin/students/export", headers=teacher).status_code == 403
    assert client.get("/admin/students/export", headers=parent).status_code == 403


def test_another_schools_children_are_not_in_the_file(client, admin, rival_student):  # noqa: F811
    body = client.get("/admin/students/export", headers=admin).text
    assert "Rival Child" not in body
