from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth,user_has_permission
from app.services.dashboard_service import BOSS_DASHBOARD_PERMISSION,FINANCE_DASHBOARD_PERMISSION,SALE_DASHBOARD_PERMISSION,get_boss_dashboard,get_finance_dashboard,get_my_work_summary,get_team_work_summary,get_sales_management_dashboard,get_sale_dashboard
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/my-work")
def my_work(db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(get_my_work_summary(db,user),"My work summary retrieved")
@router.get("/sale")
def sale_dashboard(preset:str|None=None,start_date:str|None=None,end_date:str|None=None,from_date:str|None=None,to_date:str|None=None,user_id:str|None=None,sale_id:str|None=None,team_id:str|None=None,department_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    if not (user_has_permission(user,SALE_DASHBOARD_PERMISSION) or user_has_permission(user,"dashboard.view.all")):
        raise HTTPException(403,"Bạn không có quyền xem dashboard của tôi")
    try:
        return success_response(get_sale_dashboard(db,user,preset,start_date or from_date,end_date or to_date),"Sale dashboard retrieved")
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc
@router.get("/team-work")
@router.get("/leader")
def team_work(db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(get_team_work_summary(db,user),"Team work summary retrieved")

@router.get("/boss")
def boss_dashboard(preset:str|None=None,from_date:str|None=None,to_date:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    if not (user_has_permission(user,BOSS_DASHBOARD_PERMISSION) or user_has_permission(user,"dashboard.view.all") or user_has_permission(user,"reports.view.ceo_dashboard")):
        raise HTTPException(403,"Bạn không có quyền xem dashboard giám đốc")
    try:
        return success_response(get_boss_dashboard(db,preset,from_date,to_date),"Boss dashboard retrieved")
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc

@router.get("/finance")
def finance_dashboard(preset:str|None=None,date_from:str|None=None,date_to:str|None=None,from_date:str|None=None,to_date:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    if not (user_has_permission(user, FINANCE_DASHBOARD_PERMISSION) or user_has_permission(user, "dashboard.view.all")):
        raise HTTPException(403, "Bạn không có quyền xem tổng quan tài chính")
    try:
        return success_response(get_finance_dashboard(db, preset, date_from or from_date, date_to or to_date), "Finance dashboard retrieved")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@router.get("/sales-management")
def sales_management_dashboard(preset:str|None=None,start_date:str|None=None,end_date:str|None=None,from_date:str|None=None,to_date:str|None=None,scope_type:str|None="auto",team_id:str|None=None,department_id:str|None=None,db:Session=Depends(get_db),user:User=Depends(require_auth)):
    try:
        return success_response(get_sales_management_dashboard(db,user,preset,start_date or from_date,end_date or to_date,scope_type,team_id,department_id),"Sales management dashboard retrieved")
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc
