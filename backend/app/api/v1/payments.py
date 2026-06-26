from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.payment import InvoiceAction, InvoiceCreate, PaymentScheduleCreate, PaymentScheduleUpdate, PenaltyApply, ReceiptCancel, ReceiptConfirm, ReceiptCreate
from app.services.payment_service import apply_penalty, cancel_invoice, cancel_receipt, cancel_schedule, confirm_receipt, create_invoice, create_receipt, create_schedule, get_invoice, get_receipt, get_schedule, issue_invoice, list_all_receipts, list_invoices, list_receipts, list_schedules, payment_summary, serialize_invoice, serialize_receipt, serialize_schedule, update_schedule
router=APIRouter(tags=['payments'])
@router.get('/payment-schedules')
def all(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,status_filter:str|None=Query(None,alias='status'),contract_id:UUID|None=None,deal_id:UUID|None=None,customer_id:UUID|None=None,overdue:bool|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_schedules(db,actor,page,page_size,q,status_filter,contract_id,deal_id,customer_id,overdue); return success_response([serialize_schedule(i) for i in items],meta=meta)
@router.post('/payment-schedules',status_code=status.HTTP_201_CREATED)
def post(payload:PaymentScheduleCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_schedule(create_schedule(db,payload,actor),True),'Tạo lịch thanh toán thành công')
@router.get('/payment-schedules/{payment_id}')
def get(payment_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_schedule(get_schedule(db,payment_id,actor),True))
@router.patch('/payment-schedules/{payment_id}')
def patch(payment_id:UUID,payload:PaymentScheduleUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_schedule(update_schedule(db,payment_id,payload,actor),True),'Cập nhật lịch thanh toán thành công')
@router.post('/payment-schedules/{payment_id}/cancel')
def cancel(payment_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_schedule(cancel_schedule(db,payment_id,actor),True),'Hủy lịch thanh toán thành công')
@router.post('/payment-schedules/{payment_id}/apply-penalty')
def penalty(payment_id:UUID,payload:PenaltyApply,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_schedule(apply_penalty(db,payment_id,payload,actor),True),'Áp dụng phí phạt thành công')
@router.post('/payment-schedules/{payment_id}/receipts',status_code=status.HTTP_201_CREATED)
def receipt_post(payment_id:UUID,payload:ReceiptCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_receipt(create_receipt(db,payment_id,payload,actor)),'Tạo phiếu thu thành công')
@router.get('/payment-schedules/{payment_id}/receipts')
def receipts(payment_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response([serialize_receipt(r) for r in list_receipts(db,payment_id,actor)])

@router.get('/payment-receipts')
def receipt_list(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,status_filter:str|None=Query(None,alias='status'),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_all_receipts(db,actor,page,page_size,q,status_filter); return success_response([serialize_receipt(i) for i in items],meta=meta)
@router.get('/payment-receipts/{receipt_id}')
def receipt_get(receipt_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_receipt(get_receipt(db,receipt_id,actor)))
@router.post('/payment-receipts/{receipt_id}/confirm')
def receipt_confirm_alias(receipt_id:UUID,payload:ReceiptConfirm,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_receipt(confirm_receipt(db,receipt_id,payload,actor)),'Xác nhận phiếu thu thành công')
@router.post('/payment-receipts/{receipt_id}/cancel')
def receipt_cancel_alias(receipt_id:UUID,payload:ReceiptCancel,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_receipt(cancel_receipt(db,receipt_id,payload,actor)),'Hủy phiếu thu thành công')
@router.get('/invoices')
def invoice_list(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,status_filter:str|None=Query(None,alias='status'),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_invoices(db,actor,page,page_size,q,status_filter); return success_response([serialize_invoice(i) for i in items],meta=meta)
@router.get('/invoices/{invoice_id}')
def invoice_get(invoice_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_invoice(get_invoice(db,invoice_id,actor)))
@router.post('/invoices',status_code=status.HTTP_201_CREATED)
def invoice_post(payload:InvoiceCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    if not payload.receipt_id and not getattr(payload,'payment_schedule_id',None): from fastapi import HTTPException; raise HTTPException(400,'Lịch thanh toán là bắt buộc.')
    return success_response(serialize_invoice(create_invoice(db,getattr(payload,'payment_schedule_id'),payload,actor)),'Tạo hóa đơn nháp thành công')
@router.post('/invoices/{invoice_id}/issue')
def invoice_issue(invoice_id:UUID,payload:InvoiceAction,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_invoice(issue_invoice(db,invoice_id,payload,actor)),'Phát hành hóa đơn thành công')
@router.post('/invoices/{invoice_id}/cancel')
def invoice_cancel(invoice_id:UUID,payload:InvoiceAction,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_invoice(cancel_invoice(db,invoice_id,payload,actor)),'Hủy hóa đơn thành công')

@router.post('/receipts/{receipt_id}/confirm')
def receipt_confirm(receipt_id:UUID,payload:ReceiptConfirm,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_receipt(confirm_receipt(db,receipt_id,payload,actor)),'Xác nhận thanh toán thành công')
@router.post('/receipts/{receipt_id}/cancel')
def receipt_cancel(receipt_id:UUID,payload:ReceiptCancel,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_receipt(cancel_receipt(db,receipt_id,payload,actor)),'Hủy phiếu thu thành công')
@router.post('/payment-schedules/{payment_id}/invoice',status_code=status.HTTP_201_CREATED)
def invoice(payment_id:UUID,payload:InvoiceCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_invoice(create_invoice(db,payment_id,payload,actor)),'Tạo hóa đơn nháp thành công')
@router.get('/contracts/{contract_id}/payment-schedules')
def by_contract(contract_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,_=list_schedules(db,actor,1,100,None,None,contract_id,None,None,None); return success_response([serialize_schedule(i) for i in items])
@router.get('/contracts/{contract_id}/payment-summary')
def summary(contract_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(payment_summary(db,contract_id))
