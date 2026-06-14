from datetime import datetime, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.inventory.constants import INVENTORY_STATUS_LABELS, LEGAL_STATUS_LABELS, PRICE_FIELD_LABELS, PROPERTY_TYPE_LABELS
from app.inventory.history import collect_price_changes
from app.models.project import Project
from app.models.property_price_history import PropertyPriceHistory
from app.models.property_status_history import PropertyStatusHistory
from app.models.property_unit import PropertyUnit
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.property_unit import PropertyPriceUpdate, PropertyStatusChange, PropertyUnitCreate, PropertyUnitUpdate
from app.services.audit_service import write_audit_log
from app.services.organization_service import get_accessible_user_ids_for_lead_scope
PRICE_FIELDS=("listed_price","owner_price","minimum_price","last_transaction_price")
def _scope(actor:User,prefix:str)->str|None:
    if actor.is_superuser:return "all"
    permissions=set(get_user_permissions(actor))
    for scope in ("all","department","team","own"):
        if f"{prefix}.{scope}" in permissions:return scope
    return None
def _ids(db:Session,actor:User,scope:str)->set[UUID]:return get_accessible_user_ids_for_lead_scope(db,actor,scope)
def _can(db:Session,actor:User,item:PropertyUnit,prefix:str)->bool:
    scope=_scope(actor,prefix)
    return bool(scope and (scope=="all" or item.created_by_id in _ids(db,actor,scope)))
def _require(db:Session,actor:User,item:PropertyUnit,prefix:str,message:str)->None:
    if not _can(db,actor,item,prefix):raise HTTPException(status_code=403,detail=message)
def _project(db:Session,project_id:UUID|None)->Project|None:
    if project_id is None:return None
    item=db.scalar(select(Project).where(Project.id==project_id,Project.deleted_at.is_(None)))
    if not item:raise HTTPException(status_code=400,detail="Dự án không tồn tại")
    return item
def _get(db:Session,property_id:UUID)->PropertyUnit:
    item=db.scalar(select(PropertyUnit).where(PropertyUnit.id==property_id,PropertyUnit.deleted_at.is_(None)))
    if not item:raise HTTPException(status_code=404,detail="Bất động sản không tồn tại")
    return item
def _user(user:User|None)->dict|None:return {"id":user.id,"full_name":user.full_name,"email":user.email} if user else None
def _project_summary(project:Project|None)->dict|None:return {"id":project.id,"project_code":project.project_code,"name":project.name,"province":project.province,"district":project.district,"status":project.status} if project else None
def serialize_property(item:PropertyUnit)->dict:
    return {"id":item.id,"property_code":item.property_code,"title":item.title,"project":_project_summary(item.project),"project_id":item.project_id,"description":item.description,"property_type":item.property_type,"property_type_label":PROPERTY_TYPE_LABELS.get(item.property_type,item.property_type),"inventory_status":item.inventory_status,"inventory_status_label":INVENTORY_STATUS_LABELS.get(item.inventory_status,item.inventory_status),"block":item.block,"tower":item.tower,"floor":item.floor,"unit_number":item.unit_number,"bedroom_count":item.bedroom_count,"bathroom_count":item.bathroom_count,"area_gross":item.area_gross,"area_net":item.area_net,"listed_price":item.listed_price,"owner_price":item.owner_price,"minimum_price":item.minimum_price,"legal_status":item.legal_status,"legal_status_label":LEGAL_STATUS_LABELS.get(item.legal_status),"created_at":item.created_at}
