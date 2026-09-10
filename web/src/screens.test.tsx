import { describe, expect, it } from "vitest";

import { SCREENS, groupedNav, visibleScreens } from "./screens";

/** The permissions the backend's fee_collector role holds (core/permissions.py). */
const FEE_COLLECTOR = ["students.profile.read", "fees.invoice.read", "fees.payment.collect"];

/** The transport_manager role. */
const TRANSPORT_MANAGER = [
  "students.profile.read",
  "academics.class.read",
  "transport.setup.read",
  "transport.setup.write",
  "transport.assignment.read",
  "transport.assignment.manage",
  "hr.employee.read",
  "comms.notice.read",
  "comms.message.send",
];

const ALL_MODULES = [
  "students",
  "attendance",
  "examinations",
  "fees",
  "homework",
  "communication",
  "admission",
  "timetable",
  "hr",
  "transport",
  "reports",
];

const can = (held: string[]) => (p: string) => held.includes(p);
const hasModule = (on: string[]) => (c: string) => on.includes(c);
const labelsFor = (held: string[], on: string[]) =>
  visibleScreens(can(held), hasModule(on)).map((s) => s.label);

describe("the two gates", () => {
  it("shows a fee collector the fee screen and not the staff register", () => {
    const labels = labelsFor(FEE_COLLECTOR, ALL_MODULES);
    expect(labels).toContain("Fees");
    expect(labels).not.toContain("Staff");
    expect(labels).not.toContain("Settings");
  });

  it("shows a transport manager no Fees entry", () => {
    const labels = labelsFor(TRANSPORT_MANAGER, ALL_MODULES);
    expect(labels).not.toContain("Fees");
    expect(labels).toContain("Staff");
  });

  it("hides a module the school has switched off, even from someone holding every permission", () => {
    const everyPermission = () => true;
    const withoutFees = ALL_MODULES.filter((m) => m !== "fees");
    const labels = visibleScreens(everyPermission, hasModule(withoutFees)).map((s) => s.label);
    expect(labels).not.toContain("Fees");
    // ...and the permission alone is not enough to bring it back.
    expect(visibleScreens(everyPermission, hasModule(ALL_MODULES)).map((s) => s.label)).toContain(
      "Fees",
    );
  });

  it("groups the sidebar in registry order without empty groups", () => {
    const groups = groupedNav(can(FEE_COLLECTOR), hasModule(ALL_MODULES));
    expect(groups.every((g) => g.screens.length > 0)).toBe(true);
    expect(groups.map((g) => g.group)).toEqual([...new Set(groups.map((g) => g.group))]);
  });
});

/**
 * Both gates take a list and require all of it. Declaring one permission per
 * screen is what let /attendance be gated on an exam permission while calling
 * the attendance API, and what let /settings call a fees route while declaring
 * no module - the whole point of Fix 1.
 */
describe("every declared permission and module is required, not just the first", () => {
  it("hides a screen from a caller holding only one of its two permissions", () => {
    // Attendance declares attendance.record.read AND academics.class.read: the
    // roll endpoint requires a class_section_id, so the class list is not
    // optional here the way it is on /students.
    const attendance = SCREENS.find((s) => s.path === "/attendance")!;
    expect(attendance.permissions).toHaveLength(2);

    for (const held of attendance.permissions) {
      expect(labelsFor([held], ALL_MODULES), `holding only ${held}`).not.toContain("Attendance");
    }
    expect(labelsFor(attendance.permissions, ALL_MODULES)).toContain("Attendance");
  });

  it("hides a screen when either of its modules is off", () => {
    const everyPermission = () => true;
    // Constructed rather than found, so the property is pinned even while no
    // shipped screen happens to need two modules at once. Slice 2 onwards will.
    const twoModules = {
      ...SCREENS.find((s) => s.path === "/fees")!,
      label: "Two modules",
      modules: ["fees", "students"] as const,
    };
    const registry = [twoModules];
    const visible = (on: string[]) =>
      registry.filter(
        (s) => s.modules.every((m) => on.includes(m)) && s.permissions.every(everyPermission),
      );

    expect(visible(ALL_MODULES)).toHaveLength(1);
    for (const off of ["fees", "students"]) {
      expect(
        visible(ALL_MODULES.filter((m) => m !== off)),
        `with ${off} off`,
      ).toHaveLength(0);
    }
  });

  it("keeps a read-only role on screens whose write endpoints it cannot call", () => {
    // The set is what the screen needs to LOAD. A fee collector holds
    // fees.invoice.read but not fees.invoice.generate, and must still see Fees.
    expect(FEE_COLLECTOR).not.toContain("fees.invoice.generate");
    expect(labelsFor(FEE_COLLECTOR, ALL_MODULES)).toContain("Fees");
  });

  it("keeps the roster with a fee collector and notices with a receptionist", () => {
    // Both hold the screen's own read permission but not academics.class.read,
    // which only fills a dropdown. Declaring it would have taken the student
    // lookup from the counter clerk and the notice board from the front desk -
    // the reason those two calls are gated in useClasses instead.
    expect(FEE_COLLECTOR).not.toContain("academics.class.read");
    expect(labelsFor(FEE_COLLECTOR, ALL_MODULES)).toContain("Students");

    const RECEPTIONIST = ["comms.notice.read", "comms.notice.publish"];
    expect(labelsFor(RECEPTIONIST, ALL_MODULES)).toContain("Notices");
  });

  it("hides Staff when the hr module is off, which is the default for a new school", () => {
    // core/modules.py: Module("hr", ..., default_enabled=False). The staff
    // screen reads /admin/teachers, which Fix 2 puts behind that switch.
    const withoutHr = ALL_MODULES.filter((m) => m !== "hr");
    expect(labelsFor(TRANSPORT_MANAGER, withoutHr)).not.toContain("Staff");
    expect(labelsFor(TRANSPORT_MANAGER, ALL_MODULES)).toContain("Staff");
  });

  it("keeps Settings available to a school with fees switched off", () => {
    // Settings calls /admin/fees/plans, but that panel gates itself in-page.
    // A school cannot be locked out of editing its own name and branding
    // because it does not buy the fees module.
    const withoutFees = ALL_MODULES.filter((m) => m !== "fees");
    expect(labelsFor(["admin.settings.read"], withoutFees)).toContain("Settings");
  });
});

