"""Tests for Session 18 Teacher Leave System & Ranked Substitutions."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import (
    Employee,
    LeaveStatus,
    LeaveTypeDef,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import staff_leave as svc

pytestmark = pytest.mark.usefixtures("hr_enabled")


def next_weekday(start: date, weekday: int) -> date:
    """The next date on or after `start` falling on `weekday` (Mon=0)."""
    return start + timedelta(days=(weekday - start.weekday()) % 7)


def test_teacher_leave_types_endpoint(client, teacher, db):
    """GET /teacher/leave/types returns active leave types with is_casual flag."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    # Ensure at least CL and SL leave types exist
    cl = db.scalar(select(LeaveTypeDef).where(LeaveTypeDef.school_id == t1.school_id, LeaveTypeDef.code == "CL"))
    if not cl:
        cl = svc.create_type(db, t1.school_id, code="CL", name="Casual Leave", annual_quota=Decimal("12"))
    sl = db.scalar(select(LeaveTypeDef).where(LeaveTypeDef.school_id == t1.school_id, LeaveTypeDef.code == "SL"))
    if not sl:
        sl = svc.create_type(db, t1.school_id, code="SL", name="Sick Leave", annual_quota=Decimal("10"))
    db.commit()

    resp = client.get("/teacher/leave/types", headers=teacher)
    assert resp.status_code == 200, resp.text
    types = resp.json()
    assert len(types) >= 2
    cl_item = next((t for t in types if t["code"] == "CL"), None)
    assert cl_item is not None
    assert cl_item["is_casual"] is True
    sl_item = next((t for t in types if t["code"] == "SL"), None)
    assert sl_item is not None
    assert sl_item["is_casual"] is False


def test_leave_inspect_returns_ranked_substitutes(client, teacher, db):
    """POST /teacher/leave/inspect inspects periods and returns 4-tier ranked substitutes."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    slots = list(
        db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.teacher_id == t1.id,
                TimetableSlot.day_of_week == "mon",
            )
        )
    )
    assert len(slots) > 0

    mon = next_weekday(date.today() + timedelta(days=7), 0)
    resp = client.post(
        "/teacher/leave/inspect",
        json={
            "from_date": str(mon),
            "to_date": str(mon),
            "is_half_day": False,
        },
        headers=teacher,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_periods"] == len(slots)
    assert len(data["periods"]) == len(slots)

    first_p = data["periods"][0]
    assert "ranked_substitutes" in first_p
    ranked = first_p["ranked_substitutes"]
    if len(ranked) > 0:
        sub0 = ranked[0]
        assert "teacher_id" in sub0
        assert "teacher_name" in sub0
        assert "rank" in sub0
        assert sub0["rank"] in (1, 2, 3, 4)
        assert "rank_label" in sub0
        # Ranks must be non-decreasing
        ranks = [r["rank"] for r in ranked]
        assert ranks == sorted(ranks)
        # Absent teacher cannot be in suggestions
        assert all(r["teacher_id"] != t1.id for r in ranked)


def test_casual_leave_requires_all_substitutions(client, teacher, db):
    """Applying for Casual Leave without substitutes is rejected; applying with full substitutes succeeds."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    cl = db.scalar(select(LeaveTypeDef).where(LeaveTypeDef.school_id == t1.school_id, LeaveTypeDef.code == "CL"))
    if not cl:
        cl = svc.create_type(db, t1.school_id, code="CL", name="Casual Leave", annual_quota=Decimal("12"))
        db.commit()

    mon = next_weekday(date.today() + timedelta(days=14), 0)
    inspect_resp = client.post(
        "/teacher/leave/inspect",
        json={"from_date": str(mon), "to_date": str(mon), "is_half_day": False},
        headers=teacher,
    )
    inspected = inspect_resp.json()
    periods = inspected["periods"]
    assert len(periods) > 0

    # 1. Applying without substitutions should fail with 400
    fail_resp = client.post(
        "/teacher/leave/apply",
        json={
            "leave_type_id": cl.id,
            "from_date": str(mon),
            "to_date": str(mon),
            "reason": "Personal urgent work",
            "is_half_day": False,
            "substitutions": [],
        },
        headers=teacher,
    )
    assert fail_resp.status_code == 400
    assert "Casual Leave requires a substitute" in fail_resp.json()["detail"]

    # 2. Applying with partial substitutions should also fail
    first_sub = periods[0]["ranked_substitutes"][0] if periods[0]["ranked_substitutes"] else None
    if first_sub and len(periods) > 1:
        partial_resp = client.post(
            "/teacher/leave/apply",
            json={
                "leave_type_id": cl.id,
                "from_date": str(mon),
                "to_date": str(mon),
                "reason": "Personal urgent work",
                "is_half_day": False,
                "substitutions": [
                    {
                        "slot_id": periods[0]["slot_id"],
                        "date": str(mon),
                        "substitute_teacher_id": first_sub["teacher_id"],
                    }
                ],
            },
            headers=teacher,
        )
        assert partial_resp.status_code == 400

    # 3. Applying with full substitutions succeeds
    full_subs = []
    for p in periods:
        cand = p["ranked_substitutes"][0]["teacher_id"] if p["ranked_substitutes"] else None
        assert cand is not None, f"No substitute candidate for period {p['period_no']}"
        full_subs.append({
            "slot_id": p["slot_id"],
            "date": str(mon),
            "substitute_teacher_id": cand,
        })

    succ_resp = client.post(
        "/teacher/leave/apply",
        json={
            "leave_type_id": cl.id,
            "from_date": str(mon),
            "to_date": str(mon),
            "reason": "Family ceremony",
            "is_half_day": False,
            "substitutions": full_subs,
        },
        headers=teacher,
    )
    assert succ_resp.status_code == 201, succ_resp.text
    leave_id = succ_resp.json()["id"]

    # Verify substitutions were saved with pending status
    subs = list(db.scalars(select(Substitution).where(Substitution.leave_request_id == leave_id)))
    assert len(subs) == len(periods)
    for s in subs:
        assert s.status == SubstitutionStatus.pending


