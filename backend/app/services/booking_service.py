from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from types import SimpleNamespace
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.bookings.activity import decode_activity_context, is_status_transition, status_activity_content, status_label
from app.bookings.constants import ACTIVE_BOOKING_STATUSES, BOOKING_ACTIVITY_LABELS, BOOKING_STATUS_LABELS, FINAL_BOOKING_STATUSES
from app.contracts.constants import ACTIVE_DEAL_STATUSES
from app.models.booking import Booking
from app.models.booking_activity import BookingActivity
from app.models.customer import Customer
from app.models.contract import Contract
from app.models.deal import Deal
from app.models.deal_activity import DealActivity
from app.models.lead import Lead
from app.models.property_status_history import PropertyStatusHistory
from app.models.property_unit import PropertyUnit
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.booking import BookingActivityCreate, BookingCreate, BookingStatusChange, BookingUpdate
from app.services.audit_service import write_audit_log
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.task_service import auto_cancel_booking_tasks, auto_task_for_booking_created, auto_task_for_booking_deposited

CREATE_PROPERTY_STATUSES = {"available", "negotiating"}
PROPERTY_RELEASE_BLOCKED_STATUSES = {"sold", "locked", "unavailable"}
DELETE_ALLOWED_STATUSES = {"cancelled", "expired", "refunded"}
EFFECTIVE_CONTRACT_STATUSES = {"signed", "active", "completed"}
EFFECTIVE_CONTRACT_BOOKING_MESSAGE = "Không thể thao tác booking vì đã có hợp đồng hiệu lực. Vui lòng hủy hợp đồng trước."
BOOKING_RELEASE_STATUSES = {"cancelled", "expired", "refunded"}
BOOKING_RELEASE_DEAL_MESSAGES = {
    "cancelled": ("Tự động hủy giao dịch do booking đã hủy", "Booking nguồn đã hủy nên giao dịch được tự động hủy."),
    "expired": ("Tự động hủy giao dịch do booking hết hạn", "Booking nguồn đã hết hạn nên giao dịch được tự động hủy."),
    "refunded": ("Tự động hủy giao dịch do booking đã hoàn tiền", "Booking nguồn đã hoàn tiền nên giao dịch được tự động hủy."),
}

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




def _booking_has_effective_contract(db: Session | None, booking: Booking) -> bool:
    if db is not None:
        direct_contract = db.scalar(
            select(Contract.id)
            .where(
                Contract.booking_id == booking.id,
                Contract.deleted_at.is_(None),
                Contract.status.in_(EFFECTIVE_CONTRACT_STATUSES),
            )
            .limit(1)
        )
        if direct_contract is not None:
            return True
        return db.scalar(
            select(Contract.id)
            .join(Deal, Contract.deal_id == Deal.id)
            .where(
                Deal.booking_id == booking.id,
                Deal.deleted_at.is_(None),
                Contract.deleted_at.is_(None),
                Contract.status.in_(EFFECTIVE_CONTRACT_STATUSES),
            )
            .limit(1)
        ) is not None
    return any(
        contract.deleted_at is None and contract.status in EFFECTIVE_CONTRACT_STATUSES
        for contract in booking.contracts
    ) or any(
        deal.deleted_at is None
        and any(
            contract.deleted_at is None and contract.status in EFFECTIVE_CONTRACT_STATUSES
            for contract in deal.contracts
        )
        for deal in booking.deals
    )



def _property_has_effective_contract(db: Session, property_unit_id: UUID) -> bool:
    return db.scalar(
        select(Contract.id)
        .where(
            Contract.property_unit_id == property_unit_id,
            Contract.deleted_at.is_(None),
            Contract.status.in_(EFFECTIVE_CONTRACT_STATUSES),
        )
        .limit(1)
    ) is not None


def _property_can_be_released(db: Session, property_unit_id: UUID, *, exclude_booking_id: UUID | None = None) -> bool:
    if _property_has_effective_contract(db, property_unit_id):
        return False
    active_booking_conditions = [
        Booking.property_unit_id == property_unit_id,
        Booking.deleted_at.is_(None),
        Booking.status.in_(ACTIVE_BOOKING_STATUSES),
    ]
    if exclude_booking_id is not None:
        active_booking_conditions.append(Booking.id != exclude_booking_id)
    if db.scalar(select(Booking.id).where(*active_booking_conditions).limit(1)) is not None:
        return False
    from app.services.deal_service import _active_deal_conflict_exists
    return not _active_deal_conflict_exists(db, property_unit_id=property_unit_id, exclude_booking_id=exclude_booking_id)

