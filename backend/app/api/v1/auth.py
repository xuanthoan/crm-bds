from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.permissions.dependencies import require_auth
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest
from app.services import auth_service
from app.services.user_service import serialize_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    data = auth_service.login(db, email=payload.email, password=payload.password, request=request)
    return success_response(data=data, message="Login successful")


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = auth_service.refresh_access_token(db, payload.refresh_token)
    return success_response(data=data, message="Token refreshed")


@router.post("/logout")
def logout(payload: LogoutRequest, request: Request, current_user=Depends(require_auth), db: Session = Depends(get_db)):
    auth_service.logout(db, user=current_user, refresh_token=payload.refresh_token, request=request)
    return success_response(data=None, message="Logout successful")


@router.get("/me")
def me(current_user=Depends(require_auth)):
    return success_response(data=serialize_user(current_user).model_dump(mode="json"), message="Current user")
