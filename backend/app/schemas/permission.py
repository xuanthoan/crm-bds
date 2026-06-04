from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PermissionRead(BaseModel):
    id: UUID
    name: str
    code: str
    module: str
    description: str | None
    created_at: datetime


class PermissionGroup(BaseModel):
    module: str
    permissions: list[PermissionRead]
