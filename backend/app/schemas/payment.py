from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator
from app.payments_constants import INVOICE_STATUS_LABELS, PAYMENT_METHOD_LABELS, PAYMENT_STATUS_LABELS, RECEIPT_STATUS_LABELS

class PaymentScheduleCreate(BaseModel):
    contract_id: UUID; sequence_no:int; title:str; due_date:date; expected_amount:Decimal; note:str|None=None
    @field_validator('expected_amount')
    @classmethod
    def amount(cls,v):
        if v <= 0: raise ValueError('Số tiền phải thu phải lớn hơn 0.')
        return v
class PaymentScheduleUpdate(BaseModel):
    sequence_no:int|None=None; title:str|None=None; due_date:date|None=None; expected_amount:Decimal|None=None; note:str|None=None
    @field_validator('expected_amount')
    @classmethod
    def amount(cls,v):
        if v is not None and v <= 0: raise ValueError('Số tiền phải thu phải lớn hơn 0.')
        return v
class PenaltyApply(BaseModel):
    penalty_amount:Decimal; penalty_reason:str|None=None
    @model_validator(mode='after')
    def valid(self):
        if self.penalty_amount < 0: raise ValueError('Phí phạt không được âm.')
        if self.penalty_amount > 0 and not (self.penalty_reason or '').strip(): raise ValueError('Phí phạt phải có lý do.')
        return self
class ReceiptCreate(BaseModel):
    amount:Decimal; payment_date:date|None=None; payment_method:str|None=None; reference_no:str|None=None; note:str|None=None; status:str='draft'
    @model_validator(mode='after')
    def valid(self):
        if self.amount <= 0: raise ValueError('Số tiền thanh toán phải lớn hơn 0.')
        if self.status not in RECEIPT_STATUS_LABELS: raise ValueError('Trạng thái phiếu thu không hợp lệ.')
        if self.status == 'confirmed' and self.payment_date is None: raise ValueError('Ngày thanh toán là bắt buộc khi xác nhận.')
        if self.payment_method is not None and self.payment_method not in PAYMENT_METHOD_LABELS: raise ValueError('Phương thức thanh toán không hợp lệ.')
        return self
class ReceiptConfirm(BaseModel):
    payment_date:date|None=None; payment_method:str|None=None; reference_no:str|None=None; note:str|None=None
class ReceiptCancel(BaseModel):
    cancel_reason:str|None=None; note:str|None=None
    @model_validator(mode='after')
    def valid(self):
        if not (self.cancel_reason or self.note or '').strip(): raise ValueError('Lý do hủy phiếu thu là bắt buộc.')
        return self
class InvoiceCreate(BaseModel):
    payment_schedule_id:UUID|None=None; amount:Decimal|None=None; issued_date:date|None=None; due_date:date|None=None; status:str='draft'; receipt_id:UUID|None=None; description:str|None=None; note:str|None=None
    @model_validator(mode='after')
    def valid(self):
        if self.amount is not None and self.amount <= 0: raise ValueError('Số tiền hóa đơn phải lớn hơn 0.')
        if self.status not in INVOICE_STATUS_LABELS: raise ValueError('Trạng thái hóa đơn không hợp lệ.')
        return self

class InvoiceAction(BaseModel):
    issue_date:date|None=None; cancel_reason:str|None=None; note:str|None=None
    @model_validator(mode='after')
    def cancel_valid(self):
        return self
