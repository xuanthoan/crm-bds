from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.contracts.constants import CONTRACT_STATUS_LABELS
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.payment_invoice import PaymentInvoice
from app.models.payment_receipt import PaymentReceipt
from app.models.payment_schedule import PaymentSchedule
from app.models.user import User
from app.payments_constants import INVOICE_STATUS_LABELS, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, RECEIPT_STATUS_LABELS
from app.permissions.dependencies import get_user_permissions


@dataclass
class ReportFilters:
    date_from: date | None = None
    date_to: date | None = None
    project_id: UUID | None = None
    property_id: UUID | None = None
    sale_id: UUID | None = None
    assigned_user_id: UUID | None = None
    contract_status: str | None = None
    payment_status: str | None = None
    lead_source: str | None = None
    customer_keyword: str | None = None
    contract_keyword: str | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 20


def require_finance_view(user: User) -> None:
    if user.is_superuser:
        return
    perms = set(get_user_permissions(user))
    if 'reports.view.finance' not in perms and 'reports.view.all' not in perms:
        raise HTTPException(403, 'Bạn không có quyền xem báo cáo tài chính.')


def require_finance_export(user: User) -> None:
    if user.is_superuser:
        return
    perms = set(get_user_permissions(user))
    if 'reports.export' not in perms:
        raise HTTPException(403, 'Bạn không có quyền xuất báo cáo tài chính.')


def money(v) -> Decimal:
    return Decimal(v or 0)


def _dt_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _dt_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _contract_conditions(f: ReportFilters):
    cond = [Contract.deleted_at.is_(None)]
    if f.date_from:
        cond.append(or_(Contract.signed_date >= _dt_start(f.date_from), Contract.signed_date.is_(None) & (Contract.created_at >= _dt_start(f.date_from))))
    if f.date_to:
        cond.append(or_(Contract.signed_date <= _dt_end(f.date_to), Contract.signed_date.is_(None) & (Contract.created_at <= _dt_end(f.date_to))))
    if f.project_id:
        cond.append(Contract.project_id == f.project_id)
    if f.property_id:
        cond.append(Contract.property_unit_id == f.property_id)
    if f.sale_id or f.assigned_user_id:
        cond.append(Contract.created_by_id == (f.sale_id or f.assigned_user_id))
    if f.contract_status:
        cond.append(Contract.status == f.contract_status)
    if f.lead_source:
        cond.append(Contract.customer.has(Customer.source == f.lead_source))
    if f.customer_keyword:
        term = f'%{f.customer_keyword.strip()}%'
        cond.append(Contract.customer.has(or_(Customer.full_name.ilike(term), Customer.primary_phone.ilike(term), Customer.customer_code.ilike(term))))
    if f.contract_keyword:
        cond.append(Contract.contract_code.ilike(f'%{f.contract_keyword.strip()}%'))
    return cond


def _receipt_sum_by_contract(db: Session, contract_ids: list):
    if not contract_ids:
        return {}
    rows = db.execute(select(PaymentReceipt.contract_id, func.coalesce(func.sum(PaymentReceipt.amount), 0)).where(PaymentReceipt.contract_id.in_(contract_ids), PaymentReceipt.status == 'confirmed', PaymentReceipt.deleted_at.is_(None)).group_by(PaymentReceipt.contract_id)).all()
    return {cid: money(total) for cid, total in rows}


def _overdue_by_contract(db: Session, contract_ids: list):
    today = date.today()
    data = {cid: {'oldest': None, 'days': 0, 'amount': Decimal('0')} for cid in contract_ids}
    rows = db.scalars(select(PaymentSchedule).where(PaymentSchedule.contract_id.in_(contract_ids), PaymentSchedule.deleted_at.is_(None), PaymentSchedule.due_date < today, PaymentSchedule.remaining_amount > 0, PaymentSchedule.status != 'paid').order_by(PaymentSchedule.due_date.asc()))
    for p in rows:
        days = (today - p.due_date).days
        item = data[p.contract_id]
        item['amount'] += money(p.remaining_amount)
        if item['oldest'] is None or days > item['days']:
            item['oldest'] = p.due_date
            item['days'] = days
    return data


