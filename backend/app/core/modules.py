"""The module registry — one of the plugin seams of ERP_BLUEPRINT §3.15.

Modules declare themselves here rather than being hardcoded in a navigation
list, a permission switch and a report filter separately. Everything that needs
to ask "is this module part of this school's product" reads this list, so
adding a module later is one entry, not a search for every place that assumed
the set was fixed.

`built` is honest bookkeeping: a module that is planned but not written yet can
still be listed and still be flagged off, and nothing pretends it works.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Module:
    code: str
    name: str
    built: bool
    default_enabled: bool


MODULES: list[Module] = [
    Module("students", "Students and enrolment", built=True, default_enabled=True),
    Module("attendance", "Attendance", built=True, default_enabled=True),
    Module("examinations", "Examinations", built=True, default_enabled=True),
    Module("fees", "Fees", built=True, default_enabled=True),
    Module("homework", "Homework (mobile app)", built=True, default_enabled=True),
    Module("communication", "Notices and communication", built=True, default_enabled=True),
    Module("admission", "Admission", built=False, default_enabled=True),
    Module("timetable", "Timetable", built=True, default_enabled=True),
    Module("hr", "HR and payroll", built=False, default_enabled=False),
    Module("transport", "Transport", built=True, default_enabled=False),
]

BY_CODE = {m.code: m for m in MODULES}
