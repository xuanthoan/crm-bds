from datetime import date
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, user_has_permission
from app.services import company_commission_service as svc

router=APIRouter(prefix='/company-commissions',tags=['company-commissions'])
class GenerateIn(BaseModel): contract_id: UUID; commission_rate_percent: Decimal; expected_commission_amount: Decimal|None=None; expected_receive_date: date|None=None; note: str|None=None
class ApproveIn(BaseModel): confirmed_receivable_amount: Decimal; note: str|None=None
class ReceiveIn(BaseModel): amount_received_now: Decimal; received_date: date|None=None; note: str|None=None
class HoldIn(BaseModel): hold_reason: str; note: str|None=None
class CancelIn(BaseModel): cancel_reason: str; note: str|None=None

def need(code):
    def dep(actor:User=Depends(require_auth)):
        if not user_has_permission(actor,code): raise HTTPException(status.HTTP_403_FORBIDDEN,'Bạn không có quyền thực hiện thao tác này.')
        return actor
    return dep

def filt(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),status:str|None=None,keyword:str|None=None,contract_id:UUID|None=None,from_date:date|None=None,to_date:date|None=None,payer_type:str|None=None,company_role:str|None=None): return locals()
@router.get('')
def list_items(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.view'))): return success_response(svc.list_receivables(db,**f))
@router.get('/summary')
def summary(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.view'))): return success_response(svc.summary(db,**f))
@router.get('/eligible-contracts')
def eligible(keyword:str|None=None,limit:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.create'))): return success_response(svc.eligible_contracts(db,keyword,limit))
@router.post('/generate')
def generate(payload:GenerateIn,db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.create'))): return success_response(svc.generate(db,payload.contract_id,payload.commission_rate_percent,payload.expected_commission_amount,payload.expected_receive_date,payload.note,actor),'Đã tạo hoa hồng công ty.')
@router.get('/export')
def export(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.export'))): return Response(svc.export_csv(db,**f),media_type='text/csv; charset=utf-8',headers={'Content-Disposition': f'attachment; filename="hoa-hong-cong-ty-{date.today().isoformat()}.csv"'})
@router.get('/{id}')
def detail(id:UUID,db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.view'))): return success_response(svc.detail(svc._get(db,id)))
@router.post('/{id}/approve')
def approve(id:UUID,payload:ApproveIn,db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.approve'))): return success_response(svc.approve(db,id,payload.confirmed_receivable_amount,payload.note,actor),'Đã duyệt hoa hồng công ty.')
@router.post('/{id}/receive')
def receive(id:UUID,payload:ReceiveIn,db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.receive'))): return success_response(svc.receive(db,id,payload.amount_received_now,payload.received_date,payload.note,actor),'Đã ghi nhận tiền hoa hồng công ty.')
@router.post('/{id}/hold')
def hold(id:UUID,payload:HoldIn,db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.hold'))): return success_response(svc.hold(db,id,payload.hold_reason,payload.note,actor),'Đã tạm giữ hoa hồng công ty.')
@router.post('/{id}/cancel')
def cancel(id:UUID,payload:CancelIn,db:Session=Depends(get_db),actor:User=Depends(need('company_commissions.cancel'))): return success_response(svc.cancel(db,id,payload.cancel_reason,payload.note,actor),'Đã hủy hoa hồng công ty.')
