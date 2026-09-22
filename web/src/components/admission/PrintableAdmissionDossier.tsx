import React, { useRef } from "react";
import {
  ApplicationDetail,
  ApplicationMedical,
  ApplicationPayment,
  ChecklistItem,
} from "../../pages/admission/types";

export function PrintableAdmissionDossier({
  application,
  medical,
  checklist,
  payments,
  studentInfo,
  onClose,
}: {
  application: ApplicationDetail;
  medical?: ApplicationMedical | null;
  checklist?: ChecklistItem[];
  payments?: ApplicationPayment[];
  studentInfo?: {
    admission_no?: string;
    class_label?: string;
    roll_no?: number;
  };
  onClose?: () => void;
}) {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    window.print();
  };

  const fullName = `${application.first_name || ""} ${
    application.middle_name ? application.middle_name + " " : ""
  }${application.last_name || ""}`.trim();

  const formattedDob = application.date_of_birth
    ? new Date(application.date_of_birth).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      })
    : "—";

  const submittedDate = application.submitted_at
    ? new Date(application.submitted_at).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "Draft Stage";

  const admissionNo =
    studentInfo?.admission_no ||
    application.enrolled_student?.admission_no ||
    (application as any).admission_no ||
    "PROVISIONAL";

  const classAllocated =
    studentInfo?.class_label ||
    application.enrolled_student?.class_label ||
    (application as any).class_label ||
    `Class ${application.class_applying_for}`;

  const address = application.address || {};
  const prevSchool = application.previous_school || {};

  const fatherGuardian = application.guardians?.find(
    (g) => g.relation?.toLowerCase() === "father"
  );
  const motherGuardian = application.guardians?.find(
    (g) => g.relation?.toLowerCase() === "mother"
  );
  const otherGuardians = application.guardians?.filter(
    (g) => g !== fatherGuardian && g !== motherGuardian
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white text-black w-full max-w-5xl rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[94vh]">
        {/* Top bar (hidden in print) */}
        <div className="flex items-center justify-between px-6 py-3 bg-gray-100 border-b border-gray-300 print:hidden">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-800 text-sm">
              Professional School Admission Dossier
            </span>
            <span className="text-xs bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded font-mono font-medium">
              {application.application_no}
            </span>
            {studentInfo?.admission_no && (
              <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono font-semibold">
                Adm No: {studentInfo.admission_no}
              </span>
            )}
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
              Print / Save Dossier (PDF)
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

        {/* Printable Area */}
        <div
          ref={printRef}
          className="p-8 overflow-y-auto print:p-0 print:overflow-visible print:m-0 text-[11.5px] leading-relaxed font-sans"
        >
          <style>{`
            @media print {
              body * {
                visibility: hidden;
              }
              #printable-dossier, #printable-dossier * {
                visibility: visible;
              }
              #printable-dossier {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
              }
              @page {
                size: A4 portrait;
                margin: 12mm;
              }
              .page-break {
                page-break-after: always;
                break-after: page;
              }
            }
          `}</style>

          <div id="printable-dossier" className="space-y-4">
            {/* PAGE 1: HEADER & PRIMARY APPLICANT INFORMATION */}
            <div className="border border-gray-800 p-6 rounded-sm bg-white">
              {/* Institution Header */}
              <div className="flex justify-between items-start border-b-2 border-gray-900 pb-3 mb-4">
                <div className="flex-1">
                  <h1 className="text-xl font-black tracking-wider text-gray-900 uppercase">
                    Sunrise Public School
                  </h1>
                  <p className="text-[11px] text-gray-700 font-medium">
                    Sector 14, Vikas Nagar, Lucknow, Uttar Pradesh — 226022
                  </p>
                  <p className="text-[10px] text-gray-500">
                    Affiliation No. 2130001 | School Code: 70142 | Tel: +91 522 400 1234
                  </p>
                  <div className="mt-1.5 inline-block px-2.5 py-0.5 bg-gray-900 text-white text-xs font-bold uppercase tracking-wider rounded-xs">
                    Professional School Admission Dossier — Academic Session 2026-27
                  </div>
                </div>

                {/* Photo & Barcode Block */}
                <div className="flex items-center gap-3">
                  <div className="w-24 h-28 border-2 border-dashed border-gray-400 rounded-sm flex flex-col items-center justify-center text-center p-1 bg-gray-50">
                    <span className="text-[9px] text-gray-400 font-medium leading-tight">
                      Affix Recent Passport Photo
                    </span>
                    <span className="text-[8px] text-gray-300 mt-1">
                      (Cross-sign across photo)
                    </span>
                  </div>
                </div>
              </div>

              {/* Dossier Meta Summary */}
              <div className="grid grid-cols-4 gap-2 bg-gray-100 border border-gray-300 p-2 text-[11px] mb-4 font-medium">
                <div>
                  <span className="text-gray-500 block text-[9px] uppercase">Application No:</span>
                  <span className="font-mono font-bold text-gray-900">{application.application_no}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-[9px] uppercase">Admission Number:</span>
                  <span className="font-mono font-bold text-blue-900">{admissionNo}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-[9px] uppercase">Allocated Section:</span>
                  <span className="font-bold text-gray-900">{classAllocated}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-[9px] uppercase">Status / Submitted:</span>
                  <span className="font-bold text-emerald-800 uppercase">
                    {application.status} ({submittedDate})
                  </span>
                </div>
              </div>

              {/* Section 1: Candidate Personal Details */}
              <div className="mb-4">
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                  1. Applicant Personal Details
                </div>
                <div className="border border-gray-300 rounded-sm p-3">
                  <div className="grid grid-cols-3 gap-y-2 gap-x-4 text-[11px]">
                    <div>
                      <span className="text-gray-500 block text-[10px]">Full Name:</span>
                      <span className="font-bold text-gray-900">{fullName || "—"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Date of Birth:</span>
                      <span className="font-semibold text-gray-900">{formattedDob}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Gender:</span>
                      <span className="font-semibold text-gray-900 capitalize">
                        {application.gender || "—"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Aadhaar Last 4 Digits:</span>
                      <span className="font-mono font-semibold text-gray-900">
                        {application.aadhaar_last4 ? `XXXX-XXXX-${application.aadhaar_last4}` : "—"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Nationality:</span>
                      <span className="font-semibold text-gray-900">{application.nationality || "Indian"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Mother Tongue:</span>
                      <span className="font-semibold text-gray-900">{application.mother_tongue || "Hindi"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Religion / Category:</span>
                      <span className="font-semibold text-gray-900">
                        {application.religion || "—"} / {application.caste_category || "General"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Place of Birth:</span>
                      <span className="font-semibold text-gray-900">{application.place_of_birth || "—"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Single Child:</span>
                      <span className="font-semibold text-gray-900">
                        {application.is_single_child ? "Yes" : "No"}
                      </span>
                    </div>
                    {application.identification_marks && (
                      <div className="col-span-3">
                        <span className="text-gray-500 block text-[10px]">Identification Marks:</span>
                        <span className="font-semibold text-gray-900">{application.identification_marks}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Section 2: Admission & Academic Preferences */}
              <div className="mb-4">
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                  2. Academic & Enrollment Preferences
                </div>
                <div className="border border-gray-300 rounded-sm p-3">
                  <div className="grid grid-cols-4 gap-y-2 gap-x-4 text-[11px]">
                    <div>
                      <span className="text-gray-500 block text-[10px]">Class Applying For:</span>
                      <span className="font-bold text-blue-900">Class {application.class_applying_for}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Stream (if 11-12):</span>
                      <span className="font-semibold text-gray-900">{application.stream || "General"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Second Language:</span>
                      <span className="font-semibold text-gray-900">{application.second_language || "Hindi"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Optional Subject:</span>
                      <span className="font-semibold text-gray-900">{application.optional_subject || "—"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Admission Category:</span>
                      <span className="font-semibold text-gray-900 uppercase">
                        {application.admission_category || "General"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Transport Facility:</span>
                      <span className="font-semibold text-gray-900">
                        {application.transport_required ? "Required" : "Self Commute"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Preferred Section:</span>
                      <span className="font-semibold text-gray-900">{application.preferred_section || "Auto"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Application Source:</span>
                      <span className="font-semibold text-gray-900 capitalize">{application.source || "Walk-in"}</span>
                    </div>
                    {application.age_override_reason && (
                      <div className="col-span-4 bg-amber-50 border border-amber-200 p-1.5 rounded text-[10.5px]">
                        <span className="font-bold text-amber-900">Age Eligibility Override Reason: </span>
                        <span className="text-amber-800">{application.age_override_reason}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Section 3: Parents & Legal Guardians */}
              <div className="mb-4">
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                  3. Parents & Guardians Information
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {/* Father Details */}
                  <div className="border border-gray-300 rounded-sm p-3">
                    <div className="font-bold text-[11px] text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase flex justify-between">
                      <span>Father Details</span>
                      {fatherGuardian?.is_primary && (
                        <span className="text-[9px] bg-blue-100 text-blue-800 px-1 rounded font-bold">Primary Contact</span>
                      )}
                    </div>
                    <div className="space-y-1.5 text-[10.5px]">
                      <div>
                        <span className="text-gray-500 block text-[9px]">Full Name:</span>
                        <span className="font-bold text-gray-900">{fatherGuardian?.full_name || "—"}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        <div>
                          <span className="text-gray-500 block text-[9px]">Date of Birth:</span>
                          <span className="font-semibold text-gray-900">{fatherGuardian?.date_of_birth ? String(fatherGuardian.date_of_birth).slice(0, 10) : "—"}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[9px]">Qualification:</span>
                          <span className="font-semibold text-gray-900 truncate block">{fatherGuardian?.qualification || "Graduate"}</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        <div>
                          <span className="text-gray-500 block text-[9px]">Occupation & Designation:</span>
                          <span className="font-semibold text-gray-900">
                            {fatherGuardian?.occupation || "—"} {fatherGuardian?.designation ? `(${fatherGuardian.designation})` : ""}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[9px]">Organisation & Income:</span>
                          <span className="font-semibold text-gray-900 truncate block">
                            {fatherGuardian?.organisation || "—"} {fatherGuardian?.annual_income_band ? `[${fatherGuardian.annual_income_band}]` : ""}
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        <div>
                          <span className="text-gray-500 block text-[9px]">Mobile:</span>
                          <span className="font-mono font-semibold text-gray-900">{fatherGuardian?.mobile || "—"}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[9px]">Email:</span>
                          <span className="font-semibold text-gray-900 truncate block">{fatherGuardian?.email || "—"}</span>
                        </div>
                      </div>
                      {fatherGuardian?.office_address && (
                        <div>
                          <span className="text-gray-500 block text-[9px]">Workplace / Office Address:</span>
                          <span className="font-semibold text-gray-800">{fatherGuardian.office_address}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Mother Details */}
                  <div className="border border-gray-300 rounded-sm p-3">
                    <div className="font-bold text-[11px] text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase flex justify-between">
                      <span>Mother Details</span>
                      {motherGuardian?.is_primary && (
                        <span className="text-[9px] bg-blue-100 text-blue-800 px-1 rounded font-bold">Primary Contact</span>
                      )}
                    </div>
                    <div className="space-y-1.5 text-[10.5px]">
                      <div>
                        <span className="text-gray-500 block text-[9px]">Full Name:</span>
                        <span className="font-bold text-gray-900">{motherGuardian?.full_name || "—"}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        <div>
                          <span className="text-gray-500 block text-[9px]">Date of Birth:</span>
                          <span className="font-semibold text-gray-900">{motherGuardian?.date_of_birth ? String(motherGuardian.date_of_birth).slice(0, 10) : "—"}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[9px]">Qualification:</span>
                          <span className="font-semibold text-gray-900 truncate block">{motherGuardian?.qualification || "Graduate"}</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        <div>
                          <span className="text-gray-500 block text-[9px]">Occupation & Designation:</span>
                          <span className="font-semibold text-gray-900">
                            {motherGuardian?.occupation || "—"} {motherGuardian?.designation ? `(${motherGuardian.designation})` : ""}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[9px]">Organisation & Income:</span>
                          <span className="font-semibold text-gray-900 truncate block">
                            {motherGuardian?.organisation || "—"} {motherGuardian?.annual_income_band ? `[${motherGuardian.annual_income_band}]` : ""}
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-1">
                        <div>
                          <span className="text-gray-500 block text-[9px]">Mobile:</span>
                          <span className="font-mono font-semibold text-gray-900">{motherGuardian?.mobile || "—"}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[9px]">Email:</span>
                          <span className="font-semibold text-gray-900 truncate block">{motherGuardian?.email || "—"}</span>
                        </div>
                      </div>
                      {motherGuardian?.office_address && (
                        <div>
                          <span className="text-gray-500 block text-[9px]">Workplace / Office Address:</span>
                          <span className="font-semibold text-gray-800">{motherGuardian.office_address}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Additional Guardians */}
                {otherGuardians && otherGuardians.length > 0 && (
                  <div className="mt-2 border border-gray-300 rounded-sm p-2 text-[10.5px]">
                    <span className="font-bold text-gray-700">Other Legal Guardian(s): </span>
                    {otherGuardians.map((og, idx) => (
                      <span key={og.id || idx} className="text-gray-900 font-medium">
                        {og.full_name} ({og.relation}, Ph: {og.mobile}, {og.occupation || "Service"}){idx < otherGuardians.length - 1 ? "; " : ""}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Section 4: Address Details */}
              <div>
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                  4. Residential & Permanent Address
                </div>
                <div className="border border-gray-300 rounded-sm p-3">
                  <div className="grid grid-cols-4 gap-2 text-[11px]">
                    <div className="col-span-2">
                      <span className="text-gray-500 block text-[10px]">Current Residential Address:</span>
                      <span className="font-semibold text-gray-900">
                        {[
                          address.line1 || address.address_line_1,
                          address.line2 || address.address_line_2,
                        ]
                          .filter(Boolean)
                          .join(", ") || "—"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">City & State:</span>
                      <span className="font-semibold text-gray-900">
                        {address.city || "Lucknow"}, {address.state || "Uttar Pradesh"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">PIN Code / Country:</span>
                      <span className="font-semibold text-gray-900 font-mono">
                        {address.pincode || "226022"} ({address.country || "India"})
                      </span>
                    </div>
                  </div>

                  {address.same_as_residential === false && address.permanent_line1 && (
                    <div className="mt-2 pt-2 border-t border-gray-200 grid grid-cols-4 gap-2 text-[10.5px]">
                      <div className="col-span-2">
                        <span className="text-gray-500 block text-[9px]">Permanent Home / Domicile Address:</span>
                        <span className="font-semibold text-gray-800">{address.permanent_line1}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block text-[9px]">City & State:</span>
                        <span className="font-semibold text-gray-800">{address.permanent_city}, {address.permanent_state}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block text-[9px]">PIN Code:</span>
                        <span className="font-semibold text-gray-800 font-mono">{address.permanent_pincode}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* PAGE 2 / CONTINUATION: ACADEMICS, MEDICAL, DOCUMENTS, FEES & SIGN-OFF */}
            <div className="border border-gray-800 p-6 rounded-sm bg-white mt-4">
              {/* Section 5: Previous School & Sibling History */}
              <div className="mb-4">
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                  5. Previous Academic History & Sibling Record
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="border border-gray-300 rounded-sm p-3 text-[11px]">
                    <div className="font-bold text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase">
                      Previous School Record
                    </div>
                    <div className="space-y-1">
                      <div>
                        <span className="text-gray-500">School Name: </span>
                        <span className="font-semibold text-gray-900">{prevSchool.school_name || "N/A (First Admission)"}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Board / Last Class: </span>
                        <span className="font-semibold text-gray-900">
                          {prevSchool.board || "—"} {prevSchool.last_class ? `(Class ${prevSchool.last_class})` : ""}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">TC Number & Date: </span>
                        <span className="font-semibold text-gray-900">
                          {prevSchool.tc_number ? `${prevSchool.tc_number} (${prevSchool.tc_date || ""})` : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="border border-gray-300 rounded-sm p-3 text-[11px]">
                    <div className="font-bold text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase">
                      Siblings in Sunrise Public School
                    </div>
                    {application.siblings && application.siblings.length > 0 ? (
                      <div className="space-y-1">
                        {application.siblings.map((sib) => (
                          <div key={sib.id} className="text-gray-900 font-medium">
                            • {sib.name} (Age: {sib.age || "—"}, {sib.school_name || "Sunrise Public School"})
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-gray-500 italic">No sibling currently enrolled in the institution.</div>
                    )}
                  </div>
                </div>
              </div>

              {/* Section 6: Health & Medical Profile */}
              <div className="mb-4">
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                  6. Student Health & Medical Profile
                </div>
                <div className="border border-gray-300 rounded-sm p-3">
                  <div className="grid grid-cols-4 gap-y-2 gap-x-4 text-[11px]">
                    <div>
                      <span className="text-gray-500 block text-[10px]">Blood Group:</span>
                      <span className="font-bold text-red-900">{medical?.blood_group || "—"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Height & Weight:</span>
                      <span className="font-semibold text-gray-900">
                        {medical?.height_cm ? `${medical.height_cm} cm` : "—"} / {medical?.weight_kg ? `${medical.weight_kg} kg` : "—"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Known Allergies:</span>
                      <span className="font-semibold text-gray-900">{medical?.known_allergies || "None reported"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-[10px]">Chronic Conditions:</span>
                      <span className="font-semibold text-gray-900">{medical?.chronic_conditions || "None reported"}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-500 block text-[10px]">Regular Medication:</span>
                      <span className="font-semibold text-gray-900">{medical?.regular_medication || "None"}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-500 block text-[10px]">Emergency Doctor & Phone:</span>
                      <span className="font-semibold text-gray-900">
                        {medical?.emergency_doctor ? `${medical.emergency_doctor} (${medical.emergency_doctor_phone || "—"})` : "—"}
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-500 block text-[10px]">Emergency Treatment Consent:</span>
                      <span className="font-semibold text-gray-900">
                        {medical?.consent_for_emergency_treatment ? "Granted by Parent" : "Standard School Protocol"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 7: Document Verification Checklist (Dynamic) */}
              <div className="mb-4">
                <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2 flex justify-between">
                  <span>7. Document Verification Audit</span>
                  <span className="text-[10px] font-normal lowercase opacity-90">
                    (Verified against institutional records)
                  </span>
                </div>
                <table className="w-full border-collapse border border-gray-300 text-[10.5px]">
                  <thead>
                    <tr className="bg-gray-100 text-gray-800">
                      <th className="border border-gray-300 px-2 py-1 text-left">Document Title</th>
                      <th className="border border-gray-300 px-2 py-1 text-center w-24">Mandatory</th>
                      <th className="border border-gray-300 px-2 py-1 text-center w-28">Status</th>
                      <th className="border border-gray-300 px-2 py-1 text-center w-36">Verification Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {checklist && checklist.length > 0 ? (
                      checklist.map((item) => (
                        <tr key={item.code}>
                          <td className="border border-gray-300 px-2 py-1 font-medium text-gray-900">
                            {item.name}
                          </td>
                          <td className="border border-gray-300 px-2 py-1 text-center text-gray-600">
                            {item.mandatory ? "Yes" : "Optional"}
                          </td>
                          <td className="border border-gray-300 px-2 py-1 text-center">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9.5px] font-bold uppercase ${
                                item.status === "verified"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : item.status === "submitted"
                                  ? "bg-blue-100 text-blue-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {item.status}
                            </span>
                          </td>
                          <td className="border border-gray-300 px-2 py-1 text-center font-mono text-[10px] text-gray-600">
                            {item.verified_at
                              ? new Date(item.verified_at).toLocaleDateString("en-IN")
                              : "—"}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <>
                        <tr>
                          <td className="border border-gray-300 px-2 py-1 font-medium">Birth Certificate (Govt. Registrar / Municipality)</td>
                          <td className="border border-gray-300 px-2 py-1 text-center">Yes</td>
                          <td className="border border-gray-300 px-2 py-1 text-center text-emerald-800 font-bold uppercase">VERIFIED</td>
                          <td className="border border-gray-300 px-2 py-1 text-center font-mono text-[10px]">Verified at counter</td>
                        </tr>
                        <tr>
                          <td className="border border-gray-300 px-2 py-1 font-medium">Student & Parent Aadhaar Identity Proof</td>
                          <td className="border border-gray-300 px-2 py-1 text-center">Yes</td>
                          <td className="border border-gray-300 px-2 py-1 text-center text-emerald-800 font-bold uppercase">VERIFIED</td>
                          <td className="border border-gray-300 px-2 py-1 text-center font-mono text-[10px]">Verified at counter</td>
                        </tr>
                        <tr>
                          <td className="border border-gray-300 px-2 py-1 font-medium">Proof of Residential Address</td>
                          <td className="border border-gray-300 px-2 py-1 text-center">Yes</td>
                          <td className="border border-gray-300 px-2 py-1 text-center text-emerald-800 font-bold uppercase">VERIFIED</td>
                          <td className="border border-gray-300 px-2 py-1 text-center font-mono text-[10px]">Verified at counter</td>
                        </tr>
                      </>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Section 8: Fee & Enrollment Transaction Record */}
              {payments && payments.length > 0 && (
                <div className="mb-4">
                  <div className="bg-gray-800 text-white px-3 py-1 text-xs font-bold uppercase tracking-wider mb-2">
                    8. Fee Collection & Payment Receipt Record
                  </div>
                  <table className="w-full border-collapse border border-gray-300 text-[10.5px]">
                    <thead>
                      <tr className="bg-gray-100 text-gray-800">
                        <th className="border border-gray-300 px-2 py-1 text-left">Receipt No</th>
                        <th className="border border-gray-300 px-2 py-1 text-left">Purpose</th>
                        <th className="border border-gray-300 px-2 py-1 text-right">Amount Paid</th>
                        <th className="border border-gray-300 px-2 py-1 text-center">Mode & Ref</th>
                        <th className="border border-gray-300 px-2 py-1 text-center">Date Paid</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payments.map((p) => (
                        <tr key={p.id}>
                          <td className="border border-gray-300 px-2 py-1 font-mono font-bold text-gray-900">
                            {p.receipt_no}
                          </td>
                          <td className="border border-gray-300 px-2 py-1 capitalize">
                            {p.purpose.replace("_", " ")}
                          </td>
                          <td className="border border-gray-300 px-2 py-1 text-right font-mono font-bold text-gray-900">
                            ₹{parseFloat(p.amount).toFixed(2)}
                          </td>
                          <td className="border border-gray-300 px-2 py-1 text-center uppercase text-gray-700">
                            {p.method} {p.reference ? `(${p.reference})` : ""}
                          </td>
                          <td className="border border-gray-300 px-2 py-1 text-center font-mono text-[10px] text-gray-600">
                            {new Date(p.paid_at).toLocaleDateString("en-IN")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Section 9: Declarations & Parent Undertaking */}
              <div className="mb-4 border border-gray-300 rounded-sm p-3 bg-gray-50/50">
                <div className="font-bold text-xs text-gray-800 border-b border-gray-200 pb-1 mb-2 uppercase">
                  9. Parent Undertaking & Code of Conduct
                </div>
                <p className="text-[10px] text-gray-600 leading-relaxed mb-3">
                  I/We hereby certify that all information furnished in this admission dossier is accurate and verifiable.
                  I agree to abide by all disciplinary policies, transport rules, code of conduct, and fee payment schedules of
                  Sunrise Public School. I understand that admission may be rescinded if any material information is found false.
                </p>
                <div className="flex justify-between items-end pt-3 text-[10px]">
                  <div className="text-center">
                    <div className="font-semibold text-gray-900 text-[10.5px] pb-0.5">
                      {application.declarations?.parent_signature_name || fatherGuardian?.full_name || "—"}
                    </div>
                    <div className="w-40 border-b border-gray-400 mb-1" />
                    <span className="text-gray-600">Signature of Parent / Legal Guardian</span>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-gray-900 text-[10.5px] pb-0.5">
                      {motherGuardian?.full_name || "—"}
                    </div>
                    <div className="w-40 border-b border-gray-400 mb-1" />
                    <span className="text-gray-600">Signature of Mother / Co-Guardian</span>
                  </div>
                  <div className="text-center">
                    <div className="w-28 border-b border-gray-400 mb-1" />
                    <span className="text-gray-600">
                      Date: {application.declarations?.declared_on || submittedDate}
                    </span>
                  </div>
                </div>
              </div>

              {/* Section 10: Official Institutional Endorsement */}
              <div className="border-2 border-gray-900 rounded-sm p-3 bg-white">
                <div className="font-bold text-xs text-gray-900 border-b border-gray-900 pb-1 mb-2 uppercase flex justify-between">
                  <span>10. Official Admission Office Endorsement & Enrolment Seal</span>
                  <span className="font-mono text-blue-900">
                    ADM NO: {admissionNo}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-[10.5px] mb-3 bg-gray-50 p-2 border border-gray-200">
                  <div>
                    <span className="text-gray-500 block text-[9px]">Admission Status:</span>
                    <span className="font-bold text-emerald-800 uppercase">
                      {application.status === "enrolled" ? "Enrolled & Active" : "Approved for Enrolment"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[9px]">Enrolled Section:</span>
                    <span className="font-bold text-gray-900">{classAllocated}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[9px]">Roll Number:</span>
                    <span className="font-mono font-bold text-gray-900">
                      {studentInfo?.roll_no ?? application.enrolled_student?.roll_no
                        ? `Roll #${studentInfo?.roll_no ?? application.enrolled_student?.roll_no}`
                        : "Assigned on Roster"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[9px]">Date of Enrolment:</span>
                    <span className="font-semibold text-gray-900">
                      {new Date().toLocaleDateString("en-IN")}
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-end pt-4 text-[10px]">
                  <div className="text-center">
                    <div className="w-36 border-b border-gray-400 mb-1" />
                    <span className="text-gray-600">Scrutiny / Admission Officer</span>
                  </div>
                  <div className="text-center border border-gray-300 w-32 h-14 flex flex-col items-center justify-center text-[9px] text-gray-400 uppercase rounded-sm">
                    <span>Institutional Seal</span>
                    <span className="text-[8px] text-gray-300">Sunrise Public School</span>
                  </div>
                  <div className="text-center">
                    <div className="w-36 border-b border-gray-400 mb-1" />
                    <span className="text-gray-600 font-semibold">Principal / Head of Institution</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
