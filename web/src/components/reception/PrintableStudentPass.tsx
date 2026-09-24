import React, { useRef } from "react";
import { toMediaUrl } from "../../api/client";

export interface StudentPassData {
  id: number;
  pass_code: string;
  student_id: number;
  student_name: string;
  admission_no: string;
  class_name?: string | null;
  reason: string;
  pickup_person_name: string;
  pickup_person_relation: string;
  pickup_person_phone: string;
  pickup_person_id_proof?: string | null;
  pickup_person_photo_url?: string | null;
  pass_date: string;
  pass_time: string;
  issued_by_name: string;
  status: string;
  remarks?: string | null;
}

export function PrintableStudentPass({
  pass,
  onClose,
}: {
  pass: StudentPassData;
  onClose: () => void;
}) {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    window.print();
  };

  const formattedDate = new Date(pass.pass_date).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white text-black w-full max-w-2xl rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[95vh]">
        {/* Top bar (hidden in print) */}
        <div className="flex items-center justify-between px-6 py-3 bg-gray-100 border-b border-gray-300 print:hidden">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-800 text-sm">
              Official Student Gate Pass
            </span>
            <span className="text-xs bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded font-mono font-bold">
              {pass.pass_code}
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
              Print Gate Pass
            </button>
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
          </div>
        </div>

        {/* Printable Pass Body */}
        <div ref={printRef} className="p-8 overflow-y-auto print:p-0 print:m-0 text-xs font-sans">
          <style>{`
            @media print {
              body * { visibility: hidden; }
              #printable-gate-pass, #printable-gate-pass * { visibility: visible; }
              #printable-gate-pass { position: absolute; left: 0; top: 0; width: 100%; }
              @page { size: A5 landscape; margin: 10mm; }
            }
          `}</style>

          <div id="printable-gate-pass" className="border-2 border-gray-900 p-5 rounded bg-white">
            {/* Header */}
            <div className="flex justify-between items-center border-b-2 border-gray-900 pb-3 mb-3">
              <div>
                <h1 className="text-lg font-black text-gray-900 tracking-wide uppercase">
                  Sunrise Public School
                </h1>
                <p className="text-[10px] text-gray-600">
                  Sector 14, Vikas Nagar, Lucknow — Affiliation No. 2130001
                </p>
                <div className="mt-1 inline-block bg-gray-900 text-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-xs">
                  Official Student Gate Pass (One-Time Exit)
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-gray-500 block uppercase">Pass Code</span>
                <span className="text-base font-black font-mono text-blue-900">{pass.pass_code}</span>
                <div className="text-[10px] text-gray-600 font-medium">
                  Date: <span className="font-semibold text-gray-900">{formattedDate}</span>
                </div>
                <div className="text-[10px] text-gray-600 font-medium">
                  Time: <span className="font-semibold text-gray-900">{pass.pass_time}</span>
                </div>
              </div>
            </div>

            {/* Student & Pass Particulars */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              {/* Student Details */}
              <div className="border border-gray-300 rounded p-2.5 bg-gray-50/50">
                <span className="text-[10px] font-bold text-gray-700 uppercase tracking-wider block border-b border-gray-200 pb-1 mb-1.5">
                  1. Student Particulars
                </span>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Student Name:</span>
                    <span className="font-bold text-gray-900">{pass.student_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Admission No:</span>
                    <span className="font-mono font-semibold text-gray-900">{pass.admission_no}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Class & Section:</span>
                    <span className="font-semibold text-gray-900">{pass.class_name || "—"}</span>
                  </div>
                </div>
              </div>

              {/* Pickup Person Details */}
              <div className="border border-gray-300 rounded p-2.5 bg-gray-50/50">
                <span className="text-[10px] font-bold text-gray-700 uppercase tracking-wider block border-b border-gray-200 pb-1 mb-1.5">
                  2. Authorized Escort / Pickup Person
                </span>
                <div className="flex gap-2.5">
                  {pass.pickup_person_photo_url && (
                    <img
                      src={toMediaUrl(pass.pickup_person_photo_url)}
                      alt={pass.pickup_person_name}
                      className="w-14 h-16 object-cover rounded border border-gray-300 shadow-xs flex-shrink-0"
                    />
                  )}
                  <div className="space-y-1 text-[11px] flex-1 min-w-0">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Escort Name:</span>
                      <span className="font-bold text-gray-900 truncate ml-1">{pass.pickup_person_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Relationship:</span>
                      <span className="font-semibold text-gray-900">{pass.pickup_person_relation}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Phone Number:</span>
                      <span className="font-mono font-semibold text-gray-900">{pass.pickup_person_phone}</span>
                    </div>
                    {pass.pickup_person_id_proof && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">ID Proof:</span>
                        <span className="font-semibold text-gray-800">{pass.pickup_person_id_proof}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Reason & Remarks */}
            <div className="border border-gray-300 rounded p-2.5 mb-4 text-[11px]">
              <div className="flex gap-2">
                <span className="text-gray-500 font-medium whitespace-nowrap">Reason for Leaving:</span>
                <span className="font-semibold text-gray-900">{pass.reason}</span>
              </div>
              {pass.remarks && (
                <div className="flex gap-2 mt-1">
                  <span className="text-gray-500 font-medium whitespace-nowrap">Remarks:</span>
                  <span className="text-gray-800">{pass.remarks}</span>
                </div>
              )}
            </div>

            {/* Verification Signatures */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-gray-300 text-center text-[10px]">
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  {pass.issued_by_name}
                </div>
                <div className="text-gray-500">Front Desk (Issued By)</div>
              </div>
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  Escort Signature
                </div>
                <div className="text-gray-500">Parent / Authorized Person</div>
              </div>
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  Security Guard & Out-Time
                </div>
                <div className="text-gray-500">Main Gate Checkpoint</div>
              </div>
            </div>

            <div className="mt-3 text-center text-[9px] text-gray-400 italic">
              Notice: This is a single-use authorized gate pass. Gate security must retain this slip upon departure.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
