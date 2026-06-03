from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    is_system: bool = False


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoleRead(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None
    is_system: bool
    permissions: list[str]
    created_at: datetime


class RolePermissionAssign(BaseModel):
    permission_codes: list[str]
