from pydantic import BaseModel, Field


class LeadActivityCreate(BaseModel):
    activity_type: str
    title: str | None = None
    content: str = Field(min_length=1)
