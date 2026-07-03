from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
import csv, io
from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, object_session
from app.models.commission_payment_voucher import SalesCommissionPaymentVoucher
from app.models.sales_commission import SalesCommission
from app.models.contract import Contract
from app.models.user import User
from app.services.commission_service import D, dec, money_limit, now, get_commission, get_sales_commission_payout_policy_context, _event, sync_commission_paid_amount_from_vouchers
from app.permissions.dependencies import get_user_permissions

STATUSES={'draft':'Nháp','paid':'Đã chi','cancelled':'Đã hủy'}
METHODS={'cash':'Tiền mặt','bank_transfer':'Chuyển khoản','other':'Khác'}
VALID_STATUSES=set(STATUSES); VALID_METHODS=set(METHODS)

def _code(db):
    today=date.today().strftime('%Y%m%d')
    n=db.query(func.count(SalesCommissionPaymentVoucher.id)).filter(SalesCommissionPaymentVoucher.code.like(f'SCPV-{today}-%')).scalar() or 0
    return f'SCPV-{today}-{n+1:04d}'

def _name(u): return getattr(u,'full_name',None) or getattr(u,'email',None)

def can_cancel_paid(actor):
    return getattr(actor,'is_superuser',False) or 'commissions.payment_vouchers.cancel_paid' in set(get_user_permissions(actor))

def _validate_commission_for_payment(db,c,amount):
    sync_commission_paid_amount_from_vouchers(db,c)
    if c.status in ('cancelled','on_hold'): raise HTTPException(400,'Hoa hồng này đang tạm giữ/đã hủy nên không thể lập phiếu chi.')
    if c.status not in ('approved','partially_paid','paid'): raise HTTPException(400,'Hoa hồng này chưa được duyệt.')
    if dec(c.approved_commission)<=0: raise HTTPException(400,'Hoa hồng này chưa có số tiền duyệt hợp lệ.')
    policy=get_sales_commission_payout_policy_context(db,c)
    if not policy['can_mark_paid_sales_commission']: raise HTTPException(400, policy['mark_paid_block_reason'] or 'Hoa hồng chưa đủ điều kiện chi.')
    if dec(amount)>dec(policy['remaining_payable_capacity']): raise HTTPException(400,'Số tiền chi không được vượt quá hạn mức có thể chi.')
    return policy

def recalculate_sales_commission_paid_amount(db:Session, sales_commission_id):
    c=get_commission(db,sales_commission_id)
    sync_commission_paid_amount_from_vouchers(db,c)
    if dec(c.approved_commission)>0 and dec(c.paid_amount)>dec(c.approved_commission): raise HTTPException(400,'Tổng phiếu chi vượt số tiền hoa hồng đã duyệt.')
    db.flush()
    return c

def row(v):
    c=v.commission; contract=v.contract; sale=v.sale
    return {'id':str(v.id),'code':v.code,'status':v.status,'status_label':STATUSES.get(v.status,v.status),'amount':float(v.amount or 0),'payment_date':v.payment_date.isoformat() if v.payment_date else None,'payment_method':v.payment_method,'payment_method_label':METHODS.get(v.payment_method,v.payment_method),'payment_reference':v.payment_reference,'sale_id':str(v.sale_id),'sale_name':_name(sale),'contract_id':str(v.contract_id) if v.contract_id else None,'contract_code':getattr(contract,'contract_code',None),'sales_commission_id':str(v.sales_commission_id),'sales_commission_code':getattr(c,'commission_code',None),'created_by_name':_name(v.created_by),'paid_by_name':_name(v.paid_by),'cancelled_by_name':_name(v.cancelled_by),'created_at':v.created_at.isoformat() if v.created_at else None,'paid_at':v.paid_at.isoformat() if v.paid_at else None,'cancelled_at':v.cancelled_at.isoformat() if v.cancelled_at else None,'cancel_reason':v.cancel_reason,'note':v.note,'attachment_url':v.attachment_url}

def detail(v):
    data=row(v); c=v.commission; data.update({'commission': {'code':c.commission_code,'approved_amount':float(c.approved_commission or 0),'paid_amount':float(c.paid_amount or 0),'legacy_paid_amount':float(getattr(c,'legacy_paid_amount',0) or 0),'remaining_amount':float(max(dec(c.approved_commission)-dec(c.paid_amount),D('0'))),'payout_policy':get_sales_commission_payout_policy_context(object_session(c),c)}, 'contract': {'code':getattr(v.contract,'contract_code',None),'customer':getattr(v.contract,'buyer_name',None)}, 'sale': {'id':str(v.sale_id),'name':data['sale_name']}}); return data

def base(db): return db.query(SalesCommissionPaymentVoucher).options(joinedload(SalesCommissionPaymentVoucher.commission),joinedload(SalesCommissionPaymentVoucher.contract),joinedload(SalesCommissionPaymentVoucher.sale),joinedload(SalesCommissionPaymentVoucher.created_by),joinedload(SalesCommissionPaymentVoucher.paid_by),joinedload(SalesCommissionPaymentVoucher.cancelled_by))
def get(db,id):
    v=base(db).filter(SalesCommissionPaymentVoucher.id==id).first()
    if not v: raise HTTPException(404,'Không tìm thấy phiếu chi hoa hồng.')
    return v

