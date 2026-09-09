"""Every module switch is enforced at the route, for every router that serves it.

`core/modules.py` sells each module as something a school either buys or does
not. `school_settings.module_enabled` is the dependency that makes that true,
and its own docstring states the rule this file pins:

    A switch the UI honours and the API does not is not a switch.

Eleven routers declared a module in the registry and enforced nothing. The
sharpest was HR, which `default_enabled=False` — so a brand new school that had
never switched HR on still served its staff records, salary structures,
payslips and payroll runs to anyone holding the permissions. Permissions still
applied, so it was not open to everyone; but the flag the product sells as
"this module is off for you" did nothing at all.

The test is written against the *endpoints*, not the routers, because a router
can be split later and the promise is about the surface a school can reach.
`tests/test_reports.py::test_a_module_that_is_off_has_no_reports` is the same
property for the report library.
"""

import pytest

from app.core.modules import BY_CODE
from app.services import school_settings

# Every module-gated admin surface, by the switch that must hide it.
#
# One parameterless GET per router, chosen so a 404 can only mean the gate:
# these all answer 200 with the module on and the demo school's data.
GATED: dict[str, list[str]] = {
    "hr": [
        "/admin/employees",  # hr.py — staff records
        "/admin/departments",  # hr.py
        "/admin/teachers",  # teachers.py — the staff list
        "/admin/payroll/runs",  # payroll.py — payroll runs
        "/admin/payroll/components",  # payroll.py — salary structure
        "/admin/staff-attendance",  # staff_attendance.py — the staff register
        "/admin/staff-leave",  # staff_leave.py
        "/admin/staff-leave/types",  # staff_leave.py
    ],
    "examinations": [
        "/admin/exams",  # exams.py
        "/admin/grading-scales",  # grading.py
        "/admin/assessment-schemes",  # schemes.py
        "/admin/report-cards",  # report_cards.py
    ],
    "students": [
        "/admin/students",  # students.py
    ],
    "communication": [
        "/admin/notices",  # notices.py
    ],
}


def _set(db, admin_user, code: str, on: bool) -> None:
    school_settings.set_many(db, admin_user, {f"feature.{code}": on})


@pytest.mark.parametrize("code", sorted(GATED))
def test_switching_a_module_off_takes_its_endpoints_away(code, client, admin, db, admin_user):
    """Off means 404 on every endpoint, and on means the endpoint is reachable.

    Both halves matter. Asserting only the 404 would also pass if the route had
    been deleted, or if the path were misspelled — which is exactly how a gate
    test can agree with a broken gate forever.
    """
    _set(db, admin_user, code, True)
    for path in GATED[code]:
        assert client.get(path, headers=admin).status_code != 404, (
            f"{path} is not reachable with {code} on — the test would prove nothing"
        )

    _set(db, admin_user, code, False)
    for path in GATED[code]:
        assert client.get(path, headers=admin).status_code == 404, (
            f"{path} still answers with the {code} module switched off"
        )


def test_hr_is_off_for_a_new_school_and_payroll_is_not_reachable(client, admin, db, admin_user):
    """The specific defect, stated as its own case.

    `hr` ships `default_enabled=False`, so this is not a hypothetical
    configuration — it is what every new customer gets on day one. Named
    separately from the parametrised sweep so that if someone later flips the
    default, this fails and says why rather than quietly changing meaning.
    """
    assert BY_CODE["hr"].default_enabled is False

    _set(db, admin_user, "hr", False)
    for path in ("/admin/payroll/runs", "/admin/payroll/components", "/admin/employees"):
        assert client.get(path, headers=admin).status_code == 404


def test_a_module_being_off_hides_the_route_rather_than_refusing_it(client, admin, db, admin_user):
    """404, not 403.

    Which module a school has bought is not something the API should confirm to
    a caller, and the same choice is already made for `/public/{school_code}`
    where every refusal is deliberately identical.
    """
    _set(db, admin_user, "hr", False)
    r = client.get("/admin/payroll/runs", headers=admin)
    assert r.status_code == 404
    assert r.status_code != 403


def test_the_routers_left_ungated_have_no_module_to_gate_on(client, admin, db, admin_user):
    """`classes.py`, `settings.py` and `stats.py` are correctly ungated.

    They serve no module in the registry — a school cannot switch off its own
    class list, its settings or its dashboard. Pinned so a later sweep does not
    "fix" them by inventing a module code for them.
    """
    for code in ("hr", "examinations", "students", "communication"):
        _set(db, admin_user, code, False)

    for path in ("/admin/classes", "/admin/settings", "/admin/dashboard/stats"):
        assert client.get(path, headers=admin).status_code == 200, path