def aging_bucket(days: int) -> str:
    if days <= 0: return 'current'
    if days <= 30: return 'overdue_1_30'
    if days <= 60: return 'overdue_31_60'
    if days <= 90: return 'overdue_61_90'
    return 'overdue_over_90'


def _serialize_contract(c: Contract, receipt_total: Decimal, overdue: dict):
    deposit = money(c.deposit_value)
    value = money(c.contract_value)
    collected = deposit + receipt_total
    remaining = max(value - collected, Decimal('0'))
    return {
        'contract_id': str(c.id), 'contract_code': c.contract_code,
        'customer_name': c.customer.full_name if c.customer else c.buyer_name,
        'customer_phone': c.customer.primary_phone if c.customer else c.buyer_phone,
        'project_name': c.project.name if getattr(c, 'project', None) else None,
        'property_name': c.property_unit.title if getattr(c, 'property_unit', None) else None,
        'sale_name': c.creator.full_name if getattr(c, 'creator', None) else None,
        'contract_status': c.status, 'contract_status_label': CONTRACT_STATUS_LABELS.get(c.status, c.status),
        'contract_value': value, 'deposit_value': deposit,
        'confirmed_receipts_amount': receipt_total, 'total_collected_amount': collected,
        'remaining_amount': remaining, 'payment_status': 'paid' if collected >= value else ('partial' if collected > 0 else 'pending'),
        'contract_date': c.signed_date or c.created_at,
        'oldest_overdue_due_date': overdue.get('oldest'), 'max_overdue_days': overdue.get('days', 0),
        'overdue_amount': overdue.get('amount', Decimal('0')), 'aging_bucket': aging_bucket(overdue.get('days', 0)),
    }


def get_receivable_report(db: Session, f: ReportFilters, user: User, paginate=True):
    require_finance_view(user)
    cond = _contract_conditions(f)
    contracts = list(db.scalars(select(Contract).options(selectinload(Contract.customer), selectinload(Contract.project), selectinload(Contract.property_unit), selectinload(Contract.creator)).where(*cond).order_by(Contract.created_at.desc())).unique())
    ids = [c.id for c in contracts]
    receipts = _receipt_sum_by_contract(db, ids)
    overdue = _overdue_by_contract(db, ids)
    items = [_serialize_contract(c, receipts.get(c.id, Decimal('0')), overdue.get(c.id, {})) for c in contracts]
    if f.payment_status:
        items = [i for i in items if i['payment_status'] == f.payment_status]
    total = len(items)
    if paginate:
        items = items[(f.page-1)*f.page_size:f.page*f.page_size]
    return {'items': items, 'total': total, 'page': f.page, 'page_size': f.page_size, 'total_pages': ceil(total / f.page_size) if total else 0}


def get_finance_summary(db: Session, f: ReportFilters, user: User):
    require_finance_view(user)
    receivables = get_receivable_report(db, f, user, paginate=False)['items']
    overdue = get_overdue_payment_report(db, f, user, paginate=False)['items']
    receipts = get_cash_collection_report(db, f, user, paginate=False)
    invoices = get_invoice_report(db, f, user, paginate=False)
    return {
        'total_contract_value': sum((money(i['contract_value']) for i in receivables), Decimal('0')),
        'total_deposit_value': sum((money(i['deposit_value']) for i in receivables), Decimal('0')),
        'total_confirmed_receipts': receipts['confirmed_total_amount'],
        'total_collected_with_deposit': sum((money(i['total_collected_amount']) for i in receivables), Decimal('0')),
        'total_remaining': sum((money(i['remaining_amount']) for i in receivables), Decimal('0')),
        'paid_contract_count': sum(1 for i in receivables if money(i['total_collected_amount']) >= money(i['contract_value'])),
        'receivable_contract_count': sum(1 for i in receivables if money(i['remaining_amount']) > 0),
        'overdue_payment_count': len(overdue),
        'total_overdue_amount': sum((money(i['remaining_amount']) for i in overdue), Decimal('0')),
        'confirmed_receipt_count': receipts['confirmed_receipt_count'],
        'issued_invoice_count': invoices['issued_invoice_count'],
        'issued_invoice_amount': invoices['issued_total_amount'],
    }


