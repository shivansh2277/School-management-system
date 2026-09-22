import React, { useState, useEffect } from "react";
import { ApplicationDetail } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  application: ApplicationDetail;
  onSave: (data: Partial<ApplicationDetail>) => Promise<void>;
  isSaving: boolean;
}

export function DossierStudentDetails({ application, onSave, isSaving }: Props) {
  const [formData, setFormData] = useState({
    first_name: application.first_name || "",
    middle_name: application.middle_name || "",
    last_name: application.last_name || "",
    date_of_birth: application.date_of_birth || "",
    gender: application.gender || "male",
    nationality: application.nationality || "Indian",
    religion: application.religion || "Hindu",
    caste_category: application.caste_category || "General",
    mother_tongue: application.mother_tongue || "Hindi",
    place_of_birth: application.place_of_birth || "",
    identification_marks: application.identification_marks || "",
    is_single_child: application.is_single_child || false,
    aadhaar_last4: application.aadhaar_last4 || "",
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setFormData({
      first_name: application.first_name || "",
      middle_name: application.middle_name || "",
      last_name: application.last_name || "",
      date_of_birth: application.date_of_birth || "",
      gender: application.gender || "male",
      nationality: application.nationality || "Indian",
      religion: application.religion || "Hindu",
      caste_category: application.caste_category || "General",
      mother_tongue: application.mother_tongue || "Hindi",
      place_of_birth: application.place_of_birth || "",
      identification_marks: application.identification_marks || "",
      is_single_child: application.is_single_child || false,
      aadhaar_last4: application.aadhaar_last4 || "",
    });
  }, [application]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    if (formData.aadhaar_last4 && !/^\d{4}$/.test(formData.aadhaar_last4.trim())) {
      setErrorMsg("Aadhaar last 4 digits must contain exactly 4 numeric digits.");
      return;
    }

    try {
      await onSave({
        first_name: formData.first_name.trim(),
        middle_name: formData.middle_name.trim() || null,
        last_name: formData.last_name.trim(),
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        nationality: formData.nationality.trim() || null,
        religion: formData.religion.trim() || null,
        caste_category: formData.caste_category.trim() || null,
        mother_tongue: formData.mother_tongue.trim() || null,
        place_of_birth: formData.place_of_birth.trim() || null,
        identification_marks: formData.identification_marks.trim() || null,
        is_single_child: formData.is_single_child,
        aadhaar_last4: formData.aadhaar_last4.trim() || null,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to update student details.");
    }
  };

  return (
    <Card title="1. Student / Child Personal & Identity Details">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name Fields */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="First Name *">
            <input
              type="text"
              required
              className={inputClass}
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              placeholder="e.g. Aarav"
            />
          </FormField>
          <FormField label="Middle Name">
            <input
              type="text"
              className={inputClass}
              value={formData.middle_name}
              onChange={(e) => setFormData({ ...formData, middle_name: e.target.value })}
              placeholder="e.g. Kumar (optional)"
            />
          </FormField>
          <FormField label="Last Name / Surname *">
            <input
              type="text"
              required
              className={inputClass}
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              placeholder="e.g. Sharma"
            />
          </FormField>
        </div>

        {/* DOB, Gender, Place of Birth */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="Date of Birth *">
            <input
              type="date"
              required
              className={inputClass}
              value={formData.date_of_birth}
              onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
            />
          </FormField>
          <FormField label="Gender *">
            <select
              className={inputClass}
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </FormField>
          <FormField label="Place of Birth">
            <input
              type="text"
              className={inputClass}
              value={formData.place_of_birth}
              onChange={(e) => setFormData({ ...formData, place_of_birth: e.target.value })}
              placeholder="e.g. Lucknow"
            />
          </FormField>
        </div>

        {/* Demographics */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <FormField label="Nationality">
            <input
              type="text"
              className={inputClass}
              value={formData.nationality}
              onChange={(e) => setFormData({ ...formData, nationality: e.target.value })}
              placeholder="Indian"
            />
          </FormField>
          <FormField label="Religion">
            <select
              className={inputClass}
              value={formData.religion}
              onChange={(e) => setFormData({ ...formData, religion: e.target.value })}
            >
              <option value="Hindu">Hindu</option>
              <option value="Muslim">Muslim</option>
              <option value="Sikh">Sikh</option>
              <option value="Christian">Christian</option>
              <option value="Jain">Jain</option>
              <option value="Buddhist">Buddhist</option>
              <option value="Other">Other</option>
            </select>
          </FormField>
          <FormField label="Social Category">
            <select
              className={inputClass}
              value={formData.caste_category}
              onChange={(e) => setFormData({ ...formData, caste_category: e.target.value })}
            >
              <option value="General">General</option>
              <option value="OBC">OBC</option>
              <option value="SC">SC</option>
              <option value="ST">ST</option>
              <option value="EWS">EWS</option>
            </select>
          </FormField>
          <FormField label="Mother Tongue">
            <input
              type="text"
              className={inputClass}
              value={formData.mother_tongue}
              onChange={(e) => setFormData({ ...formData, mother_tongue: e.target.value })}
              placeholder="e.g. Hindi"
            />
          </FormField>
        </div>

        {/* Identity & Flags */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <FormField label="Aadhaar Card (Last 4 Digits)">
            <div className="relative">
              <input
                type="text"
                maxLength={4}
                pattern="\d{4}"
                className={inputClass}
                value={formData.aadhaar_last4}
                onChange={(e) => setFormData({ ...formData, aadhaar_last4: e.target.value.replace(/\D/g, "") })}
                placeholder="4 digits e.g. 4321"
              />
              <span className="absolute right-2.5 top-2 text-2xs font-mono text-ink-faint">
                •••• {formData.aadhaar_last4 || "XXXX"}
              </span>
            </div>
          </FormField>

          <FormField label="Visible Identification Marks">
            <input
              type="text"
              className={inputClass}
              value={formData.identification_marks}
              onChange={(e) => setFormData({ ...formData, identification_marks: e.target.value })}
              placeholder="e.g. Mole on right cheek"
            />
          </FormField>

          <div className="flex items-center pt-6">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-ink font-medium">
              <input
                type="checkbox"
                className="w-4 h-4 rounded text-primary"
                checked={formData.is_single_child}
                onChange={(e) => setFormData({ ...formData, is_single_child: e.target.checked })}
              />
              <span>Single Child (Only Girl / Boy)</span>
            </label>
          </div>
        </div>

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Student / Child personal details saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.application.write"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving details..." : "Save Student Details"}
          </ActionButton>
        </div>
      </form>
    </Card>
  );
}
