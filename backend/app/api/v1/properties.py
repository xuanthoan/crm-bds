from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter,Depends,Query,status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.property_unit import PropertyPriceUpdate,PropertyStatusChange,PropertyUnitCreate,PropertyUnitUpdate
from app.services.property_service import change_property_status,create_property,get_property_detail,list_properties,serialize_property,serialize_property_detail,soft_delete_property,update_property,update_property_prices
router=APIRouter(prefix="/properties",tags=["properties"])
@router.get("")
def get_properties(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,project_id:UUID|None=None,property_type:str|None=None,inventory_status:str|None=None,legal_status:str|None=None,bedroom_count:int|None=Query(None,ge=0),price_min:Decimal|None=Query(None,ge=0),price_max:Decimal|None=Query(None,ge=0),area_min:Decimal|None=Query(None,ge=0),area_max:Decimal|None=Query(None,ge=0),province:str|None=None,district:str|None=None,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_properties(db,actor,page=page,page_size=page_size,q=q,project_id=project_id,property_type=property_type,inventory_status=inventory_status,legal_status=legal_status,bedroom_count=bedroom_count,price_min=price_min,price_max=price_max,area_min=area_min,area_max=area_max,province=province,district=district);return success_response([serialize_property(x) for x in items],meta=meta)
@router.post("",status_code=status.HTTP_201_CREATED)
def post_property(payload:PropertyUnitCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_property_detail(create_property(db,payload,actor)),"Tạo bất động sản thành công")
@router.get("/{property_id}")
def get_property(property_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_property_detail(get_property_detail(db,property_id,actor)))
@router.put("/{property_id}")
def put_property(property_id:UUID,payload:PropertyUnitUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_property_detail(update_property(db,property_id,payload,actor)),"Cập nhật bất động sản thành công")
@router.post("/{property_id}/status")
def post_status(property_id:UUID,payload:PropertyStatusChange,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_property_detail(change_property_status(db,property_id,payload,actor)),"Đổi trạng thái thành công")
@router.post("/{property_id}/prices")
def post_prices(property_id:UUID,payload:PropertyPriceUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_property_detail(update_property_prices(db,property_id,payload,actor)),"Cập nhật giá thành công")
@router.delete("/{property_id}")
def delete_property(property_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):soft_delete_property(db,property_id,actor);return success_response(None,"Xóa bất động sản thành công")
