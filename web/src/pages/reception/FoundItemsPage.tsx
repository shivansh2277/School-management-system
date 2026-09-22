import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Can } from "../../components/Can";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../../components/ui";

export interface FoundItem {
  id: number;
  school_id: number;
  item_name: string;
  category: string;
  description: string | null;
  found_location: string;
  found_date: string;
  found_time: string | null;
  recorded_by_name: string;
  photo_url: string | null;
  status: "reported" | "broadcasted" | "collected";
  broadcasted_at: string | null;
  claimed_by_student_id: number | null;
  claimed_by_student_name: string | null;
  claimed_by_admission_no: string | null;
  claimed_by_class_name: string | null;
  handover_photo_url: string | null;
  handover_notes: string | null;
  collected_at: string | null;
  collected_by_staff_name: string | null;
  created_at: string;
}

export function FoundItemsPage() {
  const queryClient = useQueryClient();
  const { me } = useAuth();

  const [statusFilter, setStatusFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [claimTargetItem, setClaimTargetItem] = useState<FoundItem | null>(null);
  const [viewDetailItem, setViewDetailItem] = useState<FoundItem | null>(null);

  // Form states
  const [createForm, setCreateForm] = useState({
    item_name: "",
    category: "accessories",
    description: "",
    found_location: "",
    found_date: new Date().toISOString().slice(0, 10),
    found_time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    photo_url: "",
  });

  const [claimForm, setClaimForm] = useState({
    claimed_by_student_id: null as number | null,
    claimed_by_student_name: "",
    claimed_by_admission_no: "",
    claimed_by_class_name: "",
    handover_photo_url: "",
    handover_notes: "",
  });

  const [studentSearchQuery, setStudentSearchQuery] = useState("");

  // Queries
  const itemsQuery = useQuery({
    queryKey: ["found-items", statusFilter, search],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter) params.append("status", statusFilter);
      if (search) params.append("search", search);
      const q = params.toString() ? `?${params.toString()}` : "";
      return api.get(`/admin/reception/found-items${q}` as any) as Promise<FoundItem[]>;
    },
  });

  const studentSearchQueryResults = useQuery({
    queryKey: ["student-search-found", studentSearchQuery],
    queryFn: () => {
      return api.get(`/admin/reception/students/search?q=${encodeURIComponent(studentSearchQuery)}` as any) as Promise<
        { id: number; admission_no: string; name: string; class_name: string }[]
      >;
    },
    enabled: studentSearchQuery.trim().length >= 2,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: typeof createForm) => {
      return api.post("/admin/reception/found-items" as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["found-items"] });
      setShowCreateModal(false);
      setCreateForm({
        item_name: "",
        category: "accessories",
        description: "",
        found_location: "",
        found_date: new Date().toISOString().slice(0, 10),
        found_time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
        photo_url: "",
      });
    },
  });

  const broadcastMutation = useMutation({
    mutationFn: (itemId: number) => {
      return api.post(`/admin/reception/found-items/${itemId}/broadcast` as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["found-items"] });
    },
  });

  const collectMutation = useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: typeof claimForm }) => {
      return api.post(`/admin/reception/found-items/${itemId}/collect` as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["found-items"] });
      setClaimTargetItem(null);
      setClaimForm({
        claimed_by_student_id: null,
        claimed_by_student_name: "",
        claimed_by_admission_no: "",
        claimed_by_class_name: "",
        handover_photo_url: "",
        handover_notes: "",
      });
      setStudentSearchQuery("");
    },
  });

  const items = itemsQuery.data || [];
  const totalCount = items.length;
  const broadcastedCount = items.filter((i) => i.status === "broadcasted").length;
  const collectedCount = items.filter((i) => i.status === "collected").length;

  const selectStudentForClaim = (s: { id: number; admission_no: string; name: string; class_name: string }) => {
    setClaimForm((prev) => ({
      ...prev,
      claimed_by_student_id: s.id,
      claimed_by_admission_no: s.admission_no,
      claimed_by_student_name: s.name,
      claimed_by_class_name: s.class_name,
    }));
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Found & Lost — Found Items Register</h1>
          <p className="text-sm text-ink-faint">
            Record found items, broadcast alerts to students, verify claimant identity, and manage handovers.
          </p>
        </div>
        <Can permission="reception.found_items.write">
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-semibold rounded-pill shadow-sm hover:opacity-90 transition"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            Record Found Item
          </button>
        </Can>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Found Items" value={totalCount} hint="All recorded items in register" />
        <StatCard label="Broadcasted / Active" value={broadcastedCount} hint="Notification sent to all students" />
        <StatCard label="Successfully Claimed" value={collectedCount} hint="Handover photo & identity verified" />
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center mb-4">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs font-semibold text-ink-faint uppercase">Filter:</span>
            <div className="flex gap-1">
              {[
                { label: "All Items", val: "" },
                { label: "Reported", val: "reported" },
                { label: "Broadcasted", val: "broadcasted" },
                { label: "Collected", val: "collected" },
              ].map((btn) => (
                <button
                  key={btn.val}
                  type="button"
                  onClick={() => setStatusFilter(btn.val)}
                  className={`px-3 py-1 rounded-pill text-xs font-medium transition ${
                    statusFilter === btn.val
                      ? "bg-primary text-white"
                      : "bg-ground text-ink-faint hover:text-ink hover:bg-ground-deep"
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>
          <div className="w-full sm:w-72">
            <input
              type="text"
              placeholder="Search item, location, student..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        {/* Table */}
        <DataTable<FoundItem>
          columns={[
            {
              key: "item",
              header: "Item & Description",
              render: (row) => (
                <div className="flex items-center gap-3">
                  {row.photo_url ? (
                    <img
                      src={row.photo_url}
                      alt={row.item_name}
                      className="w-10 h-10 rounded object-cover border border-rule"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded bg-ground flex items-center justify-center text-ink-faint border border-rule">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="1.5"
                          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                        />
                      </svg>
                    </div>
                  )}
                  <div>
                    <span className="font-semibold text-ink block">{row.item_name}</span>
                    <span className="text-xs text-ink-faint capitalize">{row.category}</span>
                    {row.description && (
                      <span className="text-xs text-ink-faint block truncate max-w-xs">{row.description}</span>
                    )}
                  </div>
                </div>
              ),
            },
            {
              key: "found_at",
              header: "Found Location & Date",
              render: (row) => (
                <div>
                  <span className="font-medium text-ink block">{row.found_location}</span>
                  <span className="text-xs text-ink-faint">
                    {new Date(row.found_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                    {row.found_time ? ` at ${row.found_time}` : ""}
                  </span>
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => (
                <div>
                  <Pill
                    status={
                      row.status === "collected"
                        ? "active"
                        : row.status === "broadcasted"
                        ? "in_progress"
                        : "pending"
                    }
                  >
                    {row.status.toUpperCase()}
                  </Pill>
                  {row.status === "broadcasted" && (
                    <span className="block text-[10px] text-ink-faint mt-0.5">Alerts Broadcasted</span>
                  )}
                </div>
              ),
            },
            {
              key: "claimant",
              header: "Claimant & Handover",
              render: (row) => (
                <div>
                  {row.status === "collected" ? (
                    <div>
                      <span className="font-semibold text-emerald-800 block">{row.claimed_by_student_name}</span>
                      <span className="text-xs text-ink-faint">
                        Adm: {row.claimed_by_admission_no} • {row.claimed_by_class_name || ""}
                      </span>
                      <span className="block text-[10px] text-ink-faint">
                        Handover: {row.collected_at ? new Date(row.collected_at).toLocaleDateString("en-IN") : "Done"}
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-ink-faint italic">Awaiting Claimant</span>
                  )}
                </div>
              ),
            },
            {
              key: "actions",
              header: "Actions",
              align: "right",
              render: (row) => (
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setViewDetailItem(row)}
                    className="px-2.5 py-1 text-xs font-medium text-ink-faint hover:text-ink hover:bg-ground rounded transition"
                  >
                    View
                  </button>

                  {row.status === "reported" && (
                    <Can permission="reception.found_items.write">
                      <button
                        type="button"
                        onClick={() => broadcastMutation.mutate(row.id)}
                        disabled={broadcastMutation.isPending}
                        className="px-2.5 py-1 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition"
                      >
                        Broadcast
                      </button>
                    </Can>
                  )}

                  {row.status !== "collected" && (
                    <Can permission="reception.found_items.collect">
                      <button
                        type="button"
                        onClick={() => setClaimTargetItem(row)}
                        className="px-2.5 py-1 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded transition"
                      >
                        Claim & Handover
                      </button>
                    </Can>
                  )}
                </div>
              ),
            },
          ]}
          rows={items}
          empty="No found items match the selected filter."
          loading={itemsQuery.isLoading}
          error={itemsQuery.error}
        />
      </Card>

      {/* Modal: Record Found Item */}
      {showCreateModal && (
        <Modal title="Record Found Object" onClose={() => setShowCreateModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate(createForm);
            }}
            className="space-y-4"
          >
            <FormField label="Item Name / Title">
              <input
                type="text"
                required
                placeholder="e.g. Stainless Steel Water Bottle, Titan Watch"
                value={createForm.item_name}
                onChange={(e) => setCreateForm({ ...createForm, item_name: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Category">
                <select
                  value={createForm.category}
                  onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                  className={inputClass}
                >
                  <option value="accessories">Accessories / Bottles</option>
                  <option value="electronics">Electronics / Watches</option>
                  <option value="clothing">Clothing / Uniform / Shoes</option>
                  <option value="stationery">Books / Stationery / Bag</option>
                  <option value="id_cards">ID Card / Documents</option>
                  <option value="other">Other Items</option>
                </select>
              </FormField>

              <FormField label="Found Location">
                <input
                  type="text"
                  required
                  placeholder="e.g. Library, Ground, Table 4"
                  value={createForm.found_location}
                  onChange={(e) => setCreateForm({ ...createForm, found_location: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Found Date">
                <input
                  type="date"
                  required
                  value={createForm.found_date}
                  onChange={(e) => setCreateForm({ ...createForm, found_date: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Found Time">
                <input
                  type="text"
                  placeholder="e.g. 11:30 AM"
                  value={createForm.found_time}
                  onChange={(e) => setCreateForm({ ...createForm, found_time: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <FormField label="Photo Image URL / Storage Path">
              <input
                type="text"
                placeholder="https://... or uploaded image URL"
                value={createForm.photo_url}
                onChange={(e) => setCreateForm({ ...createForm, photo_url: e.target.value })}
                className={inputClass}
              />
              <span className="text-[11px] text-ink-faint">
                Upload or link a photograph of the found object for student identification.
              </span>
            </FormField>

            <FormField label="Item Description & Identifying Marks">
              <textarea
                rows={3}
                placeholder="Color, brand name, stickers, scratches, or unique markings..."
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="px-5 py-2 bg-primary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition shadow-sm"
              >
                {createMutation.isPending ? "Recording..." : "Save Found Item"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Claim & Mark Collected */}
      {claimTargetItem && (
        <Modal
          title={`Claim & Handover: ${claimTargetItem.item_name}`}
          onClose={() => setClaimTargetItem(null)}
          wide
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!claimForm.claimed_by_student_name) {
                alert("Please select or enter the claiming student's details.");
                return;
              }
              collectMutation.mutate({ itemId: claimTargetItem.id, data: claimForm });
            }}
            className="space-y-4"
          >
            <div className="p-3 bg-blue-50/70 border border-blue-200 rounded text-xs text-blue-900">
              <p className="font-semibold">Step 5 & 6: Student Identity Verification & Handover Photo</p>
              <p className="mt-0.5">
                Verify the student's identity against school enrollment records before handing over the item.
                Record receiver details and take/link a handover photograph as proof of collection.
              </p>
            </div>

            {/* Student Search */}
            <div className="border border-rule rounded p-3 bg-ground/50">
              <FormField label="Search Enrolled Student">
                <input
                  type="text"
                  placeholder="Type admission number (e.g. 2024000001) or student name..."
                  value={studentSearchQuery}
                  onChange={(e) => setStudentSearchQuery(e.target.value)}
                  className={inputClass}
                />
              </FormField>

              {studentSearchQueryResults.data && studentSearchQueryResults.data.length > 0 && (
                <div className="mt-2 border border-rule rounded bg-surface max-h-36 overflow-y-auto divide-y divide-rule">
                  {studentSearchQueryResults.data.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => selectStudentForClaim(s)}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-ground flex justify-between items-center"
                    >
                      <div>
                        <span className="font-semibold text-ink">{s.name}</span>
                        <span className="text-ink-faint ml-2 font-mono">({s.admission_no})</span>
                      </div>
                      <span className="text-ink-faint font-medium">{s.class_name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Selected Claimant Details */}
            <div className="grid grid-cols-3 gap-3">
              <FormField label="Claimant Name">
                <input
                  type="text"
                  required
                  placeholder="Student Full Name"
                  value={claimForm.claimed_by_student_name}
                  onChange={(e) => setClaimForm({ ...claimForm, claimed_by_student_name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Admission Number">
                <input
                  type="text"
                  required
                  placeholder="e.g. 2024000001"
                  value={claimForm.claimed_by_admission_no}
                  onChange={(e) => setClaimForm({ ...claimForm, claimed_by_admission_no: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Class / Section">
                <input
                  type="text"
                  placeholder="e.g. Class 10-A"
                  value={claimForm.claimed_by_class_name}
                  onChange={(e) => setClaimForm({ ...claimForm, claimed_by_class_name: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            {/* Handover Photo & Notes */}
            <FormField label="Handover Photo URL / Verification Snapshot">
              <input
                type="text"
                placeholder="https://... photo of student receiving object"
                value={claimForm.handover_photo_url}
                onChange={(e) => setClaimForm({ ...claimForm, handover_photo_url: e.target.value })}
                className={inputClass}
              />
              <span className="text-[11px] text-ink-faint">
                Photo of the student receiving the object at the reception desk.
              </span>
            </FormField>

            <FormField label="Handover Notes / Verification Remarks">
              <textarea
                rows={2}
                placeholder="Claimant verified by ID card, confirmed bottle contents / unique mark..."
                value={claimForm.handover_notes}
                onChange={(e) => setClaimForm({ ...claimForm, handover_notes: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setClaimTargetItem(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={collectMutation.isPending}
                className="px-5 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-pill hover:bg-emerald-700 transition shadow-sm"
              >
                {collectMutation.isPending ? "Confirming..." : "Confirm Handover & Mark Collected"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: View Item Detail */}
      {viewDetailItem && (
        <Modal title={`Found Item: ${viewDetailItem.item_name}`} onClose={() => setViewDetailItem(null)}>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-rule">
              <span className="font-semibold text-sm text-ink">{viewDetailItem.item_name}</span>
              <Pill status={viewDetailItem.status === "collected" ? "active" : "pending"}>
                {viewDetailItem.status.toUpperCase()}
              </Pill>
            </div>

            <div className="grid grid-cols-2 gap-2 text-ink">
              <div>
                <span className="text-ink-faint block text-[10px] uppercase">Category</span>
                <span className="font-medium capitalize">{viewDetailItem.category}</span>
              </div>
              <div>
                <span className="text-ink-faint block text-[10px] uppercase">Found Location</span>
                <span className="font-medium">{viewDetailItem.found_location}</span>
              </div>
              <div>
                <span className="text-ink-faint block text-[10px] uppercase">Found Date & Time</span>
                <span className="font-medium">
                  {viewDetailItem.found_date} {viewDetailItem.found_time ? `(${viewDetailItem.found_time})` : ""}
                </span>
              </div>
              <div>
                <span className="text-ink-faint block text-[10px] uppercase">Recorded By</span>
                <span className="font-medium">{viewDetailItem.recorded_by_name}</span>
              </div>
            </div>

            {viewDetailItem.description && (
              <div>
                <span className="text-ink-faint block text-[10px] uppercase">Description</span>
                <p className="font-medium text-ink mt-0.5">{viewDetailItem.description}</p>
              </div>
            )}

            {viewDetailItem.photo_url && (
              <div>
                <span className="text-ink-faint block text-[10px] uppercase mb-1">Found Object Photo</span>
                <img
                  src={viewDetailItem.photo_url}
                  alt={viewDetailItem.item_name}
                  className="w-full max-h-48 object-cover rounded border border-rule"
                />
              </div>
            )}

            {viewDetailItem.status === "collected" && (
              <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded">
                <span className="font-bold text-emerald-950 uppercase text-[10px] block mb-1">
                  Collection & Handover Record
                </span>
                <div className="space-y-1 text-emerald-900">
                  <div>Claimant: {viewDetailItem.claimed_by_student_name} ({viewDetailItem.claimed_by_admission_no})</div>
                  <div>Class: {viewDetailItem.claimed_by_class_name || "—"}</div>
                  <div>Handover By: {viewDetailItem.collected_by_staff_name}</div>
                  <div>Date: {viewDetailItem.collected_at ? new Date(viewDetailItem.collected_at).toLocaleString("en-IN") : "—"}</div>
                  {viewDetailItem.handover_notes && <div>Notes: {viewDetailItem.handover_notes}</div>}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
