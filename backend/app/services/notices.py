import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.services.common import enrolment_sections, require_current_enrolment
from app.models import (
    AuditAction,
    ClassSection,
    Notice,
    NoticeAudience,
    User,
    UserRole,
)
from app.schemas.common import NoticeCreate, NoticeOut
from app.services import audit, scoping

log = logging.getLogger("notices")

SCHOOL_WIDE = {
    NoticeAudience.all,
    NoticeAudience.students,
    NoticeAudience.parents,
    NoticeAudience.teachers,
}


def to_out(db: Session, items: list[Notice]) -> list[NoticeOut]:
    labels = {c.id: c.label for c in db.scalars(select(ClassSection))}
    authors = {
        u.id: u.full_name
        for u in db.scalars(select(User).where(User.id.in_([n.published_by for n in items] or [0])))
    }
    return [
        NoticeOut(
            id=n.id,
            title=n.title,
            body=n.body,
            audience=n.audience,
            class_section_id=n.class_section_id,
            class_label=labels.get(n.class_section_id) if n.class_section_id else None,
            published_by=authors.get(n.published_by, ""),
            published_at=n.published_at,
            message_id=n.message_id,
        )
        for n in items
    ]


# Which comms audience each notice audience becomes. `students` is absent on
# purpose: a student's contact of record is their guardian's, and mailing a
# child directly is a decision about children and email that nobody has taken.
# Publishing to students still works — it simply does not send, and the caller
# is told so rather than left to assume it did.
NOTIFIABLE = {
    NoticeAudience.all: {"kind": "all_guardians"},
    NoticeAudience.parents: {"kind": "all_guardians"},
    NoticeAudience.teachers: {"kind": "staff"},
}


def _notify(db: Session, user: User, notice: Notice) -> int | None:
    """Send the notice as a message, reusing the outbox rather than growing a
    second delivery mechanism beside it (HANDOFF §9.1).

    Returns the message id, or `None` where this audience has no email route.
    A failure to send does not unpublish the notice: the board is the record,
    the message is a courtesy on top of it, and a mail server being down is not
    a reason for the circular to vanish off the wall.
    """
    from app.services import comms

    if notice.audience is NoticeAudience.class_:
        audience = {"kind": "section", "class_section_id": notice.class_section_id}
    else:
        audience = NOTIFIABLE.get(notice.audience)
    if audience is None:
        return None

    try:
        message = comms.notify(
            db,
            notice.school_id,
            template_code="general.notice",
            audience=audience,
            actor=user,
            extra={"notice_title": notice.title, "notice_body": notice.body},
        )
    except Exception:  # noqa: BLE001 - the board is the record
        log.exception("notice %s published but not sent", notice.id)
        return None
    return message.id if message else None


def publish(db: Session, user: User, body: NoticeCreate) -> NoticeOut:
    if user.role == UserRole.teacher:
        # A teacher may publish only audience=class, and only for a section they
        # teach. School-wide audiences are admin-only (BLUEPRINT §8 Notices).
        if body.audience != NoticeAudience.class_:
            raise scoping.forbidden("Teachers may only publish notices to a class they teach")
        if body.class_section_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "class_section_id is required")
        scoping.assert_teaches_section(db, user, body.class_section_id)
    elif user.role != UserRole.admin:
        raise scoping.forbidden("Only admins and teachers may publish notices")

    if body.audience == NoticeAudience.class_ and body.class_section_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "class_section_id is required for a class notice"
        )
    notice = Notice(
        school_id=user.school_id,
        title=body.title,
        body=body.body,
        audience=body.audience,
        class_section_id=body.class_section_id if body.audience == NoticeAudience.class_ else None,
        published_by=user.id,
        published_at=datetime.now(UTC),
    )
    db.add(notice)
    db.flush()
    if body.notify:
        notice.message_id = _notify(db, user, notice)
    db.commit()
    return to_out(db, [notice])[0]


def visible_to(db: Session, user: User) -> list[NoticeOut]:
    """Audience filtering on read (BLUEPRINT §8 Notices)."""
    if user.role == UserRole.admin:
        clauses = [Notice.id.is_not(None)]
    elif user.role == UserRole.teacher:
        clauses = [
            Notice.audience.in_([NoticeAudience.all, NoticeAudience.teachers]),
            Notice.class_section_id.in_(scoping.class_section_ids_for(db, user)),
        ]
    elif user.role == UserRole.student:
        student = scoping.student_for(db, user)
        enrolment = require_current_enrolment(db, student.id)
        clauses = [
            Notice.audience.in_([NoticeAudience.all, NoticeAudience.students]),
            Notice.class_section_id == enrolment.class_section_id,
        ]
    else:
        # Enrolment and Student were never joined here, so this read every
        # section in the school and showed a parent every class's notices.
        child_sections = list(
            enrolment_sections(db, scoping.child_ids_for(db, user)).values()
        )
        clauses = [
            Notice.audience.in_([NoticeAudience.all, NoticeAudience.parents]),
            Notice.class_section_id.in_(child_sections),
        ]
    items = list(
        db.scalars(select(Notice).where(or_(*clauses)).order_by(Notice.published_at.desc()))
    )
    return to_out(db, items)


def delete(db: Session, notice_id: int, user: User, reason: str) -> None:
    """`school_id` is taken from the actor, not passed, so a caller cannot forget it.

    Deleting by a bare id let one school delete another school's notices; the
    same fix `section_labels`, `subject_names` and `grade_for` already carry.

    The reason is required because this is the only destructive path in the
    product that used to commit silently: every other void, status change and
    delete is audited with the reason the person typed, and a notice removed
    off the board with no record of who or why is exactly the event somebody
    asks about later. `audit.record` refuses `AuditAction.delete` without one,
    so the requirement is enforced there rather than restated here.
    """
    notice = db.get(Notice, notice_id)
    if notice is None or notice.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notice not found")
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="notice",
        entity_id=notice.id,
        action=AuditAction.delete,
        # Snapshotted before the row goes: the audit entry is the only place
        # the title survives, and "deleted notice 41" answers nothing.
        before=audit.snapshot(notice, ["title", "audience", "published_at"]),
        reason=reason,
    )
    db.delete(notice)
    db.commit()
