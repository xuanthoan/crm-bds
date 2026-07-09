from datetime import date, datetime, time, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_activity import CustomerActivity
from app.models.customer_related_person import CustomerRelatedPerson
from app.models.lead import Lead
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.customer import CustomerActivityCreate, CustomerCreate, CustomerOwnerUpdate, CustomerRelatedPersonCreate, CustomerRelatedPersonUpdate, CustomerStatusUpdate, CustomerUpdate, LeadConvertRequest
from app.services.audit_service import write_audit_log
from app.services.lead_activity_service import create_activity_record, serialize_activity as serialize_lead_activity
from app.services.lead_service import can_view_lead, get_lead_by_id, serialize_lead
from app.services.phone_service import normalize_phone as normalize_shared_phone
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.user_service import get_user_by_id

CUSTOMER_TYPES = {"individual", "company", "investor", "agent", "other"}
CUSTOMER_STATUSES = {"active", "inactive", "potential", "vip", "blacklisted"}
CONTACT_ACTIVITY_TYPES = {"call", "zalo", "email", "meeting"}

ADVANCED_PROFILE_FIELDS = {"gender", "date_of_birth", "province", "district", "occupation", "company", "job_title", "expected_budget", "available_cash", "loan_needed", "loan_ratio", "preferred_bank", "monthly_income", "financial_rating", "buying_purpose", "interested_property_type", "preferred_direction", "preferred_view", "buying_timeline", "related_people_note"}


def calculate_customer_score(customer: Customer) -> tuple[int, str, str]:
    parts: list[str] = []
    score = {"immediate": 30, "one_month": 25, "three_months": 15, "six_months": 8, "over_six_months": 3, "unknown": 0}.get(customer.buying_timeline, 0)
    if score:
        parts.append(f"Timeline +{score}")
    financial_points = {"A": 30, "B": 20, "C": 10, "D": 0, "unknown": 0}.get(customer.financial_rating, 0)
    score += financial_points
    if financial_points:
        parts.append(f"Tài chính +{financial_points}")
    if customer.expected_budget and customer.expected_budget > 0 and customer.available_cash is not None:
        ratio = customer.available_cash / customer.expected_budget
        cash_points = 20 if ratio >= Decimal("0.3") else 15 if ratio >= Decimal("0.2") else 8 if ratio >= Decimal("0.1") else 0
        score += cash_points
        if cash_points:
            parts.append(f"Tiền mặt +{cash_points}")
    income = customer.monthly_income or 0
    income_points = 10 if income >= 50_000_000 else 6 if income >= 30_000_000 else 3 if income >= 15_000_000 else 0
    score += income_points
    if income_points:
        parts.append(f"Thu nhập +{income_points}")
    now = datetime.now(timezone.utc)
    if customer.last_contact_at:
        contact_at = customer.last_contact_at if customer.last_contact_at.tzinfo else customer.last_contact_at.replace(tzinfo=timezone.utc)
        if (now - contact_at).days <= 7:
            score += 10
            parts.append("Liên hệ gần đây +10")
    if customer.next_follow_up_at:
        score += 5
        parts.append("Có lịch chăm sóc +5")
    label = "hot" if score >= 75 else "warm" if score >= 45 else "cold" if score >= 20 else "unqualified"
    return score, label, "; ".join(parts) or "Chưa có tiêu chí cộng điểm"


def _refresh_score(customer: Customer) -> tuple[int, str | None]:
    old = (customer.score_total, customer.score_label)
    customer.score_total, customer.score_label, customer.score_note = calculate_customer_score(customer)
    customer.score_updated_at = datetime.now(timezone.utc)
    return old


def serialize_related_person(person: CustomerRelatedPerson) -> dict:
    return {"id": person.id, "full_name": person.full_name, "relationship": person.relationship_type, "phone": person.phone, "email": person.email, "note": person.note, "created_at": person.created_at, "updated_at": person.updated_at}


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
    if not scope:
        return False
    if scope == "all":
        return True
    ids = _ids(db, user, scope)
    if customer.owner_id in ids:
        return True
    if prefix == "customers.view":
        return bool(db.scalar(select(Lead.id).where(Lead.deleted_at.is_(None), Lead.customer_id == customer.id, or_(Lead.owner_id.in_(ids), Lead.created_by_id.in_(ids))).limit(1)))
    return False


