"""The mobile app's own screens: teacher, student and parent.

Every test here exists because a live sweep of the running server found the
endpoint broken, and the suite could not see it. That is the finding worth
keeping: 578 tests passed while three of the mobile app's core screens returned
500 to the very role they are built for, because nothing called them.

- `/teacher/profile` read `Employee.employee_id`, a column that does not exist.
- `/teacher/classes/{id}/students` iterated `roster()`, which returns
  Enrolments, as though it returned Students.
- `/student/profile` used a name that was never defined.
- `/parent/profile` assumed its caller was a guardian and crashed when not.
- `/teacher/classes` counted a cartesian product and reported a class of ten
  as a class of a thousand.
"""

import pytest


# --- teacher


def test_a_teacher_can_read_their_own_profile(client, teacher):
    r = client.get("/teacher/profile", headers=teacher)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"]
    # The column is `employee_code`; `employee_id` never existed on Employee.
    assert body["employee_code"]
    assert "10-A" in body["class_teacher_of"]


def test_a_teacher_can_read_their_class_roster(client, teacher, ids):
    r = client.get(f"/teacher/classes/{ids['section_10a']}/students", headers=teacher)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert len(rows) == 10, "10-A holds ten children"
    first = rows[0]
    # Ids must be the student's, not the enrolment's: the mobile app follows
    # this id to /parent and /teacher routes keyed by student.
    assert first["id"] and first["full_name"] and first["admission_no"]
    assert first["roll_no"] == 1
    assert sorted(r["roll_no"] for r in rows) == list(range(1, 11))


def test_the_roster_ids_are_student_ids(client, teacher, admin, ids):
    """The bug returned enrolment ids, which happen to be integers too - the
    kind of wrong that only shows up when something follows the link."""
    rows = client.get(
        f"/teacher/classes/{ids['section_10a']}/students", headers=teacher
    ).json()
    for row in rows[:3]:
        detail = client.get(f"/admin/students/{row['id']}", headers=admin)
        assert detail.status_code == 200, f"id {row['id']} is not a student id"
        assert detail.json()["full_name"] == row["full_name"]


def test_a_class_of_ten_is_not_reported_as_a_thousand(client, teacher):
    """`db.query(Student).filter(Enrolment...)` named two tables and joined
    neither, so every class reported 100 students x 10 enrolments."""
    rows = client.get("/teacher/classes", headers=teacher).json()
    assert rows
    for row in rows:
        assert row["student_count"] == 10, row


def test_the_class_list_agrees_with_the_roster_it_links_to(client, teacher):
    """The count and the list are two answers to one question."""
    for row in client.get("/teacher/classes", headers=teacher).json():
        roster = client.get(
            f"/teacher/classes/{row['class_section_id']}/students", headers=teacher
        )
        assert roster.status_code == 200, roster.text
        assert row["student_count"] == len(roster.json()), row["class_label"]


# --- student


def test_a_student_can_read_their_own_profile(client, student):
    r = client.get("/student/profile", headers=student)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"] and body["admission_no"]
    # The two fields the undefined name was standing in for.
    assert body["class_label"] == "10-A"
    assert body["roll_no"] == 1
    assert body["parents"], "a seeded student has a guardian"


# --- parent


def test_a_parent_can_read_their_own_profile(client, parent):
    r = client.get("/parent/profile", headers=parent)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"]
    assert len(body["children"]) == 2, "the demo parent has two children"


def test_someone_who_is_not_a_guardian_is_refused_not_crashed(client, admin, teacher):
    """`students.profile.read` is held by clerks and teachers too, so they
    reach this route. The answer is "you are not a parent", not a 500."""
    for headers in (admin, teacher):
        r = client.get("/parent/profile", headers=headers)
        assert r.status_code == 403, r.text


# --- the sweep this file came from, in miniature


@pytest.mark.parametrize(
    "path,role",
    [
        ("/teacher/profile", "teacher"),
        ("/teacher/classes", "teacher"),
        ("/teacher/timetable", "teacher"),
        ("/student/profile", "student"),
        ("/student/dashboard", "student"),
        ("/student/timetable", "student"),
        ("/parent/profile", "parent"),
        ("/parent/children", "parent"),
    ],
)
def test_the_app_screens_answer_their_own_role(client, request, path, role):
    """A smoke test over the endpoints the mobile app opens on. Cheap, and it
    is exactly what was missing when three of them were broken at once."""
    headers = request.getfixturevalue(role)
    r = client.get(path, headers=headers)
    assert r.status_code == 200, f"{path} as {role}: {r.status_code} {r.text[:300]}"
