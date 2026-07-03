from __future__ import annotations
import csv, io
from datetime import date
from decimal import Decimal
from uuid import UUID
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.project import Project
from app.models.user import User
from app.models.sales_commission import SalesCommission
from app.models.company_commission import CompanyCommissionReceivable
from app.models.commission_payment_voucher import SalesCommissionPaymentVoucher
from app.services.commission_service import sync_commission_paid_amount_from_vouchers, get_sales_commission_payout_policy_context, STATUSES as COM_STATUS_LABELS, POLICY_SOURCE_LABELS
from app.services.company_commission_service import STATUS_LABELS as CCR_STATUS_LABELS
from app.permissions.dependencies import get_user_permissions

D=Decimal

def dec(v): return D(str(v or 0))
def f(v): return float(dec(v))
def s(v): return str(v) if v is not None else None

def _base(db:Session):
    return db.query(SalesCommission).options(joinedload(SalesCommission.contract).joinedload(Contract.customer),joinedload(SalesCommission.contract).joinedload(Contract.project),joinedload(SalesCommission.sale),joinedload(SalesCommission.payment_vouchers)).join(Contract, SalesCommission.contract_id==Contract.id).outerjoin(Customer, Contract.customer_id==Customer.id).outerjoin(Project, Contract.project_id==Project.id).outerjoin(User, SalesCommission.sale_id==User.id).outerjoin(CompanyCommissionReceivable, CompanyCommissionReceivable.contract_id==Contract.id)

def _apply_filters(query, actor=None, **fil):
    perms=set(get_user_permissions(actor)) if actor else set()
    if actor and not getattr(actor,'is_superuser',False) and 'reports.commission_reconciliation.view' in perms and 'commissions.view.all' not in perms and 'commissions.view.team' not in perms:
        query=query.filter(SalesCommission.sale_id==actor.id)
    if fil.get('date_from'): query=query.filter(SalesCommission.created_at>=fil['date_from'])
    if fil.get('date_to'): query=query.filter(SalesCommission.created_at<=fil['date_to'])
    for k,col in [('project_id',Contract.project_id),('sale_id',SalesCommission.sale_id),('contract_id',SalesCommission.contract_id),('customer_id',Contract.customer_id),('company_commission_status',CompanyCommissionReceivable.status),('sales_commission_status',SalesCommission.status)]:
        if fil.get(k): query=query.filter(col==fil[k])
    if fil.get('voucher_status'):
        query=query.join(SalesCommissionPaymentVoucher, SalesCommissionPaymentVoucher.sales_commission_id==SalesCommission.id).filter(SalesCommissionPaymentVoucher.status==fil['voucher_status'])
    if fil.get('q'):
        term=f"%{fil['q'].strip()}%"
        query=query.filter(or_(Contract.contract_code.ilike(term), Customer.full_name.ilike(term), Project.name.ilike(term), User.full_name.ilike(term), User.email.ilike(term), SalesCommission.commission_code.ilike(term), CompanyCommissionReceivable.receivable_code.ilike(term)))
    return query

def _voucher_stats(c):
    stats={'draft':0,'paid':0,'cancelled':0}; paid=D('0')
    for v in c.payment_vouchers:
        if v.status=='draft': stats['draft']+=1
        elif v.status=='cancelled': stats['cancelled']+=1
        elif v.status=='paid': stats['paid']+=1
        if v.status=='paid': paid+=dec(v.amount)
    return stats, paid

def _ccr(db, contract_id): return db.query(CompanyCommissionReceivable).filter(CompanyCommissionReceivable.contract_id==contract_id).first()

def _row(db, c, actor=None):
    sync_commission_paid_amount_from_vouchers(db,c)
    ccr=_ccr(db,c.contract_id); policy=get_sales_commission_payout_policy_context(db,c,ccr,actor=actor)
    stats, voucher_paid=_voucher_stats(c); contract=c.contract; customer=getattr(contract,'customer',None); project=getattr(contract,'project',None); sale=c.sale
    company_confirmed=dec(getattr(ccr,'confirmed_receivable_amount',0) if ccr else 0); company_received=dec(getattr(ccr,'received_amount',0) if ccr else 0)
    sales_approved=dec(c.approved_commission); sales_paid=dec(c.paid_amount); remaining_sale=max(sales_approved-sales_paid,D('0')); capacity=dec(policy.get('remaining_payable_capacity'))
    flags=[]
    if not ccr: flags.append('no_company_commission')
    if not c: flags.append('no_sales_commission')
    if ccr and company_received < company_confirmed: flags.append('company_not_fully_received')
    if stats['draft']>0: flags.append('draft_voucher_pending')
    if sales_approved>0 and sales_paid<=0: flags.append('sale_unpaid')
    elif sales_approved>0 and sales_paid<sales_approved: flags.append('sale_partially_paid')
    elif sales_approved>0 and sales_paid>=sales_approved: flags.append('sale_paid')
    if sales_paid>sales_approved and sales_approved>=0: flags.append('over_paid')
    if company_received>company_confirmed and company_confirmed>=0: flags.append('over_received')
    if remaining_sale>0 and capacity < remaining_sale: flags.append('blocked_by_policy')
    status='ok' if not flags else ('over_paid' if 'over_paid' in flags else 'blocked_by_policy' if 'blocked_by_policy' in flags else 'draft_voucher_pending' if 'draft_voucher_pending' in flags else 'company_not_fully_received' if 'company_not_fully_received' in flags else flags[-1])
    return {'contract_id':s(c.contract_id),'contract_code':contract.contract_code,'contract_status':contract.status,'customer_id':s(contract.customer_id),'customer_name':getattr(customer,'full_name',None) or contract.buyer_name,'project_id':s(getattr(project,'id',None)),'project_name':getattr(project,'name',None),'sale_id':s(c.sale_id),'sale_name':getattr(sale,'full_name',None) or getattr(sale,'email',None),'company_commission_id':s(getattr(ccr,'id',None)),'company_commission_code':getattr(ccr,'receivable_code',None),'company_commission_status':getattr(ccr,'status',None),'company_commission_status_label':CCR_STATUS_LABELS.get(getattr(ccr,'status',None),getattr(ccr,'status',None)),'company_commission_confirmed_amount':f(company_confirmed),'company_commission_received_amount':f(company_received),'company_commission_remaining_amount':f(max(company_confirmed-company_received,D('0'))),'sales_commission_id':s(c.id),'sales_commission_code':c.commission_code,'sales_commission_status':c.status,'sales_commission_status_label':COM_STATUS_LABELS.get(c.status,c.status),'sales_commission_approved_amount':f(sales_approved),'sales_commission_paid_amount':f(sales_paid),'sales_commission_remaining_amount':f(remaining_sale),'payout_policy_code':policy.get('payout_policy_code'),'payout_policy_source':policy.get('payout_policy_source'),'payout_policy_source_label':POLICY_SOURCE_LABELS.get(policy.get('payout_policy_source'),policy.get('payout_policy_source')),'payout_policy_label':policy.get('payout_policy_label'),'remaining_payable_capacity':f(capacity),'voucher_draft_count':stats['draft'],'voucher_paid_count':stats['paid'],'voucher_cancelled_count':stats['cancelled'],'voucher_paid_amount':f(voucher_paid),'reconciliation_status':status,'reconciliation_flags':flags}

