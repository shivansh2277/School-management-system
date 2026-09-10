import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, money } from "../api/client";
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

type School = {
  name: string;
  address: string | null;
  city: string | null;
  phone: string | null;
  email: string | null;
  logo_url: string | null;
  primary_color: string | null;
  academic_year: string;
};

const FIELDS: [keyof School, string][] = [
  ["name", "School name"],
  ["address", "Address"],
  ["city", "City"],
  ["phone", "Phone"],
  ["email", "Email"],
  ["logo_url", "Logo URL"],
  ["primary_color", "Primary colour"],
  ["academic_year", "Academic year"],
];

type Band = { id: number; min_percent: string; grade: string };
// `/admin/fees/plans` was rebuilt in Part 3 around heads/plans/items and the
// backend route returns a plain dict, so the generated schema can't type its
// shape further than `{[key: string]: unknown}` - this local type documents
// the fields the screen actually reads.
type Plan = { id: number; name: string; class_name: string; monthly_total: string };

export function Settings() {
  const qc = useQueryClient();
  const school = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.get("/admin/settings") as Promise<School>,
  });
  // `/admin/fees/structures` was deleted when Part 3 rebuilt fees, and this
  // call has been a silent 404 ever since - the reason this slice generates
  // types. The replacement is the fee plan, which carries its own monthly
  // total summed from the items that recur monthly.
  //
  // This is the one panel on this screen that crosses a module boundary:
  // `/admin/fees/plans` sits behind `module_enabled("fees")`, while the rest of
  // Settings is a school's own profile and is always available. So the panel
  // gates itself rather than the screen declaring the fees module - a school
  // with fees switched off must still be able to edit its own name.
  const { hasModule } = useAuth();
  const feesOn = hasModule("fees");
  const structures = useQuery({
    queryKey: ["fee-plans"],
    queryFn: () => api.get("/admin/fees/plans") as Promise<Plan[]>,
    enabled: feesOn,
  });

  const bands = useQuery({
    queryKey: ["grade-bands"],
    queryFn: () => api.get("/admin/grade-bands") as Promise<Band[]>,
  });

  const [form, setForm] = useState<School | null>(null);
  useEffect(() => {
    if (school.data) setForm(school.data);
  }, [school.data]);

  const save = useMutation({
    // Guarded because `form` is null until the school query resolves, and the
    // typed body showed Save would post that null straight to the API.
    mutationFn: () => {
      if (!form) throw new Error("School settings have not loaded yet");
      return api.patch("/admin/settings", form);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });

  return (
    <>
      <Card title="School settings">
        <p className="text-xs text-ink-faint mb-4">
          Every school-specific label on any screen reads from here, so a new deployment is a
          configuration change rather than a code change.
        </p>
        {form && (
          <div className="grid gap-3 sm:grid-cols-2">
            {FIELDS.map(([key, label]) => (
              <FormField key={key} label={label}>
                <input
                  className={inputClass}
                  value={form[key] ?? ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              </FormField>
            ))}
          </div>
        )}
        <button
          onClick={() => save.mutate()}
          disabled={save.isPending || !form}
          className="mt-4 rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60"
        >
          {save.isSuccess ? "Saved" : "Save"}
        </button>
      </Card>

      <Card title="Grade bands">
        <p className="text-xs text-ink-faint mb-3">
          Grades are computed at read time from these bands and never stored.
        </p>
        <DataTable
          rows={bands.data ?? []}
          loading={bands.isLoading}
          error={bands.error}
          empty="No grade bands configured."
          columns={[
            { key: "grade", header: "Grade", render: (r) => r.grade },
            {
              key: "min",
              header: "Minimum percentage",
              align: "right",
              render: (r) => `${Number(r.min_percent)}%`,
            },
          ]}
        />
      </Card>

      <GradingSystem />

      {feesOn && <FeeCatalogue />}

      {feesOn && (
      <Card title="Fee structure">
        <DataTable
          rows={structures.data ?? []}
          loading={structures.isLoading}
          error={structures.error}
          empty="No fee structure configured."
          columns={[
            { key: "class", header: "Class", render: (r) => r.class_name },
            {
              key: "amt",
              header: "Monthly amount",
              align: "right",
              render: (r) => money(r.monthly_total),
            },
          ]}
        />
      </Card>
      )}
    </>
  );
}

/** /admin/grading-scales returns a plain dict; these are the fields read here. */
type Scale = {
  id: number;
  name: string;
  version: number;
  is_active: boolean;
  frozen_at: string | null;
  bands: { min_percent: string; grade: string; description: string | null }[];
};

type Head = { id: number; name: string; code: string; type: string; is_active: boolean };

/**
 * Changing the grading system.
 *
 * The read-only card above shows `/admin/grade-bands`, which is the active
 * scale flattened for display. This is the scale store itself: a school runs
 * one active scale, and switching to another is an explicit activation rather
 * than an edit, so a report card printed last term still means what it said.
 *
 * A frozen scale cannot have its bands rewritten - the API refuses it, and so
 * does the button, because results already published against it would silently
 * change grade. Publish a new scale and activate that instead.
 */
function GradingSystem() {
  const { can } = useAuth();
  const [editing, setEditing] = useState<Scale | null>(null);

  const scales = useQuery({
    queryKey: ["grading-scales"],
    queryFn: () => api.get("/admin/grading-scales") as Promise<Scale[]>,
    enabled: can("exam.definition.read"),
  });

  const activate = useWrite<number>({
    write: (id: number) =>
      api.post(`/admin/grading-scales/${id}/activate` as "/admin/grading-scales/{scale_id}/activate"),
    invalidates: [["grading-scales"], ["grade-bands"]],
  });

  if (!can("exam.definition.read")) return null;

  return (
    <Card title="Grading system">
      <p className="text-xs text-ink-faint mb-3">
        One scale is active at a time. Grades are computed from its bands at read time and never
        stored, so activating a different scale changes how every percentage reads from now on.
      </p>
      <DataTable
        rows={scales.data ?? []}
        loading={scales.isLoading}
        error={scales.error}
        empty="No grading scale configured yet."
        columns={[
          { key: "name", header: "Scale", render: (s) => s.name },
          { key: "ver", header: "Version", render: (s) => `v${s.version}`, align: "right" },
          {
            key: "bands",
            header: "Bands",
            render: (s) =>
              s.bands
                .map((b) => `${b.grade} ${Number(b.min_percent)}%+`)
                .join(", ") || "none",
          },
          {
            key: "state",
            header: "Status",
            render: (s) => (
              <Pill status={s.is_active ? "paid" : "pending"}>
                {s.is_active ? "active" : s.frozen_at ? "frozen" : "draft"}
              </Pill>
            ),
          },
          {
            key: "act",
            header: "",
            render: (s) => (
              <span className="flex gap-2 justify-end">
                <ActionButton
                  permission="exam.definition.write"
                  onClick={() => setEditing(s)}
                  className="!px-3 !py-1 text-xs"
                  disabled={s.frozen_at !== null}
                >
                  Edit bands
                </ActionButton>
                {!s.is_active && (
                  <ActionButton
                    permission="exam.definition.write"
                    onClick={() => activate.run(s.id)}
                    className="!px-3 !py-1 text-xs"
                    disabled={activate.busy}
                  >
                    Make active
                  </ActionButton>
                )}
              </span>
            ),
          },
        ]}
      />
      <FormError error={activate.error} />
      {editing && <EditBands scale={editing} onClose={() => setEditing(null)} />}
    </Card>
  );
}

/**
 * Rewriting one scale's bands.
 *
 * Sent as a whole list because the API replaces them wholesale - bands are a
 * ladder and editing one rung in isolation is how you end up with a gap at 79%
 * that quietly grades nobody.
 */
function EditBands({ scale, onClose }: { scale: Scale; onClose: () => void }) {
  const [rows, setRows] = useState(
    scale.bands.map((b) => ({
      grade: b.grade,
      min_percent: String(Number(b.min_percent)),
      description: b.description ?? "",
    })),
  );

  const set = (i: number, k: "grade" | "min_percent" | "description", v: string) =>
    setRows(rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)));

  const save = useWrite({
    write: () =>
      api.put(
        `/admin/grading-scales/${scale.id}/bands` as "/admin/grading-scales/{scale_id}/bands",
        rows.map((r) => ({
          grade: r.grade,
          min_percent: r.min_percent,
          description: r.description || null,
        })) as never,
      ),
    invalidates: [["grading-scales"], ["grade-bands"]],
    onDone: onClose,
  });

  return (
    <Modal title={`Bands — ${scale.name}`} onClose={onClose}>
      <div className="space-y-3">
        <p className="text-xs text-ink-faint">
          Every band, in one go: the API replaces the whole ladder rather than patching a rung,
          so what is listed here is what the scale becomes.
        </p>
        {rows.map((r, i) => (
          <div key={i} className="grid grid-cols-3 gap-2">
            <FormField label={i === 0 ? "Grade" : ""}>
              <input className={inputClass} value={r.grade} onChange={(e) => set(i, "grade", e.target.value)} />
            </FormField>
            <FormField label={i === 0 ? "Minimum %" : ""}>
              <input
                className={inputClass}
                inputMode="decimal"
                value={r.min_percent}
                onChange={(e) => set(i, "min_percent", e.target.value)}
              />
            </FormField>
            <FormField label={i === 0 ? "Description" : ""}>
              <input
                className={inputClass}
                value={r.description}
                onChange={(e) => set(i, "description", e.target.value)}
              />
            </FormField>
          </div>
        ))}
        <button
          onClick={() => setRows([...rows, { grade: "", min_percent: "", description: "" }])}
          className="text-sm text-primary hover:underline"
        >
          + Add a band
        </button>
        <FormError error={save.error} />
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <ActionButton
            permission="exam.definition.write"
            onClick={() => save.run()}
            disabled={save.busy}
          >
            {save.busy ? "Saving…" : "Replace bands"}
          </ActionButton>
        </div>
      </div>
    </Modal>
  );
}

