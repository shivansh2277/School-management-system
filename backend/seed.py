"""Idempotent demo data — BLUEPRINT §15.

`make seed` wipes every table and rebuilds from a fixed RNG seed, so running it
twice in a row leaves an identical database. Safe immediately before a demo.
"""

from __future__ import annotations

import os
import random
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.core.document_types import DEFAULT_TYPES
from app.core.message_templates import DEFAULT_TEMPLATES
from app.services import documents
from app.services import transport as transport_svc
from app.core.permissions import LEGACY_ROLE_MAP
from app.services import jobs as jobs_svc
from app.services import audit as audit_svc
from app.services import fee_setup
from app.services import fees as fees_svc
from app.services import admission as admission_svc
from app.services import grading
from app.services import hr as hr_svc
from app.services import payroll as payroll_svc
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
    Route,
    RouteStatus,
    TransportAssignmentStatus,
    TransportDirection,
    TransportFeeSlab,
    Vehicle,
    VehicleOwnership,
    EmployeeType,
    MessageCategory,
    MessageTemplate,
    Setting,
    Student,
    SchoolPeriod,
    Subject,
    Employee,
    TimetableSlot,
    ScopeType,
    User,
    UserRole,
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
    ("Environmental Studies", "EVS"),
    ("Art & Craft", "ART"),
    ("Sanskrit", "SAN"),
]

# What each stage is actually taught, following the CBSE pattern a Lucknow
# private school runs on.
#
# Every section used to hold the same six subjects, so class 1 was timetabled
# for Social Science and class 10 for none of the primary work - a curriculum
# that exists in no school. The two stages now differ the way they really do:
#
#   Primary (1-5)  Environmental Studies is the combined science-and-social
#                  subject at this stage, Computer is an introduction, and Art
#                  & Craft is timetabled rather than a free period.
#   Senior (6-10)  EVS splits into Science and Social Science, and Sanskrit
#                  comes in as the third language.
#
# Six per stage, and that number is load-bearing. Thirty teaching periods a
# week over six subjects is five each, and twelve teachers over two stages is
# exactly one specialist per stage per subject - which is what lets every
# section be taught in every period with nobody double-booked. A seventh
# subject (CBSE schools commonly also run Computer through 6-8) would divide
# 30 by 7 and leave the week ragged, so it is deliberately left out of the
# demo school rather than faked.
STAGE_SUBJECTS = {
    "primary": ["ENG", "HIN", "MAT", "EVS", "CMP", "ART"],
    "senior": ["ENG", "HIN", "MAT", "SCI", "SST", "SAN"],
}


def stage_of(class_name: str) -> str:
    """Which stage a class belongs to. Numeric names only, as CLASS_NAMES has."""
    return "primary" if int(class_name) <= 5 else "senior"

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
    # Drivers and the attendant are employees like anybody else (§5.6.6), so
    # they need a department rather than a table of their own.
    ("TRA", "Transport"),
]

