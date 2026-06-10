from datetime import datetime, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.bookings.constants import ACTIVE_BOOKING_STATUSES, BOOKING_ACTIVITY_LABELS, BOOKING_STATUS_LABELS
from app.models.booking import Booking
from app.models.booking_activity import BookingActivity
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.property_status_history import PropertyStatusHistory
from app.models.property_unit import PropertyUnit
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.booking import BookingActivityCreate, BookingCreate, BookingStatusChange, BookingUpdate
from app.services.audit_service import write_audit_log
from app.services.organization_service import get_accessible_user_ids_for_lead_scope

CREATE_PROPERTY_STATUSES = {"available", "negotiating"}
PROPERTY_RELEASE_BLOCKED_STATUSES = {"sold", "locked", "unavailable"}
DELETE_ALLOWED_STATUSES = {"draft", "cancelled", "expired", "refunded"}

def _scope(user: User, prefix: str) -> str | None:
    if user.is_superuser: return "all"
    permissions = set(get_user_permissions(user))
    return next((scope for scope in ("all", "department", "team", "own") if f"{prefix}.{scope}" in permissions), None)

def _ids(db: Session, user: User, scope: str) -> set[UUID]: return get_accessible_user_ids_for_lead_scope(db, user, scope)

def _can(db: Session, actor: User, booking: Booking, prefix: str) -> bool:
    scope = _scope(actor, prefix)
    if not scope: return False
    if scope == "all": return True
    ids = _ids(db, actor, scope)
    return booking.assigned_user_id in ids or booking.created_by_id in ids

def _require(db: Session, actor: User, booking: Booking, prefix: str, message: str = "Bạn không có quyền thao tác booking này") -> None:
    if not _can(db, actor, booking, prefix): raise HTTPException(status_code=403, detail=message)

def _user(value: User | None) -> dict | None:
    return {"id": value.id, "full_name": value.full_name, "email": value.email} if value else None

def _property(value: PropertyUnit) -> dict:
    project = value.project
    return {"id": value.id, "property_code": value.property_code, "title": value.title, "inventory_status": value.inventory_status, "project": {"id": project.id, "project_code": project.project_code, "name": project.name} if project else None}

def _activity_dict(item: BookingActivity) -> dict:
    return {"id": item.id, "activity_type": item.activity_type, "activity_label": BOOKING_ACTIVITY_LABELS.get(item.activity_type, item.activity_type), "title": item.title, "content": item.content, "old_value": item.old_value, "new_value": item.new_value, "actor": _user(item.actor), "created_at": item.created_at}

def serialize_booking(booking: Booking, detail: bool = False) -> dict:
    customer = booking.customer
    result = {"id": booking.id, "booking_code": booking.booking_code, "customer": {"id": customer.id, "customer_code": customer.customer_code, "full_name": customer.full_name, "primary_phone": customer.primary_phone}, "property": _property(booking.property_unit), "assigned_user": _user(booking.assigned_user), "status": booking.status, "status_label": BOOKING_STATUS_LABELS.get(booking.status, booking.status), "booking_amount": booking.booking_amount, "deposit_amount": booking.deposit_amount, "reservation_expires_at": booking.reservation_expires_at, "created_at": booking.created_at}
    if detail:
        result.update({"customer_id": booking.customer_id, "property_unit_id": booking.property_unit_id, "source_lead_id": booking.source_lead_id, "source_deal_id": booking.source_deal_id, "assigned_user_id": booking.assigned_user_id, "refund_amount": booking.refund_amount, "booking_date": booking.booking_date, "deposit_date": booking.deposit_date, "cancelled_at": booking.cancelled_at, "refunded_at": booking.refunded_at, "cancel_reason": booking.cancel_reason, "refund_reason": booking.refund_reason, "note": booking.note, "created_by": _user(booking.creator), "updated_by": _user(booking.updater), "updated_at": booking.updated_at, "source_lead": {"id": booking.source_lead.id, "code": booking.source_lead.code, "title": booking.source_lead.full_name} if booking.source_lead else None, "source_deal": {"id": booking.source_deal.id, "code": booking.source_deal.deal_code, "title": booking.source_deal.title} if booking.source_deal else None, "activities": [_activity_dict(item) for item in booking.activities]})
    return result

