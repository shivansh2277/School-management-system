import React, { useRef } from "react";

export interface FeeReceiptData {
  payment_id: number;
  receipt_no: string;
  amount: string;
  method: string;
  received_at: string;
  months_paid: number;
  student_name: string;
  admission_no: string;
  class_label: string;
  invoices_cleared: string[];
}

export function PrintableFeeReceiptSlip({
  receipt,
  onClose,
}: {
  receipt: FeeReceiptData;
  onClose: () => void;
}) {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    window.print();
  };

  const formattedDate = new Date(receipt.received_at).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white text-black w-full max-w-xl rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[95vh]">
        {/* Top bar (hidden in print) */}
        <div className="flex items-center justify-between px-6 py-3 bg-gray-100 border-b border-gray-300 print:hidden">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-800 text-sm">
              Fee Collection Receipt
            </span>
            <span className="text-xs bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded font-mono font-bold">
              {receipt.receipt_no}
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
              Print Receipt
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
        <div ref={printRef} className="p-6 overflow-y-auto print:p-0 print:m-0 text-xs font-sans">
          <style>{`
            @media print {
              body * { visibility: hidden; }
              #printable-fee-receipt, #printable-fee-receipt * { visibility: visible; }
              #printable-fee-receipt { position: absolute; left: 0; top: 0; width: 100%; }
              @page { size: A5 portrait; margin: 10mm; }
            }
          `}</style>

          <div id="printable-fee-receipt" className="border-2 border-gray-900 p-5 rounded bg-white">
            {/* Header */}
            <div className="text-center border-b-2 border-gray-900 pb-3 mb-3">
              <h1 className="text-lg font-black text-gray-900 tracking-wide uppercase">
                Sunrise Public School
              </h1>
              <p className="text-[10px] text-gray-600">
                Sector 14, Vikas Nagar, Lucknow, UP — Tel: +91 522 400 1234
              </p>
              <div className="mt-1 inline-block bg-emerald-900 text-white px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-xs">
                Official Fee Counter Payment Receipt
              </div>
            </div>

            {/* Receipt Meta */}
            <div className="grid grid-cols-2 gap-2 bg-gray-50 border border-gray-200 p-2.5 rounded mb-3 text-[11px]">
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Receipt No:</span>
                <span className="font-mono font-black text-gray-900">{receipt.receipt_no}</span>
              </div>
              <div className="text-right">
                <span className="text-gray-500 block text-[9px] uppercase">Date & Time:</span>
                <span className="font-semibold text-gray-900">{formattedDate}</span>
              </div>
            </div>

            {/* Student Particulars */}
            <div className="border border-gray-200 rounded p-3 mb-3 text-[11px] space-y-1.5">
              <div className="flex justify-between">
                <span className="text-gray-500">Student Name:</span>
                <span className="font-bold text-gray-900">{receipt.student_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Admission No:</span>
                <span className="font-mono font-semibold text-gray-900">{receipt.admission_no}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Class & Section:</span>
                <span className="font-semibold text-gray-900">{receipt.class_label}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Payment Mode:</span>
                <span className="font-bold text-gray-900 uppercase">{receipt.method}</span>
              </div>
            </div>

            {/* Fee Cleared Particulars */}
            <div className="border border-gray-200 rounded p-3 mb-4 text-[11px]">
              <div className="flex justify-between border-b border-gray-100 pb-1 mb-1.5 font-semibold">
                <span>Complete Months Paid:</span>
                <span className="font-bold text-emerald-800">{receipt.months_paid} Month(s)</span>
              </div>
              <div className="text-[10px] text-gray-600 mb-2">
                Invoices Settled: {receipt.invoices_cleared.join(", ")}
              </div>
              <div className="flex justify-between items-center bg-emerald-50 border border-emerald-200 p-2 rounded">
                <span className="font-bold text-emerald-950 text-xs uppercase">Total Amount Received:</span>
                <span className="text-base font-black font-mono text-emerald-900">
                  ₹{parseFloat(receipt.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Signatures */}
            <div className="grid grid-cols-2 gap-6 pt-6 border-t border-gray-300 text-center text-[10px]">
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  Cashier / Receptionist
                </div>
                <div className="text-gray-500">Fee Counter Collection Desk</div>
              </div>
              <div>
                <div className="border-t border-dashed border-gray-400 pt-1 font-semibold text-gray-900">
                  Official School Seal
                </div>
                <div className="text-gray-500">Sunrise Public School</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
