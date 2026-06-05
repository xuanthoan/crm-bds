from datetime import date, datetime, time, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.leads.constants import ASSIGN_PERMISSIONS, CONTACT_STATUSES, LEAD_PRIORITIES, LEAD_STATUSES, SALES_ROLE_CODES, UPDATE_PERMISSIONS, VIEW_PERMISSIONS
from app.models.lead import Lead
from app.models.user import User
from app.permissions.dependencies import user_has_permission
from app.schemas.lead import LeadAssign, LeadCreate, LeadStatusUpdate, LeadUpdate
from app.services.audit_service import write_audit_log
from app.services.lead_activity_service import create_activity
from app.services.user_service import get_user_by_id, user_role_codes


def _own_scope(lead: Lead, user: User) -> bool:
    return lead.owner_id == user.id or lead.created_by_id == user.id


def _has_any(user: User, permissions: tuple[str, ...]) -> bool:
    return any(user_has_permission(user, permission) for permission in permissions)


def apply_view_scope(query, user: User):
    if user_has_permission(user, "leads.view.all"):
        return query
    if _has_any(user, ("leads.view.department", "leads.view.team", "leads.view.own")):
        # Sprint 4 placeholder: team/department scope behaves like own scope until org hierarchy exists.
        return query.where(or_(Lead.owner_id == user.id, Lead.created_by_id == user.id))
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem lead")


