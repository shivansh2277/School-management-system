from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth
from app.api.admin import admission as admin_admission
from app.api.admin import attendance as admin_attendance
from app.api.admin import admission_assessment as admin_admission_assessment
from app.api.admin import admission_documents as admin_admission_documents
from app.api.admin import admission_reports as admin_admission_reports
from app.api.admin import applications as admin_applications
from app.api.admin import comms as admin_comms
from app.api.admin import conversion as admin_conversion
from app.api.admin import selection as admin_selection
from app.api.admin import classes as admin_classes
from app.api.admin import exams as admin_exams
from app.api.admin import grading as admin_grading
from app.api.admin import hr as admin_hr
from app.api.admin import payroll as admin_payroll
from app.api.admin import staff_attendance as admin_staff_attendance
from app.api.admin import staff_leave as admin_staff_leave
from app.api.admin import report_cards as admin_report_cards
from app.api.admin import reports as admin_reports
from app.api.admin import schemes as admin_schemes
from app.api.admin import promotion as admin_promotion
from app.api.admin import fee_setup as admin_fee_setup
from app.api.admin import fees as admin_fees
from app.api.admin import notices as admin_notices
from app.api.admin import settings as admin_settings
from app.api.admin import stats as admin_stats
from app.api.admin import students as admin_students
from app.api.admin import teachers as admin_teachers
from app.api.admin import timetable as admin_timetable
from app.api.admin import transport as admin_transport
from app.api.admin import inventory as admin_inventory
from app.api.admin import grievances as admin_grievances
from app.api.admin import reception as admin_reception
from app.api.public import admission as public_admission
from app.api.parent import children as parent_children
from app.api.parent import fees as parent_fees
from app.api.parent import grievances as parent_grievances
from app.api.student import academics as student_academics
from app.api.student import dashboard as student_dashboard
from app.api.teacher import announcements as teacher_announcements
from app.api.teacher import attendance as teacher_attendance
from app.api.teacher import classes as teacher_classes
from app.api.teacher import dashboard as teacher_dashboard
from app.api.teacher import homework as teacher_homework
from app.api.teacher import marks as teacher_marks
from app.api.teacher import stock as teacher_stock
from app.api.teacher import grievances as teacher_grievances
from app.api.teacher import leave as teacher_leave
from app.api.teacher import notifications as teacher_notifications
from app.core.config import settings

app = FastAPI(title="Sunrise School Management System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth,
    admin_stats, admin_students, admin_teachers, admin_classes,
    admin_exams, admin_grading, admin_schemes, admin_promotion, admin_report_cards, admin_hr, admin_staff_leave, admin_staff_attendance, admin_payroll, admin_notices, admin_comms, admin_fees, admin_fee_setup, admin_attendance, admin_timetable, admin_transport, admin_settings, admin_admission, admin_applications, admin_admission_documents, admin_admission_assessment, admin_selection, admin_conversion, admin_admission_reports, admin_reports, admin_inventory, admin_grievances, admin_reception,
    teacher_dashboard, teacher_classes, teacher_attendance,
    teacher_homework, teacher_marks, teacher_announcements, teacher_stock, teacher_grievances, teacher_leave, teacher_notifications,
    student_dashboard, student_academics,
    parent_children, parent_fees, parent_grievances,
    public_admission,
):
    app.include_router(module.router)
    app.include_router(module.router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
@app.get("/api/v1/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
