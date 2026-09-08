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

describe("the two gates", () => {
  it("shows a fee collector the fee screen and not the staff register", () => {
    const labels = visibleScreens(can(FEE_COLLECTOR), hasModule(ALL_MODULES)).map((s) => s.label);
    expect(labels).toContain("Fees");
    expect(labels).toContain("Students");
    expect(labels).not.toContain("Staff");
    expect(labels).not.toContain("Settings");
  });

  it("shows a transport manager no Fees entry", () => {
    const labels = visibleScreens(can(TRANSPORT_MANAGER), hasModule(ALL_MODULES)).map(
      (s) => s.label,
    );
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

describe("the registry itself", () => {
  it("gives every screen a path, label, group and permission", () => {
    for (const s of SCREENS) {
      expect(s.path, `${s.label} path`).toBeTruthy();
      expect(s.label, `${s.path} label`).toBeTruthy();
      expect(s.group, `${s.path} group`).toBeTruthy();
      expect(s.permission, `${s.path} permission`).toBeTruthy();
    }
  });

  it("has no duplicate paths", () => {
    const paths = SCREENS.map((s) => s.path);
    expect(paths).toEqual([...new Set(paths)]);
  });
});