def _payment_conditions(f: ReportFilters):
    cond = [PaymentSchedule.deleted_at.is_(None)]
    if f.date_from: cond.append(PaymentSchedule.due_date >= f.date_from)
    if f.date_to: cond.append(PaymentSchedule.due_date <= f.date_to)
    if f.project_id: cond.append(PaymentSchedule.contract.has(Contract.project_id == f.project_id))
    if f.property_id: cond.append(PaymentSchedule.property_unit_id == f.property_id)
    if f.sale_id or f.assigned_user_id: cond.append(PaymentSchedule.contract.has(Contract.created_by_id == (f.sale_id or f.assigned_user_id)))
    if f.contract_status: cond.append(PaymentSchedule.contract.has(Contract.status == f.contract_status))
    if f.payment_status: cond.append(PaymentSchedule.status == f.payment_status)
    if f.customer_keyword:
        term=f'%{f.customer_keyword.strip()}%'; cond.append(PaymentSchedule.customer.has(or_(Customer.full_name.ilike(term), Customer.primary_phone.ilike(term))))
    if f.contract_keyword: cond.append(PaymentSchedule.contract.has(Contract.contract_code.ilike(f'%{f.contract_keyword.strip()}%')))
    return cond


def get_overdue_payment_report(db: Session, f: ReportFilters, user: User, paginate=True):
    require_finance_view(user); today = date.today()
    cond = _payment_conditions(f) + [PaymentSchedule.due_date < today, PaymentSchedule.remaining_amount > 0, PaymentSchedule.status != 'paid']
    rows = list(db.scalars(select(PaymentSchedule).options(selectinload(PaymentSchedule.contract).selectinload(Contract.creator), selectinload(PaymentSchedule.customer)).where(*cond).order_by(PaymentSchedule.due_date.asc())).unique())
    items = [{
        'payment_id': str(p.id), 'payment_code': p.payment_code, 'contract_id': str(p.contract_id), 'contract_code': p.contract.contract_code,
        'customer_name': p.customer.full_name if p.customer else None, 'sale_name': p.contract.creator.full_name if p.contract and p.contract.creator else None,
        'installment_name': p.title, 'installment_no': p.sequence_no, 'due_date': p.due_date, 'amount_due': money(p.expected_amount) + money(p.penalty_amount),
        'paid_amount': money(p.paid_amount), 'remaining_amount': money(p.remaining_amount), 'overdue_days': (today - p.due_date).days,
        'payment_status': p.status, 'payment_status_label': PAYMENT_STATUS_LABELS.get(p.status, p.status), 'contract_status': p.contract.status,
    } for p in rows]
    items.sort(key=lambda x: (-x['overdue_days'], x['due_date']))
    total=len(items)
    if paginate: items=items[(f.page-1)*f.page_size:f.page*f.page_size]
    return {'items': items, 'total': total, 'page': f.page, 'page_size': f.page_size, 'total_pages': ceil(total/f.page_size) if total else 0}


def _receipt_conditions(f: ReportFilters):
    cond=[PaymentReceipt.deleted_at.is_(None)]
    if f.date_from: cond.append(PaymentReceipt.payment_date >= f.date_from)
    if f.date_to: cond.append(PaymentReceipt.payment_date <= f.date_to)
    if f.status: cond.append(PaymentReceipt.status == f.status)
    if f.project_id: cond.append(PaymentReceipt.payment_schedule.has(PaymentSchedule.contract.has(Contract.project_id == f.project_id)))
    if f.property_id: cond.append(PaymentReceipt.payment_schedule.has(PaymentSchedule.property_unit_id == f.property_id))
    if f.sale_id or f.assigned_user_id: cond.append(PaymentReceipt.payment_schedule.has(PaymentSchedule.contract.has(Contract.created_by_id == (f.sale_id or f.assigned_user_id))))
    if f.contract_status: cond.append(PaymentReceipt.payment_schedule.has(PaymentSchedule.contract.has(Contract.status == f.contract_status)))
    if f.customer_keyword:
        term=f'%{f.customer_keyword.strip()}%'; cond.append(PaymentReceipt.payment_schedule.has(PaymentSchedule.customer.has(or_(Customer.full_name.ilike(term), Customer.primary_phone.ilike(term)))))
    if f.contract_keyword: cond.append(PaymentReceipt.payment_schedule.has(PaymentSchedule.contract.has(Contract.contract_code.ilike(f'%{f.contract_keyword.strip()}%'))))
    return cond


