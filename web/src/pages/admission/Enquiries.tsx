import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { ActionButton } from "../../components/Can";
import {
  Card,
  ConfirmDialog,
  DataTable,
  Empty,
  ErrorState,
  FormError,
  FormField,
  Modal,
  Pill,
  inputClass,
} from "../../components/ui";
import { useClasses } from "../useClasses";
import type {
  AdmissionCycle,
  Enquiry,
  EnquiryDetail,
  EnquiryInteraction,
} from "./types";
import { PrintableEnquirySlip } from "../../components/admission/PrintableEnquirySlip";

const asDate = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleDateString("en-GB") : "—";

const isOverdue = (d: string | null | undefined) => {
  if (!d) return false;
  const today = new Date().toISOString().split("T")[0];
  return d <= today;
};

export function Enquiries() {
  const [term, setTerm] = useState("");
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [onlyDue, setOnlyDue] = useState(false);

  // Selected enquiry for detail view / drawer
  const [selectedEnquiryId, setSelectedEnquiryId] = useState<number | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [invalidatingId, setInvalidatingId] = useState<number | null>(null);
  const [printingEnquiry, setPrintingEnquiry] = useState<Enquiry | null>(null);

  const classesQuery = useClasses();

  // Cycles
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

  // Build query string
  const todayIso = new Date().toISOString().split("T")[0];
  let queryString = "";
  const params: string[] = [];
  if (cycleId) params.push(`cycle_id=${cycleId}`);
  if (statusFilter) params.push(`status=${encodeURIComponent(statusFilter)}`);
  if (onlyDue) params.push(`due_by=${todayIso}`);
  if (term.trim()) params.push(`q=${encodeURIComponent(term.trim())}`);
  if (params.length > 0) queryString = `?${params.join("&")}`;

  // Enquiries list query
  const enquiriesQuery = useQuery({
    queryKey: ["admission-enquiries", cycleId, statusFilter, onlyDue, term],
    queryFn: () =>
      api.get(
        "/admin/admission/enquiries",
        queryString,
      ) as Promise<Enquiry[]>,
  });

  // Enquiry Detail query
  const enquiryDetailQuery = useQuery({
    queryKey: ["admission-enquiry-detail", selectedEnquiryId],
    queryFn: () =>
      api.get(
        `/admin/admission/enquiries/${selectedEnquiryId}` as "/admin/admission/enquiries/{enquiry_id}",
      ) as Promise<EnquiryDetail>,
    enabled: selectedEnquiryId !== null,
  });

  // Create Enquiry form
  const [createForm, setCreateForm] = useState({
    enquirer_name: "",
    mobile: "",
    email: "",
    child_name: "",
    child_dob: "",
    class_of_interest: "Class 1",
    source: "walk_in",
    next_follow_up_on: "",
  });

  const createEnquiry = useWrite({
    write: (data: typeof createForm) =>
      api.post("/admin/admission/enquiries", {
        cycle_id: cycleId ?? undefined,
        enquirer_name: data.enquirer_name,
        mobile: data.mobile,
        email: data.email || undefined,
        child_name: data.child_name || undefined,
        child_dob: data.child_dob || undefined,
        class_of_interest: data.class_of_interest || undefined,
        source: data.source as any,
        next_follow_up_on: data.next_follow_up_on || undefined,
      } as any),
    invalidates: [
      ["admission-enquiries"],
      ["admission-dashboard", cycleId],
    ],
    onDone: (created: any) => {
      setShowCreateModal(false);
      setCreateForm({
        enquirer_name: "",
        mobile: "",
        email: "",
        child_name: "",
        child_dob: "",
        class_of_interest: "Class 1",
        source: "walk_in",
        next_follow_up_on: "",
      });
      if (created?.id) setSelectedEnquiryId(created.id);
    },
  });

  // Log Interaction form
  const [interactionForm, setInteractionForm] = useState({
    channel: "phone",
    notes: "",
    outcome: "contacted",
    next_follow_up_on: "",
  });

  const logInteraction = useWrite({
    write: (data: typeof interactionForm) =>
      api.post(
        `/admin/admission/enquiries/${selectedEnquiryId}/interactions` as "/admin/admission/enquiries/{enquiry_id}/interactions",
        {
          channel: data.channel as any,
          notes: data.notes || undefined,
          outcome: data.outcome as any,
          next_follow_up_on: data.next_follow_up_on || undefined,
        } as any,
      ),
    invalidates: [
      ["admission-enquiries"],
      ["admission-enquiry-detail", selectedEnquiryId],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => {
      setInteractionForm({
        channel: "phone",
        notes: "",
        outcome: "contacted",
        next_follow_up_on: "",
      });
    },
  });

  // Mark Invalid write
  const markInvalid = useWrite({
    write: ({ id, reason }: { id: number; reason: string }) =>
      api.del(
        `/admin/admission/enquiries/${id}` as "/admin/admission/enquiries/{enquiry_id}",
        `?reason=${encodeURIComponent(reason)}`,
      ),
    invalidates: [
      ["admission-enquiries"],
      ["admission-enquiry-detail", selectedEnquiryId],
      ["admission-dashboard", cycleId],
    ],
    onDone: () => {
      setInvalidatingId(null);
      if (selectedEnquiryId === invalidatingId) {
        setSelectedEnquiryId(null);
      }
    },
  });

  // Start Application from Enquiry write
  const startApplication = useWrite({
    write: (enq: EnquiryDetail) => {
      const parts = (enq.child_name || enq.enquirer_name).trim().split(" ");
      const firstName = parts[0] || "Applicant";
      const lastName = parts.slice(1).join(" ") || "Candidate";
      return api.post("/admin/admission/applications", {
        first_name: firstName,
        last_name: lastName,
        date_of_birth: enq.child_dob || "2020-01-01",
        gender: "other",
        class_applying_for: enq.class_of_interest || "Class 1",
        cycle_id: enq.cycle_id,
        enquiry_id: enq.id,
        source: enq.source as any,
      } as any);
    },
    invalidates: [
      ["admission-enquiries"],
      ["admission-enquiry-detail", selectedEnquiryId],
      ["admission-applications"],
      ["admission-dashboard", cycleId],
    ],
    onDone: (app: any) => {
      if (app?.id) {
        window.location.hash = "#/admission/applications";
      }
    },
  });

  const enquiries = enquiriesQuery.data ?? [];
  const detail = enquiryDetailQuery.data ?? null;

  return (
    <div className="space-y-6">
      {/* Header & Primary Action */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-ink">Enquiry Register</h1>
        </div>

        <div className="flex items-center gap-3">
          <select
            className={`${inputClass} w-auto font-medium py-1.5`}
            value={activeCycle?.id ?? ""}
            onChange={(e) => setSelectedCycleId(Number(e.target.value))}
          >
            {cycles.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.academic_year})
              </option>
            ))}
          </select>

          <ActionButton
            permission="admission.enquiry.write"
            onClick={() => setShowCreateModal(true)}
          >
            + Log enquiry
          </ActionButton>
        </div>
      </div>

      {/* Search & Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[220px]">
            <input
              className={inputClass}
              placeholder="Search enquirer name, mobile or child name..."
              value={term}
              onChange={(e) => setTerm(e.target.value)}
            />
          </div>

          <select
            className={`${inputClass} w-auto`}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="contacted">Contacted</option>
            <option value="interested">Interested</option>
            <option value="application_form_issued">Form Issued</option>
            <option value="converted">Converted to Application</option>
            <option value="not_interested">Not Interested</option>
            <option value="lost_to_competitor">Lost to Competitor</option>
            <option value="invalid">Invalid</option>
          </select>

          <button
            type="button"
            onClick={() => setOnlyDue(!onlyDue)}
            className={`px-3 py-2 rounded-input text-sm font-medium border transition-colors ${
              onlyDue
                ? "bg-danger text-white border-danger"
                : "bg-surface text-ink-soft border-rule hover:bg-ground"
            }`}
          >
            {onlyDue ? "Showing Due Today / Overdue" : "Filter: Due Today / Overdue"}
          </button>
        </div>
      </Card>

      {/* Enquiries Table */}
      <Card>
        <DataTable<Enquiry>
          loading={enquiriesQuery.isLoading}
          error={enquiriesQuery.error}
          empty={
            term || statusFilter || onlyDue
              ? "No enquiries match the search and filter criteria."
              : "No enquiries logged for this cycle yet. Click '+ Log enquiry' to register walk-ins and phone calls."
          }
          onRowClick={(r) => setSelectedEnquiryId(r.id)}
          columns={[
            {
              key: "id",
              header: "Enquiry ID",
              render: (r) => <span className="font-mono text-xs">ENQ-{r.id}</span>,
            },
            {
              key: "enquirer",
              header: "Enquirer & Contact",
              render: (r) => (
                <div>
                  <p className="font-semibold text-ink">{r.enquirer_name}</p>
                  <p className="text-xs text-ink-soft tabular">{r.mobile}</p>
                </div>
              ),
            },
            {
              key: "child",
              header: "Child & Class",
              render: (r) => (
                <div>
                  <p className="text-ink font-medium">
                    {r.child_name || <span className="text-ink-faint">Not specified</span>}
                  </p>
                  <p className="text-xs text-ink-soft">
                    {r.class_of_interest || "Class unspecified"}
                  </p>
                </div>
              ),
            },
            {
              key: "source",
              header: "Lead Source",
              render: (r) => (
                <span className="capitalize text-xs text-ink-soft">
                  {r.source.replace(/_/g, " ")}
                </span>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (r) => (
                <Pill
                  status={
                    r.status === "converted"
                      ? "present"
                      : r.status === "invalid" || r.status === "not_interested"
                        ? "absent"
                        : "pending"
                  }
                >
                  {r.status.replace(/_/g, " ").toUpperCase()}
                </Pill>
              ),
            },
            {
              key: "follow_up",
              header: "Next Follow-up",
              render: (r) => {
                const overdue = isOverdue(r.next_follow_up_on);
                const isClosed =
                  r.status === "converted" ||
                  r.status === "invalid" ||
                  r.status === "not_interested";
                return (
                  <span
                    className={`tabular text-xs font-medium ${
                      !isClosed && overdue ? "text-danger font-semibold" : "text-ink-soft"
                    }`}
                  >
                    {asDate(r.next_follow_up_on)}
                    {!isClosed && overdue && " (Due)"}
                  </span>
                );
              },
            },
            {
              key: "converted",
              header: "Conversion",
              render: (r) =>
                r.converted_application_id ? (
                  <a
                    href="#/admission/applications"
                    className="text-primary hover:underline text-xs font-medium"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Application #{r.converted_application_id}
                  </a>
                ) : (
                  <span className="text-xs text-ink-faint">—</span>
                ),
            },
            {
              key: "actions",
              header: "",
              align: "right",
              render: (r) => (
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    className="text-xs text-ink-soft hover:text-ink font-medium px-2 py-1 rounded border border-rule hover:bg-ground transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      setPrintingEnquiry(r);
                    }}
                  >
                    Print slip
                  </button>
                  <button
                    type="button"
                    className="text-xs text-primary hover:underline font-medium"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedEnquiryId(r.id);
                    }}
                  >
                    Timeline →
                  </button>
                </div>
              ),
            },
          ]}
          rows={enquiries}
        />
      </Card>

      {/* Modal: Quick Log Enquiry */}
      {showCreateModal && (
        <Modal
          title="Log Walk-in / Phone Enquiry"
          onClose={() => setShowCreateModal(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createEnquiry.run(createForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField
                label="Enquirer Name"
                error={createEnquiry.fields["enquirer_name"]}
              >
                <input
                  required
                  className={inputClass}
                  placeholder="e.g. Ramesh Kumar"
                  value={createForm.enquirer_name}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      enquirer_name: e.target.value,
                    })
                  }
                />
              </FormField>
              <FormField label="Mobile Number" error={createEnquiry.fields["mobile"]}>
                <input
                  required
                  className={inputClass}
                  placeholder="e.g. 9876543210"
                  value={createForm.mobile}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, mobile: e.target.value })
                  }
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Email (Optional)" error={createEnquiry.fields["email"]}>
                <input
                  type="email"
                  className={inputClass}
                  placeholder="parent@example.com"
                  value={createForm.email}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, email: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Lead Source">
                <select
                  className={inputClass}
                  value={createForm.source}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, source: e.target.value })
                  }
                >
                  <option value="walk_in">Walk-in Counter</option>
                  <option value="phone">Phone Call</option>
                  <option value="website">School Website</option>
                  <option value="referral">Parent / Staff Referral</option>
                  <option value="social_media">Social Media</option>
                  <option value="hoarding">Hoarding / Billboard</option>
                  <option value="digital_ad">Online / Digital Ad</option>
                  <option value="other">Other</option>
                </select>
              </FormField>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <FormField label="Child's Name (Optional)">
                <input
                  className={inputClass}
                  placeholder="e.g. Aarav Kumar"
                  value={createForm.child_name}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, child_name: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Child's DOB">
                <input
                  type="date"
                  className={inputClass}
                  value={createForm.child_dob}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, child_dob: e.target.value })
                  }
                />
              </FormField>
              <FormField label="Class of Interest">
                <input
                  className={inputClass}
                  placeholder="e.g. Class 1"
                  value={createForm.class_of_interest}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      class_of_interest: e.target.value,
                    })
                  }
                />
              </FormField>
            </div>

            <FormField label="Next Follow-up Due On">
              <input
                type="date"
                className={inputClass}
                value={createForm.next_follow_up_on}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    next_follow_up_on: e.target.value,
                  })
                }
              />
            </FormField>

            <FormError error={createEnquiry.error} />

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
                disabled={createEnquiry.busy}
                className="rounded-input bg-primary text-white text-sm font-medium px-4 py-2 hover:bg-primary-dark disabled:opacity-50"
              >
                {createEnquiry.busy ? "Saving..." : "Log Enquiry"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal / Drawer: Enquiry Detail & Interaction Timeline */}
      {selectedEnquiryId !== null && (
        <Modal
          title={`Enquiry: ENQ-${selectedEnquiryId}`}
          wide
          onClose={() => setSelectedEnquiryId(null)}
        >
          {enquiryDetailQuery.isLoading ? (
            <Empty>Loading enquiry details...</Empty>
          ) : enquiryDetailQuery.error ? (
            <ErrorState error={enquiryDetailQuery.error} />
          ) : detail ? (
            <div className="space-y-6">
              {/* Top Details Banner */}
              <div className="bg-ground rounded-input p-4 border border-rule flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-ink">
                      {detail.enquirer_name}
                    </h3>
                    <Pill status={detail.status === "converted" ? "present" : "pending"}>
                      {detail.status.replace(/_/g, " ").toUpperCase()}
                    </Pill>
                  </div>
                  <p className="text-sm text-ink-soft mt-1">
                    Phone: <span className="font-semibold tabular">{detail.mobile}</span>
                    {detail.email && ` | Email: ${detail.email}`}
                  </p>
                  <p className="text-xs text-ink-faint mt-0.5">
                    Child: {detail.child_name || "Unspecified"} | Class:{" "}
                    {detail.class_of_interest || "Unspecified"} | Source: {detail.source}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-input text-xs font-medium border border-rule bg-surface text-ink hover:bg-ground transition-colors flex items-center gap-1.5"
                    onClick={() => setPrintingEnquiry(detail)}
                  >
                    Print slip (A5)
                  </button>

                  {!detail.converted_application_id && (
                    <ActionButton
                      permission="admission.application.write"
                      variant="primary"
                      onClick={() => startApplication.run(detail)}
                      disabled={startApplication.busy}
                    >
                      {startApplication.busy ? "Starting..." : "Start application →"}
                    </ActionButton>
                  )}

                  {detail.status !== "invalid" && (
                    <ActionButton
                      permission="admission.enquiry.write"
                      variant="danger"
                      onClick={() => setInvalidatingId(detail.id)}
                    >
                      Mark invalid
                    </ActionButton>
                  )}
                </div>
              </div>

              {/* Log new interaction section */}
              <Card title="Log Follow-up Interaction">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    logInteraction.run(interactionForm);
                  }}
                  className="space-y-3"
                >
                  <div className="grid grid-cols-3 gap-3">
                    <FormField label="Contact Channel">
                      <select
                        className={inputClass}
                        value={interactionForm.channel}
                        onChange={(e) =>
                          setInteractionForm({
                            ...interactionForm,
                            channel: e.target.value,
                          })
                        }
                      >
                        <option value="phone">Phone Call</option>
                        <option value="visit">Campus Visit / Tour</option>
                        <option value="whatsapp">WhatsApp</option>
                        <option value="email">Email</option>
                        <option value="sms">SMS</option>
                      </select>
                    </FormField>

                    <FormField label="Outcome / Status Update">
                      <select
                        className={inputClass}
                        value={interactionForm.outcome}
                        onChange={(e) =>
                          setInteractionForm({
                            ...interactionForm,
                            outcome: e.target.value,
                          })
                        }
                      >
                        <option value="contacted">Contacted</option>
                        <option value="interested">Interested</option>
                        <option value="application_form_issued">Form Issued</option>
                        <option value="not_interested">Not Interested</option>
                        <option value="lost_to_competitor">Lost to Competitor</option>
                      </select>
                    </FormField>

                    <FormField label="Next Follow-up Date">
                      <input
                        type="date"
                        className={inputClass}
                        value={interactionForm.next_follow_up_on}
                        onChange={(e) =>
                          setInteractionForm({
                            ...interactionForm,
                            next_follow_up_on: e.target.value,
                          })
                        }
                      />
                    </FormField>
                  </div>

                  <FormField label="Conversation Notes">
                    <textarea
                      required
                      className={inputClass}
                      rows={2}
                      placeholder="Notes from call or campus tour..."
                      value={interactionForm.notes}
                      onChange={(e) =>
                        setInteractionForm({
                          ...interactionForm,
                          notes: e.target.value,
                        })
                      }
                    />
                  </FormField>

                  <FormError error={logInteraction.error} />

                  <div className="flex justify-end pt-1">
                    <ActionButton
                      permission="admission.enquiry.write"
                      onClick={() => logInteraction.run(interactionForm)}
                      disabled={logInteraction.busy || !interactionForm.notes.trim()}
                    >
                      {logInteraction.busy ? "Recording..." : "Record interaction"}
                    </ActionButton>
                  </div>
                </form>
              </Card>

              {/* Interaction History Timeline */}
              <Card title="Interaction History Log">
                {detail.interactions.length === 0 ? (
                  <Empty>No interactions logged yet. Log the first call above.</Empty>
                ) : (
                  <div className="space-y-3">
                    {detail.interactions.map((it) => (
                      <div
                        key={it.id}
                        className="p-3 bg-ground rounded-input border border-rule space-y-1"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold uppercase tracking-wider text-primary">
                            {it.channel}
                          </span>
                          <span className="text-ink-faint tabular">
                            {new Date(it.occurred_at).toLocaleString("en-GB")}
                          </span>
                        </div>
                        {it.notes && (
                          <p className="text-sm text-ink">{it.notes}</p>
                        )}
                        {it.outcome && (
                          <p className="text-xs text-ink-soft">
                            Outcome status:{" "}
                            <span className="font-medium text-ink">
                              {it.outcome.replace(/_/g, " ")}
                            </span>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          ) : null}
        </Modal>
      )}

      {/* Confirm Dialog: Mark Enquiry Invalid */}
      {invalidatingId !== null && (
        <ConfirmDialog
          title="Mark Enquiry as Invalid"
          intent="Closing this enquiry as invalid records that the contact was a wrong number, spam, or fake, while preserving the lead source for audit."
          confirmLabel="Mark as Invalid"
          busy={markInvalid.busy}
          error={markInvalid.error}
          onConfirm={(reason) =>
            markInvalid.run({ id: invalidatingId, reason })
          }
          onClose={() => setInvalidatingId(null)}
        />
      )}

      {/* Printable Enquiry Slip Modal */}
      {printingEnquiry && (
        <PrintableEnquirySlip
          enquiry={printingEnquiry}
          cycleName={activeCycle?.name}
          onClose={() => setPrintingEnquiry(null)}
        />
      )}
    </div>
  );
}
