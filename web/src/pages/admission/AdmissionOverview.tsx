import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api, money } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { ActionButton } from "../../components/Can";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  FormError,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../../components/ui";
import { useClasses } from "../useClasses";
import type { AdmissionCycle, SeatUsage } from "./types";

const asDate = (d: string | null) =>
  d ? new Date(d).toLocaleDateString("en-GB") : "—";

export function AdmissionOverview() {
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditCycleModal, setShowEditCycleModal] = useState(false);
  const [configuringClass, setConfiguringClass] = useState<string | null>(null);

  const classesQuery = useClasses();

  // Cycles list
  const cyclesQuery = useQuery({
    queryKey: ["admission-cycles"],
    queryFn: () =>
      api.get("/admin/admission/cycles") as Promise<AdmissionCycle[]>,
  });

  const cycles = cyclesQuery.data ?? [];
  const activeCycle =
    cycles.find((c) => c.id === selectedCycleId) ??
    cycles.find((c) => c.status === "open") ??
    cycles[0] ??
    null;
  const cycleId = activeCycle?.id ?? null;

  // Cycle Dashboard
  const dashboardQuery = useQuery({
    queryKey: ["admission-dashboard", cycleId],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/dashboard` as "/admin/admission/cycles/{cycle_id}/dashboard",
      ),
    enabled: cycleId !== null,
  });

  // Cycle Seats
  const seatsQuery = useQuery({
    queryKey: ["admission-seats", cycleId],
    queryFn: () =>
      api.get(
        `/admin/admission/cycles/${cycleId}/seats` as "/admin/admission/cycles/{cycle_id}/seats",
      ) as Promise<SeatUsage[]>,
    enabled: cycleId !== null,
  });

  // Create Cycle write
  const [cycleForm, setCycleForm] = useState({
    name: "",
    academic_year_id: 1,
    starts_on: "",
    ends_on: "",
    application_fee: "500.00",
    late_fee: "0.00",
    allow_online_applications: true,
    admission_fee_refund_policy: "Refundable before session commencement with 10% processing fee.",
  });

  const createCycle = useWrite({
    write: (data: typeof cycleForm) =>
      api.post("/admin/admission/cycles", {
        name: data.name,
        academic_year_id: Number(data.academic_year_id),
        starts_on: data.starts_on || undefined,
        ends_on: data.ends_on || undefined,
        application_fee: data.application_fee,
        late_fee: data.late_fee,
        allow_online_applications: data.allow_online_applications,
        admission_fee_refund_policy: data.admission_fee_refund_policy || undefined,
      } as any),
    invalidates: [["admission-cycles"]],
    onDone: (created: any) => {
      setShowCreateModal(false);
      if (created?.id) setSelectedCycleId(created.id);
    },
  });

  // Edit Cycle write
  const [editForm, setEditForm] = useState({
    status: "open",
    starts_on: "",
    ends_on: "",
    application_fee: "500.00",
    late_fee: "0.00",
    allow_online_applications: true,
    admission_fee_refund_policy: "",
  });

  const updateCycle = useWrite({
    write: (data: typeof editForm) =>
      api.patch(
        `/admin/admission/cycles/${cycleId}` as "/admin/admission/cycles/{cycle_id}",
        {
          status: data.status as any,
          starts_on: data.starts_on || undefined,
          ends_on: data.ends_on || undefined,
          application_fee: data.application_fee,
          late_fee: data.late_fee,
          allow_online_applications: data.allow_online_applications,
          admission_fee_refund_policy: data.admission_fee_refund_policy || undefined,
        } as any,
      ),
    invalidates: [["admission-cycles"], ["admission-dashboard", cycleId]],
    onDone: () => setShowEditCycleModal(false),
  });

  // Configure Class write
  const [classForm, setClassForm] = useState({
    class_name: "",
    stream: "",
    total_seats: 40,
    reserved_seats: "{}",
    age_on: "",
    min_age_years: "3.0",
    max_age_years: "4.5",
    requires_test: false,
    requires_interview: false,
  });

  const saveClassConfig = useWrite({
    write: (data: typeof classForm) => {
      let reserved = {};
      try {
        reserved = JSON.parse(data.reserved_seats || "{}");
      } catch {
        // empty
      }
      return api.put(
        `/admin/admission/cycles/${cycleId}/classes` as "/admin/admission/cycles/{cycle_id}/classes",
        {
          class_name: data.class_name,
          stream: data.stream || undefined,
          total_seats: Number(data.total_seats),
          reserved_seats: reserved,
          age_on: data.age_on || undefined,
          min_age_years: data.min_age_years || undefined,
          max_age_years: data.max_age_years || undefined,
          requires_test: data.requires_test,
          requires_interview: data.requires_interview,
        } as any,
      );
    },
    invalidates: [
      ["admission-seats", cycleId],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => setConfiguringClass(null),
  });

  const dbData = (dashboardQuery.data as any) || null;
  const funnelStages: { stage: string; count: number; of_previous: number | null }[] =
    dbData?.funnel?.stages ?? [];
  const todayAgenda = dbData?.today ?? { tests: [], interviews: [], follow_ups_due: 0 };
  const awaitingMap: Record<string, number> = dbData?.awaiting_action ?? {};

  const seats = seatsQuery.data ?? [];
  const totalSeats = seats.reduce((acc, s) => acc + (s.total_seats ?? 0), 0);
  const filledSeats = seats.reduce(
    (acc, s) => acc + (s.filled_total ?? (s as any).taken ?? 0),
    0,
  );
  const remainingSeats = seats.reduce(
    (acc, s) => acc + (s.remaining_total ?? (s as any).available ?? 0),
    0,
  );

  return (
    <div className="space-y-6">
      {/* Top action & Cycle Header */}
      <header className="flex flex-wrap items-center justify-between gap-4 bg-surface rounded-card shadow-card p-5">
        <div className="flex items-center gap-3">
          <div>
            <span className="text-xs font-medium uppercase tracking-wider text-ink-faint">
              Admission Season
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <select
                className={`${inputClass} max-w-xs font-semibold text-base py-1`}
                value={activeCycle?.id ?? ""}
                onChange={(e) => setSelectedCycleId(Number(e.target.value))}
                disabled={cycles.length === 0}
              >
                {cycles.length === 0 && <option value="">No cycle configured</option>}
                {cycles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.academic_year}) — {c.status.toUpperCase()}
                  </option>
                ))}
              </select>
              {activeCycle && (
                <Pill
                  status={
                    activeCycle.status === "open"
                      ? "present"
                      : activeCycle.status === "closed"
                        ? "absent"
                        : "pending"
                  }
                >
                  {activeCycle.status.toUpperCase()}
                </Pill>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {activeCycle && (
            <ActionButton
              permission="admission.cycle.write"
              onClick={() => {
                setEditForm({
                  status: activeCycle.status,
                  starts_on: activeCycle.starts_on ?? "",
                  ends_on: activeCycle.ends_on ?? "",
                  application_fee: activeCycle.application_fee,
                  late_fee: activeCycle.late_fee,
                  allow_online_applications: activeCycle.allow_online_applications,
                  admission_fee_refund_policy:
                    activeCycle.admission_fee_refund_policy ?? "",
                });
                setShowEditCycleModal(true);
              }}
            >
              Cycle settings
            </ActionButton>
          )}

          <ActionButton
            permission="admission.cycle.write"
            onClick={() => {
              if (activeCycle) {
                setCycleForm((prev) => ({
                  ...prev,
                  academic_year_id: activeCycle.academic_year_id,
                }));
              }
              setShowCreateModal(true);
            }}
          >
            + New cycle
          </ActionButton>
        </div>
      </header>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          label="Total Enquiries"
          value={funnelStages.find((s) => s.stage === "enquiries")?.count ?? 0}
          hint={
            todayAgenda.follow_ups_due > 0
              ? `${todayAgenda.follow_ups_due} follow-up(s) due today`
              : "No overdue follow-ups"
          }
        />
        <StatCard
          label="Applications"
          value={funnelStages.find((s) => s.stage === "applied")?.count ?? 0}
          hint={
            awaitingMap["under_document_verification"]
              ? `${awaitingMap["under_document_verification"]} pending doc verify`
              : "All documents processed"
          }
        />
        <StatCard
          label="Docs Verified"
          value={funnelStages.find((s) => s.stage === "documents_verified")?.count ?? 0}
          hint="Cleared for assessment"
        />
        <StatCard
          label="Shortlisted / Decided"
          value={funnelStages.find((s) => s.stage === "decided")?.count ?? 0}
          hint={`${awaitingMap["offer_issued"] ?? 0} offers awaiting response`}
        />
        <StatCard
          label="Enrolled Students"
          value={funnelStages.find((s) => s.stage === "enrolled")?.count ?? 0}
          hint="Fully converted & onboarded"
        />
        <StatCard
          label="Seats Available"
          value={remainingSeats}
          hint={`${filledSeats} / ${totalSeats} seats filled`}
        />
      </div>

      {/* Funnel progression strip */}
      <Card title="Admission Funnel Progression">
        {funnelStages.length === 0 ? (
          <Empty>No funnel metrics recorded for this cycle yet.</Empty>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {funnelStages.map((st, idx) => (
              <div
                key={st.stage}
                className="bg-ground rounded-input p-3 border border-rule flex flex-col justify-between"
              >
                <div>
                  <span className="text-xs uppercase font-semibold text-ink-faint">
                    Step {idx + 1}: {st.stage.replace(/_/g, " ")}
                  </span>
                  <p className="text-2xl font-bold tabular mt-1">{st.count}</p>
                </div>
                {st.of_previous !== null && (
                  <p className="text-xs text-ink-soft mt-2 pt-2 border-t border-rule">
                    {st.of_previous}% conversion
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Seats & Capacity Allocation */}
      <Card
        title="Class Seat Capacity & Selection Criteria"
        action={
          <ActionButton
            permission="admission.cycle.write"
            variant="primary"
            onClick={() => {
              const defaultClassName = classesQuery.data?.[0]?.class_name ?? "Class 1";
              setClassForm({
                class_name: defaultClassName,
                stream: "",
                total_seats: 40,
                reserved_seats: '{"RTE": 10, "Staff": 2}',
                age_on: activeCycle?.starts_on ?? "",
                min_age_years: "5.5",
                max_age_years: "6.5",
                requires_test: false,
                requires_interview: false,
              });
              setConfiguringClass(defaultClassName);
            }}
          >
            Configure class seats
          </ActionButton>
        }
      >
        <DataTable<SeatUsage>
          loading={seatsQuery.isLoading}
          error={seatsQuery.error}
          empty="No classes configured for this cycle. Click 'Configure class seats' above to add intake quotas."
          columns={[
            {
              key: "class_name",
              header: "Class",
              render: (r) => (
                <span className="font-semibold text-ink">
                  {r.class_name} {r.stream ? `(${r.stream})` : ""}
                </span>
              ),
            },
            {
              key: "total_seats",
              header: "Total Capacity",
              align: "right",
              render: (r) => <span className="tabular">{r.total_seats}</span>,
            },
            {
              key: "general_seats",
              header: "General Quota",
              align: "right",
              render: (r) => <span className="tabular">{r.general_seats}</span>,
            },
            {
              key: "reserved_seats",
              header: "Reserved Seats",
              render: (r) => {
                const resMap = r.reserved_seats ?? (r as any).reserved ?? {};
                const entries = Object.entries(resMap);
                if (entries.length === 0) return <span className="text-ink-faint">None</span>;
                return (
                  <div className="flex flex-wrap gap-1">
                    {entries.map(([cat, qty]) => (
                      <span
                        key={cat}
                        className="bg-ground px-1.5 py-0.5 rounded text-xs text-ink-soft border border-rule tabular"
                      >
                        {cat}: {qty as any}
                      </span>
                    ))}
                  </div>
                );
              },
            },
            {
              key: "filled_total",
              header: "Admitted / Filled",
              align: "right",
              render: (r) => {
                const filled = r.filled_total ?? (r as any).taken ?? 0;
                return (
                  <span className="tabular font-medium text-ink">
                    {filled}
                  </span>
                );
              },
            },
            {
              key: "remaining_total",
              header: "Available",
              align: "right",
              render: (r) => {
                const rem = r.remaining_total ?? (r as any).available ?? 0;
                return (
                  <span
                    className={`tabular font-semibold ${
                      rem > 0 ? "text-success" : "text-danger"
                    }`}
                  >
                    {rem}
                  </span>
                );
              },
            },
            {
              key: "actions",
              header: "",
              align: "right",
              render: (r) => (
                <ActionButton
                  permission="admission.cycle.write"
                  className="px-2.5 py-1 text-xs"
                  onClick={() => {
                    setClassForm({
                      class_name: r.class_name,
                      stream: r.stream ?? "",
                      total_seats: r.total_seats,
                      reserved_seats: JSON.stringify(r.reserved_seats ?? {}),
                      age_on: activeCycle?.starts_on ?? "",
                      min_age_years: "",
                      max_age_years: "",
                      requires_test: false,
                      requires_interview: false,
                    });
                    setConfiguringClass(r.class_name);
                  }}
                >
                  Edit seats
                </ActionButton>
              ),
            },
          ]}
          rows={seats}
        />
      </Card>

      {/* Today's Tasks & Overdue Work */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Written Tests & Observations Today">
          {todayAgenda.tests.length === 0 ? (
            <Empty>No admission tests or observations scheduled for today.</Empty>
          ) : (
            <div className="space-y-2">
              {todayAgenda.tests.map((t: any) => (
                <div
                  key={t.assessment_id}
                  className="flex items-center justify-between p-2.5 bg-ground rounded-input border border-rule text-sm"
                >
                  <div>
                    <span className="font-semibold text-ink">
                      App #{t.application_id}
                    </span>
                    <span className="text-ink-soft ml-2">
                      Venue: {t.venue || "TBD"}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-ink-faint">
                      {new Date(t.scheduled_at).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    {t.seat_no && (
                      <span className="ml-2 text-xs bg-surface px-1.5 py-0.5 rounded border border-rule">
                        Seat: {t.seat_no}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Interviews Today">
          {todayAgenda.interviews.length === 0 ? (
            <Empty>No panel interviews scheduled for today.</Empty>
          ) : (
            <div className="space-y-2">
              {todayAgenda.interviews.map((iv: any) => (
                <div
                  key={iv.interview_id}
                  className="flex items-center justify-between p-2.5 bg-ground rounded-input border border-rule text-sm"
                >
                  <div>
                    <span className="font-semibold text-ink">
                      App #{iv.application_id}
                    </span>
                    <span className="text-ink-soft ml-2">
                      Venue: {iv.venue || "TBD"}
                    </span>
                  </div>
                  <span className="text-xs text-ink-faint">
                    {new Date(iv.scheduled_at).toLocaleTimeString("en-IN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Modal: Create Cycle */}
      {showCreateModal && (
        <Modal
          title="Create Admission Cycle"
          onClose={() => setShowCreateModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createCycle.run(cycleForm);
            }}
            className="space-y-4"
          >
            <FormField label="Cycle Name" error={createCycle.fields["name"]}>
              <input
                required
                className={inputClass}
                placeholder="e.g. Academic Year 2026-27 Intake"
                value={cycleForm.name}
                onChange={(e) =>
                  setCycleForm({ ...cycleForm, name: e.target.value })
                }
              />
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Application Fee"
                error={createCycle.fields["application_fee"]}
              >
                <input
                  type="number"
                  step="0.01"
                  required
                  className={inputClass}
                  value={cycleForm.application_fee}
                  onChange={(e) =>
                    setCycleForm({
                      ...cycleForm,
                      application_fee: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Late Fee" error={createCycle.fields["late_fee"]}>
                <input
                  type="number"
                  step="0.01"
                  className={inputClass}
                  value={cycleForm.late_fee}
                  onChange={(e) =>
                    setCycleForm({ ...cycleForm, late_fee: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Starts On"
                error={createCycle.fields["starts_on"]}
              >
                <input
                  type="date"
                  className={inputClass}
                  value={cycleForm.starts_on}
                  onChange={(e) =>
                    setCycleForm({ ...cycleForm, starts_on: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Ends On" error={createCycle.fields["ends_on"]}>
                <input
                  type="date"
                  className={inputClass}
                  value={cycleForm.ends_on}
                  onChange={(e) =>
                    setCycleForm({ ...cycleForm, ends_on: e.target.value })
                  }
                />
              </FormField>
            </div>

            <FormField label="Refund Policy Details">
              <textarea
                className={inputClass}
                rows={2}
                value={cycleForm.admission_fee_refund_policy}
                onChange={(e) =>
                  setCycleForm({
                    ...cycleForm,
                    admission_fee_refund_policy: e.target.value,
                  })
                }
              />
            </FormField>

            <FormError error={createCycle.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createCycle.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {createCycle.busy ? "Creating..." : "Create Cycle"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Edit Cycle */}
      {showEditCycleModal && (
        <Modal
          title={`Edit Cycle: ${activeCycle?.name}`}
          onClose={() => setShowEditCycleModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateCycle.run(editForm);
            }}
            className="space-y-4"
          >
            <FormField label="Cycle Status">
              <select
                className={inputClass}
                value={editForm.status}
                onChange={(e) =>
                  setEditForm({ ...editForm, status: e.target.value })
                }
              >
                <option value="planning">Planning (Draft)</option>
                <option value="open">Open (Accepting Applications)</option>
                <option value="closed">Closed (Decisions & Selection)</option>
                <option value="archived">Archived</option>
              </select>
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Application Fee">
                <input
                  type="number"
                  step="0.01"
                  required
                  className={inputClass}
                  value={editForm.application_fee}
                  onChange={(e) =>
                    setEditForm({ ...editForm, application_fee: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Late Fee">
                <input
                  type="number"
                  step="0.01"
                  className={inputClass}
                  value={editForm.late_fee}
                  onChange={(e) =>
                    setEditForm({ ...editForm, late_fee: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Starts On">
                <input
                  type="date"
                  className={inputClass}
                  value={editForm.starts_on}
                  onChange={(e) =>
                    setEditForm({ ...editForm, starts_on: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Ends On">
                <input
                  type="date"
                  className={inputClass}
                  value={editForm.ends_on}
                  onChange={(e) =>
                    setEditForm({ ...editForm, ends_on: e.target.value })
                  }
                />
              </FormField>
            </div>

            <FormField label="Refund Policy Details">
              <textarea
                className={inputClass}
                rows={2}
                value={editForm.admission_fee_refund_policy}
                onChange={(e) =>
                  setEditForm({
                    ...editForm,
                    admission_fee_refund_policy: e.target.value,
                  })
                }
              />
            </FormField>

            <FormError error={updateCycle.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setShowEditCycleModal(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateCycle.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {updateCycle.busy ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Configure Class Seats */}
      {configuringClass !== null && (
        <Modal
          title={`Configure Seat Capacity: ${classForm.class_name}`}
          onClose={() => setConfiguringClass(null)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              saveClassConfig.run(classForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Class Name">
                <input
                  required
                  className={inputClass}
                  placeholder="e.g. Class 1 or Nursery"
                  value={classForm.class_name}
                  onChange={(e) =>
                    setClassForm({ ...classForm, class_name: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Stream (Optional)">
                <input
                  className={inputClass}
                  placeholder="e.g. Science, Commerce"
                  value={classForm.stream}
                  onChange={(e) =>
                    setClassForm({ ...classForm, stream: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Total Seats Capacity">
                <input
                  type="number"
                  min="1"
                  required
                  className={inputClass}
                  value={classForm.total_seats}
                  onChange={(e) =>
                    setClassForm({
                      ...classForm,
                      total_seats: Number(e.target.value),
                    })
                  }
                />
              </FormField>
              <FormField label='Reserved Seats Quota (JSON: {"RTE": 10})'>
                <input
                  className={inputClass}
                  placeholder='{"RTE": 10, "Staff": 2}'
                  value={classForm.reserved_seats}
                  onChange={(e) =>
                    setClassForm({
                      ...classForm,
                      reserved_seats: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <FormField label="Min Age (Years)">
                <input
                  type="number"
                  step="0.1"
                  className={inputClass}
                  placeholder="e.g. 5.5"
                  value={classForm.min_age_years}
                  onChange={(e) =>
                    setClassForm({
                      ...classForm,
                      min_age_years: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Max Age (Years)">
                <input
                  type="number"
                  step="0.1"
                  className={inputClass}
                  placeholder="e.g. 6.5"
                  value={classForm.max_age_years}
                  onChange={(e) =>
                    setClassForm({
                      ...classForm,
                      max_age_years: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Age As On Date">
                <input
                  type="date"
                  className={inputClass}
                  value={classForm.age_on}
                  onChange={(e) =>
                    setClassForm({ ...classForm, age_on: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="flex items-center gap-6 pt-2">
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={classForm.requires_test}
                  onChange={(e) =>
                    setClassForm({
                      ...classForm,
                      requires_test: e.target.checked,
                    })
                  }
                />
                Requires Written Assessment
              </label>
              <label className="flex items-center gap-2 text-sm text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={classForm.requires_interview}
                  onChange={(e) =>
                    setClassForm({
                      ...classForm,
                      requires_interview: e.target.checked,
                    })
                  }
                />
                Requires Interview
              </label>
            </div>

            <FormError error={saveClassConfig.error} />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm text-ink-soft hover:text-ink"
                onClick={() => setConfiguringClass(null)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saveClassConfig.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {saveClassConfig.busy ? "Saving..." : "Save Class Config"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
