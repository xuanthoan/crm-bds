from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models.lead_task import LeadTask
from app.models.task import Task, TaskAssignee
from app.models.lead_appointment import LeadAppointment
from app.models.user import User
from app.models.customer import Customer
from app.models.booking import Booking
from app.models.deal import Deal
from app.models.contract import Contract
from app.models.project import Project
from app.models.sales_commission import SalesCommission
from app.models.company_commission import CompanyCommissionReceivable
from app.models.payment_receipt import PaymentReceipt
from app.models.payment_schedule import PaymentSchedule
from app.models.payment_invoice import PaymentInvoice
from app.models.commission_payment_voucher import SalesCommissionPaymentVoucher
from app.models.user_organization_membership import UserOrganizationMembership
from app.models.team import Team
from app.models.department import Department
from app.services.lead_task_service import _accessible_ids, now, permissions, user_dict

BOSS_DASHBOARD_PERMISSION = "dashboard.boss.view"
DEFAULT_DASHBOARD_PRESET = "last_30_days"
VALID_CONTRACT_REVENUE_STATUSES = {"signed", "effective", "active", "completed", "won"}
DEPOSIT_BOOKING_STATUSES = {"deposit", "deposited", "contracted", "completed"}
SALES_COMMISSION_INCLUDED_STATUSES = {"eligible", "approved", "paid"}
COMPANY_COMMISSION_INCLUDED_STATUSES = {"pending", "approved", "partially_received", "received"}


def _bounds():
    start=datetime.combine(date.today(),time.min,tzinfo=timezone.utc); return start,start+timedelta(days=1)
def _count(db,model,*conditions):return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0
def _summary(db,user_id):
    start,end=_bounds(); active=LeadTask.status.in_({"pending","in_progress"}); live_task=LeadTask.deleted_at.is_(None); live_appt=LeadAppointment.deleted_at.is_(None)
    return {"tasks_today":_count(db,LeadTask,live_task,LeadTask.assigned_to_id==user_id,active,LeadTask.due_at>=start,LeadTask.due_at<end),"tasks_overdue":_count(db,LeadTask,live_task,LeadTask.assigned_to_id==user_id,active,LeadTask.due_at<now()),"appointments_today":_count(db,LeadAppointment,live_appt,LeadAppointment.assigned_to_id==user_id,LeadAppointment.start_at>=start,LeadAppointment.start_at<end),"appointments_upcoming":_count(db,LeadAppointment,live_appt,LeadAppointment.status.in_({"scheduled","rescheduled"}),LeadAppointment.start_at>=now(),LeadAppointment.start_at<now()+timedelta(days=7)),"leads_need_follow_up":_count(db,Lead,Lead.deleted_at.is_(None),Lead.owner_id==user_id,Lead.next_follow_up_at<now()),"completed_tasks_today":_count(db,LeadTask,live_task,LeadTask.assigned_to_id==user_id,LeadTask.status=="completed",LeadTask.completed_at>=start,LeadTask.completed_at<end)}
def get_my_work_summary(db,user):return _summary(db,user.id)
def get_team_work_summary(db,user):
    ps=permissions(user)
    scope="all" if user.is_superuser or "dashboard.view.all" in ps else "team" if "dashboard.view.team" in ps else None
    if not scope: from fastapi import HTTPException; raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    ids=_accessible_ids(db,user,scope); users=list(db.scalars(select(User).where(User.id.in_(ids),User.status=="active").order_by(User.full_name)))
    rows=[]
    for member in users:
        summary=_summary(db,member.id); rows.append({"user":user_dict(member),"leads_owned":_count(db,Lead,Lead.deleted_at.is_(None),Lead.owner_id==member.id),**summary})
    return {"team_tasks_today":sum(r["tasks_today"] for r in rows),"team_tasks_overdue":sum(r["tasks_overdue"] for r in rows),"team_appointments_today":sum(r["appointments_today"] for r in rows),"team_leads_need_follow_up":sum(r["leads_need_follow_up"] for r in rows),"per_user_summary":rows}


