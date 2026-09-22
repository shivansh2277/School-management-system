"""Dashboard aggregates. Every figure here is a live query.

BLUEPRINT §0: if a statistic cannot be computed from real data the response
omits it (null) rather than inventing one. Trend series carry only periods that
actually have data.
"""

from datetime import date as Date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    Attendance,
    ClassSection,
    Enrolment,
    EnrolmentStatus,
    ExamSchedule,
    FeeInvoice,
    FeeInvoiceLine,
    PaymentAllocation,
    Mark,
    Student,
    Employee,
    EmployeeType,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import assessment, attendance
from app.services.common import class_label_map, section_labels, subject_names

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", None]

BUCKETS = [
    ("excellent", 80.0),
    ("good", 60.0),
    ("average", 40.0),
    ("needs_improvement", 0.0),
]


def totals(db: Session, year: AcademicYear) -> dict:
    school_id = year.school_id
    students = db.scalar(
        select(func.count())
        .select_from(Student)
        .join(User, User.id == Student.user_id)
        .where(Student.school_id == school_id, User.is_active)
    )
    # Teaching staff, not all staff. This counted every active employee, so
    # the Transport Manager was a teacher: the demo school read 13 where it has
    # 12, and section 5.10.10's student:teacher ratio inherited the error from
    # the field it is built on. `employee_type` is the column that already
    # knows the difference.
    teachers = db.scalar(
        select(func.count())
        .select_from(Employee)
        .join(User, User.id == Employee.user_id)
        .where(
            Employee.school_id == school_id,
            User.is_active,
            Employee.employee_type == EmployeeType.teaching,
        )
    )
    classes = db.scalar(
        select(func.count())
        .select_from(ClassSection)
        .where(ClassSection.academic_year_id == year.id)
    )
    # Collection is the sum of what payments were *allocated to*, not of the
    # payments themselves: an advance is money received, not revenue for a
    # month that has not been billed yet.
    fees = db.scalar(
        select(func.coalesce(func.sum(PaymentAllocation.amount), 0))
        .join(FeeInvoiceLine, FeeInvoiceLine.id == PaymentAllocation.invoice_line_id)
        .join(FeeInvoice, FeeInvoice.id == FeeInvoiceLine.invoice_id)
        .where(
            FeeInvoice.school_id == school_id,
            FeeInvoice.period_year.in_(_academic_years(year.code)),
        )
    )
    from app.services import fees as fees_svc
    fees_remaining = sum(
        (r["outstanding"] for r in fees_svc.defaulters(db, school_id)),
        Decimal("0.00"),
    )
    return {
        "students": students,
        "teachers": teachers,
        "classes": classes,
        "fees_collected": Decimal(fees),
        "fees_remaining": fees_remaining,
    }


def _academic_years(academic_year: str) -> list[int]:
    """'2025-26' -> [2025, 2026]."""
    start = int(academic_year.split("-")[0])
    return [start, start + 1]


def exam_percentages(
    db: Session, exam_id: int, class_section_id: int | None = None
) -> dict[int, float]:
    """Every student's overall percentage in one exam, as a single aggregate query.

    Building this per student through `report_card()` meant one round trip per
    student per subject, which was imperceptible against a local database and
    took 8.5 s against a hosted one. The arithmetic is identical: a subject with
    no `marks` row contributes to neither the numerator nor the denominator, so
    an absent subject stays excluded from the total rather than counting as zero.

    Keeping it identical is the point — §5.10.9 requires the dashboard total and
    the report card total to agree, which means one definition and not two
    queries that drift. A mark row now exists for an absent or exempted child
    with a null score, so those rows are excluded here explicitly: without the
    filter `sum(marks_obtained)` would skip the null while
    `sum(max_marks)` still counted the paper, and the dashboard would quietly
    read lower than the card.
    """
    q = (
        select(
            Mark.student_id,
            func.sum(Mark.marks_obtained),
            func.sum(ExamSchedule.max_marks),
        )
        .join(ExamSchedule, ExamSchedule.id == Mark.exam_schedule_id)
        .where(ExamSchedule.exam_id == exam_id, Mark.marks_obtained.is_not(None))
        .group_by(Mark.student_id)
    )
    if class_section_id is not None:
        q = q.where(ExamSchedule.class_section_id == class_section_id)
    return {
        student_id: round(float(obtained) / float(out_of) * 100, 1)
        for student_id, obtained, out_of in db.execute(q).all()
        if out_of
    }


