/**
 * The fee catalogue behind the counter: what each class is charged, and who
 * has been granted a reduction.
 *
 * Fee heads live on /settings — they are school configuration, not a per-year
 * decision. What changes every session is here: the plans built from those
 * heads, and the concessions granted against them.
 *
 * **Concessions name an enrolment, not a student**, and no endpoint maps one
 * to the other. `/admin/students` does not expose `enrolment_id` and the
 * concession rows carry no name, so a list rendered straight from the API is a
 * column of numbers that mean nothing to a clerk. The names here are resolved
 * from `/admin/fees/invoices`, which carries both - the same gap the collect
 * screen hits, recorded in the packet report rather than papered over. Where a
 * concession's enrolment has no invoice the row says so instead of inventing a
 * name.
 */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, money } from "../api/client";
import { useWrite } from "../api/useWrite";
import { ActionButton } from "../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../components/ui";
import { useClasses } from "./useClasses";

/** /admin/fees/plans has no response_model; read off api/admin/fee_setup.py. */
type PlanItem = { id: number; fee_head_id: number; fee_head: string; amount: string; frequency: string };
type Plan = {
  id: number;
  name: string;
  class_name: string | null;
  academic_year_id: number;
  is_active: boolean;
  items: PlanItem[];
};

type Head = { id: number; name: string; code: string; is_active: boolean };

type Concession = {
  id: number;
  enrolment_id: number;
  type: string;
  percent: string | null;
  amount: string | null;
  reason: string;
  status: string;
  valid_from: string | null;
  valid_to: string | null;
};

/** Only the two fields needed to put a name against an enrolment. */
type InvoiceRef = { enrolment_id: number; student_name: string; admission_no: string };

export function FeeSetup() {
  return (
    <>
      <Plans />
      <Concessions />
    </>
  );
}

// --- plans ------------------------------------------------------------------

function Plans() {
  const [adding, setAdding] = useState(false);

  const plans = useQuery({
    queryKey: ["fee-plans"],
    queryFn: () => api.get("/admin/fees/plans") as Promise<Plan[]>,
  });

  return (
    <Card
      title="Fee plans"
      action={
        <ActionButton
          permission="fees.setup.manage"
          onClick={() => setAdding(true)}
          className="!px-3 !py-1.5"
        >
          Add plan
        </ActionButton>
      }
    >
      <p className="text-xs text-ink-faint mb-3">
        What a class is charged, built from the fee heads on Settings. Invoices already raised
        keep the amounts they were raised with — changing a plan changes what is generated next,
        not what a family has already been billed.
      </p>
      <DataTable
        rows={plans.data ?? []}
        loading={plans.isLoading}
        error={plans.error}
        empty="No fee plans yet — add one before generating invoices."
        columns={[
          { key: "class", header: "Class", render: (p) => p.class_name ?? "Any" },
          { key: "name", header: "Plan", render: (p) => p.name },
          {
            key: "items",
            header: "Heads",
            render: (p) =>
              p.items.length === 0
                ? "no lines"
                : p.items.map((i) => `${i.fee_head} ${money(i.amount)}`).join(", "),
          },
          {
            key: "freq",
            header: "Monthly lines",
            align: "right",
            render: (p) => p.items.filter((i) => i.frequency === "monthly").length,
          },
        ]}
      />
      {adding && <AddPlan onClose={() => setAdding(false)} />}
    </Card>
  );
}

