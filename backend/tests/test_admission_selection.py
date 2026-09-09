"""Seats, decisions, offers and the waitlist (§5.1.9(11)-(14))."""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import AdmissionCycle, AdmissionOffer, Application


@pytest.fixture()
def cycle_id(db):
    return db.scalar(select(AdmissionCycle)).id


@pytest.fixture()
def small_class(client, admin, cycle_id):
    """A class with two seats, one of them reserved for EWS — small enough
    that the seat rules actually bite."""
    client.put(
        f"/admin/admission/cycles/{cycle_id}/classes",
        json={"class_name": "12", "total_seats": 2, "reserved_seats": {"EWS": 1}},
        headers=admin,
    )
    return "12"


def _applicant(client, admin, class_name, surname, mobile, **over):
    body = {
        "first_name": "Applicant",
        "last_name": surname,
        "date_of_birth": "2010-02-02",
        "gender": "male",
        "class_applying_for": class_name,
    }
    body.update(over)
    app = client.post("/admin/admission/applications", json=body, headers=admin).json()
    client.put(
        f"/admin/admission/applications/{app['id']}/guardians",
        json=[
            {
                "relation": "father",
                "full_name": f"{surname} senior",
                "mobile": mobile,
                "is_primary": True,
            }
        ],
        headers=admin,
    )
    client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    return app


