"""The marks lock, the three states, and the audited override.

§5.4.9's rule is absolute — *every post-lock change is audited without
exception* — so the test that matters most is the one that reads the audit log
back and finds the old mark, the new mark, who moved it and why.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import AuditAction, AuditLog, ExamSchedule, Mark


def paper(db, ids, subject="maths"):
    return (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == ids["section_10a"],
            ExamSchedule.subject_id == ids[subject],
        )
        .order_by(ExamSchedule.max_marks.desc())
        .first()
    )


def enter(client, headers, p, student_id, reason=None, **fields):
    """The subject teacher's route: only the papers they teach."""
    body = {
        "exam_schedule_id": p.id,
        "entries": [{"student_id": student_id, **fields}],
    }
    if reason is not None:
        body["reason"] = reason
    return client.post("/teacher/marks", headers=headers, json=body)


def controller_enter(client, headers, p, student_id, reason=None, **fields):
    """The exam controller's route: every paper in the school, which is the
    only way an override on a subject they do not teach can happen at all."""
    body = {
        "exam_schedule_id": p.id,
        "entries": [{"student_id": student_id, **fields}],
    }
    if reason is not None:
        body["reason"] = reason
    return client.post(
        f"/admin/exams/papers/{p.id}/marks", headers=headers, json=body
    )


def mark_of(db, p, student_id):
    return db.scalar(
        select(Mark).where(
            Mark.exam_schedule_id == p.id, Mark.student_id == student_id
        )
    )


def test_a_teacher_may_enter_marks_while_the_paper_is_open(client, teacher, db, ids):
    p = paper(db, ids)
    r = enter(client, teacher, p, ids["student_1"], marks_obtained=str(p.max_marks / 2))
    assert r.status_code == 200, r.text


def test_absent_exempted_and_zero_are_three_different_things(client, teacher, db, ids):
    p = paper(db, ids)

    assert enter(client, teacher, p, ids["student_1"], marks_obtained="0").status_code == 200
    row = mark_of(db, p, ids["student_1"])
    db.refresh(row)
    assert row.marks_obtained == Decimal(0)
    assert (row.is_absent, row.is_exempted) == (False, False), "zero is a mark"

    assert enter(client, teacher, p, ids["student_1"], is_absent=True).status_code == 200
    db.refresh(row)
    assert row.marks_obtained is None and row.is_absent and not row.is_exempted

    assert enter(client, teacher, p, ids["student_1"], is_exempted=True).status_code == 200
    db.refresh(row)
    assert row.marks_obtained is None and row.is_exempted and not row.is_absent


def test_absent_and_exempted_together_is_refused(client, teacher, db, ids):
    p = paper(db, ids)
    r = enter(client, teacher, p, ids["student_1"], is_absent=True, is_exempted=True)
    assert r.status_code == 422
    assert "not both" in r.json()["detail"]


def test_an_absent_child_cannot_also_carry_a_score(client, teacher, db, ids):
    p = paper(db, ids)
    r = enter(client, teacher, p, ids["student_1"], is_absent=True, marks_obtained="5")
    assert r.status_code == 422
    assert "cannot also carry a score" in r.json()["detail"]


def test_saying_nothing_about_a_child_leaves_their_mark_alone(client, teacher, db, ids):
    """A blank cell in the grid means "not entered", not "erase what is there"."""
    p = paper(db, ids)
    enter(client, teacher, p, ids["student_1"], marks_obtained=str(p.max_marks / 2))
    before = mark_of(db, p, ids["student_1"]).marks_obtained

    assert enter(client, teacher, p, ids["student_1"]).status_code == 200
    assert mark_of(db, p, ids["student_1"]).marks_obtained == before


def test_a_paper_with_nothing_entered_cannot_be_locked(client, admin, db, ids):
    p = paper(db, ids)
    db.query(Mark).filter(Mark.exam_schedule_id == p.id).delete()
    db.flush()
    r = client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin)
    assert r.status_code == 409
    assert "nothing" in r.json()["detail"].lower()


def test_locking_is_idempotent(client, admin, db, ids):
    p = paper(db, ids)
    assert client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin).status_code == 200
    r = client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin)
    assert r.status_code == 200, "two clerks clicking lock is not a fault"
    assert r.json()["marks_locked"] is True


def test_a_teacher_cannot_change_a_mark_once_the_paper_is_locked(
    client, admin, teacher, db, ids
):
    p = paper(db, ids)
    client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin)
    r = enter(client, teacher, p, ids["student_1"], marks_obtained="1")
    assert r.status_code == 409
    assert "override" in r.json()["detail"]


def test_an_override_without_a_reason_is_refused(client, admin, db, ids):
    p = paper(db, ids)
    client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin)
    r = controller_enter(client, admin, p, ids["student_1"], marks_obtained="1")
    assert r.status_code == 422
    assert "reason is required" in r.json()["detail"]


