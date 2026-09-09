"""Admission cycles, seat configuration and the enquiry register (§5.1).

The enquiry half of the funnel. What matters here is that the register cannot
be quietly rewritten: a status only moves through a logged interaction, and
nothing is ever deleted.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import AdmissionCycle
from app.services.admission import age_years_on


@pytest.fixture()
def cycle_id(db):
    """The open cycle the seed installs."""
    cycle = db.scalar(select(AdmissionCycle))
    assert cycle is not None, "the seed should install an admission cycle"
    return cycle.id


def test_the_seeded_cycle_is_open_with_seats(client, admin, cycle_id):
    cycles = client.get("/admin/admission/cycles", headers=admin).json()
    assert [c["status"] for c in cycles] == ["open"]

    classes = client.get(
        f"/admin/admission/cycles/{cycle_id}/classes", headers=admin
    ).json()
    assert {c["class_name"] for c in classes} == {"1", "6", "9"}
    assert all(c["total_seats"] > 0 and c["age_on"] for c in classes)


def test_reserved_seats_cannot_exceed_the_total(client, admin, cycle_id):
    r = client.put(
        f"/admin/admission/cycles/{cycle_id}/classes",
        json={"class_name": "11", "total_seats": 10, "reserved_seats": {"EWS": 11}},
        headers=admin,
    )
    assert r.status_code == 422


def test_class_config_is_an_upsert(client, admin, cycle_id):
    """Seat counts are revised repeatedly during a cycle."""
    first = client.put(
        f"/admin/admission/cycles/{cycle_id}/classes",
        json={"class_name": "1", "total_seats": 44},
        headers=admin,
    ).json()
    second = client.put(
        f"/admin/admission/cycles/{cycle_id}/classes",
        json={"class_name": "1", "total_seats": 48},
        headers=admin,
    ).json()
    assert first["id"] == second["id"]
    assert second["total_seats"] == 48


def test_age_is_measured_against_the_cut_off_not_today():
    """§5.1.9(1): a child too young in April is still too young in June."""
    dob = date(2020, 6, 1)
    assert age_years_on(dob, date(2026, 3, 31)) == Decimal("5.83")
    assert age_years_on(dob, date(2027, 3, 31)) == Decimal("6.83")


def test_an_enquiry_needs_only_a_name_and_a_number(client, admin):
    r = client.post(
        "/admin/admission/enquiries",
        json={"enquirer_name": "Walk-in Parent", "mobile": "9000012345"},
        headers=admin,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "new"
    # The cycle was not given, so the open one was found.
    assert body["cycle_id"]


def test_a_status_only_moves_through_a_logged_interaction(client, admin):
    follow_up = date.today() + timedelta(days=3)
    enquiry = client.post(
        "/admin/admission/enquiries",
        json={"enquirer_name": "Kavita Joshi", "mobile": "9000012346"},
        headers=admin,
    ).json()

    r = client.post(
        f"/admin/admission/enquiries/{enquiry['id']}/interactions",
        json={
            "channel": "phone",
            "notes": "Explained the fee structure; will visit on Saturday.",
            "outcome": "interested",
            "next_follow_up_on": str(follow_up),
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    detail = r.json()
    assert detail["status"] == "interested"
    # The date sent, not a fresh reading: across midnight the second call
    # returns a different day and the echo looks wrong.
    assert detail["next_follow_up_on"] == str(follow_up)
    assert detail["interactions"][0]["notes"].startswith("Explained")


def test_closing_an_enquiry_takes_it_off_the_follow_up_list(client, admin):
    enquiry = client.post(
        "/admin/admission/enquiries",
        json={
            "enquirer_name": "Manoj Bhatt",
            "mobile": "9000012347",
            "next_follow_up_on": str(date.today()),
        },
        headers=admin,
    ).json()

    due = client.get(
        f"/admin/admission/enquiries?due_by={date.today()}", headers=admin
    ).json()
    assert enquiry["id"] in [e["id"] for e in due]

    client.post(
        f"/admin/admission/enquiries/{enquiry['id']}/interactions",
        json={"channel": "phone", "outcome": "not_interested", "notes": "Chose another school."},
        headers=admin,
    )
    due_after = client.get(
        f"/admin/admission/enquiries?due_by={date.today()}", headers=admin
    ).json()
    assert enquiry["id"] not in [e["id"] for e in due_after]


def test_an_enquiry_is_closed_as_invalid_never_deleted(client, admin):
    enquiry = client.post(
        "/admin/admission/enquiries",
        json={"enquirer_name": "Wrong Number", "mobile": "9000012348"},
        headers=admin,
    ).json()
    r = client.delete(
        f"/admin/admission/enquiries/{enquiry['id']}?reason=Wrong+number",
        headers=admin,
    )
    assert r.status_code == 204
    # Still there, and the reason is in the log: a wrong number is still a data
    # point about where enquiries come from.
    detail = client.get(
        f"/admin/admission/enquiries/{enquiry['id']}", headers=admin
    ).json()
    assert detail["status"] == "invalid"
    assert detail["interactions"][0]["notes"] == "Wrong number"


def test_the_funnel_counts_every_stage(client, admin, cycle_id):
    counts = client.get(
        f"/admin/admission/cycles/{cycle_id}/funnel", headers=admin
    ).json()["enquiries"]
    # The seed installs one enquiry in each of six stages.
    assert counts["new"] >= 1 and counts["lost_to_competitor"] >= 1
    assert sum(counts.values()) >= 6


def test_a_teacher_cannot_reach_the_enquiry_register(client, teacher):
    assert client.get("/admin/admission/enquiries", headers=teacher).status_code == 403
    assert (
        client.post(
            "/admin/admission/enquiries",
            json={"enquirer_name": "X", "mobile": "9000000000"},
            headers=teacher,
        ).status_code
        == 403
    )


def test_turning_the_admission_module_off_closes_the_register(client, admin):
    client.put(
        "/admin/configuration",
        json={"values": {"feature.admission": False}},
        headers=admin,
    )
    assert client.get("/admin/admission/enquiries", headers=admin).status_code == 404
