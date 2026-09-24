import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../../api/client";

type OpenCycleClass = {
  class_name: string;
  stream: string | null;
  total_seats: number;
  age_on: string | null;
  min_age_years: number | null;
  max_age_years: number | null;
  requires_test: boolean;
  requires_interview: boolean;
  required_documents: string[];
};

type OpenCycleData = {
  school: { code: string; name: string; city: string };
  cycle: {
    name: string;
    academic_year: string;
    starts_on: string;
    ends_on: string;
    application_fee: string | number;
    refund_policy: string | null;
  };
  classes: OpenCycleClass[];
};

type ApplicationStatusResult = {
  application_no: string;
  name: string;
  class_applying_for: string;
  status: string;
  submitted_at: string;
  action_needed: boolean;
};

export type AuthorizedPersonState = {
  id: string;
  name: string;
  relationship: string;
  phone: string;
  idProofType: string;
  idProofNumber: string;
  photoUrl: string | null;
  notes: string;
};

function PhotoUploadField({
  label,
  value,
  onChange,
  schoolCode,
  helperText,
}: {
  label: string;
  value: string | null;
  onChange: (url: string | null) => void;
  schoolCode: string;
  helperText?: string;
}) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|webp)$/i)) {
      setUploadError("Please upload a valid image file (.jpg, .png, .webp).");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setUploadError("Image file size exceeds 5MB limit.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.upload<{ url: string; filename: string }>(
        `/public/${schoolCode}/admission/upload`,
        formData
      );
      if (res?.url) {
        onChange(res.url);
      }
    } catch (err: any) {
      setUploadError(err?.message || "Failed to upload photo.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const displayUrl = value
    ? value.startsWith("http") || value.startsWith("data:")
      ? value
      : `${apiBase}${value.startsWith("/") ? "" : "/"}${value}`
    : null;

  return (
    <div>
      <label className="block text-xs font-semibold text-ink-soft mb-1">{label}</label>
      {value && displayUrl ? (
        <div className="flex items-center gap-3 p-2 bg-surface border border-rule rounded">
          <img
            src={displayUrl}
            alt="Uploaded Photo"
            className="w-12 h-14 object-cover rounded border border-rule shadow-xs"
          />
          <div className="flex-1 min-w-0">
            <span className="text-xs text-ink font-medium block truncate">Photo uploaded</span>
            <button
              type="button"
              onClick={() => onChange(null)}
              className="text-xs text-danger hover:underline font-medium mt-0.5"
            >
              Remove / Replace
            </button>
          </div>
        </div>
      ) : (
        <div>
          <label className="flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-rule rounded hover:border-primary/50 cursor-pointer bg-ground/50 hover:bg-surface text-xs text-ink-soft hover:text-ink transition">
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
            {uploading ? (
              <span className="flex items-center gap-1.5 text-primary font-medium">
                <span className="animate-spin inline-block w-3 h-3 border-2 border-primary border-t-transparent rounded-full" />
                Uploading photo...
              </span>
            ) : (
              <span>📷 Upload Photo (.jpg, .png, max 5MB)</span>
            )}
          </label>
          {helperText && <p className="text-[11px] text-ink-faint mt-1">{helperText}</p>}
        </div>
      )}
      {uploadError && <p className="text-xs text-danger mt-1">{uploadError}</p>}
    </div>
  );
}

export function PublicApplyPage() {
  const [activeTab, setActiveTab] = useState<"apply" | "status" | "info">("apply");
  const schoolCode = "SPS";

  // Query open admission cycle
  const cycleQuery = useQuery<OpenCycleData>({
    queryKey: ["public-admission-open", schoolCode],
    queryFn: () => api.rawGet<OpenCycleData>(`/public/${schoolCode}/admission/open`),
    retry: 1,
  });

  // Application Form State
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("male");
  const [selectedClass, setSelectedClass] = useState("");
  const [stream, setStream] = useState("");
  const [motherTongue, setMotherTongue] = useState("Hindi");
  const [casteCategory, setCasteCategory] = useState("General");
  const [admissionCategory, setAdmissionCategory] = useState("general");
  const [transportRequired, setTransportRequired] = useState(false);

  // Address
  const [addressLine, setAddressLine] = useState("");
  const [city, setCity] = useState("Lucknow");
  const [pinCode, setPinCode] = useState("");
  const [stateName, setStateName] = useState("Uttar Pradesh");

  // Previous School
  const [prevSchoolName, setPrevSchoolName] = useState("");
  const [prevLastClass, setPrevLastClass] = useState("");
  const [prevTcNo, setPrevTcNo] = useState("");

  // Primary Guardian
  const [guardianRelation, setGuardianRelation] = useState<"father" | "mother" | "other">("father");
  const [guardianName, setGuardianName] = useState("");
  const [guardianMobile, setGuardianMobile] = useState("");
  const [guardianEmail, setGuardianEmail] = useState("");
  const [guardianOccupation, setGuardianOccupation] = useState("");

  // Secondary Guardian (optional)
  const [hasSecondGuardian, setHasSecondGuardian] = useState(false);
  const [secRelation, setSecRelation] = useState<"father" | "mother" | "other">("mother");
  const [secName, setSecName] = useState("");
  const [secMobile, setSecMobile] = useState("");
  const [secEmail, setSecEmail] = useState("");
  const [secOccupation, setSecOccupation] = useState("");

  // Guardian Photos
  const [guardianPhotoUrl, setGuardianPhotoUrl] = useState<string | null>(null);
  const [secPhotoUrl, setSecPhotoUrl] = useState<string | null>(null);

  // Additional Authorized Pickup Persons (Permitted to collect student)
  const [authorizedPersons, setAuthorizedPersons] = useState<AuthorizedPersonState[]>([]);

  const addAuthorizedPerson = () => {
    setAuthorizedPersons((prev) => [
      ...prev,
      {
        id: Math.random().toString(36).substring(2, 9),
        name: "",
        relationship: "Grandfather",
        phone: "",
        idProofType: "Aadhaar Card",
        idProofNumber: "",
        photoUrl: null,
        notes: "",
      },
    ]);
  };

  const removeAuthorizedPerson = (id: string) => {
    setAuthorizedPersons((prev) => prev.filter((p) => p.id !== id));
  };

  const updateAuthorizedPerson = (id: string, field: keyof AuthorizedPersonState, value: any) => {
    setAuthorizedPersons((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    );
  };

  // Explicit, never pre-ticked consents (§5.1.4 step 9)
  const [consentAccuracy, setConsentAccuracy] = useState(false);
  const [consentRules, setConsentRules] = useState(false);
  const [consentData, setConsentData] = useState(false);
  const [consentMedia, setConsentMedia] = useState(false);

  // Bot honeypot
  const [honeypot, setHoneypot] = useState("");

  // Submission feedback
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submittedAppNo, setSubmittedAppNo] = useState<string | null>(null);
  const [nextStepInfo, setNextStepInfo] = useState<string | null>(null);

  // Status Lookup State
  const [searchAppNo, setSearchAppNo] = useState("");
  const [searchDob, setSearchDob] = useState("");
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statusResult, setStatusResult] = useState<ApplicationStatusResult | null>(null);

  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    // Basic frontend checks
    if (!firstName.trim() || !lastName.trim()) {
      setSubmitError("Please enter student's first and last name.");
      return;
    }
    if (!dob) {
      setSubmitError("Please provide student's date of birth.");
      return;
    }
    if (!selectedClass) {
      setSubmitError("Please select the class applying for.");
      return;
    }
    if (!guardianName.trim() || !guardianMobile.trim()) {
      setSubmitError("Please provide the primary parent/guardian's name and mobile number.");
      return;
    }
    if (!/^\d{10}$/.test(guardianMobile.trim())) {
      setSubmitError("Primary guardian mobile number must be exactly 10 digits.");
      return;
    }
    if (hasSecondGuardian && secMobile.trim() && !/^\d{10}$/.test(secMobile.trim())) {
      setSubmitError("Second guardian mobile number must be exactly 10 digits.");
      return;
    }

    // Validate authorized pickup persons if any
    for (let i = 0; i < authorizedPersons.length; i++) {
      const p = authorizedPersons[i];
      if (!p.name.trim()) {
        setSubmitError(`Authorized pickup person #${i + 1} must have a name.`);
        return;
      }
      if (!/^\d{10}$/.test(p.phone.trim())) {
        setSubmitError(`Authorized pickup person #${i + 1} (${p.name || "Unnamed"}) must have a valid 10-digit phone number.`);
        return;
      }
    }

    if (!consentAccuracy || !consentRules || !consentData) {
      setSubmitError("All mandatory declarations must be accepted before submitting.");
      return;
    }

    const guardiansList = [
      {
        relation: guardianRelation,
        full_name: guardianName.trim(),
        mobile: guardianMobile.trim(),
        email: guardianEmail.trim() || null,
        occupation: guardianOccupation.trim() || null,
        photo_url: guardianPhotoUrl || null,
        is_authorised_for_pickup: true,
        is_primary: true,
      },
    ];

    if (hasSecondGuardian && secName.trim() && secMobile.trim()) {
      guardiansList.push({
        relation: secRelation,
        full_name: secName.trim(),
        mobile: secMobile.trim(),
        email: secEmail.trim() || null,
        occupation: secOccupation.trim() || null,
        photo_url: secPhotoUrl || null,
        is_authorised_for_pickup: true,
        is_primary: false,
      });
    }

    const payload = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      middle_name: middleName.trim() || null,
      date_of_birth: dob,
      gender,
      class_applying_for: selectedClass,
      stream: stream.trim() || null,
      mother_tongue: motherTongue.trim() || null,
      caste_category: casteCategory.trim() || null,
      admission_category: admissionCategory,
      transport_required: transportRequired,
      address: addressLine.trim()
        ? {
            address_line: addressLine.trim(),
            city: city.trim(),
            pin_code: pinCode.trim(),
            state: stateName.trim(),
          }
        : null,
      previous_school: prevSchoolName.trim()
        ? {
            school_name: prevSchoolName.trim(),
            last_class: prevLastClass.trim(),
            tc_number: prevTcNo.trim(),
          }
        : null,
      guardians: guardiansList,
      authorized_pickup_persons: authorizedPersons.map((p) => ({
        name: p.name.trim(),
        relationship: p.relationship.trim(),
        phone: p.phone.trim(),
        id_proof_type: p.idProofType.trim() || null,
        id_proof_number: p.idProofNumber.trim() || null,
        photo_url: p.photoUrl || null,
        notes: p.notes.trim() || null,
      })),
      heard_about_us: "website",
      information_accuracy: consentAccuracy,
      school_rules_accepted: consentRules,
      data_processing_consent: consentData,
      photo_media_consent: consentMedia,
      website: honeypot.trim() || null,
    };

    setSubmitting(true);
    try {
      const res = await api.rawPost<{ application_no: string; status: string; next_step: string }>(
        `/public/${schoolCode}/admission/apply`,
        payload
      );
      setSubmittedAppNo(res.application_no);
      setNextStepInfo(res.next_step);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err: any) {
      setSubmitError(err?.message || "Failed to submit application. Please verify details.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusError(null);
    setStatusResult(null);

    if (!searchAppNo.trim() || !searchDob.trim()) {
      setStatusError("Please provide both the Application Number and the Child's Date of Birth.");
      return;
    }

    setStatusLoading(true);
    try {
      const query = `?application_no=${encodeURIComponent(
        searchAppNo.trim()
      )}&date_of_birth=${encodeURIComponent(searchDob.trim())}`;
      const res = await api.rawGet<ApplicationStatusResult>(
        `/public/${schoolCode}/admission/status`,
        query
      );
      setStatusResult(res);
    } catch (err: any) {
      setStatusError(
        err?.message || "No application matches that number and date of birth. Please re-check."
      );
    } finally {
      setStatusLoading(false);
    }
  };

  const resetForm = () => {
    setSubmittedAppNo(null);
    setFirstName("");
    setMiddleName("");
    setLastName("");
    setDob("");
    setGuardianName("");
    setGuardianMobile("");
    setGuardianEmail("");
    setAddressLine("");
    setPinCode("");
    setPrevSchoolName("");
    setConsentAccuracy(false);
    setConsentRules(false);
    setConsentData(false);
    setConsentMedia(false);
  };

  const cycleData = cycleQuery.data;

  return (
    <div className="min-h-screen bg-ground text-ink font-sans pb-16">
      {/* Top Banner & School Header */}
      <header className="bg-surface border-b border-rule shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-xl shadow-md">
              SPS
            </div>
            <div>
              <h1 className="text-xl font-bold text-ink tracking-tight">Sunrise Public School</h1>
              <p className="text-xs text-ink-soft">
                {cycleData ? `${cycleData.school.city} • ${cycleData.cycle.name}` : "Online Admission Portal"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex rounded-lg bg-ground p-1 border border-rule">
              <button
                onClick={() => {
                  setActiveTab("apply");
                  setSubmitError(null);
                }}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "apply" ? "bg-white text-primary shadow-sm" : "text-ink-soft hover:text-ink"
                }`}
              >
                Apply Online
              </button>
              <button
                onClick={() => {
                  setActiveTab("status");
                  setStatusError(null);
                }}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "status" ? "bg-white text-primary shadow-sm" : "text-ink-soft hover:text-ink"
                }`}
              >
                Check Status
              </button>
              <button
                onClick={() => setActiveTab("info")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "info" ? "bg-white text-primary shadow-sm" : "text-ink-soft hover:text-ink"
                }`}
              >
                Seat Matrix & Criteria
              </button>
            </div>

            <Link
              to="/login"
              className="text-xs font-semibold text-ink-soft hover:text-primary px-3 py-2 rounded-lg border border-rule hover:border-primary/40 transition-colors"
            >
              Staff Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-4 pt-8">
        {/* TAB 1: APPLY NOW */}
        {activeTab === "apply" && (
          <div>
            {submittedAppNo ? (
              /* Success Screen */
              <div className="bg-surface rounded-card border border-rule shadow-card p-8 text-center space-y-6">
                <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-3xl font-bold">
                  ✓
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-ink">Application Submitted Successfully!</h2>
                  <p className="text-sm text-ink-soft mt-1">
                    Your online admission application has been registered with the school admissions office.
                  </p>
                </div>

                <div className="bg-ground border border-rule rounded-xl p-6 max-w-md mx-auto">
                  <div className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
                    Your Application Reference Number
                  </div>
                  <div className="text-3xl font-mono font-bold text-primary mt-2 select-all">
                    {submittedAppNo}
                  </div>
                  <div className="mt-3 inline-block bg-primary/10 text-primary text-xs font-semibold px-2.5 py-1 rounded-full">
                    Status: Submitted
                  </div>
                </div>

                <div className="text-sm text-ink-soft max-w-lg mx-auto bg-blue-50 border border-blue-200 text-blue-900 rounded-lg p-4 text-left">
                  <p className="font-semibold text-xs uppercase tracking-wide text-blue-700">Next Steps:</p>
                  <p className="mt-1 text-sm">{nextStepInfo}</p>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                  <button
                    onClick={() => {
                      setSearchAppNo(submittedAppNo);
                      setSearchDob(dob);
                      setActiveTab("status");
                    }}
                    className="px-5 py-2.5 bg-primary text-white text-sm font-semibold rounded-input shadow hover:bg-primary-dark transition-all"
                  >
                    Track Status Now
                  </button>
                  <button
                    onClick={() => window.print()}
                    className="px-5 py-2.5 bg-surface border border-rule text-ink text-sm font-semibold rounded-input hover:bg-ground transition-all"
                  >
                    Print Confirmation / PDF
                  </button>
                  <button
                    onClick={resetForm}
                    className="px-5 py-2.5 bg-surface border border-rule text-ink-soft text-sm font-semibold rounded-input hover:bg-ground transition-all"
                  >
                    Submit Another Application
                  </button>
                </div>
              </div>
            ) : cycleQuery.isLoading ? (
              <div className="bg-surface rounded-card border border-rule p-12 text-center text-ink-faint">
                Loading active admission cycle and classes...
              </div>
            ) : cycleQuery.isError ? (
              <div className="bg-surface rounded-card border border-red-200 p-8 text-center space-y-3">
                <div className="text-danger font-bold text-lg">Admissions Currently Closed</div>
                <p className="text-sm text-ink-soft">
                  Sunrise Public School is not accepting online applications at this time. Please contact the
                  school reception for in-person admissions or further details.
                </p>
              </div>
            ) : (
              /* Admission Form Wizard */
              <div className="space-y-6">
                {/* Hero / Instruction Banner */}
                <div className="bg-gradient-to-r from-primary to-primary-dark text-white rounded-card p-6 shadow-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <span className="text-xs uppercase font-semibold tracking-wider bg-white/20 px-2.5 py-0.5 rounded-full">
                      Admissions Open
                    </span>
                    <h2 className="text-2xl font-bold mt-2">{cycleData?.cycle.name}</h2>
                    <p className="text-xs text-white/80 mt-1">
                      Session {cycleData?.cycle.academic_year} • Application Window: {cycleData?.cycle.starts_on} to{" "}
                      {cycleData?.cycle.ends_on}
                    </p>
                  </div>
                  <div className="bg-white/10 backdrop-blur rounded-xl px-4 py-3 border border-white/20 text-center">
                    <div className="text-xs text-white/80 font-medium">Application Fee</div>
                    <div className="text-xl font-bold text-white">
                      ₹{cycleData?.cycle.application_fee || "500"}
                    </div>
                  </div>
                </div>

                <form onSubmit={handleApplySubmit} className="space-y-6">
                  {/* Step 1: Student Information */}
                  <div className="bg-surface rounded-card border border-rule p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2 border-b border-rule pb-3">
                      <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                        1
                      </span>
                      <h3 className="text-base font-bold text-ink">Student Personal Details</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          First Name <span className="text-danger">*</span>
                        </label>
                        <input
                          required
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          placeholder="e.g. Aarav"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Middle Name</label>
                        <input
                          value={middleName}
                          onChange={(e) => setMiddleName(e.target.value)}
                          placeholder="Optional"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Last Name <span className="text-danger">*</span>
                        </label>
                        <input
                          required
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          placeholder="e.g. Sharma"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Date of Birth <span className="text-danger">*</span>
                        </label>
                        <input
                          type="date"
                          required
                          value={dob}
                          onChange={(e) => setDob(e.target.value)}
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Gender</label>
                        <select
                          value={gender}
                          onChange={(e) => setGender(e.target.value)}
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                        >
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Class Applying For <span className="text-danger">*</span>
                        </label>
                        <select
                          required
                          value={selectedClass}
                          onChange={(e) => setSelectedClass(e.target.value)}
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white font-medium"
                        >
                          <option value="">-- Select Class --</option>
                          {cycleData?.classes.map((cls) => (
                            <option key={cls.class_name} value={cls.class_name}>
                              {cls.class_name} ({cls.total_seats} seats)
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Mother Tongue</label>
                        <input
                          value={motherTongue}
                          onChange={(e) => setMotherTongue(e.target.value)}
                          placeholder="e.g. Hindi, English"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Social Category</label>
                        <select
                          value={casteCategory}
                          onChange={(e) => setCasteCategory(e.target.value)}
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                        >
                          <option value="General">General</option>
                          <option value="OBC">OBC</option>
                          <option value="SC">SC</option>
                          <option value="ST">ST</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Admission Category
                        </label>
                        <select
                          value={admissionCategory}
                          onChange={(e) => setAdmissionCategory(e.target.value)}
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                        >
                          <option value="general">General Open Seat</option>
                          <option value="rte">RTE (Right to Education)</option>
                          <option value="sibling">Sibling Enrolled</option>
                          <option value="staff_ward">Staff Ward</option>
                          <option value="management">Management Quota</option>
                        </select>
                      </div>
                    </div>

                    <div className="pt-2">
                      <label className="flex items-center gap-2 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={transportRequired}
                          onChange={(e) => setTransportRequired(e.target.checked)}
                          className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                        />
                        <span className="text-sm font-medium text-ink">
                          School Bus / Van Transport Facility Required
                        </span>
                      </label>
                    </div>
                  </div>

                  {/* Step 2: Parent / Guardian Details */}
                  <div className="bg-surface rounded-card border border-rule p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-rule pb-3">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                          2
                        </span>
                        <h3 className="text-base font-bold text-ink">Primary Parent / Guardian</h3>
                      </div>
                      <span className="text-xs bg-primary/10 text-primary font-semibold px-2 py-0.5 rounded">
                        Main Contact
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Relation</label>
                        <select
                          value={guardianRelation}
                          onChange={(e) =>
                            setGuardianRelation(e.target.value as "father" | "mother" | "other")
                          }
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                        >
                          <option value="father">Father</option>
                          <option value="mother">Mother</option>
                          <option value="other">Legal Guardian</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Full Name <span className="text-danger">*</span>
                        </label>
                        <input
                          required
                          value={guardianName}
                          onChange={(e) => setGuardianName(e.target.value)}
                          placeholder="e.g. Rajesh Sharma"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Mobile Number (10 digits) <span className="text-danger">*</span>
                        </label>
                        <input
                          required
                          maxLength={10}
                          value={guardianMobile}
                          onChange={(e) => setGuardianMobile(e.target.value.replace(/\D/g, ""))}
                          placeholder="e.g. 9876543210"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Email Address</label>
                        <input
                          type="email"
                          value={guardianEmail}
                          onChange={(e) => setGuardianEmail(e.target.value)}
                          placeholder="parent@example.com"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">Occupation</label>
                        <input
                          value={guardianOccupation}
                          onChange={(e) => setGuardianOccupation(e.target.value)}
                          placeholder="e.g. Software Engineer, Business"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                    </div>

                    <div>
                      <PhotoUploadField
                        label="Parent / Guardian Photo (Gate Escort Verification)"
                        value={guardianPhotoUrl}
                        onChange={setGuardianPhotoUrl}
                        schoolCode={schoolCode}
                        helperText="Official photograph used by gate security to verify student pickup identity."
                      />
                    </div>

                    {/* Secondary Guardian Toggle */}
                    <div className="pt-2">
                      {!hasSecondGuardian ? (
                        <button
                          type="button"
                          onClick={() => setHasSecondGuardian(true)}
                          className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                        >
                          + Add Second Parent / Co-Guardian Details
                        </button>
                      ) : (
                        <div className="border-t border-dashed border-rule pt-4 mt-2 space-y-4">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-ink-soft">
                              Second Parent / Co-Guardian
                            </h4>
                            <button
                              type="button"
                              onClick={() => setHasSecondGuardian(false)}
                              className="text-xs text-danger font-semibold hover:underline"
                            >
                              Remove
                            </button>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <label className="block text-xs font-semibold text-ink-soft mb-1">Relation</label>
                              <select
                                value={secRelation}
                                onChange={(e) =>
                                  setSecRelation(e.target.value as "father" | "mother" | "other")
                                }
                                className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                              >
                                <option value="mother">Mother</option>
                                <option value="father">Father</option>
                                <option value="other">Guardian</option>
                              </select>
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-ink-soft mb-1">
                                Full Name
                              </label>
                              <input
                                value={secName}
                                onChange={(e) => setSecName(e.target.value)}
                                placeholder="e.g. Sunita Sharma"
                                className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-ink-soft mb-1">
                                Mobile Number
                              </label>
                              <input
                                maxLength={10}
                                value={secMobile}
                                onChange={(e) => setSecMobile(e.target.value.replace(/\D/g, ""))}
                                placeholder="10 digit mobile"
                                className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                              />
                            </div>
                            <div className="md:col-span-3">
                              <PhotoUploadField
                                label="Second Parent / Co-Guardian Photo (Optional)"
                                value={secPhotoUrl}
                                onChange={setSecPhotoUrl}
                                schoolCode={schoolCode}
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Authorized Student Pickup Persons */}
                  <div className="bg-surface rounded-card border border-rule p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-rule pb-3">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">
                          ✓
                        </span>
                        <div>
                          <h3 className="text-base font-bold text-ink">
                            Authorized Student Pickup Persons
                          </h3>
                          <p className="text-xs text-ink-faint">
                            Declare grandparents, relatives, drivers, or guardians permitted to collect the student from school gates.
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={addAuthorizedPerson}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-primary hover:bg-primary/90 rounded transition flex items-center gap-1 shadow-sm"
                      >
                        + Add Authorized Person
                      </button>
                    </div>

                    {authorizedPersons.length === 0 ? (
                      <div className="text-center py-6 px-4 bg-ground/50 border border-dashed border-rule rounded-lg">
                        <p className="text-xs text-ink-soft mb-1 font-medium">
                          No additional authorized pickup persons added yet.
                        </p>
                        <p className="text-[11px] text-ink-faint mb-3">
                          Parents/Guardians above are automatically authorized. Add grandparents, family drivers, or trusted relatives who may collect your child.
                        </p>
                        <button
                          type="button"
                          onClick={addAuthorizedPerson}
                          className="px-3 py-1 text-xs font-semibold text-primary border border-primary/30 hover:bg-primary/5 rounded transition"
                        >
                          + Add Pickup Person (e.g. Grandfather / Driver)
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {authorizedPersons.map((person, idx) => (
                          <div
                            key={person.id}
                            className="p-4 border border-rule rounded-lg bg-ground/30 space-y-3"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-ink uppercase tracking-wider">
                                Authorized Person #{idx + 1}
                              </span>
                              <button
                                type="button"
                                onClick={() => removeAuthorizedPerson(person.id)}
                                className="text-xs text-danger font-semibold hover:underline"
                              >
                                Remove
                              </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">
                                  Full Name <span className="text-danger">*</span>
                                </label>
                                <input
                                  required
                                  value={person.name}
                                  onChange={(e) =>
                                    updateAuthorizedPerson(person.id, "name", e.target.value)
                                  }
                                  placeholder="e.g. Ramesh Kumar"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">
                                  Relationship with Student <span className="text-danger">*</span>
                                </label>
                                <input
                                  required
                                  value={person.relationship}
                                  onChange={(e) =>
                                    updateAuthorizedPerson(person.id, "relationship", e.target.value)
                                  }
                                  placeholder="e.g. Grandfather, Driver, Uncle"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">
                                  Mobile Phone (10 digits) <span className="text-danger">*</span>
                                </label>
                                <input
                                  required
                                  maxLength={10}
                                  value={person.phone}
                                  onChange={(e) =>
                                    updateAuthorizedPerson(
                                      person.id,
                                      "phone",
                                      e.target.value.replace(/\D/g, "")
                                    )
                                  }
                                  placeholder="e.g. 9876543210"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary bg-white"
                                />
                              </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">
                                  ID Proof Type
                                </label>
                                <select
                                  value={person.idProofType}
                                  onChange={(e) =>
                                    updateAuthorizedPerson(person.id, "idProofType", e.target.value)
                                  }
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                >
                                  <option value="Aadhaar Card">Aadhaar Card</option>
                                  <option value="Driving License">Driving License</option>
                                  <option value="Voter ID">Voter ID</option>
                                  <option value="Passport">Passport</option>
                                  <option value="PAN Card">PAN Card</option>
                                  <option value="Other">Other Official ID</option>
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">
                                  ID Proof Number
                                </label>
                                <input
                                  value={person.idProofNumber}
                                  onChange={(e) =>
                                    updateAuthorizedPerson(person.id, "idProofNumber", e.target.value)
                                  }
                                  placeholder="e.g. DL-1420110012345"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">
                                  Pickup Notes / Authorisation Window
                                </label>
                                <input
                                  value={person.notes}
                                  onChange={(e) =>
                                    updateAuthorizedPerson(person.id, "notes", e.target.value)
                                  }
                                  placeholder="e.g. Afternoon dismissal only"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                            </div>

                            <div className="pt-1">
                              <PhotoUploadField
                                label="Photograph of Authorized Person (Required for Gate Pass Verification)"
                                value={person.photoUrl}
                                onChange={(url) =>
                                  updateAuthorizedPerson(person.id, "photoUrl", url)
                                }
                                schoolCode={schoolCode}
                                helperText="Security personnel will match this photograph at the school gate before handing over student."
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Step 3: Residential Address */}
                  <div className="bg-surface rounded-card border border-rule p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2 border-b border-rule pb-3">
                      <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                        3
                      </span>
                      <h3 className="text-base font-bold text-ink">Residential Address</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2">
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Street / House Address
                        </label>
                        <input
                          value={addressLine}
                          onChange={(e) => setAddressLine(e.target.value)}
                          placeholder="e.g. 12/B, Gomti Nagar"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">City</label>
                        <input
                          value={city}
                          onChange={(e) => setCity(e.target.value)}
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">PIN Code</label>
                        <input
                          value={pinCode}
                          onChange={(e) => setPinCode(e.target.value)}
                          placeholder="e.g. 226010"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Step 4: Previous Schooling (Optional) */}
                  <div className="bg-surface rounded-card border border-rule p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2 border-b border-rule pb-3">
                      <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                        4
                      </span>
                      <h3 className="text-base font-bold text-ink">Previous School Details (If Applicable)</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Previous School Name
                        </label>
                        <input
                          value={prevSchoolName}
                          onChange={(e) => setPrevSchoolName(e.target.value)}
                          placeholder="Name of last school"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Last Class Passed
                        </label>
                        <input
                          value={prevLastClass}
                          onChange={(e) => setPrevLastClass(e.target.value)}
                          placeholder="e.g. UKG, Class 4"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-ink-soft mb-1">
                          Transfer Certificate (TC) No.
                        </label>
                        <input
                          value={prevTcNo}
                          onChange={(e) => setPrevTcNo(e.target.value)}
                          placeholder="TC reference number"
                          className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Step 5: Consents & Declarations (§5.1.4 Step 9: Explicit & Never Pre-ticked) */}
                  <div className="bg-surface rounded-card border border-rule p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2 border-b border-rule pb-3">
                      <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                        5
                      </span>
                      <h3 className="text-base font-bold text-ink">Declarations & Consent (Mandatory)</h3>
                    </div>

                    <div className="space-y-3 pt-1">
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          required
                          checked={consentAccuracy}
                          onChange={(e) => setConsentAccuracy(e.target.checked)}
                          className="mt-1 rounded border-rule text-primary focus:ring-primary h-4 w-4"
                        />
                        <span className="text-xs text-ink leading-relaxed">
                          <strong className="text-ink">Accuracy Declaration:</strong> I hereby declare that all
                          information provided in this application form is true, correct, and complete to the
                          best of my knowledge. I understand that any false statement may lead to cancellation of
                          admission.
                        </span>
                      </label>

                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          required
                          checked={consentRules}
                          onChange={(e) => setConsentRules(e.target.checked)}
                          className="mt-1 rounded border-rule text-primary focus:ring-primary h-4 w-4"
                        />
                        <span className="text-xs text-ink leading-relaxed">
                          <strong className="text-ink">School Rules & Regulations:</strong> I have read and agree
                          to abide by the school code of conduct, fee payment timelines, and disciplinary policies
                          of Sunrise Public School.
                        </span>
                      </label>

                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          required
                          checked={consentData}
                          onChange={(e) => setConsentData(e.target.checked)}
                          className="mt-1 rounded border-rule text-primary focus:ring-primary h-4 w-4"
                        />
                        <span className="text-xs text-ink leading-relaxed">
                          <strong className="text-ink">Data Processing Consent:</strong> I give full consent to
                          the school administration to process, verify, and store our submitted personal data for
                          the purpose of enrollment and educational administration.
                        </span>
                      </label>

                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={consentMedia}
                          onChange={(e) => setConsentMedia(e.target.checked)}
                          className="mt-1 rounded border-rule text-primary focus:ring-primary h-4 w-4"
                        />
                        <span className="text-xs text-ink-soft leading-relaxed">
                          <strong className="text-ink">Media & Photography (Optional):</strong> I grant permission
                          for the student to participate in school media, newsletters, and educational website
                          features.
                        </span>
                      </label>
                    </div>

                    {/* Bot honeypot */}
                    <div style={{ display: "none" }} aria-hidden="true">
                      <input
                        tabIndex={-1}
                        autoComplete="off"
                        value={honeypot}
                        onChange={(e) => setHoneypot(e.target.value)}
                      />
                    </div>
                  </div>

                  {submitError && (
                    <div className="bg-red-50 border border-red-200 text-danger text-sm rounded-lg p-4 font-medium">
                      {submitError}
                    </div>
                  )}

                  {/* Form Action Footer */}
                  <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 border-t border-rule">
                    <p className="text-xs text-ink-soft">
                      By submitting this form, you will receive an official application tracking number.
                    </p>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full md:w-auto px-8 py-3 bg-primary hover:bg-primary-dark text-white font-bold text-sm rounded-input shadow-md transition-all disabled:opacity-50"
                    >
                      {submitting ? "Submitting Application..." : "Submit Online Application"}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: CHECK APPLICATION STATUS */}
        {activeTab === "status" && (
          <div className="space-y-6">
            <div className="bg-surface rounded-card border border-rule p-8 shadow-card max-w-xl mx-auto space-y-6">
              <div>
                <h2 className="text-xl font-bold text-ink">Check Application Status</h2>
                <p className="text-xs text-ink-soft mt-1">
                  Enter your application reference number and the student's date of birth to view current progress.
                </p>
              </div>

              <form onSubmit={handleStatusCheck} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Application Reference Number
                  </label>
                  <input
                    required
                    value={searchAppNo}
                    onChange={(e) => setSearchAppNo(e.target.value.toUpperCase())}
                    placeholder="e.g. APP-2026-0001"
                    className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono font-bold outline-none focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Child's Date of Birth
                  </label>
                  <input
                    type="date"
                    required
                    value={searchDob}
                    onChange={(e) => setSearchDob(e.target.value)}
                    className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                  />
                </div>

                {statusError && (
                  <div className="bg-red-50 border border-red-200 text-danger text-xs rounded-md p-3 font-medium">
                    {statusError}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={statusLoading}
                  className="w-full py-2.5 bg-primary hover:bg-primary-dark text-white font-bold text-sm rounded-input shadow transition-all disabled:opacity-50"
                >
                  {statusLoading ? "Searching Record..." : "Check Status"}
                </button>
              </form>

              {/* Status Result Display */}
              {statusResult && (
                <div className="mt-6 border-t border-rule pt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs text-ink-faint">Application Reference</span>
                      <div className="text-base font-mono font-bold text-ink">
                        {statusResult.application_no}
                      </div>
                    </div>
                    <span
                      className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider ${
                        statusResult.status === "admitted"
                          ? "bg-emerald-100 text-emerald-800"
                          : statusResult.status === "rejected" || statusResult.status === "documents_rejected"
                          ? "bg-red-100 text-red-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {statusResult.status.replace(/_/g, " ")}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs bg-ground p-3 rounded-lg border border-rule">
                    <div>
                      <span className="text-ink-soft">Student Name</span>
                      <p className="font-semibold text-ink">{statusResult.name}</p>
                    </div>
                    <div>
                      <span className="text-ink-soft">Class Applied</span>
                      <p className="font-semibold text-ink">{statusResult.class_applying_for}</p>
                    </div>
                    <div className="col-span-2">
                      <span className="text-ink-soft">Submission Date</span>
                      <p className="font-medium text-ink">
                        {new Date(statusResult.submitted_at).toLocaleString("en-IN")}
                      </p>
                    </div>
                  </div>

                  {statusResult.action_needed && (
                    <div className="bg-amber-50 border border-amber-300 text-amber-900 rounded-lg p-3 text-xs font-medium">
                      <strong>Action Required:</strong> Immediate attention is needed regarding this
                      application. Please visit the school reception or check your registered mobile for
                      instructions.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: SEAT MATRIX & CRITERIA */}
        {activeTab === "info" && (
          <div className="space-y-6">
            <div className="bg-surface rounded-card border border-rule p-6 shadow-card space-y-6">
              <div>
                <h2 className="text-xl font-bold text-ink">Class Seat Matrix & Eligibility</h2>
                <p className="text-xs text-ink-soft mt-1">
                  Overview of available classes, age requirements, and assessment procedures.
                </p>
              </div>

              {cycleData?.classes && cycleData.classes.length > 0 ? (
                <div className="overflow-x-auto border border-rule rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-ground border-b border-rule font-semibold text-ink-soft">
                      <tr>
                        <th className="p-3">Class</th>
                        <th className="p-3">Total Intake</th>
                        <th className="p-3">Min Age</th>
                        <th className="p-3">Max Age</th>
                        <th className="p-3">Test Required</th>
                        <th className="p-3">Interview</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rule">
                      {cycleData.classes.map((c) => (
                        <tr key={c.class_name} className="hover:bg-ground/40">
                          <td className="p-3 font-semibold text-ink">{c.class_name}</td>
                          <td className="p-3 font-mono font-medium">{c.total_seats} seats</td>
                          <td className="p-3 text-ink-soft">
                            {c.min_age_years ? `${c.min_age_years} yrs` : "N/A"}
                          </td>
                          <td className="p-3 text-ink-soft">
                            {c.max_age_years ? `${c.max_age_years} yrs` : "N/A"}
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                                c.requires_test ? "bg-amber-100 text-amber-800" : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              {c.requires_test ? "Yes (Written)" : "No"}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                                c.requires_interview
                                  ? "bg-purple-100 text-purple-800"
                                  : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              {c.requires_interview ? "Yes" : "No"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-6 text-xs text-ink-faint">No class details available.</div>
              )}

              {/* Required Documents Checklist */}
              <div className="bg-ground rounded-xl p-5 border border-rule space-y-3">
                <h3 className="text-sm font-bold text-ink">Mandatory Documents Checklist for Verification</h3>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-ink-soft list-disc list-inside">
                  <li>Original & Photocopy of Student's Birth Certificate</li>
                  <li>Student's Aadhaar Card / ID Proof</li>
                  <li>Father's and Mother's Aadhaar Cards / Identity Proofs</li>
                  <li>Residential Address Proof (Electricity bill / Voter ID / Passport)</li>
                  <li>Four Recent Passport Size Photographs of the Student</li>
                  <li>Transfer Certificate (TC) from recognized previous school (Class 1 onwards)</li>
                  <li>Previous Academic Year Report Card / Marksheet</li>
                  <li>Caste / Category Certificate (if applying under SC/ST/OBC/RTE)</li>
                </ul>
              </div>

              {/* Refund Policy */}
              {cycleData?.cycle.refund_policy && (
                <div className="text-xs text-ink-soft border-t border-rule pt-4">
                  <strong className="text-ink">Admission Fee Refund Policy:</strong>{" "}
                  {cycleData.cycle.refund_policy}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
