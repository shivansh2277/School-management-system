"""Every dashboard figure must match an independently computed query.

BLUEPRINT section 0: nothing on a screen may be fabricated.
"""

from decimal import Decimal


def test_totals_match_direct_counts(client, admin, db):
    """Each headline number is the count it claims to be.

    Two things narrow the teacher count, and the test needs both or it proves
    nothing.

    The *user account* must be active, not merely the employee row. Those were
    the same number until the demo gained drivers, who are staff records
    without a working login — §5.6.8 gives a driver app access "later".

    And the employee must be **teaching staff**. This assertion previously
    counted every active employee and called the result `teachers`, which is
    how the Transport Manager came to be one: the demo school reported 13
    against its 12, and §5.10.10's student:teacher ratio inherited the error
    from the field it is built on. A test that mirrors the implementation
    rather than the intent will agree with a bug forever, which is what this
    one did.
    """
    from sqlalchemy import func, select

    from app.models import ClassSection, Employee, EmployeeType, Student, User

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    assert stats["totals"]["students"] == db.query(Student).count()
    assert stats["totals"]["classes"] == db.query(ClassSection).count()

    active_staff = db.scalar(
        select(func.count())
        .select_from(Employee)
        .join(User, User.id == Employee.user_id)
        .where(User.is_active)
    )
    active_teaching = db.scalar(
        select(func.count())
        .select_from(Employee)
        .join(User, User.id == Employee.user_id)
        .where(User.is_active, Employee.employee_type == EmployeeType.teaching)
    )
    assert stats["totals"]["teachers"] == active_teaching
    assert active_teaching < active_staff, (
        "the demo has non-teaching staff, or this assertion proves nothing"
    )
    assert active_staff < db.query(Employee).count(), (
        "the demo has staff without a login, or this assertion proves nothing"
    )


def test_fees_collected_matches_the_allocated_payments(client, admin, db):
    from sqlalchemy import func, select

    from app.models import AcademicYear, FeeInvoice, FeeInvoiceLine, PaymentAllocation

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    current = db.query(AcademicYear).filter_by(is_current=True).one()
    year = current.start_date.year
    # Collection is what was allocated to invoices of those years, not the sum
    # of payments: an advance is money held, not revenue for a month unbilled.
    expected = db.scalar(
        select(func.coalesce(func.sum(PaymentAllocation.amount), 0))
        .join(FeeInvoiceLine, FeeInvoiceLine.id == PaymentAllocation.invoice_line_id)
        .join(FeeInvoice, FeeInvoice.id == FeeInvoiceLine.invoice_id)
        .where(FeeInvoice.period_year.in_([year, year + 1]))
    )
    assert Decimal(stats["totals"]["fees_collected"]) == Decimal(expected)


def test_performance_buckets_cover_every_scored_student(client, admin, db):
    from app.models import Student

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    buckets = stats["performance"]
    assert sum(buckets.values()) == db.query(Student).count()
    assert all(v > 0 for v in buckets.values()), buckets  # seed must populate all four


def test_top_performers_are_the_actual_top_three(client, admin):
    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    top = stats["top_performers"]
    assert len(top) == 3
    assert [t["average_percent"] for t in top] == sorted(
        (t["average_percent"] for t in top), reverse=True
    )
    assert len({t["average_percent"] for t in top}) == 3  # no tie in the demo data


def test_attendance_overview_is_internally_consistent(client, admin):
    a = client.get("/admin/dashboard/stats", headers=admin).json()["attendance"]
    total = a["present"] + a["absent"] + a["leave"]
    if total == 0:
        assert a["percent"] is None  # an empty month reports nothing, not zero
    else:
        assert a["percent"] == round(a["present"] / total * 100, 1)


def test_fee_trend_carries_only_months_that_have_collections(client, admin):
    trend = client.get("/admin/dashboard/stats", headers=admin).json()["fee_trend"]
    assert trend
    assert all(Decimal(p["collected"]) > 0 for p in trend)


def test_today_schedule_is_todays_periods(client, admin, db):
    from datetime import date

    from app.models import TimetableSlot
    from app.services.stats import DAY_KEYS

    rows = client.get("/admin/dashboard/stats", headers=admin).json()["today_schedule"]
    key = DAY_KEYS[date.today().weekday()]
    expected = (
        0 if key is None else db.query(TimetableSlot).filter(TimetableSlot.day_of_week == key).count()
    )
    assert len(rows) == expected


def test_settings_accepts_its_own_get_body_back(client, admin, db):
    """Save on /settings posts the whole GET response back, and must work.

    `academic_year` is returned by the GET (the screen shows it) and used to be
    rejected by the PATCH's `extra="forbid"`, so every Save 422'd and the
    screen had never saved anything. It stays read-only — the year is an
    AcademicYear row, not a school column — but posting it back is not an
    error.
    """
    from app.models import School

    before = client.get("/admin/settings", headers=admin)
    assert before.status_code == 200
    body = {**before.json(), "city": "Kanpur"}

    saved = client.patch("/admin/settings", json=body, headers=admin)
    assert saved.status_code == 200, saved.json()
    assert saved.json()["city"] == "Kanpur"
    # The year is unchanged and was not written onto the school row.
    assert saved.json()["academic_year"] == before.json()["academic_year"]
    school = db.get(School, 1)
    db.refresh(school)
    assert not hasattr(school, "academic_year") or getattr(school, "academic_year") is None


def test_settings_still_refuses_an_unknown_field(client, admin):
    """The accept-and-ignore above is one named field, not a hole in the model."""
    bad = client.patch("/admin/settings", json={"nonsense": "x"}, headers=admin)
    assert bad.status_code == 422
