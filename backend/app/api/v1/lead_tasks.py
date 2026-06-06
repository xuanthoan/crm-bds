from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, require_permission
from app.schemas.lead_task import LeadTaskCreate, LeadTaskUpdate, LeadTaskStatusUpdate
from app.services.lead_task_service import create_task, delete_task, get_task, list_tasks, serialize_task, update_task, update_task_status
router=APIRouter(prefix="/lead-tasks",tags=["lead-tasks"])
@router.get("")
def index(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),search:str|None=None,status:str|None=None,task_type:str|None=None,priority:str|None=None,assigned_to_id:UUID|None=None,lead_id:UUID|None=None,due_from:datetime|None=None,due_to:datetime|None=None,overdue:bool=False,today:bool=False,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_tasks(db,user,page,page_size,search=search,status=status,task_type=task_type,priority=priority,assigned_to_id=assigned_to_id,lead_id=lead_id,due_from=due_from,due_to=due_to,overdue=overdue,today=today); return success_response([serialize_task(x) for x in items],"Tasks retrieved",meta)
@router.post("")
def create(payload:LeadTaskCreate,db:Session=Depends(get_db),user:User=Depends(require_permission("lead_tasks.create"))):return success_response(serialize_task(create_task(db,payload,user)),"Task created")
@router.get("/my/today")
def my_today(page:int=1,page_size:int=100,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_tasks(db,user,page,page_size,assigned_to_id=user.id,today=True);return success_response([serialize_task(x) for x in items],"Today tasks retrieved",meta)
@router.get("/my/overdue")
def my_overdue(page:int=1,page_size:int=100,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_tasks(db,user,page,page_size,assigned_to_id=user.id,overdue=True);return success_response([serialize_task(x) for x in items],"Overdue tasks retrieved",meta)
@router.get("/{task_id}")
def detail(task_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(serialize_task(get_task(db,user,task_id)))
@router.put("/{task_id}")
def update(task_id:UUID,payload:LeadTaskUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(serialize_task(update_task(db,task_id,payload,user)),"Task updated")
@router.post("/{task_id}/status")
def status(task_id:UUID,payload:LeadTaskStatusUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(serialize_task(update_task_status(db,task_id,payload,user)),"Task status updated")
@router.delete("/{task_id}")
def remove(task_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):delete_task(db,task_id,user);return success_response(message="Task deleted")
