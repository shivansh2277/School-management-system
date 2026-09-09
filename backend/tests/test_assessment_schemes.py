"""Assessment schemes: what a subject is marked out of, held as data.

The rule with teeth is the one in `set_components`: once an exam has been
marked against a component, restating that component's `max_marks` would turn
a child's 8/10 into 8/5 without touching the mark. These tests pin that, and
pin that the demo school's scheme is real rather than decorative.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Exam, ExamSchedule, Mark
from app.services import schemes

SIMPLE = [("CT", "Class Test", "Term 1", Decimal(20))]


def test_the_seeded_scheme_is_the_cbse_shape(db, ids):
    scheme = schemes.active_scheme(db, ids["year"])
    assert scheme is not None
    assert schemes.terms(db, scheme.id) == ["Term 1", "Term 2"]
    # 10 + 5 + 5 + 80: the layout the school asked for.
    assert schemes.term_total(db, scheme.id, "Term 1") == Decimal(100)
    assert schemes.term_total(db, scheme.id, "Term 2") == Decimal(100)
    assert [c.code for c in schemes.components(db, scheme.id, "Term 1")] == [
        "PT", "NB", "SE", "TERM",
    ]


def test_seeded_exams_cite_their_component_and_are_marked_out_of_it(db, ids):
    scheme = schemes.active_scheme(db, ids["year"])
    by_id = {c.id: c for c in schemes.components(db, scheme.id)}
    exams = db.scalars(
        select(Exam).where(Exam.school_id == ids["school"], Exam.term == "Term 1")
    ).all()
    assert exams, "the demo school should have a marked Term 1"
    for exam in exams:
        component = by_id[exam.scheme_component_id]
        papers = db.scalars(
            select(ExamSchedule).where(ExamSchedule.exam_id == exam.id)
        ).all()
        assert papers
        assert {p.max_marks for p in papers} == {component.max_marks}


def test_no_seeded_mark_exceeds_what_its_paper_is_out_of(db):
    """The seed scales a percentage into each component's own maximum. Getting
    that wrong would put 74/5 on a notebook."""
    over = db.scalar(
        select(Mark.id)
        .join(ExamSchedule, ExamSchedule.id == Mark.exam_schedule_id)
        .where(Mark.marks_obtained > ExamSchedule.max_marks)
        .limit(1)
    )
    assert over is None


def test_a_term_cannot_carry_the_same_code_twice(db, ids):
    with pytest.raises(Exception) as e:
        schemes.create(
            db,
            ids["school"],
            ids["year"],
            name="Dup",
            rows=[
                ("PT", "Periodic Test", "Term 1", Decimal(10)),
                ("PT", "Periodic Test Again", "Term 1", Decimal(10)),
            ],
        )
    assert "same component code twice" in str(e.value.detail)


def test_the_same_code_in_a_different_term_is_fine(db, ids):
    scheme = schemes.create(
        db,
        ids["school"],
        ids["year"],
        name="Two terms",
        rows=[
            ("PT", "Periodic Test", "Term 1", Decimal(10)),
            ("PT", "Periodic Test", "Term 2", Decimal(10)),
        ],
    )
    assert len(schemes.components(db, scheme.id)) == 2


def test_a_component_marked_out_of_nothing_is_refused(db, ids):
    with pytest.raises(Exception) as e:
        schemes.create(
            db, ids["school"], ids["year"], name="Zero",
            rows=[("X", "Nothing", "Term 1", Decimal(0))],
        )
    assert "more than zero" in str(e.value.detail)


def test_components_cannot_be_restated_once_an_exam_is_marked_against_them(db, ids):
    """The rule that protects marks already entered: an 8/10 must not silently
    become an 8/5 because somebody edited the scheme."""
    scheme = schemes.active_scheme(db, ids["year"])
    with pytest.raises(Exception) as e:
        schemes.set_components(db, scheme, SIMPLE)
    assert e.value.status_code == 409
    assert "already marked" in str(e.value.detail)


def test_an_untouched_scheme_can_still_be_edited(db, ids):
    scheme = schemes.create(db, ids["school"], ids["year"], name="Draft", rows=SIMPLE)
    schemes.set_components(
        db, scheme, [("CT", "Class Test", "Term 1", Decimal(25))]
    )
    assert schemes.term_total(db, scheme.id, "Term 1") == Decimal(25)


def test_only_one_scheme_is_in_force_for_a_year(db, ids):
    first = schemes.active_scheme(db, ids["year"])
    second = schemes.create(
        db, ids["school"], ids["year"], name="Revised", rows=SIMPLE, activate=True
    )
    db.refresh(first)
    assert first.is_active is False
    assert schemes.active_scheme(db, ids["year"]).id == second.id


def test_an_exam_takes_its_term_from_the_component_it_cites(db, ids):
    """Two places naming the term is two places to disagree, and the report
    card groups by term."""
    scheme = schemes.create(
        db, ids["school"], ids["year"], name="T2 only",
        rows=[("CT", "Class Test", "Term 2", Decimal(20))],
    )
    component = schemes.components(db, scheme.id)[0]
    exam = Exam(
        school_id=ids["school"], name="Mislabelled", term="Term 1",
        start_date="2026-09-01", end_date="2026-09-02",
    )
    db.add(exam)
    db.flush()
    schemes.attach_component(db, exam, component.id)
    assert exam.term == "Term 2"


def test_an_exam_cannot_cite_another_schools_component(db, ids):
    from app.models import School

    rival = School(code="RIVAL3", name="Rival Three")
    db.add(rival)
    db.flush()
    theirs = schemes.create(
        db, rival.id, ids["year"], name="Theirs", rows=SIMPLE
    )
    component = schemes.components(db, theirs.id)[0]
    exam = Exam(
        school_id=ids["school"], name="Ours", term="Term 1",
        start_date="2026-09-01", end_date="2026-09-02",
    )
    db.add(exam)
    db.flush()
    with pytest.raises(Exception) as e:
        schemes.attach_component(db, exam, component.id)
    assert e.value.status_code == 404


def test_an_exam_with_no_component_is_allowed(db, ids, client, admin):
    """An ordinary class test: marked, readable, and not printed on the card."""
    r = client.post(
        "/admin/exams",
        headers=admin,
        json={
            "name": "Surprise Test",
            "term": "Term 1",
            "start_date": "2026-09-01",
            "end_date": "2026-09-01",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["scheme_component_id"] is None


def test_the_api_creates_a_default_cbse_scheme_and_reports_its_terms(client, admin):
    r = client.post(
        "/admin/assessment-schemes",
        headers=admin,
        json={"name": "CBSE fresh"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert [t["term"] for t in body["terms"]] == ["Term 1", "Term 2"]
    assert [Decimal(t["total"]) for t in body["terms"]] == [Decimal(100), Decimal(100)]
    assert body["is_active"] is False, "a new scheme does not take force by itself"


def test_a_scheme_belonging_to_another_school_is_not_found(client, admin, db, ids):
    from app.models import School

    rival = School(code="RIVAL4", name="Rival Four")
    db.add(rival)
    db.flush()
    theirs = schemes.create(db, rival.id, ids["year"], name="Theirs", rows=SIMPLE)
    db.flush()
    r = client.post(f"/admin/assessment-schemes/{theirs.id}/activate", headers=admin)
    assert r.status_code == 404
