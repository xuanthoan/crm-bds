from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.audit_constants import ACTION_LABELS, MODULE_LABELS
from app.models.audit_log import AuditLog

SENSITIVE_KEYS = {'password','hashed_password','token','access_token','refresh_token','secret','api_key','otp','reset_token'}

def _jsonable(value):
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, Decimal): return float(value)
    if isinstance(value, UUID): return str(value)
    if isinstance(value, dict): return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)): return [_jsonable(v) for v in value]
    return value

def sanitize_audit_data(data):
    if data is None: return None
    if isinstance(data, dict):
        return {k: sanitize_audit_data(v) for k, v in data.items() if str(k).lower() not in SENSITIVE_KEYS}
    if isinstance(data, list): return [sanitize_audit_data(v) for v in data]
    return _jsonable(data)

def snapshot_model(model):
    if model is None: return None
    data = {}
    for column in getattr(model, '__table__').columns:
        data[column.name] = getattr(model, column.name)
    return sanitize_audit_data(data)

def diff_dict(before, after):
    before = sanitize_audit_data(before) or {}
    after = sanitize_audit_data(after) or {}
    changed = {}
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            changed[key] = {'before': before.get(key), 'after': after.get(key)}
    return changed

def get_actor_snapshot(user):
    if not user: return None, None, None
    return getattr(user, 'id', None), getattr(user, 'full_name', None), getattr(user, 'email', None)

def create_audit_log(db: Session, *, actor=None, action: str, module: str, entity_type: str, entity_id, entity_label=None,
                     before_data=None, after_data=None, changed_fields=None, description=None, reason=None, request=None,
                     request_id=None, commit: bool = False):
    actor_id, actor_name, actor_email = get_actor_snapshot(actor)
    ip_address = getattr(getattr(request, 'client', None), 'host', None) if request is not None else None
    user_agent = request.headers.get('user-agent') if request is not None and getattr(request, 'headers', None) else None
    log = AuditLog(actor_id=actor_id, user_id=actor_id, actor_name=actor_name, actor_email=actor_email, action=action,
                   module=module, entity_type=entity_type, entity_id=str(entity_id), entity_label=entity_label,
                   before_data=sanitize_audit_data(before_data), after_data=sanitize_audit_data(after_data),
                   changed_fields=sanitize_audit_data(changed_fields), description=description, reason=reason,
                   request_id=request_id, ip_address=ip_address, user_agent=user_agent)
    try:
        db.add(log)
        if commit: db.commit()
    except Exception:
        db.rollback()
    return log

def audit_log_to_dict(log: AuditLog):
    return {'id': str(log.id), 'actor_id': str(log.actor_id or log.user_id) if (log.actor_id or log.user_id) else None,
            'actor_name': log.actor_name, 'actor_email': log.actor_email, 'action': log.action,
            'action_label': ACTION_LABELS.get(log.action, log.action), 'module': log.module,
            'module_label': MODULE_LABELS.get(log.module, log.module), 'entity_type': log.entity_type,
            'entity_id': log.entity_id, 'entity_label': log.entity_label, 'before_data': log.before_data,
            'after_data': log.after_data, 'changed_fields': log.changed_fields, 'description': log.description,
            'reason': log.reason, 'ip_address': log.ip_address, 'user_agent': log.user_agent,
            'created_at': log.created_at.isoformat() if log.created_at else None}
