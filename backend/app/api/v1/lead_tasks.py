from datetime import datetime
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.lead_task import LeadTaskCreate,LeadTaskStatusUpdate,LeadTaskUpdate
from app.services.lead_task_service import *
router=APIRouter(prefix="/lead-tasks",tags=["lead-tasks"])
@router.get("")
def index(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),search:str|None=None,status_filter:str|None=Query(None,alias="status"),task_type:str|None=None,priority:str|None=None,assigned_to_id:UUID|None=None,lead_id:UUID|None=None,due_from:datetime|None=None,due_to:datetime|None=None,overdue:bool=False,today:bool=False,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_tasks(db,user,page=page,page_size=page_size,search=search,task_status=status_filter,task_type=task_type,priority=priority,assigned_to_id=assigned_to_id,lead_id=lead_id,due_from=due_from,due_to=due_to,overdue=overdue,today=today);return success_response(data=[serialize_task(x) for x in items],message="Tasks retrieved",meta=meta)
@router.get("/my/today")
def my_today(db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_tasks(db,user,page=1,page_size=100,assigned_to_id=user.id,today=True);return success_response(data=[serialize_task(x) for x in items],message="Today tasks retrieved",meta=meta)
@router.get("/my/overdue")
def my_overdue(db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_tasks(db,user,page=1,page_size=100,assigned_to_id=user.id,overdue=True);return success_response(data=[serialize_task(x) for x in items],message="Overdue tasks retrieved",meta=meta)
@router.post("")
def create(payload:LeadTaskCreate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_task(create_task(db,payload,user)),message="Task created")
def _get(db,id,user):
    item=get_task(db,id)
    if not item:raise HTTPException(404,"Không tìm thấy công việc")
    require_task_view(db,item,user);return item
@router.get("/{task_id}")
def detail(task_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_task(_get(db,task_id,user)),message="Task retrieved")
@router.put("/{task_id}")
def update(task_id:UUID,payload:LeadTaskUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_task(update_task(db,_get(db,task_id,user),payload,user)),message="Task updated")
@router.post("/{task_id}/status")
def status(task_id:UUID,payload:LeadTaskStatusUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_task(update_task_status(db,_get(db,task_id,user),payload,user)),message="Task status updated")
@router.delete("/{task_id}")
def delete(task_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):delete_task(db,_get(db,task_id,user),user);return success_response(data=None,message="Task deleted")
