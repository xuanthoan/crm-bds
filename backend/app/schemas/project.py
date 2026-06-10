from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.inventory.constants import PROJECT_STATUS_LABELS, PROJECT_TYPE_LABELS

class ProjectFields(BaseModel):
    name: str | None = Field(default=None, max_length=255); developer: str | None = Field(default=None, max_length=255)
    description: str | None = None; address: str | None = None; province: str | None = Field(default=None,max_length=100); district: str | None = Field(default=None,max_length=100); ward: str | None = Field(default=None,max_length=100)
    project_type: str | None = None; status: str | None = None
    @field_validator("developer","description","address","province","district","ward","project_type","status", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any: return None if isinstance(value,str) and not value.strip() else value
    @field_validator("name", mode="before")
    @classmethod
    def name_required(cls,value:Any)->str:
        if value is None or not str(value).strip(): raise ValueError("Tên dự án là bắt buộc")
        return str(value).strip()
    @field_validator("project_type")
    @classmethod
    def valid_type(cls,value:str|None)->str|None:
        if value is not None and value not in PROJECT_TYPE_LABELS: raise ValueError("Loại dự án không hợp lệ")
        return value
    @field_validator("status")
    @classmethod
    def valid_status(cls,value:str|None)->str|None:
        if value is not None and value not in PROJECT_STATUS_LABELS: raise ValueError("Trạng thái dự án không hợp lệ")
        return value
class ProjectCreate(ProjectFields):
    name: str = Field(max_length=255); status: str | None = "planning"
class ProjectUpdate(ProjectFields):
    name: str | None = Field(default=None,max_length=255)
    @field_validator("name", mode="before")
    @classmethod
    def optional_name(cls,value:Any)->Any:
        if value is None: return None
        if not str(value).strip(): raise ValueError("Tên dự án là bắt buộc")
        return str(value).strip()
class ProjectRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:UUID; project_code:str; name:str; developer:str|None=None; address:str|None=None; province:str|None=None; district:str|None=None; ward:str|None=None; project_type:str|None=None; project_type_label:str|None=None; status:str; status_label:str; created_at:datetime; updated_at:datetime
class ProjectDetail(ProjectRead):
    description:str|None=None; property_count:int=0