def test_a_post_lock_change_lands_in_the_audit_log_with_both_marks(
    client, admin, db, ids
):
    """The rule with no exceptions. This log is where a re-evaluation dispute
    is settled, so it must carry the old mark, the new one and the why."""
    p = paper(db, ids)
    before = mark_of(db, p, ids["student_1"]).marks_obtained
    assert before is not None
    client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin)

    new_value = before + 1 if before + 1 <= p.max_marks else Decimal(0)
    r = controller_enter(
        client,
        admin,
        p,
        ids["student_1"],
        reason="Re-evaluation requested by the guardian",
        marks_obtained=str(new_value),
    )
    assert r.status_code == 200, r.text

    mark = mark_of(db, p, ids["student_1"])
    entry = db.scalar(
        select(AuditLog)
        .where(AuditLog.entity_type == "mark", AuditLog.entity_id == mark.id)
        .order_by(AuditLog.occurred_at.desc())
    )
    assert entry is not None, "a post-lock change with no audit entry is the bug"
    assert entry.action is AuditAction.status_change
    assert entry.reason == "Re-evaluation requested by the guardian"
    assert Decimal(entry.before["marks_obtained"]) == before
    assert Decimal(entry.after["marks_obtained"]) == new_value
    assert entry.actor_label


def test_an_open_paper_edit_is_not_audited(client, teacher, db, ids):
    """A teacher fixing a typo before the lock is entering marks, not amending
    a record — the same distinction attendance draws between marking and
    correcting."""
    p = paper(db, ids)
    mark = mark_of(db, p, ids["student_1"])
    enter(client, teacher, p, ids["student_1"], marks_obtained="1")
    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "mark", AuditLog.entity_id == mark.id
        )
    )
    assert entry is None


def test_unlocking_needs_a_real_reason_and_is_audited(client, admin, db, ids):
    p = paper(db, ids)
    client.post(f"/admin/exams/papers/{p.id}/lock", headers=admin)
    short = client.post(
        f"/admin/exams/papers/{p.id}/unlock", headers=admin, json={"reason": "x"}
    )
    assert short.status_code == 422, "a three-character minimum keeps 'x' out"

    r = client.post(
        f"/admin/exams/papers/{p.id}/unlock",
        headers=admin,
        json={"reason": "Moderation found a totalling error across the section"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["marks_locked"] is False
    entry = db.scalar(
        select(AuditLog)
        .where(AuditLog.entity_type == "exam_schedule", AuditLog.entity_id == p.id)
        .order_by(AuditLog.occurred_at.desc())
    )
    assert entry.action is AuditAction.status_change
    assert "totalling error" in entry.reason


def test_the_dashboard_and_the_report_card_agree_about_an_absent_child(
    client, teacher, db, ids, student
):
    """§5.10.9: one definition, not two queries that drift. An absent paper is
    excluded from both totals, so the two numbers must still match."""
    from app.services import stats

    p = paper(db, ids)
    enter(client, teacher, p, ids["student_1"], is_absent=True)

    card = client.get(f"/student/results/{p.exam_id}", headers=student).json()
    dash = stats.exam_percentages(db, p.exam_id)[ids["student_1"]]
    assert card["overall_percent"] == pytest.approx(dash, abs=0.1)

    row = next(r for r in card["rows"] if r["is_absent"])
    assert row["marks_obtained"] is None
    assert float(card["total_max"]) == float(p.max_marks) * 5, "the absent paper is out"


def test_a_teacher_cannot_reach_a_paper_they_do_not_teach(client, other_teacher, db, ids):
    """The controller route is school-wide; the teacher route is not, and
    widening one must not widen the other."""
    p = paper(db, ids)
    r = enter(client, other_teacher, p, ids["student_1"], marks_obtained="1")
    assert r.status_code == 403


def test_a_teacher_cannot_use_the_controller_route(client, teacher, db, ids):
    """Even for their own paper: entering school-wide is the controller's
    permission, and TCH001 does not hold it."""
    p = paper(db, ids)
    r = controller_enter(client, teacher, p, ids["student_1"], marks_obtained="1")
    assert r.status_code == 403


def test_a_teacher_cannot_read_another_sections_marks_through_the_admin_route(
    client, teacher, db, ids
):
    """The hole this route nearly opened. A teacher holds `exam.marks.enter`
    *unscoped* — "own subjects only" is enforced in the service, not by the
    grant — so gating the school-wide route on that permission would have let
    any teacher mark any section."""
    p = paper(db, ids)
    r = client.get(f"/admin/exams/papers/{p.id}/marks", headers=teacher)
    assert r.status_code == 403
