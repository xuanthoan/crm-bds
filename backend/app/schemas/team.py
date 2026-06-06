from uuid import UUID
from pydantic import BaseModel, Field

class TeamCreate(BaseModel):
    department_id: UUID
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    leader_id: UUID | None = None
    status: str = "active"

class TeamUpdate(BaseModel):
    department_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    leader_id: UUID | None = None
    status: str | None = None
