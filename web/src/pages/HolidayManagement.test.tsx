import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client";
import { HolidayManagement } from "./HolidayManagement";

vi.mock("../api/client", () => ({
  api: {
    rawGet: vi.fn(),
    rawPost: vi.fn(),
  },
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    can: (p: string) => ["attendance.holiday.manage"].includes(p),
    hasModule: (m: string) => m === "attendance",
  }),
}));

vi.mock("./useClasses", () => ({
  useClasses: () => ({
    data: [
      { id: 1, class_label: "1-A" },
      { id: 2, class_label: "2-A" },
    ],
  }),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("HolidayManagement Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders declared holidays list and displays date ranges and school-wide scope", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path === "/admin/attendance/holidays") {
        return [
          {
            id: 1,
            name: "Gandhi Jayanti",
            start_date: "2026-10-02",
            end_date: "2026-10-02",
            description: "National Holiday",
            is_school_wide: true,
            status: "active",
            class_section_ids: [],
            cancellation_reason: null,
          },
        ];
      }
      return [];
    });

    renderWithClient(<HolidayManagement />);

    expect(screen.getByText("Holiday Management")).toBeInTheDocument();
    expect(await screen.findByText("Gandhi Jayanti")).toBeInTheDocument();
    expect(screen.getAllByText(/School-Wide/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Cancel Holiday")).toBeInTheDocument();
  });

  it("cancels a holiday with mandatory reason dialog", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path === "/admin/attendance/holidays") {
        return [
          {
            id: 2,
            name: "Weather Advisory Holiday",
            start_date: "2026-12-15",
            end_date: "2026-12-15",
            description: "Heavy Fog",
            is_school_wide: true,
            status: "active",
            class_section_ids: [],
            cancellation_reason: null,
          },
        ];
      }
      return [];
    });

    vi.mocked(api.rawPost).mockResolvedValue({ id: 2, status: "cancelled" });

    renderWithClient(<HolidayManagement />);

    const cancelBtns = await screen.findAllByRole("button", { name: /Cancel Holiday/i });
    fireEvent.click(cancelBtns[0]);

    expect(await screen.findByText(/Are you sure you want to cancel the holiday/i)).toBeInTheDocument();

    const reasonInput = screen.getByLabelText(/Reason/i);
    fireEvent.change(reasonInput, { target: { value: "Weather advisory lifted by District Magistrate" } });

    const modalConfirmBtn = screen.getAllByRole("button", { name: /Cancel Holiday/i })[1];
    fireEvent.click(modalConfirmBtn);

    await waitFor(() => {
      expect(api.rawPost).toHaveBeenCalledWith(
        "/admin/attendance/holidays/2/cancel",
        expect.objectContaining({
          reason: "Weather advisory lifted by District Magistrate",
        }),
      );
    });
  });
});