def serialize_property_detail(item:PropertyUnit)->dict:
    data=serialize_property(item)
    for field in ("block","tower","floor","unit_number","area_gross","balcony_area","door_direction","balcony_direction","view_description","last_transaction_price","commission_type","commission_fixed","commission_rate","owner_name","owner_phone","owner_email","owner_note","legal_note","media_images","media_videos","media_documents","media_drive_links","source","note","updated_at"):
        data[field]=getattr(item,field)
    data["created_by"]=_user(item.creator)
    data["price_history"]=[{"id":h.id,"field_name":h.field_name,"field_label":PRICE_FIELD_LABELS.get(h.field_name,h.field_name),"old_value":h.old_value,"new_value":h.new_value,"note":h.note,"changed_by":_user(h.changed_by),"created_at":h.created_at} for h in item.price_history]
    data["deals"]=[{"id":d.id,"deal_code":d.deal_code,"title":d.title,"status":d.status} for d in item.deals if d.deleted_at is None]
    data["contracts"]=[{"id":c.id,"contract_code":c.contract_code,"status":c.status,"contract_value":c.contract_value} for c in item.contracts if c.deleted_at is None]
    data["status_history"]=[{"id":h.id,"old_status":h.old_status,"old_status_label":INVENTORY_STATUS_LABELS.get(h.old_status) if h.old_status else None,"new_status":h.new_status,"new_status_label":INVENTORY_STATUS_LABELS.get(h.new_status,h.new_status),"note":h.note,"changed_by":_user(h.changed_by),"created_at":h.created_at} for h in item.status_history]
    return data
def _next_code(db:Session)->str:
    # TODO: Replace with database sequence for high-concurrency production.
    codes=db.scalars(select(PropertyUnit.property_code).where(PropertyUnit.property_code.like("PROP-%")))
    numbers=[int(code.removeprefix("PROP-")) for code in codes if code.removeprefix("PROP-").isdigit()]
    return f"PROP-{max(numbers,default=0)+1:06d}"
def _validate_prices(item:PropertyUnit)->None:
    if item.minimum_price is not None and item.listed_price is not None and item.minimum_price>item.listed_price:raise HTTPException(status_code=400,detail="Giá tối thiểu không được lớn hơn giá niêm yết")