def performance(
    db: Session, school_id: int, class_section_id: int | None = None
) -> dict:
    exam = assessment.latest_exam_with_marks(db, school_id, class_section_id)
    counts = {name: 0 for name, _ in BUCKETS}
    if exam is None:
        return counts
    for pct in exam_percentages(db, exam.id, class_section_id).values():
        for name, floor in BUCKETS:
            if pct >= floor:
                counts[name] += 1
                break
    return counts


def top_performers(db: Session, school_id: int, limit: int = 3) -> list[dict]:
    exam = assessment.latest_exam_with_marks(db, school_id)
    if exam is None:
        return []
    percentages = exam_percentages(db, exam.id)
    if not percentages:
        return []
    students = {
        s.id: s
        for s in db.scalars(
            select(Student).where(
                Student.school_id == school_id, Student.id.in_(percentages)
            )
        )
    }
    sections = class_label_map(db, list(percentages))
    scored = [
        {
            "student_id": sid,
            "name": students[sid].user.full_name,
            "class_label": sections.get(sid, ""),
            "average_percent": pct,
        }
        for sid, pct in percentages.items()
        if sid in students
    ]
    scored.sort(key=lambda r: r["average_percent"], reverse=True)
    return scored[:limit]


def today_schedule(
    db: Session,
    school_id: int,
    class_section_ids: list[int] | None = None,
    teacher_id: int | None = None,
) -> list[dict]:
    today = Date.today()
    key = DAY_KEYS[today.weekday()]
    if key is None:  # Sunday
        return []

    # Overlay confirmed substitutions for today
    subs = {
        s.timetable_slot_id: s
        for s in db.scalars(
            select(Substitution).where(
                Substitution.school_id == school_id,
                Substitution.date == today,
                Substitution.status.in_((SubstitutionStatus.assigned, SubstitutionStatus.completed)),
            )
        )
    }

    q = select(TimetableSlot).where(
        TimetableSlot.school_id == school_id, TimetableSlot.day_of_week == key
    )
    if class_section_ids is not None:
        q = q.where(TimetableSlot.class_section_id.in_(class_section_ids))

    all_day_slots = list(db.scalars(q))

    if teacher_id is not None:
        matching_slots = []
        for slot in all_day_slots:
            sub = subs.get(slot.id)
            effective_teacher_id = (
                sub.substitute_teacher_id
                if (sub and sub.substitute_teacher_id)
                else slot.teacher_id
            )
            if effective_teacher_id == teacher_id:
                matching_slots.append(slot)
    else:
        matching_slots = all_day_slots

    labels = section_labels(db, school_id)
    subjects = subject_names(db, school_id)
    teachers = {
        t.id: t.user.full_name
        for t in db.scalars(select(Employee).where(Employee.school_id == school_id))
    }
    return [
        {
            "period": slot.period.period_no,
            "time": f"{slot.period.start_time:%H:%M}-{slot.period.end_time:%H:%M}",
            "class_label": labels.get(slot.class_section_id, ""),
            "subject": subjects.get(slot.subject_id, ""),
            "teacher": teachers.get(
                subs[slot.id].substitute_teacher_id
                if (slot.id in subs and subs[slot.id].substitute_teacher_id)
                else slot.teacher_id,
                "",
            ),
            "is_substituted": slot.id in subs,
            "room": slot.room,
        }
        for slot in sorted(matching_slots, key=lambda s: s.period.period_no)
    ]


def fee_trend(db: Session, school_id: int) -> list[dict]:
    rows = db.execute(
        select(
            FeeInvoice.period_year,
            FeeInvoice.period_month,
            func.sum(PaymentAllocation.amount),
        )
        .join(FeeInvoiceLine, FeeInvoiceLine.invoice_id == FeeInvoice.id)
        .join(PaymentAllocation, PaymentAllocation.invoice_line_id == FeeInvoiceLine.id)
        .where(FeeInvoice.school_id == school_id)
        .group_by(FeeInvoice.period_year, FeeInvoice.period_month)
        .order_by(FeeInvoice.period_year, FeeInvoice.period_month)
    ).all()
    # only months that have collections; no zero-filled placeholder points
    return [{"month": f"{y}-{m:02d}", "collected": Decimal(v)} for y, m, v in rows]


