from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserResetPassword, UserUpdate
from app.services.audit_service import write_audit_log

VALID_STATUSES = {"active", "inactive", "suspended", "resigned"}


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))


def user_permission_codes(user: User) -> list[str]:
    return sorted({permission.code for role in user.roles for permission in role.permissions})


def user_role_codes(user: User) -> list[str]:
    return sorted({role.code for role in user.roles})


def user_role_code_set(user: User) -> set[str]:
    """Return role codes as a set for safe membership and intersection checks."""
    return set(user_role_codes(user) or [])


def _serialize_role(role: Role) -> dict:
    return {"id": role.id, "code": role.code, "name": role.name}


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "status": user.status,
        "is_superuser": user.is_superuser,
        "last_login_at": user.last_login_at,
        "roles": sorted([_serialize_role(role) for role in user.roles], key=lambda item: item["code"]),
        "created_at": user.created_at,
        "updated_at": user.updated_at,
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


def list_users(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    user_status: str | None = None,
    role_code: str | None = None,
) -> tuple[list[User], dict]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    query = select(User).where(User.deleted_at.is_(None))
    count_query = select(func.count(func.distinct(User.id))).select_from(User).where(User.deleted_at.is_(None))

    if search:
        term = f"%{search.strip()}%"
        condition = or_(User.email.ilike(term), User.full_name.ilike(term), User.phone.ilike(term))
        query = query.where(condition)
        count_query = count_query.where(condition)
    if user_status:
        query = query.where(User.status == user_status)
        count_query = count_query.where(User.status == user_status)
    if role_code:
        query = query.join(User.roles).where(Role.code == role_code)
        count_query = count_query.join(User.roles).where(Role.code == role_code)

    total = db.scalar(count_query) or 0
    offset = (page - 1) * page_size
    users = list(db.scalars(query.order_by(User.created_at.desc()).offset(offset).limit(page_size)).unique().all())
    meta = {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}
    return users, meta


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
    roles = _get_roles_by_codes(db, payload.role_codes)
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        phone=payload.phone,
        status=payload.status,
        hashed_password=get_password_hash(payload.password),
    )
    user.roles = roles
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        action="users.create",
        user_id=actor.id,
        entity_type="users",
        entity_id=str(user.id),
        after_data={"email": user.email, "full_name": user.full_name, "status": user.status, "roles": payload.role_codes},
    )
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
    after_data = {"full_name": user.full_name, "phone": user.phone, "status": user.status, "roles": user_role_codes(user)}
    write_audit_log(db, action="users.update", user_id=actor.id, entity_type="users", entity_id=str(user.id), before_data=before_data, after_data=after_data)
    db.commit()
    db.refresh(user)
    return user


def _active_admin_count(db: Session) -> int:
    return db.scalar(select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(User.deleted_at.is_(None), User.status == "active", Role.code == "admin")) or 0


def deactivate_user(db: Session, user: User, actor: User) -> User:
    if user.id == actor.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account")
    if "admin" in user_role_codes(user) and user.status == "active" and _active_admin_count(db) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate the last active admin user")
    before_data = {"status": user.status, "roles": user_role_codes(user)}
    user.status = "inactive"
    write_audit_log(db, action="users.deactivate", user_id=actor.id, entity_type="users", entity_id=str(user.id), before_data=before_data, after_data={"status": user.status})
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user: User, payload: UserResetPassword, actor: User) -> None:
    user.hashed_password = get_password_hash(payload.new_password)
    write_audit_log(db, action="users.reset_password", user_id=actor.id, entity_type="users", entity_id=str(user.id), after_data={"email": user.email})
    db.commit()
