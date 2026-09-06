import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, money } from "../api/client";
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

export function Settings() {
  const qc = useQueryClient();
  const school = useQuery({ queryKey: ["settings"], queryFn: () => api.get<School>("/admin/settings") });
  const structures = useQuery({
    queryKey: ["fee-structures"],
    queryFn: () => api.get<{ id: number; class_name: string; monthly_amount: string }[]>(
      "/admin/fees/structures",
    ),
  });

  const bands = useQuery({
    queryKey: ["grade-bands"],
    queryFn: () =>
      api.get<{ id: number; min_percent: string; grade: string }[]>("/admin/grade-bands"),
  });

  const [form, setForm] = useState<School | null>(null);
  useEffect(() => {
    if (school.data) setForm(school.data);
  }, [school.data]);

  const save = useMutation({
    mutationFn: () => api.patch("/admin/settings", form),
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

      <Card title="Fee structure">
        <DataTable
          rows={structures.data ?? []}
          loading={structures.isLoading}
          empty="No fee structure configured."
          columns={[
            { key: "class", header: "Class", render: (r) => r.class_name },
            {
              key: "amt",
              header: "Monthly amount",
              align: "right",
              render: (r) => money(r.monthly_amount),
            },
          ]}
        />
      </Card>
    </>
  );
}
