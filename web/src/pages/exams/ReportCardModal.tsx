import { Modal, Pill } from "../../components/ui";

export type ReportCardPayload = {
  term: string;
  student_id: number;
  student_name: string;
  admission_no: string;
  roll_no: number;
  class_label: string;
  scheme: string;
  grading_scale: string;
  attendance_percent?: number | null;
  rows: {
    subject: string;
    components: {
      code: string;
      name: string;
      max_marks: string;
      marks_obtained: string | null;
      is_absent: boolean;
      is_exempted: boolean;
    }[];
    marks_obtained: string;
    max_marks: string;
    percent: number | null;
    grade: string | null;
  }[];
  total_obtained: string;
  total_max: string;
  overall_percent: number | null;
  overall_grade: string | null;
  published?: boolean;
  document_no?: string;
  result_status?: "pass" | "fail" | "withheld" | string;
  withheld_reason?: string;
};

export function ReportCardModal({
  card,
  onClose,
}: {
  card: ReportCardPayload;
  onClose: () => void;
}) {
  const componentHeaders =
    card.rows.length > 0
      ? card.rows[0].components.map((c) => ({ code: c.code, name: c.name, max: c.max_marks }))
      : [];

  const handlePrint = () => {
    window.print();
  };

  const isWithheld = card.result_status === "withheld";

  return (
    <Modal title={`Report Card: ${card.student_name}`} onClose={onClose} wide>
      <div className="space-y-5 print:p-0">
        {/* Withholding Alert Banner */}
        {isWithheld && (
          <div className="bg-red-50 border border-red-200 rounded-card p-4 text-danger flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div className="space-y-1 text-sm">
              <p className="font-bold">OFFICIAL RESULT STATUS: WITHHELD</p>
              <p className="text-xs">
                {card.withheld_reason || "Report card is withheld under school policy due to outstanding fee dues (§0.6b). Results cannot be released until dues are cleared at the counter."}
              </p>
            </div>
          </div>
        )}

        {/* Official School Report Card Header */}
        <div className="border border-rule rounded-card p-5 bg-ground text-center space-y-2">
          <div className="flex items-center justify-between border-b border-rule pb-3">
            <div className="text-left">
              <p className="font-bold text-lg text-ink">Sunrise Public School</p>
              <p className="text-xs text-ink-faint">Affiliated to CBSE, New Delhi • Senior Secondary</p>
            </div>
            <div className="text-right text-xs">
              {card.document_no ? (
                <div className="space-y-0.5">
                  <p className="font-mono font-bold text-primary">{card.document_no}</p>
                  <Pill status="paid">ISSUED & FROZEN</Pill>
                </div>
              ) : (
                <Pill status="pending">LIVE PREVIEW</Pill>
              )}
            </div>
          </div>

          <div className="py-1">
            <h2 className="text-base font-bold tracking-wide uppercase text-ink">
              Continuous & Comprehensive Evaluation ({card.term})
            </h2>
            <p className="text-xs text-ink-soft">
              Assessment Scheme: <span className="font-semibold text-ink">{card.scheme}</span> • Scale:{" "}
              <span className="font-semibold text-ink">{card.grading_scale}</span>
            </p>
          </div>

          {/* Student Biodata Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-rule text-xs text-left">
            <div>
              <span className="text-ink-faint">Student Name:</span>
              <p className="font-bold text-ink">{card.student_name}</p>
            </div>
            <div>
              <span className="text-ink-faint">Class & Section:</span>
              <p className="font-bold text-ink">{card.class_label}</p>
            </div>
            <div>
              <span className="text-ink-faint">Admission No:</span>
              <p className="font-bold text-ink tabular">{card.admission_no}</p>
            </div>
            <div>
              <span className="text-ink-faint">Attendance:</span>
              <p className="font-bold text-ink tabular">
                {card.attendance_percent !== null && card.attendance_percent !== undefined
                  ? `${card.attendance_percent}%`
                  : "N/A"}
              </p>
            </div>
          </div>
        </div>

        {/* Marks Table */}
        <div className="border border-rule rounded-card overflow-hidden">
          <table className="w-full text-xs sm:text-sm text-left">
            <thead className="bg-ground text-ink-faint border-b border-rule">
              <tr>
                <th className="py-2.5 px-3">Subject</th>
                {componentHeaders.map((h) => (
                  <th key={h.code} className="py-2.5 px-2 text-center">
                    {h.code} <span className="text-[10px] text-ink-faint font-normal">({h.max})</span>
                  </th>
                ))}
                <th className="py-2.5 px-3 text-right">Total</th>
                <th className="py-2.5 px-3 text-right">Max</th>
                <th className="py-2.5 px-3 text-right">%</th>
                <th className="py-2.5 px-3 text-center">Grade</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {card.rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-ground/40">
                  <td className="py-2.5 px-3 font-semibold text-ink">{row.subject}</td>
                  {row.components.map((c, cIdx) => (
                    <td key={cIdx} className="py-2.5 px-2 text-center tabular text-ink-soft">
                      {c.is_absent ? (
                        <span className="text-danger font-semibold">AB</span>
                      ) : c.is_exempted ? (
                        <span className="text-amber-600 font-semibold">EX</span>
                      ) : c.marks_obtained !== null ? (
                        c.marks_obtained
                      ) : (
                        "-"
                      )}
                    </td>
                  ))}
                  <td className="py-2.5 px-3 text-right font-bold tabular text-ink">
                    {row.marks_obtained}
                  </td>
                  <td className="py-2.5 px-3 text-right tabular text-ink-faint">
                    {row.max_marks}
                  </td>
                  <td className="py-2.5 px-3 text-right tabular font-medium text-ink">
                    {row.percent !== null ? `${row.percent}%` : "-"}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    {row.grade ? (
                      <span className="inline-block font-bold text-xs px-2 py-0.5 rounded bg-primary-soft text-primary">
                        {row.grade}
                      </span>
                    ) : (
                      "-"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
            {/* Grand Total Row */}
            <tfoot className="bg-ground font-bold border-t-2 border-rule text-ink">
              <tr>
                <td className="py-3 px-3 uppercase">Grand Total</td>
                {componentHeaders.map((_, i) => (
                  <td key={i} className="py-3 px-2 text-center text-ink-faint">
                    •
                  </td>
                ))}
                <td className="py-3 px-3 text-right tabular text-primary font-bold">
                  {card.total_obtained}
                </td>
                <td className="py-3 px-3 text-right tabular text-ink-soft">
                  {card.total_max}
                </td>
                <td className="py-3 px-3 text-right tabular text-primary font-bold">
                  {card.overall_percent !== null ? `${card.overall_percent}%` : "-"}
                </td>
                <td className="py-3 px-3 text-center">
                  {card.overall_grade && (
                    <span className="inline-block font-extrabold text-sm px-2.5 py-0.5 rounded bg-primary text-white">
                      {card.overall_grade}
                    </span>
                  )}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Footer Remarks and Signoff */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-4 border-t border-rule text-xs text-center text-ink-faint">
          <div>
            <div className="h-10 border-b border-rule border-dashed mb-1" />
            <p>Class Teacher</p>
          </div>
          <div>
            <div className="h-10 border-b border-rule border-dashed mb-1" />
            <p>Exam Controller</p>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <div className="h-10 border-b border-rule border-dashed mb-1" />
            <p>Principal</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-rule print:hidden">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-ink-soft hover:text-ink font-medium"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handlePrint}
            className="rounded-input px-4 py-2 bg-surface text-primary border border-primary hover:bg-primary/10 text-sm font-medium"
          >
            🖨️ Print / Save PDF
          </button>
        </div>
      </div>
    </Modal>
  );
}
