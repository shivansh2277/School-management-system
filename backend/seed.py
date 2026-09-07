"""Idempotent demo data — BLUEPRINT §15.

`make seed` wipes every table and rebuilds from a fixed RNG seed, so running it
twice in a row leaves an identical database. Safe immediately before a demo.
"""

from __future__ import annotations

import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.core.document_types import DEFAULT_TYPES
from app.core.permissions import LEGACY_ROLE_MAP
from app.services import jobs as jobs_svc
from app.services import audit as audit_svc
from app.services import fee_setup
from app.services import fees as fees_svc
from app.services import admission as admission_svc
from app.services import grading
from app.services import hr as hr_svc
from app.services import staff_leave as staff_leave_svc
from app.services import schemes as schemes_svc
from app.services import rbac
from app.models import (
    AcademicYear,
    AcademicYearStatus,
    Attendance,
    Enrolment,
    AttendanceStatus,
    ClassSection,
    ClassSubjectTeacher,
    DocumentType,
    CustomField,
    Department,
    LeaveTypeDef,
    AdmissionCycle,
    AdmissionCycleStatus,
    CustomFieldType,
    CycleClassConfig,
    Enquiry,
    EnquirySource,
    EnquiryStatus,
    GuardianRelation,
    OwnerType,
    DayOfWeek,
    Exam,
    ExamSchedule,
    FeeFrequency,
    FeeHead,
    FeeHeadType,
    FeePlan,
    FeePlanItem,
    Gender,
    Holiday,
    Homework,
    HomeworkSubmission,
    Mark,
    Notice,
    NoticeAudience,
    Guardian,
    StudentGuardian,
    School,
    Student,
    SchoolPeriod,
    Subject,
    Employee,
    TimetableSlot,
    Role,
    RolePermission,
    ScopeType,
    User,
    UserRole,
    UserRoleAssignment,
)

ACADEMIC_YEAR = "2025-26"
CASHIER_LOGIN = "counter@sunrisepublic.edu"
SCHOOL_CODE = "SPS"
TODAY = date(2026, 9, 1)  # deterministic "today" so the seeded window never drifts

# Delete children before parents. ClassSection must go before Employee because
# class_sections.class_teacher_id references it — SQLite does not enforce
# foreign keys by default, so only Postgres catches a wrong order here.
# (class, seats, min age, max age on 31 March, written test, interview)
ADMISSION_CLASSES = [
    ("1", 40, "5.5", "7.0", False, True),
    ("6", 20, "10.0", "12.0", True, True),
    ("9", 15, "13.0", "15.0", True, False),
]

# A funnel that looks like a real one: most enquiries never become anything.
ENQUIRIES = [
    ("Ramesh Gupta", "9811100001", "Aarav Gupta", "1", EnquirySource.walk_in, EnquiryStatus.new),
    ("Neha Saxena", "9811100002", "Ira Saxena", "1", EnquirySource.website, EnquiryStatus.contacted),
    ("Imran Qureshi", "9811100003", "Zoya Qureshi", "6", EnquirySource.referral, EnquiryStatus.interested),
    ("Deepak Rawat", "9811100004", "Kabir Rawat", "6", EnquirySource.hoarding, EnquiryStatus.application_form_issued),
    ("Sunita Pandey", "9811100005", "Myra Pandey", "9", EnquirySource.phone, EnquiryStatus.not_interested),
    ("Alok Tiwari", "9811100006", "Vivaan Tiwari", "9", EnquirySource.digital_ad, EnquiryStatus.lost_to_competitor),
]

SUBJECTS = [
    ("English", "ENG"),
    ("Hindi", "HIN"),
    ("Mathematics", "MAT"),
    ("Science", "SCI"),
    ("Social Science", "SST"),
    ("Computer", "CMP"),
]

# One class teacher per section, plus subject teachers. TCH001 is first
# because the walkthrough in BLUEPRINT section 13 depends on them
# class-teaching 10-A and teaching it Mathematics.
# (name, qualification, department code, designation)
TEACHER_NAMES = [
    ("Anita Sharma", "M.Sc. Mathematics, B.Ed.", "SCI", "PGT"),
    ("Rajesh Verma", "M.A. English, B.Ed.", "LANG", "PGT"),
    ("Sunita Yadav", "M.A. Hindi, B.Ed.", "LANG", "TGT"),
    ("Praveen Mishra", "M.Sc. Physics, B.Ed.", "SCI", "PGT"),
    ("Kavita Singh", "M.A. History, B.Ed.", "HUM", "TGT"),
    ("Deepak Gupta", "MCA", "SCI", "TGT"),
    ("Neha Tiwari", "M.Sc. Chemistry, B.Ed.", "SCI", "PGT"),
    ("Amit Pandey", "M.A. Political Science, B.Ed.", "HUM", "TGT"),
    ("Ritu Srivastava", "M.Sc. Biology, B.Ed.", "SCI", "TGT"),
    ("Vikas Dubey", "M.A. Sanskrit, B.Ed.", "LANG", "TGT"),
    ("Pooja Awasthi", "B.Ed., Primary", "PRI", "PRT"),
    ("Sandeep Rastogi", "M.Com., B.Ed.", "HUM", "TGT"),
]

