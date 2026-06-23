from datetime import datetime, time, timedelta, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.task_activity import TaskActivity
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.services.notification_service import create_task_notification

STATUSES={"open","in_progress","done","cancelled"}; PRIORITIES={"low","medium","high","urgent"}; TYPES={"call_customer","follow_up","booking_expiry","contract_signing","payment_due","general"}

def _now(): return datetime.now(timezone.utc)
def _next_code(db):
    codes=db.scalars(select(Task.task_code).where(Task.task_code.like("TASK-%")))
    nums=[int(c.split("-")[-1]) for c in codes if c.split("-")[-1].isdigit()]
    return f"TASK-{max(nums,default=0)+1:06d}"
def _act(db,task,typ,title=None,content=None,old=None,new=None,actor=None):
    db.add(TaskActivity(task_id=task.id,activity_type=typ,title=title or typ,content=content,old_value=old,new_value=new,actor_id=getattr(actor,"id",None)))
def _has_view_all(user): return user.is_superuser or "tasks.view_all" in set(get_user_permissions(user)) or "tasks.view.all" in set(get_user_permissions(user))
def _can_access(user,task): return _has_view_all(user) or task.assigned_user_id==user.id or task.created_by_id==user.id
def _get(db,id):
    t=db.scalar(select(Task).where(Task.id==id,Task.deleted_at.is_(None)))
    if not t: raise HTTPException(404,"Công việc không tồn tại")
    return t