def ensure_view_access(lead: Lead, user: User) -> None:
    if user_has_permission(user, "leads.view.all"):
        return
    if _has_any(user, VIEW_PERMISSIONS) and _own_scope(lead, user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem lead này")


def ensure_update_access(lead: Lead, user: User) -> None:
    if user_has_permission(user, "leads.update.all"):
        return
    if _has_any(user, ("leads.update.team", "leads.update.own")) and _own_scope(lead, user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền cập nhật lead này")


def ensure_assign_access(lead: Lead, user: User) -> None:
    if user_has_permission(user, "leads.assign.all"):
        return
    if user_has_permission(user, "leads.assign.team") and _own_scope(lead, user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền phân công lead này")


def _user_summary(user: User | None) -> dict | None:
    return None if user is None else {"id": user.id, "full_name": user.full_name, "email": user.email}


def _activity_data(activity) -> dict:
    return {
        "id": activity.id,
        "activity_type": activity.activity_type,
        "title": activity.title,
        "content": activity.content,
        "old_value": activity.old_value,
        "new_value": activity.new_value,
        "user": _user_summary(activity.user),
        "created_at": activity.created_at,
    }


def serialize_lead(lead: Lead, detail: bool = False) -> dict:
    data = {
        "id": lead.id, "code": lead.code, "full_name": lead.full_name,
        "phone_primary": lead.phone_primary, "phone_secondary": lead.phone_secondary,
        "source": lead.source, "project_interest": lead.project_interest,
        "budget_min": lead.budget_min, "budget_max": lead.budget_max,
        "status": lead.status, "priority": lead.priority, "owner": _user_summary(lead.owner),
        "next_follow_up_at": lead.next_follow_up_at, "created_at": lead.created_at, "updated_at": lead.updated_at,
    }
    if detail:
        data.update({
            "zalo": lead.zalo, "facebook": lead.facebook, "email": lead.email, "address": lead.address,
            "location_interest": lead.location_interest, "bedroom_need": lead.bedroom_need,
            "area_min": lead.area_min, "area_max": lead.area_max, "note": lead.note,
            "created_by": _user_summary(lead.created_by), "assigned_by": _user_summary(lead.assigned_by),
            "assigned_at": lead.assigned_at, "last_contact_at": lead.last_contact_at,
            "lost_reason": lead.lost_reason, "activities": [_activity_data(activity) for activity in sorted(lead.activities, key=lambda item: item.created_at, reverse=True)],
        })
    return data


def get_lead_or_404(db: Session, lead_id: UUID) -> Lead:
    lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.deleted_at.is_(None)))
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy lead")
    return lead


def _validate_ranges(budget_min, budget_max, area_min, area_max) -> None:
    if budget_min is not None and budget_max is not None and budget_min > budget_max:
        raise HTTPException(status_code=400, detail="Ngân sách tối thiểu không được lớn hơn ngân sách tối đa")
    if area_min is not None and area_max is not None and area_min > area_max:
        raise HTTPException(status_code=400, detail="Diện tích tối thiểu không được lớn hơn diện tích tối đa")


def _normalize_phone(phone: str | None) -> str | None:
    return None if phone is None else "".join(character for character in phone if character.isdigit() or character == "+")


def _validate_phones(db: Session, primary: str, secondary: str | None, exclude_id: UUID | None = None) -> tuple[str, str | None]:
    primary = _normalize_phone(primary) or ""
    secondary = _normalize_phone(secondary)
    if not primary or (secondary and secondary == primary):
        raise HTTPException(status_code=400, detail="Số điện thoại đã tồn tại trong hệ thống" if secondary == primary else "Số điện thoại chính là bắt buộc")
    phones = [primary] + ([secondary] if secondary else [])
    query = select(Lead.id).where(Lead.deleted_at.is_(None), or_(Lead.phone_primary.in_(phones), Lead.phone_secondary.in_(phones)))
    if exclude_id:
        query = query.where(Lead.id != exclude_id)
    if db.scalar(query):
        raise HTTPException(status_code=409, detail="Số điện thoại đã tồn tại trong hệ thống")
    return primary, secondary


def _validate_owner(db: Session, owner_id: UUID) -> User:
    owner = get_user_by_id(db, owner_id)
    if owner is None or owner.status != "active":
        raise HTTPException(status_code=400, detail="Người phụ trách không tồn tại hoặc không hoạt động")
    if not SALES_ROLE_CODES.intersection(user_role_codes(owner)):
        raise HTTPException(status_code=400, detail="Người phụ trách phải có vai trò kinh doanh phù hợp")
    return owner


def _next_code(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(Lead)) or 0
    return f"LD-{count + 1:06d}"


def list_leads(db: Session, user: User, *, page: int, page_size: int, search: str | None = None, lead_status: str | None = None, priority: str | None = None, source: str | None = None, owner_id: UUID | None = None, created_from: date | None = None, created_to: date | None = None, next_follow_up_from: date | None = None, next_follow_up_to: date | None = None) -> tuple[list[Lead], dict]:
    query = apply_view_scope(select(Lead).where(Lead.deleted_at.is_(None)), user)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Lead.code.ilike(term), Lead.full_name.ilike(term), Lead.phone_primary.ilike(term), Lead.phone_secondary.ilike(term), Lead.email.ilike(term), Lead.zalo.ilike(term), Lead.facebook.ilike(term)))
    if lead_status: query = query.where(Lead.status == lead_status)
    if priority: query = query.where(Lead.priority == priority)
    if source: query = query.where(Lead.source == source)
    if owner_id: query = query.where(Lead.owner_id == owner_id)
    if created_from: query = query.where(Lead.created_at >= datetime.combine(created_from, time.min, tzinfo=timezone.utc))
    if created_to: query = query.where(Lead.created_at <= datetime.combine(created_to, time.max, tzinfo=timezone.utc))
    if next_follow_up_from: query = query.where(Lead.next_follow_up_at >= datetime.combine(next_follow_up_from, time.min, tzinfo=timezone.utc))
    if next_follow_up_to: query = query.where(Lead.next_follow_up_at <= datetime.combine(next_follow_up_to, time.max, tzinfo=timezone.utc))
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    total = db.scalar(count_query) or 0
    leads = list(db.scalars(query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique().all())
    return leads, {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def create_lead(db: Session, payload: LeadCreate, actor: User) -> Lead:
    if payload.priority not in LEAD_PRIORITIES:
        raise HTTPException(status_code=400, detail="Mức độ ưu tiên không hợp lệ")
    _validate_ranges(payload.budget_min, payload.budget_max, payload.area_min, payload.area_max)
    primary, secondary = _validate_phones(db, payload.phone_primary, payload.phone_secondary)
    owner = actor
    if payload.owner_id and payload.owner_id != actor.id:
        if not _has_any(actor, ASSIGN_PERMISSIONS):
            raise HTTPException(status_code=403, detail="Bạn không có quyền phân công lead")
        owner = _validate_owner(db, payload.owner_id)
    lead = Lead(code=_next_code(db), created_by_id=actor.id, owner_id=owner.id, phone_primary=primary, phone_secondary=secondary, **payload.model_dump(exclude={"owner_id", "phone_primary", "phone_secondary"}))
    if owner.id != actor.id:
        lead.assigned_by_id, lead.assigned_at = actor.id, datetime.now(timezone.utc)
    db.add(lead); db.flush()
    if payload.note:
        create_activity(db, lead=lead, user=actor, activity_type="note", title="Ghi chú ban đầu", content=payload.note)
    if owner.id != actor.id:
        create_activity(db, lead=lead, user=actor, activity_type="assignment", content=f"Phân công lead cho {owner.full_name}", old_value=str(actor.id), new_value=str(owner.id))
    write_audit_log(db, action="leads.create", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), after_data={"code": lead.code, "phone_primary": lead.phone_primary, "owner_id": str(lead.owner_id)})
    db.commit(); db.refresh(lead)
    return lead


def update_lead(db: Session, lead: Lead, payload: LeadUpdate, actor: User) -> Lead:
    ensure_update_access(lead, actor)
    values = payload.model_dump(exclude_unset=True)
    primary = values.get("phone_primary", lead.phone_primary)
    secondary = values.get("phone_secondary", lead.phone_secondary)
    primary, secondary = _validate_phones(db, primary, secondary, lead.id)
    budget_min, budget_max = values.get("budget_min", lead.budget_min), values.get("budget_max", lead.budget_max)
    area_min, area_max = values.get("area_min", lead.area_min), values.get("area_max", lead.area_max)
    _validate_ranges(budget_min, budget_max, area_min, area_max)
    priority = values.get("priority", lead.priority)
    if priority not in LEAD_PRIORITIES:
        raise HTTPException(status_code=400, detail="Mức độ ưu tiên không hợp lệ")
    before = {"full_name": lead.full_name, "phone_primary": lead.phone_primary, "priority": lead.priority, "note": lead.note}
    values["phone_primary"], values["phone_secondary"] = primary, secondary
    old_note = lead.note
    for key, value in values.items(): setattr(lead, key, value)
    if "note" in values and values["note"] and values["note"] != old_note:
        create_activity(db, lead=lead, user=actor, activity_type="note", title="Cập nhật ghi chú", content=values["note"])
    write_audit_log(db, action="leads.update", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data=before, after_data={"full_name": lead.full_name, "phone_primary": lead.phone_primary, "priority": lead.priority, "note": lead.note})
    db.commit(); db.refresh(lead)
    return lead


def change_status(db: Session, lead: Lead, payload: LeadStatusUpdate, actor: User) -> Lead:
    ensure_update_access(lead, actor)
    if payload.status not in LEAD_STATUSES:
        raise HTTPException(status_code=400, detail="Trạng thái lead không hợp lệ")
    if payload.status == "lost" and not payload.lost_reason:
        raise HTTPException(status_code=400, detail="Vui lòng nhập lý do mất khách")
    old = lead.status
    lead.status, lead.lost_reason = payload.status, payload.lost_reason if payload.status == "lost" else None
    if payload.status in CONTACT_STATUSES: lead.last_contact_at = datetime.now(timezone.utc)
    if old != lead.status:
        create_activity(db, lead=lead, user=actor, activity_type="status_change", title="Đổi trạng thái", content=payload.note or f"Đổi trạng thái từ {old} sang {lead.status}", old_value=old, new_value=lead.status)
        write_audit_log(db, action="leads.status_change", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"status": old}, after_data={"status": lead.status, "lost_reason": lead.lost_reason})
    db.commit(); db.refresh(lead)
    return lead


def assign_lead(db: Session, lead: Lead, payload: LeadAssign, actor: User) -> Lead:
    ensure_assign_access(lead, actor)
    owner = _validate_owner(db, payload.owner_id)
    old_owner = lead.owner_id
    lead.owner_id, lead.assigned_by_id, lead.assigned_at = owner.id, actor.id, datetime.now(timezone.utc)
    create_activity(db, lead=lead, user=actor, activity_type="assignment", title="Phân công lead", content=payload.note or f"Phân công lead cho {owner.full_name}", old_value=str(old_owner) if old_owner else None, new_value=str(owner.id))
    write_audit_log(db, action="leads.assign", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"owner_id": str(old_owner) if old_owner else None}, after_data={"owner_id": str(owner.id)})
    db.commit(); db.refresh(lead)
    return lead


def delete_lead(db: Session, lead: Lead, actor: User) -> None:
    lead.deleted_at, lead.deleted_by = datetime.now(timezone.utc), actor.id
    write_audit_log(db, action="leads.delete", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), before_data={"deleted_at": None}, after_data={"deleted_at": lead.deleted_at.isoformat()})
    db.commit()
