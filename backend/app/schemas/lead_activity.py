from pydantic import BaseModel, Field


class LeadActivityCreate(BaseModel):
    activity_type: str
    title: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=1)
