from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

TASK_TYPES={"call","zalo","email","meeting","follow_up","document","other"}; TASK_PRIORITIES={"low","medium","high","urgent"}; TASK_STATUSES={"pending","in_progress","completed","cancelled"}
class LeadTaskCreate(BaseModel):
    lead_id: UUID; title: str = Field(min_length=1,max_length=255); description: str|None=None; task_type: str; priority: str="medium"; due_at: datetime; assigned_to_id: UUID|None=None; reminder_enabled: bool=True; reminder_at: datetime|None=None
    @model_validator(mode="after")
    def validate_fields(self):
        if self.task_type not in TASK_TYPES: raise ValueError("Loại công việc không hợp lệ")
        if self.priority not in TASK_PRIORITIES: raise ValueError("Mức ưu tiên không hợp lệ")
        if self.reminder_at and self.reminder_at > self.due_at: raise ValueError("Thời gian nhắc phải trước hoặc bằng hạn xử lý")
        return self
class LeadTaskUpdate(BaseModel):
    title: str|None=Field(default=None,min_length=1,max_length=255); description: str|None=None; task_type: str|None=None; priority: str|None=None; due_at: datetime|None=None; assigned_to_id: UUID|None=None; reminder_enabled: bool|None=None; reminder_at: datetime|None=None
class LeadTaskStatusUpdate(BaseModel): status: str; result_note: str|None=None

class LeadSummary(BaseModel):
    id: UUID; code: str; full_name: str; phone_primary: str
class UserSummary(BaseModel):
    id: UUID; full_name: str; email: str
class LeadTaskRead(BaseModel):
    id: UUID; lead_id: UUID; lead: LeadSummary; title: str; description: str|None; task_type: str; status: str; priority: str; due_at: datetime; assigned_to_id: UUID; assigned_to: UserSummary; created_by: UserSummary; completed_by: UserSummary|None; completed_at: datetime|None; cancelled_at: datetime|None; reminder_enabled: bool; reminder_at: datetime|None; result_note: str|None; created_at: datetime; updated_at: datetime; is_overdue: bool; hours_overdue: int; days_overdue: int
