from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models.lead_task import LeadTask
from app.models.lead_appointment import LeadAppointment
from app.models.user import User
from app.models.customer import Customer
from app.models.booking import Booking
from app.models.deal import Deal
from app.models.contract import Contract
from app.models.project import Project
from app.models.sales_commission import SalesCommission
from app.models.company_commission import CompanyCommissionReceivable
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
    sales_commission = _money(db.scalar(select(func.coalesce(func.sum(SalesCommission.approved_commission + SalesCommission.paid_amount), 0)).where(SalesCommission.status.in_(SALES_COMMISSION_INCLUDED_STATUSES), SalesCommission.created_at >= start, SalesCommission.created_at < end)))
    company_commission_receivable = _money(db.scalar(select(func.coalesce(func.sum(CompanyCommissionReceivable.confirmed_receivable_amount), 0)).where(CompanyCommissionReceivable.status.in_(COMPANY_COMMISSION_INCLUDED_STATUSES), CompanyCommissionReceivable.created_at >= start, CompanyCommissionReceivable.created_at < end)))
    company_commission_received = _money(db.scalar(select(func.coalesce(func.sum(CompanyCommissionReceivable.received_amount), 0)).where(CompanyCommissionReceivable.status.in_(COMPANY_COMMISSION_INCLUDED_STATUSES), CompanyCommissionReceivable.created_at >= start, CompanyCommissionReceivable.created_at < end)))
    ads_cost = 0.0; roi_ratio = revenue / ads_cost if ads_cost else None; roi_profit_ratio = (revenue - ads_cost) / ads_cost if ads_cost else None
    duplicate_count = _count(db, LeadActivity, LeadActivity.activity_type == "duplicate_reengagement", LeadActivity.created_at >= start, LeadActivity.created_at < end)
    day_map = {d: {"date": d, "count": 0} for d in _dates(start, end)}; revenue_day = {d: {"date": d, "amount": 0} for d in _dates(start, end)}; contracts_day = {d: {"date": d, "count": 0} for d in _dates(start, end)}; bookings_day = {d: {"date": d, "count": 0} for d in _dates(start, end)}
    for day, count in db.execute(select(func.date(Lead.created_at), func.count()).where(Lead.deleted_at.is_(None), Lead.created_at >= start, Lead.created_at < end).group_by(func.date(Lead.created_at))): day_map[str(day)]["count"] = count
    for day, amount, count in db.execute(select(func.date(_valid_contract_date()), func.coalesce(func.sum(Contract.contract_value), 0), func.count()).where(*_valid_contracts(start, end)).group_by(func.date(_valid_contract_date()))): revenue_day[str(day)]["amount"] = _money(amount); contracts_day[str(day)]["count"] = count
    for day, count in db.execute(select(func.date(Booking.created_at), func.count()).where(Booking.deleted_at.is_(None), Booking.created_at >= start, Booking.created_at < end).group_by(func.date(Booking.created_at))): bookings_day[str(day)]["count"] = count
    lead_by_source = [{"source": s or "Chưa xác định", "count": c} for s, c in db.execute(select(Lead.source, func.count()).where(Lead.deleted_at.is_(None), Lead.created_at >= start, Lead.created_at < end).group_by(Lead.source))]
    sales7, teams7, _ = _leaderboards(db, datetime.now(timezone.utc)-timedelta(days=7), datetime.now(timezone.utc)+timedelta(days=1))
    sales30, teams30, _ = _leaderboards(db, datetime.now(timezone.utc)-timedelta(days=30), datetime.now(timezone.utc)+timedelta(days=1))
    sales_range, teams_range, top_projects = _leaderboards(db, start, end)
    summary = {"lead_new_count": lead_new, "duplicate_reengagement_count": duplicate_count, "lead_converted_to_customer_count": lead_converted, "booking_count": bookings, "deposit_count": deposits, "deal_count": deals, "contract_signed_count": contract_count, "revenue_total": revenue, "company_commission_total": company_commission_receivable, "company_commission_receivable_total": company_commission_receivable, "company_commission_received_total": company_commission_received, "sales_commission_total": sales_commission, "ads_cost_total": ads_cost, "roi_ratio": roi_ratio, "roi_profit_ratio": roi_profit_ratio}
    funnel = {"leads": lead_new, "customers": customers, "bookings": bookings, "deposits": deposits, "deals": deals, "contracts": contract_count, "lead_to_customer_rate": _rate(customers, lead_new), "lead_to_booking_rate": _rate(bookings, lead_new), "booking_to_contract_rate": _rate(contract_count, bookings), "deal_to_contract_rate": _rate(contract_count, deals)}
    range_public = {k:v for k,v in r.items() if not k.startswith("_")}
    return {"range": range_public, "summary": summary, "funnel": funnel, "time_series": {"leads_by_day": list(day_map.values()), "revenue_by_day": list(revenue_day.values()), "contracts_by_day": list(contracts_day.values()), "bookings_by_day": list(bookings_day.values())}, "breakdowns": {"lead_by_source": lead_by_source, "lead_by_project": [], "revenue_by_project": top_projects, "booking_by_project": [], "contract_by_project": []}, "rankings": {"top_sales_7_days": sales7, "top_sales_30_days": sales30, "top_teams_7_days": teams7, "top_teams_30_days": teams30, "top_projects": top_projects, "top_sources": [{"source": row["source"], "lead_count": row["count"], "booking_count": 0, "contract_count": 0, "revenue": 0, "ads_cost": 0, "roi": None} for row in lead_by_source], "top_sales_in_range": sales_range, "top_teams_in_range": teams_range}}
