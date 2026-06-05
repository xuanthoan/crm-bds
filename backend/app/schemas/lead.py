from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LeadBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone_primary: str = Field(min_length=1, max_length=50)
    phone_secondary: str | None = None
    zalo: str | None = None
    facebook: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    source: str | None = None
    project_interest: str | None = None
    location_interest: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    bedroom_need: int | None = Field(default=None, ge=0)
    area_min: Decimal | None = None
    area_max: Decimal | None = None
    priority: str = "medium"
    next_follow_up_at: datetime | None = None
    note: str | None = None


class LeadCreate(LeadBase):
    owner_id: UUID | None = None


class LeadUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone_primary: str | None = Field(default=None, min_length=1, max_length=50)
    phone_secondary: str | None = None
    zalo: str | None = None
    facebook: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    source: str | None = None
    project_interest: str | None = None
    location_interest: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    bedroom_need: int | None = Field(default=None, ge=0)
    area_min: Decimal | None = None
    area_max: Decimal | None = None
    priority: str | None = None
    next_follow_up_at: datetime | None = None
    note: str | None = None


class LeadStatusUpdate(BaseModel):
    status: str
    lost_reason: str | None = None
    note: str | None = None


class LeadAssign(BaseModel):
    owner_id: UUID
    note: str | None = None
