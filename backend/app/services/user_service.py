from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit_service import write_audit_log


def get_user_permissions(user: User) -> list[str]:
    if user.is_superuser:
        permissions = {permission.code for role in user.roles for permission in role.permissions}
        return sorted(permissions)
    permissions = {permission.code for role in user.roles for permission in role.permissions}
    return sorted(permissions)


def user_has_permission(user: User, permission_code: str) -> bool:
    return user.is_superuser or permission_code in get_user_permissions(user)


def serialize_user(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        is_superuser=user.is_superuser,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=sorted(role.code for role in user.roles),
        permissions=get_user_permissions(user),
    )


def get_user_by_id(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def list_users(db: Session, page: int = 1, page_size: int = 20) -> tuple[list[User], int]:
    stmt = select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    users = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return list(users), total


def resolve_roles(db: Session, role_codes: list[str]) -> list[Role]:
    if not role_codes:
        return []
    roles = db.scalars(select(Role).where(Role.code.in_(role_codes))).all()
    found_codes = {role.code for role in roles}
    missing = sorted(set(role_codes) - found_codes)
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown roles: {', '.join(missing)}")
    return list(roles)


def create_user(db: Session, payload: UserCreate, actor: User) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        phone=payload.phone,
        hashed_password=get_password_hash(payload.password),
        status=payload.status,
        roles=resolve_roles(db, payload.role_codes),
    )
    db.add(user)
    db.flush()
    write_audit_log(db, action="users.create", user_id=actor.id, entity_type="user", entity_id=str(user.id), after_data={"email": user.email})
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate, actor: User) -> User:
    before = {"email": user.email, "full_name": user.full_name, "phone": user.phone, "status": user.status, "roles": [role.code for role in user.roles]}
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.status is not None:
        user.status = payload.status
    if payload.role_codes is not None:
        user.roles = resolve_roles(db, payload.role_codes)
    db.flush()
    after = {"email": user.email, "full_name": user.full_name, "phone": user.phone, "status": user.status, "roles": [role.code for role in user.roles]}
    write_audit_log(db, action="users.update", user_id=actor.id, entity_type="user", entity_id=str(user.id), before_data=before, after_data=after)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User, actor: User) -> User:
    before = {"status": user.status}
    user.status = UserStatus.INACTIVE.value
    write_audit_log(db, action="users.deactivate", user_id=actor.id, entity_type="user", entity_id=str(user.id), before_data=before, after_data={"status": user.status})
    db.commit()
    db.refresh(user)
    return user