def _as_utc_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def resolve_dashboard_date_range(preset: str | None = None, from_date: date | str | None = None, to_date: date | str | None = None, today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    preset = preset or DEFAULT_DASHBOARD_PRESET
    def parse(v):
        if isinstance(v, date): return v
        return date.fromisoformat(v) if v else None
    if preset == "today": start_day = end_day = today; label = "Hôm nay"
    elif preset == "last_7_days": start_day = today - timedelta(days=6); end_day = today; label = "7 ngày qua"
    elif preset == "last_30_days": start_day = today - timedelta(days=29); end_day = today; label = "30 ngày qua"
    elif preset == "this_month": start_day = today.replace(day=1); end_day = today; label = "Tháng này"
    elif preset == "last_month":
        first_this = today.replace(day=1); end_day = first_this - timedelta(days=1); start_day = end_day.replace(day=1); label = "Tháng trước"
    elif preset == "custom":
        start_day, end_day = parse(from_date), parse(to_date)
        if not start_day or not end_day: raise ValueError("preset=custom requires from_date and to_date")
        if start_day > end_day: raise ValueError("from_date must be before or equal to to_date")
        label = f"{start_day.isoformat()} → {end_day.isoformat()}"
    else: raise ValueError("Unsupported dashboard date range preset")
    start_dt = _as_utc_day(start_day); end_dt = _as_utc_day(end_day + timedelta(days=1))
    return {"preset": preset, "from_date": start_day.isoformat(), "to_date": end_day.isoformat(), "start_datetime": start_dt.isoformat(), "end_datetime": end_dt.isoformat(), "label": label, "_start": start_dt, "_end": end_dt}


def _money(value): return float(value or 0)
def _rate(a, b): return round(a / b, 4) if b else None

def _valid_contract_date(c=Contract): return func.coalesce(c.effective_date, c.signed_date, c.created_at)
def _valid_contracts(start, end):
    return [Contract.deleted_at.is_(None), Contract.status.in_(VALID_CONTRACT_REVENUE_STATUSES), _valid_contract_date() >= start, _valid_contract_date() < end]

def _dates(start, end):
    d = start.date(); last = (end - timedelta(microseconds=1)).date(); out=[]
    while d <= last: out.append(d.isoformat()); d += timedelta(days=1)
    return out

def _primary_membership_subquery():
    return select(UserOrganizationMembership.user_id, UserOrganizationMembership.team_id, UserOrganizationMembership.department_id).where(UserOrganizationMembership.is_primary.is_(True)).subquery()

def _contract_revenue_rows(db, start, end):
    membership = _primary_membership_subquery()
    stmt = select(Contract, Deal, User, membership.c.team_id, membership.c.department_id).join(Deal, Contract.deal_id == Deal.id).join(User, Deal.owner_id == User.id).outerjoin(membership, membership.c.user_id == Deal.owner_id).where(*_valid_contracts(start, end), Deal.deleted_at.is_(None))
    return db.execute(stmt).all()

def _leaderboards(db, start, end, limit=10):
    sales, teams, projects = {}, {}, {}
    for contract, deal, sale, team_id, department_id in _contract_revenue_rows(db, start, end):
        revenue = _money(contract.contract_value)
        sale_bucket = sales.setdefault(str(sale.id), {"sale_id": str(sale.id), "sale_name": sale.full_name, "team_name": "Chưa xác định", "department_name": "Chưa xác định", "revenue": 0, "contract_count": 0})
        sale_bucket["revenue"] += revenue; sale_bucket["contract_count"] += 1
        if team_id:
            team = db.get(Team, team_id); dept = db.get(Department, department_id) if department_id else None
            if team: sale_bucket["team_name"] = team.name
            if dept: sale_bucket["department_name"] = dept.name
            team_bucket = teams.setdefault(str(team_id), {"team_id": str(team_id), "team_name": team.name if team else "Chưa xác định", "department_name": dept.name if dept else "Chưa xác định", "revenue": 0, "contract_count": 0})
            team_bucket["revenue"] += revenue; team_bucket["contract_count"] += 1
        project_id = contract.project_id or deal.project_id
        pkey = str(project_id) if project_id else "unknown"; project = db.get(Project, project_id) if project_id else None
        pb = projects.setdefault(pkey, {"project_id": str(project_id) if project_id else None, "project_name": project.name if project else "Chưa có dự án", "revenue": 0, "contract_count": 0})
        pb["revenue"] += revenue; pb["contract_count"] += 1
    sort = lambda rows: sorted(rows.values(), key=lambda r: (r["revenue"], r["contract_count"]), reverse=True)[:limit]
    return sort(sales), sort(teams), sort(projects)

def get_boss_dashboard(db: Session, preset: str | None = None, from_date: date | str | None = None, to_date: date | str | None = None) -> dict:
    r = resolve_dashboard_date_range(preset, from_date, to_date); start, end = r["_start"], r["_end"]
    lead_new = _count(db, Lead, Lead.deleted_at.is_(None), Lead.created_at >= start, Lead.created_at < end)
    lead_converted = _count(db, Lead, Lead.deleted_at.is_(None), Lead.converted_at >= start, Lead.converted_at < end)
    customers = _count(db, Customer, Customer.deleted_at.is_(None), Customer.created_at >= start, Customer.created_at < end)
    bookings = _count(db, Booking, Booking.deleted_at.is_(None), Booking.created_at >= start, Booking.created_at < end)
    deposits = _count(db, Booking, Booking.deleted_at.is_(None), Booking.status.in_(DEPOSIT_BOOKING_STATUSES), func.coalesce(Booking.deposit_date, Booking.created_at) >= start, func.coalesce(Booking.deposit_date, Booking.created_at) < end)
    deals = _count(db, Deal, Deal.deleted_at.is_(None), Deal.created_at >= start, Deal.created_at < end)
    contract_count = _count(db, Contract, *_valid_contracts(start, end))
    revenue = _money(db.scalar(select(func.coalesce(func.sum(Contract.contract_value), 0)).where(*_valid_contracts(start, end))))
    sales_commission_approved = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.approved_commission), 0)).where(SalesCommission.status.in_(SALES_COMMISSION_INCLUDED_STATUSES), SalesCommission.created_at >= start, SalesCommission.created_at < end)))
    sales_commission_paid = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.paid_amount), 0)).where(SalesCommission.status.in_(SALES_COMMISSION_INCLUDED_STATUSES), SalesCommission.created_at >= start, SalesCommission.created_at < end)))
    sales_commission = sales_commission_approved
    company_commission_receivable = _money(db.scalar(select(func.coalesce(func.sum(CompanyCommissionReceivable.confirmed_receivable_amount), 0)).where(CompanyCommissionReceivable.status.in_(COMPANY_COMMISSION_INCLUDED_STATUSES), CompanyCommissionReceivable.created_at >= start, CompanyCommissionReceivable.created_at < end)))
    company_commission_received = _money(db.scalar(select(func.coalesce(func.sum(CompanyCommissionReceivable.received_amount), 0)).where(CompanyCommissionReceivable.status.in_(COMPANY_COMMISSION_INCLUDED_STATUSES), CompanyCommissionReceivable.created_at >= start, CompanyCommissionReceivable.created_at < end)))
    customer_paid = _money(db.scalar(select(func.coalesce(func.sum(PaymentReceipt.amount), 0)).where(PaymentReceipt.deleted_at.is_(None), PaymentReceipt.status.in_({"confirmed", "paid"}), func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) >= start, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) < end)))
    customer_outstanding = max(revenue - customer_paid, 0)
    avg_contract_value = revenue / contract_count if contract_count else None
    company_commission_outstanding = max(company_commission_receivable - company_commission_received, 0)
    sales_commission_outstanding = max(sales_commission_approved - sales_commission_paid, 0)
    ads_cost = 0.0; roi_ratio = revenue / ads_cost if ads_cost else None; roi_profit_ratio = (revenue - ads_cost) / ads_cost if ads_cost else None
    gross_profit_received = company_commission_received - sales_commission_paid - ads_cost
    gross_profit_receivable = company_commission_receivable - sales_commission_approved - ads_cost
    company_collection_rate = company_commission_received / company_commission_receivable if company_commission_receivable else None
    sales_payment_rate = sales_commission_paid / sales_commission_approved if sales_commission_approved else None
    duplicate_count = _count(db, LeadActivity, LeadActivity.activity_type == "duplicate_reengagement", LeadActivity.created_at >= start, LeadActivity.created_at < end)
    day_map = {d: {"date": d, "count": 0} for d in _dates(start, end)}; revenue_day = {d: {"date": d, "amount": 0} for d in _dates(start, end)}; contracts_day = {d: {"date": d, "count": 0} for d in _dates(start, end)}; bookings_day = {d: {"date": d, "count": 0} for d in _dates(start, end)}
    for day, count in db.execute(select(func.date(Lead.created_at), func.count()).where(Lead.deleted_at.is_(None), Lead.created_at >= start, Lead.created_at < end).group_by(func.date(Lead.created_at))): day_map[str(day)]["count"] = count
    for day, amount, count in db.execute(select(func.date(_valid_contract_date()), func.coalesce(func.sum(Contract.contract_value), 0), func.count()).where(*_valid_contracts(start, end)).group_by(func.date(_valid_contract_date()))): revenue_day[str(day)]["amount"] = _money(amount); contracts_day[str(day)]["count"] = count
    for day, count in db.execute(select(func.date(Booking.created_at), func.count()).where(Booking.deleted_at.is_(None), Booking.created_at >= start, Booking.created_at < end).group_by(func.date(Booking.created_at))): bookings_day[str(day)]["count"] = count
    lead_by_source = [
        {"source": s or "Chưa xác định", "count": c}
        for s, c in db.execute(
            select(Lead.source, func.count().label("lead_count"))
            .where(Lead.deleted_at.is_(None), Lead.created_at >= start, Lead.created_at < end)
            .group_by(Lead.source)
            .order_by(func.count().desc())
            .limit(10)
        )
    ]
    sales7, teams7, _ = _leaderboards(db, datetime.now(timezone.utc)-timedelta(days=7), datetime.now(timezone.utc)+timedelta(days=1))
    sales30, teams30, _ = _leaderboards(db, datetime.now(timezone.utc)-timedelta(days=30), datetime.now(timezone.utc)+timedelta(days=1))
    sales_range, teams_range, top_projects = _leaderboards(db, start, end)
    summary = {"lead_new_count": lead_new, "duplicate_reengagement_count": duplicate_count, "lead_converted_to_customer_count": lead_converted, "booking_count": bookings, "deposit_count": deposits, "deal_count": deals, "contract_signed_count": contract_count, "revenue_total": revenue, "customer_paid_total": customer_paid, "customer_outstanding_total": customer_outstanding, "avg_contract_value": avg_contract_value, "company_commission_total": company_commission_receivable, "company_commission_receivable_total": company_commission_receivable, "company_commission_received_total": company_commission_received, "company_commission_outstanding_total": company_commission_outstanding, "sales_commission_total": sales_commission, "sales_commission_approved_total": sales_commission_approved, "sales_commission_paid_total": sales_commission_paid, "sales_commission_outstanding_total": sales_commission_outstanding, "ads_cost_total": ads_cost, "roi_ratio": roi_ratio, "roi_profit_ratio": roi_profit_ratio, "gross_profit_received_estimate": gross_profit_received, "gross_profit_receivable_estimate": gross_profit_receivable, "company_commission_collection_rate": company_collection_rate, "sales_commission_payment_rate": sales_payment_rate}
    funnel = {"leads": lead_new, "customers": customers, "bookings": bookings, "deposits": deposits, "deals": deals, "contracts": contract_count, "lead_to_customer_rate": _rate(customers, lead_new), "lead_to_booking_rate": _rate(bookings, lead_new), "booking_to_contract_rate": _rate(contract_count, bookings), "deal_to_contract_rate": _rate(contract_count, deals)}
    range_public = {k:v for k,v in r.items() if not k.startswith("_")}
    return {"range": range_public, "summary": summary, "funnel": funnel, "time_series": {"leads_by_day": list(day_map.values()), "revenue_by_day": list(revenue_day.values()), "contracts_by_day": list(contracts_day.values()), "bookings_by_day": list(bookings_day.values())}, "breakdowns": {"lead_by_source": lead_by_source, "lead_by_project": [], "revenue_by_project": top_projects, "booking_by_project": [], "contract_by_project": []}, "rankings": {"top_sales_7_days": sales7, "top_sales_30_days": sales30, "top_teams_7_days": teams7, "top_teams_30_days": teams30, "top_projects": top_projects, "top_sources": [{"source": row["source"], "lead_count": row["count"], "booking_count": 0, "contract_count": 0, "revenue": 0, "ads_cost": 0, "roi": None} for row in lead_by_source], "top_sales_in_range": sales_range, "top_teams_in_range": teams_range}}


