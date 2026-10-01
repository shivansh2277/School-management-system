import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { errorText } from "../api/errors";
import { useAuth } from "../auth/AuthContext";
import { ActionButton } from "../components/Can";
import {
  Card,
  DataTable,
  FormError,
  FormField,
  Modal,
  Pill,
  StatCard,
  inputClass,
} from "../components/ui";

type BookItem = {
  id: number;
  isbn: string | null;
  title: string;
  author: string;
  publisher: string | null;
  category: string | null;
  total_copies: number;
  available_copies: number;
  shelf_location: string | null;
  copies?: Array<{
    id: number;
    barcode: string;
    status: string;
  }>;
};

type LoanItem = {
  id: number;
  book_copy_id: number;
  accession_no: string;
  book_title: string;
  enrolment_id: number | null;
  borrower_name: string;
  borrower_type: string;
  class_label: string | null;
  roll_no: number | null;
  issued_on: string;
  due_date: string;
  returned_on: string | null;
  status: string;
  fine_amount: number;
  fine_paid: boolean;
  renewal_count: number;
};

type BorrowerInfo = {
  enrolment_id?: number;
  employee_id?: number;
  canonical_id: string;
  name: string;
  role: string;
  class_label?: string;
  roll_no?: number;
  active_loans_count: number;
  unpaid_fines_total: number;
};

