from datetime import date, datetime, time, timedelta, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.models.lead import Lead
from app.models.lead_task import LeadTask
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.lead_task import LeadTaskCreate, LeadTaskUpdate, LeadTaskStatusUpdate, TASK_STATUSES, TASK_TYPES, TASK_PRIORITIES
from app.services.audit_service import write_audit_log
from app.services.lead_activity_service import create_activity_record
from app.services.lead_service import can_update_lead, can_view_lead, get_lead_by_id
from app.services.user_service import get_user_by_id, user_role_code_set

ACTIVE={"pending","in_progress"}
def now(): return datetime.now(timezone.utc)
def user_dict(user): return {"id":user.id,"full_name":user.full_name,"email":user.email} if user else None
def lead_dict(lead): return {"id":lead.id,"code":lead.code,"full_name":lead.full_name,"phone_primary":lead.phone_primary}
def permissions(user): return set(get_user_permissions(user))
def _scope(user,prefix):
    ps=permissions(user)
    for value in ("all","department","team","own"):
        if f"{prefix}.{value}" in ps:return value
    return None
def _accessible_ids(db,user,scope):
    from app.services.organization_service import get_accessible_user_ids_for_lead_scope
    effective_scope = "department" if scope == "team" and "sales_manager" in user_role_code_set(user) else scope
    return get_accessible_user_ids_for_lead_scope(db,user,effective_scope)
def can_view_task(db,user,task):
    if task.assigned_to_id==user.id or can_view_lead(db,user,task.lead): return True
    return user.is_superuser
def can_update_task(db,user,task,complete=False):
    if user.is_superuser:return True
    scope=_scope(user,"lead_tasks.complete" if complete else "lead_tasks.update")
    return bool(scope and task.assigned_to_id in _accessible_ids(db,user,scope) and can_view_task(db,user,task))
def _assignee(db,actor,lead,requested):
    target=get_user_by_id(db,requested or lead.owner_id or actor.id)
    if not target or target.status!="active": raise HTTPException(400,"Người phụ trách công việc không hợp lệ")
    ps=permissions(actor)
    if actor.is_superuser or "lead_tasks.update.all" in ps or "leads.assign.all" in ps:return target
    scope="team" if ({"lead_tasks.update.team","leads.assign.team"}&ps) else "own"
    if target.id not in _accessible_ids(db,actor,scope): raise HTTPException(400,"Người phụ trách công việc không hợp lệ")
    return target
def _validate(due,reminder,task_type=None,priority=None):
    if reminder and due and reminder>due: raise HTTPException(400,"Thời gian nhắc phải trước hoặc bằng hạn xử lý")
    if task_type and task_type not in TASK_TYPES: raise HTTPException(400,"Loại công việc không hợp lệ")
    if priority and priority not in TASK_PRIORITIES: raise HTTPException(400,"Mức ưu tiên không hợp lệ")
def _base(): return select(LeadTask).options(joinedload(LeadTask.lead),joinedload(LeadTask.assigned_to),joinedload(LeadTask.created_by),joinedload(LeadTask.completed_by)).where(LeadTask.deleted_at.is_(None))
def _view_query(db,user,q):
    if user.is_superuser or "lead_tasks.view.all" in permissions(user): return q
    scope=_scope(user,"lead_tasks.view") or _scope(user,"leads.view")
    if not scope: raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    ids=_accessible_ids(db,user,scope)
    return q.join(Lead,Lead.id==LeadTask.lead_id).where(or_(LeadTask.assigned_to_id==user.id,LeadTask.assigned_to_id.in_(ids),Lead.owner_id.in_(ids),Lead.created_by_id.in_(ids)))
