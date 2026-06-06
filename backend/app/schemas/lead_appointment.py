from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
class LeadAppointmentCreate(BaseModel):
    lead_id: UUID; title: str = Field(min_length=1, max_length=255); description: str | None = None; appointment_type: str; start_at: datetime; end_at: datetime | None = None; location: str | None = None; meeting_link: str | None = None; assigned_to_id: UUID | None = None
class LeadAppointmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255); description: str | None = None; appointment_type: str | None = None; start_at: datetime | None = None; end_at: datetime | None = None; location: str | None = None; meeting_link: str | None = None; assigned_to_id: UUID | None = None
class LeadAppointmentStatusUpdate(BaseModel):
    status: str; result_note: str | None = None; rescheduled_start_at: datetime | None = None; rescheduled_end_at: datetime | None = None
