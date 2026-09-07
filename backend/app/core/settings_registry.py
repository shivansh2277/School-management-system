"""The setting vocabulary: level 1 and level 3 of ERP_BLUEPRINT §3.15.

Like the permission list, the vocabulary belongs to the software — a school
chooses values, it does not invent keys. Declaring the type and the default
here is what makes the store *typed* key/value rather than a bag of strings
every reader has to guess at.

Feature flags are not a second mechanism. A flag is a boolean setting named
`feature.<module>`, generated from the module registry, so a new module cannot
be added without its switch existing.

The list is short on purpose. Fee rules, grading scales and payroll rates are
settings too, but each belongs with the code that reads it — Parts 3 and 4 add
their keys here as they build the consumers. A registry of keys nothing reads
is documentation pretending to be configuration.
"""

from dataclasses import dataclass
from typing import Any

from app.core.modules import MODULES


@dataclass(frozen=True)
class SettingDef:
    key: str
    type: type
    default: Any
    description: str


SETTINGS: list[SettingDef] = [
    # --- fees (§0.6, locked). Values, not code: a school changes the sibling
    # concession without a deployment, and the number that bills is the number
    # on the configuration screen.
    SettingDef(
        "fees.sibling_concession_percent",
        int,
        10,
        "Discount for a sibling of a child already enrolled, as a percentage",
    ),
    SettingDef("fees.due_day", int, 10, "Day of the month a monthly invoice falls due"),
    # The late-fee rule of §0.6, as four numbers rather than one formula buried
    # in code. The cap exists because 100/day uncapped passes a monthly fee
    # inside two months; a school wanting a gentler rule changes these values.
    SettingDef(
        "fees.late_fee.grace_days", int, 5, "Days past due before any late fee applies"
    ),
    SettingDef(
        "fees.late_fee.initial", int, 300, "Late fee charged once the grace period ends"
    ),
    SettingDef("fees.late_fee.per_day", int, 100, "Added per further day overdue"),
    SettingDef(
        "fees.late_fee.cap_percent",
        int,
        50,
        "Late fee ceiling, as a percentage of the invoice",
    ),
    # §5.7.9: exceeding this needs an override with a reason, not a silent
    # accept. The number differs by school, so it is not a constant.
    SettingDef(
        "timetable.max_periods_per_week",
        int,
        30,
        "Maximum teaching periods one teacher may be scheduled per week",
    ),
    *(
        SettingDef(
            f"feature.{m.code}",
            bool,
            m.default_enabled,
            f"Enable the {m.name} module",
        )
        for m in MODULES
    ),
]

BY_KEY = {s.key: s for s in SETTINGS}
DEFAULTS = {s.key: s.default for s in SETTINGS}