function AddPlan({ onClose }: { onClose: () => void }) {
  const classes = useClasses();
  const [name, setName] = useState("");
  const [className, setClassName] = useState("");
  const [lines, setLines] = useState<{ fee_head_id: string; amount: string; frequency: string }[]>(
    [{ fee_head_id: "", amount: "", frequency: "monthly" }],
  );

  const heads = useQuery({
    queryKey: ["fee-heads"],
    queryFn: () => api.get("/admin/fees/heads") as Promise<Head[]>,
  });
  // The plan belongs to an academic year, and the only place the current one's
  // id is exposed is on a plan that already exists.
  const plans = useQuery({
    queryKey: ["fee-plans"],
    queryFn: () => api.get("/admin/fees/plans") as Promise<Plan[]>,
  });
  const yearId = plans.data?.[0]?.academic_year_id;

  const setLine = (i: number, k: "fee_head_id" | "amount" | "frequency", v: string) =>
    setLines(lines.map((l, j) => (j === i ? { ...l, [k]: v } : l)));

  const save = useWrite({
    write: () => {
      if (yearId === undefined) {
        throw new Error(
          "No existing plan to read the academic year from, and no endpoint exposes it on its own.",
        );
      }
      return api.post("/admin/fees/plans", {
        academic_year_id: yearId,
        name,
        class_name: className || null,
        items: lines
          .filter((l) => l.fee_head_id && l.amount)
          .map((l) => ({
            fee_head_id: Number(l.fee_head_id),
            amount: l.amount,
            frequency: l.frequency,
          })),
      } as never);
    },
    invalidates: [["fee-plans"], ["structures"]],
    onDone: onClose,
  });

  return (
    <Modal title="Add fee plan" onClose={onClose}>
      <div className="space-y-3">
        <FormField label="Plan name" error={save.fields.name}>
          <input
            className={inputClass}
            value={name}
            placeholder="Class 6 standard"
            onChange={(e) => setName(e.target.value)}
          />
        </FormField>
        <FormField label="Class" error={save.fields.class_name}>
          <select
            className={inputClass}
            value={className}
            onChange={(e) => setClassName(e.target.value)}
          >
            <option value="">Any class</option>
            {/* class_name, not the section id: a plan is per class, and every
                section of it is charged the same. */}
            {[...new Set((classes.data ?? []).map((c) => c.class_name))].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </FormField>

        <p className="text-sm text-ink-soft pt-1">Lines</p>
        {lines.map((l, i) => (
          <div key={i} className="grid grid-cols-3 gap-2">
            <select
              className={inputClass}
              value={l.fee_head_id}
              onChange={(e) => setLine(i, "fee_head_id", e.target.value)}
            >
              <option value="">Fee head</option>
              {(heads.data ?? [])
                .filter((h) => h.is_active)
                .map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name}
                  </option>
                ))}
            </select>
            <input
              className={inputClass}
              value={l.amount}
              inputMode="decimal"
              placeholder="Amount"
              onChange={(e) => setLine(i, "amount", e.target.value)}
            />
            <select
              className={inputClass}
              value={l.frequency}
              onChange={(e) => setLine(i, "frequency", e.target.value)}
            >
              <option value="monthly">monthly</option>
              <option value="one_time">one_time</option>
            </select>
          </div>
        ))}
        <button
          onClick={() => setLines([...lines, { fee_head_id: "", amount: "", frequency: "monthly" }])}
          className="text-sm text-primary hover:underline"
        >
          + Add a line
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
            permission="fees.setup.manage"
            onClick={() => save.run()}
            disabled={save.busy || !name.trim() || !lines.some((l) => l.fee_head_id && l.amount)}
          >
            {save.busy ? "Saving…" : "Create plan"}
          </ActionButton>
        </div>
      </div>
    </Modal>
  );
}

// --- concessions ------------------------------------------------------------