SALE_DASHBOARD_PERMISSION = "dashboard.sale.view"
FINANCE_DASHBOARD_PERMISSION = "dashboard.finance.view"

def get_finance_dashboard(db: Session, preset: str | None = None, from_date: date | str | None = None, to_date: date | str | None = None) -> dict:
    """Financial overview; intentionally uses no salesperson ownership scope."""
    r = resolve_dashboard_date_range(preset, from_date, to_date); start, end = r["_start"], r["_end"]
    today = datetime.now(timezone.utc).date()
    valid = [Contract.deleted_at.is_(None), Contract.status.in_({"signed", "active", "completed"})]
    ranged_valid = [*valid, _valid_contract_date() >= start, _valid_contract_date() < end]
    receipt_live = [PaymentReceipt.deleted_at.is_(None), PaymentReceipt.status.in_({"confirmed", "paid"})]
    revenue = _money(db.scalar(select(func.coalesce(func.sum(Contract.contract_value), 0)).where(*ranged_valid)))
    collected = _money(db.scalar(select(func.coalesce(func.sum(PaymentReceipt.amount), 0)).where(*receipt_live, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) >= start, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) < end)))
    schedule_live = [PaymentSchedule.deleted_at.is_(None), PaymentSchedule.status.notin_({"paid", "completed", "cancelled"}), PaymentSchedule.remaining_amount > 0]
    outstanding = _money(db.scalar(select(func.coalesce(func.sum(PaymentSchedule.remaining_amount), 0)).join(Contract, PaymentSchedule.contract_id == Contract.id).where(*schedule_live, *valid)))
    due = [*schedule_live, PaymentSchedule.due_date >= start.date(), PaymentSchedule.due_date < end.date()]
    overdue = [*schedule_live, PaymentSchedule.due_date < today]
    pending_receipt = [PaymentReceipt.deleted_at.is_(None), PaymentReceipt.status.in_({"draft", "pending", "unconfirmed"})]
    draft_invoice = [PaymentInvoice.deleted_at.is_(None), PaymentInvoice.status == "draft"]
    issued_invoice = [PaymentInvoice.deleted_at.is_(None), PaymentInvoice.status.in_({"issued", "confirmed"}), func.coalesce(PaymentInvoice.issued_at, PaymentInvoice.created_at) >= start, func.coalesce(PaymentInvoice.issued_at, PaymentInvoice.created_at) < end]
    commissions = [SalesCommission.status.notin_({"cancelled", "rejected"})]
    approved = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.approved_commission), 0)).where(*commissions, SalesCommission.status.in_({"approved", "paid"}), func.coalesce(SalesCommission.approved_at, SalesCommission.created_at) >= start, func.coalesce(SalesCommission.approved_at, SalesCommission.created_at) < end)))
    paid = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.paid_amount), 0)).where(*commissions, SalesCommission.status == "paid", func.coalesce(SalesCommission.paid_at, SalesCommission.created_at) >= start, func.coalesce(SalesCommission.paid_at, SalesCommission.created_at) < end)))
    def n(model, *conds): return _count(db, model, *conds)
    summary = {"contract_revenue": revenue, "collected_amount": collected, "outstanding_amount": outstanding, "collection_rate": _rate(collected, revenue), "due_schedule_count": n(PaymentSchedule, *due), "overdue_schedule_count": n(PaymentSchedule, *overdue), "overdue_amount": _money(db.scalar(select(func.coalesce(func.sum(PaymentSchedule.remaining_amount), 0)).where(*overdue))), "pending_receipt_count": n(PaymentReceipt, *pending_receipt), "confirmed_receipt_count": n(PaymentReceipt, *receipt_live, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) >= start, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) < end), "draft_invoice_count": n(PaymentInvoice, *draft_invoice), "issued_invoice_count": n(PaymentInvoice, *issued_invoice), "commission_approved": approved, "commission_paid": paid, "commission_outstanding": max(approved - paid, 0), "pending_commission_voucher_count": n(SalesCommissionPaymentVoucher, SalesCommissionPaymentVoucher.status.in_({"draft", "pending"}))}
    days = _dates(start, end); revenue_by_day = {d: {"date": d, "amount": 0} for d in days}; collected_by_day = {d: {"date": d, "amount": 0} for d in days}
    for d, amount in db.execute(select(func.date(_valid_contract_date()), func.sum(Contract.contract_value)).where(*ranged_valid).group_by(func.date(_valid_contract_date()))): revenue_by_day[str(d)]["amount"] = _money(amount)
    for d, amount in db.execute(select(func.date(func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at)), func.sum(PaymentReceipt.amount)).where(*receipt_live, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) >= start, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) < end).group_by(func.date(func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at)))): collected_by_day[str(d)]["amount"] = _money(amount)
    def schedule_row(s):
        c, customer = db.get(Contract, s.contract_id), db.get(Customer, s.customer_id)
        return {"id": str(s.id), "payment_code": s.payment_code, "contract_code": c.contract_code if c else "—", "customer_name": customer.full_name if customer else "—", "due_date": s.due_date.isoformat(), "expected_amount": _money(s.expected_amount), "paid_amount": _money(s.paid_amount), "remaining_amount": _money(s.remaining_amount), "status": s.status}
    overdue_rows = [schedule_row(s) for s in db.scalars(select(PaymentSchedule).where(*overdue).order_by(PaymentSchedule.due_date).limit(10))]
    pending_rows = []
    for x in db.scalars(select(PaymentReceipt).where(*pending_receipt).order_by(PaymentReceipt.created_at.desc()).limit(10)):
        c, customer, creator = db.get(Contract, x.contract_id), db.get(Customer, x.customer_id), db.get(User, x.created_by_id)
        pending_rows.append({"id": str(x.id), "receipt_code": x.receipt_code, "contract_code": c.contract_code if c else "—", "customer_name": customer.full_name if customer else "—", "payment_date": x.payment_date.isoformat() if x.payment_date else None, "amount": _money(x.amount), "creator_name": creator.full_name if creator else "—", "status": x.status})
    outstanding_rows = []
    for c in db.scalars(select(Contract).where(*valid).order_by(Contract.contract_value.desc()).limit(10)):
        paid_total = _money(db.scalar(select(func.coalesce(func.sum(PaymentSchedule.paid_amount), 0)).where(PaymentSchedule.contract_id == c.id, PaymentSchedule.deleted_at.is_(None))))
        outstanding_rows.append({"id": str(c.id), "contract_code": c.contract_code, "customer_name": (db.get(Customer, c.customer_id).full_name if db.get(Customer, c.customer_id) else "—"), "contract_value": _money(c.contract_value), "paid_amount": paid_total, "remaining_amount": max(_money(c.contract_value) - paid_total, 0), "status": c.status})
    debt_status = [{"status": "overdue", "count": summary["overdue_schedule_count"]}, {"status": "due", "count": summary["due_schedule_count"]}, {"status": "paid", "count": n(PaymentSchedule, PaymentSchedule.deleted_at.is_(None), PaymentSchedule.status.in_({"paid", "completed"}))}, {"status": "partially_paid", "count": n(PaymentSchedule, PaymentSchedule.deleted_at.is_(None), PaymentSchedule.status == "partially_paid")}]
    commission_status = [{"status": status, "count": n(SalesCommission, SalesCommission.status == status)} for status in ("pending", "approved", "paid", "rejected")]
    public_range = {k: v for k, v in r.items() if not k.startswith("_")}
    return {"range": public_range, "summary": summary, "time_series": {"revenue_by_day": list(revenue_by_day.values()), "collected_by_day": list(collected_by_day.values())}, "breakdowns": {"receivables_by_status": debt_status, "commissions_by_status": commission_status}, "alerts": [{"key": "overdue", "label": "Thanh toán quá hạn", "count": summary["overdue_schedule_count"]}, {"key": "pending_receipts", "label": "Phiếu thu chờ xác nhận", "count": summary["pending_receipt_count"]}, {"key": "draft_invoices", "label": "Hóa đơn nháp chưa phát hành", "count": summary["draft_invoice_count"]}, {"key": "commission_due", "label": "Hoa hồng đã duyệt chưa chi", "count": n(SalesCommission, SalesCommission.status == "approved")}], "tables": {"overdue_payments": overdue_rows, "pending_receipts": pending_rows, "outstanding_contracts": outstanding_rows}}

