"""Composing, addressing and sending — everything except the actual dispatch.

**Dispatch happens in the worker.** §5.9.9 is direct about why: a gateway
timeout must never fail the action that triggered the message. So nothing here
opens a socket. `send()` resolves the audience, writes the delivery rows and
`enqueue()`s a job; `dispatch()` is what the handler in `app/jobs.py` calls
once it is safely outside the request that caused it. A parent's fee payment
must not fail because an SMTP host was slow.

Three rules shape the rest:

* **Opt-out is respected for informational messages and overridden for
  statutory ones** (§5.9.9). `MANDATORY_CATEGORIES` is that line written down.
  A parent cannot opt out of "your child is absent" or "the school is closed".
* **No family's data may appear in another family's message.** That is not a
  promise to be careful, it is the shape of `MessageRecipient.context`: the
  render is handed one recipient's values and has nothing else to reach for.
* **Templates are versioned and the message snapshots what it sent**, so the
  exact text a parent received in March is still reconstructable in September
  after the template has been edited twice.
"""

from __future__ import annotations

import logging
import smtplib
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from string import Template
from typing import Protocol
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    Application,
    AuditAction,
    Channel,
    ClassSection,
    DeliveryStatus,
    Employee,
    Enrolment,
    EnrolmentStatus,
    Guardian,
    Message,
    MessageCategory,
    MessageRecipient,
    MessageStatus,
    MessageTemplate,
    NotificationPreference,
    RouteStop,
    School,
    Student,
    StudentGuardian,
    TransportAssignment,
    User,
    UserRole,
)
from app.services import audit, jobs, school_settings, scoping

log = logging.getLogger("comms")

# §5.9.9: the categories nobody may opt out of. "Your child is absent" and
# "the school is closed" are the blueprint's own examples, and they are the
# two here. Fees is deliberately *not* on the list — a school that wants its
# dues reminders to be unrefusable is making a policy choice somebody should
# make out loud, and it is one line to add. See HANDOFF §8 item S.
MANDATORY_CATEGORIES = {MessageCategory.emergency, MessageCategory.attendance}

MAX_ATTEMPTS = 3


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def _refuse(message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, message)


# --- the provider seam ------------------------------------------------------
#
# The same shape as `services/storage.py`: a Protocol, a backend that needs
# nothing running so the tests and a bare `uvicorn` work, and a real one chosen
# by configuration. Callers never learn which they have.


class Provider(Protocol):
    def send(self, *, to: str, subject: str, body: str, headers: dict) -> str: ...


class ConsoleProvider:
    """Logs instead of sending. The default, and what the tests use.

    Not a silent no-op: it returns a reference and logs the address, so a
    delivery report in development still shows rows that moved rather than a
    column of `queued` that looks like a bug in the queue.
    """

    def __init__(self) -> None:
        self._sent = 0

    def send(self, *, to: str, subject: str, body: str, headers: dict) -> str:
        self._sent += 1
        log.info("email to %s: %s", to, subject)
        return f"console-{self._sent}"


class SmtpProvider:
    """Anything speaking SMTP: Brevo and Resend both do, which is what §0.11
    names. Uses `smtplib` from the standard library rather than a provider SDK
    — one HTTP client per vendor is a dependency per vendor, and switching
    provider should be four environment variables."""

    def __init__(self, host: str, port: int, user: str, password: str, sender: str):
        self._host, self._port = host, port
        self._user, self._password, self._sender = user, password, sender

    def send(self, *, to: str, subject: str, body: str, headers: dict) -> str:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._sender
        msg["To"] = to
        for key, value in headers.items():
            if value:
                msg[key] = value
        msg.set_content(body)
        with smtplib.SMTP(self._host, self._port, timeout=20) as smtp:
            smtp.starttls()
            if self._user:
                smtp.login(self._user, self._password)
            smtp.send_message(msg)
        return msg.get("Message-ID") or "smtp"


