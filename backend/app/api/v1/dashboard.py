from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth,user_has_permission
from app.services.dashboard_service import BOSS_DASHBOARD_PERMISSION,get_boss_dashboard,get_my_work_summary,get_team_work_summary
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/my-work")
@router.get("/sale")
def my_work(db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(get_my_work_summary(db,user),"My work summary retrieved")
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
