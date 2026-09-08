from enum import StrEnum


class SchoolStatus(StrEnum):
    onboarding = "onboarding"
    active = "active"
    suspended = "suspended"  # e.g. non-payment; data retained, logins refused
    closed = "closed"


class AcademicYearStatus(StrEnum):
    """Several of these may be live at once for one school (§3.1)."""

    planning = "planning"
    admissions_open = "admissions_open"
    active = "active"
    closing = "closing"
    closed = "closed"
    archived = "archived"


class StudentStatus(StrEnum):
    """Lifetime state. Distinct from EnrolmentStatus, which is per year."""

    enrolled = "enrolled"
    active = "active"
    suspended = "suspended"
    transferred_out = "transferred_out"
    struck_off = "struck_off"
    passed_out = "passed_out"
    alumni = "alumni"


class EnrolmentStatus(StrEnum):
    """How one academic year ended for one student."""

    active = "active"
    promoted = "promoted"
    detained = "detained"
    transferred_out = "transferred_out"
    struck_off = "struck_off"
    passed_out = "passed_out"


class OwnerType(StrEnum):
    """What a document is attached to. `application` exists before the student
    does, which is why documents are polymorphic rather than a student column."""

    student = "student"
    application = "application"
    guardian = "guardian"
    employee = "employee"
    vehicle = "vehicle"
    school = "school"


class EmployeeStatus(StrEnum):
    """ERP_BLUEPRINT §5.3.7, trimmed to the states this system can actually
    reach. `applicant`, `offered` and `onboarding` belong to recruitment, which
    is not built — adding them now would be three statuses nothing can set.
    """

    active = "active"
    on_leave = "on_leave"
    notice_period = "notice_period"
    exited = "exited"


class EmployeeType(StrEnum):
    teaching = "teaching"
    administrative = "administrative"
    support = "support"


class GuardianRelation(StrEnum):
    """Who this adult is to the child. A closed list because it drives who may
    collect them from the gate, not just how a letter is addressed."""

    father = "father"
    mother = "mother"
    grandparent = "grandparent"
    sibling = "sibling"
    legal_guardian = "legal_guardian"
    other = "other"


class CustomFieldType(StrEnum):
    """What a school-defined attribute holds. Deliberately few: every type
    here has an obvious form control and an obvious validation rule."""

    text = "text"
    number = "number"
    date = "date"
    boolean = "boolean"
    select = "select"


class DocumentStatus(StrEnum):
    pending = "pending"
    submitted = "submitted"
    verified = "verified"
    rejected = "rejected"
    resubmit_required = "resubmit_required"


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    cancelled = "cancelled"


class AuditAction(StrEnum):
    create = "create"
    update = "update"
    delete = "delete"
    status_change = "status_change"
    login = "login"
    login_failed = "login_failed"
    export = "export"
    print = "print"
    void = "void"
    publish = "publish"


class ScopeType(StrEnum):
    """How far a role assignment reaches."""

    school = "school"          # everywhere in this tenant
    academic_year = "academic_year"
    class_section = "class_section"
    department = "department"
    self_only = "self"         # own record only


class UserRole(StrEnum):
    admin = "admin"
    teacher = "teacher"
    parent = "parent"
    student = "student"


class AttendanceStatus(StrEnum):
    """§5.8.4. `late` and `half_day` exist because a school records them and
    then has to answer "was the child here?" — collapsing them into present or
    absent loses the fact the office was actually asked about.

    For the percentage, present and late count as attendance, half_day as half,
    and everything else as absence. Approved leave is still reported apart from
    unexcused absence, because to a parent those are not the same conversation.
    """

    present = "present"
    absent = "absent"
    late = "late"
    half_day = "half_day"
    leave = "leave"
    excused = "excused"


class SubstitutionStatus(StrEnum):
    """§5.7.7. `unfilled` is the one that matters operationally: a class nobody
    was assigned to is the number a principal wants on a dashboard."""

    pending = "pending"
    assigned = "assigned"
    unfilled = "unfilled"
    completed = "completed"


class LeaveType(StrEnum):
    sick = "sick"
    planned = "planned"
    emergency = "emergency"


class LeaveStatus(StrEnum):
    applied = "applied"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class ComponentType(StrEnum):
    """§3.16. The three behave differently and must not be one flag: an earning
    adds to gross, a deduction comes out of net, and an employer contribution
    is a cost to the school that never touches the employee's pay at all.
    """

    earning = "earning"
    deduction = "deduction"
    employer_contribution = "employer_contribution"


