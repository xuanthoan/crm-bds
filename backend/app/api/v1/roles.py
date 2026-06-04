from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_permission
from app.schemas.role import RoleCreate, RolePermissionAssign, RoleUpdate
from app.services.role_service import assign_permissions, create_role, get_role_or_404, list_roles, serialize_role, serialize_role_detail, update_role

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
def get_roles(db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.view"))):
    return success_response(data=[serialize_role(role) for role in list_roles(db)], message="Roles retrieved")


@router.get("/{role_id}")
def get_role(role_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.view"))):
    return success_response(data=serialize_role_detail(get_role_or_404(db, role_id)), message="Role retrieved")


@router.post("")
def post_role(payload: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.create"))):
    role = create_role(db, payload, current_user)
    return success_response(data=serialize_role_detail(role), message="Role created")


@router.put("/{role_id}")
def put_role(role_id: UUID, payload: RoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.update"))):
    role = update_role(db, get_role_or_404(db, role_id), payload, current_user)
    return success_response(data=serialize_role_detail(role), message="Role updated")


@router.post("/{role_id}/permissions")
def post_role_permissions(role_id: UUID, payload: RolePermissionAssign, db: Session = Depends(get_db), current_user: User = Depends(require_permission("roles.assign_permissions"))):
    role = assign_permissions(db, get_role_or_404(db, role_id), payload, current_user)
    return success_response(data=serialize_role_detail(role), message="Role permissions assigned")
