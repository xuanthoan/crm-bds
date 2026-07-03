from datetime import date
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.user import User
from app.permissions.dependencies import require_permission as need
from app.schemas.common import success_response
from app.services import commission_payment_voucher_service as svc

router=APIRouter(prefix='/commission-payment-vouchers',tags=['commission-payment-vouchers'])
class VoucherCreate(BaseModel):
    sales_commission_id: UUID; amount: Decimal; payment_date: date|None=None; payment_method: str='bank_transfer'; payment_reference: str|None=None; note: str|None=None; attachment_url: str|None=None; status: str|None='paid'
class VoucherUpdate(BaseModel):
    amount: Decimal|None=None; payment_date: date|None=None; payment_method: str|None=None; payment_reference: str|None=None; note: str|None=None; attachment_url: str|None=None
class MarkPaidIn(BaseModel):
    payment_date: date|None=None; payment_reference: str|None=None; note: str|None=None
class CancelIn(BaseModel): reason: str

def filt(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,sales_commission_id:UUID|None=None,contract_id:UUID|None=None,sale_id:UUID|None=None,status:str|None=None,payment_method:str|None=None,payment_date_from:date|None=None,payment_date_to:date|None=None):
    return locals()
@router.get('')
def list_items(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.view'))): return success_response(svc.list_vouchers(db,**f))
@router.get('/export')
def export(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.export'))): return Response(svc.export_csv(db,**f),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="phieu-chi-hoa-hong.csv"'})
@router.post('')
def create(payload:VoucherCreate,db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.create'))): return success_response(svc.create(db,payload,actor),'Đã lập phiếu chi hoa hồng sale.')
@router.get('/{id}')
def detail(id:UUID,db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.view'))): return success_response(svc.detail(svc.get(db,id)))
@router.patch('/{id}')
def update(id:UUID,payload:VoucherUpdate,db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.update'))): return success_response(svc.update(db,id,payload,actor),'Đã cập nhật phiếu chi.')
@router.post('/{id}/mark-paid')
def mark_paid(id:UUID,payload:MarkPaidIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.mark_paid'))): return success_response(svc.mark_paid(db,id,payload,actor),'Đã xác nhận chi phiếu hoa hồng.')
@router.post('/{id}/cancel')
def cancel(id:UUID,payload:CancelIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.payment_vouchers.cancel'))): return success_response(svc.cancel(db,id,payload.reason,actor),'Đã hủy phiếu chi hoa hồng.')
