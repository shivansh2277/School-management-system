import { describe, expect, it } from "vitest";

import { SCREENS, visibleScreens } from "../../screens";

const can = (held: string[]) => (p: string) => held.includes(p);
const hasModule = (on: string[]) => (c: string) => on.includes(c);

describe("Admission screen registry and permission gating", () => {
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

  const RECEPTIONIST_PERMS = [
    "admission.cycle.read",
    "admission.cycle.write",
    "admission.enquiry.read",
    "admission.enquiry.write",
    "admission.application.read",
    "admission.application.write",
    "admission.document.verify",
    "admission.assessment.enter",
    "admission.interview.enter",
    "admission.decision.make",
    "admission.decision.override",
    "admission.application.convert",
    "admission.medical.read",
  ];

  const ADMIN_PERMS = [
    "admin.settings.read",
    "students.profile.read",
    "hr.employee.read",
    "academics.class.read",
    "attendance.record.read",
    "exam.definition.read",
    "fees.invoice.read",
    "comms.notice.read",
    "transport.setup.read",
    "inventory.item.read",
    "grievance.read",
    "admission.cycle.read",
  ];

  const FEE_COLLECTOR_PERMS = [
    "students.profile.read",
    "fees.invoice.read",
    "fees.payment.collect",
  ];

  it("shows ONLY the 5 operational Admission screens to a receptionist with admission module enabled", () => {
    const visible = visibleScreens(
      can(RECEPTIONIST_PERMS),
      hasModule(ALL_MODULES),
    );
    const admissionLabels = visible
      .filter((s) => s.group === "Admission")
      .map((s) => s.label);

    expect(admissionLabels).toEqual([
      "Enquiries",
      "Applications",
      "Merit & selection",
      "Waitlist",
      "Admission reports",
    ]);
    // Receptionist sees NOTHING else in the entire system
    expect(visible.map((s) => s.label)).toEqual(admissionLabels);
  });

  it("shows ONLY Admission dashboard under Admission to admin on main website", () => {
    const visible = visibleScreens(
      can(ADMIN_PERMS),
      hasModule(ALL_MODULES),
    );
    const admissionLabels = visible
      .filter((s) => s.group === "Admission")
      .map((s) => s.label);

    expect(admissionLabels).toEqual(["Admission dashboard"]);
    expect(visible.map((s) => s.label)).toContain("Dashboard");
    expect(visible.map((s) => s.label)).toContain("Students");
    expect(visible.map((s) => s.label)).not.toContain("Enquiries");
    expect(visible.map((s) => s.label)).not.toContain("Applications");
  });

  it("hides all Admission screens from a fee collector", () => {
    const visible = visibleScreens(
      can(FEE_COLLECTOR_PERMS),
      hasModule(ALL_MODULES),
    );
    const admissionLabels = visible
      .filter((s) => s.group === "Admission")
      .map((s) => s.label);

    expect(admissionLabels).toHaveLength(0);
  });

  it("hides all Admission screens when the admission module is disabled", () => {
    const withoutAdmission = ALL_MODULES.filter((m) => m !== "admission");
    const visible = visibleScreens(
      can(RECEPTIONIST_PERMS),
      hasModule(withoutAdmission),
    );
    const admissionLabels = visible
      .filter((s) => s.group === "Admission")
      .map((s) => s.label);

    expect(admissionLabels).toHaveLength(0);
  });

  it("every admission screen declares the admission module (6 total screens)", () => {
    const admissionScreens = SCREENS.filter((s) => s.group === "Admission");
    expect(admissionScreens.length).toBe(6);
    for (const s of admissionScreens) {
      expect(s.modules).toContain("admission");
    }
  });
});
