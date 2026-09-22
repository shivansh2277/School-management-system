import React, { useState, useEffect } from "react";
import { ApplicationMedical } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  applicationId: number;
  medical: ApplicationMedical | null | undefined;
  onSave: (data: ApplicationMedical) => Promise<void>;
  isSaving: boolean;
}

export function DossierMedical({
  applicationId,
  medical,
  onSave,
  isSaving,
}: Props) {
  const [formData, setFormData] = useState<ApplicationMedical>({
    blood_group: "B+",
    known_allergies: "",
    chronic_conditions: "",
    regular_medication: "",
    physical_disability: "",
    learning_needs: "",
    vision_hearing_notes: "",
    emergency_doctor: "",
    emergency_doctor_phone: "",
    consent_for_emergency_treatment: true,
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (medical) {
      setFormData({
        blood_group: medical.blood_group || "B+",
        known_allergies: medical.known_allergies || "",
        chronic_conditions: medical.chronic_conditions || "",
        regular_medication: medical.regular_medication || "",
        physical_disability: medical.physical_disability || "",
        learning_needs: medical.learning_needs || "",
        vision_hearing_notes: medical.vision_hearing_notes || "",
        emergency_doctor: medical.emergency_doctor || "",
        emergency_doctor_phone: medical.emergency_doctor_phone || "",
        consent_for_emergency_treatment:
          medical.consent_for_emergency_treatment !== false,
      });
    }
  }, [medical]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    try {
      await onSave({
        blood_group: formData.blood_group || null,
        known_allergies: formData.known_allergies?.trim() || null,
        chronic_conditions: formData.chronic_conditions?.trim() || null,
        regular_medication: formData.regular_medication?.trim() || null,
        physical_disability: formData.physical_disability?.trim() || null,
        learning_needs: formData.learning_needs?.trim() || null,
        vision_hearing_notes: formData.vision_hearing_notes?.trim() || null,
        emergency_doctor: formData.emergency_doctor?.trim() || null,
        emergency_doctor_phone: formData.emergency_doctor_phone?.trim() || null,
        consent_for_emergency_treatment: Boolean(
          formData.consent_for_emergency_treatment
        ),
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to update medical details.");
    }
  };

  return (
    <Card title="7. Student Medical Profile & Emergency First-Aid Authorisation">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-xs text-ink-soft">
          Permission-gated medical record kept confidential for infirmary and emergency hospital reference.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="Blood Group *">
            <select
              className={inputClass}
              value={formData.blood_group || ""}
              onChange={(e) => setFormData({ ...formData, blood_group: e.target.value })}
            >
              <option value="A+">A Positive (A+)</option>
              <option value="A-">A Negative (A-)</option>
              <option value="B+">B Positive (B+)</option>
              <option value="B-">B Negative (B-)</option>
              <option value="O+">O Positive (O+)</option>
              <option value="O-">O Negative (O-)</option>
              <option value="AB+">AB Positive (AB+)</option>
              <option value="AB-">AB Negative (AB-)</option>
            </select>
          </FormField>

          <FormField label="Family / Emergency Doctor Name">
            <input
              type="text"
              className={inputClass}
              value={formData.emergency_doctor || ""}
              onChange={(e) =>
                setFormData({ ...formData, emergency_doctor: e.target.value })
              }
              placeholder="e.g. Dr. V. K. Gupta"
            />
          </FormField>

          <FormField label="Doctor Contact Number">
            <input
              type="tel"
              className={inputClass}
              value={formData.emergency_doctor_phone || ""}
              onChange={(e) =>
                setFormData({ ...formData, emergency_doctor_phone: e.target.value })
              }
              placeholder="e.g. 9415012345"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Known Allergies (Food / Medication / Environmental)">
            <textarea
              rows={2}
              className={inputClass}
              value={formData.known_allergies || ""}
              onChange={(e) =>
                setFormData({ ...formData, known_allergies: e.target.value })
              }
              placeholder="e.g. Mild peanut sensitivity, dust allergy"
            />
          </FormField>

          <FormField label="Chronic Conditions / Long-term Medical History">
            <textarea
              rows={2}
              className={inputClass}
              value={formData.chronic_conditions || ""}
              onChange={(e) =>
                setFormData({ ...formData, chronic_conditions: e.target.value })
              }
              placeholder="e.g. Asthma, diabetes, or None"
            />
          </FormField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="Regular Daily Medication">
            <input
              type="text"
              className={inputClass}
              value={formData.regular_medication || ""}
              onChange={(e) =>
                setFormData({ ...formData, regular_medication: e.target.value })
              }
              placeholder="e.g. Inhaler as needed"
            />
          </FormField>

          <FormField label="Vision / Hearing Notes">
            <input
              type="text"
              className={inputClass}
              value={formData.vision_hearing_notes || ""}
              onChange={(e) =>
                setFormData({ ...formData, vision_hearing_notes: e.target.value })
              }
              placeholder="e.g. Wears spectacles (-1.25D)"
            />
          </FormField>

          <FormField label="Special Learning / Support Needs">
            <input
              type="text"
              className={inputClass}
              value={formData.learning_needs || ""}
              onChange={(e) =>
                setFormData({ ...formData, learning_needs: e.target.value })
              }
              placeholder="e.g. None or Attention support"
            />
          </FormField>
        </div>

        <div className="p-3 bg-ground rounded border border-rule">
          <label className="flex items-center gap-2 cursor-pointer text-sm font-semibold text-ink">
            <input
              type="checkbox"
              className="w-4 h-4 rounded text-primary"
              checked={formData.consent_for_emergency_treatment}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  consent_for_emergency_treatment: e.target.checked,
                })
              }
            />
            <span>Consent for Emergency Medical First Aid & Hospitalization</span>
          </label>
          <p className="text-2xs text-ink-soft mt-1 ml-6">
            In the event of an unforeseen medical emergency where parents cannot be immediately reached, the school infirmary staff is authorized to provide emergency medical care and hospital transport.
          </p>
        </div>

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Medical details saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.medical.read"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving medical profile..." : "Save Medical Profile"}
          </ActionButton>
        </div>
      </form>
    </Card>
  );
}
