from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID
import csv, io
from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, object_session
from app.models.contract import Contract
from app.models.deal import Deal
from app.models.customer import Customer
from app.models.payment_receipt import PaymentReceipt
from app.models.sales_commission import SalesCommission, SalesCommissionEvent
from app.models.user import User
from app.services.company_commission_service import get_company_commission_for_contract, get_company_commissions_by_contract_ids, STATUS_LABELS as CCR_STATUS_LABELS

STATUSES={"draft":"Tạm tính","eligible":"Đủ điều kiện","approved":"Đã duyệt","paid":"Đã chi trả","on_hold":"Tạm giữ","cancelled":"Đã hủy"}
COMMISSION_LEGAL_CONTRACT_STATUSES = {'signed', 'active', 'completed'}
LEGAL_STATUS_ERROR = 'Hợp đồng chưa đủ trạng thái pháp lý để tạo hoa hồng.'
D=Decimal

def now(): return datetime.now(timezone.utc)
def dec(v): return D(str(v or 0))

def _event(db,c,t,title,desc,actor):
    db.add(SalesCommissionEvent(commission_id=c.id,event_type=t,title=title,description=desc,actor_id=getattr(actor,'id',None),created_at=now()))

def _code(db):
    n=db.query(func.count(SalesCommission.id)).scalar() or 0
    return f"COM-{n+1:06d}"

def _snapshot(db, contract, rate_percent):
    receipts=dec(db.query(func.coalesce(func.sum(PaymentReceipt.amount),0)).filter(PaymentReceipt.contract_id==contract.id, PaymentReceipt.status=='confirmed', PaymentReceipt.deleted_at.is_(None)).scalar())
    cv=dec(contract.contract_value); dep=dec(contract.deposit_value); total=dep+receipts; remaining=max(cv-total,D('0'))
    ratio=dec(rate_percent)/D('100')
    eligible = contract.status in COMMISSION_LEGAL_CONTRACT_STATUSES and (contract.status == 'completed' or total >= cv)
    return dict(contract_value=cv,deposit_value=dep,confirmed_receipts_amount=receipts,total_collected_with_deposit=total,remaining_amount=remaining,estimated_commission=(cv*ratio).quantize(D('0.01')),collected_commission=(total*ratio).quantize(D('0.01')),eligible_commission=((cv*ratio).quantize(D('0.01')) if eligible else D('0')), eligible=eligible)

def _sale_id(contract): return getattr(getattr(contract,'deal',None),'owner_id',None)


def _company_commission_summary(ccr):
    if not ccr:
        return None
    return {
        "id": str(ccr.id),
        "receivable_code": ccr.receivable_code,
        "status": ccr.status,
        "status_label": CCR_STATUS_LABELS.get(ccr.status, ccr.status),
        "expected_commission_amount": float(ccr.expected_commission_amount or 0),
        "confirmed_receivable_amount": float(ccr.confirmed_receivable_amount or 0),
        "received_amount": float(ccr.received_amount or 0),
        "remaining_amount": float(ccr.remaining_amount or 0),
    }

def _paid_for_contract(db, contract_id, exclude_id=None):
    q=db.query(func.coalesce(func.sum(SalesCommission.paid_amount),0)).filter(SalesCommission.contract_id==contract_id, SalesCommission.paid_amount>0)
    if exclude_id is not None:
        q=q.filter(SalesCommission.id!=exclude_id)
    return dec(q.scalar())

