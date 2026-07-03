from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, user_has_permission
from app.services import commission_reconciliation_report_service as svc
router=APIRouter(prefix='/commission-reconciliation-report',tags=['commission-reconciliation-report'])
def need(code):
    def dep(actor:User=Depends(require_auth)):
        if not user_has_permission(actor,code): raise HTTPException(status.HTTP_403_FORBIDDEN,'Missing required permission')
        return actor
    return dep
def filt(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),date_from:date|None=None,date_to:date|None=None,project_id:UUID|None=None,sale_id:UUID|None=None,contract_id:UUID|None=None,customer_id:UUID|None=None,company_commission_status:str|None=None,sales_commission_status:str|None=None,voucher_status:str|None=None,reconciliation_status:str|None=None,q:str|None=None,has_draft_voucher:bool|None=None,only_blocked_by_policy:bool=False,only_has_remaining_sale_payable:bool=False): return locals()
@router.get('')
def report(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('reports.commission_reconciliation.view'))): return success_response(svc.list_report(db,actor=actor,**f))
@router.get('/export')
def export(f:dict=Depends(filt),db:Session=Depends(get_db),actor:User=Depends(need('reports.commission_reconciliation.export'))):
    content=svc.export_csv(db,actor=actor,**f); return Response(content,media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="doi-soat-hoa-hong-{date.today().isoformat()}.csv"'})