def resolve_sale_dashboard_scope(current_user: User) -> dict:
    return {"user_ids": {current_user.id}, "scope_type": "mine", "member_count": 1, "can_view_all": False}

def get_sale_dashboard(db: Session, user: User, preset: str | None = None, start_date: date | str | None = None, end_date: date | str | None = None) -> dict:
    r = resolve_dashboard_date_range(preset or "last_7_days", start_date, end_date)
    start, end = r["_start"], r["_end"]; today_start, today_end = _bounds(); stamp = now(); stale_before = stamp - timedelta(days=STALE_LEAD_DAYS)
    uid = user.id; ids = {uid}
    lead_base = [Lead.deleted_at.is_(None), getattr(Lead, "owner_id") == uid]
    lead_new = _count(db, Lead, *lead_base, Lead.created_at >= start, Lead.created_at < end, Lead.duplicate_detected.is_(False), Lead.duplicate_of_customer_id.is_(None))
    lead_active = _count(db, Lead, *lead_base, Lead.status.notin_(CLOSED_LEAD_STATUSES))
    lead_care_today = _count(db, Lead, *lead_base, Lead.next_follow_up_at >= today_start, Lead.next_follow_up_at < today_end, Lead.status.notin_(CLOSED_LEAD_STATUSES))
    lead_overdue = _count(db, Lead, *lead_base, Lead.next_follow_up_at.is_not(None), Lead.next_follow_up_at < stamp, Lead.status.notin_(CLOSED_LEAD_STATUSES))
    lead_without_activity = db.scalar(select(func.count()).select_from(Lead).where(*lead_base, ~Lead.activities.any())) or 0
    lead_hot = _count(db, Lead, *lead_base, Lead.priority == "hot")
    stale = _count(db, Lead, *lead_base, Lead.status.notin_(CLOSED_LEAD_STATUSES), func.coalesce(Lead.last_contact_at, Lead.created_at) < stale_before)
    accessible_customer_ids = select(Lead.customer_id).where(Lead.deleted_at.is_(None), Lead.customer_id.is_not(None), Lead.owner_id == uid)
    customer_scope = [Customer.deleted_at.is_(None), (Customer.owner_id == uid) | Customer.id.in_(accessible_customer_ids)]
    customers = _count(db, Customer, *customer_scope)
    customer_stale = _count(db, Customer, *customer_scope, func.coalesce(Customer.last_contact_at, Customer.created_at) < stale_before) if hasattr(Customer, 'last_contact_at') else 0
    funnel_customer_converted = _count(db, Lead, *lead_base, Lead.created_at >= start, Lead.created_at < end, Lead.duplicate_detected.is_(False), Lead.duplicate_of_customer_id.is_(None), Lead.converted_customer_id.is_not(None), Lead.status == "converted")
    active_task = Task.status.in_({"open", "in_progress"})
    task_owner = (Task.assigned_user_id == uid) | Task.task_assignees.any(TaskAssignee.user_id == uid)
    task_today = _count(db, Task, Task.deleted_at.is_(None), task_owner, active_task, Task.due_at >= today_start, Task.due_at < today_end)
    task_overdue = _count(db, Task, Task.deleted_at.is_(None), task_owner, active_task, Task.due_at < today_start)
    appt_today = _count(db, LeadAppointment, LeadAppointment.deleted_at.is_(None), LeadAppointment.assigned_to_id == uid, LeadAppointment.start_at >= today_start, LeadAppointment.start_at < today_end)
    appt_overdue = _count(db, LeadAppointment, LeadAppointment.deleted_at.is_(None), LeadAppointment.assigned_to_id == uid, LeadAppointment.status.in_({"scheduled", "rescheduled"}), LeadAppointment.start_at < stamp)
    bookings = _count(db, Booking, Booking.deleted_at.is_(None), Booking.assigned_user_id == uid, Booking.created_at >= start, Booking.created_at < end)
    deposits = _count(db, Booking, Booking.deleted_at.is_(None), Booking.assigned_user_id == uid, Booking.status.in_(DEPOSIT_BOOKING_STATUSES), func.coalesce(Booking.deposit_date, Booking.created_at) >= start, func.coalesce(Booking.deposit_date, Booking.created_at) < end)
    deals = _count(db, Deal, Deal.deleted_at.is_(None), Deal.owner_id == uid, Deal.created_at >= start, Deal.created_at < end)
    booking_event_in_range = or_(and_(Booking.created_at >= start, Booking.created_at < end), and_(Booking.booking_date >= start, Booking.booking_date < end), and_(Booking.deposit_date >= start, Booking.deposit_date < end), Booking.deals.any(and_(Deal.deleted_at.is_(None), Deal.owner_id == uid, Deal.created_at >= start, Deal.created_at < end)), Booking.contracts.any(and_(Contract.deleted_at.is_(None), Contract.status.in_(VALID_CONTRACT_REVENUE_STATUSES), _valid_contract_date(Contract) >= start, _valid_contract_date(Contract) < end, Contract.deal.has(Deal.owner_id == uid))))
    funnel_booking_scope = [Booking.deleted_at.is_(None), Booking.assigned_user_id == uid, booking_event_in_range]
    funnel_bookings = db.scalar(select(func.count(func.distinct(Booking.id))).where(*funnel_booking_scope)) or 0
    funnel_deposits = db.scalar(select(func.count(func.distinct(Booking.id))).where(*funnel_booking_scope, or_(Booking.status.in_(DEPOSIT_BOOKING_STATUSES), Booking.deposit_amount > 0, Booking.deposit_date.is_not(None), Booking.deals.any(Deal.deposit_amount > 0), Booking.contracts.any(Contract.deposit_value > 0)))) or 0
    funnel_deal_scope = [Deal.deleted_at.is_(None), Deal.owner_id == uid, Deal.booking_id.is_not(None), Deal.booking.has(and_(Booking.deleted_at.is_(None), Booking.assigned_user_id == uid, booking_event_in_range))]
    funnel_deals = db.scalar(select(func.count(func.distinct(Deal.id))).where(*funnel_deal_scope)) or 0
    contract_rows = db.execute(select(Contract, Deal).join(Deal, Contract.deal_id == Deal.id).where(*_valid_contracts(start, end), Deal.deleted_at.is_(None), Deal.owner_id == uid)).all()
    contract_count = len(contract_rows); revenue = sum(_money(c.contract_value) for c, _d in contract_rows)
    funnel_contracts = db.scalar(select(func.count(func.distinct(Contract.id))).join(Deal, Contract.deal_id == Deal.id).where(*_valid_contracts(start, end), *funnel_deal_scope)) or 0
    receipt_total = _money(db.scalar(select(func.coalesce(func.sum(PaymentReceipt.amount), 0)).join(Contract, PaymentReceipt.contract_id == Contract.id).join(Deal, Contract.deal_id == Deal.id).where(PaymentReceipt.deleted_at.is_(None), PaymentReceipt.status.in_({"confirmed", "paid"}), Deal.owner_id == uid, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) >= start, func.coalesce(PaymentReceipt.confirmed_at, PaymentReceipt.created_at) < end)))
    comm_q = [SalesCommission.sale_id == uid, SalesCommission.status.in_(SALES_COMMISSION_INCLUDED_STATUSES), SalesCommission.created_at >= start, SalesCommission.created_at < end]
    sc_approved = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.approved_commission), 0)).where(*comm_q))); sc_paid = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.paid_amount), 0)).where(*comm_q)))
    days = _dates(start, end); leads_by_day = {d: {"date": d, "label": d[-2:], "count": 0} for d in days}; revenue_by_day = {d: {"date": d, "label": d[-2:], "amount": 0} for d in days}
    for day, count in db.execute(select(func.date(Lead.created_at), func.count()).where(*lead_base, Lead.created_at >= start, Lead.created_at < end, Lead.duplicate_detected.is_(False), Lead.duplicate_of_customer_id.is_(None)).group_by(func.date(Lead.created_at))): leads_by_day[str(day)]["count"] = count
    for c, d in contract_rows:
        key = (c.effective_date or c.signed_date or c.created_at).date().isoformat(); revenue_by_day[key]["amount"] += _money(c.contract_value)
    summary = {"task_today_count": task_today, "task_overdue_count": task_overdue, "appointment_today_count": appt_today, "appointment_overdue_count": appt_overdue, "lead_care_today_count": lead_care_today, "lead_overdue_count": lead_overdue, "lead_new_count": lead_new, "lead_active_count": lead_active, "lead_without_activity_count": lead_without_activity, "customer_count": customers, "customer_stale_count": customer_stale, "booking_count": bookings, "deposit_count": deposits, "deal_count": deals, "contract_signed_count": contract_count, "revenue_total": revenue, "receipt_total": receipt_total, "sales_commission_approved_total": sc_approved, "sales_commission_paid_total": sc_paid, "sales_commission_outstanding_total": max(sc_approved - sc_paid, 0), "lead_to_customer_rate": _rate(funnel_customer_converted, lead_new), "sales_commission_payment_rate": _rate(sc_paid, sc_approved), "lead_hot_count": lead_hot, "lead_stale_count": stale}
    priority = [{"key":"task_overdue","label":"Công việc quá hạn","count":task_overdue,"url":"/tasks/overdue?scope=mine"},{"key":"appointment_overdue","label":"Lịch hẹn quá hạn","count":appt_overdue,"url":"/appointments?scope=mine&status=overdue"},{"key":"lead_overdue","label":"Lead quá hạn chăm sóc","count":lead_overdue,"url":"/leads/overdue?scope=mine&care_status=overdue"},{"key":"lead_hot","label":"Lead nóng","count":lead_hot,"url":"/leads?scope=mine&priority=hot"},{"key":"lead_stale","label":"Lead lâu chưa tương tác","count":stale,"url":"/leads?scope=mine&stale=true"},{"key":"customer_stale","label":"Khách lâu chưa tương tác","count":customer_stale,"url":"/customers?scope=mine&stale=true"}]
    return {"range": _range_public(r), "scope": {k: v for k, v in resolve_sale_dashboard_scope(user).items() if k != "user_ids"}, "summary": summary, "time_series": {"leads_by_day": list(leads_by_day.values()), "revenue_by_day": list(revenue_by_day.values())}, "funnel": {"lead_count": lead_new, "customer_count": funnel_customer_converted, "booking_count": funnel_bookings, "deposit_count": funnel_deposits, "deal_count": funnel_deals, "contract_count": funnel_contracts, "lead_to_customer_rate": _rate(funnel_customer_converted, lead_new), "booking_to_contract_rate": _rate(funnel_contracts, funnel_bookings)}, "priority": priority}

