from datetime import date, datetime, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, lazyload, load_only, selectinload
from app.contracts.constants import CONTRACT_STATUS_LABELS
from app.models.contract import Contract
from app.models.contract_activity import ContractActivity
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.notification import Notification
from app.models.payment_invoice import PaymentInvoice
from app.models.payment_receipt import PaymentReceipt
from app.models.payment_schedule import PaymentSchedule
from app.models.property_unit import PropertyUnit
from app.models.task import Task
from app.models.user import User
from app.payments_constants import INVOICE_STATUS_LABELS, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, RECEIPT_STATUS_LABELS
from app.permissions.dependencies import get_user_permissions
from app.schemas.payment import InvoiceCreate, PaymentScheduleCreate, PaymentScheduleUpdate, PenaltyApply, ReceiptCancel, ReceiptConfirm, ReceiptCreate
from app.services.contract_service import add_contract_activity
from app.services.notification_service import create_notification
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.task_service import create_auto_task_if_not_exists

def _next(db, column, prefix):
    codes=db.scalars(select(column).where(column.like(f"{prefix}-%")))
    nums=[int(c.split('-')[-1]) for c in codes if c and c.split('-')[-1].isdigit()]
    return f"{prefix}-{max(nums,default=0)+1:06d}"
def _scope(user):
    if user.is_superuser: return 'all'
    perms=set(get_user_permissions(user))
    for s in ('all','department','team','own'):
        if f'payments.view.{s}' in perms or (s=='all' and ('payments.view_all' in perms or 'payments.view' in perms)): return s
    return None
def _can_write(user, code): return user.is_superuser or code in set(get_user_permissions(user)) or 'payments.update' in set(get_user_permissions(user))
def _contract(db,id):
    c=db.scalar(select(Contract).where(Contract.id==id,Contract.deleted_at.is_(None)))
    if not c: raise HTTPException(404,'Hợp đồng không tồn tại')
    return c
def _schedule(db,id):
    p=db.scalar(select(PaymentSchedule).where(PaymentSchedule.id==id,PaymentSchedule.deleted_at.is_(None)))
    if not p: raise HTTPException(404,'Lịch thanh toán không tồn tại')
    return p
def _receipt(db,id):
    r=db.scalar(select(PaymentReceipt).where(PaymentReceipt.id==id,PaymentReceipt.deleted_at.is_(None)))
    if not r: raise HTTPException(404,'Phiếu thu không tồn tại')
    return r
def _total_due(p): return (p.expected_amount or Decimal('0')) + (p.penalty_amount or Decimal('0'))
def _recalc(p):
    p.remaining_amount=max(_total_due(p) - (p.paid_amount or Decimal('0')), Decimal('0'))
    if p.status == 'cancelled': return
    if p.paid_amount <= 0: p.status='pending'
    elif p.paid_amount < _total_due(p): p.status='partial'
    else: p.status='paid'
def _format_money(v): return f"{Decimal(v):,.0f}đ".replace(',', '.')
def _refresh_overdue(db,p,actor=None):
    if p.status not in {'paid','cancelled'} and p.due_date < date.today():
        if p.status != 'overdue':
            p.status='overdue'; p.updated_by_id=getattr(actor,'id',None)
            add_contract_activity(db,p.contract,actor or p.contract.creator,'payment_overdue',content=f"Đợt thanh toán {p.title} đã quá hạn.",metadata={'payment_schedule_id':str(p.id),'payment_code':p.payment_code})
            _create_overdue_task_notification(db,p,actor or p.contract.creator)
    return p
def _create_due_task(db,p,actor):
    assignee=getattr(p.contract.deal,'owner_id',None) or actor.id
    return create_auto_task_if_not_exists(db,actor,title=f"Theo dõi thanh toán {p.title} - {p.contract.contract_code}",task_type='payment_due',priority='high',assigned_user_id=assignee,related_contract_id=p.contract_id,related_deal_id=p.deal_id,related_customer_id=p.customer_id,related_property_unit_id=p.property_unit_id,due_at=datetime.combine(p.due_date, datetime.min.time(), tzinfo=timezone.utc),source_event=f"payment_schedule_due:{p.id}")
