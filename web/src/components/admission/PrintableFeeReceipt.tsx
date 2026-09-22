import React, { useRef } from "react";
import { ApplicationPayment, ApplicationRow, ApplicationDetail } from "../../pages/admission/types";

function numberToWordsINR(amountNum: number): string {
  if (isNaN(amountNum) || amountNum === 0) return "Zero Rupees Only";

  const a = [
    "", "One ", "Two ", "Three ", "Four ", "Five ", "Six ", "Seven ", "Eight ", "Nine ",
    "Ten ", "Eleven ", "Twelve ", "Thirteen ", "Fourteen ", "Fifteen ", "Sixteen ",
    "Seventeen ", "Eighteen ", "Nineteen ",
  ];
  const b = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];

  function inWords(num: number): string {
    if (num === 0) return "";
    let str = "";
    if (Math.floor(num / 10000000) > 0) {
      str += inWords(Math.floor(num / 10000000)) + "Crore ";
      num %= 10000000;
    }
    if (Math.floor(num / 100000) > 0) {
      str += inWords(Math.floor(num / 100000)) + "Lakh ";
      num %= 100000;
    }
    if (Math.floor(num / 1000) > 0) {
      str += inWords(Math.floor(num / 1000)) + "Thousand ";
      num %= 1000;
    }
    if (Math.floor(num / 100) > 0) {
      str += inWords(Math.floor(num / 100)) + "Hundred ";
      num %= 100;
    }
    if (num > 0) {
      if (num < 20) {
        str += a[num];
      } else {
        str += b[Math.floor(num / 10)] + (num % 10 !== 0 ? " " + a[num % 10] : " ");
      }
    }
    return str;
  }

  const wholePart = Math.floor(amountNum);
  const words = inWords(wholePart).trim();
  return words ? `${words} Rupees Only` : "Zero Rupees Only";
}

