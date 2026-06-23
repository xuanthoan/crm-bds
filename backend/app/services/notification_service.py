from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User

def serialize_notification(n):
    return {"id":n.id,"recipient_user_id":n.recipient_user_id,"title":n.title,"content":n.content,"notification_type":n.notification_type,"status":n.status,"related_task_id":n.related_task_id,"related_booking_id":n.related_booking_id,"related_deal_id":n.related_deal_id,"related_contract_id":n.related_contract_id,"related_customer_id":n.related_customer_id,"related_property_unit_id":n.related_property_unit_id,"read_at":n.read_at,"created_at":n.created_at}

def list_notifications(db:Session,user:User,status=None,page=1,page_size=20):
    cond=[Notification.recipient_user_id==user.id,Notification.deleted_at.is_(None)]
    if status: cond.append(Notification.status==status)
    total=db.scalar(select(func.count(Notification.id)).where(*cond)) or 0
    items=list(db.scalars(select(Notification).where(*cond).order_by(Notification.created_at.desc()).offset((page-1)*page_size).limit(page_size)))
    return items,{"page":page,"page_size":page_size,"total":total}

def unread_count(db:Session,user:User): return db.scalar(select(func.count(Notification.id)).where(Notification.recipient_user_id==user.id,Notification.status=="unread",Notification.deleted_at.is_(None))) or 0

def mark_read(db:Session,notification_id:UUID,user:User):
    n=db.scalar(select(Notification).where(Notification.id==notification_id,Notification.deleted_at.is_(None)))
    if not n: raise HTTPException(404,"Thông báo không tồn tại")
    if n.recipient_user_id!=user.id: raise HTTPException(403,"Bạn không có quyền cập nhật thông báo này")
    n.status="read"; n.read_at=n.read_at or datetime.now(timezone.utc); db.commit(); db.refresh(n); return n

def mark_all_read(db:Session,user:User):
    now=datetime.now(timezone.utc)
    for n in db.scalars(select(Notification).where(Notification.recipient_user_id==user.id,Notification.status=="unread",Notification.deleted_at.is_(None))):
        n.status="read"; n.read_at=now
    db.commit()

def create_notification(db:Session,**kw):
    n=Notification(**kw); db.add(n); return n

def create_task_notification(db:Session,task:Task,title="Bạn có công việc mới",notification_type="task_assigned"):
    if not task.assigned_user_id: return None
    return create_notification(db,recipient_user_id=task.assigned_user_id,title=title,content=task.title,notification_type=notification_type,related_task_id=task.id,related_booking_id=task.related_booking_id,related_deal_id=task.related_deal_id,related_contract_id=task.related_contract_id,related_customer_id=task.related_customer_id,related_property_unit_id=task.related_property_unit_id)
