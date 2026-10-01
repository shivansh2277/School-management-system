import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client";
import { Library } from "./Library";

vi.mock("../api/client", () => ({
  api: {
    rawGet: vi.fn(),
    rawPost: vi.fn(),
  },
  tokenStore: { get: () => "mock-token" },
  API_BASE_URL: "http://localhost:8000",
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    can: (p: string) => ["library.read", "library.manage"].includes(p),
    hasModule: (m: string) => m === "library",
  }),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("Library Component - Catalogue & Circulation Desk", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders circulation desk, active loans with canonical Enrollment ID, and catalogue tabs", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admin/library/loans")) {
        return {
          items: [
            {
              id: 1,
              book_copy_id: 101,
              accession_no: "ACC-1-1",
              book_title: "Brief History of Time",
              enrolment_id: 42,
              borrower_name: "Aarav Sharma",
              borrower_type: "student",
              class_label: "10-A",
              roll_no: 12,
              issued_on: "2026-03-01",
              due_date: "2026-03-15",
              returned_on: null,
              status: "active",
              fine_amount: 0,
              fine_paid: false,
              renewal_count: 0,
            },
          ],
          total: 1,
        };
      }
      if (path.includes("/admin/library/books")) {
        return { items: [], total: 0 };
      }
      return {};
    });

    renderWithClient(<Library />);

    expect(screen.getByText("Library & Circulation Desk")).toBeInTheDocument();
    expect(await screen.findByText("Brief History of Time")).toBeInTheDocument();
    expect(screen.getByText("Aarav Sharma")).toBeInTheDocument();
    expect(screen.getByText("ENR-42")).toBeInTheDocument();
    expect(screen.getByText("ACC-1-1")).toBeInTheDocument();
  });

  it("issues a loan using borrower canonical Enrollment ID and book accession number", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admin/library/loans")) {
        return { items: [], total: 0 };
      }
      if (path.includes("/admin/library/books")) {
        return { items: [], total: 0 };
      }
      if (path.includes("/admin/library/borrowers/lookup")) {
        return {
          canonical_id: "ENR-42",
          name: "Aarav Sharma",
          role: "Student",
          class_label: "10-A",
          active_loans_count: 0,
          unpaid_fines_total: 0,
        };
      }
      return {};
    });

    vi.mocked(api.rawPost).mockResolvedValue({ id: 10, status: "active" });

    renderWithClient(<Library />);

    const borrowerInput = screen.getByPlaceholderText(/e\.g\. ENR-1/i);
    const barcodeInput = screen.getByPlaceholderText(/e\.g\. ACC-1-1/i);
    const issueBtn = screen.getByRole("button", { name: /Issue Book/i });

    fireEvent.change(borrowerInput, { target: { value: "ENR-42" } });
    fireEvent.change(barcodeInput, { target: { value: "ACC-1-1" } });
    fireEvent.click(issueBtn);

    await waitFor(() => {
      expect(api.rawPost).toHaveBeenCalledWith(
        "/admin/library/loans/issue",
        expect.objectContaining({
          borrower_identifier: "ENR-42",
          copy_barcode: "ACC-1-1",
          loan_days: 14,
        }),
      );
    });
  });
});