SALES_MANAGEMENT_PERMISSIONS = {"dashboard.sales_manager.view", "dashboard.leader.view", "dashboard.team.view", "dashboard.sales.view.all"}
STALE_LEAD_DAYS = 7
CLOSED_LEAD_STATUSES = {"converted", "lost"}  # aligned with lead_service.list_overdue_leads


def _role_codes(user):
    return {getattr(role, "code", None) for role in getattr(user, "roles", []) if getattr(role, "code", None)}


def _scope_ids_from_memberships(db, user_ids):
    memberships = list(db.scalars(select(UserOrganizationMembership).where(UserOrganizationMembership.user_id.in_(user_ids)))) if user_ids else []
    return {m.team_id for m in memberships if m.team_id}, {m.department_id for m in memberships if m.department_id}


def resolve_sales_management_scope(db: Session, current_user: User, scope_type: str | None = "auto", team_id=None, department_id=None) -> dict:
    from fastapi import HTTPException
    ps = permissions(current_user); roles = _role_codes(current_user)
    can_view_all = current_user.is_superuser or bool(ps & {"dashboard.view.all", "dashboard.sales.view.all", "dashboard.leader.view.all"})
    requested = scope_type or "auto"
    if can_view_all:
        user_query = select(User.id).where(User.status == "active", User.deleted_at.is_(None))
        actual = "all"
        if team_id:
            user_query = user_query.join(UserOrganizationMembership, UserOrganizationMembership.user_id == User.id).where(UserOrganizationMembership.team_id == team_id); actual = "team"
        elif department_id:
            user_query = user_query.join(UserOrganizationMembership, UserOrganizationMembership.user_id == User.id).where(UserOrganizationMembership.department_id == department_id); actual = "department"
        user_ids = set(db.scalars(user_query))
    elif "sales_manager" in roles and ("dashboard.sales_manager.view" in ps or "dashboard.team.view" in ps or "dashboard.view.team" in ps):
        managed_departments = set(db.scalars(select(Department.id).where(Department.manager_id == current_user.id, Department.status == "active", Department.deleted_at.is_(None))))
        member_departments = set(db.scalars(select(UserOrganizationMembership.department_id).where(UserOrganizationMembership.user_id == current_user.id, UserOrganizationMembership.department_id.is_not(None))))
        allowed_departments = managed_departments | member_departments
        allowed_teams = set(db.scalars(select(Team.id).where(Team.department_id.in_(allowed_departments), Team.deleted_at.is_(None)))) if allowed_departments else set()
        if department_id and department_id not in allowed_departments: raise HTTPException(403, "Bạn không có quyền xem phòng ban này")
        if team_id and team_id not in allowed_teams: raise HTTPException(403, "Bạn không có quyền xem team này")
        q = select(UserOrganizationMembership.user_id)
        if team_id:
            q = q.where(UserOrganizationMembership.team_id == team_id); actual = "team"
        else:
            q = q.where(UserOrganizationMembership.department_id.in_({department_id} if department_id else allowed_departments)); actual = "department"
        user_ids = set(db.scalars(q)) | {current_user.id}
        if not allowed_departments and not user_ids: raise HTTPException(403, "Không xác định được phạm vi dashboard quản lý sale")
    elif "leader" in roles and ("dashboard.leader.view" in ps or "dashboard.team.view" in ps or "dashboard.view.team" in ps):
        allowed_teams = set(db.scalars(select(Team.id).where(Team.leader_id == current_user.id, Team.status == "active", Team.deleted_at.is_(None))))
        member_teams = set(db.scalars(select(UserOrganizationMembership.team_id).where(UserOrganizationMembership.user_id == current_user.id, UserOrganizationMembership.team_id.is_not(None))))
        allowed_teams |= member_teams
        if team_id and team_id not in allowed_teams: raise HTTPException(403, "Bạn không có quyền xem team này")
        selected = {team_id} if team_id else allowed_teams
        if not selected: raise HTTPException(403, "Không xác định được team dashboard quản lý sale")
        user_ids = set(db.scalars(select(UserOrganizationMembership.user_id).where(UserOrganizationMembership.team_id.in_(selected)))) | {current_user.id}
        actual = "team"
    else:
        raise HTTPException(403, "Bạn không có quyền xem dashboard quản lý sale")
    team_ids, department_ids = _scope_ids_from_memberships(db, user_ids)
    team = db.get(Team, team_id) if team_id else None; dept = db.get(Department, department_id) if department_id else None
    return {"user_ids": user_ids, "team_ids": team_ids, "department_ids": department_ids, "scope_type": actual, "team_id": str(team_id) if team_id else None, "team_name": team.name if team else None, "department_id": str(department_id) if department_id else None, "department_name": dept.name if dept else None, "member_count": len(user_ids), "can_view_all": can_view_all}


