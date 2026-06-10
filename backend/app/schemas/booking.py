from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.bookings.constants import BOOKING_STATUS_LABELS

BookingStatus = Literal["draft", "reserved", "deposited", "cancelled", "expired", "refunded"]

def _non_negative_amount(value: Decimal | None) -> Decimal | None:
    if value is not None and value < 0:
        raise ValueError("Số tiền không hợp lệ")
    return value


def _require_booking_amount_input(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("Tiền giữ chỗ là bắt buộc")
    return value


def _positive_booking_amount(value: Decimal | None) -> Decimal | None:
    if value is None:
        raise ValueError("Tiền giữ chỗ là bắt buộc")
    if value <= 0:
        raise ValueError("Tiền giữ chỗ phải lớn hơn 0")
    return value


def _optional_positive_booking_amount(value: Decimal | None) -> Decimal | None:
    if value is not None and value <= 0:
        raise ValueError("Tiền giữ chỗ phải lớn hơn 0")
    return value


def _positive_deposit_amount(value: Decimal | None) -> Decimal | None:
    if value is not None and value <= 0:
        raise ValueError("Tiền cọc phải lớn hơn 0")
    return value

class BookingCreate(BaseModel):
    customer_id: UUID; property_unit_id: UUID; assigned_user_id: UUID
    source_lead_id: UUID | None = None; source_deal_id: UUID | None = None
    booking_amount: Decimal | None = None; deposit_amount: Decimal | None = None
    booking_date: datetime | None = None; reservation_expires_at: datetime | None = None; deposit_date: datetime | None = None; note: str | None = None
    _require_booking_amount_input = field_validator("booking_amount", mode="before")(_require_booking_amount_input)
    _validate_booking_amount = field_validator("booking_amount")(_positive_booking_amount)
    _validate_deposit_amount = field_validator("deposit_amount")(_positive_deposit_amount)

    @model_validator(mode="after")
    def require_booking_amount(self):
        if self.booking_amount is None:
            raise ValueError("Tiền giữ chỗ là bắt buộc")
        return self

class BookingUpdate(BaseModel):
    assigned_user_id: UUID | None = None; booking_amount: Decimal | None = None; deposit_amount: Decimal | None = None
    reservation_expires_at: datetime | None = None; deposit_date: datetime | None = None; note: str | None = None
    _require_booking_amount_input = field_validator("booking_amount", mode="before")(_require_booking_amount_input)
    _validate_booking_amount = field_validator("booking_amount")(_positive_booking_amount)
    _validate_deposit_amount = field_validator("deposit_amount")(_positive_deposit_amount)

class BookingStatusChange(BaseModel):
    status: BookingStatus
    booking_amount: Decimal | None = None; deposit_amount: Decimal | None = None; refund_amount: Decimal | None = None
    reservation_expires_at: datetime | None = None; deposit_date: datetime | None = None
    cancel_reason: str | None = None; refund_reason: str | None = None; note: str | None = None
    _validate_booking_amount = field_validator("booking_amount")(_optional_positive_booking_amount)
    _validate_deposit_amount = field_validator("deposit_amount")(_positive_deposit_amount)
    _validate_refund_amount = field_validator("refund_amount")(_non_negative_amount)

    @model_validator(mode="after")
    def validate_status_requirements(self):
        if self.status not in BOOKING_STATUS_LABELS: raise ValueError("Trạng thái booking không hợp lệ")
        if self.status == "deposited" and self.deposit_amount is None: raise ValueError("Tiền cọc là bắt buộc khi đặt cọc")
        if self.status == "cancelled" and not (self.cancel_reason or "").strip(): raise ValueError("Lý do hủy là bắt buộc")
        if self.status == "refunded":
            if self.refund_amount is None: raise ValueError("Số tiền hoàn là bắt buộc")
            if not (self.refund_reason or "").strip(): raise ValueError("Lý do hoàn tiền là bắt buộc")
        return self

class BookingActivityCreate(BaseModel):
    title: str = Field(min_length=1); content: str | None = None

class UserSummary(BaseModel): id: UUID; full_name: str; email: str
class CustomerSummary(BaseModel): id: UUID; customer_code: str; full_name: str; primary_phone: str | None = None
class ProjectSummary(BaseModel): id: UUID; project_code: str; name: str
class PropertySummary(BaseModel): id: UUID; property_code: str; title: str; inventory_status: str; project: ProjectSummary | None = None
class SourceSummary(BaseModel): id: UUID; code: str; title: str | None = None
class BookingActivityRead(BaseModel):
    id: UUID; activity_type: str; activity_label: str; title: str; content: str | None; old_value: str | None; new_value: str | None; actor: UserSummary; created_at: datetime
class BookingRead(BaseModel):
    id: UUID; booking_code: str; customer: CustomerSummary; property: PropertySummary; assigned_user: UserSummary
    status: str; status_label: str; booking_amount: Decimal | None; deposit_amount: Decimal | None; reservation_expires_at: datetime | None; created_at: datetime
class BookingDetail(BookingRead):
    customer_id: UUID; property_unit_id: UUID; source_lead_id: UUID | None; source_deal_id: UUID | None; assigned_user_id: UUID
    refund_amount: Decimal | None; booking_date: datetime | None; deposit_date: datetime | None; cancelled_at: datetime | None; refunded_at: datetime | None
    cancel_reason: str | None; refund_reason: str | None; note: str | None; source_lead: SourceSummary | None; source_deal: SourceSummary | None
    created_by: UserSummary; updated_by: UserSummary | None; updated_at: datetime; activities: list[BookingActivityRead]
