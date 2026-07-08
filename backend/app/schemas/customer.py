import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from app.services.phone_service import normalize_phone

from app.customers.constants import (
    BUYING_PURPOSE_LABELS, BUYING_TIMELINE_LABELS, FINANCIAL_RATING_LABELS,
    GENDER_LABELS, PROPERTY_TYPE_LABELS, RELATED_PERSON_RELATIONSHIP_LABELS,
)

CustomerType = Literal["individual", "company", "investor", "agent", "other"]
CustomerStatus = Literal["active", "inactive", "potential", "vip", "blacklisted"]
CustomerPurpose = Literal["buy_to_live", "investment", "rent", "rent_out", "other"]
PHONE_PATTERN = re.compile(r"^\+?[\d\s-]+$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")


def normalize_customer_phone(value: str | None) -> str | None:
    return normalize_phone(value)


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
    gender: str | None = None
    date_of_birth: date | None = None
    province: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    occupation: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)
    expected_budget: Decimal | None = None
    available_cash: Decimal | None = None
    loan_needed: Decimal | None = None
    loan_ratio: Decimal | None = None
    preferred_bank: str | None = Field(default=None, max_length=255)
    monthly_income: Decimal | None = None
    financial_rating: str | None = None
    buying_purpose: str | None = None
    interested_property_type: str | None = None
    preferred_direction: str | None = Field(default=None, max_length=100)
    preferred_view: str | None = Field(default=None, max_length=255)
    buying_timeline: str | None = None
    related_people_note: str | None = None
    source: str | None = Field(default=None, max_length=80)
    interested_project: str | None = Field(default=None, max_length=255)
    interested_area: str | None = Field(default=None, max_length=255)
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    bedroom_count: int | None = None
    area_min: Decimal | None = None
    area_max: Decimal | None = None
    purpose: CustomerPurpose | None = None
    owner_id: UUID | None = None
    next_follow_up_at: datetime | None = None
    note: str | None = None

    @field_validator("secondary_phone", "email", "zalo", "facebook", "address", "gender", "province", "district", "occupation", "company", "job_title", "preferred_bank", "financial_rating", "buying_purpose", "interested_property_type", "preferred_direction", "preferred_view", "buying_timeline", "related_people_note", "source", "interested_project", "interested_area", "purpose", "owner_id", "next_follow_up_at", "note", "date_of_birth", "expected_budget", "available_cash", "loan_needed", "loan_ratio", "monthly_income", "budget_min", "budget_max", "bedroom_count", "area_min", "area_max", mode="before")
    @classmethod
    def empty_optional_value_to_none(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("primary_phone", "secondary_phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> str | None:
        return normalize_customer_phone(None if value is None else str(value))

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Email không hợp lệ")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("Ngày sinh không hợp lệ")
        return value

    @field_validator("expected_budget", "available_cash", "loan_needed", "monthly_income", "budget_min", "budget_max", "area_min", "area_max")
    @classmethod
    def validate_non_negative_decimal(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("Giá trị tài chính không hợp lệ")
        return value

    @field_validator("bedroom_count")
    @classmethod
    def validate_non_negative_integer(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("Giá trị tài chính không hợp lệ")
        return value

    @field_validator("loan_ratio")
    @classmethod
    def validate_loan_ratio(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not 0 <= value <= 100:
            raise ValueError("Tỷ lệ vay phải từ 0 đến 100")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if value is not None and value not in GENDER_LABELS:
            raise ValueError("Giới tính không hợp lệ")
        return value

    @field_validator("financial_rating")
    @classmethod
    def validate_financial_rating(cls, value: str | None) -> str | None:
        if value is not None and value not in FINANCIAL_RATING_LABELS:
            raise ValueError("Xếp hạng tài chính không hợp lệ")
        return value

    @field_validator("buying_purpose")
    @classmethod
    def validate_buying_purpose(cls, value: str | None) -> str | None:
        if value is not None and value not in BUYING_PURPOSE_LABELS:
            raise ValueError("Mục đích mua không hợp lệ")
        return value

    @field_validator("interested_property_type")
    @classmethod
    def validate_property_type(cls, value: str | None) -> str | None:
        if value is not None and value not in PROPERTY_TYPE_LABELS:
            raise ValueError("Loại hình quan tâm không hợp lệ")
        return value

    @field_validator("buying_timeline")
    @classmethod
    def validate_buying_timeline(cls, value: str | None) -> str | None:
        if value is not None and value not in BUYING_TIMELINE_LABELS:
            raise ValueError("Timeline mua không hợp lệ")
        return value


class CustomerCreate(CustomerFields):
    full_name: str = Field(min_length=1, max_length=255)
    primary_phone: str = Field(min_length=1, max_length=50)
    customer_type: CustomerType = "individual"
    status: CustomerStatus = "active"


class CustomerUpdate(CustomerFields):
    pass


class CustomerScoreRead(BaseModel):
    score_total: int
    score_label: str | None
    score_note: str | None
    score_updated_at: datetime | None


class CustomerRelatedPersonFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    relationship: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    note: str | None = None

    @field_validator("phone", "email", "note", mode="before")
    @classmethod
    def empty_to_none(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> str | None:
        return normalize_customer_phone(None if value is None else str(value))

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Email không hợp lệ")
        return value

    @field_validator("relationship")
    @classmethod
    def validate_relationship(cls, value: str | None) -> str | None:
        if value is not None and value not in RELATED_PERSON_RELATIONSHIP_LABELS:
            raise ValueError("Mối quan hệ không hợp lệ")
        return value


class CustomerRelatedPersonCreate(CustomerRelatedPersonFields):
    full_name: str = Field(min_length=1, max_length=255)
    relationship: str


class CustomerRelatedPersonUpdate(CustomerRelatedPersonFields):
    pass


class CustomerRelatedPersonRead(BaseModel):
    id: UUID
    full_name: str
    relationship: str
    phone: str | None
    email: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime


class CustomerRead(CustomerFields):
    id: UUID
    customer_code: str
    score_total: int = 0
    score_label: str | None = None
    score_updated_at: datetime | None = None
    score_note: str | None = None


class CustomerDetail(CustomerRead):
    related_people: list[CustomerRelatedPersonRead] = []


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
