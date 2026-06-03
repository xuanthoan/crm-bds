from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.permission import Permission
from app.permissions.dependencies import require_permission

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("")
def list_permissions(current_user=Depends(require_permission("permissions.view")), db: Session = Depends(get_db)):
    permissions = db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for permission in permissions:
        grouped[permission.module].append(
            {
                "id": str(permission.id),
                "name": permission.name,
                "code": permission.code,
                "module": permission.module,
                "description": permission.description,
                "created_at": permission.created_at.isoformat(),
                "updated_at": permission.updated_at.isoformat(),
            }
        )
    data = [{"module": module, "permissions": items} for module, items in grouped.items()]
    return success_response(data=data, message="Permissions retrieved")