def _create_overdue_task_notification(db,p,actor):
    assignee=getattr(p.contract.deal,'owner_id',None) or getattr(actor,'id',None)
    task=create_auto_task_if_not_exists(db,actor,title=f"Đợt thanh toán đã quá hạn: {p.title}",task_type='payment_due',priority='urgent',assigned_user_id=assignee,related_contract_id=p.contract_id,related_deal_id=p.deal_id,related_customer_id=p.customer_id,related_property_unit_id=p.property_unit_id,due_at=datetime.combine(p.due_date, datetime.min.time(), tzinfo=timezone.utc),source_event=f"payment_schedule_overdue:{p.id}")
    existing=db.scalar(select(Notification.id).where(Notification.recipient_user_id==assignee,Notification.notification_type=='payment_overdue',Notification.related_task_id==task.id,Notification.deleted_at.is_(None)).limit(1)) if assignee and task else None
    if assignee and not existing: create_notification(db,recipient_user_id=assignee,title='Đợt thanh toán đã quá hạn',content=f"{p.title} của hợp đồng {p.contract.contract_code} đã quá hạn.",notification_type='payment_overdue',related_task_id=task.id if task else None,related_contract_id=p.contract_id,related_deal_id=p.deal_id,related_customer_id=p.customer_id,related_property_unit_id=p.property_unit_id)
    return task


def _validate_contract_schedule_capacity(db, contract, amount, *, exclude_schedule_id=None):
    if not contract.contract_value or contract.contract_value <= 0:
        raise HTTPException(400, 'Hợp đồng chưa có giá trị hợp đồng hợp lệ.')
    conditions = [
        PaymentSchedule.contract_id == contract.id,
        PaymentSchedule.deleted_at.is_(None),
        PaymentSchedule.status != 'cancelled',
    ]
    if exclude_schedule_id is not None:
        conditions.append(PaymentSchedule.id != exclude_schedule_id)
    current_total = db.scalar(select(func.coalesce(func.sum(PaymentSchedule.expected_amount), 0)).where(*conditions)) or Decimal('0')
    if Decimal(current_total) + amount > contract.contract_value:
        raise HTTPException(400, 'Tổng lịch thanh toán không được vượt quá giá trị hợp đồng.')

def serialize_schedule(p,detail=False):
    _recalc(p)
    d={'id':p.id,'payment_code':p.payment_code,'contract_id':p.contract_id,'deal_id':p.deal_id,'customer_id':p.customer_id,'property_unit_id':p.property_unit_id,'sequence_no':p.sequence_no,'title':p.title,'due_date':p.due_date,'expected_amount':p.expected_amount,'paid_amount':p.paid_amount,'remaining_amount':p.remaining_amount,'penalty_amount':p.penalty_amount,'penalty_reason':p.penalty_reason,'penalty_applied_at':p.penalty_applied_at,'status':p.status,'status_label':PAYMENT_STATUS_LABELS[p.status],'payment_method':p.payment_method,'payment_method_label':PAYMENT_METHOD_LABELS.get(p.payment_method) if p.payment_method else None,'note':p.note,'contract':{'id':p.contract.id,'contract_code':p.contract.contract_code,'status':p.contract.status,'status_label':CONTRACT_STATUS_LABELS[p.contract.status]},'deal':{'id':p.deal.id,'deal_code':p.deal.deal_code,'title':p.deal.title} if p.deal else None,'customer':{'id':p.customer.id,'customer_code':p.customer.customer_code,'full_name':p.customer.full_name,'primary_phone':p.customer.primary_phone} if p.customer else None,'property':{'id':p.property_unit.id,'property_code':p.property_unit.property_code,'title':p.property_unit.title} if p.property_unit else None,'created_at':p.created_at,'updated_at':p.updated_at}
    if detail:
        d['receipts']=[serialize_receipt(r) for r in p.receipts if r.deleted_at is None]
        d['invoices']=[serialize_invoice(i) for i in p.invoices if i.deleted_at is None]
    return d