def test_every_decision_needs_a_reason_including_an_admit(client, admin, small_class):
    """§5.1.9(13): this is what makes the process defensible when challenged."""
    app = _applicant(client, admin, small_class, "Reasonless", "9855500001")
    r = client.post(
        f"/admin/admission/applications/{app['id']}/decision",
        json={"decision": "admitted", "reason": "   "},
        headers=admin,
    )
    assert r.status_code == 422

    r = client.post(
        f"/admin/admission/applications/{app['id']}/decision",
        json={"decision": "admitted", "reason": "Ranked 1 of 14 on the merit list"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "admitted"


def test_a_general_admission_cannot_eat_a_reserved_seat(client, admin, small_class):
    """§5.1.9(12): two seats, one reserved for EWS, so General has exactly
    one — the second General admit must be refused while a seat still shows as
    free."""
    first = _applicant(client, admin, small_class, "GeneralOne", "9855500002")
    second = _applicant(client, admin, small_class, "GeneralTwo", "9855500003")
    for app in (first, second):
        r = client.post(
            f"/admin/admission/applications/{app['id']}/decision",
            json={"decision": "admitted", "reason": "Merit"},
            headers=admin,
        )
        if app is first:
            assert r.status_code == 200, r.text
        else:
            assert r.status_code == 409
            assert "full" in r.json()["detail"]

    # The EWS seat is still there for the applicant it was reserved for.
    ews = _applicant(
        client, admin, small_class, "EwsChild", "9855500004", caste_category="EWS"
    )
    r = client.post(
        f"/admin/admission/applications/{ews['id']}/decision",
        json={"decision": "admitted", "reason": "Merit within the EWS pool"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["seat_category"] == "EWS"


def test_over_allocation_is_possible_but_never_accidental(client, admin, small_class, db):
    """§5.1.9(11): silent over-admission is one of the more damaging failures
    possible here."""
    _applicant(client, admin, small_class, "Filler", "9855500005")
    first = db.scalar(
        select(Application).where(Application.last_name == "Filler")
    )
    client.post(
        f"/admin/admission/applications/{first.id}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )

    extra = _applicant(client, admin, small_class, "Extra", "9855500006")
    refused = client.post(
        f"/admin/admission/applications/{extra['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )
    assert refused.status_code == 409

    approved = client.post(
        f"/admin/admission/applications/{extra['id']}/decision",
        json={
            "decision": "admitted",
            "reason": "Management approval; sibling of a current student",
            "over_allocation_approved": True,
        },
        headers=admin,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["over_allocation_approved"] is True

    history = client.get(
        f"/admin/admission/applications/{extra['id']}/decisions", headers=admin
    ).json()
    assert history[-1]["over_allocation_approved"] is True
    assert "Management approval" in history[-1]["reason"]


def test_the_merit_list_ranks_by_priority_then_score(client, admin, small_class, cycle_id):
    plain = _applicant(client, admin, small_class, "Plain", "9855500007")
    staff = _applicant(
        client, admin, small_class, "StaffWard", "9855500008", admission_category="staff_ward"
    )
    body = client.get(
        f"/admin/admission/cycles/{cycle_id}/merit?class_name={small_class}",
        headers=admin,
    ).json()
    ranked = [a["application_id"] for a in body["applicants"]]
    assert set(ranked) == {plain["id"], staff["id"]}
    # The staff-ward claim is unverified, so it earns nothing yet and the two
    # are separated only by who applied first (§5.1.9(6)).
    assert ranked == [plain["id"], staff["id"]]
    assert body["seats"]["total_seats"] == 2


def test_an_offer_must_expire_and_holds_the_seat_until_it_does(
    client, admin, small_class, db
):
    app = _applicant(client, admin, small_class, "Offered", "9855500009")
    client.post(
        f"/admin/admission/applications/{app['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )

    r = client.post(
        f"/admin/admission/applications/{app['id']}/offer",
        json={"expires_on": str(date.today() - timedelta(days=1))},
        headers=admin,
    )
    assert r.status_code == 422

    r = client.post(
        f"/admin/admission/applications/{app['id']}/offer",
        json={"expires_on": str(date.today() + timedelta(days=7)), "offer_amount": "25000"},
        headers=admin,
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "issued"

    seats = client.get(
        f"/admin/admission/cycles/{db.scalar(select(AdmissionCycle)).id}/seats?class_name={small_class}",
        headers=admin,
    ).json()[0]
    # An issued offer holds a seat exactly as firmly as an enrolment does.
    assert seats["taken"] == 1


def test_a_lapsed_offer_releases_the_seat_and_the_waitlist_moves(
    client, admin, small_class, cycle_id, db
):
    """§5.1.9(14), the automation §5.1.2(6) calls a large part of the module's
    value."""
    holder = _applicant(client, admin, small_class, "Holder", "9855500010")
    waiting = _applicant(client, admin, small_class, "Waiting", "9855500011")

    client.post(
        f"/admin/admission/applications/{holder['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{holder['id']}/offer",
        json={"expires_on": str(date.today() + timedelta(days=2))},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{waiting['id']}/decision",
        json={"decision": "waitlisted", "reason": "Ranked below the last seat"},
        headers=admin,
    )

    queue = client.get(
        f"/admin/admission/cycles/{cycle_id}/waitlist?class_name={small_class}",
        headers=admin,
    ).json()
    assert [q["rank"] for q in queue] == [1]
    assert queue[0]["application_id"] == waiting["id"]

    # Move the clock past the expiry by moving the expiry into the past.
    offer = db.scalar(
        select(AdmissionOffer).where(AdmissionOffer.application_id == holder["id"])
    )
    offer.expires_on = date.today() - timedelta(days=1)
    db.commit()

    from app.services import selection

    result = selection.expire_offers(db, offer.school_id)
    db.commit()
    assert result["expired"] == 1

    lapsed = client.get(
        f"/admin/admission/applications/{holder['id']}", headers=admin
    ).json()
    assert lapsed["status"] == "offer_expired"
    promoted = client.get(
        f"/admin/admission/applications/{waiting['id']}", headers=admin
    ).json()
    assert promoted["status"] == "admitted"
    assert result["promoted"] == [promoted["application_no"]]


def test_declining_an_offer_frees_the_seat_immediately(
    client, admin, small_class, cycle_id
):
    holder = _applicant(client, admin, small_class, "Decliner", "9855500012")
    waiting = _applicant(client, admin, small_class, "NextUp", "9855500013")
    client.post(
        f"/admin/admission/applications/{holder['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{holder['id']}/offer",
        json={"expires_on": str(date.today() + timedelta(days=7))},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{waiting['id']}/decision",
        json={"decision": "waitlisted", "reason": "Next in line"},
        headers=admin,
    )

    r = client.post(
        f"/admin/admission/applications/{holder['id']}/offer/response",
        json={"accepted": False, "reason": "Moving out of Lucknow"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "declined"

    promoted = client.get(
        f"/admin/admission/applications/{waiting['id']}", headers=admin
    ).json()
    assert promoted["status"] == "admitted"


def test_accepting_an_offer_moves_the_application_on(client, admin, small_class):
    app = _applicant(client, admin, small_class, "Accepter", "9855500014")
    client.post(
        f"/admin/admission/applications/{app['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{app['id']}/offer",
        json={"expires_on": str(date.today() + timedelta(days=7))},
        headers=admin,
    )
    r = client.post(
        f"/admin/admission/applications/{app['id']}/offer/response",
        json={"accepted": True},
        headers=admin,
    )
    assert r.json()["application_status"] == "offer_accepted"


def test_a_batch_reports_per_applicant_rather_than_failing_whole(
    client, admin, small_class, cycle_id
):
    one = _applicant(client, admin, small_class, "BatchOne", "9855500015")
    two = _applicant(client, admin, small_class, "BatchTwo", "9855500016")
    three = _applicant(client, admin, small_class, "BatchThree", "9855500017")

    body = client.post(
        f"/admin/admission/cycles/{cycle_id}/decisions",
        json={
            "decisions": [
                {"application_id": one["id"], "decision": "admitted", "reason": "Top 2"},
                {"application_id": two["id"], "decision": "admitted", "reason": "Top 2"},
                {"application_id": three["id"], "decision": "admitted", "reason": "Top 2"},
            ]
        },
        headers=admin,
    ).json()["results"]

    assert [r["ok"] for r in body] == [True, False, False]
    # One general seat: the first admit takes it, the rest are refused with a
    # reason each rather than the batch dying on the second row.
    assert all("full" in r["detail"] for r in body if not r["ok"])


def test_an_officer_cannot_approve_an_over_allocation(client, admin, small_class, db):
    from app.core.permissions import SYSTEM_ROLES

    by_code = {code: perms for code, _, perms in SYSTEM_ROLES}
    assert "admission.decision.make" in by_code["admission_officer"]
    assert "admission.decision.override" not in by_code["admission_officer"]
    assert "admission.decision.override" in by_code["principal"]
