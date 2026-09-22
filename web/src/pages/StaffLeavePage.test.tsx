import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SCREENS } from "../screens";
import { StaffLeavePage } from "./StaffLeavePage";

// Mock the API client
vi.mock("../api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
      if (url === "/admin/staff-leave" || url.startsWith("/admin/staff-leave?")) {
        return Promise.resolve([
          {
            id: 10,
            school_id: 1,
            employee_id: 5,
            employee_name: "Pooja Sharma",
            leave_type: null,
            from_date: "2026-09-21",
            to_date: "2026-09-22",
            is_half_day: false,
            days: 2,
            reason: "Personal family emergency",
            status: "applied",
            decided_by_name: null,
            decided_at: null,
            decision_note: null,
          },
        ]);
      }
      if (url === "/admin/staff-leave/10/substitution-matrix") {
        return Promise.resolve({
          leave_request_id: 10,
          teacher_name: "Pooja Sharma",
          from_date: "2026-09-21",
          to_date: "2026-09-22",
          total_periods: 2,
          covered_periods: 1,
          ready_for_approval: false,
          periods: [
            {
              slot_id: 101,
              date: "2026-09-21",
              period_no: 1,
              start_time: "08:30",
              end_time: "09:15",
              class_label: "10-A",
              subject_name: "Mathematics",
              room_number: "Room 101",
              status: "provisional",
              substitution_id: 501,
              substitute_teacher_id: 7,
              substitute_teacher_name: "Vikas Gupta",
              free_teachers: [],
            },
            {
              slot_id: 102,
              date: "2026-09-21",
              period_no: 3,
              start_time: "10:15",
              end_time: "11:00",
              class_label: "9-B",
              subject_name: "Mathematics",
              room_number: "Room 203",
              status: "unassigned",
              substitution_id: null,
              substitute_teacher_id: null,
              substitute_teacher_name: null,
              free_teachers: [
                { id: 8, name: "Sunil Verma", employee_code: "EMP-008" },
              ],
            },
          ],
        });
      }
      return Promise.reject(new Error(`Unhandled get ${url}`));
    }),
    post: vi.fn(),
    patch: vi.fn(),
    del: vi.fn(),
  },
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    can: (p: string) => ["hr.leave.read", "hr.leave.approve"].includes(p),
  }),
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("StaffLeavePage", () => {
  it("renders leave requests with substitution gating button", async () => {
    renderWithClient(<StaffLeavePage />);

    expect(screen.getByText("Staff Leave & Substitution Gate")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Pooja Sharma")).toBeInTheDocument();
      expect(screen.getByText("Personal family emergency")).toBeInTheDocument();
      expect(screen.getByText("Review & Substitute")).toBeInTheDocument();
    });
  });

  it("opens substitution matrix modal and enforces approval locking when periods are uncovered", async () => {
    renderWithClient(<StaffLeavePage />);

    await waitFor(() => {
      expect(screen.getByText("Review & Substitute")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Review & Substitute"));

    await waitFor(() => {
      expect(screen.getByText("Approval Gate Locked")).toBeInTheDocument();
      expect(screen.getByText("1 of 2 Assigned")).toBeInTheDocument();
      expect(screen.getByText("50% Covered")).toBeInTheDocument();
      expect(screen.getByText("Vikas Gupta")).toBeInTheDocument();
      expect(screen.getByText("Approve Locked (Uncovered Periods)")).toBeInTheDocument();
    });

    // Verify approve button is disabled
    const approveBtn = screen.getByText("Approve Locked (Uncovered Periods)");
    expect(approveBtn).toBeDisabled();
  });

  it("is registered in screens.ts under People with hr.leave.read permission", () => {
    const screenDef = SCREENS.find((s) => s.path === "/staff-leave");
    expect(screenDef).toBeDefined();
    expect(screenDef?.label).toBe("Staff leave");
    expect(screenDef?.permissions).toContain("hr.leave.read");
    expect(screenDef?.modules).toContain("hr");
  });
});
