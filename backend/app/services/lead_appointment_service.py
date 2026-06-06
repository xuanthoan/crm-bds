from datetime import datetime, time, timedelta, timezone
from math import ceil
from sqlalchemy import func, or_, select
from fastapi import HTTPException
from app.models.lead import Lead
from app.models.lead_appointment import LeadAppointment
from app.permissions.dependencies import get_user_permissions
from app.services.lead_service import apply_view_scope,can_update_lead,can_view_lead,get_lead_by_id
from app.services.organization_service import list_eligible_lead_assignees
from app.services.lead_activity_service import create_activity_record
from app.services.audit_service import write_audit_log
TYPES={"office_meeting","site_visit","phone_call","video_call","contract_meeting","other"}; STATUSES={"scheduled","completed","cancelled","no_show","rescheduled"}
def _p(u):return set(get_user_permissions(u))
def _user(u):return {"id":u.id,"full_name":u.full_name,"email":u.email} if u else None
def serialize_appointment(a):
    return {"id":a.id,"lead":{"id":a.lead.id,"code":a.lead.code,"full_name":a.lead.full_name,"phone_primary":a.lead.phone_primary},"title":a.title,"description":a.description,"appointment_type":a.appointment_type,"status":a.status,"start_at":a.start_at,"end_at":a.end_at,"location":a.location,"meeting_link":a.meeting_link,"assigned_to":_user(a.assigned_to),"created_by":_user(a.created_by),"completed_by":_user(a.completed_by),"completed_at":a.completed_at,"result_note":a.result_note,"created_at":a.created_at,"updated_at":a.updated_at,"is_overdue":a.status=="scheduled" and a.start_at<datetime.now(timezone.utc)}
def _scope(db,u):return or_(LeadAppointment.assigned_to_id==u.id,LeadAppointment.lead_id.in_(apply_view_scope(db,select(Lead.id).where(Lead.deleted_at.is_(None)),u)))
def _validate(p,start,end):
    if getattr(p,"appointment_type",None) and p.appointment_type not in TYPES:raise HTTPException(400,"Loại lịch hẹn không hợp lệ")
    if end and end<=start:raise HTTPException(400,"Thời gian kết thúc phải sau thời gian bắt đầu")
def _assignee(db,u,target):
    if target==u.id:return
    try: eligible=list_eligible_lead_assignees(db,u)
    except HTTPException:raise HTTPException(400,"Người phụ trách lịch hẹn không hợp lệ")
    if target not in {x.id for x in eligible}:raise HTTPException(400,"Người phụ trách lịch hẹn không hợp lệ")
def _require_view_permission(u):
    if not u.is_superuser and not (_p(u) & {"lead_appointments.view.own","lead_appointments.view.team","lead_appointments.view.all"}):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
def list_appointments(db,u,*,page=1,page_size=20,appointment_status=None,appointment_type=None,assigned_to_id=None,lead_id=None,start_from=None,start_to=None,today=False,upcoming=False):
    _require_view_permission(u);q=select(LeadAppointment).where(LeadAppointment.deleted_at.is_(None),_scope(db,u));now=datetime.now(timezone.utc);c=[]
    if appointment_status:c.append(LeadAppointment.status==appointment_status)
    if appointment_type:c.append(LeadAppointment.appointment_type==appointment_type)
    if assigned_to_id:c.append(LeadAppointment.assigned_to_id==assigned_to_id)
    if lead_id:c.append(LeadAppointment.lead_id==lead_id)
    if start_from:c.append(LeadAppointment.start_at>=start_from)
    if start_to:c.append(LeadAppointment.start_at<=start_to)
    if today:
        start=datetime.combine(now.date(),time.min,tzinfo=timezone.utc);c += [LeadAppointment.start_at>=start,LeadAppointment.start_at<start+timedelta(days=1)]
    if upcoming:c += [LeadAppointment.start_at>=now,LeadAppointment.start_at<=now+timedelta(days=7),LeadAppointment.status.in_({"scheduled","rescheduled"})]
    q=q.where(*c);total=db.scalar(select(func.count()).select_from(q.subquery())) or 0;items=list(db.scalars(q.order_by(LeadAppointment.start_at).offset((page-1)*page_size).limit(page_size)).unique());return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_appointment(db,id):return db.scalar(select(LeadAppointment).where(LeadAppointment.id==id,LeadAppointment.deleted_at.is_(None)))
def require_view(db,a,u):
    _require_view_permission(u)
    if a.assigned_to_id!=u.id and not can_view_lead(db,u,a.lead):raise HTTPException(403,"Bạn không có quyền truy cập lịch hẹn này")
