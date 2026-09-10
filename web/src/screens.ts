/**
 * Every screen in the app, declared once.
 *
 * The sidebar and the router are both derived from this list, so a menu item
 * cannot point at a route that refuses you and a route cannot exist without
 * declaring the permissions its API requires. They cannot disagree, because
 * there is only one statement of the fact.
 *
 * This is the same shape the backend already uses to stop things drifting
 * apart: core/permissions.py, core/modules.py, core/message_templates.py and
 * core/report_registry.py. Adding a screen in a later slice is one entry here
 * plus the component - navigation, routing, permission gating and module
 * hiding all follow.
 *
 * ## What a screen declares
 *
 * A screen makes several API calls and they do not all sit behind the same
 * gate, so both fields are lists and **all** of them are required. Declaring
 * one permission per screen is what let /attendance be gated on an exam
 * permission, and what let /settings call a fees-module route while declaring
 * no module at all.
 *
 * The set is **what the screen needs to load** - the endpoints it queries on
 * mount, and their gates as the backend actually declares them. Write
 * endpoints are deliberately excluded: requiring `fees.invoice.generate`
 * because the Fees screen has a Generate button would hide the whole screen
 * from a fee collector, who is exactly the person meant to use it. A write the
 * caller may not perform is refused at the route with a 403.
 *
 * A call that only powers a secondary widget - an optional filter, a picker on
 * a form - is gated at that widget instead, because hiding a whole screen over
 * one dropdown costs a role more than the broken dropdown does. `useClasses`
 * and the fee-plan panel on /settings both do this. The test suite pins which
 * roles that protects.
 *
 * Read the backend router before adding an entry. Several endpoints are not in
 * the file their name suggests: `/admin/subjects` and `/admin/timetable` are
 * served by `api/admin/classes.py` on `academics.class.read`, and
 * `/admin/grade-bands` by `api/admin/stats.py` on `admin.settings.read`.
 */
import { lazy, type ComponentType, type LazyExoticComponent } from "react";

/** The eleven codes in backend app/core/modules.py. */
export type ModuleCode =
  | "students"
  | "attendance"
  | "examinations"
  | "fees"
  | "homework"
  | "communication"
  | "admission"
  | "timetable"
  | "hr"
  | "transport"
  | "reports";

export type Screen = {
  path: string;
  label: string;
  group: string;
  /**
   * Every permission the screen's read path needs. Must all be codes in
   * backend app/core/permissions.py. Pinned by a test.
   */
  permissions: string[];
  /** Hidden entirely unless the school has all of these modules switched on. */
  modules?: ModuleCode[];
  element: LazyExoticComponent<ComponentType>;
};

