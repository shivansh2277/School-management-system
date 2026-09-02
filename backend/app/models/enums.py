from enum import StrEnum


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