def _block_effective_contract_booking_actions(db: Session, booking: Booking) -> None:
    if _booking_has_effective_contract(db, booking):
        raise HTTPException(status_code=409, detail=EFFECTIVE_CONTRACT_BOOKING_MESSAGE)

def _close_booking_deals(db: Session, booking: Booking, actor: User, target_status: str, changed_at: datetime) -> None:
    """Cancel active Deals created from this Booking after the Booking leaves active holding states."""
    if target_status not in BOOKING_RELEASE_STATUSES:
        return
    title, content = BOOKING_RELEASE_DEAL_MESSAGES[target_status]
    deals = db.scalars(
        select(Deal).where(
            Deal.booking_id == booking.id,
            Deal.deleted_at.is_(None),
            Deal.status.in_(ACTIVE_DEAL_STATUSES),
        )
    ).unique()
    for deal in deals:
        effective_contract = db.scalar(
            select(Contract.id)
            .where(
                Contract.deal_id == deal.id,
                Contract.deleted_at.is_(None),
                Contract.status.in_(EFFECTIVE_CONTRACT_STATUSES),
            )
            .limit(1)
        )
        if effective_contract is not None:
            raise HTTPException(status_code=409, detail=EFFECTIVE_CONTRACT_BOOKING_MESSAGE)
        old_status = deal.status
        deal.status = "cancelled"
        deal.pipeline_stage = "lost"
        deal.closed_at = changed_at
        deal.lost_reason = f"{content} Booking: {booking.booking_code}."
        db.add(
            DealActivity(
                deal_id=deal.id,
                user_id=actor.id,
                activity_type="close_lost",
                title=title,
                content=f"{content} Booking: {booking.booking_code}.",
                old_value=old_status,
                new_value="cancelled",
                metadata_json={"booking_id": str(booking.id), "booking_code": booking.booking_code, "booking_status": target_status},
            )
        )

def _user(value: User | None) -> dict | None:
    return {"id": value.id, "full_name": value.full_name, "email": value.email} if value else None

def _property(value: PropertyUnit) -> dict:
    project = value.project
    return {"id": value.id, "property_code": value.property_code, "title": value.title, "inventory_status": value.inventory_status, "project": {"id": project.id, "project_code": project.project_code, "name": project.name} if project else None}

def _activity_dict(item: BookingActivity) -> dict:
    context = decode_activity_context(item.content)
    transition = is_status_transition(item.old_value, item.new_value)
    return {
        "id": item.id,
        "activity_type": "status_change" if transition else item.activity_type,
        "activity_label": BOOKING_ACTIVITY_LABELS["status_change"] if transition else BOOKING_ACTIVITY_LABELS.get(item.activity_type, item.activity_type),
        "title": "Đổi trạng thái booking" if transition else item.title,
        "content": context.get("note") if transition else item.content,
        "old_value": status_label(item.old_value) if transition else item.old_value,
        "new_value": status_label(item.new_value) if transition else item.new_value,
        "context": context,
        "actor": _user(item.actor),
        "created_at": item.created_at,
    }

def _refund_basis_amount(booking: Booking) -> Decimal:
    return booking.deposit_amount or booking.booking_amount or Decimal("0")

def _deduction_amount(booking: Booking, refund_amount: Decimal | None) -> Decimal | None:
    if refund_amount is None:
        return None
    amount = _refund_basis_amount(booking) - refund_amount
    return amount if amount > 0 else Decimal("0")

def _latest_refund_context(booking: Booking) -> dict:
    refund_activities = [
        item for item in booking.activities
        if item.new_value == "refunded"
    ]
    if not refund_activities:
        return {}
    latest = max(refund_activities, key=lambda item: item.created_at)
    return decode_activity_context(latest.content)

