"""The outbox, and the four rules that make it more than a mail loop.

ERP_BLUEPRINT §5.9.9 has a long list. Four of its rules are the ones that
would actually hurt if they were wrong, and most of this file is about them:

* **dispatch happens in the worker** — a gateway timeout must never fail the
  action that triggered the message;
* **opt-out is respected for informational messages and overridden for
  statutory ones** — a parent cannot opt out of "your child is absent";
* **no family's data may appear in another family's message**, which a careless
  bulk merge is the realistic way to break;
* **the exact text sent stays reproducible** after the template is edited.
"""

from datetime import UTC, date as Date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import (
    Channel,
    ClassSection,
    DeliveryStatus,
    Employee,
    Enrolment,
    EnrolmentStatus,
    Guardian,
    Job,
    JobStatus,
    Message,
    MessageCategory,
    MessageRecipient,
    MessageStatus,
    MessageTemplate,
    Student,
    StudentGuardian,
    User,
)
from app.services import comms, jobs


@pytest.fixture(autouse=True)
def console(monkeypatch):
    """Every test uses the console provider, which is also the default.

    Asserted rather than assumed: a suite that quietly acquired a real SMTP
    host would post to real parents, and it would do it from whichever laptop
    ran it.
    """
    comms.reset_provider()
    provider = comms.get_provider()
    assert isinstance(provider, comms.ConsoleProvider)
    return provider


@pytest.fixture()
def section_id(db, ids):
    return ids["section_10a"]


def _drain(db):
    """Run the queue the way the worker does."""
    import app.jobs  # noqa: F401 - importing registers the handlers

    return jobs.drain(db)


# --- dispatch happens in the worker -----------------------------------------


def test_sending_queues_a_job_and_opens_no_socket(db, admin_user, section_id):
    """§5.9.9's first rule, and the reason the hosting decision could not be
    deferred: nothing in a request talks to a mail server."""

    class Exploding:
        def send(self, **kw):
            raise AssertionError("a send must never happen inside the request")

    comms._provider = Exploding()
    try:
        message = comms.compose(
            db,
            admin_user,
            category=MessageCategory.general,
            audience={"kind": "section", "class_section_id": section_id},
            subject="Sports day",
            body="Dear $guardian_name, sports day is on Friday.",
        )
        comms.send(db, admin_user, message)
    finally:
        comms.reset_provider()

    assert message.status is MessageStatus.sending
    queued = db.scalar(
        select(func.count(Job.id)).where(
            Job.kind == "comms.dispatch", Job.status == JobStatus.pending
        )
    )
    assert queued == 1


def test_the_worker_sends_and_records_every_outcome(db, admin_user, section_id):
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "section", "class_section_id": section_id},
        subject="Sports day",
        body="Dear $guardian_name, sports day is on Friday.",
    )
    comms.send(db, admin_user, message)
    db.commit()
    assert _drain(db) >= 1

    db.refresh(message)
    assert message.status is MessageStatus.completed
    assert message.sent_at is not None

    sent = [r for r in message.recipients if r.status is DeliveryStatus.sent]
    unreachable = [
        r for r in message.recipients if r.failure_reason == "No email address on file"
    ]
    # Everything that could be written to was, and the families with no address
    # on file are recorded as unreachable rather than quietly missing from the
    # list — which is the difference between a delivery report and a guess.
    assert sent and all(r.provider_ref for r in sent)
    assert unreachable, "the seed leaves some families with no email"
    assert len(sent) + len(unreachable) == len(message.recipients)


def test_a_failure_against_one_address_does_not_stop_the_rest(
    db, admin_user, section_id
):
    """§5.9.9: failures are retried and then surfaced, never silently dropped,
    and one bad address must not cost the other twenty-nine their message."""
    sent = []

    class OneBadAddress:
        def send(self, *, to, subject, body, headers):
            if len(sent) == 1:
                sent.append(to)
                raise RuntimeError("550 mailbox unavailable")
            sent.append(to)
            return "ok"

    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "section", "class_section_id": section_id},
        subject="Sports day",
        body="Dear $guardian_name.",
    )
    comms._provider = OneBadAddress()
    try:
        result = comms.dispatch(db, message)
    finally:
        comms.reset_provider()

    assert result["sent"] >= 1
    assert result["failed"] == 1
    # Below the attempt ceiling it goes back on the queue rather than being
    # abandoned, and the reason is written where the delivery report shows it.
    bounced = [
        r for r in message.recipients if r.failure_reason and "550" in r.failure_reason
    ]
    assert len(bounced) == 1
    assert bounced[0].attempts == 1
    assert result["retrying"] is True


