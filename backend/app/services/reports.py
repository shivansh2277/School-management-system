"""Running a report, under the same permission and scope as the screen.

ERP_BLUEPRINT section 5.10.9 calls a report becoming a way to see rows you
cannot see directly **the most common data-leak path in an ERP**, and CLAUDE.md
records it happening here once already - four read paths carried `school_id`
without filtering on it and two genuinely leaked. So this module has one job
before it has any other: every report goes through the permission gate and the
scoping helpers, and none of them assembles its own query.

That is why the runners below are thin. Each one calls a function in the
service that owns the number - `fees.defaulters()`, `payroll.totals()`,
`attendance.shortage()` - and none of them writes arithmetic of its own. A
report that needed a number nobody owned got that number written in the owning
service first (see `stats.revenue_vs_expense` and `payroll.cost_by_month`);
never the other way round, because two definitions of one figure is how the fee
dashboard and the fee report come to disagree in front of a board.

The three rules from section 5.10.9 that show up as code here:

1. **Permission and scope, not one of them.** `_authorise()` demands the
   report's permission school-wide, so a guardian's own-children grant of
   `fees.invoice.read` cannot open the school's defaulter list, and then
   narrows a class teacher to the sections they actually teach.
2. **Context on every output.** `run()` returns the academic year, the filter
   set and the generation timestamp beside the data. A printed report with no
   context is one that gets misquoted in a board meeting.
3. **No fabricated data points.** Nothing here fills a gap. The owning
   functions already omit an empty month rather than emitting a zero bar, and
   this layer must not helpfully put it back.
"""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.report_registry import BY_CODE, PARAM_TYPES, REPORTS, Report, ReportScope
from app.models import PayrollRun, Route, RouteStatus, User, UserRole
from app.services import (
    admission_reports,
    attendance,
    comms,
    fees,
    payroll,
    school_settings,
    scoping,
    stats,
    tenancy,
    timetable,
    transport,
)
from app.services.rbac import Authz


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


def definition(code: str) -> Report:
    report = BY_CODE.get(code)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown report: {code}")
    return report


def _authorise(db: Session, user: User, authz: Authz, report: Report, params: dict) -> dict:
    """The gate, and the only place a report may decide who sees what.

    Returns the parameters, possibly narrowed. A caller restricted to their own
    sections comes back with `class_section_id` pinned, so the runner cannot
    forget to apply it - the restriction is in what is handed on, not in a flag
    somebody has to remember to read.
    """
    if report.module is not None:
        # A school with transport switched off has no transport reports. The
        # switch is enforced where the request lands, the same as everywhere
        # else; a switch the UI honours and the API does not is not a switch.
        school_settings.require_module(db, user.school_id, report.module)

    # Held at all, and held over the whole school. The second half is the one
    # that matters: a guardian holds `students.profile.read` and
    # `fees.invoice.read` over their own children, and without this a report
    # would be exactly the back door section 5.10.9 names.
    if not authz.can(report.permission) or not authz.is_school_wide(report.permission):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"This role does not have permission: {report.permission}",
        )

    if user.role is not UserRole.teacher:
        return params

    # Section 5.10.8 gives a class teacher their own section and nothing wider.
    # A teacher's permissions are unscoped by design - `attendance.record.read`
    # and `exam.marks.read` are both held school-wide, and the restriction has
    # always lived in the service (HANDOFF section 4). So the school-wide check
    # above does not stop them, and this is where it has to happen.
    if report.scope != ReportScope.section:
        raise scoping.forbidden(
            f"{report.name} covers the whole school, which is not yours to run"
        )
    section_id = params.get("class_section_id")
    if section_id is None:
        raise scoping.forbidden(
            f"{report.name} must name one of your class sections"
        )
    scoping.assert_teaches_section(db, user, section_id)
    return params


def _coerce(report: Report, raw: dict) -> dict:
    """Query strings into the arguments the owning functions expect."""
    unknown = set(raw) - set(report.params)
    if unknown:
        raise _bad(
            f"{report.code} does not take {', '.join(sorted(unknown))}."
            f" Its parameters are: {', '.join(report.params) or 'none'}"
        )
    missing = [p for p in report.required if raw.get(p) in (None, "")]
    if missing:
        raise _bad(f"{report.code} needs {', '.join(missing)}")

    out = {}
    for name, value in raw.items():
        if value in (None, ""):
            continue
        try:
            out[name] = PARAM_TYPES[name](value)
        except (ValueError, TypeError) as exc:
            raise _bad(f"{name}: {exc}") from exc
    return out


# --- the runners. Each one calls the function that owns its number. ---------


def _run_row(db: Session, school_id: int, run_id: int) -> PayrollRun:
    run = db.get(PayrollRun, run_id)
    if run is None or run.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payroll run not found")
    return run


def _transport_utilisation(db: Session, school_id: int) -> list[dict]:
    """`seats()` per active route - the utilisation figure section 5.6.10
    already defines, gathered rather than recalculated."""
    routes = db.scalars(
        select(Route).where(
            Route.school_id == school_id, Route.status == RouteStatus.active
        ).order_by(Route.code)
    )
    return [transport.seats(db, route) for route in routes]


