from datetime import datetime
from uuid import UUID
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth,require_permission
from app.schemas.lead_appointment import LeadAppointmentCreate,LeadAppointmentUpdate,LeadAppointmentStatusUpdate
from app.services.lead_appointment_service import create_appointment,delete_appointment,get_appointment,list_appointments,serialize_appointment,update_appointment,update_appointment_status
router=APIRouter(prefix="/lead-appointments",tags=["lead-appointments"])
@router.get("")
def index(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),status:str|None=None,appointment_type:str|None=None,assigned_to_id:UUID|None=None,lead_id:UUID|None=None,start_from:datetime|None=None,start_to:datetime|None=None,today:bool=False,upcoming:bool=False,scope:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_auth)):
 assigned_to_id=user.id if scope=="mine" else assigned_to_id
 items,meta=list_appointments(db,user,page,page_size,status=status,appointment_type=appointment_type,assigned_to_id=assigned_to_id,lead_id=lead_id,start_from=start_from,start_to=start_to,today=today,upcoming=upcoming);return success_response([serialize_appointment(x) for x in items],"Appointments retrieved",meta)
@router.post("")
def create(payload:LeadAppointmentCreate,db:Session=Depends(get_db),user:User=Depends(require_permission("lead_appointments.create"))):return success_response(serialize_appointment(create_appointment(db,payload,user)),"Appointment created")
@router.get("/my/today")
def my_today(page:int=1,page_size:int=100,db:Session=Depends(get_db),user:User=Depends(require_auth)):
 items,meta=list_appointments(db,user,page,page_size,assigned_to_id=user.id,today=True);return success_response([serialize_appointment(x) for x in items],"Today appointments retrieved",meta)
@router.get("/my/upcoming")
def my_upcoming(page:int=1,page_size:int=100,db:Session=Depends(get_db),user:User=Depends(require_auth)):
 items,meta=list_appointments(db,user,page,page_size,assigned_to_id=user.id,upcoming=True);return success_response([serialize_appointment(x) for x in items],"Upcoming appointments retrieved",meta)
@router.get("/{appointment_id}")
def detail(appointment_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(serialize_appointment(get_appointment(db,user,appointment_id)))
@router.put("/{appointment_id}")
def update(appointment_id:UUID,payload:LeadAppointmentUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(serialize_appointment(update_appointment(db,appointment_id,payload,user)),"Appointment updated")
@router.post("/{appointment_id}/status")
def status(appointment_id:UUID,payload:LeadAppointmentStatusUpdate,db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(serialize_appointment(update_appointment_status(db,appointment_id,payload,user)),"Appointment status updated")
@router.delete("/{appointment_id}")
def remove(appointment_id:UUID,db:Session=Depends(get_db),user:User=Depends(require_auth)):delete_appointment(db,appointment_id,user);return success_response(message="Appointment deleted")