def get_cash_collection_report(db: Session, f: ReportFilters, user: User, paginate=True):
    require_finance_view(user); cond=_receipt_conditions(f)
    rows=list(db.scalars(select(PaymentReceipt).options(selectinload(PaymentReceipt.payment_schedule).selectinload(PaymentSchedule.contract), selectinload(PaymentReceipt.payment_schedule).selectinload(PaymentSchedule.customer)).where(*cond).order_by(PaymentReceipt.created_at.desc())).unique())
    confirmed_total=sum((money(r.amount) for r in rows if r.status=='confirmed'), Decimal('0'))
    items=[{'receipt_id':str(r.id),'receipt_code':r.receipt_code,'receipt_date':r.payment_date,'customer_name':r.payment_schedule.customer.full_name if r.payment_schedule and r.payment_schedule.customer else None,'contract_id':str(r.contract_id),'contract_code':r.payment_schedule.contract.contract_code if r.payment_schedule and r.payment_schedule.contract else None,'payment_id':str(r.payment_schedule_id),'payment_code':r.payment_schedule.payment_code if r.payment_schedule else None,'installment_name':r.payment_schedule.title if r.payment_schedule else None,'amount':money(r.amount),'payment_method':r.payment_method,'payment_method_label':PAYMENT_METHOD_LABELS.get(r.payment_method) if r.payment_method else None,'created_by_name':None,'status':r.status,'status_label':RECEIPT_STATUS_LABELS.get(r.status,r.status),'cancel_reason':r.cancel_reason} for r in rows]
    total=len(items)
    if paginate: items=items[(f.page-1)*f.page_size:f.page*f.page_size]
    return {'items':items,'total':total,'confirmed_total_amount':confirmed_total,'confirmed_receipt_count':sum(1 for r in rows if r.status=='confirmed'),'page':f.page,'page_size':f.page_size,'total_pages':ceil(total/f.page_size) if total else 0}


def _invoice_conditions(f: ReportFilters):
    cond=[PaymentInvoice.deleted_at.is_(None)]
    if f.date_from: cond.append(or_(PaymentInvoice.issued_date >= f.date_from, PaymentInvoice.issued_date.is_(None) & (PaymentInvoice.created_at >= _dt_start(f.date_from))))
    if f.date_to: cond.append(or_(PaymentInvoice.issued_date <= f.date_to, PaymentInvoice.issued_date.is_(None) & (PaymentInvoice.created_at <= _dt_end(f.date_to))))
    if f.status: cond.append(PaymentInvoice.status == f.status)
    if f.project_id: cond.append(PaymentInvoice.payment_schedule.has(PaymentSchedule.contract.has(Contract.project_id == f.project_id)))
    if f.property_id: cond.append(PaymentInvoice.property_unit_id == f.property_id)
    if f.sale_id or f.assigned_user_id: cond.append(PaymentInvoice.payment_schedule.has(PaymentSchedule.contract.has(Contract.created_by_id == (f.sale_id or f.assigned_user_id))))
    if f.contract_status: cond.append(PaymentInvoice.payment_schedule.has(PaymentSchedule.contract.has(Contract.status == f.contract_status)))
    if f.customer_keyword:
        term=f'%{f.customer_keyword.strip()}%'; cond.append(PaymentInvoice.payment_schedule.has(PaymentSchedule.customer.has(or_(Customer.full_name.ilike(term), Customer.primary_phone.ilike(term)))))
    if f.contract_keyword: cond.append(PaymentInvoice.payment_schedule.has(PaymentSchedule.contract.has(Contract.contract_code.ilike(f'%{f.contract_keyword.strip()}%'))))
    return cond