# Two buses, three distance slabs and two routes. Small on purpose: the demo
# exists to prove the rules run, and a fleet of twelve would prove the same
# thing more slowly.
VEHICLES = [
    ("UP32AB1234", "Tata Starbus 40", 40),
    ("UP32CD5678", "Eicher Skyline 32", 32),
]
SLABS = [("0-5 km", "800.00"), ("5-10 km", "1100.00"), ("10-15 km", "1500.00")]
# (code, name, registration, [(stop, landmark, pickup, drop, slab index)])
ROUTES = [
    (
        "R1",
        "Gomti Nagar",
        "UP32AB1234",
        [
            ("Vibhuti Khand", "Fun Republic Mall", (6, 40), (14, 25), 0),
            ("Patrakarpuram", "Patrakarpuram Crossing", (6, 55), (14, 40), 0),
            ("Vinay Khand", "Lohia Park Gate 2", (7, 10), (14, 55), 1),
            ("Vikas Khand", "Ambedkar Park", (7, 25), (15, 10), 2),
        ],
    ),
    (
        "R2",
        "Alambagh and Krishna Nagar",
        "UP32CD5678",
        [
            ("Krishna Nagar", "Sadar Bazaar", (6, 45), (14, 30), 1),
            ("Alambagh Bus Station", "Alambagh Terminal", (7, 0), (14, 45), 1),
            ("Kanpur Road", "Phoenix Palassio", (7, 20), (15, 5), 2),
        ],
    ),
]
# (login, name, designation, papers). The two drivers and the attendant have
# no working login — §5.6.8 gives a driver app access "later", and an account
# nobody uses with a known demo password is worse than no account.
# (login, name, designation, papers, can log in, monthly gross). The driver
# and attendant grosses sit below the ESI threshold of 21,000 and the manager's
# above it, which is the same spread the teaching scales were given: a
# statutory component that applies to some staff and not others is only
# exercised if the demo has both.
TRANSPORT_STAFF = [
    ("TRM001", "Rakesh Chandra Dubey", "Transport Manager", (), True, 28000),
    ("DRV001", "Suresh Kumar Yadav", "Driver",
     ("driving_licence", "police_verification"), False, 16000),
    ("DRV002", "Ram Naresh Verma", "Driver",
     ("driving_licence", "police_verification"), False, 16000),
    ("ATT001", "Sunita Devi", "Bus Attendant", ("police_verification",), False, 11000),
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
    ("Solve the linear equations worksheet", "MAT"),
    ("Draw and label the human digestive system", "SCI"),
    ("Answer the map-work questions", "SST"),
    ("Label the parts of a computer", "CMP"),
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

# The demo passwords, one per role. Overridable in one place: set
# SUNRISE_DEMO_PASSWORD and every seeded account uses it instead. This is the
# only file that needs to state them - PASSWORDS.md (gitignored) writes them
# out for whoever is running the demo, and web/smoke.mjs takes its own from
# SMOKE_PASSWORD rather than hardcoding one.
#
# They are demo credentials for a locally seeded database and protect nothing.
# The real issue is next door and recorded in ERP_BLUEPRINT sections 5 and 11:
# accounts created through the API get a fixed default password with no forced
# change on first login. That is a v0 gap in the product, not in this seed.
_DEMO_PASSWORD = os.environ.get("SUNRISE_DEMO_PASSWORD")

DEMO_PASSWORDS = {
    UserRole.admin: _DEMO_PASSWORD or "Admin@123",
    UserRole.teacher: _DEMO_PASSWORD or "Teacher@123",
    UserRole.student: _DEMO_PASSWORD or "Student@123",
    UserRole.parent: _DEMO_PASSWORD or "Parent@123",
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

    # §3.16's component set, then a salary per designation. Built through the
    # real service so a defect in the payroll rules breaks seeding rather than
    # only a test — the same bargain the fee and timetable seeding makes.
    payroll_svc.install_defaults(db, school.id)
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

    # A Lucknow private school's monthly gross by grade. Whole rupees, and
    # deliberately spread across the ESI threshold of 21,000 so the demo shows
    # a component that applies to some staff and not others.
    GROSS_BY_DESIGNATION = {
        "PGT": Decimal(42000),
        "TGT": Decimal(32000),
        "PRT": Decimal(19500),
    }
    for teacher, (_, _, _, designation) in zip(teachers, TEACHER_NAMES, strict=True):
        if payroll_svc.active_structure(db, teacher.id) is None:
            payroll_svc.set_structure(
                db,
                admin,
                teacher,
                effective_from=date(2026, 4, 1),
                monthly_gross=GROSS_BY_DESIGNATION[designation],
                note=f"{designation} scale",
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
    # Written out rather than derived, because the stages no longer share a
    # subject list and a parity trick over uneven sets balances nothing. Each
    # row is (subject, teacher index, the section indices they take it in), and
    # CLASS_NAMES is ["10","9","8","7","6","5","4","3","2","1"] — so 0-1 are
    # secondary, 2-4 middle, 5-9 primary.
    #
    # Every teacher appears exactly five times, which is what holds the load
    # chart at 25 periods each and spread 0. Verified below rather than
    # trusted: an assignment table is easy to edit into imbalance.
    #
    # Two facts the test fixtures depend on and this table must keep:
    #   TCH001 (index 0) teaches 10-A Mathematics - section 0 is in its row.
    #   TCH004 (index 3) teaches neither 10-A nor Mathematics at all.
    # One specialist per stage per subject: two stages of six subjects is
    # twelve teachers, which is exactly the staff. Each of them takes their
    # subject in all five sections of their stage, so everybody carries five
    # (section, subject) pairs and twenty-five periods a week.
    #
    # The symmetry is not tidiness, it is what makes the timetable solvable.
    # Ten sections must each be taught in all thirty periods of the week, so
    # ten of the twelve teachers are busy in every single period - there is
    # almost no slack. An earlier cut of this table spread subjects across
    # teachers unevenly and the placer simply could not fill the last few
    # periods, whatever algorithm it used.
    #
    # Two facts the fixtures depend on, both kept:
    #   TCH001 (index 0) teaches 10-A Mathematics - it holds senior Maths.
    #   TCH004 (index 3) teaches neither 10-A nor Maths - it holds primary Art.
    SENIOR, PRIMARY = (0, 1, 2, 3, 4), (5, 6, 7, 8, 9)
    TEACHING_PLAN = [
        # subject, teacher, sections
        ("MAT", 0, SENIOR),    # M.Sc. Mathematics
        ("ENG", 1, SENIOR),    # M.A. English
        ("HIN", 2, SENIOR),    # M.A. Hindi
        ("SCI", 6, SENIOR),    # M.Sc. Chemistry
        ("SST", 4, SENIOR),    # M.A. History
        ("SAN", 9, SENIOR),    # M.A. Sanskrit
        ("MAT", 11, PRIMARY),  # M.Com. takes primary arithmetic
        ("ENG", 10, PRIMARY),  # the primary teacher
        ("HIN", 7, PRIMARY),   # M.A. Political Science
        ("EVS", 8, PRIMARY),   # M.Sc. Biology - the natural fit for EVS
        ("CMP", 5, PRIMARY),   # MCA
        ("ART", 3, PRIMARY),   # M.Sc. Physics - art goes to whoever has the
    ]                          # periods, which is what a small school does

    by_code = {sub.code: sub for sub in subjects}
    load = Counter()
    for code, teacher_index, section_indices in TEACHING_PLAN:
        for si in section_indices:
            expected = STAGE_SUBJECTS[stage_of(sections[si].class_name)]
            assert code in expected, (
                f"{code} is not taught in class {sections[si].class_name}"
            )
            db.add(
                ClassSubjectTeacher(
                    class_section_id=sections[si].id,
                    subject_id=by_code[code].id,
                    teacher_id=teachers[teacher_index].id,
                )
            )
            load[teacher_index] += 1

    # Every section fully staffed, and nobody carrying more or less than five.
    for si, sec in enumerate(sections):
        planned = {c for c, _, idxs in TEACHING_PLAN if si in idxs}
        assert planned == set(STAGE_SUBJECTS[stage_of(sec.class_name)]), (
            f"class {sec.class_name} is short of {set(STAGE_SUBJECTS[stage_of(sec.class_name)]) - planned}"
        )
    assert set(load.values()) == {5}, f"uneven teaching load: {dict(load)}"
    assert len(load) == len(teachers), "a teacher was left with nothing to teach"

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
            # §0.11 made email the only v1 channel, and a school that only ever
            # collected mobile numbers can reach nobody. Most families here
            # have an address and **every seventh deliberately does not**, so
            # the unreachable list of §5.9.10 is a real number on a fresh
            # install rather than an empty screen that looks like it works.
            email=None if i % 7 == 0 else f"parent{i:03d}@example.com",
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

    # Each section gets each of ITS subjects the same number of times a week —
    # thirty teaching slots over the stage's six subjects is five each.
    # Tracking what each section still owes, and always placing whichever
    # subject is furthest behind, keeps the periods even without a scheduling
    # algorithm: a greedy "first subject whose teacher is free" drifts, and
    # that drift is what put two teachers on 30 periods while ten sat on 24.
    #
    # Per section, not global: the stages take different subjects now, so
    # dividing the week by len(subjects) would budget each section three
    # periods of each of the ten subjects in the school and leave half the
    # grid empty.
    teaching_slots = (len(periods) - sum(1 for p in periods if p.is_break)) * len(
        DayOfWeek
    )
    subjects_of = {
        sec.id: [by_code[c] for c in STAGE_SUBJECTS[stage_of(sec.class_name)]]
        for sec in sections
    }
    owed = {
        (sec.id, sub.id): teaching_slots // len(subjects_of[sec.id])
        for sec in sections
        for sub in subjects_of[sec.id]
    }

    for period in periods:
        if period.is_break:
            continue
        for day in DayOfWeek:
            for si, sec in enumerate(sections):
                # Furthest behind first; the offset breaks ties differently in
                # each section so they do not all chase the same subject at the
                # same hour and collide on its teacher.
                mine = subjects_of[sec.id]
                candidates = sorted(
                    mine,
                    key=lambda sub, sec=sec, si=si, p=period, mine=mine: (
                        -owed[(sec.id, sub.id)],
                        (mine.index(sub) + si + p.period_no) % len(mine),
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

    # Closures still ahead, so the dashboard's upcoming list has something true
    # to show. Offsets rather than fixed dates because TODAY moves with
    # whoever runs the seed, and names that describe a school's own calendar
    # rather than naming a festival the arithmetic cannot actually guarantee
    # falls on that day.
    for offset, name in ((22, "Mid-term Break"), (54, "Founder's Week"), (106, "Winter Break")):
        db.add(
            Holiday(
                academic_year_id=academic_year_id,
                date=TODAY + timedelta(days=offset),
                name=name,
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
            # The section's own subjects, not every subject in the school: a
            # class 1 paper in Social Science is not an exam anybody sits.
            for qi, sub in enumerate(subjects_of[sec.id]):
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
        # A section that actually takes the subject. Round-robin over every
        # section set homework in Social Science to class 3, which no longer
        # has a teacher for it - and used to be silently wrong rather than a
        # KeyError only because every class held every subject.
        eligible = [
            sec for sec in sections
            if code in STAGE_SUBJECTS[stage_of(sec.class_name)]
        ]
        sec = eligible[i % len(eligible)]
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
                # On every plan, and billed only to the children who actually
                # ride. Before `generate()` learned what an `optional` head
                # means, this one line charged all hundred of them. The amount
                # here is never used: transport is priced from the slab on the
                # stop the child boards at.
                FeePlanItem(
                    school_id=school.id,
                    fee_head_id=heads["TRANSPORT"].id,
                    amount=Decimal("0.00"),
                    frequency=FeeFrequency.monthly,
                ),
            ],
        )
        db.add(plan)
    db.flush()

    _seed_transport(db, school, departments, enrolment_of, students)

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

    # The wording a school starts with, and then edits (§0.18). Idempotent
    # like the document checklist: only the codes that are missing are added,
    # so a school that has already superseded one keeps its own version.
    have_templates = set(
        db.scalars(
            select(MessageTemplate.code).where(
                MessageTemplate.school_id == school.id
            )
        )
    )
    for code, name, category, subject, tmpl_body in DEFAULT_TEMPLATES:
        if code in have_templates:
            continue
        db.add(
            MessageTemplate(
                code=code,
                name=name,
                category=MessageCategory(category),
                subject=subject,
                body=tmpl_body,
            )
        )
    db.flush()

    # The demo school runs buses, so the transport module is on for it. Both
    # transport and HR default to off in the registry — they are modules a
    # school buys (§0.2c) — and the demo turning them on is what makes the
    # switch itself exercised rather than assumed.
    if db.scalar(
        select(Setting).where(
            Setting.school_id == school.id, Setting.key == "feature.transport"
        )
    ) is None:
        db.add(Setting(key="feature.transport", value=True))
    db.flush()

    _assign_roles(db, roles, sections)
    db.commit()


def _seed_transport(db: Session, school, departments: dict, enrolment_of: dict, students: list) -> None:
    """Two buses, two routes and the children on them.

    Built through the real service rather than by inserting rows, for the same
    reason the fee ledger and the timetable are: `svc.set_stops`,
    `svc.set_status` and `svc.assign` are what a school will actually call, so
    a defect in the capacity check or the compliance refusal breaks seeding
    here rather than only failing a test.

    Which means the compliance papers have to be real `documents` rows, because
    a route cannot go active without them. The bytes are placeholder demo
    content, the way the student names are; the row, the type and the expiry
    are what the refusal reads.
    """
    if db.scalar(select(Vehicle).where(Vehicle.school_id == school.id)) is not None:
        return  # idempotent, like the rest of the seed

    admin_user = db.scalar(
        select(User).where(User.school_id == school.id, User.role == UserRole.admin)
    )
    doc_types = {
        t.code: t
        for t in db.scalars(
            select(DocumentType).where(DocumentType.school_id == school.id)
        )
    }

    def paper(owner_type, owner_id, code, expires_on):
        documents.upload(
            db,
            actor=admin_user,
            owner_type=owner_type,
            owner_id=owner_id,
            filename=f"{code}-{owner_id}.pdf",
            mime_type="application/pdf",
            data=f"DEMO {code} for {owner_type.value} {owner_id}".encode(),
            document_type_id=doc_types[code].id,
            expires_on=expires_on,
        )

    # --- crew
    crew = {}
    for i, (login, name, designation, papers, can_log_in, gross) in enumerate(
        TRANSPORT_STAFF
    ):
        u = User(
            role=UserRole.admin,
            login_id=login,
            password_hash=hash_password(DEMO_PASSWORDS[UserRole.admin]),
            full_name=name,
            email=f"{login.lower()}@sunrisepublic.edu",
            phone=f"98765{40000 + i:05d}",
            is_active=can_log_in,
        )
        db.add(u)
        db.flush()
        e = Employee(
            user_id=u.id,
            employee_code=login,
            employee_type=EmployeeType.support if papers else EmployeeType.administrative,
            joining_date=date(2021, 4, 1),
            department_id=departments["TRA"].id,
            designation=designation,
        )
        db.add(e)
        db.flush()
        for code in papers:
            paper(OwnerType.employee, e.id, code, TODAY + timedelta(days=400))
        # A driver is on the payroll like anybody else. Leaving them off it
        # would put four people in the staff register that the monthly run
        # silently skips, which is the oversight `without_structure` exists to
        # surface rather than something the demo should model.
        payroll_svc.set_structure(
            db,
            admin_user,
            e,
            effective_from=date(2026, 4, 1),
            monthly_gross=Decimal(gross),
            note=f"{designation} scale",
        )
        crew[login] = e

    # --- vehicles and their papers
    vehicles = {}
    for i, (registration, model, capacity) in enumerate(VEHICLES):
        v = Vehicle(
            registration_no=registration,
            make_model=model,
            capacity=capacity,
            ownership=VehicleOwnership.owned,
        )
        db.add(v)
        db.flush()
        for j, code in enumerate(transport_svc.VEHICLE_PAPERS):
            # One paper on the first bus lapses in 45 days, so the compliance
            # dashboard has something in it on a fresh install and the 60-day
            # horizon is visibly doing something. Still valid, so the route
            # stays roadworthy — an expired one would ground the demo.
            due = 45 if (i, j) == (0, 3) else 300 + j * 30
            paper(OwnerType.vehicle, v.id, code, TODAY + timedelta(days=due))
        vehicles[registration] = v

    # --- slabs
    slabs = []
    for name, amount in SLABS:
        row = TransportFeeSlab(name=name, monthly_amount=Decimal(amount))
        db.add(row)
        slabs.append(row)
    db.flush()

    # --- routes, through the service so the rules run
    routes = []
    for idx, (code, name, registration, stops) in enumerate(ROUTES):
        r = Route(
            code=code,
            name=name,
            vehicle_id=vehicles[registration].id,
            driver_id=crew[f"DRV{idx + 1:03d}"].id,
            attendant_id=crew["ATT001"].id if idx == 0 else None,
            distance_km=Decimal("12.50") + idx,
        )
        db.add(r)
        db.flush()
        transport_svc.set_stops(
            db,
            r,
            [
                {
                    "sequence": n + 1,
                    "name": stop_name,
                    "landmark": landmark,
                    "pickup_time": time(*pickup),
                    "drop_time": time(*drop),
                    "fee_slab_id": slabs[slab_index].id,
                }
                for n, (stop_name, landmark, pickup, drop, slab_index) in enumerate(stops)
            ],
            admin_user,
        )
        transport_svc.set_status(db, r, RouteStatus.active, admin_user)
        routes.append(r)

    # --- riders. Every fourth child by roll number, spread across both routes
    # and every stop, so route utilisation and the fee opt-in both have a
    # spread rather than one bus full and one empty.
    all_stops = [stop for r in routes for stop in r.stops]
    riders = [s for s in students if enrolment_of[s.id].roll_no % 4 == 1]
    started = date(TODAY.year if TODAY.month >= 4 else TODAY.year - 1, 4, 1)
    for n, student in enumerate(riders):
        row = transport_svc.assign(
            db,
            actor=admin_user,
            enrolment=enrolment_of[student.id],
            stop=all_stops[n % len(all_stops)],
            direction=TransportDirection.both,
            start_date=started,
        )
        transport_svc.set_assignment_status(
            db,
            actor=admin_user,
            row=row,
            new_status=TransportAssignmentStatus.active,
        )
    db.flush()


def _assign_roles(db: Session, roles: dict, sections: list) -> None:
    """Give every seeded account the system role matching its primary role.

    Class teachers additionally get a `class_section`-scoped grant, which is
    what "Class Employee" actually is: the teacher role plus authority over one
    section (ERP_BLUEPRINT §3.5).
    """
    for user in db.scalars(select(User)):
        # One deliberate exception to the legacy map: the counter clerk holds
        # `fee_collector`, which has no void and no concession approval.
        # Drivers and the attendant are staff records, not accounts: their
        # user rows exist because `employees.user_id` is not nullable, and
        # §5.6.8 gives a driver app access "later". Granting them the
        # `super_admin` the legacy map would hand any `admin` row is how a demo
        # password ends up holding every permission in the product.
        if user.login_id.startswith(("DRV", "ATT")):
            continue
        code = (
            "fee_collector"
            if user.login_id == CASHIER_LOGIN
            else "transport_manager"
            if user.login_id.startswith("TRM")
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
