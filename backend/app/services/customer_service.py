import re
from datetime import date, datetime, time, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_activity import CustomerActivity
from app.models.lead import Lead
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.customer import CustomerActivityCreate, CustomerCreate, CustomerOwnerUpdate, CustomerStatusUpdate, CustomerUpdate, LeadConvertRequest
from app.services.audit_service import write_audit_log
from app.services.lead_activity_service import create_activity_record, serialize_activity as serialize_lead_activity
from app.services.lead_service import can_view_lead, get_lead_by_id, serialize_lead
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.user_service import get_user_by_id

CUSTOMER_TYPES = {"individual", "company", "investor", "agent", "other"}
CUSTOMER_STATUSES = {"active", "inactive", "potential", "vip", "blacklisted"}
CONTACT_ACTIVITY_TYPES = {"call", "zalo", "email", "meeting"}


def _permissions(user: User) -> set[str]:
    return set(get_user_permissions(user))


def _scope(user: User, prefix: str) -> str | None:
    permissions = _permissions(user)
    if user.is_superuser:
        return "all"
    for value in ("all", "department", "team", "own"):
        if f"{prefix}.{value}" in permissions:
            return value
    return None


def _ids(db: Session, user: User, scope: str) -> set[UUID]:
    return get_accessible_user_ids_for_lead_scope(db, user, scope)


def _can_access(db: Session, user: User, customer: Customer, prefix: str) -> bool:
    scope = _scope(user, prefix)
    return bool(scope and (scope == "all" or customer.owner_id in _ids(db, user, scope)))


def _require_view(db: Session, user: User, customer: Customer) -> None:
    if not _can_access(db, user, customer, "customers.view"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập khách hàng này")


def _require_update(db: Session, user: User, customer: Customer) -> None:
    if not _can_access(db, user, customer, "customers.update"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật khách hàng này")


def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\D", "", value) or None


def _validate_phone(db: Session, primary: str | None, secondary: str | None, exclude_id: UUID | None = None) -> tuple[str, str | None]:
    primary = normalize_phone(primary)
    secondary = normalize_phone(secondary)
    if not primary:
        raise HTTPException(status_code=422, detail="Số điện thoại chính là bắt buộc")
    phones = {phone for phone in (primary, secondary) if phone}
    query = select(Customer.id).where(Customer.deleted_at.is_(None), or_(Customer.primary_phone.in_(phones), Customer.secondary_phone.in_(phones)))
    if exclude_id:
        query = query.where(Customer.id != exclude_id)
    if db.scalar(query):
        raise HTTPException(status_code=409, detail="Số điện thoại khách hàng đã tồn tại")
    return primary, secondary


def _validate_ranges(data: dict) -> None:
    if data.get("budget_min") is not None and data.get("budget_max") is not None and data["budget_min"] > data["budget_max"]:
        raise HTTPException(status_code=400, detail="Ngân sách tối thiểu không được lớn hơn ngân sách tối đa")
    if data.get("area_min") is not None and data.get("area_max") is not None and data["area_min"] > data["area_max"]:
        raise HTTPException(status_code=400, detail="Diện tích tối thiểu không được lớn hơn diện tích tối đa")


def _next_code(db: Session) -> str:
    last = db.scalar(select(Customer.customer_code).order_by(Customer.customer_code.desc()).limit(1))
    number = int(last.split("-")[-1]) + 1 if last and last.startswith("CUS-") and last.split("-")[-1].isdigit() else 1
    return f"CUS-{number:06d}"


def _user_summary(user: User | None) -> dict | None:
    return {"id": user.id, "full_name": user.full_name, "email": user.email} if user else None


def serialize_customer_activity(activity: CustomerActivity) -> dict:
    return {"id": activity.id, "activity_type": activity.activity_type, "title": activity.title, "content": activity.content, "old_value": activity.old_value, "new_value": activity.new_value, "user": _user_summary(activity.user), "created_at": activity.created_at}


def _task_summary(task) -> dict:
    return {"id": task.id, "title": task.title, "status": task.status, "priority": task.priority, "due_at": task.due_at, "assigned_to": _user_summary(task.assigned_to)}


def _appointment_summary(item) -> dict:
    return {"id": item.id, "title": item.title, "status": item.status, "appointment_type": item.appointment_type, "start_at": item.start_at, "location": item.location, "assigned_to": _user_summary(item.assigned_to)}


def serialize_customer(customer: Customer, *, detail: bool = False) -> dict:
    lead = customer.source_lead
    data = {
        "id": customer.id, "customer_code": customer.customer_code, "full_name": customer.full_name,
        "customer_type": customer.customer_type, "status": customer.status, "primary_phone": customer.primary_phone,
        "secondary_phone": customer.secondary_phone, "email": customer.email, "zalo": customer.zalo,
        "facebook": customer.facebook, "address": customer.address, "source": customer.source,
        "source_lead_id": customer.source_lead_id, "source_note": customer.source_note,
        "interested_project": customer.interested_project, "interested_area": customer.interested_area,
        "budget_min": customer.budget_min, "budget_max": customer.budget_max, "bedroom_count": customer.bedroom_count,
        "area_min": customer.area_min, "area_max": customer.area_max, "purpose": customer.purpose,
        "owner": _user_summary(customer.owner), "created_by": _user_summary(customer.created_by),
        "first_contact_at": customer.first_contact_at, "last_contact_at": customer.last_contact_at,
        "next_follow_up_at": customer.next_follow_up_at, "converted_at": customer.converted_at,
        "note": customer.note, "created_at": customer.created_at, "updated_at": customer.updated_at,
        "source_lead": {"id": lead.id, "code": lead.code, "full_name": lead.full_name, "status": lead.status} if lead else None,
    }
    if detail:
        data.update({
            "activities": [serialize_customer_activity(item) for item in customer.activities],
            "lead_activities": [serialize_lead_activity(item) for item in lead.activities] if lead else [],
            "related_tasks": [_task_summary(item) for item in lead.tasks if item.deleted_at is None] if lead else [],
            "related_appointments": [_appointment_summary(item) for item in lead.appointments if item.deleted_at is None] if lead else [],
        })
    return data


def get_customer(db: Session, customer_id: UUID) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None)))


