import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api, money } from "../api/client";
import { errorText } from "../api/errors";
import { useWrite } from "../api/useWrite";
import { useAuth } from "../auth/AuthContext";
import { ActionButton } from "../components/Can";
import {
  Card,
  DataTable,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../components/ui";
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
  class_section_id: number | null;
  dob: string | null;
  gender: string | null;
  address: string | null;
  attendance_percent: number | null;
  latest_result_percent: number | null;
  homework_pending: number;
};

/** The rows of /admin/fees/defaulters this screen actually reads. */
type Owing = { student_id: number; outstanding: string; months_due: number };

export function Students() {
  const qc = useQueryClient();
  const classes = useClasses();
  const [q, setQ] = useState("");
  const [classId, setClassId] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const [chasing, setChasing] = useState(false);
  const [editing, setEditing] = useState(false);
  const { can, hasModule } = useAuth();

  /**
   * Who owes fees, in one call rather than a ledger lookup per row.
   *
   * `/admin/fees/defaulters` is the same list the chase screen shows, so the
   * two cannot disagree. Gated at the widget, not in the registry: a records
   * clerk holds students.profile.read without fees.invoice.read, and taking
   * the whole roster away from them over one column would cost more than the
   * missing column does.
   */
  const feesVisible = can("fees.invoice.read") && hasModule("fees");
  const owing = useQuery({
    queryKey: ["defaulters"],
    queryFn: () => api.get("/admin/fees/defaulters") as Promise<Owing[]>,
    enabled: feesVisible,
  });
  const owedBy = new Map((owing.data ?? []).map((o) => [o.student_id, o]));

  const params = new URLSearchParams({ page_size: "100" });
  if (q) params.set("q", q);
  if (classId) params.set("class_section_id", classId);

  const { data, isLoading, error } = useQuery({
    queryKey: ["students", q, classId],
    // Page.items is untyped in the schema (a generic pagination envelope), so
    // the real item shape is asserted here rather than re-declared.
    queryFn: () =>
      api.get("/admin/students", `?${params}`) as Promise<{ items: Row[]; total: number }>,
  });

  const detail = useQuery({
    queryKey: ["student", openId],
    // /admin/students/{student_id} has no response_model; Detail documents it.
    queryFn: () =>
      api.get(`/admin/students/${openId}` as "/admin/students/{student_id}") as Promise<Detail>,
    enabled: openId !== null,
  });

  return (
    <>
      <Card
        title={`Students${data ? ` (${data.total})` : ""}`}
        action={
          <div className="flex gap-2">
            {feesVisible && (
              <ActionButton
                permission="comms.message.send"
                onClick={() => setChasing(true)}
                className="!px-3 !py-1.5"
              >
                Email defaulters
              </ActionButton>
            )}
            <ActionButton
              permission="students.profile.write"
              onClick={() => setAdding(true)}
              className="!px-3 !py-1.5"
            >
              Add Student
            </ActionButton>
          </div>
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
          error={error}
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
            // Only where the reader may see fees at all. The column is dropped
            // rather than shown empty: a blank Fees cell reads as "nothing
            // owed", which is a statement about the family's money that this
            // screen would not actually be making.
            ...(feesVisible
              ? [
                  {
                    key: "fees",
                    header: "Fees",
                    render: (r: Row) => {
                      if (owing.isLoading) return <span className="text-ink-faint">…</span>;
                      if (owing.error) return <span className="text-danger text-xs">not loaded</span>;
                      const due = owedBy.get(r.id);
                      return due ? (
                        <Pill status="overdue">
                          {money(due.outstanding)} · {due.months_due}m
                        </Pill>
                      ) : (
                        <Pill status="paid">No dues</Pill>
                      );
                    },
                  },
                ]
              : []),
          ]}
        />
      </Card>

      {openId !== null && (
        <Modal title="Student" onClose={() => { setOpenId(null); setEditing(false); }}>
          {detail.data && editing ? (
            <EditStudent
              student={detail.data}
              onCancel={() => setEditing(false)}
              onSaved={() => {
                setEditing(false);
                qc.invalidateQueries({ queryKey: ["students"] });
                qc.invalidateQueries({ queryKey: ["student", openId] });
              }}
            />
          ) : detail.data ? (
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
              <div className="col-span-2 pt-2">
                <ActionButton
                  permission="students.profile.write"
                  onClick={() => setEditing(true)}
                >
                  Edit details
                </ActionButton>
              </div>
            </dl>
          ) : (
            <p className="text-ink-faint text-sm">Loading...</p>
          )}
        </Modal>
      )}

      {chasing && <ChaseDefaulters count={owing.data?.length} onClose={() => setChasing(false)} />}

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
          <p className="text-sm text-danger">{errorText(save.error)}</p>
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

/**
 * Correcting a student's record.
 *
 * Only the fields the API will actually accept: StudentUpdate is
 * extra="forbid", so posting the whole detail object back - class_label,
 * attendance_percent and all - is a 422. The shape of the read is not the
 * shape of the write.
 *
 * Only what changed is sent. Every field is optional on the API, so an
 * unchanged one is left out rather than written back with the same value: a
 * PATCH that rewrites fields it did not mean to touch fills an audit trail
 * with edits nobody made.
 */
function EditStudent({
  student,
  onCancel,
  onSaved,
}: {
  student: Detail;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const classes = useClasses();
  const [form, setForm] = useState({
    full_name: student.full_name,
    class_section_id: student.class_section_id ? String(student.class_section_id) : "",
    roll_no: student.roll_no != null ? String(student.roll_no) : "",
    dob: student.dob ?? "",
    gender: student.gender ?? "",
    address: student.address ?? "",
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  const save = useWrite({
    write: () => {
      const body: Record<string, unknown> = {};
      if (form.full_name !== student.full_name) body.full_name = form.full_name;
      if (form.class_section_id && Number(form.class_section_id) !== student.class_section_id)
        body.class_section_id = Number(form.class_section_id);
      if (form.roll_no && Number(form.roll_no) !== student.roll_no)
        body.roll_no = Number(form.roll_no);
      if (form.dob !== (student.dob ?? "")) body.dob = form.dob || null;
      if (form.gender !== (student.gender ?? "")) body.gender = form.gender || null;
      if (form.address !== (student.address ?? "")) body.address = form.address || null;
      return api.patch(
        `/admin/students/${student.id}` as "/admin/students/{student_id}",
        body as never,
      );
    },
    invalidates: [["students"], ["student", student.id]],
    onDone: onSaved,
  });

  return (
    <div className="space-y-3">
      <FormField label="Full name" error={save.fields.full_name}>
        <input className={inputClass} value={form.full_name} onChange={set("full_name")} />
      </FormField>
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Class" error={save.fields.class_section_id}>
          <select
            className={inputClass}
            value={form.class_section_id}
            onChange={set("class_section_id")}
          >
            <option value="">Unchanged</option>
            {classes.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.class_label}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Roll number" error={save.fields.roll_no}>
          <input className={inputClass} value={form.roll_no} onChange={set("roll_no")} />
        </FormField>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Date of birth" error={save.fields.dob}>
          {/* Native date input: the platform already has a picker, and it
              submits ISO while showing the viewer their own format. */}
          <input type="date" className={inputClass} value={form.dob} onChange={set("dob")} />
        </FormField>
        <FormField label="Gender" error={save.fields.gender}>
          <select className={inputClass} value={form.gender} onChange={set("gender")}>
            <option value="">Not recorded</option>
            <option value="male">male</option>
            <option value="female">female</option>
            <option value="other">other</option>
          </select>
        </FormField>
      </div>
      <FormField label="Address" error={save.fields.address}>
        <textarea className={inputClass} rows={2} value={form.address} onChange={set("address")} />
      </FormField>

      <FormError error={save.error} />

      <div className="flex justify-end gap-2">
        <button
          onClick={onCancel}
          className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
        >
          Cancel
        </button>
        <ActionButton
          permission="students.profile.write"
          onClick={() => save.run()}
          disabled={save.busy}
        >
          {save.busy ? "Saving…" : "Save changes"}
        </ActionButton>
      </div>
    </div>
  );
}

/**
 * The fee chase, sent as email to the guardians who owe.
 *
 * The audience is resolved by the API, not by this screen: kind "defaulters"
 * runs the same fees.defaulters() the list is drawn from, and puts only their
 * own amount in each family's message. Sending a list of student ids from here
 * would be a second definition of who is behind, and two definitions drift.
 *
 * A bulk send above the school's approval threshold does NOT go out on this
 * click - it queues for someone else to approve, because whoever writes a
 * message to four hundred families is not the person who decides it should go.
 * The result below says which of the two actually happened rather than
 * reporting "sent" either way.
 */
function ChaseDefaulters({ count, onClose }: { count?: number; onClose: () => void }) {
  const [subject, setSubject] = useState("Fee reminder");
  const [body, setBody] = useState(
    "Dear Parent, our records show fees outstanding for your child. " +
      "Please visit the school office at your earliest convenience.",
  );
  const [sent, setSent] = useState<{ recipients: number; needs_approval: boolean } | null>(null);

  const send = useWrite<void, { recipients: number; needs_approval: boolean }>({
    write: () =>
      api.post("/admin/comms/messages", {
        audience: { kind: "defaulters" },
        subject,
        body,
        channel: "email",
        send_now: true,
      } as never) as Promise<{ recipients: number; needs_approval: boolean }>,
    invalidates: [["messages"]],
    onDone: (r) => setSent({ recipients: r.recipients, needs_approval: r.needs_approval }),
  });

  return (
    <Modal title="Email fee defaulters" onClose={onClose}>
      {sent ? (
        <div className="space-y-3 text-sm">
          <p>
            {sent.needs_approval ? (
              <>
                Queued for <strong>{sent.recipients}</strong> guardian(s). It has{" "}
                <strong>not gone out</strong> — a send this size needs approval from someone
                other than whoever wrote it.
              </>
            ) : (
              <>
                Sent to <strong>{sent.recipients}</strong> guardian(s).
              </>
            )}
          </p>
          <button
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Close
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-ink-soft">
            Goes to the guardians of every student with fees outstanding
            {count !== undefined ? ` — ${count} today` : ""}. Each family sees only their own
            amount.
          </p>
          <FormField label="Subject" error={send.fields.subject}>
            <input
              className={inputClass}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </FormField>
          <FormField label="Message" error={send.fields.body}>
            <textarea
              className={inputClass}
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </FormField>
          <FormError error={send.error} />
          <div className="flex justify-end gap-2">
            <button
              onClick={onClose}
              className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
            >
              Cancel
            </button>
            <ActionButton
              permission="comms.message.send"
              onClick={() => send.run()}
              disabled={send.busy || !subject.trim() || !body.trim()}
            >
              {send.busy ? "Sending…" : "Send"}
            </ActionButton>
          </div>
        </div>
      )}
    </Modal>
  );
}