export const SCREENS: Screen[] = [
  {
    path: "/dashboard",
    label: "Dashboard",
    group: "Overview",
    // GET /admin/dashboard/stats - stats.py, admin.settings.read, ungated.
    permissions: ["admin.settings.read"],
    element: lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard }))),
  },
  {
    path: "/students",
    label: "Students",
    group: "People",
    // GET /admin/students + /admin/students/{id} - students.py,
    // students.profile.read, module students.
    //
    // Also GET /admin/classes (useClasses, academics.class.read), which is NOT
    // declared: it only fills the "all classes" filter and the create form. A
    // fee collector holds students.profile.read and not academics.class.read,
    // and looking a child up at the counter is exactly their job - declaring it
    // would hide the roster from the one role that needs it most. useClasses
    // skips the call instead.
    permissions: ["students.profile.read"],
    modules: ["students"],
    element: lazy(() => import("./pages/Students").then((m) => ({ default: m.Students }))),
  },
  {
    path: "/teachers",
    label: "Staff",
    group: "People",
    // GET /admin/teachers - teachers.py, hr.employee.read, module hr.
    permissions: ["hr.employee.read"],
    modules: ["hr"],
    element: lazy(() => import("./pages/Teachers").then((m) => ({ default: m.Teachers }))),
  },
  {
    path: "/classes",
    label: "Classes",
    group: "Academics",
    // GET /admin/classes, /admin/classes/{id}/students and /admin/timetable -
    // all classes.py, all academics.class.read, all ungated. The timetable
    // grid this screen draws comes from the classes router, not the gated
    // timetable one, so it does not depend on the timetable module.
    permissions: ["academics.class.read"],
    element: lazy(() => import("./pages/Classes").then((m) => ({ default: m.Classes }))),
  },
  {
    path: "/attendance",
    label: "Attendance",
    group: "Academics",
    // GET /admin/attendance + /admin/attendance/summary - attendance.py,
    // attendance.record.read, module attendance.
    // GET /admin/classes (useClasses) - academics.class.read.
    permissions: ["attendance.record.read", "academics.class.read"],
    modules: ["attendance"],
    element: lazy(() => import("./pages/Attendance").then((m) => ({ default: m.Attendance }))),
  },
  {
    path: "/exams",
    label: "Exams",
    group: "Academics",
    // GET /admin/exams + /admin/exams/{id}/schedule - exams.py,
    // exam.definition.read, module examinations.
    // GET /admin/subjects and /admin/classes - classes.py, academics.class.read.
    // No system role holds the first without the second, but a school-defined
    // custom role can, and then the subject picker fails.
    permissions: ["exam.definition.read", "academics.class.read"],
    modules: ["examinations"],
    element: lazy(() => import("./pages/Exams").then((m) => ({ default: m.Exams }))),
  },
  {
    path: "/fees",
    label: "Fees",
    group: "Money",
    // GET /admin/fees/invoices + /admin/fees/collection - fees.py,
    // fees.invoice.read, module fees.
    permissions: ["fees.invoice.read"],
    modules: ["fees"],
    element: lazy(() => import("./pages/Fees").then((m) => ({ default: m.Fees }))),
  },
  {
    path: "/fees/collect",
    label: "Collect fees",
    group: "Money",
    // GET /admin/students (the search that is this screen's entry point) -
    // students.py, students.profile.read. GET /admin/fees/ledger/{student_id} -
    // fees.py, fees.invoice.read. Module fees.
    //
    // Both are required to load, not one: without the search there is no way
    // to reach a ledger at all, so the roster read is the primary control here
    // rather than a secondary widget. POST /admin/fees/payments
    // (fees.payment.collect) is a write and excluded per the note above; the
    // Take button gates itself on it.
    permissions: ["fees.invoice.read", "students.profile.read"],
    modules: ["fees"],
    element: lazy(() =>
      import("./pages/CollectFees").then((m) => ({ default: m.CollectFees })),
    ),
  },
  {
    path: "/fees/defaulters",
    label: "Defaulters",
    group: "Money",
    // GET /admin/fees/defaulters - fees.py, fees.invoice.read, module fees.
    //
    // Also GET /admin/classes (useClasses), undeclared on purpose and gated at
    // the widget: it is only the class filter, and a fee collector holds
    // fees.invoice.read without academics.class.read.
    permissions: ["fees.invoice.read"],
    modules: ["fees"],
    element: lazy(() =>
      import("./pages/Defaulters").then((m) => ({ default: m.Defaulters })),
    ),
  },
  {
    path: "/fees/setup",
    label: "Fee setup",
    group: "Money",
    // GET /admin/fees/plans, /admin/fees/concessions and /admin/fees/invoices
    // (to put a name against a concession's enrolment) - fee_setup.py and
    // fees.py, all on fees.invoice.read. Module fees.
    //
    // Also GET /admin/fees/heads and /admin/classes, both inside the Add plan
    // form and gated there rather than here.
    permissions: ["fees.invoice.read"],
    modules: ["fees"],
    element: lazy(() => import("./pages/FeeSetup").then((m) => ({ default: m.FeeSetup }))),
  },
  {
    path: "/fees/periods",
    label: "Period close",
    group: "Money",
    // GET /admin/fees/periods - fees.py, fees.invoice.read, module fees.
    // Closing and reopening need fees.payment.void, which is a write and so
    // gates itself on the button rather than hiding the screen from the clerk
    // who needs to see whether a month is shut.
    permissions: ["fees.invoice.read"],
    modules: ["fees"],
    element: lazy(() => import("./pages/FeePeriods").then((m) => ({ default: m.FeePeriods }))),
  },
  {
    path: "/notices",
    label: "Notices",
    group: "Communication",
    // GET /admin/notices - notices.py, comms.notice.read, module communication.
    //
    // Also GET /admin/classes (useClasses), undeclared for the same reason as
    // /students: it is the audience picker on the publish form, and a
    // receptionist holds comms.notice.read without academics.class.read.
    permissions: ["comms.notice.read"],
    modules: ["communication"],
    element: lazy(() => import("./pages/Notices").then((m) => ({ default: m.Notices }))),
  },
  {
    path: "/configuration",
    label: "Configuration",
    group: "Administration",
    // GET /admin/configuration and GET /admin/custom-fields - both
    // api/admin/settings.py, both on the module-level `reader` =
    // require_permission("admin.settings.read", school_wide=True), neither
    // behind a module gate. The writes (PUT /admin/configuration, POST and
    // DELETE /admin/custom-fields) need admin.settings.write and are excluded
    // per the note above: they gate themselves on their own controls, and
    // declaring the write permission here would hide the module switches from
    // a read-only auditor who is meant to be able to see them.
    //
    // No module is declared on purpose. This is the screen that turns modules
    // on, so gating it on one is how a school locks itself out of its own
    // configuration.
    permissions: ["admin.settings.read"],
    element: lazy(() =>
      import("./pages/Configuration").then((m) => ({ default: m.Configuration })),
    ),
  },
  {
    path: "/settings",
    label: "Settings",
    group: "Administration",
    // GET /admin/settings and /admin/grade-bands - stats.py,
    // admin.settings.read, ungated.
    //
    // This screen also calls GET /admin/fees/plans, which is fees.invoice.read
    // behind module fees. That is NOT declared here on purpose: Settings is
    // where a school edits its own name, branding and academic year, and
    // hiding all of it because the fees module is off would be a worse failure
    // than the one being fixed. The fee-plan panel gates itself inside the
    // page instead. A cross-module panel is a panel-level gate, not a
    // screen-level one.
    permissions: ["admin.settings.read"],
    element: lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings }))),
  },
];

type Can = (permission: string) => boolean;
type HasModule = (code: string) => boolean;

/** The first module this school has switched off, or undefined. */
export function missingModule(screen: Screen, hasModule: HasModule): ModuleCode | undefined {
  return (screen.modules ?? []).find((m) => !hasModule(m));
}

/** The first permission this caller does not hold, or undefined. */
export function missingPermission(screen: Screen, can: Can): string | undefined {
  return screen.permissions.find((p) => !can(p));
}

/** Screens this caller may actually open. Both gates, all of each, in order. */
export function visibleScreens(can: Can, hasModule: HasModule): Screen[] {
  return SCREENS.filter(
    (s) => missingModule(s, hasModule) === undefined && missingPermission(s, can) === undefined,
  );
}

/** The sidebar: visible screens, in registry order, grouped by `group`. */
export function groupedNav(
  can: Can,
  hasModule: HasModule,
): { group: string; screens: Screen[] }[] {
  const out: { group: string; screens: Screen[] }[] = [];
  for (const screen of visibleScreens(can, hasModule)) {
    const existing = out.find((g) => g.group === screen.group);
    if (existing) existing.screens.push(screen);
    else out.push({ group: screen.group, screens: [screen] });
  }
  return out;
}
