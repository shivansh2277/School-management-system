import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { ActionButton } from "../../components/Can";
import { Card, DataTable, FormField, Modal, Pill, inputClass } from "../../components/ui";

type SchemeComponent = {
  id: number;
  code: string;
  name: string;
  term: string;
  max_marks: string | number;
  sequence: number;
};

type AssessmentScheme = {
  id: number;
  name: string;
  academic_year_id: number;
  is_active: boolean;
  terms: { term: string; total: string | number }[];
  components: SchemeComponent[];
};

type GradeBand = {
  min_percent: string | number;
  grade: string;
  description: string | null;
};

type GradingScale = {
  id: number;
  name: string;
  version: number;
  is_active: boolean;
  frozen_at: string | null;
  bands: GradeBand[];
};

const WRITE_PERMISSION = "exam.definition.write";

export function SchemesAndGrading() {
  const qc = useQueryClient();
  const [showCreateScheme, setShowCreateScheme] = useState(false);
  const [showCreateScale, setShowCreateScale] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState<AssessmentScheme | null>(null);
  const [selectedScale, setSelectedScale] = useState<GradingScale | null>(null);

  const schemesQuery = useQuery({
    queryKey: ["assessment-schemes"],
    queryFn: () => api.get("/admin/assessment-schemes" as "/admin/assessment-schemes") as Promise<AssessmentScheme[]>,
  });

  const scalesQuery = useQuery({
    queryKey: ["grading-scales"],
    queryFn: () => api.get("/admin/grading-scales" as "/admin/grading-scales") as Promise<GradingScale[]>,
  });

  const activateSchemeMutation = useMutation({
    mutationFn: (schemeId: number) =>
      (api.post as any)(`/admin/assessment-schemes/${schemeId}/activate`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment-schemes"] });
    },
  });

  const activateScaleMutation = useMutation({
    mutationFn: (scaleId: number) =>
      (api.post as any)(`/admin/grading-scales/${scaleId}/activate`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["grading-scales"] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Section 1: Assessment Schemes */}
      <Card
        title="CBSE Assessment Schemes & Weightages"
        action={
          <ActionButton
            permission={WRITE_PERMISSION}
            onClick={() => setShowCreateScheme(true)}
            className="!px-3 !py-1 text-xs"
          >
            + New Scheme
          </ActionButton>
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          {schemesQuery.isLoading && (
            <div className="col-span-2 py-6 text-center text-sm text-ink-faint">
              Loading assessment schemes...
            </div>
          )}

          {schemesQuery.data?.map((scheme) => (
            <div
              key={scheme.id}
              className={`rounded-card border p-4 space-y-3 transition-colors ${
                scheme.is_active ? "border-primary bg-primary/5" : "border-rule bg-surface"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-ink text-base flex items-center gap-2">
                    {scheme.name}
                    {scheme.is_active && <Pill status="paid">ACTIVE IN FORCE</Pill>}
                  </h3>
                  <p className="text-xs text-ink-soft mt-0.5">
                    {scheme.terms.map((t) => `${t.term}: Total ${t.total}M`).join(" • ")}
                  </p>
                </div>

                {!scheme.is_active && (
                  <ActionButton
                    permission={WRITE_PERMISSION}
                    className="px-2.5 py-1 text-xs"
                    disabled={activateSchemeMutation.isPending}
                    onClick={() => activateSchemeMutation.mutate(scheme.id)}
                  >
                    Activate
                  </ActionButton>
                )}
              </div>

              {/* Component Chips by Term */}
              <div className="space-y-2 pt-1 border-t border-rule/60 text-xs">
                {scheme.terms.map((t) => {
                  const termComps = scheme.components.filter((c) => c.term === t.term);
                  return (
                    <div key={t.term} className="flex items-center justify-between gap-2">
                      <span className="font-medium text-ink-soft w-16">{t.term}:</span>
                      <div className="flex flex-wrap gap-1 flex-1">
                        {termComps.map((c) => (
                          <span
                            key={c.id}
                            className="px-2 py-0.5 rounded bg-surface border border-rule text-ink font-medium text-[11px]"
                            title={c.name}
                          >
                            {c.code} ({c.max_marks}M)
                          </span>
                        ))}
                      </div>
                      <span className="font-bold text-ink tabular">{t.total}M</span>
                    </div>
                  );
                })}
              </div>

              <div className="pt-1 text-right">
                <button
                  type="button"
                  onClick={() => setSelectedScheme(scheme)}
                  className="text-xs text-primary font-medium hover:underline"
                >
                  View full breakdown →
                </button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Section 2: Grading Scales */}
      <Card
        title="Grading Scales & Performance Bands"
        action={
          <ActionButton
            permission={WRITE_PERMISSION}
            onClick={() => setShowCreateScale(true)}
            className="!px-3 !py-1 text-xs"
          >
            + New Scale Version
          </ActionButton>
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          {scalesQuery.isLoading && (
            <div className="col-span-2 py-6 text-center text-sm text-ink-faint">
              Loading grading scales...
            </div>
          )}

          {scalesQuery.data?.map((scale) => (
            <div
              key={scale.id}
              className={`rounded-card border p-4 space-y-3 transition-colors ${
                scale.is_active ? "border-primary bg-primary/5" : "border-rule bg-surface"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-ink text-base flex items-center gap-2">
                    {scale.name} <span className="text-xs text-ink-faint font-normal">v{scale.version}</span>
                    {scale.is_active && <Pill status="paid">ACTIVE IN FORCE</Pill>}
                    {scale.frozen_at && <Pill status="neutral">FROZEN</Pill>}
                  </h3>
                  <p className="text-xs text-ink-soft mt-0.5">
                    {scale.bands.length} grade bands configured
                    {scale.frozen_at && ` • Frozen on ${new Date(scale.frozen_at).toLocaleDateString()}`}
                  </p>
                </div>

                {!scale.is_active && (
                  <ActionButton
                    permission={WRITE_PERMISSION}
                    className="px-2.5 py-1 text-xs"
                    disabled={activateScaleMutation.isPending}
                    onClick={() => activateScaleMutation.mutate(scale.id)}
                  >
                    Activate
                  </ActionButton>
                )}
              </div>

              {/* Quick Preview of Top Bands */}
              <div className="flex flex-wrap gap-1.5 pt-1 border-t border-rule/60 text-xs">
                {scale.bands.map((b) => (
                  <span
                    key={b.grade}
                    className="px-2 py-0.5 rounded bg-surface border border-rule text-ink font-mono font-medium text-[11px]"
                  >
                    <b>{b.grade}</b>: ≥{b.min_percent}%
                  </span>
                ))}
              </div>

              <div className="pt-1 text-right">
                <button
                  type="button"
                  onClick={() => setSelectedScale(scale)}
                  className="text-xs text-primary font-medium hover:underline"
                >
                  View full grade ladder →
                </button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Modal: View Scheme Detail */}
      {selectedScheme && (
        <Modal title={`Scheme Detail: ${selectedScheme.name}`} onClose={() => setSelectedScheme(null)}>
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-ink-soft">
              <span>Status: {selectedScheme.is_active ? "Active" : "Inactive"}</span>
              <span>Terms: {selectedScheme.terms.map((t) => `${t.term} (${t.total}M)`).join(", ")}</span>
            </div>

            <DataTable
              rows={selectedScheme.components}
              empty="No components configured."
              columns={[
                { key: "term", header: "Term", render: (c) => c.term },
                { key: "code", header: "Code", render: (c) => <b>{c.code}</b> },
                { key: "name", header: "Component Name", render: (c) => c.name },
                { key: "max", header: "Max Marks", render: (c) => `${c.max_marks} M`, align: "right" },
              ]}
            />
          </div>
        </Modal>
      )}

      {/* Modal: View Scale Detail */}
      {selectedScale && (
        <Modal title={`Grading Scale: ${selectedScale.name} v${selectedScale.version}`} onClose={() => setSelectedScale(null)}>
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-ink-soft">
              <span>Status: {selectedScale.is_active ? "Active in force" : "Inactive"}</span>
              <span>{selectedScale.frozen_at ? "Frozen against historical report cards" : "Editable"}</span>
            </div>

            <DataTable
              rows={selectedScale.bands}
              empty="No grade bands configured."
              columns={[
                { key: "grade", header: "Grade", render: (b) => <b className="text-primary font-mono">{b.grade}</b> },
                { key: "min", header: "Min Percentage", render: (b) => `≥ ${b.min_percent}%`, align: "right" },
                { key: "desc", header: "Remark / Performance Descriptor", render: (b) => b.description || "-" },
              ]}
            />
          </div>
        </Modal>
      )}

      {/* Modal: Create Assessment Scheme */}
      {showCreateScheme && (
        <CreateSchemeModal
          onClose={() => setShowCreateScheme(false)}
          onSaved={() => {
            setShowCreateScheme(false);
            qc.invalidateQueries({ queryKey: ["assessment-schemes"] });
          }}
        />
      )}

      {/* Modal: Create Grading Scale */}
      {showCreateScale && (
        <CreateScaleModal
          onClose={() => setShowCreateScale(false)}
          onSaved={() => {
            setShowCreateScale(false);
            qc.invalidateQueries({ queryKey: ["grading-scales"] });
          }}
        />
      )}
    </div>
  );
}

function CreateSchemeModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState("CBSE Assessment Structure");
  const [activate, setActivate] = useState(false);
  const [components, setComponents] = useState([
    { code: "PT", name: "Periodic Test", term: "Term 1", max_marks: 10 },
    { code: "NB", name: "Notebook", term: "Term 1", max_marks: 5 },
    { code: "SE", name: "Subject Enrichment", term: "Term 1", max_marks: 5 },
    { code: "TERM", name: "Term Examination", term: "Term 1", max_marks: 80 },
    { code: "PT", name: "Periodic Test", term: "Term 2", max_marks: 10 },
    { code: "NB", name: "Notebook", term: "Term 2", max_marks: 5 },
    { code: "SE", name: "Subject Enrichment", term: "Term 2", max_marks: 5 },
    { code: "TERM", name: "Term Examination", term: "Term 2", max_marks: 80 },
  ]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api.post("/admin/assessment-schemes" as "/admin/assessment-schemes", {
        name,
        activate,
        components,
      } as any),
    onSuccess: onSaved,
  });

  return (
    <Modal title="Create CBSE Assessment Scheme" onClose={onClose}>
      <div className="space-y-4">
        <FormField label="Scheme Name">
          <input
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. CBSE 2026-27 Assessment Structure"
          />
        </FormField>

        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="activateScheme"
            checked={activate}
            onChange={(e) => setActivate(e.target.checked)}
            className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
          />
          <label htmlFor="activateScheme" className="text-xs font-medium text-ink cursor-pointer">
            Put in force immediately for the current academic year
          </label>
        </div>

        <div className="space-y-2 pt-2 border-t border-rule">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-ink">Components Breakdown:</span>
            <span className="text-ink-soft">Pre-filled with standard CBSE 100M per term</span>
          </div>

          <div className="max-h-60 overflow-y-auto border border-rule rounded-input divide-y divide-rule text-xs">
            {components.map((c, i) => (
              <div key={i} className="p-2.5 flex items-center justify-between gap-2 bg-ground/30">
                <span className="font-medium text-ink-soft w-16">{c.term}</span>
                <span className="font-bold text-ink w-16">{c.code}</span>
                <span className="flex-1 text-ink">{c.name}</span>
                <span className="tabular font-semibold text-ink w-16 text-right">{c.max_marks} M</span>
              </div>
            ))}
          </div>
        </div>

        {saveMutation.isError && (
          <p className="text-xs text-danger">{errorText(saveMutation.error)}</p>
        )}

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button type="button" className="px-4 py-2 text-sm text-ink-soft hover:text-ink" onClick={onClose}>
            Cancel
          </button>
          <ActionButton
            permission={WRITE_PERMISSION}
            disabled={!name.trim() || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? "Creating..." : "Create Scheme"}
          </ActionButton>
        </div>
      </div>
    </Modal>
  );
}

function CreateScaleModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState("CBSE 8-Point Scale");
  const [activate, setActivate] = useState(false);
  const [bands] = useState([
    { min_percent: 91, grade: "A1", description: "Top 1/8th of passed candidates" },
    { min_percent: 81, grade: "A2", description: "Next 1/8th of passed candidates" },
    { min_percent: 71, grade: "B1", description: "Next 1/8th of passed candidates" },
    { min_percent: 61, grade: "B2", description: "Next 1/8th of passed candidates" },
    { min_percent: 51, grade: "C1", description: "Next 1/8th of passed candidates" },
    { min_percent: 41, grade: "C2", description: "Next 1/8th of passed candidates" },
    { min_percent: 33, grade: "D", description: "Eligible for improvement" },
    { min_percent: 0, grade: "E", description: "Essential repeat" },
  ]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api.post("/admin/grading-scales" as "/admin/grading-scales", {
        name,
        activate,
        bands,
      } as any),
    onSuccess: onSaved,
  });

  return (
    <Modal title="Create / Revise CBSE Grading Scale" onClose={onClose}>
      <div className="space-y-4">
        <FormField label="Scale Name">
          <input
            className={inputClass}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. CBSE 8-Point Scale"
          />
        </FormField>

        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="activateScale"
            checked={activate}
            onChange={(e) => setActivate(e.target.checked)}
            className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
          />
          <label htmlFor="activateScale" className="text-xs font-medium text-ink cursor-pointer">
            Put in force immediately for the school
          </label>
        </div>

        <div className="space-y-2 pt-2 border-t border-rule">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-ink">Bands Ladder (CBSE Standard):</span>
            <span className="text-ink-soft">Floor at 0% required</span>
          </div>

          <div className="max-h-60 overflow-y-auto border border-rule rounded-input divide-y divide-rule text-xs">
            {bands.map((b) => (
              <div key={b.grade} className="p-2 flex items-center justify-between gap-2 bg-ground/30">
                <span className="font-bold text-primary font-mono w-10">{b.grade}</span>
                <span className="tabular font-medium text-ink w-20">≥ {b.min_percent}%</span>
                <span className="flex-1 text-ink-faint text-[11px] truncate">{b.description}</span>
              </div>
            ))}
          </div>
        </div>

        {saveMutation.isError && (
          <p className="text-xs text-danger">{errorText(saveMutation.error)}</p>
        )}

        <div className="flex justify-end gap-2 pt-2 border-t border-rule">
          <button type="button" className="px-4 py-2 text-sm text-ink-soft hover:text-ink" onClick={onClose}>
            Cancel
          </button>
          <ActionButton
            permission={WRITE_PERMISSION}
            disabled={!name.trim() || saveMutation.isPending}
            onClick={() => saveMutation.mutate()}
          >
            {saveMutation.isPending ? "Creating..." : "Save Scale Version"}
          </ActionButton>
        </div>
      </div>
    </Modal>
  );
}
