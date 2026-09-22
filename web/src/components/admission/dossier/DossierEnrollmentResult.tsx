import React from "react";
import { ApplicationDetail, ApplicationPayment } from "../../../pages/admission/types";
import { Pill } from "../../../components/ui";

interface Props {
  application: ApplicationDetail;
  onPrintDossier: () => void;
  onPrintReceipt?: (receipt: ApplicationPayment) => void;
  recentPayment?: ApplicationPayment | null;
}

export function DossierEnrollmentResult({
  application,
  onPrintDossier,
  onPrintReceipt,
  recentPayment,
}: Props) {
  const enrolled = application.enrolled_student;
  if (!enrolled && application.status !== "enrolled" && application.status !== "admitted") {
    return null;
  }

  const admNo = enrolled?.admission_no || (application as any).admission_no || "PROVISIONAL";
  const classAllocated = enrolled?.class_label || (application as any).class_label || `Class ${application.class_applying_for}`;
  const sectionAllocated = enrolled?.section || "A";
  const rollNo = enrolled?.roll_no ? `#${enrolled.roll_no}` : "Assigned on Roster";
  const academicYear = enrolled?.academic_year || "2026-27";
  const enrollmentStatus = enrolled?.status || "Active Enrollment";

  return (
    <div className="bg-emerald-50 border-2 border-emerald-500 rounded-lg p-4 text-ink shadow-sm space-y-3 mb-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-200 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-lg">
            ✓
          </div>
          <div>
            <h3 className="font-bold text-emerald-950 text-base flex items-center gap-2">
              Official Student Enrollment Confirmed
              <Pill status="present">ACTIVE ENROLLMENT</Pill>
            </h3>
            <p className="text-xs text-emerald-800">
              Candidate has been atomically transitioned from applicant to permanent enrolled student.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onPrintDossier}
            className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print Admission Dossier (PDF)
          </button>
          {recentPayment && onPrintReceipt && (
            <button
              type="button"
              onClick={() => onPrintReceipt(recentPayment)}
              className="px-3 py-1.5 bg-white border border-emerald-600 text-emerald-800 hover:bg-emerald-100 rounded text-xs font-semibold shadow-sm transition flex items-center gap-1.5"
            >
              Print Fee Receipt
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 pt-1 text-xs">
        <div className="bg-white/80 p-2.5 rounded border border-emerald-200">
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">Admission Number</span>
          <span className="font-mono font-bold text-emerald-950 text-sm">{admNo}</span>
        </div>
        <div className="bg-white/80 p-2.5 rounded border border-emerald-200">
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">Enrolled Student</span>
          <span className="font-semibold text-emerald-950 truncate block">{application.name}</span>
        </div>
        <div className="bg-white/80 p-2.5 rounded border border-emerald-200">
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">Academic Session</span>
          <span className="font-semibold text-emerald-950">{academicYear}</span>
        </div>
        <div className="bg-white/80 p-2.5 rounded border border-emerald-200">
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">Class & Stream</span>
          <span className="font-semibold text-emerald-950">{classAllocated}</span>
        </div>
        <div className="bg-white/80 p-2.5 rounded border border-emerald-200">
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">Section & Roll</span>
          <span className="font-semibold text-emerald-950">{sectionAllocated} ({rollNo})</span>
        </div>
        <div className="bg-white/80 p-2.5 rounded border border-emerald-200">
          <span className="text-[10px] uppercase font-bold text-emerald-700 block">Roster Status</span>
          <span className="font-semibold text-emerald-900 uppercase">{enrollmentStatus}</span>
        </div>
      </div>
    </div>
  );
}
