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

export interface DirectoryContact {
  id: number;
  school_id: number;
  category: string;
  name: string;
  designation_or_department?: string | null;
  phone_primary: string;
  phone_secondary?: string | null;
  email?: string | null;
  address?: string | null;
  operating_hours?: string | null;
  is_emergency: boolean;
  display_order: number;
  notes?: string | null;
  created_at: string;
}

export function DirectoryPage() {
  const queryClient = useQueryClient();
  const { me } = useAuth();

  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  // Modals for Admin CRUD
  const [showAddModal, setShowAddModal] = useState(false);
  const [editTargetContact, setEditTargetContact] = useState<DirectoryContact | null>(null);
  const [deleteTargetContact, setDeleteTargetContact] = useState<DirectoryContact | null>(null);

  const [contactForm, setContactForm] = useState({
    category: "Emergency",
    name: "",
    designation_or_department: "",
    phone_primary: "",
    phone_secondary: "",
    email: "",
    address: "",
    operating_hours: "24x7",
    is_emergency: false,
    display_order: 0,
    notes: "",
  });

  const [copiedPhone, setCopiedPhone] = useState<string | null>(null);

  // Queries
  const contactsQuery = useQuery({
    queryKey: ["directory-contacts", categoryFilter, search],
    queryFn: () => {
      const params = new URLSearchParams();
      if (categoryFilter) params.append("category", categoryFilter);
      if (search) params.append("search", search);
      const q = params.toString() ? `?${params.toString()}` : "";
      return api.get(`/admin/reception/directory${q}` as any) as Promise<DirectoryContact[]>;
    },
  });

  // Mutations (Admin CRUD only)
  const createContactMutation = useMutation({
    mutationFn: (data: typeof contactForm) => {
      return api.post("/admin/reception/directory" as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["directory-contacts"] });
      setShowAddModal(false);
      resetForm();
    },
  });

  const updateContactMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: typeof contactForm }) => {
      return api.put(`/admin/reception/directory/${id}` as any, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["directory-contacts"] });
      setEditTargetContact(null);
      resetForm();
    },
  });

  const deleteContactMutation = useMutation({
    mutationFn: (id: number) => {
      return api.del(`/admin/reception/directory/${id}` as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["directory-contacts"] });
      setDeleteTargetContact(null);
    },
  });

  const resetForm = () => {
    setContactForm({
      category: "Emergency",
      name: "",
      designation_or_department: "",
      phone_primary: "",
      phone_secondary: "",
      email: "",
      address: "",
      operating_hours: "24x7",
      is_emergency: false,
      display_order: 0,
      notes: "",
    });
  };

  const handleCopyPhone = (phone: string) => {
    navigator.clipboard.writeText(phone);
    setCopiedPhone(phone);
    setTimeout(() => setCopiedPhone(null), 2000);
  };

  const contacts = contactsQuery.data || [];
  const emergencyCount = contacts.filter((c) => c.is_emergency).length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Important Emergency & School Directory</h1>
          <p className="text-sm text-ink-faint">
            Directory of essential school, medical, civic, and emergency contacts for front desk coordination.
          </p>
        </div>

        {/* Admin CRUD Action: Gated on reception.directory.write (Admin only; Receptionist is Read-Only) */}
        <Can permission="reception.directory.write">
          <button
            type="button"
            onClick={() => {
              resetForm();
              setShowAddModal(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            Add Directory Contact
          </button>
        </Can>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Contacts" value={contacts.length} hint="Verified institutional and civic directory" />
        <StatCard label="Emergency Services" value={emergencyCount} hint="Hospitals, Police, Fire, Ambulance 24x7" />
        <StatCard
          label="Access Level"
          value={me?.user?.role === "receptionist" ? "Read-Only (Front Desk)" : "Full Management (Admin)"}
          hint={me?.user?.role === "receptionist" ? "Protected read-only access" : "Full CRUD authorized"}
        />
      </div>

      {/* Search and Category Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center mb-4">
          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1">
            <span className="text-xs font-semibold text-ink-faint uppercase whitespace-nowrap">Category:</span>
            <div className="flex gap-1.5">
              {[
                { label: "All Contacts", val: "" },
                { label: "Emergency", val: "Emergency" },
                { label: "Medical", val: "Medical" },
                { label: "Law & Order", val: "Law & Order" },
                { label: "Transport", val: "Transport" },
                { label: "Utilities", val: "Utilities" },
                { label: "Administration", val: "Administration" },
              ].map((btn) => (
                <button
                  key={btn.val}
                  type="button"
                  onClick={() => setCategoryFilter(btn.val)}
                  className={`px-3 py-1 rounded-pill text-xs font-medium whitespace-nowrap transition ${
                    categoryFilter === btn.val
                      ? "bg-primary text-white shadow-xs"
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
              placeholder="Search contact, phone, department..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        {/* Directory Contacts Table / List */}
        <DataTable<DirectoryContact>
          columns={[
            {
              key: "name",
              header: "Contact Name & Service",
              render: (row) => (
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-ink text-sm">{row.name}</span>
                    {row.is_emergency && (
                      <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-800 text-[9px] font-black uppercase tracking-wider">
                        EMERGENCY 24x7
                      </span>
                    )}
                  </div>
                  {row.designation_or_department && (
                    <span className="text-xs text-ink-faint block">{row.designation_or_department}</span>
                  )}
                  {row.notes && <span className="text-[10.5px] text-ink-faint block mt-0.5">{row.notes}</span>}
                </div>
              ),
            },
            {
              key: "category",
              header: "Category",
              render: (row) => (
                <span className="inline-block px-2.5 py-0.5 bg-ground rounded-pill text-xs font-semibold text-ink-faint border border-rule">
                  {row.category}
                </span>
              ),
            },
            {
              key: "phone",
              header: "Phone Numbers",
              render: (row) => (
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <a
                      href={`tel:${row.phone_primary}`}
                      className="font-mono font-bold text-primary hover:underline text-xs"
                    >
                      {row.phone_primary}
                    </a>
                    <button
                      type="button"
                      onClick={() => handleCopyPhone(row.phone_primary)}
                      className="text-[10px] text-ink-faint hover:text-ink px-1 rounded hover:bg-ground"
                      title="Copy phone"
                    >
                      {copiedPhone === row.phone_primary ? "✓ Copied" : "Copy"}
                    </button>
                  </div>
                  {row.phone_secondary && (
                    <div className="flex items-center gap-1.5">
                      <a
                        href={`tel:${row.phone_secondary}`}
                        className="font-mono text-xs text-ink-faint hover:text-ink"
                      >
                        {row.phone_secondary}
                      </a>
                      <button
                        type="button"
                        onClick={() => handleCopyPhone(row.phone_secondary!)}
                        className="text-[10px] text-ink-faint hover:text-ink px-1 rounded hover:bg-ground"
                      >
                        {copiedPhone === row.phone_secondary ? "✓ Copied" : "Copy"}
                      </button>
                    </div>
                  )}
                </div>
              ),
            },
            {
              key: "hours_location",
              header: "Hours & Address",
              render: (row) => (
                <div className="max-w-xs text-xs">
                  {row.operating_hours && (
                    <span className="font-semibold text-ink block">{row.operating_hours}</span>
                  )}
                  {row.address && <span className="text-ink-faint block truncate">{row.address}</span>}
                </div>
              ),
            },
            {
              key: "actions",
              header: "Manage",
              align: "right",
              render: (row) => (
                <Can permission="reception.directory.write">
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => {
                        setContactForm({
                          category: row.category,
                          name: row.name,
                          designation_or_department: row.designation_or_department || "",
                          phone_primary: row.phone_primary,
                          phone_secondary: row.phone_secondary || "",
                          email: row.email || "",
                          address: row.address || "",
                          operating_hours: row.operating_hours || "24x7",
                          is_emergency: row.is_emergency,
                          display_order: row.display_order,
                          notes: row.notes || "",
                        });
                        setEditTargetContact(row);
                      }}
                      className="px-2 py-1 text-xs font-medium text-ink-faint hover:text-ink hover:bg-ground rounded transition"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteTargetContact(row)}
                      className="px-2 py-1 text-xs font-medium text-danger hover:bg-danger/10 rounded transition"
                    >
                      Delete
                    </button>
                  </div>
                </Can>
              ),
            },
          ]}
          rows={contacts}
          empty="No contacts found in directory."
          loading={contactsQuery.isLoading}
          error={contactsQuery.error}
        />
      </Card>

      {/* Modal: Add Contact (Admin Only) */}
      {showAddModal && (
        <Modal title="Add Important Directory Contact" onClose={() => setShowAddModal(false)} wide>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createContactMutation.mutate(contactForm);
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Contact Title / Institution Name">
                <input
                  type="text"
                  required
                  placeholder="e.g. City General Hospital, District Education Office"
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Category">
                <select
                  value={contactForm.category}
                  onChange={(e) => setContactForm({ ...contactForm, category: e.target.value })}
                  className={inputClass}
                >
                  <option value="Emergency">Emergency</option>
                  <option value="Medical">Medical</option>
                  <option value="Law & Order">Law & Order</option>
                  <option value="Transport">Transport</option>
                  <option value="Utilities">Utilities</option>
                  <option value="Administration">Administration</option>
                </select>
              </FormField>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <FormField label="Designation / Department">
                <input
                  type="text"
                  placeholder="e.g. Casualty / Trauma, Fleet Ops"
                  value={contactForm.designation_or_department}
                  onChange={(e) => setContactForm({ ...contactForm, designation_or_department: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Primary Phone">
                <input
                  type="text"
                  required
                  placeholder="+91..."
                  value={contactForm.phone_primary}
                  onChange={(e) => setContactForm({ ...contactForm, phone_primary: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Secondary Phone / Hotline">
                <input
                  type="text"
                  placeholder="Alt phone number"
                  value={contactForm.phone_secondary}
                  onChange={(e) => setContactForm({ ...contactForm, phone_secondary: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Operating Hours">
                <input
                  type="text"
                  placeholder="e.g. 24x7 or 8:00 AM - 5:00 PM"
                  value={contactForm.operating_hours}
                  onChange={(e) => setContactForm({ ...contactForm, operating_hours: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Official Email">
                <input
                  type="email"
                  placeholder="contact@..."
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <FormField label="Address / Physical Location">
              <input
                type="text"
                placeholder="Full street address / landmark"
                value={contactForm.address}
                onChange={(e) => setContactForm({ ...contactForm, address: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="is_emergency_add"
                checked={contactForm.is_emergency}
                onChange={(e) => setContactForm({ ...contactForm, is_emergency: e.target.checked })}
                className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
              />
              <label htmlFor="is_emergency_add" className="text-xs font-semibold text-ink cursor-pointer">
                Mark as High-Priority Emergency Service (displays red emergency tag)
              </label>
            </div>

            <FormField label="Notes / Protocol">
              <input
                type="text"
                placeholder="e.g. Dedicated school pediatric ambulance tie-up with student discount"
                value={contactForm.notes}
                onChange={(e) => setContactForm({ ...contactForm, notes: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createContactMutation.isPending}
                className="px-5 py-2 bg-primary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition shadow-sm"
              >
                {createContactMutation.isPending ? "Saving..." : "Save Contact"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Edit Contact (Admin Only) */}
      {editTargetContact && (
        <Modal
          title={`Edit Contact: ${editTargetContact.name}`}
          onClose={() => setEditTargetContact(null)}
          wide
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateContactMutation.mutate({ id: editTargetContact.id, data: contactForm });
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Contact Title / Name">
                <input
                  type="text"
                  required
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Category">
                <select
                  value={contactForm.category}
                  onChange={(e) => setContactForm({ ...contactForm, category: e.target.value })}
                  className={inputClass}
                >
                  <option value="Emergency">Emergency</option>
                  <option value="Medical">Medical</option>
                  <option value="Law & Order">Law & Order</option>
                  <option value="Transport">Transport</option>
                  <option value="Utilities">Utilities</option>
                  <option value="Administration">Administration</option>
                </select>
              </FormField>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <FormField label="Designation / Department">
                <input
                  type="text"
                  value={contactForm.designation_or_department}
                  onChange={(e) => setContactForm({ ...contactForm, designation_or_department: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Primary Phone">
                <input
                  type="text"
                  required
                  value={contactForm.phone_primary}
                  onChange={(e) => setContactForm({ ...contactForm, phone_primary: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Secondary Phone">
                <input
                  type="text"
                  value={contactForm.phone_secondary}
                  onChange={(e) => setContactForm({ ...contactForm, phone_secondary: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="Operating Hours">
                <input
                  type="text"
                  value={contactForm.operating_hours}
                  onChange={(e) => setContactForm({ ...contactForm, operating_hours: e.target.value })}
                  className={inputClass}
                />
              </FormField>

              <FormField label="Official Email">
                <input
                  type="email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  className={inputClass}
                />
              </FormField>
            </div>

            <FormField label="Address">
              <input
                type="text"
                value={contactForm.address}
                onChange={(e) => setContactForm({ ...contactForm, address: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="is_emergency_edit"
                checked={contactForm.is_emergency}
                onChange={(e) => setContactForm({ ...contactForm, is_emergency: e.target.checked })}
                className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
              />
              <label htmlFor="is_emergency_edit" className="text-xs font-semibold text-ink cursor-pointer">
                Mark as High-Priority Emergency Service
              </label>
            </div>

            <FormField label="Notes">
              <input
                type="text"
                value={contactForm.notes}
                onChange={(e) => setContactForm({ ...contactForm, notes: e.target.value })}
                className={inputClass}
              />
            </FormField>

            <div className="flex justify-end gap-3 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setEditTargetContact(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateContactMutation.isPending}
                className="px-5 py-2 bg-primary text-white text-sm font-semibold rounded-pill hover:opacity-90 transition shadow-sm"
              >
                {updateContactMutation.isPending ? "Updating..." : "Update Contact"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Confirm Delete Contact */}
      {deleteTargetContact && (
        <Modal title="Confirm Delete Contact" onClose={() => setDeleteTargetContact(null)}>
          <div className="space-y-4 text-xs">
            <p className="text-ink">
              Are you sure you want to remove <span className="font-bold text-danger">{deleteTargetContact.name}</span> from the directory?
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteTargetContact(null)}
                className="px-4 py-2 text-sm font-medium text-ink-faint hover:text-ink transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => deleteContactMutation.mutate(deleteTargetContact.id)}
                disabled={deleteContactMutation.isPending}
                className="px-4 py-2 bg-danger text-white text-sm font-semibold rounded-pill hover:bg-danger/90 transition shadow-sm"
              >
                {deleteContactMutation.isPending ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
