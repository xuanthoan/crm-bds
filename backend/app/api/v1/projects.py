from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import create_project,get_project_detail,list_projects,serialize_project,soft_delete_project,update_project
router=APIRouter(prefix="/projects",tags=["projects"])
@router.get("")
def get_projects(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str|None=None,developer:str|None=None,province:str|None=None,district:str|None=None,project_type:str|None=None,status_filter:str|None=Query(None,alias="status"),db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    items,meta=list_projects(db,actor,page=page,page_size=page_size,q=q,developer=developer,province=province,district=district,project_type=project_type,status=status_filter);return success_response([serialize_project(x) for x in items],meta=meta)
@router.post("",status_code=status.HTTP_201_CREATED)
def post_project(payload:ProjectCreate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_project(create_project(db,payload,actor)),"Tạo dự án thành công")
@router.get("/{project_id}")
def get_project(project_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):
    item,count=get_project_detail(db,project_id,actor);return success_response(serialize_project(item,count))
@router.put("/{project_id}")
def put_project(project_id:UUID,payload:ProjectUpdate,db:Session=Depends(get_db),actor:User=Depends(require_auth)):return success_response(serialize_project(update_project(db,project_id,payload,actor)),"Cập nhật dự án thành công")
@router.delete("/{project_id}")
def delete_project(project_id:UUID,db:Session=Depends(get_db),actor:User=Depends(require_auth)):soft_delete_project(db,project_id,actor);return success_response(None,"Xóa dự án thành công")
