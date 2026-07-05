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

def create_audit_log(db: Session, *, actor=None, action: str | None = None, module: str | None = None, entity_type: str | None = None, entity_id=None, entity_label=None,
                     before_data=None, after_data=None, changed_fields=None, description=None, reason=None, request=None,
                     request_id=None, commit: bool = False):
    actor_id, actor_name, actor_email = get_actor_snapshot(actor)
    ip_address = getattr(getattr(request, 'client', None), 'host', None) if request is not None else None
    user_agent = request.headers.get('user-agent') if request is not None and getattr(request, 'headers', None) else None
    safe_action = action or 'unknown'
    safe_module = module or 'system'
    safe_entity_type = entity_type or 'system'
    safe_entity_id = str(entity_id or actor_id or 'unknown')
    log = AuditLog(actor_id=actor_id, user_id=actor_id, actor_name=actor_name, actor_email=actor_email, action=safe_action,
                   module=safe_module, entity_type=safe_entity_type, entity_id=safe_entity_id, entity_label=entity_label,
                   before_data=sanitize_audit_data(before_data), after_data=sanitize_audit_data(after_data),
                   changed_fields=sanitize_audit_data(changed_fields), description=description, reason=reason,
                   request_id=request_id, ip_address=ip_address, user_agent=user_agent)
    try:
        db.add(log)
        if commit: db.commit()
    except Exception:
        db.rollback()
    return log



STALE_MODULE_VALUES = {'audit_log', 'system', 'unknown', None, ''}
ACTION_MODULE_PREFIXES = {
    'auth.': 'auth', 'deals.': 'deals', 'bookings.': 'bookings', 'contracts.': 'contracts',
    'leads.': 'leads', 'customers.': 'customers', 'payments.': 'payments', 'receipts.': 'receipts', 'invoices.': 'invoices',
    'inventory.properties.': 'inventory.properties', 'property_units.': 'property_units',
    'sales_commission.': 'sales_commission', 'commissions.': 'sales_commission',
    'company_commission.': 'company_commission', 'commission_payment_voucher.': 'commission_payment_voucher',
    'commission_payout_policy.': 'commission_payout_policy',
}

def infer_module_from_action(module: str | None, action: str | None) -> str:
    if module not in STALE_MODULE_VALUES:
        return module or 'system'
    action_text = action or ''
    for prefix, inferred in ACTION_MODULE_PREFIXES.items():
        if action_text.startswith(prefix):
            return inferred
    return module or 'system'

def _lookup_entity_label(db: Session | None, entity_type: str | None, entity_id: str | None) -> str | None:
    if not db or not entity_type or not entity_id or entity_id in {'unknown', 'null', 'undefined'}:
        return None
    from app.models.booking import Booking
    from app.models.commission_payment_voucher import SalesCommissionPaymentVoucher
    from app.models.company_commission import CompanyCommissionReceivable
    from app.models.contract import Contract
    from app.models.deal import Deal
    from app.models.property_unit import PropertyUnit
    from app.models.sales_commission import SalesCommission
    from app.models.user import User
    normalized = entity_type.strip()
    lookups = {
        'contract': (Contract, 'contract_code'), 'contracts': (Contract, 'contract_code'),
        'booking': (Booking, 'booking_code'), 'bookings': (Booking, 'booking_code'),
        'deal': (Deal, 'deal_code'), 'deals': (Deal, 'deal_code'),
        'property_unit': (PropertyUnit, 'property_code'), 'property_units': (PropertyUnit, 'property_code'), 'inventory.properties': (PropertyUnit, 'property_code'),
        'sales_commission': (SalesCommission, 'commission_code'),
        'company_commission': (CompanyCommissionReceivable, 'receivable_code'),
        'commission_payment_voucher': (SalesCommissionPaymentVoucher, 'code'),
        'user': (User, 'email'), 'auth': (User, 'email'),
    }
    target = lookups.get(normalized)
    if not target:
        return None
    model, field_name = target
    try:
        item = db.query(model).filter(model.id == entity_id).first()
    except Exception:
        return None
    if not item:
        return None
    value = getattr(item, field_name, None)
    if normalized in {'user', 'auth'}:
        return value or getattr(item, 'full_name', None)
    return value


def _lookup_actor_snapshot(db: Session | None, actor_id) -> tuple[str | None, str | None]:
    if not db or not actor_id:
        return None, None
    from app.models.user import User
    try:
        user = db.query(User).filter(User.id == actor_id).first()
    except Exception:
        return None, None
    if not user:
        return None, None
    return getattr(user, 'full_name', None), getattr(user, 'email', None)

def _has_friendly_label(value: str | None) -> bool:
    if not value:
        return False
    text = str(value).strip().lower()
    return text not in {'null', 'undefined', 'unknown'}

def audit_log_to_dict(log: AuditLog, db: Session | None = None):
    display_module = infer_module_from_action(log.module, log.action)
    entity_label = log.entity_label if _has_friendly_label(log.entity_label) else _lookup_entity_label(db, log.entity_type, log.entity_id)
    entity_display = entity_label or None
    actor_id = log.actor_id or log.user_id
    actor_name, actor_email = log.actor_name, log.actor_email
    if not actor_name and not actor_email:
        actor_name, actor_email = _lookup_actor_snapshot(db, actor_id)
    if not actor_name and not actor_email and log.entity_type == 'user' and _has_friendly_label(entity_label):
        actor_email = entity_label
    return {'id': str(log.id), 'actor_id': str(actor_id) if actor_id else None,
            'actor_name': actor_name, 'actor_email': actor_email, 'action': log.action,
            'action_label': ACTION_LABELS.get(log.action, log.action), 'module': display_module,
            'module_label': MODULE_LABELS.get(display_module, display_module), 'entity_type': log.entity_type,
            'entity_id': log.entity_id, 'entity_label': entity_label, 'entity_display': entity_display, 'before_data': log.before_data,
            'after_data': log.after_data, 'changed_fields': log.changed_fields, 'description': log.description,
            'reason': log.reason, 'ip_address': log.ip_address, 'user_agent': log.user_agent,
            'created_at': log.created_at.isoformat() if log.created_at else None}
