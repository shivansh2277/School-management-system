/**
 * The setting store, the module switches and the custom field definitions.
 *
 * ERP_BLUEPRINT §0.18 says a records clerk configures the product. Until now
 * enabling a module needed a `curl`, which means in practice it needed the
 * developer — so a school waited on a deployment to change its own late fee.
 *
 * Three things a reader should know before changing this file:
 *
 *  - **The registry is the vocabulary.** `GET /admin/configuration` returns the
 *    definitions alongside the values, so this screen renders controls for keys
 *    it was never written against. Adding a setting in
 *    `core/settings_registry.py` makes it appear here with no frontend change.
 *    Nothing below hardcodes a setting key; the area labels are presentation
 *    only, and an unmatched key still renders, under "Other".
 *  - **The route has no `response_model`**, so the generated schema types it as
 *    `{[key: string]: unknown}`. `Config` below is hand-written off
 *    `api/admin/settings.py::read_settings` and is therefore unchecked — the
 *    same gap that put a `₹NaN` on a fee screen. Read the route, not this type,
 *    if the two ever disagree.
 *  - **A module switch takes effect on the next `/auth/me`.** The API honours it
 *    at once, but the sidebar is drawn from the cached `modules` list, so
 *    without the `refresh()` below the clerk turns Transport off, sees the menu
 *    item still there, and concludes the switch did nothing.
 *
 * Academic year management is NOT here: the backend has no academic-year
 * endpoint at all (only `services/tenancy.py::set_current_year`, which nothing
 * routes to). An empty panel promising it would be a lie about what the product
 * does. See `reports/packet-3-configuration.md`.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
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

/** Hand-written off api/admin/settings.py::read_settings — see the note above. */
type Config = {
  values: Record<string, unknown>;
  definitions: { key: string; type: string; default: unknown; description: string }[];
  modules: { code: string; name: string; built: boolean }[];
};

type CustomFieldRow = {
  id: number;
  entity: string;
  key: string;
  label: string;
  field_type: string;
  options: string[] | null;
  is_required: boolean;
  is_active: boolean;
  sort_order: number;
};

/**
 * What a school actually loses when it turns a module off, in the clerk's own
 * words rather than the module's name repeated.
 *
 * Each line was read off the routers that carry
 * `Depends(module_enabled("<code>"))` — grep for it before editing one of
 * these. A switch whose description is wrong is worse than no description: it
 * is the clerk's only warning before a whole department's screens vanish.
 */
const TURNS_OFF: Record<string, string> = {
  students:
    "The student roster, admission numbers and enrolment. Fees and attendance both hang off it, so the counter can no longer look a child up.",
  attendance: "Daily roll call, the attendance registers and the shortage list.",
  examinations: "Exams, marks entry, grading scales and report cards.",
  fees: "Invoices, the collection counter, receipts, defaulters and fee setup — and the fee pages in the parent app.",
  homework:
    "Homework set and submitted in the teacher and student apps. Nothing in these office screens reads it.",
  communication:
    "Notices and every outgoing message. The board itself disappears, not only new sends.",
  admission:
    "Enquiries, applications, assessments, offers, and converting an applicant into a student.",
  timetable: "The period grid, teacher allocation and substitutions.",
  hr: "The staff register, staff attendance, leave and payroll.",
  transport: "Vehicles, routes, stops, and which child is on which bus.",
  reports: "The whole report library and its exports.",
};

/**
 * Where a setting belongs on screen. First match wins, so the longer prefix is
 * listed first — `fees.late_fee.grace_days` is late fee, not fees.
 */
const AREAS: [prefix: string, label: string][] = [
  ["fees.late_fee.", "Late fee"],
  ["fees.sibling_concession", "Sibling concession"],
  ["fees.", "Fees"],
  ["attendance.", "Attendance"],
  ["exams.", "Examinations"],
  ["timetable.", "Teacher workload"],
  ["comms.", "Communication"],
  ["school.", "School"],
];

const areaOf = (key: string) => AREAS.find(([p]) => key.startsWith(p))?.[1] ?? "Other";

/** `fees.late_fee.per_day` -> `Per day`. The description carries the detail. */
const settingLabel = (key: string) => {
  const last = key.split(".").pop() ?? key;
  const words = last.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
};

const ENTITIES = ["student", "application", "guardian", "employee", "vehicle", "school"] as const;
const FIELD_TYPES = ["text", "number", "date", "boolean", "select"] as const;

export function Configuration() {
  const { refresh } = useAuth();
  const config = useQuery({
    queryKey: ["configuration"],
    queryFn: () => api.get("/admin/configuration") as Promise<Config>,
  });

  return (
    <>
      <Modules config={config.data} loading={config.isLoading} error={config.error} onSaved={refresh} />
      <Settings config={config.data} loading={config.isLoading} error={config.error} />
      <CustomFields />
    </>
  );
}

