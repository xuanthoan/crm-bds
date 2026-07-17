from datetime import datetime, time, timedelta, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, lazyload, load_only, selectinload
from app.models.booking import Booking
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.property_unit import PropertyUnit
from app.models.task import Task, TaskAssignee, TaskWatcher
from app.models.task_activity import TaskActivity
from app.models.task_collaboration import TaskComment, TaskRelatedLink
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.services.notification_service import create_notification, create_task_notification
from app.services.drilldown_scope import mine_only

STATUSES={"open","in_progress","done","cancelled"}; PRIORITIES={"low","medium","high","urgent"}; TYPES={"call_customer","follow_up","booking_expiry","contract_signing","payment_due","general"}


def _user_brief(u):
    return {"id": u.id, "full_name": u.full_name, "email": u.email} if u else None

def _user_label(u):
    return (getattr(u, "full_name", None) or getattr(u, "email", None) or getattr(u, "username", None) or "Không xác định") if u else "Không xác định"

def _user_labels_by_ids(db, ids):
    ids=_ids(list(ids or []))
    if not ids:
        return {}
    users=list(db.scalars(select(User).where(User.id.in_(ids))))
    return {u.id: _user_label(u) for u in users}

def _labels_for_ids(db, ids):
    labels=_user_labels_by_ids(db, ids)
    return [labels.get(uid, "Không xác định") for uid in _ids(list(ids or []))]

def _collab_change_content(db, old, new):
    added=[x for x in _ids(list(new)) if x not in old]
    removed=[x for x in _ids(list(old)) if x not in new]
    lines=[]
    if added:
        lines.append("Đã thêm: " + ", ".join(_labels_for_ids(db, added)))
    if removed:
        lines.append("Đã bỏ: " + ", ".join(_labels_for_ids(db, removed)))
    return "\n".join(lines) or None

def _join_labels(db, ids):
    return ", ".join(_labels_for_ids(db, ids))

def _ids(values):
    result=[]
    for value in values or []:
        if value and value not in result:
            result.append(value)
    return result

def _collab_users(task, rel):
    rows = getattr(task, rel, []) or []
    return [_user_brief(row.user) for row in rows if row.user and getattr(row.user, "deleted_at", None) is None]

def _collab_ids(task, rel):
    return [row.user_id for row in (getattr(task, rel, []) or [])]

def _validate_user_ids(db, ids, label):
    ids=_ids(ids)
    if not ids:
        return []
    found=set(db.scalars(select(User.id).where(User.id.in_(ids), User.status == "active", User.deleted_at.is_(None))))
    missing=[str(i) for i in ids if i not in found]
    if missing:
        raise HTTPException(400, f"{label} không tồn tại hoặc không hoạt động.")
    return ids

def _sync_collaboration(db, task, *, assignee_ids=None, watcher_ids=None, actor=None, reject_missing_primary=False):
    primary_id = task.assigned_user_id
    if primary_id and assignee_ids is None and not task.task_assignees:
        assignee_ids = [primary_id]
    if assignee_ids is not None:
        assignee_ids = _validate_user_ids(db, assignee_ids, "Người cùng thực hiện")
        if primary_id and primary_id not in assignee_ids:
            if reject_missing_primary:
                raise HTTPException(400, "Người phụ trách chính phải nằm trong danh sách người cùng thực hiện.")
            assignee_ids = [primary_id, *assignee_ids]
        old=set(_collab_ids(task, "task_assignees")); new=set(assignee_ids)
        for row in list(task.task_assignees):
            if row.user_id not in new:
                db.delete(row)
        for uid in assignee_ids:
            if uid not in old:
                task.task_assignees.append(TaskAssignee(user_id=uid, created_by_id=getattr(actor, "id", None)))
        if old != new:
            _act(db, task, "assignees_changed", "Cập nhật người cùng thực hiện", content=_collab_change_content(db, old, new), old=_join_labels(db, old), new=_join_labels(db, new), actor=actor)
    current_assignee_ids=set(assignee_ids if assignee_ids is not None else _collab_ids(task, "task_assignees"))
    if watcher_ids is not None:
        watcher_ids = [uid for uid in _validate_user_ids(db, watcher_ids, "Người quan sát") if uid not in current_assignee_ids]
    elif getattr(actor, "id", None) and actor.id not in current_assignee_ids and not any(r.user_id == actor.id for r in task.task_watchers):
        watcher_ids = [*_collab_ids(task, "task_watchers"), actor.id]
    if watcher_ids is not None:
        watcher_ids = [uid for uid in _ids(watcher_ids) if uid not in current_assignee_ids]
        old=set(_collab_ids(task, "task_watchers")); new=set(watcher_ids)
        for row in list(task.task_watchers):
            if row.user_id not in new:
                db.delete(row)
        for uid in watcher_ids:
            if uid not in old:
                task.task_watchers.append(TaskWatcher(user_id=uid, created_by_id=getattr(actor, "id", None)))
        if old != new:
            _act(db, task, "watchers_changed", "Cập nhật người quan sát", content=_collab_change_content(db, old, new), old=_join_labels(db, old), new=_join_labels(db, new), actor=actor)

