import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SCREENS, visibleScreens } from "../screens";
import { Payroll } from "./Payroll";

// Mock the API client
vi.mock("../api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
      if (url === "/admin/payroll/runs") {
        return Promise.resolve([
          {
            id: 1,
            month: "04/2026",
            run_no: 1,
            is_supplementary: false,
            status: "approved",
            working_days: 24,
            approved_at: "2026-04-30T10:00:00Z",
            paid_at: null,
            staff: 16,
            gross: "750000.00",
            deductions: "95000.00",
            net: "655000.00",
            employer_cost: "820000.00",
          },
        ]);
      }
      if (url === "/admin/payroll/components") {
        return Promise.resolve([
          {
            id: 1,
            code: "BASIC",
            name: "Basic",
            type: "earning",
            calculation: "percent_of_gross",
            value: "50",
            taxable: true,
            statutory: false,
            active: true,
            sequence: 10,
          },
          {
            id: 2,
            code: "PF",
            name: "Provident Fund",
            type: "deduction",
            calculation: "percent_of_basic",
            value: "12",
            taxable: false,
            statutory: true,
            active: true,
            sequence: 110,
          },
        ]);
      }
      if (url === "/admin/employees") {
        return Promise.resolve([
          {
            id: 1,
            employee_code: "EMP001",
            name: "Anita Sharma",
            department: "Science",
            user_role: "Teacher",
            bank_name: "State Bank of India",
            bank_account_no: "1234567890",
            bank_ifsc: "SBIN0001234",
          },
        ]);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn(),
    put: vi.fn(),
  },
  money: (val: string | number) => `₹${Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`,
}));

// Mock auth context
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "admin", name: "Administrator" },
    can: (perm: string) =>
      [
        "payroll.run.read",
        "payroll.run.manage",
        "payroll.run.approve",
        "payroll.setup.manage",
      ].includes(perm),
    hasModule: (code: string) => true,
  }),
}));

function renderPayroll() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <Payroll />
    </QueryClientProvider>,
  );
}

describe("Payroll screen", () => {
  it("registers /payroll in SCREENS with payroll.run.read and module hr", () => {
    const screenDef = SCREENS.find((s) => s.path === "/payroll");
    expect(screenDef).toBeDefined();
    expect(screenDef?.label).toBe("Payroll");
    expect(screenDef?.group).toBe("Money");
    expect(screenDef?.permissions).toContain("payroll.run.read");
    expect(screenDef?.modules).toContain("hr");
  });

  it("hides /payroll from roles without payroll.run.read", () => {
    const can = (p: string) => p === "students.profile.read";
    const hasModule = (m: string) => true;
    const labels = visibleScreens(can, hasModule).map((s) => s.label);
    expect(labels).not.toContain("Payroll");
  });

  it("shows /payroll when caller has payroll.run.read and hr module is on", () => {
    const can = (p: string) => p === "payroll.run.read";
    const hasModule = (m: string) => m === "hr";
    const labels = visibleScreens(can, hasModule).map((s) => s.label);
    expect(labels).toContain("Payroll");
  });

  it("renders page header, stat cards, and runs table", async () => {
    renderPayroll();
    expect(screen.getByText("Payroll & Salary Disbursal")).toBeInTheDocument();
    expect(screen.getByText("Total Gross Wage Bill")).toBeInTheDocument();
    expect(screen.getByText("Net Disbursal Payout")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText("04/2026").length).toBeGreaterThan(0);
    });
  });
});
