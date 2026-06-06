from datetime import date, datetime, time, timedelta, timezone
from math import ceil
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.models.lead import Lead
from app.models.lead_appointment import LeadAppointment
from app.schemas.lead_appointment import LeadAppointmentCreate, LeadAppointmentUpdate, LeadAppointmentStatusUpdate, APPOINTMENT_STATUSES, APPOINTMENT_TYPES
from app.services.audit_service import write_audit_log
from app.services.lead_activity_service import create_activity_record
from app.services.lead_service import can_update_lead, can_view_lead, get_lead_by_id
from app.services.lead_task_service import _accessible_ids, _scope, lead_dict, now, permissions, user_dict
from app.services.user_service import get_user_by_id

def _base(): return select(LeadAppointment).options(joinedload(LeadAppointment.lead),joinedload(LeadAppointment.assigned_to),joinedload(LeadAppointment.created_by),joinedload(LeadAppointment.completed_by)).where(LeadAppointment.deleted_at.is_(None))
def _view_query(db,user,q):
    if user.is_superuser or "lead_appointments.view.all" in permissions(user):return q
    scope=_scope(user,"lead_appointments.view") or _scope(user,"leads.view")
    if not scope:raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    ids=_accessible_ids(db,user,scope)
    return q.join(Lead,Lead.id==LeadAppointment.lead_id).where(or_(LeadAppointment.assigned_to_id==user.id,LeadAppointment.assigned_to_id.in_(ids),Lead.owner_id.in_(ids),Lead.created_by_id.in_(ids)))
def can_view_appointment(db,user,item): return user.is_superuser or item.assigned_to_id==user.id or can_view_lead(db,user,item.lead)
def can_update_appointment(db,user,item,complete=False):
    if user.is_superuser:return True
    scope=_scope(user,"lead_appointments.complete" if complete else "lead_appointments.update")
    return bool(scope and item.assigned_to_id in _accessible_ids(db,user,scope) and can_view_appointment(db,user,item))
def _assignee(db,actor,lead,requested):
    target=get_user_by_id(db,requested or lead.owner_id or actor.id)
    if not target or target.status!="active":raise HTTPException(400,"Người phụ trách lịch hẹn không hợp lệ")
    ps=permissions(actor)
    if actor.is_superuser or "lead_appointments.update.all" in ps or "leads.assign.all" in ps:return target
    scope="team" if ({"lead_appointments.update.team","leads.assign.team"}&ps) else "own"
    if target.id not in _accessible_ids(db,actor,scope):raise HTTPException(400,"Người phụ trách lịch hẹn không hợp lệ")
    return target
def _validate(start,end,kind=None):
    if end and end<=start:raise HTTPException(400,"Thời gian kết thúc phải sau thời gian bắt đầu")
    if kind and kind not in APPOINTMENT_TYPES:raise HTTPException(400,"Loại lịch hẹn không hợp lệ")
def serialize_appointment(item):
    return {"id":item.id,"lead":lead_dict(item.lead),"lead_id":item.lead_id,"title":item.title,"description":item.description,"appointment_type":item.appointment_type,"status":item.status,"start_at":item.start_at,"end_at":item.end_at,"location":item.location,"meeting_link":item.meeting_link,"assigned_to":user_dict(item.assigned_to),"assigned_to_id":item.assigned_to_id,"created_by":user_dict(item.created_by),"completed_by":user_dict(item.completed_by),"completed_at":item.completed_at,"result_note":item.result_note,"created_at":item.created_at,"updated_at":item.updated_at,"is_overdue":item.status in {"scheduled","rescheduled"} and item.start_at<now()}
def list_appointments(db,user,page=1,page_size=20,**filters):
    q=_view_query(db,user,_base())
    for key in ("status","appointment_type","assigned_to_id","lead_id"):
        if filters.get(key) is not None:q=q.where(getattr(LeadAppointment,key)==filters[key])
    if filters.get("start_from"):q=q.where(LeadAppointment.start_at>=filters["start_from"])
    if filters.get("start_to"):q=q.where(LeadAppointment.start_at<=filters["start_to"])
    start=datetime.combine(date.today(),time.min,tzinfo=timezone.utc)
    if filters.get("today"):q=q.where(LeadAppointment.start_at>=start,LeadAppointment.start_at<start+timedelta(days=1))
    if filters.get("upcoming"):q=q.where(LeadAppointment.status.in_({"scheduled","rescheduled"}),LeadAppointment.start_at>=now(),LeadAppointment.start_at<now()+timedelta(days=7))
    total=db.scalar(select(func.count()).select_from(q.order_by(None).subquery())) or 0
    items=list(db.scalars(q.order_by(LeadAppointment.start_at).offset((page-1)*page_size).limit(page_size)).unique())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_appointment(db,user,item_id):
    item=db.scalar(_base().where(LeadAppointment.id==item_id))
    if not item:raise HTTPException(404,"Không tìm thấy lịch hẹn")
    if not can_view_appointment(db,user,item):raise HTTPException(403,"Bạn không có quyền truy cập lịch hẹn này")
    return item
