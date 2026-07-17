from uuid import UUID
from fastapi import APIRouter,Depends,Query,status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth,require_permission
from app.schemas.contract import ContractActivityCreate,ContractCreate,ContractPaymentConfirm,ContractPaymentCreate,ContractPaymentUpdate,ContractStatusChange,ContractUpdate
from app.services.contract_service import add_contract_activity,change_contract_status,confirm_contract_payment,create_contract,create_contract_payment,get_contract_detail,list_contract_payments,list_contracts,serialize_contract,serialize_payment,soft_delete_contract,soft_delete_contract_payment,update_contract,update_contract_payment
router=APIRouter(prefix="/contracts",tags=["contracts"])
@router.get("")
def get_all(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,status_filter:str|None=Query(None,alias="status"),contract_type:str|None=None,customer_id:UUID|None=None,property_unit_id:UUID|None=None,project_id:UUID|None=None,scope:str|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
 items,meta=list_contracts(db,actor,page,page_size,q,status_filter,contract_type,customer_id,property_unit_id,project_id,scope);return success_response([serialize_contract(i) for i in items],meta=meta)
@router.post("",status_code=status.HTTP_201_CREATED)
def post(payload:ContractCreate,db:Session=Depends(get_db),actor:User=Depends(require_permission("contracts.create"))):return success_response(serialize_contract(create_contract(db,payload,actor),True),"Tạo hợp đồng thành công")
@router.get("/{contract_id}")
def get(contract_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_contract(get_contract_detail(db,contract_id,actor),True))
@router.put("/{contract_id}")
def put(contract_id:UUID,payload:ContractUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_contract(update_contract(db,contract_id,payload,actor),True),"Cập nhật hợp đồng thành công")
@router.post("/{contract_id}/status")
def status_change(contract_id:UUID,payload:ContractStatusChange,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_contract(change_contract_status(db,contract_id,payload,actor),True),"Đổi trạng thái hợp đồng thành công")
@router.delete("/{contract_id}")
def delete(contract_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):soft_delete_contract(db,contract_id,actor);return success_response(None,"Xóa hợp đồng thành công")
@router.get("/{contract_id}/payments")
def payments(contract_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response([serialize_payment(p) for p in list_contract_payments(db,contract_id,actor)])
@router.post("/{contract_id}/payments",status_code=status.HTTP_201_CREATED)
def post_payment(contract_id:UUID,payload:ContractPaymentCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_payment(create_contract_payment(db,contract_id,payload,actor)),"Tạo thanh toán thành công")
@router.put("/{contract_id}/payments/{payment_id}")
def put_payment(contract_id:UUID,payment_id:UUID,payload:ContractPaymentUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_payment(update_contract_payment(db,contract_id,payment_id,payload,actor)),"Cập nhật thanh toán thành công")
@router.post("/{contract_id}/payments/{payment_id}/confirm")
def confirm(contract_id:UUID,payment_id:UUID,payload:ContractPaymentConfirm,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_payment(confirm_contract_payment(db,contract_id,payment_id,payload,actor)),"Xác nhận thanh toán thành công")
@router.delete("/{contract_id}/payments/{payment_id}")
def delete_payment(contract_id:UUID,payment_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):soft_delete_contract_payment(db,contract_id,payment_id,actor);return success_response(None,"Xóa thanh toán thành công")
@router.post("/{contract_id}/activities",status_code=status.HTTP_201_CREATED)
def activity(contract_id:UUID,payload:ContractActivityCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
 c=get_contract_detail(db,contract_id,actor);a=add_contract_activity(db,c,actor,"note",payload.title,payload.content,metadata=payload.metadata);db.commit();db.refresh(a);return success_response(serialize_contract(c,True)["activities"][0],"Thêm hoạt động thành công")