class CalculationMethod(StrEnum):
    """How a component's amount is arrived at (§3.16).

    `slab` and `formula` from the blueprint are deliberately absent. A formula
    evaluator is an injection surface for a configuration screen a records
    clerk uses, and slab-based TDS needs an annual projection this system does
    not have — both would be guesses. TDS ships as `fixed`, entered per
    employee by whoever computes it, and says so.
    """

    fixed = "fixed"
    percent_of_basic = "percent_of_basic"
    percent_of_gross = "percent_of_gross"
    # The balancing figure: whatever is left of gross after the other earnings.
    # There can be only one, or "whatever is left" has no meaning.
    balance = "balance"
    # gross / working days x days not worked (§3.16).
    loss_of_pay = "loss_of_pay"


class PayrollRunStatus(StrEnum):
    """§5.3.7 lists draft -> calculated -> approved -> paid -> locked. Four are
    implemented: `approved` already makes the run immutable, so `locked` would
    be a second door with the same key — the same reason `FeePeriodStatus`
    stops at two.
    """

    draft = "draft"
    calculated = "calculated"
    approved = "approved"
    paid = "paid"


class NoticeAudience(StrEnum):
    all = "all"
    students = "students"
    parents = "parents"
    teachers = "teachers"
    class_ = "class"


class InvoiceStatus(StrEnum):
    """ERP_BLUEPRINT §5.5.7. `overdue` is stored as well as computed: the
    scheduled sweep moves it, and `fees.presented_status()` shows how an
    invoice reads right now without a GET writing anything."""

    draft = "draft"
    issued = "issued"
    partially_paid = "partially_paid"
    paid = "paid"
    overdue = "overdue"
    voided = "voided"
    written_off = "written_off"


class FeePeriodStatus(StrEnum):
    """§5.5.7 lists open → closed → locked. Two states are implemented: a
    closed period refuses writes, and reopening it is an audited act with a
    reason. `locked` would be a third door with the same key, so it waits for
    a school that actually needs one.
    """

    open = "open"
    closed = "closed"


class FeePaymentStatus(StrEnum):
    """A payment is never edited. It succeeded, or a contra entry reversed it
    and both rows stay (§3.9 rule 3)."""

    success = "success"
    reversed = "reversed"


class Gender(StrEnum):
    male = "male"
    female = "female"
    other = "other"


class DayOfWeek(StrEnum):
    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"


class AdmissionCycleStatus(StrEnum):
    planning = "planning"
    open = "open"
    closed = "closed"
    archived = "archived"


class EnquiryStatus(StrEnum):
    """A funnel stage, not a formality: a school takes 800 enquiries to fill
    120 seats, and conversion by source is a number management asks for
    (ERP_BLUEPRINT §5.1.7)."""

    new = "new"
    contacted = "contacted"
    interested = "interested"
    application_form_issued = "application_form_issued"
    converted = "converted"
    not_interested = "not_interested"
    lost_to_competitor = "lost_to_competitor"
    invalid = "invalid"


class EnquirySource(StrEnum):
    walk_in = "walk_in"
    phone = "phone"
    website = "website"
    referral = "referral"
    alumni = "alumni"
    hoarding = "hoarding"
    digital_ad = "digital_ad"
    other = "other"


class EnquiryChannel(StrEnum):
    """How one interaction in the follow-up log happened."""

    phone = "phone"
    visit = "visit"
    email = "email"
    whatsapp = "whatsapp"
    sms = "sms"


class ApplicationStatus(StrEnum):
    """The pipeline of ERP_BLUEPRINT §5.1.7.

    Forward moves are permission-gated; backward moves are allowed but always
    audited with a reason, because a real admissions office does reopen
    decisions and a system that forbids it just gets a second application
    record instead.
    """

    draft = "draft"
    submitted = "submitted"
    under_document_verification = "under_document_verification"
    documents_verified = "documents_verified"
    documents_rejected = "documents_rejected"
    assessment_scheduled = "assessment_scheduled"
    assessment_completed = "assessment_completed"
    interview_scheduled = "interview_scheduled"
    interview_completed = "interview_completed"
    decision_pending = "decision_pending"
    admitted = "admitted"
    waitlisted = "waitlisted"
    rejected = "rejected"
    offer_issued = "offer_issued"
    offer_accepted = "offer_accepted"
    offer_expired = "offer_expired"
    fee_paid = "fee_paid"
    enrolled = "enrolled"
    withdrawn_by_parent = "withdrawn_by_parent"
    cancelled_after_admission = "cancelled_after_admission"


class AdmissionCategory(StrEnum):
    """Why this applicant might be treated differently. Sibling and staff-ward
    are claims until verified against real records (§5.1.9(6))."""

    general = "general"
    sibling = "sibling"
    staff_ward = "staff_ward"
    management = "management"
    rte = "rte"
    sports = "sports"
    alumni_child = "alumni_child"