def test_a_recipient_is_given_up_on_only_after_three_attempts(
    db, admin_user, ids
):
    class AlwaysFails:
        def send(self, **kw):
            raise RuntimeError("connection refused")

    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "student", "student_id": ids["student_1"]},
        subject="Hello",
        body="Dear $guardian_name.",
    )
    comms._provider = AlwaysFails()
    try:
        for _ in range(comms.MAX_ATTEMPTS):
            comms.dispatch(db, message)
    finally:
        comms.reset_provider()

    recipient = message.recipients[0]
    assert recipient.attempts == comms.MAX_ATTEMPTS
    assert recipient.status is DeliveryStatus.failed
    assert message.status is MessageStatus.failed
    report = comms.delivery_report(db, message)
    assert report["failures"][0]["reason"].startswith("RuntimeError")


# --- opt-out, and the categories that override it ---------------------------


def test_a_parent_can_opt_out_of_a_circular(db, admin_user, ids):
    guardian = db.scalar(
        select(Guardian)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(
            StudentGuardian.student_id == ids["student_1"],
            StudentGuardian.is_primary.is_(True),
        )
    )
    comms.set_preference(
        db, guardian.user, category=MessageCategory.general, opted_out=True
    )
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "student", "student_id": ids["student_1"]},
        subject="Sports day",
        body="Dear $guardian_name.",
    )
    # Recorded, not omitted. §5.9.9 wants every resolved recipient logged with
    # a status, and "we deliberately did not write to this family" is a status
    # somebody will one day need to point at.
    assert [r.status for r in message.recipients] == [DeliveryStatus.opted_out]

    comms.dispatch(db, message)
    assert message.recipients[0].sent_at is None


def test_a_parent_cannot_opt_out_of_their_child_being_absent(db, admin_user, ids):
    """§5.9.9 names this one. The opt-out is stored and then overridden — the
    school's obligation to say a child is missing is not a preference."""
    guardian = db.scalar(
        select(Guardian)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(
            StudentGuardian.student_id == ids["student_1"],
            StudentGuardian.is_primary.is_(True),
        )
    )
    comms.set_preference(
        db, guardian.user, category=MessageCategory.attendance, opted_out=True
    )
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.attendance,
        audience={"kind": "student", "student_id": ids["student_1"]},
        subject="Absence",
        body="$child_name was not in school today.",
    )
    assert [r.status for r in message.recipients] == [DeliveryStatus.queued]


def test_nobody_can_opt_out_of_an_emergency(db, admin_user, ids, section_id):
    for guardian in db.scalars(select(Guardian)):
        comms.set_preference(
            db, guardian.user, category=MessageCategory.emergency, opted_out=True
        )
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.emergency,
        audience={"kind": "section", "class_section_id": section_id},
        subject="School closed",
        body="The school is closed tomorrow.",
    )
    assert message.recipients
    # Nobody is held back by a preference. The only recipients not queued are
    # the families the school has no address for at all, which is a different
    # problem and one the unreachable list exists to surface.
    assert not any(
        r.status is DeliveryStatus.opted_out for r in message.recipients
    )
    assert any(r.status is DeliveryStatus.queued for r in message.recipients)


def test_the_mandatory_list_is_stated_rather_than_scattered(db):
    """If a category stops being unrefusable it should be one line, in one
    place, that somebody changed on purpose."""
    assert comms.MANDATORY_CATEGORIES == {
        MessageCategory.emergency,
        MessageCategory.attendance,
    }


# --- no family's data in another family's message ----------------------------


def test_one_familys_amount_owed_never_reaches_another(db, admin_user):
    """The realistic way §5.9.9's last rule breaks is a careless bulk merge.

    The fee chase is the worst case: every recipient's message contains a
    figure, and getting the merge wrong sends a family somebody else's debt.
    Each recipient is rendered from its own context and there is no shared
    blob to reach into, which is the design rather than a promise.
    """
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.fees,
        audience={"kind": "defaulters"},
        template_code="fees.overdue",
    )
    assert len(message.recipients) > 1, "the seed leaves families in arrears"

    rendered = {
        r.id: comms.render(message.body, r.context) for r in message.recipients
    }
    for recipient in message.recipients:
        mine = rendered[recipient.id]
        assert recipient.context["child_name"] in mine
        for other in message.recipients:
            if other.id == recipient.id:
                continue
            other_child = other.context["child_name"]
            if other_child == recipient.context["child_name"]:
                continue  # two families can share a child's name
            assert other_child not in mine


