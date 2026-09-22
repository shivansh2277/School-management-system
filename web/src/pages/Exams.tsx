import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { errorText } from "../api/errors";
import { ActionButton } from "../components/Can";
import { Card, DataTable, FormField, Modal, Pill, inputClass } from "../components/ui";
import { MarksEntryModal, type PaperSchedule } from "./exams/MarksEntryModal";
import { ReportCardsTab } from "./exams/ReportCardsTab";
import { SchemesAndGrading } from "./exams/SchemesAndGrading";
import { useClasses } from "./useClasses";

const WRITE = "exam.definition.write";

type Exam = {
  id: number;
  name: string;
  term: string;
  start_date: string;
  end_date: string;
  scheme_component_id?: number | null;
};

export function Exams() {
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<"exams" | "schemes" | "report_cards">("exams");
  const [openExam, setOpenExam] = useState<Exam | null>(null);
  const [creating, setCreating] = useState(false);

  const exams = useQuery({ queryKey: ["exams"], queryFn: () => api.get("/admin/exams") });

  return (
    <div className="space-y-4">
      {/* Top Tab Strip */}
      <div className="flex border-b border-rule gap-2 text-sm font-medium">
        <button
          type="button"
          onClick={() => setActiveTab("exams")}
          className={`pb-2.5 px-3 border-b-2 transition-colors ${
            activeTab === "exams"
              ? "border-primary text-primary font-bold"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          📅 Exams & Datesheets
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("schemes")}
          className={`pb-2.5 px-3 border-b-2 transition-colors ${
            activeTab === "schemes"
              ? "border-primary text-primary font-bold"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          ⚖️ CBSE Schemes & Grading Scales
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("report_cards")}
          className={`pb-2.5 px-3 border-b-2 transition-colors ${
            activeTab === "report_cards"
              ? "border-primary text-primary font-bold"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          🎓 Report Cards & Publications
        </button>
      </div>

      {/* Tab 1: Exams & Schedules */}
      {activeTab === "exams" && (
        <>
          <Card
            title="Exams & Paper Schedules"
            action={
              <ActionButton
                permission={WRITE}
                onClick={() => setCreating(true)}
                className="!px-3 !py-1.5"
              >
                Create Exam
              </ActionButton>
            }
          >
            <DataTable
              rows={exams.data ?? []}
              loading={exams.isLoading}
              error={exams.error}
              onRowClick={setOpenExam}
              empty="No exams created yet."
              columns={[
                { key: "name", header: "Exam Name", render: (e) => <span className="font-semibold">{e.name}</span> },
                { key: "term", header: "Term", render: (e) => <Pill status="neutral">{e.term}</Pill> },
                { key: "from", header: "Starts", render: (e) => e.start_date },
                { key: "to", header: "Ends", render: (e) => e.end_date },
                {
                  key: "action",
                  header: "",
                  align: "right",
                  render: (e) => (
                    <button
                      type="button"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setOpenExam(e);
                      }}
                      className="px-2.5 py-1 text-xs text-primary border border-primary/30 rounded-input hover:bg-primary/5 font-semibold"
                    >
                      Datesheet & Marks →
                    </button>
                  ),
                },
              ]}
            />
          </Card>

          {creating && (
            <CreateExam
              onClose={() => setCreating(false)}
              onSaved={() => {
                setCreating(false);
                qc.invalidateQueries({ queryKey: ["exams"] });
              }}
            />
          )}

          {openExam && <ExamDetail exam={openExam} onClose={() => setOpenExam(null)} />}
        </>
      )}

      {/* Tab 2: CBSE Schemes & Grading */}
      {activeTab === "schemes" && <SchemesAndGrading />}

      {/* Tab 3: Report Cards & Publications */}
      {activeTab === "report_cards" && <ReportCardsTab />}
    </div>
  );
}

function CreateExam({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    name: "",
    term: "Term 1",
    start_date: "",
    end_date: "",
    scheme_component_id: "",
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  // Query assessment schemes to optionally link component
  const schemes = useQuery({
    queryKey: ["assessment-schemes"],
    queryFn: () => api.get("/admin/assessment-schemes" as "/admin/assessment-schemes") as Promise<any[]>,
  });
  const activeScheme = schemes.data?.find((s) => s.is_active);

  const save = useMutation({
    mutationFn: () =>
      api.post("/admin/exams", {
        name: form.name,
        term: form.term,
        start_date: form.start_date,
        end_date: form.end_date,
        scheme_component_id: form.scheme_component_id ? Number(form.scheme_component_id) : null,
      }),
    onSuccess: onSaved,
  });

  return (
    <Modal title="Create Exam" onClose={onClose}>
      <div className="space-y-3">
        <FormField label="Name">
          <input
            className={inputClass}
            placeholder="e.g. Term 1 - Term Examination"
            value={form.name}
            onChange={set("name")}
          />
        </FormField>
        <FormField label="Term">
          <select className={inputClass} value={form.term} onChange={set("term")}>
            <option value="Term 1">Term 1</option>
            <option value="Term 2">Term 2</option>
          </select>
        </FormField>

        {activeScheme && (
          <FormField label="Link to Scheme Component (Optional)">
            <select className={inputClass} value={form.scheme_component_id} onChange={set("scheme_component_id")}>
              <option value="">None (Independent Class Test)</option>
              {activeScheme.components.map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.term}: {c.code} - {c.name} ({c.max_marks}M)
                </option>
              ))}
            </select>
          </FormField>
        )}

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Starts">
            <input type="date" className={inputClass} value={form.start_date} onChange={set("start_date")} />
          </FormField>
          <FormField label="Ends">
            <input type="date" className={inputClass} value={form.end_date} onChange={set("end_date")} />
          </FormField>
        </div>
        {save.isError && <p className="text-sm text-danger">{errorText(save.error)}</p>}
        <ActionButton
          permission={WRITE}
          onClick={() => save.mutate()}
          disabled={save.isPending || !form.name || !form.start_date || !form.end_date}
          className="w-full"
        >
          Create Exam
        </ActionButton>
      </div>
    </Modal>
  );
}

function ExamDetail({ exam, onClose }: { exam: Exam; onClose: () => void }) {
  const qc = useQueryClient();
  const classes = useClasses();
  const [editingPaper, setEditingPaper] = useState<PaperSchedule | null>(null);

  const subjects = useQuery({
    queryKey: ["subjects"],
    queryFn: () => api.get("/admin/subjects") as Promise<{ id: number; name: string }[]>,
  });
  const papers = useQuery({
    queryKey: ["exam-schedule", exam.id],
    queryFn: () =>
      api.get(`/admin/exams/${exam.id}/schedule` as "/admin/exams/{exam_id}/schedule") as Promise<PaperSchedule[]>,
  });

  const [form, setForm] = useState({
    class_section_id: "",
    subject_id: "",
    exam_date: "",
    max_marks: "100",
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  const add = useMutation({
    mutationFn: () =>
      api.post(`/admin/exams/${exam.id}/schedule` as "/admin/exams/{exam_id}/schedule", {
        class_section_id: Number(form.class_section_id),
        subject_id: Number(form.subject_id),
        exam_date: form.exam_date,
        max_marks: form.max_marks,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["exam-schedule", exam.id] });
      setForm({ class_section_id: "", subject_id: "", exam_date: "", max_marks: "100" });
    },
  });

  return (
    <>
      <Modal title={`Datesheet & Papers: ${exam.name}`} onClose={onClose} wide>
      <div className="space-y-6">
          <DataTable<PaperSchedule>
            rows={papers.data ?? []}
            loading={papers.isLoading}
            error={papers.error}
            empty="No papers scheduled for this exam yet."
            columns={[
              { key: "class", header: "Class", render: (p) => <span className="font-semibold text-ink">{p.class_label}</span> },
              { key: "sub", header: "Subject", render: (p) => p.subject },
              { key: "date", header: "Date", render: (p) => p.exam_date },
              { key: "max", header: "Max", render: (p) => p.max_marks, align: "right" },
              {
                key: "marks",
                header: "Status",
                render: (p) => (
                  <div className="flex items-center gap-1.5">
                    {p.marks_locked ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-pill bg-amber-100 text-amber-800 text-xs font-semibold">
                        🔒 Locked
                      </span>
                    ) : p.marks_entered ? (
                      <Pill status="paid">Entered</Pill>
                    ) : (
                      <Pill status="pending">Pending</Pill>
                    )}
                  </div>
                ),
              },
              {
                key: "actions",
                header: "",
                align: "right",
                render: (p) => (
                  <button
                    type="button"
                    onClick={() => setEditingPaper(p)}
                    className="px-2.5 py-1 text-xs font-semibold text-white bg-primary hover:bg-primary-dark rounded-input shadow-sm"
                  >
                    {p.marks_locked ? "🔒 Overrides" : "Marks Entry →"}
                  </button>
                ),
              },
            ]}
          />

          <div className="border-t border-rule pt-4">
            <h3 className="text-sm font-semibold mb-2">Schedule a new subject paper</h3>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Class Section">
                <select className={inputClass} value={form.class_section_id} onChange={set("class_section_id")}>
                  <option value="">Select class</option>
                  {classes.data?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.class_label}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Subject">
                <select className={inputClass} value={form.subject_id} onChange={set("subject_id")}>
                  <option value="">Select subject</option>
                  {subjects.data?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Exam Date">
                <input type="date" className={inputClass} value={form.exam_date} onChange={set("exam_date")} />
              </FormField>
              <FormField label="Max marks">
                <input className={inputClass} value={form.max_marks} onChange={set("max_marks")} />
              </FormField>
            </div>
            {add.isError && <p className="text-sm text-danger mt-2">{errorText(add.error)}</p>}
            <ActionButton
              permission={WRITE}
              onClick={() => add.mutate()}
              disabled={add.isPending || !form.class_section_id || !form.subject_id || !form.exam_date}
              className="mt-3 w-full"
            >
              Add Paper to Datesheet
            </ActionButton>
          </div>
        </div>
      </Modal>

      {/* Marks Entry Grid Modal */}
      {editingPaper && (
        <MarksEntryModal
          paper={editingPaper}
          onClose={() => {
            setEditingPaper(null);
            qc.invalidateQueries({ queryKey: ["exam-schedule", exam.id] });
          }}
        />
      )}
    </>
  );
}
