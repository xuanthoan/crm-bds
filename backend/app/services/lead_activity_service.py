import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.leads.constants import CONTACT_ACTIVITY_TYPES, LEAD_ACTIVITY_TYPES
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models.user import User
from app.schemas.lead_activity import LeadActivityCreate
from app.services.audit_service import write_audit_log

UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


def create_activity_record(
    db: Session,
    *,
    lead: Lead,
    actor: User,
    activity_type: str,
    content: str,
    title: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> LeadActivity:
    activity = LeadActivity(
        lead_id=lead.id,
        user_id=actor.id,
        activity_type=activity_type,
        title=title,
        content=content,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(activity)
    return activity


def add_lead_activity(db: Session, lead: Lead, payload: LeadActivityCreate, actor: User) -> LeadActivity:
    if payload.activity_type not in LEAD_ACTIVITY_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loại hoạt động không hợp lệ")
    activity = create_activity_record(
        db,
        lead=lead,
        actor=actor,
        activity_type=payload.activity_type,
        title=payload.title,
        content=payload.content.strip(),
    )
    if payload.activity_type in CONTACT_ACTIVITY_TYPES:
        lead.last_contact_at = datetime.now(timezone.utc)
    write_audit_log(
        db,
        action="leads.add_activity",
        user_id=actor.id,
        entity_type="leads",
        entity_id=str(lead.id),
        after_data={"activity_type": payload.activity_type, "title": payload.title, "content": payload.content},
    )
    db.commit()
    db.refresh(activity)
    return activity


def _resolve_owner_name(db: Session | None, value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    identifier, separator, stored_name = value.partition(" - ")
    if separator and stored_name.strip():
        return stored_name.strip()
    if not UUID_PATTERN.fullmatch(identifier):
        return value
    user = db.scalar(select(User).where(User.id == UUID(identifier))) if db else None
    return user.full_name if user else "Người dùng không còn tồn tại"


def serialize_activity(activity: LeadActivity, db: Session | None = None) -> dict:
    old_owner_name = _resolve_owner_name(db, activity.old_value) if activity.activity_type == "assignment" else None
    new_owner_name = _resolve_owner_name(db, activity.new_value) if activity.activity_type == "assignment" else None
    return {
        "id": activity.id,
        "activity_type": activity.activity_type,
        "title": activity.title,
        "content": activity.content,
        "old_value": old_owner_name if activity.activity_type == "assignment" else activity.old_value,
        "new_value": new_owner_name if activity.activity_type == "assignment" else activity.new_value,
        "old_owner_name": old_owner_name,
        "new_owner_name": new_owner_name,
        "user": {
            "id": activity.user.id,
            "full_name": activity.user.full_name,
            "email": activity.user.email,
        },
        "created_at": activity.created_at,
    }
