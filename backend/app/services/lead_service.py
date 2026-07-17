from datetime import date, datetime, time, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.leads.constants import (
    ASSIGN_PERMISSIONS,
    CONTACT_STATUSES,
    LEAD_PRIORITIES,
    LEAD_STATUSES,
    SALES_ROLE_CODES,
    UPDATE_PERMISSIONS,
    VIEW_PERMISSIONS,
)
from app.models.lead import Lead
from app.models.customer import Customer
from app.models.customer_activity import CustomerActivity
from app.models.role import Role
from app.models.user import User
from app.models.user_organization_membership import UserOrganizationMembership
from app.permissions.dependencies import get_user_permissions
from app.schemas.lead import LeadAssign, LeadCreate, LeadStatusUpdate, LeadUpdate
from app.services.audit_service import write_audit_log
from app.services.duplicate_lead_service import detect_duplicate_customer
from app.services.lead_activity_service import create_activity_record, serialize_activity
from app.services.phone_service import normalize_phone
from app.services.user_service import get_user_by_id, user_role_code_set


def _permission_set(user: User) -> set[str]:
    return set(get_user_permissions(user))


def _has_any(user: User, permissions: set[str]) -> bool:
    return user.is_superuser or bool(_permission_set(user) & permissions)


def _own_scope_condition(user: User):
    return or_(Lead.owner_id == user.id, Lead.created_by_id == user.id)


def _scope_for_permissions(permissions: set[str], prefix: str) -> str | None:
    for scope in ("all", "department", "team", "own"):
        if f"{prefix}.{scope}" in permissions:
            return scope
    return None


def _scope_condition(db: Session, user: User, scope: str):
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    ids = get_accessible_user_ids_for_lead_scope(db, user, scope)
    return or_(Lead.owner_id.in_(ids), Lead.created_by_id.in_(ids))


def apply_view_scope(db: Session, query, user: User):
    permissions = _permission_set(user)
    if user.is_superuser or "leads.view.all" in permissions:
        return query
    scope = _scope_for_permissions(permissions, "leads.view")
    if scope:
        return query.where(_scope_condition(db, user, scope))
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thực hiện thao tác này")


def can_view_lead(db: Session, user: User, lead: Lead) -> bool:
    permissions = _permission_set(user)
    if user.is_superuser or "leads.view.all" in permissions:
        return True
    scope = _scope_for_permissions(permissions, "leads.view")
    if not scope:
        return False
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    ids = get_accessible_user_ids_for_lead_scope(db, user, scope)
    return lead.owner_id in ids or lead.created_by_id in ids


def can_update_lead(db: Session, user: User, lead: Lead) -> bool:
    permissions = _permission_set(user)
    if user.is_superuser or "leads.update.all" in permissions:
        return True
    scope = "team" if "leads.update.team" in permissions else "own" if "leads.update.own" in permissions else None
    if not scope:
        return False
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    ids = get_accessible_user_ids_for_lead_scope(db, user, scope)
    return lead.owner_id in ids or lead.created_by_id in ids


def can_assign_lead(db: Session, user: User, lead: Lead) -> bool:
    permissions = _permission_set(user)
    if user.is_superuser or "leads.assign.all" in permissions:
        return True
    if "leads.assign.team" not in permissions:
        return False
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    ids = get_accessible_user_ids_for_lead_scope(db, user, "team")
    return lead.owner_id in ids or lead.created_by_id in ids


