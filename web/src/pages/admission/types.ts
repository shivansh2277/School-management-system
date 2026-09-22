/** Types for the Admission module (ERP_BLUEPRINT §5.1). */

export type AdmissionCycle = {
  id: number;
  name: string;
  academic_year_id: number;
  academic_year: string;
  status: "planning" | "open" | "closed" | "archived";
  starts_on: string | null;
  ends_on: string | null;
  application_fee: string;
  late_fee: string;
  allow_online_applications: boolean;
  admission_fee_refund_policy: string | null;
};

export type CycleClassConfig = {
  id: number;
  class_name: string;
  stream: string | null;
  total_seats: number;
  reserved_seats: Record<string, number>;
  age_on: string | null;
  min_age_years: string | null;
  max_age_years: string | null;
  requires_test: boolean;
  requires_interview: boolean;
  required_document_codes: string[];
};

export type Enquiry = {
  id: number;
  cycle_id: number;
  enquirer_name: string;
  mobile: string;
  email: string | null;
  child_name: string | null;
  child_dob: string | null;
  class_of_interest: string | null;
  source: string;
  status: string;
  assigned_to: number | null;
  next_follow_up_on: string | null;
  converted_application_id: number | null;
};

export type EnquiryInteraction = {
  id: number;
  occurred_at: string;
  channel: string;
  notes: string | null;
  outcome: string | null;
  by_user_id: number | null;
};

export type EnquiryDetail = Enquiry & {
  interactions: EnquiryInteraction[];
};

export type ApplicationRow = {
  id: number;
  application_no: string;
  cycle_id: number;
  name: string;
  date_of_birth: string;
  gender: string;
  class_applying_for: string;
  stream: string | null;
  status: string;
  admission_category: string;
  sibling_verified: boolean;
  staff_ward_verified: boolean;
  submitted_at: string | null;
  source: string;
  student_id: number | null;
};

export type GuardianOut = {
  id: number;
  relation: string;
  full_name: string;
  date_of_birth?: string | null;
  qualification?: string | null;
  occupation: string | null;
  designation: string | null;
  organisation: string | null;
  annual_income_band: string | null;
  office_address?: string | null;
  mobile: string;
  alternate_mobile: string | null;
  email: string | null;
  is_primary: boolean;
  is_emergency_contact: boolean;
  is_authorised_for_pickup: boolean;
  is_school_alumnus: boolean;
  is_school_staff: boolean;
  employee_id: number | null;
};

export type SiblingOut = {
  id: number;
  student_id: number | null;
  name: string | null;
  age: number | null;
  school_name: string | null;
};

export type ApplicationDetail = ApplicationRow & {
  first_name: string;
  middle_name: string | null;
  last_name: string;
  nationality: string | null;
  religion: string | null;
  caste_category: string | null;
  mother_tongue: string | null;
  place_of_birth: string | null;
  identification_marks: string | null;
  is_single_child: boolean;
  aadhaar_last4: string | null;
  second_language: string | null;
  optional_subject: string | null;
  preferred_section: string | null;
  transport_required: boolean;
  address: Record<string, any>;
  previous_school: Record<string, any>;
  declarations: Record<string, any>;
  age_override_reason: string | null;
  previous_application_id: number | null;
  guardians: GuardianOut[];
  siblings: SiblingOut[];
  completeness_pct: number;
  effective_category: string;
  enrolled_student?: {
    student_id: number;
    admission_no: string;
    class_label: string;
    section?: string | null;
    roll_no?: number | null;
    academic_year?: string | null;
    status: string;
  } | null;
};

export type ApplicationMedical = {
  id?: number;
  blood_group?: string | null;
  known_allergies?: string | null;
  chronic_conditions?: string | null;
  regular_medication?: string | null;
  physical_disability?: string | null;
  learning_needs?: string | null;
  vision_hearing_notes?: string | null;
  emergency_doctor?: string | null;
  emergency_doctor_phone?: string | null;
  consent_for_emergency_treatment?: boolean;
  height_cm?: number | string | null;
  weight_kg?: number | string | null;
};

