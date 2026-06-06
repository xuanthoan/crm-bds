from uuid import UUID
from pydantic import BaseModel, Field

class MembershipCreate(BaseModel):
    user_id: UUID
    department_id: UUID | None = None
    team_id: UUID | None = None
    is_primary: bool = True
    position_title: str | None = Field(default=None, max_length=255)

class MembershipUpdate(BaseModel):
    department_id: UUID | None = None
    team_id: UUID | None = None
    is_primary: bool | None = None
    position_title: str | None = Field(default=None, max_length=255)

class LeadTransfer(BaseModel):
    new_owner_id: UUID
    reason: str = Field(min_length=1, max_length=1000)

class LeadReclaim(BaseModel):
    new_owner_id: UUID | None = None
    reason: str = Field(min_length=1, max_length=1000)