_provider: Provider | None = None


def get_provider() -> Provider:
    """One backend per process, chosen by configuration.

    No SMTP host configured means the console, so neither a developer nor the
    test suite ever needs a mail server — and nothing is ever accidentally
    posted to a real parent from a laptop.
    """
    global _provider
    if _provider is None:
        if settings.SMTP_HOST:
            _provider = SmtpProvider(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
                settings.SMTP_FROM or settings.SMTP_USER,
            )
        else:
            _provider = ConsoleProvider()
    return _provider


def reset_provider() -> None:  # pragma: no cover - test helper
    global _provider
    _provider = None


def assert_channel_enabled(db: Session, school_id: int, channel: Channel) -> None:
    """§0.11: email now, SMS and WhatsApp wired but off until a school has DLT
    registration — which is a legal step, not a toggle somebody should be able
    to flip past by accident."""
    if channel is Channel.email:
        return
    if not school_settings.get(db, school_id, f"comms.channel.{channel.value}"):
        raise _bad(
            f"{channel.value.upper()} is not enabled for this school. It needs "
            "provider credentials and, for SMS, DLT registration."
        )


# --- rendering --------------------------------------------------------------


def render(text: str, context: dict) -> str:
    """Substitute `$name` placeholders, and nothing more.

    `string.Template`, not `str.format` and not a template engine. A template
    body is typed by a school's office staff into a text box; `format_map`
    would let `{x.__class__.__mro__}` walk out of the values it was handed, and
    a real engine would put a sandbox escape behind a records clerk's screen
    for the sake of a loop nobody asked for.

    `safe_substitute` leaves an unknown placeholder standing as written rather
    than blanking it, so a mistyped `$chidl_name` is visible in the preview
    instead of quietly producing "Dear ,".
    """
    return Template(text).safe_substitute(context)


# --- audiences --------------------------------------------------------------
#
# Each resolver returns one dict per recipient: the address to write to, the
# links that put the message on somebody's 360° log, and **that recipient's
# merge values and nobody else's**.


def _school_context(db: Session, school_id: int) -> dict:
    school = db.get(School, school_id)
    return {"school_name": school.name if school else ""}


def _guardian_rows(db: Session, school_id: int, student_ids: list[int]) -> list[dict]:
    """The primary guardian of each child, with that child's own details.

    Primary rather than every guardian on the record: §5.9.9 wants one message
    per family, not one per adult, and `fees.primary_contact()` already treats
    the primary as "who the office rings".
    """
    if not student_ids:
        return []
    base = _school_context(db, school_id)
    rows = db.execute(
        select(Guardian, Student, Enrolment, ClassSection)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .join(Student, Student.id == StudentGuardian.student_id)
        .outerjoin(
            Enrolment,
            (Enrolment.student_id == Student.id)
            & (Enrolment.status == EnrolmentStatus.active),
        )
        .outerjoin(ClassSection, ClassSection.id == Enrolment.class_section_id)
        .where(
            StudentGuardian.school_id == school_id,
            StudentGuardian.student_id.in_(student_ids),
            StudentGuardian.is_primary.is_(True),
        )
    ).all()

    out = []
    for guardian, student, _enrolment, section in rows:
        out.append(
            {
                # `None` where the family has no email on file. Reported rather
                # than dropped: §5.9.10 asks for the unreachable list by name,
                # and it is the thing that drives a data-cleanup drive. Silently
                # skipping them is how a school believes it told everybody.
                "to_address": guardian.user.email or None,
                "user_id": guardian.user_id,
                "guardian_id": guardian.id,
                "student_id": student.id,
                "context": {
                    **base,
                    "guardian_name": guardian.user.full_name,
                    "child_name": student.user.full_name,
                    "admission_no": student.admission_no,
                    "class_label": section.label if section else "",
                },
            }
        )
    return out


def _audience_student(db: Session, school_id: int, spec: dict) -> list[dict]:
    return _guardian_rows(db, school_id, [int(spec["student_id"])])


