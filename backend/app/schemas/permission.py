from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PermissionRead(BaseModel):
    id: UUID
    name: str
    code: str
    module: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionGroup(BaseModel):
    module: str
    permissions: list[PermissionRead]