def require_update(db,a,u,complete=False):
    p=_p(u);prefix="lead_appointments.complete" if complete else "lead_appointments.update"
    if u.is_superuser or f"{prefix}.all" in p:return
    if a.assigned_to_id==u.id and f"{prefix}.own" in p:return
    if f"{prefix}.team" in p and can_update_lead(db,u,a.lead):return
    raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
def create_appointment(db,payload,actor):
    if "lead_appointments.create" not in _p(actor) and not actor.is_superuser:raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    lead=get_lead_by_id(db,payload.lead_id)
    if not lead:raise HTTPException(404,"Không tìm thấy lead")
    if not can_update_lead(db,actor,lead):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    _validate(payload,payload.start_at,payload.end_at);target=payload.assigned_to_id or lead.owner_id or actor.id;_assignee(db,actor,target)
    a=LeadAppointment(**payload.model_dump(exclude={"assigned_to_id"}),assigned_to_id=target,created_by_id=actor.id,status="scheduled");db.add(a);db.flush()
    if payload.start_at>datetime.now(timezone.utc) and (not lead.next_follow_up_at or payload.start_at<lead.next_follow_up_at):lead.next_follow_up_at=payload.start_at
    create_activity_record(db,lead=lead,actor=actor,activity_type="meeting",title="Tạo lịch hẹn",content=f"{a.title} - {a.start_at.isoformat()}");write_audit_log(db,action="lead_appointments.create",user_id=actor.id,entity_type="lead_appointment",entity_id=str(a.id));db.commit();db.refresh(a);return a
def update_appointment(db,a,payload,actor):
    require_update(db,a,actor);data=payload.model_dump(exclude_unset=True);start=data.get("start_at",a.start_at);end=data.get("end_at",a.end_at);_validate(payload,start,end)
    if data.get("assigned_to_id"):_assignee(db,actor,data["assigned_to_id"])
    [setattr(a,k,v) for k,v in data.items()]
    if start>datetime.now(timezone.utc) and (not a.lead.next_follow_up_at or start<a.lead.next_follow_up_at):a.lead.next_follow_up_at=start
    write_audit_log(db,action="lead_appointments.update",user_id=actor.id,entity_type="lead_appointment",entity_id=str(a.id));db.commit();db.refresh(a);return a
def update_appointment_status(db,a,payload,actor):
    require_update(db,a,actor,True)
    if payload.status not in STATUSES:raise HTTPException(400,"Trạng thái lịch hẹn không hợp lệ")
    old=f"{a.start_at.isoformat()} / {a.end_at.isoformat() if a.end_at else ''}";a.status=payload.status;a.result_note=payload.result_note;now=datetime.now(timezone.utc);title="Cập nhật lịch hẹn";action="lead_appointments.update";new=None
    if payload.status=="completed":a.completed_at=now;a.completed_by_id=actor.id;a.lead.last_contact_at=now;title="Hoàn thành lịch hẹn";action="lead_appointments.complete"
    elif payload.status=="cancelled":title="Hủy lịch hẹn";action="lead_appointments.cancel"
    elif payload.status=="no_show":title="Khách không đến";action="lead_appointments.cancel"
    elif payload.status=="rescheduled":
        if not payload.rescheduled_start_at:raise HTTPException(400,"Thời gian bắt đầu là bắt buộc")
        _validate(payload,payload.rescheduled_start_at,payload.rescheduled_end_at);a.start_at=payload.rescheduled_start_at;a.end_at=payload.rescheduled_end_at;new=f"{a.start_at.isoformat()} / {a.end_at.isoformat() if a.end_at else ''}";title="Dời lịch hẹn";action="lead_appointments.reschedule"
        if a.start_at>now:a.lead.next_follow_up_at=a.start_at
    create_activity_record(db,lead=a.lead,actor=actor,activity_type="meeting",title=title,content=payload.result_note or a.title,old_value=old if payload.status=="rescheduled" else None,new_value=new);write_audit_log(db,action=action,user_id=actor.id,entity_type="lead_appointment",entity_id=str(a.id));db.commit();db.refresh(a);return a
def delete_appointment(db,a,actor):
    if not actor.is_superuser and "lead_appointments.delete" not in _p(actor):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    require_update(db,a,actor);a.deleted_at=datetime.now(timezone.utc);write_audit_log(db,action="lead_appointments.delete",user_id=actor.id,entity_type="lead_appointment",entity_id=str(a.id));db.commit()
