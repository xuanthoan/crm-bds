from datetime import date, datetime, time, timedelta, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.lead_task import LeadTask
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.lead_task import LeadTaskCreate, LeadTaskStatusUpdate, LeadTaskUpdate
from app.services.audit_service import write_audit_log
from app.services.lead_activity_service import create_activity_record
from app.services.lead_service import apply_view_scope, can_update_lead, can_view_lead, get_lead_by_id
from app.services.organization_service import list_eligible_lead_assignees

TASK_TYPES={"call","zalo","email","meeting","follow_up","document","other"}; TASK_STATUSES={"pending","in_progress","completed","cancelled"}; PRIORITIES={"low","medium","high","urgent"}; ACTIVE={"pending","in_progress"}
def _permissions(u): return set(get_user_permissions(u))
def _summary_user(u): return {"id":u.id,"full_name":u.full_name,"email":u.email} if u else None
def _lead_summary(l): return {"id":l.id,"code":l.code,"full_name":l.full_name,"phone_primary":l.phone_primary}
def is_overdue(t, now=None): return t.status in ACTIVE and t.due_at < (now or datetime.now(timezone.utc))
def serialize_task(t):
    now=datetime.now(timezone.utc); overdue=is_overdue(t,now); hours=max(0,int((now-t.due_at).total_seconds()//3600)) if overdue else 0
    return {"id":t.id,"lead":_lead_summary(t.lead),"title":t.title,"description":t.description,"task_type":t.task_type,"status":t.status,"priority":t.priority,"due_at":t.due_at,"assigned_to":_summary_user(t.assigned_to),"created_by":_summary_user(t.created_by),"completed_by":_summary_user(t.completed_by),"completed_at":t.completed_at,"cancelled_at":t.cancelled_at,"reminder_enabled":t.reminder_enabled,"reminder_at":t.reminder_at,"result_note":t.result_note,"created_at":t.created_at,"updated_at":t.updated_at,"is_overdue":overdue,"hours_overdue":hours,"days_overdue":hours//24}
def _scope_query(db,user):
    lead_ids=apply_view_scope(db,select(Lead.id).where(Lead.deleted_at.is_(None)),user)
    return or_(LeadTask.assigned_to_id==user.id,LeadTask.lead_id.in_(lead_ids))
def _validate(payload,due=None,reminder=None):
    if getattr(payload,"task_type",None) and payload.task_type not in TASK_TYPES: raise HTTPException(400,"Loại công việc không hợp lệ")
    if getattr(payload,"priority",None) and payload.priority not in PRIORITIES: raise HTTPException(400,"Mức độ ưu tiên không hợp lệ")
    if reminder and due and reminder>due: raise HTTPException(400,"Thời gian nhắc phải trước hoặc bằng hạn xử lý")
def _assignee(db,user,target):
    if target==user.id: return user
    try: eligible=list_eligible_lead_assignees(db,user)
    except HTTPException: raise HTTPException(400,"Người phụ trách công việc không hợp lệ")
    found=next((u for u in eligible if u.id==target),None)
    if not found: raise HTTPException(400,"Người phụ trách công việc không hợp lệ")
    return found
def _require_view_permission(user):
    if not user.is_superuser and not (_permissions(user) & {"lead_tasks.view.own","lead_tasks.view.team","lead_tasks.view.all"}): raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
def list_tasks(db,user,*,page=1,page_size=20,search=None,task_status=None,task_type=None,priority=None,assigned_to_id=None,lead_id=None,due_from=None,due_to=None,overdue=False,today=False):
    _require_view_permission(user); q=select(LeadTask).where(LeadTask.deleted_at.is_(None),_scope_query(db,user)); conditions=[]; now=datetime.now(timezone.utc)
    if search:
        term=f"%{search.strip()}%";conditions.append(or_(LeadTask.title.ilike(term),LeadTask.lead.has(or_(Lead.code.ilike(term),Lead.full_name.ilike(term),Lead.phone_primary.ilike(term)))))
    if task_status: conditions.append(LeadTask.status==task_status)
    if task_type: conditions.append(LeadTask.task_type==task_type)
    if priority: conditions.append(LeadTask.priority==priority)
    if assigned_to_id: conditions.append(LeadTask.assigned_to_id==assigned_to_id)
    if lead_id: conditions.append(LeadTask.lead_id==lead_id)
    if due_from: conditions.append(LeadTask.due_at>=due_from)
    if due_to: conditions.append(LeadTask.due_at<=due_to)
    if overdue: conditions += [LeadTask.status.in_(ACTIVE),LeadTask.due_at<now]
    if today:
        start=datetime.combine(now.date(),time.min,tzinfo=timezone.utc); conditions += [LeadTask.due_at>=start,LeadTask.due_at<start+timedelta(days=1)]
    q=q.where(*conditions); total=db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items=list(db.scalars(q.order_by(LeadTask.due_at).offset((page-1)*page_size).limit(page_size)).unique())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_task(db,task_id): return db.scalar(select(LeadTask).where(LeadTask.id==task_id,LeadTask.deleted_at.is_(None)))
def require_task_view(db,t,user):
    _require_view_permission(user)
    if t.assigned_to_id!=user.id and not can_view_lead(db,user,t.lead): raise HTTPException(403,"Bạn không có quyền truy cập công việc này")
def require_task_update(db,t,user,complete=False):
    p=_permissions(user); prefix="lead_tasks.complete" if complete else "lead_tasks.update"
    if user.is_superuser or f"{prefix}.all" in p: return
    if t.assigned_to_id==user.id and f"{prefix}.own" in p: return
    if f"{prefix}.team" in p and can_update_lead(db,user,t.lead): return
    raise HTTPException(403,"Bạn không có quyền cập nhật công việc này")
def create_task(db,payload,actor):
    if "lead_tasks.create" not in _permissions(actor) and not actor.is_superuser: raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    lead=get_lead_by_id(db,payload.lead_id)
    if not lead: raise HTTPException(404,"Không tìm thấy lead")
    if not can_update_lead(db,actor,lead): raise HTTPException(403,"Bạn không có quyền cập nhật công việc này")
    _validate(payload,payload.due_at,payload.reminder_at); target=payload.assigned_to_id or lead.owner_id or actor.id; _assignee(db,actor,target)
    task=LeadTask(**payload.model_dump(exclude={"assigned_to_id"}),assigned_to_id=target,created_by_id=actor.id,status="pending"); db.add(task); db.flush()
    if payload.due_at>datetime.now(timezone.utc) and (not lead.next_follow_up_at or payload.due_at<lead.next_follow_up_at): lead.next_follow_up_at=payload.due_at
    create_activity_record(db,lead=lead,actor=actor,activity_type="follow_up",title="Tạo công việc",content=f"{task.title} - {task.due_at.isoformat()}")
    write_audit_log(db,action="lead_tasks.create",user_id=actor.id,entity_type="lead_task",entity_id=str(task.id),after_data={"title":task.title,"due_at":task.due_at.isoformat()}); db.commit(); db.refresh(task); return task
def update_task(db,t,payload,actor):
    require_task_update(db,t,actor); data=payload.model_dump(exclude_unset=True); due=data.get("due_at",t.due_at); reminder=data.get("reminder_at",t.reminder_at); _validate(payload,due,reminder)
    if data.get("assigned_to_id"): _assignee(db,actor,data["assigned_to_id"])
    before={"title":t.title,"due_at":t.due_at.isoformat()}; [setattr(t,k,v) for k,v in data.items()]
    if due>datetime.now(timezone.utc) and (not t.lead.next_follow_up_at or due<t.lead.next_follow_up_at): t.lead.next_follow_up_at=due
    write_audit_log(db,action="lead_tasks.update",user_id=actor.id,entity_type="lead_task",entity_id=str(t.id),before_data=before,after_data={"title":t.title,"due_at":t.due_at.isoformat()}); db.commit(); db.refresh(t); return t
def update_task_status(db,t,payload,actor):
    require_task_update(db,t,actor,True)
    if payload.status not in TASK_STATUSES: raise HTTPException(400,"Trạng thái công việc không hợp lệ")
    now=datetime.now(timezone.utc); t.status=payload.status; t.result_note=payload.result_note
    if payload.status=="completed":
        t.completed_at=now;t.completed_by_id=actor.id;t.cancelled_at=None; title="Hoàn thành công việc"; activity="follow_up"; action="lead_tasks.complete"
        if t.task_type in {"call","zalo","meeting"}: t.lead.last_contact_at=now
    elif payload.status=="cancelled": t.cancelled_at=now;t.completed_at=None;t.completed_by_id=None;title="Hủy công việc";activity="note";action="lead_tasks.cancel"
    else: t.completed_at=None;t.completed_by_id=None;t.cancelled_at=None;title="Cập nhật công việc";activity="follow_up";action="lead_tasks.update"
    create_activity_record(db,lead=t.lead,actor=actor,activity_type=activity,title=title,content=payload.result_note or t.title)
    write_audit_log(db,action=action,user_id=actor.id,entity_type="lead_task",entity_id=str(t.id),after_data={"status":t.status,"result_note":t.result_note});db.commit();db.refresh(t);return t
def delete_task(db,t,actor):
    if not actor.is_superuser and "lead_tasks.delete" not in _permissions(actor): raise HTTPException(403,"Bạn không có quyền thực hiện thao tác này")
    require_task_update(db,t,actor);t.deleted_at=datetime.now(timezone.utc);write_audit_log(db,action="lead_tasks.delete",user_id=actor.id,entity_type="lead_task",entity_id=str(t.id));db.commit()
