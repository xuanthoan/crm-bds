from datetime import date
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, user_has_permission
from fastapi import HTTPException, status
from app.services import commission_service as svc

router=APIRouter(prefix='/commissions',tags=['commissions'])
class GenerateIn(BaseModel): contract_id: UUID; commission_rate_percent: Decimal=Decimal('1'); note: str|None=None
class ApproveIn(BaseModel): approved_commission: Decimal|None=None; note: str|None=None; payout_policy_code: str|None=None
class PaidIn(BaseModel): paid_amount: Decimal|None=None; note: str|None=None
class HoldIn(BaseModel): hold_reason: str; note: str|None=None
class CancelIn(BaseModel): cancel_reason: str; note: str|None=None

def need(*codes):
    def dep(actor:User=Depends(require_auth)):
        if not any(user_has_permission(actor,c) for c in codes): raise HTTPException(status.HTTP_403_FORBIDDEN,'Missing required permission')
        return actor
    return dep

def filt(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),status:str|None=None,sale_id:UUID|None=None,contract_id:UUID|None=None,contract_code:str|None=None,keyword:str|None=None,date_from:date|None=None,date_to:date|None=None,approved_from:date|None=None,approved_to:date|None=None,paid_from:date|None=None,paid_to:date|None=None):
    return locals()

@router.get('')
def list_commissions(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('commissions.view','commissions.view.all','commissions.view.own','commissions.view.team'))):
    return success_response(svc.list_commissions(db,actor=actor,**f))
@router.get('/summary')
def summary(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('commissions.view','commissions.view.all','commissions.view.own','commissions.view.team'))):
    return success_response(svc.summary(db,**f))

@router.get('/eligible-contracts')
def eligible_contracts(keyword:str|None=None,page:int=Query(1,ge=1),page_size:int=Query(10,ge=1,le=50),db:Session=Depends(get_db),actor:User=Depends(need('commissions.create','commissions.update'))):
    return success_response(svc.search_eligible_contracts(db,keyword,page,page_size))
@router.get('/export')
def export(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('commissions.export'))):
    content=svc.export_csv(db,**f); return Response(content,media_type='text/csv; charset=utf-8',headers={'Content-Disposition': f'attachment; filename="danh-sach-hoa-hong-{date.today().isoformat()}.csv"'})
@router.post('/generate')
def generate(payload:GenerateIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.create','commissions.update'))):
    return success_response(svc.generate(db,payload.contract_id,payload.commission_rate_percent,payload.note,actor),'Đã tạo hoa hồng.')
@router.get('/{id}')
def detail(id:UUID,db:Session=Depends(get_db),actor:User=Depends(need('commissions.view','commissions.view.all','commissions.view.own','commissions.view.team'))):
    return success_response(svc.detail(svc.get_commission(db,id), actor))
@router.post('/{id}/approve')
def approve(id:UUID,payload:ApproveIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.approve'))): return success_response(svc.approve(db,id,payload.approved_commission,payload.note,actor,payload.payout_policy_code))
@router.post('/{id}/mark-paid')
def paid(id:UUID,payload:PaidIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.mark_paid'))): return success_response(svc.mark_paid(db,id,payload.paid_amount,payload.note,actor))
@router.post('/{id}/hold')
def hold(id:UUID,payload:HoldIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.hold','commissions.approve'))): return success_response(svc.hold(db,id,payload.hold_reason,payload.note,actor))
@router.post('/{id}/cancel')
def cancel(id:UUID,payload:CancelIn,db:Session=Depends(get_db),actor:User=Depends(need('commissions.cancel','commissions.approve'))): return success_response(svc.cancel(db,id,payload.cancel_reason,payload.note,actor))
