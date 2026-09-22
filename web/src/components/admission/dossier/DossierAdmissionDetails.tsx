import React, { useState, useEffect } from "react";
import { ApplicationDetail } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  application: ApplicationDetail;
  availableClasses: { id: string | number; class_name: string }[];
  onSave: (data: Partial<ApplicationDetail>) => Promise<void>;
  isSaving: boolean;
}

export function DossierAdmissionDetails({
  application,
  availableClasses,
  onSave,
  isSaving,
}: Props) {
  const [formData, setFormData] = useState({
    class_applying_for: application.class_applying_for || "1",
    stream: application.stream || "",
    second_language: application.second_language || "Hindi",
    optional_subject: application.optional_subject || "",
    preferred_section: application.preferred_section || "",
    admission_category: application.admission_category || "general",
    transport_required: application.transport_required || false,
    age_override_reason: application.age_override_reason || "",
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setFormData({
      class_applying_for: application.class_applying_for || "1",
      stream: application.stream || "",
      second_language: application.second_language || "Hindi",
      optional_subject: application.optional_subject || "",
      preferred_section: application.preferred_section || "",
      admission_category: application.admission_category || "general",
      transport_required: application.transport_required || false,
      age_override_reason: application.age_override_reason || "",
    });
  }, [application]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    try {
      await onSave({
        class_applying_for: formData.class_applying_for,
        stream: formData.stream.trim() || null,
        second_language: formData.second_language.trim() || null,
        optional_subject: formData.optional_subject.trim() || null,
        preferred_section: formData.preferred_section.trim() || null,
        admission_category: formData.admission_category as any,
        transport_required: formData.transport_required,
        age_override_reason: formData.age_override_reason.trim() || null,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to update admission preferences.");
    }
  };

  const isHigherSecondary =
    formData.class_applying_for === "11" ||
    formData.class_applying_for === "12" ||
    formData.class_applying_for.toLowerCase().includes("11") ||
    formData.class_applying_for.toLowerCase().includes("12");

  return (
    <Card title="2. Admission & Academic Preferences">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="Class Applying For *">
            <select
              className={inputClass}
              value={formData.class_applying_for}
              onChange={(e) => setFormData({ ...formData, class_applying_for: e.target.value })}
            >
              {availableClasses.map((c) => (
                <option key={String(c.id)} value={c.class_name}>
                  Class {c.class_name}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Academic Stream (for Class 11-12)">
            <input
              type="text"
              className={inputClass}
              value={formData.stream}
              onChange={(e) => setFormData({ ...formData, stream: e.target.value })}
              placeholder={isHigherSecondary ? "e.g. Science (PCM), Commerce" : "General / N/A"}
            />
          </FormField>

          <FormField label="Admission Category Claimed *">
            <select
              className={inputClass}
              value={formData.admission_category}
              onChange={(e) => setFormData({ ...formData, admission_category: e.target.value })}
            >
              <option value="general">General</option>
              <option value="sibling">Sibling (Concession Claim)</option>
              <option value="staff_ward">Staff Ward (Faculty Claim)</option>
              <option value="rte">RTE (Right to Education 25%)</option>
              <option value="management">Management Quota</option>
              <option value="sports">Sports / Talent Quota</option>
              <option value="alumni_child">Alumni Child</option>
            </select>
          </FormField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="Second Language Choice">
            <select
              className={inputClass}
              value={formData.second_language}
              onChange={(e) => setFormData({ ...formData, second_language: e.target.value })}
            >
              <option value="Hindi">Hindi</option>
              <option value="Sanskrit">Sanskrit</option>
              <option value="French">French</option>
              <option value="Urdu">Urdu</option>
              <option value="German">German</option>
            </select>
          </FormField>

          <FormField label="Optional / Elective Subject">
            <input
              type="text"
              className={inputClass}
              value={formData.optional_subject}
              onChange={(e) => setFormData({ ...formData, optional_subject: e.target.value })}
              placeholder="e.g. Computer Science, Art, Physical Ed"
            />
          </FormField>

          <FormField label="Preferred Section (Request only)">
            <input
              type="text"
              maxLength={4}
              className={inputClass}
              value={formData.preferred_section}
              onChange={(e) => setFormData({ ...formData, preferred_section: e.target.value.toUpperCase() })}
              placeholder="e.g. A, B, or Auto"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <div className="p-3 bg-ground rounded border border-rule">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-ink font-medium">
              <input
                type="checkbox"
                className="w-4 h-4 rounded text-primary"
                checked={formData.transport_required}
                onChange={(e) => setFormData({ ...formData, transport_required: e.target.checked })}
              />
              <span>Requires School Bus / Transportation Service</span>
            </label>
            <p className="text-2xs text-ink-soft mt-1 ml-6">
              Subject to route and pickup point seat availability at session start.
            </p>
          </div>

          <FormField label="Age Override Reason (if applicant is outside standard age band)">
            <input
              type="text"
              className={inputClass}
              value={formData.age_override_reason}
              onChange={(e) => setFormData({ ...formData, age_override_reason: e.target.value })}
              placeholder="e.g. Approved by Principal on transfer grounds"
            />
          </FormField>
        </div>

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Admission preferences saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.application.write"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving preferences..." : "Save Admission Preferences"}
          </ActionButton>
        </div>
      </form>
    </Card>
  );
}