def require_view_permission(user: User) -> None:
    if not _has_any(user, VIEW_PERMISSIONS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thực hiện thao tác này")


def require_update_access(db: Session, user: User, lead: Lead) -> None:
    if not _has_any(user, UPDATE_PERMISSIONS) or not can_update_lead(db, user, lead):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập lead này")


def require_assign_access(db: Session, user: User, lead: Lead) -> None:
    if not _has_any(user, ASSIGN_PERMISSIONS) or not can_assign_lead(db, user, lead):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thực hiện thao tác này")


def _validate_target_owner_scope(db: Session, actor: User, owner: User) -> None:
    permissions = _permission_set(actor)
    if actor.is_superuser or "leads.assign.all" in permissions:
        return
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    if "leads.assign.team" not in permissions or owner.id not in get_accessible_user_ids_for_lead_scope(db, actor, "team"):
        raise HTTPException(status_code=403, detail="Người phụ trách không nằm trong phạm vi bạn được phân công")

def _validate_ranges(budget_min: Decimal | None, budget_max: Decimal | None, area_min: Decimal | None, area_max: Decimal | None) -> None:
    if budget_min is not None and budget_max is not None and budget_min > budget_max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ngân sách tối thiểu không được lớn hơn ngân sách tối đa")
    if area_min is not None and area_max is not None and area_min > area_max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Diện tích tối thiểu không được lớn hơn diện tích tối đa")


def _validate_priority(priority: str | None) -> None:
    if priority is not None and priority not in LEAD_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mức độ ưu tiên không hợp lệ")


def _ensure_phone_unique(db: Session, phone_primary: str, phone_secondary: str | None, exclude_id: UUID | None = None) -> None:
    phones = {phone for phone in (phone_primary, phone_secondary) if phone}
    if len(phones) != len([phone for phone in (phone_primary, phone_secondary) if phone]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Số điện thoại đã tồn tại trong hệ thống")
    query = select(Lead.id).where(
        Lead.deleted_at.is_(None),
        or_(Lead.phone_primary.in_(phones), Lead.phone_secondary.in_(phones)),
    )
    if exclude_id:
        query = query.where(Lead.id != exclude_id)
    if db.scalar(query.limit(1)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Số điện thoại đã tồn tại trong hệ thống")


def _next_customer_code(db: Session) -> str:
    codes = db.scalars(select(Customer.customer_code).where(Customer.customer_code.like("CUS-%")))
    numbers = [int(code.removeprefix("CUS-")) for code in codes if code.removeprefix("CUS-").isdigit()]
    return f"CUS-{max(numbers, default=0) + 1:06d}"


def _next_lead_code(db: Session) -> str:
    latest = db.scalar(select(Lead.code).order_by(Lead.code.desc()).limit(1))
    number = int(latest.split("-")[-1]) + 1 if latest and latest.startswith("LD-") else 1
    return f"LD-{number:06d}"


def _serialize_user(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


def _audit_snapshot(lead: Lead) -> dict:
    return {
        "code": lead.code,
        "full_name": lead.full_name,
        "phone_primary": lead.phone_primary,
        "phone_secondary": lead.phone_secondary,
        "customer_id": str(lead.customer_id) if lead.customer_id else None,
        "duplicate_detected": lead.duplicate_detected,
        "duplicate_match_reason": lead.duplicate_match_reason,
        "status": lead.status,
        "priority": lead.priority,
        "owner_id": str(lead.owner_id) if lead.owner_id else None,
        "next_follow_up_at": lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None,
    }


def serialize_lead(lead: Lead, *, detail: bool = False, db: Session | None = None) -> dict:
    data = {
        "id": lead.id,
        "code": lead.code,
        "full_name": lead.full_name,
        "phone_primary": lead.phone_primary,
        "phone_secondary": lead.phone_secondary,
        "source": lead.source,
        "project_interest": lead.project_interest,
        "budget_min": lead.budget_min,
        "budget_max": lead.budget_max,
        "status": lead.status,
        "priority": lead.priority,
        "owner": _serialize_user(lead.owner),
        "next_follow_up_at": lead.next_follow_up_at,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }
    if detail:
        data.update({
            "zalo": lead.zalo,
            "facebook": lead.facebook,
            "email": lead.email,
            "address": lead.address,
            "location_interest": lead.location_interest,
            "bedroom_need": lead.bedroom_need,
            "area_min": lead.area_min,
            "area_max": lead.area_max,
            "note": lead.note,
            "created_by": _serialize_user(lead.created_by),
            "assigned_by": _serialize_user(lead.assigned_by),
            "assigned_at": lead.assigned_at,
            "last_contact_at": lead.last_contact_at,
            "converted_customer_id": lead.converted_customer_id,
            "customer_id": lead.customer_id,
            "duplicate_detected": lead.duplicate_detected,
            "duplicate_of_customer_id": lead.duplicate_of_customer_id,
            "duplicate_match_reason": lead.duplicate_match_reason,
            "duplicate_info": {
                "is_duplicate": lead.duplicate_detected,
                "customer_id": lead.customer_id or lead.duplicate_of_customer_id,
                "matched_phone": lead.duplicate_match_reason,
                "message": "Lead/khách hàng này đã tồn tại trong hệ thống. Lead mới đã được liên kết vào hồ sơ khách hàng chung." if lead.duplicate_detected else None,
                "can_view_common_profile": True,
                "can_view_other_journeys": False,
            },
            "converted_customer": {"id": lead.converted_customer.id, "customer_code": lead.converted_customer.customer_code, "full_name": lead.converted_customer.full_name} if lead.converted_customer else None,
            "converted_at": lead.converted_at,
            "converted_by": _serialize_user(lead.converted_by),
            "lost_reason": lead.lost_reason,
            "activities": [serialize_activity(activity, db) for activity in lead.activities],
        })
    return data


def get_lead_by_id(db: Session, lead_id: UUID) -> Lead | None:
    return db.scalar(select(Lead).where(Lead.id == lead_id, Lead.deleted_at.is_(None)))


def list_leads(
    db: Session,
    user: User,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    lead_status: str | None = None,
    priority: str | None = None,
    source: str | None = None,
    owner_id: UUID | None = None,
    department_id: UUID | None = None,
    team_id: UUID | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    next_follow_up_from: date | None = None,
    next_follow_up_to: date | None = None,
    scope: str | None = None,
    activity_status: str | None = None,
    has_activity: bool | None = None,
    care_status: str | None = None,
    care_due: str | None = None,
    next_follow_up: str | None = None,
    stale: bool | None = None,
) -> tuple[list[Lead], dict]:
    require_view_permission(user)
    query = apply_view_scope(db, select(Lead).where(Lead.deleted_at.is_(None)), user)
    count_query = apply_view_scope(db, select(func.count(Lead.id)).where(Lead.deleted_at.is_(None)), user)
    conditions = []
    if scope == "mine":
        conditions.append(Lead.owner_id == user.id)
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(Lead.code.ilike(term), Lead.full_name.ilike(term), Lead.phone_primary.ilike(term), Lead.phone_secondary.ilike(term), Lead.email.ilike(term), Lead.zalo.ilike(term), Lead.facebook.ilike(term)))
    if lead_status:
        if lead_status == "active":
            conditions.append(Lead.status.notin_({"converted", "lost"}))
        else:
            if lead_status not in LEAD_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trạng thái lead không hợp lệ")
            conditions.append(Lead.status == lead_status)
    if priority:
        if priority == "hot":
            conditions.append(Lead.priority.in_({"urgent", "high"}))
        else:
            _validate_priority(priority)
            conditions.append(Lead.priority == priority)
    if source:
        conditions.append(Lead.source == source)
    if scope == "mine":
        conditions.append(Lead.owner_id == user.id)
    elif owner_id:
        conditions.append(Lead.owner_id == owner_id)
    if department_id or team_id:
        from app.models.user_organization_membership import UserOrganizationMembership
        member_query = select(UserOrganizationMembership.user_id)
        if department_id: member_query = member_query.where(UserOrganizationMembership.department_id == department_id)
        if team_id: member_query = member_query.where(UserOrganizationMembership.team_id == team_id)
        conditions.append(Lead.owner_id.in_(member_query))
    if created_from:
        conditions.append(Lead.created_at >= datetime.combine(created_from, time.min, tzinfo=timezone.utc))
    if created_to:
        conditions.append(Lead.created_at <= datetime.combine(created_to, time.max, tzinfo=timezone.utc))
    if next_follow_up_from:
        conditions.append(Lead.next_follow_up_at >= datetime.combine(next_follow_up_from, time.min, tzinfo=timezone.utc))
    if next_follow_up_to:
        conditions.append(Lead.next_follow_up_at <= datetime.combine(next_follow_up_to, time.max, tzinfo=timezone.utc))
    today_start = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    today_end = datetime.combine(date.today(), time.max, tzinfo=timezone.utc)
    if care_due == "today" or next_follow_up == "today":
        conditions.extend([Lead.next_follow_up_at >= today_start, Lead.next_follow_up_at <= today_end])
    if care_status == "overdue":
        conditions.extend([Lead.next_follow_up_at.is_not(None), Lead.next_follow_up_at < datetime.now(timezone.utc)])
    if activity_status == "none" or has_activity is False:
        conditions.append(~Lead.activities.any())
    if stale:
        conditions.append(func.coalesce(Lead.last_contact_at, Lead.created_at) < datetime.now(timezone.utc) - timedelta(days=7))
    for condition in conditions:
        query = query.where(condition)
        count_query = count_query.where(condition)
    total = db.scalar(count_query) or 0
    leads = list(db.scalars(query.order_by(Lead.updated_at.desc(), Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique().all())
    return leads, {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def _eligible_owner(db: Session, owner_id: UUID) -> User:
    owner = get_user_by_id(db, owner_id)
    if owner is None or owner.status != "active" or not (user_role_code_set(owner) & SALES_ROLE_CODES):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Người phụ trách không hợp lệ")
    return owner


def _existing_lead_for_duplicate(db: Session, duplicate) -> Lead | None:
    if duplicate.matched_lead_ids:
        lead = db.get(Lead, duplicate.matched_lead_ids[0])
        if lead and lead.deleted_at is None:
            return lead
    if duplicate.matched_customer_id:
        customer = db.get(Customer, duplicate.matched_customer_id)
        if customer:
            if customer.source_lead and customer.source_lead.deleted_at is None:
                return customer.source_lead
            return db.scalar(select(Lead).where(Lead.deleted_at.is_(None), or_(Lead.customer_id == customer.id, Lead.converted_customer_id == customer.id)).order_by(Lead.created_at.asc()).limit(1))
    return None


def _actor_org_context(db: Session, actor: User) -> tuple[UUID | None, UUID | None]:
    membership = db.scalar(select(UserOrganizationMembership).where(UserOrganizationMembership.user_id == actor.id).order_by(UserOrganizationMembership.is_primary.desc(), UserOrganizationMembership.created_at.asc()).limit(1))
    return (membership.team_id if membership else None, membership.department_id if membership else None)


def _duplicate_open_url(customer: Customer | None, lead: Lead | None) -> str | None:
    if lead:
        return f"/leads/{lead.id}"
    if customer:
        return f"/customers/{customer.id}"
    return None


def _duplicate_response_data(db: Session, duplicate, customer: Customer | None, lead: Lead | None, actor: User) -> dict:
    return {
        "id": lead.id if lead else None,
        "code": lead.code if lead else None,
        "full_name": lead.full_name if lead else (customer.full_name if customer else None),
        "phone_primary": lead.phone_primary if lead else (customer.primary_phone if customer else None),
        "phone_secondary": lead.phone_secondary if lead else (customer.secondary_phone if customer else None),
        "created_at": lead.created_at if lead else (customer.created_at if customer else None),
        "owner": _serialize_user(lead.owner) if lead else (_serialize_user(customer.owner) if customer else None),
        "duplicate_info": {
            "is_duplicate": True,
            "action": "existing_customer_reengaged",
            "customer_id": customer.id if customer else None,
            "lead_id": lead.id if lead else None,
            "customer_name": customer.full_name if customer else None,
            "lead_name": lead.full_name if lead else None,
            "customer_code": customer.customer_code if customer else None,
            "lead_code": lead.code if lead else None,
            "matched_phone": duplicate.matched_phone,
            "match_reason": duplicate.match_reason,
            "open_url": _duplicate_open_url(customer, lead),
            "message": "Lead/khách hàng này đã có trong hệ thống. Bạn có thể mở hồ sơ hiện có để tiếp tục chăm sóc.",
            "can_view_common_profile": True,
            "can_view_other_journeys": bool(actor.is_superuser or "leads.view.all" in _permission_set(actor)),
        },
    }


def record_duplicate_reengagement(db: Session, duplicate, payload: LeadCreate, actor: User) -> dict:
    customer = db.get(Customer, duplicate.matched_customer_id) if duplicate.matched_customer_id else None
    existing_lead = _existing_lead_for_duplicate(db, duplicate)
    if customer is None and existing_lead and (existing_lead.customer_id or existing_lead.converted_customer_id):
        customer = db.get(Customer, existing_lead.customer_id or existing_lead.converted_customer_id)
    now = datetime.now(timezone.utc)
    team_id, department_id = _actor_org_context(db, actor)
    if customer:
        customer.is_duplicate_profile = True
        customer.last_contact_at = now
        customer.updated_at = now
        db.add(CustomerActivity(
            customer_id=customer.id,
            user_id=actor.id,
            activity_type="duplicate_reengagement",
            title="Tiếp cận lại khách trùng",
            content=payload.note,
            old_value=duplicate.matched_phone,
            new_value=duplicate.match_reason,
        ))
    if existing_lead:
        existing_lead.last_contact_at = now
        existing_lead.updated_at = now
        create_activity_record(db, lead=existing_lead, actor=actor, activity_type="other", title="Tiếp cận lại khách trùng", content=f"User {actor.full_name} nhập lại số {duplicate.matched_phone}; không tạo lead mới.", old_value=duplicate.matched_phone, new_value=duplicate.match_reason)
    event_data = {
        "action": "existing_customer_reengaged",
        "customer_id": customer.id if customer else None,
        "existing_lead_id": existing_lead.id if existing_lead else None,
        "actor_user_id": actor.id,
        "team_id": team_id,
        "department_id": department_id,
        "matched_phone": duplicate.matched_phone,
        "match_reason": duplicate.match_reason,
        "source": payload.source,
        "note": payload.note,
    }
    write_audit_log(db, action="leads.duplicate_reengaged", user_id=actor.id, entity_type="leads", entity_id=str(existing_lead.id if existing_lead else (customer.id if customer else actor.id)), after_data=event_data)
    db.commit()
    if existing_lead:
        db.refresh(existing_lead)
    if customer:
        db.refresh(customer)
    return _duplicate_response_data(db, duplicate, customer, existing_lead, actor)


def check_lead_duplicate(db: Session, phone: str | None, actor: User) -> dict:
    duplicate = detect_duplicate_customer(db, phone, None, current_user=actor)
    if not duplicate.is_duplicate:
        return {"is_duplicate": False, "message": None}
    customer = db.get(Customer, duplicate.matched_customer_id) if duplicate.matched_customer_id else None
    existing_lead = _existing_lead_for_duplicate(db, duplicate)
    info = _duplicate_response_data(db, duplicate, customer, existing_lead, actor)["duplicate_info"]
    return info


def create_lead(db: Session, payload: LeadCreate, actor: User) -> Lead | dict:
    _validate_priority(payload.priority)
    _validate_ranges(payload.budget_min, payload.budget_max, payload.area_min, payload.area_max)
    primary = normalize_phone(payload.phone_primary)
    secondary = normalize_phone(payload.phone_secondary)
    if not primary:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Số điện thoại chính là bắt buộc")
    duplicate = detect_duplicate_customer(db, primary, secondary, current_user=actor)
    if duplicate.is_duplicate:
        return record_duplicate_reengagement(db, duplicate, payload, actor)
    owner_id = actor.id
    assigned_owner = None
    if payload.owner_id and payload.owner_id != actor.id and _has_any(actor, ASSIGN_PERMISSIONS):
        assigned_owner = _eligible_owner(db, payload.owner_id)
        _validate_target_owner_scope(db, actor, assigned_owner)
        owner_id = assigned_owner.id
    customer = None
    now = datetime.now(timezone.utc)
    if duplicate.is_duplicate and duplicate.matched_customer_id:
        customer = db.get(Customer, duplicate.matched_customer_id)
    if customer is None:
        customer = Customer(
            customer_code=_next_customer_code(db),
            full_name=payload.full_name.strip(),
            primary_phone=primary,
            secondary_phone=secondary,
            phone_primary_normalized=primary,
            phone_secondary_normalized=secondary,
            email=payload.email,
            zalo=payload.zalo,
            facebook=payload.facebook,
            address=payload.address,
            source=payload.source,
            source_note=payload.note,
            interested_project=payload.project_interest,
            interested_area=payload.location_interest,
            budget_min=payload.budget_min,
            budget_max=payload.budget_max,
            bedroom_count=payload.bedroom_need,
            area_min=payload.area_min,
            area_max=payload.area_max,
            owner_id=owner_id,
            created_by_id=actor.id,
            first_touch_user_id=actor.id,
            first_touch_source=payload.source,
            first_uploaded_at=now,
            first_upload_note=payload.note,
            first_contact_at=now,
            next_follow_up_at=payload.next_follow_up_at,
            note=payload.note,
            buying_timeline="unknown",
            financial_rating="unknown",
        )
        db.add(customer)
        db.flush()
    else:
        customer.is_duplicate_profile = True
    lead = Lead(**payload.model_dump(exclude={"owner_id", "phone_primary", "phone_secondary"}), code=_next_lead_code(db), phone_primary=primary, phone_secondary=secondary, phone_primary_normalized=primary, phone_secondary_normalized=secondary, status="new", owner_id=owner_id, created_by_id=actor.id, customer_id=customer.id, duplicate_detected=duplicate.is_duplicate, duplicate_of_customer_id=customer.id if duplicate.is_duplicate else None, duplicate_match_reason=duplicate.match_reason)
    if owner_id != actor.id:
        lead.assigned_by_id = actor.id
        lead.assigned_at = datetime.now(timezone.utc)
    db.add(lead)
    db.flush()
    if customer.source_lead_id is None:
        customer.source_lead_id = lead.id
    if customer.first_lead_id is None:
        customer.first_lead_id = lead.id
    if lead.note and lead.note.strip():
        create_activity_record(db, lead=lead, actor=actor, activity_type="note", title="Ghi chú ban đầu", content=lead.note.strip())
    if assigned_owner is not None:
        create_activity_record(db, lead=lead, actor=actor, activity_type="assignment", content="Phân công lead khi tạo", old_value=actor.full_name, new_value=assigned_owner.full_name)
    write_audit_log(db, action="leads.create", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), after_data=_audit_snapshot(lead))
    write_audit_log(db, action="customers.create", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"source_lead_id": str(lead.id), "first_touch_user_id": str(actor.id)})
    db.commit()
    db.refresh(lead)
    return lead


def update_lead(db: Session, lead: Lead, payload: LeadUpdate, actor: User) -> Lead:
    require_update_access(db, actor, lead)
    values = payload.model_dump(exclude_unset=True)
    _validate_priority(values.get("priority"))
    budget_min = values.get("budget_min", lead.budget_min)
    budget_max = values.get("budget_max", lead.budget_max)
    area_min = values.get("area_min", lead.area_min)
    area_max = values.get("area_max", lead.area_max)
    _validate_ranges(budget_min, budget_max, area_min, area_max)
    primary = normalize_phone(values.get("phone_primary", lead.phone_primary))
    secondary = normalize_phone(values.get("phone_secondary", lead.phone_secondary))
    if not primary:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Số điện thoại chính là bắt buộc")
    _ensure_phone_unique(db, primary, secondary, lead.id)
    before = _audit_snapshot(lead)
    values["phone_primary"] = primary
    values["phone_secondary"] = secondary
    old_note = lead.note
    for field, value in values.items():
        setattr(lead, field, value)
    if "note" in values and values["note"] and values["note"] != old_note:
        create_activity_record(db, lead=lead, actor=actor, activity_type="note", title="Cập nhật ghi chú", content=values["note"].strip())
    write_audit_log(db, action="leads.update", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data=before, after_data=_audit_snapshot(lead))
    db.commit()
    db.refresh(lead)
    return lead


def change_lead_status(db: Session, lead: Lead, payload: LeadStatusUpdate, actor: User) -> Lead:
    require_update_access(db, actor, lead)
    if payload.status not in LEAD_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trạng thái lead không hợp lệ")
    if payload.status == "lost" and not (payload.lost_reason and payload.lost_reason.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng nhập lý do mất khách")
    old_status = lead.status
    if old_status == payload.status and lead.lost_reason == payload.lost_reason:
        return lead
    lead.status = payload.status
    lead.lost_reason = payload.lost_reason.strip() if payload.status == "lost" and payload.lost_reason else None
    if payload.status in CONTACT_STATUSES:
        lead.last_contact_at = datetime.now(timezone.utc)
    content = payload.note.strip() if payload.note and payload.note.strip() else f"Chuyển trạng thái từ {old_status} sang {payload.status}"
    create_activity_record(db, lead=lead, actor=actor, activity_type="status_change", content=content, old_value=old_status, new_value=payload.status)
    write_audit_log(db, action="leads.status_change", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"status": old_status}, after_data={"status": lead.status, "lost_reason": lead.lost_reason})
    db.commit()
    db.refresh(lead)
    return lead


def assign_lead(db: Session, lead: Lead, payload: LeadAssign, actor: User) -> Lead:
    require_assign_access(db, actor, lead)
    owner = _eligible_owner(db, payload.owner_id)
    _validate_target_owner_scope(db, actor, owner)
    old_owner_id = lead.owner_id
    old_owner_name = lead.owner.full_name if lead.owner else "Chưa phân công"
    lead.owner_id = owner.id
    lead.assigned_by_id = actor.id
    lead.assigned_at = datetime.now(timezone.utc)
    content = payload.note.strip() if payload.note and payload.note.strip() else f"Phân công lead cho {owner.full_name}"
    create_activity_record(db, lead=lead, actor=actor, activity_type="assignment", content=content, old_value=old_owner_name, new_value=owner.full_name)
    write_audit_log(db, action="leads.assign", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"owner_id": str(old_owner_id) if old_owner_id else None}, after_data={"owner_id": str(owner.id)})
    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, lead: Lead, actor: User) -> None:
    lead.deleted_at = datetime.now(timezone.utc)
    lead.deleted_by = actor.id
    write_audit_log(db, action="leads.delete", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data=_audit_snapshot(lead), after_data={"deleted_at": lead.deleted_at.isoformat(), "deleted_by": str(actor.id)})
    db.commit()


def list_overdue_leads(db: Session, user: User, *, page: int, page_size: int, owner_id: UUID | None = None, priority: str | None = None, scope: str | None = None, care_status: str | None = None):
    require_view_permission(user)
    conditions = [Lead.deleted_at.is_(None), Lead.next_follow_up_at < datetime.now(timezone.utc), Lead.status.not_in({"converted", "lost"})]
    if owner_id: conditions.append(Lead.owner_id == owner_id)
    if priority:
        _validate_priority(priority); conditions.append(Lead.priority == priority)
    query = apply_view_scope(db, select(Lead).where(*conditions), user)
    count_query = apply_view_scope(db, select(func.count(Lead.id)).where(*conditions), user)
    total = db.scalar(count_query) or 0
    leads = list(db.scalars(query.order_by(Lead.next_follow_up_at.asc()).offset((page - 1) * page_size).limit(page_size)).unique())
    return leads, {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def transfer_lead(db: Session, lead: Lead, new_owner_id: UUID, reason: str, actor: User) -> Lead:
    require_assign_access(db, actor, lead)
    owner = _eligible_owner(db, new_owner_id)
    _validate_target_owner_scope(db, actor, owner)
    previous = lead.owner
    lead.owner_id = owner.id; lead.assigned_by_id = actor.id; lead.assigned_at = datetime.now(timezone.utc)
    create_activity_record(db, lead=lead, actor=actor, activity_type="assignment", title="Chuyển lead", content=reason.strip(), old_value=previous.full_name if previous else "Chưa phân công", new_value=owner.full_name)
    write_audit_log(db, action="leads.transfer", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"owner_id": str(previous.id) if previous else None}, after_data={"owner_id": str(owner.id), "reason": reason.strip()})
    db.commit(); db.refresh(lead); return lead


def reclaim_lead(db: Session, lead: Lead, new_owner_id: UUID | None, reason: str, actor: User) -> Lead:
    permissions = _permission_set(actor)
    if actor.is_superuser or "leads.reclaim.all" in permissions:
        pass
    elif "leads.reclaim.team" in permissions:
        from app.services.organization_service import get_accessible_user_ids_for_lead_scope
        ids = get_accessible_user_ids_for_lead_scope(db, actor, "team")
        if lead.owner_id not in ids and lead.created_by_id not in ids:
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập lead này")
    else:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")
    owner = _eligible_owner(db, new_owner_id or actor.id)
    if not (actor.is_superuser or "leads.reclaim.all" in permissions):
        from app.services.organization_service import get_accessible_user_ids_for_lead_scope
        if owner.id not in get_accessible_user_ids_for_lead_scope(db, actor, "team"):
            raise HTTPException(status_code=403, detail="Người phụ trách không nằm trong phạm vi bạn được phân công")
    previous = lead.owner
    lead.owner_id = owner.id; lead.assigned_by_id = actor.id; lead.assigned_at = datetime.now(timezone.utc)
    create_activity_record(db, lead=lead, actor=actor, activity_type="assignment", title="Thu hồi lead", content=reason.strip(), old_value=previous.full_name if previous else "Chưa phân công", new_value=owner.full_name)
    write_audit_log(db, action="leads.reclaim", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"owner_id": str(previous.id) if previous else None}, after_data={"owner_id": str(owner.id), "reason": reason.strip()})
    db.commit(); db.refresh(lead); return lead
