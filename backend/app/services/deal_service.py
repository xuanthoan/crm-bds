from datetime import datetime, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.contracts.constants import ACTIVE_DEAL_STATUSES
from app.deals.constants import DEAL_PRIORITY_LABELS, DEAL_STATUS_LABELS, PIPELINE_STAGE_LABELS
from app.models.customer import Customer
from app.models.customer_activity import CustomerActivity
from app.models.booking import Booking
from app.models.contract import Contract
from app.models.property_status_history import PropertyStatusHistory
from app.models.deal import Deal
from app.models.deal_activity import DealActivity
from app.models.lead import Lead
from app.models.project import Project
from app.models.property_unit import PropertyUnit
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.deal import DealActivityCreate, DealAssignUpdate, DealCreate, DealStageUpdate, DealStatusUpdate, DealUpdate
from app.services.audit_service import write_audit_log
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.user_service import get_user_by_id, user_role_code_set

ELIGIBLE_OWNER_ROLES = {"admin", "director", "sales_manager", "leader", "sale"}


def _active_deal_conflict_exists(
    db: Session,
    *,
    property_unit_id: UUID | None = None,
    booking_id: UUID | None = None,
    exclude_deal_id: UUID | None = None,
    exclude_booking_id: UUID | None = None,
) -> bool:
    conditions = [Deal.deleted_at.is_(None), Deal.status.in_(ACTIVE_DEAL_STATUSES)]
    if property_unit_id is not None:
        conditions.append(Deal.property_unit_id == property_unit_id)
    if booking_id is not None:
        conditions.append(Deal.booking_id == booking_id)
    if exclude_deal_id is not None:
        conditions.append(Deal.id != exclude_deal_id)
    if exclude_booking_id is not None:
        conditions.append(or_(Deal.booking_id.is_(None), Deal.booking_id != exclude_booking_id))
    for deal in db.scalars(select(Deal).where(*conditions)).unique():
        has_contract = db.scalar(
            select(Contract.id)
            .where(Contract.deal_id == deal.id)
            .limit(1)
        ) is not None
        has_non_cancelled_contract = db.scalar(
            select(Contract.id)
            .where(Contract.deal_id == deal.id, Contract.deleted_at.is_(None), Contract.status != "cancelled")
            .limit(1)
        ) is not None
        if has_contract and not has_non_cancelled_contract:
            continue
        return True
    return False

def _scope(user: User, prefix: str) -> str | None:
    if user.is_superuser: return "all"
    permissions = set(get_user_permissions(user))
    for scope in ("all", "department", "team", "own"):
        if f"{prefix}.{scope}" in permissions: return scope
    return None

def _ids(db: Session, user: User, scope: str) -> set[UUID]: return get_accessible_user_ids_for_lead_scope(db, user, scope)

def _can(db: Session, actor: User, deal: Deal, prefix: str) -> bool:
    scope = _scope(actor, prefix)
    if not scope: return False
    if scope == "all": return True
    ids = _ids(db, actor, scope)
    return deal.owner_id in ids or deal.created_by_id in ids

def _require(db: Session, actor: User, deal: Deal, prefix: str, message: str) -> None:
    if not _can(db, actor, deal, prefix): raise HTTPException(status_code=403, detail=message)

def _user(user: User | None) -> dict | None:
    return {"id": user.id, "full_name": user.full_name, "email": user.email} if user else None

def _activity_dict(item: DealActivity) -> dict:
    return {"id": item.id, "activity_type": item.activity_type, "title": item.title, "content": item.content, "old_value": item.old_value, "new_value": item.new_value, "metadata_json": item.metadata_json, "user": _user(item.user), "created_at": item.created_at}

