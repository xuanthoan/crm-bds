from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_permission
from app.services.permission_service import list_permissions_grouped

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("")
def get_permissions(db: Session = Depends(get_db), current_user: User = Depends(require_permission("permissions.view"))):
    return success_response(data=list_permissions_grouped(db), message="Permissions retrieved")
