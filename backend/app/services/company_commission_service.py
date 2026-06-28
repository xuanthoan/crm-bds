from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID
import csv, io
from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.company_commission import CompanyCommissionReceivable as CCR, CompanyCommissionEvent
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.user import User

LEGAL={'signed','active','completed'}; D=Decimal
STATUS_LABELS={'draft':'Bản nháp','pending':'Chờ duyệt','approved':'Đã duyệt','partially_received':'Đã nhận một phần','received':'Đã nhận đủ','on_hold':'Tạm giữ','cancelled':'Đã hủy'}
ROLE_LABELS={'broker':'Môi giới','distribution_agent':'Đại lý phân phối','authorized_representative':'Đại diện theo ủy quyền','direct_seller':'Bên bán trực tiếp'}
PAYER_LABELS={'investor':'Chủ đầu tư','landowner':'Chủ đất','homeowner':'Chủ nhà','distribution_partner':'Đối tác phân phối','customer':'Khách hàng','our_company':'Công ty tôi','other':'Khác'}
SELLER_LABELS={'investor':'Chủ đầu tư','landowner':'Chủ đất','homeowner':'Chủ nhà','our_company':'Công ty tôi','other':'Khác'}
def now(): return datetime.now(timezone.utc)
def dec(v): return D(str(v or 0))
def _code(db): return f"CCR-{(db.query(func.count(CCR.id)).scalar() or 0)+1:06d}"
def _sale(c): return getattr(getattr(c,'deal',None),'owner',None) or getattr(getattr(c,'deal',None),'owner_id',None)
def _event(db,r,t,old,new,amount=None,note=None,reason=None,actor=None): db.add(CompanyCommissionEvent(receivable_id=r.id,event_type=t,from_status=old,to_status=new,amount=amount,note=note,reason=reason,created_by_id=getattr(actor,'id',None),created_at=now()))
def _base(db): return db.query(CCR).options(joinedload(CCR.contract).joinedload(Contract.customer),joinedload(CCR.contract).joinedload(Contract.deal),joinedload(CCR.events).joinedload(CompanyCommissionEvent.created_by))
def _get(db,id):
    r=_base(db).filter(CCR.id==id).first()
    if not r: raise HTTPException(404,'Không tìm thấy hoa hồng công ty.')
    return r
def row(r):
    c=r.contract; cust=getattr(c,'customer',None); sale=getattr(getattr(c,'deal',None),'owner',None)
    return {'id':str(r.id),'receivable_code':r.receivable_code,'contract_id':str(r.contract_id),'contract_code':getattr(c,'contract_code',None),'customer_name':getattr(cust,'full_name',None) or getattr(c,'buyer_name',None),'customer_code':getattr(cust,'customer_code',None),'customer_phone':getattr(cust,'primary_phone',None) or getattr(c,'buyer_phone',None),'sale_name':getattr(sale,'full_name',None) or getattr(sale,'email',None),'company_role':r.company_role,'company_role_label':ROLE_LABELS.get(r.company_role,r.company_role),'actual_seller_type':r.actual_seller_type,'actual_seller_type_label':SELLER_LABELS.get(r.actual_seller_type or '',r.actual_seller_type),'actual_seller_name':r.actual_seller_name,'commission_payer_type':r.commission_payer_type,'commission_payer_type_label':PAYER_LABELS.get(r.commission_payer_type or '',r.commission_payer_type),'commission_payer_name':r.commission_payer_name,'brokerage_contract_code':r.brokerage_contract_code,'brokerage_policy_note':r.brokerage_policy_note,'contract_value':float(r.contract_value),'commission_rate_percent':float(r.commission_rate_percent or 0),'expected_commission_amount':float(r.expected_commission_amount),'confirmed_receivable_amount':float(r.confirmed_receivable_amount),'received_amount':float(r.received_amount),'remaining_amount':float(r.remaining_amount),'status':r.status,'status_label':STATUS_LABELS.get(r.status,r.status),'expected_receive_date':r.expected_receive_date.isoformat() if r.expected_receive_date else None,'received_date':r.received_date.isoformat() if r.received_date else None,'created_at':r.created_at.isoformat() if r.created_at else None,'note':r.note,'hold_reason':r.hold_reason,'cancel_reason':r.cancel_reason}
