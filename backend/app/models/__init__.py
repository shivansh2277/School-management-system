from app.models.application_payment import ApplicationPayment
from app.models.selection import (
    AdmissionDecision,
    AdmissionOffer,
    WaitlistEntry,
)
from app.models.assessment_admission import (
    Assessment,
    AssessmentSubject,
    Interview,
)
from app.models.application import (
    Application,
    ApplicationGuardian,
    ApplicationMedical,
    ApplicationSibling,
)
from app.models.admission import (
    AdmissionCycle,
    CycleClassConfig,
    Enquiry,
    EnquiryInteraction,
)
from app.models.academic import (
    ClassSection,
    ClassSubjectTeacher,
    SchoolPeriod,
    Subject,
    Substitution,
    TimetableSlot,
)
from app.models.assessment import (
    AssessmentScheme,
    Exam,
    ExamSchedule,
    GradeBand,
    GradingScale,
    Mark,
    ReportCardPublication,
    SchemeComponent,
)
from app.models.enums import (
    AdmissionCategory,
    ApplicationFeePurpose,
    PaymentStatus,
    DecisionOutcome,
    OfferStatus,
    WaitlistStatus,
    AssessmentStatus,
    AssessmentType,
    InterviewRecommendation,
    AdmissionCycleStatus,
    ApplicationStatus,
    CasteCategory,
    EnquiryChannel,
    EnquirySource,
    EnquiryStatus,
    AcademicYearStatus,
    AttendanceStatus,
    AuditAction,
    LeaveStatus,
    LeaveType,
    CalculationMethod,
    ComponentType,
    CustomFieldType,
    PayrollRunStatus,
    EmployeeStatus,
    EmployeeType,
    GuardianRelation,
    DocumentStatus,
    JobStatus,
    OwnerType,
    EnrolmentStatus,
    DayOfWeek,
    Gender,
    ConcessionStatus,
    ConcessionType,
    FeeFrequency,
    FeeHeadType,
    FeePaymentStatus,
    FeePeriodStatus,
    InvoiceStatus,
    NoticeAudience,
    ScopeType,
    SchoolStatus,
    SubstitutionStatus,
    StudentStatus,
    Channel,
    DeliveryStatus,
    MessageCategory,
    MessageStatus,
    TransportAssignmentStatus,
    TransportDirection,
    UserRole,
    VehicleOwnership,
    VehicleStatus,
    RouteStatus,
)
from app.models.fees import (
    FeeConcession,
    FeeHead,
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    FeePeriod,
    FeePlan,
    FeePlanItem,
    PaymentAllocation,
    StudentFeePlan,
)
from app.models.ops import (
    Attendance,
    Holiday,
    Homework,
    HomeworkSubmission,
    Notice,
    StudentLeaveRequest,
)
from app.models.user import (
    Department,
    Employee,
    Guardian,
    Student,
    StudentGuardian,
    User,
)
from app.models.hr import (
    LeaveBalance,
    LeaveTypeDef,
    StaffAttendance,
    StaffLeaveRequest,
)
from app.models.payroll import (
    PayrollRun,
    Payslip,
    PayslipLine,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureItem,
)
from app.models.comms import (
    Message,
    MessageRecipient,
    MessageTemplate,
    NotificationPreference,
)
from app.models.transport import (
    Route,
    RouteStop,
    TransportAssignment,
    TransportFeeSlab,
    Vehicle,
)
from app.models.enrolment import Enrolment
from app.models.audit import AuditLog, NumberSequence
from app.models.documents import Document, DocumentType
from app.models.jobs import Job, ScheduledJob
from app.models.rbac import Permission, Role, RolePermission, UserRoleAssignment
from app.models.settings import CustomField, Setting
from app.models.tenancy import AcademicYear, School
