import re
from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.team import Team
from app.models.user import User
from app.models.user_organization_membership import UserOrganizationMembership
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.organization import MembershipCreate, MembershipUpdate
from app.schemas.team import TeamCreate, TeamUpdate
from app.services.audit_service import write_audit_log
from app.services.user_service import get_user_by_id, user_role_codes

CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
ACTIVE_STATUSES = {"active", "inactive"}
MANAGER_ROLES = {"sales_manager", "director", "admin", "leader"}
LEADER_ROLES = {"leader", "sales_manager", "admin"}


def _user_summary(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "roles": sorted(user_role_codes(user))}


def _department_summary(department: Department | None) -> dict | None:
    if department is None:
        return None
    return {"id": department.id, "code": department.code, "name": department.name}


def _team_summary(team: Team | None) -> dict | None:
    if team is None:
        return None
    return {"id": team.id, "code": team.code, "name": team.name, "department_id": team.department_id}


def serialize_department(department: Department) -> dict:
    return {
        "id": department.id, "code": department.code, "name": department.name,
        "description": department.description, "manager": _user_summary(department.manager),
        "status": department.status,
        "team_count": sum(1 for team in department.teams if team.deleted_at is None),
        "member_count": len({membership.user_id for membership in department.memberships}),
        "created_at": department.created_at, "updated_at": department.updated_at,
    }


def serialize_team(team: Team) -> dict:
    return {
        "id": team.id, "code": team.code, "name": team.name, "description": team.description,
        "department": _department_summary(team.department), "leader": _user_summary(team.leader),
        "status": team.status, "member_count": len({membership.user_id for membership in team.memberships}),
        "created_at": team.created_at, "updated_at": team.updated_at,
    }


def serialize_membership(membership: UserOrganizationMembership) -> dict:
    return {
        "id": membership.id, "user": _user_summary(membership.user),
        "department": _department_summary(membership.department), "team": _team_summary(membership.team),
        "is_primary": membership.is_primary, "position_title": membership.position_title,
        "created_at": membership.created_at, "updated_at": membership.updated_at,
    }


def _meta(total: int, page: int, page_size: int) -> dict:
    return {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def _validate_status(value: str) -> None:
    if value not in ACTIVE_STATUSES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")


def _validate_responsible_user(db: Session, user_id: UUID | None, roles: set[str], message: str) -> User | None:
    if user_id is None:
        return None
    user = get_user_by_id(db, user_id)
    if user is None or user.status != "active" or not (user.is_superuser or user_role_codes(user) & roles):
        raise HTTPException(status_code=400, detail=message)
    return user


def list_departments(db: Session, *, page: int, page_size: int, search: str | None = None, item_status: str | None = None):
    query = select(Department).where(Department.deleted_at.is_(None))
    if search:
        query = query.where(Department.name.ilike(f"%{search}%") | Department.code.ilike(f"%{search}%"))
    if item_status:
        query = query.where(Department.status == item_status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Department.name).offset((page - 1) * page_size).limit(page_size)).unique())
    return items, _meta(total, page, page_size)


def get_department(db: Session, department_id: UUID) -> Department | None:
    return db.scalar(select(Department).where(Department.id == department_id, Department.deleted_at.is_(None)))


def create_department(db: Session, payload: DepartmentCreate, actor: User) -> Department:
    if not CODE_PATTERN.fullmatch(payload.code):
        raise HTTPException(status_code=400, detail="Mã phòng ban chỉ được dùng chữ thường, số và dấu gạch dưới")
    if db.scalar(select(Department.id).where(Department.code == payload.code)):
        raise HTTPException(status_code=409, detail="Mã phòng ban đã tồn tại")
    _validate_status(payload.status)
    _validate_responsible_user(db, payload.manager_id, MANAGER_ROLES, "Người quản lý không hợp lệ")
    department = Department(**payload.model_dump())
    db.add(department); db.flush()
    write_audit_log(db, action="departments.create", user_id=actor.id, entity_type="department", entity_id=str(department.id), after_data={"code": department.code, "name": department.name})
    db.commit(); db.refresh(department)
    return department