def serialize_deal(deal: Deal) -> dict:
    customer = deal.customer
    return {"id": deal.id, "deal_code": deal.deal_code, "booking_id": deal.booking_id, "property_unit_id": deal.property_unit_id, "project_id": deal.project_id, "customer_id": deal.customer_id, "source_lead_id": deal.source_lead_id, "title": deal.title, "description": deal.description, "deal_type": deal.deal_type, "pipeline_stage": deal.pipeline_stage, "status": deal.status, "priority": deal.priority, "project_name": deal.project_name, "property_code": deal.property_code, "property_type": deal.property_type, "area": deal.area, "expected_value": deal.expected_value, "deposit_amount": deal.deposit_amount, "contract_value": deal.contract_value, "commission_expected": deal.commission_expected, "expected_close_date": deal.expected_close_date, "deposit_date": deal.deposit_date, "contract_date": deal.contract_date, "closed_at": deal.closed_at, "lost_reason": deal.lost_reason, "owner": _user(deal.owner), "created_by": _user(deal.creator), "assigned_by": _user(deal.assigner), "assigned_at": deal.assigned_at, "customer": {"id": customer.id, "customer_code": customer.customer_code, "full_name": customer.full_name, "primary_phone": customer.primary_phone, "owner": _user(customer.owner)} if customer else None, "source_lead": {"id": deal.source_lead.id, "code": deal.source_lead.code, "full_name": deal.source_lead.full_name} if deal.source_lead else None, "created_at": deal.created_at, "updated_at": deal.updated_at}

def serialize_deal_detail(deal: Deal) -> dict:
    return {**serialize_deal(deal), "booking": {"id": deal.booking.id, "booking_code": deal.booking.booking_code, "status": deal.booking.status} if deal.booking else None, "property": {"id": deal.property_unit.id, "property_code": deal.property_unit.property_code, "title": deal.property_unit.title} if deal.property_unit else None, "project": {"id": deal.project.id, "project_code": deal.project.project_code, "name": deal.project.name} if deal.project else None, "contracts": [{"id": c.id, "contract_code": c.contract_code, "status": c.status, "contract_value": c.contract_value} for c in deal.contracts if c.deleted_at is None], "activities": [_activity_dict(item) for item in deal.activities]}

def _next_code(db: Session) -> str:
    # TODO: Replace with database sequence for high-concurrency production.
    codes = db.scalars(select(Deal.deal_code).where(Deal.deal_code.like("DL-%")))
    numbers = [int(code.removeprefix("DL-")) for code in codes if code.removeprefix("DL-").isdigit()]
    return f"DL-{max(numbers, default=0) + 1:06d}"

def _validate_customer(db: Session, customer_id: UUID) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None)))
    if not customer: raise HTTPException(status_code=400, detail="Khách hàng không tồn tại")
    return customer

def _validate_lead(db: Session, lead_id: UUID | None) -> Lead | None:
    if lead_id is None: return None
    lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.deleted_at.is_(None)))
    if not lead: raise HTTPException(status_code=400, detail="Lead nguồn không tồn tại")
    return lead