def test_a_recipients_context_holds_only_their_own_values(db, admin_user):
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.fees,
        audience={"kind": "defaulters"},
        template_code="fees.overdue",
    )
    for recipient in message.recipients:
        # Flat, small and about one child. A context that had grown a list of
        # everybody would be the shape the leak needs.
        assert set(recipient.context) <= {
            "school_name", "guardian_name", "child_name", "admission_no",
            "class_label", "amount_due", "months_due", "days_overdue",
        }


def test_the_chase_addresses_the_same_families_the_screen_lists(db, admin_user):
    """One definition, not two queries that drift (§5.10.9).

    The defaulter list moved out of its route so that this could be true, and
    this is the test that says it still is.
    """
    from app.services import fees

    listed = {r["student_id"] for r in fees.defaulters(db, admin_user.school_id)}
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.fees,
        audience={"kind": "defaulters"},
        template_code="fees.overdue",
    )
    addressed = {r.student_id for r in message.recipients}
    # Every family written to is on the list. The two can differ only by a
    # family with no email on file, which is the unreachable list of §5.9.10.
    assert addressed <= listed
    assert addressed


# --- templates are versioned -------------------------------------------------


def test_editing_a_template_does_not_rewrite_what_was_already_sent(
    db, admin_user, ids
):
    """§5.9.9: the exact text sent stays reproducible. `services/grading.py`
    supersedes a scale the same way and for the same reason."""
    first = comms.compose(
        db,
        admin_user,
        category=MessageCategory.fees,
        audience={"kind": "student", "student_id": ids["student_1"]},
        template_code="fees.overdue",
    )
    original_body = first.body
    original_version = first.template_version

    comms.supersede(
        db,
        admin_user.school_id,
        code="fees.overdue",
        name="Fee reminder",
        category=MessageCategory.fees,
        subject="Reworded",
        body="Completely different wording for $guardian_name.",
    )

    db.refresh(first)
    assert first.body == original_body
    assert first.template_version == original_version

    second = comms.compose(
        db,
        admin_user,
        category=MessageCategory.fees,
        audience={"kind": "student", "student_id": ids["student_1"]},
        template_code="fees.overdue",
    )
    assert second.body != original_body
    assert second.template_version == original_version + 1


def test_only_one_version_of_a_template_is_live(db, admin_user):
    for _ in range(3):
        comms.supersede(
            db,
            admin_user.school_id,
            code="fees.overdue",
            name="Fee reminder",
            category=MessageCategory.fees,
            subject="s",
            body="b",
        )
    live = db.scalars(
        select(MessageTemplate).where(
            MessageTemplate.school_id == admin_user.school_id,
            MessageTemplate.code == "fees.overdue",
            MessageTemplate.is_active.is_(True),
        )
    ).all()
    assert len(live) == 1
    assert live[0].version == 4


def test_a_mistyped_placeholder_stays_visible_rather_than_going_blank(db):
    out = comms.render("Dear $chidl_name, hello.", {"child_name": "Ravi"})
    assert "$chidl_name" in out


def test_the_renderer_cannot_be_walked_out_of(db):
    """A template body is typed into a text box by office staff. `str.format`
    would let `{x.__class__.__mro__}` reach out of the values it was handed;
    `string.Template` has no attribute access at all."""
    out = comms.render("${child_name.__class__}", {"child_name": "Ravi"})
    assert "class" in out  # left as literal text, not evaluated
    assert "str" not in out


# --- approval, quiet hours, and who may address whom -------------------------


def test_a_bulk_send_above_the_threshold_needs_approving(db, admin_user):
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "all_guardians"},
        subject="Annual day",
        body="Dear $guardian_name.",
    )
    assert comms.needs_approval(db, message)
    with pytest.raises(Exception) as e:
        comms.send(db, admin_user, message)
    assert e.value.status_code == 409
    assert "threshold" in e.value.detail


def test_the_author_of_a_bulk_send_is_not_its_approver(db, admin_user):
    """The same segregation the fee counter and the payroll run already have."""
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "all_guardians"},
        subject="Annual day",
        body="Dear $guardian_name.",
    )
    with pytest.raises(Exception) as e:
        comms.approve(db, admin_user, message)
    assert e.value.status_code == 409


def test_a_small_send_needs_nobody(db, admin_user, ids):
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "student", "student_id": ids["student_1"]},
        subject="Hello",
        body="Dear $guardian_name.",
    )
    assert not comms.needs_approval(db, message)
    comms.send(db, admin_user, message)
    assert message.status in (MessageStatus.sending, MessageStatus.scheduled)


