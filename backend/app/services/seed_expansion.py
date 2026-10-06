"""Idempotent academic database expansion service for Sunrise School ERP.

Expands academic classes by adding 9 academic groups:
Pre-primary:
  - Nursery-A
  - LKG-A
  - UKG-A
Senior Secondary:
  - Class 11 (Science, Commerce, Humanities) -> 11-Sci, 11-Com, 11-Hum
  - Class 12 (Science, Commerce, Humanities) -> 12-Sci, 12-Com, 12-Hum

For every added group:
  - Demo students (10 per section) with enrolments, guardian accounts, and RBAC roles
  - Subjects, class teachers, and subject teachers (CST)
  - Timetable entries balancing teacher workload (30 slots per section, Mon-Sat)
  - Valid fee plans with standard heads (Tuition, Development, Transport)

Also cleans up student attendance:
  - Deletes attendance records dated prior to 1 October 2026
  - Seeds October 1, 2, 3 demo attendance
  - Preserves Sunday 4 October 2026 as non-school/unmarked day
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    AcademicYear,
    Attendance,
    AttendanceStatus,
    ClassSection,
    ClassSubjectTeacher,
    DayOfWeek,
    Department,
    Employee,
    EmployeeType,
    Enrolment,
    EnrolmentStatus,
    FeeFrequency,
    FeeHead,
    FeePlan,
    FeePlanItem,
    Gender,
    Guardian,
    GuardianRelation,
    Role,
    School,
    SchoolPeriod,
    ScopeType,
    Student,
    StudentGuardian,
    Subject,
    TimetableSlot,
    User,
    UserRole,
)
from app.services import payroll as payroll_svc
from app.services import rbac

DEMO_STUDENT_PASSWORD = hash_password("Sunrise@Student1")
DEMO_TEACHER_PASSWORD = hash_password("Sunrise@Teacher1")
DEMO_PARENT_PASSWORD = hash_password("Sunrise@Parent1")

NEW_SUBJECTS = [
    ("Physics", "PHY"),
    ("Chemistry", "CHE"),
    ("Biology", "BIO"),
    ("Accountancy", "ACC"),
    ("Business Studies", "BST"),
    ("Economics", "ECO"),
    ("History", "HIS"),
    ("Political Science", "POL"),
    ("Geography", "GEO"),
]

NEW_TEACHERS = [
    # (code, name, qualification, dept_code, designation)
    ("TCH013", "Anjali Saxena", "B.Ed., Early Childhood Education", "PRI", "PRT"),
    ("TCH014", "Sneha Kapoor", "Diploma in Early Childhood Care", "PRI", "PRT"),
    ("TCH015", "Meenakshi Joshi", "B.El.Ed., Montessori Trained", "PRI", "PRT"),
    ("TCH016", "Dr. Arvind Swaminathan", "Ph.D. Physics, B.Ed.", "SCI", "PGT"),
    ("TCH017", "Dr. Shalini Mukherjee", "Ph.D. Chemistry, B.Ed.", "SCI", "PGT"),
    ("TCH018", "Vivek Mathur", "M.Sc. Mathematics, B.Ed.", "SCI", "PGT"),
    ("TCH019", "Priya Nambiar", "M.Sc. Zoology, B.Ed.", "SCI", "PGT"),
    ("TCH020", "Manoj Khandelwal", "M.Com., CA Inter, B.Ed.", "HUM", "PGT"),
    ("TCH021", "Sunita Agarwal", "M.A. Economics, B.Ed.", "HUM", "PGT"),
    ("TCH022", "Dr. Harish Chandra", "Ph.D. History, B.Ed.", "HUM", "PGT"),
    ("TCH023", "Rashmi Bhatnagar", "M.A. Political Science, B.Ed.", "HUM", "PGT"),
    ("TCH024", "Rohan Ghosh", "M.Tech. Computer Science", "SCI", "PGT"),
]

NEW_SECTIONS = [
    # (class_name, section, stream, room, class_teacher_code)
    ("Nursery", "A", None, "R-Pre1", "TCH013"),
    ("LKG", "A", None, "R-Pre2", "TCH014"),
    ("UKG", "A", None, "R-Pre3", "TCH015"),
    ("11", "Sci", "Science", "R-301", "TCH016"),
    ("11", "Com", "Commerce", "R-302", "TCH020"),
    ("11", "Hum", "Humanities", "R-303", "TCH022"),
    ("12", "Sci", "Science", "R-304", "TCH017"),
    ("12", "Com", "Commerce", "R-305", "TCH021"),
    ("12", "Hum", "Humanities", "R-306", "TCH023"),
]

SECTION_SUBJECT_TEACHERS = {
    ("Nursery", "A"): [
        ("ENG", "TCH013"),
        ("HIN", "TCH014"),
        ("MAT", "TCH013"),
        ("EVS", "TCH015"),
        ("ART", "TCH014"),
        ("CMP", "TCH015"),
    ],
    ("LKG", "A"): [
        ("ENG", "TCH014"),
        ("HIN", "TCH015"),
        ("MAT", "TCH014"),
        ("EVS", "TCH013"),
        ("ART", "TCH015"),
        ("CMP", "TCH013"),
    ],
    ("UKG", "A"): [
        ("ENG", "TCH015"),
        ("HIN", "TCH013"),
        ("MAT", "TCH015"),
        ("EVS", "TCH014"),
        ("ART", "TCH013"),
        ("CMP", "TCH014"),
    ],
    ("11", "Sci"): [
        ("ENG", "TCH013"),
        ("PHY", "TCH016"),
        ("CHE", "TCH017"),
        ("MAT", "TCH018"),
        ("BIO", "TCH019"),
        ("CMP", "TCH024"),
    ],
    ("12", "Sci"): [
        ("ENG", "TCH014"),
        ("PHY", "TCH016"),
        ("CHE", "TCH017"),
        ("MAT", "TCH018"),
        ("BIO", "TCH019"),
        ("CMP", "TCH024"),
    ],
    ("11", "Com"): [
        ("ENG", "TCH015"),
        ("ACC", "TCH020"),
        ("BST", "TCH020"),
        ("ECO", "TCH021"),
        ("MAT", "TCH018"),
        ("CMP", "TCH024"),
    ],
    ("12", "Com"): [
        ("ENG", "TCH013"),
        ("ACC", "TCH020"),
        ("BST", "TCH020"),
        ("ECO", "TCH021"),
        ("MAT", "TCH018"),
        ("CMP", "TCH024"),
    ],
    ("11", "Hum"): [
        ("ENG", "TCH014"),
        ("HIS", "TCH022"),
        ("POL", "TCH023"),
        ("GEO", "TCH022"),
        ("ECO", "TCH021"),
        ("CMP", "TCH024"),
    ],
    ("12", "Hum"): [
        ("ENG", "TCH015"),
        ("HIS", "TCH022"),
        ("POL", "TCH023"),
        ("GEO", "TCH022"),
        ("ECO", "TCH021"),
        ("CMP", "TCH024"),
    ],
}

NEW_FEE_RATES = {
    "Nursery": Decimal("1100.00"),
    "LKG": Decimal("1150.00"),
    "UKG": Decimal("1200.00"),
    "11": Decimal("3200.00"),
    "12": Decimal("3500.00"),
}

STUDENT_FIRST_BOYS = [
    "Aarav", "Kabir", "Vihaan", "Aditya", "Rohan", "Vivaan", "Reyansh", "Muhammad",
    "Sai", "Arjun", "Krishna", "Aryan", "Dhruv", "Ishaan", "Shaurya", "Atharv",
]
STUDENT_FIRST_GIRLS = [
    "Saanvi", "Aanya", "Aadhya", "Diya", "Ananya", "Pari", "Myra", "Fatima",
    "Ira", "Riya", "Avani", "Prisha", "Anvi", "Sneha", "Kavya", "Navya",
]
STUDENT_LAST = [
    "Sharma", "Verma", "Yadav", "Mishra", "Singh", "Gupta", "Tiwari", "Pandey",
    "Chauhan", "Bhatnagar", "Agarwal", "Saxena", "Srivastava", "Kapoor", "Joshi",
]
PARENT_FIRST = [
    "Suresh", "Meenakshi", "Ramesh", "Kalpana", "Vinod", "Shalini", "Dinesh",
    "Rekha", "Alok", "Sarita", "Mahesh", "Nirmala", "Sanjay", "Usha", "Ajay",
    "Geeta", "Naresh", "Kamla", "Rakesh", "Sudha", "Prakash", "Bindu",
]


def expand_database(db: Session) -> dict[str, int]:
    counts = {
        "subjects_added": 0,
        "teachers_added": 0,
        "sections_added": 0,
        "cst_added": 0,
        "slots_added": 0,
        "fee_plans_added": 0,
        "students_added": 0,
        "attendance_deleted": 0,
        "attendance_seeded": 0,
    }

    school = db.scalar(select(School))
    if not school:
        raise RuntimeError("No school found in database")

    year = db.scalar(select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.is_current.is_(True)))
    if not year:
        year = db.scalar(select(AcademicYear).where(AcademicYear.school_id == school.id).order_by(AcademicYear.id.desc()))
    if not year:
        raise RuntimeError("No academic year found")

    admin_user = db.scalar(select(User).where(User.school_id == school.id, User.role == UserRole.admin))

    # Lookup RBAC roles
    roles = {r.code: r for r in db.scalars(select(Role).where(Role.school_id == school.id))}
    teacher_role = roles.get("teacher")
    student_role = roles.get("student")
    parent_role = roles.get("guardian")

    # 1. Subjects
    for name, code in NEW_SUBJECTS:
        existing_sub = db.scalar(
            select(Subject).where(Subject.school_id == school.id, Subject.code == code)
        )
        if not existing_sub:
            db.add(Subject(school_id=school.id, name=name, code=code))
            counts["subjects_added"] += 1
    db.flush()

    all_subjects = {
        s.code: s for s in db.scalars(select(Subject).where(Subject.school_id == school.id))
    }

    # 2. Departments
    depts = {
        d.code: d for d in db.scalars(select(Department).where(Department.school_id == school.id))
    }

    # 3. Teachers
    GROSS_BY_DESIGNATION = {
        "PGT": Decimal(42000),
        "TGT": Decimal(32000),
        "PRT": Decimal(22500),
    }

    for emp_code, name, qual, dept_code, designation in NEW_TEACHERS:
        existing_emp = db.scalar(
            select(Employee).where(Employee.school_id == school.id, Employee.employee_code == emp_code)
        )
        if not existing_emp:
            u = User(
                school_id=school.id,
                role=UserRole.teacher,
                login_id=emp_code,
                password_hash=DEMO_TEACHER_PASSWORD,
                full_name=name,
                email=f"{emp_code.lower()}@sunrisepublic.edu",
                phone=f"98765{30000 + int(emp_code[3:]):05d}",
                is_active=True,
            )
            db.add(u)
            db.flush()

            if teacher_role:
                rbac.assign(db, u, teacher_role, scope_type=ScopeType.school)

            emp = Employee(
                school_id=school.id,
                user_id=u.id,
                employee_code=emp_code,
                employee_type=EmployeeType.teaching,
                qualification=qual,
                joining_date=date(2022, 4, 1),
                department_id=depts.get(dept_code, next(iter(depts.values()))).id if depts else None,
                designation=designation,
            )
            db.add(emp)
            db.flush()
            counts["teachers_added"] += 1

            if admin_user and payroll_svc.active_structure(db, emp.id) is None:
                payroll_svc.set_structure(
                    db,
                    admin_user,
                    emp,
                    effective_from=date(2026, 4, 1),
                    monthly_gross=GROSS_BY_DESIGNATION.get(designation, Decimal(25000)),
                    note=f"{designation} standard scale",
                )
    db.flush()

    all_teachers = {
        e.employee_code: e
        for e in db.scalars(
            select(Employee).where(
                Employee.school_id == school.id,
                Employee.employee_type == EmployeeType.teaching,
            )
        )
    }

    # 4. Class Sections
    section_map = {}
    for cls_name, sec_letter, stream_name, room, ct_code in NEW_SECTIONS:
        existing_sec = db.scalar(
            select(ClassSection).where(
                ClassSection.academic_year_id == year.id,
                ClassSection.class_name == cls_name,
                ClassSection.section == sec_letter,
            )
        )
        if not existing_sec:
            ct = all_teachers.get(ct_code)
            new_sec = ClassSection(
                school_id=school.id,
                academic_year_id=year.id,
                class_name=cls_name,
                section=sec_letter,
                stream=stream_name,
                room=room,
                capacity=40,
                class_teacher_id=ct.id if ct else None,
            )
            db.add(new_sec)
            db.flush()
            counts["sections_added"] += 1
            section_map[(cls_name, sec_letter)] = new_sec

            if ct and teacher_role:
                rbac.assign(
                    db,
                    ct.user,
                    teacher_role,
                    scope_type=ScopeType.class_section,
                    scope_id=new_sec.id,
                )
        else:
            section_map[(cls_name, sec_letter)] = existing_sec

    # 5. Class Subject Teachers (CST)
    for (cls_name, sec_letter), sub_tchs in SECTION_SUBJECT_TEACHERS.items():
        sec = section_map.get((cls_name, sec_letter))
        if not sec:
            continue
        for sub_code, tch_code in sub_tchs:
            sub = all_subjects.get(sub_code)
            tch = all_teachers.get(tch_code)
            if not sub or not tch:
                continue
            existing_cst = db.scalar(
                select(ClassSubjectTeacher).where(
                    ClassSubjectTeacher.class_section_id == sec.id,
                    ClassSubjectTeacher.subject_id == sub.id,
                )
            )
            if not existing_cst:
                db.add(
                    ClassSubjectTeacher(
                        school_id=school.id,
                        class_section_id=sec.id,
                        subject_id=sub.id,
                        teacher_id=tch.id,
                    )
                )
                counts["cst_added"] += 1
    db.flush()

    # 6. Timetable Slots
    periods = list(
        db.scalars(
            select(SchoolPeriod)
            .where(SchoolPeriod.school_id == school.id, SchoolPeriod.is_break.is_(False))
            .order_by(SchoolPeriod.period_no)
        )
    )

    busy_teacher = {
        (slot.day_of_week, slot.period_id, slot.teacher_id)
        for slot in db.scalars(select(TimetableSlot).where(TimetableSlot.school_id == school.id))
    }
    busy_room = {
        (slot.day_of_week, slot.period_id, slot.room)
        for slot in db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.school_id == school.id, TimetableSlot.room.is_not(None)
            )
        )
    }

    days = list(DayOfWeek)

    for (cls_name, sec_letter), sub_tchs in SECTION_SUBJECT_TEACHERS.items():
        sec = section_map.get((cls_name, sec_letter))
        if not sec:
            continue
        existing_slots = db.scalars(
            select(TimetableSlot).where(TimetableSlot.class_section_id == sec.id)
        ).all()
        if existing_slots:
            continue  # Already populated

        subject_objects = []
        cst_lookup = {}
        for sub_code, tch_code in sub_tchs:
            sub = all_subjects.get(sub_code)
            tch = all_teachers.get(tch_code)
            if sub and tch:
                subject_objects.append(sub)
                cst_lookup[sub.id] = tch.id

        owed = {sub.id: 5 for sub in subject_objects}

        for period in periods:
            for day in days:
                existing_slot = db.scalar(
                    select(TimetableSlot).where(
                        TimetableSlot.class_section_id == sec.id,
                        TimetableSlot.day_of_week == day,
                        TimetableSlot.period_id == period.id,
                    )
                )
                if existing_slot:
                    continue

                candidates = sorted(
                    subject_objects,
                    key=lambda s: -owed[s.id],
                )
                placed = False
                for sub in candidates:
                    if owed[sub.id] <= 0:
                        continue
                    tch_id = cst_lookup.get(sub.id)
                    if (day, period.id, tch_id) in busy_teacher:
                        continue
                    room = sec.room
                    if (day, period.id, room) in busy_room:
                        room = None

                    db.add(
                        TimetableSlot(
                            school_id=school.id,
                            class_section_id=sec.id,
                            day_of_week=day,
                            period_id=period.id,
                            subject_id=sub.id,
                            teacher_id=tch_id,
                            room=room,
                        )
                    )
                    busy_teacher.add((day, period.id, tch_id))
                    if room:
                        busy_room.add((day, period.id, room))
                    owed[sub.id] -= 1
                    counts["slots_added"] += 1
                    placed = True
                    break

                if not placed:
                    ct_id = sec.class_teacher_id or next(iter(all_teachers.values())).id
                    sub = subject_objects[0]
                    db.add(
                        TimetableSlot(
                            school_id=school.id,
                            class_section_id=sec.id,
                            day_of_week=day,
                            period_id=period.id,
                            subject_id=sub.id,
                            teacher_id=ct_id,
                            room=sec.room,
                        )
                    )
                    counts["slots_added"] += 1
    db.flush()

    # 7. Fee Plans
    heads = {
        h.code: h for h in db.scalars(select(FeeHead).where(FeeHead.school_id == school.id))
    }

    for cls_name, monthly_rate in NEW_FEE_RATES.items():
        existing_plan = db.scalar(
            select(FeePlan).where(
                FeePlan.academic_year_id == year.id,
                FeePlan.class_name == cls_name,
            )
        )
        if not existing_plan:
            dev_fee = (monthly_rate / 5).quantize(Decimal("0.01"))
            tuition_fee = monthly_rate - dev_fee
            items = []
            if "TUITION" in heads:
                items.append(
                    FeePlanItem(
                        school_id=school.id,
                        fee_head_id=heads["TUITION"].id,
                        amount=tuition_fee,
                        frequency=FeeFrequency.monthly,
                    )
                )
            if "DEV" in heads:
                items.append(
                    FeePlanItem(
                        school_id=school.id,
                        fee_head_id=heads["DEV"].id,
                        amount=dev_fee,
                        frequency=FeeFrequency.monthly,
                    )
                )
            if "TRANSPORT" in heads:
                items.append(
                    FeePlanItem(
                        school_id=school.id,
                        fee_head_id=heads["TRANSPORT"].id,
                        amount=Decimal("0.00"),
                        frequency=FeeFrequency.monthly,
                    )
                )
            plan = FeePlan(
                school_id=school.id,
                academic_year_id=year.id,
                name=f"Class {cls_name} standard",
                class_name=cls_name,
                items=items,
            )
            db.add(plan)
            counts["fee_plans_added"] += 1
    db.flush()

    # 8. Demo Students and Enrolments
    base_adm = 2024000100
    student_idx = 0

    DOB_YEAR_OFFSET = {
        "Nursery": 2022,
        "LKG": 2021,
        "UKG": 2020,
        "11": 2009,
        "12": 2008,
    }

    for cls_name, sec_letter, _, _, _ in NEW_SECTIONS:
        sec = section_map.get((cls_name, sec_letter))
        if not sec:
            continue

        existing_enrolments = db.scalars(
            select(Enrolment).where(Enrolment.class_section_id == sec.id)
        ).all()
        if existing_enrolments:
            continue  # Already enrolled

        for roll in range(1, 11):
            student_idx += 1
            adm_num = f"{base_adm + student_idx}"
            is_boy = (roll % 2 != 0)
            first_name = (
                STUDENT_FIRST_BOYS[(student_idx * 3) % len(STUDENT_FIRST_BOYS)]
                if is_boy
                else STUDENT_FIRST_GIRLS[(student_idx * 3) % len(STUDENT_FIRST_GIRLS)]
            )
            last_name = STUDENT_LAST[(student_idx * 5) % len(STUDENT_LAST)]
            full_name = f"{first_name} {last_name}"
            dob_year = DOB_YEAR_OFFSET.get(cls_name, 2015)
            dob = date(dob_year, ((roll * 2) % 12) + 1, ((roll * 3) % 25) + 1)

            s_user = User(
                school_id=school.id,
                role=UserRole.student,
                login_id=adm_num,
                password_hash=DEMO_STUDENT_PASSWORD,
                full_name=full_name,
                email=f"student_{adm_num}@sunrisepublic.edu",
                is_active=True,
            )
            db.add(s_user)
            db.flush()

            if student_role:
                rbac.assign(db, s_user, student_role, scope_type=ScopeType.self_only)

            s = Student(
                school_id=school.id,
                user_id=s_user.id,
                admission_no=adm_num,
                dob=dob,
                gender=Gender.male if is_boy else Gender.female,
                address=f"House {100 + student_idx}, Vikas Nagar, Lucknow",
                admission_date=date(2024, 4, 1),
                apaar_id=f"99{adm_num:0>10}",
                apaar_consent=True,
            )
            db.add(s)
            db.flush()

            enr = Enrolment(
                school_id=school.id,
                student_id=s.id,
                class_section_id=sec.id,
                academic_year_id=year.id,
                roll_no=roll,
                status=EnrolmentStatus.active,
                joined_on=date(2024, 4, 1),
            )
            db.add(enr)
            db.flush()

            parent_mobile = f"98765{40000 + student_idx:05d}"
            p_first = PARENT_FIRST[(student_idx * 2) % len(PARENT_FIRST)]
            p_user = User(
                school_id=school.id,
                role=UserRole.parent,
                login_id=parent_mobile,
                password_hash=DEMO_PARENT_PASSWORD,
                full_name=f"{p_first} {last_name}",
                phone=parent_mobile,
                email=f"parent_{adm_num}@sunrisepublic.edu",
                is_active=True,
            )
            db.add(p_user)
            db.flush()

            if parent_role:
                rbac.assign(db, p_user, parent_role, scope_type=ScopeType.self_only)

            g = Guardian(
                school_id=school.id,
                user_id=p_user.id,
                occupation="Service / Professional",
            )
            db.add(g)
            db.flush()

            db.add(
                StudentGuardian(
                    school_id=school.id,
                    student_id=s.id,
                    guardian_id=g.id,
                    relation=GuardianRelation.father if is_boy else GuardianRelation.mother,
                    is_primary=True,
                )
            )

            counts["students_added"] += 1
    db.flush()

    # 9. Attendance Clean-up: Delete student attendance records prior to 1 October 2026
    del_result = db.execute(
        delete(Attendance).where(Attendance.date < date(2026, 10, 1))
    )
    counts["attendance_deleted"] = del_result.rowcount or 0
    db.flush()

    # 10. Seed Demo Attendance for Oct 1, Oct 2, Oct 3, 2026 across all active enrolments
    # Sunday Oct 4, 2026 is intentionally NOT marked.
    oct_dates = [
        date(2026, 10, 1),  # Thursday
        date(2026, 10, 2),  # Friday
        date(2026, 10, 3),  # Saturday
    ]

    all_active_enrolments = db.scalars(
        select(Enrolment).where(
            Enrolment.academic_year_id == year.id,
            Enrolment.status == EnrolmentStatus.active,
        )
    ).all()

    for att_date in oct_dates:
        for enr in all_active_enrolments:
            existing_att = db.scalar(
                select(Attendance).where(
                    Attendance.enrolment_id == enr.id,
                    Attendance.date == att_date,
                )
            )
            if existing_att:
                continue

            # 92% present, 5% absent, 3% leave
            seed_val = (enr.id * 17 + att_date.day * 13) % 100
            if seed_val < 92:
                status = AttendanceStatus.present
                remarks = None
            elif seed_val < 97:
                status = AttendanceStatus.absent
                remarks = "Uninformed absence"
            else:
                status = AttendanceStatus.leave
                remarks = "Medical leave application approved"

            db.add(
                Attendance(
                    school_id=school.id,
                    enrolment_id=enr.id,
                    date=att_date,
                    status=status,
                    remarks=remarks,
                )
            )
            counts["attendance_seeded"] += 1

    db.commit()
    return counts
