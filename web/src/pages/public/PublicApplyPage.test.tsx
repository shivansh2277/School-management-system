import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../api/client";
import { PublicApplyPage } from "./PublicApplyPage";

vi.mock("../../api/client", () => ({
  api: {
    rawGet: vi.fn(),
    rawPost: vi.fn(),
    upload: vi.fn(),
  },
  toMediaUrl: (url: string | null) => url,
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/apply"]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("PublicApplyPage - Online Admission Portal & Workflow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();

    // Default mock for open admission cycle
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admission/open")) {
        return {
          school: { code: "SPS", name: "Sunrise Public School", city: "Lucknow" },
          cycle: {
            name: "Academic Session 2025–26",
            academic_year: "2025-26",
            starts_on: "2025-01-01",
            ends_on: "2025-03-31",
            application_fee: "0",
            refund_policy: "Fees paid are non-refundable except security deposit.",
          },
          classes: [
            {
              class_name: "1",
              stream: null,
              total_seats: 40,
              age_on: "2025-03-31",
              min_age_years: 5,
              max_age_years: 7,
              requires_test: false,
              requires_interview: true,
              required_documents: ["birth_certificate", "address_proof"],
            },
            {
              class_name: "11",
              stream: "Science",
              total_seats: 60,
              age_on: "2025-03-31",
              min_age_years: 15,
              max_age_years: 17,
              requires_test: true,
              requires_interview: true,
              required_documents: ["birth_certificate", "address_proof", "report_card"],
            },
          ],
        };
      }
      return {};
    });
  });

  it("renders the portal header, open cycle information, and 7-step wizard stepper", async () => {
    renderWithClient(<PublicApplyPage />);

    expect(await screen.findByText("Sunrise Public School")).toBeInTheDocument();
    expect(screen.getByText(/Online Admission Portal • Gomti Nagar, Lucknow/i)).toBeInTheDocument();
    expect(screen.getByText("Apply Online (2025–26)")).toBeInTheDocument();
    expect(screen.getByText("Track Status & Pay Fee")).toBeInTheDocument();
    expect(screen.getByText("Seat Matrix & Criteria")).toBeInTheDocument();

    // Stepper buttons
    expect(await screen.findByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("Student Personal Details")).toBeInTheDocument();
  });

  it("validates Step 1 mandatory student fields when clicking Continue", async () => {
    renderWithClient(<PublicApplyPage />);

    const continueBtn = await screen.findByRole("button", { name: /Continue →/i });
    fireEvent.click(continueBtn);

    expect(
      await screen.findByText(/Please provide both First Name and Last Name of the student./i)
    ).toBeInTheDocument();
  });

  it("allows filling Step 1 student information and progressing to Step 2 Parent Details", async () => {
    renderWithClient(<PublicApplyPage />);

    // Fill Step 1 fields
    const firstNameInput = await screen.findByPlaceholderText("e.g. Aarav");
    const lastNameInput = screen.getByPlaceholderText("e.g. Sharma");
    const addressInput = screen.getByPlaceholderText(/Flat 402, Shalimar Gallant/i);
    const dobInput = screen.getByLabelText(/Date of Birth/i);

    fireEvent.change(firstNameInput, { target: { value: "Aarav" } });
    fireEvent.change(lastNameInput, { target: { value: "Shukla" } });
    fireEvent.change(dobInput, { target: { value: "2019-07-15" } });
    fireEvent.change(addressInput, { target: { value: "House 42, Sector 4, Gomti Nagar" } });

    // Select class
    const classSelect = screen.getByRole("combobox", { name: /Class Applying For/i });
    fireEvent.change(classSelect, { target: { value: "1" } });

    // Click Continue
    const continueBtn = screen.getByRole("button", { name: /Continue →/i });
    fireEvent.click(continueBtn);

    // Should now be on Step 2
    expect(await screen.findByText("Parent & Guardian Details")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. Rajesh Sharma")).toBeInTheDocument();
  });

  it("switches to Status tab and displays Offer Issued with Pay Fee CTA", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admission/status")) {
        return {
          application_no: "APP-2026-0042",
          name: "Samar Gupta",
          class_applying_for: "1",
          status: "offer_issued",
          stage: "offer_issued",
          submitted_at: "2026-03-01T10:00:00Z",
          action_needed: true,
          is_payable: true,
          payable_amount: "28500.00",
          documents_available: false,
          offer: {
            id: 12,
            status: "issued",
            class_name: "1",
            stream: null,
            offer_amount: "28500.00",
            expires_on: "2026-03-31",
            is_expired: false,
          },
          student: null,
          receipt: null,
        };
      }
      return {};
    });

    renderWithClient(<PublicApplyPage />);

    // Switch to status tab
    const statusTabBtn = screen.getByRole("button", { name: /Track Status & Pay Fee/i });
    fireEvent.click(statusTabBtn);

    expect(screen.getByText("Check Application & Admission Status")).toBeInTheDocument();

    const appInput = screen.getByPlaceholderText("e.g. APP-2026-0001");
    const mobileInput = screen.getByPlaceholderText(/10-digit mobile number/i);
    const searchBtn = screen.getByRole("button", { name: /Track Application Status/i });

    fireEvent.change(appInput, { target: { value: "APP-2026-0042" } });
    fireEvent.change(mobileInput, { target: { value: "9876543210" } });
    fireEvent.click(searchBtn);

    // Verify Offer Card is rendered with exact payable amount
    expect(await screen.findByText("APP-2026-0042")).toBeInTheDocument();
    expect(screen.getAllByText("Samar Gupta").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Provisional Offer Issued/i)).toBeInTheDocument();
    expect(screen.getByText("₹28,500.00")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pay Admission Fee Online/i })).toBeInTheDocument();
  });

  it("initiates mock payment and opens the Payment Gateway Modal with sandbox controls", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admission/status")) {
        return {
          application_no: "APP-2026-0042",
          name: "Samar Gupta",
          class_applying_for: "1",
          status: "offer_issued",
          stage: "offer_issued",
          submitted_at: "2026-03-01T10:00:00Z",
          action_needed: true,
          is_payable: true,
          payable_amount: "28500.00",
          documents_available: false,
          offer: {
            id: 12,
            status: "issued",
            class_name: "1",
            offer_amount: "28500.00",
            expires_on: "2026-03-31",
          },
        };
      }
      return {};
    });

    vi.mocked(api.rawPost).mockImplementation(async (path: string) => {
      if (path.includes("/payments/initiate")) {
        return {
          status: "initiated",
          order_id: "ORD-2026-0042",
          order_token: "MOCK_ORDER_TOKEN_ABC",
          amount: "28500.00",
          currency: "INR",
        };
      }
      return {};
    });

    renderWithClient(<PublicApplyPage />);

    // Go to status
    fireEvent.click(screen.getByRole("button", { name: /Track Status & Pay Fee/i }));
    fireEvent.change(screen.getByPlaceholderText("e.g. APP-2026-0001"), {
      target: { value: "APP-2026-0042" },
    });
    fireEvent.change(screen.getByPlaceholderText(/10-digit mobile number/i), {
      target: { value: "9876543210" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Track Application Status/i }));

    const payBtn = await screen.findByRole("button", { name: /Pay Admission Fee Online/i });
    fireEvent.click(payBtn);

    // Verify modal pops up
    expect(await screen.findByText("Sunrise School Payment Gateway")).toBeInTheDocument();
    expect(screen.getByText("Order Ref: ORD-2026-0042")).toBeInTheDocument();
    expect(screen.getByText("UPI / QR Code")).toBeInTheDocument();
    expect(screen.getByText("Cards (Debit / Credit)")).toBeInTheDocument();
    expect(screen.getByText("Net Banking")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Simulate Payment Success/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Simulate Failure/i })).toBeInTheDocument();
  });

  it("displays celebratory banner, student credentials, and official documents center when enrolled", async () => {
    vi.mocked(api.rawGet).mockImplementation(async (path: string) => {
      if (path.includes("/admission/status")) {
        return {
          application_no: "APP-2026-0042",
          name: "Samar Gupta",
          class_applying_for: "1",
          status: "enrolled",
          stage: "enrolled",
          submitted_at: "2026-03-01T10:00:00Z",
          action_needed: false,
          is_payable: false,
          payable_amount: "28500.00",
          documents_available: true,
          offer: {
            id: 12,
            status: "accepted",
            class_name: "1",
            offer_amount: "28500.00",
          },
          student: {
            id: 88,
            admission_no: "ADM-2026-0042",
            class_label: "Class 1-A",
            roll_no: 14,
            status: "active",
          },
          receipt: {
            receipt_no: "AR-2026-0012",
            amount: "28500.00",
            paid_at: "2026-03-10T12:00:00Z",
          },
        };
      }
      return {};
    });

    renderWithClient(<PublicApplyPage />);

    fireEvent.click(screen.getByRole("button", { name: /Track Status & Pay Fee/i }));
    fireEvent.change(screen.getByPlaceholderText("e.g. APP-2026-0001"), {
      target: { value: "APP-2026-0042" },
    });
    fireEvent.change(screen.getByPlaceholderText(/10-digit mobile number/i), {
      target: { value: "9876543210" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Track Application Status/i }));

    // Celebratory confirmation
    expect(await screen.findByText("Welcome to Sunrise Public School!")).toBeInTheDocument();
    expect(screen.getAllByText("ADM-2026-0042").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Class 1-A")).toBeInTheDocument();
    expect(screen.getByText("14")).toBeInTheDocument();
    expect(screen.getByText("AR-2026-0012")).toBeInTheDocument();

    // Student ERP credentials card
    expect(screen.getByText("Student ERP Portal Access")).toBeInTheDocument();
    expect(screen.getByText("Student@123")).toBeInTheDocument();

    // Official Documents Hub
    expect(screen.getByText("Official Admission Documents")).toBeInTheDocument();
    expect(screen.getByText("Application Dossier")).toBeInTheDocument();
    expect(screen.getByText("Provisional Admission Letter")).toBeInTheDocument();
    expect(screen.getByText("Fee Payment Receipt Voucher")).toBeInTheDocument();
  });
});
