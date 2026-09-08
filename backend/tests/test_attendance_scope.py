"""The two admin attendance screens, held to section 5.10.8's scope rule.

Both were open to a class teacher for the whole school, and it was measured
rather than argued: `TCH001` class-teaches 10-A, which holds ten children, and
`/admin/attendance/shortage` answered them with all one hundred - name,
admission number and attendance percentage - across all ten classes.

The cause is the trap HANDOFF section 4 records. Both routes are gated on
`attendance.record.read` school-wide, and a teacher *holds* that: their
permissions are unscoped by design and the restriction lives in the service.
`require_permission(..., school_wide=True)` stops a guardian and nobody else,
so a route that never applied the service half was wide open while looking
correctly gated.

Both now go through `scoping.narrow_to_own_sections()`, which is the same
function the report gate calls - one definition, so a report and the screen
beside it cannot drift apart again.
"""

import pytest

from app.services import school_settings


# --- the scope leak (HANDOFF section 8 item U)


def test_a_teacher_cannot_read_the_whole_schools_shortage_list(client, teacher):
    """The leak, at the threshold that made it visible: at 99.9 every child in
    the school qualifies, so an unscoped answer is the whole roll."""
    r = client.get(
        "/admin/attendance/shortage", headers=teacher, params={"threshold": 99.9}
    )
    assert r.status_code == 403, (
        f"a class teacher read {len(r.json())} children's attendance"
        if r.status_code == 200
        else r.text
    )


def test_a_teacher_cannot_read_the_whole_schools_absentees(client, teacher):
    r = client.get("/admin/attendance/absentees", headers=teacher)
    assert r.status_code == 403, r.text


def test_a_teacher_reads_their_own_section(client, teacher, ids):
    """Narrowed, not blocked. The class teacher of 10-A still gets 10-A."""
    r = client.get(
        "/admin/attendance/shortage",
        headers=teacher,
        params={"threshold": 99.9, "class_section_id": ids["section_10a"]},
    )
    assert r.status_code == 200, r.text
    rows = r.json()
    assert rows, "10-A has children below 99.9%"
    assert {row["class_label"] for row in rows} == {"10-A"}
    assert len(rows) == 10


def test_a_teacher_cannot_read_another_teachers_section(client, teacher, ids, db):
    from sqlalchemy import select

    from app.models import ClassSection

    foreign = db.scalar(
        select(ClassSection).where(
            ClassSection.school_id == ids["school"],
            ClassSection.id != ids["section_10a"],
        )
    )
    r = client.get(
        "/admin/attendance/shortage",
        headers=teacher,
        params={"threshold": 99.9, "class_section_id": foreign.id},
    )
    assert r.status_code == 403, r.text


def test_the_office_still_reads_the_whole_school(client, admin):
    """Narrowing a teacher must not narrow the roles the screen is for. An
    office clerk, a principal and an auditor read the school."""
    r = client.get(
        "/admin/attendance/shortage", headers=admin, params={"threshold": 99.9}
    )
    assert r.status_code == 200, r.text
    assert len(r.json()) == 100


def test_a_missing_section_is_refused_rather_than_widened(client, teacher):
    """"No filter" is exactly how this leaked. A teacher omitting the parameter
    must not fall through to the whole school."""
    r = client.get("/admin/attendance/shortage", headers=teacher)
    assert r.status_code == 403
    assert "class section" in r.json()["detail"]


# --- the threshold as a setting (HANDOFF section 8 item V)


def test_the_threshold_defaults_to_the_schools_setting(client, admin, db, admin_user):
    """It was a bare 75.0 in a function signature, unlike every other policy
    number here. A child on this list can be warned or debarred."""
    assert school_settings.get(db, admin_user.school_id, "attendance.shortage_threshold") == 75

    school_settings.set_many(db, admin_user, {"attendance.shortage_threshold": 100})
    everyone = client.get("/admin/attendance/shortage", headers=admin).json()
    assert len(everyone) == 100, "at 100% the whole roll is short"

    school_settings.set_many(db, admin_user, {"attendance.shortage_threshold": 1})
    nobody = client.get("/admin/attendance/shortage", headers=admin).json()
    assert nobody == [], "at 1% nobody is short"


