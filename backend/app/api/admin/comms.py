"""The outbox: compose, preview, approve, send, and the delivery report (§5.9).

Thin, like the rest. Two things are worth noticing about which dependency each
route carries.

`comms.emergency.broadcast` is its own permission and its own endpoint, because
§5.9.3 asks for the emergency broadcast to be deliberately separate. It
overrides every opt-out and the quiet hours, so it should not be reachable by
setting `category=emergency` on the ordinary compose route — which is exactly
what would happen if it shared one.

The bulk-approval threshold is enforced in the service rather than here, so a
future job or mobile caller inherits it instead of reimplementing it.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    Channel,
    Message,
    MessageCategory,
    MessageStatus,
    MessageTemplate,
    User,
)
from app.services import comms as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/comms",
    tags=["admin"],
    dependencies=[Depends(module_enabled("communication"))],
)
reader = require_permission("comms.message.read", school_wide=True)
sender = require_permission("comms.message.send", school_wide=True)
approver = require_permission("comms.message.approve", school_wide=True)
broadcaster = require_permission("comms.emergency.broadcast", school_wide=True)
templater = require_permission("comms.template.manage", school_wide=True)


class AudienceIn(BaseModel):
    kind: str
    class_section_id: int | None = None
    student_id: int | None = None
    route_id: int | None = None
    employee_id: int | None = None
    application_id: int | None = None
    permission: str | None = None
    min_amount: float | None = None

    def spec(self) -> dict:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class ComposeIn(BaseModel):
    audience: AudienceIn
    category: MessageCategory = MessageCategory.general
    subject: str | None = Field(default=None, max_length=200)
    body: str | None = None
    template_code: str | None = None
    channel: Channel = Channel.email
    send_now: bool = True


class BroadcastIn(BaseModel):
    """An emergency broadcast says what it is, and is confirmed in words.

    §5.9.3 wants the confirmation on the screen. Requiring it in the payload
    means the API cannot be used to skip past the screen, which is the only
    way a confirmation is worth anything.
    """

    subject: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3)
    audience: AudienceIn = AudienceIn(kind="all_guardians")
    confirm: bool


class TemplateIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=80)
    category: MessageCategory
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    channel: Channel = Channel.email


class PreferenceIn(BaseModel):
    category: MessageCategory
    channel: Channel = Channel.email
    opted_out: bool = True


def _message(db: Session, user: User, message_id: int) -> Message:
    row = db.get(Message, message_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    return row


def _out(db: Session, m: Message) -> dict:
    return {
        "id": m.id,
        "category": m.category.value,
        "channel": m.channel.value,
        "subject": m.subject,
        "status": m.status.value,
        "audience": m.audience,
        "template_version": m.template_version,
        "scheduled_for": m.scheduled_for,
        "sent_at": m.sent_at,
        "approved_by": m.approved_by,
        "recipients": len(m.recipients),
        "needs_approval": svc.needs_approval(db, m) and m.approved_by is None,
    }


# --- composing and sending --------------------------------------------------


@router.post("/preview")
def preview(
    body: AudienceIn, user: User = Depends(sender), db: Session = Depends(get_db)
) -> dict:
    """Who this would reach, before anybody sends it (§5.9.9).

    Also the honest half: `unreachable` counts the families with no address on
    file. A circular that reaches two thirds of the school should say so at the
    moment it is still a draft.
    """
    svc.assert_may_address(db, user, body.spec())
    return svc.preview(db, user.school_id, body.spec())


@router.post("/messages", status_code=status.HTTP_201_CREATED)
def compose(
    body: ComposeIn, user: User = Depends(sender), db: Session = Depends(get_db)
) -> dict:
    if body.category is MessageCategory.emergency:
        # An emergency overrides opt-out and quiet hours, so it does not come
        # through the ordinary door with a different word in the payload.
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "An emergency broadcast goes through /admin/comms/broadcast",
        )
    message = svc.compose(
        db,
        user,
        category=body.category,
        audience=body.audience.spec(),
        subject=body.subject,
        body=body.body,
        template_code=body.template_code,
        channel=body.channel,
    )
    if body.send_now and not (
        svc.needs_approval(db, message) and message.approved_by is None
    ):
        svc.send(db, user, message)
    db.commit()
    return _out(db, message)


@router.post("/messages/{message_id}/approve")
def approve(
    message_id: int, user: User = Depends(approver), db: Session = Depends(get_db)
) -> dict:
    message = _message(db, user, message_id)
    svc.approve(db, user, message)
    svc.send(db, user, message)
    db.commit()
    return _out(db, message)


@router.post("/broadcast", status_code=status.HTTP_201_CREATED)
def broadcast(
    body: BroadcastIn,
    user: User = Depends(broadcaster),
    db: Session = Depends(get_db),
) -> dict:
    """The emergency broadcast of §5.9.3, deliberately its own thing.

    It bypasses every opt-out and the quiet hours, and it skips the bulk
    approval — "the school is closed tomorrow" cannot wait for a second
    signature at nine at night, which is the situation the whole feature is
    for. It is audited like everything else, and §5.9.10 asks for that audit
    trail specifically.
    """
    if not body.confirm:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "An emergency broadcast must be confirmed: it overrides every "
            "opt-out and the quiet hours.",
        )
    message = svc.compose(
        db,
        user,
        category=MessageCategory.emergency,
        audience=body.audience.spec(),
        subject=body.subject,
        body=body.body,
    )
    message.approved_by = user.id
    svc.send(db, user, message)
    db.commit()
    return _out(db, message)


@router.post("/messages/{message_id}/cancel")
def cancel(
    message_id: int, user: User = Depends(sender), db: Session = Depends(get_db)
) -> dict:
    message = _message(db, user, message_id)
    if message.status in (MessageStatus.completed, MessageStatus.failed):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This message has already gone out"
        )
    message.status = MessageStatus.cancelled
    db.commit()
    return _out(db, message)


# --- reading ----------------------------------------------------------------


@router.get("/messages")
def messages(
    status_filter: MessageStatus | None = Query(default=None, alias="status"),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(Message).where(Message.school_id == user.school_id)
    if status_filter is not None:
        q = q.where(Message.status == status_filter)
    rows = db.scalars(q.order_by(Message.id.desc()).limit(200))
    return [_out(db, m) for m in rows]


@router.get("/messages/{message_id}")
def delivery_report(
    message_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    """The per-campaign delivery report of §5.9.10."""
    return svc.delivery_report(db, _message(db, user, message_id))


@router.get("/unreachable")
def unreachable(
    user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    """Families with no email on file (§5.9.10).

    §0.11 made email the only v1 channel, so this is the list that says how
    much of the school a circular cannot reach — and the phone number the
    office will have to ring instead.
    """
    return svc.unreachable_contacts(db, user.school_id)


# --- templates ---------------------------------------------------------------


@router.get("/templates")
def templates(
    user: User = Depends(reader), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.scalars(
        select(MessageTemplate)
        .where(
            MessageTemplate.school_id == user.school_id,
            MessageTemplate.is_active.is_(True),
        )
        .order_by(MessageTemplate.code)
    )
    return [
        {
            "id": t.id,
            "code": t.code,
            "version": t.version,
            "name": t.name,
            "category": t.category.value,
            "channel": t.channel.value,
            "subject": t.subject,
            "body": t.body,
        }
        for t in rows
    ]


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def supersede_template(
    body: TemplateIn, user: User = Depends(templater), db: Session = Depends(get_db)
) -> dict:
    """Add a version. Never an edit in place (§5.9.9).

    The wording a school uses is theirs to change without a deploy (§0.18), and
    changing it must not rewrite what was sent last term.
    """
    row = svc.supersede(
        db,
        user.school_id,
        code=body.code,
        name=body.name,
        category=body.category,
        subject=body.subject,
        body=body.body,
        channel=body.channel,
    )
    db.commit()
    return {"id": row.id, "code": row.code, "version": row.version}


# --- preferences -------------------------------------------------------------


@router.put("/preferences")
def set_preference(
    body: PreferenceIn,
    user: User = Depends(require_permission("comms.notice.read")),
    db: Session = Depends(get_db),
) -> dict:
    """A person's own opt-out, set by that person.

    Gated on a permission everybody holds, because this changes nothing but the
    caller's own preferences — and recorded even for a category that overrides
    it, so the choice is on file the day that changes.
    """
    row = svc.set_preference(
        db,
        user,
        category=body.category,
        channel=body.channel,
        opted_out=body.opted_out,
    )
    db.commit()
    return {
        "category": row.category.value,
        "channel": row.channel.value,
        "opted_out": row.opted_out,
        "honoured": row.category not in svc.MANDATORY_CATEGORIES,
    }
