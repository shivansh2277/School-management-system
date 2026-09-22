import React, { useState, useEffect } from "react";
import { ApplicationDetail, SiblingOut } from "../../../pages/admission/types";
import { Card, FormField, FormError, inputClass } from "../../../components/ui";
import { ActionButton } from "../../../components/Can";
import { api } from "../../../api/client";

interface Props {
  application: ApplicationDetail;
  onSave: (siblings: SiblingOut[]) => Promise<void>;
  isSaving: boolean;
}

export function DossierSiblings({ application, onSave, isSaving }: Props) {
  const [siblings, setSiblings] = useState<SiblingOut[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setSiblings(application.siblings || []);
  }, [application]);

  const handleSearch = async (term: string) => {
    setSearchQuery(term);
    if (term.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const res = (await api.get(
        "/admin/admission/sibling-search",
        `?q=${encodeURIComponent(term.trim())}`
      )) as any[];
      setSearchResults(res || []);
    } catch {
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const linkEnrolledSibling = (student: any) => {
    // Avoid duplicate addition
    if (siblings.some((s) => s.student_id === student.student_id)) {
      return;
    }
    setSiblings((prev) => [
      ...prev,
      {
        id: -1 * (prev.length + 1),
        student_id: student.student_id,
        name: student.name,
        age: null,
        school_name: `Sunrise Public School (${student.class_label}, Adm: ${student.admission_no})`,
      },
    ]);
    setSearchQuery("");
    setSearchResults([]);
  };

  const addManualSibling = () => {
    setSiblings((prev) => [
      ...prev,
      {
        id: -1 * (prev.length + 1),
        student_id: null,
        name: "",
        age: null,
        school_name: "",
      },
    ]);
  };

  const updateSibling = (index: number, patch: Partial<SiblingOut>) => {
    setSiblings((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  };

  const removeSibling = (index: number) => {
    setSiblings((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSavedSuccess(false);

    const validSiblings = siblings.filter(
      (s) => s.student_id !== null || (s.name && s.name.trim().length > 0)
    );

    try {
      await onSave(
        validSiblings.map((s) => ({
          ...s,
          name: s.name?.trim() || null,
          age: s.age ? Number(s.age) : null,
          school_name: s.school_name?.trim() || null,
        }))
      );
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3500);
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to save siblings.");
    }
  };

  return (
    <Card title="4. Sibling Information & School Concession Claims">
      <div className="space-y-4">
        <p className="text-xs text-ink-soft">
          Linking an enrolled sibling in Sunrise Public School automatically authenticates the Sibling Claim and drives family fee concessions.
        </p>

        {/* Live Search to link real enrolled student */}
        <div className="p-3 bg-ground rounded-input border border-rule space-y-2">
          <label className="text-xs font-semibold text-ink block">
            Link Enrolled Student from Sunrise Public School:
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              className={inputClass}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search by student name or admission number (min 2 chars)..."
            />
          </div>

          {isSearching && <p className="text-xs text-ink-faint">Searching student roster...</p>}

          {searchResults.length > 0 && (
            <div className="border border-rule rounded bg-surface divide-y divide-rule max-h-48 overflow-y-auto mt-2">
              {searchResults.map((st) => (
                <div
                  key={st.student_id}
                  className="p-2 text-xs flex items-center justify-between hover:bg-ground cursor-pointer"
                  onClick={() => linkEnrolledSibling(st)}
                >
                  <div>
                    <span className="font-bold text-ink">{st.name}</span>
                    <span className="text-ink-soft ml-2">
                      ({st.class_label} | Adm: {st.admission_no})
                    </span>
                  </div>
                  <button
                    type="button"
                    className="px-2 py-0.5 bg-primary text-white rounded text-2xs font-semibold"
                  >
                    + Link Sibling
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sibling List Form */}
        <form onSubmit={handleSave} className="space-y-3">
          {siblings.length === 0 ? (
            <div className="p-4 text-center border-2 border-dashed border-rule rounded text-xs text-ink-soft">
              No siblings recorded yet. Use the search above to link an enrolled student, or click below to enter external sibling details.
            </div>
          ) : (
            <div className="space-y-2">
              {siblings.map((s, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded border text-xs flex flex-wrap items-center gap-3 ${
                    s.student_id ? "bg-primary/5 border-primary/40" : "bg-ground border-rule"
                  }`}
                >
                  <div className="flex-1 min-w-[180px]">
                    <span className="text-[10px] text-ink-faint block uppercase">Sibling Name</span>
                    {s.student_id ? (
                      <span className="font-bold text-ink text-sm flex items-center gap-1.5">
                        {s.name}
                        <span className="bg-primary text-white text-2xs px-1.5 py-0.5 rounded font-bold">
                          ENROLLED SIBLING
                        </span>
                      </span>
                    ) : (
                      <input
                        type="text"
                        required
                        className={inputClass}
                        value={s.name || ""}
                        onChange={(e) => updateSibling(idx, { name: e.target.value })}
                        placeholder="Sibling Full Name"
                      />
                    )}
                  </div>

                  <div className="w-20">
                    <span className="text-[10px] text-ink-faint block uppercase">Age</span>
                    <input
                      type="number"
                      min={1}
                      max={30}
                      className={inputClass}
                      value={s.age ?? ""}
                      onChange={(e) =>
                        updateSibling(idx, {
                          age: e.target.value ? parseInt(e.target.value, 10) : null,
                        })
                      }
                      placeholder="Age"
                    />
                  </div>

                  <div className="flex-1 min-w-[200px]">
                    <span className="text-[10px] text-ink-faint block uppercase">School / College</span>
                    <input
                      type="text"
                      className={inputClass}
                      value={s.school_name || ""}
                      onChange={(e) => updateSibling(idx, { school_name: e.target.value })}
                      placeholder="School name or class"
                    />
                  </div>

                  <div className="pt-3">
                    <button
                      type="button"
                      onClick={() => removeSibling(idx)}
                      className="text-xs text-rose-600 hover:text-rose-800 font-medium"
                    >
                      ✕ Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={addManualSibling}
              className="text-xs font-semibold text-primary hover:underline"
            >
              + Add Non-Enrolled Sibling Manually
            </button>

            <ActionButton
              permission="admission.application.write"
              variant="primary"
              type="submit"
              disabled={isSaving}
            >
              {isSaving ? "Saving siblings..." : "Save Sibling Details"}
            </ActionButton>
          </div>

          {errorMsg && <FormError error={errorMsg} />}

          {savedSuccess && (
            <div className="p-2.5 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs font-medium flex items-center gap-1.5">
              <span>✓</span> Sibling information saved successfully.
            </div>
          )}
        </form>
      </div>
    </Card>
  );
}
