import React, { useState, useEffect } from "react";
import { ApplicationDetail, GuardianOut } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  application: ApplicationDetail;
  onSave: (guardians: GuardianOut[]) => Promise<void>;
  isSaving: boolean;
}

export function DossierGuardians({ application, onSave, isSaving }: Props) {
  const [guardians, setGuardians] = useState<GuardianOut[]>([]);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Income Bands standard for CBSE school admission forms
  const incomeBands = [
    "< ₹3 Lakhs",
    "₹3L - ₹8L",
    "₹8L - ₹15L",
    "₹15L - ₹25L",
    "> ₹25 Lakhs",
  ];

  const qualifications = [
    "Post Graduate (Master's / Ph.D / MD / MS)",
    "Graduate (B.Tech / B.E / MBBS / B.Com / B.Sc / B.A)",
    "Professional (CA / CS / CMA / Law)",
    "Diploma / Vocational",
    "Higher Secondary (10+2)",
    "Secondary (Class 10)",
    "Other",
  ];

  // Initialize from application or populate default Father & Mother slots if empty
  useEffect(() => {
    if (application.guardians && application.guardians.length > 0) {
      setGuardians(application.guardians);
    } else {
      // Default initial slots for Father and Mother to make filling effortless
      setGuardians([
        {
          id: 0,
          relation: "father",
          full_name: "",
          date_of_birth: "",
          qualification: "Graduate (B.Tech / B.E / MBBS / B.Com / B.Sc / B.A)",
          occupation: "Salaried Professional",
          designation: "",
          organisation: "",
          annual_income_band: "₹8L - ₹15L",
          office_address: "",
          mobile: "",
          alternate_mobile: "",
          email: "",
          is_primary: true,
          is_emergency_contact: true,
          is_authorised_for_pickup: true,
          is_school_alumnus: false,
          is_school_staff: false,
          employee_id: null,
        },
        {
          id: -1,
          relation: "mother",
          full_name: "",
          date_of_birth: "",
          qualification: "Graduate (B.Tech / B.E / MBBS / B.Com / B.Sc / B.A)",
          occupation: "Homemaker",
          designation: "",
          organisation: "",
          annual_income_band: "< ₹3 Lakhs",
          office_address: "",
          mobile: "",
          alternate_mobile: "",
          email: "",
          is_primary: false,
          is_emergency_contact: true,
          is_authorised_for_pickup: true,
          is_school_alumnus: false,
          is_school_staff: false,
          employee_id: null,
        },
      ]);
    }
  }, [application]);

  const updateGuardian = (index: number, patch: Partial<GuardianOut>) => {
    setGuardians((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      // If setting this one as primary, ensure other guardians are not primary
      if (patch.is_primary === true) {
        next.forEach((g, i) => {
          if (i !== index) g.is_primary = false;
        });
      }
      return next;
    });
  };

  const addGuardian = (relation: "father" | "mother" | "guardian" = "guardian") => {
    setGuardians((prev) => [
      ...prev,
      {
        id: -1 * (prev.length + 1),
        relation,
        full_name: "",
        date_of_birth: "",
        qualification: "Graduate (B.Tech / B.E / MBBS / B.Com / B.Sc / B.A)",
        occupation: "Private Service",
        designation: "",
        organisation: "",
        annual_income_band: "₹3L - ₹8L",
        office_address: "",
        mobile: "",
        alternate_mobile: "",
        email: "",
        is_primary: prev.length === 0,
        is_emergency_contact: false,
        is_authorised_for_pickup: false,
        is_school_alumnus: false,
        is_school_staff: false,
        employee_id: null,
      },
    ]);
  };

  const removeGuardian = (index: number) => {
    if (guardians.length <= 1) {
      setErrorMsg("At least one parent/guardian contact is required.");
      return;
    }
    setGuardians((prev) => {
      const next = prev.filter((_, i) => i !== index);
      if (!next.some((g) => g.is_primary) && next.length > 0) {
        next[0].is_primary = true;
      }
      return next;
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    // Filter out completely blank un-filled additional guardians
    const filledGuardians = guardians.filter(
      (g) => g.full_name.trim().length > 0 || g.mobile.trim().length > 0
    );

    if (filledGuardians.length === 0) {
      setErrorMsg("Please provide at least one guardian with full name and mobile number.");
      return;
    }

    for (const g of filledGuardians) {
      if (!g.full_name.trim()) {
        setErrorMsg(`Full Name is required for ${g.relation}.`);
        return;
      }
      if (!g.mobile.trim() || g.mobile.trim().length < 8) {
        setErrorMsg(`Valid mobile number is required for ${g.full_name} (${g.relation}).`);
        return;
      }
    }

    const primaryCount = filledGuardians.filter((g) => g.is_primary).length;
    if (primaryCount !== 1) {
      setErrorMsg("Exactly one guardian must be designated as the Primary Contact.");
      return;
    }

    try {
      await onSave(
        filledGuardians.map((g) => ({
          ...g,
          full_name: g.full_name.trim(),
          mobile: g.mobile.trim(),
          alternate_mobile: g.alternate_mobile?.trim() || null,
          email: g.email?.trim() || null,
          date_of_birth: g.date_of_birth || null,
          qualification: g.qualification?.trim() || null,
          occupation: g.occupation?.trim() || null,
          designation: g.designation?.trim() || null,
          organisation: g.organisation?.trim() || null,
          annual_income_band: g.annual_income_band || null,
          office_address: g.office_address?.trim() || null,
        }))
      );
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to save guardians information.");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-bold text-ink">
            3. Parents & Legal Guardians Information
          </h3>
          <p className="text-xs text-ink-soft">
            Complete records for Father, Mother, and Legal Guardians. Exactly one must be designated as Primary Contact.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => addGuardian("guardian")}
            className="px-3 py-1.5 rounded-input text-xs font-semibold border border-rule bg-surface text-ink hover:bg-ground transition flex items-center gap-1"
          >
            + Add Another Legal Guardian
          </button>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-4">
        {guardians.map((g, idx) => {
          const relationTitle =
            g.relation === "father"
              ? "Father's Information"
              : g.relation === "mother"
              ? "Mother's Information"
              : `Legal Guardian #${idx + 1}`;

          return (
            <Card key={idx} title={relationTitle}>
              <div className="space-y-4">
                {/* Header row with relation badge and primary contact selector */}
                <div className="flex flex-wrap items-center justify-between gap-3 bg-ground p-3 rounded-input border border-rule">
                  <div className="flex items-center gap-3">
                    <label className="text-xs font-semibold text-ink-soft flex items-center gap-1.5">
                      Relationship:
                      <select
                        className="rounded border border-rule px-2 py-1 text-xs bg-surface text-ink font-medium"
                        value={g.relation}
                        onChange={(e) =>
                          updateGuardian(idx, { relation: e.target.value as any })
                        }
                      >
                        <option value="father">Father</option>
                        <option value="mother">Mother</option>
                        <option value="guardian">Legal Guardian</option>
                      </select>
                    </label>
                  </div>

                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-xs font-bold text-ink cursor-pointer">
                      <input
                        type="radio"
                        name="primary_guardian_selector"
                        checked={g.is_primary}
                        onChange={() => updateGuardian(idx, { is_primary: true })}
                        className="text-primary focus:ring-primary w-4 h-4"
                      />
                      <span className={g.is_primary ? "text-primary font-extrabold" : "text-ink-soft"}>
                        Primary Contact {g.is_primary ? "✓ (Default for SMS/Notices)" : ""}
                      </span>
                    </label>

                    {guardians.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeGuardian(idx)}
                        className="text-xs text-rose-600 hover:text-rose-800 font-medium ml-2"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>

                {/* Personal particulars: Full Name, DOB, Qualification */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <FormField label="Full Name *">
                    <input
                      type="text"
                      required
                      className={inputClass}
                      value={g.full_name}
                      onChange={(e) => updateGuardian(idx, { full_name: e.target.value })}
                      placeholder={g.relation === "father" ? "Father's Full Name" : "Mother's Full Name"}
                    />
                  </FormField>

                  <FormField label="Date of Birth">
                    <input
                      type="date"
                      className={inputClass}
                      value={g.date_of_birth ? String(g.date_of_birth).slice(0, 10) : ""}
                      onChange={(e) => updateGuardian(idx, { date_of_birth: e.target.value })}
                    />
                  </FormField>

                  <FormField label="Highest Educational Qualification">
                    <select
                      className={inputClass}
                      value={g.qualification || ""}
                      onChange={(e) => updateGuardian(idx, { qualification: e.target.value })}
                    >
                      <option value="">Select Qualification</option>
                      {qualifications.map((q) => (
                        <option key={q} value={q}>
                          {q}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>

                {/* Employment Particulars: Occupation, Designation, Organisation, Income */}
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <FormField label="Occupation">
                    <input
                      type="text"
                      className={inputClass}
                      value={g.occupation || ""}
                      onChange={(e) => updateGuardian(idx, { occupation: e.target.value })}
                      placeholder="e.g. Salaried / Business"
                    />
                  </FormField>

                  <FormField label="Designation">
                    <input
                      type="text"
                      className={inputClass}
                      value={g.designation || ""}
                      onChange={(e) => updateGuardian(idx, { designation: e.target.value })}
                      placeholder="e.g. Senior Manager"
                    />
                  </FormField>

                  <FormField label="Organisation / Employer">
                    <input
                      type="text"
                      className={inputClass}
                      value={g.organisation || ""}
                      onChange={(e) => updateGuardian(idx, { organisation: e.target.value })}
                      placeholder="e.g. TCS / Govt Service"
                    />
                  </FormField>

                  <FormField label="Annual Income Band">
                    <select
                      className={inputClass}
                      value={g.annual_income_band || ""}
                      onChange={(e) => updateGuardian(idx, { annual_income_band: e.target.value })}
                    >
                      <option value="">Select Income Band</option>
                      {incomeBands.map((band) => (
                        <option key={band} value={band}>
                          {band}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>

                {/* Contact Particulars: Mobile, Alternate Mobile, Email, Office Address */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <FormField label="Mobile Number * (10 Digits)">
                    <input
                      type="tel"
                      required
                      className={inputClass}
                      value={g.mobile}
                      onChange={(e) => updateGuardian(idx, { mobile: e.target.value })}
                      placeholder="e.g. 9876543210"
                    />
                  </FormField>

                  <FormField label="Alternate Mobile / WhatsApp">
                    <input
                      type="tel"
                      className={inputClass}
                      value={g.alternate_mobile || ""}
                      onChange={(e) => updateGuardian(idx, { alternate_mobile: e.target.value })}
                      placeholder="Optional"
                    />
                  </FormField>

                  <FormField label="Email Address">
                    <input
                      type="email"
                      className={inputClass}
                      value={g.email || ""}
                      onChange={(e) => updateGuardian(idx, { email: e.target.value })}
                      placeholder="e.g. parent@example.com"
                    />
                  </FormField>
                </div>

                <FormField label="Office / Workplace Address">
                  <input
                    type="text"
                    className={inputClass}
                    value={g.office_address || ""}
                    onChange={(e) => updateGuardian(idx, { office_address: e.target.value })}
                    placeholder="e.g. Vibhuti Khand, Gomti Nagar, Lucknow"
                  />
                </FormField>

                {/* Authorizations & Affiliations */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 text-xs">
                  <label className="flex items-center gap-2 cursor-pointer text-ink">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded text-primary"
                      checked={g.is_emergency_contact}
                      onChange={(e) =>
                        updateGuardian(idx, { is_emergency_contact: e.target.checked })
                      }
                    />
                    <span>Emergency Contact</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer text-ink">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded text-primary"
                      checked={g.is_authorised_for_pickup}
                      onChange={(e) =>
                        updateGuardian(idx, { is_authorised_for_pickup: e.target.checked })
                      }
                    />
                    <span>Authorised for Student Pickup</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer text-ink">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded text-primary"
                      checked={g.is_school_alumnus}
                      onChange={(e) =>
                        updateGuardian(idx, { is_school_alumnus: e.target.checked })
                      }
                    />
                    <span>Sunrise School Alumnus</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer text-ink">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded text-primary"
                      checked={g.is_school_staff}
                      onChange={(e) =>
                        updateGuardian(idx, { is_school_staff: e.target.checked })
                      }
                    />
                    <span>School Staff / Faculty Member</span>
                  </label>
                </div>
              </div>
            </Card>
          );
        })}

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Parents and guardians information saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.application.write"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving guardians..." : "Save Guardians Information"}
          </ActionButton>
        </div>
      </form>
    </div>
  );
}
