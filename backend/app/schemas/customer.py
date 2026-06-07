import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

CustomerType = Literal["individual", "company", "investor", "agent", "other"]
CustomerStatus = Literal["active", "inactive", "potential", "vip", "blacklisted"]
CustomerPurpose = Literal["buy_to_live", "investment", "rent", "rent_out", "other"]

PHONE_PATTERN = re.compile(r"^\+?[\d\s-]+$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_customer_phone(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not PHONE_PATTERN.fullmatch(value):
        raise ValueError("Số điện thoại không hợp lệ")
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("84"):
        digits = f"0{digits[2:]}"
    if len(digits) != 10 or not digits.startswith("0"):
        raise ValueError("Số điện thoại không hợp lệ")
    return digits


class CustomerFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    customer_type: CustomerType | None = None
    status: CustomerStatus | None = None
    primary_phone: str | None = Field(default=None, max_length=50)
    secondary_phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
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

    @field_validator(
        "secondary_phone",
        "email",
        "zalo",
        "facebook",
        "address",
        "source",
        "interested_project",
        "interested_area",
        "purpose",
        "owner_id",
        "next_follow_up_at",
        "note",
        "budget_min",
        "budget_max",
        "bedroom_count",
        "area_min",
        "area_max",
        mode="before",
    )
    @classmethod
    def empty_optional_value_to_none(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("primary_phone", "secondary_phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> str | None:
        if value is None:
            return None
        return normalize_customer_phone(str(value))

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Email không hợp lệ")
        return value


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
