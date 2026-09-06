import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, FormField, Modal, inputClass } from "../components/ui";
import { useClasses } from "./useClasses";

type Row = {
  id: number;
  full_name: string;
  admission_no: string;
  class_label: string;
  roll_no: number;
  guardian_name: string | null;
  guardian_phone: string | null;
};

type Detail = Row & {
  dob: string | null;
  gender: string | null;
  address: string | null;
  attendance_percent: number | null;
  latest_result_percent: number | null;
  homework_pending: number;
};

export function Students() {
  const qc = useQueryClient();
  const classes = useClasses();
  const [q, setQ] = useState("");
  const [classId, setClassId] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  const params = new URLSearchParams({ page_size: "100" });
  if (q) params.set("q", q);
  if (classId) params.set("class_section_id", classId);

  const { data, isLoading } = useQuery({
    queryKey: ["students", q, classId],
    queryFn: () => api.get<{ items: Row[]; total: number }>(`/admin/students?${params}`),
  });

  const detail = useQuery({
    queryKey: ["student", openId],
    queryFn: () => api.get<Detail>(`/admin/students/${openId}`),
    enabled: openId !== null,
  });

  return (
    <>
      <Card
        title={`Students${data ? ` (${data.total})` : ""}`}
        action={
          <button
            onClick={() => setAdding(true)}
            className="rounded-input bg-primary px-3 py-1.5 text-sm text-white hover:bg-primary-dark"
          >
            Add Student
          </button>
        }
      >
        <div className="flex gap-3 mb-4">
          <input
            className={inputClass}
            placeholder="Search by name or admission number"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select className={inputClass} value={classId} onChange={(e) => setClassId(e.target.value)}>
            <option value="">All classes</option>
            {classes.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.class_label}
              </option>
            ))}
          </select>
        </div>

        <DataTable<Row>
          rows={data?.items ?? []}
          loading={isLoading}
          onRowClick={(r) => setOpenId(r.id)}
          empty="No students match this filter."
          columns={[
            {
              key: "name",
              header: "Name",
              render: (r) => (
                <span className="flex items-center gap-2">
                  <span className="w-7 h-7 rounded-full bg-primary-soft text-primary grid place-items-center text-xs font-medium">
                    {r.full_name.slice(0, 1)}
                  </span>
                  {r.full_name}
                </span>
              ),
            },
            { key: "adm", header: "Admission No.", render: (r) => r.admission_no },
            { key: "class", header: "Class", render: (r) => r.class_label },
            { key: "roll", header: "Roll", render: (r) => r.roll_no, align: "right" },
            { key: "guardian", header: "Guardian", render: (r) => r.guardian_name ?? "-" },
            { key: "phone", header: "Phone", render: (r) => r.guardian_phone ?? "-" },
          ]}
        />
      </Card>

      {openId !== null && (
        <Modal title="Student" onClose={() => setOpenId(null)}>
          {detail.data ? (
            <dl className="grid grid-cols-2 gap-3 text-sm">
              {[
                ["Name", detail.data.full_name],
                ["Admission No.", detail.data.admission_no],
                ["Class", detail.data.class_label],
                ["Roll No.", detail.data.roll_no],
                ["Date of birth", detail.data.dob ?? "-"],
                ["Gender", detail.data.gender ?? "-"],
                ["Address", detail.data.address ?? "-"],
                ["Guardian", detail.data.guardian_name ?? "-"],
                [
                  "Attendance",
                  detail.data.attendance_percent === null
                    ? "Not marked yet"
                    : `${detail.data.attendance_percent}%`,
                ],
                [
                  "Latest result",
                  detail.data.latest_result_percent === null
                    ? "No results yet"
                    : `${detail.data.latest_result_percent}%`,
                ],
                ["Homework pending", detail.data.homework_pending],
              ].map(([k, v]) => (
                <div key={String(k)}>
                  <dt className="text-ink-faint text-xs">{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-ink-faint text-sm">Loading...</p>
          )}
        </Modal>
      )}

      {adding && (
        <AddStudent
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            qc.invalidateQueries({ queryKey: ["students"] });
          }}
        />
      )}
    </>
  );
}

function AddStudent({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const classes = useClasses();
  const [form, setForm] = useState({
    full_name: "",
    admission_no: "",
    class_section_id: "",
    roll_no: "",
    guardian_name: "",
    guardian_phone: "",
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  const save = useMutation({
    mutationFn: () =>
      // One transaction creates the student login and the guardian login together.
      api.post("/admin/students", {
        full_name: form.full_name,
        admission_no: form.admission_no,
        class_section_id: Number(form.class_section_id),
        roll_no: Number(form.roll_no),
        guardian: form.guardian_phone
          ? { full_name: form.guardian_name, phone: form.guardian_phone, relation: "father" }
          : null,
      }),
    onSuccess: onSaved,
  });

  return (
    <Modal title="Add Student" onClose={onClose}>
      <div className="space-y-3">
        <FormField label="Full name">
          <input className={inputClass} value={form.full_name} onChange={set("full_name")} />
        </FormField>
        <FormField label="Admission number">
          <input className={inputClass} value={form.admission_no} onChange={set("admission_no")} />
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Class">
            <select
              className={inputClass}
              value={form.class_section_id}
              onChange={set("class_section_id")}
            >
              <option value="">Select</option>
              {classes.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.class_label}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Roll number">
            <input className={inputClass} value={form.roll_no} onChange={set("roll_no")} />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Guardian name">
            <input className={inputClass} value={form.guardian_name} onChange={set("guardian_name")} />
          </FormField>
          <FormField label="Guardian mobile (their login)">
            <input className={inputClass} value={form.guardian_phone} onChange={set("guardian_phone")} />
          </FormField>
        </div>

        {save.isError && (
          <p className="text-sm text-danger">{(save.error as Error).message}</p>
        )}
        <p className="text-xs text-ink-faint">
          The student signs in with their admission number, the guardian with their mobile number.
          Default passwords are Student@123 and Parent@123.
        </p>

        <button
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="w-full rounded-input bg-primary py-2 text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60"
        >
          {save.isPending ? "Saving..." : "Create student"}
        </button>
      </div>
    </Modal>
  );
}
