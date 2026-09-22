import React, { useRef } from "react";
import { Enquiry } from "../../pages/admission/types";

export function PrintableEnquirySlip({
  enquiry,
  cycleName,
  onClose,
}: {
  enquiry: Enquiry;
  cycleName?: string;
  onClose?: () => void;
}) {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    window.print();
  };

  const formattedDob = enquiry.child_dob
    ? new Date(enquiry.child_dob).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

  const formattedFollowUp = enquiry.next_follow_up_on
    ? new Date(enquiry.next_follow_up_on).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

  const todayFormatted = new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white text-black w-full max-w-3xl rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Top Control Bar (Hidden when printing) */}
        <div className="flex items-center justify-between px-6 py-3 bg-gray-100 border-b border-gray-300 print:hidden">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-800 text-sm">
              Official Admission Enquiry Slip (A5)
            </span>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-mono font-medium">
              ENQ-{String(enquiry.id).padStart(5, "0")}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 transition shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
                />
              </svg>
              Print Enquiry Slip
            </button>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="text-red-500 hover:text-red-700 hover:bg-red-50 p-1.5 rounded-full transition-colors flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-red-400"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Printable Slip Container */}
        <div
          ref={printRef}
          className="p-8 overflow-y-auto print:p-0 print:overflow-visible print:m-0 text-[12px] leading-normal font-sans"
        >
          <style>{`
            @media print {
              body * {
                visibility: hidden;
              }
              #printable-enquiry-slip, #printable-enquiry-slip * {
                visibility: visible;
              }
              #printable-enquiry-slip {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
              }
              @page {
                size: A5 portrait;
                margin: 10mm;
              }
            }
          `}</style>

          <div id="printable-enquiry-slip" className="border border-gray-800 p-5 rounded-sm bg-white">
            {/* School Header */}
            <div className="text-center border-b-2 border-gray-800 pb-3 mb-4">
              <h1 className="text-lg font-bold tracking-wider text-gray-900 uppercase">
                Sunrise Public School
              </h1>
              <p className="text-[11px] text-gray-600 font-medium">
                Affiliated to CBSE, New Delhi (Affiliation No. 2130001) | School Code: 70142
              </p>
              <p className="text-[10px] text-gray-500">
                Sector 14, Vikas Nagar, Lucknow, Uttar Pradesh — 226022
              </p>
              <p className="text-[10px] text-gray-500">
                Contact: +91 522 400 1234 | Email: admissions@sunrisepublic.edu | www.sunrisepublic.edu
              </p>
              <div className="mt-2 inline-block px-3 py-0.5 bg-gray-100 border border-gray-400 text-gray-800 font-bold text-xs uppercase tracking-wider">
                Admission Enquiry Slip (Parent Copy)
              </div>
            </div>

            {/* Reference Bar */}
            <div className="flex justify-between items-center text-[11px] bg-gray-50 border border-gray-300 px-3 py-1.5 mb-3">
              <div>
                <span className="font-semibold text-gray-700">Enquiry Ref No: </span>
                <span className="font-mono font-bold text-gray-900">
                  ENQ-{String(enquiry.id).padStart(5, "0")}
                </span>
              </div>
              <div>
                <span className="font-semibold text-gray-700">Date: </span>
                <span className="font-medium text-gray-900">{todayFormatted}</span>
              </div>
              <div>
                <span className="font-semibold text-gray-700">Cycle: </span>
                <span className="font-medium text-gray-900">{cycleName || "Academic Session 2026-27"}</span>
              </div>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* Applicant Details */}
              <div className="border border-gray-300 rounded-sm p-2.5">
                <div className="font-bold text-xs text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase">
                  Candidate Details
                </div>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Candidate Name:</span>
                    <span className="font-semibold text-gray-900">{enquiry.child_name || "—"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Date of Birth:</span>
                    <span className="font-semibold text-gray-900">{formattedDob}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Class of Interest:</span>
                    <span className="font-bold text-blue-900">
                      Class {enquiry.class_of_interest || "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Enquiry Channel:</span>
                    <span className="font-medium text-gray-900 capitalize">{enquiry.source || "Walk-in"}</span>
                  </div>
                </div>
              </div>

              {/* Parent/Enquirer Details */}
              <div className="border border-gray-300 rounded-sm p-2.5">
                <div className="font-bold text-xs text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase">
                  Parent / Guardian Details
                </div>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Enquirer Name:</span>
                    <span className="font-semibold text-gray-900">{enquiry.enquirer_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Primary Mobile:</span>
                    <span className="font-mono font-semibold text-gray-900">{enquiry.mobile}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Email Address:</span>
                    <span className="font-medium text-gray-900 truncate max-w-[140px]">
                      {enquiry.email || "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Next Follow-up:</span>
                    <span className="font-medium text-gray-900">{formattedFollowUp}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Document Requirements Checklist for Parent */}
            <div className="border border-gray-300 rounded-sm p-3 mb-4 bg-gray-50/50">
              <div className="font-bold text-xs text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase flex items-center justify-between">
                <span>Required Documents Checklist for Admission</span>
                <span className="text-[10px] font-normal text-gray-500 normal-case">
                  (Please bring when submitting dossier)
                </span>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10.5px] text-gray-700">
                <div className="flex items-start gap-1.5">
                  <span className="font-bold text-gray-400">□</span>
                  <span>Original Birth Certificate + 2 Photocopies</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <span className="font-bold text-gray-400">□</span>
                  <span>Aadhaar Card Copy (Student & Parents)</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <span className="font-bold text-gray-400">□</span>
                  <span>4 Student Photos, 2 of each Parent</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <span className="font-bold text-gray-400">□</span>
                  <span>Previous School Marksheet & TC (Class 1+)</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <span className="font-bold text-gray-400">□</span>
                  <span>Residence Proof (Electricity/Passport/Rent)</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <span className="font-bold text-gray-400">□</span>
                  <span>Category/Caste Certificate (if applicable)</span>
                </div>
              </div>
            </div>

            {/* Tear-off Separator */}
            <div className="relative my-4 border-t-2 border-dashed border-gray-400">
              <span className="absolute left-1/2 -top-2.5 -translate-x-1/2 bg-white px-2 text-[9px] text-gray-500 font-mono tracking-wider uppercase">
                ✄ Tear-off counter acknowledgment ✄
              </span>
            </div>

            {/* Office Copy Counterfoil */}
            <div className="pt-2 text-[10.5px]">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold uppercase tracking-wide text-gray-800">
                  Office Acknowledgment Slip — Front Desk Record
                </span>
                <span className="font-mono text-gray-600 font-medium">
                  Ref: ENQ-{String(enquiry.id).padStart(5, "0")} | Date: {todayFormatted}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-gray-700 mb-3 bg-gray-50 p-2 border border-gray-200 rounded-sm">
                <div>
                  <span className="text-gray-500 block text-[9px]">Candidate:</span>
                  <span className="font-semibold text-gray-900">{enquiry.child_name || "—"}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-[9px]">Class Applied:</span>
                  <span className="font-semibold text-gray-900">Class {enquiry.class_of_interest || "—"}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-[9px]">Enquirer & Phone:</span>
                  <span className="font-semibold text-gray-900">
                    {enquiry.enquirer_name} ({enquiry.mobile})
                  </span>
                </div>
              </div>

              {/* Signatures */}
              <div className="flex justify-between items-end pt-3 text-[10px]">
                <div className="text-center">
                  <div className="w-36 border-b border-gray-400 mb-1" />
                  <span className="text-gray-600">Parent / Visitor Signature</span>
                </div>
                <div className="text-center border border-gray-300 w-28 h-12 flex items-center justify-center text-[9px] text-gray-400 uppercase rounded-sm">
                  Desk Seal Box
                </div>
                <div className="text-center">
                  <div className="w-36 border-b border-gray-400 mb-1" />
                  <span className="text-gray-600">Front Desk Staff Signature</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
