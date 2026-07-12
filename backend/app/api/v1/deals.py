from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, require_permission
from app.schemas.deal import DealActivityCreate, DealAssignUpdate, DealCreate, DealStageUpdate, DealStatusUpdate, DealUpdate
from app.services.deal_service import add_deal_activity, assign_deal_owner, change_deal_stage, change_deal_status, create_deal, get_deal_detail, list_deal_assignees, list_deals, serialize_deal, serialize_deal_detail, soft_delete_deal, update_deal

router=APIRouter(prefix="/deals",tags=["deals"])

@router.get("")
def get_deals(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,customer_id:UUID|None=None,owner_id:UUID|None=None,pipeline_stage:str|None=None,status_filter:str|None=Query(None,alias="status"),priority:str|None=None,deal_type:str|None=None,expected_close_from:datetime|None=None,expected_close_to:datetime|None=None,created_from:datetime|None=None,created_to:datetime|None=None,date_from:datetime|None=None,date_to:datetime|None=None,stage:str|None=None,scope:str|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    if scope=="mine": owner_id=actor.id
    pipeline_stage=pipeline_stage or stage
    created_from=created_from or date_from
    created_to=created_to or date_to
    items,meta=list_deals(db,actor,page=page,page_size=page_size,q=q,customer_id=customer_id,owner_id=owner_id,pipeline_stage=pipeline_stage,status=status_filter,priority=priority,deal_type=deal_type,expected_close_from=expected_close_from,expected_close_to=expected_close_to,created_from=created_from,created_to=created_to)
    return success_response([serialize_deal(item) for item in items],meta=meta)

@router.post("",status_code=status.HTTP_201_CREATED)
def post_deal(payload:DealCreate,db:Session=Depends(get_db),actor:User=Depends(require_permission("deals.create"))): return success_response(serialize_deal_detail(create_deal(db,payload,actor)),"Tạo giao dịch thành công")

# Static routes must be declared before /{deal_id}.
@router.get("/assignees")
def get_assignees(db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response([{"id":u.id,"full_name":u.full_name,"email":u.email} for u in list_deal_assignees(db,actor)])

@router.get("/{deal_id}")
def get_deal(deal_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_deal_detail(get_deal_detail(db,deal_id,actor)))

@router.put("/{deal_id}")
def put_deal(deal_id:UUID,payload:DealUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_deal_detail(update_deal(db,deal_id,payload,actor)),"Cập nhật giao dịch thành công")

@router.post("/{deal_id}/stage")
def post_stage(deal_id:UUID,payload:DealStageUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_deal_detail(change_deal_stage(db,deal_id,payload,actor)),"Đổi giai đoạn thành công")

@router.post("/{deal_id}/status")
def post_status(deal_id:UUID,payload:DealStatusUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_deal_detail(change_deal_status(db,deal_id,payload,actor)),"Đổi trạng thái thành công")

@router.post("/{deal_id}/assign")
def post_assign(deal_id:UUID,payload:DealAssignUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(serialize_deal_detail(assign_deal_owner(db,deal_id,payload,actor)),"Phân công giao dịch thành công")

@router.post("/{deal_id}/activities",status_code=status.HTTP_201_CREATED)
def post_activity(deal_id:UUID,payload:DealActivityCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)): return success_response(add_deal_activity(db,deal_id,payload,actor) and serialize_deal_detail(get_deal_detail(db,deal_id,actor))["activities"][0],"Thêm hoạt động thành công")

@router.delete("/{deal_id}")
def delete_deal(deal_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)): soft_delete_deal(db,deal_id,actor); return success_response(None,"Xóa giao dịch thành công")