def _now(): return datetime.now(timezone.utc)
def _next_code(db):
    codes=db.scalars(select(Task.task_code).where(Task.task_code.like("TASK-%")))
    nums=[int(c.split("-")[-1]) for c in codes if c.split("-")[-1].isdigit()]
    return f"TASK-{max(nums,default=0)+1:06d}"
def _event_type(typ):
    return typ if typ.startswith("task.") else f"task.{typ}"
def _act(db,task,typ,title=None,content=None,old=None,new=None,actor=None):
    db.add(TaskActivity(task_id=task.id,activity_type=_event_type(typ),title=title or typ,content=content,old_value=old,new_value=new,actor_id=getattr(actor,"id",None)))
def _has_view_all(user): return user.is_superuser or "tasks.view_all" in set(get_user_permissions(user)) or "tasks.view.all" in set(get_user_permissions(user))
def _can_access(user,task): return _has_view_all(user) or task.assigned_user_id==user.id or task.created_by_id==user.id or user.id in set(_collab_ids(task, "task_assignees")) or user.id in set(_collab_ids(task, "task_watchers"))
def _get(db,id):
    t=db.scalar(select(Task).where(Task.id==id,Task.deleted_at.is_(None)))
    if not t: raise HTTPException(404,"Công việc không tồn tại")
    return t

def _can_assign_tasks(actor: User) -> bool:
    # System Admin may be represented by either is_superuser or the admin role.
    return actor.is_superuser or any(role.code == "admin" for role in actor.roles) or "tasks.assign" in set(get_user_permissions(actor))