def serialize_task(task):
    overdue=task.status in ACTIVE and task.due_at<now()
    hours=max(0,int((now()-task.due_at).total_seconds()//3600)) if overdue else 0
    return {"id":task.id,"lead":lead_dict(task.lead),"lead_id":task.lead_id,"title":task.title,"description":task.description,"task_type":task.task_type,"status":task.status,"priority":task.priority,"due_at":task.due_at,"assigned_to":user_dict(task.assigned_to),"assigned_to_id":task.assigned_to_id,"created_by":user_dict(task.created_by),"completed_by":user_dict(task.completed_by),"completed_at":task.completed_at,"cancelled_at":task.cancelled_at,"reminder_enabled":task.reminder_enabled,"reminder_at":task.reminder_at,"result_note":task.result_note,"created_at":task.created_at,"updated_at":task.updated_at,"is_overdue":overdue,"hours_overdue":hours,"days_overdue":hours//24}
def list_tasks(db,user,page=1,page_size=20,**filters):
    q=_view_query(db,user,_base())
    for key in ("status","task_type","priority","assigned_to_id","lead_id"):
        if filters.get(key) is not None:q=q.where(getattr(LeadTask,key)==filters[key])
    if filters.get("search"):
        term=f"%{filters['search'].strip()}%"; q=q.where(or_(LeadTask.title.ilike(term),LeadTask.lead.has(Lead.full_name.ilike(term)),LeadTask.lead.has(Lead.phone_primary.ilike(term)),LeadTask.lead.has(Lead.code.ilike(term))))
    if filters.get("due_from"):q=q.where(LeadTask.due_at>=filters["due_from"])
    if filters.get("due_to"):q=q.where(LeadTask.due_at<=filters["due_to"])
    if filters.get("overdue"):q=q.where(LeadTask.status.in_(ACTIVE),LeadTask.due_at<now())
    if filters.get("today"):
        start=datetime.combine(date.today(),time.min,tzinfo=timezone.utc); q=q.where(LeadTask.due_at>=start,LeadTask.due_at<start+timedelta(days=1))
    total=db.scalar(select(func.count()).select_from(q.order_by(None).subquery())) or 0
    items=list(db.scalars(q.order_by(LeadTask.due_at).offset((page-1)*page_size).limit(page_size)).unique())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_task(db,user,task_id):
    task=db.scalar(_base().where(LeadTask.id==task_id))
    if not task:raise HTTPException(404,"Không tìm thấy công việc")
    if not can_view_task(db,user,task):raise HTTPException(403,"Bạn không có quyền truy cập công việc này")
    return task
def _follow_up(lead,value):
    if value>now() and (not lead.next_follow_up_at or value<lead.next_follow_up_at):lead.next_follow_up_at=value
def create_task(db,payload,actor):
    lead=get_lead_by_id(db,payload.lead_id)
    if not lead:raise HTTPException(404,"Không tìm thấy lead")
    if not can_update_lead(db,actor,lead):raise HTTPException(403,"Bạn không có quyền cập nhật công việc này")
    target=_assignee(db,actor,lead,payload.assigned_to_id); data=payload.model_dump(); data["assigned_to_id"]=target.id
    task=LeadTask(**data,created_by_id=actor.id); db.add(task); _follow_up(lead,task.due_at)
    create_activity_record(db,lead=lead,actor=actor,activity_type="follow_up",title="Tạo công việc",content=f"{task.title} · {task.due_at.isoformat()}")
    write_audit_log(db,action="lead_tasks.create",user_id=actor.id,entity_type="lead_tasks",entity_id=str(task.id),after_data={"title":task.title})
    db.commit(); return get_task(db,actor,task.id)
def update_task(db,task_id,payload,actor):
    task=get_task(db,actor,task_id)
    if not can_update_task(db,actor,task):raise HTTPException(403,"Bạn không có quyền cập nhật công việc này")
    data=payload.model_dump(exclude_unset=True)
    if "assigned_to_id" in data:data["assigned_to_id"]=_assignee(db,actor,task.lead,data["assigned_to_id"]).id
    due=data.get("due_at",task.due_at); reminder=data.get("reminder_at",task.reminder_at); _validate(due,reminder,data.get("task_type"),data.get("priority"))
    for k,v in data.items():setattr(task,k,v)
    _follow_up(task.lead,task.due_at); write_audit_log(db,action="lead_tasks.update",user_id=actor.id,entity_type="lead_tasks",entity_id=str(task.id),after_data={k:str(v) if v is not None else None for k,v in data.items()})
    db.commit(); return get_task(db,actor,task.id)
def update_task_status(db,task_id,payload,actor):
    task=get_task(db,actor,task_id)
    if payload.status not in TASK_STATUSES:raise HTTPException(400,"Trạng thái công việc không hợp lệ")
    if not can_update_task(db,actor,task,True):raise HTTPException(403,"Bạn không có quyền cập nhật công việc này")
    task.status=payload.status; task.result_note=payload.result_note
    stamp=now(); title=None; activity_type="follow_up"
    if payload.status=="completed": task.completed_at=stamp; task.completed_by_id=actor.id; task.cancelled_at=None; title="Hoàn thành công việc"; task.lead.last_contact_at=stamp if task.task_type in {"call","zalo","meeting"} else task.lead.last_contact_at
    elif payload.status=="cancelled": task.cancelled_at=stamp; task.completed_at=None; task.completed_by_id=None; title="Hủy công việc"; activity_type="note"
    else: task.completed_at=None; task.completed_by_id=None; task.cancelled_at=None
    if title:create_activity_record(db,lead=task.lead,actor=actor,activity_type=activity_type,title=title,content=payload.result_note or task.title)
    action="complete" if payload.status=="completed" else "cancel" if payload.status=="cancelled" else "update"
    write_audit_log(db,action=f"lead_tasks.{action}",user_id=actor.id,entity_type="lead_tasks",entity_id=str(task.id),after_data={"status":payload.status,"result_note":payload.result_note})
    db.commit(); return get_task(db,actor,task.id)
def complete_task(db,task_id,note,actor): return update_task_status(db,task_id,LeadTaskStatusUpdate(status="completed",result_note=note),actor)
def cancel_task(db,task_id,note,actor): return update_task_status(db,task_id,LeadTaskStatusUpdate(status="cancelled",result_note=note),actor)
def delete_task(db,task_id,actor):
    task=get_task(db,actor,task_id)
    if not (actor.is_superuser or "lead_tasks.delete" in permissions(actor)):raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    task.deleted_at=now(); write_audit_log(db,action="lead_tasks.delete",user_id=actor.id,entity_type="lead_tasks",entity_id=str(task.id)); db.commit()
def list_today_tasks(db,user,**kw): return list_tasks(db,user,today=True,**kw)
def list_overdue_tasks(db,user,**kw): return list_tasks(db,user,overdue=True,**kw)
def list_my_tasks(db,user,**kw): return list_tasks(db,user,assigned_to_id=user.id,**kw)
def list_team_tasks(db,user,**kw): return list_tasks(db,user,**kw)
