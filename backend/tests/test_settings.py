"""Per-school settings, module flags and custom fields (ERP_BLUEPRINT §3.15)."""

import pytest


def test_unset_settings_read_as_their_registry_default(client, admin):
    body = client.get("/admin/configuration", headers=admin).json()
    assert body["values"]["feature.homework"] is True
    # `feature.hr` rather than `feature.transport`: both default to off, but
    # the demo school now switches transport on explicitly, which makes it a
    # stored value and no longer an example of an unset one.
    assert body["values"]["feature.hr"] is False
    assert body["values"]["feature.transport"] is True
    # The screen is rendered from the vocabulary, not from a hardcoded form.
    assert {d["key"] for d in body["definitions"]} == set(body["values"])


def test_a_key_outside_the_registry_is_refused(client, admin):
    r = client.put(
        "/admin/configuration", json={"values": {"feature.teleportation": True}}, headers=admin
    )
    assert r.status_code == 404


def test_a_setting_must_match_its_declared_type(client, admin):
    r = client.put("/admin/configuration", json={"values": {"feature.fees": 1}}, headers=admin)
    assert r.status_code == 422
    # And nothing was written on the way to the failure.
    assert client.get("/admin/configuration", headers=admin).json()["values"]["feature.fees"] is True


def test_turning_a_module_off_closes_its_routes(client, admin, teacher, student):
    assert client.get("/teacher/homework", headers=teacher).status_code == 200
    assert client.get("/student/homework", headers=student).status_code == 200

    r = client.put(
        "/admin/configuration", json={"values": {"feature.homework": False}}, headers=admin
    )
    assert r.status_code == 200
    assert r.json()["values"]["feature.homework"] is False

    assert client.get("/teacher/homework", headers=teacher).status_code == 404
    assert client.get("/student/homework", headers=student).status_code == 404
    # A module switch is not a permission: attendance is untouched.
    assert client.get("/student/attendance", headers=student).status_code == 200


def test_a_teacher_cannot_change_school_settings(client, teacher):
    assert client.get("/admin/configuration", headers=teacher).status_code == 403
    assert (
        client.put(
            "/admin/configuration", json={"values": {"feature.homework": False}}, headers=teacher
        ).status_code
        == 403
    )


@pytest.fixture()
def bus_field(client, admin):
    r = client.post(
        "/admin/custom-fields",
        json={
            "entity": "student",
            "key": "bus_pass_no",
            "label": "Bus pass number",
            "field_type": "text",
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _new_student(client, admin, ids, **over):
    body = {
        "full_name": "Custom Field Child",
        "class_section_id": ids["section_9a"],
        "roll_no": 95,
        "guardian": {"full_name": "CF Guardian", "phone": "9000000095"},
    }
    body.update(over)
    return client.post("/admin/students", json=body, headers=admin)


def test_a_custom_field_value_survives_the_round_trip(client, admin, ids, bus_field):
    r = _new_student(client, admin, ids, custom={"bus_pass_no": "UP32-441"})
    assert r.status_code == 201, r.text
    student_id = r.json()["id"]
    detail = client.get(f"/admin/students/{student_id}", headers=admin).json()
    assert detail["custom"] == {"bus_pass_no": "UP32-441"}


def test_a_value_for_an_undefined_field_is_refused_not_dropped(client, admin, ids):
    r = _new_student(client, admin, ids, custom={"favourite_colour": "blue"})
    assert r.status_code == 422
    assert "favourite_colour" in r.json()["detail"]


def test_a_select_field_only_accepts_its_options(client, admin, ids):
    client.post(
        "/admin/custom-fields",
        json={
            "entity": "student",
            "key": "shift",
            "label": "Shift",
            "field_type": "select",
            "options": ["Morning", "Afternoon"],
        },
        headers=admin,
    )
    assert _new_student(client, admin, ids, custom={"shift": "Night"}).status_code == 422
    assert _new_student(client, admin, ids, custom={"shift": "Morning"}).status_code == 201


def test_a_required_field_blocks_a_student_created_without_it(client, admin, ids):
    client.post(
        "/admin/custom-fields",
        json={
            "entity": "student",
            "key": "prev_board_roll",
            "label": "Previous board roll no",
            "field_type": "text",
            "is_required": True,
        },
        headers=admin,
    )
    r = _new_student(client, admin, ids)
    assert r.status_code == 422
    assert "Previous board roll no" in r.json()["detail"]


def test_retiring_a_field_hides_it_without_losing_the_value(client, admin, ids, bus_field):
    student_id = _new_student(
        client, admin, ids, custom={"bus_pass_no": "UP32-441"}
    ).json()["id"]

    assert (
        client.delete(f"/admin/custom-fields/{bus_field['id']}", headers=admin).status_code
        == 204
    )
    active = client.get("/admin/custom-fields", headers=admin).json()
    assert bus_field["key"] not in [f["key"] for f in active]
    # The definition is retired, so the value stops being served — but it is
    # still in the column, which is what makes reactivating it non-destructive.
    detail = client.get(f"/admin/students/{student_id}", headers=admin).json()
    assert detail["custom"] == {"bus_pass_no": "UP32-441"}
    retired = [
        f
        for f in client.get(
            "/admin/custom-fields?include_inactive=true", headers=admin
        ).json()
        if f["key"] == bus_field["key"]
    ]
    assert retired and retired[0]["is_active"] is False
