from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.lead_task import LeadTask
from app.models.lead_appointment import LeadAppointment
from app.models.user import User
from app.services.lead_task_service import _accessible_ids, now, permissions, user_dict

def _bounds():
    start=datetime.combine(date.today(),time.min,tzinfo=timezone.utc); return start,start+timedelta(days=1)
def _count(db,model,*conditions):return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0
def _summary(db,user_id):
    start,end=_bounds(); active=LeadTask.status.in_({"pending","in_progress"}); live_task=LeadTask.deleted_at.is_(None); live_appt=LeadAppointment.deleted_at.is_(None)
    return {"tasks_today":_count(db,LeadTask,live_task,LeadTask.assigned_to_id==user_id,active,LeadTask.due_at>=start,LeadTask.due_at<end),"tasks_overdue":_count(db,LeadTask,live_task,LeadTask.assigned_to_id==user_id,active,LeadTask.due_at<now()),"appointments_today":_count(db,LeadAppointment,live_appt,LeadAppointment.assigned_to_id==user_id,LeadAppointment.start_at>=start,LeadAppointment.start_at<end),"appointments_upcoming":_count(db,LeadAppointment,live_appt,LeadAppointment.assigned_to_id==user_id,LeadAppointment.status.in_({"scheduled","rescheduled"}),LeadAppointment.start_at>=now(),LeadAppointment.start_at<now()+timedelta(days=7)),"leads_need_follow_up":_count(db,Lead,Lead.deleted_at.is_(None),Lead.owner_id==user_id,Lead.next_follow_up_at<now()),"completed_tasks_today":_count(db,LeadTask,live_task,LeadTask.assigned_to_id==user_id,LeadTask.status=="completed",LeadTask.completed_at>=start,LeadTask.completed_at<end)}
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
