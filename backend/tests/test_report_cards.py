"""Report cards: the CBSE shape, the freeze, and withholding for dues.

Half of Checkpoint 4 is "a CBSE report card publishes and stays frozen", so the
test that carries the most weight is the one that publishes a card, then moves
every input underneath it — the mark, the grade band — and finds the issued
document unchanged.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Enrolment, ExamSchedule, Exam, Mark
from app.services import grading, report_cards, schemes
from app.services import school_settings


@pytest.fixture()
def enrolment(db, ids):
    return db.scalar(
        select(Enrolment).where(Enrolment.student_id == ids["student_1"])
    )


def term1_papers(db, enrolment):
    scheme = schemes.active_scheme(db, enrolment.academic_year_id)
    return report_cards._papers_of_term(
        db, scheme.id, "Term 1", enrolment.class_section_id
    )


def lock_all(db, enrolment):
    from datetime import UTC, datetime

    for p in term1_papers(db, enrolment):
        p.marks_locked_at = datetime.now(UTC)
    db.flush()


def clear_dues(db, enrolment):
    """Void every invoice so the ledger reads zero, without going through the
    payment machinery these tests are not about. `voided` is one of the two
    statuses `fees.DEAD` excludes from the outstanding sum."""
    from app.models import FeeInvoice, InvoiceStatus

    for inv in db.scalars(
        select(FeeInvoice).where(FeeInvoice.enrolment_id == enrolment.id)
    ):
        inv.status = InvoiceStatus.voided
    db.flush()
    assert report_cards.outstanding_for(db, enrolment) == 0


# --- the shape -------------------------------------------------------------


def test_the_card_has_the_cbse_columns_and_totals_a_hundred(db, enrolment):
    card = report_cards.preview(db, enrolment, "Term 1")
    assert card["rows"], "the demo school has a marked Term 1"
    row = card["rows"][0]
    assert [c["code"] for c in row["components"]] == ["PT", "NB", "SE", "TERM"]
    assert Decimal(row["max_marks"]) == Decimal(100)
    # Six subjects at 100 each.
    assert Decimal(card["total_max"]) == Decimal(600)
    assert card["overall_grade"] is not None
    assert card["published"] is False


def test_the_card_names_the_scale_version_it_was_computed_against(db, enrolment):
    card = report_cards.preview(db, enrolment, "Term 1")
    assert card["grading_scale"] == "CBSE v1"


def test_an_ordinary_class_test_never_reaches_the_card(db, enrolment, ids):
    """An exam citing no scheme component is marked and readable and simply
    does not print."""
    before = len(report_cards.preview(db, enrolment, "Term 1")["rows"])
    exam = Exam(
        school_id=ids["school"], name="Surprise", term="Term 1",
        start_date="2026-09-01", end_date="2026-09-01",
    )
    db.add(exam)
    db.flush()
    db.add(
        ExamSchedule(
            school_id=ids["school"], exam_id=exam.id,
            class_section_id=enrolment.class_section_id,
            subject_id=ids["maths"], exam_date="2026-09-01",
            max_marks=Decimal(50),
        )
    )
    db.flush()
    after = report_cards.preview(db, enrolment, "Term 1")
    assert len(after["rows"]) == before
    assert Decimal(after["total_max"]) == Decimal(600)


# --- the gates -------------------------------------------------------------


def test_publication_is_refused_while_a_paper_is_still_open(db, admin_user, enrolment):
    with pytest.raises(Exception) as e:
        report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert e.value.status_code == 409
    assert "open for marks entry" in str(e.value.detail)


def test_a_card_is_withheld_while_the_family_owes_money(db, admin_user, enrolment):
    lock_all(db, enrolment)
    assert report_cards.outstanding_for(db, enrolment) > 0, "the demo child owes"
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert row.result_status == report_cards.WITHHELD
    assert "Unpaid fees" in row.payload["withheld_reason"]


def test_withholding_is_a_policy_switch_not_a_constant(db, admin_user, enrolment, ids):
    """§5.4.9 is explicit that this is configurable. A school that issues the
    card regardless turns it off."""
    school_settings.set_many(
        db, admin_user, {"exams.withhold_results_for_dues": False}
    )
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert row.result_status == report_cards.PASS
    assert "withheld_reason" not in row.payload


def test_a_cleared_family_gets_an_unwithheld_card(db, admin_user, enrolment):
    lock_all(db, enrolment)
    clear_dues(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert row.result_status == report_cards.PASS


def test_a_withholding_cannot_be_released_while_the_money_is_still_owed(
    db, admin_user, enrolment
):
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert row.result_status == report_cards.WITHHELD
    with pytest.raises(Exception) as e:
        report_cards.release_withheld(db, admin_user, row, "parent asked nicely")
    assert e.value.status_code == 409
    assert "still owes" in str(e.value.detail)


def test_releasing_a_withholding_moves_the_status_and_not_the_marks(
    db, admin_user, enrolment
):
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    marks_before = row.payload["rows"]

    clear_dues(db, enrolment)
    released = report_cards.release_withheld(
        db, admin_user, row, "Dues cleared at the counter"
    )
    assert released.result_status == report_cards.PASS
    assert released.payload["rows"] == marks_before, "the marks were frozen"


def test_a_term_cannot_be_published_twice(db, admin_user, enrolment):
    lock_all(db, enrolment)
    first = report_cards.publish(db, admin_user, enrolment, "Term 1")
    with pytest.raises(Exception) as e:
        report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert e.value.status_code == 409
    assert first.document_no in str(e.value.detail)


def test_the_document_number_comes_from_the_gapless_sequence(db, admin_user, enrolment):
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert row.document_no.startswith("RC")
    assert row.document_no[2:].isdigit() and len(row.document_no[2:]) == 6


# --- the freeze, which is the point ----------------------------------------


def test_a_published_card_does_not_move_when_a_mark_is_corrected(
    db, admin_user, enrolment
):
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    issued_before = report_cards.issued(db, row)

    paper = term1_papers(db, enrolment)[0]
    mark = db.scalar(
        select(Mark).where(
            Mark.exam_schedule_id == paper.id,
            Mark.student_id == enrolment.student_id,
        )
    )
    mark.marks_obtained = Decimal(0)
    db.flush()

    assert report_cards.issued(db, row) == issued_before
    live = report_cards.preview(db, enrolment, "Term 1")
    assert live["total_obtained"] != issued_before["total_obtained"], (
        "the live screen should have moved; only the document is frozen"
    )


def test_a_published_card_does_not_re_grade_when_a_band_is_edited(
    db, admin_user, enrolment, ids
):
    """§0.8's actual requirement. The scale is frozen at publication, so the
    revision has to become a new version — and the issued card still cites the
    old one."""
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    grade_before = report_cards.issued(db, row)["overall_grade"]
    scale_before = report_cards.issued(db, row)["grading_scale"]

    old_scale = db.get(type(grading.active_scale(db, ids["school"])), row.grading_scale_id)
    assert old_scale.frozen_at is not None, "publication freezes the scale it cited"

    # Editing the frozen scale is refused; the way forward is a new version.
    with pytest.raises(Exception) as e:
        grading.set_bands(db, old_scale, [(Decimal(0), "P", None)])
    assert e.value.status_code == 409

    grading.create(
        db, ids["school"], name="CBSE",
        bands=[(Decimal(99), "A1", None), (Decimal(0), "E", None)],
        activate=True,
    )
    after = report_cards.issued(db, row)
    assert after["overall_grade"] == grade_before
    assert after["grading_scale"] == scale_before

    live = report_cards.preview(db, enrolment, "Term 1")
    assert live["grading_scale"] == "CBSE v2", "the live screen uses the new scale"


def test_the_issued_card_reads_back_identically_every_time(db, admin_user, enrolment):
    lock_all(db, enrolment)
    row = report_cards.publish(db, admin_user, enrolment, "Term 1")
    assert report_cards.issued(db, row) == report_cards.issued(db, row)


# --- the API ---------------------------------------------------------------


def test_readiness_lists_what_stands_in_the_way(client, admin, db, enrolment):
    r = client.get(
        "/admin/report-cards/readiness",
        headers=admin,
        params={"enrolment_id": enrolment.id, "term": "Term 1"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Six subjects times the four CBSE components of a term.
    assert len(body["unlocked_papers"]) == 24, "nothing is locked yet"
    assert Decimal(body["outstanding"]) > 0
    assert body["already_published"] is False


def test_the_api_publishes_and_then_serves_the_frozen_document(
    client, admin, db, enrolment
):
    lock_all(db, enrolment)
    r = client.post(
        "/admin/report-cards/publish",
        headers=admin,
        params={"enrolment_id": enrolment.id, "term": "Term 1"},
    )
    assert r.status_code == 201, r.text
    card = r.json()
    assert card["published"] is True
    assert card["document_no"].startswith("RC")

    listed = client.get(
        "/admin/report-cards", headers=admin, params={"term": "Term 1"}
    ).json()
    assert card["document_no"] in [x["document_no"] for x in listed]

    pub_id = next(x["id"] for x in listed if x["document_no"] == card["document_no"])
    again = client.get(f"/admin/report-cards/{pub_id}", headers=admin).json()
    assert again["rows"] == card["rows"]


def test_a_card_of_another_school_is_not_found(client, admin, db):
    r = client.get("/admin/report-cards/999999", headers=admin)
    assert r.status_code == 404