def _audience_section(db: Session, school_id: int, spec: dict) -> list[dict]:
    ids = list(
        db.scalars(
            select(Enrolment.student_id).where(
                Enrolment.school_id == school_id,
                Enrolment.class_section_id == int(spec["class_section_id"]),
                Enrolment.status == EnrolmentStatus.active,
            )
        )
    )
    return _guardian_rows(db, school_id, ids)


def _audience_all_guardians(db: Session, school_id: int, spec: dict) -> list[dict]:
    ids = list(
        db.scalars(
            select(Enrolment.student_id).where(
                Enrolment.school_id == school_id,
                Enrolment.status == EnrolmentStatus.active,
            )
        )
    )
    return _guardian_rows(db, school_id, ids)


def _audience_route(db: Session, school_id: int, spec: dict) -> list[dict]:
    """The families on one bus — §5.9.6's transport audience, and what a route
    change or a breakdown actually needs.

    `transport.LIVE` rather than a second list of statuses spelled out here:
    the set of assignments that count as "on this bus" is the transport
    module's to define, and it is already what the capacity check counts.
    """
    from app.services.transport import LIVE

    ids = list(
        db.scalars(
            select(Enrolment.student_id)
            .join(TransportAssignment, TransportAssignment.enrolment_id == Enrolment.id)
            .join(RouteStop, RouteStop.id == TransportAssignment.route_stop_id)
            .where(
                Enrolment.school_id == school_id,
                RouteStop.route_id == int(spec["route_id"]),
                TransportAssignment.status.in_(LIVE),
            )
        )
    )
    return _guardian_rows(db, school_id, ids)


def _audience_defaulters(db: Session, school_id: int, spec: dict) -> list[dict]:
    """The fee chase, addressed from the same list the defaulter screen shows.

    Calls `fees.defaulters()` rather than rebuilding the query, which is why
    that function moved out of its route. The amount owed goes into each
    family's own context — and only their own.
    """
    from app.services import fees

    rows = fees.defaulters(
        db, school_id, min_amount=_decimal(spec.get("min_amount", 0))
    )
    by_student = {r["student_id"]: r for r in rows}
    out = _guardian_rows(db, school_id, list(by_student))
    for r in out:
        owed = by_student[r["student_id"]]
        r["context"].update(
            {
                "amount_due": f"{owed['outstanding']:.2f}",
                "months_due": str(owed["months_due"]),
                "days_overdue": str(owed["days_overdue"]),
            }
        )
    return out


def _decimal(value):
    from decimal import Decimal

    return Decimal(str(value))


def _staff_rows(db: Session, school_id: int, employees: list[Employee]) -> list[dict]:
    base = _school_context(db, school_id)
    out = []
    for e in employees:
        out.append(
            {
                "to_address": e.user.email or None,
                "user_id": e.user_id,
                "context": {
                    **base,
                    "staff_name": e.user.full_name,
                    "employee_code": e.employee_code,
                },
            }
        )
    return out


def _audience_employee(db: Session, school_id: int, spec: dict) -> list[dict]:
    e = db.get(Employee, int(spec["employee_id"]))
    if e is None or e.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Employee not found")
    return _staff_rows(db, school_id, [e])


def _audience_staff(db: Session, school_id: int, spec: dict) -> list[dict]:
    """Everyone in service. A `permission` in the spec narrows it to whoever
    holds that permission, which is how the transport compliance sweep reaches
    the Transport Manager rather than the whole staff room."""
    employees = [
        e
        for e in db.scalars(select(Employee).where(Employee.school_id == school_id))
        if e.in_service
    ]
    code = spec.get("permission")
    if code:
        from app.services import rbac

        employees = [
            e for e in employees if rbac.authz_for(db, e.user).can(code)
        ]
    return _staff_rows(db, school_id, employees)


