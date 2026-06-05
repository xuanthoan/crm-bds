from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LeadFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    phone_primary: str | None = Field(default=None, max_length=50)
    phone_secondary: str | None = Field(default=None, max_length=50)
    zalo: str | None = Field(default=None, max_length=255)
    facebook: str | None = Field(default=None, max_length=500)
    email: EmailStr | None = None
    address: str | None = None
    source: str | None = Field(default=None, max_length=80)
    project_interest: str | None = Field(default=None, max_length=255)
    location_interest: str | None = Field(default=None, max_length=255)
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    bedroom_need: int | None = Field(default=None, ge=0)
    area_min: Decimal | None = Field(default=None, ge=0)
    area_max: Decimal | None = Field(default=None, ge=0)
    priority: str | None = None
    next_follow_up_at: datetime | None = None
    note: str | None = None


class LeadCreate(LeadFields):
    full_name: str = Field(min_length=1, max_length=255)
    phone_primary: str = Field(min_length=1, max_length=50)
    priority: str = "medium"
    owner_id: UUID | None = None


class LeadUpdate(LeadFields):
    pass


class LeadStatusUpdate(BaseModel):
    status: str
    lost_reason: str | None = Field(default=None, max_length=500)
    note: str | None = None


class LeadAssign(BaseModel):
    owner_id: UUID
    note: str | None = None
