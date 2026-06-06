from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.services.dashboard_service import get_my_work_summary,get_team_work_summary
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/my-work")
@router.get("/sale")
def my_work(db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(get_my_work_summary(db,user),"My work summary retrieved")
@router.get("/team-work")
@router.get("/leader")
def team_work(db:Session=Depends(get_db),user:User=Depends(require_auth)):return success_response(get_team_work_summary(db,user),"Team work summary retrieved")
