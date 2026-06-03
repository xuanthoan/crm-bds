from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]


class RoleRead(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: list[str]

    model_config = ConfigDict(from_attributes=True)
