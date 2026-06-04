import re
from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RolePermissionAssign, RoleUpdate
from app.services.audit_service import write_audit_log

ROLE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _permission_codes(role: Role) -> list[str]:
    return sorted(permission.code for permission in role.permissions)


def _permissions_by_module(role: Role) -> list[dict]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for permission in sorted(role.permissions, key=lambda item: (item.module, item.code)):
        grouped[permission.module].append(permission.code)
    return [{"module": module, "permission_codes": codes} for module, codes in grouped.items()]


def serialize_role(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_system": role.is_system,
        "permission_count": len(role.permissions),
        "created_at": role.created_at,
        "updated_at": role.updated_at,
    }


def serialize_role_detail(role: Role) -> dict:
    data = serialize_role(role)
    data["permissions"] = _permissions_by_module(role)
    data["permission_codes"] = _permission_codes(role)
    return data


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name)).all())


def get_role_or_404(db: Session, role_id: UUID) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


def _validate_role_code(code: str) -> None:
    if not ROLE_CODE_PATTERN.fullmatch(code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role code must be lowercase snake_case")


def _get_permissions_by_codes(db: Session, permission_codes: list[str]) -> list[Permission]:
    if not permission_codes:
        return []
    permissions = list(db.scalars(select(Permission).where(Permission.code.in_(permission_codes))).all())
    found_codes = {permission.code for permission in permissions}
    missing = set(permission_codes) - found_codes
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown permission codes: {', '.join(sorted(missing))}")
    return permissions


def create_role(db: Session, payload: RoleCreate, actor: User) -> Role:
    _validate_role_code(payload.code)
    if db.scalar(select(Role).where(Role.code == payload.code)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists")
    role = Role(name=payload.name, code=payload.code, description=payload.description, is_system=payload.is_system)
    role.permissions = _get_permissions_by_codes(db, payload.permission_codes)
    db.add(role)
    db.flush()
    write_audit_log(
        db,
        action="roles.create",
        user_id=actor.id,
        entity_type="roles",
        entity_id=str(role.id),
        after_data={"name": role.name, "code": role.code, "permissions": payload.permission_codes},
    )
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role: Role, payload: RoleUpdate, actor: User) -> Role:
    before_data = {"name": role.name, "code": role.code, "description": role.description, "permissions": _permission_codes(role)}
    if payload.code is not None and payload.code != role.code:
        if role.is_system:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change code for system roles")
        _validate_role_code(payload.code)
        if db.scalar(select(Role).where(Role.code == payload.code, Role.id != role.id)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists")
        role.code = payload.code
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.permission_codes is not None:
        role.permissions = _get_permissions_by_codes(db, payload.permission_codes)
    after_data = {"name": role.name, "code": role.code, "description": role.description, "permissions": _permission_codes(role)}
    write_audit_log(db, action="roles.update", user_id=actor.id, entity_type="roles", entity_id=str(role.id), before_data=before_data, after_data=after_data)
    db.commit()
    db.refresh(role)
    return role


def assign_permissions(db: Session, role: Role, payload: RolePermissionAssign, actor: User) -> Role:
    before_data = {"permissions": _permission_codes(role)}
    role.permissions = _get_permissions_by_codes(db, payload.permission_codes)
    after_data = {"permissions": _permission_codes(role)}
    write_audit_log(db, action="roles.assign_permissions", user_id=actor.id, entity_type="roles", entity_id=str(role.id), before_data=before_data, after_data=after_data)
    db.commit()
    db.refresh(role)
    return role
