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

  return (
    <>
      <Card title="Staff">
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            className={`${inputClass} flex-1 min-w-56`}
            placeholder="Name, staff number, phone or role"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className={inputClass}
            value={type}
            onChange={(e) => setType(e.target.value as typeof type)}
          >
            <option value="">Everyone{staff.data ? ` (${staff.data.length})` : ""}</option>
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
              : "No one matches that. Try a staff number, or clear the filter."
          }
          columns={[
            { key: "code", header: "Staff No.", render: (e) => e.employee_code },
            { key: "name", header: "Name", render: (e) => e.full_name },
            {
              key: "type",
              header: "Group",
              render: (e) => (
                <Pill status={e.employee_type === "support" ? "pending" : "paid"}>
                  {TYPE_LABEL[e.employee_type]}
                </Pill>
              ),
            },
            { key: "role", header: "Role", render: (e) => e.designation ?? "—" },
            { key: "dept", header: "Department", render: (e) => e.department ?? "—" },
            { key: "phone", header: "Phone", render: (e) => e.phone ?? "—" },
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
    </>
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
