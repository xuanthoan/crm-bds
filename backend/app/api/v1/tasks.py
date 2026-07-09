from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, require_permission
from app.schemas.task import TaskCancel, TaskCommentCreate, TaskComplete, TaskCreate, TaskNote, TaskRelatedLinkCreate, TaskStatusChange, TaskUpdate
from app.services.task_service import add_task_note, cancel_task, change_task_status, complete_task, create_task, create_task_comment, create_task_link, delete_task_link, get_overdue_tasks, get_task_detail, get_today_tasks, list_task_assignees, list_task_comments, list_task_links, list_task_timeline, list_tasks, serialize_task, update_task
router=APIRouter(prefix="/tasks",tags=["tasks"])
@router.get("")
def get_tasks(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,status_filter:str|None=Query(None,alias="status"),priority:str|None=None,task_type:str|None=None,assigned_user_id:UUID|None=None,due_from:datetime|None=None,due_to:datetime|None=None,lead_id:UUID|None=Query(None,alias="lead_id"),related_lead_id:UUID|None=None,related_customer_id:UUID|None=None,related_booking_id:UUID|None=None,related_deal_id:UUID|None=None,related_contract_id:UUID|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    lead_filter=related_lead_id or lead_id
    items,meta=list_tasks(db,actor,page=page,page_size=page_size,q=q,status=status_filter,priority=priority,task_type=task_type,assigned_user_id=assigned_user_id,due_from=due_from,due_to=due_to,related_lead_id=lead_filter,related_customer_id=related_customer_id,related_booking_id=related_booking_id,related_deal_id=related_deal_id,related_contract_id=related_contract_id); return success_response([serialize_task(i) for i in items],meta=meta)
@router.post("",status_code=status.HTTP_201_CREATED)
def post_task(payload:TaskCreate,db:Session=Depends(get_db),actor:User=Depends(require_permission("tasks.create"))): return success_response(serialize_task(create_task(db,payload,actor),True),"Tạo công việc thành công")
@router.get("/assignees")
def assignees(db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    return success_response([{"id":u.id,"full_name":u.full_name,"email":u.email} for u in list_task_assignees(db,actor)])
@router.get("/today")
def today(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=get_today_tasks(db,actor,page=page,page_size=page_size,q=q,with_meta=True); return success_response([serialize_task(i) for i in items],meta=meta)
@router.get("/overdue")
def overdue(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=get_overdue_tasks(db,actor,page=page,page_size=page_size,q=q,with_meta=True); return success_response([serialize_task(i) for i in items],meta=meta)

@router.get("/{task_id}/comments")
def comments(task_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(list_task_comments(db,task_id,actor))
@router.post("/{task_id}/comments",status_code=status.HTTP_201_CREATED)
def post_comment(task_id:UUID,payload:TaskCommentCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(create_task_comment(db,task_id,payload,actor),"Thêm bình luận thành công")
@router.get("/{task_id}/links")
def links(task_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(list_task_links(db,task_id,actor))
@router.post("/{task_id}/links",status_code=status.HTTP_201_CREATED)
def post_link(task_id:UUID,payload:TaskRelatedLinkCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(create_task_link(db,task_id,payload,actor),"Thêm link thành công")
@router.delete("/{task_id}/links/{link_id}")
def remove_link(task_id:UUID,link_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(delete_task_link(db,task_id,link_id,actor),"Xóa link thành công")
@router.get("/{task_id}/timeline")
def timeline(task_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(list_task_timeline(db,task_id,actor))
@router.get("/{task_id}")
def detail(task_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_task(get_task_detail(db,task_id,actor),True))
@router.put("/{task_id}")
def put_task(task_id:UUID,payload:TaskUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_task(update_task(db,task_id,payload,actor),True),"Cập nhật công việc thành công")
@router.post("/{task_id}/status")
def status_task(task_id:UUID,payload:TaskStatusChange,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_task(change_task_status(db,task_id,payload.status,payload.note,actor),True),"Đổi trạng thái công việc thành công")
@router.post("/{task_id}/complete")
def complete(task_id:UUID,payload:TaskComplete,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_task(complete_task(db,task_id,payload.note,actor),True),"Hoàn thành công việc thành công")
@router.post("/{task_id}/cancel")
def cancel(task_id:UUID,payload:TaskCancel,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_task(cancel_task(db,task_id,payload.reason,actor),True),"Hủy công việc thành công")
@router.post("/{task_id}/notes")
def note(task_id:UUID,payload:TaskNote,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_task(add_task_note(db,task_id,payload.note,actor),True),"Thêm ghi chú thành công")