def _range_public(r):
    return {"preset": r["preset"], "start_date": r["from_date"], "end_date": r["to_date"], "from_date": r["from_date"], "to_date": r["to_date"], "label": r["label"]}

def _lead_scope_condition(scope): return Lead.owner_id.in_(scope["user_ids"])
def _task_scope_condition(scope): return LeadTask.assigned_to_id.in_(scope["user_ids"])
def _appt_scope_condition(scope): return LeadAppointment.assigned_to_id.in_(scope["user_ids"])

def _alert_user(u): return {"id": str(u.id), "full_name": u.full_name} if u else None

def _lead_alert(lead):
    return {"id": str(lead.id), "title": lead.full_name, "code": lead.code, "status": lead.status, "owner": _alert_user(lead.owner), "due_at": lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None, "last_contact_at": lead.last_contact_at.isoformat() if lead.last_contact_at else None, "url": f"/leads/{lead.id}"}

def _task_alert(task):
    return {"id": str(task.id), "title": task.title, "status": task.status, "assignee": _alert_user(task.assigned_to), "due_at": task.due_at.isoformat() if task.due_at else None, "lead_id": str(task.lead_id), "url": f"/leads/{task.lead_id}"}

def _appt_alert(appt):
    return {"id": str(appt.id), "title": appt.title, "status": appt.status, "assignee": _alert_user(appt.assigned_to), "start_at": appt.start_at.isoformat() if appt.start_at else None, "lead_id": str(appt.lead_id), "url": f"/leads/{appt.lead_id}"}


