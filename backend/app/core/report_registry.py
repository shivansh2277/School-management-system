"""The report library, declared rather than built (ERP_BLUEPRINT section 5.10.3).

A registry in code, the same shape as `core/permissions.py`, `core/modules.py`,
`core/message_templates.py` and `fees.OPT_IN_SOURCES`. Each entry names what a
report is called, who may run it, which module it belongs to, what parameters
it takes and how far it reaches. The function that actually produces the numbers
is wired in `services/reports.py`.

**Why this and not the four tables section 5.10.5 lists.** `saved_reports`,
`report_schedules`, `report_runs` and four summary tables were specified before
any of the modules underneath existed. Applying the test transport and
communication both used - does anything read it yet:

- `export_audit` is not here because `audit_log` already had the shape, and
  `AuditAction.export` is now written by the export routes. A second audit trail
  is a second place to forget to look.
- The four summary tables (`attendance_summary`, `fee_collection_summary`,
  `result_summary`, `admission_funnel_summary`) are a performance answer to a
  problem nobody has measured. 100 students and 300 invoices do not need them,
  and a materialised summary that can disagree with the ledger it summarises is
  exactly the drift section 5.10.9 forbids - bought in exchange for speed
  nobody has asked for.
- `report_runs` earns a table alongside asynchronous running. These reports are
  synchronous, so a run row would record something nobody reads.
- `saved_reports` and `report_schedules` are the two that are probably real, and
  neither is built here: a scheduled report emailing each Monday is
  `services/jobs.py` plus `comms.notify()`, both of which already exist, rather
  than a new mechanism.

What a registry buys that a table does not: a report cannot exist without
naming its permission, because the field is required to construct one.
"""

from dataclasses import dataclass
from datetime import date as Date


class ReportScope:
    """How far a report reaches.

    `school` covers the whole tenant; `section` is answerable about one class
    section and is the only kind a class teacher may run (section 5.10.8).
    """

    school = "school"
    section = "section"


# How a query-string value becomes the argument its function expects. Query
# parameters arrive as strings; a report that takes a date must get a date.
PARAM_TYPES: dict[str, type | object] = {
    "class_section_id": int,
    "route_id": int,
    "run_id": int,
    "cycle_id": int,
    "exam_id": int,
    "year": int,
    "month": int,
    "limit": int,
    "within_days": int,
    "threshold": float,
    "min_amount": str,  # Decimal is built from the string, never from a float
    "code": str,
    "on": Date.fromisoformat,
    "date_from": Date.fromisoformat,
    "date_to": Date.fromisoformat,
}


@dataclass(frozen=True)
class Report:
    code: str
    name: str
    category: str
    #: Checked at the route, and demanded school-wide. A guardian holds
    #: `students.profile.read` and `fees.invoice.read` over their own children;
    #: without the school-wide demand, a report would be the way they read
    #: everybody else's.
    permission: str
    #: The feature flag this report hides behind, if any. A school with
    #: transport switched off has no transport reports.
    module: str | None = None
    scope: str = ReportScope.school
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    description: str = ""

    @property
    def params(self) -> tuple[str, ...]:
        return self.required + self.optional


