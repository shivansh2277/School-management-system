"""Building a term's report card, and freezing it at publication.

Two documents come out of this module and they are not the same thing.

**The preview** is computed live, from `marks` and the school's current grading
scale. It moves when a mark is corrected or a band is edited, which is right —
it is a screen, not a document.

**The published card is frozen** (§0.8). The whole rendered card is stored as
it was issued and read straight back; the grading scale and assessment scheme
it cited are recorded by id, and the scale is marked frozen so its bands can no
longer be edited. Reopening a card months later shows exactly what the parent
was handed, even if every band has moved since. This supersedes BLUEPRINT §7.5
for published documents only.

Two gates stand before publication, and each is a §5.4.9 or §0.6b rule rather
than a preference: every paper of the term must be locked, and a family with
unpaid dues has its result withheld — a policy switch, not a constant.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    Enrolment,
    Exam,
    ExamSchedule,
    GradingScale,
    Mark,
    ReportCardPublication,
    SchemeComponent,
    User,
)
from app.services import attendance as attendance_svc
from app.services import audit, fees, grading, schemes
from app.services.common import subject_names
from app.services.school_settings import get as get_setting

# What a result reads as. `withheld` is a real requirement, not an error state:
# §0.6b withholds the card and the transfer certificate until dues clear.
PASS = "pass"
FAIL = "fail"
WITHHELD = "withheld"


def _papers_of_term(db: Session, scheme_id: int, term: str, class_section_id: int):
    """Every paper this section sits for one term of the scheme.

    Joined through the component rather than through `exams.term`, so an exam
    that cites no component — an ordinary class test — never lands on a report
    card.
    """
    return list(
        db.scalars(
            select(ExamSchedule)
            .join(Exam, Exam.id == ExamSchedule.exam_id)
            .join(SchemeComponent, SchemeComponent.id == Exam.scheme_component_id)
            .where(
                SchemeComponent.scheme_id == scheme_id,
                SchemeComponent.term == term,
                ExamSchedule.class_section_id == class_section_id,
            )
            .order_by(SchemeComponent.sequence)
        )
    )


def build(db: Session, enrolment: Enrolment, term: str, *, scale: GradingScale) -> dict:
    """Render a term's card for one child against one grading scale.

    The scale is passed in rather than looked up so that publication and replay
    run the identical code: a frozen card is re-rendered against the version it
    cited, and a preview against whatever is in force today.
    """
    scheme = schemes.active_scheme(db, enrolment.academic_year_id)
    if scheme is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This year has no assessment scheme in force, so there is nothing "
            "to mark a report card against",
        )
    papers = _papers_of_term(db, scheme.id, term, enrolment.class_section_id)
    if not papers:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"No papers are scheduled for {term}"
        )

    marks = {
        m.exam_schedule_id: m
        for m in db.scalars(
            select(Mark).where(
                Mark.student_id == enrolment.student_id,
                Mark.exam_schedule_id.in_([p.id for p in papers]),
            )
        )
    }
    names = subject_names(db, enrolment.school_id)
    components = {
        c.id: c for c in schemes.components(db, scheme.id, term)
    }
    exam_component = {
        e.id: e.scheme_component_id
        for e in db.scalars(
            select(Exam).where(Exam.id.in_([p.exam_id for p in papers]))
        )
    }

    # subject -> its component columns, in the scheme's print order.
    subjects: dict[int, dict] = {}
    for paper in papers:
        component = components[exam_component[paper.exam_id]]
        mark = marks.get(paper.id)
        row = subjects.setdefault(
            paper.subject_id,
            {
                "subject": names.get(paper.subject_id, ""),
                "components": [],
                "obtained": Decimal(0),
                "max": Decimal(0),
            },
        )
        obtained = mark.marks_obtained if mark else None
        row["components"].append(
            {
                "code": component.code,
                "name": component.name,
                "max_marks": str(component.max_marks),
                "marks_obtained": str(obtained) if obtained is not None else None,
                "is_absent": bool(mark and mark.is_absent),
                "is_exempted": bool(mark and mark.is_exempted),
            }
        )
        if obtained is not None:
            # A component with no mark is excluded from both halves rather than
            # counted as zero — the same rule the exam card and the dashboard
            # already share (§5.10.9).
            row["obtained"] += obtained
            row["max"] += component.max_marks

    rows, total_obtained, total_max = [], Decimal(0), Decimal(0)
    for subject_id in sorted(subjects, key=lambda s: names.get(s, "")):
        row = subjects[subject_id]
        percent = (
            round(float(row["obtained"]) / float(row["max"]) * 100, 1)
            if row["max"]
            else None
        )
        total_obtained += row["obtained"]
        total_max += row["max"]
        rows.append(
            {
                "subject": row["subject"],
                "components": row["components"],
                "marks_obtained": str(row["obtained"]),
                "max_marks": str(row["max"]),
                "percent": percent,
                "grade": grading.grade_in(db, scale.id, percent),
            }
        )

    overall = (
        round(float(total_obtained) / float(total_max) * 100, 1) if total_max else None
    )
    summary = attendance_svc.student_percent(db, enrolment.student_id)
    return {
        "term": term,
        "student_id": enrolment.student_id,
        "student_name": enrolment.student.user.full_name,
        "admission_no": enrolment.student.admission_no,
        "roll_no": enrolment.roll_no,
        "class_label": enrolment.class_section.label,
        "scheme": scheme.name,
        "grading_scale": f"{scale.name} v{scale.version}",
        "attendance_percent": summary,
        "rows": rows,
        "total_obtained": str(total_obtained),
        "total_max": str(total_max),
        "overall_percent": overall,
        "overall_grade": grading.grade_in(db, scale.id, overall),
    }


def preview(db: Session, enrolment: Enrolment, term: str) -> dict:
    """The live card: recomputed every read, against today's scale."""
    scale = grading.active_scale(db, enrolment.school_id)
    if scale is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This school has no grading scale in force"
        )
    card = build(db, enrolment, term, scale=scale)
    card["published"] = False
    return card


