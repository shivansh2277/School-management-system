from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel

from app.models import AttendanceStatus, InvoiceStatus, NoticeAudience


class Page(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class PersonRef(BaseModel):
    id: int
    full_name: str


# --- attendance -------------------------------------------------------------


class AttendanceEntry(BaseModel):
    student_id: int
    status: AttendanceStatus
    remarks: str | None = None


class AttendanceMarkRequest(BaseModel):
    class_section_id: int
    date: date
    entries: list[AttendanceEntry]


class RollRow(BaseModel):
    student_id: int
    full_name: str
    roll_no: int
    status: AttendanceStatus | None = None
    remarks: str | None = None


class AttendanceSummary(BaseModel):
    present: int
    absent: int
    leave: int
    percent: float | None  # None when nothing is marked yet — never a fake 0


class AttendanceDay(BaseModel):
    date: date
    status: AttendanceStatus


class AttendanceMonth(BaseModel):
    days: list[AttendanceDay]
    summary: AttendanceSummary


# --- homework ---------------------------------------------------------------


class HomeworkCreate(BaseModel):
    class_section_id: int
    subject_id: int
    title: str
    description: str | None = None
    due_date: date


class HomeworkUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None


class HomeworkOut(BaseModel):
    id: int
    class_section_id: int
    class_label: str
    subject_id: int
    subject: str
    teacher_id: int
    teacher: str
    title: str
    description: str | None
    assigned_date: date
    due_date: date
    submitted_count: int
    total_students: int


class StudentHomeworkOut(HomeworkOut):
    submitted: bool
    submitted_at: datetime | None
    late: bool
    answer_text: str | None


class SubmissionRow(BaseModel):
    student_id: int
    full_name: str
    roll_no: int
    submitted: bool
    submitted_at: datetime | None
    late: bool
    answer_text: str | None


class SubmitRequest(BaseModel):
    answer_text: str


# --- assessment -------------------------------------------------------------


class ExamCreate(BaseModel):
    name: str
    term: str
    start_date: date
    end_date: date


class ExamOut(BaseModel):
    id: int
    name: str
    term: str
    start_date: date
    end_date: date


class ExamScheduleCreate(BaseModel):
    class_section_id: int
    subject_id: int
    exam_date: date
    start_time: time | None = None
    max_marks: Decimal


class ExamScheduleOut(BaseModel):
    id: int
    exam_id: int
    exam_name: str
    class_section_id: int
    class_label: str
    subject_id: int
    subject: str
    exam_date: date
    start_time: time | None
    max_marks: Decimal
    marks_entered: bool


class MarkEntry(BaseModel):
    student_id: int
    marks_obtained: Decimal


class MarksRequest(BaseModel):
    exam_schedule_id: int
    entries: list[MarkEntry]


class MarksRosterRow(BaseModel):
    student_id: int
    full_name: str
    roll_no: int
    marks_obtained: Decimal | None


class ReportCardRow(BaseModel):
    subject: str
    marks_obtained: Decimal | None  # None = absent; excluded from the totals
    max_marks: Decimal
    percent: float | None
    grade: str | None


class ReportCard(BaseModel):
    exam_id: int
    exam_name: str
    student_id: int
    student_name: str
    class_label: str
    rows: list[ReportCardRow]
    total_obtained: Decimal
    total_max: Decimal
    overall_percent: float | None
    overall_grade: str | None


# --- notices ----------------------------------------------------------------


class NoticeCreate(BaseModel):
    title: str
    body: str
    audience: NoticeAudience
    class_section_id: int | None = None


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    class_section_id: int
    audience: NoticeAudience = NoticeAudience.class_


class NoticeOut(BaseModel):
    id: int
    title: str
    body: str
    audience: NoticeAudience
    class_section_id: int | None
    class_label: str | None
    published_by: str
    published_at: datetime


# --- timetable --------------------------------------------------------------


class SlotOut(BaseModel):
    period: int
    day_of_week: str
    start_time: time
    end_time: time
    class_section_id: int
    class_label: str
    subject: str
    teacher: str
    room: str | None


# --- fees -------------------------------------------------------------------


class InvoiceOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    admission_no: str
    class_label: str
    month: int
    year: int
    amount: Decimal
    due_date: date
    status: InvoiceStatus
    receipt_no: str | None
    paid_at: datetime | None


class GenerateInvoicesRequest(BaseModel):
    month: int
    year: int


class GenerateInvoicesResult(BaseModel):
    created: int
    skipped: int


class PaymentResult(BaseModel):
    invoice_id: int
    receipt_no: str
    txn_ref: str
    amount: Decimal
    paid_at: datetime


class CollectionMonth(BaseModel):
    month: int
    billed: Decimal
    collected: Decimal


class CollectionSummary(BaseModel):
    year: int
    billed: Decimal
    collected: Decimal
    outstanding: Decimal
    months: list[CollectionMonth]