def list_vouchers(db,page=1,page_size=20,**f):
    q=base(db).join(SalesCommission, SalesCommissionPaymentVoucher.sales_commission_id==SalesCommission.id).outerjoin(Contract, SalesCommissionPaymentVoucher.contract_id==Contract.id).outerjoin(User, SalesCommissionPaymentVoucher.sale_id==User.id)
    for k,col in [('sales_commission_id',SalesCommissionPaymentVoucher.sales_commission_id),('contract_id',SalesCommissionPaymentVoucher.contract_id),('sale_id',SalesCommissionPaymentVoucher.sale_id),('status',SalesCommissionPaymentVoucher.status),('payment_method',SalesCommissionPaymentVoucher.payment_method)]:
        if f.get(k): q=q.filter(col==f[k])
    if f.get('payment_date_from'): q=q.filter(SalesCommissionPaymentVoucher.payment_date>=f['payment_date_from'])
    if f.get('payment_date_to'): q=q.filter(SalesCommissionPaymentVoucher.payment_date<=f['payment_date_to'])
    if f.get('q'):
        term=f"%{f['q']}%"; q=q.filter(or_(SalesCommissionPaymentVoucher.code.ilike(term),SalesCommission.commission_code.ilike(term),Contract.contract_code.ilike(term)))
    total=q.count(); items=q.order_by(SalesCommissionPaymentVoucher.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {'items':[row(v) for v in items], 'total':total}

def create(db, payload, actor):
    c=get_commission(db,payload.sales_commission_id); amount=money_limit(payload.amount)
    if amount<=0: raise HTTPException(400,'Số tiền chi phải lớn hơn 0.')
    if not c.sale_id: raise HTTPException(400,'Hoa hồng chưa có sale nhận tiền.')
    status=payload.status or 'paid'
    if status not in ('draft','paid'): raise HTTPException(400,'Trạng thái phiếu chi không hợp lệ.')
    if payload.payment_method not in VALID_METHODS: raise HTTPException(400,'Phương thức chi không hợp lệ.')
    _validate_commission_for_payment(db,c,amount)
    v=SalesCommissionPaymentVoucher(code=_code(db),sales_commission_id=c.id,contract_id=c.contract_id,sale_id=c.sale_id,amount=amount,payment_date=payload.payment_date or date.today(),payment_method=payload.payment_method,payment_reference=payload.payment_reference,status=status,created_by_id=actor.id,note=payload.note,attachment_url=payload.attachment_url,created_at=now(),updated_at=now())
    if status=='paid': v.paid_by_id=actor.id; v.paid_at=now()
    db.add(v); db.flush()
    if status=='paid': recalculate_sales_commission_paid_amount(db,c.id); _event(db,c,'payment_voucher_paid','Lập phiếu chi hoa hồng',v.code,actor)
    else: _event(db,c,'payment_voucher_draft','Lưu nháp phiếu chi hoa hồng',v.code,actor)
    db.commit(); return detail(get(db,v.id))

def update(db,id,payload,actor):
    v=get(db,id)
    if v.status!='draft': raise HTTPException(400,'Chỉ được sửa phiếu chi nháp.')
    amount=money_limit(payload.amount) if payload.amount is not None else v.amount
    _validate_commission_for_payment(db,v.commission,amount)
    for field in ['payment_date','payment_method','payment_reference','note','attachment_url']:
        val=getattr(payload,field,None)
        if val is not None: setattr(v,field,val)
    v.amount=amount; v.updated_at=now(); db.commit(); return detail(get(db,id))

def mark_paid(db,id,payload,actor):
    v=get(db,id)
    if v.status!='draft': raise HTTPException(400,'Chỉ phiếu nháp mới có thể xác nhận đã chi.')
    _validate_commission_for_payment(db,v.commission,v.amount)
    if getattr(payload,'payment_date',None): v.payment_date=payload.payment_date
    if getattr(payload,'payment_reference',None): v.payment_reference=payload.payment_reference
    if getattr(payload,'note',None): v.note=(v.note or '')+'\n'+payload.note if v.note else payload.note
    v.status='paid'; v.paid_by_id=actor.id; v.paid_at=now(); v.updated_at=now(); recalculate_sales_commission_paid_amount(db,v.sales_commission_id); _event(db,v.commission,'payment_voucher_paid','Xác nhận đã chi phiếu hoa hồng',v.code,actor); db.commit(); return detail(get(db,id))

def cancel(db,id,reason,actor):
    v=get(db,id); reason=(reason or '').strip()
    if v.status=='cancelled': raise HTTPException(400,'Phiếu chi đã hủy nên không thể thao tác.')
    if not reason: raise HTTPException(400,'Vui lòng nhập lý do hủy phiếu chi.')
    if v.status=='paid' and not can_cancel_paid(actor): raise HTTPException(403,'Bạn không có quyền hủy phiếu chi đã chi.')
    was_paid=v.status=='paid'; v.status='cancelled'; v.cancel_reason=reason; v.cancelled_by_id=actor.id; v.cancelled_at=now(); v.updated_at=now()
    if was_paid: recalculate_sales_commission_paid_amount(db,v.sales_commission_id)
    _event(db,v.commission,'payment_voucher_cancelled','Hủy phiếu chi hoa hồng',reason,actor); db.commit(); return detail(get(db,id))

def export_csv(db, **f):
    items=list_vouchers(db,page=1,page_size=10000,**f)['items']; out=io.StringIO(); w=csv.writer(out); w.writerow(['Mã phiếu','Trạng thái','Ngày chi','Sale nhận','Hợp đồng','Mã hoa hồng','Số tiền','Phương thức','Người chi','Ngày tạo','Ghi chú'])
    for i in items: w.writerow([i['code'],i['status_label'],i['payment_date'],i['sale_name'],i['contract_code'],i['sales_commission_code'],i['amount'],i['payment_method_label'],i['paid_by_name'],i['created_at'],i['note']])
    return '\ufeff'+out.getvalue()