def test_quiet_hours_hold_a_circular_and_never_an_emergency(db, admin_user):
    """§5.9.9. Set the window to cover the whole day so the assertion does not
    depend on what time the suite happens to run."""
    from app.services import school_settings

    school_settings.set_many(
        db, admin_user, {"comms.quiet_hours_start": 0, "comms.quiet_hours_end": 23}
    )
    held = comms.quiet_until(db, admin_user.school_id, MessageCategory.general)
    assert held is not None
    assert comms.quiet_until(db, admin_user.school_id, MessageCategory.emergency) is None


def test_an_unknown_audience_is_refused_rather_than_addressed_to_everybody(
    db, admin_user
):
    with pytest.raises(Exception) as e:
        comms.compose(
            db,
            admin_user,
            category=MessageCategory.general,
            audience={"kind": "everyone_probably"},
            subject="x",
            body="y",
        )
    assert e.value.status_code == 422
    assert "Unknown audience" in e.value.detail


def test_sms_is_wired_but_refused_until_a_school_has_dlt(db, admin_user, ids):
    """§0.11. Off is the default, and it is enforced at the send rather than
    only hidden in a UI."""
    with pytest.raises(Exception) as e:
        comms.compose(
            db,
            admin_user,
            category=MessageCategory.general,
            audience={"kind": "student", "student_id": ids["student_1"]},
            subject="x",
            body="y",
            channel=Channel.sms,
        )
    assert "DLT" in e.value.detail


def test_a_teacher_may_not_write_to_a_section_they_do_not_teach(
    db, ids, other_teacher, client
):
    """§5.9.8 scopes a class teacher to their own section, and the permission
    is unscoped — so the restriction has to be in the service or it is not
    there at all."""
    teacher_user = db.scalar(select(User).where(User.login_id == "TCH004"))
    with pytest.raises(Exception) as e:
        comms.assert_may_address(
            db, teacher_user, {"kind": "section", "class_section_id": ids["section_10a"]}
        )
    assert e.value.status_code == 403

    with pytest.raises(Exception) as e:
        comms.assert_may_address(db, teacher_user, {"kind": "all_guardians"})
    assert e.value.status_code == 403


# --- an applicant is not a user ---------------------------------------------


def test_a_message_can_be_addressed_to_somebody_with_no_login(db, admin_user, ids):
    """The whole reason every person link on a recipient row is nullable.

    Most applicants never become users, and the acknowledgement is the first
    message the system ever sends anybody.
    """
    from app.models import AdmissionCycle, Application, ApplicationGuardian, Gender, GuardianRelation

    cycle = db.scalar(select(AdmissionCycle).where(AdmissionCycle.school_id == ids["school"]))
    application = Application(
        school_id=ids["school"],
        cycle_id=cycle.id,
        first_name="Meera",
        last_name="Nair",
        date_of_birth=Date(2019, 3, 2),
        gender=Gender.female,
        class_applying_for="1",
        application_no="APP-TEST-1",
    )
    db.add(application)
    db.flush()
    db.add(
        ApplicationGuardian(
            school_id=ids["school"],
            application_id=application.id,
            relation=GuardianRelation.father,
            full_name="Anil Nair",
            mobile="9998887770",
            email="anil.nair@example.com",
            is_primary=True,
        )
    )
    db.flush()

    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.admission,
        audience={"kind": "application", "application_id": application.id},
        subject="We have your application for $child_name",
        body="Dear parent, application $application_no has been received.",
    )
    assert len(message.recipients) == 1
    recipient = message.recipients[0]
    assert recipient.to_address == "anil.nair@example.com"
    assert recipient.user_id is None, "an applicant is not a user"
    assert recipient.application_id == application.id
    assert "APP-TEST-1" in comms.render(message.body, recipient.context)


# --- the delivery record ----------------------------------------------------


def test_the_delivery_report_counts_every_resolved_recipient(
    db, admin_user, section_id
):
    message = comms.compose(
        db,
        admin_user,
        category=MessageCategory.general,
        audience={"kind": "section", "class_section_id": section_id},
        subject="Sports day",
        body="Dear $guardian_name.",
    )
    comms.dispatch(db, message)
    report = comms.delivery_report(db, message)
    assert report["recipients"] == len(message.recipients)
    assert sum(report["by_status"].values()) == report["recipients"]