export type ChecklistItem = {
  code: string;
  name: string;
  mandatory: boolean;
  is_conditional: boolean;
  condition_category: string | null;
  status: "pending" | "submitted" | "verified" | "rejected" | "resubmit_required";
  document_id: number | null;
  filename: string | null;
  verified_at: string | null;
};

export type ChecklistResponse = {
  items: ChecklistItem[];
  outstanding: string[];
};

export type AssessmentSubject = {
  subject: string;
  max_marks: string;
  obtained: string | null;
};

export type AssessmentOut = {
  id: number;
  application_id: number;
  assessment_type: string;
  scheduled_at: string;
  venue: string | null;
  seat_no: string | null;
  status: string;
  total_marks: string | null;
  obtained_marks: string | null;
  percent: string | null;
  is_absent: boolean;
  remarks: string | null;
  subjects: AssessmentSubject[];
};

export type InterviewOut = {
  id: number;
  application_id: number;
  scheduled_at: string;
  venue: string | null;
  panel_member_ids: number[];
  status: string;
  child_rating: number | null;
  parent_rating: number | null;
  recommendation: string | null;
  scores: Record<string, any>;
};

export type EvaluationResponse = {
  assessments: AssessmentOut[];
  interviews: InterviewOut[];
};

export type AdmissionDecision = {
  decision: "admitted" | "waitlisted" | "rejected";
  reason: string;
  seat_category: string | null;
  conditions: string | null;
  over_allocation_approved: boolean;
  decided_by: number | null;
  decided_at: string;
};

export type OfferOut = {
  id: number;
  application_id: number;
  offered_at: string;
  expires_on: string;
  offer_amount: string | null;
  status: "issued" | "accepted" | "declined" | "expired" | "withdrawn";
  accepted_at: string | null;
  released_at: string | null;
};

export type ApplicationPayment = {
  id: number;
  receipt_no: string;
  purpose: "application_fee" | "admission_fee";
  amount: string;
  method: string;
  reference: string | null;
  paid_at: string;
  status: "paid" | "voided" | "refunded";
  void_reason: string | null;
};

export type ConversionPreview = {
  student_preview?: {
    admission_no?: string;
    first_name?: string;
    last_name?: string;
    class_name?: string;
  };
  users_preview?: {
    role: string;
    username: string;
    phone?: string;
  }[];
  ready?: boolean;
  blocking_reasons?: string[];
  [key: string]: any;
};

export type SeatUsage = {
  class_name: string;
  stream: string | null;
  total_seats: number;
  general_seats: number;
  reserved_seats: Record<string, number>;
  filled_total: number;
  filled_general: number;
  filled_reserved: Record<string, number>;
  remaining_total: number;
  remaining_general: number;
  remaining_reserved: Record<string, number>;
};

export type MeritApplicant = {
  application_id: number;
  application_no: string;
  name: string;
  class_name: string;
  category: string;
  total_score: number | null;
  assessment_score: number | null;
  interview_score: number | null;
  sibling_verified: boolean;
  staff_ward_verified: boolean;
  status: string;
  rank?: number;
  priority?: number;
  composite?: number | null;
  assessment_percent?: number | null;
};

export type MeritResponse = {
  seats: SeatUsage;
  applicants: MeritApplicant[];
};

export type WaitlistEntry = {
  rank: number;
  status: string;
  application_id: number;
  application_no: string;
  name: string;
  application_status: string;
};

export type AdmissionReports = {
  funnel: Record<string, number>;
  by_source: Record<string, { enquiries: number; converted: number }>;
  seat_utilisation: {
    class_name: string;
    stream: string | null;
    total_seats: number;
    enrolled: number;
    utilisation_pct: number;
  }[];
  demographics: {
    gender: Record<string, number>;
    category: Record<string, number>;
  };
  rejections: Record<string, number>;
  cycle_time: Record<string, number>;
};
