from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit_service import write_audit_log

VALID_STATUSES = {"active", "inactive", "suspended", "resigned"}


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))


def user_permission_codes(user: User) -> list[str]:
    if user.is_superuser:
        codes = {permission.code for role in user.roles for permission in role.permissions}
        return sorted(codes)
    return sorted({permission.code for role in user.roles for permission in role.permissions})


def user_role_codes(user: User) -> list[str]:
    return sorted({role.code for role in user.roles})


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "status": user.status,
        "is_superuser": user.is_superuser,
        "last_login_at": user.last_login_at,
        "roles": user_role_codes(user),
        "permissions": user_permission_codes(user),
        "created_at": user.created_at,
    }


def serialize_current_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "status": user.status,
        "roles": user_role_codes(user),
        "permissions": user_permission_codes(user),
        "is_superuser": user.is_superuser,
    }


def list_users(db: Session, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
    query = select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
    users = list(db.scalars(query.offset(skip).limit(limit)).all())
    total = db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None))) or 0
    return users, total


def _get_roles_by_codes(db: Session, role_codes: list[str]) -> list[Role]:
    if not role_codes:
        return []
    roles = list(db.scalars(select(Role).where(Role.code.in_(role_codes))).all())
    found_codes = {role.code for role in roles}
    missing = set(role_codes) - found_codes
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown role codes: {', '.join(sorted(missing))}")
    return roles


def create_user(db: Session, payload: UserCreate, actor: User) -> User:
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user status")
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        phone=payload.phone,
        status=payload.status,
        hashed_password=get_password_hash(payload.password),
    )
    user.roles = _get_roles_by_codes(db, payload.role_codes)
    db.add(user)
    db.flush()
    write_audit_log(db, action="users.create", user_id=actor.id, entity_type="users", entity_id=str(user.id), after_data={"email": user.email, "roles": payload.role_codes})
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate, actor: User) -> User:
    before_data = {"full_name": user.full_name, "phone": user.phone, "status": user.status, "roles": user_role_codes(user)}
    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user status")
        user.status = payload.status
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.role_codes is not None:
        user.roles = _get_roles_by_codes(db, payload.role_codes)
    write_audit_log(db, action="users.update", user_id=actor.id, entity_type="users", entity_id=str(user.id), before_data=before_data, after_data={"full_name": user.full_name, "phone": user.phone, "status": user.status, "roles": user_role_codes(user)})
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User, actor: User) -> User:
    user.status = "inactive"
    write_audit_log(db, action="users.deactivate", user_id=actor.id, entity_type="users", entity_id=str(user.id), after_data={"status": user.status})
    db.commit()
    db.refresh(user)
    return user
