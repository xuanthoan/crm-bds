from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.contracts.constants import ACTIVE_CONTRACT_STATUSES, CONTRACT_ACTIVITY_LABELS, CONTRACT_STATUS_LABELS, CONTRACT_TYPE_LABELS, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, PAYMENT_TYPE_LABELS
from app.models.contract import Contract
from app.models.contract_activity import ContractActivity
from app.models.contract_payment import ContractPayment
from app.models.booking import Booking
from app.models.deal import Deal
from app.models.deal_activity import DealActivity
from app.models.property_status_history import PropertyStatusHistory
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.contract import ContractActivityCreate, ContractCreate, ContractPaymentConfirm, ContractPaymentCreate, ContractPaymentUpdate, ContractStatusChange, ContractUpdate
from app.services.audit_service import write_audit_log
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.task_service import auto_complete_contract_payment_tasks, auto_task_for_contract_payment

def _scope(user,prefix):
    if user.is_superuser:return "all"
    perms=set(get_user_permissions(user))
    for scope in ("all","department","team","own"):
        if f"{prefix}.{scope}" in perms:return scope
    return None
def _can(db,user,item,prefix):
    scope=_scope(user,prefix)
    if not scope:return False
    if scope=="all":return True
    ids=get_accessible_user_ids_for_lead_scope(db,user,scope); return item.created_by_id in ids or item.deal.owner_id in ids or item.deal.created_by_id in ids
def _require(db,user,item,prefix,msg="Bạn không có quyền thao tác hợp đồng này"):
    if not _can(db,user,item,prefix):raise HTTPException(403,msg)
def _get(db,id):
    item=db.scalar(select(Contract).where(Contract.id==id,Contract.deleted_at.is_(None)))
    if not item:raise HTTPException(404,"Hợp đồng không tồn tại")
    return item
def _payment(db,contract_id,id):
    item=db.scalar(select(ContractPayment).where(ContractPayment.id==id,ContractPayment.contract_id==contract_id,ContractPayment.deleted_at.is_(None)))
    if not item:raise HTTPException(404,"Thanh toán không tồn tại")
    return item
def _next(db,model,column,prefix):
    # TODO: Use database sequences later.
    codes=db.scalars(select(column).where(column.like(f"{prefix}-%"))); nums=[int(x.split("-")[-1]) for x in codes if x.split("-")[-1].isdigit()]; return f"{prefix}-{max(nums,default=0)+1:06d}"
def add_contract_activity(db,contract,actor,activity_type,title=None,content=None,old_value=None,new_value=None,metadata=None):
    item=ContractActivity(contract_id=contract.id,actor_id=actor.id,activity_type=activity_type,title=title or CONTRACT_ACTIVITY_LABELS.get(activity_type,activity_type),content=content,old_value=old_value,new_value=new_value,metadata_json=metadata); db.add(item); return item
def _sell_property(db,contract,actor):
    prop=contract.property_unit
    if prop.inventory_status!="sold":
        old=prop.inventory_status; prop.inventory_status="sold"; prop.updated_by_id=actor.id; db.add(PropertyStatusHistory(property_unit_id=prop.id,changed_by_id=actor.id,old_status=old,new_status="sold",note=f"Tự động cập nhật từ giao dịch {contract.deal.deal_code}"))


