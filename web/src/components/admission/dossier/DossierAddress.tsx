import React, { useState, useEffect } from "react";
import { ApplicationDetail } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";

interface Props {
  application: ApplicationDetail;
  onSave: (data: Partial<ApplicationDetail>) => Promise<void>;
  isSaving: boolean;
}

export function DossierAddress({ application, onSave, isSaving }: Props) {
  const existingAddress = application.address || {};

  const [sameAsResidential, setSameAsResidential] = useState(
    existingAddress.same_as_residential !== false
  );

  const [formData, setFormData] = useState({
    line1: existingAddress.line1 || existingAddress.address_line_1 || "",
    line2: existingAddress.line2 || existingAddress.address_line_2 || "",
    city: existingAddress.city || "Lucknow",
    state: existingAddress.state || "Uttar Pradesh",
    pincode: existingAddress.pincode || "226022",
    country: existingAddress.country || "India",
    permanent_line1: existingAddress.permanent_line1 || "",
    permanent_city: existingAddress.permanent_city || "",
    permanent_state: existingAddress.permanent_state || "",
    permanent_pincode: existingAddress.permanent_pincode || "",
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const addr = application.address || {};
    setFormData({
      line1: addr.line1 || addr.address_line_1 || "",
      line2: addr.line2 || addr.address_line_2 || "",
      city: addr.city || "Lucknow",
      state: addr.state || "Uttar Pradesh",
      pincode: addr.pincode || "226022",
      country: addr.country || "India",
      permanent_line1: addr.permanent_line1 || "",
      permanent_city: addr.permanent_city || "",
      permanent_state: addr.permanent_state || "",
      permanent_pincode: addr.permanent_pincode || "",
    });
    setSameAsResidential(addr.same_as_residential !== false);
  }, [application]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    if (!formData.line1.trim()) {
      setErrorMsg("Residential Address Line 1 is required.");
      return;
    }
    if (!formData.pincode.trim()) {
      setErrorMsg("Postal PIN code is required.");
      return;
    }

    const payload = {
      line1: formData.line1.trim(),
      address_line_1: formData.line1.trim(),
      line2: formData.line2.trim() || null,
      address_line_2: formData.line2.trim() || null,
      city: formData.city.trim() || "Lucknow",
      state: formData.state.trim() || "Uttar Pradesh",
      pincode: formData.pincode.trim(),
      country: formData.country.trim() || "India",
      same_as_residential: sameAsResidential,
      permanent_line1: sameAsResidential
        ? formData.line1.trim()
        : formData.permanent_line1.trim() || null,
      permanent_city: sameAsResidential
        ? formData.city.trim()
        : formData.permanent_city.trim() || null,
      permanent_state: sameAsResidential
        ? formData.state.trim()
        : formData.permanent_state.trim() || null,
      permanent_pincode: sameAsResidential
        ? formData.pincode.trim()
        : formData.permanent_pincode.trim() || null,
    };

    try {
      await onSave({ address: payload });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to update address.");
    }
  };

  return (
    <Card title="5. Residential & Permanent Address">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Current / Residential Address */}
        <div>
          <h4 className="text-xs font-bold text-ink uppercase tracking-wider mb-2">
            Current / Residential Address
          </h4>
          <div className="space-y-3">
            <FormField label="Address Line 1 (House No, Flat / Apartment, Building) *">
              <input
                type="text"
                required
                className={inputClass}
                value={formData.line1}
                onChange={(e) => setFormData({ ...formData, line1: e.target.value })}
                placeholder="e.g. Flat 302, Royal Enclave"
              />
            </FormField>

            <FormField label="Address Line 2 (Street, Sector, Landmark)">
              <input
                type="text"
                className={inputClass}
                value={formData.line2}
                onChange={(e) => setFormData({ ...formData, line2: e.target.value })}
                placeholder="e.g. Sector 14, Vikas Nagar"
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <FormField label="City *">
                <input
                  type="text"
                  required
                  className={inputClass}
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  placeholder="Lucknow"
                />
              </FormField>

              <FormField label="State *">
                <input
                  type="text"
                  required
                  className={inputClass}
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  placeholder="Uttar Pradesh"
                />
              </FormField>

              <FormField label="PIN Code * (6 Digits)">
                <input
                  type="text"
                  required
                  maxLength={6}
                  pattern="\d{6}"
                  className={inputClass}
                  value={formData.pincode}
                  onChange={(e) =>
                    setFormData({ ...formData, pincode: e.target.value.replace(/\D/g, "") })
                  }
                  placeholder="226022"
                />
              </FormField>
            </div>
          </div>
        </div>

        {/* Permanent Address Toggle */}
        <div className="pt-2 border-t border-rule">
          <label className="flex items-center gap-2 cursor-pointer text-sm font-semibold text-ink">
            <input
              type="checkbox"
              className="w-4 h-4 rounded text-primary"
              checked={sameAsResidential}
              onChange={(e) => setSameAsResidential(e.target.checked)}
            />
            <span>Permanent Address is identical to Current Residential Address</span>
          </label>
        </div>

        {!sameAsResidential && (
          <div className="space-y-3 pt-2 bg-ground p-3 rounded border border-rule">
            <h4 className="text-xs font-bold text-ink uppercase tracking-wider">
              Permanent Home / Domicile Address
            </h4>

            <FormField label="Permanent Address Line 1">
              <input
                type="text"
                className={inputClass}
                value={formData.permanent_line1}
                onChange={(e) =>
                  setFormData({ ...formData, permanent_line1: e.target.value })
                }
                placeholder="Permanent Street / Village / Town"
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <FormField label="Permanent City">
                <input
                  type="text"
                  className={inputClass}
                  value={formData.permanent_city}
                  onChange={(e) =>
                    setFormData({ ...formData, permanent_city: e.target.value })
                  }
                  placeholder="e.g. Kanpur"
                />
              </FormField>

              <FormField label="Permanent State">
                <input
                  type="text"
                  className={inputClass}
                  value={formData.permanent_state}
                  onChange={(e) =>
                    setFormData({ ...formData, permanent_state: e.target.value })
                  }
                  placeholder="e.g. Uttar Pradesh"
                />
              </FormField>

              <FormField label="Permanent PIN Code">
                <input
                  type="text"
                  maxLength={6}
                  className={inputClass}
                  value={formData.permanent_pincode}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      permanent_pincode: e.target.value.replace(/\D/g, ""),
                    })
                  }
                  placeholder="e.g. 208001"
                />
              </FormField>
            </div>
          </div>
        )}

        {errorMsg && <FormError error={errorMsg} />}

        {savedSuccess && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
            <span>✓</span> Address details saved successfully.
          </div>
        )}

        <div className="flex justify-end pt-2">
          <ActionButton
            permission="admission.application.write"
            variant="primary"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? "Saving address..." : "Save Address Information"}
          </ActionButton>
        </div>
      </form>
    </Card>
  );
}