/* ------------------------------------------------------------------ modules */

function Modules({
  config,
  loading,
  error,
  onSaved,
}: {
  config?: Config;
  loading: boolean;
  error: unknown;
  onSaved: () => Promise<void>;
}) {
  const [confirming, setConfirming] = useState<{ code: string; name: string } | null>(null);
  const [sidebarStale, setSidebarStale] = useState(false);

  const toggle = useWrite<{ code: string; on: boolean }>({
    write: ({ code, on }) => api.put("/admin/configuration", { values: { [`feature.${code}`]: on } }),
    invalidates: [["configuration"]],
    onDone: () => {
      setConfirming(null);
      // The switch is live at the API immediately; only the cached /auth/me
      // that draws the sidebar is behind. Re-read it, and say so, because a
      // menu that has not changed reads as a switch that did not work.
      setSidebarStale(true);
      void onSaved().finally(() => setSidebarStale(false));
    },
  });

  const rows = (config?.modules ?? []).map((m) => ({
    ...m,
    on: config?.values[`feature.${m.code}`] === true,
  }));

  return (
    <>
      <Card title="Modules">
        <p className="text-xs text-ink-faint mb-4">
          A module that is off is refused by the API, not merely hidden — the screens disappear for
          everyone at this school, whatever their role. Data already recorded is kept and comes back
          when the module does.
        </p>
        {sidebarStale && (
          <p className="text-xs text-ink-soft mb-3">Refreshing the menu…</p>
        )}
        <FormError error={toggle.error} />
        <DataTable
          rows={rows}
          loading={loading}
          error={error}
          empty="No modules are declared."
          columns={[
            {
              key: "name",
              header: "Module",
              render: (m) => (
                <>
                  <span className="font-medium">{m.name}</span>
                  <p className="text-xs text-ink-faint mt-0.5 max-w-md">
                    Turning this off stops: {TURNS_OFF[m.code] ?? "everything under this module."}
                  </p>
                </>
              ),
            },
            {
              key: "state",
              header: "Status",
              render: (m) => <Pill status={m.on ? "paid" : "pending"}>{m.on ? "On" : "Off"}</Pill>,
            },
            {
              key: "act",
              header: "",
              render: (m) => (
                <ActionButton
                  permission="admin.settings.write"
                  variant={m.on ? "danger" : "primary"}
                  className="!px-3 !py-1 text-xs"
                  disabled={toggle.busy}
                  onClick={() =>
                    m.on
                      ? setConfirming({ code: m.code, name: m.name })
                      : toggle.run({ code: m.code, on: true })
                  }
                >
                  {m.on ? "Turn off" : "Turn on"}
                </ActionButton>
              ),
            },
          ]}
        />
      </Card>

      {confirming && (
        <Modal title={`Turn off ${confirming.name}`} onClose={() => setConfirming(null)}>
          <div className="space-y-3">
            <p className="text-sm text-ink-soft">
              This stops: {TURNS_OFF[confirming.code] ?? "everything under this module."}
            </p>
            <p className="text-sm text-ink-soft">
              It applies to every user at this school at once. Nothing is deleted, and turning the
              module back on restores the screens exactly as they were.
            </p>
            {/*
              No reason is collected. `services/school_settings.py::set_many`
              audits the before/after itself but accepts no reason field, and a
              dialog that collects one and throws it away is worse than one that
              does not ask. Reported as a gap in the packet report.
            */}
            <FormError error={toggle.error} />
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setConfirming(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
              >
                Cancel
              </button>
              <ActionButton
                permission="admin.settings.write"
                variant="danger"
                disabled={toggle.busy}
                onClick={() => toggle.run({ code: confirming.code, on: false })}
              >
                Turn it off
              </ActionButton>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}

/* ----------------------------------------------------------------- settings */

function Settings({
  config,
  loading,
  error,
}: {
  config?: Config;
  loading: boolean;
  error: unknown;
}) {
  /** Only the keys the clerk has touched, as typed. Empty means nothing to save. */
  const [draft, setDraft] = useState<Record<string, string>>({});

  const defs = (config?.definitions ?? []).filter((d) => !d.key.startsWith("feature."));
  const areas = AREAS.map(([, label]) => label)
    .concat("Other")
    .map((label) => ({ label, defs: defs.filter((d) => areaOf(d.key) === label) }))
    .filter((a) => a.defs.length > 0);

  const shown = (key: string) =>
    draft[key] ?? String(config?.values[key] ?? "");

  /** The typed value to send, or an error message for this field. */
  const typed = (key: string, type: string): { value: unknown } | { problem: string } => {
    const raw = shown(key);
    if (type === "bool") return { value: raw === "true" };
    if (type === "int") {
      const n = Number(raw);
      // The backend refuses a float or a string for an int key with a 422 the
      // clerk cannot act on, so it is caught here where the input is.
      if (raw.trim() === "" || !Number.isInteger(n)) return { problem: "A whole number" };
      return { value: n };
    }
    return { value: raw };
  };

  const problems: Record<string, string> = {};
  const payload: Record<string, unknown> = {};
  for (const key of Object.keys(draft)) {
    const def = defs.find((d) => d.key === key);
    if (!def) continue;
    const t = typed(key, def.type);
    if ("problem" in t) problems[key] = t.problem;
    else payload[key] = t.value;
  }

  const save = useWrite({
    write: () => api.put("/admin/configuration", { values: payload }),
    invalidates: [["configuration"]],
    onDone: () => setDraft({}),
  });

  const dirty = Object.keys(draft).length > 0;
  const blocked = Object.keys(problems).length > 0;

  return (
    <Card
      title="Settings"
      action={
        <ActionButton
          permission="admin.settings.write"
          disabled={!dirty || blocked || save.busy}
          onClick={() => save.run()}
        >
          {save.busy ? "Saving…" : dirty ? "Save changes" : "Saved"}
        </ActionButton>
      }
    >
      <p className="text-xs text-ink-faint mb-4">
        These are the numbers the software bills and reports on, not a copy of them. Changing the
        late fee here is how the late fee changes — nothing is hard-coded behind these.
      </p>
      <FormError error={save.error} />
      {loading && defs.length === 0 && <p className="text-sm text-ink-faint py-6 text-center">Loading…</p>}
      {!!error && defs.length === 0 && (
        <p className="text-sm text-danger py-6 text-center">Could not load the settings.</p>
      )}

      {areas.map((area) => (
        <section key={area.label} className="mb-6 last:mb-0">
          <h3 className="text-sm font-semibold mb-3">{area.label}</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {area.defs.map((d) => (
              <FormField
                key={d.key}
                label={settingLabel(d.key)}
                error={problems[d.key] ?? save.fields[d.key]}
              >
                {d.type === "bool" ? (
                  <select
                    className={inputClass}
                    value={shown(d.key)}
                    onChange={(e) => setDraft({ ...draft, [d.key]: e.target.value })}
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                ) : (
                  <input
                    className={inputClass}
                    inputMode={d.type === "int" ? "numeric" : undefined}
                    value={shown(d.key)}
                    onChange={(e) => setDraft({ ...draft, [d.key]: e.target.value })}
                  />
                )}
                <p className="mt-1 text-xs text-ink-faint">{d.description}</p>
              </FormField>
            ))}
          </div>
        </section>
      ))}
    </Card>
  );
}

/* ------------------------------------------------------------ custom fields */

function CustomFields() {
  const [entity, setEntity] = useState<(typeof ENTITIES)[number]>("student");
  const [adding, setAdding] = useState(false);
  const [retiring, setRetiring] = useState<CustomFieldRow | null>(null);

  const fields = useQuery({
    queryKey: ["custom-fields", entity],
    queryFn: () =>
      api.get("/admin/custom-fields", `?entity=${entity}&include_inactive=true`) as Promise<
        CustomFieldRow[]
      >,
  });

  const retire = useWrite({
    write: () =>
      api.del(
        `/admin/custom-fields/${retiring!.id}` as "/admin/custom-fields/{field_id}",
      ),
    invalidates: [["custom-fields"]],
    onDone: () => setRetiring(null),
  });

  return (
    <>
      <Card
        title="Custom fields"
        action={
          <div className="flex items-center gap-2">
            <select
              className="rounded-input border border-rule px-3 py-1.5 text-sm outline-none focus:border-primary"
              value={entity}
              onChange={(e) => setEntity(e.target.value as (typeof ENTITIES)[number])}
            >
              {ENTITIES.map((e) => (
                <option key={e} value={e}>
                  {e}
                </option>
              ))}
            </select>
            <ActionButton permission="admin.settings.write" onClick={() => setAdding(true)}>
              Add a field
            </ActionButton>
          </div>
        }
      >
        <p className="text-xs text-ink-faint mb-4">
          Attributes this school records that the software does not ship — a caste certificate
          number, a bus pass id. Retiring one hides it from every form; the values already recorded
          are kept, so retiring by mistake loses nothing.
        </p>
        <DataTable
          rows={fields.data ?? []}
          loading={fields.isLoading}
          error={fields.error}
          empty={`No custom fields on ${entity}.`}
          columns={[
            {
              key: "label",
              header: "Field",
              render: (f) => (
                <>
                  <span className="font-medium">{f.label}</span>
                  <p className="text-xs text-ink-faint">{f.key}</p>
                </>
              ),
            },
            {
              key: "type",
              header: "Type",
              render: (f) =>
                f.field_type === "select" ? `select: ${(f.options ?? []).join(", ")}` : f.field_type,
            },
            { key: "required", header: "Required", render: (f) => (f.is_required ? "Yes" : "No") },
            {
              key: "state",
              header: "Status",
              render: (f) => (
                <Pill status={f.is_active ? "paid" : "pending"}>
                  {f.is_active ? "In use" : "Retired"}
                </Pill>
              ),
            },
            {
              key: "act",
              header: "",
              render: (f) =>
                f.is_active ? (
                  <ActionButton
                    permission="admin.settings.write"
                    variant="danger"
                    className="!px-3 !py-1 text-xs"
                    onClick={() => setRetiring(f)}
                  >
                    Retire
                  </ActionButton>
                ) : (
                  <span className="text-xs text-ink-faint">—</span>
                ),
            },
          ]}
        />
      </Card>

      {adding && <AddField entity={entity} onClose={() => setAdding(false)} />}

      {retiring && (
        <Modal title={`Retire ${retiring.label}`} onClose={() => setRetiring(null)}>
          <div className="space-y-3">
            <p className="text-sm text-ink-soft">
              “{retiring.label}” stops appearing on every {retiring.entity} form. Values already
              recorded against it are kept in the database and reappear if the field is defined
              again with the same key.
            </p>
            {/*
              No reason is collected: DELETE /admin/custom-fields/{id} takes no
              reason and `services/custom_fields.py::retire` writes no audit row
              at all, so there is nowhere to send one. Reported as a defect.
            */}
            <FormError error={retire.error} />
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setRetiring(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
              >
                Cancel
              </button>
              <ActionButton
                permission="admin.settings.write"
                variant="danger"
                disabled={retire.busy}
                onClick={() => retire.run()}
              >
                Retire it
              </ActionButton>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}

function AddField({
  entity,
  onClose,
}: {
  entity: (typeof ENTITIES)[number];
  onClose: () => void;
}) {
  const [key, setKey] = useState("");
  const [label, setLabel] = useState("");
  const [fieldType, setFieldType] = useState<(typeof FIELD_TYPES)[number]>("text");
  const [options, setOptions] = useState("");
  const [required, setRequired] = useState(false);

  const create = useWrite({
    write: () =>
      api.post("/admin/custom-fields", {
        entity,
        key: key.trim(),
        label: label.trim(),
        field_type: fieldType,
        options:
          fieldType === "select"
            ? options
                .split(",")
                .map((o) => o.trim())
                .filter(Boolean)
            : null,
        is_required: required,
      }),
    invalidates: [["custom-fields"]],
    onDone: onClose,
  });

  return (
    <Modal title={`Add a field to ${entity}`} onClose={onClose}>
      <div className="space-y-3">
        <FormField label="Key" error={create.fields.key}>
          <input
            className={inputClass}
            value={key}
            autoFocus
            onChange={(e) => setKey(e.target.value)}
            placeholder="bus_pass_no"
          />
          <p className="mt-1 text-xs text-ink-faint">
            Lower case, letters, digits and underscores, at least two characters. It is how the
            value is stored and cannot be changed afterwards.
          </p>
        </FormField>
        <FormField label="Label" error={create.fields.label}>
          <input
            className={inputClass}
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Bus pass number"
          />
        </FormField>
        <FormField label="Type" error={create.fields.field_type}>
          <select
            className={inputClass}
            value={fieldType}
            onChange={(e) => setFieldType(e.target.value as (typeof FIELD_TYPES)[number])}
          >
            {FIELD_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </FormField>
        {fieldType === "select" && (
          <FormField label="Options, separated by commas" error={create.fields.options}>
            <input
              className={inputClass}
              value={options}
              onChange={(e) => setOptions(e.target.value)}
              placeholder="Own transport, School bus, Walks"
            />
          </FormField>
        )}
        <label className="flex items-center gap-2 text-sm text-ink-soft">
          <input type="checkbox" checked={required} onChange={(e) => setRequired(e.target.checked)} />
          Required — every new record must fill it in
        </label>
        <FormError error={create.error} />
        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
          >
            Cancel
          </button>
          <ActionButton
            permission="admin.settings.write"
            disabled={create.busy || !key.trim() || !label.trim()}
            onClick={() => create.run()}
          >
            Add it
          </ActionButton>
        </div>
      </div>
    </Modal>
  );
}
