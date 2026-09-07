"""The fee catalogue: what a child is charged, and what is taken off it.

Split from `services/fees.py` deliberately. This module decides *what is owed*;
that one bills and collects it. The invoice generator asks two questions of
this file — which plan, and which concessions — and nothing else.
"""

from datetime import UTC, date as Date, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    ConcessionStatus,
    ConcessionType,
    Enrolment,
    EnrolmentStatus,
    FeeConcession,
    FeePlan,
    StudentFeePlan,
    Student,
    StudentGuardian,
    User,
)
from app.services import audit, school_settings

PAISE = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Round to paise, half-up — the way a counter clerk rounds.

    Banker's rounding is the Python default and would make a 10% concession on
    ₹1,250.50 differ from the printed fee card by a paisa. Small, and exactly
    the kind of difference a parent brings to the office.
    """
    return Decimal(value).quantize(PAISE, rounding=ROUND_HALF_UP)


def plan_for(db: Session, enrolment: Enrolment) -> FeePlan | None:
    """The plan that bills this enrolment: the individual override if one
    exists, otherwise the year's default plan for that class."""
    override = db.scalar(
        select(FeePlan)
        .join(StudentFeePlan, StudentFeePlan.fee_plan_id == FeePlan.id)
        .where(StudentFeePlan.enrolment_id == enrolment.id)
    )
    if override is not None:
        return override if override.is_active else None
    return db.scalar(
        select(FeePlan).where(
            FeePlan.academic_year_id == enrolment.academic_year_id,
            FeePlan.class_name == enrolment.class_section.class_name,
            FeePlan.is_active.is_(True),
        )
    )


def concessions_for(
    db: Session, enrolment_ids: list[int], on: Date
) -> dict[int, list[FeeConcession]]:
    """Approved concessions in force on a date, per enrolment.

    Only `approved` counts. A requested concession that quietly reduced an
    invoice would make the approval step decorative (§5.5.9).
    """
    if not enrolment_ids:
        return {}
    rows = db.scalars(
        select(FeeConcession).where(
            FeeConcession.enrolment_id.in_(enrolment_ids),
            FeeConcession.status == ConcessionStatus.approved,
        )
    )
    out: dict[int, list[FeeConcession]] = {}
    for c in rows:
        if c.valid_from and c.valid_from > on:
            continue
        if c.valid_to and c.valid_to < on:
            continue
        out.setdefault(c.enrolment_id, []).append(c)
    return out


def discount_on(line_amount: Decimal, head_id: int, concessions: list[FeeConcession]) -> Decimal:
    """What comes off one invoice line. Never more than the line itself — a
    concession is a discount, not a credit note."""
    total = Decimal(0)
    for c in concessions:
        if c.fee_head_id is not None and c.fee_head_id != head_id:
            continue
        total += (
            money(line_amount * c.percent / 100) if c.percent is not None else Decimal(c.amount)
        )
    return min(money(total), line_amount)


def decide(
    db: Session, concession: FeeConcession, actor: User, approve: bool, reason: str | None = None
) -> FeeConcession:
    if concession.status is not ConcessionStatus.requested:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This concession is already {concession.status.value}",
        )
    concession.status = ConcessionStatus.approved if approve else ConcessionStatus.rejected
    concession.approved_by = actor.id
    concession.decided_at = datetime.now(UTC)
    audit.record(
        db,
        actor=actor,
        school_id=concession.school_id,
        entity_type="fee_concession",
        entity_id=concession.id,
        action=AuditAction.status_change,
        after={"status": concession.status.value},
        # status_change refuses to commit without one, which is the point:
        # "who approved this waiver, and why" is the audit question.
        reason=reason or concession.reason,
    )
    db.commit()
    return concession


def apply_sibling_concessions(db: Session, school_id: int, actor: User | None = None) -> dict:
    """§0.6: 10% off for siblings sharing a primary guardian.

    Policy, not a request, so these are written already approved — but as
    ordinary concession rows, so one mechanism reduces every invoice and the
    concession register shows them like any other.

    The eldest by admission number pays in full and the younger children get
    the discount, which is both what schools do and deterministic: re-running
    this must not move the discount between children.
    """
    percent = Decimal(school_settings.get(db, school_id, "fees.sibling_concession_percent"))
    families: dict[int, list[tuple[str, Enrolment]]] = {}
    rows = db.execute(
        select(StudentGuardian.guardian_id, Student.admission_no, Enrolment)
        .join(Student, Student.id == StudentGuardian.student_id)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .where(
            StudentGuardian.school_id == school_id,
            StudentGuardian.is_primary.is_(True),
            Enrolment.status == EnrolmentStatus.active,
        )
    ).all()
    for guardian_id, admission_no, enrolment in rows:
        families.setdefault(guardian_id, []).append((admission_no, enrolment))

    existing = set(
        db.scalars(
            select(FeeConcession.enrolment_id).where(
                FeeConcession.school_id == school_id,
                FeeConcession.type == ConcessionType.sibling,
                FeeConcession.status == ConcessionStatus.approved,
            )
        )
    )
    created = 0
    for children in families.values():
        if len(children) < 2:
            continue
        for _, enrolment in sorted(children, key=lambda c: c[0])[1:]:
            if enrolment.id in existing:
                continue
            db.add(
                FeeConcession(
                    school_id=school_id,
                    enrolment_id=enrolment.id,
                    type=ConcessionType.sibling,
                    percent=percent,
                    reason=f"Sibling concession, {percent}% (school policy)",
                    status=ConcessionStatus.approved,
                    approved_by=actor.id if actor else None,
                    decided_at=datetime.now(UTC),
                )
            )
            created += 1
    db.commit()
    return {"granted": created, "percent": int(percent)}
