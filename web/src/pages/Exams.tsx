import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { errorText } from "../api/errors";
import { Card, DataTable, FormField, Modal, Pill, inputClass } from "../components/ui";
import { useClasses } from "./useClasses";

type Exam = { id: number; name: string; term: string; start_date: string; end_date: string };

export function Exams() {
  const qc = useQueryClient();
  const [openExam, setOpenExam] = useState<Exam | null>(null);
  const [creating, setCreating] = useState(false);

  const exams = useQuery({ queryKey: ["exams"], queryFn: () => api.get("/admin/exams") });

  return (
    <>
      <Card
        title="Exams"
        action={
          <button
            onClick={() => setCreating(true)}
            className="rounded-input bg-primary px-3 py-1.5 text-sm text-white hover:bg-primary-dark"
          >
            Create Exam
          </button>
        }
      >
        <DataTable
          rows={exams.data ?? []}
          loading={exams.isLoading}
          onRowClick={setOpenExam}
          empty="No exams created yet."
          columns={[
            { key: "name", header: "Exam", render: (e) => e.name },
            { key: "term", header: "Term", render: (e) => e.term },
            { key: "from", header: "Starts", render: (e) => e.start_date },
            { key: "to", header: "Ends", render: (e) => e.end_date },
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
  );
}

function CreateExam({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: "", term: "Term 1", start_date: "", end_date: "" });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });
  const save = useMutation({
    mutationFn: () => api.post("/admin/exams", form),
    onSuccess: onSaved,
  });

  return (
    <Modal title="Create Exam" onClose={onClose}>
      <div className="space-y-3">
        <FormField label="Name">
          <input className={inputClass} value={form.name} onChange={set("name")} />
        </FormField>
        <FormField label="Term">
          <input className={inputClass} value={form.term} onChange={set("term")} />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Starts">
            <input type="date" className={inputClass} value={form.start_date} onChange={set("start_date")} />
          </FormField>
          <FormField label="Ends">
            <input type="date" className={inputClass} value={form.end_date} onChange={set("end_date")} />
          </FormField>
        </div>
        {save.isError && <p className="text-sm text-danger">{errorText(save.error)}</p>}
        <button
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="w-full rounded-input bg-primary py-2 text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60"
        >
          Create
        </button>
      </div>
    </Modal>
  );
}

function ExamDetail({ exam, onClose }: { exam: Exam; onClose: () => void }) {
  const qc = useQueryClient();
  const classes = useClasses();
  const subjects = useQuery({
    queryKey: ["subjects"],
    // /admin/subjects has no response_model; only id and name are read here.
    queryFn: () => api.get("/admin/subjects") as Promise<{ id: number; name: string }[]>,
  });
  const papers = useQuery({
    queryKey: ["exam-schedule", exam.id],
    queryFn: () =>
      api.get(`/admin/exams/${exam.id}/schedule` as "/admin/exams/{exam_id}/schedule"),
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["exam-schedule", exam.id] }),
  });

  return (
    <Modal title={exam.name} onClose={onClose}>
      <DataTable
        rows={papers.data ?? []}
          loading={papers.isLoading}
        empty="No papers scheduled for this exam yet."
        columns={[
          { key: "class", header: "Class", render: (p) => p.class_label },
          { key: "sub", header: "Subject", render: (p) => p.subject },
          { key: "date", header: "Date", render: (p) => p.exam_date },
          { key: "max", header: "Max", render: (p) => p.max_marks, align: "right" },
          {
            key: "marks",
            header: "Marks",
            render: (p) =>
              p.marks_entered ? <Pill status="paid">Entered</Pill> : <Pill status="pending">Pending</Pill>,
          },
        ]}
      />

      <h3 className="text-sm font-medium mt-6 mb-2">Add a subject paper</h3>
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Class">
          <select className={inputClass} value={form.class_section_id} onChange={set("class_section_id")}>
            <option value="">Select</option>
            {classes.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.class_label}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Subject">
          <select className={inputClass} value={form.subject_id} onChange={set("subject_id")}>
            <option value="">Select</option>
            {subjects.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Date">
          <input type="date" className={inputClass} value={form.exam_date} onChange={set("exam_date")} />
        </FormField>
        <FormField label="Max marks">
          <input className={inputClass} value={form.max_marks} onChange={set("max_marks")} />
        </FormField>
      </div>
      {add.isError && <p className="text-sm text-danger mt-2">{errorText(add.error)}</p>}
      <button
        onClick={() => add.mutate()}
        disabled={add.isPending}
        className="mt-3 w-full rounded-input bg-primary py-2 text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60"
      >
        Add paper
      </button>
    </Modal>
  );
}