def _rollback_cancelled_contract(db, contract, actor, old_status, note=None):
    if old_status not in {"signed", "active", "completed"}:
        return None
    other_effective_contract = db.scalar(
        select(Contract.id).where(
            Contract.property_unit_id == contract.property_unit_id,
            Contract.id != contract.id,
            Contract.deleted_at.is_(None),
            Contract.status.in_({"signed", "active", "completed"}),
        ).limit(1)
    )
    if other_effective_contract:
        return None

    deal = contract.deal
    old_stage = deal.pipeline_stage
    old_deal_status = deal.status
    deal.pipeline_stage = "contract"
    deal.status = "contract_pending"
    deal.closed_at = None

    active_deposit_booking = db.scalar(
        select(Booking.id).where(
            Booking.property_unit_id == contract.property_unit_id,
            Booking.deleted_at.is_(None),
            Booking.status == "deposited",
        ).limit(1)
    )
    target_property_status = "deposited" if active_deposit_booking else "available"
    prop = contract.property_unit
    old_property_status = prop.inventory_status
    if old_property_status != target_property_status:
        prop.inventory_status = target_property_status
        prop.updated_by_id = actor.id
        reason = f"Hủy hợp đồng {contract.contract_code}; khôi phục trạng thái từ giao dịch {deal.deal_code}"
        if note:
            reason += f". Lý do: {note.strip()}"
        db.add(PropertyStatusHistory(
            property_unit_id=prop.id,
            changed_by_id=actor.id,
            old_status=old_property_status,
            new_status=target_property_status,
            note=reason,
        ))

    rollback_content = (
        f"Hợp đồng {contract.contract_code} đã hủy. "
        f"Giao dịch được đưa từ giai đoạn {old_stage} về Ký hợp đồng; "
        f"trạng thái từ {old_deal_status} về Chờ hợp đồng. "
        f"Bất động sản được khôi phục về {'Đã cọc' if active_deposit_booking else 'Còn hàng'}."
    )
    if note:
        rollback_content += f"\nGhi chú: {note.strip()}"
    activity = DealActivity(
        deal_id=deal.id,
        user_id=actor.id,
        activity_type="contract_rollback",
        title="Khôi phục giao dịch do hủy hợp đồng",
        content=rollback_content,
        old_value="Đã ký hợp đồng",
        new_value="Ký hợp đồng",
        metadata_json={
            "contract_id": str(contract.id),
            "contract_code": contract.contract_code,
            "property_old_status": old_property_status,
            "property_new_status": target_property_status,
            "booking_deposit_active": bool(active_deposit_booking),
            "note": note.strip() if note else None,
        },
    )
    db.add(activity)
    return activity
def _deal_contract_activity(db, contract, actor, old_status, new_status, note=None):
    titles = {
        "signed": "Hợp đồng đã ký",
        "active": "Hợp đồng có hiệu lực",
        "completed": "Hợp đồng hoàn tất",
        "cancelled": "Hợp đồng đã hủy",
    }
    if new_status not in titles:
        return None
    old_label = CONTRACT_STATUS_LABELS[old_status]
    new_label = CONTRACT_STATUS_LABELS[new_status]
    if new_status == "completed":
        content = f"Hợp đồng {contract.contract_code} đã hoàn tất nên giao dịch được chốt thành công."
    else:
        content = f"Hợp đồng {contract.contract_code} đã chuyển sang trạng thái {new_label}."
    if note:
        content += f"\nGhi chú: {note.strip()}"
    activity = DealActivity(
        deal_id=contract.deal_id,
        user_id=actor.id,
        activity_type="contract_status",
        title=titles[new_status],
        content=content,
        old_value=old_label,
        new_value=new_label,
        metadata_json={
            "contract_id": str(contract.id),
            "contract_code": contract.contract_code,
            "old_status_label": old_label,
            "new_status_label": new_label,
            "note": note.strip() if note else None,
        },
    )
    db.add(activity)
    return activity


def _apply_status(db, contract, actor, status):
    if status in {"signed", "active"}:
        contract.deal.status = "contracted"
        contract.deal.pipeline_stage = "contract_signed"
        contract.deal.contract_date = contract.signed_date or contract.deal.contract_date or datetime.now(timezone.utc)
        _sell_property(db, contract, actor)
    elif status == "completed":
        contract.deal.status = "completed"
        contract.deal.pipeline_stage = "completed"
        contract.deal.closed_at = datetime.now(timezone.utc)
        _sell_property(db, contract, actor)

def totals(contract):
    active = [payment for payment in contract.payments if payment.deleted_at is None]
    paid = sum((payment.amount for payment in active if payment.status == "paid"), Decimal("0"))
    planned = sum((payment.amount for payment in active if payment.status in {"planned", "overdue"}), Decimal("0"))
    deposit = contract.deposit_value or Decimal("0")
    remaining = max(contract.contract_value - deposit - paid, Decimal("0"))
    return paid, planned, remaining


def _receivable_amount(contract):
    return max(contract.contract_value - (contract.deposit_value or Decimal("0")), Decimal("0"))


def _validate_payment_capacity(db, contract, amount, *, exclude_payment_id=None, paid_only=False):
    statuses = {"paid"} if paid_only else {"planned", "overdue", "paid"}
    conditions = [
        ContractPayment.contract_id == contract.id,
        ContractPayment.deleted_at.is_(None),
        ContractPayment.status.in_(statuses),
    ]
    if exclude_payment_id is not None:
        conditions.append(ContractPayment.id != exclude_payment_id)
    current = db.scalar(select(func.coalesce(func.sum(ContractPayment.amount), 0)).where(*conditions)) or Decimal("0")
    if Decimal(current) + amount > _receivable_amount(contract):
        raise HTTPException(400, "Số tiền thanh toán vượt quá số tiền còn phải thu của hợp đồng.")