def _validate_assignee(db, actor: User, assigned_user_id):
    # Manual tasks default to the current user. Assigning someone else requires
    # the existing tasks.assign permission (superusers/admins are always allowed).
    assignee_id = assigned_user_id or actor.id
    user = db.scalar(select(User).where(User.id == assignee_id, User.status == "active", User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(400, "Người phụ trách không tồn tại.")
    if assignee_id != actor.id and not _can_assign_tasks(actor):
        raise HTTPException(403, "Bạn không có quyền giao công việc cho người này.")
    return assignee_id

def _validate(data):
    if "status" in data and data["status"] and data["status"] not in STATUSES: raise HTTPException(400,"Trạng thái công việc không hợp lệ")
    if "priority" in data and data["priority"] and data["priority"] not in PRIORITIES: raise HTTPException(400,"Độ ưu tiên không hợp lệ")
    if "task_type" in data and data["task_type"] and data["task_type"] not in TYPES: raise HTTPException(400,"Loại công việc không hợp lệ")

def serialize_task(t,detail=False):
    primary = _user_brief(t.assigned_user)
    assignees = _collab_users(t, "task_assignees")
    if primary and t.assigned_user_id not in [a["id"] for a in assignees]:
        assignees = [primary, *assignees]
    watchers = [w for w in _collab_users(t, "task_watchers") if w["id"] not in [a["id"] for a in assignees]]
    d={"id":t.id,"task_code":t.task_code,"title":t.title,"description":t.description,"task_type":t.task_type,"priority":t.priority,"status":t.status,"due_at":t.due_at,"completed_at":t.completed_at,"cancelled_at":t.cancelled_at,"assigned_user_id":t.assigned_user_id,"primary_assignee_id":t.assigned_user_id,"assigned_to_id":t.assigned_user_id,"assigned_user":primary,"assigned_to":primary,"primary_assignee":primary,"assignee_ids":[a["id"] for a in assignees],"assignees":assignees,"watcher_ids":[w["id"] for w in watchers],"watchers":watchers,"created_by_id":t.created_by_id,"creator":_user_brief(t.creator),"created_by":_user_brief(t.creator),"related_customer_id":t.related_customer_id,"related_lead_id":t.related_lead_id,"related_booking_id":t.related_booking_id,"related_deal_id":t.related_deal_id,"related_contract_id":t.related_contract_id,"related_property_unit_id":t.related_property_unit_id,"related_customer":{"id":t.related_customer.id,"customer_code":t.related_customer.customer_code,"full_name":t.related_customer.full_name,"primary_phone":t.related_customer.primary_phone} if t.related_customer else None,"related_lead":{"id":t.related_lead.id,"code":t.related_lead.code,"full_name":t.related_lead.full_name,"phone_primary":t.related_lead.phone_primary} if t.related_lead else None,"related_booking":{"id":t.related_booking.id,"booking_code":t.related_booking.booking_code} if t.related_booking else None,"related_deal":{"id":t.related_deal.id,"deal_code":t.related_deal.deal_code,"title":t.related_deal.title} if t.related_deal else None,"related_contract":{"id":t.related_contract.id,"contract_code":t.related_contract.contract_code} if t.related_contract else None,"related_property_unit":{"id":t.related_property_unit.id,"property_code":t.related_property_unit.property_code,"title":t.related_property_unit.title} if t.related_property_unit else None,"auto_generated":t.auto_generated,"source_event":t.source_event,"note":t.note,"created_at":t.created_at,"updated_at":t.updated_at}
    if detail: d["activities"]=[{"id":a.id,"activity_type":a.activity_type,"title":a.title,"content":a.content,"old_value":a.old_value,"new_value":a.new_value,"actor":{"id":a.actor.id,"full_name":a.actor.full_name} if a.actor else None,"created_at":a.created_at} for a in t.activities]
    return d

def _task_list_load_options():
    # Keep task list SQL narrow: load only the fields displayed by the UI and
    # prevent nested joined relationships from related CRM models.
    return (
        selectinload(Task.assigned_user).load_only(User.id, User.full_name, User.email),
        selectinload(Task.creator).load_only(User.id, User.full_name, User.email),
        selectinload(Task.task_assignees).selectinload(TaskAssignee.user).load_only(User.id, User.full_name, User.email),
        selectinload(Task.task_watchers).selectinload(TaskWatcher.user).load_only(User.id, User.full_name, User.email),

        selectinload(Task.related_booking).load_only(Booking.id, Booking.booking_code).lazyload("*"),
        selectinload(Task.related_deal).load_only(Deal.id, Deal.deal_code, Deal.title).lazyload("*"),
        selectinload(Task.related_contract).load_only(Contract.id, Contract.contract_code).lazyload("*"),
        selectinload(Task.related_customer).load_only(Customer.id, Customer.customer_code, Customer.full_name, Customer.primary_phone).lazyload("*"),
        selectinload(Task.related_lead).load_only(Lead.id, Lead.code, Lead.full_name, Lead.phone_primary).lazyload("*"),
        selectinload(Task.related_property_unit).load_only(PropertyUnit.id, PropertyUnit.property_code, PropertyUnit.title).lazyload("*"),
    )

def list_tasks(db,actor,page=1,page_size=20,**f):
    cond=[Task.deleted_at.is_(None)]
    if mine_only(f.get("scope")):
        cond.append(or_(Task.assigned_user_id==actor.id, Task.task_assignees.any(TaskAssignee.user_id==actor.id)))
    if not _has_view_all(actor): cond.append(or_(Task.assigned_user_id==actor.id,Task.created_by_id==actor.id,Task.task_assignees.any(TaskAssignee.user_id==actor.id),Task.task_watchers.any(TaskWatcher.user_id==actor.id)))
    for name,col in (("status",Task.status),("priority",Task.priority),("task_type",Task.task_type),("assigned_user_id",Task.assigned_user_id),("related_lead_id",Task.related_lead_id),("lead_id",Task.related_lead_id),("related_customer_id",Task.related_customer_id),("related_booking_id",Task.related_booking_id),("related_deal_id",Task.related_deal_id),("related_contract_id",Task.related_contract_id)):
        if f.get(name) is not None:
            if name=="assigned_user_id":
                cond.append(or_(Task.assigned_user_id==f[name], Task.task_assignees.any(TaskAssignee.user_id==f[name])))
            else:
                cond.append(col==f[name])
    query=select(Task).outerjoin(Task.assigned_user).outerjoin(Task.related_booking).outerjoin(Task.related_deal).outerjoin(Task.related_contract).outerjoin(Task.related_customer).outerjoin(Task.related_lead).outerjoin(Task.related_property_unit)
    if f.get("q"):
        term=f"%{f['q'].strip()}%"
        cond.append(or_(Task.task_code.ilike(term),Task.title.ilike(term),Task.task_type.ilike(term),User.full_name.ilike(term),User.email.ilike(term),Booking.booking_code.ilike(term),Deal.deal_code.ilike(term),Contract.contract_code.ilike(term),Customer.customer_code.ilike(term),Customer.full_name.ilike(term),Customer.primary_phone.ilike(term),Lead.code.ilike(term),Lead.full_name.ilike(term),Lead.phone_primary.ilike(term),PropertyUnit.property_code.ilike(term),PropertyUnit.title.ilike(term)))
    if f.get("active_only"): cond.append(Task.status.in_({"open","in_progress"}))
    if f.get("due_from"): cond.append(Task.due_at>=f["due_from"])
    if f.get("due_to"): cond.append(Task.due_at<=f["due_to"])
    if f.get("today"):
        from datetime import datetime, time, timezone, timedelta
        start=datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc); cond.append(Task.due_at>=start); cond.append(Task.due_at<start+timedelta(days=1))
    if f.get("due_before"): cond.append(Task.due_at<f["due_before"])
    total=db.scalar(query.with_only_columns(func.count(func.distinct(Task.id))).where(*cond)) or 0
    items=list(db.scalars(query.options(*_task_list_load_options()).where(*cond).order_by(Task.due_at.asc().nullslast(),Task.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}

def get_task_detail(db,id,actor):
    t=_get(db,id)
    if not _can_access(actor,t): raise HTTPException(403,"Bạn không có quyền xem công việc này")
    return t

def create_task(db,payload,actor,auto=False,source_event=None,notify_type="task_assigned"):
    data=payload if isinstance(payload,dict) else payload.model_dump(exclude_unset=True); assignee_ids=data.pop("assignee_ids", None); watcher_ids=data.pop("watcher_ids", None); data["assigned_user_id"] = data.get("primary_assignee_id") or data.get("assigned_to_id") or data.get("assigned_user_id"); data.pop("primary_assignee_id", None); data.pop("assigned_to_id", None); _validate(data)
    if not data.get("title"): raise HTTPException(400,"Tiêu đề là bắt buộc")
    data.pop("source_event", None)
    if not auto:
        data["assigned_user_id"] = _validate_assignee(db, actor, data.get("assigned_user_id"))
    t=Task(**data,task_code=_next_code(db),created_by_id=getattr(actor,"id",None),auto_generated=auto,source_event=source_event)
    db.add(t); db.flush(); _act(db,t,"created","Tạo công việc",actor=actor); _sync_collaboration(db,t,assignee_ids=assignee_ids,watcher_ids=watcher_ids,actor=actor); create_task_notification(db,t,notification_type=notify_type); db.commit(); db.refresh(t); return t

def update_task(db,id,payload,actor):
    t=get_task_detail(db,id,actor); data=payload.model_dump(exclude_unset=True); assignee_ids=data.pop("assignee_ids", None); watcher_ids=data.pop("watcher_ids", None); primary_payload=data.pop("primary_assignee_id", None); assigned_to_payload=data.pop("assigned_to_id", None);
    if primary_payload is not None or assigned_to_payload is not None or "assigned_user_id" in data:
        data["assigned_user_id"] = primary_payload or assigned_to_payload or data.get("assigned_user_id")
    _validate(data); old_assignee=t.assigned_user_id
    if "assigned_user_id" in data:
        data["assigned_user_id"] = _validate_assignee(db, actor, data.get("assigned_user_id"))
    old_status=t.status; old_due=t.due_at
    for k,v in data.items(): setattr(t,k,v)
    if "status" in data and data["status"] != old_status: _act(db,t,"completed" if data["status"]=="done" else "cancelled" if data["status"]=="cancelled" else "status_changed","Đổi trạng thái",old=old_status,new=data["status"],actor=actor)
    if "due_at" in data and data["due_at"] != old_due: _act(db,t,"due_date_changed","Đổi hạn xử lý",old=str(old_due) if old_due else None,new=str(data["due_at"]) if data["due_at"] else None,actor=actor)
    if t.status=="done": t.completed_at=t.completed_at or _now()
    elif t.status=="cancelled": t.cancelled_at=t.cancelled_at or _now()
    if "assigned_user_id" in data and data["assigned_user_id"] != old_assignee: _act(db,t,"primary_assignee_changed","Đổi người phụ trách chính",old=_join_labels(db,[old_assignee]) if old_assignee else "Không xác định",new=_join_labels(db,[data["assigned_user_id"]]) if data["assigned_user_id"] else "Không xác định",actor=actor); create_task_notification(db,t,"Bạn được giao công việc")
    _sync_collaboration(db,t,assignee_ids=assignee_ids,watcher_ids=watcher_ids,actor=actor,reject_missing_primary=True)
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
    if kw.get("related_deal_id"): cond.append(Task.related_deal_id==kw["related_deal_id"])
    existing=db.scalar(select(Task).where(*cond).limit(1))
    if existing: return existing
    return create_task(db,kw,actor,auto=True,source_event=kw.get("source_event"),notify_type="contract_payment_due" if kw.get("task_type")=="payment_due" else "task_assigned")


def auto_task_for_deal_stage(db,deal,actor):
    stage_map={
        "consulting": ("follow_up", "deal_consulting", f"Theo dõi giao dịch {deal.deal_code}", "medium"),
        "contract_pending": ("contract_signing", "deal_contract_pending", f"Chuẩn bị ký hợp đồng cho giao dịch {deal.deal_code}", "high"),
        "deposited": ("follow_up", "deal_deposited", f"Nhắc xử lý đặt cọc/giao dịch {deal.deal_code}", "high"),
        "deposit": ("follow_up", "deal_deposited", f"Nhắc xử lý đặt cọc/giao dịch {deal.deal_code}", "high"),
    }
    if deal.pipeline_stage not in stage_map or not deal.owner_id:
        return None
    task_type,source_event,title,priority=stage_map[deal.pipeline_stage]
    return create_auto_task_if_not_exists(db,actor,title=title,task_type=task_type,priority=priority,assigned_user_id=deal.owner_id,related_deal_id=deal.id,related_customer_id=deal.customer_id,related_property_unit_id=deal.property_unit_id,source_event=source_event)

def auto_reassign_deal_tasks(db,deal,old_assignee_id,actor):
    if not old_assignee_id or old_assignee_id==deal.owner_id:
        return
    old_user=db.scalar(select(User).where(User.id==old_assignee_id))
    new_user=db.scalar(select(User).where(User.id==deal.owner_id))
    content=f"Deal đổi người phụ trách nên công việc được chuyển từ {getattr(old_user,'full_name',None) or 'người phụ trách cũ'} sang {getattr(new_user,'full_name',None) or 'người phụ trách mới'}."
    for t in db.scalars(select(Task).where(Task.related_deal_id==deal.id,Task.auto_generated.is_(True),Task.source_event.in_(["deal_consulting","deal_contract_pending","deal_deposited"]),Task.deleted_at.is_(None),Task.status.in_(["open","in_progress"]))):
        if t.assigned_user_id==deal.owner_id:
            continue
        old=str(t.assigned_user_id) if t.assigned_user_id else None
        t.assigned_user_id=deal.owner_id
        _act(db,t,"assigned","Tự động chuyển công việc",content,old,str(deal.owner_id),actor)
        create_task_notification(db,t,"Bạn được giao công việc")

def _today_bounds():
    start_of_today=datetime.combine(_now().date(),time.min,tzinfo=timezone.utc)
    start_of_tomorrow=start_of_today+timedelta(days=1)
    return start_of_today,start_of_tomorrow
def get_today_tasks(db,actor,page=1,page_size=200,q=None,with_meta=False):
    start_of_today,start_of_tomorrow=_today_bounds()
    items, meta = list_tasks(db,actor,page=page,page_size=page_size,q=q,due_from=start_of_today,due_before=start_of_tomorrow,active_only=True)
    return (items, meta) if with_meta else items
def get_overdue_tasks(db,actor,page=1,page_size=200,q=None,with_meta=False):
    start_of_today,_=_today_bounds()
    items, meta = list_tasks(db,actor,page=page,page_size=page_size,q=q,due_before=start_of_today,active_only=True)
    return (items, meta) if with_meta else items

def auto_task_for_booking_created(db,booking,actor):
    due=booking.reservation_expires_at-timedelta(days=1) if booking.reservation_expires_at else None
    return create_auto_task_if_not_exists(db,actor,title=f"Theo dõi booking {booking.booking_code}",task_type="follow_up",priority="medium",assigned_user_id=booking.assigned_user_id,related_booking_id=booking.id,related_customer_id=booking.customer_id,related_property_unit_id=booking.property_unit_id,due_at=due,source_event="booking_created")
def auto_task_for_booking_deposited(db,booking,actor):
    return create_auto_task_if_not_exists(db,actor,title=f"Chuẩn bị ký hợp đồng cho booking {booking.booking_code}",task_type="contract_signing",priority="high",assigned_user_id=booking.assigned_user_id,related_booking_id=booking.id,related_customer_id=booking.customer_id,related_property_unit_id=booking.property_unit_id,source_event="booking_deposited")
def auto_cancel_booking_tasks(db,booking,actor):
    label={"cancelled":"hủy","refunded":"hoàn tiền","expired":"hết hạn"}.get(booking.status,booking.status); reason=f"Booking {booking.booking_code} đã {label} nên công việc được tự động hủy."
    for t in db.scalars(select(Task).where(Task.related_booking_id==booking.id,Task.deleted_at.is_(None),Task.status.in_(["open","in_progress"]),Task.task_type!="general")):
        t.status="cancelled"; t.cancelled_at=_now(); _act(db,t,"cancelled","Tự động hủy công việc",reason,actor=actor)
def auto_reassign_booking_tasks(db,booking,old_assignee_id,actor):
    if not old_assignee_id or old_assignee_id==booking.assigned_user_id: return
    old_user=db.scalar(select(User).where(User.id==old_assignee_id))
    new_user=db.scalar(select(User).where(User.id==booking.assigned_user_id))
    old_name=getattr(old_user,"full_name",None) or "người phụ trách cũ"
    new_name=getattr(new_user,"full_name",None) or "người phụ trách mới"
    content=f"Booking đổi người phụ trách nên công việc được chuyển từ {old_name} sang {new_name}."
    for t in db.scalars(select(Task).where(Task.related_booking_id==booking.id,Task.auto_generated.is_(True),Task.source_event.in_(["booking_created","booking_deposited"]),Task.deleted_at.is_(None),Task.status.in_(["open","in_progress"]))):
        if t.assigned_user_id==booking.assigned_user_id: continue
        old=str(t.assigned_user_id) if t.assigned_user_id else None
        t.assigned_user_id=booking.assigned_user_id
        _act(db,t,"assigned","Tự động chuyển công việc",content,old,str(booking.assigned_user_id),actor)
        create_task_notification(db,t,"Bạn được giao công việc")
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
    if not _can_assign_tasks(actor):
        query = query.where(User.id == actor.id)
    return list(db.scalars(query.order_by(User.full_name)).unique())


def _notify_task_participants(db, task, actor, title, notification_type):
    recipients = {task.created_by_id, task.assigned_user_id, *_collab_ids(task, "task_assignees"), *_collab_ids(task, "task_watchers")}
    recipients.discard(None); recipients.discard(getattr(actor, "id", None))
    for uid in recipients:
        create_notification(db, recipient_user_id=uid, title=title, content=task.title, notification_type=notification_type, related_task_id=task.id, related_booking_id=task.related_booking_id, related_deal_id=task.related_deal_id, related_contract_id=task.related_contract_id, related_customer_id=task.related_customer_id, related_property_unit_id=task.related_property_unit_id)

def _comment_dict(c):
    return {"id":c.id,"task_id":c.task_id,"content":c.content,"author":_user_brief(c.author),"created_at":c.created_at,"updated_at":c.updated_at,"is_deleted":c.is_deleted}

def _link_dict(x):
    return {"id":x.id,"task_id":x.task_id,"title":x.title,"url":x.url,"note":x.note,"created_by":_user_brief(x.created_by),"created_at":x.created_at,"updated_at":x.updated_at}

def list_task_comments(db, task_id, actor):
    task=get_task_detail(db, task_id, actor)
    return [_comment_dict(c) for c in db.scalars(select(TaskComment).where(TaskComment.task_id==task.id, TaskComment.is_deleted.is_(False)).order_by(TaskComment.created_at.asc()))]

def create_task_comment(db, task_id, payload, actor):
    task=get_task_detail(db, task_id, actor); content=payload.content.strip()
    c=TaskComment(task_id=task.id, author_id=actor.id, content=content); db.add(c); db.flush()
    _act(db, task, "comment_added", "Thêm bình luận", content=(content[:180] + "…") if len(content)>180 else content, actor=actor)
    _notify_task_participants(db, task, actor, "Có bình luận mới trong công việc", "task_comment_added")
    db.commit(); db.refresh(c); return _comment_dict(c)

def list_task_links(db, task_id, actor):
    task=get_task_detail(db, task_id, actor)
    return [_link_dict(x) for x in db.scalars(select(TaskRelatedLink).where(TaskRelatedLink.task_id==task.id, TaskRelatedLink.is_deleted.is_(False)).order_by(TaskRelatedLink.created_at.desc()))]

def create_task_link(db, task_id, payload, actor):
    task=get_task_detail(db, task_id, actor); title=payload.title.strip(); url=payload.url.strip(); note=payload.note.strip() if payload.note else None
    if not (url.startswith("http://") or url.startswith("https://")): raise HTTPException(400,"URL phải bắt đầu bằng http:// hoặc https://")
    x=TaskRelatedLink(task_id=task.id, title=title, url=url, note=note, created_by_id=actor.id); db.add(x); db.flush()
    _act(db, task, "link_added", "Thêm link liên quan", content=title, actor=actor)
    _notify_task_participants(db, task, actor, "Có link liên quan mới trong công việc", "task_link_added")
    db.commit(); db.refresh(x); return _link_dict(x)

def delete_task_link(db, task_id, link_id, actor):
    task=get_task_detail(db, task_id, actor)
    x=db.scalar(select(TaskRelatedLink).where(TaskRelatedLink.id==link_id, TaskRelatedLink.task_id==task.id, TaskRelatedLink.is_deleted.is_(False)))
    if not x: raise HTTPException(404,"Link liên quan không tồn tại")
    x.is_deleted=True; _act(db, task, "link_deleted", "Xóa link liên quan", content=x.title, actor=actor); db.commit(); return {"deleted": True}

def list_task_timeline(db, task_id, actor):
    task=get_task_detail(db, task_id, actor)
    return [{"id":a.id,"task_id":a.task_id,"event_type":a.activity_type,"title":a.title,"description":a.content,"actor":{"id":a.actor.id,"full_name":a.actor.full_name,"email":a.actor.email} if a.actor else None,"old_value":a.old_value,"new_value":a.new_value,"created_at":a.created_at} for a in db.scalars(select(TaskActivity).where(TaskActivity.task_id==task.id).order_by(TaskActivity.created_at.desc()))]