def serialize_booking(booking: Booking, detail: bool = False) -> dict:
    customer = booking.customer
    result = {"id": booking.id, "booking_code": booking.booking_code, "customer": {"id": customer.id, "customer_code": customer.customer_code, "full_name": customer.full_name, "primary_phone": customer.primary_phone}, "property": _property(booking.property_unit), "assigned_user": _user(booking.assigned_user), "status": booking.status, "status_label": BOOKING_STATUS_LABELS.get(booking.status, booking.status), "booking_amount": booking.booking_amount, "deposit_amount": booking.deposit_amount, "reservation_expires_at": booking.reservation_expires_at, "created_at": booking.created_at}
    if detail:
        refund_context = _latest_refund_context(booking)
        result.update({"customer_id": booking.customer_id, "property_unit_id": booking.property_unit_id, "source_lead_id": booking.source_lead_id, "source_deal_id": booking.source_deal_id, "assigned_user_id": booking.assigned_user_id, "refund_amount": booking.refund_amount, "deduction_amount": _deduction_amount(booking, booking.refund_amount), "booking_date": booking.booking_date, "deposit_date": booking.deposit_date, "cancelled_at": booking.cancelled_at, "refunded_at": booking.refunded_at, "cancel_reason": booking.cancel_reason, "refund_reason": booking.refund_reason, "deduction_reason": refund_context.get("deduction_reason"), "note": booking.note, "created_by": _user(booking.creator), "updated_by": _user(booking.updater), "updated_at": booking.updated_at, "source_lead": {"id": booking.source_lead.id, "code": booking.source_lead.code, "title": booking.source_lead.full_name} if booking.source_lead else None, "source_deal": {"id": booking.source_deal.id, "code": booking.source_deal.deal_code, "title": booking.source_deal.title} if booking.source_deal else None, "linked_deals": [{"id": d.id, "deal_code": d.deal_code, "title": d.title, "status": d.status, "expected_value": d.expected_value} for d in booking.deals if d.deleted_at is None], "has_effective_contract": _booking_has_effective_contract(None, booking), "activities": [_activity_dict(item) for item in booking.activities]})
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

def _lock_property_row(db: Session, property_id: UUID) -> None:
    """Lock only the property_units row, without ORM eager joins.

    PropertyUnit.project is configured with joined eager loading. Selecting the
    entity while applying FOR UPDATE therefore adds a nullable LEFT OUTER JOIN
    that PostgreSQL cannot lock. Selecting only the primary-key column keeps
    this statement on the base table while retaining the row lock until the
    transaction completes.
    """
    locked_id = db.scalar(
        select(PropertyUnit.id)
        .where(PropertyUnit.id == property_id, PropertyUnit.deleted_at.is_(None))
        .with_for_update(of=PropertyUnit)
    )
    if locked_id is None:
        raise HTTPException(status_code=400, detail="Bất động sản không tồn tại")


def _validate_property(db: Session, property_id: UUID) -> PropertyUnit:
    query = (
        select(PropertyUnit)
        .where(PropertyUnit.id == property_id, PropertyUnit.deleted_at.is_(None))
        .execution_options(populate_existing=True)
    )
    value = db.scalar(query)
    if not value:
        raise HTTPException(status_code=400, detail="Bất động sản không tồn tại")
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

def _effective_amount(payload_amount, current_amount):
    return payload_amount if payload_amount is not None else current_amount


def _validate_status_amounts(booking: Booking, payload: BookingStatusChange) -> None:
    booking_amount = _effective_amount(payload.booking_amount, booking.booking_amount)
    if payload.status == "reserved" and (booking_amount is None or booking_amount <= 0):
        raise HTTPException(status_code=400, detail="Tiền giữ chỗ là bắt buộc khi giữ chỗ")
    if payload.status == "deposited" and (payload.deposit_amount is None or payload.deposit_amount <= 0):
        raise HTTPException(status_code=400, detail="Tiền cọc là bắt buộc khi đặt cọc")
    if payload.status == "refunded":
        basis_amount = _refund_basis_amount(booking)
        if payload.refund_amount is None:
            raise HTTPException(status_code=400, detail="Số tiền hoàn là bắt buộc")
        if payload.refund_amount < 0:
            raise HTTPException(status_code=400, detail="Số tiền hoàn không được âm")
        if payload.refund_amount > basis_amount:
            raise HTTPException(status_code=400, detail="Số tiền hoàn không được vượt quá số tiền booking.")


