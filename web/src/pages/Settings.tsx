import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, money } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Card, DataTable, FormField, inputClass } from "../components/ui";

type School = {
  name: string;
  address: string | null;
  city: string | null;
  phone: string | null;
  email: string | null;
  logo_url: string | null;
  primary_color: string | null;
  academic_year: string;
};

const FIELDS: [keyof School, string][] = [
  ["name", "School name"],
  ["address", "Address"],
  ["city", "City"],
  ["phone", "Phone"],
  ["email", "Email"],
  ["logo_url", "Logo URL"],
  ["primary_color", "Primary colour"],
  ["academic_year", "Academic year"],
];

type Band = { id: number; min_percent: string; grade: string };
// `/admin/fees/plans` was rebuilt in Part 3 around heads/plans/items and the
// backend route returns a plain dict, so the generated schema can't type its
// shape further than `{[key: string]: unknown}` - this local type documents
// the fields the screen actually reads.
type Plan = { id: number; name: string; class_name: string; monthly_total: string };

export function Settings() {
  const qc = useQueryClient();
  const school = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.get("/admin/settings") as Promise<School>,
  });
  // `/admin/fees/structures` was deleted when Part 3 rebuilt fees, and this
  // call has been a silent 404 ever since - the reason this slice generates
  // types. The replacement is the fee plan, which carries its own monthly
  // total summed from the items that recur monthly.
  //
  // This is the one panel on this screen that crosses a module boundary:
  // `/admin/fees/plans` sits behind `module_enabled("fees")`, while the rest of
  // Settings is a school's own profile and is always available. So the panel
  // gates itself rather than the screen declaring the fees module - a school
  // with fees switched off must still be able to edit its own name.
  const { hasModule } = useAuth();
  const feesOn = hasModule("fees");
  const structures = useQuery({
    queryKey: ["fee-plans"],
    queryFn: () => api.get("/admin/fees/plans") as Promise<Plan[]>,
    enabled: feesOn,
  });

  const bands = useQuery({
    queryKey: ["grade-bands"],
    queryFn: () => api.get("/admin/grade-bands") as Promise<Band[]>,
  });

  const [form, setForm] = useState<School | null>(null);
  useEffect(() => {
    if (school.data) setForm(school.data);
  }, [school.data]);

  const save = useMutation({
    // Guarded because `form` is null until the school query resolves, and the
    // typed body showed Save would post that null straight to the API.
    mutationFn: () => {
      if (!form) throw new Error("School settings have not loaded yet");
      return api.patch("/admin/settings", form);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });

  return (
    <>
      <Card title="School settings">
        <p className="text-xs text-ink-faint mb-4">
          Every school-specific label on any screen reads from here, so a new deployment is a
          configuration change rather than a code change.
        </p>
        {form && (
          <div className="grid gap-3 sm:grid-cols-2">
            {FIELDS.map(([key, label]) => (
              <FormField key={key} label={label}>
                <input
                  className={inputClass}
                  value={form[key] ?? ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              </FormField>
            ))}
          </div>
        )}
        <button
          onClick={() => save.mutate()}
          disabled={save.isPending || !form}
          className="mt-4 rounded-input bg-primary px-4 py-2 text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60"
        >
          {save.isSuccess ? "Saved" : "Save"}
        </button>
      </Card>

      <Card title="Grade bands">
        <p className="text-xs text-ink-faint mb-3">
          Grades are computed at read time from these bands and never stored.
        </p>
        <DataTable
          rows={bands.data ?? []}
          loading={bands.isLoading}
          error={bands.error}
          empty="No grade bands configured."
          columns={[
            { key: "grade", header: "Grade", render: (r) => r.grade },
            {
              key: "min",
              header: "Minimum percentage",
              align: "right",
              render: (r) => `${Number(r.min_percent)}%`,
            },
          ]}
        />
      </Card>

      {feesOn && (
      <Card title="Fee structure">
        <DataTable
          rows={structures.data ?? []}
          loading={structures.isLoading}
          error={structures.error}
          empty="No fee structure configured."
          columns={[
            { key: "class", header: "Class", render: (r) => r.class_name },
            {
              key: "amt",
              header: "Monthly amount",
              align: "right",
              render: (r) => money(r.monthly_total),
            },
          ]}
        />
      </Card>
      )}
    </>
  );
}
