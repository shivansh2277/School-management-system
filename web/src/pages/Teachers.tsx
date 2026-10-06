/**
 * Everyone who works at the school, not only the ones who teach.
 *
 * This screen used to read `/admin/teachers`, which returns teaching staff and
 * nothing else. The school's 16 employees include two drivers, a bus attendant
 * and an office administrator, and none of them appeared anywhere in the
 * product - they existed only as rows nobody could look at. `/admin/employees`
 * is the list that has always covered all of them, plus
 * `/admin/employees/{id}` for a full record.
 *
 * `employee_type` is the school's own three-way split (models/enums.py):
 * teaching, administrative, support. Support is the drivers, the attendant and
 * the cleaning staff - the people a school runs on and a staff list usually
 * forgets.
 *
 * Neither endpoint declares a `response_model`, so the shapes below are
 * hand-written against `services/hr.py::profile` rather than checked by the
 * compiler.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { Card, DataTable, Empty, ErrorState, Modal, Pill, inputClass } from "../components/ui";

/** services/hr.py::profile */
type Employee = {
  id: number;
  employee_code: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  employee_type: "teaching" | "administrative" | "support";
  status: string;
  qualification: string | null;
  designation: string | null;
  department_id: number | null;
  department: string | null;
  reporting_to_id: number | null;
  reporting_to: string | null;
  joining_date: string | null;
  exited_on: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
};

/** The school's words for its own three staff groups, not the enum's. */
const TYPE_LABEL: Record<Employee["employee_type"], string> = {
  administrative: "School administration",
  teaching: "Teaching staff",
  support: "Support staff",
};

const TYPES = ["administrative", "teaching", "support"] as const;

/** ISO on the wire, dd/mm/yyyy on screen (Part Three rule 6). */
const asDate = (iso: string | null) =>
  iso === null ? "—" : new Date(iso).toLocaleDateString("en-GB");

