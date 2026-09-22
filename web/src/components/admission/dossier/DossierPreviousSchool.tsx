import React, { useState, useEffect } from "react";
import { ApplicationDetail } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  application: ApplicationDetail;
  onSave: (data: Partial<ApplicationDetail>) => Promise<void>;
  isSaving: boolean;
}

export function DossierPreviousSchool({ application, onSave, isSaving }: Props) {
  const existing = application.previous_school || {};

  const [isFreshAdmission, setIsFreshAdmission] = useState(
    existing.is_fresh_admission === true ||
      (!existing.school_name &&
        (application.class_applying_for === "1" ||
          application.class_applying_for.toLowerCase().includes("nursery") ||
          application.class_applying_for.toLowerCase().includes("kg")))
  );

  const [formData, setFormData] = useState({
    school_name: existing.school_name || "",
    board: existing.board || "CBSE",
    last_class_passed: existing.last_class_passed || existing.last_class || "",
    tc_number: existing.tc_number || "",
    tc_date: existing.tc_date || "",
    percentage_or_grade: existing.percentage_or_grade || existing.grade || "",
    reason_for_leaving: existing.reason_for_leaving || "",
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const prev = application.previous_school || {};
    setFormData({
      school_name: prev.school_name || "",
      board: prev.board || "CBSE",
      last_class_passed: prev.last_class_passed || prev.last_class || "",
      tc_number: prev.tc_number || "",
      tc_date: prev.tc_date || "",
      percentage_or_grade: prev.percentage_or_grade || prev.grade || "",
      reason_for_leaving: prev.reason_for_leaving || "",
    });
    setIsFreshAdmission(prev.is_fresh_admission === true);
  }, [application]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    const payload = isFreshAdmission
      ? {
          is_fresh_admission: true,
          school_name: "N/A (Fresh Admission)",
          board: "None",
          last_class_passed: "None",
        }
      : {
          is_fresh_admission: false,
          school_name: formData.school_name.trim(),
          board: formData.board.trim() || "CBSE",
          last_class_passed: formData.last_class_passed.trim(),
          last_class: formData.last_class_passed.trim(),
          tc_number: formData.tc_number.trim() || null,
          tc_date: formData.tc_date || null,
          percentage_or_grade: formData.percentage_or_grade.trim() || null,
          reason_for_leaving: formData.reason_for_leaving.trim() || null,
        };

    try {
      await onSave({ previous_school: payload });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to update previous school details.");
    }
  };

  return (
    <Card title="6. Previous School & Academic History">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="p-3 bg-ground rounded border border-rule">
          <label className="flex items-center gap-2 cursor-pointer text-sm font-semibold text-ink">
            <input
              type="checkbox"
              className="w-4 h-4 rounded text-primary"
              checked={isFreshAdmission}
              onChange={(e) => setIsFreshAdmission(e.target.checked)}
            />
            <span>Fresh Entry / First-Time School Admission (e.g. Nursery, KG, or Class 1 Fresh)</span>
          </label>
          <p className="text-2xs text-ink-soft mt-1 ml-6">
            If checked, Transfer Certificate (TC) and previous school records are exempt.
          </p>
        </div>

        {!isFreshAdmission && (
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <FormField label="Previous School Name *">
                <input
                  type="text"
                  required={!isFreshAdmission}
                  className={inputClass}
                  value={formData.school_name}
                  onChange={(e) => setFormData({ ...formData, school_name: e.target.value })}
                  placeholder="e.g. Delhi Public School / Little Angels"
                />
              </FormField>

              <FormField label="Affiliated Education Board">
                <select
                  className={inputClass}
                  value={formData.board}
                  onChange={(e) => setFormData({ ...formData, board: e.target.value })}
                >
                  <option value="CBSE">CBSE (Central Board)</option>
                  <option value="ICSE">ICSE / CISCE</option>
                  <option value="UP Board">UP Board (Uttar Pradesh)</option>
                  <option value="Other State Board">Other State Board</option>
                  <option value="IB">IB (International Baccalaureate)</option>
                  <option value="Cambridge">Cambridge / IGCSE</option>
                </select>
              </FormField>

              <FormField label="Last Class Passed / Attended *">
                <input
                  type="text"
                  required={!isFreshAdmission}
                  className={inputClass}
                  value={formData.last_class_passed}
                  onChange={(e) =>
                    setFormData({ ...formData, last_class_passed: e.target.value })
                  }
                  placeholder="e.g. Class 5 or UKG"
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <FormField label="Transfer Certificate (TC) Number">
                <input
                  type="text"
                  className={inputClass}
                  value={formData.tc_number}
                  onChange={(e) => setFormData({ ...formData, tc_number: e.target.value })}
                  placeholder="e.g. TC-2026-0881"
                />
              </FormField>

              <FormField label="TC Issue Date">
                <input
                  type="date"
                  className={inputClass}
                  value={formData.tc_date}
                  onChange={(e) => setFormData({ ...formData, tc_date: e.target.value })}
                />
              </FormField>

              <FormField label="Marks (%) or Grade Obtained">
                <input
                  type="text"
                  className={inputClass}
                  value={formData.percentage_or_grade}
                  onChange={(e) =>
                    setFormData({ ...formData, percentage_or_grade: e.target.value })
                  }
                  placeholder="e.g. 91.5% or A1"
                />
              </FormField>
            </div>

            <FormField label="Reason for Leaving Previous School">
              <input
                type="text"
                className={inputClass}
                value={formData.reason_for_leaving}
                onChange={(e) =>
                  setFormData({ ...formData, reason_for_leaving: e.target.value })
                }
                placeholder="e.g. Parent job relocation to Lucknow / Change of residence"
              />
            </FormField>
          </div>
        )}

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Previous school record saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.application.write"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving school record..." : "Save Previous School Record"}
          </ActionButton>
        </div>
      </form>
    </Card>
  );
}