def get_sales_commission_payout_policy_context(db, c, ccr=None, paid_for_contract_total=None):
    if ccr is None:
        ccr=get_company_commission_for_contract(db, c.contract_id)
    paid_other=(dec(paid_for_contract_total)-dec(c.paid_amount)) if paid_for_contract_total is not None else _paid_for_contract(db, c.contract_id, c.id)
    current_paid=dec(c.paid_amount)
    received=dec(getattr(ccr,'received_amount',0) if ccr else 0)
    approved=dec(c.approved_commission)
    capacity=max(received-paid_other-current_paid, D('0')) if ccr else D('0')
    max_payable=min(approved, capacity) if approved > 0 else D('0')
    approve_reason=None; mark_reason=None; warning=None
    if not ccr:
        approve_reason='Hợp đồng chưa có khoản hoa hồng công ty, chưa thể duyệt hoa hồng sale.'
        mark_reason='Hợp đồng chưa có khoản hoa hồng công ty, chưa thể chi hoa hồng sale.'
    elif ccr.status=='cancelled':
        approve_reason='Khoản hoa hồng công ty đã hủy, không thể duyệt hoa hồng sale.'
        mark_reason='Khoản hoa hồng công ty đã hủy, không thể chi hoa hồng sale.'
    elif ccr.status=='on_hold':
        approve_reason='Khoản hoa hồng công ty đang tạm giữ, chưa thể duyệt hoa hồng sale.'
        mark_reason='Khoản hoa hồng công ty đang tạm giữ, chưa thể chi hoa hồng sale.'
    elif ccr.status not in ('pending','approved','partially_received','received'):
        approve_reason='Trạng thái hoa hồng công ty chưa cho phép duyệt hoa hồng sale.'
        mark_reason='Trạng thái hoa hồng công ty chưa cho phép chi hoa hồng sale.'
    elif ccr.status not in ('partially_received','received') or received<=0:
        mark_reason='Công ty chưa nhận hoa hồng công ty, chưa thể chi hoa hồng sale.'
        warning='Công ty chưa nhận hoa hồng công ty. Bạn có thể duyệt, nhưng chưa thể chi trả cho sale.'
    elif ccr.status=='partially_received':
        warning='Công ty mới nhận một phần hoa hồng công ty.'
    if ccr and mark_reason is None and max_payable <= 0:
        mark_reason='Số tiền chi hoa hồng sale không được vượt số hoa hồng công ty đã nhận.'
    return {
        'has_company_commission': ccr is not None,
        'company_commission_id': str(ccr.id) if ccr else None,
        'company_commission_code': ccr.receivable_code if ccr else None,
        'company_commission_status': ccr.status if ccr else None,
        'company_commission_status_label': CCR_STATUS_LABELS.get(ccr.status, ccr.status) if ccr else None,
        'company_commission_expected_amount': float(ccr.expected_commission_amount or 0) if ccr else 0,
        'company_commission_confirmed_amount': float(ccr.confirmed_receivable_amount or 0) if ccr else 0,
        'company_commission_received_amount': float(received),
        'company_commission_remaining_amount': float(ccr.remaining_amount or 0) if ccr else 0,
        'sales_commission_approved_amount': float(approved),
        'sales_commission_paid_amount': float(current_paid),
        'max_payable_amount': float(max_payable),
        'remaining_payable_capacity': float(max_payable),
        'can_approve_sales_commission': approve_reason is None,
        'approve_block_reason': approve_reason,
        'can_mark_paid_sales_commission': mark_reason is None and max_payable > 0,
        'mark_paid_block_reason': mark_reason,
        'warning_message': warning,
    }

def row(c, policy=None, company_commission=None):
    contract=c.contract; customer=getattr(contract,'customer',None); sale=c.sale
    db=object_session(c)
    if policy is None:
        policy=get_sales_commission_payout_policy_context(db, c, company_commission) if db else {}
    if company_commission is None and db:
        company_commission=get_company_commission_for_contract(db, c.contract_id)
    data={"id":str(c.id),"commission_code":c.commission_code,"contract_id":str(c.contract_id),"contract_code":getattr(contract,'contract_code',None),"sale_id":str(c.sale_id) if c.sale_id else None,"sale_name":getattr(sale,'full_name',None) or getattr(sale,'email',None) or 'Chưa gán sale',"customer_name":getattr(customer,'full_name',None) or getattr(contract,'buyer_name',None),"customer_phone":getattr(customer,'primary_phone',None) or getattr(contract,'buyer_phone',None),"contract_value":float(c.contract_value),"total_collected_with_deposit":float(c.total_collected_with_deposit),"remaining_amount":float(c.remaining_amount),"commission_rate_percent":float(c.commission_rate_percent),"eligible_commission":float(c.eligible_commission),"approved_commission":float(c.approved_commission or 0),"paid_amount":float(c.paid_amount or 0),"status":c.status,"status_label":STATUSES.get(c.status,c.status),"approved_at":c.approved_at.isoformat() if c.approved_at else None,"paid_at":c.paid_at.isoformat() if c.paid_at else None,"created_at":c.created_at.isoformat() if c.created_at else None,"hold_reason":c.hold_reason,"cancel_reason":c.cancel_reason,"note":c.note}
    data.update({"company_commission_code":policy.get("company_commission_code"),"company_commission_status":policy.get("company_commission_status"),"company_commission_status_label":policy.get("company_commission_status_label"),"company_commission_received_amount":policy.get("company_commission_received_amount",0),"company_commission_remaining_amount":policy.get("company_commission_remaining_amount",0),"can_approve_by_company_commission_policy":policy.get("can_approve_sales_commission",False),"approve_block_reason":policy.get("approve_block_reason"),"can_mark_paid_by_company_commission_policy":policy.get("can_mark_paid_sales_commission",False),"mark_paid_block_reason":policy.get("mark_paid_block_reason"),"remaining_payable_capacity":policy.get("remaining_payable_capacity",0),"payout_policy":policy,"company_commission":_company_commission_summary(company_commission)})
    return data

