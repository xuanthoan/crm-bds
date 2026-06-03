from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, generate_refresh_token, hash_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserStatus
from app.services.audit_service import write_audit_log
from app.services.user_service import serialize_user

BLOCKED_STATUSES = {UserStatus.INACTIVE.value, UserStatus.SUSPENDED.value, UserStatus.RESIGNED.value}


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status in BLOCKED_STATUSES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active")
    return user


def create_refresh_token_record(db: Session, user: User) -> str:
    refresh_token = generate_refresh_token()
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token_record)
    return refresh_token


def login(db: Session, *, email: str, password: str, request: Request) -> dict:
    user = authenticate_user(db, email, password)
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token_record(db, user)
    user.last_login_at = datetime.now(UTC)
    write_audit_log(
        db,
        action="auth.login",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": serialize_user(user).model_dump(mode="json"),
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    token_record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    now = datetime.now(UTC)
    if token_record is None or token_record.revoked_at is not None or token_record.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = db.get(User, token_record.user_id)
    if user is None or user.deleted_at is not None or user.status in BLOCKED_STATUSES:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return {"access_token": create_access_token(str(user.id)), "refresh_token": refresh_token, "token_type": "bearer"}


def logout(db: Session, *, user: User, refresh_token: str | None, request: Request) -> None:
    if refresh_token:
        token_record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
        if token_record and token_record.user_id == user.id and token_record.revoked_at is None:
            token_record.revoked_at = datetime.now(UTC)
    write_audit_log(
        db,
        action="auth.logout",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()


def get_user_from_token(db: Session, user_id: str) -> User:
    try:
        parsed_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from exc
    user = db.get(User, parsed_user_id)
    if user is None or user.deleted_at is not None or user.status in BLOCKED_STATUSES:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authenticated user")
    return user