def test_an_explicit_threshold_still_wins_over_the_setting(client, admin, db, admin_user):
    """A report asking "who is under 60" must not change school policy."""
    school_settings.set_many(db, admin_user, {"attendance.shortage_threshold": 1})
    asked = client.get(
        "/admin/attendance/shortage", headers=admin, params={"threshold": 100}
    ).json()
    assert len(asked) == 100
    assert (
        school_settings.get(db, admin_user.school_id, "attendance.shortage_threshold")
        == 1
    ), "the question changed the answer, not the policy"


def test_the_threshold_is_in_the_configuration_screen(client, admin):
    """It has to be reachable by the records clerk section 0.18 describes, not
    only by a developer."""
    values = client.get("/admin/configuration", headers=admin).json()["values"]
    assert values["attendance.shortage_threshold"] == 75


def test_the_setting_is_validated_like_every_other(client, admin):
    r = client.put(
        "/admin/configuration",
        headers=admin,
        json={"values": {"attendance.shortage_threshold": "three quarters"}},
    )
    assert r.status_code == 422, r.text


def test_the_report_and_the_screen_use_the_same_threshold(client, admin, db, admin_user):
    """One definition. The report calls `attendance.shortage()`, which reads the
    setting, so changing the policy moves both."""
    school_settings.set_many(db, admin_user, {"attendance.shortage_threshold": 100})
    screen = client.get("/admin/attendance/shortage", headers=admin).json()
    report = client.get("/admin/reports/attendance.shortage", headers=admin).json()["data"]
    assert len(screen) == len(report) == 100
    assert [r["student_id"] for r in screen] == [r["student_id"] for r in report]


# --- the student roster, narrowed the same way (found by the live sweep)


def _foreign_child(client, admin, teacher):
    """A child in a section this teacher does not teach."""
    mine = {c["class_label"] for c in client.get("/teacher/classes", headers=teacher).json()}
    everyone = client.get(
        "/admin/students", headers=admin, params={"page_size": 200}
    ).json()["items"]
    return next(s for s in everyone if s["class_label"] not in mine), mine


def test_a_teacher_reads_only_their_own_sections_children(client, admin, teacher):
    """The roster carries a guardian's phone, and the detail screen behind it
    carries date of birth and home address. It was answering any of the twelve
    teachers for all one hundred children."""
    victim, mine = _foreign_child(client, admin, teacher)
    seen = client.get("/admin/students", headers=teacher, params={"page_size": 200}).json()
    assert seen["total"] < 100
    assert {s["class_label"] for s in seen["items"]} <= mine
    assert victim["id"] not in {s["id"] for s in seen["items"]}


def test_a_teacher_cannot_open_another_sections_child_by_id(client, admin, teacher):
    """An id is guessable, so narrowing only the list would be no narrowing."""
    victim, _ = _foreign_child(client, admin, teacher)
    r = client.get(f"/admin/students/{victim['id']}", headers=teacher)
    assert r.status_code == 403, r.text


def test_a_teacher_can_still_open_their_own_pupil(client, teacher, ids):
    roster = client.get(
        f"/teacher/classes/{ids['section_10a']}/students", headers=teacher
    ).json()
    r = client.get(f"/admin/students/{roster[0]['id']}", headers=teacher)
    assert r.status_code == 200, r.text
    assert r.json()["class_label"] == "10-A"


def test_the_office_still_reads_every_child(client, admin):
    body = client.get("/admin/students", headers=admin, params={"page_size": 200}).json()
    assert body["total"] == 100


def test_a_teachers_export_is_narrowed_too_if_they_could_run_it(client, teacher):
    """A teacher does not hold `students.profile.export`, so the download is
    refused outright - but the export shares `_roster()`, so the narrowing
    would apply to it as well if a school ever granted them the permission."""
    assert client.get("/admin/students/export", headers=teacher).status_code == 403
