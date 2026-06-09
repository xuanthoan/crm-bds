import re
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.inventory.constants import COMMISSION_TYPE_LABELS, INVENTORY_STATUS_LABELS, LEGAL_STATUS_LABELS, PROPERTY_TYPE_LABELS
from app.schemas.customer import EMAIL_PATTERN, normalize_customer_phone

OPTIONAL_TEXT=("description","block","tower","floor","unit_number","door_direction","balcony_direction","view_description","commission_type","owner_name","owner_phone","owner_email","owner_note","legal_status","legal_note","media_images","media_videos","media_documents","media_drive_links","source","note")
MONEY=("listed_price","owner_price","minimum_price","last_transaction_price","commission_fixed")
AREA=("area_gross","area_net","balcony_area")
class PropertyFields(BaseModel):
    project_id:UUID|None=None; title:str|None=Field(default=None,max_length=255); description:str|None=None
    property_type:str|None=None; inventory_status:str|None=None
    block:str|None=None; tower:str|None=None; floor:str|None=None; unit_number:str|None=None
    bedroom_count:int|None=None; bathroom_count:int|None=None
    area_gross:Decimal|None=None; area_net:Decimal|None=None; balcony_area:Decimal|None=None
    door_direction:str|None=None; balcony_direction:str|None=None; view_description:str|None=None
    listed_price:Decimal|None=None; owner_price:Decimal|None=None; minimum_price:Decimal|None=None; last_transaction_price:Decimal|None=None
    commission_type:str|None=None; commission_fixed:Decimal|None=None; commission_rate:Decimal|None=None
    owner_name:str|None=None; owner_phone:str|None=None; owner_email:str|None=None; owner_note:str|None=None
    legal_status:str|None=None; legal_note:str|None=None
    media_images:str|None=None; media_videos:str|None=None; media_documents:str|None=None; media_drive_links:str|None=None
    source:str|None=None; note:str|None=None
    @field_validator(*OPTIONAL_TEXT,"project_id","bedroom_count","bathroom_count",*MONEY,*AREA,"commission_rate",mode="before")
    @classmethod
    def blank_to_none(cls,value:Any)->Any:return None if isinstance(value,str) and not value.strip() else value
    @field_validator("title",mode="before")
    @classmethod
    def title_value(cls,value:Any)->Any:
        if value is None:return None
        if not str(value).strip():raise ValueError("Tên bất động sản là bắt buộc")
        return str(value).strip()
    @field_validator("property_type")
    @classmethod
    def type_value(cls,value:str|None)->str|None:
        if value is not None and value not in PROPERTY_TYPE_LABELS:raise ValueError("Loại bất động sản không hợp lệ")
        return value
    @field_validator("inventory_status")
    @classmethod
    def status_value(cls,value:str|None)->str|None:
        if value is not None and value not in INVENTORY_STATUS_LABELS:raise ValueError("Trạng thái kho hàng không hợp lệ")
        return value
    @field_validator("legal_status")
    @classmethod
    def legal_value(cls,value:str|None)->str|None:
        if value is not None and value not in LEGAL_STATUS_LABELS:raise ValueError("Trạng thái pháp lý không hợp lệ")
        return value
    @field_validator("commission_type")
    @classmethod
    def commission_value(cls,value:str|None)->str|None:
        if value is not None and value not in COMMISSION_TYPE_LABELS:raise ValueError("Loại hoa hồng không hợp lệ")
        return value
    @field_validator(*MONEY)
    @classmethod
    def money_value(cls,value:Decimal|None)->Decimal|None:
        if value is not None and value<0:raise ValueError("Giá trị không hợp lệ")
        return value
    @field_validator(*AREA)
    @classmethod
    def area_value(cls,value:Decimal|None)->Decimal|None:
        if value is not None and value<0:raise ValueError("Diện tích không hợp lệ")
        return value
    @field_validator("bedroom_count","bathroom_count")
    @classmethod
    def count_value(cls,value:int|None)->int|None:
        if value is not None and value<0:raise ValueError("Giá trị không hợp lệ")
        return value
    @field_validator("commission_rate")
    @classmethod
    def rate_value(cls,value:Decimal|None)->Decimal|None:
        if value is not None and not 0<=value<=100:raise ValueError("Tỷ lệ hoa hồng phải từ 0 đến 100")
        return value
    @field_validator("owner_phone",mode="before")
    @classmethod
    def phone_value(cls,value:Any)->str|None:return normalize_customer_phone(None if value is None else str(value))
    @field_validator("owner_email")
    @classmethod
    def email_value(cls,value:str|None)->str|None:
        if value is None:return None
        value=value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(value):raise ValueError("Email không hợp lệ")
        return value
    @model_validator(mode="after")
    def compare_prices(self):
        if self.minimum_price is not None and self.listed_price is not None and self.minimum_price>self.listed_price:raise ValueError("Giá tối thiểu không được lớn hơn giá niêm yết")
        return self
class PropertyUnitCreate(PropertyFields):
    title:str=Field(max_length=255); property_type:str="apartment"; inventory_status:str|None="available"
class PropertyUnitUpdate(PropertyFields): pass
class PropertyStatusChange(BaseModel):
    inventory_status:str; note:str|None=None
    @field_validator("inventory_status")
    @classmethod
    def status_value(cls,value:str)->str:
        if value not in INVENTORY_STATUS_LABELS:raise ValueError("Trạng thái kho hàng không hợp lệ")
        return value
    @field_validator("note",mode="before")
    @classmethod
    def blank_note(cls,value:Any)->Any:return None if isinstance(value,str) and not value.strip() else value
class PropertyPriceUpdate(BaseModel):
    listed_price:Decimal|None=None; owner_price:Decimal|None=None; minimum_price:Decimal|None=None; last_transaction_price:Decimal|None=None; note:str|None=None
    @field_validator("listed_price","owner_price","minimum_price","last_transaction_price",mode="before")
    @classmethod
    def blank_number(cls,value:Any)->Any:return None if isinstance(value,str) and not value.strip() else value
    @field_validator("listed_price","owner_price","minimum_price","last_transaction_price")
    @classmethod
    def money_value(cls,value:Decimal|None)->Decimal|None:
        if value is not None and value<0:raise ValueError("Giá trị không hợp lệ")
        return value
    @model_validator(mode="after")
    def compare_prices(self):
        if self.minimum_price is not None and self.listed_price is not None and self.minimum_price>self.listed_price:raise ValueError("Giá tối thiểu không được lớn hơn giá niêm yết")
        return self
class PropertyRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:UUID; property_code:str; title:str; project:dict|None=None; property_type:str; property_type_label:str; inventory_status:str; inventory_status_label:str; bedroom_count:int|None=None; area_net:Decimal|None=None; listed_price:Decimal|None=None; owner_price:Decimal|None=None; minimum_price:Decimal|None=None; legal_status:str|None=None; legal_status_label:str|None=None; created_at:datetime
class PropertyDetail(PropertyRead):
    description:str|None=None; created_by:dict|None=None; updated_at:datetime; price_history:list[dict]=[]; status_history:list[dict]=[]
