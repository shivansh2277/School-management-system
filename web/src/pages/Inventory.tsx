import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { ActionButton, Can } from "../components/Can";
import {
  Card,
  DataTable,
  Empty,
  ErrorState,
  FormField,
  FormError,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";

type Tab = "catalogue" | "requests" | "discrepancies";

const CATEGORIES = [
  "All",
  "Science Lab",
  "Mathematics",
  "Art & Craft",
  "Stationery",
  "Medical Room",
] as const;

export function Inventory() {
  const qc = useQueryClient();
  const { can } = useAuth();

  const [activeTab, setActiveTab] = useState<Tab>("catalogue");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [search, setSearch] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [requestStatusFilter, setRequestStatusFilter] = useState("pending");

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [adjustingItem, setAdjustingItem] = useState<{
    id: number;
    name: string;
    current_quantity: number;
    location: string;
    unit: string;
    has_discrepancy: boolean;
    discrepancy_notes?: string | null;
  } | null>(null);
  const [flaggingItem, setFlaggingItem] = useState<{
    id?: number;
    name?: string;
    category?: string;
    location?: string;
  } | null>(null);
  const [showFlagModal, setShowFlagModal] = useState(false);
  const [decidingRequest, setDecidingRequest] = useState<{
    id: number;
    item_name: string;
    action: "approved" | "rejected";
  } | null>(null);

  // Queries
  const statsQuery = useQuery({
    queryKey: ["inventory", "stats"],
    queryFn: () => api.get("/admin/inventory/stats"),
  });

  const itemsParams = useMemo(() => {
    const p = new URLSearchParams();
    if (selectedCategory && selectedCategory !== "All") p.set("category", selectedCategory);
    if (lowStockOnly) p.set("low_stock_only", "true");
    if (activeTab === "discrepancies") p.set("has_discrepancy_only", "true");
    if (search.trim()) p.set("search", search.trim());
    const qs = p.toString();
    return qs ? `?${qs}` : "";
  }, [selectedCategory, lowStockOnly, activeTab, search]);

  const itemsQuery = useQuery({
    queryKey: [
      "inventory",
      "items",
      selectedCategory,
      lowStockOnly,
      activeTab === "discrepancies",
      search,
    ],
    queryFn: () => api.get("/admin/inventory/items", itemsParams) as Promise<any[]>,
  });

  const requestsParams = useMemo(() => {
    const p = new URLSearchParams();
    if (requestStatusFilter && requestStatusFilter !== "all") p.set("status", requestStatusFilter);
    const qs = p.toString();
    return qs ? `?${qs}` : "";
  }, [requestStatusFilter]);

  const requestsQuery = useQuery({
    queryKey: ["inventory", "requests", requestStatusFilter],
    queryFn: () => api.get("/admin/inventory/requests", requestsParams) as Promise<any[]>,
  });

  const stats = statsQuery.data;
  const items = useMemo(() => itemsQuery.data ?? [], [itemsQuery.data]);
  const requests = useMemo(() => requestsQuery.data ?? [], [requestsQuery.data]);
  const discrepancies = useMemo(
    () => (itemsQuery.data ?? []).filter((it: any) => it.has_discrepancy),
    [itemsQuery.data],
  );

  return (
    <div className="space-y-6">
      {/* Page Heading — clean and concise per owner directive */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Stock & Inventory</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setFlaggingItem(null);
              setShowFlagModal(true);
            }}
            className="rounded-input border border-primary text-primary px-3 py-1.5 text-sm font-medium hover:bg-primary/10 transition-colors"
          >
            Flag Diminishing Stock
          </button>
          <Can permission="inventory.item.write">
            <button
              type="button"
              onClick={() => setShowAddModal(true)}
              className="rounded-input bg-primary text-white px-3 py-1.5 text-sm font-medium hover:bg-primary-dark transition-colors"
            >
              + Add Item
            </button>
          </Can>
        </div>
      </header>

      {/* Overview Highlights (3 StatCards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          label="Low-stock items"
          value={stats?.low_stock_count ?? "—"}
          hint="Require review or reorder"
        />
        <StatCard
          label="Pending approvals"
          value={stats?.pending_approvals_count ?? "—"}
          hint="Purchase and issue requests"
        />
        <StatCard
          label="Stock discrepancies"
          value={stats?.discrepancies_count ?? "—"}
          hint="Awaiting investigation"
        />
      </div>

      {/* Critical Stock Alerts Banner */}
      {stats?.critical_alerts && stats.critical_alerts.length > 0 && (
        <section className="bg-amber-500/10 border border-amber-500/30 rounded-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-danger animate-pulse" />
              <h2 className="text-sm font-semibold text-ink">Critical stock alerts</h2>
            </div>
            <span className="text-xs font-medium text-danger">Action required</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {stats.critical_alerts.map((alert: any, idx: number) => (
              <div
                key={idx}
                className="bg-surface rounded-card p-3.5 border border-rule flex flex-col justify-between shadow-sm"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-ink leading-tight">{alert.title}</p>
                    <Pill status={alert.level === "critical" ? "voided" : "pending"}>
                      {alert.level === "critical" ? "Critical" : "Low stock"}
                    </Pill>
                  </div>
                  <p className="text-xs text-ink-soft mt-1 font-medium">{alert.subtitle}</p>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-rule">
                  <span className="text-ink-faint">
                    {alert.current_quantity} / {alert.min_quantity} {alert.unit}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setFlaggingItem({
                        id: alert.item_id,
                        name: alert.title,
                        category: alert.category,
                        location: alert.location,
                      });
                      setShowFlagModal(true);
                    }}
                    className="text-primary font-semibold hover:underline"
                  >
                    Reorder / Flag &rarr;
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-rule flex gap-6 text-sm font-medium">
        <button
          type="button"
          onClick={() => setActiveTab("catalogue")}
          className={`pb-3 transition-colors ${
            activeTab === "catalogue"
              ? "border-b-2 border-primary text-primary font-semibold"
              : "text-ink-soft hover:text-ink"
          }`}
        >
          Stock Catalogue ({items.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("requests")}
          className={`pb-3 flex items-center gap-1.5 transition-colors ${
            activeTab === "requests"
              ? "border-b-2 border-primary text-primary font-semibold"
              : "text-ink-soft hover:text-ink"
          }`}
        >
          <span>Requests & Approvals</span>
          {stats?.pending_approvals_count !== undefined && (
            <span className="px-1.5 py-0.2 rounded-full text-xs bg-amber-500/20 text-amber-800 font-bold">
              {stats.pending_approvals_count}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("discrepancies")}
          className={`pb-3 flex items-center gap-1.5 transition-colors ${
            activeTab === "discrepancies"
              ? "border-b-2 border-primary text-primary font-semibold"
              : "text-ink-soft hover:text-ink"
          }`}
        >
          <span>Stock Discrepancies</span>
          {stats?.discrepancies_count !== undefined && (
            <span className="px-1.5 py-0.2 rounded-full text-xs bg-danger/20 text-danger font-bold">
              {stats.discrepancies_count}
            </span>
          )}
        </button>
      </div>

      {/* Tab 1: Catalogue */}
      {activeTab === "catalogue" && (
        <Card>
          <div className="space-y-4">
            {/* Filter and search bar */}
            <div className="flex flex-col lg:flex-row gap-3 items-start lg:items-center justify-between">
              {/* Category filter pills */}
              <div className="flex flex-wrap gap-1.5">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSelectedCategory(cat)}
                    className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                      selectedCategory === cat
                        ? "bg-primary text-white"
                        : "bg-surface text-ink-soft border border-rule hover:bg-ground"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Search and low-stock checkbox */}
              <div className="flex items-center gap-3 w-full lg:w-auto">
                <input
                  type="text"
                  placeholder="Search item, room, chemical..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className={`${inputClass} w-full sm:w-64`}
                />
                <label className="flex items-center gap-2 text-xs text-ink whitespace-nowrap cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={lowStockOnly}
                    onChange={(e) => setLowStockOnly(e.target.checked)}
                    className="rounded text-primary focus:ring-primary h-4 w-4"
                  />
                  <span>Low stock only</span>
                </label>
              </div>
            </div>

            {/* Catalogue Table */}
            <DataTable
              loading={itemsQuery.isLoading}
              error={itemsQuery.error}
              empty="No inventory items found matching your filters."
              columns={[
                {
                  key: "name",
                  header: "Item Name",
                  render: (row: any) => (
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-ink">{row.name}</span>
                        {row.is_critical && (
                          <span className="text-[10px] bg-danger/10 text-danger px-1.5 py-0.5 rounded font-semibold uppercase">
                            Critical
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-ink-faint">{row.category}</span>
                    </div>
                  ),
                },
                {
                  key: "location",
                  header: "Room / Location",
                  render: (row: any) => (
                    <span className="font-medium text-ink-soft">{row.location}</span>
                  ),
                },
                {
                  key: "stock",
                  header: "Current Stock",
                  render: (row: any) => (
                    <div>
                      <span className="font-semibold text-ink tabular">{row.current_quantity}</span>
                      <span className="text-xs text-ink-faint ml-1">/ min {row.min_quantity}</span>
                      <span className="text-xs text-ink-soft ml-1.5 font-medium">{row.unit}</span>
                    </div>
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row: any) => {
                    if (row.has_discrepancy) {
                      return <Pill status="voided">Discrepancy</Pill>;
                    }
                    if (row.current_quantity <= 0) {
                      return <Pill status="voided">Out of stock</Pill>;
                    }
                    if (row.current_quantity <= row.min_quantity) {
                      return <Pill status="pending">Low stock</Pill>;
                    }
                    return <Pill status="active">In stock</Pill>;
                  },
                },
                {
                  key: "actions",
                  header: "Actions",
                  align: "right",
                  render: (row: any) => (
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setFlaggingItem({
                            id: row.id,
                            name: row.name,
                            category: row.category,
                            location: row.location,
                          });
                          setShowFlagModal(true);
                        }}
                        className="text-xs text-ink-soft hover:text-primary font-medium px-2 py-1 rounded border border-rule hover:border-primary"
                      >
                        Flag / Request
                      </button>
                      <Can permission="inventory.item.write">
                        <button
                          type="button"
                          onClick={() => setAdjustingItem(row)}
                          className="text-xs bg-primary/10 text-primary hover:bg-primary/20 font-medium px-2.5 py-1 rounded"
                        >
                          Adjust
                        </button>
                      </Can>
                    </div>
                  ),
                },
              ]}
              rows={items}
            />
          </div>
        </Card>
      )}

      {/* Tab 2: Requests & Approvals */}
      {activeTab === "requests" && (
        <Card title="Stock Requests & Diminishing Flags">
          <div className="space-y-4">
            {/* Status Filter buttons */}
            <div className="flex gap-2">
              {(["pending", "approved", "rejected", "all"] as const).map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setRequestStatusFilter(st)}
                  className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors ${
                    requestStatusFilter === st
                      ? "bg-primary text-white"
                      : "bg-surface text-ink-soft border border-rule hover:bg-ground"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <DataTable
              loading={requestsQuery.isLoading}
              error={requestsQuery.error}
              empty="No requests or flags in this view."
              columns={[
                {
                  key: "item",
                  header: "Item & Room",
                  render: (row: any) => (
                    <div>
                      <p className="font-medium text-ink">{row.item_name}</p>
                      <p className="text-xs text-ink-faint">
                        {row.location} &middot; {row.category}
                      </p>
                    </div>
                  ),
                },
                {
                  key: "quantity",
                  header: "Qty Needed",
                  render: (row: any) => (
                    <span className="font-semibold text-ink tabular">{row.quantity_requested}</span>
                  ),
                },
                {
                  key: "urgency",
                  header: "Urgency",
                  render: (row: any) => {
                    const statusMap: Record<string, string> = {
                      critical: "voided",
                      urgent: "pending",
                      normal: "active",
                    };
                    return (
                      <Pill status={statusMap[row.urgency] ?? "active"}>
                        {row.urgency.toUpperCase()}
                      </Pill>
                    );
                  },
                },
                {
                  key: "type",
                  header: "Flag Type",
                  render: (row: any) => (
                    <span className="text-xs font-medium text-ink-soft capitalize">
                      {row.flag_type === "diminishing" ? "Teacher flag" : row.flag_type}
                    </span>
                  ),
                },
                {
                  key: "requester",
                  header: "Requested By & Reason",
                  render: (row: any) => (
                    <div className="max-w-md">
                      <p className="text-xs font-semibold text-ink">{row.requested_by_name}</p>
                      <p className="text-xs text-ink-soft line-clamp-2 mt-0.5">{row.reason}</p>
                    </div>
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (row: any) => {
                    const statusMap: Record<string, string> = {
                      pending: "pending",
                      approved: "active",
                      rejected: "voided",
                      fulfilled: "active",
                    };
                    return (
                      <Pill status={statusMap[row.status] ?? "active"}>
                        {row.status.toUpperCase()}
                      </Pill>
                    );
                  },
                },
                {
                  key: "actions",
                  header: "Decision",
                  align: "right",
                  render: (row: any) => {
                    if (row.status !== "pending") {
                      return (
                        <span className="text-xs text-ink-faint italic">
                          {row.decision_note || "Resolved"}
                        </span>
                      );
                    }
                    return (
                      <Can
                        permission="inventory.request.approve"
                        fallback={<span className="text-xs text-ink-faint">Awaiting review</span>}
                      >
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() =>
                              setDecidingRequest({
                                id: row.id,
                                item_name: row.item_name,
                                action: "approved",
                              })
                            }
                            className="text-xs bg-emerald-600 text-white hover:bg-emerald-700 px-2 py-1 rounded font-medium"
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              setDecidingRequest({
                                id: row.id,
                                item_name: row.item_name,
                                action: "rejected",
                              })
                            }
                            className="text-xs bg-danger text-white hover:opacity-90 px-2 py-1 rounded font-medium"
                          >
                            Reject
                          </button>
                        </div>
                      </Can>
                    );
                  },
                },
              ]}
              rows={requests}
            />
          </div>
        </Card>
      )}

      {/* Tab 3: Discrepancies */}
      {activeTab === "discrepancies" && (
        <Card title="Stock Discrepancies Awaiting Investigation">
          <div className="space-y-4">
            <DataTable
              loading={itemsQuery.isLoading}
              error={itemsQuery.error}
              empty="No stock discrepancies currently flagged."
              columns={[
                {
                  key: "item",
                  header: "Item & Room",
                  render: (row: any) => (
                    <div>
                      <p className="font-semibold text-ink">{row.name}</p>
                      <p className="text-xs text-ink-faint">
                        {row.location} &middot; {row.category}
                      </p>
                    </div>
                  ),
                },
                {
                  key: "recorded",
                  header: "Recorded Stock",
                  render: (row: any) => (
                    <div>
                      <span className="font-bold text-ink tabular">{row.current_quantity}</span>
                      <span className="text-xs text-ink-soft ml-1">{row.unit}</span>
                    </div>
                  ),
                },
                {
                  key: "notes",
                  header: "Audit Finding / Investigation Notes",
                  render: (row: any) => (
                    <div className="max-w-md bg-danger/5 border border-danger/20 rounded p-2 text-xs text-danger font-medium">
                      {row.discrepancy_notes || "Physical count mismatch flagged for review"}
                    </div>
                  ),
                },
                {
                  key: "actions",
                  header: "Action",
                  align: "right",
                  render: (row: any) => (
                    <Can permission="inventory.item.write">
                      <button
                        type="button"
                        onClick={() => setAdjustingItem(row)}
                        className="text-xs bg-primary text-white hover:bg-primary-dark px-3 py-1.5 rounded font-medium"
                      >
                        Reconcile & Resolve
                      </button>
                    </Can>
                  ),
                },
              ]}
              rows={discrepancies}
            />
          </div>
        </Card>
      )}

      {/* Modal 1: Flag Diminishing Stock (Available to Teachers & Staff) */}
      {showFlagModal && (
        <FlagStockModal
          initialItem={flaggingItem}
          items={items}
          onClose={() => {
            setShowFlagModal(false);
            setFlaggingItem(null);
          }}
          onSuccess={() => {
            setShowFlagModal(false);
            setFlaggingItem(null);
            qc.invalidateQueries({ queryKey: ["inventory"] });
          }}
        />
      )}

      {/* Modal 2: Adjust Stock Quantity & Log Discrepancies */}
      {adjustingItem && (
        <AdjustStockModal
          item={adjustingItem}
          onClose={() => setAdjustingItem(null)}
          onSuccess={() => {
            setAdjustingItem(null);
            qc.invalidateQueries({ queryKey: ["inventory"] });
          }}
        />
      )}

      {/* Modal 3: Add New Inventory Item */}
      {showAddModal && (
        <AddItemModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            qc.invalidateQueries({ queryKey: ["inventory"] });
          }}
        />
      )}

      {/* Modal 4: Decide on Stock Request */}
      {decidingRequest && (
        <DecideRequestModal
          request={decidingRequest}
          onClose={() => setDecidingRequest(null)}
          onSuccess={() => {
            setDecidingRequest(null);
            qc.invalidateQueries({ queryKey: ["inventory"] });
          }}
        />
      )}
    </div>
  );
}

/** Modal for teachers and staff to flag diminishing stock or request items */
function FlagStockModal({
  initialItem,
  items,
  onClose,
  onSuccess,
}: {
  initialItem: { id?: number; name?: string; category?: string; location?: string } | null;
  items: any[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [selectedItemId, setSelectedItemId] = useState<number | undefined>(initialItem?.id);
  const [itemName, setItemName] = useState(initialItem?.name ?? "");
  const [category, setCategory] = useState(initialItem?.category ?? "Science Lab");
  const [location, setLocation] = useState(initialItem?.location ?? "Science Lab");
  const [quantity, setQuantity] = useState(5);
  const [urgency, setUrgency] = useState<"normal" | "urgent" | "critical">("urgent");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: (body: any) => api.post("/admin/inventory/requests", body),
    onSuccess,
    onError: (err) => setError(err),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;
    mutation.mutate({
      item_id: selectedItemId,
      item_name: itemName.trim(),
      category: category.trim(),
      location: location.trim(),
      quantity_requested: Number(quantity),
      urgency,
      flag_type: "diminishing",
      reason: reason.trim(),
    });
  };

  const handleSelectChange = (idStr: string) => {
    if (!idStr) {
      setSelectedItemId(undefined);
      return;
    }
    const id = Number(idStr);
    setSelectedItemId(id);
    const found = items.find((i) => i.id === id);
    if (found) {
      setItemName(found.name);
      setCategory(found.category);
      setLocation(found.location);
    }
  };

  return (
    <Modal title="Flag Diminishing Stock / Request Supplies" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4 text-sm">
        <FormField label="Choose Existing Item (Optional)">
          <select
            value={selectedItemId ?? ""}
            onChange={(e) => handleSelectChange(e.target.value)}
            className={inputClass}
          >
            <option value="">-- Or enter custom item name below --</option>
            {items.map((it) => (
              <option key={it.id} value={it.id}>
                {it.name} ({it.location} &middot; {it.current_quantity} {it.unit} left)
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Item Name">
          <input
            type="text"
            required
            value={itemName}
            onChange={(e) => setItemName(e.target.value)}
            placeholder="e.g. Hydrochloric Acid 500ml or White Chalk"
            className={inputClass}
          />
        </FormField>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Category">
            <input
              type="text"
              required
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={inputClass}
            />
          </FormField>
          <FormField label="Room / Location">
            <input
              type="text"
              required
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className={inputClass}
            />
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Quantity Needed">
            <input
              type="number"
              min="1"
              required
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className={inputClass}
            />
          </FormField>
          <FormField label="Urgency Level">
            <select
              value={urgency}
              onChange={(e) => setUrgency(e.target.value as any)}
              className={inputClass}
            >
              <option value="normal">Normal</option>
              <option value="urgent">Urgent</option>
              <option value="critical">Critical (Immediate practical/class need)</option>
            </select>
          </FormField>
        </div>

        <FormField label="Diminishing Reason & Classroom Context">
          <textarea
            rows={3}
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Explain why this item is running low or needed for upcoming classes..."
            className={inputClass}
          />
        </FormField>

        <FormError error={error} />

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending || !reason.trim() || !itemName.trim()}
            className="rounded-input bg-primary text-white px-4 py-2 font-medium hover:bg-primary-dark disabled:opacity-60"
          >
            {mutation.isPending ? "Submitting..." : "Submit Stock Flag"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** Modal to adjust stock count or record physical discrepancy */
function AdjustStockModal({
  item,
  onClose,
  onSuccess,
}: {
  item: {
    id: number;
    name: string;
    current_quantity: number;
    location: string;
    unit: string;
    has_discrepancy: boolean;
    discrepancy_notes?: string | null;
  };
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [newQty, setNewQty] = useState(item.current_quantity);
  const [hasDiscrepancy, setHasDiscrepancy] = useState(item.has_discrepancy);
  const [discrepancyNotes, setDiscrepancyNotes] = useState(item.discrepancy_notes ?? "");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: (body: any) =>
      api.patch(
        `/admin/inventory/items/${item.id}/adjust` as "/admin/inventory/items/{item_id}/adjust",
        body,
      ),
    onSuccess,
    onError: (err) => setError(err),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;
    mutation.mutate({
      new_quantity: Number(newQty),
      reason: reason.trim(),
      has_discrepancy: hasDiscrepancy,
      discrepancy_notes: hasDiscrepancy ? discrepancyNotes.trim() || reason.trim() : null,
    });
  };

  return (
    <Modal title={`Adjust Stock: ${item.name}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4 text-sm">
        <div className="bg-surface rounded-card p-3 border border-rule">
          <p className="text-xs text-ink-faint">Location</p>
          <p className="font-semibold text-ink">{item.location}</p>
          <p className="text-xs text-ink-faint mt-1">Current Recorded Quantity</p>
          <p className="font-bold text-ink tabular">
            {item.current_quantity} {item.unit}
          </p>
        </div>

        <FormField label={`New Physical Count (${item.unit})`}>
          <input
            type="number"
            min="0"
            required
            value={newQty}
            onChange={(e) => setNewQty(Math.max(0, parseInt(e.target.value) || 0))}
            className={inputClass}
          />
        </FormField>

        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={hasDiscrepancy}
            onChange={(e) => setHasDiscrepancy(e.target.checked)}
            className="rounded text-danger focus:ring-danger h-4 w-4"
          />
          <span className="font-medium text-ink">
            Flag as physical stock discrepancy awaiting investigation
          </span>
        </label>

        {hasDiscrepancy && (
          <FormField label="Discrepancy Investigation Notes">
            <textarea
              rows={2}
              value={discrepancyNotes}
              onChange={(e) => setDiscrepancyNotes(e.target.value)}
              placeholder="e.g. Audit found broken items or count mismatch against delivery invoice..."
              className={inputClass}
            />
          </FormField>
        )}

        <FormField label="Audited Reason for Adjustment (Mandatory)">
          <textarea
            rows={2}
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why is this stock count being changed? (Saved to audit_log)"
            className={inputClass}
          />
        </FormField>

        <FormError error={error} />

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending || !reason.trim()}
            className="rounded-input bg-primary text-white px-4 py-2 font-medium hover:bg-primary-dark disabled:opacity-60"
          >
            {mutation.isPending ? "Saving..." : "Save Adjustment"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** Modal to add a new stock item */
function AddItemModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Science Lab");
  const [location, setLocation] = useState("Science Lab");
  const [unit, setUnit] = useState("pieces");
  const [currentQty, setCurrentQty] = useState(10);
  const [minQty, setMinQty] = useState(5);
  const [cost, setCost] = useState("");
  const [isCritical, setIsCritical] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: (body: any) => api.post("/admin/inventory/items", body),
    onSuccess,
    onError: (err) => setError(err),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    mutation.mutate({
      name: name.trim(),
      category: category.trim(),
      location: location.trim(),
      unit: unit.trim(),
      current_quantity: Number(currentQty),
      min_quantity: Number(minQty),
      unit_cost: cost.trim() ? Number(cost) : undefined,
      is_critical: isCritical,
    });
  };

  return (
    <Modal title="Add Stock Item" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4 text-sm">
        <FormField label="Item Name">
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Copper Sulphate Crystals 250g"
            className={inputClass}
          />
        </FormField>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Category">
            <input
              type="text"
              required
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className={inputClass}
            />
          </FormField>
          <FormField label="Location / Room">
            <input
              type="text"
              required
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className={inputClass}
            />
          </FormField>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <FormField label="Unit of Measure">
            <input
              type="text"
              required
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              placeholder="e.g. bottles, boxes, reams"
              className={inputClass}
            />
          </FormField>
          <FormField label="Opening Stock">
            <input
              type="number"
              min="0"
              required
              value={currentQty}
              onChange={(e) => setCurrentQty(Math.max(0, parseInt(e.target.value) || 0))}
              className={inputClass}
            />
          </FormField>
          <FormField label="Min Reorder Level">
            <input
              type="number"
              min="0"
              required
              value={minQty}
              onChange={(e) => setMinQty(Math.max(0, parseInt(e.target.value) || 0))}
              className={inputClass}
            />
          </FormField>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Estimated Unit Cost (₹, optional)">
            <input
              type="number"
              step="0.01"
              value={cost}
              onChange={(e) => setCost(e.target.value)}
              placeholder="e.g. 150.00"
              className={inputClass}
            />
          </FormField>
          <div className="flex items-center pt-6">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={isCritical}
                onChange={(e) => setIsCritical(e.target.checked)}
                className="rounded text-danger focus:ring-danger h-4 w-4"
              />
              <span className="text-xs font-semibold text-danger">Mark as Critical supply</span>
            </label>
          </div>
        </div>

        <FormError error={error} />

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending || !name.trim()}
            className="rounded-input bg-primary text-white px-4 py-2 font-medium hover:bg-primary-dark disabled:opacity-60"
          >
            {mutation.isPending ? "Adding..." : "Add to Stock"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/** Modal to approve or reject requests */
function DecideRequestModal({
  request,
  onClose,
  onSuccess,
}: {
  request: { id: number; item_name: string; action: "approved" | "rejected" };
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [note, setNote] = useState("");
  const [error, setError] = useState<unknown>(null);

  const mutation = useMutation({
    mutationFn: (body: any) =>
      api.post(
        `/admin/inventory/requests/${request.id}/decide` as "/admin/inventory/requests/{request_id}/decide",
        body,
      ),
    onSuccess,
    onError: (err) => setError(err),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({
      status: request.action,
      decision_note: note.trim() || undefined,
    });
  };

  const isApprove = request.action === "approved";

  return (
    <Modal
      title={`${isApprove ? "Approve" : "Reject"} Request: ${request.item_name}`}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-sm">
        <p className="text-ink-soft">
          Are you sure you want to {request.action} this stock request?
        </p>

        <FormField label="Decision Note / Reason">
          <textarea
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={
              isApprove
                ? "e.g. Approved for purchase indent..."
                : "e.g. Sufficient stock available in store..."
            }
            className={inputClass}
          />
        </FormField>

        <FormError error={error} />

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button
            type="button"
            onClick={onClose}
            className="rounded-input border border-rule px-4 py-2 hover:bg-ground"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className={`rounded-input px-4 py-2 text-white font-medium ${
              isApprove ? "bg-emerald-600 hover:bg-emerald-700" : "bg-danger hover:opacity-90"
            }`}
          >
            {mutation.isPending ? "Submitting..." : `Confirm ${isApprove ? "Approval" : "Rejection"}`}
          </button>
        </div>
      </form>
    </Modal>
  );
}