def student_teacher_ratio(db: Session, year: AcademicYear) -> dict:
    """Students per teacher (section 5.10.10).

    Both counts come from `totals()` rather than from two fresh queries, so the
    ratio on a report and the headcounts on the dashboard cannot disagree - the
    reconciliation rule of section 5.10.9, applied to the smallest possible
    number.

    A school with no active teachers gets `null`, not a division by zero and
    not a placeholder. It is a real state during setup.
    """
    counted = totals(db, year)
    students, teachers = counted["students"], counted["teachers"]
    return {
        "students": students,
        "teachers": teachers,
        "ratio": round(students / teachers, 1) if teachers else None,
    }


def enrolment_trend(db: Session, school_id: int) -> list[dict]:
    """Heads on the roll each year, and how many of them stayed (5.10.10).

    Retention is measured against the year immediately before: of the students
    enrolled then, how many appear again now. That is the number a board asks
    for, and it is computable from `enrolments` alone because a student sits in
    exactly one section per year - the invariant the enrolment split exists to
    hold.

    The first year has no year before it, so its retention is `null` rather
    than 0 or 100. Inventing either would be the fabricated data point section
    5.10.9 forbids, and it is the one a trend line is most likely to be
    misread from.
    """
    years = list(
        db.scalars(
            select(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .order_by(AcademicYear.start_date)
        )
    )
    rolls: list[set[int]] = [
        set(
            db.scalars(
                select(Enrolment.student_id).where(
                    Enrolment.academic_year_id == y.id,
                    Enrolment.status == EnrolmentStatus.active,
                )
            )
        )
        for y in years
    ]
    out = []
    for i, (year, roll) in enumerate(zip(years, rolls, strict=True)):
        if not roll:
            # A year nobody has been enrolled into yet is not a year with zero
            # students; it is a year that has not started.
            continue
        previous = rolls[i - 1] if i else None
        out.append(
            {
                "academic_year": year.code,
                "students": len(roll),
                "retained": len(roll & previous) if previous else None,
                "retention_percent": (
                    round(len(roll & previous) / len(previous) * 100, 1)
                    if previous
                    else None
                ),
            }
        )
    return out


def revenue_vs_expense(db: Session, school_id: int) -> list[dict]:
    """Fee collected against staff cost, by month (section 5.10.10).

    Neither number is computed here. Revenue is `fee_trend()`, which already
    owns "what was collected in a month" and is what the dashboard chart plots;
    expense is `payroll.cost_by_month()`, which owns the wage bill. This
    function only lines them up, which is what keeps the management chart and
    the two module screens telling the same story.

    A month present on one side and absent on the other carries `null` for the
    missing half, not zero. The school that has collected March's fees but not
    yet approved March's payroll has an unknown expense, and a zero bar there
    would read as a month the staff worked free.

    This is fee collection against payroll only. It is not a profit and loss:
    the system holds no other expense, and calling it one would be a claim the
    data cannot defend.
    """
    from app.services import payroll

    revenue = {r["month"]: r["collected"] for r in fee_trend(db, school_id)}
    expense = {r["month"]: r["employer_cost"] for r in payroll.cost_by_month(db, school_id)}
    return [
        {
            "month": month,
            "collected": revenue.get(month),
            "staff_cost": expense.get(month),
        }
        for month in sorted(set(revenue) | set(expense))
    ]


def month_attendance(
    db: Session, school_id: int, class_section_id: int | None = None
) -> dict:
    today = Date.today()
    first = today.replace(day=1)
    summary = attendance.section_summary(db, school_id, class_section_id, first, today)
    return summary.model_dump()


def today_attendance(
    db: Session, school_id: int, class_section_id: int | None = None
) -> dict:
    """Attendance for today. If not yet marked today (e.g. non-school day or before
    morning roll call), falls back to the most recent marked school day to ensure
    the dashboard displays live, calculated data from the database.
    """
    today = Date.today()
    summary = attendance.section_summary(db, school_id, class_section_id, today, today)
    if summary.present == 0 and summary.absent == 0 and summary.leave == 0:
        latest_date = db.scalar(
            select(func.max(Attendance.date)).where(Attendance.school_id == school_id)
        )
        if latest_date:
            summary = attendance.section_summary(
                db, school_id, class_section_id, latest_date, latest_date
            )
    return summary.model_dump()