/**
 * Adding to the fee catalogue.
 *
 * A head is what a charge is called - Tuition, Transport, Late Fee. A plan is
 * a class's set of heads and amounts. Nothing here edits money that has
 * already been invoiced: changing a plan changes what future invoices are
 * generated from, which is why there is no edit control on an existing one.
 */
function FeeCatalogue() {
  const { can } = useAuth();
  const [adding, setAdding] = useState(false);

  const heads = useQuery({
    queryKey: ["fee-heads"],
    queryFn: () => api.get("/admin/fees/heads") as Promise<Head[]>,
    enabled: can("fees.invoice.read"),
  });

  if (!can("fees.invoice.read")) return null;

  return (
    <Card
      title="Fee heads"
      action={
        <ActionButton
          permission="fees.setup.manage"
          onClick={() => setAdding(true)}
          className="!px-3 !py-1.5"
        >
          Add fee head
        </ActionButton>
      }
    >
      <p className="text-xs text-ink-faint mb-3">
        What a charge is called. Plans below draw their lines from these, and an invoice that has
        already been raised keeps the head it was raised with.
      </p>
      <DataTable
        rows={heads.data ?? []}
        loading={heads.isLoading}
        error={heads.error}
        empty="No fee heads configured — add one before building a plan."
        columns={[
          { key: "code", header: "Code", render: (h) => h.code },
          { key: "name", header: "Name", render: (h) => h.name },
          { key: "type", header: "Type", render: (h) => h.type },
          {
            key: "state",
            header: "Status",
            render: (h) => (
              <Pill status={h.is_active ? "paid" : "pending"}>
                {h.is_active ? "active" : "retired"}
              </Pill>
            ),
          },
        ]}
      />
      {adding && <AddFeeHead onClose={() => setAdding(false)} />}
    </Card>
  );
}