def get_customer_detail(db: Session, customer_id: UUID, actor: User) -> Customer:
    customer = get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    _require_view(db, actor, customer)
    return customer


def list_customers(db: Session, actor: User, *, page: int, page_size: int, search: str | None = None, customer_status: str | None = None, customer_type: str | None = None, owner_id: UUID | None = None, source: str | None = None, project: str | None = None, next_follow_up_from: date | None = None, next_follow_up_to: date | None = None):
    scope = _scope(actor, "customers.view")
    if not scope:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập khách hàng này")
    conditions = [Customer.deleted_at.is_(None)]
    if scope != "all": conditions.append(Customer.owner_id.in_(_ids(db, actor, scope)))
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(Customer.customer_code.ilike(term), Customer.full_name.ilike(term), Customer.primary_phone.ilike(term), Customer.secondary_phone.ilike(term), Customer.email.ilike(term)))
    if customer_status: conditions.append(Customer.status == customer_status)
    if customer_type: conditions.append(Customer.customer_type == customer_type)
    if owner_id: conditions.append(Customer.owner_id == owner_id)
    if source: conditions.append(Customer.source.ilike(f"%{source}%"))
    if project: conditions.append(Customer.interested_project.ilike(f"%{project}%"))
    if next_follow_up_from: conditions.append(Customer.next_follow_up_at >= datetime.combine(next_follow_up_from, time.min, tzinfo=timezone.utc))
    if next_follow_up_to: conditions.append(Customer.next_follow_up_at <= datetime.combine(next_follow_up_to, time.max, tzinfo=timezone.utc))
    total = db.scalar(select(func.count(Customer.id)).where(*conditions)) or 0
    items = list(db.scalars(select(Customer).where(*conditions).order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
    return items, {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def list_customer_assignees(db: Session, actor: User) -> list[User]:
    scope = _scope(actor, "customers.assign")
    if not scope:
        return [actor]
    ids = _ids(db, actor, scope)
    return list(db.scalars(select(User).where(User.id.in_(ids), User.status == "active", User.deleted_at.is_(None)).order_by(User.full_name)).unique())


def _validate_owner(db: Session, actor: User, owner_id: UUID, prefix: str = "customers.assign") -> User:
    owner = get_user_by_id(db, owner_id)
    if not owner or owner.status != "active":
        raise HTTPException(status_code=400, detail="Người phụ trách khách hàng không hợp lệ")
    scope = _scope(actor, prefix)
    if not scope or (scope != "all" and owner.id not in _ids(db, actor, scope)):
        raise HTTPException(status_code=400, detail="Người phụ trách khách hàng không hợp lệ")
    return owner


def _activity(db: Session, customer: Customer, actor: User, activity_type: str, title: str, content: str | None = None, old_value: str | None = None, new_value: str | None = None) -> CustomerActivity:
    item = CustomerActivity(customer_id=customer.id, user_id=actor.id, activity_type=activity_type, title=title, content=content, old_value=old_value, new_value=new_value)
    db.add(item)
    return item


def create_customer(db: Session, payload: CustomerCreate, actor: User) -> Customer:
    if "customers.create" not in _permissions(actor) and not actor.is_superuser:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật khách hàng này")
    data = payload.model_dump()
    data["full_name"] = data["full_name"].strip()
    if not data["full_name"]: raise HTTPException(status_code=422, detail="Họ tên khách hàng là bắt buộc")
    data["primary_phone"], data["secondary_phone"] = _validate_phone(db, data["primary_phone"], data.get("secondary_phone"))
    _validate_ranges(data)
    owner_id = data.pop("owner_id") or actor.id
    _validate_owner(db, actor, owner_id)
    customer = Customer(**data, owner_id=owner_id, customer_code=_next_code(db), created_by_id=actor.id)
    db.add(customer); db.flush()
    _activity(db, customer, actor, "other", "Tạo khách hàng", "Khách hàng được tạo thủ công")
    write_audit_log(db, action="customers.create", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"customer_code": customer.customer_code, "owner_id": str(owner_id)})
    db.commit(); db.refresh(customer)
    return customer


def update_customer(db: Session, customer: Customer, payload: CustomerUpdate, actor: User) -> Customer:
    _require_update(db, actor, customer)
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data and (not data["full_name"] or not data["full_name"].strip()): raise HTTPException(status_code=422, detail="Họ tên khách hàng là bắt buộc")
    if "owner_id" in data:
        owner_id = data.pop("owner_id")
        if owner_id: _validate_owner(db, actor, owner_id)
        customer.owner_id = owner_id
    primary = data.get("primary_phone", customer.primary_phone); secondary = data.get("secondary_phone", customer.secondary_phone)
    if "primary_phone" in data or "secondary_phone" in data:
        data["primary_phone"], data["secondary_phone"] = _validate_phone(db, primary, secondary, customer.id)
    merged = {"budget_min": data.get("budget_min", customer.budget_min), "budget_max": data.get("budget_max", customer.budget_max), "area_min": data.get("area_min", customer.area_min), "area_max": data.get("area_max", customer.area_max)}
    _validate_ranges(merged)
    for key, value in data.items(): setattr(customer, key, value)
    customer.updated_by_id = actor.id
    _activity(db, customer, actor, "other", "Cập nhật khách hàng", "Thông tin khách hàng đã được cập nhật")
    write_audit_log(db, action="customers.update", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"fields": sorted(data)})
    db.commit(); db.refresh(customer); return customer


def update_customer_status(db: Session, customer: Customer, payload: CustomerStatusUpdate, actor: User) -> Customer:
    _require_update(db, actor, customer); old = customer.status; customer.status = payload.status; customer.updated_by_id = actor.id
    _activity(db, customer, actor, "status_change", "Đổi trạng thái khách hàng", payload.note, old, payload.status)
    write_audit_log(db, action="customers.status_change", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), before_data={"status": old}, after_data={"status": payload.status})
    db.commit(); db.refresh(customer); return customer


