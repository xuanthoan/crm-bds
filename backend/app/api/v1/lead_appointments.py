from datetime import datetime
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.lead_appointment import LeadAppointmentCreate,LeadAppointmentStatusUpdate,LeadAppointmentUpdate
from app.services.lead_appointment_service import *
router=APIRouter(prefix="/lead-appointments",tags=["lead-appointments"])
@router.get("")
def index(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),status_filter:str|None=Query(None,alias="status"),appointment_type:str|None=None,assigned_to_id:UUID|None=None,lead_id:UUID|None=None,start_from:datetime|None=None,start_to:datetime|None=None,today:bool=False,upcoming:bool=False,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_appointments(db,user,page=page,page_size=page_size,appointment_status=status_filter,appointment_type=appointment_type,assigned_to_id=assigned_to_id,lead_id=lead_id,start_from=start_from,start_to=start_to,today=today,upcoming=upcoming);return success_response(data=[serialize_appointment(x) for x in items],message="Appointments retrieved",meta=meta)
@router.get("/my/today")
def my_today(db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_appointments(db,user,page=1,page_size=100,assigned_to_id=user.id,today=True);return success_response(data=[serialize_appointment(x) for x in items],message="Today appointments retrieved",meta=meta)
@router.get("/my/upcoming")
def my_upcoming(db:Session=Depends(get_db),user:User=Depends(require_auth)):
    items,meta=list_appointments(db,user,page=1,page_size=100,assigned_to_id=user.id,upcoming=True);return success_response(data=[serialize_appointment(x) for x in items],message="Upcoming appointments retrieved",meta=meta)
@router.post("")
def create(payload:LeadAppointmentCreate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_appointment(create_appointment(db,payload,user)),message="Appointment created")
def _get(db,id,user):
    item=get_appointment(db,id)
    if not item:raise HTTPException(404,"Không tìm thấy lịch hẹn")
    require_view(db,item,user);return item
@router.get("/{appointment_id}")
def detail(appointment_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_appointment(_get(db,appointment_id,user)),message="Appointment retrieved")
@router.put("/{appointment_id}")
def update(appointment_id:UUID,payload:LeadAppointmentUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_appointment(update_appointment(db,_get(db,appointment_id,user),payload,user)),message="Appointment updated")
@router.post("/{appointment_id}/status")
def status(appointment_id:UUID,payload:LeadAppointmentStatusUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(data=serialize_appointment(update_appointment_status(db,_get(db,appointment_id,user),payload,user)),message="Appointment status updated")
@router.delete("/{appointment_id}")
def delete(appointment_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):delete_appointment(db,_get(db,appointment_id,user),user);return success_response(data=None,message="Appointment deleted")