def detail(r):
    x=row(r); c=r.contract; cust=getattr(c,'customer',None); sale=getattr(getattr(c,'deal',None),'owner',None)
    x.update({'contract':{'id':str(c.id),'contract_code':c.contract_code,'contract_value':float(c.contract_value),'status':c.status},'customer':{'name':x['customer_name'],'code':x['customer_code'],'phone':x['customer_phone']},'sale':{'name':x['sale_name']},'events':[{'id':str(e.id),'event_type':e.event_type,'from_status':e.from_status,'to_status':e.to_status,'amount':float(e.amount or 0) if e.amount is not None else None,'note':e.note,'reason':e.reason,'created_by_name':getattr(e.created_by,'full_name',None) or getattr(e.created_by,'email',None) if e.created_by else None,'created_at':e.created_at.isoformat()} for e in r.events]})
    return x
def _query(db, **f):
    q=_base(db).join(Contract,CCR.contract_id==Contract.id).outerjoin(Customer,Contract.customer_id==Customer.id)
    if f.get('status'): q=q.filter(CCR.status==f['status'])
    if f.get('contract_id'): q=q.filter(CCR.contract_id==f['contract_id'])
    if f.get('payer_type'): q=q.filter(CCR.commission_payer_type==f['payer_type'])
    if f.get('company_role'): q=q.filter(CCR.company_role==f['company_role'])
    if f.get('from_date'): q=q.filter(CCR.created_at>=f['from_date'])
    if f.get('to_date'): q=q.filter(CCR.created_at<=f['to_date'])
    kw=(f.get('keyword') or '').strip()
    if kw: q=q.filter(or_(CCR.receivable_code.ilike(f'%{kw}%'),Contract.contract_code.ilike(f'%{kw}%'),Customer.full_name.ilike(f'%{kw}%'),Customer.primary_phone.ilike(f'%{kw}%'),CCR.actual_seller_name.ilike(f'%{kw}%'),CCR.commission_payer_name.ilike(f'%{kw}%'),CCR.brokerage_contract_code.ilike(f'%{kw}%')))
    return q

def get_company_commission_for_contract(db, contract_id):
    return _base(db).filter(CCR.contract_id==contract_id).first()

def list_receivables(db,page=1,page_size=20,**f):
    q=_query(db,**f); total=q.count(); items=q.order_by(CCR.created_at.desc()).offset((page-1)*page_size).limit(page_size).all(); return {'items':[row(i) for i in items],'total':total}
def summary(db,**f):
    items=[row(i) for i in _query(db,**f).all()]
    return {'total_expected_commission_amount':sum(i['expected_commission_amount'] for i in items),'total_confirmed_receivable_amount':sum(i['confirmed_receivable_amount'] for i in items),'total_received_amount':sum(i['received_amount'] for i in items),'total_remaining_amount':sum(i['remaining_amount'] for i in items),'total_count':len(items),**{s+'_count':sum(i['status']==s for i in items) for s in ['pending','approved','partially_received','received','on_hold','cancelled']}}
