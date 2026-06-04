from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_permission
from app.schemas.user import UserCreate, UserResetPassword, UserUpdate
from app.services.user_service import create_user, deactivate_user, get_user_by_id, list_users, reset_user_password, serialize_user, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    role_code: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.view")),
):
    users, meta = list_users(db, page=page, page_size=page_size, search=search, user_status=status_filter, role_code=role_code)
    return success_response(data=[serialize_user(user) for user in users], message="Users retrieved", meta=meta)


@router.post("")
def post_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.create"))):
    user = create_user(db, payload, current_user)
    return success_response(data=serialize_user(user), message="User created")


def _get_user(db: Session, user_id: UUID) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/{user_id}")
def get_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.view"))):
    return success_response(data=serialize_user(_get_user(db, user_id)), message="User retrieved")


@router.put("/{user_id}")
def put_user(user_id: UUID, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.update"))):
    user = update_user(db, _get_user(db, user_id), payload, current_user)
    return success_response(data=serialize_user(user), message="User updated")


@router.post("/{user_id}/deactivate")
def deactivate(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.deactivate"))):
    user = deactivate_user(db, _get_user(db, user_id), current_user)
    return success_response(data=serialize_user(user), message="User deactivated")


@router.post("/{user_id}/reset-password")
def reset_password(user_id: UUID, payload: UserResetPassword, db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.update"))):
    reset_user_password(db, _get_user(db, user_id), payload, current_user)
    return success_response(data=None, message="Password reset successful")
