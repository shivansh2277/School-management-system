import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../api/client";
import { AdmissionExceptions } from "./AdmissionExceptions";

vi.mock("../../api/client", () => ({
  api: {
    rawGet: vi.fn(),
    rawPost: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("AdmissionExceptions Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the exception interface and lists existing overrides", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path === "/admin/admission/document-overrides") {
        return [
          {
            id: 1,
            application_id: 10,
            application_no: "APP-2026-0010",
            applicant_name: "Rahul Verma",
            class_applying_for: "UKG",
            document_code: "birth_certificate",
            status: "approved",
            authorized_by_name: "Principal Officer",
            reason: "Under process at Municipal Corporation",
            authorized_at: "2026-03-01T10:00:00Z",
          },
        ];
      }
      return [];
    });

    renderWithClient(<AdmissionExceptions />);

    expect(screen.getByText("Admission Document Overrides & Exceptions")).toBeInTheDocument();
    expect(screen.getByText("Admin Scoped Exception Authorization")).toBeInTheDocument();

    expect(await screen.findByText("APP-2026-0010")).toBeInTheDocument();
    expect(screen.getByText("Rahul Verma")).toBeInTheDocument();
    expect(screen.getByText("birth certificate")).toBeInTheDocument();
  });

  it("automatically renders pending queue items and supports Approve action", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path === "/admin/admission/document-overrides") {
        return [
          {
            id: 101,
            application_id: 1024,
            application_no: "APP-1024",
            applicant_name: "Rahul Sharma",
            class_applying_for: "UKG",
            document_code: "birth_certificate",
            document_name: "Birth Certificate",
            status: "pending",
            reason: "Document exception requested",
            created_at: "2026-10-05T10:00:00Z",
            authorized_by_name: null,
            authorized_at: null,
          },
        ];
      }
      return [];
    });

    vi.mocked(api.rawPost).mockResolvedValue({ success: true });

    renderWithClient(<AdmissionExceptions />);

    expect(await screen.findByText("Rahul Sharma")).toBeInTheDocument();
    expect(screen.getByText("APP-1024")).toBeInTheDocument();
    expect(screen.getByText("Birth Certificate")).toBeInTheDocument();
    expect(screen.getByText("Document exception requested")).toBeInTheDocument();
    expect(screen.getByText("1 Pending")).toBeInTheDocument();

    // Find and click Approve button
    const approveBtn = screen.getByRole("button", { name: "Approve" });
    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(api.rawPost).toHaveBeenCalledWith(
        "/admin/admission/document-overrides/101/approve",
        {},
      );
    });
  });

  it("supports Reject action from pending queue with rejection reason", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path === "/admin/admission/document-overrides") {
        return [
          {
            id: 102,
            application_id: 1025,
            application_no: "APP-1025",
            applicant_name: "Pooja Singh",
            class_applying_for: "1",
            document_code: "transfer_certificate",
            document_name: "Transfer Certificate",
            status: "pending",
            reason: "Previous school closed early",
            created_at: "2026-10-05T11:00:00Z",
            authorized_by_name: null,
            authorized_at: null,
          },
        ];
      }
      return [];
    });

    vi.mocked(api.rawPost).mockResolvedValue({ success: true });

    renderWithClient(<AdmissionExceptions />);

    expect(await screen.findByText("Pooja Singh")).toBeInTheDocument();

    const rejectBtn = screen.getByRole("button", { name: "Reject" });
    fireEvent.click(rejectBtn);

    // Modal should appear
    expect(screen.getByText(/Reason for Rejection/i)).toBeInTheDocument();
    const reasonInput = screen.getByPlaceholderText(/State the reason for rejecting/i);
    fireEvent.change(reasonInput, { target: { value: "Must produce original certificate before admission" } });

    const confirmRejectBtn = screen.getByRole("button", { name: /Confirm Rejection/i });
    fireEvent.click(confirmRejectBtn);

    await waitFor(() => {
      expect(api.rawPost).toHaveBeenCalledWith(
        "/admin/admission/document-overrides/102/reject",
        { reason: "Must produce original certificate before admission" },
      );
    });
  });

  it("looks up draft application and authorizes a document exception", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/applications/lookup")) {
        return {
          id: 42,
          application_no: "DFT-42",
          full_name: "Ananya Sen",
          date_of_birth: "2021-08-15",
          class_applying_for: "Nursery",
          status: "draft",
          checklist: [
            { document_code: "birth_certificate", document_name: "Birth Certificate", required: true, has_override: false },
            { document_code: "address_proof", document_name: "Address Proof", required: true, has_override: false },
          ],
          overrides: [],
        };
      }
      if (path === "/admin/admission/document-overrides") {
        return [];
      }
      return {};
    });

    vi.mocked(api.rawPost).mockResolvedValue({ id: 99, status: "authorized" });

    renderWithClient(<AdmissionExceptions />);

    const refInput = screen.getByPlaceholderText(/Enter Draft Ref/i);
    const lookupBtn = screen.getByRole("button", { name: /Lookup Draft/i });

    fireEvent.change(refInput, { target: { value: "DFT-42" } });
    fireEvent.click(lookupBtn);

    expect(await screen.findByText("Ananya Sen")).toBeInTheDocument();
    expect(screen.getByText("DFT-42")).toBeInTheDocument();
    expect(screen.getAllByText(/Mandatory/i).length).toBeGreaterThanOrEqual(1);

    const authorizeBtn = screen.getByRole("button", { name: /Authorize Document Exception/i });
    fireEvent.click(authorizeBtn);

    await waitFor(() => {
      expect(api.rawPost).toHaveBeenCalledWith(
        "/admin/admission/applications/42/document-overrides",
        expect.objectContaining({
          document_code: "birth_certificate",
          reason: expect.any(String),
        }),
      );
    });
  });
});