def _validate_project(db: Session, project_id: UUID | None) -> Project | None:
    if project_id is None:
        return None
    project = db.scalar(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    if not project:
        raise HTTPException(status_code=400, detail="Dự án không tồn tại")
    return project

def _property_link_data(
    db: Session,
    property_unit_id: UUID,
    project_id: UUID | None,
    *,
    require_available: bool,
) -> dict:
    property_unit = db.scalar(select(PropertyUnit).where(PropertyUnit.id == property_unit_id))
    if not property_unit:
        raise HTTPException(status_code=400, detail="Bất động sản không tồn tại")
    if property_unit.deleted_at is not None:
        raise HTTPException(status_code=400, detail="Bất động sản đã bị xóa")
    if require_available and property_unit.inventory_status != "available":
        raise HTTPException(status_code=400, detail="Bất động sản không còn khả dụng để tạo giao dịch mới.")
    if project_id is not None and project_id != property_unit.project_id:
        raise HTTPException(status_code=400, detail="Dự án không khớp với bất động sản đã chọn.")
    project = property_unit.project
    return {
        "property_unit_id": property_unit.id,
        "property_code": property_unit.property_code,
        "property_type": property_unit.property_type,
        "area": str(property_unit.area_net or property_unit.area_gross) if (property_unit.area_net or property_unit.area_gross) is not None else None,
        "project_id": property_unit.project_id,
        "project_name": project.name if project else None,
        "_listed_price": property_unit.listed_price,
    }

def _apply_inventory_link(
    db: Session,
    data: dict,
    *,
    require_available: bool,
) -> None:
    if "property_unit_id" in data and data["property_unit_id"] is not None:
        linked = _property_link_data(
            db,
            data["property_unit_id"],
            data.get("project_id"),
            require_available=require_available,
        )
        listed_price = linked.pop("_listed_price")
        data.update(linked)
        if data.get("expected_value") is None and listed_price is not None:
            data["expected_value"] = listed_price
        return
    if "project_id" in data:
        project = _validate_project(db, data["project_id"])
        data["project_name"] = project.name if project else None
    if "property_unit_id" in data and data["property_unit_id"] is None:
        data.update(property_code=None, property_type=None, area=None)

def _validate_owner(db: Session, actor: User, owner_id: UUID, *, assigning: bool = False) -> User:
    owner = get_user_by_id(db, owner_id)
    if not owner or owner.status != "active" or owner.deleted_at is not None or not (owner.is_superuser or user_role_code_set(owner) & ELIGIBLE_OWNER_ROLES): raise HTTPException(status_code=400, detail="Người phụ trách không hợp lệ")
    scope = _scope(actor, "deals.assign")
    if assigning and not scope: raise HTTPException(status_code=403, detail="Bạn không có quyền phân công giao dịch này")
    if scope and scope != "all" and owner.id not in _ids(db, actor, scope): raise HTTPException(status_code=400, detail="Người phụ trách không hợp lệ")
    if not scope and owner.id != actor.id: raise HTTPException(status_code=400, detail="Người phụ trách không hợp lệ")
    return owner

def _add(db: Session, deal: Deal, actor: User, activity_type: str, title: str, content: str | None = None, old_value: str | None = None, new_value: str | None = None, metadata_json: dict | None = None) -> DealActivity:
    item = DealActivity(deal_id=deal.id, user_id=actor.id, activity_type=activity_type, title=title, content=content, old_value=old_value, new_value=new_value, metadata_json=metadata_json); db.add(item); return item

def _get(db: Session, deal_id: UUID) -> Deal:
    deal = db.scalar(select(Deal).where(Deal.id == deal_id, Deal.deleted_at.is_(None)))
    if not deal: raise HTTPException(status_code=404, detail="Giao dịch không tồn tại")
    return deal

def get_deal_detail(db: Session, deal_id: UUID, actor: User) -> Deal:
    deal = _get(db, deal_id); _require(db, actor, deal, "deals.view", "Bạn không có quyền truy cập giao dịch này"); return deal

def list_deals(db: Session, actor: User, *, page: int, page_size: int, q: str | None = None, customer_id: UUID | None = None, owner_id: UUID | None = None, pipeline_stage: str | None = None, status: str | None = None, priority: str | None = None, deal_type: str | None = None, expected_close_from: datetime | None = None, expected_close_to: datetime | None = None, created_from: datetime | None = None, created_to: datetime | None = None):
    scope = _scope(actor, "deals.view")
    if not scope: raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập giao dịch này")
    conditions = [Deal.deleted_at.is_(None)]
    if scope != "all":
        ids = _ids(db, actor, scope); conditions.append(or_(Deal.owner_id.in_(ids), Deal.created_by_id.in_(ids)))
    if q:
        term=f"%{q.strip()}%"; conditions.append(or_(Deal.deal_code.ilike(term), Deal.title.ilike(term), Deal.customer.has(or_(Customer.full_name.ilike(term), Customer.primary_phone.ilike(term)))))
    for column, value in ((Deal.customer_id, customer_id), (Deal.owner_id, owner_id), (Deal.pipeline_stage, pipeline_stage), (Deal.status, status), (Deal.priority, priority), (Deal.deal_type, deal_type)):
        if value is not None: conditions.append(column == value)
    if expected_close_from: conditions.append(Deal.expected_close_date >= expected_close_from)
    if expected_close_to: conditions.append(Deal.expected_close_date <= expected_close_to)
    if created_from: conditions.append(Deal.created_at >= created_from)
    if created_to: conditions.append(Deal.created_at <= created_to)
    total = db.scalar(select(func.count(Deal.id)).where(*conditions)) or 0
    items = list(db.scalars(select(Deal).where(*conditions).order_by(Deal.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique())
    return items, {"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}

def create_deal(db: Session, payload: DealCreate, actor: User) -> Deal:
    data=payload.model_dump(); _validate_customer(db, data.pop("customer_id")); _validate_lead(db, data.get("source_lead_id")); owner=_validate_owner(db, actor, data.pop("owner_id"))
    _apply_inventory_link(db, data, require_available=True)
    if data.get("property_unit_id") is not None and _active_deal_conflict_exists(db, property_unit_id=data["property_unit_id"]):
        raise HTTPException(status_code=409, detail="Bất động sản này đã có giao dịch đang hoạt động.")
    now=datetime.now(timezone.utc)
    if data.get("pipeline_stage") == "completed": data["status"] = "won"; data["closed_at"] = data.get("closed_at") or now
    elif data.get("pipeline_stage") == "lost": data["status"] = "lost"; data["closed_at"] = data.get("closed_at") or now
    elif data.get("status") in {"won", "lost", "cancelled"}: data["closed_at"] = data.get("closed_at") or now
    deal=Deal(**data, customer_id=payload.customer_id, owner_id=owner.id, created_by_id=actor.id, deal_code=_next_code(db)); db.add(deal); db.flush()
    _add(db, deal, actor, "update", "Tạo giao dịch", deal.title)
    if deal.status == "won": _add(db, deal, actor, "close_won", "Chốt thành công")
    elif deal.status in {"lost", "cancelled"}: _add(db, deal, actor, "close_lost", "Thất bại / Hủy", deal.lost_reason)
    write_audit_log(db, action="deals.create", user_id=actor.id, entity_type="deals", entity_id=str(deal.id), after_data={"deal_code":deal.deal_code}); db.commit(); db.refresh(deal); return deal

def update_deal(db: Session, deal_id: UUID, payload: DealUpdate, actor: User) -> Deal:
    deal=_get(db,deal_id); _require(db,actor,deal,"deals.update","Bạn không có quyền cập nhật giao dịch này"); before=serialize_deal(deal); data=payload.model_dump(exclude_unset=True)
    for protected in ("pipeline_stage", "status", "closed_at", "deposit_date", "contract_date", "lost_reason"):
        data.pop(protected, None)
    if "property_unit_id" in data:
        require_available = data["property_unit_id"] != deal.property_unit_id
        _apply_inventory_link(db, data, require_available=require_available)
    elif "project_id" in data:
        if deal.property_unit_id is not None and data["project_id"] != deal.project_id:
            raise HTTPException(status_code=400, detail="Dự án không khớp với bất động sản đã chọn.")
        _apply_inventory_link(db, data, require_available=False)
    for key,value in data.items(): setattr(deal,key,value)
    if deal.contract_value is not None and deal.deposit_amount is not None and deal.contract_value < deal.deposit_amount: raise HTTPException(status_code=400,detail="Giá trị hợp đồng phải lớn hơn hoặc bằng tiền đặt cọc")
    _add(db,deal,actor,"update","Cập nhật giao dịch"); write_audit_log(db,action="deals.update",user_id=actor.id,entity_type="deals",entity_id=str(deal.id),before_data={"title":before["title"]},after_data={"title":deal.title}); db.commit(); db.refresh(deal); return deal

def change_deal_stage(db: Session, deal_id: UUID, payload: DealStageUpdate, actor: User) -> Deal:
    deal=_get(db,deal_id); _require(db,actor,deal,"deals.stage","Bạn không có quyền đổi giai đoạn giao dịch này"); old=deal.pipeline_stage; data=payload.model_dump(exclude={"note"},exclude_unset=True)
    for key,value in data.items(): setattr(deal,key,value)
    if deal.contract_value is not None and deal.deposit_amount is not None and deal.contract_value < deal.deposit_amount: raise HTTPException(status_code=400,detail="Giá trị hợp đồng phải lớn hơn hoặc bằng tiền đặt cọc")
    now=datetime.now(timezone.utc)
    if deal.pipeline_stage=="completed": deal.status="won"; deal.closed_at=deal.closed_at or now
    if deal.pipeline_stage=="lost": deal.status="lost"; deal.closed_at=deal.closed_at or now
    _add(db,deal,actor,"stage_change","Đổi giai đoạn",payload.note,PIPELINE_STAGE_LABELS[old],PIPELINE_STAGE_LABELS[deal.pipeline_stage])
    if deal.pipeline_stage=="deposit": _add(db,deal,actor,"deposit","Ghi nhận đặt cọc",payload.note)
    if deal.pipeline_stage=="contract": _add(db,deal,actor,"contract","Ghi nhận ký hợp đồng",payload.note)
    if deal.pipeline_stage=="completed": _add(db,deal,actor,"close_won","Chốt thành công",payload.note)
    if deal.pipeline_stage=="lost": _add(db,deal,actor,"close_lost","Thất bại / Hủy",deal.lost_reason)
    write_audit_log(db,action="deals.stage_change",user_id=actor.id,entity_type="deals",entity_id=str(deal.id),before_data={"pipeline_stage":old},after_data={"pipeline_stage":deal.pipeline_stage}); db.commit(); db.refresh(deal); return deal

def change_deal_status(db: Session, deal_id: UUID, payload: DealStatusUpdate, actor: User) -> Deal:
    deal=_get(db,deal_id); _require(db,actor,deal,"deals.status","Bạn không có quyền đổi trạng thái giao dịch này"); old=deal.status
    if payload.status == "contracted" and not db.scalar(select(Contract.id).where(Contract.deal_id == deal.id, Contract.deleted_at.is_(None), Contract.status.in_({"signed", "active", "completed"})).limit(1)): raise HTTPException(status_code=400, detail="Giao dịch phải có hợp đồng đã ký trước khi chuyển trạng thái.")
    deal.status=payload.status
    if payload.lost_reason is not None: deal.lost_reason=payload.lost_reason
    if deal.status in {"won","completed","lost","cancelled"}: deal.closed_at=payload.closed_at or deal.closed_at or datetime.now(timezone.utc)
    _add(db,deal,actor,"status_change","Đổi trạng thái",payload.note,DEAL_STATUS_LABELS[old],DEAL_STATUS_LABELS[deal.status])
    if deal.status=="won": _add(db,deal,actor,"close_won","Chốt thành công",payload.note)
    elif deal.status in {"lost","cancelled"}:
        _add(db,deal,actor,"close_lost","Thất bại / Hủy",deal.lost_reason)
        if deal.property_unit and deal.property_unit.inventory_status != "sold":
            active_booking = db.scalar(select(Booking.id).where(Booking.property_unit_id == deal.property_unit_id, Booking.deleted_at.is_(None), Booking.status.in_({"draft", "reserved", "deposited"})).limit(1))
            active_deal = db.scalar(select(Deal.id).where(Deal.property_unit_id == deal.property_unit_id, Deal.id != deal.id, Deal.deleted_at.is_(None), Deal.status.in_({"open", "negotiating", "contract_pending", "contracted", "payment_in_progress"})).limit(1))
            if not active_booking and not active_deal:
                previous = deal.property_unit.inventory_status; deal.property_unit.inventory_status = "available"; deal.property_unit.updated_by_id = actor.id; db.add(PropertyStatusHistory(property_unit_id=deal.property_unit_id, changed_by_id=actor.id, old_status=previous, new_status="available", note=f"Tự động cập nhật từ giao dịch {deal.deal_code}"))
    write_audit_log(db,action="deals.status_change",user_id=actor.id,entity_type="deals",entity_id=str(deal.id),before_data={"status":old},after_data={"status":deal.status}); db.commit(); db.refresh(deal); return deal

def assign_deal_owner(db: Session, deal_id: UUID, payload: DealAssignUpdate, actor: User) -> Deal:
    deal=_get(db,deal_id); _require(db,actor,deal,"deals.assign","Bạn không có quyền phân công giao dịch này"); owner=_validate_owner(db,actor,payload.owner_id,assigning=True); old_name=deal.owner.full_name if deal.owner else "Chưa phân công"; deal.owner_id=owner.id; deal.assigned_by_id=actor.id; deal.assigned_at=datetime.now(timezone.utc); _add(db,deal,actor,"assign","Phân công giao dịch",payload.note,old_name,owner.full_name); write_audit_log(db,action="deals.assign",user_id=actor.id,entity_type="deals",entity_id=str(deal.id),after_data={"owner_name":owner.full_name}); db.commit(); db.refresh(deal); return deal

def add_deal_activity(db: Session, deal_id: UUID, payload: DealActivityCreate, actor: User) -> DealActivity:
    deal=_get(db,deal_id); _require(db,actor,deal,"deals.add_activity","Bạn không có quyền thêm hoạt động giao dịch này"); item=_add(db,deal,actor,payload.activity_type,payload.title,payload.content,metadata_json=payload.metadata_json); db.flush(); write_audit_log(db,action="deals.add_activity",user_id=actor.id,entity_type="deals",entity_id=str(deal.id),after_data={"activity_type":payload.activity_type}); db.commit(); db.refresh(item); return item

def soft_delete_deal(db: Session, deal_id: UUID, actor: User) -> None:
    deal = _get(db, deal_id)
    _require(db, actor, deal, "deals.delete", "Bạn không có quyền xóa giao dịch này")
    deleted_at = datetime.now(timezone.utc)
    deal.deleted_at = deleted_at
    deal.deleted_by_id = actor.id
    expected_value = (
        f"{deal.expected_value:,.0f}".replace(",", ".") + " ₫"
        if deal.expected_value is not None
        else "Chưa cập nhật"
    )
    customer_activity = CustomerActivity(
        customer_id=deal.customer_id,
        user_id=actor.id,
        activity_type="update",
        title="Xóa giao dịch",
        content=(
            f"Mã giao dịch: {deal.deal_code}\n"
            f"Tên giao dịch: {deal.title}\n"
            f"Giá trị dự kiến: {expected_value}\n"
            f"Người xóa: {actor.full_name}\n"
            f"Thời gian xóa: {deleted_at.strftime('%d/%m/%Y %H:%M:%S UTC')}"
        ),
    )
    db.add(customer_activity)
    write_audit_log(db, action="deals.delete", user_id=actor.id, entity_type="deals", entity_id=str(deal.id))
    db.commit()

def list_deal_assignees(db: Session, actor: User) -> list[User]:
    scope=_scope(actor,"deals.assign")
    if not scope: return [actor] if (actor.is_superuser or user_role_code_set(actor)&ELIGIBLE_OWNER_ROLES) else []
    ids=_ids(db,actor,scope); users=db.scalars(select(User).where(User.id.in_(ids),User.status=="active",User.deleted_at.is_(None)).order_by(User.full_name)).unique()
    return [user for user in users if user.is_superuser or user_role_code_set(user)&ELIGIBLE_OWNER_ROLES]