def _audience_application(db: Session, school_id: int, spec: dict) -> list[dict]:
    """An applicant, who is **not a user** (CLAUDE.md) and usually never
    becomes one. This is the audience the whole nullable-links design exists
    for: the address comes off the application form itself."""
    app = db.get(Application, int(spec["application_id"]))
    if app is None or app.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return [
        {
            "to_address": _application_email(db, app),
            "application_id": app.id,
            "context": {
                **_school_context(db, school_id),
                "child_name": f"{app.first_name} {app.last_name}",
                "application_no": app.application_no or "",
                "class_applying_for": app.class_applying_for,
            },
        }
    ]


def _application_email(db: Session, app: Application) -> str | None:
    from app.models import ApplicationGuardian

    row = db.scalar(
        select(ApplicationGuardian)
        .where(ApplicationGuardian.application_id == app.id)
        .order_by(ApplicationGuardian.is_primary.desc(), ApplicationGuardian.id)
    )
    return row.email if row is not None else None


# name -> resolver. The same registry shape as `fees.OPT_IN_SOURCES`: an
# audience nothing here can resolve is refused rather than silently addressed
# to everybody, which is the failure mode worth designing against.
AUDIENCES: dict[str, Callable[[Session, int, dict], list[dict]]] = {
    "student": _audience_student,
    "section": _audience_section,
    "all_guardians": _audience_all_guardians,
    "route": _audience_route,
    "defaulters": _audience_defaulters,
    "employee": _audience_employee,
    "staff": _audience_staff,
    "application": _audience_application,
}


def resolve(db: Session, school_id: int, audience: dict) -> list[dict]:
    kind = audience.get("kind")
    resolver = AUDIENCES.get(kind)
    if resolver is None:
        raise _bad(
            f"Unknown audience {kind!r}. Known: " + ", ".join(sorted(AUDIENCES))
        )
    return resolver(db, school_id, audience)


# --- who may address whom ---------------------------------------------------


def assert_may_address(db: Session, user: User, audience: dict) -> None:
    """§5.9.8's scoping, applied where scoping belongs.

    A teacher holds `comms.message.send` school-wide — permissions here are
    unscoped and the restriction lives in the service, which is the pattern
    §4 of the handoff warns must not be skipped. A class teacher writing to a
    section they do not teach is the realistic leak, and it is refused here.
    """
    if user.role is not UserRole.teacher:
        return
    kind = audience.get("kind")
    if kind == "section":
        scoping.assert_teaches_section(db, user, int(audience["class_section_id"]))
        return
    if kind == "student":
        scoping.assert_can_read_student(db, user, int(audience["student_id"]))
        return
    raise scoping.forbidden(
        "A teacher may write to a section they teach, or to one of its students"
    )


# --- opt-out ----------------------------------------------------------------


def opted_out_users(
    db: Session, school_id: int, category: MessageCategory, channel: Channel
) -> set[int]:
    """Who has asked not to receive this — and an empty set when they cannot.

    §5.9.9: informational messages respect the preference, statutory ones
    override it. Returning nothing for a mandatory category is how the override
    is expressed, rather than a branch at every call site that somebody will
    eventually forget.
    """
    if category in MANDATORY_CATEGORIES:
        return set()
    return set(
        db.scalars(
            select(NotificationPreference.user_id).where(
                NotificationPreference.school_id == school_id,
                NotificationPreference.category == category,
                NotificationPreference.channel == channel,
                NotificationPreference.opted_out.is_(True),
            )
        )
    )


def set_preference(
    db: Session,
    user: User,
    *,
    category: MessageCategory,
    channel: Channel = Channel.email,
    opted_out: bool = True,
) -> NotificationPreference:
    """Record a person's choice. Accepted even for a mandatory category.

    Refusing to store it would be the wrong place to argue: the preference is
    what somebody asked for, and `opted_out_users` is where the school's
    obligation to tell them their child is missing overrides it. Storing it
    also means the day a category stops being mandatory, the choice is already
    on file.
    """
    row = db.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user.id,
            NotificationPreference.category == category,
            NotificationPreference.channel == channel,
        )
    )
    if row is None:
        row = NotificationPreference(
            school_id=user.school_id,
            user_id=user.id,
            category=category,
            channel=channel,
        )
        db.add(row)
    row.opted_out = opted_out
    db.flush()
    return row


