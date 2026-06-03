from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


def serialize_role(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_system": role.is_system,
        "permissions": sorted(permission.code for permission in role.permissions),
        "created_at": role.created_at,
    }


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name)).all())


def get_role_or_404(db: Session, role_id: UUID) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


def create_role(db: Session, payload: RoleCreate) -> Role:
    if db.scalar(select(Role).where(Role.code == payload.code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists")
    role = Role(name=payload.name, code=payload.code, description=payload.description, is_system=payload.is_system)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role: Role, payload: RoleUpdate) -> Role:
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    db.commit()
    db.refresh(role)
    return role


def assign_permissions(db: Session, role: Role, permission_codes: list[str]) -> Role:
    permissions = list(db.scalars(select(Permission).where(Permission.code.in_(permission_codes))).all()) if permission_codes else []
    found_codes = {permission.code for permission in permissions}
    missing = set(permission_codes) - found_codes
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown permission codes: {', '.join(sorted(missing))}")
    role.permissions = permissions
    db.commit()
    db.refresh(role)
    return role