describe("the registry itself", () => {
  it("gives every screen a path, label, group and at least one permission", () => {
    for (const s of SCREENS) {
      expect(s.path, `${s.label} path`).toBeTruthy();
      expect(s.label, `${s.path} label`).toBeTruthy();
      expect(s.group, `${s.path} group`).toBeTruthy();
      expect(s.permissions.length, `${s.path} permissions`).toBeGreaterThan(0);
    }
  });

  it("has no duplicate paths, and no screen repeats a permission or module", () => {
    const paths = SCREENS.map((s) => s.path);
    expect(paths).toEqual([...new Set(paths)]);
    for (const s of SCREENS) {
      expect(s.permissions, `${s.path} permissions`).toEqual([...new Set(s.permissions)]);
      expect(s.modules ?? [], `${s.path} modules`).toEqual([...new Set(s.modules ?? [])]);
    }
  });
});

/**
 * The screen that turns modules on must not itself be behind a module.
 *
 * A school with every module switched off - which is what a fresh tenant
 * looks like before it is configured, and what one accidental "turn off"
 * away from - would otherwise have no way back except a curl, which is the
 * exact state Packet 3 exists to end.
 */
describe("Configuration is reachable when everything is switched off", () => {
  it("shows on admin.settings.read alone, with no modules enabled", () => {
    expect(labelsFor(["admin.settings.read"], [])).toContain("Configuration");
  });

  it("stays hidden from a fee collector, who does not hold admin.settings.read", () => {
    expect(FEE_COLLECTOR).not.toContain("admin.settings.read");
    expect(labelsFor(FEE_COLLECTOR, ALL_MODULES)).not.toContain("Configuration");
  });
});

/**
 * Transport is the transport manager's screen, and it must not need the
 * assignment permissions to open.
 *
 * The routes, buses and expiring-papers lists are all `transport.setup.read`.
 * Only the who-rides-this-route drill-down needs `transport.assignment.read`,
 * and that is gated at the widget with <Can>. Declaring it on the screen would
 * hide all three lists from a setup reader, which is the failure Contract 1's
 * note about over-declaring is about - and it is the kind of thing a later
 * session "tidies up" into the entry without noticing what it costs.
 */
describe("Transport", () => {
  it("shows for the transport manager", () => {
    expect(labelsFor(TRANSPORT_MANAGER, ALL_MODULES)).toContain("Transport");
  });

  it("opens on transport.setup.read alone, without either assignment permission", () => {
    const setupOnly = ["transport.setup.read"];
    expect(labelsFor(setupOnly, ALL_MODULES)).toContain("Transport");
  });

  it("disappears with the transport module, which is off for most schools", () => {
    const withoutTransport = ALL_MODULES.filter((m) => m !== "transport");
    expect(labelsFor(TRANSPORT_MANAGER, withoutTransport)).not.toContain("Transport");
  });

  it("stays hidden from a fee collector", () => {
    expect(labelsFor(FEE_COLLECTOR, ALL_MODULES)).not.toContain("Transport");
  });
});
