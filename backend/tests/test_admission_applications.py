"""Applications: drafts, submission rules and status movement (§5.1.4, §5.1.9).

The rules worth a test are the ones that are easy to get backwards: a warning
that should not be a block, a block that should not be a warning, and a status
that must not move silently.
"""

from datetime import date

import pytest
from sqlalchemy import select

from app.models import AdmissionCycle, Application, AuditLog


@pytest.fixture()
def cycle_id(db):
    return db.scalar(select(AdmissionCycle)).id


def _draft(client, admin, **over):
    body = {
        "first_name": "Anaya",
        "last_name": "Verma",
        "date_of_birth": "2019-05-14",
        "gender": "female",
        "class_applying_for": "1",
    }
    body.update(over)
    r = client.post("/admin/admission/applications", json=body, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


def _guardian(client, admin, application_id, **over):
    body = {
        "relation": "father",
        "full_name": "Rakesh Verma",
        "mobile": "9811155501",
        "is_primary": True,
    }
    body.update(over)
    r = client.put(
        f"/admin/admission/applications/{application_id}/guardians",
        json=[body],
        headers=admin,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_a_draft_saves_before_it_is_complete(client, admin):
    app = _draft(client, admin)
    assert app["status"] == "draft"
    assert app["application_no"] is None  # not burned on an abandoned draft
    assert 0 < app["completeness_pct"] < 100


def test_submission_needs_steps_one_to_three(client, admin):
    app = _draft(client, admin)
    r = client.post(
        f"/admin/admission/applications/{app['id']}/submit", headers=admin
    )
    assert r.status_code == 422
    assert "guardian" in r.json()["detail"]

    _guardian(client, admin, app["id"])
    r = client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "submitted"
    assert r.json()["application_no"].startswith("APP")


def test_exactly_one_primary_contact(client, admin):
    app = _draft(client, admin)
    two_primaries = [
        {"relation": "father", "full_name": "A", "mobile": "9811155502", "is_primary": True},
        {"relation": "mother", "full_name": "B", "mobile": "9811155503", "is_primary": True},
    ]
    r = client.put(
        f"/admin/admission/applications/{app['id']}/guardians",
        json=two_primaries,
        headers=admin,
    )
    assert r.status_code == 422

    none_primary = [dict(g, is_primary=False) for g in two_primaries]
    r = client.put(
        f"/admin/admission/applications/{app['id']}/guardians",
        json=none_primary,
        headers=admin,
    )
    assert r.status_code == 422


def test_an_out_of_range_age_warns_and_still_submits(client, admin):
    """§5.1.9(1): out of range is an override decision, not a rejection. A
    validation error here would hide the applicant from the office entirely."""
    app = _draft(client, admin, date_of_birth="2023-05-14")  # far too young for class 1
    _guardian(client, admin, app["id"], mobile="9811155504")
    r = client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "submitted"
    assert any("below the minimum" in w for w in body["warnings"])


def test_a_recorded_override_silences_the_age_warning(client, admin):
    app = _draft(client, admin, date_of_birth="2023-05-14")
    _guardian(client, admin, app["id"], mobile="9811155505")
    client.patch(
        f"/admin/admission/applications/{app['id']}",
        json={"age_override_reason": "Management approval, letter on file"},
        headers=admin,
    )
    body = client.post(
        f"/admin/admission/applications/{app['id']}/submit", headers=admin
    ).json()
    assert body["warnings"] == []


def test_a_duplicate_is_shown_not_blocked(client, admin):
    """§5.1.9(2): genuine twins exist. A hard block just produces a worse
    second record."""
    first = _draft(client, admin)
    _guardian(client, admin, first["id"], mobile="9811155506")
    client.post(f"/admin/admission/applications/{first['id']}/submit", headers=admin)

    twin = _draft(client, admin, first_name="Aarohi")
    _guardian(client, admin, twin["id"], mobile="9811155506")
    body = client.post(
        f"/admin/admission/applications/{twin['id']}/submit", headers=admin
    ).json()
    assert body["status"] == "submitted"
    reasons = " ".join(r for d in body["possible_duplicates"] for r in d["reasons"])
    assert "Same surname and date of birth" in reasons
    assert "9811155506" in reasons


def test_a_sibling_claim_counts_only_once_it_points_at_a_student(client, admin, db):
    app = _draft(client, admin, admission_category="sibling")
    assert app["effective_category"] == "general"  # unverified, so it does not count

    matches = client.get(
        "/admin/admission/sibling-search?q=2024", headers=admin
    ).json()
    assert matches, "the seeded students should be searchable by admission number"

    detail = client.put(
        f"/admin/admission/applications/{app['id']}/siblings",
        json=[{"student_id": matches[0]["student_id"]}],
        headers=admin,
    ).json()
    assert detail["sibling_verified"] is True
    assert detail["effective_category"] == "sibling"


def test_a_free_text_sibling_earns_nothing(client, admin):
    app = _draft(client, admin, admission_category="sibling")
    detail = client.put(
        f"/admin/admission/applications/{app['id']}/siblings",
        json=[{"name": "Some Child", "age": 9, "school_name": "Elsewhere"}],
        headers=admin,
    ).json()
    assert detail["sibling_verified"] is False
    assert detail["effective_category"] == "general"


def test_moving_an_application_backwards_needs_a_reason(client, admin, db):
    app = _draft(client, admin)
    _guardian(client, admin, app["id"], mobile="9811155507")
    client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    client.post(
        f"/admin/admission/applications/{app['id']}/status",
        json={"status": "documents_verified"},
        headers=admin,
    )

    r = client.post(
        f"/admin/admission/applications/{app['id']}/status",
        json={"status": "under_document_verification"},
        headers=admin,
    )
    assert r.status_code == 422

    r = client.post(
        f"/admin/admission/applications/{app['id']}/status",
        json={
            "status": "under_document_verification",
            "reason": "Birth certificate turned out to be a photocopy",
        },
        headers=admin,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "under_document_verification"

    logged = db.scalars(
        select(AuditLog).where(AuditLog.entity_type == "application")
    ).all()
    assert any("photocopy" in (row.reason or "") for row in logged)


def test_converting_an_enquiry_closes_it_and_links_both_ways(client, admin, db):
    enquiry = client.post(
        "/admin/admission/enquiries",
        json={"enquirer_name": "Priya Nair", "mobile": "9811155508"},
        headers=admin,
    ).json()

    app = _draft(client, admin, enquiry_id=enquiry["id"], last_name="Nair")
    detail = client.get(
        f"/admin/admission/enquiries/{enquiry['id']}", headers=admin
    ).json()
    assert detail["status"] == "converted"
    assert detail["converted_application_id"] == app["id"]
    assert detail["next_follow_up_on"] is None


def test_medical_is_gated_apart_from_the_rest_of_the_application(client, admin, db):
    """§15: a receptionist who may see the application must not thereby learn
    about a child's epilepsy."""
    from app.core.permissions import SYSTEM_ROLES

    receptionist = dict((code, perms) for code, _, perms in SYSTEM_ROLES)["receptionist"]
    officer = dict((code, perms) for code, _, perms in SYSTEM_ROLES)["admission_officer"]
    assert "admission.medical.read" not in receptionist
    assert "admission.medical.read" not in officer

    app = _draft(client, admin)
    r = client.put(
        f"/admin/admission/applications/{app['id']}/medical",
        json={"known_allergies": "Peanuts", "consent_for_emergency_treatment": True},
        headers=admin,
    )
    assert r.status_code == 200
    assert r.json()["known_allergies"] == "Peanuts"
    # And it is not smuggled out through the ordinary detail view.
    detail = client.get(
        f"/admin/admission/applications/{app['id']}", headers=admin
    ).json()
    assert "known_allergies" not in str(detail)


def test_an_enrolled_application_is_closed_to_further_moves(client, admin, db):
    app_row = db.get(Application, _draft(client, admin)["id"])
    app_row.status = "enrolled"
    db.commit()
    r = client.post(
        f"/admin/admission/applications/{app_row.id}/status",
        json={"status": "rejected", "reason": "changed our mind"},
        headers=admin,
    )
    assert r.status_code == 409


def test_a_teacher_cannot_read_applications(client, teacher):
    assert (
        client.get("/admin/admission/applications", headers=teacher).status_code == 403
    )