def _next_code(db: Session) -> str:
    # TODO: Replace with database sequence for high-concurrency production.
    codes = db.scalars(select(Booking.booking_code).where(Booking.booking_code.like("BK-%")))
    numbers = [int(code.removeprefix("BK-")) for code in codes if code.removeprefix("BK-").isdigit()]
    return f"BK-{max(numbers, default=0) + 1:06d}"

def _validate_customer(db: Session, customer_id: UUID) -> Customer:
    value = db.scalar(select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None)))
    if not value: raise HTTPException(status_code=400, detail="Khách hàng không tồn tại")
    return value

def _validate_property(db: Session, property_id: UUID, *, lock: bool = False) -> PropertyUnit:
    query = select(PropertyUnit).where(PropertyUnit.id == property_id, PropertyUnit.deleted_at.is_(None))
    value = db.scalar(query.with_for_update() if lock else query)
    if not value: raise HTTPException(status_code=400, detail="Bất động sản không tồn tại")
    return value

def _validate_user(db: Session, user_id: UUID) -> User:
    value = db.scalar(select(User).where(User.id == user_id, User.status == "active", User.deleted_at.is_(None)))
    if not value: raise HTTPException(status_code=400, detail="Người phụ trách không tồn tại")
    return value

def _validate_source(db: Session, model, value: UUID | None, message: str):
    if value is None: return None
    conditions = [model.id == value]
    if hasattr(model, "deleted_at"): conditions.append(model.deleted_at.is_(None))
    item = db.scalar(select(model).where(*conditions))
    if not item: raise HTTPException(status_code=400, detail=message)
    return item

def _active_booking_exists(db: Session, property_id: UUID, exclude_id: UUID | None = None) -> bool:
    conditions = [Booking.property_unit_id == property_id, Booking.deleted_at.is_(None), Booking.status.in_(ACTIVE_BOOKING_STATUSES)]
    if exclude_id: conditions.append(Booking.id != exclude_id)
    return db.scalar(select(Booking.id).where(*conditions).limit(1)) is not None

def _add_activity(db: Session, booking: Booking, actor: User, activity_type: str, title: str | None = None, content: str | None = None, old_value: str | None = None, new_value: str | None = None) -> BookingActivity:
    item = BookingActivity(booking_id=booking.id, actor_id=actor.id, activity_type=activity_type, title=title or BOOKING_ACTIVITY_LABELS[activity_type], content=content, old_value=old_value, new_value=new_value)
    db.add(item); return item

def _change_property_status(db: Session, booking: Booking, actor: User, new_status: str, note: str) -> None:
    prop = booking.property_unit
    if prop.inventory_status == new_status: return
    old_status = prop.inventory_status
    prop.inventory_status = new_status; prop.updated_by_id = actor.id
    db.add(PropertyStatusHistory(property_unit_id=prop.id, changed_by_id=actor.id, old_status=old_status, new_status=new_status, note=note))

def get_booking(db: Session, booking_id: UUID) -> Booking | None:
    return db.scalar(select(Booking).where(Booking.id == booking_id, Booking.deleted_at.is_(None)))

def get_booking_detail(db: Session, booking_id: UUID, actor: User) -> Booking:
    value = get_booking(db, booking_id)
    if not value: raise HTTPException(status_code=404, detail="Không tìm thấy booking")
    _require(db, actor, value, "bookings.view", "Bạn không có quyền xem booking này")
    return value