def update_department(db: Session, department: Department, payload: DepartmentUpdate, actor: User) -> Department:
    data = payload.model_dump(exclude_unset=True)
    if "status" in data: _validate_status(data["status"])
    if "manager_id" in data: _validate_responsible_user(db, data["manager_id"], MANAGER_ROLES, "Người quản lý không hợp lệ")
    before = {"name": department.name, "status": department.status, "manager_id": str(department.manager_id) if department.manager_id else None}
    for key, value in data.items(): setattr(department, key, value)
    write_audit_log(db, action="departments.update", user_id=actor.id, entity_type="department", entity_id=str(department.id), before_data=before, after_data={"name": department.name, "status": department.status, "manager_id": str(department.manager_id) if department.manager_id else None})
    db.commit(); db.refresh(department)
    return department


def delete_department(db: Session, department: Department, actor: User) -> None:
    active_teams = db.scalar(select(func.count(Team.id)).where(Team.department_id == department.id, Team.deleted_at.is_(None), Team.status == "active")) or 0
    if active_teams:
        raise HTTPException(status_code=409, detail="Không thể vô hiệu hóa phòng ban đang có nhóm hoạt động")
    department.status = "inactive"; department.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, action="departments.delete", user_id=actor.id, entity_type="department", entity_id=str(department.id), before_data={"status": "active"}, after_data={"status": "inactive"})
    db.commit()


def list_teams(db: Session, *, page: int, page_size: int, department_id: UUID | None = None, search: str | None = None, item_status: str | None = None):
    query = select(Team).where(Team.deleted_at.is_(None))
    if department_id: query = query.where(Team.department_id == department_id)
    if search: query = query.where(Team.name.ilike(f"%{search}%") | Team.code.ilike(f"%{search}%"))
    if item_status: query = query.where(Team.status == item_status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Team.name).offset((page - 1) * page_size).limit(page_size)).unique())
    return items, _meta(total, page, page_size)


def get_team(db: Session, team_id: UUID) -> Team | None:
    return db.scalar(select(Team).where(Team.id == team_id, Team.deleted_at.is_(None)))


def _active_department(db: Session, department_id: UUID) -> Department:
    department = get_department(db, department_id)
    if department is None or department.status != "active":
        raise HTTPException(status_code=400, detail="Phòng ban không hợp lệ")
    return department


def create_team(db: Session, payload: TeamCreate, actor: User) -> Team:
    if not CODE_PATTERN.fullmatch(payload.code): raise HTTPException(status_code=400, detail="Mã nhóm chỉ được dùng chữ thường, số và dấu gạch dưới")
    if db.scalar(select(Team.id).where(Team.code == payload.code)): raise HTTPException(status_code=409, detail="Mã nhóm đã tồn tại")
    _active_department(db, payload.department_id); _validate_status(payload.status)
    _validate_responsible_user(db, payload.leader_id, LEADER_ROLES, "Leader không hợp lệ")
    team = Team(**payload.model_dump()); db.add(team); db.flush()
    write_audit_log(db, action="teams.create", user_id=actor.id, entity_type="team", entity_id=str(team.id), after_data={"code": team.code, "name": team.name})
    db.commit(); db.refresh(team); return team


def update_team(db: Session, team: Team, payload: TeamUpdate, actor: User) -> Team:
    data = payload.model_dump(exclude_unset=True)
    if "department_id" in data: _active_department(db, data["department_id"])
    if "status" in data: _validate_status(data["status"])
    if "leader_id" in data: _validate_responsible_user(db, data["leader_id"], LEADER_ROLES, "Leader không hợp lệ")
    before = {"name": team.name, "status": team.status, "department_id": str(team.department_id), "leader_id": str(team.leader_id) if team.leader_id else None}
    for key, value in data.items(): setattr(team, key, value)
    write_audit_log(db, action="teams.update", user_id=actor.id, entity_type="team", entity_id=str(team.id), before_data=before, after_data={"name": team.name, "status": team.status, "department_id": str(team.department_id), "leader_id": str(team.leader_id) if team.leader_id else None})
    db.commit(); db.refresh(team); return team


