"""The section 5.10.10 management figures that had no owning function.

Most of what a report library needs already existed across the services. Four
KPIs did not: revenue versus expense by month, enrolment and retention trend,
student:teacher ratio, and chronic absenteeism. The fourth turned out to be
`attendance.shortage()` under another name and was left alone; these are the
other three, each written in the service that owns the data rather than in the
report that wanted it.

What is pinned here is mostly the honesty rules, because they are what a report
gets wrong: a number that reconciles with the screen it came from, and a gap
that stays a gap instead of becoming a zero.
"""

from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import AcademicYear, PayrollRunStatus, Payslip
from app.services import payroll, stats

YEAR, MONTH = 2026, 8


@pytest.fixture()
def approved_run(db, admin_user):
    """One month's payroll, taken all the way to approved."""
    run = payroll.open_run(db, admin_user, year=YEAR, month=MONTH)
    payroll.calculate(db, admin_user, run)
    payroll.approve(db, admin_user, run)
    return run


# --- student:teacher ratio


def test_the_ratio_uses_the_same_headcounts_as_the_dashboard(db, ids):
    """Section 5.10.9's reconciliation rule on the smallest possible number: if
    the ratio counted heads itself, a report and the dashboard could disagree
    about how many teachers the school has."""
    year = db.get(AcademicYear, ids["year"])
    counted = stats.totals(db, year)
    ratio = stats.student_teacher_ratio(db, year)
    assert ratio["students"] == counted["students"]
    assert ratio["teachers"] == counted["teachers"]
    assert ratio["ratio"] == round(counted["students"] / counted["teachers"], 1)


def test_a_school_with_no_teachers_gets_no_ratio_rather_than_a_crash(db, ids):
    """A real state during setup, and the obvious place for a divide by zero."""
    from app.models import Employee, User

    year = db.get(AcademicYear, ids["year"])
    for e in db.scalars(select(Employee).where(Employee.school_id == ids["school"])):
        db.get(User, e.user_id).is_active = False
    db.flush()
    assert stats.student_teacher_ratio(db, year)["ratio"] is None


# --- enrolment and retention trend


def test_the_first_year_has_no_retention_figure(db, ids):
    """There is no year before it to have retained anyone from. Reporting 0 or
    100 would be the fabricated data point section 5.10.9 forbids, and it is
    the one a trend line is most likely to be misread from."""
    trend = stats.enrolment_trend(db, ids["school"])
    assert trend, "the demo school has a roll"
    assert trend[0]["retention_percent"] is None
    assert trend[0]["retained"] is None
    assert trend[0]["students"] == 100


def test_retention_counts_the_children_who_came_back(db, ids):
    """A second year holding some of the first year's children."""
    from app.models import ClassSection, Enrolment, EnrolmentStatus

    school_id = ids["school"]
    first = db.get(AcademicYear, ids["year"])
    nxt = AcademicYear(
        school_id=school_id,
        code="2026-27",
        start_date="2026-04-01",
        end_date="2027-03-31",
    )
    db.add(nxt)
    db.flush()
    section = ClassSection(
        school_id=school_id,
        academic_year_id=nxt.id,
        class_name="10",
        section="A",
    )
    db.add(section)
    db.flush()
    stayed = list(
        db.scalars(
            select(Enrolment.student_id)
            .where(Enrolment.academic_year_id == first.id)
            .limit(30)
        )
    )
    for roll, student_id in enumerate(stayed, start=1):
        db.add(
            Enrolment(
                school_id=school_id,
                student_id=student_id,
                academic_year_id=nxt.id,
                class_section_id=section.id,
                roll_no=roll,
                status=EnrolmentStatus.active,
            )
        )
    db.flush()

    trend = stats.enrolment_trend(db, school_id)
    latest = trend[-1]
    assert latest["academic_year"] == "2026-27"
    assert latest["students"] == 30
    assert latest["retained"] == 30
    # 30 of the previous year's 100.
    assert latest["retention_percent"] == 30.0