REPORTS: list[Report] = [
    # --- Fees
    Report(
        "fees.daybook",
        "Daily collection daybook",
        "Fees",
        "fees.invoice.read",
        module="fees",
        optional=("on",),
        description="Every payment taken on one day, by mode, with the day's total.",
    ),
    Report(
        "fees.defaulters",
        "Fee defaulters",
        "Fees",
        "fees.invoice.read",
        module="fees",
        optional=("class_section_id", "min_amount", "on"),
        description="Who owes what, worst first, with a contact to ring.",
    ),
    Report(
        "fees.collection",
        "Collection efficiency by month",
        "Fees",
        "fees.invoice.read",
        module="fees",
        required=("year",),
        description="Billed against collected for each month of a calendar year.",
    ),
    # --- Attendance
    Report(
        "attendance.summary",
        "Attendance summary",
        "Attendance",
        "attendance.record.read",
        module="attendance",
        scope=ReportScope.section,
        optional=("class_section_id", "date_from", "date_to"),
        description="Present, absent, late and leave over a date range.",
    ),
    Report(
        "attendance.absentees",
        "Absentees on a day",
        "Attendance",
        "attendance.record.read",
        module="attendance",
        scope=ReportScope.section,
        optional=("on", "class_section_id"),
        description="Who was away, with a guardian to telephone.",
    ),
    Report(
        "attendance.shortage",
        "Chronic absenteeism",
        "Attendance",
        "attendance.record.read",
        module="attendance",
        scope=ReportScope.section,
        optional=("threshold", "class_section_id"),
        description=(
            "Children below the attendance threshold, worst first. Section "
            "5.10.10's chronic absenteeism: the same list, seen in November "
            "rather than the week before the exam."
        ),
    ),
    # --- Academics
    Report(
        "academics.performance",
        "Performance distribution",
        "Academics",
        "exam.marks.read",
        module="examinations",
        scope=ReportScope.section,
        optional=("class_section_id",),
        description="How the latest marked exam fell across the grade bands.",
    ),
    Report(
        "academics.top_performers",
        "Top performers",
        "Academics",
        "exam.marks.read",
        module="examinations",
        optional=("limit",),
        description="The highest overall percentages in the latest marked exam.",
    ),
    # --- Timetable
    Report(
        "timetable.workload",
        "Teacher workload",
        "Timetable",
        "timetable.slot.read",
        module="timetable",
        description="Periods per teacher against the school's ceiling, and the spread.",
    ),
    Report(
        "timetable.completeness",
        "Timetable completeness",
        "Timetable",
        "timetable.slot.read",
        module="timetable",
        description="Which sections still have unfilled periods.",
    ),
    # --- HR and payroll
    Report(
        "payroll.register",
        "Statutory register",
        "Payroll",
        "payroll.run.read",
        module="hr",
        required=("run_id", "code"),
        description="Every payslip in a run carrying one salary component.",
    ),
    Report(
        "payroll.cost_by_department",
        "Payroll cost by department",
        "Payroll",
        "payroll.run.read",
        module="hr",
        required=("run_id",),
        description="What one run cost, split by the department people sit in.",
    ),
    Report(
        "payroll.cost_by_month",
        "Wage bill by month",
        "Payroll",
        "payroll.run.read",
        module="hr",
        description="Employer cost of every approved and paid run, by month.",
    ),
    # --- Transport
    Report(
        "transport.utilisation",
        "Route utilisation",
        "Transport",
        "transport.setup.read",
        module="transport",
        description="Seats taken against seats fitted, for every active route.",
    ),
    Report(
        "transport.expiring_papers",
        "Expiring compliance papers",
        "Transport",
        "transport.setup.read",
        module="transport",
        optional=("within_days",),
        description="Vehicle and crew documents lapsing, soonest first.",
    ),
    # --- Communication
    Report(
        "comms.unreachable",
        "Unreachable families",
        "Communication",
        "comms.message.read",
        module="communication",
        description=(
            "Guardians with no address on the only channel section 0.11 "
            "enabled. Open question T is decided by this number."
        ),
    ),
    # --- Admission
    Report(
        "admission.funnel",
        "Admission funnel",
        "Admission",
        "admission.application.read",
        module="admission",
        required=("cycle_id",),
        description="Enquiry through to enrolled, with the drop at each stage.",
    ),
    Report(
        "admission.seat_utilisation",
        "Seat utilisation",
        "Admission",
        "admission.application.read",
        module="admission",
        required=("cycle_id",),
        description="Seats configured, offered, taken and left, by class.",
    ),
    # --- Management. On `admin.settings.read`, the same permission the
    # executive dashboard already uses, because these are the whole-school
    # figures section 9.2 puts in front of a principal.
    Report(
        "management.enrolment_trend",
        "Enrolment and retention trend",
        "Management",
        "admin.settings.read",
        module="reports",
        description="Heads on the roll each year, and how many came back.",
    ),
    Report(
        "management.student_teacher_ratio",
        "Student:teacher ratio",
        "Management",
        "admin.settings.read",
        module="reports",
        description="Active students per active teacher.",
    ),
    Report(
        "management.revenue_vs_expense",
        "Revenue versus expense",
        "Management",
        "admin.settings.read",
        module="reports",
        description=(
            "Fee collected against staff cost, by month. Not a profit and "
            "loss: the system holds no other expense."
        ),
    ),
]

BY_CODE = {r.code: r for r in REPORTS}
CATEGORIES = list(dict.fromkeys(r.category for r in REPORTS))
