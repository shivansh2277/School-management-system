"""Admin student CRUD.

Untested until now, and the enrolment split had broken both halves of it: the
create route referenced ClassSection and Enrolment without importing them, and
the update route wrote class_section_id onto the Student, where the column no
longer exists.
"""


def _create(client, admin, ids, **over):
    body = {
        "full_name": "Test Child",
        "class_section_id": ids["section_9a"],
        "roll_no": 91,
        "guardian": {"full_name": "Test Guardian", "phone": "9000000091"},
    }
    body.update(over)
    return client.post("/admin/students", json=body, headers=admin)


def test_creating_a_student_enrols_them_and_allocates_an_admission_no(
    client, admin, ids
):
    r = _create(client, admin, ids)
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["class_section_id"] == ids["section_9a"]
    assert row["roll_no"] == 91
    # §0.21: 4-digit joining year + 6-digit sequence, allocated not supplied.
    assert len(row["admission_no"]) == 10 and row["admission_no"].isdigit()

    listed = client.get(
        f"/admin/students?class_section_id={ids['section_9a']}", headers=admin
    ).json()
    assert row["id"] in [s["id"] for s in listed["items"]]


def test_moving_a_student_to_another_section_actually_moves_them(client, admin, ids):
    student_id = _create(client, admin, ids).json()["id"]
    r = client.patch(
        f"/admin/students/{student_id}",
        json={"class_section_id": ids["section_8a"], "roll_no": 92},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["class_section_id"] == ids["section_8a"]

    detail = client.get(f"/admin/students/{student_id}", headers=admin).json()
    assert detail["class_section_id"] == ids["section_8a"]
    assert detail["roll_no"] == 92


def test_a_student_cannot_be_created_into_a_section_that_does_not_exist(
    client, admin, ids
):
    assert _create(client, admin, ids, class_section_id=999999).status_code == 404


def test_the_first_guardian_recorded_is_the_one_the_school_rings(client, admin, ids, db):
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    from app.models import StudentGuardian

    student_id = _create(client, admin, ids).json()["id"]
    links = list(
        db.scalars(
            select(StudentGuardian).where(StudentGuardian.student_id == student_id)
        )
    )
    assert [link.is_primary for link in links] == [True]

    # A second primary contact for the same child is refused by the database,
    # not by a convention someone has to remember (ERP_BLUEPRINT §3.4).
    db.add(
        StudentGuardian(
            school_id=links[0].school_id,
            guardian_id=links[0].guardian_id,
            student_id=student_id,
            relation="mother",
            is_primary=True,
        )
    )
    try:
        db.flush()
        raise AssertionError("a second primary guardian was accepted")
    except IntegrityError:
        db.rollback()