export function Teachers() {
  const [q, setQ] = useState("");
  const [type, setType] = useState<"" | Employee["employee_type"]>("");
  const [openId, setOpenId] = useState<number | null>(null);

  const staff = useQuery({
    queryKey: ["employees"],
    // Exited staff are excluded by the API's own default: they are kept for
    // ever but are not the answer to "who works here".
    queryFn: () => api.get("/admin/employees") as Promise<Employee[]>,
  });

  const detail = useQuery({
    queryKey: ["employee", openId],
    queryFn: () =>
      api.get(`/admin/employees/${openId}` as "/admin/employees/{employee_id}") as Promise<Employee>,
    enabled: openId !== null,
  });

  // What the office actually knows when it goes looking: a name, a staff
  // number, a phone, or what somebody does (Part Three rule 2).
  const needle = q.trim().toLowerCase();
  const rows = (staff.data ?? [])
    .filter((e) => type === "" || e.employee_type === type)
    .filter(
      (e) =>
        needle === "" ||
        [e.full_name, e.employee_code, e.phone, e.designation, e.department]
          .filter(Boolean)
          .some((f) => String(f).toLowerCase().includes(needle)),
    );

  const counts = TYPES.map((t) => ({
    type: t,
    n: (staff.data ?? []).filter((e) => e.employee_type === t).length,
  }));

  const totalStaff = staff.data?.length ?? 0;
  const teachingCount = counts.find((c) => c.type === "teaching")?.n ?? 0;
  const adminCount = counts.find((c) => c.type === "administrative")?.n ?? 0;
  const supportCount = counts.find((c) => c.type === "support")?.n ?? 0;

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Staff Directory</h1>
          <p className="text-xs text-ink-faint mt-0.5">
            Teaching faculty, administrative leadership, and operational support staff
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {totalStaff} Total Staff
          </span>
        </div>
      </div>

      {/* Staff Breakdown Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <button
          type="button"
          onClick={() => setType("")}
          className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
            type === ""
              ? "bg-slate-900 text-white border-slate-900 shadow-sm"
              : "bg-surface border-rule/80 hover:border-slate-300 shadow-2xs"
          }`}
        >
          <span className={`text-xs font-semibold ${type === "" ? "text-slate-300" : "text-ink-soft"}`}>
            All Personnel
          </span>
          <div className={`text-2xl font-extrabold mt-0.5 tabular ${type === "" ? "text-white" : "text-ink"}`}>
            {totalStaff}
          </div>
          <span className={`text-[11px] ${type === "" ? "text-slate-400" : "text-ink-faint"}`}>
            Active employees
          </span>
        </button>

        <button
          type="button"
          onClick={() => setType("teaching")}
          className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
            type === "teaching"
              ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
              : "bg-surface border-rule/80 hover:border-indigo-200 shadow-2xs"
          }`}
        >
          <span className={`text-xs font-semibold ${type === "teaching" ? "text-indigo-100" : "text-ink-soft"}`}>
            Teaching Faculty
          </span>
          <div className={`text-2xl font-extrabold mt-0.5 tabular ${type === "teaching" ? "text-white" : "text-indigo-600"}`}>
            {teachingCount}
          </div>
          <span className={`text-[11px] ${type === "teaching" ? "text-indigo-200" : "text-indigo-700/80"}`}>
            Academic instruction
          </span>
        </button>

        <button
          type="button"
          onClick={() => setType("administrative")}
          className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
            type === "administrative"
              ? "bg-blue-600 text-white border-blue-600 shadow-sm"
              : "bg-surface border-rule/80 hover:border-blue-200 shadow-2xs"
          }`}
        >
          <span className={`text-xs font-semibold ${type === "administrative" ? "text-blue-100" : "text-ink-soft"}`}>
            Administration
          </span>
          <div className={`text-2xl font-extrabold mt-0.5 tabular ${type === "administrative" ? "text-white" : "text-blue-600"}`}>
            {adminCount}
          </div>
          <span className={`text-[11px] ${type === "administrative" ? "text-blue-200" : "text-blue-700/80"}`}>
            Office & leadership
          </span>
        </button>

        <button
          type="button"
          onClick={() => setType("support")}
          className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
            type === "support"
              ? "bg-amber-600 text-white border-amber-600 shadow-sm"
              : "bg-surface border-rule/80 hover:border-amber-200 shadow-2xs"
          }`}
        >
          <span className={`text-xs font-semibold ${type === "support" ? "text-amber-100" : "text-ink-soft"}`}>
            Support Staff
          </span>
          <div className={`text-2xl font-extrabold mt-0.5 tabular ${type === "support" ? "text-white" : "text-amber-600"}`}>
            {supportCount}
          </div>
          <span className={`text-[11px] ${type === "support" ? "text-amber-200" : "text-amber-700/80"}`}>
            Transport & operations
          </span>
        </button>
      </div>

      {/* Roster Card */}
      <Card
        title={`Staff Register (${rows.length})`}
        action={
          <span className="text-xs text-ink-faint">
            Click row to view complete employment record
          </span>
        }
      >
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            className={`${inputClass} flex-1 min-w-56`}
            placeholder="Search by name, staff code, role, or phone..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className={`${inputClass} sm:w-60`}
            value={type}
            onChange={(e) => setType(e.target.value as typeof type)}
          >
            <option value="">All Groups ({totalStaff})</option>
            {counts.map((c) => (
              <option key={c.type} value={c.type}>
                {TYPE_LABEL[c.type]} ({c.n})
              </option>
            ))}
          </select>
        </div>

        <DataTable<Employee>
          rows={rows}
          loading={staff.isLoading}
          error={staff.error}
          onRowClick={(e) => setOpenId(e.id)}
          empty={
            needle === "" && type === ""
              ? "Nobody on the staff register yet."
              : "No one matches that filter. Clear the filter or try a different search."
          }
          columns={[
            {
              key: "code",
              header: "Staff Code",
              render: (e) => (
                <span className="font-mono text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200/60">
                  {e.employee_code}
                </span>
              ),
            },
            {
              key: "name",
              header: "Employee Name",
              render: (e) => (
                <span className="font-semibold text-ink flex items-center gap-2.5">
                  <span className="w-7 h-7 rounded-full bg-slate-100 text-slate-700 border border-slate-200 flex items-center justify-center text-xs font-bold shrink-0">
                    {e.full_name.charAt(0)}
                  </span>
                  <span className="hover:text-primary transition-colors">{e.full_name}</span>
                </span>
              ),
            },
            {
              key: "type",
              header: "Department Group",
              render: (e) => {
                const colorMap = {
                  teaching: "bg-indigo-50 text-indigo-700 border-indigo-200",
                  administrative: "bg-blue-50 text-blue-700 border-blue-200",
                  support: "bg-amber-50 text-amber-700 border-amber-200",
                };
                return (
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${colorMap[e.employee_type] || "bg-slate-100"}`}>
                    {TYPE_LABEL[e.employee_type]}
                  </span>
                );
              },
            },
            { key: "role", header: "Designation", render: (e) => <span className="font-medium text-ink-soft">{e.designation ?? "—"}</span> },
            { key: "dept", header: "Department", render: (e) => <span className="text-ink-soft">{e.department ?? "—"}</span> },
            {
              key: "phone",
              header: "Contact Phone",
              render: (e) =>
                e.phone ? (
                  <a
                    href={`tel:${e.phone}`}
                    onClick={(ev) => ev.stopPropagation()}
                    className="text-primary hover:underline text-xs font-medium"
                  >
                    {e.phone}
                  </a>
                ) : (
                  <span className="text-ink-faint text-xs">—</span>
                ),
            },
          ]}
        />
      </Card>

      {openId !== null && (
        <Modal title="Staff record" onClose={() => setOpenId(null)}>
          {/* An error branch, not a bare "Loading...". A failed detail used to
              leave the Students drawer loading for ever; the same shape here
              would do the same thing. */}
          {detail.error ? (
            <ErrorState error={detail.error} />
          ) : detail.data ? (
            <Details employee={detail.data} />
          ) : (
            <Empty>Loading…</Empty>
          )}
        </Modal>
      )}
    </div>
  );
}

function Details({ employee }: { employee: Employee }) {
  const fields: [string, string | number][] = [
    ["Staff number", employee.employee_code],
    ["Group", TYPE_LABEL[employee.employee_type]],
    ["Role", employee.designation ?? "—"],
    ["Department", employee.department ?? "—"],
    ["Qualification", employee.qualification ?? "—"],
    ["Reports to", employee.reporting_to ?? "—"],
    ["Joined", asDate(employee.joining_date)],
    ["Status", employee.status.replace("_", " ")],
    ["Phone", employee.phone ?? "—"],
    ["Email", employee.email ?? "—"],
    ["Emergency contact", employee.emergency_contact_name ?? "—"],
    ["Emergency phone", employee.emergency_contact_phone ?? "—"],
  ];

  return (
    <>
      <div className="mb-4">
        <p className="font-semibold">{employee.full_name}</p>
        <p className="text-xs text-ink-faint">
          {employee.designation ?? TYPE_LABEL[employee.employee_type]}
          {employee.department ? ` · ${employee.department}` : ""}
        </p>
      </div>

      <dl className="grid grid-cols-2 gap-3 text-sm">
        {fields.map(([k, v]) => (
          <div key={k}>
            <dt className="text-ink-faint text-xs">{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>

      {employee.exited_on && (
        <p className="mt-4 text-xs text-ink-faint">
          Left on {asDate(employee.exited_on)}. The record is kept rather than deleted.
        </p>
      )}

      <p className="mt-4 text-xs text-ink-faint">
        Pay, PF and bank details are deliberately not shown here — they sit behind
        <code className="mx-1">hr.salary.read</code>, which is a separate permission.
      </p>
    </>
  );
}
