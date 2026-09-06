"""Idempotent demo data — BLUEPRINT §15.

`make seed` wipes every table and rebuilds from a fixed RNG seed, so running it
twice in a row leaves an identical database. Safe immediately before a demo.
"""

from __future__ import annotations

import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.core.document_types import DEFAULT_TYPES
from app.core.permissions import LEGACY_ROLE_MAP
from app.services import audit as audit_svc
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
    OwnerType,
    DayOfWeek,
    Exam,
    ExamSchedule,
    FeeInvoice,
    FeePayment,
    FeeStructure,
    Gender,
    GradeBand,
    Homework,
    HomeworkSubmission,
    InvoiceStatus,
    Mark,
    Notice,
    NoticeAudience,
    Parent,
    ParentStudent,
    School,
    Student,
    Subject,
    Teacher,
    TimetableSlot,
    Role,
    RolePermission,
    ScopeType,
    User,
    UserRole,
    UserRoleAssignment,
)

ACADEMIC_YEAR = "2025-26"
SCHOOL_CODE = "SPS"
TODAY = date(2026, 9, 1)  # deterministic "today" so the seeded window never drifts

# Delete children before parents. ClassSection must go before Teacher because
# class_sections.class_teacher_id references it — SQLite does not enforce
# foreign keys by default, so only Postgres catches a wrong order here.
WIPE_ORDER = [
    FeePayment, FeeInvoice, FeeStructure, Mark, ExamSchedule, Exam, GradeBand,
    HomeworkSubmission, Homework, Attendance, Notice, TimetableSlot,
    ClassSubjectTeacher, ParentStudent, Enrolment, Student, ClassSection,
    Parent, Teacher, Subject, UserRoleAssignment, RolePermission, Role,
    User, AcademicYear, School,
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
TEACHER_NAMES = [
    ("Anita Sharma", "M.Sc. Mathematics, B.Ed."),
    ("Rajesh Verma", "M.A. English, B.Ed."),
    ("Sunita Yadav", "M.A. Hindi, B.Ed."),
    ("Praveen Mishra", "M.Sc. Physics, B.Ed."),
    ("Kavita Singh", "M.A. History, B.Ed."),
    ("Deepak Gupta", "MCA"),
    ("Neha Tiwari", "M.Sc. Chemistry, B.Ed."),
    ("Amit Pandey", "M.A. Political Science, B.Ed."),
    ("Ritu Srivastava", "M.Sc. Biology, B.Ed."),
    ("Vikas Dubey", "M.A. Sanskrit, B.Ed."),
    ("Pooja Awasthi", "B.Ed., Primary"),
    ("Sandeep Rastogi", "M.Com., B.Ed."),
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
OCCUPATIONS = ["Shopkeeper", "Bank Officer", "Teacher", "Farmer", "Engineer", "Homemaker"]

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
    ("Parent-Teacher Meeting this Saturday",
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

GRADE_BANDS = [
    (91, "A1"), (81, "A2"), (71, "B1"), (61, "B2"),
    (51, "C1"), (41, "C2"), (33, "D"), (0, "E"),
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
    for model in WIPE_ORDER:
        db.query(model).delete()
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

    # From here on every row is stamped with this school automatically.
    _stamp_tenant(db, school.id)

    # This school's copy of the roles that ship with the product.
    roles = rbac.install_system_roles(db, school.id)

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
    db.add_all(GradeBand(min_percent=Decimal(p), grade=g) for p, g in GRADE_BANDS)

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

    teachers: list[Teacher] = []
    for i, (name, qual) in enumerate(TEACHER_NAMES, start=1):
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
        t = Teacher(
            user_id=u.id,
            employee_id=emp,
            qualification=qual,
            joining_date=date(2019 + (i % 5), 6, 1),
        )
        db.add(t)
        teachers.append(t)
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

    # Who teaches what, where. Each section is covered by three of the six
    # teachers (two subjects each) so that teacher scoping is a real boundary --
    # a rotation over all six would leave every teacher inside every section.
    # The 10-A group is ordered so TCH001 teaches Mathematics there, which the
    # walkthrough in BLUEPRINT section 13 depends on.
    # Each section is covered by three teachers, two subjects each, drawn on a
    # stride that keeps most teachers out of most sections. A flat rotation over
    # every teacher would put everyone inside every section and make the
    # scoping tests vacuous.
    for si, sec in enumerate(sections):
        if si == 0:
            # 10-A is fixed so TCH001 teaches it Mathematics (subject index 2).
            group = [1, 0, 2]
        else:
            group = [(si * 3 + k) % len(teachers) for k in range(3)]
        for qi, sub in enumerate(subjects):
            db.add(
                ClassSubjectTeacher(
                    class_section_id=sec.id,
                    subject_id=sub.id,
                    teacher_id=teachers[group[qi // 2]].id,
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
    parents: list[Parent] = []
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
        p = Parent(user_id=u.id, occupation=OCCUPATIONS[i % len(OCCUPATIONS)])
        db.add(p)
        parents.append(p)
    db.flush()

    for p, pair in zip(parents[:2], sibling_pairs, strict=True):
        for child in pair:
            db.add(ParentStudent(parent_id=p.id, student_id=child.id, relation="father"))
    for p, child in zip(parents[2:], singles, strict=True):
        db.add(ParentStudent(parent_id=p.id, student_id=child.id, relation="father"))
    db.flush()

    # --- timetable --------------------------------------------------------
    cst = {
        (row.class_section_id, row.subject_id): row.teacher_id
        for row in db.query(ClassSubjectTeacher).all()
    }
    for sec in sections:
        for di, day in enumerate(DayOfWeek):
            for period in range(1, 7):
                sub = subjects[(di + period) % len(subjects)]
                start, end = PERIOD_TIMES[period - 1]
                db.add(
                    TimetableSlot(
                        class_section_id=sec.id,
                        day_of_week=day,
                        period_no=period,
                        start_time=start,
                        end_time=end,
                        subject_id=sub.id,
                        teacher_id=cst[(sec.id, sub.id)],
                        room=ROOMS[(di + period) % len(ROOMS)],
                    )
                )
    db.flush()

    # Class and roll number now live on the enrolment, so look them up once
    # rather than per student per loop.
    enrolment_of = {e.student_id: e for e in db.query(Enrolment).all()}

    # --- attendance: 60 school days, ~92/5/3 with per-student variation ----
    class_teacher_of = {s.id: s.class_teacher_id for s in sections}
    days = school_days(TODAY, 60)
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
                Attendance(student_id=s.id, date=d, status=status, marked_by=marker, remarks=None)
            )
    db.flush()

    # --- exams and marks --------------------------------------------------
    exams = [
        Exam(name="Term 1 - Unit Test 1", term="Term 1",
             start_date=TODAY - timedelta(days=70), end_date=TODAY - timedelta(days=64)),
        Exam(name="Term 1 - Half Yearly", term="Term 1",
             start_date=TODAY - timedelta(days=30), end_date=TODAY - timedelta(days=24)),
    ]
    db.add_all(exams)
    db.flush()

    for exam in exams:
        for sec in sections:
            for qi, sub in enumerate(subjects):
                sched = ExamSchedule(
                    exam_id=exam.id,
                    class_section_id=sec.id,
                    subject_id=sub.id,
                    exam_date=exam.start_date + timedelta(days=qi),
                    start_time=time(9, 0),
                    max_marks=Decimal("100.00"),
                )
                db.add(sched)
                db.flush()
                for s in (x for x in students if enrolment_of[x.id].class_section_id == sec.id):
                    # ability band per student keeps all four donut buckets populated
                    base = 30 + (enrolment_of[s.id].roll_no * 8) % 60
                    score = max(0, min(100, base + rng.randint(-6, 12)))
                    db.add(
                        Mark(
                            exam_schedule_id=sched.id,
                            student_id=s.id,
                            marks_obtained=Decimal(score),
                            entered_by=cst[(sec.id, sub.id)],
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
    db.add_all(FeeStructure(class_name=c, monthly_amount=a) for c, a in fees.items())

    class_name_of = {s.id: s.class_name for s in sections}
    for back in (3, 2, 1):
        month, year = month_back(TODAY, back)
        for s in students:
            amount = fees[class_name_of[enrolment_of[s.id].class_section_id]]
            due = date(year, month, 10)
            paid = (enrolment_of[s.id].roll_no + month) % 3 != 0
            inv = FeeInvoice(
                student_id=s.id,
                month=month,
                year=year,
                amount=amount,
                due_date=due,
                # every seeded month is already past its due date
                status=InvoiceStatus.paid if paid else InvoiceStatus.overdue,
            )
            db.add(inv)
            db.flush()
            if paid:
                # Draw from the same sequence the application uses, so the
                # counter reflects what has actually been issued and a payment
                # taken right after seeding does not collide.
                db.add(
                    FeePayment(
                        invoice_id=inv.id,
                        amount=amount,
                        paid_at=datetime.combine(due, time(11, 0), tzinfo=UTC),
                        method="simulated",
                        txn_ref=f"SIM-{rng.getrandbits(48):012X}",
                        receipt_no=audit_svc.next_number(
                            db,
                            school.id,
                            kind="receipt",
                            year=year,
                            prefix=f"SPS/RCP/{year}/",
                            width=6,
                        ),
                    )
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

    _assign_roles(db, roles, sections)
    db.commit()


def _assign_roles(db: Session, roles: dict, sections: list) -> None:
    """Give every seeded account the system role matching its primary role.

    Class teachers additionally get a `class_section`-scoped grant, which is
    what "Class Teacher" actually is: the teacher role plus authority over one
    section (ERP_BLUEPRINT §3.5).
    """
    for user in db.scalars(select(User)):
        code = LEGACY_ROLE_MAP[user.role.value]
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
        teacher = db.get(Teacher, sec.class_teacher_id)
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
