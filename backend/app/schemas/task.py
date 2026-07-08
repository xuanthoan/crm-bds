from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class TaskBase(BaseModel):
    @field_validator("assigned_user_id", "primary_assignee_id", "assigned_to_id", mode="before")
    @classmethod
    def blank_assignee_to_none(cls, value):
        if value == "" or value is None:
            return None
        return value

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    task_type: str | None = "general"
    priority: str | None = "medium"
    due_at: datetime | None = None
    assigned_user_id: UUID | None = None
    primary_assignee_id: UUID | None = None
    assigned_to_id: UUID | None = None
    assignee_ids: list[UUID] | None = None
    watcher_ids: list[UUID] | None = None
    related_customer_id: UUID | None = None
    related_lead_id: UUID | None = None
    related_booking_id: UUID | None = None
    related_deal_id: UUID | None = None
    related_contract_id: UUID | None = None
    related_property_unit_id: UUID | None = None
    note: str | None = None
class TaskCreate(TaskBase):
    title: str = Field(..., min_length=1, max_length=255)
    task_type: str = "general"
class TaskUpdate(TaskBase):
    pass
class TaskStatusChange(BaseModel):
    status: str
    note: str | None = None
class TaskComplete(BaseModel):
    note: str | None = None
class TaskCancel(BaseModel):
    reason: str | None = None
class TaskNote(BaseModel):
    note: str = Field(..., min_length=1)


class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    @field_validator("content")
    @classmethod
    def trim_content(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Nội dung bình luận là bắt buộc")
        return value

class TaskRelatedLinkCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2048)
    note: str | None = Field(None, max_length=2000)
    @field_validator("title", "url", mode="before")
    @classmethod
    def trim_required(cls, value):
        return value.strip() if isinstance(value, str) else value
    @field_validator("url")
    @classmethod
    def http_only(cls, value):
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("URL phải bắt đầu bằng http:// hoặc https://")
        return value