def _top_users(rows, key): return sorted(rows.values(), key=lambda x: x.get(key, 0), reverse=True)[:10]


def _resolve_sales_management_project(db: Session, contract: Contract, deal: Deal | None) -> tuple[str, str | None, str, str]:
    """Resolve project for top_projects_by_revenue without changing revenue attribution.

    Fallback order follows Sprint 33.2 business rule and only uses fields that exist in
    the current schema: contract.project_id, deal.project_id, booking/property unit
    project_id, then lead project_interest as a named bucket.
    """
    project_id = contract.project_id or (deal.project_id if deal else None)
    source = "contract.project_id" if contract.project_id else "deal.project_id" if project_id else "unknown"
    if not project_id and contract.booking and contract.booking.property_unit and contract.booking.property_unit.project_id:
        project_id = contract.booking.property_unit.project_id; source = "booking.property_unit.project_id"
    if not project_id and contract.property_unit and contract.property_unit.project_id:
        project_id = contract.property_unit.project_id; source = "contract.property_unit.project_id"
    if not project_id and deal and deal.property_unit and deal.property_unit.project_id:
        project_id = deal.property_unit.project_id; source = "deal.property_unit.project_id"
    if project_id:
        project = db.get(Project, project_id)
        return str(project_id), str(project_id), project.name if project else "Chưa có dự án", source
    lead_project = (deal.source_lead.project_interest if deal and deal.source_lead else None) or (deal.project_name if deal else None)
    if lead_project:
        return f"lead_project:{lead_project}", None, lead_project, "lead.project_interest"
    return "unknown", None, "Chưa có dự án", "unknown"


