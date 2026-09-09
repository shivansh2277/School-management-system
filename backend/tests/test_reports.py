"""The report library: the gate, the context, and the numbers reconciling.

ERP_BLUEPRINT section 5.10.9 calls a report becoming a way to see rows you
cannot see directly the most common data-leak path in an ERP, and CLAUDE.md
records that leak happening in this codebase once already. So most of what is
pinned here is the gate rather than the arithmetic: who is refused, what a
class teacher is narrowed to, and that the download shows the same rows as the
screen.

The other half is reconciliation. A report calls the function that owns its
number, so the test that matters is that the report and the module screen give
the same answer - not that either gives a particular one.
"""

import csv
import io

import pytest
from sqlalchemy import select

from app.core.report_registry import BY_CODE, REPORTS
from app.models import AuditAction, AuditLog
from app.services import fees, payroll, school_settings

YEAR, MONTH = 2026, 8


@pytest.fixture()
def all_modules(db, admin_user):
    """HR and transport default to off; the demo school has both."""
    school_settings.set_many(
        db, admin_user, {"feature.hr": True, "feature.transport": True}
    )
    return True


@pytest.fixture()
def approved_run(db, admin_user):
    run = payroll.open_run(db, admin_user, year=YEAR, month=MONTH)
    payroll.calculate(db, admin_user, run)
    payroll.approve(db, admin_user, run)
    return run


def _cycle_id(client, admin):
    r = client.get("/admin/admission/cycles", headers=admin)
    rows = r.json() if r.status_code == 200 else []
    rows = rows.get("items", rows) if isinstance(rows, dict) else rows
    return rows[0]["id"] if rows else None


# --- the library


def test_the_library_lists_reports_by_category(client, admin, all_modules):
    body = client.get("/admin/reports", headers=admin).json()
    assert body["categories"]
    codes = {r["code"] for r in body["reports"]}
    assert "fees.defaulters" in codes
    assert "management.revenue_vs_expense" in codes
    # Every entry says what it needs before anybody runs it (section 5.10.4).
    for r in body["reports"]:
        assert r["permission"] and r["scope"] in ("school", "section")


def test_a_module_that_is_off_has_no_reports(client, admin, db, admin_user):
    """A switch the UI honours and the API does not is not a switch."""
    school_settings.set_many(db, admin_user, {"feature.transport": False})
    codes = {r["code"] for r in client.get("/admin/reports", headers=admin).json()["reports"]}
    assert "transport.utilisation" not in codes
    assert client.get("/admin/reports/transport.utilisation", headers=admin).status_code == 404


def test_the_library_hides_what_the_caller_could_not_run(client, teacher, all_modules):
    """A library that lists a report and then refuses it teaches people to
    ignore it - and 'Payroll cost by department' leaks its own shape."""
    codes = {r["code"] for r in client.get("/admin/reports", headers=teacher).json()["reports"]}
    assert "payroll.cost_by_month" not in codes
    assert "fees.defaulters" not in codes
    assert "attendance.shortage" in codes  # section-scoped, and theirs to run


# --- every report actually runs


def test_every_registered_report_runs(client, admin, db, all_modules, approved_run):
    """The parity check. A registry entry whose function has drifted - a
    renamed argument, a changed signature - is otherwise only discovered by
    whoever opens that one report in front of somebody."""
    cycle_id = _cycle_id(client, admin)
    supply = {
        "year": str(YEAR),
        "run_id": str(approved_run.id),
        "code": "BASIC",
        "cycle_id": str(cycle_id) if cycle_id else None,
    }
    ran, skipped = [], []
    for report in REPORTS:
        params = {p: supply[p] for p in report.required}
        if any(v is None for v in params.values()):
            skipped.append(report.code)
            continue
        r = client.get(f"/admin/reports/{report.code}", headers=admin, params=params)
        assert r.status_code == 200, f"{report.code}: {r.status_code} {r.text}"
        assert "data" in r.json()
        ran.append(report.code)
    assert len(ran) >= len(REPORTS) - len(skipped)
    assert not skipped, f"no fixture data for {skipped}"


