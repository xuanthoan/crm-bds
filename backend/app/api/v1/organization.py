from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import get_user_permissions, require_auth, require_permission
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.organization import MembershipCreate, MembershipUpdate
from app.schemas.team import TeamCreate, TeamUpdate
from app.services.user_service import user_role_codes
from app.services.organization_service import (
    create_department, create_membership, create_team, delete_department, delete_membership, delete_team,
    get_department, get_membership, get_team, list_departments, list_memberships, list_teams,
    serialize_department, serialize_membership, serialize_team, update_department, update_membership, update_team,
)

departments_router = APIRouter(prefix="/departments", tags=["organization"])
teams_router = APIRouter(prefix="/teams", tags=["organization"])
organization_router = APIRouter(prefix="/organization", tags=["organization"])

def _require_read(user: User) -> None:
    if not user.is_superuser and not ({"users.view", "settings.manage_master_data", "leads.view.own", "leads.view.team", "leads.view.department", "leads.view.all"} & set(get_user_permissions(user))):
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")

def _department(db: Session, item_id: UUID):
    item = get_department(db, item_id)
    if item is None: raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")
    return item

def _team(db: Session, item_id: UUID):
    item = get_team(db, item_id)
    if item is None: raise HTTPException(status_code=404, detail="Không tìm thấy nhóm")
    return item

@departments_router.get("")
def departments(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100), search: str | None = None, status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db), user: User = Depends(require_auth)):
    _require_read(user); items, meta = list_departments(db, page=page, page_size=page_size, search=search, item_status=status_filter)
    return success_response(data=[serialize_department(item) for item in items], message="Departments retrieved", meta=meta)

@departments_router.post("")
def post_department(payload: DepartmentCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("settings.manage_master_data"))):
    return success_response(data=serialize_department(create_department(db, payload, user)), message="Department created")

@departments_router.get("/{department_id}")
def department_detail(department_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_auth)):
    _require_read(user); return success_response(data=serialize_department(_department(db, department_id)), message="Department retrieved")

@departments_router.put("/{department_id}")
def put_department(department_id: UUID, payload: DepartmentUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("settings.manage_master_data"))):
    return success_response(data=serialize_department(update_department(db, _department(db, department_id), payload, user)), message="Department updated")

@departments_router.delete("/{department_id}")
def remove_department(department_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_permission("settings.manage_master_data"))):
    delete_department(db, _department(db, department_id), user); return success_response(data=None, message="Department deactivated")

@teams_router.get("")
def teams(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100), department_id: UUID | None = None, search: str | None = None, status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db), user: User = Depends(require_auth)):
    _require_read(user); items, meta = list_teams(db, page=page, page_size=page_size, department_id=department_id, search=search, item_status=status_filter)
    return success_response(data=[serialize_team(item) for item in items], message="Teams retrieved", meta=meta)

@teams_router.post("")
def post_team(payload: TeamCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("settings.manage_master_data"))):
    return success_response(data=serialize_team(create_team(db, payload, user)), message="Team created")

@teams_router.get("/{team_id}")
def team_detail(team_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_auth)):
    _require_read(user); return success_response(data=serialize_team(_team(db, team_id)), message="Team retrieved")

@teams_router.put("/{team_id}")
def put_team(team_id: UUID, payload: TeamUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("settings.manage_master_data"))):
    return success_response(data=serialize_team(update_team(db, _team(db, team_id), payload, user)), message="Team updated")

@teams_router.delete("/{team_id}")
def remove_team(team_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_permission("settings.manage_master_data"))):
    delete_team(db, _team(db, team_id), user); return success_response(data=None, message="Team deactivated")

@organization_router.get("/memberships")
def memberships(page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100), department_id: UUID | None = None, team_id: UUID | None = None, user_id: UUID | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("users.view"))):
    items, meta = list_memberships(db, page=page, page_size=page_size, department_id=department_id, team_id=team_id, user_id=user_id)
    return success_response(data=[serialize_membership(item) for item in items], message="Memberships retrieved", meta=meta)

@organization_router.post("/memberships")
def post_membership(payload: MembershipCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("users.update"))):
    return success_response(data=serialize_membership(create_membership(db, payload, user)), message="Membership created")

@organization_router.put("/memberships/{membership_id}")
def put_membership(membership_id: UUID, payload: MembershipUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("users.update"))):
    membership = get_membership(db, membership_id)
    if membership is None: raise HTTPException(status_code=404, detail="Không tìm thấy phân bổ nhân sự")
    return success_response(data=serialize_membership(update_membership(db, membership, payload, user)), message="Membership updated")

@organization_router.delete("/memberships/{membership_id}")
def remove_membership(membership_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_permission("users.update"))):
    membership = get_membership(db, membership_id)
    if membership is None: raise HTTPException(status_code=404, detail="Không tìm thấy phân bổ nhân sự")
    delete_membership(db, membership, user); return success_response(data=None, message="Membership deleted")


@organization_router.get("/lead-scope-users")
def lead_scope_users(db: Session = Depends(get_db), user: User = Depends(require_auth)):
    from sqlalchemy import select
    from app.leads.constants import SALES_ROLE_CODES
    from app.models.user import User as UserModel
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    permissions = set(get_user_permissions(user))
    if user.is_superuser or "leads.assign.all" in permissions or "leads.view.all" in permissions:
        ids = get_accessible_user_ids_for_lead_scope(db, user, "all")
    elif "leads.view.department" in permissions:
        ids = get_accessible_user_ids_for_lead_scope(db, user, "department")
    elif "leads.assign.team" in permissions or "leads.view.team" in permissions:
        ids = get_accessible_user_ids_for_lead_scope(db, user, "team")
    else:
        ids = {user.id}
    users = list(db.scalars(select(UserModel).where(UserModel.id.in_(ids), UserModel.status == "active", UserModel.deleted_at.is_(None))).unique())
    data = [{"id": item.id, "full_name": item.full_name, "email": item.email, "roles": [{"id": role.id, "code": role.code, "name": role.name} for role in item.roles]} for item in users if item.is_superuser or user_role_codes(item) & SALES_ROLE_CODES]
    return success_response(data=data, message="Lead scope users retrieved")