def list_report(db:Session, page=1, page_size=20, actor=None, **filters):
    q=_apply_filters(_base(db),actor=actor,**filters).distinct()
    rows=[_row(db,c,actor) for c in q.order_by(SalesCommission.created_at.desc()).all()]
    if filters.get('has_draft_voucher') is not None: rows=[r for r in rows if (r['voucher_draft_count']>0)==filters['has_draft_voucher']]
    if filters.get('only_blocked_by_policy'): rows=[r for r in rows if 'blocked_by_policy' in r['reconciliation_flags']]
    if filters.get('only_has_remaining_sale_payable'): rows=[r for r in rows if r['sales_commission_remaining_amount']>0]
    if filters.get('reconciliation_status'): rows=[r for r in rows if filters['reconciliation_status'] in ([r['reconciliation_status']]+r['reconciliation_flags'])]
    active=[r for r in rows if r['sales_commission_status']!='cancelled' and r['company_commission_status']!='cancelled']
    summary={'total_company_commission_confirmed':sum(r['company_commission_confirmed_amount'] for r in active),'total_company_commission_received':sum(r['company_commission_received_amount'] for r in active),'total_company_commission_remaining':sum(r['company_commission_remaining_amount'] for r in active),'total_sales_commission_approved':sum(r['sales_commission_approved_amount'] for r in active),'total_sales_commission_paid':sum(r['sales_commission_paid_amount'] for r in active),'total_sales_commission_remaining':sum(r['sales_commission_remaining_amount'] for r in active),'total_remaining_payable_capacity':sum(r['remaining_payable_capacity'] for r in active),'draft_voucher_count':sum(r['voucher_draft_count'] for r in active),'paid_voucher_count':sum(r['voucher_paid_count'] for r in active),'cancelled_voucher_count':sum(r['voucher_cancelled_count'] for r in active),'row_count':len(rows),'sale_unpaid_count':sum('sale_unpaid' in r['reconciliation_flags'] for r in active),'sale_partially_paid_count':sum('sale_partially_paid' in r['reconciliation_flags'] for r in active),'sale_paid_count':sum('sale_paid' in r['reconciliation_flags'] for r in active),'blocked_by_policy_count':sum('blocked_by_policy' in r['reconciliation_flags'] for r in active),'over_paid_count':sum('over_paid' in r['reconciliation_flags'] for r in active),'over_received_count':sum('over_received' in r['reconciliation_flags'] for r in active)}
    total=len(rows); start=(page-1)*page_size
    return {'summary':summary,'items':rows[start:start+page_size],'pagination':{'page':page,'page_size':page_size,'total':total,'pages':(total+page_size-1)//page_size}}

def export_csv(db, actor=None, **filters):
    data=list_report(db,page=1,page_size=10000,actor=actor,**filters); out=io.StringIO(); w=csv.writer(out)
    headers=['Mã hợp đồng','Dự án','Khách hàng','Sale','Mã HH công ty','Trạng thái HH công ty','HH công ty xác nhận','HH công ty đã nhận','HH công ty còn phải thu','Mã HH sale','Trạng thái HH sale','HH sale đã duyệt','HH sale đã chi','HH sale còn phải chi','Chính sách chi','Hạn mức còn có thể chi','Phiếu nháp','Phiếu đã chi','Trạng thái đối soát','Cảnh báo']
    w.writerow(headers)
    for r in data['items']:
        w.writerow([r['contract_code'],r['project_name'],r['customer_name'],r['sale_name'],r['company_commission_code'],r['company_commission_status_label'],r['company_commission_confirmed_amount'],r['company_commission_received_amount'],r['company_commission_remaining_amount'],r['sales_commission_code'],r['sales_commission_status_label'],r['sales_commission_approved_amount'],r['sales_commission_paid_amount'],r['sales_commission_remaining_amount'],r['payout_policy_label'],r['remaining_payable_capacity'],r['voucher_draft_count'],r['voucher_paid_count'],r['reconciliation_status'],', '.join(r['reconciliation_flags'])])
    return '\ufeff'+out.getvalue()
