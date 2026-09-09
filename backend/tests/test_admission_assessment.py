"""Applicant assessment and interview (§5.1.9(7)-(10))."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import User

YESTERDAY = (datetime.now(UTC) - timedelta(days=1)).isoformat()
TOMORROW = (datetime.now(UTC) + timedelta(days=1)).isoformat()


@pytest.fixture()
def application(client, admin):
    app = client.post(
        "/admin/admission/applications",
        json={
            "first_name": "Riya",
            "last_name": "Chauhan",
            "date_of_birth": "2014-07-11",
            "gender": "female",
            "class_applying_for": "6",
        },
        headers=admin,
    ).json()
    client.put(
        f"/admin/admission/applications/{app['id']}/guardians",
        json=[
            {
                "relation": "mother",
                "full_name": "Pooja Chauhan",
                "mobile": "9866600001",
                "is_primary": True,
            }
        ],
        headers=admin,
    )
    client.post(f"/admin/admission/applications/{app['id']}/submit", headers=admin)
    return app


def _schedule(client, admin, application_id, when=YESTERDAY):
    r = client.post(
        f"/admin/admission/applications/{application_id}/assessments",
        json={
            "assessment_type": "written_test",
            "scheduled_at": when,
            "venue": "Hall A",
            "seat_no": "A-14",
            "subjects": [
                {"subject": "Mathematics", "max_marks": "40"},
                {"subject": "English", "max_marks": "40"},
            ],
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_scheduling_moves_the_application_along(client, admin, application):
    _schedule(client, admin, application["id"])
    detail = client.get(
        f"/admin/admission/applications/{application['id']}", headers=admin
    ).json()
    assert detail["status"] == "assessment_scheduled"


def test_marks_cannot_be_entered_before_the_paper_is_sat(client, admin, application):
    """§5.1.9(7)."""
    row = _schedule(client, admin, application["id"], when=TOMORROW)
    r = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={"obtained_marks": "30", "total_marks": "80"},
        headers=admin,
    )
    assert r.status_code == 409


def test_marks_cannot_exceed_the_maximum(client, admin, application):
    row = _schedule(client, admin, application["id"])
    r = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={"obtained_marks": "90", "total_marks": "80"},
        headers=admin,
    )
    assert r.status_code == 422

    r = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={
            "obtained_marks": "60",
            "total_marks": "80",
            "subject_marks": {"Mathematics": "45"},
        },
        headers=admin,
    )
    assert r.status_code == 422
    assert "Mathematics" in r.json()["detail"]


def test_absent_is_not_a_score_of_zero(client, admin, application):
    """§5.1.9(8): a child who did not sit the paper has not scored badly, and
    averaging the two together is a lie about the cohort."""
    row = _schedule(client, admin, application["id"])
    body = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={"is_absent": True},
        headers=admin,
    ).json()
    assert body["status"] == "absent"
    assert body["is_absent"] is True
    assert body["obtained_marks"] is None
    assert body["percent"] is None


def test_recording_marks_completes_the_stage(client, admin, application):
    row = _schedule(client, admin, application["id"])
    body = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={
            "obtained_marks": "62",
            "total_marks": "80",
            "subject_marks": {"Mathematics": "34", "English": "28"},
        },
        headers=admin,
    ).json()
    assert body["percent"] == "77.50"
    assert [s["obtained"] for s in body["subjects"]] == ["34.00", "28.00"]

    detail = client.get(
        f"/admin/admission/applications/{application['id']}", headers=admin
    ).json()
    assert detail["status"] == "assessment_completed"


def test_changing_a_recorded_mark_needs_a_reason(client, admin, application, db):
    """§5.1.9(10)."""
    row = _schedule(client, admin, application["id"])
    client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={"obtained_marks": "62", "total_marks": "80"},
        headers=admin,
    )
    r = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={"obtained_marks": "72", "total_marks": "80"},
        headers=admin,
    )
    assert r.status_code == 422

    r = client.post(
        f"/admin/admission/assessments/{row['id']}/marks",
        json={
            "obtained_marks": "72",
            "total_marks": "80",
            "reason": "Section C was not totalled",
        },
        headers=admin,
    )
    assert r.status_code == 200
    assert r.json()["obtained_marks"] == "72.00"

    from app.models import AuditLog

    logged = db.scalars(select(AuditLog).where(AuditLog.entity_type == "assessment")).all()
    assert any("totalled" in (row.reason or "") for row in logged)


def test_a_panel_member_sees_no_one_elses_score_until_they_submit(
    client, admin, teacher, application, db
):
    """§5.1.9(9): otherwise the second panelist agrees with the first and the
    school has one opinion wearing three hats."""
    admin_user = db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))
    teacher_user = db.scalar(select(User).where(User.login_id == "TCH001"))

    created = client.post(
        f"/admin/admission/applications/{application['id']}/interviews",
        json={
            "scheduled_at": YESTERDAY,
            "venue": "Principal's office",
            "panel_member_ids": [admin_user.id, teacher_user.id],
        },
        headers=admin,
    )
    assert created.status_code == 201, created.text
    interview_id = created.json()["id"]

    client.post(
        f"/admin/admission/interviews/{interview_id}/feedback",
        json={"child_rating": 4, "parent_rating": 5, "recommendation": "admit"},
        headers=admin,
    )

    # The teacher has not scored yet, so they see nothing of the admin's view.
    blind = client.get(
        f"/admin/admission/interviews/{interview_id}", headers=teacher
    ).json()
    assert blind["scores"] == {}

    client.post(
        f"/admin/admission/interviews/{interview_id}/feedback",
        json={"child_rating": 3, "parent_rating": 4, "recommendation": "waitlist"},
        headers=teacher,
    )
    open_now = client.get(
        f"/admin/admission/interviews/{interview_id}", headers=teacher
    ).json()
    assert len(open_now["scores"]) == 2
    # The summary is the panel's average, not whoever saved last.
    assert open_now["child_rating"] == 4  # round((4 + 3) / 2)
    assert open_now["status"] == "completed"

    detail = client.get(
        f"/admin/admission/applications/{application['id']}", headers=admin
    ).json()
    assert detail["status"] == "interview_completed"


def test_someone_off_the_panel_cannot_score(client, admin, teacher, application, db):
    admin_user = db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))
    interview_id = client.post(
        f"/admin/admission/applications/{application['id']}/interviews",
        json={"scheduled_at": YESTERDAY, "panel_member_ids": [admin_user.id]},
        headers=admin,
    ).json()["id"]

    r = client.post(
        f"/admin/admission/interviews/{interview_id}/feedback",
        json={"child_rating": 5},
        headers=teacher,
    )
    assert r.status_code == 403


def test_feedback_cannot_precede_the_interview(client, admin, application, db):
    admin_user = db.scalar(select(User).where(User.login_id == "admin@sunrisepublic.edu"))
    interview_id = client.post(
        f"/admin/admission/applications/{application['id']}/interviews",
        json={"scheduled_at": TOMORROW, "panel_member_ids": [admin_user.id]},
        headers=admin,
    ).json()["id"]
    r = client.post(
        f"/admin/admission/interviews/{interview_id}/feedback",
        json={"child_rating": 5},
        headers=admin,
    )
    assert r.status_code == 409
