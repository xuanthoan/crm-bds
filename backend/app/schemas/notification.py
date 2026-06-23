from uuid import UUID
from pydantic import BaseModel
class NotificationCreate(BaseModel):
    recipient_user_id: UUID
    title: str
    content: str | None = None
    notification_type: str = "system"
    related_task_id: UUID | None = None
    related_booking_id: UUID | None = None
    related_deal_id: UUID | None = None
    related_contract_id: UUID | None = None
    related_customer_id: UUID | None = None
    related_property_unit_id: UUID | None = None