def test_a_year_nobody_is_enrolled_into_yet_is_absent_not_zero(db, ids):
    """An empty year is a year that has not started, not a year with no
    children in it."""
    db.add(
        AcademicYear(
            school_id=ids["school"],
            code="2027-28",
            start_date="2027-04-01",
            end_date="2028-03-31",
        )
    )
    db.flush()
    assert "2027-28" not in [r["academic_year"] for r in stats.enrolment_trend(db, ids["school"])]


# --- revenue versus expense


def test_the_wage_bill_is_the_employer_cost_of_the_approved_run(db, ids, approved_run):
    """Employer cost, not net pay: the school's PF and ESI contributions are
    money it spends and no payslip pays out."""
    months = payroll.cost_by_month(db, ids["school"])
    row = next(r for r in months if r["month"] == f"{YEAR}-{MONTH:02d}")
    expected = db.scalar(
        select(Payslip)
        .where(Payslip.run_id == approved_run.id)
        .with_only_columns(Payslip.employer_cost)
    )
    assert expected is not None
    assert row["employer_cost"] == payroll.totals(db, approved_run)["employer_cost"]
    assert row["payslips"] == payroll.totals(db, approved_run)["payslips"]


def test_a_draft_run_is_not_yet_an_expense(db, ids, admin_user):
    """Somebody is still editing it. Putting it on a management chart would
    show a cost the school has not committed to."""
    run = payroll.open_run(db, admin_user, year=YEAR, month=MONTH)
    payroll.calculate(db, admin_user, run)
    assert run.status is PayrollRunStatus.calculated
    assert payroll.cost_by_month(db, ids["school"]) == []


def test_revenue_versus_expense_leaves_the_missing_half_null(db, ids):
    """The demo school has fee collections and no approved payroll run. A zero
    staff cost there would read as a month the staff worked free."""
    rows = stats.revenue_vs_expense(db, ids["school"])
    assert rows, "the demo ledger has collections"
    assert all(r["staff_cost"] is None for r in rows)
    assert any(r["collected"] is not None for r in rows)


def test_revenue_versus_expense_reuses_the_two_owning_functions(
    db, ids, approved_run
):
    """Neither number is computed in the chart. Revenue is `fee_trend()`, which
    is what the dashboard plots; expense is `cost_by_month()`. If either drifts
    from its owner, the management view and the module screen disagree."""
    school_id = ids["school"]
    rows = {r["month"]: r for r in stats.revenue_vs_expense(db, school_id)}
    for r in stats.fee_trend(db, school_id):
        assert rows[r["month"]]["collected"] == r["collected"]
    for r in payroll.cost_by_month(db, school_id):
        assert rows[r["month"]]["staff_cost"] == r["employer_cost"]
    # And the months are the union of the two sides, not the intersection: a
    # month present on one and absent on the other still appears.
    assert set(rows) == {r["month"] for r in stats.fee_trend(db, school_id)} | {
        r["month"] for r in payroll.cost_by_month(db, school_id)
    }
    assert rows[f"{YEAR}-{MONTH:02d}"]["staff_cost"] > Decimal(0)


def test_only_teaching_staff_count_as_teachers(db, ids):
    """`totals()` counted every active employee, so the Transport Manager was a
    teacher: the demo school read 13 against its 12, and section 5.10.10's
    student:teacher ratio inherited it. Found by running the report against the
    seeded database and not recognising the number."""
    from app.models import Employee, EmployeeType, User

    year = db.get(AcademicYear, ids["year"])
    teaching = db.scalar(
        select(func.count())
        .select_from(Employee)
        .join(User, User.id == Employee.user_id)
        .where(
            Employee.school_id == ids["school"],
            User.is_active,
            Employee.employee_type == EmployeeType.teaching,
        )
    )
    all_staff = db.scalar(
        select(func.count())
        .select_from(Employee)
        .join(User, User.id == Employee.user_id)
        .where(Employee.school_id == ids["school"], User.is_active)
    )
    assert teaching < all_staff, "the demo school has non-teaching staff to exclude"
    assert stats.totals(db, year)["teachers"] == teaching
    assert stats.student_teacher_ratio(db, year)["teachers"] == teaching
