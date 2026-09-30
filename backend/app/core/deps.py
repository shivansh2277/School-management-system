from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models import User, UserRole

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(creds.credentials)
    if not payload or payload.get("typ") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if getattr(user, "app_access_blocked", False):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "App access has been blocked by administrator")
    token_ver = payload.get("ver")
    if token_ver is not None and token_ver != getattr(user, "token_version", 1):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or password changed. Please log in again.")
    return user


def require_role(*roles: UserRole):
    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Out of scope for this role")
        return user

    return _dep
