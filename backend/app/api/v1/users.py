from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.permissions.dependencies import require_permission
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import create_user, deactivate_user, get_user_by_id, list_users, serialize_user, update_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(require_permission("users.view")),
    db: Session = Depends(get_db),
):
    users, total = list_users(db, page=page, page_size=page_size)
    data = {"items": [serialize_user(user).model_dump(mode="json") for user in users], "total": total, "page": page, "page_size": page_size}
    return success_response(data=data, message="Users retrieved")


@router.post("")
def post_user(payload: UserCreate, current_user=Depends(require_permission("users.create")), db: Session = Depends(get_db)):
    user = create_user(db, payload, current_user)
    return success_response(data=serialize_user(user).model_dump(mode="json"), message="User created")


@router.get("/{user_id}")
def get_user(user_id: UUID, current_user=Depends(require_permission("users.view")), db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    return success_response(data=serialize_user(user).model_dump(mode="json"), message="User retrieved")


@router.put("/{user_id}")
def put_user(user_id: UUID, payload: UserUpdate, current_user=Depends(require_permission("users.update")), db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    updated_user = update_user(db, user, payload, current_user)
    return success_response(data=serialize_user(updated_user).model_dump(mode="json"), message="User updated")


@router.post("/{user_id}/deactivate")
def deactivate(user_id: UUID, current_user=Depends(require_permission("users.deactivate")), db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    updated_user = deactivate_user(db, user, current_user)
    return success_response(data=serialize_user(updated_user).model_dump(mode="json"), message="User deactivated")
