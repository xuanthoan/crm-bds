from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, require_permission
from app.schemas.booking import BookingActivityCreate, BookingCreate, BookingStatusChange, BookingUpdate
from app.services.booking_service import add_booking_activity, change_booking_status, create_booking, get_booking_detail, list_booking_assignees, list_bookings, serialize_booking, soft_delete_booking, update_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.get("")
def get_bookings(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,customer_id:UUID|None=None,property_unit_id:UUID|None=None,assigned_user_id:UUID|None=None,status_filter:str|None=Query(None,alias="status"),created_from:datetime|None=None,created_to:datetime|None=None,expires_from:datetime|None=None,expires_to:datetime|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_bookings(db,actor,page=page,page_size=page_size,q=q,customer_id=customer_id,property_unit_id=property_unit_id,assigned_user_id=assigned_user_id,status=status_filter,created_from=created_from,created_to=created_to,expires_from=expires_from,expires_to=expires_to)
    return success_response([serialize_booking(item) for item in items],meta=meta)

@router.post("",status_code=status.HTTP_201_CREATED)
def post_booking(payload:BookingCreate,db:Session=Depends(get_db),actor:User=Depends(require_permission("bookings.create"))): return success_response(serialize_booking(create_booking(db,payload,actor),True),"Tạo booking thành công")

# Static routes are declared before /{booking_id}.
@router.get("/assignees")
def get_assignees(db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response([{"id":u.id,"full_name":u.full_name,"email":u.email} for u in list_booking_assignees(db,actor)])

@router.get("/{booking_id}")
def get_booking(booking_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_booking(get_booking_detail(db,booking_id,actor),True))

@router.put("/{booking_id}")
def put_booking(booking_id:UUID,payload:BookingUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_booking(update_booking(db,booking_id,payload,actor),True),"Cập nhật booking thành công")

@router.post("/{booking_id}/status")
def post_booking_status(booking_id:UUID,payload:BookingStatusChange,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_booking(change_booking_status(db,booking_id,payload,actor),True),"Đổi trạng thái booking thành công")

@router.post("/{booking_id}/activities",status_code=status.HTTP_201_CREATED)
def post_booking_activity(booking_id:UUID,payload:BookingActivityCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    add_booking_activity(db,booking_id,payload,actor)
    return success_response(serialize_booking(get_booking_detail(db,booking_id,actor),True)["activities"][0],"Thêm hoạt động thành công")

@router.delete("/{booking_id}")
def delete_booking(booking_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): soft_delete_booking(db,booking_id,actor); return success_response(None,"Xóa booking thành công")
