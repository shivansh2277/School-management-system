"""Assessment schemes: what a subject is marked out of, as data (§5.4.3).

A CBSE subject carries four marks in a term — periodic test, notebook, subject
enrichment and the term examination — and the report card prints all four and
totals them. v0 could hold exactly one number per subject per exam, so it could
not produce that card at all.

The scheme is configuration, not code (§0.5, §0.15). A school running three
terms, or marking the notebook out of ten, changes rows on a screen. Nothing
here hardcodes 10/5/5/80; that set is a seed default and nothing more.
"""

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AssessmentScheme, Exam, SchemeComponent

# The default a Lucknow CBSE school starts from (§0.5). Editable in full: this
# is what the setup screen is pre-filled with, not what the code assumes.
CBSE_DEFAULT: list[tuple[str, str, str, Decimal]] = [
    ("PT", "Periodic Test", "Term 1", Decimal(10)),
    ("NB", "Notebook", "Term 1", Decimal(5)),
    ("SE", "Subject Enrichment", "Term 1", Decimal(5)),
    ("TERM", "Term Examination", "Term 1", Decimal(80)),
    ("PT", "Periodic Test", "Term 2", Decimal(10)),
    ("NB", "Notebook", "Term 2", Decimal(5)),
    ("SE", "Subject Enrichment", "Term 2", Decimal(5)),
    ("TERM", "Term Examination", "Term 2", Decimal(80)),
]


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def active_scheme(db: Session, academic_year_id: int) -> AssessmentScheme | None:
    return db.scalar(
        select(AssessmentScheme).where(
            AssessmentScheme.academic_year_id == academic_year_id,
            AssessmentScheme.is_active.is_(True),
        )
    )


def components(
    db: Session, scheme_id: int, term: str | None = None
) -> list[SchemeComponent]:
    """A scheme's components in print order, optionally for one term."""
    q = select(SchemeComponent).where(SchemeComponent.scheme_id == scheme_id)
    if term is not None:
        q = q.where(SchemeComponent.term == term)
    return list(db.scalars(q.order_by(SchemeComponent.sequence)))


def terms(db: Session, scheme_id: int) -> list[str]:
    """The scheme's terms, in the order their components were sequenced."""
    rows = db.execute(
        select(SchemeComponent.term, func.min(SchemeComponent.sequence))
        .where(SchemeComponent.scheme_id == scheme_id)
        .group_by(SchemeComponent.term)
        .order_by(func.min(SchemeComponent.sequence), SchemeComponent.term)
    ).all()
    return [term for term, _ in rows]


def term_total(db: Session, scheme_id: int, term: str) -> Decimal:
    """What a subject is out of for one term — the report card's denominator."""
    total = db.scalar(
        select(func.sum(SchemeComponent.max_marks)).where(
            SchemeComponent.scheme_id == scheme_id, SchemeComponent.term == term
        )
    )
    return Decimal(total or 0)


def create(
    db: Session,
    school_id: int,
    academic_year_id: int,
    *,
    name: str,
    rows: list[tuple[str, str, str, Decimal]],
    activate: bool = False,
) -> AssessmentScheme:
    """A scheme and its components. `rows` are (code, name, term, max_marks)."""
    if not rows:
        raise _bad("An assessment scheme needs at least one component")

    scheme = AssessmentScheme(
        school_id=school_id,
        academic_year_id=academic_year_id,
        name=name,
        is_active=False,
    )
    db.add(scheme)
    db.flush()
    set_components(db, scheme, rows)
    if activate:
        activate_scheme(db, scheme)
    db.flush()
    return scheme


def set_components(
    db: Session, scheme: AssessmentScheme, rows: list[tuple[str, str, str, Decimal]]
) -> list[SchemeComponent]:
    """Replace a scheme's components wholesale.

    Refused once any exam cites one of them: the marks already entered are out
    of the old number, and silently restating what they were out of is how a
    child's 8/10 becomes 8/5.
    """
    cited = db.scalar(
        select(func.count(Exam.id))
        .join(SchemeComponent, SchemeComponent.id == Exam.scheme_component_id)
        .where(SchemeComponent.scheme_id == scheme.id)
    )
    if cited:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{cited} exam(s) are already marked against this scheme's "
            "components. Create a new scheme rather than restating what marks "
            "already entered were out of.",
        )
    if not rows:
        raise _bad("An assessment scheme needs at least one component")

    seen = {(term, code) for code, _, term, _ in rows}
    if len(seen) != len(rows):
        raise _bad("A term cannot carry the same component code twice")
    if any(marks <= 0 for _, _, _, marks in rows):
        raise _bad("A component must be marked out of more than zero")

    for old in db.scalars(
        select(SchemeComponent).where(SchemeComponent.scheme_id == scheme.id)
    ):
        db.delete(old)
    db.flush()

    made = [
        SchemeComponent(
            school_id=scheme.school_id,
            scheme_id=scheme.id,
            code=code,
            name=name,
            term=term,
            max_marks=Decimal(str(max_marks)),
            sequence=i,
        )
        for i, (code, name, term, max_marks) in enumerate(rows)
    ]
    db.add_all(made)
    db.flush()
    return made


def activate_scheme(db: Session, scheme: AssessmentScheme) -> AssessmentScheme:
    """Put a scheme in force for its year, standing the previous one down."""
    current = active_scheme(db, scheme.academic_year_id)
    if current is not None and current.id != scheme.id:
        current.is_active = False
        db.flush()
    scheme.is_active = True
    db.flush()
    return scheme


def attach_component(db: Session, exam: Exam, component_id: int | None) -> Exam:
    """Point an exam at the report-card column it fills, or at none.

    The exam's `term` is taken from the component rather than trusted from the
    caller: two places naming the term is two places to disagree, and the
    report card groups by term.
    """
    if component_id is None:
        exam.scheme_component_id = None
        return exam

    component = db.get(SchemeComponent, component_id)
    if component is None or component.school_id != exam.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheme component not found")
    exam.scheme_component_id = component.id
    exam.term = component.term
    db.flush()
    return exam
