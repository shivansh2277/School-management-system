/**
 * Who owes what, worst first, with a number to ring.
 *
 * A list without a contact is a report; a list with one is a chase, and the
 * chase is the job. So the guardian's phone is a column, not something behind
 * a click into the student record.
 *
 * **There is deliberately no "total being chased" figure.** Every amount here
 * arrives as a string because `Numeric` is serialised as one, and adding them
 * up in the browser means parsing money into a JS float - the one thing
 * CLAUDE.md's money rules forbid, and the reason a concession can end up a
 * paisa away from the printed fee card. No endpoint returns that total today,
 * so the screen reports the count it can defend and omits the sum it cannot.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, money } from "../api/client";
import { Card, DataTable, StatCard, inputClass } from "../components/ui";
import { useClasses } from "./useClasses";

/** /admin/fees/defaulters has no response_model; read off services/fees.py. */
type Defaulter = {
  student_id: number;
  enrolment_id: number;
  student_name: string;
  admission_no: string;
  class_label: string;
  /** The guardian to ring. An object, not a string. */
  contact: { name: string | null; phone: string | null; email: string | null } | null;
  months_due: number;
  oldest_due_date: string;
  outstanding: string;
  late_fee: string;
  days_overdue: number;
};

const asDate = (iso: string) => new Date(iso).toLocaleDateString("en-GB");

export function Defaulters() {
  const [minAmount, setMinAmount] = useState("");
  const [classId, setClassId] = useState("");
  const classes = useClasses();

  const query = new URLSearchParams();
  if (minAmount.trim()) query.set("min_amount", minAmount.trim());
  if (classId) query.set("class_section_id", classId);
  const suffix = query.toString() ? `?${query}` : "";

  const rows = useQuery({
    queryKey: ["defaulters", minAmount, classId],
    queryFn: () => api.get("/admin/fees/defaulters", suffix) as Promise<Defaulter[]>,
  });

  const list = rows.data ?? [];

  return (
    <div className="space-y-6">
      {/* Header Surface Card */}
      <div className="bg-surface rounded-card shadow-card p-4 sm:p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-ink">Fee Defaulters</h1>
        </div>
        <div>
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
            {rows.isLoading ? "Loading..." : `${list.length} students overdue`}
          </span>
        </div>
      </div>

      <Card title="Chase Filter Criteria">
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="block text-sm">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Owing at least (₹)</span>
            <input
              className={`${inputClass} mt-1`}
              value={minAmount}
              inputMode="decimal"
              placeholder="e.g. 5000"
              onChange={(e) => setMinAmount(e.target.value)}
            />
          </label>
          {/*
            The class filter is a secondary widget and gates itself: a fee
            collector holds fees.invoice.read without academics.class.read, and
            hiding the whole chase list over one dropdown would cost them more
            than the missing dropdown does. Same trade as /notices.
          */}
          {classes.data && (
            <label className="block text-sm">
              <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Filter by Class</span>
              <select
                className={`${inputClass} mt-1`}
                value={classId}
                onChange={(e) => setClassId(e.target.value)}
              >
                <option value="">Every class</option>
                {classes.data.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.class_label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <StatCard
            label="Defaulters to Chase"
            value={rows.isLoading ? "…" : list.length}
            hint={minAmount ? `Filtered >= ₹${minAmount}` : "All outstanding accounts"}
          />
        </div>
      </Card>

      <Card
        title="Outstanding Defaulters Register"
        action={
          <span className="text-xs text-ink-faint">
            Sorted worst-first by balance & age
          </span>
        }
      >
        <DataTable
          rows={list}
          loading={rows.isLoading}
          error={rows.error}
          empty="Nobody owes anything on these filters — nothing to chase."
          columns={[
            {
              key: "name",
              header: "Student",
              render: (d) => (
                <span className="font-semibold text-ink">{d.student_name}</span>
              ),
            },
            {
              key: "adm",
              header: "Admission No.",
              render: (d) => (
                <span className="font-mono text-xs text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200/60">
                  {d.admission_no}
                </span>
              ),
            },
            {
              key: "class",
              header: "Class",
              render: (d) => (
                <span className="text-xs font-medium text-slate-700 bg-slate-50 px-2 py-0.5 rounded border border-slate-200/50">
                  {d.class_label}
                </span>
              ),
            },
            {
              key: "ring",
              header: "Contact / Who to Ring",
              render: (d) =>
                d.contact?.phone ? (
                  <span className="flex items-center gap-1.5">
                    <a
                      className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline bg-primary/5 px-2 py-1 rounded border border-primary/20"
                      href={`tel:${d.contact.phone}`}
                    >
                      <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      {d.contact.phone}
                    </a>
                    {d.contact.name ? (
                      <span className="text-ink-faint text-xs">({d.contact.name})</span>
                    ) : null}
                  </span>
                ) : (
                  // Not "—": no number on file is a fact the office can act on.
                  <span className="text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 text-xs font-medium">
                    no number on file
                  </span>
                ),
            },
            {
              key: "months",
              header: "Months",
              render: (d) => (
                <span className="font-semibold text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                  {d.months_due}m
                </span>
              ),
              align: "right",
            },
            {
              key: "since",
              header: "Oldest Due",
              render: (d) => (
                <span className="text-xs">
                  <span className="text-ink-soft">{asDate(d.oldest_due_date)}</span>
                  <span className="ml-1 text-rose-600 font-semibold">({d.days_overdue}d)</span>
                </span>
              ),
            },
            {
              key: "fine",
              header: "Late Fee",
              render: (d) => <span className="font-mono text-xs text-amber-700">{money(d.late_fee)}</span>,
              align: "right",
            },
            {
              key: "due",
              header: "Outstanding",
              render: (d) => <span className="font-mono font-bold text-rose-700">{money(d.outstanding)}</span>,
              align: "right",
            },
          ]}
        />
      </Card>
    </div>
  );
}