def _status_update_data(payload: BookingStatusChange) -> dict:
    common = {"note"}
    fields_by_status = {
        "draft": common,
        "reserved": common | {"booking_amount", "reservation_expires_at"},
        "deposited": common | {"deposit_amount", "deposit_date"},
        "cancelled": common | {"cancel_reason"},
        "expired": common,
        "refunded": common | {"refund_amount", "refund_reason"},
    }
    data = payload.model_dump(exclude_unset=True, include=fields_by_status[payload.status])
    return {key: value for key, value in data.items() if value is not None}

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
    _validate_customer(db, payload.customer_id)
    _lock_property_row(db, payload.property_unit_id)
    prop = _validate_property(db, payload.property_unit_id)
    _validate_user(db, payload.assigned_user_id)
    _validate_source(db, Lead, payload.source_lead_id, "Lead nguồn không tồn tại"); _validate_source(db, Deal, payload.source_deal_id, "Giao dịch nguồn không tồn tại")
    if prop.inventory_status not in CREATE_PROPERTY_STATUSES: raise HTTPException(status_code=400, detail="Bất động sản hiện không khả dụng để giữ chỗ")
    if _active_booking_exists(db, prop.id): raise HTTPException(status_code=409, detail="Bất động sản đã có booking đang hoạt động")
    data = payload.model_dump(); data["booking_date"] = data["booking_date"] or datetime.now(timezone.utc)
    booking = Booking(**data, booking_code=_next_code(db), status="draft", created_by_id=actor.id)
    db.add(booking); db.flush(); _add_activity(db, booking, actor, "created"); auto_task_for_booking_created(db, booking, actor)
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
    _block_effective_contract_booking_actions(db, booking)
    if booking.status in FINAL_BOOKING_STATUSES and payload.status in ACTIVE_BOOKING_STATUSES:
        raise HTTPException(status_code=409, detail="Booking đã kết thúc không thể chuyển lại trạng thái giữ chỗ hoặc đặt cọc.")
    _lock_property_row(db, booking.property_unit_id)
    booking.property_unit = _validate_property(db, booking.property_unit_id)
    now = datetime.now(timezone.utc)
    _validate_status_amounts(booking, payload)
    if payload.status == "reserved" and payload.reservation_expires_at and payload.reservation_expires_at <= now: raise HTTPException(status_code=400, detail="Ngày hết hạn giữ chỗ không hợp lệ")
    if payload.status in ACTIVE_BOOKING_STATUSES and _active_booking_exists(db, booking.property_unit_id, booking.id): raise HTTPException(status_code=409, detail="Bất động sản đã có booking đang hoạt động")
    old_status = booking.status; data = _status_update_data(payload)
    for key, value in data.items(): setattr(booking, key, value)
    booking.status = payload.status; booking.updated_by_id = actor.id
    _close_booking_deals(db, booking, actor, payload.status, now)
    if payload.status == "reserved":
        _change_property_status(db, booking, actor, "reserved", f"Tự động cập nhật từ booking {booking.booking_code}")
    elif payload.status == "deposited":
        booking.deposit_date = booking.deposit_date or now
        auto_task_for_booking_deposited(db, booking, actor)
        _change_property_status(db, booking, actor, "deposited", f"Tự động cập nhật từ booking {booking.booking_code}")
    elif payload.status == "cancelled":
        booking.cancelled_at = now
        if booking.property_unit.inventory_status != "sold" and _property_can_be_released(db, booking.property_unit_id, exclude_booking_id=booking.id): _change_property_status(db, booking, actor, "available", f"Booking {booking.booking_code} đã hủy")
    elif payload.status == "expired":
        if booking.property_unit.inventory_status != "sold" and _property_can_be_released(db, booking.property_unit_id, exclude_booking_id=booking.id): _change_property_status(db, booking, actor, "available", f"Booking {booking.booking_code} đã hết hạn")
    elif payload.status == "refunded":
        booking.refunded_at = now
        if booking.property_unit.inventory_status not in PROPERTY_RELEASE_BLOCKED_STATUSES and _property_can_be_released(db, booking.property_unit_id, exclude_booking_id=booking.id): _change_property_status(db, booking, actor, "available", f"Booking {booking.booking_code} đã hoàn tiền")
    if payload.status in {"cancelled", "expired", "refunded"}:
        auto_cancel_booking_tasks(db, booking, actor)
    activity_payload = payload
    if payload.status == "refunded":
        activity_payload = SimpleNamespace(**payload.model_dump(), deduction_amount=_deduction_amount(booking, booking.refund_amount))
    activity_content = status_activity_content(activity_payload)
    activity_context = decode_activity_context(activity_content)
    _add_activity(db, booking, actor, "status_change", title="Đổi trạng thái booking", content=activity_content, old_value=old_status, new_value=payload.status)
    write_audit_log(db, action="bookings.status_change", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id), before_data={"status": old_status}, after_data={"status": booking.status, **activity_context})
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
    _block_effective_contract_booking_actions(db, booking)
    if booking.status not in DELETE_ALLOWED_STATUSES:
        raise HTTPException(status_code=409, detail="Không thể xóa booking đang hoạt động. Vui lòng hủy booking trước.")
    _add_activity(db, booking, actor, "deleted"); booking.deleted_at = datetime.now(timezone.utc); booking.deleted_by_id = actor.id
    write_audit_log(db, action="bookings.delete", user_id=actor.id, entity_type="bookings", entity_id=str(booking.id)); db.commit()