export function Library() {
  const qc = useQueryClient();
  const { can } = useAuth();
  const [tab, setTab] = useState<"circulation" | "catalogue" | "fines">("circulation");

  // Books catalogue state
  const [bookSearch, setBookSearch] = useState("");
  const [addingBook, setAddingBook] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newAuthor, setNewAuthor] = useState("");
  const [newIsbn, setNewIsbn] = useState("");
  const [newPublisher, setNewPublisher] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [newShelf, setNewShelf] = useState("");
  const [newCopies, setNewCopies] = useState(1);

  // Circulation state
  const [borrowerId, setBorrowerId] = useState("");
  const [bookBarcode, setBookBarcode] = useState("");
  const [loanDays, setLoanDays] = useState(14);
  const [circulationStatus, setCirculationStatus] = useState<string | null>(null);

  // Return modal state
  const [returningLoan, setReturningLoan] = useState<LoanItem | null>(null);
  const [returnCondition, setReturnCondition] = useState("good");
  const [returnRemarks, setReturnRemarks] = useState("");

  // Fine settlement state
  const [settlingLoan, setSettlingLoan] = useState<LoanItem | null>(null);
  const [fineAction, setFineAction] = useState<"paid" | "waived">("paid");
  const [fineReason, setFineReason] = useState("Fee counter receipt confirmed");

  // Books Query
  const booksQuery = useQuery({
    queryKey: ["library-books", bookSearch],
    queryFn: () =>
      api.rawGet<{ items: BookItem[]; total: number }>(
        `/admin/library/books${bookSearch ? `?q=${encodeURIComponent(bookSearch)}` : ""}`,
      ),
  });

  // Loans Query
  const loansQuery = useQuery({
    queryKey: ["library-loans", tab],
    queryFn: () => {
      const statusParam = tab === "fines" ? "?status=fines" : "?status=active";
      return api.rawGet<{ items: LoanItem[]; total: number }>(`/admin/library/loans${statusParam}`);
    },
  });

  // Borrower Lookup
  const borrowerQuery = useQuery({
    queryKey: ["borrower-lookup", borrowerId],
    queryFn: () =>
      api.rawGet<BorrowerInfo>(`/admin/library/borrowers/lookup?q=${encodeURIComponent(borrowerId.trim())}`),
    enabled: borrowerId.trim().length >= 2,
  });

  // Mutations
  const createBookMutation = useMutation({
    mutationFn: async () => {
      return api.rawPost("/admin/library/books", {
        title: newTitle,
        author: newAuthor,
        isbn: newIsbn || null,
        publisher: newPublisher || null,
        category: newCategory || null,
        shelf_location: newShelf || null,
        initial_copies: Number(newCopies),
      });
    },
    onSuccess: () => {
      setAddingBook(false);
      setNewTitle("");
      setNewAuthor("");
      setNewIsbn("");
      qc.invalidateQueries({ queryKey: ["library-books"] });
    },
  });

  const issueMutation = useMutation({
    mutationFn: async () => {
      return api.rawPost("/admin/library/loans/issue", {
        borrower_identifier: borrowerId.trim(),
        copy_barcode: bookBarcode.trim(),
        loan_days: Number(loanDays),
      });
    },
    onSuccess: () => {
      setCirculationStatus("Book successfully issued to borrower.");
      setBookBarcode("");
      qc.invalidateQueries({ queryKey: ["library-loans"] });
      qc.invalidateQueries({ queryKey: ["library-books"] });
      qc.invalidateQueries({ queryKey: ["borrower-lookup", borrowerId] });
    },
  });

  const returnMutation = useMutation({
    mutationFn: async ({ loanId, condition, remarks }: { loanId: number; condition: string; remarks: string }) => {
      return api.rawPost(`/admin/library/loans/${loanId}/return`, {
        condition,
        remarks: remarks || null,
      });
    },
    onSuccess: (data: any) => {
      setReturningLoan(null);
      setCirculationStatus(
        `Book returned successfully. ${data.fine_amount > 0 ? `Late fine due: ₹${data.fine_amount}` : "No fine due."}`,
      );
      qc.invalidateQueries({ queryKey: ["library-loans"] });
      qc.invalidateQueries({ queryKey: ["library-books"] });
    },
  });

  const renewMutation = useMutation({
    mutationFn: async (loanId: number) => {
      return api.rawPost(`/admin/library/loans/${loanId}/renew`, { additional_days: 14 });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["library-loans"] });
    },
  });

  const settleFineMutation = useMutation({
    mutationFn: async ({ loanId, action, reason }: { loanId: number; action: string; reason: string }) => {
      return api.rawPost(`/admin/library/loans/${loanId}/settle-fine`, { action, reason });
    },
    onSuccess: () => {
      setSettlingLoan(null);
      qc.invalidateQueries({ queryKey: ["library-loans"] });
    },
  });

  const handleIssue = (e: React.FormEvent) => {
    e.preventDefault();
    if (!borrowerId.trim() || !bookBarcode.trim()) return;
    setCirculationStatus(null);
    issueMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Library & Circulation Desk</h1>
          <p className="text-sm text-ink-soft">
            Manage catalogue, barcode accessions, and book circulation using canonical Enrollment ID (ENR-&#123;id&#125;).
          </p>
        </div>

        <div className="flex gap-2">
          {can("library.manage") && (
            <button
              onClick={() => setAddingBook(true)}
              className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90"
            >
              + Add New Book
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-rule gap-6">
        <button
          onClick={() => setTab("circulation")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "circulation"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Circulation Desk
        </button>
        <button
          onClick={() => setTab("catalogue")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "catalogue"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Catalogue & Copies ({booksQuery.data?.total ?? 0})
        </button>
        <button
          onClick={() => setTab("fines")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "fines"
              ? "border-primary text-primary"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          Overdue Fines
        </button>
      </div>

      {circulationStatus && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-card text-sm">
          ✓ {circulationStatus}
        </div>
      )}

      {/* Circulation Desk Tab */}
      {tab === "circulation" && (
        <div className="space-y-6">
          {/* Issue Section */}
          <Card title="Quick Issue (Scan Barcode / Enter Enrollment ID)">
            <form onSubmit={handleIssue} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <FormField label="Borrower Enrollment ID or Code">
                  <input
                    type="text"
                    className={inputClass}
                    placeholder="e.g. ENR-1 or Student Name..."
                    value={borrowerId}
                    onChange={(e) => setBorrowerId(e.target.value)}
                    required
                  />
                </FormField>

                <FormField label="Book Accession No or Barcode">
                  <input
                    type="text"
                    className={inputClass}
                    placeholder="e.g. ACC-1-1 or BC-ACC-0001..."
                    value={bookBarcode}
                    onChange={(e) => setBookBarcode(e.target.value)}
                    required
                  />
                </FormField>

                <FormField label="Loan Period (Days)">
                  <input
                    type="number"
                    min="1"
                    max="60"
                    className={inputClass}
                    value={loanDays}
                    onChange={(e) => setLoanDays(Number(e.target.value))}
                    required
                  />
                </FormField>
              </div>

              {borrowerQuery.data && (
                <div className="p-3 bg-ground border border-rule rounded-card text-xs flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="font-semibold text-sm">{borrowerQuery.data.name}</span>{" "}
                    <span className="font-mono text-ink-soft">({borrowerQuery.data.canonical_id})</span> •{" "}
                    {borrowerQuery.data.class_label ? `Class ${borrowerQuery.data.class_label}` : borrowerQuery.data.role}
                  </div>
                  <div className="flex gap-4">
                    <span>
                      Active Loans: <strong>{borrowerQuery.data.active_loans_count}</strong>
                    </span>
                    {borrowerQuery.data.unpaid_fines_total > 0 && (
                      <span className="text-danger font-medium">
                        Unpaid Fines: ₹{borrowerQuery.data.unpaid_fines_total}
                      </span>
                    )}
                  </div>
                </div>
              )}

              <FormError error={issueMutation.error} />

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={issueMutation.isPending || !borrowerId.trim() || !bookBarcode.trim()}
                  className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  {issueMutation.isPending ? "Issuing..." : "Issue Book"}
                </button>
              </div>
            </form>
          </Card>

          {/* Active Loans Table */}
          <Card title="Active & Overdue Circulation Loans">
            <DataTable
              rows={loansQuery.data?.items ?? []}
              loading={loansQuery.isLoading}
              error={loansQuery.error}
              empty="No active book loans at this time."
              columns={[
                {
                  key: "acc",
                  header: "Accession",
                  render: (r) => <span className="font-mono text-xs">{r.accession_no}</span>,
                },
                {
                  key: "book",
                  header: "Book Title",
                  render: (r) => <span className="font-medium">{r.book_title}</span>,
                },
                {
                  key: "borrower",
                  header: "Borrower",
                  render: (r) => (
                    <div>
                      <p className="font-medium text-xs">{r.borrower_name}</p>
                      <p className="font-mono text-ink-faint text-[11px]">
                        {r.enrolment_id ? `ENR-${r.enrolment_id}` : "Staff"}
                      </p>
                    </div>
                  ),
                },
                {
                  key: "issued",
                  header: "Issued",
                  render: (r) => <span className="text-xs">{r.issued_on}</span>,
                },
                {
                  key: "due",
                  header: "Due Date",
                  render: (r) => (
                    <span
                      className={`text-xs font-medium ${
                        new Date(r.due_date) < new Date() ? "text-danger font-bold" : ""
                      }`}
                    >
                      {r.due_date}
                    </span>
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (r) => <Pill status={r.status}>{r.status}</Pill>,
                },
                {
                  key: "fine",
                  header: "Fine",
                  render: (r) =>
                    r.fine_amount > 0 ? (
                      <span className="text-danger font-semibold tabular">₹{r.fine_amount}</span>
                    ) : (
                      <span className="text-ink-faint">-</span>
                    ),
                },
                {
                  key: "actions",
                  header: "Actions",
                  align: "right",
                  render: (r) => (
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => renewMutation.mutate(r.id)}
                        disabled={renewMutation.isPending || r.renewal_count >= 2}
                        title={r.renewal_count >= 2 ? "Max renewals reached" : "Extend loan by 14 days"}
                        className="rounded border border-rule px-2 py-1 text-xs hover:bg-ground disabled:opacity-40"
                      >
                        Renew ({r.renewal_count}/2)
                      </button>
                      <button
                        onClick={() => setReturningLoan(r)}
                        className="rounded bg-primary/10 text-primary hover:bg-primary/20 px-2 py-1 text-xs font-medium"
                      >
                        Return
                      </button>
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </div>
      )}

      {/* Catalogue Tab */}
      {tab === "catalogue" && (
        <Card
          title="Library Catalogue & Accession Inventory"
          action={
            <div className="w-72">
              <input
                type="text"
                className={inputClass}
                placeholder="Search by title, author, ISBN..."
                value={bookSearch}
                onChange={(e) => setBookSearch(e.target.value)}
              />
            </div>
          }
        >
          <DataTable
            rows={booksQuery.data?.items ?? []}
            loading={booksQuery.isLoading}
            error={booksQuery.error}
            empty="No books in catalogue matching search."
            columns={[
              {
                key: "isbn",
                header: "ISBN",
                render: (r) => <span className="font-mono text-xs">{r.isbn ?? "-"}</span>,
              },
              {
                key: "title",
                header: "Title & Author",
                render: (r) => (
                  <div>
                    <p className="font-medium text-ink">{r.title}</p>
                    <p className="text-xs text-ink-soft">by {r.author}</p>
                  </div>
                ),
              },
              {
                key: "category",
                header: "Category",
                render: (r) => <span className="text-xs">{r.category ?? "-"}</span>,
              },
              {
                key: "shelf",
                header: "Shelf Location",
                render: (r) => (
                  <span className="font-mono text-xs bg-ground px-2 py-0.5 rounded border border-rule">
                    {r.shelf_location ?? "General"}
                  </span>
                ),
              },
              {
                key: "copies",
                header: "Available / Total",
                render: (r) => (
                  <span
                    className={`font-semibold text-xs tabular ${
                      r.available_copies === 0 ? "text-danger" : "text-emerald-700"
                    }`}
                  >
                    {r.available_copies} / {r.total_copies}
                  </span>
                ),
              },
            ]}
          />
        </Card>
      )}

      {/* Fines Tab */}
      {tab === "fines" && (
        <Card title="Outstanding Library Fines">
          <DataTable
            rows={loansQuery.data?.items ?? []}
            loading={loansQuery.isLoading}
            error={loansQuery.error}
            empty="No outstanding library fines."
            columns={[
              {
                key: "acc",
                header: "Accession",
                render: (r) => <span className="font-mono text-xs">{r.accession_no}</span>,
              },
              {
                key: "book",
                header: "Book Title",
                render: (r) => <span className="font-medium text-xs">{r.book_title}</span>,
              },
              {
                key: "borrower",
                header: "Borrower",
                render: (r) => (
                  <div>
                    <span className="font-medium text-xs">{r.borrower_name}</span>{" "}
                    <span className="font-mono text-ink-faint text-[11px]">
                      {r.enrolment_id ? `(ENR-${r.enrolment_id})` : "(Staff)"}
                    </span>
                  </div>
                ),
              },
              {
                key: "due",
                header: "Due Date",
                render: (r) => <span className="text-xs text-danger font-medium">{r.due_date}</span>,
              },
              {
                key: "fine",
                header: "Fine Amount",
                render: (r) => <span className="font-bold text-sm text-danger tabular">₹{r.fine_amount}</span>,
              },
              {
                key: "actions",
                header: "Action",
                align: "right",
                render: (r) => (
                  <button
                    onClick={() => setSettlingLoan(r)}
                    className="rounded bg-primary px-3 py-1 text-white text-xs font-medium hover:bg-primary/90"
                  >
                    Settle / Waive Fine
                  </button>
                ),
              },
            ]}
          />
        </Card>
      )}

      {/* Add Book Modal */}
      {addingBook && (
        <Modal title="Add New Book to Catalogue" onClose={() => setAddingBook(false)}>
          <div className="space-y-4">
            <FormField label="Book Title">
              <input
                type="text"
                className={inputClass}
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                required
              />
            </FormField>

            <FormField label="Author">
              <input
                type="text"
                className={inputClass}
                value={newAuthor}
                onChange={(e) => setNewAuthor(e.target.value)}
                required
              />
            </FormField>

            <div className="grid grid-cols-2 gap-3">
              <FormField label="ISBN">
                <input
                  type="text"
                  className={inputClass}
                  value={newIsbn}
                  onChange={(e) => setNewIsbn(e.target.value)}
                />
              </FormField>

              <FormField label="Publisher">
                <input
                  type="text"
                  className={inputClass}
                  value={newPublisher}
                  onChange={(e) => setNewPublisher(e.target.value)}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <FormField label="Category">
                <input
                  type="text"
                  className={inputClass}
                  placeholder="e.g. Science, Fiction"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                />
              </FormField>

              <FormField label="Shelf Location">
                <input
                  type="text"
                  className={inputClass}
                  placeholder="e.g. A-12, B-04"
                  value={newShelf}
                  onChange={(e) => setNewShelf(e.target.value)}
                />
              </FormField>

              <FormField label="Initial Copies">
                <input
                  type="number"
                  min="1"
                  max="50"
                  className={inputClass}
                  value={newCopies}
                  onChange={(e) => setNewCopies(Number(e.target.value))}
                />
              </FormField>
            </div>

            <FormError error={createBookMutation.error} />

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setAddingBook(false)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => createBookMutation.mutate()}
                disabled={createBookMutation.isPending || !newTitle || !newAuthor}
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {createBookMutation.isPending ? "Adding..." : "Add Book & Generate Accessions"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Return Book Modal */}
      {returningLoan && (
        <Modal title="Process Book Return" onClose={() => setReturningLoan(null)}>
          <div className="space-y-4">
            <div className="p-3 bg-ground border border-rule rounded-card text-xs">
              <p className="font-semibold text-sm">{returningLoan.book_title}</p>
              <p className="font-mono text-ink-soft">Accession: {returningLoan.accession_no}</p>
              <p className="mt-1">
                Borrower: <strong>{returningLoan.borrower_name}</strong> (Due: {returningLoan.due_date})
              </p>
            </div>

            <FormField label="Book Condition">
              <select
                className={inputClass}
                value={returnCondition}
                onChange={(e) => setReturnCondition(e.target.value)}
              >
                <option value="good">Good / Normal Wear</option>
                <option value="fair">Fair</option>
                <option value="damaged">Damaged (Fine may apply)</option>
                <option value="lost">Lost</option>
              </select>
            </FormField>

            <FormField label="Staff Remarks (Optional)">
              <input
                type="text"
                className={inputClass}
                placeholder="Notes on return or condition..."
                value={returnRemarks}
                onChange={(e) => setReturnRemarks(e.target.value)}
              />
            </FormField>

            <FormError error={returnMutation.error} />

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setReturningLoan(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() =>
                  returnMutation.mutate({
                    loanId: returningLoan.id,
                    condition: returnCondition,
                    remarks: returnRemarks,
                  })
                }
                disabled={returnMutation.isPending}
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {returnMutation.isPending ? "Processing..." : "Confirm Return"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Settle Fine Modal */}
      {settlingLoan && (
        <Modal title="Settle Outstanding Library Fine" onClose={() => setSettlingLoan(null)}>
          <div className="space-y-4">
            <div className="p-3 bg-ground border border-rule rounded-card text-xs space-y-1">
              <p className="font-semibold text-sm">{settlingLoan.book_title}</p>
              <p>Borrower: <strong>{settlingLoan.borrower_name}</strong></p>
              <p className="text-danger font-semibold text-sm">Fine Due: ₹{settlingLoan.fine_amount}</p>
            </div>

            <FormField label="Settlement Action">
              <select
                className={inputClass}
                value={fineAction}
                onChange={(e) => setFineAction(e.target.value as "paid" | "waived")}
              >
                <option value="paid">Paid (Receipt Collected)</option>
                <option value="waived">Waived (Administrative Exemption)</option>
              </select>
            </FormField>

            <FormField label="Audit Reason / Receipt No.">
              <input
                type="text"
                className={inputClass}
                value={fineReason}
                onChange={(e) => setFineReason(e.target.value)}
                required
              />
            </FormField>

            <FormError error={settleFineMutation.error} />

            <div className="flex gap-2 justify-end pt-2">
              <button
                type="button"
                onClick={() => setSettlingLoan(null)}
                className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() =>
                  settleFineMutation.mutate({
                    loanId: settlingLoan.id,
                    action: fineAction,
                    reason: fineReason,
                  })
                }
                disabled={settleFineMutation.isPending || !fineReason.trim()}
                className="rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                {settleFineMutation.isPending ? "Recording..." : "Record Settlement"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
