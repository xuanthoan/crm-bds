from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest
from app.services import auth_service
from app.services.user_service import serialize_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    data = auth_service.login(db, payload.email, payload.password, request)
    return success_response(data=data, message="Login successful")


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = auth_service.refresh_access_token(db, payload.refresh_token)
    return success_response(data=data, message="Token refreshed")


@router.post("/logout")
def logout(payload: LogoutRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    auth_service.logout(db, current_user, payload.refresh_token, request)
    return success_response(data=None, message="Logout successful")


@router.get("/me")
def me(current_user: User = Depends(require_auth)):
    return success_response(data=serialize_current_user(current_user), message="Current user")