def _require_view(db: Session, user: User, customer: Customer) -> None:
    if not _can_access(db, user, customer, "customers.view"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập khách hàng này")


def _require_update(db: Session, user: User, customer: Customer) -> None:
    if not _can_access(db, user, customer, "customers.update"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật khách hàng này")


def normalize_phone(value: str | None) -> str | None:
    return normalize_shared_phone(value)


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
    # TODO: Replace with database sequence for high-concurrency production.
    codes = db.scalars(select(Customer.customer_code).where(Customer.customer_code.like("CUS-%")))
    numbers = [int(code.removeprefix("CUS-")) for code in codes if code.removeprefix("CUS-").isdigit()]
    return f"CUS-{max(numbers, default=0) + 1:06d}"


def _user_summary(user: User | None) -> dict | None:
    return {"id": user.id, "full_name": user.full_name, "email": user.email} if user else None


def serialize_customer_activity(activity: CustomerActivity) -> dict:
    return {"id": activity.id, "activity_type": activity.activity_type, "title": activity.title, "content": activity.content, "old_value": activity.old_value, "new_value": activity.new_value, "user": _user_summary(activity.user), "created_at": activity.created_at}


def _task_summary(task) -> dict:
    return {"id": task.id, "title": task.title, "status": task.status, "priority": task.priority, "due_at": task.due_at, "assigned_to": _user_summary(task.assigned_to)}


def _appointment_summary(item) -> dict:
    return {"id": item.id, "title": item.title, "status": item.status, "appointment_type": item.appointment_type, "start_at": item.start_at, "location": item.location, "assigned_to": _user_summary(item.assigned_to)}


def _can_view_all_journeys(actor: User | None) -> bool:
    return bool(actor and (actor.is_superuser or "customers.view.all" in _permissions(actor) or "leads.view.all" in _permissions(actor)))


def _visible_journey_leads(db: Session | None, actor: User | None, customer: Customer) -> list[Lead]:
    leads = [lead for lead in customer.journey_leads if lead.deleted_at is None]
    if db is None or actor is None or _can_view_all_journeys(actor):
        return leads
    return [lead for lead in leads if can_view_lead(db, actor, lead)]


def serialize_customer(customer: Customer, *, detail: bool = False, db: Session | None = None, actor: User | None = None) -> dict:
    lead = customer.source_lead
    visible_leads = _visible_journey_leads(db, actor, customer) if detail else []
    if detail and lead and db is not None and actor is not None and not _can_view_all_journeys(actor) and not can_view_lead(db, actor, lead):
        lead = visible_leads[0] if visible_leads else None
    has_multiple_journeys = len([item for item in customer.journey_leads if item.deleted_at is None]) > 1
    data = {
        "id": customer.id, "customer_code": customer.customer_code, "full_name": customer.full_name,
        "customer_type": customer.customer_type, "status": customer.status, "primary_phone": customer.primary_phone,
        "secondary_phone": customer.secondary_phone, "email": customer.email, "zalo": customer.zalo,
        "facebook": customer.facebook, "address": customer.address,
        "gender": customer.gender, "date_of_birth": customer.date_of_birth, "province": customer.province, "district": customer.district,
        "occupation": customer.occupation, "company": customer.company, "job_title": customer.job_title,
        "expected_budget": customer.expected_budget, "available_cash": customer.available_cash, "loan_needed": customer.loan_needed,
        "loan_ratio": customer.loan_ratio, "preferred_bank": customer.preferred_bank, "monthly_income": customer.monthly_income,
        "financial_rating": customer.financial_rating, "buying_purpose": customer.buying_purpose,
        "interested_property_type": customer.interested_property_type, "preferred_direction": customer.preferred_direction,
        "preferred_view": customer.preferred_view, "buying_timeline": customer.buying_timeline, "related_people_note": customer.related_people_note,
        "score_total": customer.score_total, "score_label": customer.score_label, "score_updated_at": customer.score_updated_at, "score_note": customer.score_note,
        "source": customer.source,
        "source_lead_id": customer.source_lead_id, "source_note": customer.source_note,
        "first_lead_id": customer.first_lead_id, "first_upload_note": customer.first_upload_note,
        "first_uploaded_at": customer.first_uploaded_at, "first_touch_user": _user_summary(customer.first_touch_user),
        "is_duplicate_profile": customer.is_duplicate_profile or has_multiple_journeys,
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
            "duplicate_visibility": {"has_multiple_journeys": has_multiple_journeys, "can_view_all_journeys": _can_view_all_journeys(actor), "message": "Bạn đang xem toàn bộ hành trình của khách hàng này." if _can_view_all_journeys(actor) else "Khách hàng này có nhiều hành trình/lead trong hệ thống. Bạn chỉ thấy chi tiết hành trình thuộc phạm vi quyền của mình."},
            "journey_leads": [{"id": item.id, "code": item.code, "full_name": item.full_name, "owner": _user_summary(item.owner), "status": item.status, "duplicate_detected": item.duplicate_detected} for item in visible_leads],
            "activities": [serialize_customer_activity(item) for item in customer.activities],
            "lead_activities": [serialize_lead_activity(activity) for item in visible_leads for activity in item.activities],
            "related_tasks": [_task_summary(task) for item in visible_leads for task in item.tasks if task.deleted_at is None],
            "related_appointments": [_appointment_summary(appt) for item in visible_leads for appt in item.appointments if appt.deleted_at is None],
            "related_people": [serialize_related_person(item) for item in customer.related_people if item.deleted_at is None],
            "contracts": [{"id": c.id, "contract_code": c.contract_code, "status": c.status, "contract_value": c.contract_value, "total_paid": sum((p.amount for p in c.payments if p.deleted_at is None and p.status == "paid"), 0), "property": {"id": c.property_unit.id, "property_code": c.property_unit.property_code}} for c in customer.contracts if c.deleted_at is None],
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


def list_customers(db: Session, actor: User, *, page: int, page_size: int, search: str | None = None, customer_status: str | None = None, customer_type: str | None = None, owner_id: UUID | None = None, source: str | None = None, project: str | None = None, next_follow_up_from: date | None = None, next_follow_up_to: date | None = None, gender: str | None = None, province: str | None = None, district: str | None = None, financial_rating: str | None = None, buying_purpose: str | None = None, interested_property_type: str | None = None, buying_timeline: str | None = None, score_label: str | None = None, score_min: int | None = None, score_max: int | None = None):
    scope = _scope(actor, "customers.view")
    if not scope:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập khách hàng này")
    conditions = [Customer.deleted_at.is_(None)]
    if scope != "all":
        ids = _ids(db, actor, scope)
        accessible_customer_ids = select(Lead.customer_id).where(Lead.deleted_at.is_(None), Lead.customer_id.is_not(None), or_(Lead.owner_id.in_(ids), Lead.created_by_id.in_(ids)))
        conditions.append(or_(Customer.owner_id.in_(ids), Customer.id.in_(accessible_customer_ids)))
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(Customer.customer_code.ilike(term), Customer.full_name.ilike(term), Customer.primary_phone.ilike(term), Customer.secondary_phone.ilike(term), Customer.email.ilike(term)))
    if customer_status: conditions.append(Customer.status == customer_status)
    if customer_type: conditions.append(Customer.customer_type == customer_type)
    if owner_id: conditions.append(Customer.owner_id == owner_id)
    if source: conditions.append(Customer.source.ilike(f"%{source}%"))
    if project: conditions.append(Customer.interested_project.ilike(f"%{project}%"))
    if gender: conditions.append(Customer.gender == gender)
    if province: conditions.append(Customer.province.ilike(f"%{province}%"))
    if district: conditions.append(Customer.district.ilike(f"%{district}%"))
    if financial_rating: conditions.append(Customer.financial_rating == financial_rating)
    if buying_purpose: conditions.append(Customer.buying_purpose == buying_purpose)
    if interested_property_type: conditions.append(Customer.interested_property_type == interested_property_type)
    if buying_timeline: conditions.append(Customer.buying_timeline == buying_timeline)
    if score_label: conditions.append(Customer.score_label == score_label)
    if score_min is not None: conditions.append(Customer.score_total >= score_min)
    if score_max is not None: conditions.append(Customer.score_total <= score_max)
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


def _set_customer_owner(db: Session, customer: Customer, owner_id: UUID | None, actor: User, note: str | None = None) -> bool:
    if owner_id is None:
        raise HTTPException(status_code=400, detail="Người phụ trách khách hàng không hợp lệ")
    new_owner = _validate_owner(db, actor, owner_id)
    if customer.owner_id == new_owner.id:
        return False
    old_owner_name = customer.owner.full_name if customer.owner else "Chưa phân công"
    customer.owner_id = new_owner.id
    customer.updated_by_id = actor.id
    _activity(
        db,
        customer,
        actor,
        "owner_change",
        "Đổi người phụ trách",
        note,
        old_owner_name,
        new_owner.full_name,
    )
    return True


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
    data["phone_primary_normalized"] = data["primary_phone"]
    data["phone_secondary_normalized"] = data.get("secondary_phone")
    customer = Customer(**data, owner_id=owner_id, customer_code=_next_code(db), created_by_id=actor.id, first_touch_user_id=actor.id, first_touch_source=data.get("source"), first_uploaded_at=datetime.now(timezone.utc), first_upload_note=data.get("note"))
    _refresh_score(customer)
    db.add(customer); db.flush()
    _activity(db, customer, actor, "other", "Tạo khách hàng", "Khách hàng được tạo thủ công")
    write_audit_log(db, action="customers.create", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"customer_code": customer.customer_code, "owner_id": str(owner_id)})
    db.commit(); db.refresh(customer)
    return customer


def update_customer(db: Session, customer: Customer, payload: CustomerUpdate, actor: User) -> Customer:
    _require_update(db, actor, customer)
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data and (not data["full_name"] or not data["full_name"].strip()): raise HTTPException(status_code=422, detail="Họ tên khách hàng là bắt buộc")
    owner_changed = False
    if "owner_id" in data:
        owner_changed = _set_customer_owner(db, customer, data.pop("owner_id"), actor)
    primary = data.get("primary_phone", customer.primary_phone); secondary = data.get("secondary_phone", customer.secondary_phone)
    if "primary_phone" in data or "secondary_phone" in data:
        data["primary_phone"], data["secondary_phone"] = _validate_phone(db, primary, secondary, customer.id)
        data["phone_primary_normalized"] = data["primary_phone"]
        data["phone_secondary_normalized"] = data["secondary_phone"]
    merged = {"budget_min": data.get("budget_min", customer.budget_min), "budget_max": data.get("budget_max", customer.budget_max), "area_min": data.get("area_min", customer.area_min), "area_max": data.get("area_max", customer.area_max)}
    _validate_ranges(merged)
    old_score = (customer.score_total, customer.score_label)
    for key, value in data.items(): setattr(customer, key, value)
    customer.updated_by_id = actor.id
    _refresh_score(customer)
    if ADVANCED_PROFILE_FIELDS.intersection(data):
        _activity(db, customer, actor, "update", "Cập nhật hồ sơ khách hàng", "Thông tin hồ sơ khách hàng đã được cập nhật")
    else:
        _activity(db, customer, actor, "other", "Cập nhật khách hàng", "Thông tin khách hàng đã được cập nhật")
    if old_score != (customer.score_total, customer.score_label):
        _activity(db, customer, actor, "update", "Cập nhật điểm khách hàng", old_value=f"{old_score[1] or 'Chưa có'} / {old_score[0]}", new_value=f"{customer.score_label} / {customer.score_total}")
    updated_fields = sorted([*data, *(["owner_id"] if owner_changed else [])])
    write_audit_log(db, action="customers.update", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"fields": updated_fields})
    db.commit(); db.refresh(customer); return customer