def list_booking_assignees(db: Session, actor: User) -> list[User]:
    scope = _scope(actor, "bookings.update") or _scope(actor, "bookings.view") or "own"
    ids = _ids(db, actor, scope)
    return list(db.scalars(select(User).where(User.id.in_(ids), User.status == "active", User.deleted_at.is_(None)).order_by(User.full_name)).unique())

def create_deal_from_booking(db: Session, booking_id: UUID, payload, actor: User) -> Deal:
    """Convert one deposited booking into one active closing deal."""
    from app.models.deal_activity import DealActivity
    from app.services.deal_service import _active_deal_conflict_exists, _next_code as next_deal_code
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.deleted_at.is_(None)))
    if not booking: raise HTTPException(status_code=404, detail="Booking không tồn tại")
    if booking.status != "deposited": raise HTTPException(status_code=400, detail="Chỉ booking đã cọc mới được chuyển thành giao dịch.")
    _require(db, actor, booking, "bookings.view", "Bạn không có quyền xem booking này")
    if not (actor.is_superuser or "deals.create" in set(get_user_permissions(actor))): raise HTTPException(status_code=403, detail="Bạn không có quyền tạo giao dịch")
    _lock_property_row(db, booking.property_unit_id)
    prop = _validate_property(db, booking.property_unit_id)
    _validate_customer(db, booking.customer_id)
    if _active_deal_conflict_exists(db, booking_id=booking.id): raise HTTPException(status_code=409, detail="Booking này đã có giao dịch đang hoạt động.")
    if _active_deal_conflict_exists(db, property_unit_id=prop.id): raise HTTPException(status_code=409, detail="Bất động sản này đã có giao dịch đang hoạt động.")
    title = payload.title or f"Giao dịch từ booking {booking.booking_code} - {prop.property_code}"
    expected = payload.expected_value if payload.expected_value is not None else (prop.listed_price or booking.deposit_amount or 0)
    deal = Deal(deal_code=next_deal_code(db), booking_id=booking.id, property_unit_id=prop.id, project_id=prop.project_id, customer_id=booking.customer_id, source_lead_id=booking.source_lead_id, title=title, description=payload.note, deal_type=prop.property_type if prop.property_type in {"apartment","townhouse","villa","land","shophouse","other"} else "other", pipeline_stage="contract", status="contract_pending", priority="medium", project_name=prop.project.name if prop.project else None, property_code=prop.property_code, property_type=prop.property_type, expected_value=expected, deposit_amount=booking.deposit_amount, deposit_date=booking.deposit_date, owner_id=booking.assigned_user_id, created_by_id=actor.id)
    db.add(deal); db.flush(); db.add(DealActivity(deal_id=deal.id,user_id=actor.id,activity_type="contract",title="Tạo giao dịch từ booking",content=payload.note)); _add_activity(db,booking,actor,"updated",title="Tạo giao dịch",content=f"Đã tạo giao dịch {deal.deal_code}")
    if prop.inventory_status not in {"sold","locked","unavailable"}: prop.inventory_status="deposited"
    write_audit_log(db,action="deals.create_from_booking",user_id=actor.id,entity_type="deals",entity_id=str(deal.id),after_data={"booking_id":str(booking.id),"property_unit_id":str(prop.id)})
    db.commit(); db.refresh(deal); return deal
