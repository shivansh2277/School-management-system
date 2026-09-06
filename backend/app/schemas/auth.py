from pydantic import BaseModel, Field

from app.models import UserRole


class LoginRequest(BaseModel):
    role: UserRole
    login_id: str
    password: str
    # Logins are unique per school, not globally: two schools both have an
    # "admin" and both may issue admission no 2026000001. The web app supplies
    # this from its subdomain or configured school; it stays optional so a
    # single-school deployment need not ask for it.
    school_code: str | None = None


class UserOut(BaseModel):
    id: int
    role: UserRole
    login_id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    photo_url: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class ChildRef(BaseModel):
    id: int
    name: str
    class_label: str
    admission_no: str


class MeOut(BaseModel):
    user: UserOut
    # exactly one of these is populated, by role
    admission_no: str | None = None
    class_label: str | None = None
    roll_no: int | None = None
    employee_id: str | None = None
    sections: list[str] | None = None
    children: list[ChildRef] | None = None