def serialize_receipt(r): return {'id':r.id,'receipt_code':r.receipt_code,'payment_schedule_id':r.payment_schedule_id,'contract_id':r.contract_id,'deal_id':r.deal_id,'customer_id':r.customer_id,'amount':r.amount,'payment_date':r.payment_date,'payment_method':r.payment_method,'payment_method_label':PAYMENT_METHOD_LABELS.get(r.payment_method) if r.payment_method else None,'reference_no':r.reference_no,'received_by_id':r.received_by_id,'note':r.note,'status':r.status,'status_label':RECEIPT_STATUS_LABELS[r.status],'created_at':r.created_at}
def serialize_invoice(i): return {'id':i.id,'invoice_code':i.invoice_code,'contract_id':i.contract_id,'payment_schedule_id':i.payment_schedule_id,'customer_id':i.customer_id,'amount':i.amount,'issued_date':i.issued_date,'status':i.status,'status_label':INVOICE_STATUS_LABELS[i.status],'note':i.note,'created_at':i.created_at}
def payment_summary(db,contract_id):
    rows=list(db.scalars(select(PaymentSchedule).where(PaymentSchedule.contract_id==contract_id,PaymentSchedule.deleted_at.is_(None))))
    for p in rows: _recalc(p)
    return {'total_expected':sum((_total_due(p) for p in rows),Decimal('0')),'total_paid':sum((p.paid_amount for p in rows),Decimal('0')),'total_remaining':sum((p.remaining_amount for p in rows),Decimal('0')),'overdue_count':sum(1 for p in rows if p.status=='overdue')}