def _validate_assignee(db, actor: User, assigned_user_id):
    # Manual tasks default to the current user. Assigning someone else requires
    # the existing tasks.assign permission (superusers are always allowed).
    assignee_id = assigned_user_id or actor.id
    user = db.scalar(select(User).where(User.id == assignee_id, User.status == "active", User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(400, "Người phụ trách không tồn tại.")
    if assignee_id != actor.id and not (actor.is_superuser or "tasks.assign" in set(get_user_permissions(actor))):
        raise HTTPException(403, "Bạn không có quyền giao công việc cho người này.")
    return assignee_id

def _validate(data):
    if "status" in data and data["status"] and data["status"] not in STATUSES: raise HTTPException(400,"Trạng thái công việc không hợp lệ")
    if "priority" in data and data["priority"] and data["priority"] not in PRIORITIES: raise HTTPException(400,"Độ ưu tiên không hợp lệ")
    if "task_type" in data and data["task_type"] and data["task_type"] not in TYPES: raise HTTPException(400,"Loại công việc không hợp lệ")

def serialize_task(t,detail=False):
    d={"id":t.id,"task_code":t.task_code,"title":t.title,"description":t.description,"task_type":t.task_type,"priority":t.priority,"status":t.status,"due_at":t.due_at,"completed_at":t.completed_at,"cancelled_at":t.cancelled_at,"assigned_user_id":t.assigned_user_id,"assigned_user":{"id":t.assigned_user.id,"full_name":t.assigned_user.full_name,"email":t.assigned_user.email} if t.assigned_user else None,"created_by_id":t.created_by_id,"related_customer_id":t.related_customer_id,"related_lead_id":t.related_lead_id,"related_booking_id":t.related_booking_id,"related_deal_id":t.related_deal_id,"related_contract_id":t.related_contract_id,"related_property_unit_id":t.related_property_unit_id,"auto_generated":t.auto_generated,"source_event":t.source_event,"note":t.note,"created_at":t.created_at,"updated_at":t.updated_at}
    if detail: d["activities"]=[{"id":a.id,"activity_type":a.activity_type,"title":a.title,"content":a.content,"old_value":a.old_value,"new_value":a.new_value,"actor":{"id":a.actor.id,"full_name":a.actor.full_name} if a.actor else None,"created_at":a.created_at} for a in t.activities]
    return d

def list_tasks(db,actor,page=1,page_size=20,**f):
    cond=[Task.deleted_at.is_(None)]
    if not _has_view_all(actor): cond.append(or_(Task.assigned_user_id==actor.id,Task.created_by_id==actor.id))
    for name,col in (("status",Task.status),("priority",Task.priority),("task_type",Task.task_type),("assigned_user_id",Task.assigned_user_id),("related_customer_id",Task.related_customer_id),("related_booking_id",Task.related_booking_id),("related_deal_id",Task.related_deal_id),("related_contract_id",Task.related_contract_id)):
        if f.get(name) is not None: cond.append(col==f[name])
    if f.get("q"): cond.append(or_(Task.task_code.ilike(f"%{f['q']}%"),Task.title.ilike(f"%{f['q']}%")))
    if f.get("due_from"): cond.append(Task.due_at>=f["due_from"])
    if f.get("due_to"): cond.append(Task.due_at<=f["due_to"])
    total=db.scalar(select(func.count(Task.id)).where(*cond)) or 0
    items=list(db.scalars(select(Task).where(*cond).order_by(Task.due_at.asc().nullslast(),Task.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}

def get_task_detail(db,id,actor):
    t=_get(db,id)
    if not _can_access(actor,t): raise HTTPException(403,"Bạn không có quyền xem công việc này")
    return t

def create_task(db,payload,actor,auto=False,source_event=None,notify_type="task_assigned"):
    data=payload if isinstance(payload,dict) else payload.model_dump(exclude_unset=True); _validate(data)
    if not data.get("title"): raise HTTPException(400,"Tiêu đề là bắt buộc")
    data.pop("source_event", None)
    if not auto:
        data["assigned_user_id"] = _validate_assignee(db, actor, data.get("assigned_user_id"))
    t=Task(**data,task_code=_next_code(db),created_by_id=getattr(actor,"id",None),auto_generated=auto,source_event=source_event)
    db.add(t); db.flush(); _act(db,t,"created","Tạo công việc",actor=actor); create_task_notification(db,t,notification_type=notify_type); db.commit(); db.refresh(t); return t

def update_task(db,id,payload,actor):
    t=get_task_detail(db,id,actor); data=payload.model_dump(exclude_unset=True); _validate(data); old_assignee=t.assigned_user_id
    if "assigned_user_id" in data:
        data["assigned_user_id"] = _validate_assignee(db, actor, data.get("assigned_user_id"))
    for k,v in data.items(): setattr(t,k,v)
    if t.status=="done": t.completed_at=t.completed_at or _now()
    elif t.status=="cancelled": t.cancelled_at=t.cancelled_at or _now()
    if "assigned_user_id" in data and data["assigned_user_id"] != old_assignee: _act(db,t,"assigned","Giao công việc",old=str(old_assignee),new=str(data["assigned_user_id"]),actor=actor); create_task_notification(db,t,"Bạn được giao công việc")
    db.commit(); db.refresh(t); return t

def change_task_status(db,id,status,note,actor):
    t=get_task_detail(db,id,actor); _validate({"status":status})
    if t.status=="cancelled" and status=="done": raise HTTPException(409,"Không thể hoàn thành công việc đã hủy")
    if t.status=="done" and status=="cancelled": raise HTTPException(409,"Không thể hủy công việc đã hoàn thành")
    old=t.status; t.status=status; t.completed_at=_now() if status=="done" else None; t.cancelled_at=_now() if status=="cancelled" else None
    _act(db,t,"completed" if status=="done" else "cancelled" if status=="cancelled" else "status_changed","Đổi trạng thái công việc",note,old,status,actor); db.commit(); db.refresh(t); return t

def complete_task(db,id,note,actor): return change_task_status(db,id,"done",note,actor)
def cancel_task(db,id,reason,actor): return change_task_status(db,id,"cancelled",reason,actor)
def add_task_note(db,id,note,actor):
    t=get_task_detail(db,id,actor); _act(db,t,"note_added","Thêm ghi chú",note,actor=actor); db.commit(); db.refresh(t); return t

def create_auto_task_if_not_exists(db,actor=None,**kw):
    cond=[Task.deleted_at.is_(None),Task.status.in_(["open","in_progress"]),Task.source_event==kw.get("source_event"),Task.task_type==kw.get("task_type"),Task.assigned_user_id==kw.get("assigned_user_id")]
    if kw.get("related_booking_id"): cond.append(Task.related_booking_id==kw["related_booking_id"])
    if kw.get("related_contract_id"): cond.append(Task.related_contract_id==kw["related_contract_id"])
    existing=db.scalar(select(Task).where(*cond).limit(1))
    if existing: return existing
    return create_task(db,kw,actor,auto=True,source_event=kw.get("source_event"),notify_type="contract_payment_due" if kw.get("task_type")=="payment_due" else "task_assigned")

def get_today_tasks(db,actor):
    start=datetime.combine(_now().date(),time.min,tzinfo=timezone.utc); end=start+timedelta(days=1)
    items=list_tasks(db,actor,page=1,page_size=200,due_to=end)[0]
    return [t for t in items if t.status in {"open","in_progress"}]
def get_overdue_tasks(db,actor):
    items=list_tasks(db,actor,page=1,page_size=200,due_to=_now())[0]
    return [t for t in items if t.status in {"open","in_progress"}]

def auto_task_for_booking_created(db,booking,actor):
    due=booking.reservation_expires_at-timedelta(days=1) if booking.reservation_expires_at else None
    return create_auto_task_if_not_exists(db,actor,title=f"Theo dõi booking {booking.booking_code}",task_type="follow_up",priority="medium",assigned_user_id=booking.assigned_user_id,related_booking_id=booking.id,related_customer_id=booking.customer_id,related_property_unit_id=booking.property_unit_id,due_at=due,source_event="booking_created")
def auto_task_for_booking_deposited(db,booking,actor):
    return create_auto_task_if_not_exists(db,actor,title=f"Chuẩn bị ký hợp đồng cho booking {booking.booking_code}",task_type="contract_signing",priority="high",assigned_user_id=booking.assigned_user_id,related_booking_id=booking.id,related_customer_id=booking.customer_id,related_property_unit_id=booking.property_unit_id,source_event="booking_deposited")
def auto_cancel_booking_tasks(db,booking,actor):
    label={"cancelled":"hủy","refunded":"hoàn tiền","expired":"hết hạn"}.get(booking.status,booking.status); reason=f"Booking {booking.booking_code} đã {label} nên công việc được tự động hủy."
    for t in db.scalars(select(Task).where(Task.related_booking_id==booking.id,Task.deleted_at.is_(None),Task.status.in_(["open","in_progress"]),Task.task_type!="general")):
        t.status="cancelled"; t.cancelled_at=_now(); _act(db,t,"cancelled","Tự động hủy công việc",reason,actor=actor)
def auto_task_for_contract_payment(db,contract,actor):
    from app.services.contract_service import totals
    _,_,remaining=totals(contract)
    if remaining<=0: return None
    assignee=getattr(contract.deal,"owner_id",None) or actor.id
    return create_auto_task_if_not_exists(db,actor,title=f"Theo dõi thanh toán hợp đồng {contract.contract_code}",task_type="payment_due",priority="high",assigned_user_id=assignee,related_contract_id=contract.id,related_deal_id=contract.deal_id,related_booking_id=contract.booking_id,related_customer_id=contract.customer_id,related_property_unit_id=contract.property_unit_id,source_event="contract_payment_due")
def auto_complete_contract_payment_tasks(db,contract,actor):
    for t in db.scalars(select(Task).where(Task.related_contract_id==contract.id,Task.task_type=="payment_due",Task.status.in_(["open","in_progress"]),Task.deleted_at.is_(None))):
        t.status="done"; t.completed_at=_now(); _act(db,t,"completed","Tự động hoàn thành","Hợp đồng đã hoàn tất.",actor=actor)


def list_task_assignees(db, actor: User):
    query = select(User).where(User.status == "active", User.deleted_at.is_(None))
    if not (actor.is_superuser or "tasks.assign" in set(get_user_permissions(actor))):
        query = query.where(User.id == actor.id)
    return list(db.scalars(query.order_by(User.full_name)).unique())
