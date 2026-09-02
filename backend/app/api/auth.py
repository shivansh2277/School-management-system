from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import ClassSection, Student, User, UserRole
from app.schemas.auth import (
    AccessToken,
    ChangePasswordRequest,
    ChildRef,
    LoginRequest,
    MeOut,
    RefreshRequest,
    TokenPair,
    UserOut,
)
from app.services import scoping

router = APIRouter(prefix="/auth", tags=["auth"])

_BAD_CREDS = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials for this role")


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.login_id == body.login_id))
    # The role tab must match users.role: correct credentials through the wrong
    # tab are rejected (BLUEPRINT §9).
    if user is None or user.role != body.role or not user.is_active:
        raise _BAD_CREDS
    if not verify_password(body.password, user.password_hash):
        raise _BAD_CREDS
    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
        user=UserOut.model_validate(user, from_attributes=True),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> AccessToken:
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    return AccessToken(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeOut:
    out = MeOut(user=UserOut.model_validate(user, from_attributes=True))
    if user.role == UserRole.student:
        s = scoping.student_for(db, user)
        out.admission_no = s.admission_no
        out.class_label = s.class_section.label
        out.roll_no = s.roll_no
    elif user.role == UserRole.teacher:
        t = scoping.teacher_for(db, user)
        out.employee_id = t.employee_id
        ids = scoping.class_section_ids_for(db, user)
        out.sections = [
            cs.label for cs in db.scalars(select(ClassSection).where(ClassSection.id.in_(ids)))
        ]
    elif user.role == UserRole.parent:
        ids = scoping.child_ids_for(db, user)
        out.children = [
            ChildRef(
                id=s.id,
                name=s.user.full_name,
                class_label=s.class_section.label,
                admission_no=s.admission_no,
            )
            for s in db.scalars(select(Student).where(Student.id.in_(ids)))
        ]
    return out


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