def _follow_up(lead,value):
    if value>now() and (not lead.next_follow_up_at or value<lead.next_follow_up_at):lead.next_follow_up_at=value
def create_appointment(db,payload,actor):
    lead=get_lead_by_id(db,payload.lead_id)
    if not lead:raise HTTPException(404,"Không tìm thấy lead")
    if not can_update_lead(db,actor,lead):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    target=_assignee(db,actor,lead,payload.assigned_to_id); data=payload.model_dump(); data["assigned_to_id"]=target.id
    item=LeadAppointment(**data,created_by_id=actor.id); db.add(item); _follow_up(lead,item.start_at)
    create_activity_record(db,lead=lead,actor=actor,activity_type="meeting",title="Tạo lịch hẹn",content=f"{item.title} · {item.start_at.isoformat()}")
    write_audit_log(db,action="lead_appointments.create",user_id=actor.id,entity_type="lead_appointments",entity_id=str(item.id),after_data={"title":item.title})
    db.commit(); return get_appointment(db,actor,item.id)
def update_appointment(db,item_id,payload,actor):
    item=get_appointment(db,actor,item_id)
    if not can_update_appointment(db,actor,item):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    data=payload.model_dump(exclude_unset=True)
    if "assigned_to_id" in data:data["assigned_to_id"]=_assignee(db,actor,item.lead,data["assigned_to_id"]).id
    _validate(data.get("start_at",item.start_at),data.get("end_at",item.end_at),data.get("appointment_type"))
    for k,v in data.items():setattr(item,k,v)
    _follow_up(item.lead,item.start_at); write_audit_log(db,action="lead_appointments.update",user_id=actor.id,entity_type="lead_appointments",entity_id=str(item.id),after_data={k:str(v) if v is not None else None for k,v in data.items()})
    db.commit(); return get_appointment(db,actor,item.id)
def update_appointment_status(db,item_id,payload,actor):
    item=get_appointment(db,actor,item_id)
    if payload.status not in APPOINTMENT_STATUSES:raise HTTPException(400,"Trạng thái lịch hẹn không hợp lệ")
    if not can_update_appointment(db,actor,item,True):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    old=f"{item.start_at.isoformat()} - {item.end_at.isoformat() if item.end_at else ''}"; title={"completed":"Hoàn thành lịch hẹn","cancelled":"Hủy lịch hẹn","no_show":"Khách không đến","rescheduled":"Dời lịch hẹn"}.get(payload.status)
    if payload.status=="rescheduled":
        if not payload.rescheduled_start_at:raise HTTPException(400,"Thời gian bắt đầu là bắt buộc")
        _validate(payload.rescheduled_start_at,payload.rescheduled_end_at); item.start_at=payload.rescheduled_start_at; item.end_at=payload.rescheduled_end_at; _follow_up(item.lead,item.start_at)
    item.status=payload.status; item.result_note=payload.result_note
    if payload.status=="completed":item.completed_at=now(); item.completed_by_id=actor.id; item.lead.last_contact_at=now()
    elif payload.status!="completed":item.completed_at=None; item.completed_by_id=None
    if title:
        new=f"{item.start_at.isoformat()} - {item.end_at.isoformat() if item.end_at else ''}"
        create_activity_record(db,lead=item.lead,actor=actor,activity_type="meeting",title=title,content=payload.result_note or item.title,old_value=old if payload.status=="rescheduled" else None,new_value=new if payload.status=="rescheduled" else None)
    action={"completed":"complete","cancelled":"cancel","rescheduled":"reschedule"}.get(payload.status,"update")
    write_audit_log(db,action=f"lead_appointments.{action}",user_id=actor.id,entity_type="lead_appointments",entity_id=str(item.id),after_data={"status":payload.status})
    db.commit(); return get_appointment(db,actor,item.id)
def complete_appointment(db,i,n,a):return update_appointment_status(db,i,LeadAppointmentStatusUpdate(status="completed",result_note=n),a)
def cancel_appointment(db,i,n,a):return update_appointment_status(db,i,LeadAppointmentStatusUpdate(status="cancelled",result_note=n),a)
def reschedule_appointment(db,i,s,e,n,a):return update_appointment_status(db,i,LeadAppointmentStatusUpdate(status="rescheduled",result_note=n,rescheduled_start_at=s,rescheduled_end_at=e),a)
def delete_appointment(db,item_id,actor):
    item=get_appointment(db,actor,item_id)
    if not (actor.is_superuser or "lead_appointments.delete" in permissions(actor)):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    item.deleted_at=now(); write_audit_log(db,action="lead_appointments.delete",user_id=actor.id,entity_type="lead_appointments",entity_id=str(item.id)); db.commit()
def list_today_appointments(db,user,**kw):return list_appointments(db,user,today=True,**kw)
def list_upcoming_appointments(db,user,**kw):return list_appointments(db,user,upcoming=True,**kw)
