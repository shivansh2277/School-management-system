from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.services.common import enrolment_sections, require_current_enrolment
from app.models import (
    ClassSection,
    Notice,
    NoticeAudience,
    User,
    UserRole,
)
from app.schemas.common import NoticeCreate, NoticeOut
from app.services import scoping

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
        )
        for n in items
    ]


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


def delete(db: Session, notice_id: int) -> None:
    notice = db.get(Notice, notice_id)
    if notice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notice not found")
    db.delete(notice)
    db.commit()
