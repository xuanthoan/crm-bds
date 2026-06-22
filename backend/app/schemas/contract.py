from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator
from app.contracts.constants import CONTRACT_STATUS_LABELS, CONTRACT_TYPE_LABELS, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, PAYMENT_TYPE_LABELS

def positive(value: Decimal | None, message: str):
    if value is None: raise ValueError("Giá trị hợp đồng là bắt buộc")
    if value <= 0: raise ValueError(message)
    return value
class ContractCreate(BaseModel):
    deal_id: UUID; contract_value: Decimal; contract_type:str="deposit_contract"; status:str="draft"; contract_number:str|None=None; signed_date:datetime|None=None; effective_date:datetime|None=None; handover_date:datetime|None=None; deposit_value:Decimal|None=None; buyer_name:str|None=None; buyer_phone:str|None=None; buyer_email:str|None=None; buyer_id_number:str|None=None; buyer_address:str|None=None; seller_name:str|None=None; seller_phone:str|None=None; seller_email:str|None=None; seller_representative:str|None=None; note:str|None=None
    _value=field_validator("contract_value")(lambda v: positive(v,"Giá trị hợp đồng phải lớn hơn 0"))
    @model_validator(mode="after")
    def valid(self):
        if self.status not in CONTRACT_STATUS_LABELS: raise ValueError("Trạng thái hợp đồng không hợp lệ")
        if self.contract_type not in CONTRACT_TYPE_LABELS: raise ValueError("Loại hợp đồng không hợp lệ")
        return self
class ContractUpdate(BaseModel):
    contract_value:Decimal|None=None; contract_type:str|None=None; status:str|None=None; contract_number:str|None=None; signed_date:datetime|None=None; effective_date:datetime|None=None; handover_date:datetime|None=None; deposit_value:Decimal|None=None; buyer_name:str|None=None; buyer_phone:str|None=None; buyer_email:str|None=None; buyer_id_number:str|None=None; buyer_address:str|None=None; seller_name:str|None=None; seller_phone:str|None=None; seller_email:str|None=None; seller_representative:str|None=None; note:str|None=None
    @field_validator("contract_value")
    @classmethod
    def value(cls,v): return positive(v,"Giá trị hợp đồng phải lớn hơn 0") if v is not None else v
class ContractStatusChange(BaseModel): status:str; note:str|None=None
class ContractPaymentCreate(BaseModel):
    contract_id:UUID|None=None; amount:Decimal; payment_type:str="payment"; status:str="planned"; due_date:datetime|None=None; paid_date:datetime|None=None; payment_method:str|None=None; reference_number:str|None=None; note:str|None=None
    _amount=field_validator("amount")(lambda v: positive(v,"Số tiền thanh toán phải lớn hơn 0"))
    @model_validator(mode="after")
    def valid(self):
        if self.status not in PAYMENT_STATUS_LABELS: raise ValueError("Trạng thái thanh toán không hợp lệ")
        if self.payment_type not in PAYMENT_TYPE_LABELS: raise ValueError("Loại thanh toán không hợp lệ")
        return self
class ContractPaymentUpdate(BaseModel):
    payment_type:str|None=None; status:str|None=None; amount:Decimal|None=None; due_date:datetime|None=None; paid_date:datetime|None=None; payment_method:str|None=None; reference_number:str|None=None; note:str|None=None
    @field_validator("amount")
    @classmethod
    def amount_positive(cls,v): return positive(v,"Số tiền thanh toán phải lớn hơn 0") if v is not None else v
    @field_validator("payment_method")
    @classmethod
    def method(cls,v):
        if v is not None and v not in PAYMENT_METHOD_LABELS: raise ValueError("Phương thức thanh toán không hợp lệ")
        return v
class ContractPaymentConfirm(BaseModel):
    paid_date:datetime|None=None; payment_method:str|None=None; reference_number:str|None=None; note:str|None=None
    @field_validator("payment_method")
    @classmethod
    def method(cls,v):
        if v is not None and v not in PAYMENT_METHOD_LABELS: raise ValueError("Phương thức thanh toán không hợp lệ")
        return v
class ContractActivityCreate(BaseModel): title:str; content:str|None=None; metadata:dict[str,Any]|None=None
class BookingDealCreate(BaseModel): expected_value:Decimal|None=None; title:str|None=None; note:str|None=None