# A Lucknow private school's staff entitlement. Rows, not constants: §3.15 puts
# per-school configuration in tables, and a school that gives 15 casual days
# changes a number on a screen.
LEAVE_TYPES = [
    ("CL", "Casual Leave", Decimal(12), True),
    ("SL", "Sick Leave", Decimal(10), True),
    ("EL", "Earned Leave", Decimal(15), True),
    ("LWP", "Leave Without Pay", Decimal(0), False),
]

DEPARTMENTS = [
    ("SCI", "Science and Mathematics"),
    ("LANG", "Languages"),
    ("HUM", "Humanities"),
    ("PRI", "Primary"),
    ("ADM", "Administration"),
]

# Classes 10 down to 1, one section each. 10-A first so it keeps the lowest
# admission numbers, which the demo walkthrough uses.
CLASS_NAMES = ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]
STUDENTS_PER_SECTION = 10

FIRST_NAMES = [
    "Aarav", "Ishita", "Rohan", "Ananya", "Kabir", "Meera", "Arjun", "Sanya",
    "Vivaan", "Diya", "Aditya", "Riya", "Kartik", "Nisha", "Yash", "Priya",
    "Harsh", "Tanvi", "Nikhil", "Aisha", "Manav", "Pooja", "Rahul", "Sneha",
    "Devansh", "Kritika", "Shaurya", "Anvi", "Reyansh", "Myra", "Atharv",
    "Saanvi", "Ayaan", "Navya", "Krish", "Ira", "Dhruv", "Aadhya", "Om",
    "Kiara",
]


def student_name(n: int) -> str:
    """Deterministic and non-repeating across 100 students: 40 first names
    against 8 surnames gives 320 distinct combinations."""
    return f"{FIRST_NAMES[n % len(FIRST_NAMES)]} {SURNAMES[(n // len(FIRST_NAMES)) % len(SURNAMES)]}"
SURNAMES = [
    "Sharma", "Verma", "Yadav", "Mishra", "Singh", "Gupta", "Tiwari", "Pandey",
]
PARENT_FIRST = [
    "Suresh", "Meenakshi", "Ramesh", "Kalpana", "Vinod", "Shalini", "Dinesh",
    "Rekha", "Alok", "Sarita", "Mahesh", "Nirmala", "Sanjay", "Usha", "Ajay",
    "Geeta", "Naresh", "Kamla", "Rakesh", "Sudha", "Prakash", "Bindu",
]
OCCUPATIONS = ["Shopkeeper", "Bank Officer", "Employee", "Farmer", "Engineer", "Homemaker"]

ROOMS = ["R-101", "R-102", "R-201", "R-202", "Lab-1", "Lab-2"]

# (title, subject code). Paired deliberately: a rotation over the subject list
# filed "Write a Python program" under Social Science, which is the first thing
# a reviewer notices on the homework screen.
HOMEWORK_TITLES = [
    ("Chapter 4 exercise questions", "MAT"),
    ("Write a paragraph on your favourite festival", "ENG"),
    ("Solve the quadratic equations worksheet", "MAT"),
    ("Draw and label the human digestive system", "SCI"),
    ("Answer the map-work questions", "SST"),
    ("Write a Python program to reverse a string", "CMP"),
    ("Summarise the poem in your own words", "HIN"),
    ("Revision problems from last week", "SCI"),
]

NOTICES = [
    ("Annual Sports Day on 12 October",
     "All students must report by 7:30 AM in sports uniform.", NoticeAudience.all),
    ("Guardian-Employee Meeting this Saturday",
     "PTM will be held from 10:00 AM to 1:00 PM.", NoticeAudience.parents),
    ("Library books due",
     "Return all borrowed books before the half-yearly exams.", NoticeAudience.students),
    ("Staff meeting on Friday",
     "All teaching staff to assemble in the conference room at 3:00 PM.", NoticeAudience.teachers),
    ("Half-yearly exam datesheet released",
     "The datesheet is on the notice board outside the office.", NoticeAudience.all),
    ("Class 10-A extra Mathematics class",
     "Extra class every Tuesday from 2:00 PM to 3:00 PM.", NoticeAudience.class_),
]

# The CBSE scale, with the word the report card actually prints alongside the
# code. A school edits these on the grading-scale screen; they are a starting
# point, not a constant.
GRADE_BANDS = [
    (91, "A1", "Outstanding"), (81, "A2", "Excellent"),
    (71, "B1", "Very good"), (61, "B2", "Good"),
    (51, "C1", "Fair"), (41, "C2", "Average"),
    (33, "D", "Below average"), (0, "E", "Needs improvement"),
]

