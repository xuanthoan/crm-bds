from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.lead import Lead
from app.models.user import User
from app.permissions.dependencies import require_auth, require_permission
from app.schemas.lead import LeadAssign, LeadCreate, LeadStatusUpdate, LeadUpdate
from app.schemas.lead_activity import LeadActivityCreate
from app.schemas.organization import LeadReclaim, LeadTransfer
from app.services.lead_activity_service import add_lead_activity, serialize_activity
from app.services.lead_service import (
    assign_lead,
    can_view_lead,
    change_lead_status,
    create_lead,
    delete_lead,
    get_lead_by_id,
    list_leads,
    list_overdue_leads,
    reclaim_lead,
    transfer_lead,
    require_update_access,
    serialize_lead,
    update_lead,
)

router = APIRouter(prefix="/leads", tags=["leads"])


def _get_accessible_lead(db: Session, lead_id: UUID, current_user: User) -> Lead:
    lead = get_lead_by_id(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy lead")
    if not can_view_lead(db, current_user, lead):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập lead này")
    return lead


@router.get("")
def get_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    source: str | None = Query(None),
    owner_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    team_id: UUID | None = Query(None),
    created_from: date | None = Query(None),
    created_to: date | None = Query(None),
    next_follow_up_from: date | None = Query(None),
    next_follow_up_to: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    leads, meta = list_leads(db, current_user, page=page, page_size=page_size, search=search, lead_status=status_filter, priority=priority, source=source, owner_id=owner_id, department_id=department_id, team_id=team_id, created_from=created_from, created_to=created_to, next_follow_up_from=next_follow_up_from, next_follow_up_to=next_follow_up_to)
    return success_response(data=[serialize_lead(lead) for lead in leads], message="Leads retrieved", meta=meta)


@router.get("/overdue")
def get_overdue_leads(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), owner_id: UUID | None = None, priority: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    leads, meta = list_overdue_leads(db, current_user, page=page, page_size=page_size, owner_id=owner_id, priority=priority)
    return success_response(data=[serialize_lead(lead) for lead in leads], message="Overdue leads retrieved", meta=meta)


@router.post("")
def post_lead(payload: LeadCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("leads.create"))):
    return success_response(data=serialize_lead(create_lead(db, payload, current_user), detail=True), message="Lead created")


@router.get("/{lead_id}")
def get_lead(lead_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_lead(_get_accessible_lead(db, lead_id, current_user), detail=True), message="Lead retrieved")


@router.put("/{lead_id}")
def put_lead(lead_id: UUID, payload: LeadUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = _get_accessible_lead(db, lead_id, current_user)
    return success_response(data=serialize_lead(update_lead(db, lead, payload, current_user), detail=True), message="Lead updated")


@router.post("/{lead_id}/status")
def post_lead_status(lead_id: UUID, payload: LeadStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = _get_accessible_lead(db, lead_id, current_user)
    return success_response(data=serialize_lead(change_lead_status(db, lead, payload, current_user), detail=True), message="Lead status updated")


@router.post("/{lead_id}/assign")
def post_lead_assignment(lead_id: UUID, payload: LeadAssign, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = _get_accessible_lead(db, lead_id, current_user)
    return success_response(data=serialize_lead(assign_lead(db, lead, payload, current_user), detail=True), message="Lead assigned")


@router.post("/{lead_id}/transfer")
def post_lead_transfer(lead_id: UUID, payload: LeadTransfer, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = _get_accessible_lead(db, lead_id, current_user)
    return success_response(data=serialize_lead(transfer_lead(db, lead, payload.new_owner_id, payload.reason, current_user), detail=True), message="Lead transferred")


@router.post("/{lead_id}/reclaim")
def post_lead_reclaim(lead_id: UUID, payload: LeadReclaim, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = get_lead_by_id(db, lead_id)
    if lead is None: raise HTTPException(status_code=404, detail="Không tìm thấy lead")
    return success_response(data=serialize_lead(reclaim_lead(db, lead, payload.new_owner_id, payload.reason, current_user), detail=True), message="Lead reclaimed")


@router.post("/{lead_id}/activities")
def post_lead_activity(lead_id: UUID, payload: LeadActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = _get_accessible_lead(db, lead_id, current_user)
    require_update_access(db, current_user, lead)
    return success_response(data=serialize_activity(add_lead_activity(db, lead, payload, current_user)), message="Lead activity added")


@router.delete("/{lead_id}")
def remove_lead(lead_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_permission("leads.delete"))):
    lead = _get_accessible_lead(db, lead_id, current_user)
    delete_lead(db, lead, current_user)
    return success_response(data=None, message="Lead deleted")
