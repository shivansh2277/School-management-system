from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import UserRole


class AdminUserAccessItem(BaseModel):
    id: int
    login_id: str
    role: UserRole
    full_name: str
    phone: str | None = None
    email: str | None = None
    is_active: bool
    app_access_blocked: bool
    token_version: int
    created_at: datetime | None = None
    identifier: str | None = None  # admission_no or staff_code
    subtext: str | None = None     # class section or department or children names
    roles: list[str] = Field(default_factory=list)


class BlockUserRequest(BaseModel):
    reason: str | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=6)


class AssignUserRoleRequest(BaseModel):
    role_code: str = Field(min_length=1, max_length=40)


class UserAccessActionResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    app_access_blocked: bool
    token_version: int
    roles: list[str] = Field(default_factory=list)
