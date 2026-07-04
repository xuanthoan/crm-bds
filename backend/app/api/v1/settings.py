from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, user_has_permission
from app.services import settings_service as svc

router = APIRouter(prefix='/settings', tags=['settings'])


class CommissionPayoutPolicyIn(BaseModel):
    policy_code: str


def need(*codes):
    def dep(actor: User = Depends(require_auth)):
        if actor.is_superuser or any(user_has_permission(actor, c) for c in codes):
            return actor
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Missing required permission')
    return dep


@router.get('/commission-payout-policy')
def get_policy(db: Session = Depends(get_db), actor: User = Depends(need('settings.manage', 'settings.manage_master_data', 'commissions.view'))):
    return success_response(svc.get_sales_commission_payout_policy(db))


@router.put('/commission-payout-policy')
def update_policy(payload: CommissionPayoutPolicyIn, db: Session = Depends(get_db), actor: User = Depends(need('settings.manage', 'settings.manage_master_data'))):
    return success_response(svc.update_sales_commission_payout_policy(db, payload.policy_code, actor), 'Đã cập nhật chính sách chi hoa hồng sale.')