def test_every_report_states_its_year_filters_and_timestamp(client, admin):
    """Section 5.10.9, on the output rather than in the request."""
    body = client.get(
        "/admin/reports/fees.collection", headers=admin, params={"year": YEAR}
    ).json()
    assert body["meta"]["academic_year"]
    assert body["meta"]["filters"] == {"year": str(YEAR)}
    assert body["meta"]["generated_at"]
    assert body["meta"]["generated_by"]


# --- the gate


def test_a_guardian_cannot_run_the_schools_defaulter_list(client, parent):
    """A guardian holds `fees.invoice.read` over their own children. Without
    the school-wide demand, this report is how they read everybody else's."""
    assert client.get("/admin/reports/fees.defaulters", headers=parent).status_code == 403


def test_a_teacher_cannot_run_a_whole_school_report(client, teacher, all_modules):
    """Section 5.10.8 gives a class teacher their own section. A teacher holds
    `attendance.record.read` school-wide - the restriction has always lived in
    the service (HANDOFF section 4), so the school-wide check cannot be what
    stops them."""
    r = client.get("/admin/reports/academics.top_performers", headers=teacher)
    assert r.status_code == 403, r.text


def test_a_teacher_must_name_a_section_and_it_must_be_theirs(
    client, teacher, ids, db
):
    from app.models import ClassSection

    # No section at all: the whole school by omission is the failure mode.
    assert (
        client.get("/admin/reports/attendance.shortage", headers=teacher).status_code
        == 403
    )
    # Their own section: allowed.
    own = client.get(
        "/admin/reports/attendance.shortage",
        headers=teacher,
        params={"class_section_id": ids["section_10a"]},
    )
    assert own.status_code == 200, own.text
    # Somebody else's: refused.
    others = db.scalars(
        select(ClassSection).where(ClassSection.school_id == ids["school"])
    ).all()
    foreign = next(s for s in others if s.id != ids["section_10a"])
    r = client.get(
        "/admin/reports/attendance.shortage",
        headers=teacher,
        params={"class_section_id": foreign.id},
    )
    assert r.status_code == 403, "a teacher ran a report on a section they do not teach"


