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
