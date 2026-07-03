from datetime import datetime, timezone
from math import ceil
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.inventory.constants import PROJECT_STATUS_LABELS, PROJECT_TYPE_LABELS
from app.models.project import Project
from app.models.property_unit import PropertyUnit
from app.models.user import User
from app.permissions.dependencies import get_user_permissions
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.audit_service import write_audit_log

PROPERTY_ACCESS_PREFIX="inventory.properties."
def _permissions(actor:User)->set[str]: return set(get_user_permissions(actor))
def can_view_projects(actor:User)->bool: return actor.is_superuser or "inventory.projects.view.all" in _permissions(actor) or any(p.startswith(PROPERTY_ACCESS_PREFIX) for p in _permissions(actor))
def can_view_commission_policy(actor:User)->bool: return actor.is_superuser or "projects.view_commission_policy" in _permissions(actor) or "projects.manage_commission_policy" in _permissions(actor)
def can_manage_commission_policy(actor:User)->bool: return actor.is_superuser or "projects.manage_commission_policy" in _permissions(actor)
def _require(actor:User,code:str,message:str)->None:
    if not actor.is_superuser and code not in _permissions(actor): raise HTTPException(status_code=403,detail=message)
def _get(db:Session,project_id:UUID)->Project:
    item=db.scalar(select(Project).where(Project.id==project_id,Project.deleted_at.is_(None)))
    if not item: raise HTTPException(status_code=404,detail="Dự án không tồn tại")
    return item
def serialize_project(item:Project,property_count:int|None=None,actor:User|None=None)->dict:
    can_view_sensitive = bool(actor and can_view_commission_policy(actor))
    data={"id":item.id,"project_code":item.project_code,"name":item.name,"developer":item.developer,"description":item.description,"address":item.address,"province":item.province,"district":item.district,"ward":item.ward,"project_type":item.project_type,"project_type_label":PROJECT_TYPE_LABELS.get(item.project_type),"status":item.status,"status_label":PROJECT_STATUS_LABELS.get(item.status,item.status),"sales_commission_payout_policy_default":item.sales_commission_payout_policy_default,"sales_commission_policy_note":item.sales_commission_policy_note,"created_at":item.created_at,"updated_at":item.updated_at}
    if can_view_sensitive: data["company_commission_policy_note"]=item.company_commission_policy_note
    if property_count is not None:data["property_count"]=property_count
    return data
def _next_code(db:Session)->str:
    # TODO: Replace with database sequence for high-concurrency production.
    codes=db.scalars(select(Project.project_code).where(Project.project_code.like("PRJ-%")))
    numbers=[int(code.removeprefix("PRJ-")) for code in codes if code.removeprefix("PRJ-").isdigit()]
    return f"PRJ-{max(numbers,default=0)+1:06d}"
def list_projects(db:Session,actor:User,*,page:int=1,page_size:int=20,q:str|None=None,developer:str|None=None,province:str|None=None,district:str|None=None,project_type:str|None=None,status:str|None=None)->tuple[list[Project],dict]:
    if not can_view_projects(actor):raise HTTPException(status_code=403,detail="Bạn không có quyền xem dự án")
    query=select(Project).where(Project.deleted_at.is_(None))
    if q:
        term=f"%{q.strip()}%"; query=query.where(or_(Project.project_code.ilike(term),Project.name.ilike(term),Project.developer.ilike(term),Project.address.ilike(term)))
    for column,value in ((Project.developer,developer),(Project.province,province),(Project.district,district),(Project.project_type,project_type),(Project.status,status)):
        if value:query=query.where(column==value)
    total=db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items=list(db.scalars(query.order_by(Project.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all())
    return items,{"page":page,"page_size":page_size,"total":total,"total_pages":ceil(total/page_size) if total else 0}
def get_project_detail(db:Session,project_id:UUID,actor:User)->tuple[Project,int]:
    if not can_view_projects(actor):raise HTTPException(status_code=403,detail="Bạn không có quyền xem dự án")
    item=_get(db,project_id); count=db.scalar(select(func.count(PropertyUnit.id)).where(PropertyUnit.project_id==item.id,PropertyUnit.deleted_at.is_(None))) or 0
    return item,count
def create_project(db:Session,payload:ProjectCreate,actor:User)->Project:
    _require(actor,"inventory.projects.create","Bạn không có quyền tạo dự án")
    data=payload.model_dump(exclude_none=True)
    if any(k in data for k in ("sales_commission_payout_policy_default","sales_commission_policy_note","company_commission_policy_note")) and not can_manage_commission_policy(actor): raise HTTPException(status_code=403,detail="Bạn không có quyền quản lý chính sách hoa hồng dự án")
    item=Project(project_code=_next_code(db),created_by_id=actor.id,**data); db.add(item); db.flush()
    write_audit_log(db,action="inventory.projects.create",user_id=actor.id,entity_type="projects",entity_id=str(item.id),after_data={"project_code":item.project_code,"name":item.name}); db.commit(); db.refresh(item); return item
def update_project(db:Session,project_id:UUID,payload:ProjectUpdate,actor:User)->Project:
    _require(actor,"inventory.projects.update","Bạn không có quyền cập nhật dự án"); item=_get(db,project_id); before={"name":item.name,"status":item.status}
    data=payload.model_dump(exclude_unset=True)
    if any(k in data for k in ("sales_commission_payout_policy_default","sales_commission_policy_note","company_commission_policy_note")) and not can_manage_commission_policy(actor): raise HTTPException(status_code=403,detail="Bạn không có quyền quản lý chính sách hoa hồng dự án")
    for key,value in data.items():setattr(item,key,value)
    item.updated_by_id=actor.id; write_audit_log(db,action="inventory.projects.update",user_id=actor.id,entity_type="projects",entity_id=str(item.id),before_data=before,after_data={"name":item.name,"status":item.status}); db.commit(); db.refresh(item); return item
def soft_delete_project(db:Session,project_id:UUID,actor:User)->None:
    _require(actor,"inventory.projects.delete","Bạn không có quyền xóa dự án"); item=_get(db,project_id)
    active_property_count=db.scalar(select(func.count(PropertyUnit.id)).where(PropertyUnit.project_id==item.id,PropertyUnit.deleted_at.is_(None))) or 0
    if active_property_count>0:
        raise HTTPException(
            status_code=409,
            detail=f"Dự án hiện còn {active_property_count} bất động sản. Vui lòng xử lý các bất động sản trước khi xóa dự án.",
        )
    item.deleted_at=datetime.now(timezone.utc); item.deleted_by_id=actor.id
    write_audit_log(db,action="inventory.projects.delete",user_id=actor.id,entity_type="projects",entity_id=str(item.id),before_data={"project_code":item.project_code,"name":item.name}); db.commit()