def serialize_contract(item,detail=False):
    paid,planned,remaining=totals(item); data={"id":item.id,"contract_code":item.contract_code,"deal_id":item.deal_id,"booking_id":item.booking_id,"customer_id":item.customer_id,"property_unit_id":item.property_unit_id,"project_id":item.project_id,"contract_type":item.contract_type,"contract_type_label":CONTRACT_TYPE_LABELS[item.contract_type],"status":item.status,"status_label":CONTRACT_STATUS_LABELS[item.status],"contract_number":item.contract_number,"signed_date":item.signed_date,"contract_value":item.contract_value,"deposit_value":item.deposit_value,"deposit_amount":item.deposit_value or Decimal("0"),"total_paid":paid,"total_planned":planned,"remaining_amount":remaining,"customer":{"id":item.customer.id,"customer_code":item.customer.customer_code,"full_name":item.customer.full_name},"property":{"id":item.property_unit.id,"property_code":item.property_unit.property_code,"title":item.property_unit.title},"project":{"id":item.project.id,"project_code":item.project.project_code,"name":item.project.name} if item.project else None,"deal":{"id":item.deal.id,"deal_code":item.deal.deal_code,"title":item.deal.title,"status":item.deal.status},"created_at":item.created_at}
    if detail:data.update({k:getattr(item,k) for k in ("effective_date","handover_date","buyer_name","buyer_phone","buyer_email","buyer_id_number","buyer_address","seller_name","seller_phone","seller_email","seller_representative","note","updated_at")}); data["booking"]={"id":item.booking.id,"booking_code":item.booking.booking_code,"status":item.booking.status} if item.booking else None; data["payments"]=[serialize_payment(p) for p in item.payments if p.deleted_at is None]; data["activities"]=[{"id":a.id,"activity_type":a.activity_type,"activity_label":CONTRACT_ACTIVITY_LABELS.get(a.activity_type,a.activity_type),"title":a.title,"content":a.content,"old_value":a.old_value,"new_value":a.new_value,"metadata":a.metadata_json,"actor":{"id":a.actor.id,"full_name":a.actor.full_name},"created_at":a.created_at} for a in item.activities]
    return data