def get_sales_management_dashboard(db: Session, user: User, preset: str | None = None, start_date: date | str | None = None, end_date: date | str | None = None, scope_type: str | None = "auto", team_id=None, department_id=None) -> dict:
    r = resolve_dashboard_date_range(preset or "last_7_days", start_date, end_date); start, end = r["_start"], r["_end"]; today_start, today_end = _bounds(); stamp = now(); stale_before = stamp - timedelta(days=STALE_LEAD_DAYS)
    scope = resolve_sales_management_scope(db, user, scope_type, team_id, department_id); ids = scope["user_ids"] or {user.id}
    lead_base = [Lead.deleted_at.is_(None), _lead_scope_condition(scope)]
    lead_new = _count(db, Lead, *lead_base, Lead.created_at >= start, Lead.created_at < end, Lead.duplicate_detected.is_(False), Lead.duplicate_of_customer_id.is_(None))
    assigned = _count(db, Lead, *lead_base, Lead.owner_id.is_not(None))
    unassigned = _count(db, Lead, Lead.deleted_at.is_(None), Lead.owner_id.is_(None), Lead.created_at >= start, Lead.created_at < end)
    overdue = _count(db, Lead, *lead_base, Lead.next_follow_up_at.is_not(None), Lead.next_follow_up_at < stamp, Lead.status.notin_(CLOSED_LEAD_STATUSES))
    without_activity = db.scalar(select(func.count()).select_from(Lead).where(*lead_base, ~Lead.activities.any())) or 0
    stale = _count(db, Lead, *lead_base, Lead.status.notin_(CLOSED_LEAD_STATUSES), func.coalesce(Lead.last_contact_at, Lead.created_at) < stale_before)
    duplicate_count = _count(db, LeadActivity, LeadActivity.activity_type == "duplicate_reengagement", LeadActivity.user_id.in_(ids), LeadActivity.created_at >= start, LeadActivity.created_at < end)
    active_task = LeadTask.status.in_({"pending", "in_progress"})
    task_today = _count(db, LeadTask, LeadTask.deleted_at.is_(None), _task_scope_condition(scope), active_task, LeadTask.due_at >= today_start, LeadTask.due_at < today_end)
    task_overdue = _count(db, LeadTask, LeadTask.deleted_at.is_(None), _task_scope_condition(scope), active_task, LeadTask.due_at < stamp)
    appt_today = _count(db, LeadAppointment, LeadAppointment.deleted_at.is_(None), _appt_scope_condition(scope), LeadAppointment.start_at >= today_start, LeadAppointment.start_at < today_end)
    appt_overdue = _count(db, LeadAppointment, LeadAppointment.deleted_at.is_(None), _appt_scope_condition(scope), LeadAppointment.status.in_({"scheduled", "rescheduled"}), LeadAppointment.start_at < stamp)
    bookings = _count(db, Booking, Booking.deleted_at.is_(None), Booking.assigned_user_id.in_(ids), Booking.created_at >= start, Booking.created_at < end)
    deposits = _count(db, Booking, Booking.deleted_at.is_(None), Booking.assigned_user_id.in_(ids), Booking.status.in_(DEPOSIT_BOOKING_STATUSES), func.coalesce(Booking.deposit_date, Booking.created_at) >= start, func.coalesce(Booking.deposit_date, Booking.created_at) < end)
    deals = _count(db, Deal, Deal.deleted_at.is_(None), Deal.owner_id.in_(ids), Deal.created_at >= start, Deal.created_at < end)
    contract_stmt = select(Contract, Deal, User).join(Deal, Contract.deal_id == Deal.id).join(User, Deal.owner_id == User.id).where(*_valid_contracts(start, end), Deal.deleted_at.is_(None), Deal.owner_id.in_(ids))
    contract_rows = db.execute(contract_stmt).all(); contract_count = len(contract_rows); revenue = sum(_money(c.contract_value) for c, _d, _u in contract_rows)
    comm_q = [SalesCommission.sale_id.in_(ids), SalesCommission.status.in_(SALES_COMMISSION_INCLUDED_STATUSES), SalesCommission.created_at >= start, SalesCommission.created_at < end]
    sc_approved = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.approved_commission), 0)).where(*comm_q))); sc_paid = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.paid_amount), 0)).where(*comm_q)))
    days = _dates(start, end); leads_by_day = {d: {"date": d, "label": d[-2:], "count": 0} for d in days}; revenue_by_day = {d: {"date": d, "label": d[-2:], "amount": 0} for d in days}; tasks_by_day = {d: {"date": d, "label": d[-2:], "count": 0} for d in days}; appts_by_day = {d: {"date": d, "label": d[-2:], "count": 0} for d in days}
    for day, count in db.execute(select(func.date(Lead.created_at), func.count()).where(*lead_base, Lead.created_at >= start, Lead.created_at < end, Lead.duplicate_detected.is_(False), Lead.duplicate_of_customer_id.is_(None)).group_by(func.date(Lead.created_at))): leads_by_day[str(day)]["count"] = count
    for c, d, u in contract_rows:
        key = _valid_contract_date(c.__class__) if False else (c.effective_date or c.signed_date or c.created_at).date().isoformat(); revenue_by_day[key]["amount"] += _money(c.contract_value)
    for day, count in db.execute(select(func.date(LeadTask.due_at), func.count()).where(LeadTask.deleted_at.is_(None), _task_scope_condition(scope), active_task, LeadTask.due_at >= start, LeadTask.due_at < end).group_by(func.date(LeadTask.due_at))): tasks_by_day[str(day)]["count"] = count
    for day, count in db.execute(select(func.date(LeadAppointment.start_at), func.count()).where(LeadAppointment.deleted_at.is_(None), _appt_scope_condition(scope), LeadAppointment.start_at >= start, LeadAppointment.start_at < end).group_by(func.date(LeadAppointment.start_at))): appts_by_day[str(day)]["count"] = count
    customers = _count(db, Customer, Customer.deleted_at.is_(None), Customer.created_at >= start, Customer.created_at < end)
    sales = {str(uid): {"sale_id": str(uid), "sale_name": (db.get(User, uid).full_name if db.get(User, uid) else "Chưa xác định"), "revenue": 0, "contract_count": 0, "activity_count": 0, "overdue_lead_count": 0} for uid in ids}
    projects = {}; sources = {}
    for c, d, u in contract_rows:
        b = sales.setdefault(str(u.id), {"sale_id": str(u.id), "sale_name": u.full_name, "revenue": 0, "contract_count": 0, "activity_count": 0, "overdue_lead_count": 0}); b["revenue"] += _money(c.contract_value); b["contract_count"] += 1
        project_key, project_id, project_name, project_source = _resolve_sales_management_project(db, c, d)
        pb = projects.setdefault(project_key, {"project_id": project_id, "id": project_id, "project_name": project_name, "name": project_name, "project_source": project_source, "revenue": 0, "contract_count": 0, "lead_count": 0})
        pb["revenue"] += _money(c.contract_value); pb["contract_count"] += 1
        if d.source_lead_id: pb["lead_count"] += 1
    for uid, cnt in db.execute(select(LeadActivity.user_id, func.count()).where(LeadActivity.user_id.in_(ids), LeadActivity.created_at >= start, LeadActivity.created_at < end).group_by(LeadActivity.user_id)): sales.setdefault(str(uid), {"sale_id": str(uid), "sale_name": "Chưa xác định", "revenue": 0, "contract_count": 0, "activity_count": 0, "overdue_lead_count": 0})["activity_count"] = cnt
    for uid, cnt in db.execute(select(Lead.owner_id, func.count()).where(*lead_base, Lead.next_follow_up_at.is_not(None), Lead.next_follow_up_at < stamp).group_by(Lead.owner_id)):
        if uid: sales.setdefault(str(uid), {"sale_id": str(uid), "sale_name": "Chưa xác định", "revenue": 0, "contract_count": 0, "activity_count": 0, "overdue_lead_count": 0})["overdue_lead_count"] = cnt
    for src, cnt in db.execute(select(Lead.source, func.count()).where(*lead_base, Lead.created_at >= start, Lead.created_at < end).group_by(Lead.source).order_by(func.count().desc()).limit(10)): sources[src or "Chưa xác định"] = {"source": src or "Chưa xác định", "lead_count": cnt}
    summary = {"member_count": len(ids), "lead_new_count": lead_new, "lead_assigned_count": assigned, "lead_unassigned_count": unassigned, "lead_overdue_count": overdue, "lead_without_activity_count": without_activity, "lead_stale_count": stale, "duplicate_reengagement_count": duplicate_count, "task_today_count": task_today, "task_overdue_count": task_overdue, "appointment_today_count": appt_today, "appointment_overdue_count": appt_overdue, "booking_count": bookings, "deposit_count": deposits, "deal_count": deals, "contract_signed_count": contract_count, "revenue_total": revenue, "avg_contract_value": revenue / contract_count if contract_count else None, "sales_commission_approved_total": sc_approved, "sales_commission_paid_total": sc_paid, "sales_commission_outstanding_total": max(sc_approved - sc_paid, 0), "lead_to_customer_rate": _rate(customers, lead_new), "booking_to_contract_rate": _rate(contract_count, bookings)}
    return {"range": _range_public(r), "scope": {k: v for k, v in scope.items() if k != "user_ids"}, "summary": summary, "time_series": {"leads_by_day": list(leads_by_day.values()), "revenue_by_day": list(revenue_by_day.values()), "tasks_overdue_by_day": list(tasks_by_day.values()), "appointments_by_day": list(appts_by_day.values())}, "funnel": {"lead_count": lead_new, "customer_count": customers, "booking_count": bookings, "deposit_count": deposits, "deal_count": deals, "contract_count": contract_count, "lead_to_customer_rate": _rate(customers, lead_new), "booking_to_contract_rate": _rate(contract_count, bookings)}, "rankings": {"top_sales_by_revenue": _top_users(sales, "revenue"), "top_sales_by_contract_count": _top_users(sales, "contract_count"), "top_sales_by_activity_count": _top_users(sales, "activity_count"), "top_sales_with_overdue_leads": _top_users(sales, "overdue_lead_count"), "top_sources_by_lead_count": list(sources.values())[:10], "top_projects_by_revenue": sorted(projects.values(), key=lambda x: x["revenue"], reverse=True)[:10]}, "alerts": {"unassigned_leads": [_lead_alert(x) for x in db.scalars(select(Lead).where(Lead.deleted_at.is_(None), Lead.owner_id.is_(None)).order_by(Lead.created_at.desc()).limit(10)).unique()], "overdue_leads": [_lead_alert(x) for x in db.scalars(select(Lead).where(*lead_base, Lead.next_follow_up_at.is_not(None), Lead.next_follow_up_at < stamp).order_by(Lead.next_follow_up_at).limit(10)).unique()], "stale_leads": [_lead_alert(x) for x in db.scalars(select(Lead).where(*lead_base, func.coalesce(Lead.last_contact_at, Lead.created_at) < stale_before).order_by(func.coalesce(Lead.last_contact_at, Lead.created_at)).limit(10)).unique()], "overdue_tasks": [_task_alert(x) for x in db.scalars(select(LeadTask).where(LeadTask.deleted_at.is_(None), _task_scope_condition(scope), active_task, LeadTask.due_at < stamp).order_by(LeadTask.due_at).limit(10)).unique()], "today_appointments": [_appt_alert(x) for x in db.scalars(select(LeadAppointment).where(LeadAppointment.deleted_at.is_(None), _appt_scope_condition(scope), LeadAppointment.start_at >= today_start, LeadAppointment.start_at < today_end).order_by(LeadAppointment.start_at).limit(10)).unique()]}}