RUNNERS = {
    "fees.daybook": lambda db, u, p: fees.daybook(
        db, u.school_id, p.get("on") or _today()
    ),
    "fees.defaulters": lambda db, u, p: fees.defaulters(
        db,
        u.school_id,
        min_amount=Decimal(p["min_amount"]) if "min_amount" in p else Decimal(0),
        class_section_id=p.get("class_section_id"),
        on=p.get("on"),
    ),
    "fees.collection": lambda db, u, p: fees.collection(db, p["year"], u.school_id),
    "attendance.summary": lambda db, u, p: attendance.section_summary(
        db, u.school_id, p.get("class_section_id"), p.get("date_from"), p.get("date_to")
    ).model_dump(),
    "attendance.absentees": lambda db, u, p: attendance.absentees(
        db, u.school_id, p.get("on") or _today(), p.get("class_section_id")
    ),
    "attendance.shortage": lambda db, u, p: attendance.shortage(
        db, u.school_id, p.get("threshold", 75.0), p.get("class_section_id")
    ),
    "academics.performance": lambda db, u, p: stats.performance(
        db, u.school_id, p.get("class_section_id")
    ),
    "academics.top_performers": lambda db, u, p: stats.top_performers(
        db, u.school_id, p.get("limit", 3)
    ),
    "timetable.workload": lambda db, u, p: timetable.workload(db, u.school_id),
    "timetable.completeness": lambda db, u, p: timetable.completeness(
        db, u.school_id, tenancy.current_year(db, u.school_id).id
    ),
    "payroll.register": lambda db, u, p: payroll.register(
        db, _run_row(db, u.school_id, p["run_id"]), p["code"]
    ),
    "payroll.cost_by_department": lambda db, u, p: payroll.cost_by_department(
        db, _run_row(db, u.school_id, p["run_id"])
    ),
    "payroll.cost_by_month": lambda db, u, p: payroll.cost_by_month(db, u.school_id),
    "transport.utilisation": lambda db, u, p: _transport_utilisation(db, u.school_id),
    "transport.expiring_papers": lambda db, u, p: transport.expiring_papers(
        db, u.school_id, **({"within_days": p["within_days"]} if "within_days" in p else {})
    ),
    "comms.unreachable": lambda db, u, p: comms.unreachable_contacts(db, u.school_id),
    "admission.funnel": lambda db, u, p: admission_reports.funnel(
        db, u.school_id, p["cycle_id"]
    ),
    "admission.seat_utilisation": lambda db, u, p: admission_reports.seat_utilisation(
        db, u.school_id, p["cycle_id"]
    ),
    "management.enrolment_trend": lambda db, u, p: stats.enrolment_trend(db, u.school_id),
    "management.student_teacher_ratio": lambda db, u, p: stats.student_teacher_ratio(
        db, tenancy.current_year(db, u.school_id)
    ),
    "management.revenue_vs_expense": lambda db, u, p: stats.revenue_vs_expense(
        db, u.school_id
    ),
}


def _today():
    from datetime import date as Date

    return Date.today()


def _may_run(db: Session, user: User, authz: Authz, report: Report) -> bool:
    """The library filter: the same three questions `_authorise` asks, minus
    the per-section one, which needs a section id the library does not have."""
    if report.module is not None and not school_settings.enabled(
        db, user.school_id, report.module
    ):
        return False
    if not (authz.can(report.permission) and authz.is_school_wide(report.permission)):
        return False
    return user.role is not UserRole.teacher or report.scope == ReportScope.section


def available(db: Session, user: User, authz: Authz) -> list[dict]:
    """The library (section 5.10.3), showing only what this caller could run.

    A library that lists a report and then refuses it teaches people to ignore
    it - and it leaks the shape of what it is hiding, which for a report named
    "Payroll cost by department" is itself worth not saying.
    """
    return [
        {
            "code": report.code,
            "name": report.name,
            "category": report.category,
            "permission": report.permission,
            "scope": report.scope,
            "required": list(report.required),
            "optional": list(report.optional),
            "description": report.description,
        }
        for report in REPORTS
        if _may_run(db, user, authz, report)
    ]


def run(db: Session, user: User, authz: Authz, code: str, raw: dict) -> dict:
    """One report, with the context section 5.10.9 requires stated on it."""
    report = definition(code)
    params = _coerce(report, raw)
    params = _authorise(db, user, authz, report, params)

    data = RUNNERS[report.code](db, user, params)
    year = tenancy.current_year(db, user.school_id)
    return {
        "report": {
            "code": report.code,
            "name": report.name,
            "category": report.category,
            "scope": report.scope,
        },
        # Section 5.10.9: academic year, filter set and generation timestamp,
        # on the output rather than in the request that produced it. The
        # filters are echoed back as they were applied, not as they were asked
        # for, so a teacher's report says which section it was narrowed to.
        "meta": {
            "academic_year": year.code,
            "filters": {k: str(v) for k, v in sorted(params.items())},
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "generated_by": user.full_name,
        },
        "data": data,
    }