def list_schedules(db,actor,page=1,page_size=20,q=None,status=None,contract_id=None,deal_id=None,customer_id=None,overdue=None):
    scope=_scope(actor)
    if not scope: raise HTTPException(403,'Bạn không có quyền xem thanh toán')
    cond=[PaymentSchedule.deleted_at.is_(None)]
    if scope!='all':
        ids=get_accessible_user_ids_for_lead_scope(db,actor,scope); cond.append(PaymentSchedule.contract.has(or_(Contract.created_by_id.in_(ids),Contract.deal.has(or_(Deal.owner_id.in_(ids),Deal.created_by_id.in_(ids))))))
    if status: cond.append(PaymentSchedule.status==status)
    if overdue is True: cond.append(PaymentSchedule.due_date < date.today()); cond.append(PaymentSchedule.status.notin_(['paid','cancelled']))
    for col,val in ((PaymentSchedule.contract_id,contract_id),(PaymentSchedule.deal_id,deal_id),(PaymentSchedule.customer_id,customer_id)):
        if val is not None: cond.append(col==val)
    if q:
        term=f"%{q.strip()}%"; cond.append(or_(PaymentSchedule.payment_code.ilike(term),PaymentSchedule.title.ilike(term),PaymentSchedule.contract.has(Contract.contract_code.ilike(term)),PaymentSchedule.deal.has(Deal.deal_code.ilike(term)),PaymentSchedule.customer.has(or_(Customer.full_name.ilike(term),Customer.primary_phone.ilike(term)))))
    query=select(PaymentSchedule).options(selectinload(PaymentSchedule.contract).load_only(Contract.id,Contract.contract_code,Contract.status),selectinload(PaymentSchedule.deal).load_only(Deal.id,Deal.deal_code,Deal.title),selectinload(PaymentSchedule.customer).load_only(Customer.id,Customer.customer_code,Customer.full_name,Customer.primary_phone),selectinload(PaymentSchedule.property_unit).load_only(PropertyUnit.id,PropertyUnit.property_code,PropertyUnit.title),lazyload('*')).where(*cond)
    total=db.scalar(select(func.count(PaymentSchedule.id)).where(*cond)) or 0
    items=list(db.scalars(query.order_by(PaymentSchedule.due_date.asc(),PaymentSchedule.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique())
    changed=False
    for p in items:
        old=p.status; _refresh_overdue(db,p,actor); changed=changed or old!=p.status
    if changed: db.commit()
    return items,{'page':page,'page_size':page_size,'total':total,'total_pages':ceil(total/page_size) if total else 0}
def get_schedule(db,id,actor): p=_schedule(db,id); _refresh_overdue(db,p,actor); db.commit(); db.refresh(p); return p
def create_schedule(db,payload:PaymentScheduleCreate,actor):
    if not _can_write(actor,'payments.create'): raise HTTPException(403,'Bạn không có quyền tạo lịch thanh toán')
    c=_contract(db,payload.contract_id)
    if c.status=='cancelled': raise HTTPException(400,'Không thể tạo lịch thanh toán cho hợp đồng đã hủy.')
    _validate_contract_schedule_capacity(db, c, payload.expected_amount)
    if db.scalar(select(PaymentSchedule.id).where(PaymentSchedule.contract_id==c.id,PaymentSchedule.sequence_no==payload.sequence_no,PaymentSchedule.deleted_at.is_(None))): raise HTTPException(409,'Số thứ tự đợt thanh toán đã tồn tại trong hợp đồng này.')
    p=PaymentSchedule(payment_code=_next(db,PaymentSchedule.payment_code,'PMT'),contract_id=c.id,deal_id=c.deal_id,customer_id=c.customer_id,property_unit_id=c.property_unit_id,sequence_no=payload.sequence_no,title=payload.title,due_date=payload.due_date,expected_amount=payload.expected_amount,paid_amount=Decimal('0'),remaining_amount=payload.expected_amount,created_by_id=actor.id,note=payload.note)
    db.add(p); db.flush(); add_contract_activity(db,c,actor,'payment_schedule_created',content=f"Tạo lịch thanh toán {p.title}, số tiền {_format_money(p.expected_amount)}, hạn {p.due_date.strftime('%d/%m/%Y')}.",metadata={'payment_schedule_id':str(p.id),'payment_code':p.payment_code}); _create_due_task(db,p,actor); _refresh_overdue(db,p,actor); db.commit(); db.refresh(p); return p
def update_schedule(db,id,payload:PaymentScheduleUpdate,actor):
    p=_schedule(db,id)
    if not _can_write(actor,'payments.update'): raise HTTPException(403,'Bạn không có quyền cập nhật thanh toán')
    if p.status in {'paid','cancelled'}: raise HTTPException(409,'Không thể sửa đợt thanh toán đã thanh toán đủ hoặc đã hủy.')
    data=payload.model_dump(exclude_unset=True)
    if 'sequence_no' in data and data['sequence_no']!=p.sequence_no and db.scalar(select(PaymentSchedule.id).where(PaymentSchedule.contract_id==p.contract_id,PaymentSchedule.sequence_no==data['sequence_no'],PaymentSchedule.id!=p.id,PaymentSchedule.deleted_at.is_(None))): raise HTTPException(409,'Số thứ tự đợt thanh toán đã tồn tại trong hợp đồng này.')
    _validate_contract_schedule_capacity(db, p.contract, data.get('expected_amount', p.expected_amount), exclude_schedule_id=p.id)
    for k,v in data.items(): setattr(p,k,v)
    _recalc(p); p.updated_by_id=actor.id; add_contract_activity(db,p.contract,actor,'payment_schedule_updated',content=f"Cập nhật lịch thanh toán {p.title}.",metadata={'payment_schedule_id':str(p.id),'payment_code':p.payment_code}); _refresh_overdue(db,p,actor); db.commit(); db.refresh(p); return p
def apply_penalty(db,id,payload:PenaltyApply,actor):
    p=_schedule(db,id)
    if p.status=='cancelled': raise HTTPException(409,'Đợt thanh toán đã hủy không thể áp dụng phí phạt.')
    p.penalty_amount=payload.penalty_amount; p.penalty_reason=payload.penalty_reason; p.penalty_applied_at=datetime.now(timezone.utc) if payload.penalty_amount>0 else None; p.updated_by_id=actor.id; _recalc(p)
    add_contract_activity(db,p.contract,actor,'payment_penalty',content=f"Áp dụng phí phạt {_format_money(p.penalty_amount)} do {p.penalty_reason}.",metadata={'payment_schedule_id':str(p.id),'payment_code':p.payment_code}); db.commit(); db.refresh(p); return p
def cancel_schedule(db,id,actor):
    p=_schedule(db,id)
    if p.status=='paid': raise HTTPException(409,'Không thể hủy đợt thanh toán đã thanh toán đủ.')
    p.status='cancelled'; p.updated_by_id=actor.id; add_contract_activity(db,p.contract,actor,'payment_schedule_cancelled',content=f"Hủy lịch thanh toán {p.title}."); db.commit(); db.refresh(p); return p
def create_receipt(db,schedule_id,payload:ReceiptCreate,actor):
    p=_schedule(db,schedule_id)
    if p.status=='cancelled': raise HTTPException(409,'Đợt thanh toán đã hủy nên không thể ghi nhận thanh toán.')
    r=PaymentReceipt(receipt_code=_next(db,PaymentReceipt.receipt_code,'RCP'),payment_schedule_id=p.id,contract_id=p.contract_id,deal_id=p.deal_id,customer_id=p.customer_id,amount=payload.amount,payment_date=payload.payment_date,payment_method=payload.payment_method,reference_no=payload.reference_no,note=payload.note,status='draft',created_by_id=actor.id,received_by_id=actor.id if payload.status=='confirmed' else None)
    db.add(r); db.flush()
    if payload.status=='confirmed': _confirm_receipt(db,r,actor)
    db.commit(); db.refresh(r); return r
def _confirm_receipt(db,r,actor,payload=None):
    if r.status=='cancelled': raise HTTPException(409,'Không thể xác nhận phiếu thu đã hủy.')
    if r.status=='confirmed': return r
    p=r.payment_schedule
    payment_date=getattr(payload,'payment_date',None) or r.payment_date
    if payment_date is None: raise HTTPException(400,'Ngày thanh toán là bắt buộc khi xác nhận.')
    if (p.paid_amount or Decimal('0')) + r.amount > _total_due(p): raise HTTPException(400,'Không thể thanh toán vượt quá số tiền còn lại.')
    r.payment_date=payment_date; r.payment_method=getattr(payload,'payment_method',None) or r.payment_method; r.reference_no=getattr(payload,'reference_no',None) or r.reference_no; r.note=getattr(payload,'note',None) or r.note; r.received_by_id=actor.id; r.status='confirmed'; r.updated_by_id=actor.id
    p.paid_amount=(p.paid_amount or Decimal('0'))+r.amount; p.payment_method=r.payment_method or p.payment_method; _recalc(p)
    add_contract_activity(db,p.contract,actor,'payment_receipt_confirmed',content=f"Xác nhận thanh toán {r.receipt_code} số tiền {_format_money(r.amount)} cho {p.title}.",metadata={'payment_schedule_id':str(p.id),'receipt_code':r.receipt_code})
    if p.status=='paid': add_contract_activity(db,p.contract,actor,'payment_schedule_paid',content=f"Đợt thanh toán {p.title} đã được thanh toán đủ.")
    title='Khách hàng đã thanh toán đủ' if p.status=='paid' else 'Khách hàng đã thanh toán một phần'; assignee=getattr(p.contract.deal,'owner_id',None)
    if assignee: create_notification(db,recipient_user_id=assignee,title=title,content=f"{p.title} - {p.contract.contract_code}: {_format_money(r.amount)}",notification_type='payment_paid',related_contract_id=p.contract_id,related_deal_id=p.deal_id,related_customer_id=p.customer_id,related_property_unit_id=p.property_unit_id)
    return r
def confirm_receipt(db,id,payload:ReceiptConfirm,actor):
    r=_receipt(db,id); _confirm_receipt(db,r,actor,payload); db.commit(); db.refresh(r); return r
def cancel_receipt(db,id,payload:ReceiptCancel,actor):
    r=_receipt(db,id)
    if r.status=='cancelled': raise HTTPException(409,'Phiếu thu đã hủy.')
    p=r.payment_schedule
    if r.status=='confirmed': p.paid_amount=max((p.paid_amount or Decimal('0'))-r.amount,Decimal('0')); _recalc(p)
    r.status='cancelled'; r.note=payload.note or r.note; r.updated_by_id=actor.id; add_contract_activity(db,p.contract,actor,'payment_receipt_cancelled',content=f"Hủy phiếu thu {r.receipt_code} của {p.title}."); db.commit(); db.refresh(r); return r
def list_receipts(db,schedule_id,actor): return [r for r in _schedule(db,schedule_id).receipts if r.deleted_at is None]
def create_invoice(db,schedule_id,payload:InvoiceCreate,actor):
    p=_schedule(db,schedule_id); amount=payload.amount or _total_due(p)
    inv=PaymentInvoice(invoice_code=_next(db,PaymentInvoice.invoice_code,'INV'),contract_id=p.contract_id,payment_schedule_id=p.id,customer_id=p.customer_id,amount=amount,issued_date=payload.issued_date,status=payload.status,note=payload.note,created_by_id=actor.id)
    db.add(inv); db.flush(); add_contract_activity(db,p.contract,actor,'payment_invoice_created',content=f"Tạo hóa đơn nháp {inv.invoice_code} cho {p.title}, số tiền {_format_money(inv.amount)}."); db.commit(); db.refresh(inv); return inv