def get_invoice_report(db: Session, f: ReportFilters, user: User, paginate=True):
    require_finance_view(user); cond=_invoice_conditions(f)
    rows=list(db.scalars(select(PaymentInvoice).options(selectinload(PaymentInvoice.payment_schedule).selectinload(PaymentSchedule.contract), selectinload(PaymentInvoice.payment_schedule).selectinload(PaymentSchedule.customer), selectinload(PaymentInvoice.receipt)).where(*cond).order_by(PaymentInvoice.created_at.desc())).unique())
    issued_total=sum((money(i.amount) for i in rows if i.status=='issued'), Decimal('0'))
    items=[{'invoice_id':str(i.id),'invoice_code':i.invoice_code,'created_at':i.created_at,'issued_at':i.issued_at,'issued_date':i.issued_date,'customer_name':i.payment_schedule.customer.full_name if i.payment_schedule and i.payment_schedule.customer else None,'contract_id':str(i.contract_id),'contract_code':i.payment_schedule.contract.contract_code if i.payment_schedule and i.payment_schedule.contract else None,'payment_id':str(i.payment_schedule_id) if i.payment_schedule_id else None,'payment_code':i.payment_schedule.payment_code if i.payment_schedule else None,'receipt_id':str(i.receipt_id) if i.receipt_id else None,'receipt_code':i.receipt.receipt_code if i.receipt else None,'amount':money(i.amount),'status':i.status,'status_label':INVOICE_STATUS_LABELS.get(i.status,i.status),'cancel_reason':i.cancel_reason,'created_by_name':None} for i in rows]
    total=len(items)
    if paginate: items=items[(f.page-1)*f.page_size:f.page*f.page_size]
    return {'items':items,'total':total,'issued_total_amount':issued_total,'issued_invoice_count':sum(1 for i in rows if i.status=='issued'),'page':f.page,'page_size':f.page_size,'total_pages':ceil(total/f.page_size) if total else 0}


def build_csv(headers, rows):
    buf=io.StringIO(); buf.write('\ufeff'); writer=csv.writer(buf); writer.writerow(headers); writer.writerows(rows); return buf.getvalue()

# Sprint 19 — Sales Commission, Revenue Attribution & Performance Report
DEFAULT_COMMISSION_RATE_PERCENT = Decimal('1')
UNKNOWN_LEAD_SOURCE = 'Không rõ nguồn'
UNASSIGNED_SALE = 'Chưa gán sale'
UNKNOWN_PROJECT = 'Không xác định'


def normalize_commission_rate_percent(value: Decimal | int | float | None) -> Decimal:
    rate = DEFAULT_COMMISSION_RATE_PERCENT if value is None else Decimal(str(value))
    if rate < 0 or rate > 100:
        raise HTTPException(422, 'Tỷ lệ hoa hồng phải từ 0 đến 100%.')
    return rate


def _commission_ratio(rate_percent: Decimal) -> Decimal:
    return rate_percent / Decimal('100')


def require_commission_view(user: User) -> None:
    if user.is_superuser:
        return
    perms = set(get_user_permissions(user))
    if 'reports.view.commissions' not in perms and 'reports.view.all' not in perms:
        raise HTTPException(403, 'Bạn không có quyền xem báo cáo hoa hồng.')


def require_revenue_view(user: User) -> None:
    if user.is_superuser:
        return
    perms = set(get_user_permissions(user))
    if 'reports.view.revenue' not in perms and 'reports.view.all' not in perms:
        raise HTTPException(403, 'Bạn không có quyền xem báo cáo doanh thu.')


