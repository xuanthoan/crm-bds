from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class AuditLogRead(BaseModel):
    id: UUID
    actor_id: UUID | None = None
    actor_name: str | None = None
    actor_email: str | None = None
    action: str
    action_label: str | None = None
    module: str
    module_label: str | None = None
    entity_type: str
    entity_id: str
    entity_label: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    changed_fields: dict | None = None
    description: str | None = None
    reason: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
