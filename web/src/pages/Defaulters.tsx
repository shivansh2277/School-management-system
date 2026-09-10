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
    <>
      <Card title="Fee defaulters">
        <div className="grid gap-3 sm:grid-cols-3 mb-4">
          <label className="block text-sm">
            <span className="text-ink-soft">Owing at least</span>
            <input
              className={`${inputClass} mt-1`}
              value={minAmount}
              inputMode="decimal"
              placeholder="any amount"
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
              <span className="text-ink-soft">Class</span>
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
          <StatCard label="Students to chase" value={rows.isLoading ? "…" : list.length} />
        </div>

        <DataTable
          rows={list}
          loading={rows.isLoading}
          error={rows.error}
          empty="Nobody owes anything on these filters — nothing to chase."
          columns={[
            { key: "name", header: "Student", render: (d) => d.student_name },
            { key: "adm", header: "Admission No.", render: (d) => d.admission_no },
            { key: "class", header: "Class", render: (d) => d.class_label },
            {
              key: "ring",
              header: "Who to ring",
              render: (d) =>
                d.contact?.phone ? (
                  <span>
                    <a className="text-primary hover:underline" href={`tel:${d.contact.phone}`}>
                      {d.contact.phone}
                    </a>
                    {d.contact.name ? (
                      <span className="text-ink-faint"> · {d.contact.name}</span>
                    ) : null}
                  </span>
                ) : (
                  // Not "—": no number on file is a fact the office can act on.
                  <span className="text-danger text-xs">no number on file</span>
                ),
            },
            { key: "months", header: "Months", render: (d) => d.months_due, align: "right" },
            {
              key: "since",
              header: "Oldest due",
              render: (d) => (
                <span>
                  {asDate(d.oldest_due_date)}
                  <span className="text-ink-faint text-xs"> · {d.days_overdue}d</span>
                </span>
              ),
            },
            { key: "fine", header: "Late fee", render: (d) => money(d.late_fee), align: "right" },
            {
              key: "due",
              header: "Outstanding",
              render: (d) => <strong>{money(d.outstanding)}</strong>,
              align: "right",
            },
          ]}
        />
      </Card>
    </>
  );
}
