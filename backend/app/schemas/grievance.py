from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GrievanceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    category: str = Field(default="general", max_length=60)
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    student_id: int | None = None


class GrievanceReplyCreate(BaseModel):
    message: str = Field(min_length=1)
    is_internal: bool = False


class GrievanceAssign(BaseModel):
    assigned_to_id: int  # employee_id


class GrievanceStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved", "closed"]
    resolution_notes: str | None = None


class GrievanceReplyOut(BaseModel):
    id: int
    grievance_id: int
    author_id: int
    author_name: str
    author_role: str
    message: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GrievanceOut(BaseModel):
    id: int
    school_id: int
    title: str
    description: str
    category: str
    raised_by_id: int
    raised_by_role: str
    raised_by_name: str
    student_id: int | None = None
    student_name: str | None = None
    status: str
    priority: str
    assigned_to_id: int | None = None
    assigned_to_name: str | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    replies_count: int = 0
    replies: list[GrievanceReplyOut] = []

    class Config:
        from_attributes = True


class GrievanceStatsOut(BaseModel):
    total_count: int
    open_count: int
    in_progress_count: int
    resolved_count: int
    teacher_count: int
    parent_count: int
