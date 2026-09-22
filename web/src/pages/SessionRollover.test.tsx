import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SCREENS, visibleScreens } from "../screens";
import { SessionRollover } from "./SessionRollover";

// Mock the API client
vi.mock("../api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
      if (url === "/admin/promotion/years") {
        return Promise.resolve([
          {
            id: 1,
            code: "2025-26",
            start_date: "2025-04-01",
            end_date: "2026-03-31",
            status: "active",
            is_current: true,
            is_writable: true,
          },
          {
            id: 2,
            code: "2026-27",
            start_date: "2026-04-01",
            end_date: "2027-03-31",
            status: "planning",
            is_current: false,
            is_writable: true,
          },
        ]);
      }
      if (url === "/admin/classes") {
        return Promise.resolve([
          {
            id: 101,
            class_name: "10",
            section: "A",
            class_label: "10-A",
            academic_year: "2025-26",
            class_teacher_id: 1,
            class_teacher: "Anita Sharma",
            student_count: 35,
            subjects: ["Maths", "Science"],
          },
          {
            id: 102,
            class_name: "10",
            section: "B",
            class_label: "10-B",
            academic_year: "2025-26",
            class_teacher_id: 2,
            class_teacher: "Rajesh Verma",
            student_count: 32,
            subjects: ["Maths", "Science"],
          },
        ]);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn((url: string, payload: any) => {
      if (url === "/admin/promotion/preview") {
        return Promise.resolve({
          from_year: "2025-26",
          to_year: "2026-27",
          from_section: "10-A",
          to_section: "11-A",
          lines: [
            {
              student_id: 201,
              student_name: "Aarav Sharma",
              admission_no: "ADM2024001",
              from_roll_no: 1,
              outcome: payload?.outcomes?.[201] || "promote",
              to_class_label: payload?.outcomes?.[201] === "detain" ? null : "11-A",
              to_roll_no: payload?.outcomes?.[201] === "detain" ? null : 1,
              note: null,
            },
            {
              student_id: 202,
              student_name: "Diya Patel",
              admission_no: "ADM2024002",
              from_roll_no: 2,
              outcome: payload?.outcomes?.[202] || "promote",
              to_class_label: "11-A",
              to_roll_no: 2,
              note: null,
            },
          ],
          blockers: [],
          can_commit: true,
        });
      }
      if (url === "/admin/promotion/commit") {
        return Promise.resolve({
          from_year: "2025-26",
          to_year: "2026-27",
          from_section: "10-A",
          to_section: "11-A",
          lines: [],
          blockers: [],
          can_commit: true,
        });
      }
      return Promise.resolve({});
    }),
  },
}));

// Mock auth context
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    me: { role: "admin", full_name: "Principal Sharma", academic_year: "2025-26" },
    can: (perm: string) =>
      [
        "students.enrolment.promote",
        "academics.class.read",
        "academics.class.write",
      ].includes(perm),
    hasModule: (code: string) => true,
  }),
}));

function renderSessionRollover() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SessionRollover />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Session Rollover screen", () => {
  it("registers /admin/session-rollover in SCREENS with students.enrolment.promote and module students", () => {
    const screenDef = SCREENS.find((s) => s.path === "/admin/session-rollover");
    expect(screenDef).toBeDefined();
    expect(screenDef?.label).toBe("Session rollover");
    expect(screenDef?.group).toBe("Academics");
    expect(screenDef?.permissions).toContain("students.enrolment.promote");
    expect(screenDef?.permissions).toContain("academics.class.read");
    expect(screenDef?.modules).toContain("students");
  });

  it("hides /admin/session-rollover from roles without students.enrolment.promote", () => {
    const can = (p: string) => p === "academics.class.read";
    const hasModule = (m: string) => true;
    const labels = visibleScreens(can, hasModule).map((s) => s.label);
    expect(labels).not.toContain("Session rollover");
  });

  it("shows /admin/session-rollover when user holds promoter and reader permissions", () => {
    const can = (p: string) =>
      ["students.enrolment.promote", "academics.class.read"].includes(p);
    const hasModule = (m: string) => m === "students";
    const labels = visibleScreens(can, hasModule).map((s) => s.label);
    expect(labels).toContain("Session rollover");
  });

  it("renders wizard step 1 with header and section picker", async () => {
    renderSessionRollover();
    expect(
      screen.getByText("Session Rollover & Promotion Wizard"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Step 1: Select Academic Session & Source Class Section"),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("10-A")).toBeInTheDocument();
      expect(screen.getByText("10-B")).toBeInTheDocument();
    });
  });

  it("progresses to step 2 after selecting section and clicking inspect", async () => {
    renderSessionRollover();

    await waitFor(() => {
      expect(screen.getByText("10-A")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("10-A"));

    await waitFor(() => {
      expect(
        screen.getByText("Inspect Roster & Next Steps →"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Inspect Roster & Next Steps →"));

    await waitFor(() => {
      expect(screen.getByText("Roster Review for Class 10-A → 11-A")).toBeInTheDocument();
      expect(screen.getByText("Aarav Sharma")).toBeInTheDocument();
      expect(screen.getByText("Diya Patel")).toBeInTheDocument();
    });
  });
});