PERIOD_TIMES = [
    (time(8, 0), time(9, 0)),
    (time(9, 0), time(10, 0)),
    (time(10, 0), time(11, 0)),
    (time(11, 30), time(12, 30)),
    (time(12, 30), time(13, 30)),
    (time(13, 30), time(14, 0)),
]

DEMO_PASSWORDS = {
    UserRole.admin: "Admin@123",
    UserRole.teacher: "Teacher@123",
    UserRole.student: "Student@123",
    UserRole.parent: "Parent@123",
}


def school_days(end: date, count: int) -> list[date]:
    """The `count` most recent Mon-Sat days ending on or before `end`, oldest first."""
    days, cursor = [], end
    while len(days) < count:
        if cursor.weekday() != 6:  # skip Sunday
            days.append(cursor)
        cursor -= timedelta(days=1)
    return sorted(days)


def month_back(anchor: date, months: int) -> tuple[int, int]:
    """(month, year) `months` calendar months before `anchor`."""
    index = anchor.year * 12 + (anchor.month - 1) - months
    return index % 12 + 1, index // 12


def _stamp_tenant(db: Session, school_id: int) -> None:
    """Fill in `school_id` on anything added without one.

    Every seeded row belongs to the one demo school, so stamping them in a
    single flush hook is both shorter and safer than threading the id through
    forty constructors, where one omission would fail at COMMIT with an opaque
    NOT NULL error. Seed-only: application code sets the tenant explicitly.
    """
    from sqlalchemy import event

    from app.models.base import TenantBase

    @event.listens_for(db, "before_flush")
    def _fill(session, _ctx, _instances):  # pragma: no cover - test-time hook
        for obj in session.new:
            if isinstance(obj, TenantBase) and obj.school_id is None:
                obj.school_id = school_id


def wipe(db: Session) -> None:
    """Empty every table.

    This used to be a hand-ordered list of models, which went stale the moment
    a migration added a table nobody remembered to add to it: seeding a
    migrated Postgres database failed on `document_types` still referencing
    `schools`. So the order came from `sorted_tables` instead — until
    `employees` and `departments` began pointing at each other (a department
    has a head, an employee has a department). A cycle has no topological
    order, so SQLAlchemy drops those foreign keys from its sort and warns that
    it may raise instead in a later release. The order it produced was then
    correct only by luck.

    On Postgres, `TRUNCATE ... CASCADE` is one statement that does not need an
    order at all, which is the right answer to a cycle rather than a second
    hand-maintained list of the columns to null first. SQLite has no CASCADE
    and does not enforce foreign keys anyway, so the delete loop stands there.
    """
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        # No sort at all: asking for one is what emits the cycle warning, and
        # TRUNCATE CASCADE does not want an order.
        names = ", ".join(f'"{t}"' for t in Base.metadata.tables)
        db.execute(text(f"TRUNCATE {names} CASCADE"))
    else:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    db.commit()


