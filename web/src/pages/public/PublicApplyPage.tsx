import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { api, toMediaUrl } from "../../api/client";

// =====================================================================
// Types
// =====================================================================

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

export type UploadedDocState = {
  code: string;
  filename: string;
  url: string;
  size: number;
};

export type ApplicationStatusResult = {
  application_no: string;
  name: string;
  class_applying_for: string;
  status: string;
  stage: "submitted" | "under_review" | "offer_issued" | "enrolled" | "rejected";
  submitted_at: string;
  action_needed: boolean;
  is_payable: boolean;
  payable_amount: string | null;
  documents_available: boolean;
  offer?: {
    id: number;
    status: string;
    class_name: string;
    stream: string | null;
    offer_amount: string | null;
    expires_on: string;
    is_expired: boolean;
  } | null;
  student?: {
    id: number;
    admission_no: string;
    class_label: string;
    roll_no: number | null;
    status: string;
  } | null;
  receipt?: {
    receipt_no: string;
    amount: string;
    paid_at: string;
  } | null;
};

// =====================================================================
// Universal File & Photo Uploader Component
// =====================================================================

function UniversalUploadField({
  label,
  value,
  filename,
  onChange,
  schoolCode,
  helperText,
  acceptPdf = false,
  required = false,
}: {
  label: string;
  value: string | null;
  filename?: string | null;
  onChange: (url: string | null, filename: string | null, size: number) => void;
  schoolCode: string;
  helperText?: string;
  acceptPdf?: boolean;
  required?: boolean;
}) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const isImage = file.type.startsWith("image/") || /\.(jpg|jpeg|png|webp)$/i.test(file.name);
    const isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);

    if (acceptPdf ? !isImage && !isPdf : !isImage) {
      setUploadError(acceptPdf ? "Allowed file types: JPG, PNG, WEBP, or PDF." : "Allowed file types: JPG, PNG, WEBP.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File size exceeds 10MB limit.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.upload<{ url: string; filename: string; size: number }>(
        `/public/${schoolCode}/admission/upload`,
        formData
      );
      if (res?.url) {
        onChange(res.url, res.filename || file.name, res.size || file.size);
      }
    } catch (err: any) {
      setUploadError(err?.message || "Failed to upload file.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const isPdf = value?.toLowerCase().endsWith(".pdf") || filename?.toLowerCase().endsWith(".pdf");
  const displayUrl = toMediaUrl(value);

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="block text-xs font-semibold text-ink-soft">
          {label} {required && <span className="text-danger">*</span>}
        </label>
        {value && (
          <span className="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <span>✓</span> Uploaded
          </span>
        )}
      </div>

      {value ? (
        <div className="flex items-center gap-3 p-3 bg-ground border border-rule rounded-lg">
          {isPdf ? (
            <div className="w-12 h-14 bg-red-100 text-red-700 font-bold rounded flex flex-col items-center justify-center text-[10px] border border-red-200 shrink-0">
              <span className="text-base">📄</span>
              <span>PDF</span>
            </div>
          ) : displayUrl ? (
            <img
              src={displayUrl}
              alt="Uploaded Preview"
              className="w-12 h-14 object-cover rounded border border-rule shadow-xs shrink-0"
            />
          ) : (
            <div className="w-12 h-14 bg-slate-200 text-slate-600 font-bold rounded flex items-center justify-center text-xs shrink-0">
              FILE
            </div>
          )}

          <div className="flex-1 min-w-0">
            <span className="text-xs text-ink font-medium block truncate">
              {filename || "Uploaded Document"}
            </span>
            <div className="flex items-center gap-3 mt-1">
              {displayUrl && (
                <a
                  href={displayUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline font-semibold"
                >
                  View File
                </a>
              )}
              <button
                type="button"
                onClick={() => onChange(null, null, 0)}
                className="text-xs text-danger hover:underline font-semibold"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <label className="flex flex-col items-center justify-center p-4 border-2 border-dashed border-rule rounded-lg hover:border-primary/50 cursor-pointer bg-ground/40 hover:bg-surface text-xs text-ink-soft hover:text-ink transition group">
            <input
              type="file"
              accept={acceptPdf ? ".jpg,.jpeg,.png,.webp,.pdf" : ".jpg,.jpeg,.png,.webp"}
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
            {uploading ? (
              <span className="flex items-center gap-2 text-primary font-medium">
                <span className="animate-spin inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
                Uploading document...
              </span>
            ) : (
              <div className="text-center space-y-1">
                <div className="text-lg group-hover:scale-110 transition-transform">
                  {acceptPdf ? "📁" : "📷"}
                </div>
                <div className="font-semibold text-primary">Click to select and upload</div>
                <div className="text-[11px] text-ink-faint">
                  {acceptPdf ? "Supports PDF, JPG, PNG (Max 10MB)" : "Supports JPG, PNG, WEBP (Max 10MB)"}
                </div>
              </div>
            )}
          </label>
          {helperText && <p className="text-[11px] text-ink-faint mt-1.5">{helperText}</p>}
        </div>
      )}
      {uploadError && <p className="text-xs text-danger font-medium mt-1">{uploadError}</p>}
    </div>
  );
}

// =====================================================================
// Main Public Admission Component
// =====================================================================

export function PublicApplyPage() {
  const [activeTab, setActiveTab] = useState<"apply" | "status" | "info">("apply");
  const schoolCode = "SPS";

  // Admission Cycle Query
  const cycleQuery = useQuery<OpenCycleData>({
    queryKey: ["public-admission-open", schoolCode],
    queryFn: () => api.rawGet<OpenCycleData>(`/public/${schoolCode}/admission/open`),
    retry: 1,
  });

  // -------------------------------------------------------------------
  // Wizard Step Tracker: 1 to 7
  // -------------------------------------------------------------------
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Step 1: Student Information
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("male");
  const [selectedClass, setSelectedClass] = useState("");
  const [stream, setStream] = useState("");
  const [nationality, setNationality] = useState("Indian");
  const [religion, setReligion] = useState("Hindu");
  const [casteCategory, setCasteCategory] = useState("General");
  const [admissionCategory, setAdmissionCategory] = useState("general");
  const [motherTongue, setMotherTongue] = useState("Hindi");
  const [placeOfBirth, setPlaceOfBirth] = useState("Lucknow");
  const [identificationMarks, setIdentificationMarks] = useState("");
  const [isSingleChild, setIsSingleChild] = useState(false);
  const [aadhaarLast4, setAadhaarLast4] = useState("");
  const [secondLanguage, setSecondLanguage] = useState("Hindi");
  const [transportRequired, setTransportRequired] = useState(false);
  const [studentPhotoUrl, setStudentPhotoUrl] = useState<string | null>(null);

  // Address
  const [addressLine, setAddressLine] = useState("");
  const [city, setCity] = useState("Lucknow");
  const [pinCode, setPinCode] = useState("226010");
  const [stateName, setStateName] = useState("Uttar Pradesh");

  // Step 2: Parent / Guardian Details
  // Primary Guardian
  const [guardianRelation, setGuardianRelation] = useState<"father" | "mother" | "other">("father");
  const [guardianName, setGuardianName] = useState("");
  const [guardianMobile, setGuardianMobile] = useState("");
  const [guardianEmail, setGuardianEmail] = useState("");
  const [guardianQualification, setGuardianQualification] = useState("Post Graduate");
  const [guardianOccupation, setGuardianOccupation] = useState("");
  const [guardianDesignation, setGuardianDesignation] = useState("");
  const [guardianOrganisation, setGuardianOrganisation] = useState("");
  const [guardianIncomeBand, setGuardianIncomeBand] = useState("10-20 LPA");
  const [guardianOfficeAddress, setGuardianOfficeAddress] = useState("");
  const [guardianAltMobile, setGuardianAltMobile] = useState("");
  const [guardianPhotoUrl, setGuardianPhotoUrl] = useState<string | null>(null);

  // Secondary Guardian (optional)
  const [hasSecondGuardian, setHasSecondGuardian] = useState(false);
  const [secRelation, setSecRelation] = useState<"father" | "mother" | "other">("mother");
  const [secName, setSecName] = useState("");
  const [secMobile, setSecMobile] = useState("");
  const [secEmail, setSecEmail] = useState("");
  const [secQualification, setSecQualification] = useState("Graduate");
  const [secOccupation, setSecOccupation] = useState("");
  const [secDesignation, setSecDesignation] = useState("");
  const [secOrganisation, setSecOrganisation] = useState("");
  const [secIncomeBand, setSecIncomeBand] = useState("5-10 LPA");
  const [secOfficeAddress, setSecOfficeAddress] = useState("");
  const [secPhotoUrl, setSecPhotoUrl] = useState<string | null>(null);

  // Authorized Pickup Persons (Escorts)
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
        notes: "Authorized for afternoon pickup",
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

  // Step 3: Academic History
  const [prevSchoolName, setPrevSchoolName] = useState("");
  const [prevBoard, setPrevBoard] = useState("CBSE");
  const [prevLastClass, setPrevLastClass] = useState("");
  const [prevPercentage, setPrevPercentage] = useState("");
  const [prevTcNo, setPrevTcNo] = useState("");

  // Step 4: Siblings & Medical
  const [hasSibling, setHasSibling] = useState(false);
  const [siblingName, setSiblingName] = useState("");
  const [siblingAge, setSiblingAge] = useState("");
  const [siblingClassId, setSiblingClassId] = useState("");

  const [bloodGroup, setBloodGroup] = useState("B+");
  const [knownAllergies, setKnownAllergies] = useState("");
  const [chronicConditions, setChronicConditions] = useState("");
  const [regularMedication, setRegularMedication] = useState("");
  const [emergencyDoctor, setEmergencyDoctor] = useState("");
  const [emergencyDoctorPhone, setEmergencyDoctorPhone] = useState("");
  const [consentEmergencyTreatment, setConsentEmergencyTreatment] = useState(true);

  // Step 5: Document Uploads
  const [uploadedDocs, setUploadedDocs] = useState<Record<string, UploadedDocState>>({});

  const handleDocChange = (code: string, url: string | null, filename: string | null, size: number) => {
    setUploadedDocs((prev) => {
      const next = { ...prev };
      if (!url) {
        delete next[code];
      } else {
        next[code] = { code, filename: filename || code, url, size };
      }
      return next;
    });
  };

  // Step 6: Mandatory Declarations
  const [consentAccuracy, setConsentAccuracy] = useState(false);
  const [consentRules, setConsentRules] = useState(false);
  const [consentData, setConsentData] = useState(false);
  const [consentMedia, setConsentMedia] = useState(false);
  const [honeypot, setHoneypot] = useState("");

  // Step 7: Submission Result
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submittedAppNo, setSubmittedAppNo] = useState<string | null>(null);
  const [nextStepInfo, setNextStepInfo] = useState<string | null>(null);

  // -------------------------------------------------------------------
  // Status Lookup State
  // -------------------------------------------------------------------
  const [searchAppNo, setSearchAppNo] = useState("");
  const [searchMobile, setSearchMobile] = useState("");
  const [searchDob, setSearchDob] = useState("");
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statusResult, setStatusResult] = useState<ApplicationStatusResult | null>(null);

  // -------------------------------------------------------------------
  // Mock Payment Gateway Modal State
  // -------------------------------------------------------------------
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentInitiating, setPaymentInitiating] = useState(false);
  const [paymentProcessing, setPaymentProcessing] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [orderToken, setOrderToken] = useState<string | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [payableAmount, setPayableAmount] = useState<string | null>(null);
  const [paymentMethodTab, setPaymentMethodTab] = useState<"upi" | "card" | "netbanking">("upi");
  const [selectedBank, setSelectedBank] = useState("sbi");

  // -------------------------------------------------------------------
  // Official Gated Document Preview Modal State
  // -------------------------------------------------------------------
  const [activeDocModal, setActiveDocModal] = useState<"dossier" | "admission_letter" | "receipt" | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docData, setDocData] = useState<any | null>(null);
  const [docError, setDocError] = useState<string | null>(null);

  // -------------------------------------------------------------------
  // Step Validation Helpers
  // -------------------------------------------------------------------
  const validateStep = (step: number): boolean => {
    setSubmitError(null);
    if (step === 1) {
      if (!firstName.trim() || !lastName.trim()) {
        setSubmitError("Please provide both First Name and Last Name of the student.");
        return false;
      }
      if (!dob) {
        setSubmitError("Please provide the student's Date of Birth.");
        return false;
      }
      if (!selectedClass) {
        setSubmitError("Please select the class applying for.");
        return false;
      }
      if (aadhaarLast4 && (!/^\d{4}$/.test(aadhaarLast4.trim()))) {
        setSubmitError("Aadhaar last 4 digits must be exactly 4 numeric digits.");
        return false;
      }
      if (!addressLine.trim() || !pinCode.trim()) {
        setSubmitError("Please fill in Street Address and PIN Code.");
        return false;
      }
      return true;
    }
    if (step === 2) {
      if (!guardianName.trim() || !guardianMobile.trim()) {
        setSubmitError("Primary Parent / Guardian Full Name and Mobile Number are required.");
        return false;
      }
      if (!/^\d{10}$/.test(guardianMobile.trim())) {
        setSubmitError("Primary guardian mobile number must be exactly 10 digits.");
        return false;
      }
      if (hasSecondGuardian && secMobile.trim() && !/^\d{10}$/.test(secMobile.trim())) {
        setSubmitError("Second guardian mobile number must be exactly 10 digits.");
        return false;
      }
      for (let i = 0; i < authorizedPersons.length; i++) {
        const p = authorizedPersons[i];
        if (!p.name.trim() || !/^\d{10}$/.test(p.phone.trim())) {
          setSubmitError(`Authorized pickup person #${i + 1} requires a valid name and 10-digit mobile phone.`);
          return false;
        }
      }
      return true;
    }
    if (step === 5) {
      if (!uploadedDocs["birth_certificate"]?.url) {
        setSubmitError("Please upload the Student's Birth Certificate (Mandatory).");
        return false;
      }
      if (!uploadedDocs["address_proof"]?.url) {
        setSubmitError("Please upload a valid Residential Address Proof (Mandatory).");
        return false;
      }
      return true;
    }
    if (step === 6) {
      if (!consentAccuracy || !consentRules || !consentData) {
        setSubmitError("All mandatory declarations must be accepted before submitting your application.");
        return false;
      }
      return true;
    }
    return true;
  };

  const safeScrollTo = (top: number) => {
    if (typeof window !== "undefined" && typeof window.scrollTo === "function") {
      try {
        window.scrollTo({ top, behavior: "smooth" });
      } catch {
        // Fallback for test environments
      }
    }
  };

  const handleNextStep = () => {
    if (validateStep(currentStep)) {
      setSubmitError(null);
      setCurrentStep((prev) => Math.min(prev + 1, 6));
      safeScrollTo(120);
    }
  };

  const handlePrevStep = () => {
    setSubmitError(null);
    setCurrentStep((prev) => Math.max(prev - 1, 1));
    safeScrollTo(120);
  };

  // -------------------------------------------------------------------
  // Submit Application Handler
  // -------------------------------------------------------------------
  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateStep(6)) return;

    const guardiansList = [
      {
        relation: guardianRelation,
        full_name: guardianName.trim(),
        mobile: guardianMobile.trim(),
        email: guardianEmail.trim() || null,
        qualification: guardianQualification.trim() || null,
        occupation: guardianOccupation.trim() || null,
        designation: guardianDesignation.trim() || null,
        organisation: guardianOrganisation.trim() || null,
        annual_income_band: guardianIncomeBand.trim() || null,
        office_address: guardianOfficeAddress.trim() || null,
        alternate_mobile: guardianAltMobile.trim() || null,
        photo_url: guardianPhotoUrl || null,
        is_authorised_for_pickup: true,
        is_primary: true,
        is_emergency_contact: true,
      },
    ];

    if (hasSecondGuardian && secName.trim() && secMobile.trim()) {
      guardiansList.push({
        relation: secRelation,
        full_name: secName.trim(),
        mobile: secMobile.trim(),
        email: secEmail.trim() || null,
        qualification: secQualification.trim() || null,
        occupation: secOccupation.trim() || null,
        designation: secDesignation.trim() || null,
        organisation: secOrganisation.trim() || null,
        annual_income_band: secIncomeBand.trim() || null,
        office_address: secOfficeAddress.trim() || null,
        alternate_mobile: null,
        photo_url: secPhotoUrl || null,
        is_authorised_for_pickup: true,
        is_primary: false,
        is_emergency_contact: true,
      });
    }

    const docList = Object.values(uploadedDocs).map((d) => ({
      code: d.code,
      filename: d.filename,
      url: d.url,
      size: d.size,
    }));

    if (studentPhotoUrl) {
      docList.push({
        code: "student_photo",
        filename: "student_photo.jpg",
        url: studentPhotoUrl,
        size: 10240,
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
      nationality: nationality.trim() || "Indian",
      religion: religion.trim() || null,
      caste_category: casteCategory.trim() || null,
      admission_category: admissionCategory,
      mother_tongue: motherTongue.trim() || null,
      place_of_birth: placeOfBirth.trim() || null,
      identification_marks: identificationMarks.trim() || null,
      is_single_child: isSingleChild,
      aadhaar_last4: aadhaarLast4.trim() || null,
      second_language: secondLanguage.trim() || null,
      transport_required: transportRequired,
      photo_url: studentPhotoUrl || null,
      address: {
        address_line: addressLine.trim(),
        city: city.trim(),
        pin_code: pinCode.trim(),
        state: stateName.trim(),
      },
      previous_school: prevSchoolName.trim()
        ? {
            school_name: prevSchoolName.trim(),
            board: prevBoard.trim() || null,
            last_class: prevLastClass.trim() || null,
            percentage: prevPercentage.trim() || null,
            tc_number: prevTcNo.trim() || null,
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
      siblings:
        hasSibling && siblingName.trim()
          ? [
              {
                name: siblingName.trim(),
                age: siblingAge ? parseInt(siblingAge, 10) : null,
                school_name: "Sunrise School",
                student_id: siblingClassId.trim() || null,
              },
            ]
          : [],
      medical: {
        blood_group: bloodGroup,
        known_allergies: knownAllergies.trim() || null,
        chronic_conditions: chronicConditions.trim() || null,
        regular_medication: regularMedication.trim() || null,
        emergency_doctor: emergencyDoctor.trim() || null,
        emergency_doctor_phone: emergencyDoctorPhone.trim() || null,
        consent_for_emergency_treatment: consentEmergencyTreatment,
      },
      documents: docList,
      heard_about_us: "website",
      information_accuracy: consentAccuracy,
      school_rules_accepted: consentRules,
      data_processing_consent: consentData,
      photo_media_consent: consentMedia,
      website: honeypot.trim() || null,
    };

    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await api.rawPost<{ application_no: string; status: string; next_step: string }>(
        `/public/${schoolCode}/admission/apply`,
        payload
      );
      setSubmittedAppNo(res.application_no);
      setNextStepInfo(res.next_step);
      setCurrentStep(7);
      safeScrollTo(0);
    } catch (err: any) {
      setSubmitError(err?.message || "Failed to submit application. Please verify details.");
    } finally {
      setSubmitting(false);
    }
  };

  // -------------------------------------------------------------------
  // Application Status Check Handler
  // -------------------------------------------------------------------
  const handleStatusCheck = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setStatusError(null);
    setStatusResult(null);

    const cleanApp = searchAppNo.trim().toUpperCase();
    const cleanMobile = searchMobile.trim().replace(/\D/g, "");
    const cleanDob = searchDob.trim();

    if (!cleanApp) {
      setStatusError("Please enter your Application Reference Number (e.g. APP-2026-0001).");
      return;
    }

    if (!cleanMobile && !cleanDob) {
      setStatusError("Please enter the registered parent/guardian mobile number.");
      return;
    }

    setStatusLoading(true);
    try {
      let query = `?application_no=${encodeURIComponent(cleanApp)}`;
      if (cleanMobile) {
        query += `&mobile=${encodeURIComponent(cleanMobile)}`;
      }
      if (cleanDob) {
        query += `&date_of_birth=${encodeURIComponent(cleanDob)}`;
      }

      const res = await api.rawGet<ApplicationStatusResult>(
        `/public/${schoolCode}/admission/status`,
        query
      );
      setStatusResult(res);
    } catch (err: any) {
      setStatusError(
        err?.message ||
          "No matching application found. Please verify the Application Reference Number and registered Guardian Mobile Number."
      );
    } finally {
      setStatusLoading(false);
    }
  };

  // -------------------------------------------------------------------
  // Initiate Mock Payment Flow
  // -------------------------------------------------------------------
  const handleInitiatePayment = async () => {
    if (!statusResult) return;
    setPaymentInitiating(true);
    setPaymentError(null);
    try {
      const payload = {
        application_no: statusResult.application_no,
        mobile: searchMobile.trim() || undefined,
      };
      const res = await api.rawPost<{
        status: string;
        order_id: string;
        order_token: string;
        amount: string;
        currency: string;
      }>(`/public/${schoolCode}/admission/payments/initiate`, payload);

      setOrderId(res.order_id);
      setOrderToken(res.order_token);
      setPayableAmount(res.amount);
      setShowPaymentModal(true);
    } catch (err: any) {
      setPaymentError(err?.message || "Failed to initiate payment gateway order.");
    } finally {
      setPaymentInitiating(false);
    }
  };

  // -------------------------------------------------------------------
  // Process Mock Payment Simulation (Success / Failure / Cancel)
  // -------------------------------------------------------------------
  const handleProcessPayment = async (scenario: "success" | "failure" | "cancel") => {
    if (!orderToken) return;
    setPaymentProcessing(true);
    setPaymentError(null);

    const idempotencyKey = `PAY-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    try {
      const res = await api.rawPost<{
        status: string;
        receipt_no?: string;
        message?: string;
        error?: string;
      }>(`/public/${schoolCode}/admission/payments/process`, {
        order_token: orderToken,
        scenario,
        idempotency_key: idempotencyKey,
      });

      if (scenario === "success" && res.status === "success") {
        setShowPaymentModal(false);
        // Refresh status to enrolled state
        await handleStatusCheck();
      } else if (scenario === "failure") {
        setPaymentError(res.error || "Payment simulation failed. Card / bank transaction declined.");
      } else if (scenario === "cancel") {
        setShowPaymentModal(false);
      }
    } catch (err: any) {
      setPaymentError(err?.message || "Payment processing exception occurred.");
    } finally {
      setPaymentProcessing(false);
    }
  };

  // -------------------------------------------------------------------
  // Gated Document Viewer Handler
  // -------------------------------------------------------------------
  const handleOpenDocModal = async (docType: "dossier" | "admission_letter" | "receipt") => {
    if (!statusResult) return;
    setActiveDocModal(docType);
    setDocLoading(true);
    setDocError(null);
    setDocData(null);
    try {
      const mobileParam = searchMobile.trim() || guardianMobile.trim();
      const res = await api.rawGet<any>(
        `/public/${schoolCode}/admission/documents/${docType}?application_no=${encodeURIComponent(
          statusResult.application_no
        )}&mobile=${encodeURIComponent(mobileParam)}`
      );
      setDocData(res);
    } catch (err: any) {
      setDocError(err?.message || "Failed to load official document. Please contact the admissions cell.");
    } finally {
      setDocLoading(false);
    }
  };

  const resetForm = () => {
    setSubmittedAppNo(null);
    setCurrentStep(1);
    setFirstName("");
    setMiddleName("");
    setLastName("");
    setDob("");
    setGuardianName("");
    setGuardianMobile("");
    setGuardianEmail("");
    setAddressLine("");
    setPinCode("226010");
    setPrevSchoolName("");
    setUploadedDocs({});
    setStudentPhotoUrl(null);
    setConsentAccuracy(false);
    setConsentRules(false);
    setConsentData(false);
    setConsentMedia(false);
  };

  const cycleData = cycleQuery.data;

  return (
    <div className="min-h-screen bg-ground text-ink font-sans pb-24">
      {/* Top Header & Portal Navigation */}
      <header className="bg-surface border-b border-rule shadow-sm sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-3 hover:opacity-95 transition-opacity">
              <div className="w-11 h-11 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-lg shadow-sm">
                SPS
              </div>
              <div>
                <h1 className="text-lg font-bold text-ink tracking-tight flex items-center gap-2">
                  Sunrise Public School
                  <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                    CBSE
                  </span>
                </h1>
                <p className="text-xs text-ink-soft">
                  Online Admission Portal • Gomti Nagar, Lucknow
                </p>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex rounded-lg bg-ground p-1 border border-rule">
              <button
                onClick={() => {
                  setActiveTab("apply");
                  setSubmitError(null);
                }}
                className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "apply" ? "bg-white text-primary shadow-xs" : "text-ink-soft hover:text-ink"
                }`}
              >
                Apply Online (2025–26)
              </button>
              <button
                onClick={() => {
                  setActiveTab("status");
                  setStatusError(null);
                }}
                className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "status" ? "bg-white text-primary shadow-xs" : "text-ink-soft hover:text-ink"
                }`}
              >
                Track Status & Pay Fee
              </button>
              <button
                onClick={() => setActiveTab("info")}
                className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "info" ? "bg-white text-primary shadow-xs" : "text-ink-soft hover:text-ink"
                }`}
              >
                Seat Matrix & Criteria
              </button>
            </div>

            <Link
              to="/login"
              className="text-xs font-semibold text-ink-soft hover:text-primary px-3 py-1.5 rounded-lg border border-rule hover:border-primary/40 transition-colors"
            >
              Staff ERP Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-4xl mx-auto px-4 pt-8">
        {/* ============================================================= */}
        {/* TAB 1: 7-STEP ADMISSION WIZARD                                */}
        {/* ============================================================= */}
        {activeTab === "apply" && (
          <div>
            {currentStep === 7 && submittedAppNo ? (
              /* Success Screen */
              <div className="bg-surface rounded-card border border-rule shadow-card p-8 md:p-12 text-center space-y-6 animate-fade-in">
                <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-4xl font-bold shadow-xs">
                  ✓
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                    Application Successfully Registered
                  </span>
                  <h2 className="text-2xl md:text-3xl font-bold text-ink mt-3">
                    Application Submitted to Admissions Cell
                  </h2>
                  <p className="text-sm text-ink-soft max-w-lg mx-auto mt-2">
                    Thank you for applying to Sunrise Public School. Your application and uploaded documents have
                    been securely forwarded to our Admissions Committee for initial verification.
                  </p>
                </div>

                <div className="bg-ground border border-rule rounded-2xl p-6 max-w-md mx-auto shadow-inner">
                  <div className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
                    Official Application Reference Number
                  </div>
                  <div className="text-3xl font-mono font-bold text-primary mt-2 select-all tracking-wider">
                    {submittedAppNo}
                  </div>
                  <div className="mt-3 flex items-center justify-center gap-2">
                    <span className="inline-block bg-primary/10 text-primary text-xs font-semibold px-3 py-1 rounded-full">
                      Status: Submitted & In Verification Queue
                    </span>
                  </div>
                </div>

                <div className="text-sm text-ink-soft max-w-xl mx-auto bg-blue-50/80 border border-blue-200 text-blue-900 rounded-xl p-5 text-left space-y-2">
                  <p className="font-bold text-xs uppercase tracking-wide text-blue-800 flex items-center gap-1.5">
                    <span>ℹ️</span> What Happens Next?
                  </p>
                  <p className="text-xs text-blue-950 leading-relaxed">
                    1. <strong>Document Verification:</strong> The admissions desk will review your uploaded
                    birth certificate and address proof within 1–2 working days.
                  </p>
                  <p className="text-xs text-blue-950 leading-relaxed">
                    2. <strong>Interaction / Assessment:</strong> For qualifying grades, the school office will
                    send an SMS alert to your registered mobile (<strong>{guardianMobile}</strong>) with the
                    interview schedule.
                  </p>
                  <p className="text-xs text-blue-950 leading-relaxed">
                    3. <strong>Provisional Offer & Fee Payment:</strong> Once selected, your status will reflect{" "}
                    <strong>Offer Issued</strong>, allowing you to pay the admission fee online and finalize
                    enrollment.
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                  <button
                    onClick={() => {
                      setSearchAppNo(submittedAppNo);
                      setSearchMobile(guardianMobile);
                      setActiveTab("status");
                      handleStatusCheck();
                    }}
                    className="px-6 py-3 bg-primary text-white text-sm font-semibold rounded-input shadow-md hover:bg-primary-dark transition-all flex items-center gap-2"
                  >
                    <span>🔍</span> Track Application Status Now
                  </button>
                  <button
                    onClick={() => window.print()}
                    className="px-5 py-3 bg-surface border border-rule text-ink text-sm font-semibold rounded-input hover:bg-ground transition-all flex items-center gap-2"
                  >
                    <span>🖨️</span> Print Submission Slip
                  </button>
                  <button
                    onClick={resetForm}
                    className="px-5 py-3 bg-surface border border-rule text-ink-soft text-sm font-semibold rounded-input hover:bg-ground transition-all"
                  >
                    Submit Another Application
                  </button>
                </div>
              </div>
            ) : cycleQuery.isLoading ? (
              <div className="bg-surface rounded-card border border-rule p-12 text-center text-ink-faint">
                <span className="animate-spin inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full mb-3" />
                <p>Loading active admission cycle and classes...</p>
              </div>
            ) : cycleQuery.isError ? (
              <div className="bg-surface rounded-card border border-red-200 p-8 text-center space-y-3">
                <div className="text-danger font-bold text-lg">Admissions Currently Closed</div>
                <p className="text-sm text-ink-soft">
                  Sunrise Public School is not accepting online applications at this time. Please contact the
                  school reception at +91 522 261 1101 for in-person admissions or further details.
                </p>
              </div>
            ) : (
              /* Wizard Application Container */
              <div className="space-y-6">
                {/* Admissions Header Card */}
                <div className="bg-gradient-to-r from-primary to-primary-dark text-white rounded-card p-6 shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <span className="text-xs uppercase font-bold tracking-wider bg-white/20 px-2.5 py-0.5 rounded-full">
                      CBSE Admissions Open
                    </span>
                    <h2 className="text-2xl font-bold mt-2">{cycleData?.cycle.name}</h2>
                    <p className="text-xs text-white/80 mt-1">
                      Academic Year {cycleData?.cycle.academic_year} • Complete 7-Step Online Application
                    </p>
                  </div>
                  <div className="bg-white/10 backdrop-blur rounded-xl px-4 py-2.5 border border-white/20 text-center">
                    <div className="text-[11px] text-white/80 font-medium">Application Processing</div>
                    <div className="text-sm font-bold text-white">Admissions Cell Direct</div>
                  </div>
                </div>

                {/* 7-Step Horizontal Stepper */}
                <div className="bg-surface rounded-card border border-rule p-4 shadow-xs">
                  <div className="grid grid-cols-6 gap-2">
                    {[
                      { step: 1, label: "Student" },
                      { step: 2, label: "Parents" },
                      { step: 3, label: "Academic" },
                      { step: 4, label: "Health" },
                      { step: 5, label: "Documents" },
                      { step: 6, label: "Review" },
                    ].map((s) => (
                      <button
                        key={s.step}
                        type="button"
                        onClick={() => {
                          if (s.step < currentStep) setCurrentStep(s.step);
                        }}
                        disabled={s.step > currentStep}
                        className={`text-center py-2 px-1 rounded-lg transition-all ${
                          currentStep === s.step
                            ? "bg-primary text-white font-bold shadow-xs"
                            : s.step < currentStep
                            ? "bg-emerald-50 text-emerald-800 font-semibold hover:bg-emerald-100"
                            : "text-ink-faint cursor-not-allowed"
                        }`}
                      >
                        <div className="text-xs">
                          {s.step < currentStep ? "✓" : `Step ${s.step}`}
                        </div>
                        <div className="text-[11px] truncate hidden sm:block">{s.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <form onSubmit={handleApplySubmit} className="space-y-6">
                  {/* ------------------------------------------------------------- */}
                  {/* STEP 1: STUDENT PERSONAL DETAILS                              */}
                  {/* ------------------------------------------------------------- */}
                  {currentStep === 1 && (
                    <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-6">
                      <div className="flex items-center justify-between border-b border-rule pb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-7 h-7 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                            1
                          </span>
                          <div>
                            <h3 className="text-base font-bold text-ink">Student Personal Details</h3>
                            <p className="text-xs text-ink-soft">Enter legal name and birth information as per Birth Certificate.</p>
                          </div>
                        </div>
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
                          <label htmlFor="student-dob" className="block text-xs font-semibold text-ink-soft mb-1">
                            Date of Birth <span className="text-danger">*</span>
                          </label>
                          <input
                            id="student-dob"
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
                          <label htmlFor="student-class" className="block text-xs font-semibold text-ink-soft mb-1">
                            Class Applying For <span className="text-danger">*</span>
                          </label>
                          <select
                            id="student-class"
                            required
                            value={selectedClass}
                            onChange={(e) => setSelectedClass(e.target.value)}
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white font-medium"
                          >
                            <option value="">-- Select Class --</option>
                            {cycleData?.classes.map((cls) => (
                              <option key={cls.class_name} value={cls.class_name}>
                                Class {cls.class_name} ({cls.total_seats} seats)
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Stream (if class 11 or 12) */}
                      {(selectedClass === "11" || selectedClass === "12") && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-ground p-4 rounded-xl border border-rule">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Senior Secondary Stream Choice
                            </label>
                            <select
                              value={stream}
                              onChange={(e) => setStream(e.target.value)}
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                            >
                              <option value="">Select Stream</option>
                              <option value="Science (PCM)">Science (PCM - Physics, Chemistry, Maths)</option>
                              <option value="Science (PCB)">Science (PCB - Physics, Chemistry, Biology)</option>
                              <option value="Commerce">Commerce with Mathematics / Applied Maths</option>
                              <option value="Humanities">Humanities / Arts</option>
                            </select>
                          </div>
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">Nationality</label>
                          <input
                            value={nationality}
                            onChange={(e) => setNationality(e.target.value)}
                            placeholder="Indian"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
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
                          <label className="block text-xs font-semibold text-ink-soft mb-1">Place of Birth</label>
                          <input
                            value={placeOfBirth}
                            onChange={(e) => setPlaceOfBirth(e.target.value)}
                            placeholder="City of Birth"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                            <option value="EWS">EWS</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">Admission Quota Category</label>
                          <select
                            value={admissionCategory}
                            onChange={(e) => setAdmissionCategory(e.target.value)}
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                          >
                            <option value="general">General Open Seat</option>
                            <option value="rte">RTE (Right to Education 25%)</option>
                            <option value="sibling">Sibling Enrolled</option>
                            <option value="staff_ward">Staff Ward</option>
                            <option value="management">Management Quota</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Student Aadhaar Card (Last 4 digits)
                          </label>
                          <input
                            maxLength={4}
                            value={aadhaarLast4}
                            onChange={(e) => setAadhaarLast4(e.target.value.replace(/\D/g, ""))}
                            placeholder="e.g. 5678"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Second Language Preference
                          </label>
                          <select
                            value={secondLanguage}
                            onChange={(e) => setSecondLanguage(e.target.value)}
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                          >
                            <option value="Hindi">Hindi</option>
                            <option value="Sanskrit">Sanskrit</option>
                            <option value="French">French</option>
                            <option value="German">German</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Visible Identification Mark (Optional)
                          </label>
                          <input
                            value={identificationMarks}
                            onChange={(e) => setIdentificationMarks(e.target.value)}
                            placeholder="e.g. Small mole on right cheek"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
                      </div>

                      {/* Residential Address */}
                      <div className="border-t border-rule pt-4 space-y-4">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-ink">Residential Address</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="md:col-span-2">
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Street / House Address <span className="text-danger">*</span>
                            </label>
                            <input
                              required
                              value={addressLine}
                              onChange={(e) => setAddressLine(e.target.value)}
                              placeholder="e.g. Flat 402, Shalimar Gallant, Sector 4, Gomti Nagar"
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
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              PIN Code <span className="text-danger">*</span>
                            </label>
                            <input
                              required
                              maxLength={6}
                              value={pinCode}
                              onChange={(e) => setPinCode(e.target.value)}
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Checkbox Options */}
                      <div className="border-t border-rule pt-3 space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={transportRequired}
                            onChange={(e) => setTransportRequired(e.target.checked)}
                            className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                          />
                          <span className="text-xs font-medium text-ink">
                            School Bus / GPS-enabled Transport Facility Required
                          </span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={isSingleChild}
                            onChange={(e) => setIsSingleChild(e.target.checked)}
                            className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                          />
                          <span className="text-xs font-medium text-ink">
                            Single Child (Eligible for Single Girl Child / Single Child Category)
                          </span>
                        </label>
                      </div>

                      {/* Photo Upload */}
                      <div className="border-t border-rule pt-4">
                        <UniversalUploadField
                          label="Student Recent Passport Photograph"
                          value={studentPhotoUrl}
                          onChange={(url) => setStudentPhotoUrl(url)}
                          schoolCode={schoolCode}
                          helperText="White background passport size photo of the student. Required for ID card."
                        />
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STEP 2: PARENT & GUARDIAN DETAILS                             */}
                  {/* ------------------------------------------------------------- */}
                  {currentStep === 2 && (
                    <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-6">
                      <div className="flex items-center justify-between border-b border-rule pb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-7 h-7 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                            2
                          </span>
                          <div>
                            <h3 className="text-base font-bold text-ink">Parent & Guardian Details</h3>
                            <p className="text-xs text-ink-soft">Declare primary parents and authorized gate escorts.</p>
                          </div>
                        </div>
                        <span className="text-xs bg-primary/10 text-primary font-semibold px-2 py-0.5 rounded">
                          Primary Contact
                        </span>
                      </div>

                      {/* Primary Guardian */}
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Relationship</label>
                            <select
                              value={guardianRelation}
                              onChange={(e) => setGuardianRelation(e.target.value as any)}
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
                              placeholder="9876543210"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Qualification</label>
                            <input
                              value={guardianQualification}
                              onChange={(e) => setGuardianQualification(e.target.value)}
                              placeholder="e.g. B.Tech, M.Sc, MBA"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Annual Income Band</label>
                            <select
                              value={guardianIncomeBand}
                              onChange={(e) => setGuardianIncomeBand(e.target.value)}
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                            >
                              <option value="Below 5 LPA">Below ₹5 Lakhs / annum</option>
                              <option value="5-10 LPA">₹5 Lakhs – ₹10 Lakhs / annum</option>
                              <option value="10-20 LPA">₹10 Lakhs – ₹20 Lakhs / annum</option>
                              <option value="20-50 LPA">₹20 Lakhs – ₹50 Lakhs / annum</option>
                              <option value="Above 50 LPA">Above ₹50 Lakhs / annum</option>
                            </select>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Occupation</label>
                            <input
                              value={guardianOccupation}
                              onChange={(e) => setGuardianOccupation(e.target.value)}
                              placeholder="e.g. Software Engineer, Doctor, Advocate"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Designation</label>
                            <input
                              value={guardianDesignation}
                              onChange={(e) => setGuardianDesignation(e.target.value)}
                              placeholder="e.g. Senior Director, Manager"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Organisation / Company</label>
                            <input
                              value={guardianOrganisation}
                              onChange={(e) => setGuardianOrganisation(e.target.value)}
                              placeholder="e.g. Infosys, TCS, AIIMS"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Office Address</label>
                            <input
                              value={guardianOfficeAddress}
                              onChange={(e) => setGuardianOfficeAddress(e.target.value)}
                              placeholder="Office locality, Lucknow"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Alternate Phone</label>
                            <input
                              maxLength={10}
                              value={guardianAltMobile}
                              onChange={(e) => setGuardianAltMobile(e.target.value.replace(/\D/g, ""))}
                              placeholder="Alternate contact number"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                            />
                          </div>
                        </div>

                        <UniversalUploadField
                          label="Primary Parent Photograph (Required for Gate Pickup ID)"
                          value={guardianPhotoUrl}
                          onChange={(url) => setGuardianPhotoUrl(url)}
                          schoolCode={schoolCode}
                          helperText="Official photograph matched by campus security gate guards for student release."
                        />
                      </div>

                      {/* Secondary Guardian Toggle */}
                      <div className="border-t border-rule pt-4">
                        {!hasSecondGuardian ? (
                          <button
                            type="button"
                            onClick={() => setHasSecondGuardian(true)}
                            className="text-xs font-semibold text-primary hover:underline flex items-center gap-1.5 py-1"
                          >
                            <span>+</span> Add Second Parent / Co-Guardian Details
                          </button>
                        ) : (
                          <div className="border border-rule rounded-xl p-4 bg-ground/30 space-y-4">
                            <div className="flex items-center justify-between">
                              <h4 className="text-xs font-bold uppercase tracking-wider text-ink">
                                Second Parent / Co-Guardian
                              </h4>
                              <button
                                type="button"
                                onClick={() => setHasSecondGuardian(false)}
                                className="text-xs text-danger font-semibold hover:underline"
                              >
                                Remove Co-Guardian
                              </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">Relationship</label>
                                <select
                                  value={secRelation}
                                  onChange={(e) => setSecRelation(e.target.value as any)}
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                >
                                  <option value="mother">Mother</option>
                                  <option value="father">Father</option>
                                  <option value="other">Guardian</option>
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">Full Name</label>
                                <input
                                  value={secName}
                                  onChange={(e) => setSecName(e.target.value)}
                                  placeholder="e.g. Sunita Sharma"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">Mobile Number</label>
                                <input
                                  maxLength={10}
                                  value={secMobile}
                                  onChange={(e) => setSecMobile(e.target.value.replace(/\D/g, ""))}
                                  placeholder="10-digit mobile"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary bg-white"
                                />
                              </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">Occupation</label>
                                <input
                                  value={secOccupation}
                                  onChange={(e) => setSecOccupation(e.target.value)}
                                  placeholder="e.g. Professor, Homemaker, Architect"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-ink-soft mb-1">Email Address</label>
                                <input
                                  type="email"
                                  value={secEmail}
                                  onChange={(e) => setSecEmail(e.target.value)}
                                  placeholder="second.parent@example.com"
                                  className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                />
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Authorized Pickup Persons (Escort Pass) */}
                      <div className="border-t border-rule pt-4 space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-ink">
                              Authorized Gate Pickup Persons (Escort Authorizations)
                            </h4>
                            <p className="text-[11px] text-ink-soft mt-0.5">
                              Authorize grandparents, trusted family relatives, or drivers to collect your child from the school gate.
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={addAuthorizedPerson}
                            className="px-3 py-1.5 text-xs font-semibold text-primary border border-primary/30 hover:bg-primary/5 rounded-lg transition"
                          >
                            + Add Escort Person
                          </button>
                        </div>

                        {authorizedPersons.length === 0 ? (
                          <div className="text-center py-4 bg-ground rounded-lg border border-dashed border-rule text-xs text-ink-soft">
                            Parents listed above are automatically authorized. Click "+ Add Escort Person" if a grandparent or driver will collect the student.
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {authorizedPersons.map((p, idx) => (
                              <div key={p.id} className="p-4 border border-rule rounded-xl bg-ground/40 space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-bold text-ink uppercase">
                                    Authorized Person #{idx + 1}
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => removeAuthorizedPerson(p.id)}
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
                                      value={p.name}
                                      onChange={(e) => updateAuthorizedPerson(p.id, "name", e.target.value)}
                                      placeholder="e.g. Ramesh Kumar"
                                      className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-xs font-semibold text-ink-soft mb-1">
                                      Relationship <span className="text-danger">*</span>
                                    </label>
                                    <input
                                      required
                                      value={p.relationship}
                                      onChange={(e) => updateAuthorizedPerson(p.id, "relationship", e.target.value)}
                                      placeholder="e.g. Grandfather, Driver"
                                      className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-xs font-semibold text-ink-soft mb-1">
                                      Phone Number (10 digits) <span className="text-danger">*</span>
                                    </label>
                                    <input
                                      required
                                      maxLength={10}
                                      value={p.phone}
                                      onChange={(e) => updateAuthorizedPerson(p.id, "phone", e.target.value.replace(/\D/g, ""))}
                                      placeholder="9876543210"
                                      className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary bg-white"
                                    />
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STEP 3: ACADEMIC HISTORY & PREVIOUS SCHOOL                    */}
                  {/* ------------------------------------------------------------- */}
                  {currentStep === 3 && (
                    <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-6">
                      <div className="flex items-center gap-2 border-b border-rule pb-3">
                        <span className="w-7 h-7 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                          3
                        </span>
                        <div>
                          <h3 className="text-base font-bold text-ink">Academic History & Previous School</h3>
                          <p className="text-xs text-ink-soft">
                            Applicable for students transferring from another school. Leave blank if applying for Nursery.
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="md:col-span-2">
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Previous School Name
                          </label>
                          <input
                            value={prevSchoolName}
                            onChange={(e) => setPrevSchoolName(e.target.value)}
                            placeholder="e.g. St. Francis College, Delhi Public School, Lucknow"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Affiliation Board
                          </label>
                          <select
                            value={prevBoard}
                            onChange={(e) => setPrevBoard(e.target.value)}
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                          >
                            <option value="CBSE">CBSE</option>
                            <option value="ICSE / ISC">ICSE / ISC</option>
                            <option value="UP Board">UP State Board</option>
                            <option value="IB / Cambridge">IB / Cambridge</option>
                            <option value="Other">Other Recognized Board</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Last Class Passed / Attended
                          </label>
                          <input
                            value={prevLastClass}
                            onChange={(e) => setPrevLastClass(e.target.value)}
                            placeholder="e.g. UKG, Class 3"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Percentage / Grade Obtained
                          </label>
                          <input
                            value={prevPercentage}
                            onChange={(e) => setPrevPercentage(e.target.value)}
                            placeholder="e.g. 91.5% or A1"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-ink-soft mb-1">
                            Transfer Certificate (TC) Number (If issued)
                          </label>
                          <input
                            value={prevTcNo}
                            onChange={(e) => setPrevTcNo(e.target.value)}
                            placeholder="e.g. TC/2026/042"
                            className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STEP 4: HEALTH RECORD & SIBLINGS                              */}
                  {/* ------------------------------------------------------------- */}
                  {currentStep === 4 && (
                    <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-6">
                      <div className="flex items-center gap-2 border-b border-rule pb-3">
                        <span className="w-7 h-7 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                          4
                        </span>
                        <div>
                          <h3 className="text-base font-bold text-ink">Medical Information & Siblings</h3>
                          <p className="text-xs text-ink-soft">
                            Confidential health profile for school clinic and emergency protocols.
                          </p>
                        </div>
                      </div>

                      {/* Sibling Record */}
                      <div className="border border-rule rounded-xl p-4 bg-ground/30 space-y-3">
                        <label className="flex items-center gap-2 cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={hasSibling}
                            onChange={(e) => setHasSibling(e.target.checked)}
                            className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                          />
                          <span className="text-xs font-bold text-ink">
                            Does the student have a brother or sister currently studying at Sunrise School?
                          </span>
                        </label>

                        {hasSibling && (
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                            <div>
                              <label className="block text-xs font-semibold text-ink-soft mb-1">Sibling Full Name</label>
                              <input
                                value={siblingName}
                                onChange={(e) => setSiblingName(e.target.value)}
                                placeholder="e.g. Ananya Sharma"
                                className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-ink-soft mb-1">Sibling Age</label>
                              <input
                                type="number"
                                value={siblingAge}
                                onChange={(e) => setSiblingAge(e.target.value)}
                                placeholder="e.g. 9"
                                className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-semibold text-ink-soft mb-1">Current Class / Student ID</label>
                              <input
                                value={siblingClassId}
                                onChange={(e) => setSiblingClassId(e.target.value)}
                                placeholder="e.g. Class 4-B or SPS-2022-019"
                                className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white"
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Medical & Health Info */}
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">Blood Group</label>
                            <select
                              value={bloodGroup}
                              onChange={(e) => setBloodGroup(e.target.value)}
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary bg-white font-semibold"
                            >
                              <option value="A+">A Positive (A+)</option>
                              <option value="A-">A Negative (A-)</option>
                              <option value="B+">B Positive (B+)</option>
                              <option value="B-">B Negative (B-)</option>
                              <option value="O+">O Positive (O+)</option>
                              <option value="O-">O Negative (O-)</option>
                              <option value="AB+">AB Positive (AB+)</option>
                              <option value="AB-">AB Negative (AB-)</option>
                              <option value="Unknown">Not Known Yet</option>
                            </select>
                          </div>
                          <div className="md:col-span-2">
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Known Allergies (Food, Medicines, Dust, etc.)
                            </label>
                            <input
                              value={knownAllergies}
                              onChange={(e) => setKnownAllergies(e.target.value)}
                              placeholder="e.g. Peanuts, Penicillin, Dust allergy (or None)"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Chronic Health Conditions / Medical History
                            </label>
                            <input
                              value={chronicConditions}
                              onChange={(e) => setChronicConditions(e.target.value)}
                              placeholder="e.g. Asthma, Childhood seizures (or None)"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Regular Prescription Medications
                            </label>
                            <input
                              value={regularMedication}
                              onChange={(e) => setRegularMedication(e.target.value)}
                              placeholder="Medication name and dosage (or None)"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Family Physician / Emergency Doctor Name
                            </label>
                            <input
                              value={emergencyDoctor}
                              onChange={(e) => setEmergencyDoctor(e.target.value)}
                              placeholder="e.g. Dr. V. K. Mishra"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm outline-none focus:border-primary"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-ink-soft mb-1">
                              Emergency Doctor Phone Number
                            </label>
                            <input
                              maxLength={10}
                              value={emergencyDoctorPhone}
                              onChange={(e) => setEmergencyDoctorPhone(e.target.value.replace(/\D/g, ""))}
                              placeholder="e.g. 9415000000"
                              className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                            />
                          </div>
                        </div>

                        <div className="pt-2">
                          <label className="flex items-center gap-2 cursor-pointer select-none">
                            <input
                              type="checkbox"
                              checked={consentEmergencyTreatment}
                              onChange={(e) => setConsentEmergencyTreatment(e.target.checked)}
                              className="rounded border-rule text-primary focus:ring-primary h-4 w-4"
                            />
                            <span className="text-xs text-ink font-medium">
                              I authorize Sunrise Public School to administer first aid and arrange emergency hospital medical treatment if required.
                            </span>
                          </label>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STEP 5: DOCUMENT UPLOADS                                      */}
                  {/* ------------------------------------------------------------- */}
                  {currentStep === 5 && (
                    <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-6">
                      <div className="flex items-center gap-2 border-b border-rule pb-3">
                        <span className="w-7 h-7 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                          5
                        </span>
                        <div>
                          <h3 className="text-base font-bold text-ink">Document Uploads</h3>
                          <p className="text-xs text-ink-soft">
                            Upload clear scans or photographs of required documents (PDF, JPG, PNG up to 10MB).
                          </p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <UniversalUploadField
                          label="1. Student's Official Birth Certificate"
                          required
                          acceptPdf
                          value={uploadedDocs["birth_certificate"]?.url || null}
                          filename={uploadedDocs["birth_certificate"]?.filename}
                          onChange={(url, fname, size) => handleDocChange("birth_certificate", url, fname, size)}
                          schoolCode={schoolCode}
                          helperText="Issued by Municipal Corporation / Registrar of Births. Mandatory for age verification."
                        />

                        <UniversalUploadField
                          label="2. Residential Address Proof"
                          required
                          acceptPdf
                          value={uploadedDocs["address_proof"]?.url || null}
                          filename={uploadedDocs["address_proof"]?.filename}
                          onChange={(url, fname, size) => handleDocChange("address_proof", url, fname, size)}
                          schoolCode={schoolCode}
                          helperText="Electricity Bill, Water Bill, Passport, or Guardian Aadhaar Card showing Lucknow address."
                        />

                        <UniversalUploadField
                          label="3. Previous School Marksheet / Report Card"
                          acceptPdf
                          value={uploadedDocs["previous_report_card"]?.url || null}
                          filename={uploadedDocs["previous_report_card"]?.filename}
                          onChange={(url, fname, size) => handleDocChange("previous_report_card", url, fname, size)}
                          schoolCode={schoolCode}
                          helperText="Last annual report card from previous school (Optional for Nursery)."
                        />

                        <UniversalUploadField
                          label="4. Parent / Guardian Identity Proof"
                          acceptPdf
                          value={uploadedDocs["parent_id_proof"]?.url || null}
                          filename={uploadedDocs["parent_id_proof"]?.filename}
                          onChange={(url, fname, size) => handleDocChange("parent_id_proof", url, fname, size)}
                          schoolCode={schoolCode}
                          helperText="Aadhaar Card, Passport, Voter ID, or Driving License of father or mother."
                        />
                      </div>
                    </div>
                  )}

                  {/* ------------------------------------------------------------- */}
                  {/* STEP 6: REVIEW & MANDATORY DECLARATIONS                       */}
                  {/* ------------------------------------------------------------- */}
                  {currentStep === 6 && (
                    <div className="space-y-6">
                      {/* Review Summary Card */}
                      <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-6">
                        <div className="flex items-center justify-between border-b border-rule pb-3">
                          <div className="flex items-center gap-2">
                            <span className="w-7 h-7 rounded-full bg-primary text-white text-xs flex items-center justify-center font-bold">
                              6
                            </span>
                            <div>
                              <h3 className="text-base font-bold text-ink">Review Application Summary</h3>
                              <p className="text-xs text-ink-soft">Review entered data before final submission.</p>
                            </div>
                          </div>
                          <span className="text-xs bg-amber-100 text-amber-900 font-semibold px-2.5 py-1 rounded-full">
                            Draft Review
                          </span>
                        </div>

                        {/* Summary Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                          <div className="bg-ground p-4 rounded-xl border border-rule space-y-2">
                            <div className="flex justify-between items-center border-b border-rule pb-1.5">
                              <span className="font-bold text-ink uppercase tracking-wider text-[11px]">
                                Student Details
                              </span>
                              <button
                                type="button"
                                onClick={() => setCurrentStep(1)}
                                className="text-primary hover:underline font-semibold"
                              >
                                Edit
                              </button>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Full Name:</span>
                              <span className="font-semibold text-ink">{`${firstName} ${middleName} ${lastName}`.trim()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Class Applying:</span>
                              <span className="font-semibold text-primary">Class {selectedClass}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Date of Birth:</span>
                              <span className="font-medium text-ink">{dob || "—"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Gender:</span>
                              <span className="capitalize text-ink">{gender}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Transport Needed:</span>
                              <span className="text-ink">{transportRequired ? "Yes (School Bus)" : "No (Self)"}</span>
                            </div>
                          </div>

                          <div className="bg-ground p-4 rounded-xl border border-rule space-y-2">
                            <div className="flex justify-between items-center border-b border-rule pb-1.5">
                              <span className="font-bold text-ink uppercase tracking-wider text-[11px]">
                                Parent / Guardian
                              </span>
                              <button
                                type="button"
                                onClick={() => setCurrentStep(2)}
                                className="text-primary hover:underline font-semibold"
                              >
                                Edit
                              </button>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Primary Contact:</span>
                              <span className="font-semibold text-ink">{guardianName}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Mobile Number:</span>
                              <span className="font-mono text-ink font-semibold">{guardianMobile}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Email:</span>
                              <span className="text-ink truncate max-w-[160px]">{guardianEmail || "—"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Occupation:</span>
                              <span className="text-ink">{guardianOccupation || "—"}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Escort Persons:</span>
                              <span className="text-ink">{authorizedPersons.length} added</span>
                            </div>
                          </div>

                          <div className="bg-ground p-4 rounded-xl border border-rule space-y-2">
                            <div className="flex justify-between items-center border-b border-rule pb-1.5">
                              <span className="font-bold text-ink uppercase tracking-wider text-[11px]">
                                Address & Academic
                              </span>
                              <button
                                type="button"
                                onClick={() => setCurrentStep(1)}
                                className="text-primary hover:underline font-semibold"
                              >
                                Edit
                              </button>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Address:</span>
                              <span className="text-ink truncate max-w-[180px]">{addressLine}, {city}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">PIN Code:</span>
                              <span className="font-mono text-ink">{pinCode}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Previous School:</span>
                              <span className="text-ink truncate max-w-[180px]">{prevSchoolName || "First Admission"}</span>
                            </div>
                          </div>

                          <div className="bg-ground p-4 rounded-xl border border-rule space-y-2">
                            <div className="flex justify-between items-center border-b border-rule pb-1.5">
                              <span className="font-bold text-ink uppercase tracking-wider text-[11px]">
                                Documents & Medical
                              </span>
                              <button
                                type="button"
                                onClick={() => setCurrentStep(5)}
                                className="text-primary hover:underline font-semibold"
                              >
                                Edit
                              </button>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Birth Certificate:</span>
                              <span className={uploadedDocs["birth_certificate"] ? "text-emerald-600 font-semibold" : "text-danger"}>
                                {uploadedDocs["birth_certificate"] ? "✓ Uploaded" : "Missing"}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Address Proof:</span>
                              <span className={uploadedDocs["address_proof"] ? "text-emerald-600 font-semibold" : "text-danger"}>
                                {uploadedDocs["address_proof"] ? "✓ Uploaded" : "Missing"}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-ink-soft">Blood Group:</span>
                              <span className="font-bold text-ink">{bloodGroup}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Mandatory Declarations (Explicit & Never Pre-ticked) */}
                      <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-sm space-y-4">
                        <div className="border-b border-rule pb-3">
                          <h3 className="text-base font-bold text-ink">Declarations & Consent (Mandatory)</h3>
                          <p className="text-xs text-ink-soft">
                            Please read carefully and accept each declaration to complete application submission.
                          </p>
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
                              best of my knowledge. I understand that any false statement or concealed information
                              may result in immediate cancellation of admission.
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
                              to abide by the CBSE code of conduct, fee payment timelines, attendance norms, and
                              disciplinary policies of Sunrise Public School.
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
                              the school administration to process, verify, and store our submitted personal data
                              and identity documents for official enrollment and educational administrative purposes.
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
                              features highlighting academic or co-curricular achievements.
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
                    </div>
                  )}

                  {/* Submission Error Banner */}
                  {submitError && (
                    <div className="bg-red-50 border border-red-200 text-danger text-sm rounded-xl p-4 font-medium flex items-center gap-2">
                      <span>⚠️</span>
                      <span>{submitError}</span>
                    </div>
                  )}

                  {/* Wizard Step Navigation Footer */}
                  <div className="flex items-center justify-between pt-2">
                    {currentStep > 1 ? (
                      <button
                        type="button"
                        onClick={handlePrevStep}
                        className="px-5 py-2.5 bg-surface border border-rule hover:bg-ground text-ink text-sm font-semibold rounded-input transition"
                      >
                        &larr; Back
                      </button>
                    ) : <div />}

                    {currentStep < 6 ? (
                      <button
                        type="button"
                        onClick={handleNextStep}
                        className="px-6 py-2.5 bg-primary hover:bg-primary-dark text-white text-sm font-bold rounded-input shadow-md transition flex items-center gap-2"
                      >
                        Continue &rarr;
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={submitting}
                        className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-input shadow-md transition-all disabled:opacity-50 flex items-center gap-2"
                      >
                        {submitting ? (
                          <>
                            <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                            <span>Submitting Application...</span>
                          </>
                        ) : (
                          <>
                            <span>✓</span>
                            <span>Submit Admission Application</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

        {/* ============================================================= */}
        {/* TAB 2: APPLICATION STATUS LOOKUP, PAYMENT & DOCUMENTS         */}
        {/* ============================================================= */}
        {activeTab === "status" && (
          <div className="space-y-6">
            <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-card max-w-xl mx-auto space-y-6">
              <div>
                <h2 className="text-xl font-bold text-ink">Check Application & Admission Status</h2>
                <p className="text-xs text-ink-soft mt-1">
                  Enter your Application Reference Number and registered Guardian Mobile Number to track progress,
                  pay admission fees, and download official admission records.
                </p>
              </div>

              <form onSubmit={handleStatusCheck} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Application Reference Number <span className="text-danger">*</span>
                  </label>
                  <input
                    required
                    value={searchAppNo}
                    onChange={(e) => setSearchAppNo(e.target.value.toUpperCase())}
                    placeholder="e.g. APP-2026-0001"
                    className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono font-bold outline-none focus:border-primary tracking-wide"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-soft mb-1">
                    Registered Guardian Mobile Number <span className="text-danger">*</span>
                  </label>
                  <input
                    maxLength={10}
                    value={searchMobile}
                    onChange={(e) => setSearchMobile(e.target.value.replace(/\D/g, ""))}
                    placeholder="10-digit mobile number entered on form"
                    className="w-full rounded-input border border-rule px-3 py-2 text-sm font-mono outline-none focus:border-primary"
                  />
                  <p className="text-[11px] text-ink-faint mt-1">
                    For privacy protection, status lookup requires matching the registered mobile number.
                  </p>
                </div>

                <div className="pt-1">
                  <details className="text-xs text-ink-faint">
                    <summary className="cursor-pointer hover:text-ink font-medium">
                      Or search using student's Date of Birth (legacy)
                    </summary>
                    <div className="pt-2">
                      <input
                        type="date"
                        value={searchDob}
                        onChange={(e) => setSearchDob(e.target.value)}
                        className="w-full rounded-input border border-rule px-3 py-2 text-xs outline-none focus:border-primary"
                      />
                    </div>
                  </details>
                </div>

                {statusError && (
                  <div className="bg-red-50 border border-red-200 text-danger text-xs rounded-lg p-3 font-medium flex items-center gap-2">
                    <span>⚠️</span>
                    <span>{statusError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={statusLoading}
                  className="w-full py-3 bg-primary hover:bg-primary-dark text-white font-bold text-sm rounded-input shadow transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {statusLoading ? (
                    <>
                      <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                      <span>Checking Status...</span>
                    </>
                  ) : (
                    <>
                      <span>🔍</span>
                      <span>Track Application Status</span>
                    </>
                  )}
                </button>
              </form>

              {/* Status Result Display */}
              {statusResult && (
                <div className="mt-8 border-t border-rule pt-6 space-y-6">
                  {/* Status Header */}
                  <div className="flex items-center justify-between bg-ground p-4 rounded-xl border border-rule">
                    <div>
                      <span className="text-[11px] text-ink-faint uppercase font-bold tracking-wider">
                        Application Ref
                      </span>
                      <div className="text-lg font-mono font-bold text-ink">
                        {statusResult.application_no}
                      </div>
                    </div>
                    <span
                      className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider ${
                        statusResult.stage === "enrolled"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : statusResult.stage === "offer_issued"
                          ? "bg-purple-100 text-purple-900 border border-purple-300 animate-pulse"
                          : statusResult.stage === "rejected"
                          ? "bg-red-100 text-red-800 border border-red-300"
                          : "bg-blue-100 text-blue-800 border border-blue-300"
                      }`}
                    >
                      {statusResult.stage.replace(/_/g, " ")}
                    </span>
                  </div>

                  {/* 4-Stage Visual Journey Timeline */}
                  <div className="bg-surface p-4 rounded-xl border border-rule space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-ink">
                      Admission Progress Journey
                    </h4>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      {[
                        {
                          key: "submitted",
                          title: "Submitted",
                          desc: "Registered",
                          isDone: true,
                          isCurrent: statusResult.stage === "submitted",
                        },
                        {
                          key: "under_review",
                          title: "Review",
                          desc: "Verification",
                          isDone: ["under_review", "offer_issued", "enrolled"].includes(statusResult.stage),
                          isCurrent: statusResult.stage === "under_review",
                        },
                        {
                          key: "offer_issued",
                          title: "Offer & Fee",
                          desc: "Payment",
                          isDone: ["offer_issued", "enrolled"].includes(statusResult.stage),
                          isCurrent: statusResult.stage === "offer_issued",
                        },
                        {
                          key: "enrolled",
                          title: "Enrolled",
                          desc: "Confirmed",
                          isDone: statusResult.stage === "enrolled",
                          isCurrent: statusResult.stage === "enrolled",
                        },
                      ].map((step, idx) => (
                        <div
                          key={step.key}
                          className={`p-2.5 rounded-lg border text-xs transition-all ${
                            step.isCurrent
                              ? "bg-primary/10 border-primary text-primary font-bold shadow-xs"
                              : step.isDone
                              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                              : "bg-ground/50 border-rule text-ink-faint"
                          }`}
                        >
                          <div className="text-xs font-bold">
                            {step.isDone ? "✓" : idx + 1}
                          </div>
                          <div className="font-semibold mt-1">{step.title}</div>
                          <div className="text-[10px] text-ink-faint">{step.desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Applicant Details Card */}
                  <div className="grid grid-cols-2 gap-3 text-xs bg-ground p-4 rounded-xl border border-rule">
                    <div>
                      <span className="text-ink-soft">Applicant Student</span>
                      <p className="font-bold text-ink text-sm mt-0.5">{statusResult.name}</p>
                    </div>
                    <div>
                      <span className="text-ink-soft">Class Applied</span>
                      <p className="font-semibold text-ink text-sm mt-0.5">Class {statusResult.class_applying_for}</p>
                    </div>
                    <div className="col-span-2 pt-2 border-t border-rule flex justify-between">
                      <span className="text-ink-soft">Submission Date:</span>
                      <span className="font-medium text-ink">
                        {new Date(statusResult.submitted_at).toLocaleDateString("en-IN", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })}
                      </span>
                    </div>
                  </div>

                  {/* ----------------------------------------------------------- */}
                  {/* PROVISIONAL ADMISSION OFFER & FEE PAYMENT CARD              */}
                  {/* ----------------------------------------------------------- */}
                  {statusResult.stage === "offer_issued" && statusResult.is_payable && (
                    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-purple-300 rounded-2xl p-6 space-y-4 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-purple-700 bg-purple-100 px-3 py-1 rounded-full">
                          🎉 Provisional Offer Issued
                        </span>
                        {statusResult.offer?.expires_on && (
                          <span className="text-xs font-medium text-purple-900">
                            Offer Valid Till: <strong>{statusResult.offer.expires_on}</strong>
                          </span>
                        )}
                      </div>

                      <div>
                        <h3 className="text-lg font-bold text-purple-950">
                          Congratulations! Admission Offer Granted
                        </h3>
                        <p className="text-xs text-purple-900/80 mt-1 leading-relaxed">
                          The Admissions Committee has approved admission for{" "}
                          <strong>{statusResult.name}</strong> to Class{" "}
                          <strong>{statusResult.offer?.class_name || statusResult.class_applying_for}</strong>.
                          Please complete the admission fee payment online to confirm and finalize enrollment.
                        </p>
                      </div>

                      <div className="bg-white rounded-xl p-4 border border-purple-200 flex items-center justify-between">
                        <div>
                          <div className="text-xs text-ink-soft font-medium">Total Admission Fee Payable</div>
                          <div className="text-2xl font-bold text-primary font-mono mt-0.5">
                            ₹{parseFloat(statusResult.payable_amount || "0").toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </div>
                          <div className="text-[11px] text-ink-faint mt-0.5">
                            Includes Composite Annual Fee & Enrollment Charges
                          </div>
                        </div>
                        <button
                          onClick={handleInitiatePayment}
                          disabled={paymentInitiating}
                          className="px-6 py-3 bg-primary hover:bg-primary-dark text-white font-bold text-sm rounded-input shadow-md transition-all flex items-center gap-2"
                        >
                          {paymentInitiating ? (
                            <>
                              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                              <span>Connecting Gateway...</span>
                            </>
                          ) : (
                            <>
                              <span>💳</span>
                              <span>Pay Admission Fee Online</span>
                            </>
                          )}
                        </button>
                      </div>

                      {paymentError && (
                        <div className="bg-red-50 border border-red-200 text-danger text-xs rounded-lg p-3 font-medium">
                          {paymentError}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ----------------------------------------------------------- */}
                  {/* ENROLLED CONFIRMATION, ERP CREDENTIALS & DOCUMENTS HUB      */}
                  {/* ----------------------------------------------------------- */}
                  {statusResult.stage === "enrolled" && (
                    <div className="space-y-6">
                      {/* Celebratory Banner */}
                      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white rounded-2xl p-6 shadow-md space-y-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center text-2xl font-bold">
                            🎓
                          </div>
                          <div>
                            <span className="text-[11px] font-bold uppercase tracking-wider bg-white/20 px-2.5 py-0.5 rounded-full">
                              Formally Enrolled & Confirmed
                            </span>
                            <h3 className="text-xl font-bold mt-1">
                              Welcome to Sunrise Public School!
                            </h3>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 text-xs">
                          <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                            <span className="text-white/70 block">Permanent Admission No</span>
                            <span className="font-mono font-bold text-sm text-white">
                              {statusResult.student?.admission_no || "Confirmed"}
                            </span>
                          </div>
                          <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                            <span className="text-white/70 block">Assigned Section</span>
                            <span className="font-bold text-sm text-white">
                              {statusResult.student?.class_label || `Class ${statusResult.class_applying_for}`}
                            </span>
                          </div>
                          <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                            <span className="text-white/70 block">Roll Number</span>
                            <span className="font-mono font-bold text-sm text-white">
                              {statusResult.student?.roll_no ?? "Allocated"}
                            </span>
                          </div>
                          <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                            <span className="text-white/70 block">Fee Receipt No</span>
                            <span className="font-mono font-bold text-sm text-white">
                              {statusResult.receipt?.receipt_no || "Issued"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Student ERP Login Credentials Card */}
                      <div className="bg-surface rounded-xl border border-rule p-5 space-y-3 shadow-xs">
                        <div className="flex items-center justify-between border-b border-rule pb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-primary text-base">🔑</span>
                            <h4 className="text-sm font-bold text-ink">Student ERP Portal Access</h4>
                          </div>
                          <span className="text-[11px] bg-primary/10 text-primary font-semibold px-2 py-0.5 rounded">
                            Active
                          </span>
                        </div>
                        <p className="text-xs text-ink-soft">
                          Your student account has been provisioned on the Sunrise ERP system. You can sign in to view class timetables, fee receipts, and digital report cards.
                        </p>
                        <div className="grid grid-cols-2 gap-3 text-xs bg-ground p-3 rounded-lg border border-rule font-mono">
                          <div>
                            <span className="text-ink-soft text-[10px] uppercase block font-sans">Student User ID</span>
                            <span className="font-bold text-ink text-sm select-all">
                              {statusResult.student?.admission_no}
                            </span>
                          </div>
                          <div>
                            <span className="text-ink-soft text-[10px] uppercase block font-sans">Initial Password</span>
                            <span className="font-bold text-primary text-sm select-all">
                              Student@123
                            </span>
                          </div>
                        </div>
                        <div className="pt-1 flex items-center justify-between">
                          <span className="text-[11px] text-ink-faint">
                            * Please change your password upon first login.
                          </span>
                          <Link
                            to="/login"
                            className="px-4 py-1.5 bg-primary hover:bg-primary-dark text-white text-xs font-semibold rounded-lg shadow-xs transition"
                          >
                            Sign In to Student Portal &rarr;
                          </Link>
                        </div>
                      </div>

                      {/* Official Documents Center */}
                      {statusResult.documents_available && (
                        <div className="bg-surface rounded-xl border border-rule p-5 space-y-4 shadow-xs">
                          <div className="border-b border-rule pb-2 flex items-center justify-between">
                            <div>
                              <h4 className="text-sm font-bold text-ink">Official Admission Documents</h4>
                              <p className="text-[11px] text-ink-soft">
                                Officially signed documents available for immediate download or printing.
                              </p>
                            </div>
                            <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2.5 py-0.5 rounded-full">
                              Verified & Gated
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <button
                              type="button"
                              onClick={() => handleOpenDocModal("dossier")}
                              className="p-3 text-left bg-ground hover:bg-primary/5 rounded-xl border border-rule hover:border-primary/40 transition group"
                            >
                              <div className="text-xl mb-1 group-hover:scale-110 transition-transform">📋</div>
                              <div className="text-xs font-bold text-ink group-hover:text-primary">
                                Application Dossier
                              </div>
                              <div className="text-[11px] text-ink-soft mt-0.5">
                                Complete CBSE admission record with student and guardian profiles.
                              </div>
                              <div className="text-[11px] text-primary font-semibold mt-2 flex items-center gap-1">
                                <span>Preview / Print &rarr;</span>
                              </div>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleOpenDocModal("admission_letter")}
                              className="p-3 text-left bg-ground hover:bg-primary/5 rounded-xl border border-rule hover:border-primary/40 transition group"
                            >
                              <div className="text-xl mb-1 group-hover:scale-110 transition-transform">📜</div>
                              <div className="text-xs font-bold text-ink group-hover:text-primary">
                                Provisional Admission Letter
                              </div>
                              <div className="text-[11px] text-ink-soft mt-0.5">
                                Official letterhead signed by Principal confirming admission.
                              </div>
                              <div className="text-[11px] text-primary font-semibold mt-2 flex items-center gap-1">
                                <span>Preview / Print &rarr;</span>
                              </div>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleOpenDocModal("receipt")}
                              className="p-3 text-left bg-ground hover:bg-primary/5 rounded-xl border border-rule hover:border-primary/40 transition group"
                            >
                              <div className="text-xl mb-1 group-hover:scale-110 transition-transform">🧾</div>
                              <div className="text-xs font-bold text-ink group-hover:text-primary">
                                Fee Payment Receipt Voucher
                              </div>
                              <div className="text-[11px] text-ink-soft mt-0.5">
                                Formal fee voucher with receipt number and amount breakdown.
                              </div>
                              <div className="text-[11px] text-primary font-semibold mt-2 flex items-center gap-1">
                                <span>Preview / Print &rarr;</span>
                              </div>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* TAB 3: SEAT MATRIX & ELIGIBILITY CRITERIA                     */}
        {/* ============================================================= */}
        {activeTab === "info" && (
          <div className="space-y-6">
            <div className="bg-surface rounded-card border border-rule p-6 md:p-8 shadow-card space-y-6">
              <div>
                <h2 className="text-xl font-bold text-ink">Class Seat Matrix & Eligibility Norms</h2>
                <p className="text-xs text-ink-soft mt-1">
                  CBSE Affiliation No: 2132849 • School Code: 70892 • Session {cycleData?.cycle.academic_year || "2025–26"}
                </p>
              </div>

              {cycleData?.classes && cycleData.classes.length > 0 ? (
                <div className="overflow-x-auto border border-rule rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-ground border-b border-rule font-semibold text-ink-soft">
                      <tr>
                        <th className="p-3">Class</th>
                        <th className="p-3">Intake Capacity</th>
                        <th className="p-3">Min Age</th>
                        <th className="p-3">Max Age</th>
                        <th className="p-3">Assessment Mode</th>
                        <th className="p-3">Parent Interaction</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rule">
                      {cycleData.classes.map((c) => (
                        <tr key={c.class_name} className="hover:bg-ground/40">
                          <td className="p-3 font-bold text-ink">Class {c.class_name}</td>
                          <td className="p-3 font-mono font-semibold text-primary">{c.total_seats} seats</td>
                          <td className="p-3 text-ink-soft">{c.min_age_years ? `${c.min_age_years} yrs` : "—"}</td>
                          <td className="p-3 text-ink-soft">{c.max_age_years ? `${c.max_age_years} yrs` : "—"}</td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                                c.requires_test ? "bg-amber-100 text-amber-900" : "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {c.requires_test ? "Written Readiness Assessment" : "Direct Interaction"}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                                c.requires_interview ? "bg-purple-100 text-purple-900" : "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {c.requires_interview ? "Mandatory" : "Optional"}
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

              {/* Document Checklist */}
              <div className="bg-ground rounded-xl p-5 border border-rule space-y-3">
                <h3 className="text-sm font-bold text-ink">Mandatory Verification Checklist at Admission Cell</h3>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-ink-soft list-disc list-inside">
                  <li>Original & Photocopy of Student's Official Birth Certificate</li>
                  <li>Student's Aadhaar Card / Identity Card</li>
                  <li>Father's and Mother's Aadhaar Cards / Identity Proofs</li>
                  <li>Residential Address Proof (Electricity bill / Passport / Voter ID)</li>
                  <li>Four Recent Passport Size Photographs of the Student</li>
                  <li>Transfer Certificate (TC) from recognized previous school (Class 1 onwards)</li>
                  <li>Previous Academic Year Report Card / Marksheet</li>
                  <li>Caste / Quota Certificate (if applying under SC/ST/OBC/RTE)</li>
                </ul>
              </div>

              {cycleData?.cycle.refund_policy && (
                <div className="text-xs text-ink-soft border-t border-rule pt-4">
                  <strong className="text-ink">Fee Refund & Withdrawal Policy:</strong>{" "}
                  {cycleData.cycle.refund_policy}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* ============================================================= */}
      {/* CONTROLLED MOCK PAYMENT GATEWAY MODAL                         */}
      {/* ============================================================= */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
          <div className="bg-surface rounded-2xl border border-rule shadow-2xl max-w-lg w-full overflow-hidden my-8">
            {/* Payment Header */}
            <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center font-bold text-lg">
                  🔒
                </div>
                <div>
                  <h3 className="font-bold text-base">Sunrise School Payment Gateway</h3>
                  <p className="text-xs text-white/70">Order Ref: {orderId || "MOCK-ORDER"}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-white/70">Total Amount</div>
                <div className="text-xl font-bold font-mono text-emerald-400">
                  ₹{parseFloat(payableAmount || statusResult?.payable_amount || "0").toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            {/* Sandbox Simulation Notice Banner */}
            <div className="bg-amber-50 border-b border-amber-200 p-3 px-5 text-amber-900 text-xs flex items-center gap-2">
              <span className="text-base">🧪</span>
              <div>
                <strong>Admissions Sandbox Mode:</strong> This is a secure mock payment gateway simulating
                Razorpay / BillDesk processing. Use the simulation controls below to test outcomes.
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Payment Method Selector */}
              <div className="flex rounded-lg bg-ground p-1 border border-rule">
                <button
                  type="button"
                  onClick={() => setPaymentMethodTab("upi")}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
                    paymentMethodTab === "upi" ? "bg-white text-primary shadow-xs" : "text-ink-soft hover:text-ink"
                  }`}
                >
                  UPI / QR Code
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethodTab("card")}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
                    paymentMethodTab === "card" ? "bg-white text-primary shadow-xs" : "text-ink-soft hover:text-ink"
                  }`}
                >
                  Cards (Debit / Credit)
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethodTab("netbanking")}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition ${
                    paymentMethodTab === "netbanking" ? "bg-white text-primary shadow-xs" : "text-ink-soft hover:text-ink"
                  }`}
                >
                  Net Banking
                </button>
              </div>

              {/* Tab 1: UPI */}
              {paymentMethodTab === "upi" && (
                <div className="text-center space-y-4 py-2">
                  <div className="w-36 h-36 mx-auto bg-white border-2 border-dashed border-rule rounded-xl p-2 flex flex-col items-center justify-center shadow-xs">
                    {/* Mock QR SVG */}
                    <div className="grid grid-cols-6 gap-1 w-28 h-28 p-1 bg-slate-50 border border-slate-200 rounded">
                      {Array.from({ length: 36 }).map((_, i) => (
                        <div
                          key={i}
                          className={`rounded-xs ${
                            (i % 2 === 0 && i % 3 === 0) || i === 0 || i === 5 || i === 30 || i === 35
                              ? "bg-slate-800"
                              : "bg-slate-200"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="text-xs text-ink-soft">
                    Scan with any UPI app: <strong>Google Pay, PhonePe, Paytm, BHIM</strong>
                  </div>
                  <div className="bg-ground px-3 py-1.5 rounded-lg border border-rule text-xs font-mono inline-block text-ink">
                    VPA: <strong>sunrise.sps@icici</strong>
                  </div>
                </div>
              )}

              {/* Tab 2: Cards */}
              {paymentMethodTab === "card" && (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-ink-soft font-semibold mb-1">Card Number</label>
                    <input
                      readOnly
                      value="4532 •••• •••• 8892"
                      className="w-full rounded-input border border-rule px-3 py-2 font-mono bg-ground"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-ink-soft font-semibold mb-1">Valid Thru</label>
                      <input
                        readOnly
                        value="12 / 28"
                        className="w-full rounded-input border border-rule px-3 py-2 font-mono bg-ground"
                      />
                    </div>
                    <div>
                      <label className="block text-ink-soft font-semibold mb-1">CVV</label>
                      <input
                        readOnly
                        value="•••"
                        className="w-full rounded-input border border-rule px-3 py-2 font-mono bg-ground"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Net Banking */}
              {paymentMethodTab === "netbanking" && (
                <div className="space-y-3 text-xs">
                  <label className="block text-ink-soft font-semibold">Select Bank</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { id: "sbi", name: "State Bank of India" },
                      { id: "hdfc", name: "HDFC Bank" },
                      { id: "icici", name: "ICICI Bank" },
                      { id: "axis", name: "Axis Bank" },
                    ].map((b) => (
                      <button
                        key={b.id}
                        type="button"
                        onClick={() => setSelectedBank(b.id)}
                        className={`p-2.5 rounded-lg border text-left font-medium transition ${
                          selectedBank === b.id
                            ? "border-primary bg-primary/5 text-primary font-bold"
                            : "border-rule bg-ground text-ink"
                        }`}
                      >
                        {b.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Error Message */}
              {paymentError && (
                <div className="bg-red-50 border border-red-200 text-danger text-xs rounded-lg p-3 font-medium">
                  {paymentError}
                </div>
              )}

              {/* Controlled Gateway Simulation Controls */}
              <div className="border-t border-rule pt-4 space-y-3">
                <div className="text-[11px] font-bold uppercase tracking-wider text-ink-soft text-center">
                  Simulate Gateway Response
                </div>
                <div className="flex flex-col sm:flex-row gap-2">
                  <button
                    type="button"
                    disabled={paymentProcessing}
                    onClick={() => handleProcessPayment("success")}
                    className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-input shadow-md transition disabled:opacity-50 flex items-center justify-center gap-1.5"
                  >
                    {paymentProcessing ? (
                      <span className="animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                    ) : (
                      <>
                        <span>✓</span>
                        <span>Simulate Payment Success</span>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    disabled={paymentProcessing}
                    onClick={() => handleProcessPayment("failure")}
                    className="py-2.5 px-4 bg-red-100 hover:bg-red-200 text-red-800 font-bold text-xs rounded-input transition disabled:opacity-50"
                  >
                    Simulate Failure
                  </button>

                  <button
                    type="button"
                    disabled={paymentProcessing}
                    onClick={() => handleProcessPayment("cancel")}
                    className="py-2.5 px-3 bg-surface hover:bg-ground border border-rule text-ink-soft text-xs font-semibold rounded-input transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================= */}
      {/* OFFICIAL GATED DOCUMENT VIEWER & PRINTABLE MODAL              */}
      {/* ============================================================= */}
      {activeDocModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
          <div className="bg-surface rounded-2xl border border-rule shadow-2xl max-w-3xl w-full overflow-hidden my-8 flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="bg-ground border-b border-rule p-4 px-6 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-ink">
                  {activeDocModal === "dossier" && "Completed Student Admission Dossier"}
                  {activeDocModal === "admission_letter" && "Provisional Admission Confirmation Letter"}
                  {activeDocModal === "receipt" && "Official Fee Payment Receipt Voucher"}
                </h3>
                <p className="text-xs text-ink-soft">Sunrise Public School • Official Record</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg shadow-xs hover:bg-primary-dark transition flex items-center gap-1.5"
                >
                  <span>🖨️</span> Print / Save PDF
                </button>
                <button
                  type="button"
                  onClick={() => setActiveDocModal(null)}
                  className="px-3 py-1.5 bg-surface border border-rule text-ink-soft hover:text-ink text-xs font-semibold rounded-lg hover:bg-ground transition"
                >
                  ✕ Close
                </button>
              </div>
            </div>

            {/* Document Content */}
            <div className="p-6 md:p-8 overflow-y-auto flex-1 space-y-6 text-ink">
              {docLoading ? (
                <div className="py-12 text-center text-ink-faint">
                  <span className="animate-spin inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full mb-3" />
                  <p className="text-xs font-semibold">Generating authentic printable document...</p>
                </div>
              ) : docError ? (
                <div className="bg-red-50 border border-red-200 text-danger p-4 rounded-xl text-xs font-medium">
                  {docError}
                </div>
              ) : docData ? (
                <div className="border border-rule rounded-xl p-6 md:p-8 bg-white shadow-sm space-y-6 text-ink font-sans printable-area">
                  {/* Document Header Letterhead */}
                  <div className="border-b-2 border-primary pb-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-14 h-14 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-xl shadow-xs">
                        SPS
                      </div>
                      <div>
                        <h2 className="text-xl font-bold tracking-tight text-slate-900">
                          {docData.school?.name || "Sunrise Public School"}
                        </h2>
                        <p className="text-xs text-slate-600">
                          Sector 4, Gomti Nagar, Lucknow, Uttar Pradesh 226010
                        </p>
                        <p className="text-[11px] text-slate-500">
                          CBSE Affiliation No: 2132849 • School Code: 70892 • admissions@sunrisepublic.edu
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-xs">
                      <div className="font-mono font-bold text-slate-900">{docData.student?.admission_no}</div>
                      <div className="text-[10px] text-slate-500 uppercase">Admission Number</div>
                    </div>
                  </div>

                  {/* DOCUMENT 1: PROVISIONAL ADMISSION LETTER */}
                  {activeDocModal === "admission_letter" && (
                    <div className="space-y-6 text-xs text-slate-800 leading-relaxed">
                      <div className="text-center py-2">
                        <span className="text-xs font-bold uppercase tracking-widest text-primary border-b-2 border-primary pb-1">
                          Provisional Admission Confirmation Letter
                        </span>
                        <div className="text-[11px] text-slate-500 mt-2">
                          Academic Session: 2025–26 • Date of Issue: {docData.student?.admission_date || new Date().toLocaleDateString("en-IN")}
                        </div>
                      </div>

                      <div className="space-y-1">
                        <p><strong>To,</strong></p>
                        <p>The Parents / Guardians of <strong>{docData.application?.full_name}</strong>,</p>
                        <p>{docData.application?.address?.address_line}, {docData.application?.address?.city || "Lucknow"} - {docData.application?.address?.pin_code}</p>
                      </div>

                      <p>
                        Dear Parents,
                      </p>
                      <p>
                        We take immense pleasure in informing you that your ward, <strong>{docData.application?.full_name}</strong>,
                        has been formally granted provisional admission into <strong>{docData.student?.class_label}</strong> at
                        Sunrise Public School, Gomti Nagar, Lucknow, for the Academic Session 2025–26.
                      </p>
                      <p>
                        The admission has been confirmed following the successful verification of submitted credentials
                        and receipt of the initial admission fee under Receipt No: <strong>{docData.payment?.receipt_no}</strong>.
                      </p>

                      {/* Summary Table */}
                      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2 text-xs">
                        <div className="grid grid-cols-2 gap-2">
                          <div><span className="text-slate-500">Student Name:</span> <strong>{docData.application?.full_name}</strong></div>
                          <div><span className="text-slate-500">Permanent Admission No:</span> <strong className="font-mono">{docData.student?.admission_no}</strong></div>
                          <div><span className="text-slate-500">Class & Section:</span> <strong>{docData.student?.class_label}</strong></div>
                          <div><span className="text-slate-500">Allocated Roll Number:</span> <strong className="font-mono">{docData.student?.roll_no ?? "Allocated"}</strong></div>
                        </div>
                      </div>

                      <p>
                        The regular academic session will commence as per the published school academic calendar.
                        Textbooks, stationery lists, and school uniform guidelines are available at the administration desk.
                      </p>

                      <div className="pt-8 flex justify-between items-end border-t border-slate-200">
                        <div>
                          <p className="text-[11px] text-slate-500">Admissions Cell Direct</p>
                          <p className="font-semibold text-slate-800">Registrar & Admissions Dean</p>
                        </div>
                        <div className="text-right">
                          <p className="text-[11px] text-slate-500">Approved by</p>
                          <p className="font-bold text-slate-900">Dr. Sunita Sharma, Ph.D.</p>
                          <p className="text-[10px] text-slate-500">Principal, Sunrise Public School</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* DOCUMENT 2: FEE PAYMENT RECEIPT VOUCHER */}
                  {activeDocModal === "receipt" && (
                    <div className="space-y-6 text-xs text-slate-800">
                      <div className="text-center py-2">
                        <span className="text-xs font-bold uppercase tracking-widest text-emerald-800 border-b-2 border-emerald-600 pb-1">
                          Official Admission Fee Payment Receipt
                        </span>
                        <div className="text-[11px] text-slate-500 mt-2">
                          Voucher No: <strong className="font-mono text-slate-900">{docData.payment?.receipt_no}</strong> • Date: {docData.payment?.paid_at ? new Date(docData.payment.paid_at).toLocaleString("en-IN") : "Today"}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
                        <div>
                          <span className="text-slate-500 text-[11px] block">Student Name</span>
                          <strong className="text-sm">{docData.application?.full_name}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Admission Number</span>
                          <strong className="font-mono text-sm">{docData.student?.admission_no}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Class & Section</span>
                          <strong>{docData.student?.class_label}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Payment Gateway Reference</span>
                          <strong className="font-mono">{docData.payment?.reference || "MOCK-TRANS"}</strong>
                        </div>
                      </div>

                      <table className="w-full text-left border border-slate-200 rounded-lg">
                        <thead className="bg-slate-100 border-b border-slate-200 font-semibold text-slate-700">
                          <tr>
                            <th className="p-3">S.No</th>
                            <th className="p-3">Fee Head / Description</th>
                            <th className="p-3 text-right">Amount (INR)</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          <tr>
                            <td className="p-3">1</td>
                            <td className="p-3">
                              <strong>Admission & Enrollment Fee</strong>
                              <div className="text-[11px] text-slate-500">
                                Class {docData.application?.class_applying_for} • Academic Session 2025–26
                              </div>
                            </td>
                            <td className="p-3 text-right font-mono font-bold">
                              ₹{parseFloat(docData.payment?.amount || "0").toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                          <tr className="bg-slate-50 font-bold">
                            <td colSpan={2} className="p-3 text-right text-slate-700">Total Paid:</td>
                            <td className="p-3 text-right font-mono text-primary text-sm">
                              ₹{parseFloat(docData.payment?.amount || "0").toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        </tbody>
                      </table>

                      <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <span className="text-slate-500">Amount in Words: </span>
                        <strong>{docData.payment?.amount_in_words || "Zero Rupees Only"}</strong>
                      </div>

                      <div className="pt-6 flex justify-between items-end text-xs text-slate-600">
                        <div>
                          <p>Payment Mode: <strong>Online Mock Payment Gateway</strong></p>
                          <p>Status: <strong className="text-emerald-700 font-semibold">Payment Confirmed & Settled</strong></p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-slate-900">Authorized Accounts Signatory</p>
                          <p className="text-[10px] text-slate-500">Sunrise Public School Finance Cell</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* DOCUMENT 3: APPLICATION DOSSIER */}
                  {activeDocModal === "dossier" && (
                    <div className="space-y-6 text-xs text-slate-800">
                      <div className="text-center py-2">
                        <span className="text-xs font-bold uppercase tracking-widest text-primary border-b-2 border-primary pb-1">
                          Official Student Admission Dossier
                        </span>
                        <div className="text-[11px] text-slate-500 mt-2">
                          Application Reference: <strong className="font-mono">{docData.application?.application_no}</strong> • Status: Enrolled
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
                        <div>
                          <span className="text-slate-500 text-[11px] block">Student Legal Name</span>
                          <strong className="text-sm">{docData.application?.full_name}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Admission Number</span>
                          <strong className="font-mono text-sm">{docData.student?.admission_no}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Class Allocated</span>
                          <strong>{docData.student?.class_label}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Date of Birth</span>
                          <strong>{docData.application?.date_of_birth}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Residential Address</span>
                          <span>{docData.application?.address?.address_line}, {docData.application?.address?.city}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 text-[11px] block">Transport Required</span>
                          <span>{docData.application?.transport_required ? "Yes (School Bus)" : "No"}</span>
                        </div>
                      </div>

                      {/* Guardian Record */}
                      <div className="space-y-2">
                        <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                          Registered Parents & Guardians
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {docData.guardians?.map((g: any, idx: number) => (
                            <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                              <div className="font-bold text-slate-900 capitalize">
                                {g.full_name} ({g.relation})
                              </div>
                              <div className="text-slate-600">Mobile: <span className="font-mono font-semibold">{g.mobile}</span></div>
                              {g.email && <div className="text-slate-600">Email: {g.email}</div>}
                              {g.occupation && <div className="text-slate-600">Occupation: {g.occupation}</div>}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="pt-4 border-t border-slate-200 flex justify-between items-center text-[11px] text-slate-500">
                        <span>Official CBSE Registry Copy • Sunrise Public School</span>
                        <span>Generated on {new Date().toLocaleDateString("en-IN")}</span>
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