# --- composing --------------------------------------------------------------


def active_template(db: Session, school_id: int, code: str) -> MessageTemplate:
    row = db.scalar(
        select(MessageTemplate).where(
            MessageTemplate.school_id == school_id,
            MessageTemplate.code == code,
            MessageTemplate.is_active.is_(True),
        )
    )
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"No active template with code {code!r}"
        )
    return row


def supersede(
    db: Session,
    school_id: int,
    *,
    code: str,
    name: str,
    category: MessageCategory,
    subject: str,
    body: str,
    channel: Channel = Channel.email,
) -> MessageTemplate:
    """Add a version and stand the previous one down.

    Never an edit in place, for the reason §5.9.9 gives: the exact text sent
    must be reproducible later. `services/grading.py` supersedes a grading
    scale the same way, and for the same reason.
    """
    current = db.scalar(
        select(MessageTemplate)
        .where(
            MessageTemplate.school_id == school_id, MessageTemplate.code == code
        )
        .order_by(MessageTemplate.version.desc())
    )
    if current is not None:
        current.is_active = False
        db.flush()
    row = MessageTemplate(
        school_id=school_id,
        code=code,
        version=(current.version + 1) if current is not None else 1,
        name=name,
        category=category,
        subject=subject,
        body=body,
        channel=channel,
        is_active=True,
    )
    db.add(row)
    db.flush()
    return row


def preview(db: Session, school_id: int, audience: dict) -> dict:
    """Who this would reach, before anybody sends it.

    §5.9.9 requires the count up front. It is also the honest answer to "is
    this the right audience" — a builder that says 412 when the office expected
    40 has caught the mistake at the only moment it is cheap.
    """
    rows = resolve(db, school_id, audience)
    reachable = [r for r in rows if r["to_address"]]
    return {
        "audience": audience,
        "resolved": len(rows),
        "recipients": len(reachable),
        # Counted, never assumed. §5.10.9 forbids a fabricated data point, and
        # a zero here that nobody computed would be exactly that — while the
        # real number is the one that says a circular reached two thirds of the
        # school.
        "unreachable": len(rows) - len(reachable),
        "sample": [r["to_address"] for r in reachable[:5]],
    }


def compose(
    db: Session,
    actor: User,
    *,
    category: MessageCategory,
    audience: dict,
    subject: str | None = None,
    body: str | None = None,
    template_code: str | None = None,
    channel: Channel = Channel.email,
) -> Message:
    """Build the message and its delivery rows. Sends nothing.

    Recipients are resolved **now** rather than at dispatch, so the list the
    office approved is the list that goes out. Resolving at send time would let
    a child who left on Friday receive Monday's circular, and would make the
    count shown at approval a guess.
    """
    school_id = actor.school_id
    assert_channel_enabled(db, school_id, channel)
    assert_may_address(db, actor, audience)

    template = None
    if template_code is not None:
        template = active_template(db, school_id, template_code)
        subject = subject or template.subject
        body = body or template.body
        category = template.category
    if not subject or not body:
        raise _bad("A message needs a subject and a body, or a template")

    rows = resolve(db, school_id, audience)
    opted_out = opted_out_users(db, school_id, category, channel)

    message = Message(
        school_id=school_id,
        category=category,
        channel=channel,
        template_id=template.id if template else None,
        template_version=template.version if template else None,
        subject=subject,
        body=body,
        audience=audience,
        status=MessageStatus.draft,
        created_by=actor.id,
    )
    db.add(message)
    db.flush()

    unreachable = 0
    for row in rows:
        user_id = row.get("user_id")
        address = row["to_address"]
        # Every resolved recipient gets a row with a status (§5.9.9), including
        # the two kinds that will never be written to. "We deliberately did not
        # message this family" and "we had no way to" are both things somebody
        # will one day need to point at, and a missing row cannot be pointed at.
        if not address:
            unreachable += 1
            status_ = DeliveryStatus.failed
            reason = "No email address on file"
        elif user_id is not None and user_id in opted_out:
            status_ = DeliveryStatus.opted_out
            reason = None
        else:
            status_ = DeliveryStatus.queued
            reason = None
        db.add(
            MessageRecipient(
                school_id=school_id,
                message_id=message.id,
                user_id=user_id,
                guardian_id=row.get("guardian_id"),
                student_id=row.get("student_id"),
                application_id=row.get("application_id"),
                to_address=address or "",
                channel=channel,
                context=row["context"],
                status=status_,
                failure_reason=reason,
            )
        )
    db.flush()
    audit.record(
        db,
        actor=actor,
        school_id=school_id,
        entity_type="message",
        entity_id=message.id,
        action=AuditAction.create,
        after={
            "category": category.value,
            "audience": audience,
            "recipients": len(rows),
            "unreachable": unreachable,
        },
    )
    db.flush()
    return message