def eligible_contracts(db, keyword=None, limit=20):
    q=db.query(Contract).outerjoin(Customer,Contract.customer_id==Customer.id).filter(Contract.deleted_at.is_(None))
    if keyword:
        t=f"%{keyword.strip()}%"; q=q.filter(or_(Contract.contract_code.ilike(t),Customer.full_name.ilike(t),Customer.primary_phone.ilike(t),Contract.buyer_name.ilike(t)))
    out=[]
    for c in q.order_by(Contract.created_at.desc()).limit(limit).all():
        has=db.query(CCR.id).filter(CCR.contract_id==c.id).first() is not None; reason=None
        if c.status=='cancelled': reason='Hợp đồng đã hủy, không thể tạo hoa hồng công ty.'
        elif has: reason='Hợp đồng này đã có khoản hoa hồng công ty.'
        elif c.status not in LEGAL: reason='Hợp đồng chưa đủ trạng thái pháp lý để tạo hoa hồng công ty.'
        cust=getattr(c,'customer',None); sale=getattr(getattr(c,'deal',None),'owner',None)
        out.append({'contract_id':str(c.id),'contract_code':c.contract_code,'customer_name':getattr(cust,'full_name',None) or c.buyer_name,'customer_code':getattr(cust,'customer_code',None),'customer_phone':getattr(cust,'primary_phone',None) or c.buyer_phone,'sale_name':getattr(sale,'full_name',None) or getattr(sale,'email',None),'contract_value':float(c.contract_value),'contract_status':c.status,'company_role':c.company_role,'actual_seller_type':c.actual_seller_type,'actual_seller_name':c.actual_seller_name,'commission_payer_type':c.commission_payer_type,'commission_payer_name':c.commission_payer_name,'brokerage_contract_code':c.brokerage_contract_code,'has_company_commission':has,'is_eligible_for_company_commission':reason is None,'reason':reason})
    return {'items':out,'total':len(out)}
def generate(db,contract_id,rate,expected,expected_date,note,actor):
    rate=dec(rate)
    if rate<=0: raise HTTPException(400,'Tỷ lệ hoa hồng công ty phải lớn hơn 0.')
    c=db.query(Contract).filter(Contract.id==contract_id,Contract.deleted_at.is_(None)).first()
    if not c: raise HTTPException(404,'Không tìm thấy hợp đồng.')
    if c.status=='cancelled': raise HTTPException(400,'Hợp đồng đã hủy, không thể tạo hoa hồng công ty.')
    if c.status not in LEGAL: raise HTTPException(400,'Hợp đồng chưa đủ trạng thái pháp lý để tạo hoa hồng công ty.')
    if db.query(CCR.id).filter(CCR.contract_id==c.id).first(): raise HTTPException(400,'Hợp đồng này đã có khoản hoa hồng công ty.')
    exp=dec(expected) if expected is not None else (dec(c.contract_value)*rate/D('100')).quantize(D('0.01'))
    if exp<=0: raise HTTPException(400,'Hoa hồng dự kiến phải lớn hơn 0.')
    r=CCR(receivable_code=_code(db),contract_id=c.id,company_role=c.company_role or 'broker',actual_seller_type=c.actual_seller_type,actual_seller_name=c.actual_seller_name,commission_payer_type=c.commission_payer_type,commission_payer_name=c.commission_payer_name,brokerage_contract_code=c.brokerage_contract_code,brokerage_policy_note=c.brokerage_policy_note,contract_value=c.contract_value,commission_rate_percent=rate,expected_commission_amount=exp,confirmed_receivable_amount=exp,remaining_amount=exp,status='pending',expected_receive_date=expected_date,note=note,created_by_id=actor.id,created_at=now(),updated_at=now())
    db.add(r); db.flush(); _event(db,r,'created',None,'pending',exp,note,actor=actor); db.commit(); return detail(_get(db,r.id))
def approve(db,id,amount,note,actor):
    r=_get(db,id)
    if r.status not in ('pending','on_hold'): raise HTTPException(400,'Chỉ khoản hoa hồng công ty chờ duyệt hoặc tạm giữ mới được duyệt.')
    amt=dec(amount)
    if amt<=0: raise HTTPException(400,'Hoa hồng xác nhận phải lớn hơn 0.')
    if amt>dec(r.expected_commission_amount): raise HTTPException(400,'Hoa hồng xác nhận không được vượt quá hoa hồng dự kiến.')
    old=r.status; r.status='approved'; r.confirmed_receivable_amount=amt; r.remaining_amount=amt-dec(r.received_amount); r.approved_by_id=actor.id; r.approved_at=now(); r.note=note or r.note; _event(db,r,'approved',old,r.status,amt,note,actor=actor); db.commit(); return detail(_get(db,id))
