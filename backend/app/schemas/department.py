from uuid import UUID
from pydantic import BaseModel, Field

class DepartmentCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    manager_id: UUID | None = None
    status: str = "active"

class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    manager_id: UUID | None = None
    status: str | None = None