export function PrintableFeeReceipt({
  payment,
  application,
  studentInfo,
  onClose,
}: {
  payment: ApplicationPayment;
  application: ApplicationRow | ApplicationDetail;
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

  const amountNumber = parseFloat(payment.amount) || 0;
  const words = numberToWordsINR(amountNumber);

  const paidDateFormatted = payment.paid_at
    ? new Date(payment.paid_at).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : new Date().toLocaleDateString("en-IN");

  const candidateName =
    "first_name" in application
      ? `${application.first_name} ${application.middle_name ? application.middle_name + " " : ""}${application.last_name}`
      : application.name;

  const admissionNo =
    studentInfo?.admission_no || (application as any).admission_no || "PROVISIONAL";

  const classAllocated =
    studentInfo?.class_label || (application as any).class_label || `Class ${application.class_applying_for}`;

  const purposeTitle =
    payment.purpose === "admission_fee"
      ? "Final Admission Fee"
      : "Application Processing & Registration Fee";

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white text-black w-full max-w-4xl rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Top Control Bar (Hidden when printing) */}
        <div className="flex items-center justify-between px-6 py-3 bg-gray-100 border-b border-gray-300 print:hidden">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-800 text-sm">
              Official Fee Voucher / Receipt
            </span>
            <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-mono font-medium">
              {payment.receipt_no}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 text-white rounded text-sm font-medium hover:bg-emerald-700 transition shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
                />
              </svg>
              Print Receipt Voucher
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
          className="p-8 overflow-y-auto print:p-0 print:overflow-visible print:m-0 text-[12px] font-sans"
        >
          <style>{`
            @media print {
              body * {
                visibility: hidden;
              }
              #printable-fee-receipt, #printable-fee-receipt * {
                visibility: visible;
              }
              #printable-fee-receipt {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
              }
              @page {
                size: A4 portrait;
                margin: 10mm;
              }
            }
          `}</style>

          <div
            id="printable-fee-receipt"
            className="border-2 border-gray-900 p-6 rounded-sm bg-white shadow-sm"
          >
            {/* Institution Header */}
            <div className="flex justify-between items-center border-b-2 border-gray-900 pb-3 mb-3">
              <div>
                <h1 className="text-xl font-black tracking-wide text-gray-900 uppercase">
                  Sunrise Public School
                </h1>
                <p className="text-[11px] text-gray-700 font-medium">
                  Sector 14, Vikas Nagar, Lucknow, Uttar Pradesh — 226022
                </p>
                <p className="text-[10px] text-gray-500">
                  Affiliation No. 2130001 | School Code: 70142 | Tel: +91 522 400 1234
                </p>
              </div>
              <div className="text-right">
                <span className="inline-block px-3 py-1 bg-emerald-100 text-emerald-900 border border-emerald-300 text-xs font-bold uppercase tracking-wider rounded-sm mb-1">
                  Official Fee Receipt
                </span>
                <p className="font-mono text-xs font-bold text-gray-900">
                  No: {payment.receipt_no}
                </p>
                <p className="text-[10px] text-gray-600">{paidDateFormatted}</p>
              </div>
            </div>

            {/* Metadata Bar */}
            <div className="grid grid-cols-4 gap-2 bg-gray-50 border border-gray-300 p-2 text-[11px] mb-3">
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Application No:</span>
                <span className="font-mono font-bold text-gray-900">{application.application_no}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Admission Number:</span>
                <span className="font-mono font-bold text-blue-900">{admissionNo}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Class & Section:</span>
                <span className="font-bold text-gray-900">{classAllocated}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Payment Mode:</span>
                <span className="font-semibold text-gray-900 uppercase">
                  {payment.method} {payment.reference ? `(${payment.reference})` : ""}
                </span>
              </div>
            </div>

            {/* Student Info */}
            <div className="border border-gray-200 p-2.5 rounded-sm mb-3 bg-white">
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-gray-500">Student Name: </span>
                  <span className="font-bold text-gray-900">{candidateName}</span>
                </div>
                <div>
                  <span className="text-gray-500">Academic Session: </span>
                  <span className="font-semibold text-gray-800">2026–2027</span>
                </div>
              </div>
            </div>

            {/* Fee Table */}
            <table className="w-full border-collapse border border-gray-300 text-[11px] mb-3">
              <thead>
                <tr className="bg-gray-100 text-gray-800 text-left">
                  <th className="border border-gray-300 px-3 py-1.5 w-12 text-center">#</th>
                  <th className="border border-gray-300 px-3 py-1.5">Fee Head / Description</th>
                  <th className="border border-gray-300 px-3 py-1.5 w-32 text-right">Amount (INR)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border border-gray-300 px-3 py-2 text-center text-gray-600">1</td>
                  <td className="border border-gray-300 px-3 py-2">
                    <div className="font-semibold text-gray-900">{purposeTitle}</div>
                    <div className="text-[10px] text-gray-500">
                      Non-refundable registration and institutional enrollment fee
                    </div>
                  </td>
                  <td className="border border-gray-300 px-3 py-2 text-right font-mono font-bold text-gray-900">
                    ₹{parseFloat(payment.amount).toFixed(2)}
                  </td>
                </tr>
                <tr className="bg-gray-50 font-bold">
                  <td colSpan={2} className="border border-gray-300 px-3 py-1.5 text-right uppercase text-[10px]">
                    Total Amount Paid:
                  </td>
                  <td className="border border-gray-300 px-3 py-1.5 text-right font-mono text-sm text-emerald-800">
                    ₹{parseFloat(payment.amount).toFixed(2)}
                  </td>
                </tr>
              </tbody>
            </table>

            {/* Amount in words */}
            <div className="p-2 border border-gray-300 rounded-sm bg-gray-50 text-[11px] mb-4">
              <span className="font-semibold text-gray-700">Amount in Words: </span>
              <span className="font-medium text-gray-900 italic capitalize">{words}</span>
            </div>

            {/* Bottom Signatures & Seal */}
            <div className="flex justify-between items-end pt-4 text-[10px] border-t border-gray-200">
              <div className="text-center">
                <div className="w-36 border-b border-gray-400 mb-1" />
                <span className="text-gray-600">Parent / Depositor Signature</span>
              </div>
              <div className="text-center border border-gray-300 w-32 h-14 flex flex-col items-center justify-center text-[9px] text-gray-400 uppercase rounded-sm">
                <span>Official Seal</span>
                <span className="text-[8px] text-gray-300">Sunrise Public School</span>
              </div>
              <div className="text-center">
                <div className="w-36 border-b border-gray-400 mb-1" />
                <span className="text-gray-600 font-medium">Authorized Cashier / Admission Officer</span>
              </div>
            </div>

            <div className="text-center text-[9px] text-gray-400 mt-4 border-t border-gray-100 pt-2 font-mono">
              System generated acknowledgment voucher • Valid without physical signature if digitally stamped • ERP-REF-{payment.id}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