def update_customer_status(db: Session, customer: Customer, payload: CustomerStatusUpdate, actor: User) -> Customer:
    _require_update(db, actor, customer); old = customer.status; customer.status = payload.status; customer.updated_by_id = actor.id
    _activity(db, customer, actor, "status_change", "Đổi trạng thái khách hàng", payload.note, old, payload.status)
    write_audit_log(db, action="customers.status_change", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), before_data={"status": old}, after_data={"status": payload.status})
    db.commit(); db.refresh(customer); return customer


def update_customer_owner(db: Session, customer: Customer, payload: CustomerOwnerUpdate, actor: User) -> Customer:
    _require_view(db, actor, customer)
    old_owner_id = customer.owner_id
    changed = _set_customer_owner(db, customer, payload.owner_id, actor, payload.note)
    if changed:
        write_audit_log(db, action="customers.assign", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), before_data={"owner_id": str(old_owner_id) if old_owner_id else None}, after_data={"owner_id": str(payload.owner_id)})
        db.commit()
        db.refresh(customer)
    return customer


def add_customer_activity(db: Session, customer: Customer, payload: CustomerActivityCreate, actor: User) -> CustomerActivity:
    if not _can_access(db, actor, customer, "customers.add_activity"):
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật khách hàng này")
    content = payload.content.strip()
    if not content: raise HTTPException(status_code=422, detail="Nội dung là bắt buộc")
    item = _activity(db, customer, actor, payload.activity_type, payload.title or {"note":"Ghi chú", "call":"Cuộc gọi", "zalo":"Zalo", "email":"Email", "meeting":"Cuộc hẹn", "other":"Hoạt động"}[payload.activity_type], content)
    if payload.activity_type in CONTACT_ACTIVITY_TYPES:
        customer.last_contact_at = datetime.now(timezone.utc)
        _refresh_score(customer)
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
        phone_primary_normalized=primary, phone_secondary_normalized=secondary,
        source=lead.source, source_lead_id=lead.id, source_note=lead.note, interested_project=lead.project_interest,
        interested_area=lead.location_interest, budget_min=lead.budget_min, budget_max=lead.budget_max, bedroom_count=lead.bedroom_need,
        area_min=lead.area_min, area_max=lead.area_max, owner_id=owner_id, created_by_id=actor.id,
        first_contact_at=lead.created_at, last_contact_at=lead.last_contact_at, next_follow_up_at=lead.next_follow_up_at,
        converted_at=now, note=payload.note or lead.note, buying_timeline="unknown", financial_rating="unknown")
    _refresh_score(customer)
    db.add(customer); db.flush()
    lead.status = "converted"; lead.converted_customer_id = customer.id; lead.converted_at = now; lead.converted_by_id = actor.id
    _activity(db, customer, actor, "conversion", "Chuyển đổi từ lead", f"Lead {lead.code} đã được chuyển thành khách hàng")
    create_activity_record(db, lead=lead, actor=actor, activity_type="status_change", title="Chuyển đổi khách hàng", content=f"Lead đã được chuyển thành khách hàng {customer.customer_code}", old_value=None, new_value="converted")
    write_audit_log(db, action="customers.create", user_id=actor.id, entity_type="customers", entity_id=str(customer.id), after_data={"source_lead_id": str(lead.id)})
    write_audit_log(db, action="leads.convert", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), after_data={"customer_id": str(customer.id)})
    db.commit(); db.refresh(customer); db.refresh(lead); return customer, lead


