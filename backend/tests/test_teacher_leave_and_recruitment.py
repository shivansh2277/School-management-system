"""Tests for Teacher Leave Management (mobile apply, substitution gating, purge on rejection)."""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.models import (

    Employee,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)

pytestmark = pytest.mark.usefixtures("hr_enabled")


def next_weekday(start: date, weekday: int) -> date:
    """The next date on or after `start` falling on `weekday` (Mon=0)."""
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def test_teacher_mobile_leave_apply_and_history(client, teacher, db):
    """Teacher applies for leave through mobile API without leave type or balance consumption."""
    start = next_weekday(date.today() + timedelta(days=2), 0)  # Next Monday
    end = start + timedelta(days=1)  # Tuesday

    resp = client.post(
        "/teacher/leave/apply",
        json={
            "from_date": str(start),
            "to_date": str(end),
            "reason": "Family function attending out of town",
            "is_half_day": False,
        },
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "applied"
    assert data["leave_type"] is None
    assert data["leave_type_name"] == "Teacher Leave"
    assert data["reason"] == "Family function attending out of town"

    # Verify history endpoint
    hist_resp = client.get("/teacher/leave/history", headers=teacher)
    assert hist_resp.status_code == 200
    hist = hist_resp.json()
    assert any(h["id"] == data["id"] for h in hist)

    # Verify teacher cannot double-apply for overlapping dates
    overlap_resp = client.post(
        "/teacher/leave/apply",
        json={
            "from_date": str(start),
            "to_date": str(end),
            "reason": "Another reason",
        },
        headers=teacher,
    )
    assert overlap_resp.status_code == 409


def test_timetable_substitution_gate_blocks_approval(client, teacher, admin, db):
    """Admin cannot approve teacher leave until 100% of affected periods have confirmed substitutes."""
    # Find teacher 1's Monday classes
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    slots = list(
        db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.teacher_id == t1.id,
                TimetableSlot.day_of_week == "mon",
            )
        )
    )
    assert len(slots) > 0, "Teacher TCH001 has no Monday classes seeded"

    mon = next_weekday(date.today() + timedelta(days=14), 0)
    apply_resp = client.post(
        "/teacher/leave/apply",
        json={
            "from_date": str(mon),
            "to_date": str(mon),
            "reason": "Doctor appointment",
        },
        headers=teacher,
    )
    assert apply_resp.status_code == 201
    leave_id = apply_resp.json()["id"]

    # Admin checks substitution matrix
    matrix_resp = client.get(
        f"/admin/staff-leave/{leave_id}/substitution-matrix",
        headers=admin,
    )
    assert matrix_resp.status_code == 200
    matrix = matrix_resp.json()
    assert matrix["total_periods"] == len(slots)
    assert matrix["covered_periods"] == 0
    assert matrix["is_fully_covered"] is False

    # Attempting approval with 0 substitutes MUST fail with 400 Bad Request
    appr_resp = client.post(
        f"/admin/staff-leave/{leave_id}/approve-with-substitutions",
        json={"note": "Premature approval attempt"},
        headers=admin,
    )
    assert appr_resp.status_code == 400
    assert "lack confirmed substitutes" in appr_resp.json()["detail"]


def test_provisional_substitution_assignment_and_approval(client, teacher, other_teacher, admin, db):
    """Assigning substitutes across all affected periods allows leave approval and notifies parties."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    slots = list(
        db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.teacher_id == t1.id,
                TimetableSlot.day_of_week == "mon",
            )
        )
    )
    mon = next_weekday(date.today() + timedelta(days=21), 0)
    apply_resp = client.post(
        "/teacher/leave/apply",
        json={
            "from_date": str(mon),
            "to_date": str(mon),
            "reason": "Wedding in family",
        },
        headers=teacher,
    )
    assert apply_resp.status_code == 201
    leave_id = apply_resp.json()["id"]

    # Retrieve matrix to get free teachers for each period
    matrix = client.get(
        f"/admin/staff-leave/{leave_id}/substitution-matrix",
        headers=admin,
    ).json()

    # Assign a substitute for every period
    for period in matrix["periods"]:
        slot_id = period["slot_id"]
        avail = period["available_teachers"]
        assert len(avail) > 0, f"No free teacher available for period {period['period_no']}"
        sub_teacher_id = avail[0]["teacher_id"]

        assign_resp = client.post(
            f"/admin/staff-leave/{leave_id}/provisional-substitution",
            json={
                "slot_id": slot_id,
                "date": str(mon),
                "substitute_teacher_id": sub_teacher_id,
                "reason": "Arranged cover",
            },
            headers=admin,
        )
        assert assign_resp.status_code == 200, assign_resp.text
        assert assign_resp.json()["status"] == "provisional"

    # Check matrix again: now 100% covered
    matrix_after = client.get(
        f"/admin/staff-leave/{leave_id}/substitution-matrix",
        headers=admin,
    ).json()
    assert matrix_after["covered_periods"] == matrix_after["total_periods"]
    assert matrix_after["is_fully_covered"] is True

    # Now approval succeeds!
    approve_resp = client.post(
        f"/admin/staff-leave/{leave_id}/approve-with-substitutions",
        json={"note": "Approved with full cover"},
        headers=admin,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # Substitutions are confirmed (assigned status)
    subs = list(
        db.scalars(
            select(Substitution).where(Substitution.leave_request_id == leave_id)
        )
    )
    assert len(subs) == len(slots)
    for s in subs:
        assert s.status == SubstitutionStatus.assigned


def test_leave_rejection_purges_provisional_substitutions(client, teacher, admin, db):
    """Rejecting a leave request purges all provisional substitutions and leaves the timetable restored."""
    tue = next_weekday(date.today() + timedelta(days=28), 1)

    apply_resp = client.post(
        "/teacher/leave/apply",
        json={
            "from_date": str(tue),
            "to_date": str(tue),
            "reason": "Personal work",
        },
        headers=teacher,
    )
    assert apply_resp.status_code == 201
    leave_id = apply_resp.json()["id"]

    matrix = client.get(
        f"/admin/staff-leave/{leave_id}/substitution-matrix",
        headers=admin,
    ).json()

    if matrix["periods"]:
        first_period = matrix["periods"][0]
        avail = first_period["available_teachers"]
        if avail:
            sub_id = avail[0]["teacher_id"]
            client.post(
                f"/admin/staff-leave/{leave_id}/provisional-substitution",
                json={
                    "slot_id": first_period["slot_id"],
                    "date": str(tue),
                    "substitute_teacher_id": sub_id,
                },
                headers=admin,
            )

    # Verify provisional substitution exists in db
    subs_before = list(
        db.scalars(
            select(Substitution).where(Substitution.leave_request_id == leave_id)
        )
    )
    assert len(subs_before) > 0

    # Admin rejects leave
    rej_resp = client.post(
        f"/admin/staff-leave/{leave_id}/reject",
        json={"reason": "Critical exams scheduled that day"},
        headers=admin,
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "rejected"

    # All provisional substitutions tied to this leave are completely purged!
    subs_after = list(
        db.scalars(
            select(Substitution).where(Substitution.leave_request_id == leave_id)
        )
    )
    assert len(subs_after) == 0

