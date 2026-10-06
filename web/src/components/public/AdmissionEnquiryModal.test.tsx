import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../api/client";
import { AdmissionEnquiryModal } from "./AdmissionEnquiryModal";

vi.mock("../../api/client", () => ({
  api: {
    rawPost: vi.fn(),
  },
}));

describe("AdmissionEnquiryModal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits admission enquiry to /public/SPS/admission/enquiry and shows confirmation", async () => {
    vi.mocked(api.rawPost).mockResolvedValue({
      status: "success",
      enquiry_id: 101,
      enquiry_no: "ENQ-0101",
      message: "Enquiry registered successfully! Our admissions desk will get in touch with you shortly.",
    });

    render(
      <MemoryRouter>
        <AdmissionEnquiryModal isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByText("Admission Enquiry")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Vikramaditya Verma/i)).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/Vikramaditya Verma/i), {
      target: { value: "Vikramaditya Verma" },
    });
    fireEvent.change(screen.getByPlaceholderText(/\+91 98765 43210/i), {
      target: { value: "+91 98765 43210" },
    });

    const submitBtn = screen.getByRole("button", { name: /Submit Enquiry/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.rawPost).toHaveBeenCalledWith(
        "/public/SPS/admission/enquiry",
        expect.objectContaining({
          enquirer_name: "Vikramaditya Verma",
          mobile: "+91 98765 43210",
        }),
      );
    });

    expect(await screen.findByText(/Enquiry Received!/i)).toBeInTheDocument();
    expect(screen.getByText(/Reference: ENQ-0101/i)).toBeInTheDocument();
  });
});
