import React, { useState, useEffect } from "react";
import { ApplicationDetail } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  application: ApplicationDetail;
  onSave: (data: Partial<ApplicationDetail>) => Promise<void>;
  isSaving: boolean;
}

export function DossierDeclarations({ application, onSave, isSaving }: Props) {
  const existing = application.declarations || {};

  const [formData, setFormData] = useState({
    information_accuracy: existing.information_accuracy !== false,
    school_rules_accepted: existing.school_rules_accepted !== false,
    data_processing_consent: existing.data_processing_consent !== false,
    transport_undertaking: existing.transport_undertaking !== false,
    parent_signature_name:
      existing.parent_signature_name ||
      application.guardians?.find((g) => g.is_primary)?.full_name ||
      "",
    declared_on:
      existing.declared_on || new Date().toISOString().slice(0, 10),
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const decl = application.declarations || {};
    setFormData({
      information_accuracy: decl.information_accuracy !== false,
      school_rules_accepted: decl.school_rules_accepted !== false,
      data_processing_consent: decl.data_processing_consent !== false,
      transport_undertaking: decl.transport_undertaking !== false,
      parent_signature_name:
        decl.parent_signature_name ||
        application.guardians?.find((g) => g.is_primary)?.full_name ||
        "",
      declared_on:
        decl.declared_on || new Date().toISOString().slice(0, 10),
    });
  }, [application]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    if (!formData.information_accuracy) {
      setErrorMsg("Information accuracy declaration is mandatory.");
      return;
    }
    if (!formData.parent_signature_name.trim()) {
      setErrorMsg("Please enter the name of the parent / guardian signing this declaration.");
      return;
    }

    try {
      await onSave({
        declarations: {
          information_accuracy: formData.information_accuracy,
          school_rules_accepted: formData.school_rules_accepted,
          data_processing_consent: formData.data_processing_consent,
          transport_undertaking: formData.transport_undertaking,
          parent_signature_name: formData.parent_signature_name.trim(),
          declared_on: formData.declared_on,
        },
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to save declarations.");
    }
  };

  return (
    <Card title="8. Parental Declarations, Code of Conduct & Digital Sign-off">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-xs text-ink-soft">
          Statutory declarations required for student enrollment under CBSE Bye-Laws.
        </p>

        <div className="space-y-3 bg-ground p-4 rounded-input border border-rule text-xs">
          <label className="flex items-start gap-2.5 cursor-pointer text-ink font-medium">
            <input
              type="checkbox"
              required
              className="w-4 h-4 rounded text-primary mt-0.5"
              checked={formData.information_accuracy}
              onChange={(e) =>
                setFormData({ ...formData, information_accuracy: e.target.checked })
              }
            />
            <span>
              <strong>Information Accuracy Undertaking:</strong> I hereby declare that all information furnished in this admission application is true, complete, and accurate to the best of my knowledge. I understand that any false statement or concealed information may result in forfeiture of admission.
            </span>
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer text-ink font-medium">
            <input
              type="checkbox"
              required
              className="w-4 h-4 rounded text-primary mt-0.5"
              checked={formData.school_rules_accepted}
              onChange={(e) =>
                setFormData({ ...formData, school_rules_accepted: e.target.checked })
              }
            />
            <span>
              <strong>School Code of Conduct & Rules:</strong> I agree to abide by the disciplinary rules, attendance thresholds (75% minimum), examination guidelines, and fee schedules of Sunrise Public School.
            </span>
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer text-ink font-medium">
            <input
              type="checkbox"
              required
              className="w-4 h-4 rounded text-primary mt-0.5"
              checked={formData.data_processing_consent}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  data_processing_consent: e.target.checked,
                })
              }
            />
            <span>
              <strong>Data Processing & Educational Portal Consent:</strong> I authorize the school to store and process student academic records, attendance, and emergency demographic data in the school ERP and CBSE reporting databases.
            </span>
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer text-ink font-medium">
            <input
              type="checkbox"
              className="w-4 h-4 rounded text-primary mt-0.5"
              checked={formData.transport_undertaking}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  transport_undertaking: e.target.checked,
                })
              }
            />
            <span>
              <strong>Transport & Bus Service Undertaking:</strong> I understand that school bus routes and stops are scheduled centrally by school management and may not be altered without prior written administrative approval.
            </span>
          </label>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <FormField label="Parent / Guardian Digital Signature (Full Name) *">
            <input
              type="text"
              required
              className={inputClass}
              value={formData.parent_signature_name}
              onChange={(e) =>
                setFormData({ ...formData, parent_signature_name: e.target.value })
              }
              placeholder="e.g. Rajesh Sharma"
            />
          </FormField>

          <FormField label="Date of Declaration *">
            <input
              type="date"
              required
              className={inputClass}
              value={formData.declared_on}
              onChange={(e) =>
                setFormData({ ...formData, declared_on: e.target.value })
              }
            />
          </FormField>
        </div>

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Declarations and parental undertaking saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.application.write"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving declarations..." : "Save Declarations"}
          </ActionButton>
        </div>
      </form>
    </Card>
  );
}
