from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.leads.constants import LEAD_ACTIVITY_TYPES
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models.user import User
from app.schemas.lead_activity import LeadActivityCreate
from app.services.audit_service import write_audit_log


def create_activity(
    db: Session,
    *,
    lead: Lead,
    user: User,
    activity_type: str,
    content: str,
    title: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> LeadActivity:
    activity = LeadActivity(lead_id=lead.id, user_id=user.id, activity_type=activity_type, title=title, content=content, old_value=old_value, new_value=new_value)
    db.add(activity)
    return activity


def add_activity(db: Session, lead: Lead, payload: LeadActivityCreate, actor: User) -> LeadActivity:
    if payload.activity_type not in LEAD_ACTIVITY_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loại hoạt động không hợp lệ")
    activity = create_activity(db, lead=lead, user=actor, activity_type=payload.activity_type, title=payload.title, content=payload.content)
    if payload.activity_type in {"call", "zalo", "meeting"}:
        lead.last_contact_at = datetime.now(timezone.utc)
    write_audit_log(db, action="leads.add_activity", user_id=actor.id, entity_type="leads", entity_id=str(lead.id), after_data={"activity_type": payload.activity_type, "title": payload.title})
    db.commit()
    db.refresh(activity)
    return activity