class CasteCategory(StrEnum):
    general = "general"
    obc = "obc"
    sc = "sc"
    st = "st"
    ews = "ews"


class AssessmentType(StrEnum):
    """§5.1.2(4): assessment differs sharply by age. Nursery is an observation,
    class 6 is a written paper, class 11 is a previous-board result — one rigid
    "test marks" field fits none of them well."""

    written_test = "written_test"
    readiness_observation = "readiness_observation"
    previous_result_review = "previous_result_review"


class AssessmentStatus(StrEnum):
    scheduled = "scheduled"
    completed = "completed"
    absent = "absent"
    cancelled = "cancelled"


class InterviewRecommendation(StrEnum):
    strong_admit = "strong_admit"
    admit = "admit"
    waitlist = "waitlist"
    reject = "reject"


class DecisionOutcome(StrEnum):
    admitted = "admitted"
    waitlisted = "waitlisted"
    rejected = "rejected"


class OfferStatus(StrEnum):
    issued = "issued"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"
    withdrawn = "withdrawn"


class WaitlistStatus(StrEnum):
    waiting = "waiting"
    offered = "offered"
    converted = "converted"
    lapsed = "lapsed"
    withdrawn = "withdrawn"


class ApplicationFeePurpose(StrEnum):
    """§5.1.9(15): the application fee is non-refundable, the admission fee is
    refundable per the policy recorded on the cycle. Keeping them apart is what
    makes that enforceable rather than a matter of memory."""

    application_fee = "application_fee"
    admission_fee = "admission_fee"


class PaymentStatus(StrEnum):
    paid = "paid"
    voided = "voided"
    refunded = "refunded"


class FeeHeadType(StrEnum):
    """What kind of charge this is. `optional` is the one that matters
    operationally: transport and meals are billed only to who opted in, and a
    plan that cannot say so ends up charging every child for the bus."""

    recurring = "recurring"
    one_time = "one_time"
    optional = "optional"


class FeeFrequency(StrEnum):
    monthly = "monthly"
    one_time = "one_time"


class ConcessionType(StrEnum):
    sibling = "sibling"
    staff_ward = "staff_ward"
    rte = "rte"
    management = "management"
    scholarship = "scholarship"
    other = "other"


class ConcessionStatus(StrEnum):
    """§5.5.9: a concession affects money only once someone approved it, and
    who approved it is exactly what an audit asks."""

    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class VehicleStatus(StrEnum):
    """ERP_BLUEPRINT §5.6.7. Only `active` may carry children: the other three
    are the reasons a bus is off the road, kept distinct because "in the
    workshop this week" and "sold" are not the same operational fact."""

    active = "active"
    under_maintenance = "under_maintenance"
    grounded = "grounded"
    retired = "retired"


class VehicleOwnership(StrEnum):
    owned = "owned"
    hired = "hired"


class RouteStatus(StrEnum):
    planned = "planned"
    active = "active"
    suspended = "suspended"
    closed = "closed"


class TransportDirection(StrEnum):
    """Which legs of the journey a child rides. `both` is the ordinary case."""

    pickup = "pickup"
    drop = "drop"
    both = "both"


class TransportAssignmentStatus(StrEnum):
    """§5.6.7. `ended` is not a delete: the row stays so the history of who rode
    which bus survives, and only the billing stops (§5.6.9)."""

    requested = "requested"
    active = "active"
    suspended = "suspended"
    ended = "ended"


class Channel(StrEnum):
    """§0.11: email only for v1. The other two exist so the provider interface
    has something to be an interface *to*, and stay disabled per school until
    DLT registration exists — not so that a half-built SMS path can be
    switched on by accident."""

    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"


class MessageCategory(StrEnum):
    """What a message is about, which is what opt-out is decided against.

    §5.9.9 draws the line: informational messages respect an opt-out, statutory
    and emergency ones override it. `MANDATORY_CATEGORIES` in
    `services/comms.py` is that line, written down.
    """

    emergency = "emergency"
    attendance = "attendance"
    fees = "fees"
    examination = "examination"
    transport = "transport"
    admission = "admission"
    hr = "hr"
    general = "general"


class MessageStatus(StrEnum):
    """§5.9.7, minus `sending` as a resting state: dispatch is a job, so a
    message is either waiting to be picked up or has been."""

    draft = "draft"
    scheduled = "scheduled"
    sending = "sending"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class DeliveryStatus(StrEnum):
    """§5.9.7, trimmed to the states an SMTP send can actually reach.

    `delivered`, `read` and `bounced` need a provider webhook to observe, and
    three statuses nothing can ever set would be a delivery report that lies
    by omission. They belong with the webhook that reports them.
    """

    queued = "queued"
    sent = "sent"
    failed = "failed"
    opted_out = "opted_out"