def delete_team(db: Session, team: Team, actor: User) -> None:
    team.status = "inactive"; team.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, action="teams.delete", user_id=actor.id, entity_type="team", entity_id=str(team.id), before_data={"status": "active"}, after_data={"status": "inactive"})
    db.commit()


def _normalize_membership(db: Session, department_id: UUID | None, team_id: UUID | None) -> tuple[UUID, UUID | None]:
    team = get_team(db, team_id) if team_id else None
    if team_id and (team is None or team.status != "active"): raise HTTPException(status_code=400, detail="Thông tin phân bổ nhân sự không hợp lệ")
    if team:
        if department_id and department_id != team.department_id: raise HTTPException(status_code=400, detail="Nhóm không thuộc phòng ban đã chọn")
        department_id = team.department_id
    if department_id is None: raise HTTPException(status_code=400, detail="Thông tin phân bổ nhân sự không hợp lệ")
    _active_department(db, department_id)
    return department_id, team_id


def list_memberships(db: Session, *, page: int, page_size: int, department_id: UUID | None = None, team_id: UUID | None = None, user_id: UUID | None = None):
    query = select(UserOrganizationMembership)
    if department_id: query = query.where(UserOrganizationMembership.department_id == department_id)
    if team_id: query = query.where(UserOrganizationMembership.team_id == team_id)
    if user_id: query = query.where(UserOrganizationMembership.user_id == user_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(UserOrganizationMembership.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
    return items, _meta(total, page, page_size)


def get_membership(db: Session, membership_id: UUID) -> UserOrganizationMembership | None:
    return db.get(UserOrganizationMembership, membership_id)


def create_membership(db: Session, payload: MembershipCreate, actor: User) -> UserOrganizationMembership:
    user = get_user_by_id(db, payload.user_id)
    if user is None or user.status != "active": raise HTTPException(status_code=400, detail="Thông tin phân bổ nhân sự không hợp lệ")
    department_id, team_id = _normalize_membership(db, payload.department_id, payload.team_id)
    if payload.is_primary:
        db.query(UserOrganizationMembership).filter(UserOrganizationMembership.user_id == payload.user_id).update({"is_primary": False})
    duplicate = db.scalar(select(UserOrganizationMembership.id).where(UserOrganizationMembership.user_id == payload.user_id, UserOrganizationMembership.department_id == department_id, UserOrganizationMembership.team_id == team_id))
    if duplicate: raise HTTPException(status_code=409, detail="Thông tin phân bổ nhân sự đã tồn tại")
    membership = UserOrganizationMembership(user_id=payload.user_id, department_id=department_id, team_id=team_id, is_primary=payload.is_primary, position_title=payload.position_title)
    db.add(membership); db.flush()
    write_audit_log(db, action="memberships.create", user_id=actor.id, entity_type="organization_membership", entity_id=str(membership.id), after_data={"user_id": str(payload.user_id), "department_id": str(department_id), "team_id": str(team_id) if team_id else None})
    db.commit(); db.refresh(membership); return membership


def update_membership(db: Session, membership: UserOrganizationMembership, payload: MembershipUpdate, actor: User) -> UserOrganizationMembership:
    data = payload.model_dump(exclude_unset=True)
    department_id, team_id = _normalize_membership(db, data.get("department_id", membership.department_id), data.get("team_id", membership.team_id))
    if data.get("is_primary"):
        db.query(UserOrganizationMembership).filter(UserOrganizationMembership.user_id == membership.user_id, UserOrganizationMembership.id != membership.id).update({"is_primary": False})
    before = {"department_id": str(membership.department_id), "team_id": str(membership.team_id) if membership.team_id else None, "is_primary": membership.is_primary}
    membership.department_id = department_id; membership.team_id = team_id
    for key in ("is_primary", "position_title"):
        if key in data: setattr(membership, key, data[key])
    write_audit_log(db, action="memberships.update", user_id=actor.id, entity_type="organization_membership", entity_id=str(membership.id), before_data=before, after_data={"department_id": str(department_id), "team_id": str(team_id) if team_id else None, "is_primary": membership.is_primary})
    db.commit(); db.refresh(membership); return membership


def delete_membership(db: Session, membership: UserOrganizationMembership, actor: User) -> None:
    write_audit_log(db, action="memberships.delete", user_id=actor.id, entity_type="organization_membership", entity_id=str(membership.id), before_data={"user_id": str(membership.user_id), "department_id": str(membership.department_id), "team_id": str(membership.team_id) if membership.team_id else None})
    db.delete(membership); db.commit()


def get_user_primary_membership(db: Session, user_id: UUID) -> UserOrganizationMembership | None:
    return db.scalar(select(UserOrganizationMembership).where(UserOrganizationMembership.user_id == user_id).order_by(UserOrganizationMembership.is_primary.desc(), UserOrganizationMembership.created_at.asc()).limit(1))


def get_user_team_ids(db: Session, user_id: UUID) -> set[UUID]:
    member_ids = set(db.scalars(select(UserOrganizationMembership.team_id).where(UserOrganizationMembership.user_id == user_id, UserOrganizationMembership.team_id.is_not(None))))
    led_ids = set(db.scalars(select(Team.id).where(Team.leader_id == user_id, Team.status == "active", Team.deleted_at.is_(None))))
    return member_ids | led_ids


def get_user_department_ids(db: Session, user_id: UUID) -> set[UUID]:
    member_ids = set(db.scalars(select(UserOrganizationMembership.department_id).where(UserOrganizationMembership.user_id == user_id, UserOrganizationMembership.department_id.is_not(None))))
    managed_ids = set(db.scalars(select(Department.id).where(Department.manager_id == user_id, Department.status == "active", Department.deleted_at.is_(None))))
    return member_ids | managed_ids


def get_subordinate_user_ids_for_team_scope(db: Session, current_user: User) -> set[UUID]:
    team_ids = set(db.scalars(select(Team.id).where(Team.leader_id == current_user.id, Team.status == "active", Team.deleted_at.is_(None))))
    users = set(db.scalars(select(UserOrganizationMembership.user_id).where(UserOrganizationMembership.team_id.in_(team_ids)))) if team_ids else set()
    return users | {current_user.id}


def get_subordinate_user_ids_for_department_scope(db: Session, current_user: User) -> set[UUID]:
    department_ids = set(db.scalars(select(Department.id).where(Department.manager_id == current_user.id, Department.status == "active", Department.deleted_at.is_(None))))
    if not department_ids:
        primary = get_user_primary_membership(db, current_user.id)
        if primary and primary.department_id:
            led = db.scalar(select(Team.id).where(Team.leader_id == current_user.id, Team.department_id == primary.department_id, Team.deleted_at.is_(None)))
            if led: department_ids.add(primary.department_id)
    users = set(db.scalars(select(UserOrganizationMembership.user_id).where(UserOrganizationMembership.department_id.in_(department_ids)))) if department_ids else set()
    return users | {current_user.id}


def get_accessible_user_ids_for_lead_scope(db: Session, current_user: User, permission_type: str) -> set[UUID]:
    if permission_type == "all":
        return set(db.scalars(select(User.id).where(User.status == "active", User.deleted_at.is_(None))))
    if permission_type == "department": return get_subordinate_user_ids_for_department_scope(db, current_user)
    if permission_type == "team": return get_subordinate_user_ids_for_team_scope(db, current_user)
    return {current_user.id}
