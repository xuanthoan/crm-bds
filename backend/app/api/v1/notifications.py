from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.services.notification_service import list_notifications, mark_all_read, mark_read, serialize_notification, unread_count
router=APIRouter(prefix="/notifications",tags=["notifications"])
@router.get("")
def get_notifications(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),status_filter:str|None=Query(None,alias="status"),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_notifications(db,actor,status_filter,page,page_size); return success_response([serialize_notification(i) for i in items],meta=meta)
@router.get("/unread-count")
def count(db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response({"unread_count":unread_count(db,actor)})
@router.post("/{notification_id}/read")
def read(notification_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_notification(mark_read(db,notification_id,actor)),"Đã đánh dấu thông báo")
@router.post("/read-all")
def read_all(db:Session=Depends(get_db),actor:User=Depends(require_auth)): mark_all_read(db,actor); return success_response(None,"Đã đánh dấu tất cả thông báo")
