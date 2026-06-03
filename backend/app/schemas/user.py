from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserStatusValue = Literal["active", "inactive", "suspended", "resigned"]


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str | None = None
    status: UserStatusValue = "active"


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    role_codes: list[str] = []


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    status: UserStatusValue | None = None
    role_codes: list[str] | None = None


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None
    status: str
    is_superuser: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    roles: list[str]
    permissions: list[str]

    model_config = ConfigDict(from_attributes=True)


class PaginatedUsers(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int
