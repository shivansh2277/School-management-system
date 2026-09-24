import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useWrite } from "../../api/useWrite";
import { FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

export type FeeSlab = {
  id: number;
  name: string;
  monthly_amount: number;
  is_active: boolean;
};

export function SlabsModal({ onClose }: { onClose: () => void }) {
  const [editingSlab, setEditingSlab] = useState<FeeSlab | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");

  const slabsQuery = useQuery({
    queryKey: ["transport-slabs"],
    queryFn: () => api.get("/admin/transport/slabs") as Promise<FeeSlab[]>,
  });

  const saveSlab = useWrite({
    write: async () => {
      const payload = {
        name: name.trim(),
        monthly_amount: parseFloat(amount) || 0,
      };

      if (editingSlab) {
        return api.patch(
          `/admin/transport/slabs/${editingSlab.id}` as "/admin/transport/slabs/{slab_id}",
          { ...payload, is_active: editingSlab.is_active },
        );
      } else {
        return api.post("/admin/transport/slabs", payload);
      }
    },
    invalidates: [["transport-slabs"], ["transport-routes"]],
    onDone: () => {
      setIsAdding(false);
      setEditingSlab(null);
      setName("");
      setAmount("");
    },
  });

  const slabs = slabsQuery.data ?? [];

  return (
    <Modal title="Transport Distance Fee Slabs" onClose={onClose} wide>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-ink-soft">
          Fee slabs are linked to route stops. Monthly fees are charged based on the boarding stop.
        </p>
        {!isAdding && !editingSlab && (
          <button
            type="button"
            onClick={() => {
              setName("");
              setAmount("");
              setIsAdding(true);
            }}
            className="rounded-input bg-primary px-3 py-1.5 text-white text-xs font-medium hover:opacity-90"
          >
            + Add Fee Slab
          </button>
        )}
      </div>

      {(isAdding || editingSlab) && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            saveSlab.run();
          }}
          className="mb-6 p-4 rounded-card bg-ground border border-rule space-y-3"
        >
          <h4 className="text-sm font-semibold text-ink">
            {editingSlab ? `Edit Fee Slab (${editingSlab.name})` : "Create New Distance Fee Slab"}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormField label="Slab Name / Range" error={saveSlab.fields.name}>
              <input
                className={inputClass}
                placeholder="e.g. 0-5 km or Gomti Nagar Local"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </FormField>
            <FormField label="Monthly Fee (₹)" error={saveSlab.fields.monthly_amount}>
              <input
                className={inputClass}
                type="number"
                step="1"
                min="0"
                placeholder="e.g. 800"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </FormField>
          </div>
          <FormError error={saveSlab.error} />
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => {
                setIsAdding(false);
                setEditingSlab(null);
              }}
              className="rounded-input border border-rule px-3 py-1.5 text-xs hover:bg-canvas"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saveSlab.busy || !name.trim() || !amount}
              className="rounded-input bg-primary px-4 py-1.5 text-white text-xs font-medium hover:opacity-90 disabled:opacity-60"
            >
              {saveSlab.busy ? "Saving..." : editingSlab ? "Update Slab" : "Create Slab"}
            </button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto border border-rule rounded-card">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-ground border-b border-rule text-left text-ink-soft">
              <th className="p-3">Slab Name</th>
              <th className="p-3 text-right">Monthly Fee</th>
              <th className="p-3 text-center">Status</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {slabs.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-4 text-center text-ink-faint">
                  No distance fee slabs configured.
                </td>
              </tr>
            ) : (
              slabs.map((s) => (
                <tr key={s.id} className="hover:bg-ground/50">
                  <td className="p-3 font-medium text-ink">{s.name}</td>
                  <td className="p-3 text-right font-semibold text-primary">₹{Number(s.monthly_amount).toFixed(2)}</td>
                  <td className="p-3 text-center">
                    <Pill status={s.is_active ? "active" : "danger"}>
                      {s.is_active ? "Active" : "Inactive"}
                    </Pill>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      type="button"
                      onClick={() => {
                        setIsAdding(false);
                        setEditingSlab(s);
                        setName(s.name);
                        setAmount(String(s.monthly_amount));
                      }}
                      className="rounded-input border border-rule px-2.5 py-1 text-xs hover:bg-canvas"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end pt-4">
        <button
          type="button"
          onClick={onClose}
          className="rounded-input border border-rule px-4 py-2 text-sm hover:bg-canvas"
        >
          Close
        </button>
      </div>
    </Modal>
  );
}