# --- approving and sending --------------------------------------------------


def queued_count(db: Session, message: Message) -> int:
    return sum(
        1 for r in message.recipients if r.status is DeliveryStatus.queued
    )


def needs_approval(db: Session, message: Message) -> bool:
    threshold = int(
        school_settings.get(db, message.school_id, "comms.bulk_approval_threshold")
    )
    return queued_count(db, message) > threshold


def approve(db: Session, actor: User, message: Message) -> Message:
    if message.status not in (MessageStatus.draft, MessageStatus.scheduled):
        raise _refuse("Only a message that has not gone out can be approved")
    if message.created_by == actor.id:
        # The same segregation the fee counter and the payroll run already
        # have: whoever writes a bulk send to four hundred families is not the
        # person who decides it should go.
        raise _refuse("A bulk send is approved by somebody other than its author")
    message.approved_by = actor.id
    message.approved_at = datetime.now(UTC)
    audit.record(
        db,
        actor=actor,
        school_id=message.school_id,
        entity_type="message",
        entity_id=message.id,
        action=AuditAction.status_change,
        after={"approved": True, "recipients": queued_count(db, message)},
        reason="bulk send approved",
    )
    db.flush()
    return message


def _local_now(db: Session, school_id: int) -> datetime:
    """The wall clock in the school's office.

    CLAUDE.md records what comparing a local date against a UTC column already
    cost once: the office is five and a half hours ahead of the column. Quiet
    hours are a statement about somebody's evening, so they are decided here
    and nowhere else.
    """
    tz = school_settings.get(db, school_id, "school.timezone")
    try:
        return datetime.now(ZoneInfo(tz))
    except Exception:  # noqa: BLE001 - a mistyped zone must not stop a send
        log.warning("unknown timezone %r for school %s; using UTC", tz, school_id)
        return datetime.now(UTC)


def quiet_until(db: Session, school_id: int, category: MessageCategory) -> datetime | None:
    """When this message may go out, or `None` for now.

    §5.9.9: quiet hours hold anything that is not an emergency. An emergency
    broadcast bypasses them, which is most of the point of having a separate
    kind of send.
    """
    if category is MessageCategory.emergency:
        return None
    start = int(school_settings.get(db, school_id, "comms.quiet_hours_start"))
    end = int(school_settings.get(db, school_id, "comms.quiet_hours_end"))
    now = _local_now(db, school_id)
    # The window wraps midnight, which is the ordinary case: 21:00 to 07:00.
    inside = now.hour >= start or now.hour < end if start > end else start <= now.hour < end
    if not inside:
        return None
    release = now.replace(hour=end, minute=0, second=0, microsecond=0)
    if release <= now:
        release += timedelta(days=1)
    return release.astimezone(UTC)


