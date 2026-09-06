"""Writing the audit log, and allocating gapless document numbers."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditAction, AuditLog, NumberSequence, User

# Actions where "why" matters more than "what", and which therefore refuse to
# commit without a reason. Deliberately a short, explicit list rather than a
# rule: auditing everything produces noise nobody reads (ERP_BLUEPRINT §3.6).
REASON_REQUIRED = {
    AuditAction.void,
    AuditAction.status_change,
    AuditAction.delete,
}


def _diff(before: dict | None, after: dict | None) -> tuple[dict | None, dict | None]:
    """Keep only the fields that actually changed."""
    if before is None or after is None:
        return before, after
    changed = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
    if not changed:
        return None, None
    return (
        {k: before.get(k) for k in changed},
        {k: after.get(k) for k in changed},
    )


def record(
    db: Session,
    *,
    actor: User | None,
    school_id: int,
    entity_type: str,
    action: AuditAction,
    entity_id: int | None = None,
    before: dict | None = None,
    after: dict | None = None,
    reason: str | None = None,
    academic_year_id: int | None = None,
    ip: str | None = None,
) -> AuditLog:
    if action in REASON_REQUIRED and not (reason and reason.strip()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"A reason is required to {action.value} a {entity_type}",
        )

    before, after = _diff(before, after)
    row = AuditLog(
        school_id=school_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=actor.id if actor else None,
        # Denormalised so the log stays readable after the account is renamed
        # or removed.
        actor_label=actor.full_name if actor else "system",
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before=before,
        after=after,
        reason=reason,
        academic_year_id=academic_year_id,
        ip=ip,
    )
    db.add(row)
    return row


def snapshot(obj, fields: list[str]) -> dict:
    """A plain-JSON view of the fields worth auditing on a model instance."""
    out = {}
    for f in fields:
        v = getattr(obj, f, None)
        out[f] = str(v) if hasattr(v, "isoformat") or hasattr(v, "value") else v
    return out


def next_number(
    db: Session,
    school_id: int,
    kind: str,
    year: int,
    *,
    prefix: str | None = None,
    width: int = 6,
) -> str:
    """Allocate the next number in a gapless per-school, per-year sequence.

    The row is locked FOR UPDATE so two concurrent callers serialise instead of
    racing to the same value — the failure v0's `max(seq) + 1` had. SQLite has
    no row locking, but it serialises writes at the database level, so the
    behaviour holds there too.
    """
    q = select(NumberSequence).where(
        NumberSequence.school_id == school_id,
        NumberSequence.kind == kind,
        NumberSequence.year == year,
    )
    if db.bind is not None and db.bind.dialect.name != "sqlite":
        q = q.with_for_update()

    seq = db.scalar(q)
    if seq is None:
        seq = NumberSequence(
            school_id=school_id,
            kind=kind,
            year=year,
            prefix=prefix,
            width=width,
            next_value=1,
        )
        db.add(seq)
        db.flush()

    value = seq.next_value
    seq.next_value = value + 1
    db.flush()

    body = str(value).zfill(seq.width)
    return f"{seq.prefix}{body}" if seq.prefix else body


def admission_number(db: Session, school_id: int, joining_year: int) -> str:
    """`YYYY` + 6-digit sequence, e.g. 2026000147 (ERP_BLUEPRINT §0.21).

    Ten digits rather than fourteen because office staff read this number aloud
    and type it dozens of times a day. Permanent and immutable for life: a
    student who leaves and rejoins keeps the original.
    """
    return next_number(
        db,
        school_id,
        kind="admission",
        year=joining_year,
        prefix=str(joining_year),
        width=6,
    )