def detail(c):
    r=row(c); contract=c.contract; customer=getattr(contract,'customer',None)
    r.update({"deposit_value":float(c.deposit_value),"confirmed_receipts_amount":float(c.confirmed_receipts_amount),"estimated_commission":float(c.estimated_commission),"collected_commission":float(c.collected_commission),"contract_status":getattr(contract,'status',None),"payment_status":getattr(contract,'payment_status',None),"approved_by_name":getattr(c.approved_by,'full_name',None) or getattr(c.approved_by,'email',None) if c.approved_by else None,"paid_by_name":getattr(c.paid_by,'full_name',None) or getattr(c.paid_by,'email',None) if c.paid_by else None,"events":[{"id":str(e.id),"event_type":e.event_type,"title":e.title,"description":e.description,"actor_name":getattr(e.actor,'full_name',None) or getattr(e.actor,'email',None) if e.actor else None,"created_at":e.created_at.isoformat()} for e in c.events]})
    return r

def base_query(db): return db.query(SalesCommission).options(joinedload(SalesCommission.contract).joinedload(Contract.customer),joinedload(SalesCommission.contract).joinedload(Contract.deal),joinedload(SalesCommission.sale),joinedload(SalesCommission.events).joinedload(SalesCommissionEvent.actor),joinedload(SalesCommission.approved_by),joinedload(SalesCommission.paid_by))

