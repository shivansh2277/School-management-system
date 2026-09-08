/**
 * Every screen in the app, declared once.
 *
 * The sidebar and the router are both derived from this list, so a menu item
 * cannot point at a route that refuses you and a route cannot exist without
 * declaring the permission its API requires. They cannot disagree, because
 * there is only one statement of the fact.
 *
 * This is the same shape the backend already uses to stop things drifting
 * apart: core/permissions.py, core/modules.py, core/message_templates.py and
 * core/report_registry.py. Adding a screen in a later slice is one entry here
 * plus the component - navigation, routing, permission gating and module
 * hiding all follow.
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
  /** Must be a code in backend app/core/permissions.py. Pinned by a test. */
  permission: string;
  /** Hidden entirely when the school has this module switched off. */
  module?: ModuleCode;
  element: LazyExoticComponent<ComponentType>;
};

export const SCREENS: Screen[] = [
  {
    path: "/",
    label: "Dashboard",
    group: "Overview",
    permission: "admin.settings.read",
    element: lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard }))),
  },
  {
    path: "/students",
    label: "Students",
    group: "People",
    permission: "students.profile.read",
    module: "students",
    element: lazy(() => import("./pages/Students").then((m) => ({ default: m.Students }))),
  },
  {
    path: "/teachers",
    label: "Staff",
    group: "People",
    permission: "hr.employee.read",
    element: lazy(() => import("./pages/Teachers").then((m) => ({ default: m.Teachers }))),
  },
  {
    path: "/classes",
    label: "Classes",
    group: "Academics",
    permission: "academics.class.read",
    element: lazy(() => import("./pages/Classes").then((m) => ({ default: m.Classes }))),
  },
  {
    path: "/attendance",
    label: "Attendance",
    group: "Academics",
    permission: "attendance.record.read",
    module: "attendance",
    element: lazy(() => import("./pages/Attendance").then((m) => ({ default: m.Attendance }))),
  },
  {
    path: "/exams",
    label: "Exams",
    group: "Academics",
    permission: "exam.definition.read",
    module: "examinations",
    element: lazy(() => import("./pages/Exams").then((m) => ({ default: m.Exams }))),
  },
  {
    path: "/fees",
    label: "Fees",
    group: "Money",
    permission: "fees.invoice.read",
    module: "fees",
    element: lazy(() => import("./pages/Fees").then((m) => ({ default: m.Fees }))),
  },
  {
    path: "/notices",
    label: "Notices",
    group: "Communication",
    permission: "comms.notice.read",
    module: "communication",
    element: lazy(() => import("./pages/Notices").then((m) => ({ default: m.Notices }))),
  },
  {
    path: "/settings",
    label: "Settings",
    group: "Administration",
    permission: "admin.settings.read",
    element: lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings }))),
  },
];

type Can = (permission: string) => boolean;
type HasModule = (code: string) => boolean;

/** Screens this caller may actually open. Both gates, in order. */
export function visibleScreens(can: Can, hasModule: HasModule): Screen[] {
  return SCREENS.filter(
    (s) => (s.module === undefined || hasModule(s.module)) && can(s.permission),
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
