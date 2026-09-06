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