def list_commissions(db, page=1, page_size=20, **f):
    q=base_query(db).join(Contract, SalesCommission.contract_id==Contract.id).outerjoin(Customer, Contract.customer_id==Customer.id).outerjoin(User, SalesCommission.sale_id==User.id)
    if f.get('status'): q=q.filter(SalesCommission.status==f['status'])
    if f.get('sale_id'): q=q.filter(SalesCommission.sale_id==f['sale_id'])
    if f.get('contract_id'): q=q.filter(SalesCommission.contract_id==f['contract_id'])
    kw=f.get('keyword') or f.get('contract_code')
    if kw: q=q.filter(or_(SalesCommission.commission_code.ilike(f'%{kw}%'), Contract.contract_code.ilike(f'%{kw}%'), Customer.full_name.ilike(f'%{kw}%')))
    for key,col,op in [('date_from',SalesCommission.created_at,lambda c,v:c>=v),('date_to',SalesCommission.created_at,lambda c,v:c<=v),('approved_from',SalesCommission.approved_at,lambda c,v:c>=v),('approved_to',SalesCommission.approved_at,lambda c,v:c<=v),('paid_from',SalesCommission.paid_at,lambda c,v:c>=v),('paid_to',SalesCommission.paid_at,lambda c,v:c<=v)]:
        if f.get(key): q=q.filter(op(col, f[key]))
    total=q.count(); items=q.order_by(SalesCommission.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    ccr_by_contract=get_company_commissions_by_contract_ids(db, [c.contract_id for c in items])
    paid_totals=dict(db.query(SalesCommission.contract_id, func.coalesce(func.sum(SalesCommission.paid_amount),0)).filter(SalesCommission.contract_id.in_([c.contract_id for c in items]), SalesCommission.paid_amount>0).group_by(SalesCommission.contract_id).all()) if items else {}
    rows=[]
    for c in items:
        ccr=ccr_by_contract.get(c.contract_id)
        policy=get_sales_commission_payout_policy_context(db, c, ccr, paid_totals.get(c.contract_id, 0))
        rows.append(row(c, policy, ccr))
    return {"items":rows,"total":total}

def summary(db, **f):
    summary_filters = dict(f)
    summary_filters.pop('page', None)
    summary_filters.pop('page_size', None)
    items=list_commissions(db,page=1,page_size=10000,**summary_filters)['items']
    return {"total_eligible_commission":sum(i['eligible_commission'] for i in items),"total_approved_commission":sum(i['approved_commission'] for i in items),"total_paid_amount":sum(i['paid_amount'] for i in items),"total_company_commission_received_linked":sum(i.get('company_commission_received_amount') or 0 for i in items),"missing_company_commission_count":sum(not i.get('company_commission_code') for i in items),"blocked_mark_paid_count":sum(i.get('status')=='approved' and not i.get('can_mark_paid_by_company_commission_policy') for i in items),"pending_count":sum(i['status']=='eligible' for i in items),"approved_count":sum(i['status']=='approved' for i in items),"paid_count":sum(i['status']=='paid' for i in items),"on_hold_count":sum(i['status']=='on_hold' for i in items),"cancelled_count":sum(i['status']=='cancelled' for i in items)}


def search_eligible_contracts(db, keyword=None, page=1, page_size=10):
    q=db.query(Contract).outerjoin(Customer, Contract.customer_id==Customer.id).outerjoin(SalesCommission, SalesCommission.contract_id==Contract.id).filter(Contract.deleted_at.is_(None))
    if keyword:
        term=f"%{keyword.strip()}%"
        q=q.filter(or_(Contract.contract_code.ilike(term), Contract.buyer_name.ilike(term), Contract.buyer_phone.ilike(term), Customer.full_name.ilike(term), Customer.primary_phone.ilike(term)))
    contracts=q.order_by(Contract.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    items=[]
    for contract in contracts:
        snap=_snapshot(db, contract, Decimal('1'))
        has_commission=db.query(SalesCommission.id).filter(SalesCommission.contract_id==contract.id).first() is not None
        customer=getattr(contract,'customer',None)
        is_cancelled=contract.status=='cancelled'
        has_legal_status=contract.status in COMMISSION_LEGAL_CONTRACT_STATUSES
        is_eligible=bool(snap['eligible']) and not is_cancelled and not has_commission
        if is_cancelled:
            reason='Hợp đồng đã hủy, không thể tạo hoa hồng.'
        elif has_commission:
            reason='Hợp đồng này đã có hoa hồng.'
        elif not has_legal_status:
            reason=LEGAL_STATUS_ERROR
        elif not snap['eligible']:
            reason='Hợp đồng chưa hoàn tất hoặc chưa thu đủ tiền.'
        else:
            reason=None
        items.append({
            'contract_id': str(contract.id),
            'contract_code': contract.contract_code,
            'customer_name': getattr(customer,'full_name',None) or contract.buyer_name,
            'customer_phone': getattr(customer,'primary_phone',None) or contract.buyer_phone,
            'contract_value': float(snap['contract_value']),
            'deposit_value': float(snap['deposit_value']),
            'total_collected_with_deposit': float(snap['total_collected_with_deposit']),
            'remaining_amount': float(snap['remaining_amount']),
            'contract_status': contract.status,
            'payment_status': 'paid' if snap['remaining_amount'] <= 0 else 'unpaid',
            'is_eligible_for_commission': is_eligible,
            'reason': reason,
            'has_commission': has_commission,
        })
    return {'items': items, 'total': len(items)}

def get_commission(db,id):
    c=base_query(db).filter(SalesCommission.id==id).first()
    if not c: raise HTTPException(404,'Không tìm thấy hoa hồng.')
    return c

def generate(db, contract_id, rate, note, actor):
    if rate<0 or rate>100: raise HTTPException(400,'Tỷ lệ hoa hồng phải trong khoảng 0–100%.')
    contract=db.query(Contract).options(joinedload(Contract.deal),joinedload(Contract.customer)).filter(Contract.id==contract_id).first()
    if not contract: raise HTTPException(404,'Không tìm thấy hợp đồng.')
    if contract.status=='cancelled': raise HTTPException(400,'Hợp đồng đã hủy, không thể tạo hoa hồng.')
    if contract.status not in COMMISSION_LEGAL_CONTRACT_STATUSES: raise HTTPException(400,LEGAL_STATUS_ERROR)
    snap=_snapshot(db,contract,rate)
    if not snap.pop('eligible'): raise HTTPException(400,'Hợp đồng chưa đủ điều kiện tạo hoa hồng: chưa hoàn tất hoặc chưa thu đủ tiền.')
    c=db.query(SalesCommission).filter_by(contract_id=contract.id).first()
    if c and c.status=='cancelled': raise HTTPException(400,'Hoa hồng của hợp đồng này đã bị hủy. Vui lòng tạo lại thủ công sau khi xác nhận nghiệp vụ.')
    if c and c.status in ('approved','paid'): raise HTTPException(400,'Hoa hồng đã duyệt hoặc đã chi trả, không thể cập nhật snapshot.')
    if not c:
        c=SalesCommission(commission_code=_code(db),contract_id=contract.id,created_by_id=actor.id,created_at=now(),updated_at=now()) ; db.add(c); ev='generated'; title='Tạo hoa hồng'
    else: ev='regenerated'; title='Cập nhật từ hợp đồng'
    for k,v in snap.items(): setattr(c,k,v)
    c.sale_id=_sale_id(contract); c.commission_rate_percent=rate; c.status='eligible'; c.note=note or c.note; c.updated_at=now()
    db.flush(); _event(db,c,ev,title,note,actor); db.commit(); db.refresh(c); return detail(get_commission(db,c.id))

def approve(db,id,amount,note,actor):
    c=get_commission(db,id)
    if c.status not in ('eligible','on_hold'): raise HTTPException(400,'Chỉ hoa hồng đủ điều kiện hoặc tạm giữ mới được duyệt.')
    policy=get_sales_commission_payout_policy_context(db,c)
    if not policy['can_approve_sales_commission']: raise HTTPException(400, policy['approve_block_reason'])
    amt=dec(amount) if amount is not None else dec(c.eligible_commission)
    if amt<0 or amt>dec(c.eligible_commission): raise HTTPException(400,'Số tiền duyệt không hợp lệ hoặc vượt hoa hồng đủ điều kiện.')
    c.status='approved'; c.approved_commission=amt; c.approved_by_id=actor.id; c.approved_at=now(); c.note=note or c.note; _event(db,c,'approved','Duyệt hoa hồng',note,actor); db.commit(); return detail(get_commission(db,id))

def mark_paid(db,id,amount,note,actor):
    c=get_commission(db,id)
    if c.status!='approved': raise HTTPException(400,'Chỉ hoa hồng đã duyệt mới được đánh dấu đã chi trả.')
    policy=get_sales_commission_payout_policy_context(db,c)
    if not policy['can_mark_paid_sales_commission']: raise HTTPException(400, policy['mark_paid_block_reason'])
    amt=dec(amount) if amount is not None else dec(c.approved_commission)
    if amt<0 or amt>dec(c.approved_commission): raise HTTPException(400,'Số tiền chi trả không hợp lệ hoặc vượt số tiền đã duyệt.')
    if amt>dec(policy['remaining_payable_capacity']): raise HTTPException(400,'Số tiền chi hoa hồng sale không được vượt số hoa hồng công ty đã nhận.')
    c.status='paid'; c.paid_amount=amt; c.paid_by_id=actor.id; c.paid_at=now(); c.note=note or c.note; _event(db,c,'paid','Đánh dấu đã chi trả',note,actor); db.commit(); return detail(get_commission(db,id))

def hold(db,id,reason,note,actor):
    c=get_commission(db,id); reason=(reason or '').strip()
    if c.status not in ('eligible','approved'): raise HTTPException(400,'Chỉ hoa hồng đủ điều kiện hoặc đã duyệt mới được tạm giữ.')
    if not reason: raise HTTPException(400,'Vui lòng nhập lý do tạm giữ.')
    c.status='on_hold'; c.hold_reason=reason; c.note=note or c.note; _event(db,c,'held','Tạm giữ hoa hồng',reason,actor); db.commit(); return detail(get_commission(db,id))

def cancel(db,id,reason,note,actor):
    c=get_commission(db,id); reason=(reason or '').strip()
    if c.status=='paid': raise HTTPException(400,'Hoa hồng đã chi trả, không thể hủy.')
    if not reason: raise HTTPException(400,'Vui lòng nhập lý do hủy.')
    c.status='cancelled'; c.cancel_reason=reason; c.note=note or c.note; _event(db,c,'cancelled','Hủy hoa hồng',reason,actor); db.commit(); return detail(get_commission(db,id))

def export_csv(db, **f):
    items=list_commissions(db,page=1,page_size=10000,**f)['items']; out=io.StringIO(); w=csv.writer(out)
    w.writerow(['Mã hoa hồng','Mã hợp đồng','Sale','Khách hàng','Giá trị hợp đồng','Đã thu gồm cọc','Còn lại','Tỷ lệ hoa hồng','Hoa hồng đủ điều kiện','Hoa hồng đã duyệt','Đã chi trả','Trạng thái','Ngày duyệt','Ngày chi trả','Lý do tạm giữ','Lý do hủy','Ghi chú'])
    for i in items: w.writerow([i['commission_code'],i['contract_code'],i['sale_name'],i['customer_name'],i['contract_value'],i['total_collected_with_deposit'],i['remaining_amount'],i['commission_rate_percent'],i['eligible_commission'],i['approved_commission'],i['paid_amount'],i['status_label'],i['approved_at'],i['paid_at'],i['hold_reason'],i['cancel_reason'],i['note']])
    return '\ufeff'+out.getvalue()