def test_the_unreachable_list_names_who_cannot_be_emailed(db, admin_user):
    """§5.9.10 asks for this by name, and §0.11 is why it matters.

    Email is the only v1 channel, so a school whose parents were only ever
    asked for a mobile number reaches a fraction of its families. The honest
    counterweight to a delivery report is the count of people it never tried.
    """
    missing = comms.unreachable_contacts(db, admin_user.school_id)
    assert missing, "the seed leaves some families without an email"
    for row in missing:
        assert row["phone"], "what the office has instead, and will ring"

    preview = comms.preview(db, admin_user.school_id, {"kind": "all_guardians"})
    assert preview["unreachable"] > 0
    assert preview["recipients"] + preview["unreachable"] == preview["resolved"]


# --- wiring: the modules that had notifications and no way to send them ------


def test_the_overdue_sweep_chases_the_families_it_just_found(db, admin_user, ids):
    """The fee chase of §5.9, on the back of the sweep that already knows who
    is behind — and addressed through `fees.defaulters()`, so the families
    dunned are the families the office's screen lists."""
    import app.jobs  # noqa: F401
    from app.models import Job
    from app.services import fees

    job = jobs.enqueue(db, "fees.overdue_sweep", school_id=admin_user.school_id)
    db.flush()
    result = db.get(Job, job.id)
    from app.jobs import overdue_sweep

    out = overdue_sweep(db, result)
    assert out["chase_error"] is None
    assert out["chased"] > 0

    message = db.scalars(
        select(Message)
        .where(Message.category == MessageCategory.fees)
        .order_by(Message.id.desc())
    ).first()
    addressed = {r.student_id for r in message.recipients}
    assert addressed <= {r["student_id"] for r in fees.defaulters(db, admin_user.school_id)}


def test_a_broken_chase_does_not_undo_the_late_fees(db, admin_user, monkeypatch):
    """The coupling §5.9.9 exists to prevent, one layer in from the gateway
    timeout it names.

    `jobs.run_one` rolls the transaction back when a handler raises, so an
    exception escaping the chase would silently reverse the overdue marking and
    the late fees the sweep had just computed. A communication problem must
    never undo money work. This is the test for the bug that fix exists for.
    """
    import app.jobs
    from app.models import Job
    from app.services import comms as comms_module

    def explode(*a, **kw):
        raise RuntimeError("mail server on fire")

    monkeypatch.setattr(comms_module, "notify", explode)

    job = jobs.enqueue(db, "fees.overdue_sweep", school_id=admin_user.school_id)
    db.flush()
    out = app.jobs.overdue_sweep(db, db.get(Job, job.id))

    # The job succeeded, the money work stands, and the failure is reported
    # rather than dropped.
    assert "mail server on fire" in out["chase_error"]
    assert out["chased"] == 0
    assert out["late_fees_charged"] >= 0
    assert "marked_overdue" in out


def test_an_automated_send_is_not_held_up_by_the_bulk_threshold(db, admin_user):
    """A nightly chase is not an accidental blast.

    The approval gate exists so a person cannot write to the whole school by
    mistake (§5.9.9). A scheduled job running a template the school wrote and a
    schedule the school enabled was approved once, deliberately. Requiring a
    second signature every morning would mean the chase never goes out — or
    that somebody clicks approve unread daily, which is worse than not asking.
    """
    message = comms.notify(
        db,
        admin_user.school_id,
        template_code="fees.overdue",
        audience={"kind": "defaulters"},
    )
    assert message is not None
    assert comms.needs_approval(db, message), "this is a bulk send by any measure"
    assert message.approved_by is None
    assert message.status in (MessageStatus.sending, MessageStatus.scheduled)


def test_a_school_that_never_wrote_the_wording_still_gets_its_sweep(db, admin_user):
    """`notify` returns None rather than raising when a template is missing.

    A school losing its overdue *marking* because nobody edited a message
    template would be the tail wagging the dog.
    """
    for row in db.scalars(
        select(MessageTemplate).where(MessageTemplate.code == "fees.overdue")
    ):
        row.is_active = False
    db.flush()
    assert (
        comms.notify(
            db,
            admin_user.school_id,
            template_code="fees.overdue",
            audience={"kind": "defaulters"},
        )
        is None
    )


def test_the_transport_expiry_alert_reaches_whoever_holds_the_permission(
    db, admin_user
):
    """Addressed by permission rather than by role name, so a school that
    renames the Transport Manager or splits the job in two still reaches the
    person who actually does it."""
    rows = comms.resolve(
        db,
        admin_user.school_id,
        {"kind": "staff", "permission": "transport.setup.write"},
    )
    assert rows, "somebody holds transport.setup.write"
    everyone = comms.resolve(db, admin_user.school_id, {"kind": "staff"})
    assert len(rows) < len(everyone), "not the whole staff room"
