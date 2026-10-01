import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client";
import { Certificates } from "./Certificates";

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
    can: (p: string) => ["certificates.read", "certificates.request", "certificates.approve", "certificates.issue"].includes(p),
    hasModule: (m: string) => m === "certificates",
  }),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("Certificates Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders certificate list with canonical Enrollment ID and approval actions", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admin/certificates")) {
        return {
          items: [
            {
              id: 1,
              certificate_no: "TC-2026-0001",
              certificate_type: "transfer_certificate",
              student_id: 10,
              student_name: "Pooja Mishra",
              admission_no: "ADM-100",
              enrolment_id: 15,
              canonical_enrolment_id: "ENR-15",
              class_label: "12-B",
              status: "requested",
              issue_date: null,
              issued_by_name: null,
              requested_by_name: "Office Clerk",
              is_reissue: false,
              reissue_count: 0,
              reissue_reason: null,
            },
          ],
          total: 1,
        };
      }
      return {};
    });

    renderWithClient(<Certificates />);

    expect(screen.getByText("Student Certificates")).toBeInTheDocument();
    expect(await screen.findByText("TC-2026-0001")).toBeInTheDocument();
    expect(screen.getByText("Pooja Mishra")).toBeInTheDocument();
    expect(screen.getByText(/ENR-15/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Approve/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reject/i })).toBeInTheDocument();
  });

  it("prompts with student exit warning when issuing a Transfer Certificate (TC)", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admin/certificates")) {
        return {
          items: [
            {
              id: 2,
              certificate_no: "TC-2026-0002",
              certificate_type: "transfer_certificate",
              student_id: 20,
              student_name: "Vikas Patel",
              admission_no: "ADM-200",
              enrolment_id: 25,
              canonical_enrolment_id: "ENR-25",
              class_label: "10-A",
              status: "approved",
              issue_date: null,
              issued_by_name: null,
              requested_by_name: "Admin",
              is_reissue: false,
              reissue_count: 0,
              reissue_reason: null,
            },
          ],
          total: 1,
        };
      }
      return {};
    });

    renderWithClient(<Certificates />);

    const issueBtn = await screen.findByRole("button", { name: /^Issue$/i });
    fireEvent.click(issueBtn);

    // Verify critical student exit warning dialog appears
    expect(await screen.findByText(/CONFIRM TRANSFER CERTIFICATE ISSUANCE \(CRITICAL ACTION\)/i)).toBeInTheDocument();
    expect(screen.getByText(/STUDENT STATUS TRANSITION WARNING/i)).toBeInTheDocument();
    expect(screen.getByText(/transferred_out/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Confirm TC Issuance & Student Exit/i })).toBeInTheDocument();
  });
});
