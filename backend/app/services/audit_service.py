from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(json_safe(key)): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return str(value)


def _module_from_action(action: str | None) -> str:
    if not action:
        return "system"
    prefix = action.split(".", 1)[0].strip()
    return prefix or "system"


def write_audit_log(
    db: Session,
    *,
    action: str | None,
    user_id: UUID | None = None,
    module: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    entity_label: str | None = None,
    description: str | None = None,
    reason: str | None = None,
    before_data: dict | None = None,
    after_data: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    safe_action = action or "unknown"
    safe_module = module or _module_from_action(safe_action)
    safe_entity_type = entity_type or safe_module or "system"
    safe_entity_id = str(entity_id or user_id or "unknown")
    audit_log = AuditLog(
        actor_id=user_id,
        user_id=user_id,
        action=safe_action,
        module=safe_module,
        entity_type=safe_entity_type,
        entity_id=safe_entity_id,
        entity_label=entity_label,
        description=description,
        reason=reason,
        before_data=json_safe(before_data),
        after_data=json_safe(after_data),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    return audit_log
