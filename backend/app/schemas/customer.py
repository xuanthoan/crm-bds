from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

CustomerType = Literal["individual", "company", "investor", "agent", "other"]
CustomerStatus = Literal["active", "inactive", "potential", "vip", "blacklisted"]
CustomerPurpose = Literal["buy_to_live", "investment", "rent", "rent_out", "other"]


class CustomerFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    customer_type: CustomerType | None = None
    status: CustomerStatus | None = None
    primary_phone: str | None = Field(default=None, max_length=50)
    secondary_phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    zalo: str | None = Field(default=None, max_length=255)
    facebook: str | None = Field(default=None, max_length=500)
    address: str | None = None
    source: str | None = Field(default=None, max_length=80)
    interested_project: str | None = Field(default=None, max_length=255)
    interested_area: str | None = Field(default=None, max_length=255)
    budget_min: Decimal | None = Field(default=None, ge=0)
    budget_max: Decimal | None = Field(default=None, ge=0)
    bedroom_count: int | None = Field(default=None, ge=0)
    area_min: Decimal | None = Field(default=None, ge=0)
    area_max: Decimal | None = Field(default=None, ge=0)
    purpose: CustomerPurpose | None = None
    owner_id: UUID | None = None
    next_follow_up_at: datetime | None = None
    note: str | None = None


class CustomerCreate(CustomerFields):
    full_name: str = Field(min_length=1, max_length=255)
    primary_phone: str = Field(min_length=1, max_length=50)
    customer_type: CustomerType = "individual"
    status: CustomerStatus = "active"


class CustomerUpdate(CustomerFields):
    pass


class CustomerStatusUpdate(BaseModel):
    status: CustomerStatus
    note: str | None = None


class CustomerOwnerUpdate(BaseModel):
    owner_id: UUID
    note: str | None = None


class CustomerActivityCreate(BaseModel):
    activity_type: Literal["note", "call", "zalo", "email", "meeting", "other"]
    title: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=1)


class LeadConvertRequest(BaseModel):
    customer_type: CustomerType = "individual"
    status: CustomerStatus = "active"
    owner_id: UUID | None = None
    note: str | None = None
    merge_strategy: Literal["create_new", "reject_existing"] = "reject_existing"
