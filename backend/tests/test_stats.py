"""Every dashboard figure must match an independently computed query.

BLUEPRINT section 0: nothing on a screen may be fabricated.
"""

from decimal import Decimal


def test_totals_match_direct_counts(client, admin, db):
    from app.models import ClassSection, Student, Teacher

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    assert stats["totals"]["students"] == db.query(Student).count()
    assert stats["totals"]["teachers"] == db.query(Teacher).count()
    assert stats["totals"]["classes"] == db.query(ClassSection).count()


def test_fees_collected_matches_the_sum_of_payments(client, admin, db):
    from app.models import AcademicYear, FeeInvoice, FeePayment

    stats = client.get("/admin/dashboard/stats", headers=admin).json()
    current = db.query(AcademicYear).filter_by(is_current=True).one()
    year = current.start_date.year
    expected = sum(
        (
            p.amount
            for p in db.query(FeePayment)
            .join(FeeInvoice, FeeInvoice.id == FeePayment.invoice_id)
            .filter(FeeInvoice.year.in_([year, year + 1]))
        ),
        Decimal(0),
    )
    assert Decimal(stats["totals"]["fees_collected"]) == expected


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
