from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
APPOINTMENT_TYPES={"office_meeting","site_visit","phone_call","video_call","contract_meeting","other"}; APPOINTMENT_STATUSES={"scheduled","completed","cancelled","no_show","rescheduled"}
class LeadAppointmentCreate(BaseModel):
    lead_id: UUID; title: str=Field(min_length=1,max_length=255); description: str|None=None; appointment_type: str; start_at: datetime; end_at: datetime|None=None; location: str|None=None; meeting_link: str|None=None; assigned_to_id: UUID|None=None
    @model_validator(mode="after")
    def validate_fields(self):
        if self.appointment_type not in APPOINTMENT_TYPES: raise ValueError("Loại lịch hẹn không hợp lệ")
        if self.end_at and self.end_at <= self.start_at: raise ValueError("Thời gian kết thúc phải sau thời gian bắt đầu")
        return self
class LeadAppointmentUpdate(BaseModel):
    title: str|None=Field(default=None,min_length=1,max_length=255); description: str|None=None; appointment_type: str|None=None; start_at: datetime|None=None; end_at: datetime|None=None; location: str|None=None; meeting_link: str|None=None; assigned_to_id: UUID|None=None
class LeadAppointmentStatusUpdate(BaseModel): status: str; result_note: str|None=None; rescheduled_start_at: datetime|None=None; rescheduled_end_at: datetime|None=None

class LeadSummary(BaseModel):
    id: UUID; code: str; full_name: str; phone_primary: str
class UserSummary(BaseModel):
    id: UUID; full_name: str; email: str
class LeadAppointmentRead(BaseModel):
    id: UUID; lead_id: UUID; lead: LeadSummary; title: str; description: str|None; appointment_type: str; status: str; start_at: datetime; end_at: datetime|None; location: str|None; meeting_link: str|None; assigned_to_id: UUID; assigned_to: UserSummary; created_by: UserSummary; completed_by: UserSummary|None; completed_at: datetime|None; result_note: str|None; created_at: datetime; updated_at: datetime; is_overdue: bool
