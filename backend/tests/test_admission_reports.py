"""The admission dashboard and its reports (§5.1.3 screen 1, §5.1.10)."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import AdmissionCycle


@pytest.fixture()
def cycle_id(db):
    return db.scalar(select(AdmissionCycle)).id


def _applicant(client, admin, surname, mobile, class_name="6", **over):
    body = {
        "first_name": "Report",
        "last_name": surname,
        "date_of_birth": "2014-06-06",
        "gender": "female",
        "class_applying_for": class_name,
    }
    body.update(over)
    app = client.post("/admin/admission/applications", json=body, headers=admin).json()
    client.put(
        f"/admin/admission/applications/{app['id']}/guardians",
        json=[
            {
                "relation": "mother",
                "full_name": f"{surname} parent",
                "mobile": mobile,
                "is_primary": True,
            }
        ],
        headers=admin,
    )
    client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    return app


def test_the_funnel_starts_at_enquiries_and_narrows(client, admin, cycle_id):
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
    assert body["overall_conversion_pct"] == 0.0


def test_seat_utilisation_reports_offers_as_well_as_seats(client, admin, cycle_id):
    app = _applicant(client, admin, "SeatOne", "9833300002")
    client.post(
        f"/admin/admission/applications/{app['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )
    client.post(
        f"/admin/admission/applications/{app['id']}/offer",
        json={"expires_on": str(date.today() + timedelta(days=5))},
        headers=admin,
    )

    rows = client.get(
        f"/admin/admission/cycles/{cycle_id}/reports", headers=admin
    ).json()["seat_utilisation"]
    row = next(r for r in rows if r["class_name"] == "6")
    assert row["taken"] == 1
    assert row["offers_made"] == 1
    assert row["offer_acceptance_pct"] == 0.0
    assert 0 < row["filled_pct"] <= 100


def test_rejection_reasons_are_grouped(client, admin, cycle_id):
    """Which is the whole point of insisting on a reason: it shows whether the
    criteria are being applied consistently."""
    for i, surname in enumerate(("RejectOne", "RejectTwo")):
        app = _applicant(client, admin, surname, f"983330001{i}")
        client.post(
            f"/admin/admission/applications/{app['id']}/decision",
            json={"decision": "rejected", "reason": "Below the cut-off in the written test"},
            headers=admin,
        )
    rows = client.get(
        f"/admin/admission/cycles/{cycle_id}/reports", headers=admin
    ).json()["rejections"]
    assert rows[0]["reason"] == "Below the cut-off in the written test"
    assert rows[0]["count"] == 2


def test_demographics_count_verified_priority_only(client, admin, cycle_id):
    app = _applicant(
        client, admin, "ClaimedSibling", "9833300020", admission_category="sibling"
    )
    client.post(
        f"/admin/admission/applications/{app['id']}/decision",
        json={"decision": "admitted", "reason": "Merit"},
        headers=admin,
    )
    body = client.get(
        f"/admin/admission/cycles/{cycle_id}/reports", headers=admin
    ).json()["demographics"]
    # The claim was never verified against a real student, so it earns no
    # share of the intake (§5.1.9(6)).
    assert body["sibling_share_pct"] == 0.0
    assert body["admitted"]["gender"]["female"] >= 1


def test_the_dashboard_shows_todays_work(client, admin, cycle_id):
    app = _applicant(client, admin, "Scheduled", "9833300030")
    in_an_hour = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    client.post(
        f"/admin/admission/applications/{app['id']}/assessments",
        json={"assessment_type": "written_test", "scheduled_at": in_an_hour, "venue": "Hall B"},
        headers=admin,
    )

    body = client.get(
        f"/admin/admission/cycles/{cycle_id}/dashboard", headers=admin
    ).json()
    assert len(body["today"]["tests"]) == 1
    assert body["today"]["tests"][0]["venue"] == "Hall B"
    # The seed leaves follow-ups due, so the register has work waiting too.
    assert body["today"]["follow_ups_due"] >= 1
    assert body["awaiting_action"]["assessment_scheduled"] >= 1


def test_source_effectiveness_covers_enquiries_and_applications(client, admin, cycle_id):
    rows = client.get(
        f"/admin/admission/cycles/{cycle_id}/reports", headers=admin
    ).json()["by_source"]
    by_source = {r["source"]: r for r in rows}
    # The seeded register spreads across channels; every row carries both
    # halves so "cost per enquiry" and "cost per admission" are answerable.
    assert "website" in by_source
    assert all("enquiries" in r and "enrolled" in r for r in rows)


def test_a_receptionist_cannot_read_the_dashboard(client, admin, cycle_id):
    from app.core.permissions import SYSTEM_ROLES

    perms = {code: granted for code, _, granted in SYSTEM_ROLES}["receptionist"]
    # The dashboard shows decisions and scores; the front desk sees neither
    # (§5.1.8).
    assert "admission.application.read" not in perms
