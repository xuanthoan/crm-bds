from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.permission import Permission
from app.models.role import Role
from app.permissions.dependencies import require_permission
from app.schemas.role import RoleCreate, RolePermissionsUpdate, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


def serialize_role(role: Role) -> dict:
    return {
        "id": str(role.id),
        "name": role.name,
        "code": role.code,
        "description": role.description,
        "is_system": role.is_system,
        "created_at": role.created_at.isoformat(),
        "updated_at": role.updated_at.isoformat(),
        "permissions": sorted(permission.code for permission in role.permissions),
    }


def get_role_or_404(db: Session, role_id: UUID) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.get("")
def list_roles(current_user=Depends(require_permission("roles.view")), db: Session = Depends(get_db)):
    roles = db.scalars(select(Role).order_by(Role.name)).all()
    return success_response(data=[serialize_role(role) for role in roles], message="Roles retrieved")


@router.post("")
def create_role(payload: RoleCreate, current_user=Depends(require_permission("roles.create")), db: Session = Depends(get_db)):
    existing = db.scalar(select(Role).where(Role.code == payload.code))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists")
    role = Role(name=payload.name, code=payload.code, description=payload.description, is_system=False)
    db.add(role)
    db.commit()
    db.refresh(role)
    return success_response(data=serialize_role(role), message="Role created")


@router.put("/{role_id}")
def update_role(role_id: UUID, payload: RoleUpdate, current_user=Depends(require_permission("roles.update")), db: Session = Depends(get_db)):
    role = get_role_or_404(db, role_id)
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    db.commit()
    db.refresh(role)
    return success_response(data=serialize_role(role), message="Role updated")


@router.post("/{role_id}/permissions")
def assign_permissions(role_id: UUID, payload: RolePermissionsUpdate, current_user=Depends(require_permission("roles.assign_permissions")), db: Session = Depends(get_db)):
    role = get_role_or_404(db, role_id)
    permissions = db.scalars(select(Permission).where(Permission.code.in_(payload.permission_codes))).all()
    found_codes = {permission.code for permission in permissions}
    missing = sorted(set(payload.permission_codes) - found_codes)
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown permissions: {', '.join(missing)}")
    role.permissions = list(permissions)
    db.commit()
    db.refresh(role)
    return success_response(data=serialize_role(role), message="Role permissions assigned")