def _login(client, login_id, password, role="admin"):
    r = client.post(
        "/auth/login", json={"role": role, "login_id": login_id, "password": password}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_a_fee_collector_cannot_run_a_payroll_report(client, all_modules):
    """Each report carries its own permission, so holding one module's does not
    open another's. The counter clerk exists to make section 5.5.9's
    segregation demonstrable, and it reaches reports too."""
    counter = _login(client, "counter@sunrisepublic.edu", "Admin@123")
    # It can run the fee reports its own role is for.
    assert client.get("/admin/reports/fees.defaulters", headers=counter).status_code == 200
    # And not what every colleague is paid.
    assert (
        client.get("/admin/reports/payroll.cost_by_month", headers=counter).status_code
        == 403
    )


# --- parameters


def test_an_unknown_report_is_a_404(client, admin):
    assert client.get("/admin/reports/fees.invented", headers=admin).status_code == 404


def test_a_missing_required_parameter_says_which(client, admin):
    r = client.get("/admin/reports/fees.collection", headers=admin)
    assert r.status_code == 422
    assert "year" in r.text


def test_an_unknown_parameter_is_refused_not_ignored(client, admin):
    """The registry declares what a report takes, so nothing else can be
    passed - which is also why there is no ad-hoc query builder here."""
    r = client.get(
        "/admin/reports/fees.collection",
        headers=admin,
        params={"year": YEAR, "school_id": 999},
    )
    assert r.status_code == 422
    assert "school_id" in r.text


def test_a_parameter_of_the_wrong_type_is_refused(client, admin):
    r = client.get("/admin/reports/fees.daybook", headers=admin, params={"on": "last tuesday"})
    assert r.status_code == 422


# --- reconciliation and honesty


def test_the_defaulter_report_and_the_office_screen_agree(client, admin, db, ids):
    """One definition, not two queries that drift. `fees.defaulters()` was
    moved out of its route precisely so the chase and the screen could agree;
    the report is the third caller."""
    reported = client.get("/admin/reports/fees.defaulters", headers=admin).json()["data"]
    owned = fees.defaulters(db, ids["school"])
    assert [r["student_id"] for r in reported] == [r["student_id"] for r in owned]


def test_the_collection_report_matches_the_fee_service(client, admin, db, ids):
    reported = client.get(
        "/admin/reports/fees.collection", headers=admin, params={"year": 2026}
    ).json()["data"]
    owned = fees.collection(db, 2026, ids["school"])
    assert reported["collected"] == str(owned["collected"])
    assert len(reported["months"]) == len(owned["months"])


def test_a_month_with_no_invoices_shows_no_row(client, admin):
    """No fabricated data points (section 5.10.9): a month with no invoices
    shows no bar, not a zero bar."""
    months = client.get(
        "/admin/reports/fees.collection", headers=admin, params={"year": 2026}
    ).json()["data"]["months"]
    assert months
    assert len(months) < 12
    assert all(m["billed"] != "0.00" for m in months)


# --- export


def test_a_report_export_is_audited(client, admin, db, ids):
    """Section 5.10.9's audit is not only for the student roster. A defaulter
    list is a list of families and what they owe."""
    r = client.get("/admin/reports/fees.defaulters/export", headers=admin)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")

    row = db.scalars(
        select(AuditLog)
        .where(AuditLog.action == AuditAction.export)
        .order_by(AuditLog.id.desc())
    ).first()
    assert row is not None
    assert row.entity_type == "report:fees.defaulters"
    assert row.school_id == ids["school"]
    assert row.after["rows"] > 0


def test_the_export_shows_the_same_rows_as_the_screen(client, admin):
    """The download runs the identical `run()` the screen does, not a second
    query written for the file."""
    on_screen = client.get("/admin/reports/fees.defaulters", headers=admin).json()["data"]
    body = client.get("/admin/reports/fees.defaulters/export", headers=admin).text
    rows = list(csv.DictReader(io.StringIO("\n".join(body.splitlines()[1:]))))
    assert len(rows) == len(on_screen)
    assert [r["student_id"] for r in rows] == [str(r["student_id"]) for r in on_screen]


def test_the_export_carries_the_context_line(client, admin):
    line = client.get("/admin/reports/fees.defaulters/export", headers=admin).text.splitlines()[0]
    assert line.startswith("#")
    assert "Fee defaulters" in line
    assert "academic year" in line


def test_a_teacher_cannot_export_what_they_cannot_run(client, teacher):
    r = client.get("/admin/reports/fees.defaulters/export", headers=teacher)
    assert r.status_code == 403


# --- the registry itself


def test_every_report_names_a_permission_that_exists():
    """A typo here is a report that nobody can run, or worse, one whose gate
    silently never matches."""
    from app.core.permissions import PERMISSIONS

    known = {c for c, _ in PERMISSIONS}
    for report in REPORTS:
        assert report.permission in known, report.code


def test_every_report_names_a_module_that_exists():
    from app.core.modules import BY_CODE as MODULES

    for report in REPORTS:
        assert report.module is None or report.module in MODULES, report.code


def test_every_declared_parameter_can_be_coerced():
    from app.core.report_registry import PARAM_TYPES

    for report in REPORTS:
        for name in report.params:
            assert name in PARAM_TYPES, f"{report.code}: {name}"


def test_every_report_has_a_runner():
    from app.services.reports import RUNNERS

    assert set(RUNNERS) == set(BY_CODE)