def _commission_contracts(db: Session, f: ReportFilters):
    return list(db.scalars(select(Contract).options(selectinload(Contract.customer), selectinload(Contract.project), selectinload(Contract.property_unit), selectinload(Contract.creator), selectinload(Contract.deal).selectinload(Deal.property_unit), selectinload(Contract.deal).selectinload(Deal.project), selectinload(Contract.deal).selectinload(Deal.owner)).where(*_contract_conditions(f)).order_by(Contract.created_at.desc())).unique())


def _sale_id(c: Contract):
    return c.created_by_id or (c.deal.owner_id if c.deal else None)


def _sale_name(c: Contract):
    return (c.creator.full_name if getattr(c, 'creator', None) else None) or (c.deal.owner.full_name if getattr(c, 'deal', None) and c.deal.owner else None) or UNASSIGNED_SALE


def _lead_source(c: Contract):
    return (c.customer.source if getattr(c, 'customer', None) else None) or UNKNOWN_LEAD_SOURCE


def _project_id(c: Contract):
    return c.project_id or (c.deal.project_id if c.deal else None)


def _project_name(c: Contract):
    return (c.project.name if getattr(c, 'project', None) else None) or (c.deal.project.name if getattr(c, 'deal', None) and c.deal.project else None) or (c.property_unit.title if getattr(c, 'property_unit', None) else None) or (c.deal.property_unit.title if getattr(c, 'deal', None) and c.deal.property_unit else None) or UNKNOWN_PROJECT


def _commission_row(c: Contract, receipt_total: Decimal, rate_percent: Decimal):
    ratio = _commission_ratio(rate_percent)
    deposit = money(c.deposit_value); value = money(c.contract_value); collected = deposit + receipt_total
    remaining = max(value - collected, Decimal('0'))
    estimated = value * ratio; collected_commission = collected * ratio
    is_cancelled = c.status == 'cancelled'
    eligible = (not is_cancelled) and (c.status == 'completed' or collected >= value)
    status = 'cancelled' if is_cancelled else ('eligible' if eligible else 'not_eligible')
    return {'contract_id': str(c.id), 'contract_code': c.contract_code, 'customer_name': c.customer.full_name if c.customer else c.buyer_name, 'customer_phone': c.customer.primary_phone if c.customer else c.buyer_phone, 'sale_id': str(_sale_id(c)) if _sale_id(c) else None, 'sale_name': _sale_name(c), 'lead_source': _lead_source(c), 'project_id': str(_project_id(c)) if _project_id(c) else None, 'project_name': _project_name(c), 'contract_status': c.status, 'payment_status': 'paid' if collected >= value else ('partial' if collected > 0 else 'pending'), 'contract_value': value, 'deposit_value': deposit, 'confirmed_receipts_amount': receipt_total, 'total_collected_with_deposit': collected, 'remaining_amount': remaining, 'commission_rate_percent': rate_percent, 'estimated_commission': estimated, 'collected_commission': collected_commission, 'eligible_commission': estimated if eligible else Decimal('0'), 'commission_status': status}


def get_commission_report(db: Session, f: ReportFilters, user: User, commission_rate_percent=None, paginate=True):
    require_commission_view(user); rate = normalize_commission_rate_percent(commission_rate_percent)
    contracts = _commission_contracts(db, f); receipts = _receipt_sum_by_contract(db, [c.id for c in contracts])
    items = [_commission_row(c, receipts.get(c.id, Decimal('0')), rate) for c in contracts]
    if f.payment_status: items = [i for i in items if i['payment_status'] == f.payment_status]
    total = len(items)
    if paginate: items = items[(f.page-1)*f.page_size:f.page*f.page_size]
    return {'items': items, 'total': total, 'page': f.page, 'page_size': f.page_size, 'total_pages': ceil(total/f.page_size) if total else 0}


