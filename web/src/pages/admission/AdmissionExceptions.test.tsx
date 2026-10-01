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