def send(
    db: Session, actor: User, message: Message, *, system: bool = False
) -> Message:
    """Hand the message to the worker. Opens no socket (§5.9.9).

    `system=True` is for a message a scheduled job raised, and it skips the
    bulk-approval gate. That gate exists so a person cannot accidentally write
    to the whole school (§5.9.9); a nightly fee chase is not an accident. The
    school approved it once and deliberately — by writing the template and
    enabling the schedule — and requiring a second signature every morning
    would mean the chase never goes out at all, or that somebody clicks
    approve unread every day, which is worse than not asking.

    It is not a hole: the send is audited like any other, appears in the
    outbox with its delivery report, and only `notify()` passes it.
    """
    if message.status not in (MessageStatus.draft, MessageStatus.scheduled):
        raise _refuse(f"This message is already {message.status.value}")
    if not system and needs_approval(db, message) and message.approved_by is None:
        threshold = school_settings.get(
            db, message.school_id, "comms.bulk_approval_threshold"
        )
        raise _refuse(
            f"{queued_count(db, message)} recipients is above this school's "
            f"threshold of {threshold}; it needs approving first"
        )

    hold_until = quiet_until(db, message.school_id, message.category)
    message.status = MessageStatus.scheduled if hold_until else MessageStatus.sending
    message.scheduled_for = hold_until
    db.flush()

    jobs.enqueue(
        db,
        "comms.dispatch",
        school_id=message.school_id,
        payload={"message_id": message.id},
        run_after=hold_until,
        idempotency_key=f"comms:dispatch:{message.id}",
        requested_by=actor.id if actor else None,
    )
    audit.record(
        db,
        actor=actor,
        school_id=message.school_id,
        entity_type="message",
        entity_id=message.id,
        action=AuditAction.status_change,
        after={
            "status": message.status.value,
            "held_until": str(hold_until) if hold_until else None,
            "recipients": queued_count(db, message),
            "system": system,
        },
        reason="queued for dispatch by a scheduled job" if system else "queued for dispatch",
    )
    db.flush()
    return message


# --- dispatch, called only from the worker ----------------------------------


def dispatch(db: Session, message: Message) -> dict:
    """Send every queued recipient, one at a time, recording each outcome.

    A failure against one address must not stop the other three hundred, so
    each send is caught individually and written down. §5.9.9: failures are
    retried with backoff and then surfaced, never silently dropped — so a
    recipient below `MAX_ATTEMPTS` goes back to `queued` and the job re-queues
    itself, and one that has exhausted them stays `failed` with its reason on
    the row where the delivery report will show it.
    """
    provider = get_provider()
    headers = {
        "Reply-To": school_settings.get(db, message.school_id, "comms.reply_to"),
    }
    sent = failed = 0
    retryable = False

    for recipient in message.recipients:
        if recipient.status is not DeliveryStatus.queued:
            continue
        recipient.attempts += 1
        try:
            ref = provider.send(
                to=recipient.to_address,
                # Rendered per recipient, from that recipient's context alone.
                # There is no shared blob to accidentally merge in, which is
                # what stops one family's amount owed reaching another's inbox.
                subject=render(message.subject, recipient.context),
                body=render(message.body, recipient.context),
                headers=headers,
            )
        except Exception as exc:  # noqa: BLE001 - one address must not stop the run
            recipient.failure_reason = f"{type(exc).__name__}: {exc}"[:500]
            if recipient.attempts < MAX_ATTEMPTS:
                recipient.status = DeliveryStatus.queued
                retryable = True
            else:
                recipient.status = DeliveryStatus.failed
            failed += 1
            log.warning("send to %s failed: %s", recipient.to_address, exc)
        else:
            recipient.status = DeliveryStatus.sent
            recipient.sent_at = datetime.now(UTC)
            recipient.provider_ref = ref
            recipient.failure_reason = None
            sent += 1

    if retryable:
        # Backoff in the same shape `jobs.run_one` uses for a failed job.
        jobs.enqueue(
            db,
            "comms.dispatch",
            school_id=message.school_id,
            payload={"message_id": message.id},
            run_after=datetime.now(UTC) + timedelta(minutes=5),
            idempotency_key=f"comms:dispatch:{message.id}:retry:{datetime.now(UTC):%Y%m%d%H%M}",
        )
    else:
        message.status = (
            MessageStatus.failed
            if sent == 0 and failed > 0
            else MessageStatus.completed
        )
        message.sent_at = datetime.now(UTC)
    db.flush()
    return {
        "message_id": message.id,
        "sent": sent,
        "failed": failed,
        "retrying": retryable,
    }


