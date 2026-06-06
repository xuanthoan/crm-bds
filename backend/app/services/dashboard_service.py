from datetime import datetime,time,timedelta,timezone
from fastapi import HTTPException
from sqlalchemy import func,select
from app.models.lead import Lead
from app.models.lead_task import LeadTask
from app.models.lead_appointment import LeadAppointment
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
from app.services.lead_task_service import serialize_task
from app.services.lead_appointment_service import serialize_appointment

def _day():
    now=datetime.now(timezone.utc);start=datetime.combine(now.date(),time.min,tzinfo=timezone.utc);return now,start,start+timedelta(days=1)
def get_my_work_summary(db,user):
    p=set(get_user_permissions(user))
    if not user.is_superuser and not (p & {"dashboard.view.own","dashboard.view.team","dashboard.view.all"}):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    now,start,end=_day();active={"pending","in_progress"}
    tq=select(LeadTask).where(LeadTask.deleted_at.is_(None),LeadTask.assigned_to_id==user.id)
    aq=select(LeadAppointment).where(LeadAppointment.deleted_at.is_(None),LeadAppointment.assigned_to_id==user.id)
    today=list(db.scalars(tq.where(LeadTask.due_at>=start,LeadTask.due_at<end)).unique());overdue=list(db.scalars(tq.where(LeadTask.status.in_(active),LeadTask.due_at<now)).unique());appointments=list(db.scalars(aq.where(LeadAppointment.start_at>=start,LeadAppointment.start_at<end)).unique());upcoming=list(db.scalars(aq.where(LeadAppointment.start_at>=now,LeadAppointment.start_at<=now+timedelta(days=7),LeadAppointment.status.in_({"scheduled","rescheduled"}))).unique())
    leads=list(db.scalars(select(Lead).where(Lead.deleted_at.is_(None),Lead.owner_id==user.id,Lead.next_follow_up_at<now,Lead.status.not_in({"converted","lost"}))).unique())
    completed=db.scalar(select(func.count(LeadTask.id)).where(LeadTask.assigned_to_id==user.id,LeadTask.completed_at>=start,LeadTask.completed_at<end,LeadTask.deleted_at.is_(None))) or 0
    return {"tasks_today":len(today),"tasks_overdue":len(overdue),"appointments_today":len(appointments),"appointments_upcoming":len(upcoming),"leads_need_follow_up":len(leads),"completed_tasks_today":completed,"today_tasks":[serialize_task(x) for x in today[:10]],"overdue_tasks":[serialize_task(x) for x in overdue[:10]],"upcoming_appointments":[serialize_appointment(x) for x in upcoming[:10]],"follow_up_leads":[{"id":x.id,"code":x.code,"full_name":x.full_name,"next_follow_up_at":x.next_follow_up_at} for x in leads[:10]]}
def _team_ids(db,user):
    p=set(get_user_permissions(user))
    if user.is_superuser or "dashboard.view.all" in p:return get_accessible_user_ids_for_lead_scope(db,user,"all")
    if "dashboard.view.team" not in p:raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    if "leads.view.department" in p:return get_accessible_user_ids_for_lead_scope(db,user,"department")
    return get_accessible_user_ids_for_lead_scope(db,user,"team")
def get_team_work_summary(db,user):
    ids=_team_ids(db,user);now,start,end=_day();active={"pending","in_progress"};users=list(db.scalars(select(User).where(User.id.in_(ids),User.status=="active")).unique());rows=[]
    for member in users:
        base=[LeadTask.deleted_at.is_(None),LeadTask.assigned_to_id==member.id];today=db.scalar(select(func.count(LeadTask.id)).where(*base,LeadTask.due_at>=start,LeadTask.due_at<end)) or 0;overdue=db.scalar(select(func.count(LeadTask.id)).where(*base,LeadTask.status.in_(active),LeadTask.due_at<now)) or 0;completed=db.scalar(select(func.count(LeadTask.id)).where(*base,LeadTask.completed_at>=start,LeadTask.completed_at<end)) or 0;appts=db.scalar(select(func.count(LeadAppointment.id)).where(LeadAppointment.deleted_at.is_(None),LeadAppointment.assigned_to_id==member.id,LeadAppointment.start_at>=start,LeadAppointment.start_at<end)) or 0;leads=db.scalar(select(func.count(Lead.id)).where(Lead.deleted_at.is_(None),Lead.owner_id==member.id)) or 0;follow=db.scalar(select(func.count(Lead.id)).where(Lead.deleted_at.is_(None),Lead.owner_id==member.id,Lead.next_follow_up_at<now,Lead.status.not_in({"converted","lost"}))) or 0
        rows.append({"user":{"id":member.id,"full_name":member.full_name,"email":member.email},"leads_owned":leads,"tasks_today":today,"tasks_overdue":overdue,"appointments_today":appts,"completed_today":completed,"leads_need_follow_up":follow})
    return {"team_tasks_today":sum(x["tasks_today"] for x in rows),"team_tasks_overdue":sum(x["tasks_overdue"] for x in rows),"team_appointments_today":sum(x["appointments_today"] for x in rows),"team_leads_need_follow_up":sum(x["leads_need_follow_up"] for x in rows),"per_user_summary":rows}