def outstanding_for(db: Session, enrolment: Enrolment) -> Decimal:
    """What this enrolment owes, asked of the fee ledger rather than answered
    here. §0.6b needs one definition of "cleared", and it is the one the
    counter clerk collects against."""
    return Decimal(fees.ledger(db, enrolment.id)["outstanding"])


def unlocked_papers(db: Session, enrolment: Enrolment, term: str) -> list[ExamSchedule]:
    """§5.4.9: results cannot be published until every paper is locked."""
    scheme = schemes.active_scheme(db, enrolment.academic_year_id)
    if scheme is None:
        return []
    return [
        p
        for p in _papers_of_term(db, scheme.id, term, enrolment.class_section_id)
        if not p.is_locked
    ]


def published(db: Session, enrolment_id: int, term: str) -> ReportCardPublication | None:
    return db.scalar(
        select(ReportCardPublication).where(
            ReportCardPublication.enrolment_id == enrolment_id,
            ReportCardPublication.term == term,
        )
    )


def publish(
    db: Session, user: User, enrolment: Enrolment, term: str
) -> ReportCardPublication:
    """Freeze and issue one child's card for a term."""
    existing = published(db, enrolment.id, term)
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{term} has already been published for this student as "
            f"{existing.document_no}. A correction is a new document, not an "
            "edit to this one.",
        )

    unlocked = unlocked_papers(db, enrolment, term)
    if unlocked:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{len(unlocked)} paper(s) in {term} are still open for marks entry. "
            "Lock them before publishing.",
        )

    scale = grading.active_scale(db, enrolment.school_id)
    if scale is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This school has no grading scale in force"
        )
    scheme = schemes.active_scheme(db, enrolment.academic_year_id)
    card = build(db, enrolment, term, scale=scale)

    # §0.6b, and §5.4.9's "configurable policy, not hardcoded": a school that
    # does not withhold turns the switch off, and the card publishes as normal.
    status_value = PASS
    if get_setting(db, enrolment.school_id, "exams.withhold_results_for_dues"):
        owed = outstanding_for(db, enrolment)
        if owed > 0:
            status_value = WITHHELD
            card["withheld_reason"] = f"Unpaid fees of {owed}"

    card["result_status"] = status_value
    card["published"] = True

    row = ReportCardPublication(
        school_id=enrolment.school_id,
        enrolment_id=enrolment.id,
        term=term,
        scheme_id=scheme.id,
        grading_scale_id=scale.id,
        document_no=audit.next_number(
            db,
            enrolment.school_id,
            kind="report_card",
            year=enrolment.academic_year_id,
            prefix="RC",
        ),
        published_at=datetime.now(UTC),
        published_by=user.id,
        result_status=status_value,
        payload=card,
    )
    db.add(row)
    db.flush()
    card["document_no"] = row.document_no
    row.payload = dict(card)

    # From here the scale's bands are history rather than configuration.
    grading.freeze(db, scale)
    audit.record(
        db,
        actor=user,
        school_id=enrolment.school_id,
        entity_type="report_card",
        entity_id=row.id,
        action=AuditAction.publish,
        after={
            "document_no": row.document_no,
            "term": term,
            "result_status": status_value,
        },
        academic_year_id=enrolment.academic_year_id,
    )
    db.commit()
    return row


def issued(db: Session, publication: ReportCardPublication) -> dict:
    """The card exactly as it was issued. Never recomputed."""
    card = dict(publication.payload)
    card["document_no"] = publication.document_no
    card["published_at"] = publication.published_at
    card["result_status"] = publication.result_status
    return card


def release_withheld(
    db: Session, user: User, publication: ReportCardPublication, reason: str
) -> ReportCardPublication:
    """Lift a withholding once dues are cleared.

    The marks on the card do not move — they were frozen at publication and
    stay frozen. Only the result status changes, and it is audited with a
    reason like any other status change.
    """
    if publication.result_status != WITHHELD:
        return publication
    enrolment = db.get(Enrolment, publication.enrolment_id)
    owed = outstanding_for(db, enrolment)
    if owed > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This family still owes {owed}. §0.6b withholds the card until "
            "that is cleared.",
        )
    audit.record(
        db,
        actor=user,
        school_id=publication.school_id,
        entity_type="report_card",
        entity_id=publication.id,
        action=AuditAction.status_change,
        before={"result_status": publication.result_status},
        after={"result_status": PASS},
        reason=reason,
    )
    publication.result_status = PASS
    payload = dict(publication.payload)
    payload["result_status"] = PASS
    payload.pop("withheld_reason", None)
    publication.payload = payload
    db.commit()
    return publication