function AddFeeHead({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ name: "", code: "", type: "recurring" });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm({ ...form, [k]: e.target.value });

  const save = useWrite({
    write: () =>
      api.post("/admin/fees/heads", {
        name: form.name,
        code: form.code.toUpperCase(),
        type: form.type,
      } as never),
    invalidates: [["fee-heads"]],
    onDone: onClose,
  });

  return (
    <Modal title="Add fee head" onClose={onClose}>
      <div className="space-y-3">
        <FormField label="Name" error={save.fields.name}>
          <input className={inputClass} value={form.name} onChange={set("name")} placeholder="Tuition Fee" />
        </FormField>
        <FormField label="Code" error={save.fields.code}>
          <input className={inputClass} value={form.code} onChange={set("code")} placeholder="TUI" />
        </FormField>
        <FormField label="Type" error={save.fields.type}>
          <select className={inputClass} value={form.type} onChange={set("type")}>
            <option value="recurring">recurring — charged every cycle</option>
            <option value="one_time">one_time — charged once</option>
          </select>
        </FormField>
        <FormError error={save.error} />
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <ActionButton
            permission="fees.setup.manage"
            onClick={() => save.run()}
            disabled={save.busy || !form.name.trim() || !form.code.trim()}
          >
            {save.busy ? "Saving…" : "Add head"}
          </ActionButton>
        </div>
      </div>
    </Modal>
  );
}
