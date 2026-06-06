from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
class LeadTaskCreate(BaseModel):
    lead_id: UUID; title: str = Field(min_length=1, max_length=255); description: str | None = None; task_type: str; priority: str = "medium"; due_at: datetime; assigned_to_id: UUID | None = None; reminder_enabled: bool = True; reminder_at: datetime | None = None
class LeadTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255); description: str | None = None; task_type: str | None = None; priority: str | None = None; due_at: datetime | None = None; assigned_to_id: UUID | None = None; reminder_enabled: bool | None = None; reminder_at: datetime | None = None
class LeadTaskStatusUpdate(BaseModel):
    status: str; result_note: str | None = None