def seed(db: Session) -> None:  # noqa: PLR0915 - linear script; splitting it would only hide it
    rng = random.Random(20260901)
    wipe(db)

    school = School(
        code=SCHOOL_CODE,
        name="Sunrise Public School",
        address="Sector 5, Vikas Nagar",
        city="Lucknow",
        state="Uttar Pradesh",
        phone="+91 522 400 1234",
        email="office@sunrisepublic.edu",
        primary_color="#5B4BE0",
        board="CBSE",
    )
    db.add(school)
    db.flush()

    start_year = int(ACADEMIC_YEAR.split("-")[0])
    year = AcademicYear(
        school_id=school.id,
        code=ACADEMIC_YEAR,
        start_date=date(start_year, 4, 1),
        end_date=date(start_year + 1, 3, 31),
        status=AcademicYearStatus.active,
        is_current=True,
    )
    db.add(year)
    db.flush()
    # `year` gets rebound to a calendar year further down; hold the id.
    academic_year_id = year.id

    # From here on every row is stamped with this school automatically.
    _stamp_tenant(db, school.id)

    # This school's copy of the roles that ship with the product.
    roles = rbac.install_system_roles(db, school.id)
    jobs_svc.install_schedules(db)

    # The document checklist a new tenant starts with. Idempotent, because the
    # migration installs these too and the seed runs on top of a migrated
    # database as often as a freshly created one.
    have = set(
        db.scalars(
            select(DocumentType.code).where(DocumentType.school_id == school.id)
        )
    )
    for i, (code, name, applies, mand, cat, exp, conf) in enumerate(DEFAULT_TYPES):
        if code in have:
            continue
        db.add(
            DocumentType(
                code=code,
                name=name,
                applies_to=OwnerType(applies),
                is_mandatory=mand,
                required_if_category=cat,
                has_expiry=exp,
                is_confidential=conf,
                sort_order=(i + 1) * 10,
            )
        )
    db.flush()

    # Two school-defined attributes, so the demo shows what level 2 of the
    # customization ladder (§3.15) actually looks like on a student form.
    if not db.scalar(select(CustomField.id).where(CustomField.school_id == school.id)):
        db.add_all(
            [
                CustomField(
                    entity=OwnerType.student,
                    key="father_occupation",
                    label="Father's occupation",
                    field_type=CustomFieldType.text,
                    sort_order=10,
                ),
                CustomField(
                    entity=OwnerType.student,
                    key="house",
                    label="House",
                    field_type=CustomFieldType.select,
                    options=["Ganga", "Yamuna", "Saraswati", "Narmada"],
                    sort_order=20,
                ),
            ]
        )
        db.flush()

    # Built through the real service so the band rules the API enforces are the
    # rules the demo data obeys.
    if grading.active_scale(db, school.id) is None:
        grading.create(
            db,
            school.id,
            name="CBSE",
            bands=[(Decimal(p), g, d) for p, g, d in GRADE_BANDS],
            activate=True,
        )

    # --- people -----------------------------------------------------------
    admin = User(
        role=UserRole.admin,
        login_id="admin@sunrisepublic.edu",
        password_hash=hash_password(DEMO_PASSWORDS[UserRole.admin]),
        full_name="Office Administrator",
        email="admin@sunrisepublic.edu",
        phone="+91 522 400 1234",
    )
    db.add(admin)

    # A cashier, so the segregation of duties in §5.5.9 is demonstrable rather
    # than theoretical: this account may take money and may not cancel it.
    cashier = User(
        role=UserRole.admin,
        login_id=CASHIER_LOGIN,
        password_hash=hash_password(DEMO_PASSWORDS[UserRole.admin]),
        full_name="Fee Counter Clerk",
        email=CASHIER_LOGIN,
        phone="+91 522 400 1235",
    )
    db.add(cashier)

    teachers: list[Employee] = []
    departments = {}
    for code, dept_name in DEPARTMENTS:
        existing = db.scalar(
            select(Department).where(
                Department.school_id == school.id, Department.code == code
            )
        )
        departments[code] = existing or hr_svc.create_department(
            db, school.id, code=code, name=dept_name
        )
    db.flush()

    for i, (name, qual, dept_code, designation) in enumerate(TEACHER_NAMES, start=1):
        emp = f"TCH{i:03d}"
        u = User(
            role=UserRole.teacher,
            login_id=emp,
            password_hash=hash_password(DEMO_PASSWORDS[UserRole.teacher]),
            full_name=name,
            email=f"{emp.lower()}@sunrisepublic.edu",
            phone=f"98765{20000 + i:05d}",
        )
        db.add(u)
        db.flush()
        t = Employee(
            user_id=u.id,
            employee_code=emp,
            qualification=qual,
            joining_date=date(2019 + (i % 5), 6, 1),
            department_id=departments[dept_code].id,
            designation=designation,
        )
        db.add(t)
        teachers.append(t)
    db.flush()

    # A head per teaching department, so §5.3.8's department scoping has
    # something real to point at rather than a nullable column nothing fills.
    for code in ("SCI", "LANG", "HUM", "PRI"):
        dept = departments[code]
        if dept.head_employee_id is None:
            first = next(
                (
                    t
                    for t, (_, _, dc, _) in zip(teachers, TEACHER_NAMES, strict=True)
                    if dc == code
                ),
                None,
            )
            if first is not None:
                hr_svc.set_head(db, dept, first)
    db.flush()

    for code, name, quota, paid in LEAVE_TYPES:
        if not db.scalar(
            select(LeaveTypeDef).where(
                LeaveTypeDef.school_id == school.id, LeaveTypeDef.code == code
            )
        ):
            staff_leave_svc.create_type(
                db, school.id, code=code, name=name, annual_quota=quota, is_paid=paid
            )
    db.flush()

    subjects = [Subject(name=n, code=c) for n, c in SUBJECTS]
    db.add_all(subjects)
    db.flush()

    # Order matters: sections[0] is 10-A, which the §13 walkthrough uses.
    sections = [
        ClassSection(
            class_name=name,
            section="A",
            academic_year_id=year.id,
            class_teacher_id=teachers[i].id,
            capacity=STUDENTS_PER_SECTION + 10,
            room=ROOMS[i % len(ROOMS)],
        )
        for i, name in enumerate(CLASS_NAMES)
    ]
    db.add_all(sections)
    db.flush()

    # Who teaches what, where — assigned by subject, which is both how a real
    # school staffs itself and what makes the load come out even.
    #
    # Two teachers cover each subject and split the ten sections between them,
    # so every teacher carries exactly five (section, subject) pairs. With six
    # subjects over thirty teaching periods a week that is 25 periods each, and
    # the load chart's spread is 0.
    #
    # The previous scheme gave each section three teachers taking two subjects
    # apiece. That cannot balance: thirty teacher-section assignments over
    # twelve teachers is 2.5 each, so six people ended up on three sections and
    # six on two — 30 periods against 18, which is what the chart showed.
    #
    # Scoping stays a real boundary: each teacher is in five of the ten
    # sections, not all of them. The alternating split is what keeps TCH004 out
    # of 10-A, which `other_teacher` depends on.
    SUBJECT_TEACHERS = {
        "ENG": (1, 10),   # M.A. English, and the primary teacher
        "HIN": (2, 9),    # M.A. Hindi, and the Sanskrit teacher
        "MAT": (0, 11),   # M.Sc. Mathematics, and the M.Com.
        "SCI": (3, 6),    # Physics takes the even sections, Chemistry the odd
                          # (this way round keeps TCH004 out of 10-A, which the
                          # `other_teacher` fixture depends on)
        "SST": (4, 7),    # History and Political Science
        "CMP": (5, 8),    # MCA, and the Biology teacher — a small school does
    }                     # exactly this
    for si, sec in enumerate(sections):
        for qi, sub in enumerate(subjects):
            first, second = SUBJECT_TEACHERS[sub.code]
            # Alternating by (section + subject) gives each of the pair five
            # sections whichever way the parity falls.
            chosen = first if (si + qi) % 2 == 0 else second
            db.add(
                ClassSubjectTeacher(
                    class_section_id=sec.id,
                    subject_id=sub.id,
                    teacher_id=teachers[chosen].id,
                )
            )
    db.flush()

    students: list[Student] = []
    for si, sec in enumerate(sections):
        for r in range(1, STUDENTS_PER_SECTION + 1):
            n = si * STUDENTS_PER_SECTION + r  # 10-A takes the first numbers
            full_name = student_name(n - 1)
            # YYYY + 6-digit sequence, from the same counter the application
            # uses (ERP_BLUEPRINT section 0.21).
            adm = audit_svc.admission_number(db, school.id, 2024)
            u = User(
                role=UserRole.student,
                login_id=adm,
                password_hash=hash_password(DEMO_PASSWORDS[UserRole.student]),
                full_name=full_name,
            )
            db.add(u)
            db.flush()
            s = Student(
                user_id=u.id,
                admission_no=adm,
                dob=date(2010 - si, 1 + (n % 12), 1 + (n % 27)),
                gender=Gender.female if n % 2 == 0 else Gender.male,
                address=f"House {100 + n}, Vikas Nagar, Lucknow",
                admission_date=date(2024, 4, 1),
            )
            db.add(s)
            db.flush()
            # Class and roll number are facts about a year, not about the
            # student (ERP_BLUEPRINT §3.2).
            db.add(
                Enrolment(
                    student_id=s.id,
                    academic_year_id=year.id,
                    class_section_id=sec.id,
                    roll_no=r,
                    joined_on=date(2024, 4, 1),
                )
            )
            students.append(s)
    db.flush()

    # 2 parents with two children each (siblings in 10-A), then one per
    # remaining student. The sibling pair exists so the parent app's child
    # switcher has something to switch between.
    sibling_pairs = [(students[0], students[1]), (students[2], students[3])]
    singles = students[4:]
    parents: list[Guardian] = []
    for i in range(1, len(singles) + 3):
        mobile = f"98765{i:05d}"
        u = User(
            role=UserRole.parent,
            login_id=mobile,
            password_hash=hash_password(DEMO_PASSWORDS[UserRole.parent]),
            full_name=(
                f"{PARENT_FIRST[(i - 1) % len(PARENT_FIRST)]} "
                f"{SURNAMES[(i - 1) % len(SURNAMES)]}"
            ),
            phone=mobile,
        )
        db.add(u)
        db.flush()
        p = Guardian(user_id=u.id, occupation=OCCUPATIONS[i % len(OCCUPATIONS)])
        db.add(p)
        parents.append(p)
    db.flush()

    for p, pair in zip(parents[:2], sibling_pairs, strict=True):
        for child in pair:
            db.add(
                StudentGuardian(
                    guardian_id=p.id,
                    student_id=child.id,
                    relation=GuardianRelation.father,
                    is_primary=True,
                )
            )
    for p, child in zip(parents[2:], singles, strict=True):
        db.add(
            StudentGuardian(
                guardian_id=p.id,
                student_id=child.id,
                relation=GuardianRelation.father,
                is_primary=True,
            )
        )
    db.flush()

    # --- timetable --------------------------------------------------------
    # Built greedily against the same rules the API enforces: a teacher in one
    # place at a time, a room hosting one class, a section taught one thing.
    # v0 seeded this blindly and produced 144 teacher double-bookings and 36
    # room clashes, which made every conflict report noise. Where no valid
    # placement exists the slot is left empty on purpose — §5.7.9 wants an
    # incomplete timetable to be visibly incomplete, and `/admin/timetable/
    # completeness` reports exactly those gaps.
    periods = [
        SchoolPeriod(
            period_no=i + 1,
            start_time=start,
            end_time=end,
            is_break=(i + 1 == 6),
            name="Break" if i + 1 == 6 else None,
        )
        for i, (start, end) in enumerate(PERIOD_TIMES)
    ]
    db.add_all(periods)
    db.flush()

    cst = {
        (row.class_section_id, row.subject_id): row.teacher_id
        for row in db.query(ClassSubjectTeacher).all()
    }
    # Marks record the user who entered them, not the employment record: an
    # exam controller entering a correction may hold no teaching post.
    teacher_user_id = {e.id: e.user_id for e in db.query(Employee).all()}
    busy_teacher: set[tuple] = set()   # (day, period, teacher)
    busy_room: set[tuple] = set()      # (day, period, room)
    placed = skipped = 0

    # Each section gets each subject the same number of times a week — thirty
    # teaching slots over six subjects is five each. Tracking what each section
    # still owes, and always placing whichever subject is furthest behind,
    # keeps the periods even without a scheduling algorithm: a greedy "first
    # subject whose teacher is free" drifts, and that drift is what put two
    # teachers on 30 periods while ten sat on 24.
    per_subject = (len(periods) - sum(1 for p in periods if p.is_break)) * len(
        DayOfWeek
    ) // len(subjects)
    owed = {
        (sec.id, sub.id): per_subject for sec in sections for sub in subjects
    }

    for period in periods:
        if period.is_break:
            continue
        for day in DayOfWeek:
            for si, sec in enumerate(sections):
                # Furthest behind first; the offset breaks ties differently in
                # each section so they do not all chase the same subject at the
                # same hour and collide on its teacher.
                candidates = sorted(
                    subjects,
                    key=lambda sub, sec=sec, si=si, p=period: (
                        -owed[(sec.id, sub.id)],
                        (subjects.index(sub) + si + p.period_no) % len(subjects),
                    ),
                )
                for sub in candidates:
                    if owed[(sec.id, sub.id)] <= 0:
                        continue
                    teacher_id = cst.get((sec.id, sub.id))
                    if teacher_id is None:
                        continue
                    if (day, period.id, teacher_id) in busy_teacher:
                        continue
                    room = ROOMS[(si + period.period_no) % len(ROOMS)]
                    if (day, period.id, room) in busy_room:
                        room = None  # taught in their own classroom instead
                    db.add(
                        TimetableSlot(
                            class_section_id=sec.id,
                            day_of_week=day,
                            period_id=period.id,
                            subject_id=sub.id,
                            teacher_id=teacher_id,
                            room=room,
                        )
                    )
                    busy_teacher.add((day, period.id, teacher_id))
                    if room:
                        busy_room.add((day, period.id, room))
                    owed[(sec.id, sub.id)] -= 1
                    placed += 1
                    break
                else:
                    skipped += 1
    db.flush()

    # Class and roll number now live on the enrolment, so look them up once
    # rather than per student per loop.
    enrolment_of = {e.student_id: e for e in db.query(Enrolment).all()}

    # --- holidays: the register and the percentage both need them ----------
    # Two inside the attendance window, so the denominator is provably not
    # "every Monday to Saturday".
    holiday_days = {TODAY - timedelta(days=21), TODAY - timedelta(days=40)}
    for i, day in enumerate(sorted(holiday_days)):
        db.add(
            Holiday(
                academic_year_id=academic_year_id,
                date=day,
                name=["Founder's Day", "Local Festival"][i],
            )
        )
    db.flush()

    # --- attendance: 60 school days, ~92/5/3 with per-student variation ----
    class_teacher_of = {s.id: s.class_teacher_id for s in sections}
    days = [d for d in school_days(TODAY, 60) if d not in holiday_days]
    for s in students:
        marker = class_teacher_of[enrolment_of[s.id].class_section_id]
        absent_rate = 0.02 + (enrolment_of[s.id].roll_no % 4) * 0.02  # varies so percentages differ
        for d in days:
            roll = rng.random()
            if roll < absent_rate:
                status = AttendanceStatus.absent
            elif roll < absent_rate + 0.03:
                status = AttendanceStatus.leave
            else:
                status = AttendanceStatus.present
            db.add(
                Attendance(
                    enrolment_id=enrolment_of[s.id].id,
                    date=d,
                    status=status,
                    marked_by=marker,
                    remarks=None,
                )
            )
    db.flush()

    # --- assessment scheme, exams and marks -------------------------------
    # The scheme comes first: an exam cites the report-card column it fills,
    # and the column says what the paper is out of. Built through the service,
    # so a defect in the scheme rules breaks the seed rather than only a test
    # (the same bargain the fee and timetable seeding already makes).
    scheme = schemes_svc.active_scheme(db, academic_year_id)
    if scheme is None:
        scheme = schemes_svc.create(
            db,
            school.id,
            academic_year_id,
            name="CBSE 2026-27",
            rows=schemes_svc.CBSE_DEFAULT,
            activate=True,
        )

    # Term 1 is examined; Term 2 has its columns defined and nothing entered,
    # which is what a school actually looks like in the middle of a year.
    term1 = schemes_svc.components(db, scheme.id, term="Term 1")
    exams = []
    for offset, component in enumerate(term1):
        exam = Exam(
            name=f"Term 1 - {component.name}",
            term=component.term,
            start_date=TODAY - timedelta(days=70 - offset * 14),
            end_date=TODAY - timedelta(days=64 - offset * 14),
            scheme_component_id=component.id,
        )
        db.add(exam)
        exams.append((exam, component))
    db.flush()

    for exam, component in exams:
        for sec in sections:
            for qi, sub in enumerate(subjects):
                sched = ExamSchedule(
                    exam_id=exam.id,
                    class_section_id=sec.id,
                    subject_id=sub.id,
                    exam_date=exam.start_date + timedelta(days=qi),
                    start_time=time(9, 0),
                    max_marks=component.max_marks,
                )
                db.add(sched)
                db.flush()
                for s in (x for x in students if enrolment_of[x.id].class_section_id == sec.id):
                    # ability band per student keeps all four donut buckets populated
                    base = 30 + (enrolment_of[s.id].roll_no * 8) % 60
                    percent = max(0, min(100, base + rng.randint(-6, 12)))
                    score = fee_setup.money(
                        component.max_marks * Decimal(percent) / Decimal(100)
                    )
                    db.add(
                        Mark(
                            exam_schedule_id=sched.id,
                            student_id=s.id,
                            marks_obtained=score,
                            entered_by=teacher_user_id[cst[(sec.id, sub.id)]],
                        )
                    )
    db.flush()

    # --- homework ---------------------------------------------------------
    by_code = {s.code: s for s in subjects}
    for i, (title, code) in enumerate(HOMEWORK_TITLES):
        sec = sections[i % len(sections)]
        sub = by_code[code]
        assigned = TODAY - timedelta(days=14 - i)
        hw = Homework(
            class_section_id=sec.id,
            subject_id=sub.id,
            teacher_id=cst[(sec.id, sub.id)],
            title=title,
            description="Complete the work neatly in your notebook and submit on time.",
            assigned_date=assigned,
            due_date=assigned + timedelta(days=3),
        )
        db.add(hw)
        db.flush()
        roster = [x for x in students if enrolment_of[x.id].class_section_id == sec.id]
        for s in roster[: 5 + (i % 3)]:  # some submit, some do not
            late = (i + enrolment_of[s.id].roll_no) % 5 == 0
            offset = 4 if late else 1  # late ones land after due_date
            db.add(
                HomeworkSubmission(
                    homework_id=hw.id,
                    student_id=s.id,
                    answer_text="Completed the exercise as instructed.",
                    submitted_at=datetime.combine(
                        assigned + timedelta(days=offset), time(18, 30), tzinfo=UTC
                    ),
                )
            )
    db.flush()

    # --- fees: the three months before the current one --------------------
    # Rises with the class, the way a real fee card does.
    fees = {
        name: Decimal(f"{1200 + int(name) * 160}.00") for name in CLASS_NAMES
    }

    # The catalogue that replaces the flat structure above: heads a school
    # actually itemises on a fee card, and one plan per class carrying them.
    heads = {}
    for code, name, kind in (
        ("TUITION", "Tuition Fee", FeeHeadType.recurring),
        ("DEV", "Development Fee", FeeHeadType.recurring),
        ("TRANSPORT", "Transport Fee", FeeHeadType.optional),
        ("ADMISSION", "Admission Fee", FeeHeadType.one_time),
    ):
        head = FeeHead(name=name, code=code, type=kind)
        db.add(head)
        heads[code] = head
    db.flush()

    for class_name, monthly in fees.items():
        # Development fee is a fifth of the card, the way most schools split it,
        # so the invoice has more than one line to prove the model.
        development = (monthly / 5).quantize(Decimal("0.01"))
        plan = FeePlan(
            academic_year_id=academic_year_id,
            name=f"Class {class_name} standard",
            class_name=class_name,
            items=[
                FeePlanItem(
                    school_id=school.id,
                    fee_head_id=heads["TUITION"].id,
                    amount=monthly - development,
                    frequency=FeeFrequency.monthly,
                ),
                FeePlanItem(
                    school_id=school.id,
                    fee_head_id=heads["DEV"].id,
                    amount=development,
                    frequency=FeeFrequency.monthly,
                ),
            ],
        )
        db.add(plan)
    db.flush()

    # The demo parent has two children, so the sibling rule has something to
    # act on and the concession register is not empty on a fresh install.
    fee_setup.apply_sibling_concessions(db, school.id)

    # Three months of history, billed through the real invoice generator
    # rather than by hand: a seed that fabricates rows cannot catch a defect in
    # the code that will produce them in production.
    for back in (3, 2, 1):
        month, year = month_back(TODAY, back)
        fees_svc.generate(db, month, year, school.id)

    # Collection: most families pay in full, some part-pay, some have not paid
    # at all. Deterministic from the roll number, so a demo walkthrough shows
    # the same student in the same state every time.
    for s in students:
        enrolment = enrolment_of[s.id]
        pattern = enrolment.roll_no % 3
        if pattern == 0:  # nothing paid — the defaulter list needs entries
            continue
        outstanding = fees_svc.outstanding_invoices(db, enrolment.id)
        for invoice in outstanding[:-1]:
            fees_svc.collect(
                db,
                enrolment.id,
                fees_svc.totals(db, invoice)["balance"],
                idempotency_key=f"seed-{invoice.id}",
                method="cash",
                received_at=datetime.combine(invoice.due_date, time(11, 0), tzinfo=UTC),
            )
        if pattern == 2 and outstanding:
            # Half of the latest month, so `partially_paid` and a receipt whose
            # allocation covers only part of an invoice both exist in demo data.
            latest = outstanding[-1]
            half = (fees_svc.totals(db, latest)["balance"] / 2).quantize(Decimal("0.01"))
            if half > 0:
                fees_svc.collect(
                    db,
                    enrolment.id,
                    half,
                    idempotency_key=f"seed-part-{latest.id}",
                    method="upi",
                    received_at=datetime.combine(latest.due_date, time(12, 0), tzinfo=UTC),
                )
    db.flush()

    # --- notices ----------------------------------------------------------
    for i, (title, body, audience) in enumerate(NOTICES):
        db.add(
            Notice(
                title=title,
                body=body,
                audience=audience,
                class_section_id=sections[0].id if audience == NoticeAudience.class_ else None,
                published_by=admin.id,
                published_at=datetime.combine(
                    TODAY - timedelta(days=len(NOTICES) - i), time(9, 0), tzinfo=UTC
                ),
            )
        )

    # --- admission: an open cycle with seats and a live enquiry register ----
    cycle = AdmissionCycle(
        academic_year_id=academic_year_id,
        name=f"Admissions {ACADEMIC_YEAR}",
        status=AdmissionCycleStatus.open,
        starts_on=date(start_year, 1, 5),
        ends_on=date(start_year, 3, 31),
        application_fee=Decimal("500.00"),
        late_fee=Decimal("250.00"),
        admission_fee_refund_policy=(
            "The application fee is non-refundable. The admission fee is "
            "refunded in full if the seat is declined before the session begins."
        ),
    )
    db.add(cycle)
    db.flush()
    for class_name, seats, min_age, max_age, test, interview in ADMISSION_CLASSES:
        db.add(
            CycleClassConfig(
                cycle_id=cycle.id,
                class_name=class_name,
                total_seats=seats,
                reserved_seats={"EWS": max(1, seats // 10)},
                age_on=date(start_year, 3, 31),
                min_age_years=Decimal(min_age),
                max_age_years=Decimal(max_age),
                requires_test=test,
                requires_interview=interview,
                required_document_codes=["birth_certificate", "photo", "address_proof"],
            )
        )
    for i, (name, mobile, child, klass, source, enq_status) in enumerate(ENQUIRIES):
        db.add(
            Enquiry(
                cycle_id=cycle.id,
                enquirer_name=name,
                mobile=mobile,
                child_name=child,
                class_of_interest=klass,
                source=source,
                status=enq_status,
                next_follow_up_on=(
                    None
                    if enq_status in admission_svc.CLOSED_ENQUIRY_STATUSES
                    else TODAY + timedelta(days=i % 5)
                ),
            )
        )
    db.flush()

    _assign_roles(db, roles, sections)
    db.commit()


def _assign_roles(db: Session, roles: dict, sections: list) -> None:
    """Give every seeded account the system role matching its primary role.

    Class teachers additionally get a `class_section`-scoped grant, which is
    what "Class Employee" actually is: the teacher role plus authority over one
    section (ERP_BLUEPRINT §3.5).
    """
    for user in db.scalars(select(User)):
        # One deliberate exception to the legacy map: the counter clerk holds
        # `fee_collector`, which has no void and no concession approval.
        code = (
            "fee_collector"
            if user.login_id == CASHIER_LOGIN
            else LEGACY_ROLE_MAP[user.role.value]
        )
        # Students and guardians hold their permissions over their own records
        # only. Granting them school-wide would let a parent read the admin
        # roster, since both hold students.profile.read.
        scope = (
            ScopeType.self_only
            if code in ("student", "guardian")
            else ScopeType.school
        )
        rbac.assign(db, user, roles[code], scope_type=scope)

    class_teacher_role = roles["teacher"]
    for sec in sections:
        if sec.class_teacher_id is None:
            continue
        teacher = db.get(Employee, sec.class_teacher_id)
        rbac.assign(
            db,
            teacher.user,
            class_teacher_role,
            scope_type=ScopeType.class_section,
            scope_id=sec.id,
        )
    db.flush()


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    print("Seeded Sunrise Public School demo data.")


if __name__ == "__main__":
    main()
