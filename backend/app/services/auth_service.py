import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.audit_service import write_audit_log
from app.services.user_service import get_user_by_email, serialize_current_user


def _client_ip(request: Request | None) -> str | None:
    return request.client.host if request and request.client else None


def _user_agent(request: Request | None) -> str | None:
    return request.headers.get("user-agent") if request else None


def create_refresh_token(db: Session, user: User) -> str:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(48)
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_token)
    return raw_token


def login(db: Session, email: str, password: str, request: Request | None = None) -> dict:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active")

    user.last_login_at = datetime.now(timezone.utc)
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(db, user)
    write_audit_log(db, action="auth.login", user_id=user.id, ip_address=_client_ip(request), user_agent=_user_agent(request))
    db.commit()
    db.refresh(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": serialize_current_user(user),
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    now = datetime.now(timezone.utc)
    if not stored or stored.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    user = stored.user
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active")
    access_token = create_access_token(str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": serialize_current_user(user),
    }


def logout(db: Session, user: User, refresh_token: str | None = None, request: Request | None = None) -> None:
    if refresh_token:
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token), RefreshToken.user_id == user.id))
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
    write_audit_log(db, action="auth.logout", user_id=user.id, ip_address=_client_ip(request), user_agent=_user_agent(request))
    db.commit()
