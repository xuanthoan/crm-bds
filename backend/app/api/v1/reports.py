from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.services.report_service import ReportFilters, build_csv, get_cash_collection_report, get_finance_summary, get_invoice_report, get_overdue_payment_report, get_receivable_report, require_finance_export

router = APIRouter(prefix='/reports/finance', tags=['reports'])

def filters(date_from:date|None=None,date_to:date|None=None,project_id:UUID|None=None,property_id:UUID|None=None,sale_id:UUID|None=None,assigned_user_id:UUID|None=None,contract_status:str|None=None,payment_status:str|None=None,lead_source:str|None=None,customer_keyword:str|None=Query(None, alias='customer'),contract_keyword:str|None=Query(None, alias='contract_code'),status:str|None=None,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100)):
    return ReportFilters(date_from,date_to,project_id,property_id,sale_id,assigned_user_id,contract_status,payment_status,lead_source,customer_keyword,contract_keyword,status,page,page_size)

@router.get('/summary')
def summary(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(get_finance_summary(db,f,actor))
@router.get('/receivables')
def receivables(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(get_receivable_report(db,f,actor))
@router.get('/overdue-payments')
def overdue(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(get_overdue_payment_report(db,f,actor))
@router.get('/cash-collection')
def cash(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(get_cash_collection_report(db,f,actor))
@router.get('/invoices')
def invoices(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(get_invoice_report(db,f,actor))

def csv_response(content:str, name:str):
    return Response(content, media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{name}-{date.today().isoformat()}.csv"'})

@router.get('/receivables/export')
def receivables_export(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    require_finance_export(actor); items=get_receivable_report(db,f,actor,False)['items']; rows=[[i['contract_id'],i['contract_code'],i['customer_name'],i['customer_phone'],i['sale_name'],i['contract_status_label'],i['contract_value'],i['deposit_value'],i['confirmed_receipts_amount'],i['total_collected_amount'],i['remaining_amount'],i['payment_status'],i['oldest_overdue_due_date'],i['max_overdue_days'],i['overdue_amount'],i['aging_bucket']] for i in items]
    return csv_response(build_csv(['ID hợp đồng','Mã hợp đồng','Khách hàng','Số điện thoại','Sale phụ trách','Trạng thái HĐ','Giá trị HĐ','Tiền cọc','Đã thu phiếu thu','Tổng đã thu','Còn phải thu','Trạng thái thanh toán','Ngày quá hạn lâu nhất','Số ngày quá hạn','Số tiền quá hạn','Nhóm tuổi nợ'], rows),'bao-cao-cong-no')
@router.get('/overdue-payments/export')
def overdue_export(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    require_finance_export(actor); items=get_overdue_payment_report(db,f,actor,False)['items']; rows=[[i['payment_id'],i['payment_code'],i['contract_id'],i['contract_code'],i['customer_name'],i['sale_name'],i['installment_name'],i['installment_no'],i['due_date'],i['amount_due'],i['paid_amount'],i['remaining_amount'],i['overdue_days'],i['payment_status'],i['contract_status']] for i in items]
    return csv_response(build_csv(['ID PMT','Mã PMT','ID hợp đồng','Mã hợp đồng','Khách hàng','Sale phụ trách','Tên đợt','Số thứ tự','Ngày đến hạn','Phải thu','Đã thu','Còn lại','Số ngày quá hạn','Trạng thái PMT','Trạng thái HĐ'], rows),'bao-cao-pmt-qua-han')
@router.get('/cash-collection/export')
def cash_export(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    require_finance_export(actor); items=get_cash_collection_report(db,f,actor,False)['items']; rows=[[i['receipt_id'],i['receipt_code'],i['receipt_date'],i['customer_name'],i['contract_code'],i['payment_code'],i['installment_name'],i['amount'],i['payment_method_label'],i['created_by_name'],i['status_label'],i['cancel_reason']] for i in items]
    return csv_response(build_csv(['ID phiếu thu','Mã phiếu thu','Ngày thu','Khách hàng','Mã hợp đồng','Mã PMT','Đợt thanh toán','Số tiền','Phương thức','Người tạo','Trạng thái','Lý do hủy'], rows),'bao-cao-dong-tien')
@router.get('/invoices/export')
def invoice_export(f:ReportFilters=Depends(filters),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    require_finance_export(actor); items=get_invoice_report(db,f,actor,False)['items']; rows=[[i['invoice_id'],i['invoice_code'],i['created_at'],i['issued_date'],i['customer_name'],i['contract_code'],i['payment_code'],i['receipt_code'],i['amount'],i['status_label'],i['cancel_reason'],i['created_by_name']] for i in items]
    return csv_response(build_csv(['ID hóa đơn','Mã hóa đơn','Ngày tạo','Ngày phát hành','Khách hàng','Mã hợp đồng','Mã PMT','Mã phiếu thu','Số tiền','Trạng thái','Lý do hủy','Người tạo'], rows),'bao-cao-hoa-don')
