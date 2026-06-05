from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth, require_permission
from app.schemas.lead import LeadAssign, LeadCreate, LeadStatusUpdate, LeadUpdate
from app.schemas.lead_activity import LeadActivityCreate
from app.services.lead_activity_service import add_activity
from app.services.lead_service import assign_lead, change_status, create_lead, delete_lead, ensure_update_access, ensure_view_access, get_lead_or_404, list_leads, serialize_lead, update_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("")
def get_leads(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, status: str | None = None, priority: str | None = None, source: str | None = None, owner_id: UUID | None = None, created_from: date | None = None, created_to: date | None = None, next_follow_up_from: date | None = None, next_follow_up_to: date | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    leads, meta = list_leads(db, current_user, page=page, page_size=page_size, search=search, lead_status=status, priority=priority, source=source, owner_id=owner_id, created_from=created_from, created_to=created_to, next_follow_up_from=next_follow_up_from, next_follow_up_to=next_follow_up_to)
    return success_response(data=[serialize_lead(lead) for lead in leads], message="Leads retrieved", meta=meta)


@router.post("")
def post_lead(payload: LeadCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("leads.create"))):
    return success_response(data=serialize_lead(create_lead(db, payload, current_user), detail=True), message="Lead created")


@router.get("/{lead_id}")
def get_lead(lead_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = get_lead_or_404(db, lead_id); ensure_view_access(lead, current_user)
    return success_response(data=serialize_lead(lead, detail=True), message="Lead retrieved")


@router.put("/{lead_id}")
def put_lead(lead_id: UUID, payload: LeadUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_lead(update_lead(db, get_lead_or_404(db, lead_id), payload, current_user), detail=True), message="Lead updated")


@router.post("/{lead_id}/status")
def post_status(lead_id: UUID, payload: LeadStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_lead(change_status(db, get_lead_or_404(db, lead_id), payload, current_user), detail=True), message="Lead status updated")


@router.post("/{lead_id}/assign")
def post_assign(lead_id: UUID, payload: LeadAssign, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_lead(assign_lead(db, get_lead_or_404(db, lead_id), payload, current_user), detail=True), message="Lead assigned")


@router.post("/{lead_id}/activities")
def post_activity(lead_id: UUID, payload: LeadActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    lead = get_lead_or_404(db, lead_id); ensure_update_access(lead, current_user)
    activity = add_activity(db, lead, payload, current_user)
    return success_response(data={"id": activity.id, "activity_type": activity.activity_type, "created_at": activity.created_at}, message="Lead activity added")


@router.delete("/{lead_id}")
def remove_lead(lead_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_permission("leads.delete"))):
    delete_lead(db, get_lead_or_404(db, lead_id), current_user)
    return success_response(data=None, message="Lead deleted")