def test_non_casual_leave_applies_without_substitutions(client, teacher, db):
    """Non-casual leaves (e.g. SL / Medical) can be applied directly without substitutions."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    sl = db.scalar(select(LeaveTypeDef).where(LeaveTypeDef.school_id == t1.school_id, LeaveTypeDef.code == "SL"))
    if not sl:
        sl = svc.create_type(db, t1.school_id, code="SL", name="Sick Leave", annual_quota=Decimal("10"))
        db.commit()

    tue = next_weekday(date.today() + timedelta(days=21), 1)
    resp = client.post(
        "/teacher/leave/apply",
        json={
            "leave_type_id": sl.id,
            "from_date": str(tue),
            "to_date": str(tue),
            "reason": "Doctor appointment for routine checkup",
            "is_half_day": False,
        },
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "applied"
    assert data["leave_type"] == "SL"


def test_substitute_accept_workflow_and_approval_gate(client, teacher, other_teacher, admin, db):
    """Proposed substitute accepts request -> status becomes assigned -> admin can approve."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    t4 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH004"))
    cl = db.scalar(select(LeaveTypeDef).where(LeaveTypeDef.school_id == t1.school_id, LeaveTypeDef.code == "CL"))
    if not cl:
        cl = svc.create_type(db, t1.school_id, code="CL", name="Casual Leave", annual_quota=Decimal("12"))
        db.commit()

    wed = next_weekday(date.today() + timedelta(days=28), 2)
    inspect_resp = client.post(
        "/teacher/leave/inspect",
        json={"from_date": str(wed), "to_date": str(wed), "is_half_day": False},
        headers=teacher,
    )
    periods = inspect_resp.json()["periods"]
    assert len(periods) > 0

    full_subs = [
        {"slot_id": p["slot_id"], "date": str(wed), "substitute_teacher_id": t4.id}
        for p in periods
    ]

    apply_resp = client.post(
        "/teacher/leave/apply",
        json={
            "leave_type_id": cl.id,
            "from_date": str(wed),
            "to_date": str(wed),
            "reason": "Important personal obligation",
            "is_half_day": False,
            "substitutions": full_subs,
        },
        headers=teacher,
    )
    assert apply_resp.status_code == 201
    leave_id = apply_resp.json()["id"]

    # 1. Admin attempts approval before acceptance -> MUST fail
    premature_resp = client.post(
        f"/admin/staff-leave/{leave_id}/approve-with-substitutions",
        json={"note": "Attempt approval before acceptance"},
        headers=admin,
    )
    assert premature_resp.status_code == 400
    assert "lack confirmed substitutes" in premature_resp.json()["detail"]

    # 2. Other teacher (TCH004) checks pending substitution requests
    reqs_resp = client.get("/teacher/substitutions/requests", headers=other_teacher)
    assert reqs_resp.status_code == 200
    pending_reqs = reqs_resp.json()
    assert any(r["leave_request_id"] == leave_id for r in pending_reqs)

    # 3. Other teacher accepts all requests for this leave
    for pr in pending_reqs:
        if pr["leave_request_id"] == leave_id:
            accept_resp = client.post(
                f"/teacher/substitutions/{pr['id']}/respond",
                json={"action": "accept"},
                headers=other_teacher,
            )
            assert accept_resp.status_code == 200
            assert accept_resp.json()["status"] == "assigned"

    # 4. Now admin approval succeeds!
    approve_resp = client.post(
        f"/admin/staff-leave/{leave_id}/approve-with-substitutions",
        json={"note": "Approved after teacher confirmation"},
        headers=admin,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


def test_substitute_reject_and_reassign_workflow(client, teacher, other_teacher, admin, db):
    """Proposed substitute rejects request -> teacher reassigns to another candidate -> approval succeeds."""
    t1 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH001"))
    t4 = db.scalar(select(Employee).join(User).where(User.login_id == "TCH004"))
    cl = db.scalar(select(LeaveTypeDef).where(LeaveTypeDef.school_id == t1.school_id, LeaveTypeDef.code == "CL"))
    if not cl:
        cl = svc.create_type(db, t1.school_id, code="CL", name="Casual Leave", annual_quota=Decimal("12"))
        db.commit()

    thu = next_weekday(date.today() + timedelta(days=35), 3)
    inspect_resp = client.post(
        "/teacher/leave/inspect",
        json={"from_date": str(thu), "to_date": str(thu), "is_half_day": False},
        headers=teacher,
    )
    periods = inspect_resp.json()["periods"]
    assert len(periods) > 0

    full_subs = [
        {"slot_id": p["slot_id"], "date": str(thu), "substitute_teacher_id": t4.id}
        for p in periods
    ]

    apply_resp = client.post(
        "/teacher/leave/apply",
        json={
            "leave_type_id": cl.id,
            "from_date": str(thu),
            "to_date": str(thu),
            "reason": "Home renovation supervision",
            "is_half_day": False,
            "substitutions": full_subs,
        },
        headers=teacher,
    )
    assert apply_resp.status_code == 201
    leave_id = apply_resp.json()["id"]

    # 1. Other teacher rejects the first request
    reqs_resp = client.get("/teacher/substitutions/requests", headers=other_teacher)
    my_reqs = [r for r in reqs_resp.json() if r["leave_request_id"] == leave_id]
    target_req = my_reqs[0]

    rej_resp = client.post(
        f"/teacher/substitutions/{target_req['id']}/respond",
        json={"action": "reject", "reason": "Already busy on that day"},
        headers=other_teacher,
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "rejected"

    # 2. Teacher checks application substitutions status
    app_subs_resp = client.get(
        f"/teacher/leave/applications/{leave_id}/substitutions",
        headers=teacher,
    )
    assert app_subs_resp.status_code == 200
    app_subs_data = app_subs_resp.json()
    assert app_subs_data["is_fully_accepted"] is False
    rej_p = next(p for p in app_subs_data["periods"] if p["slot_id"] == target_req["slot_id"])
    assert rej_p["status"] == "rejected"
    assert rej_p["can_reassign"] is True
    assert len(rej_p["ranked_substitutes"]) > 0

    # 3. Teacher reassigns the rejected period to another substitute candidate
    new_cand = rej_p["ranked_substitutes"][0]["teacher_id"]
    reassign_resp = client.post(
        f"/teacher/leave/applications/{leave_id}/reassign",
        json={
            "slot_id": target_req["slot_id"],
            "date": str(thu),
            "new_substitute_teacher_id": new_cand,
        },
        headers=teacher,
    )
    assert reassign_resp.status_code == 200
    assert reassign_resp.json()["status"] == "pending"
    assert reassign_resp.json()["substitute_teacher_id"] == new_cand
