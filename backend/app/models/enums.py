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
    present = "present"
    absent = "absent"
    leave = "leave"


class NoticeAudience(StrEnum):
    all = "all"
    students = "students"
    parents = "parents"
    teachers = "teachers"
    class_ = "class"


class InvoiceStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"


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
