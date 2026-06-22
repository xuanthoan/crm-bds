from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.deals.constants import DEAL_ACTIVITY_TYPES, DEAL_PRIORITIES, DEAL_STATUSES, DEAL_TYPES, PIPELINE_STAGES

OPTIONAL_TEXT_FIELDS = {"description", "project_name", "property_code", "property_type", "area", "lost_reason"}
MONEY_FIELDS = ("expected_value", "deposit_amount", "contract_value", "commission_expected")

def _blank_to_none(value: Any) -> Any:
    return None if isinstance(value, str) and not value.strip() else value.strip() if isinstance(value, str) else value

class DealFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = None; description: str | None = None
    deal_type: str | None = None; pipeline_stage: str | None = None; status: str | None = None; priority: str | None = None
    property_unit_id: UUID | None = None; project_id: UUID | None = None
    project_name: str | None = None; property_code: str | None = None; property_type: str | None = None; area: str | None = None
    expected_value: Decimal | None = None; deposit_amount: Decimal | None = None; contract_value: Decimal | None = None; commission_expected: Decimal | None = None
    expected_close_date: datetime | None = None; deposit_date: datetime | None = None; contract_date: datetime | None = None; closed_at: datetime | None = None
    lost_reason: str | None = None

    @field_validator("title", *OPTIONAL_TEXT_FIELDS, mode="before")
    @classmethod
    def normalize_text(cls, value: Any) -> Any: return _blank_to_none(value)

    @field_validator(*MONEY_FIELDS, mode="before")
    @classmethod
    def normalize_money(cls, value: Any) -> Any:
        if value is None or value == "": return None
        try: result = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc: raise ValueError("Giá trị tiền không hợp lệ") from exc
        if not result.is_finite() or result < 0: raise ValueError("Giá trị tiền không hợp lệ")
        return result

    @model_validator(mode="after")
    def validate_values(self):
        if self.deal_type is not None and self.deal_type not in DEAL_TYPES: raise ValueError("Loại giao dịch không hợp lệ")
        if self.pipeline_stage is not None and self.pipeline_stage not in PIPELINE_STAGES: raise ValueError("Giai đoạn giao dịch không hợp lệ")
        if self.status is not None and self.status not in DEAL_STATUSES: raise ValueError("Trạng thái giao dịch không hợp lệ")
        if self.priority is not None and self.priority not in DEAL_PRIORITIES: raise ValueError("Ưu tiên không hợp lệ")
        if self.contract_value is not None and self.deposit_amount is not None and self.contract_value < self.deposit_amount: raise ValueError("Giá trị hợp đồng phải lớn hơn hoặc bằng tiền đặt cọc")
        if self.status in {"lost", "cancelled"} and not self.lost_reason: raise ValueError("Vui lòng nhập lý do thất bại/hủy giao dịch")
        if self.pipeline_stage == "lost" and not self.lost_reason: raise ValueError("Vui lòng nhập lý do thất bại/hủy giao dịch")
        return self

class DealCreate(DealFields):
    customer_id: UUID; source_lead_id: UUID | None = None; owner_id: UUID
    title: str
    deal_type: str = "apartment"; pipeline_stage: str = "new"; status: str = "open"; priority: str = "medium"

class DealUpdate(DealFields): pass
class DealStageUpdate(DealFields):
    pipeline_stage: str
    note: str | None = None
class DealStatusUpdate(BaseModel):
    status: str; lost_reason: str | None = None; note: str | None = None; closed_at: datetime | None = None
    @field_validator("lost_reason", "note", mode="before")
    @classmethod
    def normalize_text(cls, value): return _blank_to_none(value)
    @model_validator(mode="after")
    def validate_status(self):
        if self.status not in DEAL_STATUSES: raise ValueError("Trạng thái giao dịch không hợp lệ")
        if self.status in {"lost", "cancelled"} and not self.lost_reason: raise ValueError("Vui lòng nhập lý do thất bại/hủy giao dịch")
        return self
class DealAssignUpdate(BaseModel): owner_id: UUID; note: str | None = None
class DealActivityCreate(BaseModel):
    activity_type: str; title: str; content: str | None = None; metadata_json: dict | None = None
    @field_validator("title", "content", mode="before")
    @classmethod
    def normalize_text(cls, value): return _blank_to_none(value)
    @field_validator("activity_type")
    @classmethod
    def valid_type(cls, value):
        if value not in DEAL_ACTIVITY_TYPES: raise ValueError("Loại hoạt động không hợp lệ")
        return value
