import React, { useRef } from "react";

export interface TeacherMeetingData {
  id: number;
  slip_code: string;
  teacher_id: number;
  teacher_name: string;
  visitor_name: string;
  visitor_phone: string;
  visitor_relation?: string | null;
  student_name?: string | null;
  student_admission_no?: string | null;
  reason: string;
  meeting_date: string;
  meeting_time: string;
  status: string;
  response_notes?: string | null;
  created_by_name: string;
  responded_at?: string | null;
}

export function PrintableTeacherMeetingSlip({
  meeting,
  onClose,
}: {
  meeting: TeacherMeetingData;
  onClose: () => void;
}) {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    window.print();
  };

  const formattedDate = new Date(meeting.meeting_date).toLocaleDateString("en-IN", {
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
              Teacher Visitor Meeting Slip
            </span>
            <span className="text-xs bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded font-mono font-bold">
              {meeting.slip_code}
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
              Print Meeting Slip
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

        {/* Printable Slip Body */}
        <div ref={printRef} className="p-8 overflow-y-auto print:p-0 print:m-0 text-xs font-sans">
          <style>{`
            @media print {
              body * { visibility: hidden; }
              #printable-teacher-slip, #printable-teacher-slip * { visibility: visible; }
              #printable-teacher-slip { position: absolute; left: 0; top: 0; width: 100%; }
              @page { size: A5 landscape; margin: 10mm; }
            }
          `}</style>

          <div id="printable-teacher-slip" className="border-2 border-gray-900 p-5 rounded bg-white">
            {/* Header */}
            <div className="flex justify-between items-center border-b-2 border-gray-900 pb-3 mb-3">
              <div>
                <h1 className="text-lg font-black text-gray-900 tracking-wide uppercase">
                  Sunrise Public School
                </h1>
                <p className="text-[10px] text-gray-600">
                  Staff Faculty Room & Front Desk Liaison
                </p>
                <div className="mt-1 inline-block bg-emerald-900 text-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-xs">
                  Teacher Appointment / Parent-Teacher Interaction Slip
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-gray-500 block uppercase">Slip No</span>
                <span className="text-base font-black font-mono text-emerald-900">{meeting.slip_code}</span>
                <div className="text-[10px] text-gray-600 font-medium">
                  Date: <span className="font-semibold text-gray-900">{formattedDate}</span>
                </div>
                <div className="text-[10px] text-gray-600 font-medium">
                  Time: <span className="font-semibold text-gray-900">{meeting.meeting_time}</span>
                </div>
              </div>
            </div>

            {/* Teacher & Visitor Particulars */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              {/* Teacher Details */}
              <div className="border border-gray-300 rounded p-2.5 bg-gray-50/50">
                <span className="text-[10px] font-bold text-gray-700 uppercase tracking-wider block border-b border-gray-200 pb-1 mb-1.5">
                  1. Faculty Member Requested
                </span>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Teacher Name:</span>
                    <span className="font-bold text-gray-900">{meeting.teacher_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status:</span>
                    <span
                      className={`px-2 py-0.2 rounded text-[10px] font-bold uppercase ${
                        meeting.status === "accepted"
                          ? "bg-emerald-100 text-emerald-800"
                          : meeting.status === "declined"
                          ? "bg-red-100 text-red-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {meeting.status}
                    </span>
                  </div>
                  {meeting.response_notes && (
                    <div>
                      <span className="text-gray-500 block text-[10px]">Teacher Notes:</span>
                      <span className="font-medium text-gray-800 italic">{meeting.response_notes}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Visitor Details */}
              <div className="border border-gray-300 rounded p-2.5 bg-gray-50/50">
                <span className="text-[10px] font-bold text-gray-700 uppercase tracking-wider block border-b border-gray-200 pb-1 mb-1.5">
                  2. Visitor Particulars
                </span>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Visitor Name:</span>
                    <span className="font-bold text-gray-900">{meeting.visitor_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Relationship:</span>
                    <span className="font-semibold text-gray-900">{meeting.visitor_relation || "Parent / Guardian"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Phone Number:</span>
                    <span className="font-mono font-semibold text-gray-900">{meeting.visitor_phone}</span>
                  </div>
                  {meeting.student_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Student:</span>
                      <span className="font-semibold text-gray-900">
                        {meeting.student_name} {meeting.student_admission_no ? `(${meeting.student_admission_no})` : ""}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Reason */}
            <div className="border border-gray-300 rounded p-2.5 mb-4 text-[11px]">
              <span className="text-gray-500 font-medium block text-[10px] uppercase">Agenda / Topic:</span>
              <p className="font-semibold text-gray-900 mt-0.5">{meeting.reason}</p>
            </div>

            {/* Signatures */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-gray-300 text-center text-[10px]">
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  {meeting.created_by_name}
                </div>
                <div className="text-gray-500">Front Desk Officer</div>
              </div>
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  Visitor Signature
                </div>
                <div className="text-gray-500">Parent / Guest</div>
              </div>
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  {meeting.teacher_name}
                </div>
                <div className="text-gray-500">Teacher Signature</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
