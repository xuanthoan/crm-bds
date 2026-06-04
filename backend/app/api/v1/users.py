from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_permission
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import create_user, deactivate_user, get_user_by_id, list_users, serialize_user, update_user
from fastapi import HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def get_users(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(require_permission("users.view"))):
    users, total = list_users(db, skip, limit)
    return success_response(data=[serialize_user(user) for user in users], message="Users retrieved", meta={"skip": skip, "limit": limit, "total": total})


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
