from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    is_system: bool = False
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    permission_codes: list[str] | None = None


class RoleRead(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None
    is_system: bool
    permission_count: int
    created_at: datetime
    updated_at: datetime


class RolePermissionAssign(BaseModel):
    permission_codes: list[str]