def receive(db,id,amount,received_date,note,actor):
    r=_get(db,id)
    if r.status not in ('approved','partially_received'): raise HTTPException(400,'Chỉ khoản hoa hồng công ty đã duyệt mới được ghi nhận đã nhận tiền.')
    amt=dec(amount)
    if amt<=0: raise HTTPException(400,'Số tiền nhận lần này phải lớn hơn 0.')
    if dec(r.received_amount)+amt>dec(r.confirmed_receivable_amount): raise HTTPException(400,'Số tiền đã nhận không được vượt quá hoa hồng xác nhận.')
    old=r.status; r.received_amount=dec(r.received_amount)+amt; r.remaining_amount=max(dec(r.confirmed_receivable_amount)-dec(r.received_amount),D('0')); r.status='received' if r.remaining_amount==0 else 'partially_received'; r.marked_received_by_id=actor.id; r.marked_received_at=now();
    if r.status=='received': r.received_date=received_date or date.today()
    r.note=note or r.note; _event(db,r,r.status,old,r.status,amt,note,actor=actor); db.commit(); return detail(_get(db,id))
def hold(db,id,reason,note,actor):
    r=_get(db,id); reason=(reason or '').strip()
    if r.status not in ('pending','approved'): raise HTTPException(400,'Chỉ khoản hoa hồng công ty chờ duyệt hoặc đã duyệt mới được tạm giữ.')
    if not reason: raise HTTPException(400,'Lý do tạm giữ là bắt buộc.')
    old=r.status; r.status='on_hold'; r.hold_reason=reason; r.note=note or r.note; _event(db,r,'held',old,r.status,note=note,reason=reason,actor=actor); db.commit(); return detail(_get(db,id))
def cancel(db,id,reason,note,actor):
    r=_get(db,id); reason=(reason or '').strip()
    if r.status in ('partially_received','received') or dec(r.received_amount)>0: raise HTTPException(400,'Khoản hoa hồng công ty đã nhận tiền, không thể hủy.')
    if r.status not in ('pending','approved','on_hold'): raise HTTPException(400,'Trạng thái hiện tại không cho phép hủy hoa hồng công ty.')
    if not reason: raise HTTPException(400,'Lý do hủy là bắt buộc.')
    old=r.status; r.status='cancelled'; r.cancel_reason=reason; r.cancelled_by_id=actor.id; r.cancelled_at=now(); r.note=note or r.note; _event(db,r,'cancelled',old,r.status,note=note,reason=reason,actor=actor); db.commit(); return detail(_get(db,id))
def export_csv(db,**f):
    out=io.StringIO(); w=csv.writer(out); items=[row(i) for i in _query(db,**f).all()]
    w.writerow(['Mã hoa hồng công ty','Mã hợp đồng','Khách hàng','Sale','Vai trò công ty','Bên bán thực tế','Tên bên bán','Bên trả hoa hồng','Tên bên trả hoa hồng','Mã hợp đồng/chính sách môi giới','Giá trị hợp đồng','Tỷ lệ HH công ty','HH dự kiến','HH xác nhận','Đã nhận','Còn phải thu','Trạng thái','Ngày dự kiến nhận','Ngày nhận đủ','Ghi chú'])
    for i in items: w.writerow([i['receivable_code'],i['contract_code'],i['customer_name'],i['sale_name'],i['company_role_label'],i['actual_seller_type_label'],i['actual_seller_name'],i['commission_payer_type_label'],i['commission_payer_name'],i['brokerage_contract_code'],i['contract_value'],i['commission_rate_percent'],i['expected_commission_amount'],i['confirmed_receivable_amount'],i['received_amount'],i['remaining_amount'],i['status_label'],i['expected_receive_date'],i['received_date'],i['note']])
    return '\ufeff'+out.getvalue()