def serialize_payment(p):return {"id":p.id,"payment_code":p.payment_code,"contract_id":p.contract_id,"payment_type":p.payment_type,"payment_type_label":PAYMENT_TYPE_LABELS[p.payment_type],"status":p.status,"status_label":PAYMENT_STATUS_LABELS[p.status],"amount":p.amount,"due_date":p.due_date,"paid_date":p.paid_date,"payment_method":p.payment_method,"payment_method_label":PAYMENT_METHOD_LABELS.get(p.payment_method) if p.payment_method else None,"reference_number":p.reference_number,"note":p.note,"created_at":p.created_at}
def list_contracts(db,actor,page=1,page_size=20,q=None,status=None,contract_type=None,customer_id=None,property_unit_id=None,project_id=None):
    scope=_scope(actor,"contracts.view");
    if not scope:raise HTTPException(403,"Bạn không có quyền xem hợp đồng")
    conditions=[Contract.deleted_at.is_(None)]
    if scope!="all":
        ids=get_accessible_user_ids_for_lead_scope(db,actor,scope); conditions.append(or_(Contract.created_by_id.in_(ids),Contract.deal.has(or_(Deal.owner_id.in_(ids),Deal.created_by_id.in_(ids)))))
    if q: conditions.append(or_(Contract.contract_code.ilike(f"%{q}%"),Contract.contract_number.ilike(f"%{q}%")))
    for col,val in ((Contract.status,status),(Contract.contract_type,contract_type),(Contract.customer_id,customer_id),(Contract.property_unit_id,property_unit_id),(Contract.project_id,project_id)):
        if val is not None:conditions.append(col==val)
    total=db.scalar(select(func.count(Contract.id)).where(*conditions)) or 0; items=list(db.scalars(select(Contract).where(*conditions).order_by(Contract.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique()); return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_contract_detail(db,id,actor):
    item=_get(db,id); _require(db,actor,item,"contracts.view","Bạn không có quyền xem hợp đồng này"); return item
def create_contract(db,payload:ContractCreate,actor):
    deal=db.scalar(select(Deal).where(Deal.id==payload.deal_id,Deal.deleted_at.is_(None)))
    if not deal:raise HTTPException(404,"Giao dịch không tồn tại")
    if deal.status in {"cancelled","lost"}:raise HTTPException(400,"Không thể tạo hợp đồng cho giao dịch đã hủy")
    if not deal.property_unit_id:raise HTTPException(400,"Bất động sản không tồn tại")
    if db.scalar(select(Contract.id).where(Contract.deal_id==deal.id,Contract.deleted_at.is_(None),Contract.status.in_(ACTIVE_CONTRACT_STATUSES))):raise HTTPException(409,"Giao dịch này đã có hợp đồng đang hoạt động")
    inherited_deposit = (deal.booking.deposit_amount or Decimal("0")) if deal.booking else (payload.deposit_value or Decimal("0"))
    data=payload.model_dump(); data.update(contract_code=_next(db,Contract,Contract.contract_code,"HD"),booking_id=deal.booking_id,customer_id=deal.customer_id,property_unit_id=deal.property_unit_id,project_id=deal.project_id,created_by_id=actor.id,deposit_value=inherited_deposit,remaining_value=max(payload.contract_value-inherited_deposit,Decimal("0")))
    item=Contract(**data); db.add(item); db.flush()
    content=f"Hợp đồng {item.contract_code} được tạo từ giao dịch {deal.deal_code}"
    metadata = None
    if inherited_deposit > 0:
        content += f"\nTiền cọc kế thừa từ booking {deal.booking.booking_code}: {inherited_deposit}"
        metadata = {"booking_code": deal.booking.booking_code, "inherited_deposit_amount": str(inherited_deposit)}
    add_contract_activity(db,item,actor,"created",content=content,metadata=metadata); _apply_status(db,item,actor,item.status); auto_task_for_contract_payment(db,item,actor); write_audit_log(db,action="contracts.create",user_id=actor.id,entity_type="contracts",entity_id=str(item.id)); db.commit(); db.refresh(item); return item
def update_contract(db,id,payload,actor):
    item=_get(db,id); _require(db,actor,item,"contracts.update"); data=payload.model_dump(exclude_unset=True); old={k:str(getattr(item,k)) for k in data}; [setattr(item,k,v) for k,v in data.items()]; item.updated_by_id=actor.id; add_contract_activity(db,item,actor,"updated",content=", ".join(data)); write_audit_log(db,action="contracts.update",user_id=actor.id,entity_type="contracts",entity_id=str(item.id),before_data=old,after_data={k:str(v) for k,v in data.items()}); db.commit(); db.refresh(item); return item
def change_contract_status(db, id, payload: ContractStatusChange, actor):
    item = _get(db, id)
    _require(db, actor, item, "contracts.status")
    if payload.status not in CONTRACT_STATUS_LABELS:
        raise HTTPException(400, "Trạng thái hợp đồng không hợp lệ")
    old = item.status
    if old == "cancelled" and payload.status != "cancelled":
        raise HTTPException(409, "Hợp đồng đã hủy không thể kích hoạt hoặc ký lại. Vui lòng tạo hợp đồng mới.")
    item.status = payload.status
    item.updated_by_id = actor.id
    _apply_status(db, item, actor, payload.status)
    rollback_activity = None
    if payload.status == "cancelled":
        rollback_activity = _rollback_cancelled_contract(db, item, actor, old, payload.note)
    status_content = payload.note.strip() if payload.note else None
    if rollback_activity:
        status_content = (
            f"{status_content + chr(10) if status_content else ''}"
            f"Đã khôi phục giao dịch về Chờ hợp đồng và bất động sản về "
            f"{'Đã cọc' if rollback_activity.metadata_json['booking_deposit_active'] else 'Còn hàng'}."
        )
    add_contract_activity(
        db,
        item,
        actor,
        "status_change",
        content=status_content,
        old_value=CONTRACT_STATUS_LABELS[old],
        new_value=CONTRACT_STATUS_LABELS[payload.status],
        metadata={
            "old_status_label": CONTRACT_STATUS_LABELS[old],
            "new_status_label": CONTRACT_STATUS_LABELS[payload.status],
            "note": payload.note.strip() if payload.note else None,
            "rollback_property_status": rollback_activity.metadata_json["property_new_status"] if rollback_activity else None,
        },
    )
    _deal_contract_activity(db, item, actor, old, payload.status, payload.note)
    if payload.status in {"signed", "active"}:
        auto_task_for_contract_payment(db, item, actor)
    elif payload.status == "completed":
        auto_complete_contract_payment_tasks(db, item, actor)
    write_audit_log(db, action="contracts.status_change", user_id=actor.id, entity_type="contracts", entity_id=str(item.id))
    db.commit()
    db.refresh(item)
    return item
def soft_delete_contract(db,id,actor):
    item=_get(db,id); _require(db,actor,item,"contracts.delete")
    if item.status not in {"draft","cancelled"}:raise HTTPException(409,"Không thể xóa hợp đồng đã ký hoặc hoàn tất.")
    item.deleted_at=datetime.now(timezone.utc); item.deleted_by_id=actor.id; add_contract_activity(db,item,actor,"deleted"); write_audit_log(db,action="contracts.delete",user_id=actor.id,entity_type="contracts",entity_id=str(item.id)); db.commit()
def list_contract_payments(db,contract_id,actor):return [p for p in get_contract_detail(db,contract_id,actor).payments if p.deleted_at is None]
def create_contract_payment(db,contract_id,payload:ContractPaymentCreate,actor):
    c=_get(db,contract_id); _require(db,actor,c,"contracts.payment.update" if False else "contracts.payment.view");
    if not (actor.is_superuser or "contracts.payment.create" in set(get_user_permissions(actor))):raise HTTPException(403,"Bạn không có quyền tạo thanh toán")
    if payload.status in {"planned", "overdue", "paid"}:
        _validate_payment_capacity(db, c, payload.amount)
    d=payload.model_dump(exclude={"contract_id"}); p=ContractPayment(**d,payment_code=_next(db,ContractPayment,ContractPayment.payment_code,"PAY"),contract_id=c.id,deal_id=c.deal_id,customer_id=c.customer_id,property_unit_id=c.property_unit_id,created_by_id=actor.id); db.add(p); db.flush(); add_contract_activity(db,c,actor,"payment_created",metadata={"payment_code":p.payment_code,"amount":str(p.amount),"payment_type_label":PAYMENT_TYPE_LABELS[p.payment_type],"payment_status_label":PAYMENT_STATUS_LABELS[p.status]}); write_audit_log(db,action="contracts.payment.create",user_id=actor.id,entity_type="contract_payments",entity_id=str(p.id)); db.commit(); db.refresh(p); return p
def update_contract_payment(db,contract_id,id,payload:ContractPaymentUpdate,actor):
    c=_get(db,contract_id); _require(db,actor,c,"contracts.payment.update"); p=_payment(db,contract_id,id); data=payload.model_dump(exclude_unset=True)
    next_status=data.get("status",p.status); next_amount=data.get("amount",p.amount)
    if next_status in {"planned","overdue","paid"}:_validate_payment_capacity(db,c,next_amount,exclude_payment_id=p.id)
    [setattr(p,k,v) for k,v in data.items()]; p.updated_by_id=actor.id; db.commit(); db.refresh(p); return p
def confirm_contract_payment(db,contract_id,id,payload:ContractPaymentConfirm,actor):
    c=_get(db,contract_id); _require(db,actor,c,"contracts.payment.confirm"); p=_payment(db,contract_id,id)
    _validate_payment_capacity(db, c, p.amount, exclude_payment_id=p.id, paid_only=True)
    p.status="paid"; p.paid_date=payload.paid_date or datetime.now(timezone.utc); p.payment_method=payload.payment_method or p.payment_method; p.reference_number=payload.reference_number or p.reference_number; p.note=payload.note or p.note; p.updated_by_id=actor.id
    add_contract_activity(db,c,actor,"payment_paid",content=p.note,metadata={"payment_code":p.payment_code,"amount":str(p.amount),"payment_method":p.payment_method,"payment_method_label":PAYMENT_METHOD_LABELS.get(p.payment_method) if p.payment_method else None,"reference_number":p.reference_number,"paid_date":p.paid_date.isoformat(),"payment_status_label":PAYMENT_STATUS_LABELS[p.status]}); write_audit_log(db,action="contracts.payment.confirm",user_id=actor.id,entity_type="contract_payments",entity_id=str(p.id)); db.commit(); db.refresh(p); return p
def soft_delete_contract_payment(db,contract_id,id,actor):
    c=_get(db,contract_id); _require(db,actor,c,"contracts.payment.update"); p=_payment(db,contract_id,id); p.deleted_at=datetime.now(timezone.utc); p.deleted_by_id=actor.id; add_contract_activity(db,c,actor,"payment_cancelled",content=p.payment_code); db.commit()
