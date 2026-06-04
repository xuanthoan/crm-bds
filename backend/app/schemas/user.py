from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str | None = None
    status: str = "active"


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    role_codes: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    status: str | None = None
    role_codes: list[str] | None = None


class UserResetPassword(BaseModel):
    new_password: str = Field(min_length=8)


class UserRoleRead(BaseModel):
    id: UUID
    code: str
    name: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None
    status: str
    is_superuser: bool
    last_login_at: datetime | None
    roles: list[UserRoleRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CurrentUser(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    status: str
    roles: list[str]
    permissions: list[str]
    is_superuser: bool