def delivery_report(db: Session, message: Message) -> dict:
    """§5.9.10, per campaign: what went, what did not, and why."""
    by_status: dict[str, int] = {}
    for r in message.recipients:
        by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
    failures = [
        {"to": r.to_address, "reason": r.failure_reason, "attempts": r.attempts}
        for r in message.recipients
        if r.status is DeliveryStatus.failed
    ]
    return {
        "message_id": message.id,
        "status": message.status.value,
        "subject": message.subject,
        "category": message.category.value,
        "recipients": len(message.recipients),
        "by_status": by_status,
        "failures": failures,
    }


def unreachable_contacts(db: Session, school_id: int) -> list[dict]:
    """Families and staff with no email on file (§5.9.10).

    The list that drives a data-cleanup drive, and the honest counterweight to
    a delivery report that only counts what it could attempt. §0.11 chose email
    for v1; a school whose parents were only ever asked for a mobile number
    needs to see how many of them that leaves out.
    """
    rows = db.execute(
        select(Student, Guardian, User)
        .join(StudentGuardian, StudentGuardian.student_id == Student.id)
        .join(Guardian, Guardian.id == StudentGuardian.guardian_id)
        .join(User, User.id == Guardian.user_id)
        .where(
            StudentGuardian.school_id == school_id,
            StudentGuardian.is_primary.is_(True),
            (User.email.is_(None)) | (User.email == ""),
        )
    ).all()
    return [
        {
            "student_id": student.id,
            "student_name": student.user.full_name,
            "admission_no": student.admission_no,
            "guardian_name": user.full_name,
            # What the school does have, which is what the office will ring.
            "phone": user.phone,
        }
        for student, _guardian, user in rows
    ]


# --- the shorthand every other module uses ----------------------------------


def notify(
    db: Session,
    school_id: int,
    *,
    template_code: str,
    audience: dict,
    actor: User | None = None,
    extra: dict | None = None,
) -> Message | None:
    """Send a templated message from inside another module's workflow.

    Returns `None` when the school has no such template rather than raising,
    which is deliberate: a school that has not written its own "fees overdue"
    wording should not have its nightly fee sweep fail because of it. The job
    result says how many notifications it sent, so a zero is visible.
    """
    template = db.scalar(
        select(MessageTemplate).where(
            MessageTemplate.school_id == school_id,
            MessageTemplate.code == template_code,
            MessageTemplate.is_active.is_(True),
        )
    )
    if template is None:
        log.info("school %s has no active template %r", school_id, template_code)
        return None

    system = actor or db.scalar(
        select(User).where(User.school_id == school_id, User.role == UserRole.admin)
    )
    message = compose(
        db,
        system,
        category=template.category,
        audience=audience,
        template_code=template_code,
        channel=template.channel,
    )
    if extra:
        for recipient in message.recipients:
            recipient.context = {**recipient.context, **extra}
    db.flush()
    if not queued_count(db, message):
        message.status = MessageStatus.completed
        message.sent_at = datetime.now(UTC)
        db.flush()
        return message
    return send(db, system, message, system=True)
