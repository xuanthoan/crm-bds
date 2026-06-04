from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import get_user_by_id, user_permission_codes

bearer_scheme = HTTPBearer(auto_error=False)


def get_user_permissions(user: User) -> list[str]:
    return user_permission_codes(user)


def user_has_permission(user: User, permission_code: str) -> bool:
    if user.is_superuser:
        return True
    return permission_code in set(get_user_permissions(user))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None
    user = get_user_by_id(db, user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_auth(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_permission(permission_code: str):
    def dependency(current_user: User = Depends(require_auth)) -> User:
        if not user_has_permission(current_user, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required permission")
        return current_user

    return dependency