def list_bookings(db: Session, actor: User, *, page: int = 1, page_size: int = 20, q: str | None = None, customer_id: UUID | None = None, property_unit_id: UUID | None = None, assigned_user_id: UUID | None = None, status: str | None = None, created_from: datetime | None = None, created_to: datetime | None = None, expires_from: datetime | None = None, expires_to: datetime | None = None):
    scope = _scope(actor, "bookings.view")
    if not scope: raise HTTPException(status_code=403, detail="Bạn không có quyền xem booking")
    conditions = [Booking.deleted_at.is_(None)]
    if scope != "all":
        ids = _ids(db, actor, scope); conditions.append(or_(Booking.assigned_user_id.in_(ids), Booking.created_by_id.in_(ids)))
    if q:
        term = f"%{q.strip()}%"; conditions.append(or_(Booking.booking_code.ilike(term), Booking.customer.has(Customer.full_name.ilike(term)), Booking.property_unit.has(or_(PropertyUnit.property_code.ilike(term), PropertyUnit.title.ilike(term)))))
    if customer_id: conditions.append(Booking.customer_id == customer_id)
    if property_unit_id: conditions.append(Booking.property_unit_id == property_unit_id)
    if assigned_user_id: conditions.append(Booking.assigned_user_id == assigned_user_id)
    if status:
        if status not in BOOKING_STATUS_LABELS: raise HTTPException(status_code=400, detail="Trạng thái booking không hợp lệ")
        conditions.append(Booking.status == status)
    if created_from: conditions.append(Booking.created_at >= created_from)
    if created_to: conditions.append(Booking.created_at <= created_to)
    if expires_from: conditions.append(Booking.reservation_expires_at >= expires_from)
    if expires_to: conditions.append(Booking.reservation_expires_at <= expires_to)
    total = db.scalar(select(func.count(Booking.id)).where(*conditions)) or 0
    items = list(db.scalars(select(Booking).where(*conditions).order_by(Booking.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
    return items, {"page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}

def create_booking(db: Session, payload: BookingCreate, actor: User) -> Booking:
    _validate_customer(db, payload.customer_id); prop = _validate_property(db, payload.property_unit_id, lock=True); _validate_user(db, payload.assigned_user_id)
    _validate_source(db, Lead, payload.source_lead_id, "Lead nguồn không tồn tại"); _validate_source(db, Deal, payload.source_deal_id, "Giao dịch nguồn không tồn tại")
    if prop.inventory_status not in CREATE_PROPERTY_STATUSES: raise HTTPException(status_code=400, detail="Bất động sản hiện không khả dụng để giữ chỗ")
    if _active_booking_exists(db, prop.id): raise HTTPException(status_code=409, detail="Bất động sản đã có booking đang hoạt động")
    data = payload.model_dump(); data["booking_date"] = data["booking_date"] or datetime.now(timezone.utc)
    booking = Booking(**data, booking_code=_next_code(db), status="draft", created_by_id=actor.id)
    db.add(booking); db.flush(); _add_activity(db, booking, actor, "created")
    write_audit_log(db, action="bookings.create", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id), after_data={"booking_code": booking.booking_code, "status": booking.status})
    db.commit(); db.refresh(booking); return booking

def update_booking(db: Session, booking_id: UUID, payload: BookingUpdate, actor: User) -> Booking:
    booking = get_booking(db, booking_id)
    if not booking: raise HTTPException(status_code=404, detail="Không tìm thấy booking")
    _require(db, actor, booking, "bookings.update")
    data = payload.model_dump(exclude_unset=True)
    if "assigned_user_id" in data: _validate_user(db, data["assigned_user_id"])
    changes = {key: (getattr(booking, key), value) for key, value in data.items() if getattr(booking, key) != value}
    for key, value in data.items(): setattr(booking, key, value)
    booking.updated_by_id = actor.id
    if changes: _add_activity(db, booking, actor, "updated", content=", ".join(changes), old_value=str({k: str(v[0]) for k, v in changes.items()}), new_value=str({k: str(v[1]) for k, v in changes.items()}))
    write_audit_log(db, action="bookings.update", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id), before_data={k: str(v[0]) for k, v in changes.items()}, after_data={k: str(v[1]) for k, v in changes.items()})
    db.commit(); db.refresh(booking); return booking

def change_booking_status(db: Session, booking_id: UUID, payload: BookingStatusChange, actor: User) -> Booking:
    booking = get_booking(db, booking_id)
    if not booking: raise HTTPException(status_code=404, detail="Không tìm thấy booking")
    prefix = "bookings.refund" if payload.status == "refunded" else "bookings.status"
    _require(db, actor, booking, prefix)
    now = datetime.now(timezone.utc)
    if payload.status == "reserved" and payload.reservation_expires_at and payload.reservation_expires_at <= now: raise HTTPException(status_code=400, detail="Ngày hết hạn giữ chỗ không hợp lệ")
    if payload.status in ACTIVE_BOOKING_STATUSES and _active_booking_exists(db, booking.property_unit_id, booking.id): raise HTTPException(status_code=409, detail="Bất động sản đã có booking đang hoạt động")
    old_status = booking.status; data = payload.model_dump(exclude_unset=True); data.pop("status", None)
    for key, value in data.items(): setattr(booking, key, value)
    booking.status = payload.status; booking.updated_by_id = actor.id
    if payload.status == "reserved":
        _change_property_status(db, booking, actor, "reserved", f"Tự động cập nhật từ booking {booking.booking_code}")
    elif payload.status == "deposited":
        booking.deposit_date = booking.deposit_date or now
        _change_property_status(db, booking, actor, "deposited", f"Tự động cập nhật từ booking {booking.booking_code}")
    elif payload.status == "cancelled":
        booking.cancelled_at = now
        if booking.property_unit.inventory_status != "sold": _change_property_status(db, booking, actor, "available", f"Booking {booking.booking_code} đã hủy")
    elif payload.status == "expired":
        if booking.property_unit.inventory_status != "sold": _change_property_status(db, booking, actor, "available", f"Booking {booking.booking_code} đã hết hạn")
    elif payload.status == "refunded":
        booking.refunded_at = now
        if booking.property_unit.inventory_status not in PROPERTY_RELEASE_BLOCKED_STATUSES: _change_property_status(db, booking, actor, "available", f"Booking {booking.booking_code} đã hoàn tiền")
    _add_activity(db, booking, actor, payload.status if payload.status != "draft" else "status_change", content=payload.note, old_value=old_status, new_value=payload.status)
    write_audit_log(db, action="bookings.status_change", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id), before_data={"status": old_status}, after_data={"status": booking.status})
    db.commit(); db.refresh(booking); return booking

def add_booking_activity(db: Session, booking_id: UUID, payload: BookingActivityCreate, actor: User) -> BookingActivity:
    booking = get_booking(db, booking_id)
    if not booking: raise HTTPException(status_code=404, detail="Không tìm thấy booking")
    _require(db, actor, booking, "bookings.update")
    item = _add_activity(db, booking, actor, "note", payload.title, payload.content)
    write_audit_log(db, action="bookings.activity.create", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id))
    db.commit(); db.refresh(item); return item

def soft_delete_booking(db: Session, booking_id: UUID, actor: User) -> None:
    booking = get_booking(db, booking_id)
    if not booking: raise HTTPException(status_code=404, detail="Không tìm thấy booking")
    _require(db, actor, booking, "bookings.delete")
    if booking.status not in DELETE_ALLOWED_STATUSES: raise HTTPException(status_code=400, detail="Không thể xóa booking đang giữ chỗ hoặc đã cọc. Vui lòng hủy booking trước.")
    _add_activity(db, booking, actor, "deleted"); booking.deleted_at = datetime.now(timezone.utc); booking.deleted_by_id = actor.id
    write_audit_log(db, action="bookings.delete", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id)); db.commit()

def list_booking_assignees(db: Session, actor: User) -> list[User]:
    scope = _scope(actor, "bookings.update") or _scope(actor, "bookings.view") or "own"
    ids = _ids(db, actor, scope)
    return list(db.scalars(select(User).where(User.id.in_(ids), User.status == "active", User.deleted_at.is_(None)).order_by(User.full_name)).unique())
