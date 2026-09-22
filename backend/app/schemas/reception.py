"""Pydantic schemas for receptionist operational modules."""
from datetime import date as Date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class FoundItemCreate(BaseModel):
    item_name: str = Field(..., max_length=150)
    category: str = Field(default="other", max_length=50)
    description: str | None = None
    found_location: str = Field(..., max_length=150)
    found_date: Date
    found_time: str | None = Field(default=None, max_length=20)
    photo_url: str | None = None


class FoundItemCollect(BaseModel):
    claimed_by_student_id: int | None = None
    claimed_by_student_name: str | None = Field(default=None, max_length=120)
    claimed_by_admission_no: str | None = Field(default=None, max_length=50)
    claimed_by_class_name: str | None = Field(default=None, max_length=50)
    handover_photo_url: str | None = None
    handover_notes: str | None = None


class FoundItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    item_name: str
    category: str
    description: str | None = None
    found_location: str
    found_date: Date
    found_time: str | None = None
    recorded_by_id: int
    recorded_by_name: str
    photo_url: str | None = None
    status: str
    broadcasted_at: datetime | None = None
    claimed_by_student_id: int | None = None
    claimed_by_student_name: str | None = None
    claimed_by_admission_no: str | None = None
    claimed_by_class_name: str | None = None
    handover_photo_url: str | None = None
    handover_notes: str | None = None
    collected_at: datetime | None = None
    collected_by_staff_id: int | None = None
    collected_by_staff_name: str | None = None
    created_at: datetime


class StudentAuthorizedPersonIn(BaseModel):
    name: str = Field(..., max_length=120)
    relationship: str = Field(..., max_length=60)
    phone: str = Field(..., max_length=30)
    id_proof_type: str | None = Field(default=None, max_length=50)
    id_proof_number: str | None = Field(default=None, max_length=50)
    photo_url: str | None = None
    notes: str | None = None
    is_active: bool = True


class StudentAuthorizedPersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    student_id: int
    name: str
    relationship: str
    phone: str
    id_proof_type: str | None = None
    id_proof_number: str | None = None
    photo_url: str | None = None
    is_active: bool
    notes: str | None = None
    created_at: datetime


class StudentPassCreate(BaseModel):
    student_id: int
    reason: str
    pickup_person_name: str = Field(..., max_length=120)
    pickup_person_relation: str = Field(..., max_length=60)
    pickup_person_phone: str = Field(..., max_length=30)
    pickup_person_id_proof: str | None = Field(default=None, max_length=80)
    pass_date: Date
    pass_time: str = Field(..., max_length=20)
    remarks: str | None = None


class StudentPassStatusUpdate(BaseModel):
    status: str
    remarks: str | None = None


class StudentPassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    pass_code: str
    student_id: int
    student_name: str
    admission_no: str
    class_name: str | None = None
    reason: str
    pickup_person_name: str
    pickup_person_relation: str
    pickup_person_phone: str
    pickup_person_id_proof: str | None = None
    pass_date: Date
    pass_time: str
    issued_by_id: int
    issued_by_name: str
    status: str
    remarks: str | None = None
    created_at: datetime


class PrincipalMeetingCreate(BaseModel):
    visitor_name: str = Field(..., max_length=120)
    visitor_phone: str = Field(..., max_length=30)
    visitor_organization: str | None = Field(default=None, max_length=120)
    student_name: str | None = Field(default=None, max_length=120)
    student_admission_no: str | None = Field(default=None, max_length=50)
    reason: str
    meeting_date: Date
    meeting_time: str = Field(..., max_length=20)


class PrincipalMeetingRespond(BaseModel):
    status: str  # accepted, declined, waiting, completed, cancelled
    wait_duration_minutes: int | None = None
    response_notes: str | None = None


class PrincipalMeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    slip_code: str
    visitor_name: str
    visitor_phone: str
    visitor_organization: str | None = None
    student_name: str | None = None
    student_admission_no: str | None = None
    reason: str
    meeting_date: Date
    meeting_time: str
    status: str
    wait_duration_minutes: int | None = None
    response_notes: str | None = None
    responded_at: datetime | None = None
    created_by_id: int
    created_by_name: str
    created_at: datetime


class TeacherMeetingCreate(BaseModel):
    teacher_id: int
    visitor_name: str = Field(..., max_length=120)
    visitor_phone: str = Field(..., max_length=30)
    visitor_relation: str | None = Field(default=None, max_length=60)
    student_name: str | None = Field(default=None, max_length=120)
    student_admission_no: str | None = Field(default=None, max_length=50)
    reason: str
    meeting_date: Date
    meeting_time: str = Field(..., max_length=20)


class TeacherMeetingRespond(BaseModel):
    status: str  # accepted, declined, completed, cancelled
    response_notes: str | None = None


class TeacherMeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    slip_code: str
    teacher_id: int
    teacher_name: str
    visitor_name: str
    visitor_phone: str
    visitor_relation: str | None = None
    student_name: str | None = None
    student_admission_no: str | None = None
    reason: str
    meeting_date: Date
    meeting_time: str
    status: str
    response_notes: str | None = None
    responded_at: datetime | None = None
    created_by_id: int
    created_by_name: str
    created_at: datetime


class DirectoryContactIn(BaseModel):
    category: str = Field(default="Emergency", max_length=60)
    name: str = Field(..., max_length=150)
    designation_or_department: str | None = Field(default=None, max_length=120)
    phone_primary: str = Field(..., max_length=40)
    phone_secondary: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    address: str | None = None
    operating_hours: str | None = Field(default=None, max_length=100)
    is_emergency: bool = False
    display_order: int = 0
    notes: str | None = None


class DirectoryContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    category: str
    name: str
    designation_or_department: str | None = None
    phone_primary: str
    phone_secondary: str | None = None
    email: str | None = None
    address: str | None = None
    operating_hours: str | None = None
    is_emergency: bool
    display_order: int
    notes: str | None = None
    created_at: datetime


class ReceptionFeeCollectIn(BaseModel):
    enrolment_id: int
    num_months: int
    payment_method: str = "cash"
    notes: str | None = None