def update_customer_owner(db: Session, customer: Customer, payload: CustomerOwnerUpdate, actor: User) -> Customer:
    _require_view(db, actor, customer); _validate_owner(db, actor, payload.owner_id); old = customer.owner_id
    customer.owner_id = payload.owner_id; customer.updated_by_id = actor.id
    _activity(db, customer, actor, "owner_change", "Đổi người phụ trách", payload.note, str(old) if old else None, str(payload.owner_id))
    write_audit_log(db, action="customers.assign", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), before_data={"owner_id": str(old) if old else None}, after_data={"owner_id": str(payload.owner_id)})
    db.commit(); db.refresh(customer); return customer


def add_customer_activity(db: Session, customer: Customer, payload: CustomerActivityCreate, actor: User) -> CustomerActivity:
    if not _can_access(db, actor, customer, "customers.add_activity"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật khách hàng này")
    content = payload.content.strip()
    if not content: raise HTTPException(status_code=422, detail="Nội dung là bắt buộc")
    item = _activity(db, customer, actor, payload.activity_type, payload.title or {"note":"Ghi chú", "call":"Cuộc gọi", "zalo":"Zalo", "email":"Email", "meeting":"Cuộc hẹn", "other":"Hoạt động"}[payload.activity_type], content)
    if payload.activity_type in CONTACT_ACTIVITY_TYPES: customer.last_contact_at = datetime.now(timezone.utc)
    write_audit_log(db, action="customers.add_activity", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"activity_type": payload.activity_type})
    db.commit(); db.refresh(item); return item