def get_commission_summary(db: Session, f: ReportFilters, user: User, commission_rate_percent=None):
    items = get_commission_report(db, f, user, commission_rate_percent, False)['items']
    return {'total_contract_count': len(items), 'eligible_contract_count': sum(1 for i in items if i['commission_status']=='eligible'), 'not_eligible_contract_count': sum(1 for i in items if i['commission_status']=='not_eligible'), 'cancelled_contract_count': sum(1 for i in items if i['commission_status']=='cancelled'), 'total_contract_value': sum((money(i['contract_value']) for i in items), Decimal('0')), 'total_collected_with_deposit': sum((money(i['total_collected_with_deposit']) for i in items), Decimal('0')), 'total_remaining_amount': sum((money(i['remaining_amount']) for i in items), Decimal('0')), 'estimated_commission': sum((money(i['estimated_commission']) for i in items), Decimal('0')), 'collected_commission': sum((money(i['collected_commission']) for i in items), Decimal('0')), 'eligible_commission': sum((money(i['eligible_commission']) for i in items), Decimal('0')), 'commission_rate_percent': normalize_commission_rate_percent(commission_rate_percent)}


def _group_revenue(items, key_fn, id_key, name_key, include_commission=True):
    groups = {}
    for i in items:
        gid, name = key_fn(i); g = groups.setdefault((gid, name), {'total_contract_count':0,'completed_contract_count':0,'cancelled_contract_count':0,'total_contract_value':Decimal('0'),'total_deposit_value':Decimal('0'),'confirmed_receipts_amount':Decimal('0'),'total_collected_with_deposit':Decimal('0'),'total_remaining_amount':Decimal('0'),'estimated_commission':Decimal('0'),'collected_commission':Decimal('0'),'eligible_commission':Decimal('0')})
        g['total_contract_count'] += 1; g['completed_contract_count'] += 1 if i['contract_status']=='completed' else 0; g['cancelled_contract_count'] += 1 if i['contract_status']=='cancelled' else 0
        for k in ['total_contract_value','total_deposit_value','confirmed_receipts_amount','total_collected_with_deposit','total_remaining_amount','estimated_commission','collected_commission','eligible_commission']:
            source = {'total_contract_value':'contract_value','total_deposit_value':'deposit_value'}.get(k,k); g[k] += money(i[source])
    rows=[]
    for (gid,name), g in groups.items():
        count=g['total_contract_count']; row={id_key: gid, name_key: name, **g, 'average_contract_value': g['total_contract_value']/count if count else Decimal('0'), 'completion_rate': g['completed_contract_count']/count if count else 0}
        if not include_commission:
            row.pop('estimated_commission', None); row.pop('collected_commission', None); row.pop('eligible_commission', None); row.pop('total_deposit_value', None); row.pop('confirmed_receipts_amount', None)
        rows.append(row)
    rows.sort(key=lambda r: r['total_contract_value'], reverse=True)
    return rows


def _revenue_items(db, f, user, rate):
    require_revenue_view(user); contracts=_commission_contracts(db,f); receipts=_receipt_sum_by_contract(db,[c.id for c in contracts]); return [_commission_row(c, receipts.get(c.id, Decimal('0')), rate) for c in contracts]


def get_revenue_by_sale(db: Session, f: ReportFilters, user: User, commission_rate_percent=None):
    rate=normalize_commission_rate_percent(commission_rate_percent); rows=_group_revenue(_revenue_items(db,f,user,rate), lambda i:(i['sale_id'], i['sale_name']), 'sale_id', 'sale_name', True); return {'items':rows,'total':len(rows)}

def get_revenue_by_source(db: Session, f: ReportFilters, user: User, commission_rate_percent=None):
    rate=normalize_commission_rate_percent(commission_rate_percent); rows=_group_revenue(_revenue_items(db,f,user,rate), lambda i:(i['lead_source'], i['lead_source']), 'lead_source', 'lead_source', False); return {'items':rows,'total':len(rows)}

def get_revenue_by_project(db: Session, f: ReportFilters, user: User, commission_rate_percent=None):
    rate=normalize_commission_rate_percent(commission_rate_percent); rows=_group_revenue(_revenue_items(db,f,user,rate), lambda i:(i['project_id'], i['project_name']), 'project_id', 'project_name', False); return {'items':rows,'total':len(rows)}