function Concessions() {
  const [deciding, setDeciding] = useState<{ row: Concession; approve: boolean } | null>(null);

  const list = useQuery({
    queryKey: ["concessions"],
    queryFn: () => api.get("/admin/fees/concessions") as Promise<Concession[]>,
  });

  // enrolment_id -> a name, from the only endpoint that carries both.
  const invoices = useQuery({
    queryKey: ["invoices-for-names"],
    queryFn: () => api.get("/admin/fees/invoices") as Promise<InvoiceRef[]>,
  });
  const nameOf = new Map(
    (invoices.data ?? []).map((i) => [i.enrolment_id, `${i.student_name} · ${i.admission_no}`]),
  );

  const decide = useWrite<string>({
    write: (reason: string) =>
      api.post(
        `/admin/fees/concessions/${deciding!.row.id}/decide` as "/admin/fees/concessions/{concession_id}/decide",
        { approve: deciding!.approve, reason },
      ),
    invalidates: [["concessions"], ["invoices"], ["fee-plans"]],
    onDone: () => setDeciding(null),
  });

  const sweep = useWrite({
    write: () => api.post("/admin/fees/concessions/sibling-sweep"),
    invalidates: [["concessions"]],
  });

  return (
    <>
      <Card
        title="Concessions"
        action={
          <ActionButton
            permission="fees.setup.manage"
            onClick={() => sweep.run()}
            disabled={sweep.busy}
            className="!px-3 !py-1.5"
          >
            {sweep.busy ? "Running…" : "Run sibling sweep"}
          </ActionButton>
        }
      >
        <p className="text-xs text-ink-faint mb-3">
          A reduction is requested by one person and approved by another. The sibling sweep grants
          the school&apos;s standing sibling policy to every family that qualifies and is safe to
          re-run — it will not double-grant.
        </p>
        <FormError error={sweep.error} />
        <DataTable
          rows={list.data ?? []}
          loading={list.isLoading}
          error={list.error}
          empty="No concessions requested."
          columns={[
            {
              key: "who",
              header: "Student",
              render: (c) =>
                nameOf.get(c.enrolment_id) ?? (
                  // Not a dash: "we could not resolve this" and "this family has
                  // no name" are different statements.
                  <span className="text-ink-faint text-xs">
                    enrolment {c.enrolment_id} — no invoice to name it from
                  </span>
                ),
            },
            { key: "type", header: "Type", render: (c) => c.type.replace("_", " ") },
            {
              key: "value",
              header: "Reduction",
              align: "right",
              render: (c) =>
                c.percent !== null ? `${Number(c.percent)}%` : c.amount ? money(c.amount) : "—",
            },
            { key: "why", header: "Reason", render: (c) => c.reason },
            {
              key: "state",
              header: "Status",
              render: (c) => (
                <Pill
                  status={
                    c.status === "approved"
                      ? "paid"
                      : c.status === "rejected" || c.status === "expired"
                        ? "overdue"
                        : "pending"
                  }
                >
                  {c.status}
                </Pill>
              ),
            },
            {
              key: "act",
              header: "",
              render: (c) =>
                // "requested" is the waiting state, not "pending" - the enum in
                // models/enums.py is requested/approved/rejected/expired. The
                // first cut of this guard said "pending", so the Approve and
                // Reject buttons rendered for nothing and the approval step was
                // unreachable. Only a request still waiting can be decided; the
                // API refuses the rest, so no button is offered for them.
                c.status !== "requested" ? null : (
                  <span className="flex gap-2 justify-end">
                    <ActionButton
                      permission="fees.concession.approve"
                      className="!px-3 !py-1 text-xs"
                      onClick={() => setDeciding({ row: c, approve: true })}
                    >
                      Approve
                    </ActionButton>
                    <ActionButton
                      permission="fees.concession.approve"
                      variant="danger"
                      className="!px-3 !py-1 text-xs"
                      onClick={() => setDeciding({ row: c, approve: false })}
                    >
                      Reject
                    </ActionButton>
                  </span>
                ),
            },
          ]}
        />
      </Card>

      {deciding && (
        <ConfirmDialog
          title={`${deciding.approve ? "Approve" : "Reject"} concession`}
          confirmLabel={deciding.approve ? "Approve" : "Reject"}
          busy={decide.busy}
          error={decide.error}
          intent={
            <p>
              {nameOf.get(deciding.row.enrolment_id) ?? `Enrolment ${deciding.row.enrolment_id}`} —{" "}
              {deciding.row.percent !== null
                ? `${Number(deciding.row.percent)}%`
                : deciding.row.amount
                  ? money(deciding.row.amount)
                  : "a reduction"}
              , requested as “{deciding.row.reason}”.
              {deciding.approve
                ? " Approving it reduces what this family is billed from the next invoice onwards."
                : " Rejecting it leaves the family billed in full."}
            </p>
          }
          onConfirm={(reason) => decide.run(reason)}
          onClose={() => {
            decide.reset();
            setDeciding(null);
          }}
        />
      )}
    </>
  );
}
