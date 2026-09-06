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