def list_properties(db:Session,actor:User,*,page:int=1,page_size:int=20,q:str|None=None,project_id:UUID|None=None,property_type:str|None=None,inventory_status:str|None=None,legal_status:str|None=None,bedroom_count:int|None=None,price_min=None,price_max=None,area_min=None,area_max=None,province:str|None=None,district:str|None=None)->tuple[list[PropertyUnit],dict]:
    scope=_scope(actor,"inventory.properties.view")
    if not scope:raise HTTPException(status_code=403,detail="Bạn không có quyền xem kho hàng")
    query=select(PropertyUnit).outerjoin(Project).where(PropertyUnit.deleted_at.is_(None))
    if scope!="all":query=query.where(PropertyUnit.created_by_id.in_(_ids(db,actor,scope)))
    if q:
        term=f"%{q.strip()}%"; query=query.where(or_(PropertyUnit.property_code.ilike(term),PropertyUnit.title.ilike(term),PropertyUnit.owner_phone.ilike(term),Project.name.ilike(term)))
    for column,value in ((PropertyUnit.project_id,project_id),(PropertyUnit.property_type,property_type),(PropertyUnit.inventory_status,inventory_status),(PropertyUnit.legal_status,legal_status),(PropertyUnit.bedroom_count,bedroom_count),(Project.province,province),(Project.district,district)):
        if value is not None and value!="":query=query.where(column==value)
    if price_min is not None:query=query.where(PropertyUnit.listed_price>=price_min)
    if price_max is not None:query=query.where(PropertyUnit.listed_price<=price_max)
    if area_min is not None:query=query.where(PropertyUnit.area_net>=area_min)
    if area_max is not None:query=query.where(PropertyUnit.area_net<=area_max)
    total=db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items=list(db.scalars(query.order_by(PropertyUnit.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique().all())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_property_detail(db:Session,property_id:UUID,actor:User)->PropertyUnit:
    item=_get(db,property_id); _require(db,actor,item,"inventory.properties.view","Bạn không có quyền xem bất động sản này"); return item
def create_property(db:Session,payload:PropertyUnitCreate,actor:User)->PropertyUnit:
    if not actor.is_superuser and "inventory.properties.create" not in set(get_user_permissions(actor)):raise HTTPException(status_code=403,detail="Bạn không có quyền tạo bất động sản")
    _project(db,payload.project_id); item=PropertyUnit(property_code=_next_code(db),created_by_id=actor.id,**payload.model_dump(exclude_none=True)); _validate_prices(item); db.add(item); db.flush()
    db.add(PropertyStatusHistory(property_unit_id=item.id,changed_by_id=actor.id,old_status=None,new_status=item.inventory_status,note="Khởi tạo bất động sản"))
    for field in PRICE_FIELDS:
        value=getattr(item,field)
        if value is not None:db.add(PropertyPriceHistory(property_unit_id=item.id,changed_by_id=actor.id,field_name=field,old_value=None,new_value=value,note="Khởi tạo bất động sản"))
    write_audit_log(db,action="inventory.properties.create",user_id=actor.id,entity_type="property_units",entity_id=str(item.id),after_data={"property_code":item.property_code,"title":item.title}); db.commit(); db.refresh(item); return item
def update_property(db:Session,property_id:UUID,payload:PropertyUnitUpdate,actor:User)->PropertyUnit:
    item=_get(db,property_id); _require(db,actor,item,"inventory.properties.update","Bạn không có quyền cập nhật bất động sản này")
    data=payload.model_dump(exclude_unset=True); _project(db,data.get("project_id")) if "project_id" in data else None
    price_changes=collect_price_changes(item,data,PRICE_FIELDS)
    if price_changes:_require(db,actor,item,"inventory.properties.price.update","Bạn không có quyền cập nhật giá bất động sản này")
    old_status=item.inventory_status
    for key,value in data.items():setattr(item,key,value)
    _validate_prices(item); item.updated_by_id=actor.id
    for field,old,new in price_changes:db.add(PropertyPriceHistory(property_unit_id=item.id,changed_by_id=actor.id,field_name=field,old_value=old,new_value=new))
    if "inventory_status" in data and item.inventory_status!=old_status:
        _require(db,actor,item,"inventory.properties.status","Bạn không có quyền đổi trạng thái bất động sản này"); db.add(PropertyStatusHistory(property_unit_id=item.id,changed_by_id=actor.id,old_status=old_status,new_status=item.inventory_status))
    write_audit_log(db,action="inventory.properties.update",user_id=actor.id,entity_type="property_units",entity_id=str(item.id),after_data={"title":item.title}); db.commit(); db.refresh(item); return item
def change_property_status(db:Session,property_id:UUID,payload:PropertyStatusChange,actor:User)->PropertyUnit:
    item=_get(db,property_id); _require(db,actor,item,"inventory.properties.status","Bạn không có quyền đổi trạng thái bất động sản này")
    old=item.inventory_status
    if old!=payload.inventory_status:
        item.inventory_status=payload.inventory_status; item.updated_by_id=actor.id; db.add(PropertyStatusHistory(property_unit_id=item.id,changed_by_id=actor.id,old_status=old,new_status=item.inventory_status,note=payload.note))
    write_audit_log(db,action="inventory.properties.status_change",user_id=actor.id,entity_type="property_units",entity_id=str(item.id),before_data={"inventory_status":old},after_data={"inventory_status":item.inventory_status}); db.commit(); db.refresh(item); return item
def update_property_prices(db:Session,property_id:UUID,payload:PropertyPriceUpdate,actor:User)->PropertyUnit:
    item=_get(db,property_id); _require(db,actor,item,"inventory.properties.price.update","Bạn không có quyền cập nhật giá bất động sản này")
    data=payload.model_dump(exclude={"note"},exclude_unset=True); changes=collect_price_changes(item,data,PRICE_FIELDS)
    for field,_old,new in changes:setattr(item,field,new)
    _validate_prices(item); item.updated_by_id=actor.id
    for field,old,new in changes:db.add(PropertyPriceHistory(property_unit_id=item.id,changed_by_id=actor.id,field_name=field,old_value=old,new_value=new,note=payload.note))
    write_audit_log(db,action="inventory.properties.price_update",user_id=actor.id,entity_type="property_units",entity_id=str(item.id),after_data={"changed_fields":[x[0] for x in changes]}); db.commit(); db.refresh(item); return item
def soft_delete_property(db:Session,property_id:UUID,actor:User)->None:
    item=_get(db,property_id); _require(db,actor,item,"inventory.properties.delete","Bạn không có quyền xóa bất động sản này")
    item.deleted_at=datetime.now(timezone.utc);item.deleted_by_id=actor.id
    write_audit_log(db,action="inventory.properties.delete",user_id=actor.id,entity_type="property_units",entity_id=str(item.id),before_data={"property_code":item.property_code,"title":item.title});db.commit()