def list_related_people(db: Session, customer_id: UUID, actor: User) -> list[CustomerRelatedPerson]:
    customer = get_customer_detail(db, customer_id, actor)
    return [item for item in customer.related_people if item.deleted_at is None]


def add_related_person(db: Session, customer_id: UUID, payload: CustomerRelatedPersonCreate, actor: User) -> CustomerRelatedPerson:
    customer = get_customer_detail(db, customer_id, actor)
    _require_update(db, actor, customer)
    data = payload.model_dump()
    relationship_type = data.pop("relationship")
    person = CustomerRelatedPerson(
        customer_id=customer.id,
        created_by_id=actor.id,
        relationship_type=relationship_type,
        **data,
    )
    db.add(person); db.flush()
    _activity(db, customer, actor, "update", "Thêm người liên quan", person.full_name)
    db.commit(); db.refresh(person); return person


def _get_related_person(db: Session, person_id: UUID) -> CustomerRelatedPerson:
    person = db.scalar(select(CustomerRelatedPerson).where(CustomerRelatedPerson.id == person_id, CustomerRelatedPerson.deleted_at.is_(None)))
    if not person:
        raise HTTPException(status_code=404, detail="Người liên quan không tồn tại")
    return person


def update_related_person(db: Session, customer_id: UUID, person_id: UUID, payload: CustomerRelatedPersonUpdate, actor: User) -> CustomerRelatedPerson:
    customer = get_customer_detail(db, customer_id, actor)
    _require_update(db, actor, customer)
    person = _get_related_person(db, person_id)
    if person.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="Người liên quan không tồn tại")
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("full_name") is None and "full_name" in updates:
        raise HTTPException(status_code=422, detail="Họ tên người liên quan là bắt buộc")
    if updates.get("relationship") is None and "relationship" in updates:
        raise HTTPException(status_code=422, detail="Mối quan hệ không hợp lệ")
    if "relationship" in updates:
        updates["relationship_type"] = updates.pop("relationship")
    for key, value in updates.items():
        setattr(person, key, value)
    _activity(db, customer, actor, "update", "Cập nhật người liên quan", person.full_name)
    db.commit(); db.refresh(person); return person


def delete_related_person(db: Session, customer_id: UUID, person_id: UUID, actor: User) -> None:
    customer = get_customer_detail(db, customer_id, actor)
    _require_update(db, actor, customer)
    person = _get_related_person(db, person_id)
    if person.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="Người liên quan không tồn tại")
    person.deleted_at = datetime.now(timezone.utc)
    _activity(db, customer, actor, "update", "Xóa người liên quan", person.full_name)
    db.commit()