def soft_delete_customer(db: Session, customer: Customer, actor: User) -> None:
    if not actor.is_superuser and "customers.delete" not in _permissions(actor): raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật khách hàng này")
    _require_view(db, actor, customer); customer.deleted_at = datetime.now(timezone.utc); customer.deleted_by_id = actor.id
    write_audit_log(db, action="customers.delete", user_id=actor.id, entity_type="customers", entity_id=str(customer.id)); db.commit()


def _can_convert(db: Session, actor: User, lead: Lead) -> bool:
    scope = _scope(actor, "leads.convert")
    if not scope: return False
    return scope == "all" or lead.owner_id in _ids(db, actor, scope) or lead.created_by_id in _ids(db, actor, scope)


def convert_lead_to_customer(db: Session, lead_id: UUID, payload: LeadConvertRequest, actor: User) -> tuple[Customer, Lead]:
    lead = get_lead_by_id(db, lead_id)
    if not lead: raise HTTPException(status_code=404, detail="Không tìm thấy lead")
    if not can_view_lead(db, actor, lead) or not _can_convert(db, actor, lead): raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập lead này")
    if lead.converted_customer_id or lead.status == "converted": raise HTTPException(status_code=409, detail="Lead này đã được chuyển thành khách hàng")
    primary, secondary = _validate_phone(db, lead.phone_primary, lead.phone_secondary)
    owner_id = payload.owner_id or lead.owner_id or actor.id; _validate_owner(db, actor, owner_id)
    now = datetime.now(timezone.utc)
    customer = Customer(customer_code=_next_code(db), full_name=lead.full_name, customer_type=payload.customer_type, status=payload.status,
        primary_phone=primary, secondary_phone=secondary, email=lead.email, zalo=lead.zalo, facebook=lead.facebook, address=lead.address,
        source=lead.source, source_lead_id=lead.id, source_note=lead.note, interested_project=lead.project_interest,
        interested_area=lead.location_interest, budget_min=lead.budget_min, budget_max=lead.budget_max, bedroom_count=lead.bedroom_need,
        area_min=lead.area_min, area_max=lead.area_max, owner_id=owner_id, created_by_id=actor.id,
        first_contact_at=lead.created_at, last_contact_at=lead.last_contact_at, next_follow_up_at=lead.next_follow_up_at,
        converted_at=now, note=payload.note or lead.note)
    db.add(customer); db.flush()
    lead.status = "converted"; lead.converted_customer_id = customer.id; lead.converted_at = now; lead.converted_by_id = actor.id
    _activity(db, customer, actor, "conversion", "Chuyển đổi từ lead", f"Lead {lead.code} đã được chuyển thành khách hàng")
    create_activity_record(db, lead=lead, actor=actor, activity_type="status_change", title="Chuyển đổi khách hàng", content=f"Lead đã được chuyển thành khách hàng {customer.customer_code}", old_value=None, new_value="converted")
    write_audit_log(db, action="customers.create", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"source_lead_id": str(lead.id)})
    write_audit_log(db, action="leads.convert", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), after_data={"customer_id": str(customer.id)})
    db.commit(); db.refresh(customer); db.refresh(lead); return customer, lead
